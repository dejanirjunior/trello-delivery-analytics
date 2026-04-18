from pathlib import Path
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


def main():
    if not INPUT_FILE.exists():
        print("Arquivo kanban_dataset.csv não encontrado em ./data")
        return

    df = pd.read_csv(INPUT_FILE)

    if "cliente" not in df.columns:
        print("Coluna 'cliente' não encontrada no dataset.")
        return

    clientes = sorted(df["cliente"].dropna().unique())

    for cliente in clientes:
        slug = slugify(cliente)

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Portal do Cliente - {cliente}</title>
  <style>
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f4f6f8;
      margin: 0;
      color: #1f2937;
    }}

    header {{
      background: #183a66;
      color: white;
      padding: 28px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.18);
    }}

    header h1 {{
      margin: 0;
      font-size: 1.5rem;
    }}

    header p {{
      margin: 8px 0 0;
      opacity: 0.9;
    }}

    .container {{
      max-width: 960px;
      margin: 0 auto;
      padding: 32px 20px 40px;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
    }}

    .card {{
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }}

    .card h2 {{
      margin: 0 0 10px;
      color: #183a66;
      font-size: 1.1rem;
    }}

    .card p {{
      margin: 0 0 18px;
      line-height: 1.6;
      color: #4b5563;
    }}

    .btn {{
      display: inline-block;
      text-decoration: none;
      background: #183a66;
      color: white;
      padding: 10px 16px;
      border-radius: 10px;
      font-weight: 600;
    }}

    .btn:hover {{
      opacity: 0.92;
    }}
  </style>
</head>
<body>
  <header>
    <h1>📁 Portal do Cliente - {cliente}</h1>
    <p>Acesse a visão operacional e a visão executiva do projeto.</p>
  </header>

  <div class="container">
    <div class="grid">
      <div class="card">
        <h2>🗂️ Kanban do Projeto</h2>
        <p>Visualização simplificada das demandas em andamento, com foco no acompanhamento operacional.</p>
        <a class="btn" href="kanban_{slug}.html">Abrir Kanban</a>
      </div>

      <div class="card">
        <h2>📊 Dashboard Executivo</h2>
        <p>Visão consolidada com indicadores, riscos, prioridades e acompanhamento das entregas do cliente.</p>
        <a class="btn" href="dashboard_{slug}.html">Abrir Dashboard</a>
      </div>
    </div>
  </div>
</body>
</html>
"""
        output_file = DATA_DIR / f"portal_{slug}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Portal do cliente gerado em: {output_file}")


if __name__ == "__main__":
    main()

