from pathlib import Path
from datetime import datetime

file = Path("app/templates/worklog/daily_history.html")
content = file.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"{file}.bak_dark_fix_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

# remove fundo branco e borda clara
content = content.replace("background:#ffffff;", "")
content = content.replace("border:1px solid #d0d5dd;", "")

# mantém height, remove excesso
content = content.replace(
    'style="width:100%; height:40px; color:#111827; ; border-radius:8px;"',
    'style="width:100%; height:40px;"'
)

# caso geral (mais seguro)
content = content.replace(
    'style="width:100%; height:40px; color:#111827;  border-radius:8px;"',
    'style="width:100%; height:40px;"'
)

file.write_text(content, encoding="utf-8")

print("OK: inputs da Daily History agora seguem o padrão dark do sistema.")
