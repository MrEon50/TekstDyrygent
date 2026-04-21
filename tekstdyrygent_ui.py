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

class UIMixin:
    # bind_shortcuts
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
        self.root.bind('<Escape>', self.clear_all_custom_selections)

        self.root.bind('<Control-Alt-f>', lambda e: self.bold_all_text())
        self.root.bind('<Control-q>', lambda e: self.jump_to_start())
        self.root.bind('<Control-w>', lambda e: self.jump_word_forward())
        self.root.bind('<Control-s>', lambda e: self.jump_word_backward())
        
        def custom_prompt_action(e):
            self.ollama_transform_custom()
            return 'break'

        def selection_prompt_action(e):
            self.ollama_selection_as_prompt()
            return 'break'

        self.root.bind('<Control-Shift-O>', custom_prompt_action)
        self.root.bind('<Control-Shift-o>', custom_prompt_action)
        self.root.bind('<Control-Shift-M>', selection_prompt_action)
        self.root.bind('<Control-Shift-m>', selection_prompt_action)

        def cancel_ai_action(e):
            self.ollama_cancel()
            return 'break'

        self.root.bind('<Control-Shift-X>', cancel_ai_action)
        self.root.bind('<Control-Shift-x>', cancel_ai_action)

        # Skrót do powtarzania promptu
        self.root.bind('<Control-Alt-p>', lambda e: self.ollama_repeat_last_prompt())

        # Nowe skróty
        self.root.bind('<F5>', lambda e: self.quick_save())
        
        def safe_undo(e):
            self.undo_action()
            return 'break'

        def safe_redo(e):
            self.redo_action()
            return 'break'

        def safe_delete_line(e):
            self.delete_current_line()
            return 'break'

        self.text_area.bind('<Control-z>', safe_undo)
        self.text_area.bind('<Control-Shift-Z>', safe_redo)
        self.text_area.bind('<Control-Shift-Y>', safe_redo)
        
        # Skrót do usuwania linii
        self.text_area.bind('<Control-d>', safe_delete_line)
        self.text_area.bind('<Control-Delete>', safe_delete_line)
        
        # Wielokrotne zaznaczanie i duplikaty pod Ctrl+Klik
        self.text_area.bind('<Control-Button-1>', self.multi_select_click)
        self.text_area.bind('<Control-Double-Button-1>', self.find_duplicates_of_word)

        # Prawy przycisk myszy - zaznaczanie
        self.text_area.bind('<Button-3>', self.right_click_select_word)
        self.text_area.bind('<Control-Button-3>', self.ctrl_right_click_select_column)

        # Obsługa klawiatury dla zaznaczenia kolumnowego
        self.text_area.bind('<Delete>', self.handle_column_delete)
        self.text_area.bind('<BackSpace>', self.handle_column_backspace)
        self.text_area.bind('<Control-c>', self.handle_column_copy)
        self.text_area.bind('<Control-x>', self.handle_column_cut)
        self.text_area.bind('<Control-v>', self.handle_column_paste)

    # center_window
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

    # change_bg_color
    def change_bg_color(self):
        color = colorchooser.askcolor(title="Wybierz kolor tła")[1]
        if color:
            self.bg_color = color
            self.text_area.config(bg=color)
            # Automatycznie zapisz ustawienia
            self.save_settings()

    # change_cursor_color
    def change_cursor_color(self):
        """Zmiana koloru kursora"""
        color = colorchooser.askcolor(title="Wybierz kolor kursora")[1]
        if color:
            self.cursor_color = color
            self.text_area.config(insertbackground=color)
            # Automatycznie zapisz ustawienia
            self.save_settings()

    # change_font_family
    def change_font_family(self):
        """Zmiana rodziny fontów"""
        window_id = "font_family"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        font_window = tk.Toplevel(self.root)
        font_window.withdraw()
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

        font_window.deiconify()

    # change_font_size
    def change_font_size(self):
        window_id = "font_size"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        font_window = tk.Toplevel(self.root)
        font_window.withdraw()
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
        font_window.deiconify()

    # change_text_color
    def change_text_color(self):
        color = colorchooser.askcolor(title="Wybierz kolor tekstu")[1]
        if color:
            self.text_color = color
            self.text_area.config(fg=color)
            # Automatycznie zapisz ustawienia
            self.save_settings()

    # exit_app
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

    # notification_settings
    def notification_settings(self):
        """Okno ustawień powiadomień o przekroczeniach"""
        window_id = "notification_settings"
        if window_id in self.open_windows:
            return  # Okno już otwarte

        settings_window = tk.Toplevel(self.root)
        settings_window.withdraw()
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
        settings_window.deiconify()

    # on_window_configure
    def on_window_configure(self, event):
        """Obsługa zmiany rozmiaru okna - zapewnia widoczność pasków"""
        if event.widget == self.root:
            # Wymuszenie aktualizacji układu
            self.root.update_idletasks()

    # setup_ui
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
        edit_menu.add_separator()
        edit_menu.add_command(label="Ustawienia Ollama", command=self.ollama_config_window)

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

        # Przycisk AI z menu
        self.ai_menu = tk.Menu(self.root, tearoff=0)
        self.ai_menu.add_command(label="🤖 Podsumuj", command=lambda: self.ollama_transform("podsumuj"))
        self.ai_menu.add_command(label="✏️ Popraw tekst", command=lambda: self.ollama_transform("popraw"))
        self.ai_menu.add_command(label="📝 Rozwiń", command=lambda: self.ollama_transform("rozwin"))
        self.ai_menu.add_command(label="🔄 Parafrazuj", command=lambda: self.ollama_transform("parafrazuj"))
        self.ai_menu.add_command(label="🌐 Tłumacz na...", command=self.ollama_translate)
        self.ai_menu.add_separator()
        self.ai_menu.add_command(label="🎯 Custom prompt (kontekst)...", command=self.ollama_transform_custom)
        self.ai_menu.add_command(label="⚡ Zaznaczenie jako prompt...", command=self.ollama_selection_as_prompt)
        self.ai_menu.add_command(label="❌ Anuluj generowanie (Ctrl+Shift+X)", command=self.ollama_cancel)
        self.ai_menu.add_separator()
        self.ai_menu.add_command(label="⚙️ Ustawienia Ollama", command=self.ollama_config_window)

        def post_ai_menu():
            self.ai_menu.post(self.ai_button.winfo_rootx(), self.ai_button.winfo_rooty() - 250)

        self.ai_button = tk.Button(button_frame, text="🤖 AI", command=post_ai_menu,
                                 bg="#D1FFD1", fg="#2E1A47", font=("Arial", 10, "bold"))
        self.ai_button.pack(side=tk.LEFT, padx=2)

        tk.Button(button_frame, text="🔄 Powtórz", command=self.ollama_repeat_last_prompt,
                  bg="#D1FFD1", fg="#2E1A47", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)


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

    # show_about
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


