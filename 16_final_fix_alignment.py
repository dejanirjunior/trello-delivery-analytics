from pathlib import Path
from datetime import datetime

css = Path("app/static/style.css")
content = css.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/static/style.css.bak_FINAL_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

marker = "OPTARIS FINAL ALIGN FIX"

patch = """

/* === OPTARIS FINAL ALIGN FIX === */

/* FORÇA PADRÃO REAL */
input,
select,
button,
a[style*="background"] {
    height: 40px !important;
    box-sizing: border-box !important;
}

/* BOTÕES (TODOS IGUAIS) */
button,
a[style*="background"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 14px !important;
    line-height: normal !important;
}

/* INPUTS */
input,
select {
    padding: 0 10px !important;
}

/* GRID CORRETO */
div[style*="grid-template-columns"] {
    align-items: end !important;
}

/* FLEX CORRETO */
div[style*="display:flex"] {
    align-items: end !important;
}

/* REMOVE DIFERENÇAS ENTRE <a> E <button> */
a[style*="background"] {
    text-decoration: none !important;
}

/* GARANTE ALINHAMENTO EM TODOS OS FILTROS */
form div {
    align-items: end !important;
}

"""

if marker in content:
    print("Já aplicado.")
else:
    css.write_text(content + "\n" + patch, encoding="utf-8")
    print("Patch FINAL aplicado.")

