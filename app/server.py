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
DB_PATH = Path("/data/auth.db")
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


def has_trello_data_for_client(slug):
    import csv
    file_path = BASE_DIR / "data" / "cards_enriched.csv"

    if not file_path.exists():
        return False

    slug_lower = slug.lower()

    with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            cliente = (row.get("cliente_label") or "").strip().lower()

            if cliente == slug_lower:
                return True

    return False


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
    SELECT id, username, password_hash, role, clients, active, must_change_password
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
    INSERT INTO users (username, password_hash, role, clients, active, must_change_password)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (username, password_hash, role, "", 1, 1))

    user_id = cursor.lastrowid

    for client_id in client_ids:
        cursor.execute("""
        INSERT OR IGNORE INTO user_clients (user_id, client_id)
        VALUES (?, ?)
        """, (user_id, client_id))

    conn.commit()
    conn.close()


def update_user_password(user_id, new_password):
    password_hash = generate_password_hash(new_password)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET password_hash = ?, must_change_password = 0
    WHERE id = ?
    """, (password_hash, user_id))

    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, username, role, active, must_change_password
    FROM users
    WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()
    conn.close()

    return user


def get_user_client_ids(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT client_id
    FROM user_clients
    WHERE user_id = ?
    """, (user_id,))

    ids = [str(row["client_id"]) for row in cursor.fetchall()]
    conn.close()

    return ids


def update_user_profile(user_id, role, client_ids):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET role = ?
    WHERE id = ?
    """, (role, user_id))

    cursor.execute("DELETE FROM user_clients WHERE user_id = ?", (user_id,))

    for client_id in client_ids:
        cursor.execute("""
        INSERT OR IGNORE INTO user_clients (user_id, client_id)
        VALUES (?, ?)
        """, (user_id, client_id))

    conn.commit()
    conn.close()


def set_user_active(user_id, active):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET active = ?
    WHERE id = ?
    """, (active, user_id))

    conn.commit()
    conn.close()


def reset_user_password(user_id, new_password):
    password_hash = generate_password_hash(new_password)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET password_hash = ?, must_change_password = 1
    WHERE id = ?
    """, (password_hash, user_id))

    conn.commit()
    conn.close()



def audit_log(action, target_type=None, target_value=None):
    user = get_current_user()
    username = user["username"] if user else session.get("user", "anonymous")
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO audit_logs (username, action, target_type, target_value, ip_address)
    VALUES (?, ?, ?, ?, ?)
    """, (username, action, target_type, target_value, ip_address))

    conn.commit()
    conn.close()


def require_login():
    if not is_logged():
        return redirect("/login")

    user = get_current_user()

    if user and user["must_change_password"] == 1 and request.path != "/trocar-senha":
        return redirect("/trocar-senha")

    return None


init_db()
create_default_user()
sync_clients_json_to_db()


def get_nav_items():
    user = get_current_user()

    if not user:
        return []

    role = user["role"]

    if role == "admin":
        return [
            ("Clientes", "/admin/clientes"),
            ("Usuários", "/admin/usuarios"),
            ("Auditoria", "/admin/audit"),
            ("Daily", "/daily"),
            ("Histórico Daily", "/daily_history"),
            ("Registro de Horas", "/"),
            ("Histórico Horas", "/worklog_history"),
            ("PM View", "/views/pm_view.html"),
            ("Forecast", "/views/pm_forecast_view.html")
        ]

    if role == "internal":
        return [
            ("Clientes", "/admin/clientes"),
            ("Daily", "/daily"),
            ("Histórico Daily", "/daily_history"),
            ("Registro de Horas", "/"),
            ("Histórico Horas", "/worklog_history")
        ]

    if role == "client":
        return []

    return []


def base_layout(title, content):
    nav_html = "".join([
        f'<a class="btn btn-secondary" href="{url}">{label}</a>'
        for label, url in get_nav_items()
    ])

    logout_html = ""
    if is_logged():
        logout_html = '<a class="btn btn-danger" href="/logout">Sair</a>'

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <main class="page">
            <div class="top-menu">
                <div class="top-menu-links">
                    {nav_html}
                </div>
                <div class="top-menu-logout">
                    {logout_html}
                </div>
            </div>

            {content}
        
