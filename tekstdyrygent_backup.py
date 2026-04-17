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

class TekstDyrygent:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TekstDyrygent - Notatnik")
        self.root.geometry("1200x800")

        # Ustaw ikonę programu
        try:
            self.root.iconbitmap("icon.ico")
        except:
            # Jeśli nie ma pliku icon.ico, użyj domyślnej ikony
            pass

        # Domyślne ustawienia
        self.font_size = 12
        self.font_family = "Arial"
        self.text_color = "black"
        self.bg_color = "white"
        self.cursor_color = "black"
        self.show_line_numbers = False
        self.show_duplicates = False
        self.min_duplicate_length = 3  # Minimalna długość duplikatów
        self.duplicate_first_letter = ""  # Filtr pierwszej litery
        self.available_fonts = self.get_available_fonts()

        # Zabezpieczenie przed wielokrotnym otwieraniem okien
        self.open_windows = set()

        # Ustawienia linijki do czytania
        self.reading_line_active = False
        self.reading_line_color = "lightblue"
        self.current_reading_line = 1

        # Pomiar prędkości pisania
        self.start_time = time.time()  # Czas uruchomienia aplikacji
        self.typing_session_start = None
        self.typing_session_chars = 0
        self.last_key_time = 0
        self.typing_speeds = []  # Historia prędkości
        self.current_typing_text = ""

        # Ustawienia powiadomień o przekroczeniach
        self.notifications_enabled = False  # Domyślnie wyłączone
        self.time_limit_minutes = 60  # Domyślnie 60 minut
        self.line_limit = 100  # Domyślnie 100 linii
        self.size_limit_kb = 100  # Domyślnie 100 KB
        self.time_warning_shown = False
        self.line_warning_shown = False
        self.size_warning_shown = False

        # Zaznaczanie kolumnowe
        self.column_selection_active = False
        self.column_start_pos = None
        self.column_end_pos = None
        self.column_selection_tags = []

        # Wielokrotne zaznaczanie
        self.multi_selection_tags = []

        # Schowek kolumnowy
        self.column_clipboard = []

        # Zaznaczanie prawym przyciskiem
        self.right_click_selection_tags = []

        # Spis treści
        self.table_of_contents = []  # Lista elementów spisu treści
        self.toc_file_path = None    # Ścieżka do pliku spisu treści
        self.current_file = None     # Aktualnie otwarty plik

        # Wczytaj zapisane ustawienia użytkownika
        self.load_user_settings()

        self.setup_ui()
        self.bind_shortcuts()
        
    def get_available_fonts(self):
        """Pobiera dostępne fonty systemowe i z foldera fonts (jeśli istnieje)"""
        # Fonty systemowe
        system_fonts = list(tkFont.families())
        
        # Próba załadowania fontów z foldera fonts
        fonts_folder = os.path.join(os.getcwd(), "fonts")
        custom_fonts = []
        
        if os.path.exists(fonts_folder):
            custom_fonts = [os.path.splitext(file)[0]
                           for file in os.listdir(fonts_folder)
                           if file.lower().endswith(('.ttf', '.otf'))]
        
        # Połącz wszystkie fonty i usuń duplikaty
        all_fonts = sorted(list(set(system_fonts + custom_fonts)))
        return all_fonts
        
    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Pliki
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Pliki", menu=file_menu)
        file_menu.add_command(label="Otwórz tekst", command=self.open_file)
        file_menu.add_command(label="Otwórz z formatowaniem", command=self.open_formatted)
        file_menu.add_command(label="Zapisz jako tekst", command=self.save_file)
        file_menu.add_command(label="Zapisz z formatowaniem", command=self.save_formatted)
        file_menu.add_command(label="Szybki zapis (F5)", command=self.quick_save)
        file_menu.add_separator()
        file_menu.add_command(label="Zakończ", command=self.exit_app)

        # Menu Edycja
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edycja", menu=edit_menu)
        edit_menu.add_command(label="Cofnij", command=self.undo_action)
        edit_menu.add_command(label="Ponów", command=self.redo_action)
        edit_menu.add_separator()
        edit_menu.add_command(label="Zapisz ustawienia", command=lambda: self.save_settings(show_message=True))
        edit_menu.add_command(label="Przywróć ustawienia domyślne", command=self.restore_default_settings)
        edit_menu.add_separator()
        edit_menu.add_command(label="Ustawienia powiadomień", command=self.notification_settings)

        # Menu Info
        info_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Info", menu=info_menu)
        info_menu.add_command(label="Instrukcja", command=self.show_help)
        info_menu.add_command(label="O programie", command=self.show_about)

        # Główny kontener z układem grid dla lepszej kontroli
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_container = tk.Frame(self.root)
        main_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # Frame dla tekstu - główny obszar
        text_frame = tk.Frame(main_container)
        text_frame.grid(row=0, column=0, sticky="nsew", pady=(0,5))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Główne pole tekstowe z obsługą undo/redo (max 50 kroków)
        self.text_area = tk.Text(text_frame, wrap=tk.WORD, undo=True, maxundo=50,
                                font=(self.font_family, self.font_size),
                                fg=self.text_color, bg=self.bg_color,
                                insertbackground=self.cursor_color)
        self.text_area.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.text_area.yview)

        # Pasek przycisków - zawsze widoczny na dole
        button_frame = tk.Frame(main_container, relief=tk.RAISED, bd=1)
        button_frame.grid(row=1, column=0, sticky="ew", pady=(0,2))

        # Stylizacja tekstu
        tk.Button(button_frame, text="Rozmiar tekstu", command=self.change_font_size, bg="#E0CFF2", fg="#2E1A47").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Font", command=self.change_font_family, bg="#E0CFF2", fg="#2E1A47").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Kolor tekstu", command=self.change_text_color, bg="#E0CFF2", fg="#2E1A47").pack(side=tk.LEFT, padx=6)  # większy odstęp

        # Stylizacja edytora
        tk.Button(button_frame, text="Kolor tła", command=self.change_bg_color, bg="#9EFF9E", fg="#2E1A47").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Kolor kursora", command=self.change_cursor_color, bg="#9EFF9E", fg="#2E1A47").pack(side=tk.LEFT, padx=6)

        # Narzędzia i analiza
        tk.Button(button_frame, text="Numeracja", command=self.toggle_line_numbers, fg="#2E1A47").pack(side=tk.LEFT, padx=2)
        self.duplicate_button = tk.Button(button_frame, text="Duplikaty", command=self.toggle_duplicates, fg="#2E1A47")
        self.duplicate_button.pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Raport", command=self.show_report, bg="#9EECF5", fg="#2E1A47").pack(side=tk.LEFT, padx=6)

        # Porządkowanie i wizualne
        tk.Button(button_frame, text="Czyść", command=self.clear_selected_lines, bg="#F0C8B4", fg="#2E1A47").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Puste linie", command=self.empty_lines_manager, bg="#FFFA9E", fg="#2E1A47").pack(side=tk.LEFT, padx=2)
        self.reading_line_button = tk.Button(button_frame, text="Linijka", command=self.toggle_reading_line, bg="#FFFA9E", fg="#2E1A47")
        self.reading_line_button.pack(side=tk.LEFT, padx=6)

        # Wyszukiwanie i inne
        tk.Label(button_frame, text="Znajdź:", bg=button_frame['bg'], fg="#2E1A47").pack(side=tk.LEFT, padx=(10,2))
        self.search_entry = tk.Entry(button_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        self.search_entry.bind('<Return>', self.search_text)

        self.notifications_button = tk.Button(button_frame, text="🔔", command=self.toggle_notifications,
                                            bg="lightgray", width=3, font=("Arial", 10))
        self.notifications_button.pack(side=tk.LEFT, padx=2)
        self.update_notifications_button()

        tk.Button(button_frame, text="Spis treści", command=self.open_table_of_contents,
                bg="#87C749", font=("Arial", 10)).pack(side=tk.LEFT, padx=6)


        # Pasek komend - zawsze widoczny
        self.command_frame = tk.Frame(main_container, relief=tk.RAISED, bd=1)
        self.command_frame.grid(row=2, column=0, sticky="ew", pady=(0,2))

        tk.Label(self.command_frame, text="Komenda:").pack(side=tk.LEFT, padx=(5,0))
        self.command_entry = tk.Entry(self.command_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,5))
        self.command_entry.bind('<Return>', self.execute_command)

        # Pasek statusu - zawsze widoczny na samym dole
        self.status_bar = tk.Label(main_container, text="Znaków: 0 | Linia: 1 | Kolumna: 1 | Zaznaczenie: 0",
                                  relief=tk.SUNKEN, anchor=tk.W, bd=1)
        self.status_bar.grid(row=3, column=0, sticky="ew")

        # Bindy dla aktualizacji statusu
        self.text_area.bind('<KeyRelease>', self.update_status)
        self.text_area.bind('<ButtonRelease>', self.update_status)
        self.text_area.bind('<Motion>', self.update_status)
        self.text_area.bind('<Button-1>', self.on_click)
        self.text_area.bind('<Double-Button-1>', self.on_double_click)
        self.text_area.bind('<KeyPress>', self.on_key_press_combined)

        # Zaznaczanie kolumnowe myszą (pozostawiam Alt bez Shift)
        self.text_area.bind('<Alt-Button-1>', self.start_column_selection)
        self.text_area.bind('<Alt-B1-Motion>', self.update_column_selection)
        self.text_area.bind('<Alt-ButtonRelease-1>', self.end_column_selection)

        # Bind dla zmiany rozmiaru okna
        self.root.bind('<Configure>', self.on_window_configure)

    def on_window_configure(self, event):
        """Obsługa zmiany rozmiaru okna - zapewnia widoczność pasków"""
        if event.widget == self.root:
            # Wymuszenie aktualizacji układu
            self.root.update_idletasks()

    def bind_shortcuts(self):
        # Skróty klawiszowe
        self.root.bind('<Control-f>', lambda e: self.format_selection('bold'))
        self.root.bind('<Control-i>', lambda e: self.format_selection('italic'))
        self.root.bind('<Control-y>', lambda e: self.format_selection('yellow'))
        self.root.bind('<Control-r>', lambda e: self.format_selection('red'))
        self.root.bind('<Control-b>', lambda e: self.format_selection('blue'))
        self.root.bind('<Control-g>', lambda e: self.format_selection('green'))
        self.root.bind('<Control-p>', lambda e: self.format_selection('purple'))
        self.root.bind('<Control-0>', lambda e: self.format_selection('clear'))

        self.root.bind('<Control-Alt-f>', lambda e: self.bold_all_text())
        self.root.bind('<Control-q>', lambda e: self.jump_to_start())
        self.root.bind('<Control-w>', lambda e: self.jump_word_forward())
        self.root.bind('<Control-s>', lambda e: self.jump_word_backward())

        # Nowe skróty
        self.root.bind('<F5>', lambda e: self.quick_save())
        self.root.bind('<Control-z>', lambda e: self.undo_action())
        self.root.bind('<Control-Shift-Y>', lambda e: self.redo_action())  # Ctrl+Shift+Y dla redo
        # Skrót do usuwania linii
        self.root.bind('<Control-d>', lambda e: self.delete_current_line())
        self.root.bind('<Control-Delete>', lambda e: self.delete_current_line())
        
        # Wielokrotne zaznaczanie
        self.text_area.bind('<Control-Shift-Button-1>', self.multi_select_click)

        # Prawy przycisk myszy - zaznaczanie
        self.text_area.bind('<Button-3>', self.right_click_select_word)
        self.text_area.bind('<Control-Button-3>', self.ctrl_right_click_select_column)

        # Obsługa klawiatury dla zaznaczenia kolumnowego
        self.text_area.bind('<Delete>', self.handle_column_delete)
        self.text_area.bind('<BackSpace>', self.handle_column_backspace)
        self.text_area.bind('<Control-c>', self.handle_column_copy)
        self.text_area.bind('<Control-x>', self.handle_column_cut)
        self.text_area.bind('<Control-v>', self.handle_column_paste)
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_area.delete('1.0', tk.END)
                    self.text_area.insert('1.0', content)
                    self.current_file = file_path  # Ustaw aktualny plik
                    self.root.title(f"TekstDyrygent - {file_path}")
                    messagebox.showinfo("Sukces", "Plik wczytany pomyślnie")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można otworzyć pliku: {e}")

    def open_formatted(self):
        """Otwiera plik z zachowanym formatowaniem (.tdyf)"""
        file_path = filedialog.askopenfilename(
            filetypes=[("TekstDyrygent Format", "*.tdyf"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    save_data = pickle.load(file)

                # Wyczyść obecny tekst i formatowanie
                self.text_area.delete('1.0', tk.END)
                for tag in self.text_area.tag_names():
                    if tag not in ['sel', 'current']:
                        self.text_area.tag_delete(tag)

                # Wstaw tekst
                self.text_area.insert('1.0', save_data['text'])

                # Przywróć ustawienia programu
                if 'font_family' in save_data:
                    self.font_family = save_data['font_family']
                if 'font_size' in save_data:
                    self.font_size = save_data['font_size']
                if 'text_color' in save_data:
                    self.text_color = save_data['text_color']
                if 'bg_color' in save_data:
                    self.bg_color = save_data['bg_color']
                if 'cursor_color' in save_data:
                    self.cursor_color = save_data['cursor_color']

                # Zaktualizuj główne pole tekstowe
                self.text_area.config(
                    font=(self.font_family, self.font_size),
                    fg=self.text_color,
                    bg=self.bg_color,
                    insertbackground=self.cursor_color
                )

                # Przywróć wszystkie tagi formatowania
                if 'tags' in save_data:
                    for tag_name, tag_data in save_data['tags'].items():
                        # Przywróć zakresy tagu
                        for start, end in tag_data['ranges']:
                            self.text_area.tag_add(tag_name, start, end)

                        # Przywróć konfigurację tagu
                        if tag_data['font']:
                            self.text_area.tag_config(tag_name, font=tag_data['font'])
                        if tag_data['background']:
                            self.text_area.tag_config(tag_name, background=tag_data['background'])
                        if tag_data['foreground']:
                            self.text_area.tag_config(tag_name, foreground=tag_data['foreground'])

                messagebox.showinfo("Info", "Plik z formatowaniem wczytany pomyślnie")

            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można otworzyć pliku z formatowaniem: {e}")

    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Pliki tekstowe", "*.txt"), ("UTF-8", "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get('1.0', tk.END))
                self.current_file = file_path  # Ustaw aktualny plik
                self.root.title(f"TekstDyrygent - {file_path}")
                messagebox.showinfo("Info", "Plik zapisany pomyślnie")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać pliku: {e}")

    def save_formatted(self):
        """Zapisuje plik z zachowaniem formatowania (kolory, pogrubienia, itp.)"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".tdyf",
            filetypes=[("TekstDyrygent Format", "*.tdyf"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            try:
                # Zbierz wszystkie dane do zapisania
                save_data = {
                    'text': self.text_area.get('1.0', tk.END),
                    'tags': {},
                    'font_family': self.font_family,
                    'font_size': self.font_size,
                    'text_color': self.text_color,
                    'bg_color': self.bg_color,
                    'cursor_color': self.cursor_color
                }

                # Zbierz wszystkie tagi formatowania
                for tag_name in self.text_area.tag_names():
                    if tag_name not in ['sel', 'current']:  # Pomiń systemowe tagi
                        ranges = self.text_area.tag_ranges(tag_name)
                        if ranges:
                            # Konwertuj pozycje na stringi
                            tag_ranges = []
                            for i in range(0, len(ranges), 2):
                                start = str(ranges[i])
                                end = str(ranges[i+1])
                                tag_ranges.append((start, end))

                            # Pobierz konfigurację tagu
                            tag_config = self.text_area.tag_cget(tag_name, 'font')
                            tag_bg = self.text_area.tag_cget(tag_name, 'background')
                            tag_fg = self.text_area.tag_cget(tag_name, 'foreground')

                            save_data['tags'][tag_name] = {
                                'ranges': tag_ranges,
                                'font': tag_config,
                                'background': tag_bg,
                                'foreground': tag_fg
                            }

                # Zapisz do pliku
                with open(file_path, 'wb') as file:
                    pickle.dump(save_data, file)

                messagebox.showinfo("Info", f"Plik z formatowaniem zapisany jako: {file_path}")

            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać pliku z formatowaniem: {e}")

    def quick_save(self):
        """Szybki zapis - F5"""
        # Sprawdź czy jest jakiś tekst
        text_content = self.text_area.get('1.0', tk.END).strip()
        if not text_content:
            messagebox.showwarning("Uwaga", "Brak tekstu do zapisania!")
            return

        # Automatyczna nazwa pliku z datą i czasem
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"tekst_{timestamp}.txt"

        try:
            with open(default_filename, 'w', encoding='utf-8') as file:
                file.write(self.text_area.get('1.0', tk.END))
            self.current_file = default_filename  # Ustaw aktualny plik
            self.root.title(f"TekstDyrygent - {default_filename}")
            messagebox.showinfo("Szybki zapis", f"Plik zapisany jako: {default_filename}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać pliku: {e}")

    def exit_app(self):
        """Zakończ aplikację z potwierdzeniem"""
        # Sprawdź czy są niezapisane zmiany
        text_content = self.text_area.get('1.0', tk.END).strip()
        if text_content:
            result = messagebox.askyesnocancel(
                "Zakończ",
                "Czy chcesz zapisać zmiany przed zakończeniem?\n\n"
                "Tak - zapisz i zakończ\n"
                "Nie - zakończ bez zapisywania\n"
                "Anuluj - powrót do edycji"
            )
            if result is True:  # Tak - zapisz
                self.save_file()
                self.root.quit()
            elif result is False:  # Nie - nie zapisuj
                self.root.quit()
            # None - Anuluj, nie rób nic
        else:
            self.root.quit()

    def undo_action(self):
        """Cofnij ostatnią akcję (do 3 kroków)"""
        try:
            self.text_area.edit_undo()
        except tk.TclError:
            messagebox.showinfo("Cofnij", "Brak akcji do cofnięcia")

    def redo_action(self):
        """Ponów cofniętą akcję"""
        try:
            self.text_area.edit_redo()
        except tk.TclError:
            messagebox.showinfo("Ponów", "Brak akcji do ponowienia")

    def execute_command(self, event=None):
        command = self.command_entry.get().strip()
        if not command:
            return

        try:
            # Obsługa wielu komend po przecinku: /lin(4):y, /lit(6):b, /bol(12):f
            if ',' in command and any(cmd.strip().startswith(('/lin(', '/lit(', '/bol(', '/aka(')) for cmd in command.split(',')):
                commands = [cmd.strip() for cmd in command.split(',')]
                for single_command in commands:
                    if single_command:
                        self.execute_single_command(single_command)
            else:
                # Pojedyncza komenda
                self.execute_single_command(command)

        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd wykonania komendy: {e}")

        self.command_entry.delete(0, tk.END)

    def execute_single_command(self, command):
        """Wykonuje pojedynczą komendę"""
        if command.startswith('/del('):
            self.cmd_delete(command)
        elif command.startswith('/cha('):
            self.cmd_change(command)
        elif command.startswith('/spc('):
            self.cmd_spaces(command)
        elif command.startswith('/aka('):
            self.cmd_indent(command)
        elif command.startswith('/cut('):
            self.cmd_cut_lines(command)
        elif command.startswith('/swp('):
            self.cmd_swap_lines(command)
        elif command.startswith('/cln('):
            self.cmd_clean_empty_lines(command)
        elif command.startswith('/cnt('):
            self.cmd_count_text(command)
        elif command.startswith('/col('):
            self.cmd_column_select(command)
        elif command.startswith('/alf('):  # NOWA KOMENDA
            self.cmd_alphabetical_sort(command)
        elif command.startswith('/rln('):  # NOWA KOMENDA
            self.cmd_remove_lines(command)
        else:
            messagebox.showwarning("Błąd", f"Nieznana komenda: {command}")

    def cmd_delete(self, command):
        # /del(0):słowo - usuwa wszystkie wystąpienia słowa
        match = re.match(r'/del\((\d+)\):(.+)', command)
        if match:
            word = match.group(2)
            text = self.text_area.get('1.0', tk.END)
            new_text = text.replace(word, '')
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', new_text)
            
    def cmd_change(self, command):
        # /cha(nowe):stare - zamienia stare na nowe
        match = re.match(r'/cha\(([^)]+)\):(.+)', command)
        if match:
            new_word = match.group(1)
            old_word = match.group(2)
            text = self.text_area.get('1.0', tk.END)
            new_text = text.replace(old_word, new_word)
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', new_text)
            
    def cmd_spaces(self, command):
        # /spc(1):3 - zamienia potrójne spacje na pojedyncze
        match = re.match(r'/spc\((\d+)\):(\d+)', command)
        if match:
            target_spaces = int(match.group(1))
            source_spaces = int(match.group(2))
            text = self.text_area.get('1.0', tk.END)
            new_text = text.replace(' ' * source_spaces, ' ' * target_spaces)
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', new_text)
            
    def cmd_indent(self, command):
        # /aka(4-8):2 - dodaje wcięcia między liniami 4-8 (zakres)
        # /aka(2, 4, 7, 6, 12):2 - dodaje wcięcia do pojedynczych linii (po przecinku)

        lines = self.text_area.get('1.0', tk.END).split('\n')

        # Najpierw sprawdź zakres (ma myślnik)
        if '-' in command:
            range_match = re.match(r'/aka\((\d+)-(\d+)\):(\d+)', command)
            if range_match:
                # Zakres linii: /aka(4-8):2
                start_line = int(range_match.group(1))
                end_line = int(range_match.group(2))
                spaces = int(range_match.group(3))

                for i in range(start_line-1, min(end_line, len(lines))):
                    if i < len(lines) and lines[i].strip():
                        lines[i] = ' ' * spaces + lines[i]
        else:
            # Pojedyncze linie: /aka(2, 4, 7, 6, 12):2
            single_match = re.match(r'/aka\(\s*([^)]+)\s*\):\s*(\d+)', command)
            if single_match:
                lines_str = single_match.group(1)
                spaces = int(single_match.group(2))

                # Parsuj numery linii po przecinku
                try:
                    line_numbers = [int(num.strip()) for num in lines_str.split(',') if num.strip()]
                    if line_numbers:  # Sprawdź czy są jakieś numery
                        for line_num in line_numbers:
                            i = line_num - 1  # Konwersja na indeks (0-based)
                            if 0 <= i < len(lines):
                                lines[i] = ' ' * spaces + lines[i]
                    else:
                        messagebox.showerror("Błąd", "Nie podano numerów linii")
                        return
                except ValueError:
                    messagebox.showerror("Błąd", "Nieprawidłowy format numerów linii")
                    return

        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', '\n'.join(lines))
            
    def cmd_cut_lines(self, command):
        # /cut(1,2,3):82 - skraca linie i przenosi od pozycji 82
        # /cut(0):82 - wszystkie linie

        # Sprawdź czy to wszystkie linie czy pojedyncze
        all_match = re.match(r'/cut\(0\):(\d+)', command)
        single_match = re.match(r'/cut\(\s*([^)]+)\s*\):\s*(\d+)', command)

        lines = self.text_area.get('1.0', tk.END).split('\n')

        if all_match:
            # Wszystkie linie: /cut(0):82
            cut_position = int(all_match.group(1))

            # Przetwarzaj od końca, żeby indeksy się nie przesuwały
            i = len(lines) - 1
            while i >= 0:
                if len(lines[i]) > cut_position:
                    # Podziel linię
                    remaining_text = lines[i][cut_position:]
                    lines[i] = lines[i][:cut_position]
                    # Wstaw pozostały tekst jako nową linię
                    lines.insert(i + 1, remaining_text)
                i -= 1

        elif single_match:
            # Pojedyncze linie: /cut(1,2,3):82
            lines_str = single_match.group(1)
            cut_position = int(single_match.group(2))

            try:
                line_numbers = [int(num.strip()) for num in lines_str.split(',')]
                # Sortuj od największego do najmniejszego, żeby indeksy się nie przesuwały
                line_numbers.sort(reverse=True)

                # Przechowuj nowe linie do dodania
                new_lines_to_add = []

                for line_num in line_numbers:
                    i = line_num - 1  # Konwersja na indeks (0-based)
                    if 0 <= i < len(lines) and len(lines[i]) > cut_position:
                        # Podziel linię
                        remaining_text = lines[i][cut_position:]
                        lines[i] = lines[i][:cut_position]
                        # Zapamiętaj gdzie wstawić nową linię
                        new_lines_to_add.append((i + 1, remaining_text))

                # Wstaw nowe linie (od końca, żeby indeksy się nie przesuwały)
                for insert_pos, text in new_lines_to_add:
                    lines.insert(insert_pos, text)

            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format numerów linii")
                return

        # Zastąp tekst
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', '\n'.join(lines))

    def cmd_swap_lines(self, command):
        # /swp(2):7 - zamień miejscami linie z 2 na 7
        match = re.match(r'/swp\(\s*(\d+)\s*\):\s*(\d+)', command)
        if match:
            line1 = int(match.group(1))
            line2 = int(match.group(2))

            lines = self.text_area.get('1.0', tk.END).split('\n')

            # Sprawdź czy linie istnieją
            if 1 <= line1 <= len(lines) and 1 <= line2 <= len(lines):
                # Zamień miejscami (indeksy 0-based)
                i1, i2 = line1 - 1, line2 - 1
                lines[i1], lines[i2] = lines[i2], lines[i1]

                # Zastąp tekst
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert('1.0', '\n'.join(lines))

                messagebox.showinfo("Sukces", f"Zamieniono miejscami linie {line1} i {line2}")
            else:
                messagebox.showerror("Błąd", f"Linie {line1} lub {line2} nie istnieją!")
        else:
            messagebox.showerror("Błąd", "Nieprawidłowy format komendy /swp(linia1):linia2")

    def cmd_clean_empty_lines(self, command):
        # /cln(0) - usuń puste linie z całego tekstu
        if command == '/cln(0)':
            lines = self.text_area.get('1.0', tk.END).split('\n')

            # Usuń puste linie (zachowaj tylko niepuste)
            non_empty_lines = [line for line in lines if line.strip()]

            # Policz ile usunięto
            removed_count = len(lines) - len(non_empty_lines)

            # Zastąp tekst
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', '\n'.join(non_empty_lines))

            messagebox.showinfo("Sukces", f"Usunięto {removed_count} pustych linii")
        else:
            messagebox.showerror("Błąd", "Użyj: /cln(0) - usuwa wszystkie puste linie")

    def cmd_count_text(self, command):
        # /cnt(tekst) - policz wystąpienia "tekst"
        match = re.match(r'/cnt\(\s*([^)]+)\s*\)', command)
        if match:
            search_text = match.group(1).strip()

            if search_text:
                # Pobierz cały tekst
                full_text = self.text_area.get('1.0', tk.END)

                # Policz wystąpienia (case-insensitive)
                count = full_text.lower().count(search_text.lower())

                # Policz w ilu liniach występuje
                lines = full_text.split('\n')
                lines_with_text = sum(1 for line in lines if search_text.lower() in line.lower())

                messagebox.showinfo("Wynik zliczania",
                                   f"Tekst '{search_text}' występuje:\n"
                                   f"• {count} razy w całym tekście\n"
                                   f"• W {lines_with_text} liniach")
            else:
                messagebox.showerror("Błąd", "Nie podano tekstu do zliczenia")
        else:
            messagebox.showerror("Błąd", "Użyj: /cnt(tekst) - zlicza wystąpienia tekstu")

    def cmd_column_select(self, command):
        # /col(3-15):12 - zaznacz od linii 3 do 15 kolumnę 12
        # /col(2,5,8):7 - zaznacz w liniach 2,5,8 kolumnę 7
        match = re.match(r'/col\(\s*([^)]+)\s*\):\s*(\d+)', command)
        if match:
            lines_str = match.group(1)
            column = int(match.group(2))

            # Wyczyść poprzednie zaznaczenia kolumnowe
            self.clear_column_selection()

            try:
                if '-' in lines_str:
                    # Zakres linii: /col(3-15):12
                    start_line, end_line = map(int, lines_str.split('-'))
                    line_numbers = list(range(start_line, end_line + 1))
                else:
                    # Pojedyncze linie: /col(2,5,8):7
                    line_numbers = [int(num.strip()) for num in lines_str.split(',') if num.strip()]

                if line_numbers:
                    # Utwórz zaznaczenie kolumnowe
                    for line_num in line_numbers:
                        # Sprawdź czy linia istnieje
                        line_start = f"{line_num}.0"
                        line_end = f"{line_num}.end"

                        try:
                            line_text = self.text_area.get(line_start, line_end)
                            line_length = len(line_text)

                            # Sprawdź czy kolumna istnieje w tej linii
                            if column < line_length:
                                # Zaznacz jeden znak w kolumnie
                                tag_name = f"column_sel_{line_num}_{column}"
                                start_pos = f"{line_num}.{column}"
                                end_pos = f"{line_num}.{column + 1}"

                                self.text_area.tag_add(tag_name, start_pos, end_pos)
                                self.text_area.tag_config(tag_name, background='lightblue', foreground='black')
                                self.column_selection_tags.append(tag_name)

                        except tk.TclError:
                            # Linia nie istnieje
                            continue

                    messagebox.showinfo("Sukces", f"Zaznaczono kolumnę {column} w {len(line_numbers)} liniach")
                else:
                    messagebox.showerror("Błąd", "Nie podano numerów linii")

            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format numerów linii lub kolumny")
        else:
            messagebox.showerror("Błąd", "Użyj: /col(linie):kolumna\nPrzykłady:\n/col(3-15):12\n/col(2,5,8):7")
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
                
        except Exception as e:
            print(f"Błąd podczas usuwania linii: {e}")
    def multi_select_click(self, event):
        """Wielokrotne zaznaczanie fragmentów (Ctrl+Shift+klik)"""
        # Pobierz pozycję kliknięcia
        click_pos = self.text_area.index(f"@{event.x},{event.y}")

        # Znajdź granice słowa
        line_start = click_pos.split('.')[0] + '.0'
        line_end = click_pos.split('.')[0] + '.end'
        line_text = self.text_area.get(line_start, line_end)

        # Znajdź pozycję w linii
        column = int(click_pos.split('.')[1])

        if column < len(line_text):
            # Znajdź początek słowa
            start_col = column
            while start_col > 0 and (line_text[start_col-1].isalnum() or line_text[start_col-1] == '_'):
                start_col -= 1

            # Znajdź koniec słowa
            end_col = column
            while end_col < len(line_text) and (line_text[end_col].isalnum() or line_text[end_col] == '_'):
                end_col += 1

            # Utwórz zaznaczenie słowa
            if start_col < end_col:
                line_num = click_pos.split('.')[0]
                tag_name = f"multi_sel_{len(self.multi_selection_tags)}_{line_num}_{start_col}"
                start_pos = f"{line_num}.{start_col}"
                end_pos = f"{line_num}.{end_col}"

                self.text_area.tag_add(tag_name, start_pos, end_pos)
                self.text_area.tag_config(tag_name, background='yellow', foreground='black')
                self.multi_selection_tags.append(tag_name)

        return "break"

    def get_column_selection_data(self):
        """Pobiera dane z zaznaczenia kolumnowego"""
        if not self.column_selection_tags:
            return []

        column_data = []
        for tag in self.column_selection_tags:
            try:
                # Pobierz zaznaczony tekst
                ranges = self.text_area.tag_ranges(tag)
                if ranges:
                    start_pos = ranges[0]
                    end_pos = ranges[1]
                    text = self.text_area.get(start_pos, end_pos)
                    line_num = int(str(start_pos).split('.')[0])
                    col_num = int(str(start_pos).split('.')[1])
                    column_data.append({
                        'line': line_num,
                        'column': col_num,
                        'text': text,
                        'start': start_pos,
                        'end': end_pos
                    })
            except:
                continue

        return sorted(column_data, key=lambda x: x['line'])

    def handle_column_delete(self, event):
        """Obsługuje klawisz Delete dla zaznaczenia kolumnowego i prawego przycisku"""
        # Sprawdź zaznaczenie prawym przyciskiem
        if self.right_click_selection_tags:
            for tag in reversed(self.right_click_selection_tags):
                try:
                    ranges = self.text_area.tag_ranges(tag)
                    if ranges:
                        self.text_area.delete(ranges[0], ranges[1])
                except:
                    continue
            self.clear_right_click_selection()
            return "break"

        # Sprawdź zaznaczenie kolumnowe
        if self.column_selection_tags:
            column_data = self.get_column_selection_data()
            if column_data:
                # Usuń od końca żeby nie psuć indeksów
                for data in reversed(column_data):
                    self.text_area.delete(data['start'], data['end'])

                self.clear_column_selection()
                return "break"
        return None

    def handle_column_backspace(self, event):
        """Obsługuje klawisz Backspace dla zaznaczenia kolumnowego"""
        if self.column_selection_tags:
            return self.handle_column_delete(event)
        return None

    def handle_column_copy(self, event):
        """Obsługuje Ctrl+C dla zaznaczenia kolumnowego i prawego przycisku"""
        # Sprawdź zaznaczenie prawym przyciskiem
        if self.right_click_selection_tags:
            copied_text = []
            for tag in self.right_click_selection_tags:
                try:
                    ranges = self.text_area.tag_ranges(tag)
                    if ranges:
                        text = self.text_area.get(ranges[0], ranges[1])
                        copied_text.append(text)
                except:
                    continue

            if copied_text:
                # Skopiuj do systemowego schowka
                clipboard_text = '\n'.join(copied_text)
                self.root.clipboard_clear()
                self.root.clipboard_append(clipboard_text)
                return "break"

        # Sprawdź zaznaczenie kolumnowe
        if self.column_selection_tags:
            column_data = self.get_column_selection_data()
            if column_data:
                # Zapisz do schowka kolumnowego
                self.column_clipboard = [data['text'] for data in column_data]

                # Skopiuj też do systemowego schowka
                clipboard_text = '\n'.join(self.column_clipboard)
                self.root.clipboard_clear()
                self.root.clipboard_append(clipboard_text)

                return "break"
        return None

    def handle_column_cut(self, event):
        """Obsługuje Ctrl+X dla zaznaczenia kolumnowego"""
        if self.column_selection_tags:
            # Najpierw skopiuj
            self.handle_column_copy(event)
            # Potem usuń
            self.handle_column_delete(event)
            return "break"
        return None

    def handle_column_paste(self, event):
        """Obsługuje Ctrl+V dla zaznaczenia kolumnowego"""
        if self.column_selection_tags and self.column_clipboard:
            column_data = self.get_column_selection_data()
            if column_data:
                # Zastąp zaznaczone znaki zawartością schowka
                for i, data in enumerate(reversed(column_data)):
                    if i < len(self.column_clipboard):
                        self.text_area.delete(data['start'], data['end'])
                        self.text_area.insert(data['start'], self.column_clipboard[-(i+1)])

                self.clear_column_selection()
                return "break"
        return None

    def handle_column_type(self, event):
        """Obsługuje wpisywanie znaków w zaznaczeniu kolumnowym i prawym przyciskiem"""
        if len(event.char) == 1 and event.char.isprintable():
            # Sprawdź zaznaczenie prawym przyciskiem
            if self.right_click_selection_tags:
                for tag in reversed(self.right_click_selection_tags):
                    try:
                        ranges = self.text_area.tag_ranges(tag)
                        if ranges:
                            self.text_area.delete(ranges[0], ranges[1])
                            self.text_area.insert(ranges[0], event.char)
                    except:
                        continue
                self.clear_right_click_selection()
                return "break"

            # Sprawdź zaznaczenie kolumnowe
            if self.column_selection_tags:
                column_data = self.get_column_selection_data()
                if column_data:
                    # Zastąp wszystkie zaznaczone znaki tym samym znakiem
                    for data in reversed(column_data):
                        self.text_area.delete(data['start'], data['end'])
                        self.text_area.insert(data['start'], event.char)

                    self.clear_column_selection()
                    return "break"
        return None

    def clear_right_click_selection(self):
        """Usuwa wszystkie tagi zaznaczenia prawym przyciskiem"""
        for tag in self.right_click_selection_tags:
            self.text_area.tag_delete(tag)
        self.right_click_selection_tags = []

    def right_click_select_word(self, event):
        """Zaznacza słowo prawym kliknięciem (można zaznaczać wiele słów)"""
        # Pobierz pozycję kliknięcia
        click_pos = self.text_area.index(f"@{event.x},{event.y}")

        # Pobierz cały tekst linii
        line_start = click_pos.split('.')[0] + '.0'
        line_end = click_pos.split('.')[0] + '.end'
        line_text = self.text_area.get(line_start, line_end)

        # Znajdź pozycję w linii
        column = int(click_pos.split('.')[1])

        if column < len(line_text):
            # Znajdź początek słowa
            start_col = column
            while start_col > 0 and (line_text[start_col-1].isalnum() or line_text[start_col-1] == '_'):
                start_col -= 1

            # Znajdź koniec słowa
            end_col = column
            while end_col < len(line_text) and (line_text[end_col].isalnum() or line_text[end_col] == '_'):
                end_col += 1

            # Utwórz zaznaczenie słowa
            if start_col < end_col:
                line_num = click_pos.split('.')[0]
                tag_name = f"right_click_word_{len(self.right_click_selection_tags)}_{line_num}_{start_col}"
                start_pos = f"{line_num}.{start_col}"
                end_pos = f"{line_num}.{end_col}"

                self.text_area.tag_add(tag_name, start_pos, end_pos)
                self.text_area.tag_config(tag_name, background='lightgreen', foreground='black')
                self.right_click_selection_tags.append(tag_name)

        return "break"

    def ctrl_right_click_select_column(self, event):
        """Zaznacza całą kolumnę Ctrl+prawym kliknięciem (można zaznaczać wiele kolumn)"""
        # Pobierz pozycję kliknięcia
        click_pos = self.text_area.index(f"@{event.x},{event.y}")
        column = int(click_pos.split('.')[1])

        # Pobierz wszystkie linie tekstu
        text = self.text_area.get('1.0', tk.END)
        lines = text.split('\n')

        # Zaznacz kolumnę we wszystkich liniach
        for line_num in range(1, len(lines)):
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"

            try:
                line_text = self.text_area.get(line_start, line_end)
                if column < len(line_text):
                    # Zaznacz jeden znak w kolumnie
                    tag_name = f"right_click_column_{len(self.right_click_selection_tags)}_{line_num}_{column}"
                    start_pos = f"{line_num}.{column}"
                    end_pos = f"{line_num}.{column + 1}"

                    self.text_area.tag_add(tag_name, start_pos, end_pos)
                    self.text_area.tag_config(tag_name, background='lightcoral', foreground='white')
                    self.right_click_selection_tags.append(tag_name)

            except tk.TclError:
                continue

        return "break"

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

    def bold_all_text(self):
        self.text_area.tag_add("all_bold", "1.0", tk.END)
        self.text_area.tag_config("all_bold", font=(self.font_family, self.font_size, "bold"))
        
    def jump_to_start(self):
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)
        
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
            
    def on_click(self, event):
        # Anuluj zaznaczenia przy normalnym kliknięciu (bez Ctrl+Shift)
        if not (event.state & 0x4 and event.state & 0x1):  # Nie Ctrl+Shift
            if self.column_selection_active:
                self.column_selection_active = False
                self.clear_column_selection()
            self.clear_multi_selection()
            self.clear_right_click_selection()
        self.update_status()
        
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

    def select_all_same_words(self, event):
        """Zaznacza wszystkie wystąpienia tego samego słowa (Ctrl + podwójne kliknięcie)"""
        # Pobierz pozycję kliknięcia
        click_pos = self.text_area.index(f"@{event.x},{event.y}")

        # Znajdź granice słowa
        word_start = self.text_area.search(r'\b', click_pos, "1.0", backwards=True, regexp=True)
        word_end = self.text_area.search(r'\b', click_pos, tk.END, regexp=True)

        if word_start and word_end:
            # Pobierz słowo
            word = self.text_area.get(word_start, word_end)
            if word.strip():
                # Usuń poprzednie zaznaczenia
                self.text_area.tag_remove(tk.SEL, "1.0", tk.END)

                # Znajdź wszystkie wystąpienia słowa
                start_pos = "1.0"
                while True:
                    start_pos = self.text_area.search(word, start_pos, tk.END, nocase=True)
                    if not start_pos:
                        break

                    # Sprawdź czy to całe słowo (nie część większego słowa)
                    char_before = self.text_area.get(f"{start_pos}-1c", start_pos)
                    char_after = self.text_area.get(f"{start_pos}+{len(word)}c", f"{start_pos}+{len(word)+1}c")

                    if (not char_before.isalnum() and char_before != '_') and \
                       (not char_after.isalnum() and char_after != '_'):
                        end_pos = f"{start_pos}+{len(word)}c"
                        self.text_area.tag_add(tk.SEL, start_pos, end_pos)

                    start_pos = f"{start_pos}+1c"

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

    def on_key_press_combined(self, event):
        """Kombinowana obsługa klawiszy - pomiar prędkości i zaznaczenie kolumnowe"""
        # Najpierw sprawdź zaznaczenie kolumnowe
        if self.column_selection_tags:
            result = self.handle_column_type(event)
            if result == "break":
                return result

        # Potem obsłuż pomiar prędkości pisania
        return self.on_key_press(event)

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

    def find_duplicates_of_word(self, event):
        """Znajduje duplikaty klikniętego słowa (Ctrl + podwójne kliknięcie)"""
        try:
            # Pobierz pozycję kliknięcia
            click_pos = self.text_area.index(f"@{event.x},{event.y}")

            # Pobierz cały tekst linii
            line_start = click_pos.split('.')[0] + '.0'
            line_end = click_pos.split('.')[0] + '.end'
            line_text = self.text_area.get(line_start, line_end)

            # Znajdź pozycję w linii
            column = int(click_pos.split('.')[1])

            # Znajdź granice słowa w linii
            if column < len(line_text):
                # Znajdź początek słowa
                start_col = column
                while start_col > 0 and (line_text[start_col-1].isalnum() or line_text[start_col-1] == '_'):
                    start_col -= 1

                # Znajdź koniec słowa
                end_col = column
                while end_col < len(line_text) and (line_text[end_col].isalnum() or line_text[end_col] == '_'):
                    end_col += 1

                # Pobierz słowo
                if start_col < end_col:
                    word = line_text[start_col:end_col]

                    if word.strip() and len(word) >= 2:  # Min 2 znaki
                        # Znajdź wszystkie wystąpienia
                        full_text = self.text_area.get('1.0', tk.END)
                        words = re.findall(r'\b\w+\b', full_text.lower())

                        # Policz wystąpienia
                        word_lower = word.lower()
                        count = words.count(word_lower)

                        if count > 1:
                            # Usuń poprzednie podświetlenia
                            self.text_area.tag_remove("duplicate_highlight", "1.0", tk.END)

                            # Podświetl wszystkie wystąpienia
                            start_pos = "1.0"
                            found_positions = []
                            while True:
                                start_pos = self.text_area.search(word, start_pos, tk.END, nocase=True)
                                if not start_pos:
                                    break

                                # Sprawdź czy to całe słowo
                                char_before = self.text_area.get(f"{start_pos}-1c", start_pos)
                                char_after = self.text_area.get(f"{start_pos}+{len(word)}c", f"{start_pos}+{len(word)+1}c")

                                if (not char_before.isalnum() and char_before != '_') and \
                                   (not char_after.isalnum() and char_after != '_'):
                                    end_pos = f"{start_pos}+{len(word)}c"
                                    self.text_area.tag_add("duplicate_highlight", start_pos, end_pos)
                                    found_positions.append(start_pos)

                                start_pos = f"{start_pos}+1c"

                            # Konfiguruj podświetlenie
                            self.text_area.tag_config("duplicate_highlight", background='lightcoral', foreground='white')

                            # Pokaż wynik
                            messagebox.showinfo("Duplikaty znalezione",
                                               f"Słowo '{word}' występuje {count} razy w tekście.\n"
                                               f"Wszystkie wystąpienia zostały podświetlone.")
                        else:
                            messagebox.showinfo("Brak duplikatów", f"Słowo '{word}' występuje tylko raz.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd wyszukiwania duplikatów: {e}")
        

    def clear_column_selection(self):
        """Usuwa wszystkie tagi zaznaczenia kolumnowego"""
        for tag in self.column_selection_tags:
            self.text_area.tag_delete(tag)
        self.column_selection_tags = []

    def clear_multi_selection(self):
        """Usuwa wszystkie tagi wielokrotnego zaznaczania"""
        for tag in self.multi_selection_tags:
            self.text_area.tag_delete(tag)
        self.multi_selection_tags = []

    def create_column_selection(self, start_line, start_col, end_line, end_col):
        """Tworzy zaznaczenie kolumnowe między dwoma punktami"""
        self.clear_column_selection()

        # Upewnij się, że start jest przed end
        if start_line > end_line or (start_line == end_line and start_col > end_col):
            start_line, end_line = end_line, start_line
            start_col, end_col = end_col, start_col

        # Utwórz zaznaczenie dla każdej linii
        for line in range(start_line, end_line + 1):
            # Sprawdź czy linia istnieje
            line_start = f"{line}.0"
            line_end = f"{line}.end"

            try:
                line_text = self.text_area.get(line_start, line_end)
                line_length = len(line_text)

                # Oblicz kolumny dla tej linii
                actual_start_col = min(start_col, line_length)
                actual_end_col = min(end_col, line_length)

                if actual_start_col < actual_end_col:
                    # Utwórz tag dla tego fragmentu
                    tag_name = f"column_sel_{line}_{actual_start_col}_{actual_end_col}"
                    start_pos = f"{line}.{actual_start_col}"
                    end_pos = f"{line}.{actual_end_col}"

                    self.text_area.tag_add(tag_name, start_pos, end_pos)
                    self.text_area.tag_config(tag_name, background='lightblue', foreground='black')
                    self.column_selection_tags.append(tag_name)

            except tk.TclError:
                # Linia nie istnieje
                break

    def start_column_selection(self, event):
        """Rozpoczyna zaznaczanie kolumnowe myszą (Alt + klik)"""
        self.column_selection_active = True
        pos = self.text_area.index(f"@{event.x},{event.y}")
        self.column_start_pos = pos
        self.column_end_pos = pos

        # Wyczyść poprzednie zaznaczenie
        self.clear_column_selection()

        return "break"

    def update_column_selection(self, event):
        """Aktualizuje zaznaczenie kolumnowe podczas przeciągania (Alt + przeciągnij)"""
        if self.column_selection_active:
            self.column_end_pos = self.text_area.index(f"@{event.x},{event.y}")
            start_line, start_col = map(int, self.column_start_pos.split("."))
            end_line, end_col = map(int, self.column_end_pos.split("."))
            self.create_column_selection(start_line, start_col, end_line, end_col)

            return "break"

    def cmd_alphabetical_sort(self, command):
        """
        /alf(0) - sortuje wszystkie linie alfabetycznie
        /alf(3) - sortuje tylko linie z 3 spacjami na początku
        """
        match = re.match(r'/alf\((\d+)\)', command)
        if not match:
            messagebox.showerror("Błąd", "Użyj: /alf(liczba_spacji)")
            return

        target_spaces = int(match.group(1))
        lines = self.text_area.get('1.0', tk.END).split('\n')

        if lines and lines[-1] == '':
            lines.pop()

        # Podział na linie pasujące i pozostałe z indeksami
        matching = [(i, line) for i, line in enumerate(lines)
                    if line.strip() and (line.startswith(' ' * target_spaces) and
                    len(line) - len(line.lstrip(' ')) == target_spaces)]
        non_matching = [(i, line) for i, line in enumerate(lines) if i not in [idx for idx, _ in matching]]

        if not matching:
            messagebox.showinfo("Info", f"Brak linii z {target_spaces} spacjami na początku")
            return

        # Sortuj tylko dopasowane linie
        sorted_lines = sorted([line for _, line in matching], key=lambda l: l.strip().lower())

        # Składanie finalnej listy linii
        result_lines = list(lines)  # kopia
        for (i, _), sorted_line in zip(matching, sorted_lines):
            result_lines[i] = sorted_line

        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', '\n'.join(result_lines))
        messagebox.showinfo("Sukces", f"Posortowano {len(matching)} linii z {target_spaces} spacjami")


    def cmd_remove_lines(self, command):
        """
        /rln(tekst) - usuwa wszystkie linie zawierające określony tekst
        """
        match = re.match(r'/rln\(\s*([^)]+)\s*\)', command)
        if not match:
            messagebox.showerror("Błąd", "Użyj: /rln(tekst_do_usunięcia)")
            return

        search_text = match.group(1)
        lines = self.text_area.get('1.0', tk.END).split('\n')

        # Usuń ostatnią pustą linię, jeśli istnieje
        if lines and lines[-1] == '':
            lines = lines[:-1]

        original_count = len(lines)
        filtered_lines = [line for line in lines if search_text not in line]
        removed_count = original_count - len(filtered_lines)

        if removed_count == 0:
            messagebox.showinfo("Info", f"Nie znaleziono linii zawierających: '{search_text}'")
            return

        # Zastąp tekst przefiltrowanymi liniami
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', '\n'.join(filtered_lines))
        messagebox.showinfo("Sukces", f"Usunięto {removed_count} linii zawierających: '{search_text}'")


    def end_column_selection(self, event):
        """Kończy zaznaczanie kolumnowe myszą"""
        if self.column_selection_active:
            pos = self.text_area.index(f"@{event.x},{event.y}")
            self.column_end_pos = pos

            # Finalne zaznaczenie
            start_line, start_col = map(int, self.column_start_pos.split('.'))
            end_line, end_col = map(int, self.column_end_pos.split('.'))
            self.create_column_selection(start_line, start_col, end_line, end_col)

        return "break"

    def column_select_up(self, event):
        """Rozszerza zaznaczenie kolumnowe w górę (Alt + Strzałka w górę)"""
        current_pos = self.text_area.index(tk.INSERT)
        current_line, current_col = map(int, current_pos.split('.'))

        if not self.column_selection_active:
            # Rozpocznij nowe zaznaczenie kolumnowe od kursora w górę
            self.column_selection_active = True
            self.column_start_pos = current_pos

            # Sprawdź czy można iść w górę
            if current_line > 1:
                self.column_end_pos = f"{current_line - 1}.{current_col}"
                # Przesuń kursor w górę
                new_pos = f"{current_line - 1}.{current_col}"
                self.text_area.mark_set(tk.INSERT, new_pos)
                self.text_area.see(tk.INSERT)
            else:
                self.column_end_pos = current_pos
        else:
            # Rozszerz istniejące zaznaczenie w górę
            start_line, start_col = map(int, self.column_start_pos.split('.'))
            end_line, end_col = map(int, self.column_end_pos.split('.'))

            # Sprawdź kierunek obecnego zaznaczenia
            if end_line < start_line:
                # Zaznaczenie idzie w górę - rozszerz dalej w górę
                if end_line > 1:
                    self.column_end_pos = f"{end_line - 1}.{end_col}"
                    new_pos = f"{end_line - 1}.{current_col}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                    self.text_area.see(tk.INSERT)
            else:
                # Zaznaczenie idzie w dół - zmniejsz zaznaczenie
                if end_line > start_line:
                    self.column_end_pos = f"{end_line - 1}.{end_col}"
                    new_pos = f"{end_line - 1}.{current_col}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                    self.text_area.see(tk.INSERT)

        # Utwórz zaznaczenie
        start_line, start_col = map(int, self.column_start_pos.split('.'))
        end_line, end_col = map(int, self.column_end_pos.split('.'))
        self.create_column_selection(start_line, start_col, end_line, end_col)

        return "break"

    def column_select_down(self, event):
        """Rozszerza zaznaczenie kolumnowe w dół (Alt + Strzałka w dół)"""
        current_pos = self.text_area.index(tk.INSERT)
        current_line, current_col = map(int, current_pos.split('.'))

        # Sprawdź ile linii ma tekst
        text = self.text_area.get('1.0', tk.END)
        total_lines = len(text.split('\n')) - 1

        if not self.column_selection_active:
            # Rozpocznij nowe zaznaczenie kolumnowe od kursora w dół
            self.column_selection_active = True
            self.column_start_pos = current_pos

            # Sprawdź czy można iść w dół
            if current_line < total_lines:
                self.column_end_pos = f"{current_line + 1}.{current_col}"
                # Przesuń kursor w dół
                new_pos = f"{current_line + 1}.{current_col}"
                self.text_area.mark_set(tk.INSERT, new_pos)
                self.text_area.see(tk.INSERT)
            else:
                self.column_end_pos = current_pos
        else:
            # Rozszerz istniejące zaznaczenie w dół
            start_line, start_col = map(int, self.column_start_pos.split('.'))
            end_line, end_col = map(int, self.column_end_pos.split('.'))

            # Sprawdź kierunek obecnego zaznaczenia
            if end_line > start_line:
                # Zaznaczenie idzie w dół - rozszerz dalej w dół
                if end_line < total_lines:
                    self.column_end_pos = f"{end_line + 1}.{end_col}"
                    new_pos = f"{end_line + 1}.{current_col}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                    self.text_area.see(tk.INSERT)
            else:
                # Zaznaczenie idzie w górę - zmniejsz zaznaczenie
                if end_line < start_line:
                    self.column_end_pos = f"{end_line + 1}.{end_col}"
                    new_pos = f"{end_line + 1}.{current_col}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                    self.text_area.see(tk.INSERT)

        # Utwórz zaznaczenie
        start_line, start_col = map(int, self.column_start_pos.split('.'))
        end_line, end_col = map(int, self.column_end_pos.split('.'))
        self.create_column_selection(start_line, start_col, end_line, end_col)

        return "break"

    def column_select_left(self, event):
        """Rozszerza zaznaczenie kolumnowe w lewo (Alt + Strzałka w lewo)"""
        current_pos = self.text_area.index(tk.INSERT)
        current_line, current_col = map(int, current_pos.split('.'))

        if not self.column_selection_active:
            # Rozpocznij nowe zaznaczenie kolumnowe od kursora w lewo
            self.column_selection_active = True
            self.column_start_pos = current_pos

            # Sprawdź czy można iść w lewo
            if current_col > 0:
                self.column_end_pos = f"{current_line}.{current_col - 1}"
                # Przesuń kursor w lewo
                new_pos = f"{current_line}.{current_col - 1}"
                self.text_area.mark_set(tk.INSERT, new_pos)
                self.text_area.see(tk.INSERT)
            else:
                self.column_end_pos = current_pos
        else:
            # Rozszerz istniejące zaznaczenie w lewo/prawo
            start_line, start_col = map(int, self.column_start_pos.split('.'))
            end_line, end_col = map(int, self.column_end_pos.split('.'))

            # Sprawdź kierunek obecnego zaznaczenia
            if end_col < start_col:
                # Zaznaczenie idzie w lewo - rozszerz dalej w lewo
                if end_col > 0:
                    self.column_end_pos = f"{end_line}.{end_col - 1}"
                    new_pos = f"{current_line}.{max(0, current_col - 1)}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                    self.text_area.see(tk.INSERT)
            else:
                # Zaznaczenie idzie w prawo - zmniejsz zaznaczenie
                if end_col > start_col:
                    self.column_end_pos = f"{end_line}.{end_col - 1}"
                    new_pos = f"{current_line}.{max(0, current_col - 1)}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                    self.text_area.see(tk.INSERT)

        # Utwórz zaznaczenie
        start_line, start_col = map(int, self.column_start_pos.split('.'))
        end_line, end_col = map(int, self.column_end_pos.split('.'))
        self.create_column_selection(start_line, start_col, end_line, end_col)

        return "break"

    def column_select_right(self, event):
        """Rozszerza zaznaczenie kolumnowe w prawo (Alt + Strzałka w prawo)"""
        current_pos = self.text_area.index(tk.INSERT)
        current_line, current_col = map(int, current_pos.split('.'))

        # Sprawdź długość obecnej linii
        line_start = f"{current_line}.0"
        line_end = f"{current_line}.end"
        line_text = self.text_area.get(line_start, line_end)
        line_length = len(line_text)

        if not self.column_selection_active:
            # Rozpocznij nowe zaznaczenie kolumnowe od kursora w prawo
            self.column_selection_active = True
            self.column_start_pos = current_pos

            # Sprawdź czy można iść w prawo
            if current_col < line_length:
                self.column_end_pos = f"{current_line}.{current_col + 1}"
                # Przesuń kursor w prawo
                new_pos = f"{current_line}.{current_col + 1}"
                self.text_area.mark_set(tk.INSERT, new_pos)
                self.text_area.see(tk.INSERT)
            else:
                self.column_end_pos = current_pos
        else:
            # Rozszerz istniejące zaznaczenie w prawo/lewo
            start_line, start_col = map(int, self.column_start_pos.split('.'))
            end_line, end_col = map(int, self.column_end_pos.split('.'))

            # Sprawdź kierunek obecnego zaznaczenia
            if end_col > start_col:
                # Zaznaczenie idzie w prawo - rozszerz dalej w prawo
                if end_col < line_length:
                    self.column_end_pos = f"{end_line}.{end_col + 1}"
                    new_pos = f"{current_line}.{current_col + 1}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                    self.text_area.see(tk.INSERT)
            else:
                # Zaznaczenie idzie w lewo - zmniejsz zaznaczenie
                if end_col < start_col:
                    self.column_end_pos = f"{end_line}.{end_col + 1}"
                    new_pos = f"{current_line}.{current_col + 1}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                    self.text_area.see(tk.INSERT)

        # Utwórz zaznaczenie
        start_line, start_col = map(int, self.column_start_pos.split('.'))
        end_line, end_col = map(int, self.column_end_pos.split('.'))
        self.create_column_selection(start_line, start_col, end_line, end_col)

        return "break"

    def change_font_size(self):
        window_id = "font_size"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        font_window = tk.Toplevel(self.root)
        font_window.title("Rozmiar tekstu")
        self.center_window(font_window, 35, 20)
        
        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        try:
            font_window.iconbitmap("icon.ico")
        except:
            pass

        tk.Label(font_window, text="Podaj rozmiar (8–88):").pack(pady=5)
        entry = tk.Entry(font_window)
        entry.insert(0, str(self.font_size))
        entry.pack(pady=5)

        def confirm():
            try:
                new_size = int(entry.get())
                if 8 <= new_size <= 88:
                    self.font_size = new_size
                    self.text_area.config(font=(self.font_family, self.font_size))
                    self.save_settings()
                    self.root.update_idletasks()
                    on_close()
            except:
                pass  # Możesz tu dodać komunikat o błędzie

        tk.Button(font_window, text="Zastosuj", command=confirm).pack(pady=5)

        def on_close():
            self.open_windows.discard(window_id)
            font_window.destroy()

        font_window.protocol("WM_DELETE_WINDOW", on_close)


    def change_font_family(self):
        """Zmiana rodziny fontów"""
        window_id = "font_family"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        font_window = tk.Toplevel(self.root)
        font_window.title("Wybierz Font")
        font_window.transient(self.root)
        self.center_window(font_window, 35, 50)

        self.open_windows.add(window_id)

        # Poprawnie przypisujemy on_close do zamknięcia okna
        def on_close():
            self.open_windows.discard(window_id)
            font_window.destroy()

        font_window.protocol("WM_DELETE_WINDOW", on_close)  # <<< TO BYŁO KLUCZOWE!

        # Zapasowe zabezpieczenie przy niszczeniu okna
        font_window.bind("<Destroy>", lambda e: self.open_windows.discard(window_id))

        try:
            font_window.iconbitmap("icon.ico")
        except:
            pass

        listbox = tk.Listbox(font_window, height=20)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for font in self.available_fonts:
            listbox.insert(tk.END, font)

        if self.font_family in self.available_fonts:
            index = self.available_fonts.index(self.font_family)
            listbox.selection_set(index)
            listbox.see(index)

        
        def apply_font():
            selection = listbox.curselection()
            if selection:
                selected_font = self.available_fonts[selection[0]]
                self.font_family = selected_font
                self.text_area.config(font=(self.font_family, self.font_size))
                # Automatycznie zapisz ustawienia
                self.save_settings()
                font_window.destroy()
                
        def preview_font(event):
            selection = listbox.curselection()
            if selection:
                selected_font = self.available_fonts[selection[0]]
                try:
                    # Podgląd fontu w etykiecie
                    preview_label.config(font=(selected_font, 14), 
                                       text=f"Podgląd fontu: {selected_font}")
                except:
                    preview_label.config(text=f"Font niedostępny: {selected_font}")
        
        # Podgląd fontu
        preview_label = tk.Label(font_window, text="Podgląd fontu", height=2)
        preview_label.pack(pady=5)
        
        listbox.bind('<<ListboxSelect>>', preview_font)
        
        # Przyciski
        button_frame = tk.Frame(font_window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Zastosuj", command=apply_font).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Anuluj", command=font_window.destroy).pack(side=tk.LEFT, padx=5)
            
    def change_text_color(self):
        color = colorchooser.askcolor(title="Wybierz kolor tekstu")[1]
        if color:
            self.text_color = color
            self.text_area.config(fg=color)
            # Automatycznie zapisz ustawienia
            self.save_settings()

    def change_bg_color(self):
        color = colorchooser.askcolor(title="Wybierz kolor tła")[1]
        if color:
            self.bg_color = color
            self.text_area.config(bg=color)
            # Automatycznie zapisz ustawienia
            self.save_settings()

    def change_cursor_color(self):
        """Zmiana koloru kursora"""
        color = colorchooser.askcolor(title="Wybierz kolor kursora")[1]
        if color:
            self.cursor_color = color
            self.text_area.config(insertbackground=color)
            # Automatycznie zapisz ustawienia
            self.save_settings()
            
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
        
    def save_report(self, report):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Pliki tekstowe", "*.txt")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(report)
            messagebox.showinfo("Info", "Raport zapisany")
            
    def update_status(self, event=None):
        # Pozycja kursora
        cursor_pos = self.text_area.index(tk.INSERT)
        line, column = cursor_pos.split('.')

        # Liczba znaków
        total_chars = len(self.text_area.get('1.0', tk.END)) - 1  # -1 dla końcowego \n

        # Rozmiar pliku w bajtach
        text_bytes = len(self.text_area.get('1.0', tk.END).encode('utf-8')) - 1
        if text_bytes < 1024:
            size_str = f"{text_bytes}B"
        elif text_bytes < 1024 * 1024:
            size_str = f"{text_bytes/1024:.1f}KB"
        else:
            size_str = f"{text_bytes/(1024*1024):.1f}MB"

        # Zaznaczenie
        try:
            selection = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            selected_chars = len(selection)
        except tk.TclError:
            selected_chars = 0

        # Czas korzystania z aplikacji
        current_time = time.time()
        usage_seconds = int(current_time - self.start_time)
        hours = usage_seconds // 3600
        minutes = (usage_seconds % 3600) // 60
        seconds = usage_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Prędkość pisania
        if self.typing_speeds:
            avg_speed = sum(self.typing_speeds) / len(self.typing_speeds)
            speed_str = f" | Prędkość: {avg_speed:.0f} zn/min"
        else:
            speed_str = ""

        # Sprawdź przekroczenia i pokaż powiadomienia
        self.check_limits(usage_seconds // 60, int(line), text_bytes // 1024)

        # Aktualizuj pasek statusu
        self.status_bar.config(
            text=f"Znaków: {total_chars} | Rozmiar: {size_str} | Linia: {line} | Kolumna: {int(column)+1} | Zaznaczenie: {selected_chars} | Czas: {time_str}{speed_str}"
        )

        # Aktualizacja duplikatów z opóźnieniem
        if self.show_duplicates:
            self.root.after(200, self.highlight_duplicates)  # Zwiększone opóźnienie dla lepszej wydajności
            
    def show_help(self):
        window_id = "help"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        help_text = """INSTRUKCJA TEKSTDYRYGENT

SKRÓTY KLAWISZOWE:
Ctrl+F - pogrub zaznaczenie
Ctrl+Y/R/B/G/P - kolory (żółty/czerwony/niebieski/zielony/fioletowy)
Ctrl+0 - usuń formatowanie
Ctrl+D/DEL - usuń linie na której jest kursor
Ctrl+Alt+F - pogrub cały tekst
Ctrl+Q - przejdź na początek
Ctrl+W/S - skacz między słowami
F5 - szybki zapis
Ctrl+Z - cofnij (do 50 kroków)
Ctrl+Shift+Y - ponów

ZAZNACZANIE:
Alt+przeciągnij myszą - zaznacz prostokątny blok tekstu
Ctrl+Shift+klik - wielokrotne zaznaczanie słów
Ctrl+podwójne kliknięcie - zaznacz wszystkie duplikaty słowa
Prawy klik - zaznacz słowo (można zaznaczać wiele słów)
Ctrl+prawy klik - zaznacz kolumnę (można zaznaczać wiele kolumn)
Kliknij normalnie - anuluj wszystkie zaznaczenia

EDYCJA ZAZNACZENIA KOLUMNOWEGO:
Delete/Backspace - usuń zaznaczone znaki
Ctrl+C - skopiuj zaznaczone znaki
Ctrl+X - wytnij zaznaczone znaki
Ctrl+V - wklej do zaznaczonych pozycji

SPIS TREŚCI:
Przycisk "Spis treści" - otwiera okno nawigacji
Dodaj element - tytuł (max 95 znaków) + numer linii + kolor
Kolory przycisków: żółty, zielony, niebieski
Kliknij przycisk z numerem - przejdź do linii
Zapisz/Wczytaj - automatycznie dla każdego pliku
× - usuń element ze spisu treści

MENU:
Pliki → Otwórz, Zapisz, Szybki zapis (F5), Zakończ
Edycja → Cofnij, Ponów
Info → Instrukcja

KOMENDY:
/del(0):słowo - usuń słowo
/cha(nowe):stare - zamień stare na nowe
/spc(1):3 - zamień potrójne spacje na pojedyncze
/aka(4-8):2 - dodaj wcięcia (zakres linii)
/cut(1,2,3):82 - skraca linie i przenosi od pozycji 82
/cut(0):82 - wszystkie linie
/col(3-15):12 - zaznacz kolumnę 12 w liniach 3-15
/col(2,5,8):7 - zaznacz kolumnę 7 w liniach 2,5,8
/swp(2):7 - zamień miejscami linie z 2 na 7
/cln(0) - usuń puste linie z całego tekstu
/cnt(tekst) - policz wystąpienia "tekst"
/alf(3) - sortuj alfabetycznie linie np. z 3 spacjami lub 0 wszystkie linie bez spacji
/rln(tekst) - usuń linie zawierające "tekst"

PRZYCISKI:
• Czyść - usuwa formatowanie z wybranych linii
• Puste linie - wypełnia puste linie tekstem
• Linijka - pomoc w czytaniu z nawigacją strzałkami

SKRÓTY KLAWISZOWE:
• Ctrl+0 - czyści wszystkie formatowania
• Ctrl+podwójne kliknięcie - zaznacza wszystkie takie same słowa
• Strzałki (gdy linijka aktywna) - nawigacja po liniach
• Shift+strzałki - przeskok o 5 linii
• Home/End - początek/koniec tekstu

FUNKCJE:
- Przycisk "Font" - wybór fontów systemowych i z folderu "fonts"
- Przycisk "Kolor kursora" - zmiana koloru kursora
- Przycisk "Numeracja" - numeruje określone linie tekstu
- Przycisk "Raport" - szczegółowe statystyki tekstu
- Paski komend i przycisków są zawsze widoczne
"""

        # Okno instrukcji z większą czcionką
        help_window = tk.Toplevel(self.root)
        help_window.title("Instrukcja - TekstDyrygent")
        help_window.transient(self.root)
        self.center_window(help_window, 50, 60)

        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        # Usuń z listy po zamknięciu
        def on_close():
            self.open_windows.discard(window_id)
            help_window.destroy()

        help_window.protocol("WM_DELETE_WINDOW", on_close)

        # Ustaw ikonę dla okna instrukcji
        try:
            help_window.iconbitmap("icon.ico")
        except:
            pass

        # Frame z scrollbarem
        frame = tk.Frame(help_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Pole tekstowe z większą czcionką
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Arial", 12),
                             bg="lightyellow", fg="black", state='normal')
        scrollbar = tk.Scrollbar(frame)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

        # Wstaw tekst instrukcji
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')  # Tylko do odczytu

        # Przycisk zamknij
        tk.Button(help_window, text="Zamknij", command=on_close,
                 bg="lightcoral", font=("Arial", 11), width=15).pack(pady=5)

    def show_about(self):
        """Okno O programie z danymi autora"""
        window_id = "about"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        about_text = """TekstDyrygent - Zaawansowany Notatnik
Wersja 1.0

🎯 AUTOR:
Fundamentalist90@proton.me

📝 OPIS:
Edytor tekstu z zaawansowanymi funkcjami formatowania,
statystykami, powiadomieniami, komendami i analizą duplikatów.

💝 LICENCJA:
Program jest w pełni darmowy!

🙏 PODZIĘKOWANIA:
Jeśli lubisz ten notatnik, proszę o ewentualne podziękowanie.

💰 DAROWIZNY (opcjonalnie):
Bardzo dziękuję za każdą najbardziej symboliczną darowiznę:

Bitcoin (BTC):
1J7pgoCRRzqRvY8vQ1KzhdaXpGbVLoQFnG

Tron (TRX):
TVGAM39FrwMFcyCZ4aZEE46CvEd9Adgbeo

Miłego korzystania z TekstDyrygenta :-)
Pozdrawiam serdecznie...
"""

        # Okno O programie
        about_window = tk.Toplevel(self.root)
        about_window.title("O programie - TekstDyrygent")
        about_window.geometry("800x600")
        about_window.transient(self.root)

        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        # Usuń z listy po zamknięciu
        def on_close():
            self.open_windows.discard(window_id)
            about_window.destroy()

        about_window.protocol("WM_DELETE_WINDOW", on_close)

        # Ustaw ikonę dla okna O programie
        try:
            about_window.iconbitmap("icon.ico")
        except:
            pass

        # Frame z scrollbarem
        frame = tk.Frame(about_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Pole tekstowe z informacjami
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Arial", 11),
                             bg="lightyellow", fg="black", state='normal',
                             relief=tk.FLAT, bd=10)
        scrollbar = tk.Scrollbar(frame)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

        # Wstaw tekst
        text_widget.insert('1.0', about_text)
        text_widget.config(state='disabled')  # Tylko do odczytu

        # Przyciski
        button_frame = tk.Frame(about_window)
        button_frame.pack(pady=10)

        # Przycisk kopiowania emaila
        def copy_email():
            about_window.clipboard_clear()
            about_window.clipboard_append("Fundamentalist90@proton.me")
            messagebox.showinfo("Skopiowano", "Email skopiowany do schowka!")

        # Przycisk kopiowania BTC
        def copy_btc():
            about_window.clipboard_clear()
            about_window.clipboard_append("1J7pgoCRRzqRvY8vQ1KzhdaXpGbVLoQFnG")
            messagebox.showinfo("Skopiowano", "Adres BTC skopiowany do schowka!")

        # Przycisk kopiowania TRX
        def copy_trx():
            about_window.clipboard_clear()
            about_window.clipboard_append("TVGAM39FrwMFcyCZ4aZEE46CvEd9Adgbeo")
            messagebox.showinfo("Skopiowano", "Adres TRX skopiowany do schowka!")

        tk.Button(button_frame, text="📧 Kopiuj Email", command=copy_email,
                 bg="lightblue", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="₿ Kopiuj BTC", command=copy_btc,
                 bg="orange", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="🔷 Kopiuj TRX", command=copy_trx,
                 bg="lightgreen", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Zamknij", command=on_close,
                 bg="lightcoral", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)

    def load_user_settings(self):
        """Wczytuje zapisane ustawienia użytkownika"""
        try:
            settings_file = "tekstdyrygent_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as file:
                    settings = json.load(file)

                # Zastosuj ustawienia jeśli istnieją
                self.font_size = settings.get('font_size', self.font_size)
                self.font_family = settings.get('font_family', self.font_family)
                self.text_color = settings.get('text_color', self.text_color)
                self.bg_color = settings.get('bg_color', self.bg_color)
                self.cursor_color = settings.get('cursor_color', self.cursor_color)

        except Exception:
            # Jeśli nie można wczytać ustawień, użyj domyślnych
            pass

    def save_settings(self, show_message=False):
        """Zapisuje obecne ustawienia użytkownika"""
        try:
            settings = {
                'font_size': self.font_size,
                'font_family': self.font_family,
                'text_color': self.text_color,
                'bg_color': self.bg_color,
                'cursor_color': self.cursor_color
            }

            settings_file = "tekstdyrygent_settings.json"
            with open(settings_file, 'w', encoding='utf-8') as file:
                json.dump(settings, file, indent=2, ensure_ascii=False)

            if show_message:
                messagebox.showinfo("Ustawienia",
                                  f"Ustawienia zapisane pomyślnie!\n\n"
                                  f"Font: {self.font_family} {self.font_size}pt\n"
                                  f"Kolor tekstu: {self.text_color}\n"
                                  f"Kolor tła: {self.bg_color}\n"
                                  f"Kolor kursora: {self.cursor_color}\n\n"
                                  f"Ustawienia będą zastosowane przy następnym uruchomieniu.")

        except Exception as e:
            if show_message:
                messagebox.showerror("Błąd", f"Nie można zapisać ustawień: {e}")

    def restore_default_settings(self):
        """Przywraca ustawienia domyślne"""
        result = messagebox.askyesno("Przywróć domyślne",
                                   "Czy na pewno chcesz przywrócić ustawienia domyślne?\n\n"
                                   "Obecne ustawienia zostaną zastąpione domyślnymi:\n"
                                   "• Font: Arial 12pt\n"
                                   "• Kolor tekstu: czarny\n"
                                   "• Kolor tła: biały\n"
                                   "• Kolor kursora: czarny")

        if result:
            # Przywróć domyślne wartości
            self.font_size = 12
            self.font_family = "Arial"
            self.text_color = "black"
            self.bg_color = "white"
            self.cursor_color = "black"

            # Zastosuj zmiany do interfejsu
            self.text_area.config(
                font=(self.font_family, self.font_size),
                fg=self.text_color,
                bg=self.bg_color,
                insertbackground=self.cursor_color
            )

            # Zapisz domyślne ustawienia
            self.save_settings(show_message=False)

            messagebox.showinfo("Przywrócono", "Ustawienia domyślne zostały przywrócone i zapisane!")

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

    def notification_settings(self):
        """Okno ustawień powiadomień o przekroczeniach"""
        window_id = "notification_settings"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        settings_window = tk.Toplevel(self.root)
        settings_window.title("Ustawienia powiadomień")
        settings_window.transient(self.root)
        self.center_window(settings_window, 40, 45)

        # Dodaj do listy otwartych okien
        self.open_windows.add(window_id)

        # Usuń z listy po zamknięciu
        def on_close():
            self.open_windows.discard(window_id)
            settings_window.destroy()

        settings_window.protocol("WM_DELETE_WINDOW", on_close)

        # Ustaw ikonę
        try:
            settings_window.iconbitmap("icon.ico")
        except:
            pass

        tk.Label(settings_window, text="USTAWIENIA POWIADOMIEŃ O PRZEKROCZENIACH",
                font=("Arial", 12, "bold")).pack(pady=10)

        # Informacja o działaniu
        info_frame = tk.Frame(settings_window, bg="lightyellow", relief=tk.RIDGE, bd=2)
        info_frame.pack(pady=10, padx=20, fill=tk.X)

        info_text = """ℹ️ JAK TO DZIAŁA:
• Ustaw poniżej limity ostrzeżeń
• Włącz powiadomienia przyciskiem 🔔 na pasku narzędzi
• Otrzymasz ostrzeżenie gdy przekroczysz ustawione limity
• Wyłącz przyciskiem 🔕 gdy nie chcesz ostrzeżeń"""

        tk.Label(info_frame, text=info_text, font=("Arial", 9), bg="lightyellow",
                justify=tk.LEFT).pack(pady=8, padx=10)

        # Czas siedzenia
        time_frame = tk.Frame(settings_window)
        time_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(time_frame, text="⏰ Czas korzystania (minuty):", font=("Arial", 10)).pack(anchor=tk.W)
        time_var = tk.IntVar(value=self.time_limit_minutes)
        time_entry = tk.Entry(time_frame, textvariable=time_var, width=10)
        time_entry.pack(anchor=tk.W, pady=2)

        # Liczba linii
        line_frame = tk.Frame(settings_window)
        line_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(line_frame, text="📝 Maksymalna liczba linii:", font=("Arial", 10)).pack(anchor=tk.W)
        line_var = tk.IntVar(value=self.line_limit)
        line_entry = tk.Entry(line_frame, textvariable=line_var, width=10)
        line_entry.pack(anchor=tk.W, pady=2)

        # Rozmiar pliku
        size_frame = tk.Frame(settings_window)
        size_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(size_frame, text="💾 Maksymalny rozmiar (KB):", font=("Arial", 10)).pack(anchor=tk.W)
        size_var = tk.IntVar(value=self.size_limit_kb)
        size_entry = tk.Entry(size_frame, textvariable=size_var, width=10)
        size_entry.pack(anchor=tk.W, pady=2)

        def apply_settings():
            try:
                # Pobierz nowe wartości
                new_time = time_var.get()
                new_line = line_var.get()
                new_size = size_var.get()

                # Walidacja
                if new_time < 1 or new_time > 1440:  # Max 24h
                    messagebox.showerror("Błąd", "Czas musi być między 1 a 1440 minut!")
                    return

                if new_line < 10 or new_line > 10000:
                    messagebox.showerror("Błąd", "Liczba linii musi być między 10 a 10000!")
                    return

                if new_size < 1 or new_size > 100000:  # Max 100MB
                    messagebox.showerror("Błąd", "Rozmiar musi być między 1 a 100000 KB!")
                    return

                # Zapisz nowe ustawienia
                self.time_limit_minutes = new_time
                self.line_limit = new_line
                self.size_limit_kb = new_size

                # Automatycznie resetuj ostrzeżenia po zmianie ustawień
                self.time_warning_shown = False
                self.line_warning_shown = False
                self.size_warning_shown = False

                on_close()

                # Pokaż komunikat z nowymi ustawieniami
                status = "włączone" if self.notifications_enabled else "wyłączone"
                messagebox.showinfo("Ustawienia zapisane",
                                   f"✅ Nowe limity ostrzeżeń:\n\n"
                                   f"⏰ Czas: {self.time_limit_minutes} minut\n"
                                   f"📝 Linie: {self.line_limit}\n"
                                   f"💾 Rozmiar: {self.size_limit_kb} KB\n\n"
                                   f"Powiadomienia są obecnie: {status}\n"
                                   f"Użyj przycisku 🔔/🔕 aby włączyć/wyłączyć.")

            except ValueError:
                messagebox.showerror("Błąd", "Wprowadź prawidłowe liczby!")

        # Przyciski
        button_frame = tk.Frame(settings_window)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Zapisz", command=apply_settings,
                 bg="lightgreen", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Anuluj", command=on_close,
                 bg="lightcoral", width=12).pack(side=tk.LEFT, padx=5)

        time_entry.focus_set()

    def center_window(self, window, width_percent=38, height_percent=38):
        """Wyśrodkowuje okno względem głównego okna aplikacji"""
        # Pobierz rozmiar głównego okna
        self.root.update_idletasks()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()

        # Oblicz rozmiar nowego okna (procent głównego okna)
        new_width = int(main_width * width_percent / 100)
        new_height = int(main_height * height_percent / 100)

        # Minimalne rozmiary
        min_width = 400
        min_height = 300
        new_width = max(new_width, min_width)
        new_height = max(new_height, min_height)

        # Oblicz pozycję wyśrodkowania
        center_x = main_x + (main_width - new_width) // 2
        center_y = main_y + (main_height - new_height) // 2

        # Ustaw geometrię okna
        window.geometry(f"{new_width}x{new_height}+{center_x}+{center_y}")

    def toggle_notifications(self):
        """Przełącza stan powiadomień"""
        self.notifications_enabled = not self.notifications_enabled
        self.update_notifications_button()

        if self.notifications_enabled:
            messagebox.showinfo("Powiadomienia",
                               "🔔 Powiadomienia WŁĄCZONE\n\n"
                               "Będziesz otrzymywać ostrzeżenia o:\n"
                               f"• Czasie > {self.time_limit_minutes} min\n"
                               f"• Liniach > {self.line_limit}\n"
                               f"• Rozmiarze > {self.size_limit_kb} KB\n\n"
                               "Kliknij przycisk 🔔 aby wyłączyć.")
        else:
            messagebox.showinfo("Powiadomienia",
                               "🔕 Powiadomienia WYŁĄCZONE\n\n"
                               "Nie będziesz otrzymywać ostrzeżeń.\n"
                               "Kliknij przycisk 🔕 aby włączyć.")

    def update_notifications_button(self):
        """Aktualizuje wygląd przycisku powiadomień"""
        if self.notifications_enabled:
            self.notifications_button.config(text="🔔", bg="lightgreen",
                                            relief=tk.RAISED)
        else:
            self.notifications_button.config(text="🔕", bg="lightgray",
                                            relief=tk.FLAT)

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

    def reading_line_up(self, event):
        """Przesuń linijkę w górę"""
        if self.reading_line_active and self.current_reading_line > 1:
            self.current_reading_line -= 1
            self.update_reading_line()
        return "break"  # Zatrzymaj domyślne zachowanie

    def reading_line_down(self, event):
        """Przesuń linijkę w dół"""
        if self.reading_line_active:
            text = self.text_area.get('1.0', tk.END)
            max_lines = len(text.split('\n'))
            if self.current_reading_line < max_lines:
                self.current_reading_line += 1
                self.update_reading_line()
        return "break"

    def reading_line_up_5(self, event):
        """Przesuń linijkę o 5 w górę"""
        if self.reading_line_active:
            self.current_reading_line = max(1, self.current_reading_line - 5)
            self.update_reading_line()
        return "break"

    def reading_line_down_5(self, event):
        """Przesuń linijkę o 5 w dół"""
        if self.reading_line_active:
            text = self.text_area.get('1.0', tk.END)
            max_lines = len(text.split('\n'))
            self.current_reading_line = min(max_lines, self.current_reading_line + 5)
            self.update_reading_line()
        return "break"

    def reading_line_home(self, event):
        """Przesuń linijkę na początek"""
        if self.reading_line_active:
            self.current_reading_line = 1
            self.update_reading_line()
        return "break"

    def reading_line_end(self, event):
        """Przesuń linijkę na koniec"""
        if self.reading_line_active:
            text = self.text_area.get('1.0', tk.END)
            max_lines = len(text.split('\n'))
            self.current_reading_line = max_lines
            self.update_reading_line()
        return "break"

    def run(self):
        self.root.mainloop()

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

if __name__ == "__main__":
    app = TekstDyrygent()
    app.run()
