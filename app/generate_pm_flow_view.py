from pathlib import Path
import pandas as pd
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

LEADTIME = DATA_DIR / "lead_time_cards.csv"
BACKLOG = DATA_DIR / "flow_backlog_refinado_weekly.csv"
STAGE_TIMES = DATA_DIR / "stage_times.csv"

OUTPUT = DATA_DIR / "pm_flow_view.html"


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
    max_lead = round(df_lead["lead_time_days"].max(), 2) if not df_lead.empty else 0
    total_pulled = int(df_backlog["cards_puxados"].sum()) if not df_backlog.empty else 0

    stage_summary = build_stage_summary(df_stage)

    data = {
        "lead": df_lead.to_dict(orient="records"),
        "backlog": df_backlog.to_dict(orient="records"),
        "stage_summary": stage_summary.to_dict(orient="records"),
        "avg_lead": avg_lead,
        "max_lead": max_lead,
        "total_pulled": total_pulled,
    }

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flow - PM</title>
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
      max-height: 360px;
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
        <h1>📈 Visão de Flow - PM</h1>
        <div class="subtitle">
          Indicadores de fluxo para gestão tática: lead time por card, puxada de backlog para refinado
          e duração média por etapa, incluindo UAT e Deploy PRD.
        </div>
      </div>
      <div>
        <a class="btn" href="pm_view.html">⬅ Voltar para visão tática</a>
      </div>
    </div>
  </header>

  <div class="container">
    <section class="kpis">
      <div class="kpi">
        <div class="kpi-label">Lead time médio (dias)</div>
        <div class="kpi-value">{avg_lead}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Maior lead time (dias)</div>
        <div class="kpi-value">{max_lead}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Cards puxados para refinado</div>
        <div class="kpi-value">{total_pulled}</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Lead time por card</h2>
        <canvas id="lead"></canvas>
      </div>

      <div class="panel">
        <h2>Backlog → Refinado por responsável</h2>
        <canvas id="backlog"></canvas>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Duração média por etapa (dias)</h2>
        <canvas id="stages"></canvas>
      </div>

      <div class="panel">
        <h2>Leitura tática</h2>
        <p style="line-height:1.7; font-size:0.95rem;">
          Esta visão apoia a gestão do fluxo com foco em tempo de atravessamento, entrada de demanda
          e permanência média em cada etapa, incluindo validação interna, UAT do cliente e deploy em produção.
        </p>
      </div>
    </section>
  </div>

  <script>
    const data = {json.dumps(data, ensure_ascii=False)};

    new Chart(document.getElementById("lead"), {{
      type: "bar",
      data: {{
        labels: data.lead.map(x => x.card_name),
        datasets: [{{
          label: "Lead Time (dias)",
          data: data.lead.map(x => x.lead_time_days),
          backgroundColor: "#285ea8"
        }}]
      }},
      options: {{
        indexAxis: 'y',
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

    print("Dashboard PM Flow gerado:", OUTPUT)


if __name__ == "__main__":
    main()


