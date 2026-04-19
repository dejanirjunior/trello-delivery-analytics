from pathlib import Path
import json
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "kanban_dataset.csv"


def safe_value(value, default=""):
    if pd.isna(value):
        return default
    return value


def format_date(value):
    if pd.isna(value) or not value:
        return ""
    try:
        dt = pd.to_datetime(value, utc=True)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)


def slugify(text):
    text = str(text).strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s-]+", "_", text)
    return text


def build_card_record(row):
    return {
        "id": safe_value(row.get("card_id")),
        "title": safe_value(row.get("titulo")),
        "status": safe_value(row.get("status_kanban"), "To Do"),
        "cliente": safe_value(row.get("cliente"), "Sem cliente"),
        "bloqueado": bool(row.get("bloqueado")) if not pd.isna(row.get("bloqueado")) else False,
        "priority": safe_value(row.get("priority"), "Sem prioridade"),
        "risk": safe_value(row.get("risk"), "Sem risco"),
        "effort": None if pd.isna(row.get("effort")) else row.get("effort"),
        "executed_hours": None if pd.isna(row.get("total_horas_executado")) else row.get("total_horas_executado"),
        "commitment_date": format_date(row.get("data_compromisso")),
        "trello_due_date": format_date(row.get("due_date")),
        "last_activity": format_date(row.get("last_activity")),
        "tipo": safe_value(row.get("tipo"), "GERAL"),
    }


def build_html(data_json, cliente_nome):
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Painel Kanban - {cliente_nome}</title>
<style>
  :root {{
    --done: #0a7a4a;
    --done-bg: #e8f8ef;
    --prog: #0d7dbf;
    --prog-bg: #eaf4fb;
    --todo: #5a607a;
    --todo-bg: #f4f6f8;
    --navy: #1b3a6b;
    --gold: #d4860a;
    --block: #c0392b;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #f0f2f7;
    min-height: 100vh;
    color: #1a1a2e;
  }}

  header {{
    background: var(--navy);
    color: #fff;
    padding: 18px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,0,0,.25);
    position: sticky;
    top: 0;
    z-index: 100;
  }}

  .badge-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    padding: 14px 28px 0;
  }}

  .badge {{
    display: flex;
    align-items: center;
    gap: 6px;
    background: #fff;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: .8rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.1);
    font-weight: 600;
  }}

  .badge .dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }}

  .filters {{
    padding: 12px 28px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: center;
  }}

  .filters label {{
    font-size: .8rem;
    color: #555;
    font-weight: 600;
  }}

  .filters select,
  .filters input {{
    padding: 6px 10px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: .82rem;
    background: #fff;
  }}

  .filters input {{
    min-width: 220px;
  }}

  .filters button {{
    padding: 6px 14px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: .82rem;
    background: #fff;
    cursor: pointer;
  }}

  .board {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 16px 28px 40px;
    align-items: start;
  }}

  .column {{
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,.08);
    overflow: hidden;
  }}

  .col-header {{
    padding: 14px 16px 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 2px solid;
  }}

  .col-done .col-header {{
    color: var(--done);
    border-color: var(--done);
    background: var(--done-bg);
  }}

  .col-doing .col-header {{
    color: var(--prog);
    border-color: var(--prog);
    background: var(--prog-bg);
  }}

  .col-todo .col-header {{
    color: var(--todo);
    border-color: #aab0c4;
    background: var(--todo-bg);
  }}

  .cards {{
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-height: 40px;
  }}

  .card {{
    border-radius: 8px;
    border: 1px solid #e0e4ef;
    padding: 10px 12px;
    background: #fff;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    cursor: pointer;
  }}

  .card-id {{
    font-size: .68rem;
    font-weight: 700;
    margin-bottom: 5px;
    font-family: monospace;
    color: #666;
  }}

  .card-title {{
    font-size: .82rem;
    line-height: 1.4;
    color: #2c3050;
    margin-bottom: 8px;
  }}

  .card-footer {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
  }}

  .tag {{
    font-size: .68rem;
    padding: 2px 7px;
    border-radius: 10px;
    font-weight: 600;
  }}

  .tag-client {{
    background: #eef0fa;
    color: var(--navy);
  }}

  .tag-type {{
    background: #fff3e0;
    color: var(--gold);
  }}

  .tag-block {{
    background: #fdecea;
    color: var(--block);
  }}

  .hidden {{
    display: none !important;
  }}

  .modal-overlay {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.45);
    z-index: 200;
    align-items: center;
    justify-content: center;
  }}

  .modal-overlay.open {{
    display: flex;
  }}

  .modal {{
    background: #fff;
    border-radius: 14px;
    max-width: 560px;
    width: 92%;
    padding: 28px;
    position: relative;
    box-shadow: 0 8px 32px rgba(0,0,0,.2);
    max-height: 80vh;
    overflow-y: auto;
  }}

  .modal-close {{
    position: absolute;
    top: 14px;
    right: 16px;
    background: none;
    border: none;
    font-size: 1.4rem;
    cursor: pointer;
    color: #888;
  }}

  .modal-row {{
    font-size: .85rem;
    margin-bottom: 8px;
  }}

  @media (max-width: 900px) {{
    .board {{
      grid-template-columns: 1fr;
    }}
  }}
