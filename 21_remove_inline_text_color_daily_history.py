from pathlib import Path
from datetime import datetime

file = Path("app/templates/worklog/daily_history.html")
content = file.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"{file}.bak_remove_color_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

# remove TODOS os color:#111827 inline
content = content.replace("color:#111827;", "")
content = content.replace("color:#111827", "")

# remove também alguns tons que podem quebrar contraste
content = content.replace("color:#344054;", "")
content = content.replace("color:#344054", "")

file.write_text(content, encoding="utf-8")

print("OK: cores inline removidas do daily_history.")
