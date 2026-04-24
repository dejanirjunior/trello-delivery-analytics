from pathlib import Path
from html import escape
import json
import pandas as pd

from client_config import load_clients

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_FILE = DATA_DIR / "kanban_dataset.csv"


STATUS_ORDER = ["To Do", "Doing", "Done", "Block"]


def safe(v):
    if pd.isna(v):
        return ""
    return escape(str(v))


def pct(part, total):
    return int((part / total) * 100) if total else 0


def counts_for(df, column):
    if column not in df.columns:
        return {}, [], []

    counts = df[column].fillna("Não informado").astype(str).value_counts().to_dict()
    labels = list(counts.keys())
    values = [int(v) for v in counts.values()]
    return counts, labels, values


def build_dashboard_html(cliente, slug, df):
    total = len(df)
    done = len(df[df["status_kanban"] == "Done"])
    blocked = len(df[df["status_kanban"] == "Block"])
    doing = len(df[df["status_kanban"] == "Doing"])
    todo = len(df[df["status_kanban"] == "To Do"])
    progress = pct(done, total)

    high_risk = 0
    if "risk" in df.columns:
        high_risk = len(df[df["risk"].astype(str).str.lower() == "high"])

    status_values = [todo, doing, done, blocked]
    status_labels = ["To Do", "Doing", "Done", "Block"]

    _, module_labels, module_values = counts_for(df, "modulos")
    _, risk_labels, risk_values = counts_for(df, "risk")
    _, priority_labels, priority_values = counts_for(df, "priority")

    critical = df[
        (df["status_kanban"] == "Block")
        | (df.get("risk", "").astype(str).str.lower() == "high")
    ].head(20)

    rows = ""
    for _, r in critical.iterrows():
        rows += f"""
        <tr>
            <td>{safe(r.get("titulo"))}</td>
            <td>{safe(r.get("status_kanban"))}</td>
            <td>{safe(r.get("modulos", "Sem módulo informado"))}</td>
            <td>{safe(r.get("risk", "Sem risco"))}</td>
            <td>{safe(r.get("priority", "Sem prioridade"))}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe(cliente)} · Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
:root {{
  --bg:#0b0f1a;
  --surface:#131929;
  --surface2:#1a2238;
  --border:rgba(255,255,255,.08);
  --text:#e8eaf0;
  --muted:#8891a8;
  --gold:#c9a84c;
  --gold-light:#e4c97e;
  --done:#3ecf8e;
  --progress:#4f8ef7;
  --blocked:#f06565;
  --todo:#454f65;
}}

* {{
  box-sizing:border-box;
  margin:0;
  padding:0;
}}

body {{
  font-family:'DM Sans', sans-serif;
  background:
    radial-gradient(circle at top left, rgba(201,168,76,.08), transparent 28%),
    radial-gradient(circle at top right, rgba(79,142,247,.08), transparent 30%),
    var(--bg);
  color:var(--text);
  min-height:100vh;
}}

body::before {{
  content:'';
  position:fixed;
  inset:0;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events:none;
  opacity:.5;
}}

.page {{
  position:relative;
  z-index:1;
  max-width:1200px;
  margin:0 auto;
  padding:40px 32px 80px;
}}

.header {{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:24px;
  margin-bottom:42px;
  padding-bottom:32px;
  border-bottom:1px solid var(--border);
}}

.eyebrow {{
  font-size:11px;
  font-weight:700;
  letter-spacing:.18em;
  color:var(--gold);
  text-transform:uppercase;
  margin-bottom:10px;
}}

.header h1 {{
  font-family:'DM Serif Display', serif;
  font-size:42px;
  line-height:1.1;
}}

.header h1 em {{
  color:var(--gold-light);
}}

.header-sub {{
  color:var(--muted);
  margin-top:8px;
  font-size:13px;
}}

.top-nav {{
  margin-top:18px;
  display:flex;
  gap:10px;
  flex-wrap:wrap;
}}

.nav-btn {{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:112px;
  padding:9px 15px;
  border-radius:999px;
  background:var(--surface2);
  color:var(--text);
  font-size:12px;
  font-weight:700;
  text-decoration:none;
  border:1px solid rgba(255,255,255,.14);
}}

.nav-btn.active {{
  background:linear-gradient(90deg,var(--gold),var(--gold-light));
  color:#0b0f1a;
  border-color:transparent;
}}

.header-kpi {{
  text-align:right;
  color:var(--muted);
  font-size:12px;
}}

.header-kpi strong {{
  display:block;
  color:var(--text);
  font-size:24px;
}}

.kpis {{
  display:grid;
  grid-template-columns:repeat(4, 1fr);
  gap:16px;
  margin-bottom:28px;
}}

.kpi {{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:16px;
  padding:22px;
  box-shadow:0 20px 70px rgba(0,0,0,.18);
}}

.kpi-label {{
  font-size:11px;
  color:var(--muted);
  text-transform:uppercase;
  letter-spacing:.12em;
  font-weight:700;
  margin-bottom:8px;
}}

.kpi-value {{
  font-family:'DM Serif Display', serif;
  font-size:38px;
  line-height:1;
}}

.kpi-note {{
  color:var(--muted);
  font-size:12px;
  margin-top:8px;
}}

.grid {{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:18px;
  margin-bottom:18px;
}}

.panel {{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:18px;
  padding:22px;
  min-height:330px;
}}

.panel h2 {{
  font-size:12px;
  color:var(--gold);
  text-transform:uppercase;
  letter-spacing:.14em;
  margin-bottom:18px;
}}

.chart-wrap {{
  height:260px;
}}

.table-panel {{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:18px;
  padding:22px;
  margin-top:18px;
  overflow-x:auto;
}}

.table-panel h2 {{
  font-size:12px;
  color:var(--gold);
  text-transform:uppercase;
  letter-spacing:.14em;
  margin-bottom:16px;
}}

table {{
  width:100%;
  border-collapse:collapse;
  font-size:12px;
}}

th {{
  color:var(--muted);
  text-align:left;
  text-transform:uppercase;
  letter-spacing:.08em;
  font-size:10px;
  padding:10px;
  border-bottom:1px solid var(--border);
}}

td {{
  padding:12px 10px;
  border-bottom:1px solid rgba(255,255,255,.05);
  color:var(--text);
}}

.footer {{
  margin-top:58px;
  padding-top:24px;
  border-top:1px solid var(--border);
  display:flex;
  justify-content:space-between;
  font-size:11px;
  color:var(--muted);
}}

@media (max-width: 900px) {{
  .header {{
    flex-direction:column;
  }}

  .header-kpi {{
    text-align:left;
  }}

  .kpis,
  .grid {{
    grid-template-columns:1fr;
  }}
}}
</style>
</head>

<body>
<div class="page">

<header class="header">
  <div>
    <div class="eyebrow">Dashboard Analítico · Projeto</div>
    <h1>{safe(cliente)} — <em>Dashboard</em></h1>
    <div class="header-sub">Indicadores complementares da operação do projeto</div>

    <div class="top-nav">
      <a href="/views/executive_{slug}.html" class="nav-btn">📊 Executivo</a>
      <a href="/views/dashboard_{slug}.html" class="nav-btn active">📈 Dashboard</a>
    </div>
  </div>

  <div class="header-kpi">
    <strong>{progress}%</strong>
    Progresso global
  </div>
</header>

<section class="kpis">
  <div class="kpi">
    <div class="kpi-label">Total de cards</div>
    <div class="kpi-value">{total}</div>
    <div class="kpi-note">Demandas monitoradas</div>
  </div>

  <div class="kpi">
    <div class="kpi-label">Progresso</div>
    <div class="kpi-value">{progress}%</div>
    <div class="kpi-note">Done / Total</div>
  </div>

  <div class="kpi">
    <div class="kpi-label">Bloqueados</div>
    <div class="kpi-value">{blocked}</div>
    <div class="kpi-note">Cards em Block</div>
  </div>

  <div class="kpi">
    <div class="kpi-label">Risco alto</div>
    <div class="kpi-value">{high_risk}</div>
    <div class="kpi-note">Itens com exposição elevada</div>
  </div>
</section>

<section class="grid">
  <div class="panel">
    <h2>Distribuição por status</h2>
    <div class="chart-wrap"><canvas id="statusChart"></canvas></div>
  </div>

  <div class="panel">
    <h2>Distribuição por módulo</h2>
    <div class="chart-wrap"><canvas id="moduleChart"></canvas></div>
  </div>
</section>

<section class="grid">
  <div class="panel">
    <h2>Risco</h2>
    <div class="chart-wrap"><canvas id="riskChart"></canvas></div>
  </div>

  <div class="panel">
    <h2>Prioridade</h2>
    <div class="chart-wrap"><canvas id="priorityChart"></canvas></div>
  </div>
</section>

<section class="table-panel">
  <h2>Cards críticos</h2>
  <table>
    <thead>
      <tr>
        <th>Card</th>
        <th>Status</th>
        <th>Módulo</th>
        <th>Risco</th>
        <th>Prioridade</th>
      </tr>
    </thead>
    <tbody>
      {rows if rows else '<tr><td colspan="5">Nenhum card crítico encontrado.</td></tr>'}
    </tbody>
  </table>
</section>

<div class="footer">
  <div>Gerado automaticamente com base nos dados do Trello · Optaris</div>
  <div>{safe(cliente)} · {total} cards · {progress}% de progresso</div>
</div>

</div>

<script>
Chart.defaults.color = '#8891a8';
Chart.defaults.borderColor = 'rgba(255,255,255,0.08)';
Chart.defaults.font.family = 'DM Sans';

const colors = ['#454f65', '#4f8ef7', '#3ecf8e', '#f06565', '#c9a84c', '#f0a046', '#a78bfa', '#38bdf8'];

function makeBarChart(id, labels, values, label) {{
  new Chart(document.getElementById(id), {{
    type: 'bar',
    data: {{
      labels,
      datasets: [{{
        label,
        data: values,
        backgroundColor: colors,
        borderRadius: 8
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }}
      }},
      scales: {{
        y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }},
        x: {{ grid: {{ display: false }} }}
      }}
    }}
  }});
}}

function makeDoughnutChart(id, labels, values) {{
  new Chart(document.getElementById(id), {{
    type: 'doughnut',
    data: {{
      labels,
      datasets: [{{
        data: values,
        backgroundColor: colors,
        borderWidth: 0
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {{
        legend: {{
          position: 'bottom',
          labels: {{
            boxWidth: 10,
            usePointStyle: true
          }}
        }}
      }}
    }}
  }});
}}

makeBarChart('statusChart', {json.dumps(status_labels)}, {json.dumps(status_values)}, 'Cards');
makeDoughnutChart('moduleChart', {json.dumps(module_labels)}, {json.dumps(module_values)});
makeBarChart('riskChart', {json.dumps(risk_labels)}, {json.dumps(risk_values)}, 'Cards');
makeDoughnutChart('priorityChart', {json.dumps(priority_labels)}, {json.dumps(priority_values)});
</script>

</body>
</html>
"""


def generate():
    if not INPUT_FILE.exists():
        print("Arquivo kanban_dataset.csv não encontrado")
        return

    df = pd.read_csv(INPUT_FILE)
    clients = load_clients()

    for client in clients:
        name = client["name"]
        slug = client["slug"]

        df_client = df[df["cliente"] == name].copy()
        html = build_dashboard_html(name, slug, df_client)

        output = DATA_DIR / f"dashboard_{slug}.html"
        output.write_text(html, encoding="utf-8")

        print(f"Gerado: {output}")


if __name__ == "__main__":
    generate()