</style>
</head>
<body>

<header>
  <h1>🗂️ Painel Kanban - {cliente_nome}</h1>
  <span id="visible-count">0 demandas</span>
</header>

<div class="badge-row">
  <div class="badge"><div class="dot" style="background:var(--todo)"></div><span id="cnt-todo">0 To Do</span></div>
  <div class="badge"><div class="dot" style="background:var(--prog)"></div><span id="cnt-doing">0 Doing</span></div>
  <div class="badge"><div class="dot" style="background:var(--done)"></div><span id="cnt-done">0 Done</span></div>
</div>

<div class="filters">
  <label>Buscar:</label>
  <input type="text" id="filter-search" placeholder="Pesquisar demanda..." oninput="applyFilters()">

  <label>Bloqueado:</label>
  <select id="filter-block" onchange="applyFilters()">
    <option value="">Todos</option>
    <option value="true">Sim</option>
    <option value="false">Não</option>
  </select>

  <button onclick="clearFilters()">✕ Limpar filtros</button>
</div>

<div class="board">
  <div class="column col-todo">
    <div class="col-header">
      <h2>📋 To Do</h2>
      <span class="col-count" id="hdr-todo">0</span>
    </div>
    <div class="cards" id="col-To Do"></div>
  </div>

  <div class="column col-doing">
    <div class="col-header">
      <h2>🔄 Doing</h2>
      <span class="col-count" id="hdr-doing">0</span>
    </div>
    <div class="cards" id="col-Doing"></div>
  </div>

  <div class="column col-done">
    <div class="col-header">
      <h2>✅ Done</h2>
      <span class="col-count" id="hdr-done">0</span>
    </div>
    <div class="cards" id="col-Done"></div>
  </div>
</div>

<div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
  <div class="modal">
    <button class="modal-close" onclick="closeModalDirect()">×</button>
    <div id="modal-content"></div>
  </div>
</div>

<script>
const DATA = {data_json};

function buildCard(item) {{
  const div = document.createElement('div');
  div.className = 'card';
  div.dataset.title = (item.title || '').toLowerCase();
  div.dataset.status = item.status || 'To Do';
  div.dataset.block = String(!!item.bloqueado);

  let footer = '';
  footer += `<span class="tag tag-client">${{item.cliente || 'Sem cliente'}}</span>`;
  footer += `<span class="tag tag-type">${{item.tipo || 'GERAL'}}</span>`;
  if (item.bloqueado) {{
    footer += `<span class="tag tag-block">BLOCK</span>`;
  }}

  div.innerHTML = `
    <div class="card-id">${{item.id}}</div>
    <div class="card-title">${{item.title}}</div>
    <div class="card-footer">${{footer}}</div>
  `;

  div.addEventListener('click', () => openModal(item));
  return div;
}}

function renderAll() {{
  ['To Do','Doing','Done'].forEach(status => {{
    document.getElementById('col-' + status).innerHTML = '';
  }});

  DATA.forEach(item => {{
    const card = buildCard(item);
    const target = document.getElementById('col-' + item.status);
    if (target) {{
      target.appendChild(card);
    }}
  }});

  applyFilters();
}}

