from pathlib import Path
from datetime import datetime

files = [
    "app/templates/worklog/registro_horas.html",
    "app/templates/worklog/daily_history.html",
    "app/templates/worklog/worklog_history.html",
]

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

for file_path in files:
    p = Path(file_path)
    content = p.read_text(encoding="utf-8")

    backup = Path(f"{file_path}.bak_refactor_{stamp}")
    backup.write_text(content, encoding="utf-8")

    # remove grid inline problemático
    content = content.replace(
        'style="display:grid;',
        'class="filter-grid" style="'
    )

    # remove align-items bagunçado
    content = content.replace("align-items:end;", "")
    content = content.replace("align-items:flex-end;", "")

    # normaliza containers de botão
    content = content.replace(
        'style="display:flex; gap:8px;',
        'class="filter-actions" style="'
    )

    p.write_text(content, encoding="utf-8")
    print(f"Refatorado: {file_path}")

# agora adiciona CSS correto
css = Path("app/static/style.css")
css_content = css.read_text(encoding="utf-8")

if "FILTER GRID SYSTEM" not in css_content:
    css_patch = """

/* === FILTER GRID SYSTEM === */

.filter-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    align-items: end;
}

.filter-grid input,
.filter-grid select {
    height: 40px;
}

.filter-actions {
    display: flex;
    gap: 8px;
    align-items: end;
}

.filter-actions button,
.filter-actions a {
    height: 40px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

"""
    css.write_text(css_content + css_patch, encoding="utf-8")
    print("CSS aplicado.")

print("OK: refatoração aplicada.")
