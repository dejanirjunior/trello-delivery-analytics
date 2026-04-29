from pathlib import Path
from datetime import datetime
import re

server = Path("app/server.py")

content = server.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/server.py.bak_before_css_fix_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

# procurar bloco <head>
if "style.css" in content:
    print("CSS já parece estar sendo incluído. Nenhuma alteração aplicada.")
    raise SystemExit(0)

# injetar dentro do head
new_content = re.sub(
    r"(<head>.*?</head>)",
    r"""\1
<link rel="stylesheet" href="/static/style.css">
""",
    content,
    flags=re.DOTALL
)

# fallback se não encontrar head corretamente
if new_content == content:
    new_content = content.replace(
        "<head>",
        """<head>
<link rel="stylesheet" href="/static/style.css">
"""
    )

server.write_text(new_content, encoding="utf-8")

print("OK: CSS global injetado no base_layout.")
