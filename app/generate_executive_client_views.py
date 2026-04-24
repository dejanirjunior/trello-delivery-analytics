from pathlib import Path
from html import escape
import pandas as pd

from executive_metrics import build_executive_summary, load_data, filter_by_client
from client_config import load_clients


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


STATUS_ORDER = ["Done", "Doing", "Block", "To Do"]
STATUS_LABELS = {
    "Done": "Finalizado",
    "Doing": "Em andamento",
    "Block": "Bloqueado",
    "To Do": "Não iniciado",
}
STATUS_COLORS = {
    "Done": "#3ecf8e",
    "Doing": "#4f8ef7",
    "Block": "#f06565",
    "To Do": "#454f65",
}

MODULE_ORDER = [
    "CRM",
    "Compras",
    "Suprimentos",
    "Contratos",
    "Fornecedor",
    "Orcamento",
    "Sem módulo informado",
]


def slugify_client(client):
    return client.lower().replace(" ", "_")


def safe(value):
    if pd.isna(value):
        return ""
    return escape(str(value))


def split_modules(value):
    if pd.isna(value) or not str(value).strip():
        return ["Sem módulo informado"]
    return [m.strip() for m in str(value).split("|") if m.strip()]


def pct(part, total):
    if not total:
        return 0
    return int((part / total) * 100)


def build_donut_gradient(status):
    total = sum(status.values())
    if total == 0:
        return "#1a2238 0deg 360deg"

    start = 0
    parts = []

    for key in STATUS_ORDER:
        value = status.get(key, 0)
        degrees = (value / total) * 360
        end = start + degrees
        color = STATUS_COLORS[key]
        parts.append(f"{color} {start:.2f}deg {end:.2f}deg")
        start = end

    return ", ".join(parts)


def build_module_data(df):
    rows = []

    for _, row in df.iterrows():
        for module in split_modules(row.get("modulos")):
            rows.append({
                "module": module,
                "status": row.get("status_kanban", "To Do"),
            })

    if not rows:
        return []

    mod_df = pd.DataFrame(rows)

    modules = []
    all_modules = list(MODULE_ORDER)

    for module in sorted(mod_df["module"].dropna().unique()):
        if module not in all_modules:
            all_modules.append(module)

    for module in all_modules:
        subset = mod_df[mod_df["module"] == module]
        if subset.empty:
            continue

        total = len(subset)
        done = len(subset[subset["status"] == "Done"])
        doing = len(subset[subset["status"] == "Doing"])
        block = len(subset[subset["status"] == "Block"])
        todo = len(subset[subset["status"] == "To Do"])

        modules.append({
            "name": module,
            "total": total,
            "progress": pct(done, total),
            "done": done,
            "doing": doing,
            "block": block,
            "todo": todo,
        })

    return modules


def render_status_legend(status):
    html = ""

    for key in STATUS_ORDER:
        html += f"""
        <div class="legend-item">
            <div class="legend-dot" style="background:{STATUS_COLORS[key]}"></div>
            <span>{STATUS_LABELS[key]}</span>
            <strong>{status.get(key, 0)}</strong>
        </div>
        """

    return html


def render_module_cards(modules):
    if not modules:
        return '<div class="empty">Sem dados de módulos.</div>'

    html = ""

    for i, module in enumerate(modules, start=1):
        name = safe(module["name"])
        progress = module["progress"]

        accent = "#4f8ef7"
        if name == "Compras":
            accent = "#f0a046"
        elif name == "Orcamento":
            accent = "#3ecf8e"
        elif name == "Contratos":
            accent = "#c9a84c"
        elif name == "Fornecedor":
            accent = "#a78bfa"
        elif name == "Suprimentos":
            accent = "#38bdf8"
        elif name == "Sem módulo informado":
            accent = "#7c8daa"

        html += f"""
        <div class="module-card" style="--accent:{accent}">
            <div class="module-num">Módulo {i}</div>
            <div class="module-name">{name}</div>

            <div class="module-progress">
                <div class="module-progress-top">
                    <span>Progresso</span>
                    <strong>{progress}%</strong>
                </div>
                <div class="mod-bar-track">
                    <div class="mod-bar-fill" style="width:{progress}%"></div>
                </div>
            </div>

            <div class="module-stats">
                <div class="stat-chip"><span style="background:#3ecf8e"></span>{module["done"]} Finalizados</div>
                <div class="stat-chip"><span style="background:#4f8ef7"></span>{module["doing"]} Em andamento</div>
                <div class="stat-chip"><span style="background:#f06565"></span>{module["block"]} Bloqueados</div>
                <div class="stat-chip"><span style="background:#454f65"></span>{module["todo"]} Não iniciados</div>
            </div>
        </div>
        """

    return html