"""

        about_window = tk.Toplevel(self.root)
        about_window.withdraw()
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

        tk.Button(button_frame, text="📧 Kopiuj Email", command=copy_email,
                 bg="lightblue", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Zamknij", command=on_close,
                 bg="lightcoral", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)

        about_window.deiconify()

    # show_help
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
Ctrl+Shift+O - wywołaj AI (Custom prompt z kontekstem)
Ctrl+Shift+M - zaznaczenie jako prompt (odpowiedź wkleja poniżej zaznaczenia)
Ctrl+Shift+X - anuluj generowanie AI
Ctrl+Q - przejdź na początek
Ctrl+W/S - skacz między słowami
F5 - szybki zapis
Ctrl+Z - cofnij (do 50 kroków)
Ctrl+Shift+Y - ponów
Ctrl+Alt+P - powtórz ostatni custom prompt
Esc - anuluj wszystkie zaznaczenia (kolumnowe, multi, duplikaty)

ZAZNACZANIE:
Alt+przeciągnij myszą - zaznacz prostokątny blok tekstu
Ctrl+klik - zaznaczanie wielu słów LUB duplikatów (wyświetla komunikat o ilości)
Ctrl+Double click - wyszukaj wszystkie wystąpienia słowa (duplikaty)
Prawy klik - zaznacz słowo (można zaznaczać wiele słów)
Ctrl+prawy klik - zaznacz kolumnę (zoptymalizowane dla dużych plików)
Kliknij normalnie - anuluj wszystkie zaznaczenia i podświetlenia

EDYCJA ZAZNACZENIA KOLUMNOWEGO:
Delete/Backspace - usuń zaznaczone znaki
Ctrl+C - skopiuj zaznaczone znaki
Ctrl+X - wytnij zaznaczone znaki
Ctrl+V - wklej do zaznaczonych pozycji

AI (OLLAMA):
• Przycisk "🤖 AI" - menu szybkich akcji
• Przycisk "🔄 Powtórz" - wykonuje ostatni własny prompt natychmiast
• Wielokrotne zaznaczenie (Ctrl+Klik): AI zbiera tekst ze wszystkich zaznaczonych miejsc i odpowiada pod ostatnim z nich (wygodne przy uzupełnianiu wielu fragmentów).
• Ctrl+Shift+X - natychmiastowe przerwanie pracy AI

SPIS TREŚCI:
Przycisk "Spis treści" - otwiera okno nawigacji
Dodaj element - tytuł (max 95 znaków) + numer linii + kolor
Kolory przycisków: żółty, zielony, niebieski
Kliknij przycisk z numerem - przejdź do linii
Zapisz/Wczytaj - automatycznie dla każdego pliku
× - usuń element ze spisu treści

MENU:
Pliki → Otwórz, Zapisz, Szybki zapis (F5), Zakończ
Edycja → Cofnij, Ponów, Ustawienia Ollama
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
/ollama(model):zadanie:zakres - AI transform (zakres: 0, sel, 10-20)

PRZYCISKI:
• Czyść - usuwa formatowanie z wybranych linii
• Puste linie - wypełnia puste linie tekstem
• Linijka - pomoc w czytaniu z nawigacją strzałkami
• 🤖 AI - menu szybkich akcji sztucznej inteligencji (Ollama)
• 🔄 Powtórz - powtarza ostatni prompt AI

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
- Pasek statusu pokazuje aktywny model AI
- Paski komend i przycisków są zawsze widoczne
"""

        help_window = tk.Toplevel(self.root)
        help_window.withdraw()
        help_window.title("Instrukcja - TekstDyrygent")
        help_window.transient(self.root)
        self.center_window(help_window, 50, 75)

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
                 
        help_window.deiconify()

    # toggle_notifications
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

    # update_notifications_button
    def update_notifications_button(self):
        """Aktualizuje wygląd przycisku powiadomień"""
        if self.notifications_enabled:
            self.notifications_button.config(text="🔔", bg="lightgreen",
                                            relief=tk.RAISED)
        else:
            self.notifications_button.config(text="🔕", bg="lightgray",
                                            relief=tk.FLAT)

    # update_status
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

        # Aktualizuj pasek statusu (nie nadpisuj gdy AI pracuje)
        if not getattr(self, '_ollama_working', False):
            model_info = f" | AI: {self.ollama_model}" if hasattr(self, 'ollama_model') else ""
            self.status_bar.config(
                text=f"Znaków: {total_chars} | Rozmiar: {size_str} | Linia: {line} | Kolumna: {int(column)+1} | Zaznaczenie: {selected_chars} | Czas: {time_str}{speed_str}{model_info}"
            )

        # Aktualizacja duplikatów z opóźnieniem
        if self.show_duplicates:
            self.root.after(200, self.highlight_duplicates)  # Zwiększone opóźnienie dla lepszej wydajności

