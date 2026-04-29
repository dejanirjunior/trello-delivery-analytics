from pathlib import Path
from datetime import datetime
import subprocess

server = Path("app/server.py")
content = server.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/server.py.bak_before_audit_css_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

marker = "/* === OPTARIS AUDIT DARK BLOCK FIX === */"

patch = r"""
        /* === OPTARIS AUDIT DARK BLOCK FIX === */
        body.admin-page .content [style*="background:#111827"],
        body.admin-page .content [style*="background: #111827"],
        body.admin-page .content [style*="background:#0f172a"],
        body.admin-page .content [style*="background: #0f172a"],
        body.admin-page .content [style*="background:var(--surface)"],
        body.admin-page .content [style*="background: var(--surface)"] {
            color: #f8fafc !important;
        }

        body.admin-page .content [style*="background:#111827"] *,
        body.admin-page .content [style*="background: #111827"] *,
        body.admin-page .content [style*="background:#0f172a"] *,
        body.admin-page .content [style*="background: #0f172a"] *,
        body.admin-page .content [style*="background:var(--surface)"] *,
        body.admin-page .content [style*="background: var(--surface)"] * {
            color: #f8fafc !important;
        }

        body.admin-page .content [style*="background:#111827"] th,
        body.admin-page .content [style*="background: #111827"] th,
        body.admin-page .content [style*="background:#0f172a"] th,
        body.admin-page .content [style*="background: #0f172a"] th,
        body.admin-page .content [style*="background:var(--surface)"] th,
        body.admin-page .content [style*="background: var(--surface)"] th {
            color: #facc15 !important;
        }

        body.admin-page .content [style*="background:#111827"] input,
        body.admin-page .content [style*="background:#111827"] select,
        body.admin-page .content [style*="background:#111827"] textarea,
        body.admin-page .content [style*="background: #111827"] input,
        body.admin-page .content [style*="background: #111827"] select,
        body.admin-page .content [style*="background: #111827"] textarea {
            background: #1e293b !important;
            color: #ffffff !important;
            border-color: #334155 !important;
        }

        body.admin-page .content [style*="background:#111827"] input::placeholder,
        body.admin-page .content [style*="background: #111827"] input::placeholder {
            color: #94a3b8 !important;
        }
"""

if marker in content:
    print("Patch já existe no server.py. Nenhuma alteração.")
    raise SystemExit(0)

idx = content.find("</style>")
if idx == -1:
    raise SystemExit("ERRO: não encontrei </style> no base_layout/server.py")

new_content = content[:idx] + "\n" + patch + "\n" + content[idx:]
server.write_text(new_content, encoding="utf-8")

check = subprocess.run(["python3", "-m", "py_compile", str(server)], capture_output=True, text=True)

if check.returncode != 0:
    server.write_text(content, encoding="utf-8")
    print("ERRO: server.py ficou inválido. Rollback aplicado.")
    print(check.stderr)
    raise SystemExit(1)

print("OK: CSS da Auditoria injetado no CSS embutido do base_layout.")
