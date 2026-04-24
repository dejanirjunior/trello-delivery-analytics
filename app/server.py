from flask import Flask, jsonify, send_from_directory, request, redirect
from flask_cors import CORS
import subprocess
from pathlib import Path
import json
import re

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
CLIENTS_FILE = CONFIG_DIR / "clients.json"


def load_clients():
    if not CLIENTS_FILE.exists():
        return {"clients": []}

    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_clients(data):
    CONFIG_DIR.mkdir(exist_ok=True)

    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "Servidor de atualização ativo"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "trello-dashboard-update-server"
    })


@app.route("/update", methods=["POST"])
def update():
    try:
        main_script = str(BASE_DIR / "app" / "main.py")

        result = subprocess.run(
            ["python3", main_script],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )

        status = "success" if result.returncode == 0 else "error"

        return jsonify({
            "status": status,
            "output": result.stdout[-4000:],
            "warnings": result.stderr[-4000:] if status == "success" and result.stderr else None,
            "error": result.stderr[-4000:] if status == "error" else None
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/admin/clientes", methods=["GET"])
def admin_clientes():
    data = load_clients()
    clients = data.get("clients", [])

    rows = ""
    for client in clients:
        name = client.get("name", "")
        slug = client.get("slug", "")

        rows += f"""
        <tr>
            <td>{name}</td>
            <td><code>{slug}</code></td>
            <td>
                <a href="/views/portal_{slug}.html" target="_blank">Portal</a>
                <a href="/views/executive_{slug}.html" target="_blank">Executivo</a>
                <a href="/views/kanban_{slug}.html" target="_blank">Kanban</a>
                <a href="/views/dashboard_{slug}.html" target="_blank">Dashboard</a>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Admin · Clientes</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #eef2f7;
                margin: 0;
                padding: 30px;
                color: #1f2937;
            }}

            .wrap {{
                max-width: 1000px;
                margin: 0 auto;
            }}

            .header {{
                background: #ffffff;
                border: 1px solid #d6dde7;
                border-radius: 14px;
                padding: 22px;
                margin-bottom: 18px;
                box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
            }}

            h1 {{
                margin: 0 0 6px 0;
                font-size: 28px;
            }}

            p {{
                margin: 0;
                color: #667085;
            }}

            .card {{
                background: #ffffff;
                border: 1px solid #d6dde7;
                border-radius: 14px;
                padding: 20px;
                margin-bottom: 18px;
                box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
            }}

            label {{
                display: block;
                font-weight: 700;
                margin-bottom: 6px;
                font-size: 13px;
            }}

            input {{
                width: 100%;
                padding: 11px;
                border: 1px solid #cfd6df;
                border-radius: 10px;
                margin-bottom: 12px;
                font-size: 14px;
            }}

            button {{
                background: #0d6efd;
                color: #ffffff;
                border: none;
                padding: 12px 18px;
                border-radius: 10px;
                font-weight: 700;
                cursor: pointer;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }}

            th, td {{
                border-bottom: 1px solid #e5e7eb;
                padding: 12px;
                text-align: left;
            }}

            th {{
                color: #475467;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: .08em;
            }}

            a {{
                display: inline-block;
                margin-right: 10px;
                color: #0d6efd;
                font-weight: 700;
                text-decoration: none;
            }}

            .hint {{
                background: #eef4ff;
                border: 1px solid #d7e3ff;
                color: #38517a;
                padding: 12px;
                border-radius: 10px;
                font-size: 13px;
                line-height: 1.4;
                margin-top: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="header">
                <h1>Cadastro de Clientes</h1>
                <p>Clientes cadastrados aqui entram no processo de geração de views do Trello.</p>
                <div class="hint">
                    Para trazer dados, o Trello precisa ter uma label com o mesmo nome do cliente.
                    Exemplo: cliente <strong>4Network</strong> precisa da label <strong>4Network</strong>.
                </div>
            </div>

            <div class="card">
                <h2>Novo cliente</h2>

                <form method="POST" action="/admin/clientes">
                    <label>Nome do cliente</label>
                    <input name="name" placeholder="Ex: Novo Cliente" required>

                    <label>Slug</label>
                    <input name="slug" placeholder="Ex: novo-cliente">

                    <button type="submit">Cadastrar cliente</button>
                </form>
            </div>

            <div class="card">
                <h2>Clientes cadastrados</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Cliente</th>
                            <th>Slug</th>
                            <th>Views</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    return html


@app.route("/admin/clientes", methods=["POST"])
def salvar_cliente():
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip()

    if not name:
        return jsonify({
            "status": "error",
            "error": "Nome do cliente é obrigatório"
        }), 400

    if not slug:
        slug = slugify(name)
    else:
        slug = slugify(slug)

    data = load_clients()
    clients = data.get("clients", [])

    for client in clients:
        if client.get("slug") == slug:
            return jsonify({
                "status": "error",
                "error": f"Cliente com slug '{slug}' já existe"
            }), 400

    clients.append({
        "name": name,
        "slug": slug
    })

    data["clients"] = clients
    save_clients(data)

    return redirect("/admin/clientes")


@app.route("/views/<path:filename>", methods=["GET"])
def servir_views(filename):
    try:
        return send_from_directory(str(DATA_DIR), filename)
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
