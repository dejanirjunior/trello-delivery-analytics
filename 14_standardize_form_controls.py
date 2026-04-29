from pathlib import Path
from datetime import datetime

css = Path("app/static/style.css")

content = css.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/static/style.css.bak_form_controls_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

marker = "OPTARIS FORM CONTROLS STANDARD"

patch = """

/* === OPTARIS FORM CONTROLS STANDARD === */

/* PADRÃO GLOBAL */
input,
select,
button {
    height: 42px;
    box-sizing: border-box;
}

/* BOTÕES */
button,
.btn,
a.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 16px;
    font-weight: 700;
    line-height: normal;
}

/* INPUTS */
input,
select {
    padding: 0 12px;
}

/* GRID DE FILTROS */
.card form > div[style*="grid"],
.card > div[style*="grid"] {
    align-items: end !important;
}

/* FLEX DE BOTÕES */
div[style*="display:flex"] {
    align-items: end !important;
}

"""

if marker in content:
    print("Já aplicado.")
else:
    css.write_text(content + "\n" + patch, encoding="utf-8")
    print("Patch aplicado.")

