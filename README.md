# 🎵 TekstDyrygent - Zaawansowany Notatnik AI

**TekstDyrygent** to potężny, modularny edytor tekstu napisany w Pythonie (Tkinter), zaprojektowany z myślą o efektywnej pracy z tekstem, zaawansowanym formatowaniu oraz lokalnej integracji ze sztuczną inteligencją (Ollama).

## 🚀 Główne Funkcje

### 📝 Edycja i Formatowanie
*   **Wielokolorowe formatowanie**: Szybkie kolorowanie zaznaczonego tekstu (żółty, czerwony, niebieski, zielony, fioletowy).
*   **Zarządzanie fontami**: Obsługa fontów systemowych oraz ładowanie własnych z folderu `fonts`.
*   **Czyszczenie formatowania**: Usuwanie stylów z wybranych linii lub całego dokumentu.
*   **Puste linie**: Automatyczne wypełnianie pustych linii zadanym tekstem.

### 🖱️ Zaawansowane Zaznaczanie
*   **Zaznaczanie kolumnowe (prostokątne)**: `Alt + mysz` lub komendy `/col`.
*   **Edycja kolumnowa**: Usuwanie, kopiowanie i wklejanie tekstu w pionowych blokach.
*   **Wielokrotne zaznaczanie**: `Ctrl + Shift + Klik` do zaznaczania wielu słów naraz.
*   **Zaznaczanie duplikatów**: `Ctrl + Double Click` zaznacza wszystkie wystąpienia danego słowa.

### 🤖 Integracja AI (Ollama)
Program łączy się lokalnie z serwerem **Ollama**, oferując:
*   **Streaming (Real-time)**: Odpowiedzi AI pojawiają się w edytorze w czasie rzeczywistym (znak po znaku).
*   **AI Transform**: Szybkie akcje (Podsumuj, Popraw błędy, Rozwiń, Parafrazuj, Tłumacz na dowolny język).
*   **Zaznaczenie jako Prompt**: `Ctrl + Shift + M` wysyła zaznaczony tekst jako polecenie bezpośrednio do modelu.
*   **Custom Prompt**: `Ctrl + Shift + O` pozwala na wpisanie własnego zapytania z uwzględnieniem kontekstu zaznaczenia.
*   **Anulowanie (Safety)**: `Ctrl + Shift + X` pozwala natychmiast przerwać generowanie tekstu przez AI.
*   **System Prompt**: Możliwość zdefiniowania stałej instrukcji dla AI (np. "Odpowiadaj tylko po polsku" lub "Bądź kreatywnym asystentem"), która nadaje modelowi charakter.
*   **Kontrola nad zaznaczeniem**: Opcja wyboru, czy odpowiedź AI ma zastąpić zaznaczony tekst, czy zostać dopisana pod spodem (z czytelnym separatorem).
*   **Optymalizacja wydajności**: Możliwość ustawienia `num_ctx` (rozmiar kontekstu) oraz `keep_alive` (utrzymywanie modelu w pamięci RAM/VRAM) dla błyskawicznych odpowiedzi.
*   **Pasek statusu**: Wyświetla czas generowania oraz aktualny stan (Ładowanie modelu / Generowanie / Gotowe).

### 🛠️ Narzędzia i Analiza
*   **Spis Treści (TOC)**: Dynamiczna nawigacja po dokumencie (zapisywana automatycznie w plikach `.tdyf`).
*   **Raport Tekstowy**: Szczegółowe statystyki (liczba słów, znaków, najczęstsze słowa, unikalne słowa).
*   **Analiza duplikatów**: Podświetlanie powtarzających się fragmentów tekstu w czasie rzeczywistym.
*   **Linijka do czytania**: Wizualna pomoc ułatwiająca czytanie długich tekstów linia po linii.
*   **Powiadomienia o limitach**: Ostrzeżenia o czasie pracy, liczbie linii lub rozmiarze pliku.

## ⌨️ Skróty Klawiszowe

| Skrót | Akcja |
| :--- | :--- |
| **Ctrl + F** | Pogrubienie zaznaczenia |
| **Ctrl + Y / R / B / G / P** | Kolorowanie (Żółty, Czerwony, Niebieski, Zielony, Fioletowy) |
| **Ctrl + 0** | Usuń formatowanie |
| **Ctrl + Alt + F** | Pogrubienie całego tekstu |
| **Ctrl + Shift + O** | **AI Custom Prompt** (z kontekstem) |
| **Ctrl + Shift + M** | **Zaznaczenie jako prompt** (wynik poniżej) |
| **Ctrl + Shift + X** | **Anuluj generowanie AI** (natychmiastowe przerwanie) |
| **Ctrl + D / Delete** | Usuń bieżącą linię |
| **F5** | Szybki zapis |
| **Ctrl + Z / Ctrl + Shift + Y** | Cofnij / Ponów (50 kroków) |
| **Ctrl + Q** | Przeskok na początek dokumentu |
| **Alt + Mysz** | Zaznaczanie kolumnowe |

## 💻 Komendy Terminala

Wpisuj komendy w dolnym pasku "Komenda:":

*   `/ollama(model):zadanie:zakres` – Wywołanie AI (zakresy: `0`-całość, `sel`-zaznaczenie, `10-20`-linie).
*   `/alf(n)` – Sortowanie alfabetyczne linii z `n` spacjami na początku.
*   `/rln(tekst)` – Usuwanie wszystkich linii zawierających `tekst`.
*   `/cha(nowe):stare` – Zamiana tekstu.
*   `/del(0):słowo` – Usuwanie wszystkich wystąpień słowa.
*   `/spc(1):3` – Zamiana potrójnych spacji na pojedyncze.
*   `/cnt(tekst)` – Zliczanie wystąpień tekstu.
*   `/swp(1):5` – Zamiana miejscami linii 1 i 5.

## 🏗️ Architektura

Projekt jest oparty na wzorcu **Mixin**, co pozwala na łatwe rozszerzanie funkcjonalności bez tworzenia monolitycznego kodu:
*   `tekstdyrygent.py` – Główny punkt wejścia i inicjalizacja.
*   `tekstdyrygent_ui.py` – Interfejs użytkownika i bindowanie skrótów.
*   `tekstdyrygent_ollama.py` – Logika AI i komunikacja z API Ollama.
*   `tekstdyrygent_commands.py` – Parser i logika komend terminala.
*   `tekstdyrygent_toolsfeatures.py` – Zaawansowane narzędzia (linijka, raporty, duplikaty).
*   `tekstdyrygent_filemgr.py` – Obsługa plików, ustawień i fontów.
*   `tekstdyrygent_selection.py` – Obsługa zaawansowanego zaznaczania (kolumnowe, multi-click).

## ⚙️ Wymagania

1.  **Python 3.x**
2.  **Ollama** (opcjonalnie, dla funkcji AI) – musi działać w tle na `localhost:11434`.
3.  Plik `icon.ico` w głównym katalogu (dla ikon okien).

---
*Autor: Fundamentalist90@proton.me*
