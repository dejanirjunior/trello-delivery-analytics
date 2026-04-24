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


def safe(value):
    if value is None or pd.isna(value):
        return ""
    return escape(str(value))


def split_modules(value):
    if value is None or pd.isna(value) or not str(value).strip():
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

    if df.empty:
        return []

    if "modulos" not in df.columns:
        df = df.copy()
        df["modulos"] = "Sem módulo informado"

    for _, row in df.iterrows():
        for module in split_modules(row.get("modulos")):
            rows.append({
                "module": module,
                "status": row.get("status_kanban", "To Do"),
            })

    if not rows:
        return []

    mod_df = pd.DataFrame(rows)
    all_modules = list(MODULE_ORDER)

    for module in sorted(mod_df["module"].dropna().unique()):
        if module not in all_modules:
            all_modules.append(module)

    modules = []

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


def module_class(name):
    normalized = str(name).lower()

    if "crm" in normalized:
        return "crm"
    if "compra" in normalized:
        return "compras"
    if "orcamento" in normalized or "orçamento" in normalized:
        return "orcamento"

    return "generic"


def module_badge_class(name):
    normalized = str(name).lower()

    if "crm" in normalized:
        return "crm"
    if "compra" in normalized:
        return "cp"
    if "orcamento" in normalized or "orçamento" in normalized:
        return "orc"

    return "gen"


def render_status_legend(status):
    html = ""

    for key in STATUS_ORDER:
        html += f"""
        <div class="legend-item">
            <div class="legend-dot" style="background:{STATUS_COLORS[key]}"></div>
            {STATUS_LABELS[key]} <strong>{status.get(key, 0)}</strong>
        </div>
        """

    return html


def render_module_cards(modules):
    if not modules:
        return '<div class="empty">Sem dados de módulos.</div>'

    html = ""

    for i, module in enumerate(modules, start=1):
        name = safe(module["name"])
        cls = module_class(module["name"])

        html += f"""
        <div class="module-card {cls}">
            <div class="module-num">Módulo {i}</div>
            <div class="module-name">{name}</div>

            <div class="module-progress">
                <div class="module-progress-top">
                    <span>Progresso</span>
                    <strong>{module["progress"]}%</strong>
                </div>
                <div class="mod-bar-track">
                    <div class="mod-bar-fill" style="--target: {module["progress"]}%"></div>
                </div>
            </div>

            <div class="module-stats">
                <div class="stat-chip"><div class="dot" style="background:var(--done)"></div>{module["done"]} Finalizados</div>
                <div class="stat-chip"><div class="dot" style="background:var(--progress)"></div>{module["doing"]} Em andamento</div>
                <div class="stat-chip"><div class="dot" style="background:var(--blocked)"></div>{module["block"]} Bloqueados</div>
                <div class="stat-chip"><div class="dot" style="background:var(--not-started)"></div>{module["todo"]} Não iniciados</div>
            </div>

            <div class="module-detail">
                <div class="module-detail-title">Classificação</div>
                {module["total"]} cards vinculados a este módulo.
            </div>
        </div>
        """

    return html


