from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = BASE_DIR / "demo"

INPUT_FILE = DEMO_DIR / "forecast_montecarlo_summary_demo.json"
OUTPUT_FILE = DEMO_DIR / "pm_forecast_view_demo.html"


def main():
    if not INPUT_FILE.exists():
        print("Arquivo forecast_montecarlo_summary_demo.json não encontrado")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Demo - Probabilistic Forecast</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {{
    font-family: Arial;
    background:#f4f7fb;
    margin:0;
}}

header {{
    background:#183a66;
    color:white;
    padding:20px;
}}

.container {{
    padding:20px;
}}

.kpis {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
    gap:15px;
    margin-bottom:20px;
}}

.kpi {{
    background:white;
    padding:15px;
    border-radius:10px;
}}

.grid {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:20px;
}}

.panel {{
    background:white;
    padding:15px;
    border-radius:10px;
}}

.table-panel {{
    margin-top:20px;
    background:white;
    padding:15px;
    border-radius:10px;
}}

table {{
    width:100%;
    border-collapse:collapse;
}}

th,td {{
    padding:8px;
    border-bottom:1px solid #ddd;
}}
</style>
</head>

<body>

<header>
<h1>🎯 DEMO - Probabilistic Forecast</h1>
<div>Simulação realista com Monte Carlo baseada em dados fictícios</div>
</header>

<div class="container">

<div class="kpis">
<div class="kpi"><b>Cards</b><br>{data["backlog_snapshot"]["open_cards"]}</div>
<div class="kpi"><b>Story Points</b><br>{data["backlog_snapshot"]["total_story_points"]}</div>
<div class="kpi"><b>Effort</b><br>{data["backlog_snapshot"]["total_effort"]}</div>
<div class="kpi"><b>Histórico</b><br>{data["historical_base"]["completed_cards"]}</div>
</div>

<div class="grid">
<div class="panel">
<h3>Cards</h3>
<canvas id="chartCards"></canvas>
</div>

<div class="panel">
<h3>Effort</h3>
<canvas id="chartEffort"></canvas>
</div>
</div>

<div class="grid">
<div class="panel">
<h3>Story Points</h3>
<canvas id="chartStory"></canvas>
</div>

<div class="panel">
<h3>Interpretação</h3>
<p>P50 = cenário provável<br>
P70/P85 = conservador<br>
P95 = alta segurança</p>
</div>
</div>

<div class="table-panel">
<h3>Resumo</h3>
<table>
<tr><th>Modelo</th><th>P50</th><th>P70</th><th>P85</th><th>P95</th></tr>
<tr>
<td>Cards</td>
<td>{data["forecast_by_cards"]["p50"]}</td>
<td>{data["forecast_by_cards"]["p70"]}</td>
<td>{data["forecast_by_cards"]["p85"]}</td>
<td>{data["forecast_by_cards"]["p95"]}</td>
</tr>

<tr>
<td>Story Points</td>
<td>{data["forecast_by_story_points"]["p50"]}</td>
<td>{data["forecast_by_story_points"]["p70"]}</td>
<td>{data["forecast_by_story_points"]["p85"]}</td>
<td>{data["forecast_by_story_points"]["p95"]}</td>
</tr>

<tr>
<td>Effort</td>
<td>{data["forecast_by_effort"]["p50"]}</td>
<td>{data["forecast_by_effort"]["p70"]}</td>
<td>{data["forecast_by_effort"]["p85"]}</td>
<td>{data["forecast_by_effort"]["p95"]}</td>
</tr>
</table>
</div>

</div>

<script>
const data = {json.dumps(data)};

function histogram(values) {{
    const buckets = {{}};
    values.forEach(v => {{
        const k = Math.round(v);
        buckets[k] = (buckets[k]||0)+1;
    }});
    return {{
        labels:Object.keys(buckets),
        values:Object.values(buckets)
    }};
}}

const cards = histogram(data.raw_samples.cards||[]);
const effort = histogram(data.raw_samples.effort||[]);
const story = histogram(data.raw_samples.story_points||[]);

new Chart(document.getElementById('chartCards'), {{
type:'bar',
data:{{labels:cards.labels,datasets:[{{data:cards.values}}]}}
}});

new Chart(document.getElementById('chartEffort'), {{
type:'bar',
data:{{labels:effort.labels,datasets:[{{data:effort.values}}]}}
}});

new Chart(document.getElementById('chartStory'), {{
type:'bar',
data:{{labels:story.labels,datasets:[{{data:story.values}}]}}
}});
</script>

</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Demo gerada em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()


