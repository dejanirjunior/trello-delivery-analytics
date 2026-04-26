from flask import Flask, jsonify, send_from_directory, request, redirect, session
from flask_cors import CORS
import subprocess
from pathlib import Path
import json
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
CORS(app)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
DB_PATH = BASE_DIR / "app" / "auth.db"
CLIENTS_FILE = CONFIG_DIR / "clients.json"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        clients TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(client_id) REFERENCES clients(id),
        UNIQUE(user_id, client_id)
    )
    """)

    conn.commit()
    conn.close()


def create_default_user():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    user = cursor.fetchone()

    if not user:
        password = generate_password_hash("admin123")

        cursor.execute("""
        INSERT INTO users (username, password_hash, role, clients, active)
        VALUES (?, ?, ?, ?, ?)
        """, ("admin", password, "admin", "*", 1))

        conn.commit()

    conn.close()


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


def load_clients_json():
    if not CLIENTS_FILE.exists():
        return {"clients": []}

    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_clients_json(data):
    CONFIG_DIR.mkdir(exist_ok=True)

    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sync_clients_json_to_db():
    data = load_clients_json()
    clients = data.get("clients", [])

    conn = get_db()
    cursor = conn.cursor()

    for client in clients:
        name = client.get("name", "").strip()
        slug = client.get("slug", "").strip().lower()

        if not name or not slug:
            continue

        cursor.execute("""
        INSERT OR IGNORE INTO clients (name, slug, active)
        VALUES (?, ?, ?)
        """, (name, slug, 1))

    conn.commit()
    conn.close()


def get_clients():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, slug, active
    FROM clients
    WHERE active = 1
    ORDER BY name
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_user_by_username(username):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, username, password_hash, role, clients, active
    FROM users
    WHERE username = ?
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    return user


def get_current_user():
    username = session.get("user")

    if not username:
        return None

    return get_user_by_username(username)


def is_logged():
    return get_current_user() is not None


def is_admin():
    user = get_current_user()
    return bool(user and user["role"] == "admin")


def user_has_client_access(slug):
    user = get_current_user()

    if not user:
        return False

    if user["role"] == "admin":
        return True

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 1
    FROM user_clients uc
    JOIN clients c ON c.id = uc.client_id
    WHERE uc.user_id = ?
      AND c.slug = ?
      AND c.active = 1
    LIMIT 1
    """, (user["id"], slug))

    allowed = cursor.fetchone()
    conn.close()

    return allowed is not None


