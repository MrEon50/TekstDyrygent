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

class CommandsMixin:
    # cmd_alphabetical_sort
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

    # cmd_change
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

    # cmd_clean_empty_lines
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

    # cmd_column_select
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

    # cmd_count_text
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

    # cmd_cut_lines
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

    # cmd_delete
    def cmd_delete(self, command):
        # /del(0):słowo - usuwa wszystkie wystąpienia słowa
        match = re.match(r'/del\((\d+)\):(.+)', command)
        if match:
            word = match.group(2)
            text = self.text_area.get('1.0', tk.END)
            new_text = text.replace(word, '')
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', new_text)

    # cmd_indent
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

    # cmd_ollama
    def cmd_ollama(self, command):
        """
        /ollama(model):prompt:zakres
        Zakres: 0 (całość), sel (zaznaczenie), 10-20 (linie)
        """
        match = re.match(r'/ollama\(([^)]+)\):(.+)', command)
        if match:
            model_name = match.group(1)
            rest = match.group(2)
            
            # Spróbuj wyłuskać zakres z końca (ostatni dwukropek)
            parts = rest.rsplit(':', 1)
            range_val = 'sel' # Domyślnie zaznaczenie
            prompt = rest

            if len(parts) == 2:
                if parts[1] in ['0', 'sel'] or re.match(r'\d+-\d+', parts[1]):
                    prompt = parts[0]
                    range_val = parts[1]
                
            # Zapamiętaj stary model i ustaw nowy dla tej komendy
            old_model = self.ollama_model
            self.ollama_model = model_name
            self.update_status()
            
            # Pobierz tekst do przetworzenia
            text_to_process = ""
            target_start = None
            target_end = None

            if range_val == '0':
                text_to_process = self.text_area.get("1.0", tk.END).strip()
                target_start, target_end = "1.0", tk.END
            elif range_val == 'sel':
                try:
                    text_to_process = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                    target_start, target_end = tk.SEL_FIRST, tk.SEL_LAST
                except:
                    text_to_process = self.text_area.get("1.0", tk.END).strip()
                    target_start, target_end = "1.0", tk.END
            elif '-' in range_val:
                try:
                    start, end = map(int, range_val.split('-'))
                    text_to_process = self.text_area.get(f"{start}.0", f"{end}.end")
                    target_start, target_end = f"{start}.0", f"{end}.end"
                except:
                    messagebox.showerror("Błąd", "Nieprawidłowy zakres linii")
                    return

            if not text_to_process:
                messagebox.showwarning("AI", "Brak tekstu w podanym zakresie")
                return

            old_status = self.status_bar.cget("text")
            self.status_bar.config(text="🤖 AI (komenda) generuje... Proszę czekać.", fg="blue")

            def restore_cmd_status():
                """Przywróć status bar i model przy błędzie"""
                self.status_bar.config(text=old_status, fg="black")
                self.ollama_model = old_model
                self.update_status()

            def handle_cmd_response(response):
                self.status_bar.config(text=old_status, fg="black")
                # Wstawianie wyniku
                if target_start and target_end:
                    if range_val == 'sel':
                        # Specyfika usuwania zaznaczenia
                        try:
                            self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
                            self.text_area.insert(tk.INSERT, response)
                        except:
                            self.text_area.delete("1.0", tk.END)
                            self.text_area.insert("1.0", response)
                    else:
                        self.text_area.delete(target_start, target_end)
                        self.text_area.insert(target_start, response)
                
                # Przywróć model
                self.ollama_model = old_model
                self.update_status()
                messagebox.showinfo("AI", f"Komenda AI wykonana (model: {model_name})")

            self.call_ollama(prompt, text_to_process, lambda t: None, handle_cmd_response, on_error=restore_cmd_status)
        else:
            messagebox.showerror("Błąd", "Użyj: /ollama(model):prompt:zakres\nZakresy: 0, sel, 10-20")

    # cmd_remove_lines
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

    # cmd_spaces
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

    # cmd_swap_lines
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

    # execute_command
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

    # execute_single_command
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
        elif command.startswith('/ollama('): # OLLAMA AI
            self.cmd_ollama(command)
        else:
            messagebox.showwarning("Błąd", f"Nieznana komenda: {command}")