def render_kanban(df):
    html = ""

    for status_key in ["Done", "Doing", "Block", "To Do"]:
        subset = df[df["status_kanban"] == status_key].head(8)
        color = STATUS_COLORS[status_key]
        title = STATUS_LABELS[status_key]
        count = len(df[df["status_kanban"] == status_key])

        cards_html = ""

        if subset.empty:
            cards_html = '<div class="kanban-empty">Sem cards nesta etapa.</div>'
        else:
            for _, row in subset.iterrows():
                module = safe(row.get("modulos", "Sem módulo informado"))
                title_card = safe(row.get("titulo", ""))
                risk = safe(row.get("risk", ""))

                risk_html = f'<span class="mini-risk">Risk: {risk}</span>' if risk else ""

                cards_html += f"""
                <div class="kanban-card">
                    <div class="kanban-card-title">{title_card}</div>
                    <div class="kanban-card-meta">{module}</div>
                    {risk_html}
                </div>
                """

        html += f"""
        <div class="kanban-col">
            <div class="kanban-header">
                <div class="kanban-header-inner">
                    <div class="kanban-dot" style="background:{color}"></div>
                    <div class="kanban-title" style="color:{color}">{title}</div>
                </div>
                <div class="kanban-count">{count}</div>
            </div>
            <div class="kanban-body">
                {cards_html}
            </div>
        </div>
        """

    return html


def render_alerts(summary, df):
    blocked = summary["blocked"]
    high_risk = summary["high_risk"]
    overdue = summary["overdue"]

    sem_modulo = len(df[df["modulos"].astype(str).str.contains("Sem módulo informado", na=False)])

    alerts = [
        {
            "icon": "⛔",
            "title": "Cards bloqueados",
            "desc": f"{len(blocked)} cards estão marcados com BLOCK e exigem acompanhamento.",
            "badge": f"{len(blocked)} bloqueados",
        },
        {
            "icon": "⚠️",
            "title": "Risco alto",
            "desc": f"{len(high_risk)} cards estão sinalizados com risco alto.",
            "badge": f"{len(high_risk)} em risco",
        },
        {
            "icon": "⏰",
            "title": "Prazos vencidos",
            "desc": f"{len(overdue)} cards possuem data vencida e ainda não estão concluídos.",
            "badge": f"{len(overdue)} atrasados",
        },
        {
            "icon": "🧩",
            "title": "Classificação por módulo",
            "desc": f"{sem_modulo} cards ainda estão sem label de módulo.",
            "badge": f"{sem_modulo} sem módulo",
        },
    ]

    html = ""

    for alert in alerts:
        html += f"""
        <div class="alert-card">
            <div class="alert-icon">{alert["icon"]}</div>
            <div>
                <div class="alert-title">{alert["title"]}</div>
                <div class="alert-desc">{alert["desc"]}</div>
                <div class="alert-badge">● {alert["badge"]}</div>
            </div>
        </div>
        """

    return html


def build_html(client):
    summary = build_executive_summary(client)
    df_all = load_data()
    df = filter_by_client(df_all, client)

    total = summary["total_cards"]
    progress = summary["progress"]
    status = summary["status"]
    modules = build_module_data(df)

    donut = build_donut_gradient(status)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe(client)} · Panorama Executivo</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {{
    --bg: #0b0f1a;
    --surface: #131929;
    --surface2: #1a2238;
    --border: rgba(255,255,255,0.08);
    --text: #e8eaf0;
    --muted: #8891a8;
    --gold: #c9a84c;
    --gold-light: #e4c97e;
}}

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: 'DM Sans', sans-serif;
    background:
        radial-gradient(circle at top left, rgba(201,168,76,0.08), transparent 28%),
        radial-gradient(circle at top right, rgba(79,142,247,0.08), transparent 30%),
        #0b0f1a;
    color: var(--text);
    min-height: 100vh;
    font-size: 14px;
    line-height: 1.5;
}}

