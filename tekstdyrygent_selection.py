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

class SelectionMixin:
    # clear_column_selection
    def clear_column_selection(self):
        """Usuwa wszystkie tagi zaznaczenia kolumnowego"""
        for tag in self.column_selection_tags:
            self.text_area.tag_delete(tag)
        self.column_selection_tags = []

    # clear_multi_selection
    def clear_multi_selection(self):
        """Usuwa wszystkie tagi wielokrotnego zaznaczania"""
        for tag in self.multi_selection_tags:
            self.text_area.tag_delete(tag)
        self.multi_selection_tags = []

    # clear_right_click_selection
    def clear_right_click_selection(self):
        """Usuwa wszystkie tagi zaznaczenia prawym przyciskiem"""
        for tag in self.right_click_selection_tags:
            self.text_area.tag_delete(tag)
        self.right_click_selection_tags = []

    # column_select_down
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

    # column_select_left
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

    # column_select_right
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

    # column_select_up
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

    # create_column_selection
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

    # ctrl_right_click_select_column
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

    # end_column_selection
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

    # find_duplicates_of_word
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

    # get_column_selection_data
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

    # handle_column_backspace
    def handle_column_backspace(self, event):
        """Obsługuje klawisz Backspace dla zaznaczenia kolumnowego"""
        if self.column_selection_tags:
            return self.handle_column_delete(event)
        return None

    # handle_column_copy
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

    # handle_column_cut
    def handle_column_cut(self, event):
        """Obsługuje Ctrl+X dla zaznaczenia kolumnowego"""
        if self.column_selection_tags:
            # Najpierw skopiuj
            self.handle_column_copy(event)
            # Potem usuń
            self.handle_column_delete(event)
            return "break"
        return None

    # handle_column_delete
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

    # handle_column_paste
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

    # handle_column_type
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

    # multi_select_click
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

    # right_click_select_word
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

    # select_all_same_words
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

    # start_column_selection
    def start_column_selection(self, event):
        """Rozpoczyna zaznaczanie kolumnowe myszą (Alt + klik)"""
        self.column_selection_active = True
        pos = self.text_area.index(f"@{event.x},{event.y}")
        self.column_start_pos = pos
        self.column_end_pos = pos

        # Wyczyść poprzednie zaznaczenie
        self.clear_column_selection()

        return "break"

    # update_column_selection
    def update_column_selection(self, event):
        """Aktualizuje zaznaczenie kolumnowe podczas przeciągania (Alt + przeciągnij)"""
        if self.column_selection_active:
            self.column_end_pos = self.text_area.index(f"@{event.x},{event.y}")
            start_line, start_col = map(int, self.column_start_pos.split("."))
            end_line, end_col = map(int, self.column_end_pos.split("."))
            self.create_column_selection(start_line, start_col, end_line, end_col)

            return "break"

