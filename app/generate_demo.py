from pathlib import Path
import pandas as pd
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = BASE_DIR / "demo"

INPUT = DEMO_DIR / "sample_kanban_dataset.csv"
OUTPUT = DEMO_DIR / "demo_dashboard.html"


def main():
    df = pd.read_csv(INPUT)

    data = df.to_dict(orient="records")

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>Demo Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{ font-family: Arial; background: #f4f7fb; padding: 20px; }}
.card {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
</style>
</head>

<body>

<h1>Demo - Dashboard de Projetos</h1>

<div class="card">
<h2>Demandas por Cliente</h2>
<canvas id="chartCliente"></canvas>
</div>

<div class="card">
<h2>Status</h2>
<canvas id="chartStatus"></canvas>
</div>

<script>
const data = {json.dumps(data)};

function countBy(field) {{
  const result = {{}};
  data.forEach(d => {{
    const key = d[field] || "N/A";
    result[key] = (result[key] || 0) + 1;
  }});
  return result;
}}

const cliente = countBy("cliente");
new Chart(document.getElementById("chartCliente"), {{
  type: "bar",
  data: {{
    labels: Object.keys(cliente),
    datasets: [{{
      data: Object.values(cliente)
    }}]
  }}
}});

const status = countBy("status_kanban");
new Chart(document.getElementById("chartStatus"), {{
  type: "doughnut",
  data: {{
    labels: Object.keys(status),
    datasets: [{{
      data: Object.values(status)
    }}]
  }}
}});
</script>

</body>
</html>
"""

    with open(OUTPUT, "w") as f:
        f.write(html)

    print("Demo gerado:", OUTPUT)


if __name__ == "__main__":
    main()
