from pathlib import Path
import re

print("\n=== 1) Arquivos com body/base_layout/content/admin-page ===")
for p in Path("app").rglob("*.py"):
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if any(x in txt for x in ["<body", "base_layout", "admin-page", "content"]):
        print("\n---", p, "---")
        for i, line in enumerate(txt.splitlines(), 1):
            if any(x in line for x in ["<body", "base_layout", "admin-page", "content"]):
                print(f"{i}: {line[:220]}")

print("\n=== 2) Rotas de Clientes/Auditoria ===")
for p in Path("app").rglob("*.py"):
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if "audit" in txt.lower() or "clientes" in txt.lower() or "client" in txt.lower():
        print("\n---", p, "---")
        for i, line in enumerate(txt.splitlines(), 1):
            low = line.lower()
            if "@app.route" in line or "audit" in low or "clientes" in low or "client-card" in low:
                print(f"{i}: {line[:220]}")

print("\n=== 3) CSS carregado no HTML ===")
for p in Path("app").rglob("*.py"):
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if "style.css" in txt or "url_for('static'" in txt or 'url_for("static"' in txt:
        print("\n---", p, "---")
        for i, line in enumerate(txt.splitlines(), 1):
            if "style.css" in line or "static" in line:
                print(f"{i}: {line[:220]}")

print("\n=== 4) Inline color escuro em páginas administrativas ===")
for p in Path("app").rglob("*.py"):
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if "color:#111827" in txt or "color: #111827" in txt or "color:#0" in txt:
        print("\n---", p, "---")
        for i, line in enumerate(txt.splitlines(), 1):
            if "color:#111827" in line or "color: #111827" in line or "color:#0" in line:
                print(f"{i}: {line[:220]}")

print("\n=== 5) Últimos patches no CSS ===")
css = Path("app/static/style.css")
if css.exists():
    lines = css.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines[-160:], max(1, len(lines)-159)):
        print(f"{i}: {line}")
