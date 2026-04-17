import json
import urllib.request
import urllib.error
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

class OllamaMixin:
    def init_ollama(self):
        """Inicjalizacja ustawień Ollama"""
        self.ollama_settings_file = "ollama_settings.json"
        self.ollama_enabled = False
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "mistral"
        self.ollama_timeout = 60
        self.ollama_show_in_new_window = False
        self.ollama_replace_selection = True
        
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

    def call_ollama(self, prompt, text_content, callback):
        """Wywołanie API Ollama w osobnym wątku"""
        def worker():
            try:
                if text_content:
                    full_prompt = f"{prompt}\n\nOto tekst do przetworzenia:\n{text_content}"
                else:
                    full_prompt = prompt
                    
                data = json.dumps({
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": False
                }).encode("utf-8")
                
                req = urllib.request.Request(
                    f"{self.ollama_url}/api/generate",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                
                with urllib.request.urlopen(req, timeout=self.ollama_timeout) as response:
                    result = json.loads(response.read().decode())
                    response_text = result.get("response", "")
                    self.root.after(0, lambda: callback(response_text))
            except urllib.error.URLError as e:
                self.root.after(0, lambda: messagebox.showerror("Błąd Ollama", f"Nie można połączyć się z serwerem Ollama.\nUpewnij się, że Ollama działa na {self.ollama_url}\n\nSzczegóły: {e}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Błąd", f"Wystąpił błąd podczas komunikacji z AI: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def ollama_transform(self, action_name, custom_prompt=None):
        """Główna funkcja transformacji tekstu przez AI"""
        # Pobierz tekst (zaznaczenie lub całość)
        try:
            selection = self.text_area.tag_ranges(tk.SEL)
            text_to_process = ""
            target_range = None
            
            if selection:
                text_to_process = self.text_area.get(selection[0], selection[1])
                target_range = selection
            else:
                full_text = self.text_area.get("1.0", tk.END).strip()
                if full_text:
                    text_to_process = full_text
                    target_range = ("1.0", tk.END)
                else:
                    target_range = (tk.INSERT, tk.INSERT)
                
            if not text_to_process and action_name != "custom":
                messagebox.showwarning("AI", "Brak tekstu do przetworzenia!")
                return

            prompts = {
                "podsumuj": "Streść poniższy tekst w kilku konkretnych punktach:",
                "popraw": "Popraw błędy ortograficzne, interpunkcyjne i gramatyczne w poniższym tekście, zachowując jego styl. Zwróć tylko poprawiony tekst:",
                "rozwin": "Rozwiń poniższy tekst, dodając więcej szczegółów i kontekstu:",
                "parafrazuj": "Sparafrazuj poniższy tekst, zmieniając słownictwo, ale zachowując oryginalny sens:",
                "tlumacz": "Przetłumacz poniższy tekst na język polski (jeśli jest obcy) lub na angielski (jeśli jest polski):"
            }
            
            final_prompt = custom_prompt if custom_prompt else prompts.get(action_name, "Przetwórz poniższy tekst:")

            # Pokaż status "Generowanie..."
            old_status = self.status_bar.cget("text")
            self.status_bar.config(text="🤖 AI generuje odpowiedź... Proszę czekać.", fg="blue")

            def handle_response(response):
                self.status_bar.config(text=old_status, fg="black")
                
                if self.ollama_show_in_new_window:
                    self.show_ai_result_window(response)
                elif self.ollama_replace_selection and text_to_process:
                    if selection:
                        self.text_area.delete(selection[0], selection[1])
                        self.text_area.insert(selection[0], response)
                    else:
                        self.text_area.delete("1.0", tk.END)
                        self.text_area.insert("1.0", response)
                else:
                    # Wstaw po zaznaczeniu/tekście lub w miejscu kursora
                    insert_pos = target_range[1] if target_range and text_to_process else tk.INSERT
                    separator = f"\n\n--- AI ({self.ollama_model}) ---\n" if text_to_process else ""
                    self.text_area.insert(insert_pos, f"{separator}{response}\n")

            self.call_ollama(final_prompt, text_to_process, handle_response)
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd AI: {e}")

    def show_ai_result_window(self, text):
        """Pokazuje wynik AI w nowym oknie"""
        res_window = tk.Toplevel(self.root)
        res_window.title(f"Wynik AI - {self.ollama_model}")
        res_window.geometry("600x400")
        
        try:
            res_window.iconbitmap("icon.ico")
        except:
            pass
        
        txt = tk.Text(res_window, wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", text)
        
        btn_frame = tk.Frame(res_window)
        btn_frame.pack(fill=tk.X)
        
        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("AI", "Skopiowano do schowka")
            
        tk.Button(btn_frame, text="Kopiuj wynik", command=copy).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Zamknij", command=res_window.destroy).pack(side=tk.RIGHT, padx=5, pady=5)

    def ollama_config_window(self):
        """Okno konfiguracji Ollama"""
        win = tk.Toplevel(self.root)
        win.title("Ustawienia Ollama")
        win.geometry("400x450")
        win.transient(self.root)
        self.center_window(win, 30, 40)
        
        try:
            win.iconbitmap("icon.ico")
        except:
            pass
        
        tk.Label(win, text="KONFIGURACJA OLLAMA", font=("Arial", 12, "bold")).pack(pady=10)
        
        tk.Label(win, text="URL serwera (domyślnie localhost:11434):").pack(anchor=tk.W, padx=20)
        url_entry = tk.Entry(win, width=40)
        url_entry.insert(0, self.ollama_url)
        url_entry.pack(padx=20, pady=5)
        
        tk.Label(win, text="Model:").pack(anchor=tk.W, padx=20)
        
        models = self.get_ollama_models()
        model_var = tk.StringVar(value=self.ollama_model)
        
        if models:
            model_dropdown = tk.OptionMenu(win, model_var, *models)
        else:
            model_dropdown = tk.OptionMenu(win, model_var, self.ollama_model)
            tk.Label(win, text="(Nie połączono z serwerem, wpisz model poniżej)", fg="red", font=("Arial", 8)).pack(padx=20)
            
        model_dropdown.pack(padx=20, pady=5, fill=tk.X)
        
        tk.Label(win, text="Ręczny wybór modelu (jeśli brak na liście):").pack(anchor=tk.W, padx=20)
        manual_model_entry = tk.Entry(win, width=40)
        manual_model_entry.insert(0, self.ollama_model)
        manual_model_entry.pack(padx=20, pady=5)

        # Opcje
        new_win_var = tk.BooleanVar(value=self.ollama_show_in_new_window)
        tk.Checkbutton(win, text="Pokaż odpowiedź w nowym oknie", variable=new_win_var).pack(anchor=tk.W, padx=20)
        
        replace_var = tk.BooleanVar(value=self.ollama_replace_selection)
        tk.Checkbutton(win, text="Zastąp zaznaczenie/tekst", variable=replace_var).pack(anchor=tk.W, padx=20)
        
        tk.Label(win, text="Timeout (sekundy):").pack(anchor=tk.W, padx=20)
        timeout_entry = tk.Entry(win, width=10)
        timeout_entry.insert(0, str(self.ollama_timeout))
        timeout_entry.pack(anchor=tk.W, padx=20, pady=5)

        def save():
            self.ollama_url = url_entry.get()
            self.ollama_model = manual_model_entry.get() if manual_model_entry.get() != self.ollama_model else model_var.get()
            try:
                self.ollama_timeout = int(timeout_entry.get())
            except:
                pass
            self.ollama_show_in_new_window = new_win_var.get()
            self.ollama_replace_selection = replace_var.get()
            self.save_ollama_settings()
            self.update_status()
            win.destroy()
            messagebox.showinfo("Ollama", "Ustawienia zapisane!")

        def test_conn():
            models = self.get_ollama_models()
            if models:
                messagebox.showinfo("Test", f"Połączono! Znaleziono modele: {', '.join(models)}")
            else:
                messagebox.showerror("Test", "Nie można połączyć się z serwerem Ollama.")

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Testuj", command=test_conn, bg="lightblue", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Zapisz", command=save, bg="lightgreen", width=10).pack(side=tk.LEFT, padx=5)

    def custom_askstring(self, title, prompt, initialvalue=""):
        """Niestandardowe okno dialogowe z ikoną icon.ico"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        # Rozmiar okna dostosowany
        self.center_window(dialog, 30, 20)
        
        try:
            dialog.iconbitmap("icon.ico")
        except:
            pass
            
        tk.Label(dialog, text=prompt, padx=10, pady=10).pack()
        entry = tk.Entry(dialog, width=40)
        entry.insert(0, initialvalue)
        entry.pack(padx=10, pady=5)
        entry.focus_set()
        
        result = [None]
        
        def on_ok(event=None):
            result[0] = entry.get()
            dialog.destroy()
            
        def on_cancel(event=None):
            dialog.destroy()
            
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Anuluj", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)
        
        entry.bind("<Return>", on_ok)
        entry.bind("<Escape>", on_cancel)
        
        self.root.wait_window(dialog)
        return result[0]

    def ollama_transform_custom(self):
        """Transformacja z własnym promptem"""
        prompt = self.custom_askstring("AI Custom Prompt", "Wpisz polecenie dla AI (np. 'Napisz kontynuację', 'Zrób tabelę'):")
        if prompt:
            self.ollama_transform("custom", custom_prompt=prompt)

    def ollama_translate(self):
        """Tłumaczenie na wybrany przez użytkownika język"""
        lang = self.custom_askstring("Tłumacz AI", "Na jaki język przetłumaczyć tekst?", initialvalue="angielski")
        if lang:
            prompt = f"Przetłumacz poniższy tekst na język {lang}. Zwróć wyłącznie przetłumaczony tekst, bez żadnych dodatkowych komentarzy:"
            self.ollama_transform("custom", custom_prompt=prompt)


    def ollama_selection_as_prompt(self):
        """Używa zaznaczonego tekstu jako prompt i wkleja wynik pod spodem."""
        try:
            selection = self.text_area.tag_ranges(tk.SEL)
            if not selection:
                messagebox.showwarning("AI", "Zaznacz tekst, który ma być użyty jako prompt!")
                return
            
            prompt_text = self.text_area.get(selection[0], selection[1])
            target_end = selection[1]
            
            old_status = self.status_bar.cget("text")
            self.status_bar.config(text="🤖 AI generuje odpowiedź na prompt... Proszę czekać.", fg="blue")

            def handle_response(response):
                self.status_bar.config(text=old_status, fg="black")
                self.text_area.insert(target_end, f"\n\n{response}\n")

            # Pusty kontekst text_content="": model reaguje tylko na prompt
            self.call_ollama(prompt_text, "", handle_response)
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd AI: {e}")

