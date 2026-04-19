from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "kanban_dataset.csv"
OUTPUT_FILE = DATA_DIR / "pm_view.html"


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
    executed = pd.to_numeric(pd.Series([row.get("total_horas_executado")]), errors="coerce").iloc[0]

    return {
        "id": safe_value(row.get("card_id")),
        "titulo": safe_value(row.get("titulo")),
        "cliente": safe_value(row.get("cliente"), "Sem cliente"),
        "status": safe_value(row.get("status_kanban"), "To Do"),
        "bloqueado": bool(row.get("bloqueado")) if not pd.isna(row.get("bloqueado")) else False,
        "priority": safe_value(row.get("priority"), "Sem prioridade"),
        "risk": safe_value(row.get("risk"), "Sem risco"),
        "effort": None if pd.isna(effort) else float(effort),
        "executed_hours": None if pd.isna(executed) else float(executed),
        "effort_preenchido": False if pd.isna(effort) else True,
        "data_compromisso": format_date(row.get("data_compromisso")),
        "due_date": format_date(row.get("due_date")),
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
  <title>Visão do Gerente de Projetos</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f7fb; margin: 0; color: #1f2937; }}
    header {{ background: linear-gradient(135deg, #183a66, #0f2744); color: white; padding: 24px 28px; }}
    .header-row {{ display:flex; justify-content:space-between; align-items:flex-start; gap:20px; flex-wrap:wrap; }}
    .header-actions {{ display:flex; gap:10px; flex-wrap:wrap; }}
    .btn {{
      display:inline-flex;
      align-items:center;
      justify-content:center;
      text-decoration:none;
      color:white;
      padding:10px 14px;
      border-radius:10px;
      background:rgba(255,255,255,0.08);
      border:1px solid rgba(255,255,255,0.25);
      cursor:pointer;
      font: inherit;
      min-width: 160px;
    }}
    .btn:disabled {{
      opacity: 0.7;
      cursor: not-allowed;
    }}
    .container {{ padding: 24px 28px 40px; }}
    .filters, .kpi, .panel, .table-panel {{ background:white; border-radius:16px; box-shadow:0 6px 18px rgba(17,24,39,0.08); }}
    .filters {{ padding:16px; display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px; }}
    .filters select, .filters input, .filters button {{ padding:9px 12px; border:1px solid #d1d5db; border-radius:10px; }}
    .kpis {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(220px,1fr)); gap:16px; margin-bottom:24px; }}
    .kpi {{ padding:18px 20px; }}
    .kpi-label {{ font-size:.79rem; color:#6b7280; margin-bottom:10px; font-weight:700; text-transform:uppercase; }}
    .kpi-value {{ font-size:1.9rem; font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:1.3fr 1fr; gap:20px; margin-bottom:24px; }}
    .panel {{ padding:18px 20px; }}
    .panel h2, .table-panel h2 {{ margin:0 0 14px; font-size:1rem; color:#183a66; }}
    .table-panel {{ padding:18px 20px; overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:.88rem; }}
    thead {{ background:#eef2f7; }}
    th, td {{ padding:10px 12px; border-bottom:1px solid #e5e7eb; text-align:left; }}
    .tag {{ display:inline-block; padding:4px 8px; border-radius:999px; font-size:.72rem; font-weight:700; }}
    .tag-danger {{ background:#fdecea; color:#b42318; }}
    .tag-ok {{ background:#e8f8ef; color:#15803d; }}
    #update-status {{
      margin-top: 10px;
      font-size: 0.9rem;
      opacity: 0.95;
    }}
    @media (max-width: 960px) {{ .grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <div class="header-row">
      <div>
        <h1>🧭 Visão do Gerente de Projetos</h1>
        <div>Acompanhamento tático consolidado das demandas por cliente, status, bloqueio, esforço e horas executadas.</div>
        <div id="update-status"></div>
      </div>
      <div class="header-actions">
        <a class="btn" href="pm_flow_view.html">📈 Ver visão de flow</a>
        <button class="btn" id="update-btn" onclick="updateData()">🔄 Atualizar dados</button>
      </div>
    </div>
  </header>

  <div class="container">
    <section class="filters">
      <label>Cliente:</label>
      <select id="filter-client">
        <option value="">Todos</option>
      </select>

      <label>Status:</label>
      <select id="filter-status">
        <option value="">Todos</option>
        <option value="To Do">To Do</option>
        <option value="Doing">Doing</option>
        <option value="Done">Done</option>
      </select>

      <label>Bloqueado:</label>
      <select id="filter-block">
        <option value="">Todos</option>
        <option value="true">Sim</option>
        <option value="false">Não</option>
      </select>

      <label>Buscar:</label>
      <input type="text" id="filter-search" placeholder="Pesquisar demanda...">

      <button id="apply-filters">Aplicar</button>
      <button id="clear-filters">Limpar</button>
    </section>

    <section class="kpis">
      <div class="kpi">
        <div class="kpi-label">Total de demandas</div>
        <div class="kpi-value" id="kpi-total">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Effort total</div>
        <div class="kpi-value" id="kpi-effort">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Horas executadas</div>
        <div class="kpi-value" id="kpi-executed">0</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Bloqueadas</div>
        <div class="kpi-value" id="kpi-blocked">0</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Demandas por cliente</h2>
        <canvas id="clienteChart"></canvas>
      </div>
      <div class="panel">
        <h2>Status das demandas</h2>
        <canvas id="statusChart"></canvas>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Prioridade</h2>
        <canvas id="priorityChart"></canvas>
      </div>
      <div class="panel">
        <h2>Risco</h2>
        <canvas id="riskChart"></canvas>
      </div>
    </section>

    <section class="table-panel">
      <h2>Backlog operacional</h2>
      <table>
        <thead>
          <tr>
            <th>Cliente</th>
            <th>Demanda</th>
            <th>Status</th>
            <th>Bloqueado</th>
            <th>Prioridade</th>
            <th>Risco</th>
            <th>Effort</th>
            <th>Horas Executadas</th>
            <th>Data Compromisso</th>
            <th>Prazo Trello</th>
            <th>Última atualização</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </section>
  </div>

  <script>
    const DATA = {data_json};
    const CLIENTES = {clientes_json};

    const filterClient = document.getElementById('filter-client');
    const filterStatus = document.getElementById('filter-status');
    const filterBlock = document.getElementById('filter-block');
    const filterSearch = document.getElementById('filter-search');

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

    function updateKPIs(data) {{
      const total = data.length;
      const effort = data.reduce((acc, item) => acc + (item.effort || 0), 0);
      const executed = data.reduce((acc, item) => acc + (item.executed_hours || 0), 0);
      const blocked = data.filter(item => item.bloqueado).length;

      document.getElementById('kpi-total').textContent = total;
      document.getElementById('kpi-effort').textContent = effort.toFixed(0);
      document.getElementById('kpi-executed').textContent = executed.toFixed(0);
      document.getElementById('kpi-blocked').textContent = blocked;
    }}

    function updateCharts(data) {{
      const clienteCounts = countBy(data, 'cliente', 'Sem cliente');
      const statusCounts = countBy(data, 'status', 'Não definido');
      const priorityCounts = countBy(data, 'priority', 'Sem prioridade');
      const riskCounts = countBy(data, 'risk', 'Sem risco');

      clienteChart.data.labels = Object.keys(clienteCounts);
      clienteChart.data.datasets[0].data = Object.values(clienteCounts);
      clienteChart.update();

      statusChart.data.labels = Object.keys(statusCounts);
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

      data.forEach(item => {{
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${{item.cliente}}</td>
          <td>${{item.titulo}}</td>
          <td>${{item.status}}</td>
          <td>${{item.bloqueado ? '<span class="tag tag-danger">Sim</span>' : '<span class="tag tag-ok">Não</span>'}}</td>
          <td>${{item.priority}}</td>
          <td>${{item.risk}}</td>
          <td>${{item.effort ?? ''}}</td>
          <td>${{item.executed_hours ?? ''}}</td>
          <td>${{item.data_compromisso || ''}}</td>
          <td>${{item.due_date || ''}}</td>
          <td>${{item.last_activity || ''}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function applyFilters() {{
      const client = filterClient.value;
      const status = filterStatus.value;
      const block = filterBlock.value;
      const search = filterSearch.value.toLowerCase();

      const filtered = DATA.filter(item => {{
        const matchClient = !client || item.cliente === client;
        const matchStatus = !status || item.status === status;
        const matchBlock = !block || String(item.bloqueado) === block;
        const matchSearch = !search || item.titulo.toLowerCase().includes(search);
        return matchClient && matchStatus && matchBlock && matchSearch;
      }});

      updateKPIs(filtered);
      updateCharts(filtered);
      updateTable(filtered);
    }}

    async function updateData() {{
      const btn = document.getElementById("update-btn");
      const statusBox = document.getElementById("update-status");

      const confirmed = confirm("Deseja atualizar os dados agora?");
      if (!confirmed) return;

      btn.disabled = true;
      btn.innerText = "⏳ Atualizando...";
      statusBox.innerText = "Executando atualização do pipeline...";

      try {{
        const response = await fetch("http://192.168.100.10:5000/update", {{
          method: "POST"
        }});

        const data = await response.json();

        if (data.status === "success") {{
          statusBox.innerText = "Atualização concluída com sucesso. Recarregando a página...";
          setTimeout(() => {{
            window.location.reload();
          }}, 1200);
        }} else {{
          const errorText = data.error || "Erro desconhecido";
          statusBox.innerText = "Falha na atualização.";
          alert("Erro na atualização:\\n\\n" + errorText);
        }}
      }} catch (error) {{
        statusBox.innerText = "Falha ao conectar ao serviço de atualização.";
        alert("Erro ao conectar com o servidor de atualização:\\n\\n" + error);
      }} finally {{
        btn.disabled = false;
        btn.innerText = "🔄 Atualizar dados";
      }}
    }}

    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('clear-filters').addEventListener('click', () => {{
      filterClient.value = '';
      filterStatus.value = '';
      filterBlock.value = '';
      filterSearch.value = '';
      applyFilters();
    }});

    updateKPIs(DATA);
    updateCharts(DATA);
    updateTable(DATA);
  </script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"View do gerente de projetos gerada em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()


