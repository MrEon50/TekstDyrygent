import re
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog
import tkinter.font as tkFont
import time
import datetime
import pickle
import json
import os
import sys
from collections import Counter

class ToolsFeaturesMixin:
    # bold_all_text
    def bold_all_text(self):
        self.text_area.tag_add("all_bold", "1.0", tk.END)
        self.text_area.tag_config("all_bold", font=(self.font_family, self.font_size, "bold"))

    # check_limits
    def check_limits(self, minutes_used, current_line, size_kb):
        """Sprawdza przekroczenia limitów i pokazuje powiadomienia"""
        # Sprawdź czy powiadomienia są włączone
        if not self.notifications_enabled:
            return

        # Sprawdź czas
        if minutes_used >= self.time_limit_minutes and not self.time_warning_shown:
            self.time_warning_shown = True
            messagebox.showwarning("Przekroczenie czasu",
                                 f"⏰ Uwaga!\n\n"
                                 f"Korzystasz z notatnika już {minutes_used} minut.\n"
                                 f"Ustawiony limit: {self.time_limit_minutes} minut.\n\n"
                                 f"Może czas na przerwę? 😊")

        # Sprawdź liczbę linii
        if current_line >= self.line_limit and not self.line_warning_shown:
            self.line_warning_shown = True
            messagebox.showwarning("Przekroczenie linii",
                                 f"📝 Uwaga!\n\n"
                                 f"Twój tekst ma już {current_line} linii.\n"
                                 f"Ustawiony limit: {self.line_limit} linii.\n\n"
                                 f"Może warto podzielić tekst na części?")

        # Sprawdź rozmiar pliku
        if size_kb >= self.size_limit_kb and not self.size_warning_shown:
            self.size_warning_shown = True
            messagebox.showwarning("Przekroczenie rozmiaru",
                                 f"💾 Uwaga!\n\n"
                                 f"Rozmiar pliku: {size_kb} KB.\n"
                                 f"Ustawiony limit: {self.size_limit_kb} KB.\n\n"
                                 f"Duży plik może działać wolniej.")

    # clear_all_formatting
    def clear_all_formatting(self):
        """Usuwa wszystkie formatowania i przywraca ustawienia domyślne użytkownika"""
        # Lista wszystkich możliwych tagów formatowania
        format_tags = ['bold', 'italic', 'yellow', 'red', 'blue', 'green', 'purple', 'all_bold', 'reading_line']

        # Usuń podstawowe tagi
        for tag in format_tags:
            self.text_area.tag_remove(tag, "1.0", tk.END)

        # Usuń tagi linii (line_bg_, text_color_, bold_)
        for tag_name in self.text_area.tag_names():
            if any(tag_name.startswith(prefix) for prefix in ['line_bg_', 'text_color_', 'bold_']):
                self.text_area.tag_remove(tag_name, "1.0", tk.END)

        # Przywróć ustawienia domyślne użytkownika
        self.text_area.config(
            font=(self.font_family, self.font_size),
            fg=self.text_color,
            bg=self.bg_color,
            insertbackground=self.cursor_color
        )

        # Wyłącz linijkę jeśli była aktywna
        if self.reading_line_active:
            self.reading_line_active = False
            self.reading_line_button.config(bg="yellow", text="Linijka")
            # Usuń skróty klawiszowe
            try:
                self.root.unbind('<Up>')
                self.root.unbind('<Down>')
                self.root.unbind('<Shift-Up>')
                self.root.unbind('<Shift-Down>')
                self.root.unbind('<Home>')
                self.root.unbind('<End>')
            except:
                pass

    # clear_selected_lines
    def clear_selected_lines(self):
        """Czyści formatowanie z wybranych linii"""
        window_id = "clear_lines"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        clear_window = tk.Toplevel(self.root)
        clear_window.title("Czyść formatowanie")
        clear_window.transient(self.root)
        self.center_window(clear_window, 40, 30)

        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        # Usuń z listy po zamknięciu
        def on_close():
            self.open_windows.discard(window_id)
            clear_window.destroy()

        clear_window.protocol("WM_DELETE_WINDOW", on_close)

        # Ustaw ikonę
        try:
            clear_window.iconbitmap("icon.ico")
        except:
            pass

        tk.Label(clear_window, text="CZYSZCZENIE FORMATOWANIA",
                font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(clear_window, text="Wybierz linie do wyczyszczenia:",
                font=("Arial", 10)).pack(pady=5)

        # Pole wprowadzania linii
        entry_frame = tk.Frame(clear_window)
        entry_frame.pack(pady=10)

        tk.Label(entry_frame, text="Numery linii:").pack(side=tk.LEFT)
        lines_var = tk.StringVar(value="1,3,5")
        lines_entry = tk.Entry(entry_frame, textvariable=lines_var, width=20)
        lines_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(clear_window, text="Przykład: 1,3,4,5,8,9,12 lub zostaw puste dla wszystkich",
                font=("Arial", 9), fg="gray").pack(pady=5)

        def apply_clear():
            try:
                lines_input = lines_var.get().strip()

                if not lines_input:
                    # Wyczyść wszystkie formatowania
                    self.clear_all_formatting()
                    on_close()
                    messagebox.showinfo("Sukces", "Wyczyszczono formatowanie z całego tekstu!")
                else:
                    # Wyczyść wybrane linie
                    line_numbers = [int(num.strip()) for num in lines_input.split(',')]

                    for line_num in line_numbers:
                        # Usuń formatowanie z konkretnej linii
                        start_pos = f"{line_num}.0"
                        end_pos = f"{line_num}.end"

                        # Usuń wszystkie tagi formatowania z tej linii
                        for tag_name in self.text_area.tag_names():
                            if tag_name not in ['sel', 'current']:
                                self.text_area.tag_remove(tag_name, start_pos, end_pos)

                    on_close()
                    messagebox.showinfo("Sukces", f"Wyczyszczono formatowanie z linii: {lines_input}")

            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format numerów linii!")
            except Exception as e:
                messagebox.showerror("Błąd", f"Błąd czyszczenia: {e}")

        # Przyciski
        button_frame = tk.Frame(clear_window)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Wyczyść", command=apply_clear,
                 bg="lightgreen", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Anuluj", command=on_close,
                 bg="lightcoral", width=12).pack(side=tk.LEFT, padx=5)

        lines_entry.focus_set()

    # delete_current_line
    def delete_current_line(self):
        """Usuwa aktualną linię, jeśli kursor znajduje się na niej"""
        try:
            # Pobieramy pozycję kursora
            cursor_pos = self.text_area.index(tk.INSERT)
            
            # Rozdzielamy pozycję na wiersz i kolumnę
            line_num = int(cursor_pos.split('.')[0])
            
            # Pobieramy całą linię
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            
            # Sprawdzamy, czy kursor jest w tej linii (nie na końcu)
            current_line_content = self.text_area.get(line_start, line_end)
            
            if current_line_content or cursor_pos == line_start:
                # Usuwamy całą linię
                self.text_area.delete(line_start, f"{line_num + 1}.0")
                
                # Dodajemy do historii undo
                self.text_area.edit_separator()
                
        except Exception as e:
            print(f"Błąd podczas usuwania linii: {e}")

    # empty_lines_manager
    def empty_lines_manager(self):
        """Zarządzanie pustymi liniami"""
        window_id = "empty_lines"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        empty_window = tk.Toplevel(self.root)
        empty_window.title("Puste linie")
        empty_window.transient(self.root)
        self.center_window(empty_window, 40, 35)

        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        # Usuń z listy po zamknięciu
        def on_close():
            self.open_windows.discard(window_id)
            empty_window.destroy()

        empty_window.protocol("WM_DELETE_WINDOW", on_close)

        # Ustaw ikonę
        try:
            empty_window.iconbitmap("icon.ico")
        except:
            pass

        # Znajdź puste linie
        text = self.text_area.get('1.0', tk.END)
        lines = text.split('\n')
        empty_lines = []

        for i, line in enumerate(lines):
            if not line.strip():  # Pusta linia lub tylko białe znaki
                empty_lines.append(i + 1)  # Numeracja od 1

        tk.Label(empty_window, text="ZARZĄDZANIE PUSTYMI LINIAMI",
                font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(empty_window, text=f"Znaleziono {len(empty_lines)} pustych linii: {', '.join(map(str, empty_lines[:10]))}" +
                ("..." if len(empty_lines) > 10 else ""),
                font=("Arial", 10)).pack(pady=5)

        if not empty_lines:
            tk.Label(empty_window, text="Brak pustych linii w tekście!",
                    font=("Arial", 10), fg="red").pack(pady=10)
            tk.Button(empty_window, text="Zamknij", command=empty_window.destroy,
                     bg="lightcoral", width=12).pack(pady=10)
            return

        # Pole wprowadzania tekstu do wstawienia
        tk.Label(empty_window, text="Tekst do wstawienia w puste linie (max 100 znaków):",
                font=("Arial", 10)).pack(pady=(20,5))

        text_var = tk.StringVar(value="---")
        text_entry = tk.Entry(empty_window, textvariable=text_var, width=50)
        text_entry.pack(pady=5)

        # Licznik znaków
        char_count_label = tk.Label(empty_window, text="Znaków: 3/100", font=("Arial", 9), fg="gray")
        char_count_label.pack()

        def update_char_count(*args):
            current_text = text_var.get()
            count = len(current_text)
            char_count_label.config(text=f"Znaków: {count}/100")
            if count > 100:
                char_count_label.config(fg="red")
                text_var.set(current_text[:100])  # Obetnij do 100 znaków
            else:
                char_count_label.config(fg="gray")

        text_var.trace_add('write', update_char_count)

        def fill_empty_lines():
            try:
                fill_text = text_var.get()
                if len(fill_text) > 100:
                    messagebox.showerror("Błąd", "Tekst nie może być dłuższy niż 100 znaków!")
                    return

                # Pobierz aktualny tekst
                current_text = self.text_area.get('1.0', tk.END)
                lines = current_text.split('\n')

                # Wypełnij puste linie
                filled_count = 0
                for i, line in enumerate(lines):
                    if not line.strip():  # Pusta linia
                        lines[i] = fill_text
                        filled_count += 1

                # Zastąp tekst
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert('1.0', '\n'.join(lines))

                on_close()
                messagebox.showinfo("Sukces", f"Wypełniono {filled_count} pustych linii tekstem: '{fill_text}'")

            except Exception as e:
                messagebox.showerror("Błąd", f"Błąd wypełniania: {e}")

        # Przyciski
        button_frame = tk.Frame(empty_window)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Wypełnij", command=fill_empty_lines,
                 bg="lightgreen", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Anuluj", command=on_close,
                 bg="lightcoral", width=12).pack(side=tk.LEFT, padx=5)

        text_entry.focus_set()

    # end_typing_session
    def end_typing_session(self, end_time):
        """Kończy sesję pisania i oblicza prędkość"""
        if self.typing_session_start:
            duration_minutes = (end_time - self.typing_session_start) / 60
            chars_per_minute = self.typing_session_chars / duration_minutes

            # Dodaj do historii
            self.typing_speeds.append(chars_per_minute)

            # Zachowaj tylko ostatnie 10 pomiarów
            if len(self.typing_speeds) > 10:
                self.typing_speeds = self.typing_speeds[-10:]

            # Reset sesji
            self.typing_session_start = None
            self.typing_session_chars = 0
            self.current_typing_text = ""

    # format_selection
    def format_selection(self, format_type):
        try:
            selection = self.text_area.tag_ranges(tk.SEL)
            if selection:
                start, end = selection[0], selection[1]
                
                if format_type == 'bold':
                    self.text_area.tag_add("bold", start, end)
                    self.text_area.tag_config("bold", font=(self.font_family, self.font_size, "bold"))
                elif format_type == 'italic':
                    self.text_area.tag_add("italic", start, end)
                    self.text_area.tag_config("italic", font=(self.font_family, self.font_size, "italic"))
                elif format_type in ['yellow', 'red', 'blue', 'green', 'purple']:
                    self.text_area.tag_add(format_type, start, end)
                    self.text_area.tag_config(format_type, background=format_type)
                elif format_type == 'clear':
                    # Usuwa wszystkie formatowania z zaznaczenia
                    for tag in ['bold', 'italic', 'yellow', 'red', 'blue', 'green', 'purple']:
                        self.text_area.tag_remove(tag, start, end)
            else:
                # Jeśli nie ma zaznaczenia i format_type to 'clear', wyczyść cały tekst
                if format_type == 'clear':
                    self.clear_all_formatting()
        except tk.TclError:
            # Jeśli błąd i format_type to 'clear', wyczyść cały tekst
            if format_type == 'clear':
                self.clear_all_formatting()

    # highlight_duplicates
    def highlight_duplicates(self):
        if not self.show_duplicates:
            return

        text = self.text_area.get('1.0', tk.END)
        words = re.findall(r'\b\w+\b', text.lower())

        # Filtruj słowa według minimalnej długości
        filtered_words = [w for w in words if len(w) >= self.min_duplicate_length]

        # Filtruj według pierwszej litery (jeśli ustawiona)
        if self.duplicate_first_letter:
            filtered_words = [w for w in filtered_words if w.startswith(self.duplicate_first_letter)]

        word_counts = Counter(filtered_words)
        duplicates = {word for word, count in word_counts.items() if count > 1}

        self.text_area.tag_remove("duplicate", "1.0", tk.END)

        for word in duplicates:
            start = '1.0'
            while True:
                start = self.text_area.search(word, start, tk.END, nocase=True)
                if not start:
                    break
                end = f"{start}+{len(word)}c"
                self.text_area.tag_add("duplicate", start, end)
                start = end

        self.text_area.tag_config("duplicate", background='lightgreen')

    # jump_to_start
    def jump_to_start(self):
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)

    # jump_word_backward
    def jump_word_backward(self):
        """Skacze między słowami do tyłu w tej samej linii"""
        current_pos = self.text_area.index(tk.INSERT)
        current_line = current_pos.split('.')[0]
        current_col = int(current_pos.split('.')[1])
        line_start = f"{current_line}.0"

        # Pobierz tekst od początku linii do kursora
        text_from_start = self.text_area.get(line_start, current_pos)

        # Jeśli jesteśmy na początku linii, nie rób nic
        if current_col == 0:
            return

        # Znajdź wszystkie słowa w linii
        words = list(re.finditer(r'\S+', text_from_start))

        if words:
            # Sprawdź czy jesteśmy w środku słowa czy na spacji
            current_word = None
            for word in words:
                if word.start() <= current_col - 1 < word.end():
                    current_word = word
                    break

            if current_word and current_col > current_word.start():
                # Jesteśmy w środku słowa - idź na jego początek
                new_pos = self.text_area.index(f"{line_start}+{current_word.start()}c")
            else:
                # Jesteśmy na spacji lub na początku słowa - idź na początek poprzedniego słowa
                prev_words = [w for w in words if w.end() <= current_col]
                if prev_words:
                    prev_word = prev_words[-1]
                    new_pos = self.text_area.index(f"{line_start}+{prev_word.start()}c")
                else:
                    # Przejdź na początek linii
                    new_pos = line_start

            self.text_area.mark_set(tk.INSERT, new_pos)
            self.text_area.see(tk.INSERT)

    # jump_word_forward
    def jump_word_forward(self):
        """Skacze między słowami do przodu w tej samej linii"""
        current_pos = self.text_area.index(tk.INSERT)
        current_line = current_pos.split('.')[0]
        line_end = f"{current_line}.end"
        
        # Pobierz tekst od kursora do końca linii
        text_to_end = self.text_area.get(current_pos, line_end)
        
        # Znajdź następne słowo (pomijając spacje na początku)
        match = re.search(r'\S+', text_to_end)
        if match:
            # Przesuń kursor na koniec znalezionego słowa
            word_end_offset = match.end()
            new_pos = self.text_area.index(f"{current_pos}+{word_end_offset}c")
            self.text_area.mark_set(tk.INSERT, new_pos)
            self.text_area.see(tk.INSERT)

    # on_click
    def on_click(self, event):
        # Anuluj zaznaczenia przy normalnym kliknięciu (bez Ctrl+Shift)
        if not (event.state & 0x4 and event.state & 0x1):  # Nie Ctrl+Shift
            if self.column_selection_active:
                self.column_selection_active = False
                self.clear_column_selection()
            self.clear_multi_selection()
            self.clear_right_click_selection()
        self.update_status()

    # on_double_click
    def on_double_click(self, event):
        # Sprawdź czy Ctrl jest wciśnięty
        if event.state & 0x4:  # Ctrl key
            self.find_duplicates_of_word(event)
        else:
            # Zaznacza słowo przy podwójnym kliknięciu
            current_pos = self.text_area.index(tk.INSERT)
            word_start = self.text_area.search(r'\b', current_pos, "1.0", backwards=True, regexp=True)
            word_end = self.text_area.search(r'\b', current_pos, tk.END, regexp=True)

            if word_start and word_end:
                self.text_area.tag_add(tk.SEL, word_start, word_end)

    # on_key_press
    def on_key_press(self, event):
        """Obsługuje naciśnięcia klawiszy dla pomiaru prędkości pisania"""
        current_time = time.time()

        # Sprawdź czy to znak do pisania (nie strzałki, ctrl itp.)
        if len(event.char) == 1 and event.char.isprintable():
            time_since_last = current_time - self.last_key_time if self.last_key_time > 0 else 0

            # Sprawdź warunki rozpoczęcia sesji
            if self.typing_session_start is None:
                # Rozpocznij sesję jeśli przerwa była ≤ 1.5s lub to pierwszy znak
                if time_since_last <= 1.5 or self.last_key_time == 0:
                    self.typing_session_start = current_time
                    self.typing_session_chars = 1
                    self.current_typing_text = event.char
                else:
                    # Za długa przerwa, nie rozpoczynaj sesji
                    pass
            else:
                # Kontynuuj sesję
                if time_since_last <= 2.0:  # Przerwa ≤ 2s
                    self.typing_session_chars += 1
                    self.current_typing_text += event.char

                    # Sprawdź czy zakończyć sesję (min 25 znaków, min 5 sekund)
                    session_duration = current_time - self.typing_session_start
                    if (self.typing_session_chars >= 25 and session_duration >= 5 and
                        session_duration >= 15):  # Min 15 sekund sesji
                        # Zakończ sesję i oblicz prędkość
                        self.end_typing_session(current_time)
                else:
                    # Za długa przerwa, zakończ sesję jeśli spełnia warunki
                    session_duration = current_time - self.typing_session_start
                    if self.typing_session_chars >= 25 and session_duration >= 5:
                        self.end_typing_session(current_time)
                    else:
                        # Sesja za krótka, anuluj
                        self.typing_session_start = None
                        self.typing_session_chars = 0
                        self.current_typing_text = ""

            self.last_key_time = current_time

    # on_key_press_combined
    def on_key_press_combined(self, event):
        """Kombinowana obsługa klawiszy - pomiar prędkości i zaznaczenie kolumnowe"""
        # Najpierw sprawdź zaznaczenie kolumnowe
        if self.column_selection_tags:
            result = self.handle_column_type(event)
            if result == "break":
                return result

        # Potem obsłuż pomiar prędkości pisania
        return self.on_key_press(event)

    # open_table_of_contents
    def open_table_of_contents(self):
        """Otwiera okno spisu treści"""
        window_id = "table_of_contents"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        toc_window = tk.Toplevel(self.root)
        toc_window.title("Spis treści")

        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        # Usuń z listy po zamknięciu
        def on_close():
            self.open_windows.discard(window_id)
            toc_window.destroy()

        toc_window.protocol("WM_DELETE_WINDOW", on_close)

        # Oblicz rozmiary względem głównego okna
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        # 40% szerokości i 60% wysokości głównego okna
        toc_width = int(main_width * 0.4)
        toc_height = int(main_height * 0.6)

        # Pozycja wyśrodkowana względem głównego okna
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()

        toc_x = main_x + (main_width - toc_width) // 2
        toc_y = main_y + (main_height - toc_height) // 2

        toc_window.geometry(f"{toc_width}x{toc_height}+{toc_x}+{toc_y}")

        # Ustaw ikonę
        try:
            toc_window.iconbitmap("icon.ico")
        except:
            pass

        # Główny frame
        main_frame = tk.Frame(toc_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)



        # Frame dla spisu treści z przewijaniem
        toc_frame = tk.Frame(main_frame)
        toc_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar i Canvas dla przewijania
        canvas = tk.Canvas(toc_frame, bg="white")
        scrollbar = tk.Scrollbar(toc_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Lista elementów spisu treści
        self.toc_items_frame = scrollable_frame
        self.refresh_toc_display()

        # Frame dla dodawania nowych elementów
        add_frame = tk.Frame(main_frame)
        add_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(add_frame, text="Dodaj element:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        # Entry dla tytułu (max 95 znaków)
        title_frame = tk.Frame(add_frame)
        title_frame.pack(fill=tk.X, pady=2)
        tk.Label(title_frame, text="Tytuł (max 95 znaków):").pack(side=tk.LEFT)
        title_entry = tk.Entry(title_frame, font=("Arial", 12))
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Frame dla numeru linii i koloru
        controls_frame = tk.Frame(add_frame)
        controls_frame.pack(fill=tk.X, pady=2)

        tk.Label(controls_frame, text="Linia:").pack(side=tk.LEFT)
        line_entry = tk.Entry(controls_frame, width=8)
        line_entry.pack(side=tk.LEFT, padx=(5, 10))

        tk.Label(controls_frame, text="Kolor:").pack(side=tk.LEFT)
        color_var = tk.StringVar(value="yellow")

        tk.Radiobutton(controls_frame, text="Spis treści", variable=color_var, value="yellow",
                      bg="lightyellow").pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(controls_frame, text="Zakładki", variable=color_var, value="green",
                      bg="lightgreen").pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(controls_frame, text="Informacje", variable=color_var, value="blue",
                      bg="lightblue").pack(side=tk.LEFT, padx=2)

        # Przyciski akcji
        buttons_frame = tk.Frame(add_frame)
        buttons_frame.pack(fill=tk.X, pady=(5, 0))

        def add_toc_item():
            title = title_entry.get().strip()
            if len(title) > 95:
                title = title[:95]

            try:
                line_num = int(line_entry.get())
                color = color_var.get()

                if title and line_num > 0:
                    self.table_of_contents.append({
                        'title': title,
                        'line': line_num,
                        'color': color
                    })
                    self.refresh_toc_display()
                    title_entry.delete(0, tk.END)
                    line_entry.delete(0, tk.END)
                else:
                    messagebox.showwarning("Błąd", "Podaj tytuł i prawidłowy numer linii")
            except ValueError:
                messagebox.showerror("Błąd", "Numer linii musi być liczbą")

        def save_toc():
            if self.current_file:
                # Zapisz spis treści dla aktualnego pliku
                toc_file = self.current_file.replace('.txt', '_toc.json')
                try:
                    with open(toc_file, 'w', encoding='utf-8') as f:
                        json.dump(self.table_of_contents, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("Sukces", f"Spis treści zapisany do:\n{toc_file}")
                except Exception as e:
                    messagebox.showerror("Błąd", f"Nie można zapisać spisu treści:\n{e}")
            else:
                messagebox.showwarning("Błąd", "Najpierw zapisz plik tekstowy")

        def load_toc():
            if self.current_file:
                toc_file = self.current_file.replace('.txt', '_toc.json')
                try:
                    with open(toc_file, 'r', encoding='utf-8') as f:
                        self.table_of_contents = json.load(f)
                    self.refresh_toc_display()
                    messagebox.showinfo("Sukces", "Spis treści wczytany")
                except FileNotFoundError:
                    messagebox.showinfo("Info", "Brak zapisanego spisu treści dla tego pliku")
                except Exception as e:
                    messagebox.showerror("Błąd", f"Nie można wczytać spisu treści:\n{e}")
            else:
                # Pozwól wybrać plik spisu treści
                from tkinter import filedialog
                toc_file = filedialog.askopenfilename(
                    title="Wybierz plik spisu treści",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
                if toc_file:
                    try:
                        with open(toc_file, 'r', encoding='utf-8') as f:
                            self.table_of_contents = json.load(f)
                        self.refresh_toc_display()
                        messagebox.showinfo("Sukces", "Spis treści wczytany")
                    except Exception as e:
                        messagebox.showerror("Błąd", f"Nie można wczytać spisu treści:\n{e}")

        tk.Button(buttons_frame, text="+ Dodaj", command=add_toc_item,
                 bg="lightgreen").pack(side=tk.LEFT, padx=2)
        tk.Button(buttons_frame, text="Zapisz", command=save_toc,
                 bg="lightyellow").pack(side=tk.LEFT, padx=2)
        tk.Button(buttons_frame, text="Wczytaj", command=load_toc,
                 bg="lightblue").pack(side=tk.LEFT, padx=2)

        # Automatycznie wczytaj spis treści jeśli istnieje
        if self.current_file:
            load_toc()

    # reading_line_down
    def reading_line_down(self, event):
        """Przesuń linijkę w dół"""
        if self.reading_line_active:
            text = self.text_area.get('1.0', tk.END)
            max_lines = len(text.split('\n'))
            if self.current_reading_line < max_lines:
                self.current_reading_line += 1
                self.update_reading_line()
        return "break"

    # reading_line_down_5
    def reading_line_down_5(self, event):
        """Przesuń linijkę o 5 w dół"""
        if self.reading_line_active:
            text = self.text_area.get('1.0', tk.END)
            max_lines = len(text.split('\n'))
            self.current_reading_line = min(max_lines, self.current_reading_line + 5)
            self.update_reading_line()
        return "break"

    # reading_line_end
    def reading_line_end(self, event):
        """Przesuń linijkę na koniec"""
        if self.reading_line_active:
            text = self.text_area.get('1.0', tk.END)
            max_lines = len(text.split('\n'))
            self.current_reading_line = max_lines
            self.update_reading_line()
        return "break"

    # reading_line_home
    def reading_line_home(self, event):
        """Przesuń linijkę na początek"""
        if self.reading_line_active:
            self.current_reading_line = 1
            self.update_reading_line()
        return "break"

    # reading_line_up
    def reading_line_up(self, event):
        """Przesuń linijkę w górę"""
        if self.reading_line_active and self.current_reading_line > 1:
            self.current_reading_line -= 1
            self.update_reading_line()
        return "break"  # Zatrzymaj domyślne zachowanie

    # reading_line_up_5
    def reading_line_up_5(self, event):
        """Przesuń linijkę o 5 w górę"""
        if self.reading_line_active:
            self.current_reading_line = max(1, self.current_reading_line - 5)
            self.update_reading_line()
        return "break"

    # redo_action
    def redo_action(self):
        """Ponów cofniętą akcję"""
        try:
            self.text_area.edit_redo()
        except tk.TclError:
            messagebox.showinfo("Ponów", "Brak akcji do ponowienia")

    # refresh_toc_display
    def refresh_toc_display(self):
        """Odświeża wyświetlanie spisu treści"""
        if not hasattr(self, 'toc_items_frame'):
            return

        # Wyczyść poprzednie elementy
        for widget in self.toc_items_frame.winfo_children():
            widget.destroy()

        # Dodaj elementy spisu treści
        for i, item in enumerate(self.table_of_contents):
            item_frame = tk.Frame(self.toc_items_frame)
            item_frame.pack(fill=tk.X, pady=2)

            # Tytuł elementu
            title_label = tk.Label(item_frame, text=item['title'],
                                  font=("Arial", 12), anchor=tk.W)
            title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Przycisk z numerem linii
            color_map = {
                'yellow': 'lightyellow',
                'green': 'lightgreen',
                'blue': 'lightblue'
            }

            def jump_to_line(line_num):
                def jump():
                    try:
                        # Sprawdź czy linia istnieje
                        total_lines = int(self.text_area.index(tk.END).split('.')[0]) - 1
                        if line_num > total_lines:
                            messagebox.showwarning("Błąd", f"Linia {line_num} nie istnieje.\nDokument ma tylko {total_lines} linii.")
                            return

                        # Przejdź do linii
                        self.text_area.mark_set(tk.INSERT, f"{line_num}.0")
                        self.text_area.see(f"{line_num}.0")

                        # Przewiń tak żeby linia była na górze (jeśli to możliwe)
                        if total_lines > 0:
                            fraction = max(0, min(1, (line_num - 1) / total_lines))
                            self.text_area.yview_moveto(fraction)

                        # Podświetl linię na chwilę
                        self.text_area.tag_remove("highlight_line", "1.0", tk.END)
                        line_start = f"{line_num}.0"
                        line_end = f"{line_num}.end"
                        self.text_area.tag_add("highlight_line", line_start, line_end)
                        self.text_area.tag_config("highlight_line", background="yellow")

                        # Usuń podświetlenie po 2 sekundach
                        self.root.after(2000, lambda: self.text_area.tag_remove("highlight_line", "1.0", tk.END))

                    except Exception as e:
                        messagebox.showerror("Błąd", f"Nie można przejść do linii {line_num}: {str(e)}")
                return jump

            line_button = tk.Button(item_frame, text=str(item['line']),
                                   bg=color_map.get(item['color'], 'lightgray'),
                                   command=jump_to_line(item['line']),
                                   width=6)
            line_button.pack(side=tk.RIGHT, padx=2)

            # Przycisk usuwania
            def delete_item(index):
                def delete():
                    if messagebox.askyesno("Usuń", f"Usunąć element '{self.table_of_contents[index]['title']}'?"):
                        del self.table_of_contents[index]
                        self.refresh_toc_display()
                return delete

            delete_button = tk.Button(item_frame, text="×", bg="lightcoral",
                                     command=delete_item(i), width=3)
            delete_button.pack(side=tk.RIGHT, padx=2)

    # save_report
    def save_report(self, report):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Pliki tekstowe", "*.txt")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(report)
            messagebox.showinfo("Info", "Raport zapisany")

    # search_text
    def search_text(self, event=None):
        search_term = self.search_entry.get()
        if not search_term:
            return
            
        # Usuń poprzednie zaznaczenia wyszukiwania
        self.text_area.tag_remove("search_highlight", "1.0", tk.END)
        
        text = self.text_area.get('1.0', tk.END)
        count = text.lower().count(search_term.lower())
        
        if count > 0:
            # Zaznacz wszystkie wystąpienia
            start = '1.0'
            while True:
                start = self.text_area.search(search_term, start, tk.END, nocase=True)
                if not start:
                    break
                end = f"{start}+{len(search_term)}c"
                self.text_area.tag_add("search_highlight", start, end)
                start = end
            
            # Konfiguracja podświetlenia wyszukiwania
            self.text_area.tag_config("search_highlight", background='yellow', foreground='red')
            
            # Przejdź do pierwszego wystąpienia
            first_pos = self.text_area.search(search_term, '1.0', tk.END, nocase=True)
            if first_pos:
                self.text_area.mark_set(tk.INSERT, first_pos)
                self.text_area.see(tk.INSERT)
                
        messagebox.showinfo("Wyszukiwanie", f"Znaleziono {count} wystąpień")

    # show_report
    def show_report(self):
        window_id = "report"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        text = self.text_area.get('1.0', tk.END)
        if not text.strip():
            messagebox.showwarning("Uwaga", "Brak tekstu do analizy!")
            return

        # Podstawowe statystyki
        lines = text.split('\n')
        # Usuń ostatnią pustą linię jeśli istnieje
        if lines and lines[-1] == '':
            lines = lines[:-1]

        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = Counter(words)

        # 1. Liczba wielkich liter
        uppercase_count = sum(1 for c in text if c.isupper())

        # 2. Liczba znaków # (hash)
        hash_count = text.count('#')

        # 3. Najwięcej duplikatów słów dłuższych niż 4 litery (tylko litery, max 32 znaki)
        def is_valid_duplicate_word(word):
            # Tylko litery, długość > 4, max 32 znaki
            return (len(word) > 4 and
                    len(word) <= 32 and
                    word.isalpha())

        long_words = [w for w in words if is_valid_duplicate_word(w)]
        long_word_counts = Counter(long_words)
        most_duplicated_long = long_word_counts.most_common(1)

        # 4. Wszystkie używane linie (niepuste)
        used_lines = len([line for line in lines if line.strip()])

        # 5. Wszystkich znaków w tekście (bez końcowego \n)
        total_chars = len(text) - 1 if text.endswith('\n') else len(text)

        # 6. Analiza liter z procentami - polskie litery
        polish_letters = 'AĄBCĆDEĘFGHIJKLŁMNŃOÓPQRSŚTUVWXYZŹŻ'
        special_chars = '#-,.'
        all_chars = polish_letters + special_chars

        char_counts = {}
        for char in all_chars:
            count_upper = text.upper().count(char)
            char_counts[char] = count_upper

        # Oblicz procenty
        total_letters = sum(char_counts.values())

        # Formatowanie statystyk liter w wierszach po 6 z równymi odstępami
        letter_stats = []
        chars_per_row = 6

        for i in range(0, len(all_chars), chars_per_row):
            row_chars = all_chars[i:i+chars_per_row]
            row_stats = []

            for char in row_chars:
                count = char_counts[char]
                percent = (count / total_letters * 100) if total_letters > 0 else 0
                # Zwięzły format bez niepotrzebnych zer
                formatted_cell = f"{char}({percent:.0f}%):{count}"
                row_stats.append(f"{formatted_cell:<12}")  # Zmniejszona szerokość do 12 znaków

            # Dopełnij wiersz do 6 elementów jeśli potrzeba
            while len(row_stats) < chars_per_row:
                row_stats.append(" " * 12)  # Puste komórki też 12 znaków

            # Połącz z mniejszymi separatorami
            letter_stats.append(" |".join(row_stats) + " |")

        # 7. Dodatkowe statystyki kluczowe
        # Średnia długość słowa
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0

        # Funkcja sprawdzająca czy słowo jest prawidłowe (tylko litery, max 32 znaki)
        def is_valid_longest_word(word):
            """Sprawdza czy słowo jest prawidłowe do statystyk najdłuższego słowa"""
            return (word.isalpha() and
                    len(word) <= 32 and
                    len(word) >= 2)  # Minimum 2 litery

        # Filtruj słowa dla najdłuższego słowa
        valid_longest_words = [w for w in words if is_valid_longest_word(w)]

        # Najdłuższe słowo (tylko litery, max 32 znaki)
        longest_word = max(valid_longest_words, key=len) if valid_longest_words else "brak"

        # Linia z największą liczbą znaków
        max_chars_line = 0
        max_chars_count = 0
        for i, line in enumerate(lines, 1):
            char_count = len(line)
            if char_count > max_chars_count:
                max_chars_count = char_count
                max_chars_line = i

        # Linia z największą liczbą spacji
        max_spaces_line = 0
        max_spaces_count = 0
        for i, line in enumerate(lines, 1):
            space_count = line.count(' ')
            if space_count > max_spaces_count:
                max_spaces_count = space_count
                max_spaces_line = i

        # Stosunek wielkich do małych liter
        lowercase_count = sum(1 for c in text if c.islower())
        upper_lower_ratio = (uppercase_count / lowercase_count) if lowercase_count > 0 else 0

        # Najczęstsza litera
        letter_only_counts = {k: v for k, v in char_counts.items() if k.isalpha() and v > 0}
        most_common_letter = max(letter_only_counts.items(), key=lambda x: x[1]) if letter_only_counts else ("brak", 0)

        # Gęstość tekstu (znaki na linię)
        text_density = total_chars / used_lines if used_lines > 0 else 0

        # Ciągi znaków dłuższe niż 32
        def count_long_sequences(text, max_length=32):
            """Liczy ciągi znaków (bez spacji) dłuższe niż max_length"""
            # Podziel tekst na słowa/ciągi (bez spacji)
            sequences = re.findall(r'\S+', text)  # \S+ = ciągi znaków bez białych znaków
            long_sequences = [seq for seq in sequences if len(seq) > max_length]
            return len(long_sequences)

        long_sequences_count = count_long_sequences(text)

        # Tworzenie raportu
        report = f"""RAPORT STATYSTYCZNY TEKSTDYRYGENT

PODSTAWOWE STATYSTYKI:
Liczba wszystkich wielkich liter w notatniku: {uppercase_count}
Ile jest wszystkich (#) w notatniku: {hash_count}
Najwięcej duplikatów jakie słowo więcej niż 4 litery może mieć: {most_duplicated_long[0][0] if most_duplicated_long else 'brak'} ({most_duplicated_long[0][1] if most_duplicated_long else 0} wystąpień)
Wszystkie używane linie: {used_lines}
Wszystkich znaków w tekście: {total_chars}

ANALIZA LITER Z PROCENTAMI:
{chr(10).join(letter_stats)}

DODATKOWE STATYSTYKI KLUCZOWE:
Średnia długość słowa: {avg_word_length:.1f} znaków
Najdłuższe słowo: "{longest_word}" ({len(longest_word)} znaków)
Długość znaków przekraczająca ponad 32: {long_sequences_count}
Linia z największą liczbą znaków: {max_chars_line} (znaków: {max_chars_count})
Linia z największą liczbą spacji: {max_spaces_line} (spacji: {max_spaces_count})
Stosunek wielkich do małych liter: {upper_lower_ratio:.2f}
Najczęstsza litera: {most_common_letter[0]} ({most_common_letter[1]} wystąpień)
Gęstość tekstu: {text_density:.1f} znaków na linię

POZOSTAŁE INFORMACJE:
Wszystkich linii (z pustymi): {len(lines)}
Liczba różnych słów: {len(word_counts)}
Liczba spacji: {text.count(' ')}
Najdłuższa linia: {max(range(len(lines)), key=lambda i: len(lines[i])) + 1 if lines else 0}
"""

        # Okno raportu - większe dla więcej danych
        report_window = tk.Toplevel(self.root)
        report_window.title("Raport Statystyczny - TekstDyrygent")
        report_window.transient(self.root)
        self.center_window(report_window, 70, 70)

        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        # Usuń z listy po zamknięciu
        def on_close():
            self.open_windows.discard(window_id)
            report_window.destroy()

        report_window.protocol("WM_DELETE_WINDOW", on_close)

        # Ustaw ikonę dla okna raportu
        try:
            report_window.iconbitmap("icon.ico")
        except:
            pass

        # Scrollbar dla długiego raportu
        frame = tk.Frame(report_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Courier New", 12))
        scrollbar = tk.Scrollbar(frame)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert('1.0', report)
        text_widget.config(state='disabled')

        # Przyciski
        button_frame = tk.Frame(report_window)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Zapisz raport",
                 command=lambda: self.save_report(report),
                 bg="#9FFCFD", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Zamknij",
                 command=on_close,
                 bg="#F09999", width=15).pack(side=tk.LEFT, padx=5)

    # toggle_duplicates
    def toggle_duplicates(self):
        """Przełącza duplikaty z opcją minimalnej długości słów i filtrem pierwszej litery"""
        if not self.show_duplicates:
            window_id = "duplicates"
            if window_id in self.open_windows:
                return  # Okno już otwarte

            # Okno dialogowe dla ustawień duplikatów
            duplicate_window = tk.Toplevel(self.root)
            duplicate_window.title("Ustawienia duplikatów")
            duplicate_window.transient(self.root)
            duplicate_window.grab_set()
            self.center_window(duplicate_window, 35, 25)

            # Dodaj do listy otwartych okien
            self.open_windows.add(window_id)

            # Usuń z listy po zamknięciu
            def on_close():
                self.open_windows.discard(window_id)
                duplicate_window.destroy()

            duplicate_window.protocol("WM_DELETE_WINDOW", on_close)
            # Ustaw ikonę
            try:
                duplicate_window.iconbitmap("icon.ico")
            except:
                pass

            # Minimalna długość słów
            tk.Label(duplicate_window, text="Powyżej ilu znaków pokazywać duplikaty?").grid(row=0, column=0, padx=10, pady=5, sticky="w")
            min_length_var = tk.IntVar(value=3)
            length_entry = tk.Entry(duplicate_window, textvariable=min_length_var, width=10)
            length_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

            # Filtr pierwszej litery
            tk.Label(duplicate_window, text="Pierwsza litera (opcjonalnie):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
            first_letter_var = tk.StringVar(value="")
            letter_entry = tk.Entry(duplicate_window, textvariable=first_letter_var, width=10)
            letter_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

            # Przykład
            example_label = tk.Label(duplicate_window, text="Przykład: 'm' - tylko duplikaty zaczynające się od 'm'",
                                   fg="gray", font=("Arial", 9))
            example_label.grid(row=2, column=0, columnspan=2, pady=5)

            def apply_duplicates():
                self.min_duplicate_length = min_length_var.get()
                self.duplicate_first_letter = first_letter_var.get().lower().strip()

                # Walidacja pierwszej litery
                if self.duplicate_first_letter and not self.duplicate_first_letter.isalpha():
                    messagebox.showerror("Błąd", "Pierwsza litera musi być literą alfabetu!")
                    return

                self.show_duplicates = True
                self.duplicate_button.config(bg='lightgreen')
                self.highlight_duplicates()
                on_close()

            def cancel_duplicates():
                on_close()

            button_frame = tk.Frame(duplicate_window)
            button_frame.grid(row=3, column=0, columnspan=2, pady=15)

            tk.Button(button_frame, text="OK", command=apply_duplicates, bg="lightgreen").pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Anuluj", command=cancel_duplicates, bg="lightcoral").pack(side=tk.LEFT, padx=5)

            length_entry.focus_set()
            length_entry.bind('<Return>', lambda e: apply_duplicates())
            letter_entry.bind('<Return>', lambda e: apply_duplicates())

        else:
            # Wyłącz duplikaty
            self.show_duplicates = False
            self.duplicate_button.config(bg='SystemButtonFace')
            self.text_area.tag_remove("duplicate", "1.0", tk.END)

    # toggle_line_numbers
    def toggle_line_numbers(self):
        """Numerowanie linii tekstu - uproszczona wersja z lepszą obsługą błędów"""
        # Sprawdź czy jest jakiś tekst
        text = self.text_area.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("Uwaga", "Brak tekstu do numerowania!")
            return

        # Okno dialogowe dla ustawień numeracji
        window_id = "line_numbering"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        numbering_window = tk.Toplevel(self.root)
        numbering_window.title("Numeracja linii")
        numbering_window.transient(self.root)
        numbering_window.grab_set()
        self.center_window(numbering_window, 40, 35)

        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        # Usuń z listy po zamknięciu
        def on_close():
            self.open_windows.discard(window_id)
            numbering_window.destroy()

        numbering_window.protocol("WM_DELETE_WINDOW", on_close)
        # Ustaw ikonę
        try:
            numbering_window.iconbitmap("icon.ico")
        except:
            pass

        # Policz linie w tekście
        lines = text.split('\n')
        total_lines = len(lines)

        # Informacja o liczbie linii
        info_label = tk.Label(numbering_window, text=f"Tekst ma {total_lines} linii",
                             font=("Arial", 10, "bold"), fg="blue")
        info_label.grid(row=0, column=0, columnspan=2, pady=5)

        # Linia początkowa
        tk.Label(numbering_window, text="Od linii:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        start_line_var = tk.IntVar(value=1)
        start_line_entry = tk.Entry(numbering_window, textvariable=start_line_var, width=15)
        start_line_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Linia końcowa
        tk.Label(numbering_window, text="Do linii:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        end_line_var = tk.IntVar(value=min(5, total_lines))
        end_line_entry = tk.Entry(numbering_window, textvariable=end_line_var, width=15)
        end_line_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Liczba początkowa numeracji
        tk.Label(numbering_window, text="Numer początkowy:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        start_number_var = tk.IntVar(value=1)
        start_number_entry = tk.Entry(numbering_window, textvariable=start_number_var, width=15)
        start_number_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # Znak po numerze
        tk.Label(numbering_window, text="Znak po numerze:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        separator_var = tk.StringVar(value=".")
        separator_entry = tk.Entry(numbering_window, textvariable=separator_var, width=15)
        separator_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Spacje po znaku
        tk.Label(numbering_window, text="Spacje po znaku:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        spacing_var = tk.IntVar(value=4)
        spacing_entry = tk.Entry(numbering_window, textvariable=spacing_var, width=15)
        spacing_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Przykład dynamiczny
        example_label = tk.Label(numbering_window, text="", fg="green", font=("Arial", 9))
        example_label.grid(row=6, column=0, columnspan=2, pady=5)

        def update_example():
            """Aktualizuje przykład na żywo"""
            try:
                num = start_number_var.get()
                sep = separator_var.get() or "."
                spaces = " " * spacing_var.get()
                example_text = f"Przykład: '{num}{sep}{spaces}tekst linii'"
                example_label.config(text=example_text)
            except:
                example_label.config(text="Przykład: '1.    tekst linii'")

        # Bindy do aktualizacji przykładu
        for var in [start_number_var, separator_var, spacing_var]:
            if hasattr(var, 'trace_add'):
                var.trace_add('write', lambda *args: update_example())

        update_example()  # Początkowy przykład

        def apply_numbering():
            try:
                # Pobierz wartości z bezpieczną obsługą błędów
                start_line = start_line_var.get()
                end_line = end_line_var.get()
                start_num = start_number_var.get()
                separator = separator_var.get().strip()
                spacing = spacing_var.get()

                # Walidacja danych
                if start_line < 1:
                    messagebox.showerror("Błąd", "Linia początkowa musi być większa od 0!")
                    return

                if end_line > total_lines:
                    messagebox.showerror("Błąd", f"Linia końcowa nie może być większa od {total_lines}!")
                    return

                if start_line > end_line:
                    messagebox.showerror("Błąd", "Linia początkowa nie może być większa od końcowej!")
                    return

                if spacing < 0 or spacing > 20:
                    messagebox.showerror("Błąd", "Liczba spacji musi być między 0 a 20!")
                    return

                if not separator:
                    separator = "."

                # Pobierz tekst i podziel na linie
                current_text = self.text_area.get('1.0', tk.END)
                lines = current_text.split('\n')

                # Usuń ostatnią pustą linię jeśli istnieje
                if lines and lines[-1] == '':
                    lines = lines[:-1]

                # Dodaj numerację
                current_number = start_num
                spacing_text = ' ' * spacing

                for i in range(start_line - 1, end_line):  # -1 bo indeksy od 0
                    if i < len(lines):
                        original_line = lines[i]
                        lines[i] = f"{current_number}{separator}{spacing_text}{original_line}"
                        current_number += 1

                # Zastąp tekst
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert('1.0', '\n'.join(lines))

                messagebox.showinfo("Sukces", f"Numeracja zastosowana do linii {start_line}-{end_line}")
                on_close()

            except tk.TclError as e:
                messagebox.showerror("Błąd", f"Błąd interfejsu: {str(e)}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nieoczekiwany błąd: {str(e)}")

        def cancel_numbering():
            on_close()

        # Przyciski
        button_frame = tk.Frame(numbering_window)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Zastosuj", command=apply_numbering,
                 bg="lightgreen", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Anuluj", command=cancel_numbering,
                 bg="lightcoral", width=10).pack(side=tk.LEFT, padx=5)

        # Focus i bindy
        start_line_entry.focus_set()
        start_line_entry.bind('<Return>', lambda e: apply_numbering())

        # Dodaj tooltips (podpowiedzi)
        def create_tooltip(widget, text):
            def on_enter(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                label = tk.Label(tooltip, text=text, background="yellow", font=("Arial", 8))
                label.pack()
                widget.tooltip = tooltip

            def on_leave(event):
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    del widget.tooltip

            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)

        # Dodaj podpowiedzi
        create_tooltip(start_line_entry, "Pierwsza linia do numerowania")
        create_tooltip(end_line_entry, "Ostatnia linia do numerowania")
        create_tooltip(separator_entry, "Znak po numerze (np. . : ) -)")
        create_tooltip(spacing_entry, "Ile spacji między numerem a tekstem")

    # toggle_reading_line
    def toggle_reading_line(self):
        """Przełącza linijkę do czytania"""
        if not self.reading_line_active:
            window_id = "reading_line_config"
            if window_id in self.open_windows:
                return  # Okno już otwarte

            # Włącz linijkę
            self.reading_line_active = True

            # Okno konfiguracji linijki
            config_window = tk.Toplevel(self.root)
            config_window.title("Konfiguracja linijki")
            config_window.transient(self.root)
            self.center_window(config_window, 40, 40)

            # Dodaj do listy otwartych okien
            self.open_windows.add(window_id)

            # Usuń z listy po zamknięciu
            def on_close():
                self.open_windows.discard(window_id)
                config_window.destroy()

            config_window.protocol("WM_DELETE_WINDOW", on_close)

            # Ustaw ikonę
            try:
                config_window.iconbitmap("icon.ico")
            except:
                pass

            tk.Label(config_window, text="LINIJKA DO CZYTANIA",
                    font=("Arial", 12, "bold")).pack(pady=10)

            tk.Label(config_window, text="Wybierz kolor podświetlenia:",
                    font=("Arial", 10)).pack(pady=5)

            # Wybór koloru
            color_frame = tk.Frame(config_window)
            color_frame.pack(pady=10)

            colors = [
                ("Jasnoniebieski", "lightblue"),
                ("Jasnożółty", "lightyellow"),
                ("Jasnozielony", "lightgreen"),
                ("Jasnoróżowy", "lightpink"),
                ("Jasnoszary", "lightgray")
            ]

            color_var = tk.StringVar(value="lightblue")
            for name, color in colors:
                tk.Radiobutton(color_frame, text=name, variable=color_var, value=color,
                              bg=color).pack(anchor=tk.W)

            def apply_reading_line():
                self.reading_line_color = color_var.get()
                self.current_reading_line = 1
                self.update_reading_line()

                # Dodaj skróty klawiszowe dla linijki
                self.root.bind('<Up>', self.reading_line_up)
                self.root.bind('<Down>', self.reading_line_down)
                self.root.bind('<Shift-Up>', self.reading_line_up_5)
                self.root.bind('<Shift-Down>', self.reading_line_down_5)
                self.root.bind('<Home>', self.reading_line_home)
                self.root.bind('<End>', self.reading_line_end)

                # Zmień wygląd przycisku
                self.reading_line_button.config(bg="lightgreen", text="Linijka ON")

                on_close()
                messagebox.showinfo("Linijka", "Linijka aktywna! Użyj strzałek do nawigacji.")

            # Przyciski
            button_frame = tk.Frame(config_window)
            button_frame.pack(pady=20)

            tk.Button(button_frame, text="Włącz", command=apply_reading_line,
                     bg="lightgreen", width=12).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Anuluj", command=on_close,
                     bg="lightcoral", width=12).pack(side=tk.LEFT, padx=5)
        else:
            # Wyłącz linijkę
            self.reading_line_active = False
            self.text_area.tag_remove("reading_line", "1.0", tk.END)

            # Usuń skróty klawiszowe
            self.root.unbind('<Up>')
            self.root.unbind('<Down>')
            self.root.unbind('<Shift-Up>')
            self.root.unbind('<Shift-Down>')
            self.root.unbind('<Home>')
            self.root.unbind('<End>')

            # Przywróć wygląd przycisku
            self.reading_line_button.config(bg="#FFFE9E", text="Linijka")

            messagebox.showinfo("Linijka", "Linijka wyłączona!")

    # undo_action
    def undo_action(self):
        """Cofnij ostatnią akcję (do 3 kroków)"""
        try:
            self.text_area.edit_undo()
        except tk.TclError:
            messagebox.showinfo("Cofnij", "Brak akcji do cofnięcia")

    # update_reading_line
    def update_reading_line(self):
        """Aktualizuje pozycję linijki do czytania"""
        if self.reading_line_active:
            # Usuń poprzednią linijkę
            self.text_area.tag_remove("reading_line", "1.0", tk.END)

            # Dodaj nową linijkę - całą linię z końcem
            start_pos = f"{self.current_reading_line}.0"
            end_pos = f"{self.current_reading_line}.end+1c"  # +1c żeby objąć znak końca linii
            self.text_area.tag_add("reading_line", start_pos, end_pos)
            self.text_area.tag_config("reading_line", background=self.reading_line_color,
                                    relief="raised", borderwidth=1)

            # Przewiń do linii
            self.text_area.see(start_pos)

            # Ustaw kursor na początku linii
            self.text_area.mark_set(tk.INSERT, start_pos)