body::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    opacity: 0.5;
}}

.page {{
    position: relative;
    z-index: 1;
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 32px 80px;
}}

.header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 56px;
    padding-bottom: 32px;
    border-bottom: 1px solid var(--border);
}}

.eyebrow {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: var(--gold);
    text-transform: uppercase;
    margin-bottom: 10px;
}}

.header h1 {{
    font-family: 'DM Serif Display', serif;
    font-size: 44px;
    line-height: 1.05;
}}

.header h1 em {{
    color: var(--gold-light);
}}

.header-sub {{
    color: var(--muted);
    margin-top: 10px;
    font-size: 13px;
}}

.header-date {{
    text-align: right;
    font-size: 12px;
    color: var(--muted);
}}

.header-date strong {{
    display: block;
    font-size: 24px;
    color: var(--text);
}}

.hero {{
    background: linear-gradient(180deg, rgba(19,25,41,0.96), rgba(16,22,36,0.96));
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 38px 42px;
    margin-bottom: 34px;
    display: grid;
    grid-template-columns: 1fr 360px;
    gap: 44px;
    align-items: center;
    box-shadow: 0 24px 80px rgba(0,0,0,0.25);
    position: relative;
    overflow: hidden;
}}

.hero::before {{
    content: '';
    position: absolute;
    top: -90px;
    right: 200px;
    width: 320px;
    height: 320px;
    background: radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%);
}}

.progress-label {{
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--gold);
    font-weight: 700;
    margin-bottom: 8px;
}}

.progress-number {{
    font-family: 'DM Serif Display', serif;
    font-size: 76px;
    line-height: 1;
}}

.progress-number span {{
    font-size: 34px;
    color: var(--muted);
}}

.progress-desc {{
    color: var(--muted);
    font-size: 13px;
    margin-top: 8px;
}}

.bar-track {{
    margin-top: 22px;
    background: var(--surface2);
    border-radius: 100px;
    height: 10px;
    overflow: hidden;
}}

.bar-fill {{
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, var(--gold), var(--gold-light));
}}

.donut-area {{
    display: flex;
    align-items: center;
    gap: 28px;
    position: relative;
    z-index: 1;
}}

.donut {{
    width: 132px;
    height: 132px;
    border-radius: 50%;
    background: conic-gradient({donut});
    display: grid;
    place-items: center;
}}

.donut::after {{
    content: '';
    width: 84px;
    height: 84px;
    background: #131929;
    border-radius: 50%;
    position: absolute;
}}

.donut-center {{
    position: absolute;
    text-align: center;
    z-index: 2;
}}

.donut-center strong {{
    display: block;
    font-family: 'DM Serif Display', serif;
    font-size: 25px;
}}

.donut-center span {{
    font-size: 9px;
    color: var(--muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}

.legend {{
    display: flex;
    flex-direction: column;
    gap: 9px;
    min-width: 170px;
}}

.legend-item {{
    display: grid;
    grid-template-columns: 10px 1fr auto;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--muted);
}}

.legend-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
}}

.legend-item strong {{
    color: var(--text);
}}

.section-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 16px;
    margin-top: 42px;
}}

.modules-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}}

.module-card {{
    background: rgba(19,25,41,0.96);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 28px 24px;
    position: relative;
    overflow: hidden;
}}

.module-card::after {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--accent);
}}

.module-num {{
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 700;
    margin-bottom: 7px;
}}

.module-name {{
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    margin-bottom: 20px;
}}

.module-progress-top {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 7px;
}}

.module-progress-top strong {{
    color: var(--text);
    font-size: 14px;
}}

.mod-bar-track {{
    background: #080b12;
    border-radius: 100px;
    height: 6px;
    overflow: hidden;
}}

.mod-bar-fill {{
    height: 100%;
    background: var(--accent);
    border-radius: 100px;
}}

.module-stats {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 17px;
}}

.stat-chip {{
    display: flex;
    align-items: center;
    gap: 6px;
    background: #0b0f1a;
    border: 1px solid var(--border);
    border-radius: 100px;
    padding: 4px 10px;
    font-size: 11px;
    color: var(--muted);
}}

.stat-chip span {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
}}

.kanban-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
}}

