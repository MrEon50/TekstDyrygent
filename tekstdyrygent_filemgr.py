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

class FileMgrMixin:
    # get_available_fonts
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

    # load_user_settings
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

    # open_file
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            content = None
            for encoding in ['utf-8', 'cp1250', 'iso-8859-2', 'windows-1250']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is not None:
                try:
                    self.text_area.delete('1.0', tk.END)
                    self.text_area.insert('1.0', content)
                    self.current_file = file_path  # Ustaw aktualny plik
                    self.root.title(f"TekstDyrygent - {file_path}")
                    messagebox.showinfo("Sukces", "Plik wczytany pomyślnie")
                except Exception as e:
                    messagebox.showerror("Błąd", f"Błąd interfejsu przy wczytywaniu: {e}")
            else:
                messagebox.showerror("Błąd", "Nie można otworzyć pliku: nieznane kodowanie lub plik uszkodzony.")

    # open_formatted
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

    # quick_save
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

    # restore_default_settings
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

    # save_file
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

    # save_formatted
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

    # save_settings
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

