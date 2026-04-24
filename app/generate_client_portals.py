from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


CLIENTS = {
    "4network": {
        "title": "Portal 4Network",
        "description": "Acompanhamento de projeto — visão restrita ao cliente.",
        "kanban": "kanban_4network.html",
        "dashboard": "dashboard_4network.html",
    },
    "consigaz": {
        "title": "Portal Consigaz",
        "description": "Acompanhamento de projeto — visão restrita ao cliente.",
        "kanban": "kanban_consigaz.html",
        "dashboard": "dashboard_consigaz.html",
    },
}


def build_portal(slug: str, config: dict) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>{config["title"]}</title>
<style>
    body {{
        font-family: Arial, sans-serif;
        background: #eef2f7;
        margin: 0;
        padding: 40px;
        color: #1f2937;
    }}

    .wrap {{
        max-width: 900px;
        margin: 0 auto;
    }}

    .header {{
        background: white;
        border: 1px solid #d6dde7;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
    }}

    h1 {{
        margin: 0 0 8px 0;
        font-size: 30px;
    }}

    p {{
        margin: 0;
        color: #667085;
    }}

    .grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(220px, 1fr));
        gap: 18px;
    }}

    .card {{
        background: white;
        border: 1px solid #d6dde7;
        border-radius: 16px;
        padding: 24px;
        text-decoration: none;
        color: #1f2937;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
        transition: 0.2s;
    }}

    .card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 18px rgba(16, 24, 40, 0.12);
    }}

    .card h2 {{
        margin: 0 0 8px 0;
        font-size: 22px;
    }}

    .card p {{
        color: #667085;
        font-size: 14px;
    }}
</style>
</head>
<body>
<div class="wrap">
    <div class="header">
        <h1>{config["title"]}</h1>
        <p>{config["description"]}</p>
    </div>

    <div class="grid">
        <a class="card" href="/clientes/{slug}/kanban">
            <h2>📌 Kanban</h2>
            <p>Visão operacional dos cards do projeto.</p>
        </a>

        <a class="card" href="/clientes/{slug}/dashboard">
            <h2>📊 Dashboard</h2>
            <p>Indicadores e visão executiva do projeto.</p>
        </a>
    </div>
</div>
</body>
</html>
"""


def main():
    for slug, config in CLIENTS.items():
        output_path = DATA_DIR / f"portal_{slug}.html"
        output_path.write_text(build_portal(slug, config), encoding="utf-8")
        print(f"Portal gerado: {output_path}")


if __name__ == "__main__":
    main()
