from pathlib import Path
from datetime import datetime

css = Path("app/static/style.css")

content = css.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/static/style.css.bak_worklog_align_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

marker = "OPTARIS WORKLOG ALIGNMENT FIX"

patch = """

/* === OPTARIS WORKLOG ALIGNMENT FIX === */

/* Corrige grids dos filtros */
.worklog-page form div[style*="grid-template-columns"] {
    align-items: end !important;
}

/* Padroniza altura de inputs/select */
.worklog-page input,
.worklog-page select {
    height: 40px !important;
    box-sizing: border-box;
}

/* Remove desalinhamento de containers flex */
.worklog-page form div[style*="display:flex"] {
    align-items: end !important;
}

/* Corrige botões */
.worklog-page button,
.worklog-page a[role="button"],
.worklog-page form a {
    height: 40px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: normal !important;
    padding: 0 14px !important;
}

/* Remove hacks antigos */
.worklog-page button[style*="line-height"] {
    line-height: normal !important;
}

/* Corrige grid interno dos cards */
.worklog-fields {
    align-items: end !important;
}

"""

if marker in content:
    print("Patch já aplicado.")
else:
    css.write_text(content + "\n" + patch, encoding="utf-8")
    print("Patch aplicado com sucesso.")

