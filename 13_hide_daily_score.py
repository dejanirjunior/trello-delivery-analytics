from pathlib import Path
from datetime import datetime
import subprocess

template = Path("app/templates/worklog/daily.html")

content = template.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/templates/worklog/daily.html.bak_hide_score_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

old = "Score {{ card.score }} · {{ card.reason_text }}"
new = "{{ card.reason_text }}"

if old not in content:
    print("Trecho exato do Score não encontrado. Nenhuma alteração aplicada.")
    raise SystemExit(0)

content = content.replace(old, new)

template.write_text(content, encoding="utf-8")

# valida se o template ainda existe e se o server compila
check = subprocess.run(
    ["python3", "-m", "py_compile", "app/server.py"],
    capture_output=True,
    text=True
)

if check.returncode != 0:
    template.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    print("ERRO: server.py inválido. Rollback aplicado.")
    print(check.stderr)
    raise SystemExit(1)

print("OK: Score removido apenas da exibição da Daily.")
