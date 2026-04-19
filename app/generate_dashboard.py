from pathlib import Path
import json
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "kanban_dataset.csv"


def slugify(text):
    text = str(text).strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s-]+", "_", text)
    return text


def build_dashboard_html(cliente, df_cliente):
    total_cards = len(df_cliente)
    total_effort = pd.to_numeric(df_cliente["effort"], errors="coerce").fillna(0).sum()
    total_executed = pd.to_numeric(df_cliente["total_horas_executado"], errors="coerce").fillna(0).sum()
    bloqueados = int(df_cliente["bloqueado"].fillna(False).astype(bool).sum())

    status_counts = (
        df_cliente["status_kanban"]
        .fillna("Não definido")
        .value_counts()
        .reindex(["To Do", "Doing", "Done"], fill_value=0)
    )

    priority_counts = df_cliente["priority"].fillna("Sem prioridade").value_counts()
    risk_counts = df_cliente["risk"].fillna("Sem risco").value_counts()

    table_df = df_cliente[[
        "titulo",
        "status_kanban",
        "priority",
        "risk",
        "bloqueado",
        "effort",
        "total_horas_executado",
        "data_compromisso",
        "due_date"
    ]].copy()

    table_df["priority"] = table_df["priority"].fillna("Sem prioridade")
    table_df["risk"] = table_df["risk"].fillna("Sem risco")
    table_df["effort"] = pd.to_numeric(table_df["effort"], errors="coerce").fillna(0)
    table_df["total_horas_executado"] = pd.to_numeric(table_df["total_horas_executado"], errors="coerce").fillna(0)
    table_df["bloqueado"] = table_df["bloqueado"].apply(lambda x: "Sim" if bool(x) else "Não")
    table_df["data_compromisso"] = table_df["data_compromisso"].fillna("Não informada")
    table_df["due_date"] = table_df["due_date"].fillna("Não informada")

    rows = []
    for _, row in table_df.iterrows():
        rows.append(f"""
        <tr>
            <td>{row['titulo']}</td>
            <td>{row['status_kanban']}</td>
            <td>{row['priority']}</td>
            <td>{row['risk']}</td>
            <td>{row['bloqueado']}</td>
            <td>{row['effort']}</td>
            <td>{row['total_horas_executado']}</td>
            <td>{row['data_compromisso']}</td>
            <td>{row['due_date']}</td>
        </tr>
        """)

    status_labels = json.dumps(list(status_counts.index))
    status_values = json.dumps([int(v) for v in status_counts.values])

    priority_labels = json.dumps([str(x) for x in priority_counts.index.tolist()])
    priority_values = json.dumps([int(v) for v in priority_counts.values.tolist()])

    risk_labels = json.dumps([str(x) for x in risk_counts.index.tolist()])
    risk_values = json.dumps([int(v) for v in risk_counts.values.tolist()])

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Executivo - {cliente}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f8; margin: 0; color: #1f2937; }}
    header {{ background: #183a66; color: white; padding: 22px 28px; box-shadow: 0 2px 8px rgba(0,0,0,0.18); }}
    header h1 {{ margin: 0; font-size: 1.4rem; }}
    header p {{ margin: 6px 0 0; opacity: 0.85; font-size: 0.95rem; }}
    .container {{ padding: 24px 28px 40px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .kpi {{ background: white; border-radius: 14px; padding: 18px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .kpi-label {{ font-size: 0.82rem; color: #6b7280; margin-bottom: 8px; font-weight: 600; text-transform: uppercase; }}
    .kpi-value {{ font-size: 1.8rem; font-weight: 700; color: #111827; }}
    .grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 24px; }}
    .panel {{ background: white; border-radius: 14px; padding: 18px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .panel h2 {{ margin: 0 0 14px; font-size: 1rem; color: #183a66; }}
    .table-panel {{ background: white; border-radius: 14px; padding: 18px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
    thead {{ background: #eef2f7; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; }}
  </style>
</head>
<body>
  <header>
    <h1>📊 Dashboard Executivo - {cliente}</h1>
    <p>Visão consolidada do andamento das demandas do cliente</p>
  </header>

  <div class="container">
    <section class="kpis">
      <div class="kpi">
        <div class="kpi-label">Total de demandas</div>
        <div class="kpi-value">{total_cards}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Effort total</div>
        <div class="kpi-value">{total_effort:.0f}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Horas executadas</div>
        <div class="kpi-value">{total_executed:.0f}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Bloqueadas</div>
        <div class="kpi-value">{bloqueados}</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Status das demandas</h2>
        <canvas id="statusChart"></canvas>
      </div>
      <div class="panel">
        <h2>Prioridade</h2>
        <canvas id="priorityChart"></canvas>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Risco</h2>
        <canvas id="riskChart"></canvas>
      </div>
      <div class="panel">
        <h2>Resumo executivo</h2>
        <p style="line-height:1.7; font-size:0.95rem;">
          Este painel apresenta a distribuição atual das demandas do cliente, com foco em andamento, bloqueios,
          esforço planejado, horas executadas e exposição a risco.
        </p>
      </div>
    </section>

    <section class="table-panel">
      <h2>Demandas em acompanhamento</h2>
      <table>
        <thead>
          <tr>
            <th>Demanda</th>
            <th>Status</th>
            <th>Prioridade</th>
            <th>Risco</th>
            <th>Bloqueado</th>
            <th>Effort</th>
            <th>Horas Executadas</th>
            <th>Data Compromisso</th>
            <th>Prazo Trello</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>
  </div>

  <script>
    const statusLabels = {status_labels};
    const statusValues = {status_values};
    const priorityLabels = {priority_labels};
    const priorityValues = {priority_values};
    const riskLabels = {risk_labels};
    const riskValues = {risk_values};

    new Chart(document.getElementById('statusChart'), {{
      type: 'bar',
      data: {{
        labels: statusLabels,
        datasets: [{{ label: 'Demandas', data: statusValues }}]
      }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});

    new Chart(document.getElementById('priorityChart'), {{
      type: 'doughnut',
      data: {{
        labels: priorityLabels,
        datasets: [{{ data: priorityValues }}]
      }},
      options: {{ responsive: true }}
    }});

    new Chart(document.getElementById('riskChart'), {{
      type: 'bar',
      data: {{
        labels: riskLabels,
        datasets: [{{ label: 'Risco', data: riskValues }}]
      }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
    }});
  </script>
</body>
</html>
"""
    return html


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
        html = build_dashboard_html(cliente, df_cliente)

        output_file = DATA_DIR / f"dashboard_{slugify(cliente)}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Dashboard gerado em: {output_file}")


if __name__ == "__main__":
    main()


