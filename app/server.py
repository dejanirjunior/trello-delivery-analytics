from flask import Flask, jsonify, send_from_directory, request, redirect, session
from flask_cors import CORS
import subprocess
from pathlib import Path
import json
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"
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
        clients TEXT
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
        INSERT INTO users (username, password_hash, role, clients)
        VALUES (?, ?, ?, ?)
        """, ("admin", password, "admin", "*"))

        conn.commit()

    conn.close()

init_db()
create_default_user()

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

def is_logged():
    return "user" in session

def get_current_user():
    if not is_logged():
        return None

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (session["user"],))
    user = cursor.fetchone()
    conn.close()

    return user

def has_access(slug):
    user = get_current_user()

    if not user:
        return False

    if user["clients"] == "*":
        return True

    allowed = [c.strip() for c in user["clients"].split(",")]
    return slug in allowed

@app.route("/")
def home():
    if not is_logged():
        return redirect("/login")

    return jsonify({"status": "ok", "message": "Logado"})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user"] = username
            return redirect("/admin/clientes")

        return "<h2>Login inválido</h2><a href='/login'>Tentar novamente</a>"

    return """
    <html>
    <body>
        <h2>Login</h2>
        <form method="POST">
            <input name="username" required>
            <input name="password" type="password" required>
            <button type="submit">Entrar</button>
        </form>
    </body>
    </html>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/update", methods=["POST"])
def update():
    if not is_logged():
        return redirect("/login")

    main_script = str(BASE_DIR / "app" / "main.py")

    result = subprocess.run(
        ["python3", main_script],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR)
    )

    return jsonify({
        "status": "success" if result.returncode == 0 else "error",
        "output": result.stdout[-2000:],
        "error": result.stderr[-2000:]
    })

@app.route("/admin/clientes", methods=["GET"])
def admin_clientes():
    if not is_logged():
        return redirect("/login")

    data = load_clients()
    rows = ""

    for c in data.get("clients", []):
        rows += f"<tr><td>{c['name']}</td><td>{c['slug']}</td></tr>"

    return f"<h1>Clientes</h1><a href='/logout'>Sair</a><table>{rows}</table>"

@app.route("/admin/clientes", methods=["POST"])
def salvar_cliente():
    if not is_logged():
        return redirect("/login")

    name = request.form.get("name", "")
    slug = slugify(request.form.get("slug") or name)

    data = load_clients()
    data["clients"].append({"name": name, "slug": slug})
    save_clients(data)

    return redirect("/admin/clientes")

@app.route("/views/<path:filename>")
def views(filename):
    if not is_logged():
        return redirect("/login")

    match = re.search(r"_(.*?)\.html", filename)
    if match:
        if not has_access(match.group(1)):
            return "Acesso negado", 403

    return send_from_directory(DATA_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
