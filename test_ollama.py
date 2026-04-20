"""
TEST DIAGNOSTYCZNY OLLAMA
Uruchom: python test_ollama.py
Pokaże czy Ollama odpowiada i jak szybko.
"""
import json
import urllib.request
import time

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:e4b"
PROMPT = "Najwyższy szczyt górski w Ameryce Południowej? Odpowiedz krótko."

print(f"=== TEST OLLAMA ===")
print(f"URL:   {OLLAMA_URL}")
print(f"Model: {MODEL}")
print(f"Pytanie: {PROMPT}")
print()

# 1. Sprawdź czy Ollama działa
print("[1] Sprawdzam czy Ollama działa...")
try:
    with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
        data = json.loads(r.read())
        models = [m["name"] for m in data.get("models", [])]
        print(f"    OK! Modele: {models}")
        if MODEL not in models:
            print(f"    UWAGA: model '{MODEL}' NIE jest na liście!")
        else:
            print(f"    Model '{MODEL}' ZNALEZIONY.")
except Exception as e:
    print(f"    BŁĄD: {e}")
    print("    Ollama nie działa lub nie jest uruchomiona!")
    exit(1)

print()

# 2. Test generowania z licznikiem tokenów
print("[2] Wysyłam zapytanie do modelu... (czekaj)")
t0 = time.time()
first_token_time = None
token_count = 0

payload = json.dumps({
    "model": MODEL,
    "prompt": PROMPT,
    "stream": True
}).encode("utf-8")

req = urllib.request.Request(
    f"{OLLAMA_URL}/api/generate",
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        print("    Połączono! Oczekuję na pierwszy token...")
        print("    Odpowiedź: ", end="", flush=True)
        
        while True:
            line = resp.readline()
            if not line:
                break
            try:
                chunk = json.loads(line.decode("utf-8"))
            except Exception:
                continue
            
            if "error" in chunk:
                print(f"\n    BŁĄD OLLAMA: {chunk['error']}")
                break
            
            token = chunk.get("response", "")
            if token:
                if first_token_time is None:
                    first_token_time = time.time()
                    print(f"\n    Czas do pierwszego tokenu: {first_token_time - t0:.1f}s")
                    print("    Odpowiedź: ", end="", flush=True)
                print(token, end="", flush=True)
                token_count += 1
            
            if chunk.get("done", False):
                break

    total = time.time() - t0
    print(f"\n\n    Tokeny: {token_count}")
    print(f"    Czas całkowity: {total:.1f}s")

except Exception as e:
    print(f"\n    BŁĄD: {e}")

print("\n=== KONIEC TESTU ===")