def get_users_with_clients():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, username, role, active
    FROM users
    ORDER BY username
    """)

    users = cursor.fetchall()

    result = []

    for user in users:
        cursor.execute("""
        SELECT c.name, c.slug
        FROM user_clients uc
        JOIN clients c ON c.id = uc.client_id
        WHERE uc.user_id = ?
        ORDER BY c.name
        """, (user["id"],))

        linked_clients = cursor.fetchall()

        result.append({
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "active": user["active"],
            "clients": linked_clients
        })

    conn.close()

    return result


def create_user(username, password, role, client_ids):
    conn = get_db()
    cursor = conn.cursor()

    password_hash = generate_password_hash(password)

    cursor.execute("""
    INSERT INTO users (username, password_hash, role, clients, active)
    VALUES (?, ?, ?, ?, ?)
    """, (username, password_hash, role, "", 1))

    user_id = cursor.lastrowid

    for client_id in client_ids:
        cursor.execute("""
        INSERT OR IGNORE INTO user_clients (user_id, client_id)
        VALUES (?, ?)
        """, (user_id, client_id))

    conn.commit()
    conn.close()


def require_login():
    if not is_logged():
        return redirect("/login")

    return None


init_db()
create_default_user()
sync_clients_json_to_db()

def base_layout(title, content):
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #0b0f1a;
                --surface: #131929;
                --surface2: #1a2238;
                --border: rgba(255,255,255,0.08);
                --text: #e8eaf0;
                --muted: #8891a8;
                --gold: #c9a84c;
                --gold-light: #e4c97e;
                --danger: #f06565;
            }}

            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                min-height: 100vh;
                font-family: 'DM Sans', sans-serif;
                background: var(--bg);
                color: var(--text);
            }}

            body::before {{
                content: '';
                position: fixed;
                inset: 0;
                background: radial-gradient(circle at top right, rgba(201,168,76,0.10), transparent 35%);
                pointer-events: none;
            }}

            .page {{
                position: relative;
                z-index: 1;
                max-width: 1180px;
                margin: 0 auto;
                padding: 40px 32px 80px;
            }}

            .header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 24px;
                padding-bottom: 28px;
                margin-bottom: 28px;
                border-bottom: 1px solid var(--border);
            }}

            .eyebrow {{
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.18em;
                color: var(--gold);
                text-transform: uppercase;
                margin-bottom: 10px;
            }}

            h1 {{
                font-family: 'DM Serif Display', serif;
                font-size: 42px;
                line-height: 1.1;
                margin: 0;
            }}
            h2, h3 {{
                margin-top: 0;
            }}

            p {{
                color: var(--muted);
            }}

            .card {{
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 24px;
                margin-bottom: 22px;
                box-shadow: 0 18px 40px rgba(0,0,0,0.18);
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                gap: 18px;
            }}

            .client-card {{
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 22px;
            }}

            input, select {{
                width: 100%;
                padding: 12px;
                margin: 7px 0 14px;
                border-radius: 12px;
                border: 1px solid var(--border);
                background: var(--surface2);
                color: var(--text);
            }}

            label {{
                display: block;
                color: var(--muted);
                font-size: 13px;
                font-weight: 700;
            }}

            button, .btn {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 11px 16px;
                border-radius: 999px;
                border: 0;
                background: linear-gradient(90deg, var(--gold), var(--gold-light));
                color: #0b0f1a;
                font-weight: 800;
                text-decoration: none;
                cursor: pointer;
                margin-right: 8px;
            }}

            .btn-secondary {{
                background: var(--surface2);
                color: var(--text);
                border: 1px solid var(--border);
            }}

            .btn-danger {{
                color: var(--danger);
                text-decoration: none;
                font-weight: 800;
            }}

            .links {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 16px;
            }}

            .checkbox-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 8px;
                margin: 10px 0 16px;
            }}

            .checkbox-item {{
                background: var(--surface2);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 10px;
                color: var(--text);
            }}

            .checkbox-item input {{
                width: auto;
                margin-right: 8px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th, td {{
                padding: 12px;
                border-bottom: 1px solid var(--border);
                text-align: left;
                vertical-align: top;
            }}

            th {{
                color: var(--gold);
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: .08em;
            }}

            code {{
                color: var(--gold-light);
            }}

            .error {{
                color: var(--danger);
                font-weight: 700;
            }}
        </style>
    </head>
    <body>
        <main class="page">
            {content}
        </main>
    </body>
    </html>
    """


@app.route("/")
def home():
    if not is_logged():
        return redirect("/login")

    return redirect("/admin/clientes")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_username(username)

        if user and user["active"] == 1 and check_password_hash(user["password_hash"], password):
            session["user"] = username
            return redirect("/admin/clientes")

        error = "Usuário ou senha inválidos."

    return base_layout("Login · Optaris", f"""
        <div style="max-width:430px;margin:80px auto;">
            <div class="eyebrow">Optaris Delivery Platform</div>
            <h1>Portal de Acesso</h1>
            <p>Entre para acessar dashboards, portais de clientes e gestão administrativa.</p>

            <div class="card">
                <form method="POST">
                    <label>Usuário ou e-mail</label>
                    <input name="username" placeholder="exemplo@empresa.com" required>

                    <label>Senha</label>
                    <input name="password" type="password" placeholder="Digite sua senha" required>

                    <button type="submit">Entrar</button>
                </form>
                <p class="error">{error}</p>
            </div>
        </div>
    """)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "trello-dashboard"
    })


@app.route("/update", methods=["POST"])
def update():
    guard = require_login()
    if guard:
        return guard

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
    guard = require_login()
    if guard:
        return guard

    clients = get_clients()

    cards = ""

    for client in clients:
        slug = client["slug"]
        cards += f"""
        <div class="client-card">
            <div class="eyebrow">Cliente</div>
            <h3>{client["name"]}</h3>
            <p><code>{slug}</code></p>

            <div class="links">
                <a class="btn btn-secondary" href="/views/executive_{slug}.html">Executivo</a>
                <a class="btn btn-secondary" href="/views/dashboard_{slug}.html">Dashboard</a>
            </div>
        </div>
        """

    admin_links = ""
    if is_admin():
        admin_links = """
        <a class="btn btn-secondary" href="/admin/usuarios">Usuários</a>
        """

    return base_layout("Clientes · Optaris", f"""
        <div class="header">
            <div>
                <div class="eyebrow">Administração</div>
                <h1>Clientes</h1>
                <p>Gerencie clientes cadastrados e acesse as views disponíveis.</p>
            </div>
            <div>
                {admin_links}
                <a class="btn-danger" href="/logout">Sair</a>
            </div>
        </div>

        <div class="card">
            <h2>Novo cliente</h2>
            <form method="POST" action="/admin/clientes">
                <label>Nome do cliente</label>
                <input name="name" placeholder="Ex: 4Network" required>

                <label>Slug</label>
                <input name="slug" placeholder="Ex: 4network">

                <button type="submit">Cadastrar cliente</button>
            </form>
        </div>

        <div class="grid">
            {cards}
        </div>
    """)


