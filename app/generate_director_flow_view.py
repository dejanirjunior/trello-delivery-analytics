from pathlib import Path
import pandas as pd
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

THROUGHPUT = DATA_DIR / "throughput_weekly.csv"
LEADTIME = DATA_DIR / "lead_time_cards.csv"
BACKLOG = DATA_DIR / "flow_backlog_refinado_weekly.csv"
STAGE_TIMES = DATA_DIR / "stage_times.csv"

OUTPUT = DATA_DIR / "director_flow_view.html"


def load_csv_or_empty(path: Path, columns: list[str]) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)


def build_stage_summary(df_stage: pd.DataFrame) -> pd.DataFrame:
    if df_stage.empty:
        return pd.DataFrame(columns=["stage", "avg_days"])

    summary = (
        df_stage.groupby("stage", dropna=False)["duration_days"]
        .mean()
        .reset_index(name="avg_days")
    )

    desired_order = ["Refinado", "Em dev", "Q.A.", "UAT", "Concluído", "Deploy PRD"]
    summary["order"] = summary["stage"].apply(
        lambda x: desired_order.index(x) if x in desired_order else 999
    )
    summary = summary.sort_values("order").drop(columns=["order"])
    summary["avg_days"] = summary["avg_days"].round(2)
    return summary


def main():
    df_throughput = load_csv_or_empty(THROUGHPUT, ["week", "cards_entregues"])
    df_lead = load_csv_or_empty(
        LEADTIME,
        ["card_id", "card_name", "start_refinado", "end_done", "lead_time_days"],
    )
    df_backlog = load_csv_or_empty(BACKLOG, ["member", "week", "cards_puxados"])
    df_stage = load_csv_or_empty(
        STAGE_TIMES,
        ["card_id", "card_name", "stage", "entered_at", "left_at", "duration_days"],
    )

    avg_lead = round(df_lead["lead_time_days"].mean(), 2) if not df_lead.empty else 0
    total_delivered = int(df_throughput["cards_entregues"].sum()) if not df_throughput.empty else 0
    total_pulled = int(df_backlog["cards_puxados"].sum()) if not df_backlog.empty else 0

    stage_summary = build_stage_summary(df_stage)

    data = {
        "throughput": df_throughput.to_dict(orient="records"),
        "backlog": df_backlog.to_dict(orient="records"),
        "stage_summary": stage_summary.to_dict(orient="records"),
        "avg_lead": avg_lead,
        "total_delivered": total_delivered,
        "total_pulled": total_pulled,
    }

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flow - Diretoria</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg: #f4f7fb;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #183a66;
      --border: #e5e7eb;
      --shadow: 0 6px 18px rgba(17, 24, 39, 0.08);
      --radius: 16px;
      --blue: #285ea8;
      --navy: #183a66;
      --green: #15803d;
      --orange: #b45309;
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
    }}

    .subtitle {{
      margin-top: 8px;
      opacity: 0.9;
      font-size: 0.96rem;
      line-height: 1.5;
      max-width: 760px;
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

    .container {{
      padding: 24px 28px 40px;
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
      grid-template-columns: 1fr 1fr;
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
      max-height: 340px;
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
        <h1>📈 Visão de Flow - Diretoria</h1>
        <div class="subtitle">
          Indicadores executivos de fluxo, entrada de demanda, throughput, lead time médio e duração média por etapa,
          incluindo UAT e Deploy PRD.
        </div>
      </div>
      <div>
        <a class="btn" href="director_view.html">⬅ Voltar para visão executiva</a>
      </div>
    </div>
  </header>

  <div class="container">
    <section class="kpis">
      <div class="kpi">
        <div class="kpi-label">Total de entregas</div>
        <div class="kpi-value">{total_delivered}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Lead time médio (dias)</div>
        <div class="kpi-value">{avg_lead}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Cards puxados para refinado</div>
        <div class="kpi-value">{total_pulled}</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Throughput semanal</h2>
        <canvas id="throughput"></canvas>
      </div>

      <div class="panel">
        <h2>Entrada de demanda por semana</h2>
        <canvas id="backlog"></canvas>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Duração média por etapa (dias)</h2>
        <canvas id="stages"></canvas>
      </div>

      <div class="panel">
        <h2>Leitura executiva</h2>
        <p style="line-height:1.7; font-size:0.95rem;">
          Esta visão resume o comportamento do fluxo de entrega, destacando volume entregue, entrada de novas demandas,
          tempo médio de atravessamento e duração média por etapa do processo.
        </p>
      </div>
    </section>
  </div>

  <script>
    const data = {json.dumps(data, ensure_ascii=False)};

    new Chart(document.getElementById("throughput"), {{
      type: "line",
      data: {{
        labels: data.throughput.map(x => x.week),
        datasets: [{{
          label: "Cards entregues",
          data: data.throughput.map(x => x.cards_entregues),
          borderColor: "#285ea8",
          backgroundColor: "rgba(40,94,168,0.12)",
          fill: true,
          tension: 0.25
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ display: false }}
        }}
      }}
    }});

    new Chart(document.getElementById("backlog"), {{
      type: "bar",
      data: {{
        labels: data.backlog.map(x => `${{x.member}} - ${{x.week}}`),
        datasets: [{{
          label: "Cards puxados",
          data: data.backlog.map(x => x.cards_puxados),
          backgroundColor: "#183a66"
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ display: false }}
        }}
      }}
    }});

    new Chart(document.getElementById("stages"), {{
      type: "bar",
      data: {{
        labels: data.stage_summary.map(x => x.stage),
        datasets: [{{
          label: "Dias médios",
          data: data.stage_summary.map(x => x.avg_days),
          backgroundColor: "#b45309"
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ display: false }}
        }}
      }}
    }});
  </script>
</body>
</html>
"""

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print("Dashboard Diretor Flow gerado:", OUTPUT)


if __name__ == "__main__":
    main()


