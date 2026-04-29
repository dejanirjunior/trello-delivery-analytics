from pathlib import Path
from datetime import datetime
import subprocess

server = Path("app/server.py")
content = server.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/server.py.bak_before_embedded_admin_css_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

marker = "OPTARIS EMBEDDED ADMIN CONTRAST FIX"

if marker in content:
    print("Patch já existe. Nenhuma alteração feita.")
    raise SystemExit(0)

patch = """
        /* === OPTARIS EMBEDDED ADMIN CONTRAST FIX === */
        body.admin-page .content .card,
        body.admin-page .content .client-card {{
            background: #111827 !important;
            border: 1px solid #243044 !important;
            color: #f8fafc !important;
        }}

        body.admin-page .content .card h1,
        body.admin-page .content .card h2,
        body.admin-page .content .card h3,
        body.admin-page .content .card h4,
        body.admin-page .content .card p,
        body.admin-page .content .card span,
        body.admin-page .content .card div,
        body.admin-page .content .card label,
        body.admin-page .content .card strong,
        body.admin-page .content .card small,
        body.admin-page .content .card td,
        body.admin-page .content .card li,
        body.admin-page .content .client-card h1,
        body.admin-page .content .client-card h2,
        body.admin-page .content .client-card h3,
        body.admin-page .content .client-card h4,
        body.admin-page .content .client-card p,
        body.admin-page .content .client-card span,
        body.admin-page .content .client-card div,
        body.admin-page .content .client-card label,
        body.admin-page .content .client-card strong,
        body.admin-page .content .client-card small,
        body.admin-page .content .client-card td,
        body.admin-page .content .client-card li {{
            color: #f8fafc !important;
        }}

        body.admin-page .content .card th,
        body.admin-page .content .client-card th,
        body.admin-page .content .card .eyebrow,
        body.admin-page .content .client-card .eyebrow {{
            color: #facc15 !important;
            font-weight: 900 !important;
        }}

        body.admin-page .content .card .muted,
        body.admin-page .content .card .subtitle,
        body.admin-page .content .client-card .muted,
        body.admin-page .content .client-card .subtitle {{
            color: #cbd5e1 !important;
        }}

        body.admin-page .content .card input,
        body.admin-page .content .card select,
        body.admin-page .content .card textarea,
        body.admin-page .content .client-card input,
        body.admin-page .content .client-card select,
        body.admin-page .content .client-card textarea {{
            background: #1e293b !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
        }}

        body.admin-page .content .card input::placeholder,
        body.admin-page .content .card textarea::placeholder {{
            color: #94a3b8 !important;
        }}

        body.admin-page .content .card option,
        body.admin-page .content .client-card option {{
            background: #1e293b !important;
            color: #ffffff !important;
        }}

        body.admin-page .content .card table td,
        body.admin-page .content .card table th,
        body.admin-page .content .client-card table td,
        body.admin-page .content .client-card table th {{
            border-color: #243044 !important;
        }}

        body.admin-page .content .card a:not(.btn),
        body.admin-page .content .client-card a:not(.btn) {{
            color: #93c5fd !important;
        }}
"""

idx = content.find("</style>")
if idx == -1:
    raise SystemExit("ERRO: </style> não encontrado em app/server.py")

new_content = content[:idx] + "\n" + patch + "\n" + content[idx:]
server.write_text(new_content, encoding="utf-8")

check = subprocess.run(
    ["python3", "-m", "py_compile", str(server)],
    capture_output=True,
    text=True
)

if check.returncode != 0:
    server.write_text(content, encoding="utf-8")
    print("ERRO: server.py inválido. Rollback aplicado.")
    print(check.stderr)
    raise SystemExit(1)

print("OK: CSS embutido corrigido com chaves escapadas.")
