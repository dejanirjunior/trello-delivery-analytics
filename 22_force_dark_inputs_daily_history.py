from pathlib import Path
from datetime import datetime

css = Path("app/static/style.css")
content = css.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/static/style.css.bak_force_dark_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

marker = "OPTARIS FORCE DARK INPUTS"

patch = """

/* === OPTARIS FORCE DARK INPUTS === */

/* força modo dark nativo do browser */
.worklog-page input[type="date"],
.worklog-page select {
    color-scheme: dark;
    background: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #334155 !important;
}

/* texto interno do date */
.worklog-page input[type="date"]::-webkit-datetime-edit {
    color: #ffffff !important;
}

/* ícone do calendário */
.worklog-page input[type="date"]::-webkit-calendar-picker-indicator {
    filter: invert(1);
}

/* select dropdown */
.worklog-page select option {
    background: #1e293b;
    color: #ffffff;
}

"""

if marker in content:
    print("Já aplicado.")
else:
    css.write_text(content + "\n" + patch, encoding="utf-8")
    print("Patch aplicado.")