def render_kanban(df):
    html = ""

    for status_key in STATUS_ORDER:
        subset_all = df[df["status_kanban"] == status_key]
        subset = subset_all.head(8)
        color = STATUS_COLORS[status_key]
        title = STATUS_LABELS[status_key]
        count = len(subset_all)

        cards_html = ""

        if subset.empty:
            cards_html = '<div class="kanban-empty">Sem cards nesta etapa.</div>'
        else:
            for idx, (_, row) in enumerate(subset.iterrows(), start=1):
                title_card = safe(row.get("titulo", ""))
                module = safe(row.get("modulos", "Sem módulo informado"))
                module_cls = module_badge_class(module)

                cards_html += f"""
                <div class="kanban-card">
                    <div class="card-id">#{idx}</div>
                    {title_card}
                    <div class="card-module {module_cls}">{module}</div>
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


def build_card_list(df, limit=5):
    if df.empty:
        return '<div class="alert-empty">Nenhum card encontrado.</div>'

    cards = ""

    for _, row in df.head(limit).iterrows():
        titulo = safe(row.get("titulo", ""))
        modulo = safe(row.get("modulos", "Sem módulo informado"))
        responsavel = safe(row.get("assigned_members", ""))

        meta_parts = []

        if modulo:
            meta_parts.append(modulo)

        if responsavel:
            meta_parts.append(responsavel)

        meta = " · ".join(meta_parts)

        cards += f"""
        <div class="alert-item">
            <strong>{titulo}</strong>
            <div class="alert-meta">{meta}</div>
        </div>
        """

    if len(df) > limit:
        cards += f'<div class="alert-more">+{len(df) - limit} outros cards</div>'

    return cards


def render_alerts(summary, df):
    blocked = summary["blocked"]
    high_risk = summary["high_risk"]
    overdue = summary["overdue"]

    if "modulos" in df.columns:
        sem_modulo = df[df["modulos"].astype(str).str.contains("Sem módulo informado", na=False)]
    else:
        sem_modulo = df

    return f"""
    <div class="alert-card">
        <div class="alert-icon">⛔</div>
        <div class="alert-content">
            <div class="alert-title">Cards bloqueados</div>
            <div class="alert-desc">{len(blocked)} cards estão marcados como bloqueados e exigem acompanhamento.</div>
            <div class="alert-badge">● {len(blocked)} bloqueados</div>
            {build_card_list(blocked)}
        </div>
    </div>

    <div class="alert-card">
        <div class="alert-icon">⚠️</div>
        <div class="alert-content">
            <div class="alert-title">Risco alto</div>
            <div class="alert-desc">{len(high_risk)} cards estão sinalizados com risco alto.</div>
            <div class="alert-badge">● {len(high_risk)} em risco</div>
            {build_card_list(high_risk)}
        </div>
    </div>

    <div class="alert-card">
        <div class="alert-icon">⏰</div>
        <div class="alert-content">
            <div class="alert-title">Prazos vencidos</div>
            <div class="alert-desc">{len(overdue)} cards possuem data vencida e ainda não foram concluídos.</div>
            <div class="alert-badge">● {len(overdue)} atrasados</div>
            {build_card_list(overdue)}
        </div>
    </div>

    <div class="alert-card">
        <div class="alert-icon">🧩</div>
        <div class="alert-content">
            <div class="alert-title">Classificação por módulo</div>
            <div class="alert-desc">{len(sem_modulo)} cards ainda estão sem label de módulo.</div>
            <div class="alert-badge">● {len(sem_modulo)} sem módulo</div>
            {build_card_list(sem_modulo)}
        </div>
    </div>
    """


def build_html(client_name, slug):
    summary = build_executive_summary(client_name)
    df_all = load_data()
    df = filter_by_client(df_all, client_name)

    if "modulos" not in df.columns:
        df = df.copy()
        df["modulos"] = "Sem módulo informado"

    total = summary["total_cards"]
    progress = summary["progress"]
    status = summary["status"]
    modules = build_module_data(df)
    module_count = len([m for m in modules if m["name"] != "Sem módulo informado"])
    donut = build_donut_gradient(status)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe(client_name)} · Panorama Executivo</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0b0f1a;
    --surface: #131929;
    --surface2: #1a2238;
    --border: rgba(255,255,255,0.07);
    --text: #e8eaf0;
    --muted: #8891a8;
    --gold: #c9a84c;
    --gold-light: #e4c97e;
    --done: #3ecf8e;
    --progress: #4f8ef7;
    --blocked: #f06565;
    --waiting: #f0a046;
    --todo: #7c8daa;
    --not-started: #454f65;
  }}

  *, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  html {{
    scroll-behavior: smooth;
  }}

  body {{
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
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
    z-index: 0;
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
    gap: 24px;
    margin-bottom: 56px;
    padding-bottom: 32px;
    border-bottom: 1px solid var(--border);
  }}

  .eyebrow {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.18em;
    color: var(--gold);
    text-transform: uppercase;
    margin-bottom: 10px;
  }}

  .header h1 {{
    font-family: 'DM Serif Display', serif;
    font-size: 42px;
    line-height: 1.1;
    color: var(--text);
  }}

  .header h1 em {{
    font-style: italic;
    color: var(--gold-light);
  }}

  .header-sub {{
    color: var(--muted);
    margin-top: 8px;
    font-size: 13px;
  }}

  .top-nav {{
    margin-top: 18px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    position: relative;
    z-index: 20;
  }}

  .nav-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 112px;
    padding: 9px 15px;
    border-radius: 999px;
    background: #1a2238;
    color: #e8eaf0;
    font-size: 12px;
    font-weight: 700;
    text-decoration: none;
    border: 1px solid rgba(255,255,255,0.14);
    transition: 0.2s;
  }}

  .nav-btn:hover {{
    background: #263149;
    color: #ffffff;
    transform: translateY(-1px);
  }}

  .nav-btn.active {{
    background: linear-gradient(90deg, var(--gold), var(--gold-light));
    color: #0b0f1a;
    border-color: transparent;
  }}

  .header-date {{
    text-align: right;
    font-size: 12px;
    color: var(--muted);
  }}

  .header-date strong {{
    display: block;
    font-size: 22px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 2px;
  }}

  .hero-progress {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 36px 40px;
    margin-bottom: 32px;
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 40px;
    align-items: center;
    position: relative;
    overflow: hidden;
  }}

  .hero-progress::before {{
    content: '';
    position: absolute;
    top: -60px;
    right: 200px;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(201,168,76,0.08) 0%, transparent 70%);
    pointer-events: none;
  }}

  .progress-label {{
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--gold);
    font-weight: 600;
    margin-bottom: 8px;
  }}

  .progress-number {{
    font-family: 'DM Serif Display', serif;
    font-size: 72px;
    line-height: 1;
    color: var(--text);
  }}

  .progress-number span {{
    font-size: 32px;
    color: var(--muted);
  }}

  .progress-desc {{
    color: var(--muted);
    font-size: 13px;
    margin-top: 6px;
  }}

  .progress-bar-wrap {{
    margin-top: 20px;
  }}

  .bar-track {{
    background: var(--surface2);
    border-radius: 100px;
    height: 10px;
    overflow: hidden;
  }}

  .bar-fill {{
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, var(--gold) 0%, var(--gold-light) 100%);
    width: 0;
    animation: growBar 1.2s cubic-bezier(.22,.9,.36,1) forwards;
  }}

  @keyframes growBar {{
    to {{
      width: var(--target);
    }}
  }}

  .donut-area {{
    display: flex;
    align-items: center;
    gap: 24px;
    position: relative;
    z-index: 1;
  }}

  .donut-wrap {{
    position: relative;
    width: 120px;
    height: 120px;
    flex-shrink: 0;
    border-radius: 50%;
    background: conic-gradient({donut});
  }}

  .donut-wrap::after {{
    content: '';
    position: absolute;
    inset: 17px;
    background: var(--surface);
    border-radius: 50%;
  }}

  .donut-center {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 2;
  }}

  .donut-center .dc-num {{
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    color: var(--text);
  }}

  .donut-center .dc-label {{
    font-size: 9px;
    color: var(--muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}

  .legend {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 165px;
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--muted);
  }}

  .legend-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }}

  .legend-item strong {{
    color: var(--text);
    font-weight: 600;
    margin-left: auto;
    padding-left: 16px;
  }}

  .section-title {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 16px;
    margin-top: 40px;
  }}

  .modules-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }}

  .module-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px 24px;
    position: relative;
    overflow: hidden;
    animation: fadeUp 0.5s ease both;
  }}

  .module-card:nth-child(2) {{
    animation-delay: 0.1s;
  }}

  .module-card:nth-child(3) {{
    animation-delay: 0.2s;
  }}

  @keyframes fadeUp {{
    from {{
      opacity: 0;
      transform: translateY(16px);
    }}
    to {{
      opacity: 1;
      transform: translateY(0);
    }}
  }}

  .module-card::after {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
  }}

  .module-card.crm::after {{
    background: var(--progress);
  }}

  .module-card.compras::after {{
    background: var(--waiting);
  }}

  .module-card.orcamento::after {{
    background: var(--done);
  }}

  .module-card.generic::after {{
    background: var(--gold);
  }}

  .module-num {{
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 600;
    margin-bottom: 6px;
  }}

  .module-name {{
    font-family: 'DM Serif Display', serif;
    font-size: 20px;
    color: var(--text);
    line-height: 1.2;
    margin-bottom: 20px;
  }}

  .module-progress {{
    margin-bottom: 16px;
  }}

  .module-progress-top {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    font-size: 12px;
    color: var(--muted);
  }}

  .module-progress-top strong {{
    color: var(--text);
    font-size: 14px;
  }}

  .mod-bar-track {{
    background: var(--bg);
    border-radius: 100px;
    height: 6px;
    overflow: hidden;
  }}

  .mod-bar-fill {{
    height: 100%;
    border-radius: 100px;
    animation: growBar 1.2s cubic-bezier(.22,.9,.36,1) forwards;
    width: 0;
  }}

  .crm .mod-bar-fill {{
    background: var(--progress);
  }}

  .compras .mod-bar-fill {{
    background: var(--waiting);
  }}

  .orcamento .mod-bar-fill {{
    background: var(--done);
  }}

  .generic .mod-bar-fill {{
    background: var(--gold);
  }}

  .module-stats {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
  }}

  .stat-chip {{
    display: flex;
    align-items: center;
    gap: 5px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 100px;
    padding: 4px 10px;
    font-size: 11px;
    color: var(--muted);
  }}

  .stat-chip .dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }}

  .module-detail {{
    margin-top: 16px;
    font-size: 11px;
    color: var(--muted);
    line-height: 1.6;
  }}

  .module-detail-title {{
    margin-bottom: 4px;
    color: var(--text);
    font-size: 12px;
    font-weight: 500;
  }}

  .kanban-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }}

  .kanban-col {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
  }}

  .kanban-header {{
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}

  .kanban-header-inner {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .kanban-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }}

  .kanban-title {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }}

  .kanban-count {{
    background: var(--bg);
    border-radius: 100px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text);
  }}

  .kanban-body {{
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}

  .kanban-card {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 11px;
    color: var(--muted);
    line-height: 1.4;
    transition: border-color 0.2s, transform 0.2s;
    cursor: default;
  }}

  .kanban-card:hover {{
    border-color: rgba(255,255,255,0.15);
    transform: translateY(-1px);
  }}

  .kanban-card .card-id {{
    font-size: 10px;
    color: var(--gold);
    font-weight: 600;
    margin-bottom: 4px;
  }}

  .kanban-card .card-module {{
    display: inline-block;
    font-size: 9px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 2px 6px;
    border-radius: 4px;
    margin-top: 6px;
    font-weight: 600;
  }}

  .kanban-card .card-module.crm {{
    background: rgba(79,142,247,0.15);
    color: var(--progress);
  }}

  .kanban-card .card-module.cp {{
    background: rgba(240,160,70,0.15);
    color: var(--waiting);
  }}

  .kanban-card .card-module.orc {{
    background: rgba(62,207,142,0.15);
    color: var(--done);
  }}

  .kanban-card .card-module.gen {{
    background: rgba(201,168,76,0.15);
    color: var(--gold);
  }}

  .kanban-empty {{
    font-size: 11px;
    color: var(--muted);
  }}

  .alerts-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}

  .alert-card {{
    background: var(--surface);
    border: 1px solid rgba(240, 101, 101, 0.2);
    border-radius: 14px;
    padding: 20px 22px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
  }}

  .alert-icon {{
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: rgba(240,101,101,0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 16px;
  }}

  .alert-content {{
    width: 100%;
  }}

  .alert-title {{
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
  }}

  .alert-desc {{
    font-size: 11px;
    color: var(--muted);
    line-height: 1.5;
  }}

  .alert-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(240,101,101,0.15);
    border: 1px solid rgba(240,101,101,0.3);
    color: var(--blocked);
    border-radius: 100px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
    margin-top: 8px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }}

  .alert-item {{
    margin-top: 10px;
    padding: 8px;
    border-radius: 8px;
    background: var(--bg);
    font-size: 11px;
    border: 1px solid var(--border);
  }}

  .alert-item strong {{
    display: block;
    color: var(--text);
    line-height: 1.35;
  }}

  .alert-meta {{
    color: var(--muted);
    font-size: 10px;
    margin-top: 4px;
  }}

  .alert-more,
  .alert-empty {{
    margin-top: 8px;
    font-size: 11px;
    color: var(--muted);
  }}

  .footer {{
    margin-top: 60px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: var(--not-started);
  }}

  .empty {{
    color: var(--muted);
  }}

  @media (max-width: 900px) {{
    .header {{
      flex-direction: column;
    }}

    .header-date {{
      text-align: left;
    }}

    .hero-progress {{
      grid-template-columns: 1fr;
    }}

    .modules-grid {{
      grid-template-columns: 1fr;
    }}

    .kanban-grid {{
      grid-template-columns: 1fr;
    }}

    .alerts-grid {{
      grid-template-columns: 1fr;
    }}
  }}
</style>
</head>

<body>
<div class="page">

  <header class="header">
    <div class="header-left">
      <div class="eyebrow">Relatório Executivo · Panorama do Projeto</div>
      <h1>{safe(client_name)} &mdash; <em>Planning</em></h1>
      <div class="header-sub">Delivery Analytics · Optaris</div>

      <div class="top-nav">
        <a href="/views/executive_{slug}.html" class="nav-btn active">📊 Executivo</a>
        <a href="/views/kanban_{slug}.html" class="nav-btn">📌 Kanban</a>
        <a href="/views/dashboard_{slug}.html" class="nav-btn">📈 Dashboard</a>
      </div>
    </div>

    <div class="header-date">
      <strong>{progress}%</strong>
      Progresso Global
    </div>
  </header>

  <div class="hero-progress">
    <div>
      <div class="progress-label">Avanço Geral do Projeto</div>
      <div class="progress-number">{progress}<span>%</span></div>
      <div class="progress-desc">{total} cards monitorados · {module_count} módulos classificados</div>
      <div class="progress-bar-wrap">
        <div class="bar-track">
          <div class="bar-fill" style="--target: {progress}%"></div>
        </div>
      </div>
    </div>

    <div class="donut-area">
      <div class="donut-wrap">
        <div class="donut-center">
          <div class="dc-num">{total}</div>
          <div class="dc-label">cards</div>
        </div>
      </div>

      <div class="legend">
        {render_status_legend(status)}
      </div>
    </div>
  </div>

  <div class="section-title">Módulos do Projeto</div>
  <div class="modules-grid">
    {render_module_cards(modules)}
  </div>

  <div class="section-title" style="margin-top:48px;">Board de Status · Cards do Projeto</div>
  <div class="kanban-grid">
    {render_kanban(df)}
  </div>

  <div class="section-title" style="margin-top:48px;">⚠ Impedimentos &amp; Pontos de Atenção</div>
  <div class="alerts-grid">
    {render_alerts(summary, df)}
  </div>

  <div class="footer">
    <div>Gerado automaticamente com base nos dados do Trello · Optaris</div>
    <div>Progresso geral: <strong style="color:var(--gold)">{progress}%</strong> · {total} cards</div>
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

        html = build_html(name, slug)
        output = DATA_DIR / f"executive_{slug}.html"
        output.write_text(html, encoding="utf-8")

        print(f"Gerado: {output}")


if __name__ == "__main__":
    generate()


