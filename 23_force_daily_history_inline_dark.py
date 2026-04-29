from pathlib import Path
from datetime import datetime

file = Path("app/templates/worklog/daily_history.html")
content = file.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"{file}.bak_force_inline_dark_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

content = content.replace(
    'select name="developer_name" style="width:100%; height:40px; color:#111827;   border-radius:8px;"',
    'select name="developer_name" style="width:100%; height:40px; color:#ffffff; background:#1e293b; border:1px solid #334155; border-radius:8px; color-scheme:dark;"'
)

content = content.replace(
    'input type="date" name="start_date" value="{{ start_date }}" style="width:100%; height:40px; color:#111827;   border-radius:8px;"',
    'input type="date" name="start_date" value="{{ start_date }}" style="width:100%; height:40px; color:#ffffff; background:#1e293b; border:1px solid #334155; border-radius:8px; color-scheme:dark;"'
)

content = content.replace(
    'input type="date" name="end_date" value="{{ end_date }}" style="width:100%; height:40px; color:#111827;   border-radius:8px;"',
    'input type="date" name="end_date" value="{{ end_date }}" style="width:100%; height:40px; color:#ffffff; background:#1e293b; border:1px solid #334155; border-radius:8px; color-scheme:dark;"'
)

content = content.replace(
    'div style="height:40px; display:flex; align-items:center; background:#f9fafb;  border-radius:8px; padding:0 10px; color:#111827;"',
    'div style="height:40px; display:flex; align-items:center; background:#1e293b; border:1px solid #334155; border-radius:8px; padding:0 10px; color:#ffffff;"'
)

file.write_text(content, encoding="utf-8")

print("Depois da alteração:")
for i, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
    if "developer_name" in line or "start_date" in line or "end_date" in line:
        print(f"{i}: {line}")
