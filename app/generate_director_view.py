from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "kanban_dataset.csv"
OUTPUT_FILE = DATA_DIR / "director_view.html"


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


def build_record(row):
    effort = pd.to_numeric(pd.Series([row.get("effort")]), errors="coerce").iloc[0]
    return {
        "id": safe_value(row.get("card_id")),
        "titulo": safe_value(row.get("titulo")),
        "cliente": safe_value(row.get("cliente"), "Sem cliente"),
        "status": safe_value(row.get("status_kanban"), "To Do"),
        "bloqueado": bool(row.get("bloqueado")) if not pd.isna(row.get("bloqueado")) else False,
        "priority": safe_value(row.get("priority"), "Sem prioridade"),
        "risk": safe_value(row.get("risk"), "Sem risco"),
        "effort": None if pd.isna(effort) else float(effort),
        "data_entrega": format_date(row.get("data_de_entrega")),
        "last_activity": format_date(row.get("last_activity")),
        "tipo": safe_value(row.get("tipo"), "GERAL"),
    }


def main():
    if not INPUT_FILE.exists():
        print("Arquivo kanban_dataset.csv não encontrado em ./data")
        return

    df = pd.read_csv(INPUT_FILE)
    records = [build_record(row) for _, row in df.iterrows()]
    clientes = sorted({r["cliente"] for r in records if r["cliente"]})

    data_json = json.dumps(records, ensure_ascii=False)
    clientes_json = json.dumps(clientes, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard da Diretoria</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg: #f4f7fb;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #183a66;
      --primary-2: #285ea8;
      --border: #e5e7eb;
      --success: #15803d;
      --warning: #b45309;
      --danger: #b42318;
      --shadow: 0 6px 18px rgba(17, 24, 39, 0.08);
      --radius: 16px;
    }}

    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: 'Segoe UI', Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}

    header {{
      background: linear-gradient(135deg, var(--primary), #0f2744);
      color: white;
      padding: 24px 28px;
      box-shadow: var(--shadow);
    }}

    .header-row {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 20px;
      flex-wrap: wrap;
    }}

    h1 {{
      margin: 0;
      font-size: 1.55rem;
      font-weight: 700;
      letter-spacing: 0.01em;
    }}

    .subtitle {{
      margin-top: 8px;
      opacity: 0.9;
      font-size: 0.96rem;
      max-width: 760px;
      line-height: 1.5;
    }}

    .top-actions {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
      border: 1px solid rgba(255,255,255,0.25);
      color: white;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 0.88rem;
      font-weight: 600;
      background: rgba(255,255,255,0.08);
      backdrop-filter: blur(6px);
    }}

    .btn:hover {{
      background: rgba(255,255,255,0.16);
    }}

    .lang-box {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .lang-box select {{
      padding: 8px 10px;
      border-radius: 10px;
      border: none;
      font-size: 0.85rem;
    }}

    .container {{
      padding: 24px 28px 40px;
    }}

    .filters {{
      background: var(--card);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 16px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
      margin-bottom: 20px;
    }}

    .filters label {{
      font-size: .82rem;
      color: #4b5563;
      font-weight: 600;
    }}

    .filters select, .filters button {{
      padding: 9px 12px;
      border: 1px solid #d1d5db;
      border-radius: 10px;
      background: #fff;
      font-size: .88rem;
    }}

    .filters button {{
      cursor: pointer;
      font-weight: 600;
    }}

    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .kpi {{
      background: var(--card);
      border-radius: var(--radius);
      padding: 18px 20px;
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
    }}

    .kpi-label {{
      font-size: 0.79rem;
      color: var(--muted);
      margin-bottom: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .kpi-value {{
      font-size: 1.9rem;
      font-weight: 700;
      color: #111827;
    }}

    .grid {{
      display: grid;
      grid-template-columns: 1.25fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}

    .panel {{
      background: var(--card);
      border-radius: var(--radius);
      padding: 18px 20px;
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
    }}

    .panel h2 {{
      margin: 0 0 14px;
      font-size: 1rem;
      color: var(--primary);
    }}

    .panel canvas {{
      width: 100% !important;
      max-height: 320px;
    }}

    .table-panel {{
      background: var(--card);
      border-radius: var(--radius);
      padding: 18px 20px;
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
      overflow-x: auto;
    }}

    .table-panel h2 {{
      margin: 0 0 14px;
      font-size: 1rem;
      color: var(--primary);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}

    thead {{
      background: #eef2f7;
    }}

    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}

    th {{
      color: #374151;
      font-size: 0.79rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    tr:hover {{
      background: #fafbfc;
    }}

    .tag {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 0.72rem;
      font-weight: 700;
    }}

    .tag-yes {{
      background: #fdecea;
      color: var(--danger);
    }}

    .tag-no {{
      background: #e8f8ef;
      color: var(--success);
    }}

    @media (max-width: 960px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-row">
      <div>
        <h1 id="title">🏢 Dashboard da Diretoria</h1>
        <div class="subtitle" id="subtitle">Visão consolidada interna das demandas, com opção de filtro por cliente e acesso à análise de flow.</div>
      </div>

      <div class="top-actions">
        <a class="btn" href="director_flow_view.html" id="flow-button">📈 Ver visão de flow</a>
        <div class="lang-box">
          <label id="language-label" for="language-select">Idioma:</label>
          <select id="language-select">
            <option value="pt">Português</option>
            <option value="es">Español</option>
          </select>
        </div>
      </div>
    </div>
  </header>

  <div class="container">
    <section class="filters">
      <label id="filter-client-label" for="filter-client">Cliente:</label>
      <select id="filter-client">
        <option value="">Todos</option>
      </select>

      <label id="filter-status-label" for="filter-status">Status:</label>
      <select id="filter-status">
        <option value="">Todos</option>
        <option value="To Do">To Do</option>
        <option value="Doing">Doing</option>
        <option value="Done">Done</option>
      </select>

      <button id="apply-filters">Aplicar</button>
      <button id="clear-filters">Limpar</button>
    </section>

    <section class="kpis">
      <div class="kpi">
        <div class="kpi-label" id="kpi-total-label">Total de demandas</div>
        <div class="kpi-value" id="kpi-total">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label" id="kpi-effort-label">Effort total</div>
        <div class="kpi-value" id="kpi-effort">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label" id="kpi-blocked-label">Bloqueadas</div>
        <div class="kpi-value" id="kpi-blocked">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label" id="kpi-done-label">Concluídas</div>
        <div class="kpi-value" id="kpi-done">0</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2 id="chart-client-title">Demandas por cliente</h2>
        <canvas id="clienteChart"></canvas>
      </div>
      <div class="panel">
        <h2 id="chart-status-title">Status das demandas</h2>
        <canvas id="statusChart"></canvas>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2 id="chart-priority-title">Prioridade</h2>
        <canvas id="priorityChart"></canvas>
      </div>
      <div class="panel">
        <h2 id="chart-risk-title">Risco</h2>
        <canvas id="riskChart"></canvas>
      </div>
    </section>

    <section class="table-panel">
      <h2 id="table-title">Demandas consolidadas</h2>
      <table>
        <thead>
          <tr>
            <th id="th-client">Cliente</th>
            <th id="th-demand">Demanda</th>
            <th id="th-status">Status</th>
            <th id="th-blocked">Bloqueado</th>
            <th id="th-priority">Prioridade</th>
            <th id="th-risk">Risco</th>
            <th id="th-effort">Effort</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </section>
  </div>

  <script>
    const DATA = {data_json};
    const CLIENTES = {clientes_json};

    const translations = {{
      pt: {{
        title: "🏢 Dashboard da Diretoria",
        subtitle: "Visão consolidada interna das demandas, com opção de filtro por cliente e acesso à análise de flow.",
        language: "Idioma:",
        flow_button: "📈 Ver visão de flow",
        filter_client: "Cliente:",
        filter_status: "Status:",
        apply: "Aplicar",
        clear: "Limpar",
        all: "Todos",
        kpi_total: "Total de demandas",
        kpi_effort: "Effort total",
        kpi_blocked: "Bloqueadas",
        kpi_done: "Concluídas",
        chart_client: "Demandas por cliente",
        chart_status: "Status das demandas",
        chart_priority: "Prioridade",
        chart_risk: "Risco",
        table: "Demandas consolidadas",
        th_client: "Cliente",
        th_demand: "Demanda",
        th_status: "Status",
        th_blocked: "Bloqueado",
        th_priority: "Prioridade",
        th_risk: "Risco",
        th_effort: "Effort",
        yes: "Sim",
        no: "Não",
        labels_status: {{
          "To Do": "To Do",
          "Doing": "Doing",
          "Done": "Done"
        }}
      }},
      es: {{
        title: "🏢 Panel de Dirección",
        subtitle: "Vista consolidada interna de las demandas, con opción de filtro por cliente y acceso al análisis de flujo.",
        language: "Idioma:",
        flow_button: "📈 Ver vista de flujo",
        filter_client: "Cliente:",
        filter_status: "Estado:",
        apply: "Aplicar",
        clear: "Limpiar",
        all: "Todos",
        kpi_total: "Total de demandas",
        kpi_effort: "Esfuerzo total",
        kpi_blocked: "Bloqueadas",
        kpi_done: "Completadas",
        chart_client: "Demandas por cliente",
        chart_status: "Estado de las demandas",
        chart_priority: "Prioridad",
        chart_risk: "Riesgo",
        table: "Demandas consolidadas",
        th_client: "Cliente",
        th_demand: "Demanda",
        th_status: "Estado",
        th_blocked: "Bloqueado",
        th_priority: "Prioridad",
        th_risk: "Riesgo",
        th_effort: "Esfuerzo",
        yes: "Sí",
        no: "No",
        labels_status: {{
          "To Do": "Por hacer",
          "Doing": "En progreso",
          "Done": "Finalizado"
        }}
      }}
    }};

    let currentLanguage = "pt";

    const filterClient = document.getElementById('filter-client');
    const filterStatus = document.getElementById('filter-status');
    const languageSelect = document.getElementById('language-select');

    CLIENTES.forEach(cliente => {{
      const option = document.createElement('option');
      option.value = cliente;
      option.textContent = cliente;
      filterClient.appendChild(option);
    }});

    const clienteChart = new Chart(document.getElementById('clienteChart'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ label: 'Demandas', data: [], backgroundColor: '#285ea8' }}] }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});

    const statusChart = new Chart(document.getElementById('statusChart'), {{
      type: 'doughnut',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: ['#94a3b8', '#285ea8', '#15803d'] }}] }},
      options: {{ responsive: true }}
    }});

    const priorityChart = new Chart(document.getElementById('priorityChart'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ label: 'Prioridade', data: [], backgroundColor: '#b45309' }}] }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});

    const riskChart = new Chart(document.getElementById('riskChart'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ label: 'Risco', data: [], backgroundColor: '#b42318' }}] }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});

    function countBy(data, field, defaultValue) {{
      const counts = {{}};
      data.forEach(item => {{
        const key = item[field] || defaultValue;
        counts[key] = (counts[key] || 0) + 1;
      }});
      return counts;
    }}

    function translateStatus(status) {{
      return translations[currentLanguage].labels_status[status] || status;
    }}

    function applyLanguage(lang) {{
      currentLanguage = lang;
      const t = translations[lang];

      document.getElementById("title").innerText = t.title;
      document.getElementById("subtitle").innerText = t.subtitle;
      document.getElementById("language-label").innerText = t.language;
      document.getElementById("flow-button").innerText = t.flow_button;
      document.getElementById("filter-client-label").innerText = t.filter_client;
      document.getElementById("filter-status-label").innerText = t.filter_status;
      document.getElementById("apply-filters").innerText = t.apply;
      document.getElementById("clear-filters").innerText = t.clear;

      document.getElementById("kpi-total-label").innerText = t.kpi_total;
      document.getElementById("kpi-effort-label").innerText = t.kpi_effort;
      document.getElementById("kpi-blocked-label").innerText = t.kpi_blocked;
      document.getElementById("kpi-done-label").innerText = t.kpi_done;

      document.getElementById("chart-client-title").innerText = t.chart_client;
      document.getElementById("chart-status-title").innerText = t.chart_status;
      document.getElementById("chart-priority-title").innerText = t.chart_priority;
      document.getElementById("chart-risk-title").innerText = t.chart_risk;

      document.getElementById("table-title").innerText = t.table;
      document.getElementById("th-client").innerText = t.th_client;
      document.getElementById("th-demand").innerText = t.th_demand;
      document.getElementById("th-status").innerText = t.th_status;
      document.getElementById("th-blocked").innerText = t.th_blocked;
      document.getElementById("th-priority").innerText = t.th_priority;
      document.getElementById("th-risk").innerText = t.th_risk;
      document.getElementById("th-effort").innerText = t.th_effort;

      filterClient.options[0].text = t.all;
      filterStatus.options[0].text = t.all;
      filterStatus.options[1].text = translateStatus("To Do");
      filterStatus.options[2].text = translateStatus("Doing");
      filterStatus.options[3].text = translateStatus("Done");

      applyFilters();
    }}

    function updateKPIs(data) {{
      const total = data.length;
      const effort = data.reduce((acc, item) => acc + (item.effort || 0), 0);
      const blocked = data.filter(item => item.bloqueado).length;
      const done = data.filter(item => item.status === 'Done').length;

      document.getElementById('kpi-total').textContent = total;
      document.getElementById('kpi-effort').textContent = effort.toFixed(0);
      document.getElementById('kpi-blocked').textContent = blocked;
      document.getElementById('kpi-done').textContent = done;
    }}

    function updateCharts(data) {{
      const clienteCounts = countBy(data, 'cliente', 'Sem cliente');
      const statusCounts = countBy(data, 'status', 'Não definido');
      const priorityCounts = countBy(data, 'priority', 'Sem prioridade');
      const riskCounts = countBy(data, 'risk', 'Sem risco');

      clienteChart.data.labels = Object.keys(clienteCounts);
      clienteChart.data.datasets[0].data = Object.values(clienteCounts);
      clienteChart.update();

      statusChart.data.labels = Object.keys(statusCounts).map(translateStatus);
      statusChart.data.datasets[0].data = Object.values(statusCounts);
      statusChart.update();

      priorityChart.data.labels = Object.keys(priorityCounts);
      priorityChart.data.datasets[0].data = Object.values(priorityCounts);
      priorityChart.update();

      riskChart.data.labels = Object.keys(riskCounts);
      riskChart.data.datasets[0].data = Object.values(riskCounts);
      riskChart.update();
    }}

    function updateTable(data) {{
      const tbody = document.getElementById('table-body');
      tbody.innerHTML = '';

      const t = translations[currentLanguage];

      data.forEach(item => {{
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${{item.cliente}}</td>
          <td>${{item.titulo}}</td>
          <td>${{translateStatus(item.status)}}</td>
          <td>${{item.bloqueado ? `<span class="tag tag-yes">${{t.yes}}</span>` : `<span class="tag tag-no">${{t.no}}</span>`}}</td>
          <td>${{item.priority}}</td>
          <td>${{item.risk}}</td>
          <td>${{item.effort ?? ''}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function applyFilters() {{
      const client = filterClient.value;
      const status = filterStatus.value;

      const filtered = DATA.filter(item => {{
        const matchClient = !client || item.cliente === client;
        const matchStatus = !status || item.status === status;
        return matchClient && matchStatus;
      }});

      updateKPIs(filtered);
      updateCharts(filtered);
      updateTable(filtered);
    }}

    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('clear-filters').addEventListener('click', () => {{
      filterClient.value = '';
      filterStatus.value = '';
      applyFilters();
    }});

    languageSelect.addEventListener('change', function() {{
      applyLanguage(this.value);
    }});

    applyLanguage("pt");
  </script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"View da diretoria gerada em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