@app.route("/admin/clientes", methods=["POST"])
def salvar_cliente():
    guard = require_login()
    if guard:
        return guard

    if not is_admin():
        return "Acesso negado", 403

    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip()

    if not name:
        return "Nome do cliente é obrigatório", 400

    if not slug:
        slug = slugify(name)
    else:
        slug = slugify(slug)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO clients (name, slug, active)
    VALUES (?, ?, ?)
    """, (name, slug, 1))

    conn.commit()
    conn.close()

    data = load_clients_json()
    clients = data.get("clients", [])

    if not any(c.get("slug") == slug for c in clients):
        clients.append({"name": name, "slug": slug})
        data["clients"] = clients
        save_clients_json(data)

    return redirect("/admin/clientes")


@app.route("/admin/usuarios", methods=["GET"])
def admin_usuarios():
    guard = require_login()
    if guard:
        return guard

    if not is_admin():
        return "Acesso negado", 403

    clients = get_clients()
    users = get_users_with_clients()

    client_checkboxes = ""

    for client in clients:
        client_checkboxes += f"""
        <label class="checkbox-item">
            <input type="checkbox" name="client_ids" value="{client["id"]}">
            {client["name"]}
        </label>
        """

    rows = ""

    for user in users:
        linked = ", ".join([c["name"] for c in user["clients"]]) or "Acesso total/admin ou sem cliente vinculado"
        status = "Ativo" if user["active"] == 1 else "Inativo"

        rows += f"""
        <tr>
            <td>{user["username"]}</td>
            <td><code>{user["role"]}</code></td>
            <td>{linked}</td>
            <td>{status}</td>
        </tr>
        """

    return base_layout("Usuários · Optaris", f"""
        <div class="header">
            <div>
                <div class="eyebrow">Controle de acesso</div>
                <h1>Usuários</h1>
                <p>Cadastre logins internos e logins de clientes com acesso multi-cliente.</p>
            </div>
            <div>
                <a class="btn btn-secondary" href="/admin/clientes">Clientes</a>
                <a class="btn-danger" href="/logout">Sair</a>
            </div>
        </div>

        <div class="card">
            <h2>Novo usuário</h2>

            <form method="POST" action="/admin/usuarios">
                <label>Usuário ou e-mail</label>
                <input name="username" placeholder="usuario@empresa.com" required>

                <label>Senha inicial</label>
                <input name="password" type="password" placeholder="Senha inicial" required>

                <label>Perfil</label>
                <select name="role" required>
                    <option value="client">Cliente</option>
                    <option value="internal">Interno Optaris</option>
                    <option value="admin">Administrador</option>
                </select>

                <label>Clientes permitidos</label>
                <div class="checkbox-grid">
                    {client_checkboxes}
                </div>

                <button type="submit">Criar usuário</button>
            </form>
        </div>

        <div class="card">
            <h2>Usuários cadastrados</h2>

            <table>
                <thead>
                    <tr>
                        <th>Usuário</th>
                        <th>Perfil</th>
                        <th>Clientes</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    """)


@app.route("/admin/usuarios", methods=["POST"])
def salvar_usuario():
    guard = require_login()
    if guard:
        return guard

    if not is_admin():
        return "Acesso negado", 403

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "client").strip()
    client_ids = request.form.getlist("client_ids")

    if not username or not password:
        return "Usuário e senha são obrigatórios", 400

    if role not in ["admin", "internal", "client"]:
        return "Perfil inválido", 400

    try:
        create_user(username, password, role, client_ids)
    except sqlite3.IntegrityError:
        return "Usuário já existe", 400

    return redirect("/admin/usuarios")


@app.route("/views/<path:filename>")
def views(filename):
    guard = require_login()
    if guard:
        return guard

    match = re.search(r"_(.*?)\.html", filename)

    if match:
        slug = match.group(1)

        if not user_has_client_access(slug):
            return "Acesso negado", 403

    return send_from_directory(DATA_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
