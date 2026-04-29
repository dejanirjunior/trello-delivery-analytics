from pathlib import Path
import re

targets = [
    Path("app/generate_pm_view.py"),
    Path("app/server.py"),
]

for path in targets:
    print("\n" + "="*80)
    print(path)
    print("="*80)

    if not path.exists():
        print("Arquivo não encontrado")
        continue

    text = path.read_text(encoding="utf-8", errors="ignore")

    for term in ["fetch(", "/trello/update", "Erro na atualização", "Erro desconhecido", "success", "status", "message", "error"]:
        if term in text:
            print(f"\n--- Ocorrências de: {term} ---")
            lines = text.splitlines()
            for i, line in enumerate(lines, start=1):
                if term in line:
                    start = max(1, i-4)
                    end = min(len(lines), i+6)
                    for n in range(start, end+1):
                        print(f"{n}: {lines[n-1]}")
                    print("-"*40)
