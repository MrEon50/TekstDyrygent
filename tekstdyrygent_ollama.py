import json
import urllib.request
import urllib.error
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog


class OllamaMixin:
    def init_ollama(self):
        """Inicjalizacja ustawień Ollama"""
        self.ollama_settings_file = "ollama_settings.json"
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "mistral"
        self.ollama_timeout = 300
        self.ollama_num_ctx = 2048      # Mniejszy kontekst = szybsza odpowiedź
        self.ollama_keep_alive = "10m"  # Trzymaj model w RAM przez 10 minut
        self.ollama_system_prompt = ""  # Główna instrukcja (np. "Odpowiadaj po polsku")
        self._ollama_cancel = False
        self._ollama_working = False
        self.ollama_show_in_new_window = False
        self.ollama_replace_selection = False  # Domyślnie NIE zastępuj (dopisz pod spodem)
        # Wewnętrzny znacznik pozycji wstawiania (line.col jako string)
        self._ai_insert_pos = None
        self._first_token_received = False

        self.load_ollama_settings()

    def load_ollama_settings(self):
        """Wczytuje ustawienia z pliku"""
        try:
            import os
            if os.path.exists(self.ollama_settings_file):
                with open(self.ollama_settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.ollama_url = data.get("url", self.ollama_url)
                    self.ollama_model = data.get("model", self.ollama_model)
                    self.ollama_timeout = data.get("timeout", self.ollama_timeout)
                    self.ollama_num_ctx = data.get("num_ctx", self.ollama_num_ctx)
                    self.ollama_keep_alive = data.get("keep_alive", self.ollama_keep_alive)
                    self.ollama_system_prompt = data.get("system_prompt", self.ollama_system_prompt)
                    self.ollama_show_in_new_window = data.get("show_in_new_window", self.ollama_show_in_new_window)
                    self.ollama_replace_selection = data.get("replace_selection", self.ollama_replace_selection)
        except Exception as e:
            print(f"Błąd ładowania ustawień Ollama: {e}")

    def save_ollama_settings(self):
        """Zapisuje ustawienia do pliku"""
        try:
            data = {
                "url": self.ollama_url,
                "model": self.ollama_model,
                "timeout": self.ollama_timeout,
                "num_ctx": self.ollama_num_ctx,
                "keep_alive": self.ollama_keep_alive,
                "system_prompt": self.ollama_system_prompt,
                "show_in_new_window": self.ollama_show_in_new_window,
                "replace_selection": self.ollama_replace_selection
            }
            with open(self.ollama_settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Błąd zapisu ustawień Ollama: {e}")

    def get_ollama_models(self):
        """Pobiera listę modeli z serwera Ollama"""
        try:
            url = f"{self.ollama_url}/api/tags"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    #  Niskopoziomowe wywołanie Ollama – strumień tokenów w tle           #
    # ------------------------------------------------------------------ #
    def _ai_append(self, token):
        """
        Wstawia kolejny token dokładnie w miejscu wskazanym przez
        self._ai_insert_pos i przesuwa ten wskaźnik o długość tokenu.
        Działa wyłącznie w wątku GUI (wywołane przez root.after).
        """
        if self._ollama_cancel:
            return
        if not self._ai_insert_pos:
            return
        try:
            pos = self._ai_insert_pos
            self.text_area.insert(pos, token)
            # Przesuń wskaźnik o liczbę wstawionych znaków
            self._ai_insert_pos = self.text_area.index(f"{pos} + {len(token)} chars")
            self.text_area.see(self._ai_insert_pos)
        except Exception as e:
            # Pokaż błąd w status bar zamiast go chować
            try:
                self.status_bar.config(
                    text=f"⚠️ Błąd wstawiania tekstu AI: {e}", fg="orange")
            except Exception:
                pass

    def call_ollama(self, prompt, text_content, on_token, on_done, on_error=None):
        """
        Uruchamia generowanie w wątku daemon.
        on_token(token: str)  – wywoływany dla każdego tokenu (w GUI przez after(0))
        on_done(full_text)    – wywoływany po zakończeniu (w GUI przez after(0))
        on_error()            – opcjonalny callback błędu
        """
        self._ollama_cancel = False
        self._ollama_working = True
        start_time = time.time()

        self._first_token_received = False

        def tick():
            if not self._ollama_working:
                return
            elapsed = int(time.time() - start_time)
            try:
                if self._first_token_received:
                    label = f"🤖 AI generuje... ({elapsed}s)  [Ctrl+Shift+X = anuluj]"
                else:
                    label = f"⏳ Ładowanie modelu ({elapsed}s) – czekaj...  [Ctrl+Shift+X = anuluj]"
                self.status_bar.config(text=label)
            except Exception:
                pass
            self.root.after(1000, tick)

        self.root.after(1000, tick)

        def worker():
            try:
                full_prompt = (
                    f"{prompt}\n\nOto tekst do przetworzenia:\n{text_content}"
                    if text_content else prompt
                )

                payload_dict = {
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": True,
                    "keep_alive": self.ollama_keep_alive,
                    "options": {
                        "num_ctx": self.ollama_num_ctx
                    }
                }
                
                if self.ollama_system_prompt:
                    payload_dict["system"] = self.ollama_system_prompt

                payload = json.dumps(payload_dict).encode("utf-8")

                req = urllib.request.Request(
                    f"{self.ollama_url}/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )

                collected = []
                with urllib.request.urlopen(req, timeout=self.ollama_timeout) as resp:
                    # readline() zamiast for-loop aby ominąć wewnętrzne buforowanie urllib
                    while True:
                        if self._ollama_cancel:
                            return

                        raw_line = resp.readline()
                        if not raw_line:
                            break

                        try:
                            chunk = json.loads(raw_line.decode("utf-8").strip())
                        except json.JSONDecodeError:
                            continue

                        # Błąd zwrócony przez Ollama (np. model nie istnieje)
                        if "error" in chunk:
                            err_text = f"\n[BŁĄD OLLAMA: {chunk['error']}]\n"
                            collected.append(err_text)
                            self.root.after(0, on_token, err_text)
                            break

                        token = chunk.get("response", "")
                        if token:
                            if not self._first_token_received:
                                self._first_token_received = True
                            collected.append(token)
                            self.root.after(0, on_token, token)

                        if chunk.get("done", False):
                            break

                if self._ollama_cancel:
                    return

                self._ollama_working = False
                full = "".join(collected)
                self.root.after(0, lambda: on_done(full))

            except urllib.error.URLError as exc:
                if self._ollama_cancel:
                    return
                self._ollama_working = False
                msg = (
                    f"Nie można połączyć się z Ollama.\n"
                    f"Upewnij się, że serwer działa na {self.ollama_url}\n\n"
                    f"Szczegóły: {exc}"
                )
                def _url_err():
                    if on_error:
                        on_error()
                    messagebox.showerror("Błąd Ollama", msg)
                self.root.after(0, _url_err)

            except Exception as exc:
                if self._ollama_cancel:
                    return
                self._ollama_working = False
                msg = f"Błąd komunikacji z AI: {exc}"
                def _gen_err():
                    if on_error:
                        on_error()
                    messagebox.showerror("Błąd", msg)
                self.root.after(0, _gen_err)

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------ #
    #  Anulowanie                                                          #
    # ------------------------------------------------------------------ #
    def ollama_cancel(self):
        """Natychmiastowe anulowanie generowania"""
        if self._ollama_working:
            self._ollama_cancel = True
            self._ollama_working = False
            try:
                self.status_bar.config(text="❌ Generowanie anulowane.", fg="red")
                self.root.after(3000, lambda: self.status_bar.config(fg="black"))
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    #  Wysokopoziomowe wejście – transformacja zaznaczenia / całości       #
    # ------------------------------------------------------------------ #
    def ollama_transform(self, action_name, custom_prompt=None):
        """Główna funkcja transformacji tekstu przez AI"""
        if self._ollama_working:
            messagebox.showwarning("AI", "AI już pracuje. Poczekaj lub anuluj (Ctrl+Shift+X).")
            return

        try:
            selection = self.text_area.tag_ranges(tk.SEL)

            if selection:
                text_to_process = self.text_area.get(selection[0], selection[1])
                sel_start = self.text_area.index(selection[0])
                sel_end   = self.text_area.index(selection[1])
                has_selection = True
            else:
                text_to_process = self.text_area.get("1.0", tk.END).strip()
                sel_start = "1.0"
                sel_end   = self.text_area.index(tk.END)
                has_selection = False

            if not text_to_process and action_name != "custom":
                messagebox.showwarning("AI", "Brak tekstu do przetworzenia!")
                return

            prompts = {
                "podsumuj":   "Streść poniższy tekst w kilku konkretnych punktach:",
                "popraw":     "Popraw błędy ortograficzne, interpunkcyjne i gramatyczne, zachowując styl. Zwróć tylko poprawiony tekst:",
                "rozwin":     "Rozwiń poniższy tekst, dodając więcej szczegółów i kontekstu:",
                "parafrazuj": "Sparafrazuj poniższy tekst, zmieniając słownictwo, zachowując sens:",
                "tlumacz":    "Przetłumacz poniższy tekst na polski (jeśli obcy) lub angielski (jeśli polski):",
            }

            final_prompt = custom_prompt if custom_prompt else prompts.get(action_name, "Przetwórz poniższy tekst:")

            old_status = self.status_bar.cget("text")
            self.status_bar.config(text="🤖 AI łączy się z modelem...", fg="blue")

            def restore_status():
                if not self._ollama_cancel:
                    self.status_bar.config(text="✅ Gotowe.", fg="green")
                    self.root.after(2000, lambda: self.status_bar.config(
                        text=old_status, fg="black"))

            # --- Tryb: nowe okno ---
            if self.ollama_show_in_new_window:
                res_win, txt_widget = self._create_result_window()

                def on_token(t):
                    if not self._ollama_cancel:
                        txt_widget.insert(tk.END, t)
                        txt_widget.see(tk.END)

                def on_done(full):
                    restore_status()

                self.call_ollama(final_prompt, text_to_process, on_token, on_done, restore_status)
                return

            # --- Tryb: zastąp zaznaczenie / cały tekst ---
            if self.ollama_replace_selection and text_to_process:
                if has_selection:
                    self.text_area.delete(sel_start, sel_end)
                    self._ai_insert_pos = sel_start
                else:
                    self.text_area.delete("1.0", tk.END)
                    self._ai_insert_pos = "1.0"

                def on_token(t):
                    self._ai_append(t)

                def on_done(full):
                    restore_status()

                self.call_ollama(final_prompt, text_to_process, on_token, on_done, restore_status)
                return

            # --- Tryb: dołącz pod tekstem ---
            if text_to_process:
                separator = f"\n\n--- AI ({self.ollama_model}) ---\n"
                self.text_area.insert(sel_end, separator)
                # Pozycja wstawiania = zaraz po separatorze
                self._ai_insert_pos = self.text_area.index(
                    f"{sel_end} + {len(separator)} chars")
            else:
                self._ai_insert_pos = self.text_area.index(tk.INSERT)

            def on_token(t):
                self._ai_append(t)

            def on_done(full):
                self._ai_append("\n")
                restore_status()

            self.call_ollama(final_prompt, text_to_process, on_token, on_done, restore_status)

        except Exception as exc:
            messagebox.showerror("Błąd", f"Błąd AI: {exc}")

    # ------------------------------------------------------------------ #
    #  Zaznaczenie jako prompt                                             #
    # ------------------------------------------------------------------ #
    def ollama_selection_as_prompt(self):
        """Używa zaznaczonego tekstu jako prompt, wkleja wynik pod nim."""
        if self._ollama_working:
            messagebox.showwarning("AI", "AI już pracuje. Poczekaj lub anuluj (Ctrl+Shift+X).")
            return

        try:
            selection = self.text_area.tag_ranges(tk.SEL)
            if not selection:
                messagebox.showwarning("AI", "Zaznacz tekst, który ma być użyty jako prompt!")
                return

            prompt_text = self.text_area.get(selection[0], selection[1])
            # Zapamiętaj indeks początku i końca zaznaczenia jako stały string
            target_start = self.text_area.index(selection[0])
            target_end = self.text_area.index(selection[1])

            old_status = self.status_bar.cget("text")
            self.status_bar.config(text="🤖 AI łączy się z modelem...", fg="blue")

            def restore_status():
                if not self._ollama_cancel:
                    self.status_bar.config(text="✅ Gotowe.", fg="green")
                    self.root.after(2000, lambda: self.status_bar.config(
                        text=old_status, fg="black"))

            # --- Tryb: nowe okno ---
            if self.ollama_show_in_new_window:
                res_win, txt_widget = self._create_result_window()

                def on_token(t):
                    if not self._ollama_cancel:
                        txt_widget.insert(tk.END, t)
                        txt_widget.see(tk.END)

                def on_done(full):
                    restore_status()

                self.call_ollama(prompt_text, "", on_token, on_done, restore_status)
                return

            # --- Tryb: zastąp zaznaczenie ---
            if self.ollama_replace_selection:
                self.text_area.delete(target_start, target_end)
                self._ai_insert_pos = target_start

                def on_token(t):
                    self._ai_append(t)

                def on_done(full):
                    restore_status()

                self.call_ollama(prompt_text, "", on_token, on_done, restore_status)
                return

            # --- Tryb: dołącz pod tekstem (domyślnie) ---
            separator = f"\n\n--- AI ({self.ollama_model}) ---\n"
            self.text_area.insert(target_end, separator)
            self._ai_insert_pos = self.text_area.index(
                f"{target_end} + {len(separator)} chars")

            def on_token(t):
                self._ai_append(t)

            def on_done(full):
                self._ai_append("\n")
                restore_status()

            # Brak kontekstu tekstowego – tylko prompt
            self.call_ollama(prompt_text, "", on_token, on_done, restore_status)

        except Exception as exc:
            messagebox.showerror("Błąd", f"Błąd AI: {exc}")

    # ------------------------------------------------------------------ #
    #  Custom prompt (z zapamiętaniem zaznaczenia)                        #
    # ------------------------------------------------------------------ #
    def ollama_transform_custom(self):
        """Transformacja z własnym promptem"""
        # Zapamiętaj zaznaczenie PRZED otwarciem okna dialogowego
        sel = self.text_area.tag_ranges(tk.SEL)

        prompt = self.custom_askstring(
            "AI Custom Prompt",
            "Wpisz polecenie dla AI\n(np. 'Wyjaśnij pojęcia', 'Zrób tabelę', 'Napisz kontynuację'):"
        )

        # Odtwórz zaznaczenie
        if sel:
            self.text_area.tag_add(tk.SEL, sel[0], sel[1])

        if prompt:
            self.ollama_transform("custom", custom_prompt=prompt)

    def ollama_translate(self):
        """Tłumaczenie na wybrany język"""
        sel = self.text_area.tag_ranges(tk.SEL)

        lang = self.custom_askstring(
            "Tłumacz AI",
            "Na jaki język przetłumaczyć tekst?",
            initialvalue="angielski"
        )

        if sel:
            self.text_area.tag_add(tk.SEL, sel[0], sel[1])

        if lang:
            prompt = (f"Przetłumacz poniższy tekst na język {lang}. "
                      f"Zwróć wyłącznie przetłumaczony tekst, bez komentarzy:")
            self.ollama_transform("custom", custom_prompt=prompt)

    # ------------------------------------------------------------------ #
    #  Okno dialogowe do wpisywania promptu                               #
    # ------------------------------------------------------------------ #
    def custom_askstring(self, title, prompt, initialvalue=""):
        """Niestandardowe okno dialogowe"""
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()  # Ukryj na czas budowania (zapobiega mignięciu w rogu)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 35, 22)

        try:
            dialog.iconbitmap("icon.ico")
        except Exception:
            pass

        tk.Label(dialog, text=prompt, padx=10, pady=10, justify=tk.LEFT).pack(anchor=tk.W)
        entry = tk.Entry(dialog, width=50)
        entry.insert(0, initialvalue)
        entry.pack(padx=10, pady=5, fill=tk.X)
        entry.focus_set()

        result = [None]

        def on_ok(event=None):
            result[0] = entry.get()
            dialog.destroy()

        def on_cancel(event=None):
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=on_ok, width=12,
                  bg="lightgreen").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Anuluj", command=on_cancel, width=12,
                  bg="lightcoral").pack(side=tk.LEFT, padx=5)

        entry.bind("<Return>", on_ok)
        entry.bind("<Escape>", on_cancel)

        dialog.deiconify()  # Pokaż okno, gdy jest już wyśrodkowane
        self.root.wait_window(dialog)
        return result[0]

    # ------------------------------------------------------------------ #
    #  Okno konfiguracji                                                   #
    # ------------------------------------------------------------------ #
    def ollama_config_window(self):
        """Okno konfiguracji Ollama"""
        win = tk.Toplevel(self.root)
        win.withdraw()  # Ukryj na czas budowania
        win.title("Ustawienia Ollama")
        win.transient(self.root)
        self.center_window(win, 35, 60)

        try:
            win.iconbitmap("icon.ico")
        except Exception:
            pass

        tk.Label(win, text="KONFIGURACJA OLLAMA",
                 font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(win, text="URL serwera:").pack(anchor=tk.W, padx=20)
        url_entry = tk.Entry(win, width=42)
        url_entry.insert(0, self.ollama_url)
        url_entry.pack(padx=20, pady=4)

        tk.Label(win, text="Model (wybierz z listy lub wpisz ręcznie):").pack(
            anchor=tk.W, padx=20)

        models = self.get_ollama_models()
        model_var = tk.StringVar(value=self.ollama_model)

        if models:
            model_dropdown = tk.OptionMenu(win, model_var, *models)
        else:
            model_dropdown = tk.OptionMenu(win, model_var, self.ollama_model)
            tk.Label(win, text="(Brak połączenia – wpisz model ręcznie poniżej)",
                     fg="red", font=("Arial", 8)).pack(padx=20)

        model_dropdown.pack(padx=20, pady=4, fill=tk.X)

        tk.Label(win, text="Ręczna nazwa modelu:").pack(anchor=tk.W, padx=20)
        manual_entry = tk.Entry(win, width=42)
        manual_entry.insert(0, self.ollama_model)
        manual_entry.pack(padx=20, pady=4)

        tk.Label(win, text="System Prompt (instrukcje dla modelu, np. 'Odpowiadaj po polsku'):").pack(anchor=tk.W, padx=20)
        sysprompt_entry = tk.Entry(win, width=50)
        sysprompt_entry.insert(0, self.ollama_system_prompt)
        sysprompt_entry.pack(padx=20, pady=4)

        new_win_var  = tk.BooleanVar(value=self.ollama_show_in_new_window)
        replace_var  = tk.BooleanVar(value=self.ollama_replace_selection)
        tk.Checkbutton(win, text="Pokaż odpowiedź w nowym oknie",
                       variable=new_win_var).pack(anchor=tk.W, padx=20)
        tk.Checkbutton(win, text="Zastąp zaznaczenie (jeśli odznaczone, dopisze się pod spodem)",
                       variable=replace_var).pack(anchor=tk.W, padx=20)

        tk.Label(win, text="Timeout (s):").pack(anchor=tk.W, padx=20)
        timeout_entry = tk.Entry(win, width=10)
        timeout_entry.insert(0, str(self.ollama_timeout))
        timeout_entry.pack(anchor=tk.W, padx=20, pady=4)

        tk.Label(win, text="Kontekst (num_ctx) – mniej = szybciej, np. 2048:").pack(anchor=tk.W, padx=20)
        numctx_entry = tk.Entry(win, width=10)
        numctx_entry.insert(0, str(self.ollama_num_ctx))
        numctx_entry.pack(anchor=tk.W, padx=20, pady=4)

        tk.Label(win, text="Keep-alive (czas w RAM, np. 10m, 1h, -1 = zawsze):").pack(anchor=tk.W, padx=20)
        keepalive_entry = tk.Entry(win, width=10)
        keepalive_entry.insert(0, str(self.ollama_keep_alive))
        keepalive_entry.pack(anchor=tk.W, padx=20, pady=4)

        def save():
            self.ollama_url = url_entry.get().strip()
            # Priorytet: ręczne pole > dropdown
            manual = manual_entry.get().strip()
            self.ollama_model = manual if manual else model_var.get()
            try:
                self.ollama_timeout = int(timeout_entry.get())
            except ValueError:
                pass
            try:
                self.ollama_num_ctx = int(numctx_entry.get())
            except ValueError:
                pass
            self.ollama_keep_alive = keepalive_entry.get().strip() or "10m"
            self.ollama_system_prompt = sysprompt_entry.get().strip()
            self.ollama_show_in_new_window = new_win_var.get()
            self.ollama_replace_selection  = replace_var.get()
            self.save_ollama_settings()
            try:
                self.update_status()
            except Exception:
                pass
            win.destroy()
            messagebox.showinfo("Ollama", "Ustawienia zapisane!")

        def test_conn():
            found = self.get_ollama_models()
            if found:
                messagebox.showinfo("Test połączenia",
                                    f"✅ Połączono!\nZnalezione modele:\n" + "\n".join(found))
            else:
                messagebox.showerror("Test połączenia",
                                     "❌ Nie można połączyć się z serwerem Ollama.")

        btn_f = tk.Frame(win)
        btn_f.pack(pady=16)
        tk.Button(btn_f, text="Testuj połączenie", command=test_conn,
                  bg="lightblue", width=16).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="Zapisz", command=save,
                  bg="lightgreen", width=10).pack(side=tk.LEFT, padx=5)

        win.deiconify()  # Pokaż gotowe, wyśrodkowane okno

    # ------------------------------------------------------------------ #
    #  Pomocnicze okno wyników AI                                          #
    # ------------------------------------------------------------------ #
    def _create_result_window(self):
        """Tworzy okno na wyniki AI ze scrollbarem."""
        win = tk.Toplevel(self.root)
        win.withdraw()  # Ukryj na czas budowania
        win.title(f"Wynik AI – {self.ollama_model}")
        self.center_window(win, 45, 50)  # Użycie center_window zamiast twardej geometrii
        try:
            win.iconbitmap("icon.ico")
        except Exception:
            pass

        frame = tk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
        sb  = tk.Scrollbar(frame, command=txt.yview)
        txt.config(yscrollcommand=sb.set)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_f = tk.Frame(win)
        btn_f.pack(fill=tk.X)

        def copy_all():
            self.root.clipboard_clear()
            self.root.clipboard_append(txt.get("1.0", tk.END).strip())
            messagebox.showinfo("AI", "Skopiowano do schowka!")

        tk.Button(btn_f, text="Kopiuj", command=copy_all,
                  bg="lightblue").pack(side=tk.LEFT, padx=5, pady=4)
        tk.Button(btn_f, text="Zamknij", command=win.destroy,
                  bg="lightcoral").pack(side=tk.RIGHT, padx=5, pady=4)

        win.deiconify()  # Pokaż okno po zbudowaniu
        return win, txt

    # kompatybilność wsteczna
    def show_ai_result_window(self, text):
        _, txt = self._create_result_window()
        txt.insert("1.0", text)