.kanban-col {{
    background: rgba(19,25,41,0.96);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
}}

.kanban-header {{
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.kanban-header-inner {{
    display: flex;
    gap: 8px;
    align-items: center;
}}

.kanban-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
}}

.kanban-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
}}

.kanban-count {{
    background: #0b0f1a;
    border-radius: 100px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 700;
}}

.kanban-body {{
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}}

.kanban-card {{
    background: #0b0f1a;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 11px 12px;
}}

.kanban-card-title {{
    font-size: 12px;
    color: var(--text);
    line-height: 1.35;
}}

.kanban-card-meta {{
    margin-top: 6px;
    font-size: 10px;
    color: var(--gold);
}}

.mini-risk {{
    display: inline-block;
    margin-top: 6px;
    font-size: 10px;
    color: #f06565;
}}

.kanban-empty {{
    font-size: 12px;
    color: var(--muted);
}}

.alerts-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}}

.alert-card {{
    background: rgba(19,25,41,0.96);
    border: 1px solid rgba(240,101,101,0.22);
    border-radius: 16px;
    padding: 20px 22px;
    display: flex;
    gap: 14px;
}}

.alert-icon {{
    width: 38px;
    height: 38px;
    border-radius: 11px;
    background: rgba(240,101,101,0.15);
    display: flex;
    align-items: center;
    justify-content: center;
}}

.alert-title {{
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 4px;
}}

.alert-desc {{
    font-size: 11px;
    color: var(--muted);
}}

.alert-badge {{
    display: inline-flex;
    margin-top: 8px;
    background: rgba(240,101,101,0.15);
    border: 1px solid rgba(240,101,101,0.30);
    color: #f06565;
    border-radius: 100px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}

.footer {{
    margin-top: 58px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #667085;
}}

.empty {{
    color: var(--muted);
}}

@media (max-width: 980px) {{
    .header,
    .hero {{
        grid-template-columns: 1fr;
        display: block;
    }}

    .header-date {{
        text-align: left;
        margin-top: 24px;
    }}

    .modules-grid,
    .kanban-grid,
    .alerts-grid {{
        grid-template-columns: 1fr;
    }}

    .hero {{
        padding: 28px;
    }}
}}
</style>
</head>

<body>
<div class="page">

<header class="header">
    <div>
        <div class="eyebrow">Relatório Executivo · Panorama do Projeto</div>
        <h1>{safe(client)} — <em>Planning</em></h1>
        <div class="header-sub">Delivery Analytics · Optaris</div>
    </div>
    <div class="header-date">
        <strong>{progress}%</strong>
        Progresso Global
    </div>
</header>

<section class="hero">
    <div>
        <div class="progress-label">Avanço Geral do Projeto</div>
        <div class="progress-number">{progress}<span>%</span></div>
        <div class="progress-desc">{total} cards monitorados · progresso calculado por cards concluídos</div>
        <div class="bar-track">
            <div class="bar-fill" style="width:{progress}%"></div>
        </div>
    </div>

    <div class="donut-area">
        <div class="donut">
            <div class="donut-center">
                <strong>{total}</strong>
                <span>cards</span>
            </div>
        </div>
        <div class="legend">
            {render_status_legend(status)}
        </div>
    </div>
</section>

<div class="section-title">Módulos do Projeto</div>
<div class="modules-grid">
    {render_module_cards(modules)}
</div>

<div class="section-title">Board Executivo · Cards por Status</div>
<div class="kanban-grid">
    {render_kanban(df)}
</div>

<div class="section-title">Impedimentos & Pontos de Atenção</div>
<div class="alerts-grid">
    {render_alerts(summary, df)}
</div>

<div class="footer">
    <div>Gerado automaticamente pelo Trello Delivery Analytics</div>
    <div>{safe(client)} · {progress}% de progresso · {total} cards</div>
</div>

</div>
</body>
</html>
"""


def generate():
    clients = load_clients()

    if not clients:
        print("Nenhum cliente cadastrado.")
        return

    for client in clients:
        name = client["name"]
        slug = client["slug"]

        print(f"\nGerando view para: {name}")

        html = build_html(name)

        output = DATA_DIR / f"executive_{slug}.html"
        output.write_text(html, encoding="utf-8")

        print(f"Gerado: {output}")

if __name__ == "__main__":
    generate()