function applyFilters() {{
  const search = document.getElementById('filter-search').value.toLowerCase();
  const block = document.getElementById('filter-block').value;

  const counts = {{ 'To Do': 0, 'Doing': 0, 'Done': 0 }};
  let total = 0;

  document.querySelectorAll('.card').forEach(card => {{
    const cardTitle = card.dataset.title;
    const cardStatus = card.dataset.status;
    const cardBlock = card.dataset.block;

    const searchMatch = !search || cardTitle.includes(search);
    const blockMatch = !block || cardBlock === block;

    const show = searchMatch && blockMatch;
    card.classList.toggle('hidden', !show);

    if (show) {{
      counts[cardStatus] = (counts[cardStatus] || 0) + 1;
      total++;
    }}
  }});

  document.getElementById('hdr-todo').textContent = counts['To Do'] || 0;
  document.getElementById('hdr-doing').textContent = counts['Doing'] || 0;
  document.getElementById('hdr-done').textContent = counts['Done'] || 0;

  document.getElementById('cnt-todo').textContent = `${{counts['To Do'] || 0}} To Do`;
  document.getElementById('cnt-doing').textContent = `${{counts['Doing'] || 0}} Doing`;
  document.getElementById('cnt-done').textContent = `${{counts['Done'] || 0}} Done`;
  document.getElementById('visible-count').textContent = `${{total}} demandas`;
}}

function clearFilters() {{
  document.getElementById('filter-search').value = '';
  document.getElementById('filter-block').value = '';
  applyFilters();
}}

function openModal(item) {{
  document.getElementById('modal-content').innerHTML = `
    <div class="modal-row"><strong>ID:</strong> ${{item.id}}</div>
    <div class="modal-row"><strong>Demanda:</strong> ${{item.title}}</div>
    <div class="modal-row"><strong>Status:</strong> ${{item.status}}</div>
    <div class="modal-row"><strong>Cliente:</strong> ${{item.cliente || 'Sem cliente'}}</div>
    <div class="modal-row"><strong>Tipo:</strong> ${{item.tipo || 'GERAL'}}</div>
    <div class="modal-row"><strong>Bloqueado:</strong> ${{item.bloqueado ? 'Sim' : 'Não'}}</div>
    <div class="modal-row"><strong>Prioridade:</strong> ${{item.priority || 'Sem prioridade'}}</div>
    <div class="modal-row"><strong>Risco:</strong> ${{item.risk || 'Sem risco'}}</div>
    <div class="modal-row"><strong>Effort:</strong> ${{item.effort ?? 'Não informado'}}</div>
    <div class="modal-row"><strong>Total Horas Executado:</strong> ${{item.executed_hours ?? 'Não informado'}}</div>
    <div class="modal-row"><strong>Data Compromisso:</strong> ${{item.commitment_date || 'Não informada'}}</div>
    <div class="modal-row"><strong>Prazo Trello:</strong> ${{item.trello_due_date || 'Não informado'}}</div>
    <div class="modal-row"><strong>Última atualização:</strong> ${{item.last_activity || 'Não informada'}}</div>
  `;
  document.getElementById('modal-overlay').classList.add('open');
}}

function closeModal(e) {{
  if (e.target === document.getElementById('modal-overlay')) {{
    closeModalDirect();
  }}
}}

function closeModalDirect() {{
  document.getElementById('modal-overlay').classList.remove('open');
}}

document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeModalDirect();
}});

renderAll();
</script>
</body>
</html>
"""


def main():
    if not INPUT_FILE.exists():
        print("Arquivo kanban_dataset.csv não encontrado em ./data")
        return

    df = pd.read_csv(INPUT_FILE)

    if "cliente" not in df.columns:
        print("Coluna 'cliente' não encontrada no dataset.")
        return

    clientes = sorted(df["cliente"].dropna().unique())

    if not clientes:
        print("Nenhum cliente encontrado no dataset.")
        return

    for cliente in clientes:
        df_cliente = df[df["cliente"] == cliente].copy()
        records = [build_card_record(row) for _, row in df_cliente.iterrows()]
        data_json = json.dumps(records, ensure_ascii=False)

        html = build_html(data_json, cliente)

        output_file = DATA_DIR / f"kanban_{slugify(cliente)}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"HTML Kanban gerado em: {output_file}")


if __name__ == "__main__":
    main()