<footer class="optaris-footer" style="
    margin-top:40px;
    padding:20px;
    text-align:center;
    font-size:12px;
    color:#888;
    border-top:1px solid rgba(255,255,255,0.10);
">
    © Plataforma Optaris ·
    <a href="/politica-privacidade" style="color:#888; text-decoration:underline;">
        Política de Privacidade
    </a>
</footer>

        </main>
    </body>
    </html>
    """


@app.route("/")
def home():
    if not is_logged():
        return redirect("/login")

    return base_layout("Clientes · Optaris", f"""
        <div class="card">
            <h2>Status</h2>
            <p>{message}</p>
            <a class="btn btn-secondary" href="/admin/clientes">Voltar</a>
        </div>
    """)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_username(username)

        if user and user["active"] == 1 and check_password_hash(user["password_hash"], password):
            session["user"] = username
            audit_log("login_success", "user", username)

            if user["must_change_password"] == 1:
                return redirect("/trocar-senha")

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


@app.route("/trocar-senha", methods=["GET", "POST"])
def trocar_senha():
    guard = require_login()
    if guard:
        return guard

    user = get_current_user()
    error = ""

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not check_password_hash(user["password_hash"], current_password):
            error = "Senha atual incorreta."
        elif len(new_password) < 8:
            error = "A nova senha deve ter pelo menos 8 caracteres."
        elif new_password != confirm_password:
            error = "A confirmação da senha não confere."
        else:
            update_user_password(user["id"], new_password)
            return redirect("/admin/clientes")

    return base_layout("Trocar senha · Optaris", f"""
        <div style="max-width:520px;margin:70px auto;">
            <div class="eyebrow">Segurança da conta</div>
            <h1>Trocar senha</h1>
            <p>Por segurança, altere sua senha inicial antes de continuar.</p>

            <div class="card">
                <form method="POST">
                    <label>Senha atual</label>
                    <input name="current_password" type="password" placeholder="Digite sua senha atual" required>

                    <label>Nova senha</label>
                    <input name="new_password" type="password" placeholder="Mínimo de 8 caracteres" required>

                    <label>Confirmar nova senha</label>
                    <input name="confirm_password" type="password" placeholder="Repita a nova senha" required>

                    <button type="submit">Salvar nova senha</button>
                </form>

                <p class="error">{error}</p>
            </div>
        </div>
    """)


@app.route("/logout")
def logout():
    audit_log("logout", "user", session.get("user", "unknown"))
    session.clear()
    return redirect("/login")


# =========================
# WORKLOG LOCAL REDIRECTS
# =========================

def get_worklog_base_url():
    host = request.host.split(":")[0]

    if host in ["localhost", "127.0.0.1"]:
        return "http://localhost:8003"

    return ""


@app.route("/daily")
def redirect_daily():
    base = get_worklog_base_url()
    if base:
        return redirect(f"{base}/daily")
    return redirect("/daily")


@app.route("/daily_history")
def redirect_daily_history():
    base = get_worklog_base_url()
    if base:
        return redirect(f"{base}/daily_history")
    return redirect("/daily_history")


@app.route("/worklog_history")
def redirect_worklog_history():
    base = get_worklog_base_url()
    if base:
        return redirect(f"{base}/worklog_history")
    return redirect("/worklog_history")


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


@app.route("/admin")
@app.route("/admin/")
def admin_home():
    guard = require_login()
    if guard:
        return guard

    return redirect("/admin/clientes")


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
        <a class="btn btn-secondary" href="/admin/audit">Auditoria</a>
        """

    return base_layout("Clientes · Optaris", f"""
        <div class="header">
            <div>
                <div class="eyebrow">Administração</div>
                <h1>Clientes</h1>
                <p>Gerencie clientes cadastrados e acesse as views disponíveis.</p>
            </div>
            <div></div>
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

    has_data = has_trello_data_for_client(slug)

    if has_data:
        try:
            subprocess.run(
                ["python3", str(BASE_DIR / "app" / "main.py")],
                capture_output=True,
                text=True,
                cwd=str(BASE_DIR)
            )
            message = "Cliente cadastrado e dashboards gerados."
        except Exception:
            message = "Cliente cadastrado, mas falha ao gerar dashboards."
    else:
        message = "Cliente cadastrado, mas NÃO há dados no Trello para esse cliente."

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
            <td>
                <a class="btn btn-secondary" href="/admin/usuarios/{user["id"]}/editar">Editar</a>
                <a class="btn btn-secondary" href="/admin/usuarios/{user["id"]}/resetar-senha">Resetar senha</a>
                <form method="POST" action="/admin/usuarios/{user["id"]}/toggle" style="display:inline;">
                    <button type="submit" class="btn-secondary">{ "Desativar" if user["active"] == 1 else "Ativar" }</button>
                </form>
            </td>
        </tr>
        """

    return base_layout("Usuários · Optaris", f"""
        <div class="header">
            <div>
                <div class="eyebrow">Controle de acesso</div>
                <h1>Usuários</h1>
                <p>Cadastre logins internos e logins de clientes com acesso multi-cliente.</p>
            </div>
            <div></div>
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
                        <th>Ações</th>
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
        audit_log("user_created", "user", username)
    except sqlite3.IntegrityError:
        return "Usuário já existe", 400

    return redirect("/admin/usuarios")


@app.route("/admin/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
def editar_usuario(user_id):
    guard = require_login()
    if guard:
        return guard

    if not is_admin():
        return "Acesso negado", 403

    user = get_user_by_id(user_id)

    if not user:
        return "Usuário não encontrado", 404

    if request.method == "POST":
        role = request.form.get("role", "client").strip()
        client_ids = request.form.getlist("client_ids")

        if role not in ["admin", "internal", "client"]:
            return "Perfil inválido", 400

        update_user_profile(user_id, role, client_ids)
        audit_log("user_updated", "user", user["username"])
        return redirect("/admin/usuarios")

    clients = get_clients()
    selected_ids = get_user_client_ids(user_id)

    client_checkboxes = ""

    for client in clients:
        checked = "checked" if str(client["id"]) in selected_ids else ""

        client_checkboxes += f"""
        <label class="checkbox-item">
            <input type="checkbox" name="client_ids" value="{client["id"]}" {checked}>
            {client["name"]}
        </label>
        """

    return base_layout("Editar usuário · Optaris", f"""
        <div class="card">
            <h2>Editar usuário</h2>
            <p>{user["username"]}</p>

            <form method="POST">
                <label>Perfil</label>
                <select name="role" required>
                    <option value="client" {"selected" if user["role"] == "client" else ""}>Cliente</option>
                    <option value="internal" {"selected" if user["role"] == "internal" else ""}>Interno</option>
                    <option value="admin" {"selected" if user["role"] == "admin" else ""}>Admin</option>
                </select>

                <div class="checkbox-grid">
                    {client_checkboxes}
                </div>

                <button>Salvar</button>
            </form>
        </div>
    """)


@app.route("/admin/usuarios/<int:user_id>/resetar-senha", methods=["GET", "POST"])
def resetar_senha_usuario(user_id):
    guard = require_login()
    if guard:
        return guard

    if not is_admin():
        return "Acesso negado", 403

    user = get_user_by_id(user_id)

    if not user:
        return "Usuário não encontrado", 404

    error = ""

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(new_password) < 8:
            error = "Senha deve ter 8 caracteres"
        elif new_password != confirm_password:
            error = "Confirmação incorreta"
        else:
            reset_user_password(user_id, new_password)
            audit_log("password_reset", "user", user["username"])
            return redirect("/admin/usuarios")

    return base_layout("Resetar senha", f"""
        <div class="card">
            <h2>Resetar senha</h2>
            <p>{user["username"]}</p>

            <form method="POST">
                <input name="new_password" type="password" placeholder="Nova senha" required>
                <input name="confirm_password" type="password" placeholder="Confirmar senha" required>
                <button>Resetar</button>
            </form>

            <p class="error">{error}</p>
        </div>
    """)


@app.route("/admin/usuarios/<int:user_id>/toggle", methods=["POST"])
def toggle_usuario(user_id):
    guard = require_login()
    if guard:
        return guard

    if not is_admin():
        return "Acesso negado", 403

    current_user = get_current_user()

    if current_user and current_user["id"] == user_id:
        return "Não pode desativar a si mesmo", 400

    user = get_user_by_id(user_id)

    if not user:
        return "Usuário não encontrado", 404

    new_status = 0 if user["active"] == 1 else 1
    set_user_active(user_id, new_status)

    action = "user_deactivated" if new_status == 0 else "user_activated"
    audit_log(action, "user", user["username"])

    return redirect("/admin/usuarios")


@app.route("/admin/audit", methods=["GET"])
def admin_audit():
    guard = require_login()
    if guard:
        return guard

    if not is_admin():
        return "Acesso negado", 403

    username = request.args.get("username", "").strip()
    action = request.args.get("action", "").strip()
    limit_raw = request.args.get("limit", "100").strip()

    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 100

    if limit < 10:
        limit = 10

    if limit > 500:
        limit = 500

    query = """
    SELECT id, username, action, target_type, target_value, ip_address, created_at
    FROM audit_logs
    WHERE 1 = 1
    """

    params = []

    if username:
        query += " AND username LIKE ?"
        params.append(f"%{username}%")

    if action:
        query += " AND action = ?"
        params.append(action)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    logs = cursor.fetchall()

    cursor.execute("""
    SELECT DISTINCT action
    FROM audit_logs
    ORDER BY action
    """)
    actions = cursor.fetchall()

    conn.close()

    action_options = '<option value="">Todas as ações</option>'

    for item in actions:
        selected = "selected" if item["action"] == action else ""
        action_options += f'<option value="{item["action"]}" {selected}>{item["action"]}</option>'

    rows = ""

    for log in logs:
        rows += f"""
        <tr>
            <td>{log["created_at"]}</td>
            <td>{log["username"] or ""}</td>
            <td><code>{log["action"]}</code></td>
            <td>{log["target_type"] or ""}</td>
            <td>{log["target_value"] or ""}</td>
            <td>{log["ip_address"] or ""}</td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
            <td colspan="6">Nenhum log encontrado para os filtros informados.</td>
        </tr>
        """

    return base_layout("Auditoria · Optaris", f"""
        <div class="header">
            <div>
                <div class="eyebrow">Segurança e governança</div>
                <h1>Auditoria</h1>
                <p>Consulte eventos de login, alterações de usuários, reset de senha e acesso às views.</p>
            </div>
            <div></div>
        </div>

        <div class="card">
            <h2>Filtros</h2>

            <form method="GET" action="/admin/audit">
                <label>Usuário</label>
                <input name="username" value="{username}" placeholder="ex: admin ou email">

                <label>Ação</label>
                <select name="action">
                    {action_options}
                </select>

                <label>Limite de registros</label>
                <input name="limit" value="{limit}" placeholder="100">

                <button type="submit">Filtrar</button>
                <a class="btn btn-secondary" href="/admin/audit">Limpar</a>
            </form>
        </div>

        <div class="card">
            <h2>Últimos eventos</h2>

            <table>
                <thead>
                    <tr>
                        <th>Data/hora</th>
                        <th>Usuário</th>
                        <th>Ação</th>
                        <th>Tipo</th>
                        <th>Alvo</th>
                        <th>IP</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    """)


def render_html_file_with_app_nav(filename):
    file_path = DATA_DIR / filename

    if not file_path.exists():
        return send_from_directory(DATA_DIR, filename)

    html = file_path.read_text(encoding="utf-8")

    nav_html = "".join([
        f'<a class="optaris-global-nav-link" href="{url}">{label}</a>'
        for label, url in get_nav_items()
    ])

    logout_html = '<a class="optaris-global-nav-link optaris-global-nav-danger" href="/logout">Sair</a>'

    injected_menu = f"""
    <div class="optaris-global-nav">
        <div class="optaris-global-nav-inner">
            <div class="optaris-global-nav-links">
                {nav_html}
            </div>
            <div class="optaris-global-nav-logout">
                {logout_html}
            </div>
        </div>
    </div>
    """

    isolated_css = """
    <style>
        .optaris-global-nav {
            width: 100%;
            background: #0b0f1a;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding: 8px 16px;
            box-sizing: border-box;
            font-family: Arial, sans-serif;
            position: relative;
            z-index: 9999;
        }

        .optaris-global-nav-inner {
            max-width: 1180px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .optaris-global-nav-links {
            display: flex;
            align-items: center;
            gap: 6px;
            overflow-x: auto;
            white-space: nowrap;
            padding-bottom: 2px;
        }

        .optaris-global-nav-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            height: 28px;
            padding: 0 10px;
            border-radius: 8px;
            background: #1a2238;
            color: #e8eaf0 !important;
            border: 1px solid rgba(255,255,255,0.10);
            text-decoration: none !important;
            font-size: 12px;
            font-weight: 600;
            line-height: 1;
            flex: 0 0 auto;
        }

        .optaris-global-nav-link:hover {
            background: #263149;
            color: #ffffff !important;
        }

        .optaris-global-nav-danger {
            color: #f06565 !important;
            background: transparent;
        }

        .optaris-global-nav-logout {
            flex: 0 0 auto;
        }
    </style>
    """

    if "</head>" in html:
        html = html.replace("</head>", isolated_css + "\n</head>", 1)

    import re
    html, count = re.subn(
        r"<body([^>]*)>",
        r"<body\1>" + injected_menu,
        html,
        count=1,
        flags=re.IGNORECASE
    )

    if count == 0:
        html = injected_menu + html

    return html


@app.route("/views/<path:filename>")
def views(filename):
    admin_only_files = {
        "pm_view.html",
        "pm_flow_view.html",
        "pm_forecast_view.html",
        "director_view.html",
        "director_flow_view.html"
    }
    guard = require_login()
    if guard:
        return guard

    match = re.search(r"_(.*?)\.html", filename)

    if match:
        slug = match.group(1)

        if not user_has_client_access(slug):
            return "Acesso negado", 403

    audit_log("view_accessed", "file", filename)

    if filename in admin_only_files:
        return render_html_file_with_app_nav(filename)

    return send_from_directory(DATA_DIR, filename)

from app.weekly_routes import register_weekly_routes

register_weekly_routes(app, {
    "base_layout": base_layout,
    "require_login": require_login,
    "get_current_user": get_current_user,
    "user_has_client_access": user_has_client_access,
    "request": request,
    "redirect": redirect,
})


# =========================
# WEEKLY COMPARE DIRECT ROUTE
# =========================

@app.route("/weekly/compare/<int:weekly_id>")
def weekly_compare_direct(weekly_id):
    guard = require_login()
    if guard:
        return guard

    from html import escape
    from app.weekly_service import compare_weeklies, is_blocked, is_high_risk, is_highest_risk, calculate_block_streak

    def s(value):
        return escape(str(value or ""))

    def badge(card):
        html = ""
        if is_blocked(card):
            html += '<span style="background:#dc2626;color:white;padding:4px 8px;border-radius:999px;font-weight:800;">BLOCK</span> '
        if is_highest_risk(card):
            html += '<span style="background:#991b1b;color:white;padding:4px 8px;border-radius:999px;font-weight:800;">RISCO MÁXIMO</span> '
        elif is_high_risk(card):
            html += '<span style="background:#f59e0b;color:#111827;padding:4px 8px;border-radius:999px;font-weight:800;">Risco alto</span> '
        return html

    def render_cards(title, cards, empty):
        if not cards:
            body = f"<p>{s(empty)}</p>"
        else:
            body = ""
            for c in cards:
                body += f"""
                <div class="card">
                    <h3>{s(c.get("card_name"))}</h3>
                    <p>{badge(c)}</p>
<p><strong>Semanas em BLOCK:</strong> {calculate_block_streak(current_weekly["client_slug"], c.get("card_id"))}</p>
                    <p>Status: <strong>{s(c.get("lista"))}</strong></p>
                    <p>Responsável: <strong>{s(c.get("assigned_members") or "Não informado")}</strong></p>
                    <p>Risco: <strong>{s(c.get("risk") or "Não informado")}</strong></p>
                    <p>Prioridade: <strong>{s(c.get("priority") or "Não informada")}</strong></p>
                </div>
                """

        return f"""
        <div class="card">
            <h2>{s(title)} ({len(cards)})</h2>
            {body}
        </div>
        """

    data = compare_weeklies(weekly_id)

    if not data:
        return "Weekly não encontrada", 404

    current = data["current"]
    previous = data["previous"]
    comparison = data["comparison"]

    current_weekly = current["weekly"]

    if not user_has_client_access(current_weekly["client_slug"]):
        return "Acesso negado", 403

    if not previous or not comparison:
        return base_layout("Comparação Weekly · Optaris", f"""
            <div class="header">
                <div>
                    <div class="eyebrow">Comparação histórica</div>
                    <h1>Comparação da Weekly</h1>
                    <p>Não existe Weekly anterior para comparar com a Weekly de {s(current_weekly["date"])}.</p>
                </div>
                <div>
                    <a class="btn btn-secondary" href="/weekly/view/{current_weekly["id"]}">Voltar</a>
                </div>
            </div>

            <div class="card">
                <p>Crie pelo menos duas Weeklies para este cliente para habilitar a comparação automática.</p>
            </div>
        """)

    previous_weekly = previous["weekly"]

    summary = f"""
    <div class="grid">
        <div class="card"><h3>Ainda bloqueados</h3><h1>{len(comparison["still_blocked"])}</h1></div>
        <div class="card"><h3>Novos bloqueios</h3><h1>{len(comparison["new_blocked"])}</h1></div>
        <div class="card"><h3>Bloqueios resolvidos</h3><h1>{len(comparison["resolved_blocked"])}</h1></div>
        <div class="card"><h3>Novos riscos</h3><h1>{len(comparison["new_risk"])}</h1></div>
        <div class="card"><h3>Riscos resolvidos</h3><h1>{len(comparison["resolved_risk"])}</h1></div>
    </div>
    """

    return base_layout("Comparação Weekly · Optaris", f"""
        <div class="header">
            <div>
                <div class="eyebrow">Comparação histórica</div>
                <h1>{s(current_weekly["client_slug"])} · {s(previous_weekly["date"])} → {s(current_weekly["date"])}</h1>
                <p>Comparação automática entre a Weekly atual e a Weekly anterior.</p>
            </div>
            <div>
                <a class="btn btn-secondary" href="/weekly/view/{current_weekly["id"]}">Voltar para Weekly atual</a> <a class="btn btn-primary" href="/weekly/pdf/{current_weekly["id"]}">Exportar PDF</a>
            </div>
        </div>

        {summary}

        {render_cards("🔴 Continuam bloqueados", comparison["still_blocked"], "Nenhum card permaneceu bloqueado.")}
        {render_cards("🆕 Novos bloqueios", comparison["new_blocked"], "Nenhum novo bloqueio surgiu.")}
        {render_cards("✅ Bloqueios resolvidos", comparison["resolved_blocked"], "Nenhum bloqueio foi resolvido.")}
        {render_cards("⚠️ Riscos que continuam", comparison["still_risk"], "Nenhum risco permaneceu ativo.")}
        {render_cards("🆕 Novos riscos alto/máximo", comparison["new_risk"], "Nenhum novo risco surgiu.")}
        {render_cards("✅ Riscos resolvidos", comparison["resolved_risk"], "Nenhum risco foi resolvido.")}
    """)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from flask import send_file



from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from io import BytesIO
from flask import send_file


@app.route("/weekly/pdf/<int:weekly_id>")
def weekly_pdf(weekly_id):
    guard = require_login()
    if guard:
        return guard

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak

    from app.weekly_service import get_weekly_detail, is_blocked, is_high_risk, is_highest_risk

    detail = get_weekly_detail(weekly_id)
    if not detail:
        return "Weekly não encontrada", 404

    weekly = detail["weekly"]
    notes = detail["notes"]
    cards = detail["cards"]
    blocked_cards = detail["blocked_cards"]
    high_risk_cards = detail["high_risk_cards"]

    if not user_has_client_access(weekly["client_slug"]):
        return "Acesso negado", 403

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("OptarisTitle", parent=styles["Title"], fontSize=20, leading=24, spaceAfter=6)
    h2_style = ParagraphStyle("OptarisH2", parent=styles["Heading2"], fontSize=13, leading=16, spaceBefore=12, spaceAfter=8)
    normal = ParagraphStyle("OptarisNormal", parent=styles["Normal"], fontSize=8.5, leading=11)
    small = ParagraphStyle("OptarisSmall", parent=styles["Normal"], fontSize=7.5, leading=9.5, textColor=colors.HexColor("#4b5563"))
    white = ParagraphStyle("OptarisWhite", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.white)

    def clean(value):
        return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def make_logo():
        try:
            logo = Image("/app/app/static/logo.png")
            max_w = 34 * mm
            max_h = 14 * mm
            ratio = logo.imageWidth / logo.imageHeight
            draw_w = max_w
            draw_h = draw_w / ratio

            if draw_h > max_h:
                draw_h = max_h
                draw_w = draw_h * ratio

            logo.drawWidth = draw_w
            logo.drawHeight = draw_h
            return logo
        except Exception:
            return Paragraph("<b>Optaris</b>", title_style)

    usable_width = A4[0] - doc.leftMargin - doc.rightMargin

    header = Table(
        [[
            make_logo(),
            Paragraph(
                f"<b>RELATÓRIO WEEKLY</b><br/><font size='8'>Cliente: {clean(weekly['client_slug'])} · Data: {clean(weekly['date'])}</font>",
                title_style
            )
        ]],
        colWidths=[42 * mm, usable_width - 42 * mm]
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(header)

    meta = Table(
        [[
            Paragraph("<b>Cliente</b><br/>" + clean(weekly["client_slug"]), normal),
            Paragraph("<b>Data</b><br/>" + clean(weekly["date"]), normal),
            Paragraph("<b>Responsável</b><br/>" + clean(weekly["created_by"]), normal),
            Paragraph("<b>Gerado em</b><br/>" + clean(weekly["created_at"]), normal),
        ]],
        colWidths=[usable_width / 4] * 4
    )
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f4f6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(meta)
    story.append(Spacer(1, 10))

    total = len(cards)
    blocked = len(blocked_cards)
    risk = len(high_risk_cards)
    ok = max(total - blocked - risk, 0)

    kpis = Table(
        [[
            Paragraph("<b>Total</b><br/><br/><font size='16'>" + str(total) + "</font>", white),
            Paragraph("<b>Bloqueados</b><br/><br/><font size='16'>" + str(blocked) + "</font>", white),
            Paragraph("<b>Risco alto/máximo</b><br/><br/><font size='16'>" + str(risk) + "</font>", white),
            Paragraph("<b>Sem criticidade</b><br/><br/><font size='16'>" + str(ok) + "</font>", white),
        ]],
        colWidths=[usable_width / 4] * 4
    )
    kpis.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#111827")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#dc2626")),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#f59e0b")),
        ("BACKGROUND", (3, 0), (3, 0), colors.HexColor("#16a34a")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.white),
        ("INNERGRID", (0, 0), (-1, -1), 1, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(kpis)

    story.append(Paragraph("Resumo executivo da reunião", h2_style))
    notes_table = Table(
        [
            [Paragraph("<b>Riscos gerais</b>", normal), Paragraph(clean(notes["risks"] if notes else "") or "Não informado.", normal)],
            [Paragraph("<b>Próximos passos</b>", normal), Paragraph(clean(notes["next_steps"] if notes else "") or "Não informado.", normal)],
            [Paragraph("<b>Observações</b>", normal), Paragraph(clean(notes["notes"] if notes else "") or "Não informado.", normal)],
        ],
        colWidths=[38 * mm, usable_width - 38 * mm]
    )
    notes_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(notes_table)

    def criticidade(card):
        if is_blocked(card):
            return "BLOCK", colors.HexColor("#dc2626")
        if is_highest_risk(card):
            return "RISCO MÁXIMO", colors.HexColor("#991b1b")
        if is_high_risk(card):
            return "RISCO ALTO", colors.HexColor("#f59e0b")
        return "NORMAL", colors.HexColor("#6b7280")

    def comments_text(card):
        comments = card.get("_comments", {}) or {}
        parts = []
        if comments.get("block_comment"):
            parts.append("<b>Bloqueio:</b> " + clean(comments.get("block_comment")))
        if comments.get("risk_comment"):
            parts.append("<b>Risco:</b> " + clean(comments.get("risk_comment")))
        if comments.get("next_step"):
            parts.append("<b>Próximo passo:</b> " + clean(comments.get("next_step")))
        return "<br/>".join(parts) if parts else "Sem comentário específico."

    def render_section(title, section_cards):
        story.append(Paragraph(title, h2_style))

        if not section_cards:
            story.append(Paragraph("Nenhum card nesta seção.", normal))
            return

        rows = [[
            Paragraph("<b>Card</b>", white),
            Paragraph("<b>Criticidade</b>", white),
            Paragraph("<b>Status</b>", white),
            Paragraph("<b>Responsável</b>", white),
            Paragraph("<b>Comentários / próximos passos</b>", white),
        ]]

        row_colors = []

        for card in section_cards:
            label, color = criticidade(card)
            row_colors.append(color)
            rows.append([
                Paragraph("<b>" + clean(card.get("card_name")) + "</b>", normal),
                Paragraph("<b>" + label + "</b><br/>Prioridade: " + clean(card.get("priority") or "Não informada"), normal),
                Paragraph(clean(card.get("lista") or "Não informado"), normal),
                Paragraph(clean(card.get("assigned_members") or "Não informado"), normal),
                Paragraph(comments_text(card), small),
            ])

        table = Table(
            rows,
            colWidths=[45 * mm, 30 * mm, 24 * mm, 30 * mm, usable_width - 129 * mm],
            repeatRows=1
        )

        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]

        for idx, color in enumerate(row_colors, start=1):
            table_style.append(("LINEBEFORE", (0, idx), (0, idx), 4, color))
            table_style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#ffffff")))

        table.setStyle(TableStyle(table_style))
        story.append(table)

    render_section("Cards bloqueados", blocked_cards)
    render_section("Cards com risco alto ou máximo", high_risk_cards)

    story.append(PageBreak())
    render_section("Snapshot completo da Weekly", cards)

    story.append(Spacer(1, 12))
    story.append(Paragraph("Documento gerado automaticamente pela Plataforma Optaris de Gestão de Delivery.", small))

    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"weekly_{weekly['client_slug']}_{weekly['date']}_{weekly_id}.pdf",
        mimetype="application/pdf"
    )

# =========================
# POLÍTICA DE PRIVACIDADE (LGPD)
# =========================

@app.route("/politica-privacidade")
def politica_privacidade():
    return base_layout("Política de Privacidade · Optaris", '''
        <div class="card">
            <h1>Política de Privacidade</h1>

            <p>Esta plataforma é destinada à gestão de projetos e atividades operacionais, com acesso restrito a usuários autorizados.</p>

            <h2>1. Dados tratados</h2>
            <p>Podemos tratar dados como nome de usuário, identificação de responsáveis em atividades e registros operacionais.</p>

            <h2>2. Finalidade</h2>
            <p>Os dados são utilizados exclusivamente para gestão de projetos e acompanhamento de atividades.</p>

            <h2>3. Compartilhamento</h2>
            <p>Os dados não são compartilhados com terceiros externos.</p>

            <h2>4. Segurança</h2>
            <p>São aplicadas medidas de controle de acesso e autenticação.</p>

            <h2>5. Direitos do titular</h2>
            <p>Usuários podem solicitar atualização ou exclusão de dados.</p>
        </div>
    ''')
