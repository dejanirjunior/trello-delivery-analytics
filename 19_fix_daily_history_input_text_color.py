from pathlib import Path
from datetime import datetime

css = Path("app/static/style.css")
content = css.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/static/style.css.bak_daily_history_text_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

marker = "OPTARIS DAILY HISTORY INPUT TEXT FIX"

patch = """

/* === OPTARIS DAILY HISTORY INPUT TEXT FIX === */
.worklog-page select,
.worklog-page input[type="date"] {
    color: #ffffff !important;
}

.worklog-page select option {
    background: #1e293b !important;
    color: #ffffff !important;
}

.worklog-page input[type="date"]::-webkit-datetime-edit,
.worklog-page input[type="date"]::-webkit-datetime-edit-fields-wrapper,
.worklog-page input[type="date"]::-webkit-datetime-edit-text,
.worklog-page input[type="date"]::-webkit-datetime-edit-month-field,
.worklog-page input[type="date"]::-webkit-datetime-edit-day-field,
.worklog-page input[type="date"]::-webkit-datetime-edit-year-field {
    color: #ffffff !important;
}

.worklog-page input[type="date"]::-webkit-calendar-picker-indicator {
    filter: invert(1);
}

"""

if marker in content:
    print("Patch já existe.")
else:
    css.write_text(content + "\n" + patch, encoding="utf-8")
    print("Patch aplicado.")
