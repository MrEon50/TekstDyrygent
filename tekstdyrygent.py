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

from tekstdyrygent_filemgr import FileMgrMixin
from tekstdyrygent_commands import CommandsMixin
from tekstdyrygent_selection import SelectionMixin
from tekstdyrygent_toolsfeatures import ToolsFeaturesMixin
from tekstdyrygent_ui import UIMixin
from tekstdyrygent_ollama import OllamaMixin

class TekstDyrygent(FileMgrMixin, CommandsMixin, SelectionMixin, ToolsFeaturesMixin, UIMixin, OllamaMixin):
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

        # Inicjalizacja Ollama
        self.init_ollama()

        # Wczytaj zapisane ustawienia użytkownika
        self.load_user_settings()

        self.setup_ui()
        self.bind_shortcuts()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TekstDyrygent()
    app.run()
