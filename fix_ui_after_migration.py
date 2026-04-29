from pathlib import Path
import re
from datetime import datetime

ROOT = Path(".")
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")

def backup(path: Path):
    if path.exists():
        bkp = path.with_suffix(path.suffix + f".bak_{STAMP}")
        bkp.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"BACKUP: {path} -> {bkp}")

def write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")
    print(f"UPDATED: {path}")

# 1) Fix server.py home error: NameError message undefined
server = ROOT / "app/server.py"
backup(server)
txt = server.read_text(encoding="utf-8")

# Insere fallback seguro antes de return f""" que usa {message}, se ainda não houver message definido na função home
pattern = r'(@app\.route\(["\']\/["\']\)\s*\ndef\s+home\s*\([^)]*\):\s*)'
if "def home" in txt and "{message}" in txt:
    def repl(m):
        block_start = m.group(1)
        return block_start + '\n    message = "Bem-vindo ao sistema"\n'
    txt = re.sub(pattern, repl, txt, count=1)

# Alternativa extra: se ainda houver referência solta problemática, não quebra
txt = txt.replace("<p>{message}</p>", "<p>{message if 'message' in locals() else 'Bem-vindo ao sistema'}</p>")

write(server, txt)

# 2) CSS final patch
css_path = ROOT / "app/static/style.css"
backup(css_path)
css = css_path.read_text(encoding="utf-8")

patch = r'''

/* =========================================================
   POST-MIGRATION UI FIX — contrast, admin/client pages, forms
   Added safely after migration.
   ========================================================= */

/* Admin / Clientes / Auditoria: cards escuros precisam de texto claro */
body.admin-page .content .card,
body.admin-page .content .client-card,
.content .admin-card-dark,
.content .audit-card-dark {
    background: #111827 !important;
    border: 1px solid #243044 !important;
    color: #f8fafc !important;
}

body.admin-page .content .card *,
body.admin-page .content .client-card *,
.content .admin-card-dark *,
.content .audit-card-dark * {
    color: #f8fafc !important;
}

body.admin-page .content .card p,
body.admin-page .content .client-card p,
body.admin-page .content .card small,
body.admin-page .content .client-card small,
body.admin-page .content .card .muted,
body.admin-page .content .client-card .muted,
.content .audit-card-dark .muted,
.content .admin-card-dark .muted {
    color: #cbd5e1 !important;
}

body.admin-page .content .card th,
body.admin-page .content .client-card th,
body.admin-page .content .card .eyebrow,
body.admin-page .content .client-card .eyebrow,
.content .audit-card-dark th,
.content .admin-card-dark th {
    color: #facc15 !important;
    font-weight: 900 !important;
}

/* Tabelas de admin/auditoria */
body.admin-page .content table td,
body.admin-page .content table td *,
body.admin-page .content table tr,
.content .audit-card-dark table td,
.content .audit-card-dark table td * {
    color: #f8fafc !important;
}

body.admin-page .content table {
    background: transparent !important;
}

body.admin-page .content table td,
body.admin-page .content table th {
    border-color: #243044 !important;
}

/* Inputs em cards escuros */
body.admin-page .content .card input,
body.admin-page .content .card select,
body.admin-page .content .card textarea,
body.admin-page .content .client-card input,
body.admin-page .content .client-card select,
body.admin-page .content .client-card textarea {
    background: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #334155 !important;
}

body.admin-page .content .card input::placeholder,
body.admin-page .content .card textarea::placeholder,
body.admin-page .content .client-card input::placeholder,
body.admin-page .content .client-card textarea::placeholder {
    color: #94a3b8 !important;
}

/* Botões dentro de forms: alinhamento consistente */
.worklog-page form button,
.worklog-page form .btn,
.worklog-page form a.btn,
.worklog-page form a[role="button"],
body.admin-page form button,
body.admin-page form .btn,
body.admin-page form a.btn {
    min-height: 40px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    vertical-align: middle !important;
    line-height: 1 !important;
    margin-top: 0 !important;
}

/* Worklog continua claro */
body:not(.admin-page) .content .worklog-page,
body:not(.admin-page) .content .worklog-page .card,
body:not(.admin-page) .content .worklog-page .worklog-card {
    color: #111827 !important;
}

body:not(.admin-page) .content .worklog-page .card {
    background: #ffffff !important;
    border-color: #e5e7eb !important;
}

body:not(.admin-page) .content .worklog-page h1,
body:not(.admin-page) .content .worklog-page h2,
body:not(.admin-page) .content .worklog-page h3,
body:not(.admin-page) .content .worklog-page label,
body:not(.admin-page) .content .worklog-page td,
body:not(.admin-page) .content .worklog-page th,
body:not(.admin-page) .content .worklog-page strong {
    color: #111827 !important;
}

body:not(.admin-page) .content .worklog-page p,
body:not(.admin-page) .content .worklog-page .muted,
body:not(.admin-page) .content .worklog-page .subtitle {
    color: #667085 !important;
}

body:not(.admin-page) .content .worklog-page input,
body:not(.admin-page) .content .worklog-page select,
body:not(.admin-page) .content .worklog-page textarea {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #d0d5dd !important;
}

/* Corrige botões desalinhados em grids de filtro */
.worklog-page form div[style*="align-items:start"],
.worklog-page form div[style*="align-items:end"] {
    align-items: end !important;
}

.worklog-page form a {
    text-decoration: none !important;
}
'''

if "POST-MIGRATION UI FIX" not in css:
    css += patch

write(css_path, css)

# 3) Worklog templates: remove top:-8px do botão Adicionar
for rel in [
    "app/templates/worklog/registro_horas.html",
    "app/templates/worklog/daily_history.html",
    "app/templates/worklog/worklog_history.html",
]:
    p = ROOT / rel
    if p.exists():
        backup(p)
        t = p.read_text(encoding="utf-8")
        t = t.replace("position:relative; top:-8px;", "")
        t = t.replace("align-items:start;", "align-items:end;")
        t = t.replace("height:100%;", "")
        write(p, t)

print("\nPatch concluído.")
