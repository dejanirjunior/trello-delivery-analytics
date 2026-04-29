from pathlib import Path
from datetime import datetime

file = Path("app/templates/worklog/daily_history.html")
content = file.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"{file}.bak_wrapper_class_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

old = '<div style="max-width:1080px; margin:0 auto; color:#111827;">'
new = '<div class="worklog-page" style="max-width:1080px; margin:0 auto; color:#111827;">'

if old not in content:
    print("Wrapper original não encontrado. Nenhuma alteração aplicada.")
else:
    content = content.replace(old, new, 1)
    file.write_text(content, encoding="utf-8")
    print("OK: daily_history agora usa class worklog-page.")
