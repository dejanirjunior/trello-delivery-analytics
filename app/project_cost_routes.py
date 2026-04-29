from flask import Blueprint, request, redirect
import sqlite3
from pathlib import Path
from html import escape
from datetime import date, datetime

project_cost_bp = Blueprint("project_cost", __name__)

DB_PATH = Path("data/project_cost.db")
AUTH_DB_PATH = Path("/data/auth.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_auth_db():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def require_admin():
    from app.server import require_login, is_admin

    guard = require_login()
    if guard:
        return guard

    if not is_admin():
        return "Acesso negado", 403

    return None


def money(value):
    if value is None or value == "":
        return "-"

    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def parse_date(value):
    if not value:
        return None

    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def days_between(start, end):
    if not start or not end or end < start:
        return 0

    return (end - start).days + 1


def calculate_allocation_cost(monthly_cost, allocation_percent, start_date, end_date, project_start, calculation_end):
    allocation_start = parse_date(start_date)
    allocation_end = parse_date(end_date) if end_date else calculation_end
    project_start_date = parse_date(project_start)

    effective_start = max(allocation_start, project_start_date)
    effective_end = min(allocation_end, calculation_end)

    total_days = days_between(effective_start, effective_end)
    daily_cost = float(monthly_cost) / 30.0
    allocation_factor = float(allocation_percent) / 100.0

    return daily_cost * total_days * allocation_factor, total_days


def semaphore(cost, reference_value):
    if not reference_value or float(reference_value) <= 0:
        return {
            "label": "Sem referencia",
            "class": "neutral",
            "percent": None,
        }

    percent = (float(cost) / float(reference_value)) * 100.0

    if percent < 70:
        return {"label": "Verde", "class": "green", "percent": percent}

    if percent < 90:
        return {"label": "Amarelo", "class": "yellow", "percent": percent}

    return {"label": "Vermelho", "class": "red", "percent": percent}


def load_clients():
    auth = get_auth_db()
    rows = auth.execute("""
        SELECT id, name, slug
        FROM clients
        WHERE active = 1
        ORDER BY name
    """).fetchall()
    auth.close()
    return rows


@project_cost_bp.route("/admin/project-costs/add-role", methods=["POST"])
def add_cost_role():
    guard = require_admin()
    if guard:
        return guard

    name = (request.form.get("name") or "").strip()
    cost = request.form.get("cost")

    if name and cost:
        conn = get_db()
        conn.execute(
            "INSERT INTO cost_roles (name, monthly_cost) VALUES (?, ?)",
            (name, float(cost))
        )
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")




@project_cost_bp.route("/admin/project-costs/edit-role", methods=["POST"])
def edit_role():
    guard = require_admin()
    if guard:
        return guard

    role_id = request.form.get("role_id")
    name = (request.form.get("name") or "").strip()
    cost = request.form.get("cost")

    if role_id and name and cost:
        conn = get_db()
        conn.execute(
            "UPDATE cost_roles SET name = ?, monthly_cost = ? WHERE id = ?",
            (name, float(cost), int(role_id))
        )
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")


@project_cost_bp.route("/admin/project-costs/delete-role", methods=["POST"])
def delete_role():
    guard = require_admin()
    if guard:
        return guard

    role_id = request.form.get("role_id")

    if role_id:
        conn = get_db()
        conn.execute("DELETE FROM cost_roles WHERE id = ?", (int(role_id),))
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")


@project_cost_bp.route("/admin/project-costs/add-project", methods=["POST"])
def add_project():
    guard = require_admin()
    if guard:
        return guard

    client_id = request.form.get("client_id")
    start_date = request.form.get("start_date")
    reference_value = request.form.get("reference_value")

    if client_id and start_date:
        conn = get_db()
        conn.execute(
            """
            INSERT INTO projects (client_id, start_date, reference_value)
            VALUES (?, ?, ?)
            """,
            (
                int(client_id),
                start_date,
                float(reference_value) if reference_value else None,
            )
        )
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")


@project_cost_bp.route("/admin/project-costs/edit-project", methods=["POST"])
def edit_project():
    guard = require_admin()
    if guard:
        return guard

    project_id = request.form.get("project_id")
    start_date = request.form.get("start_date")
    reference_value = request.form.get("reference_value")

    if project_id:
        conn = get_db()
        conn.execute(
            """
            UPDATE projects
            SET
                start_date = COALESCE(NULLIF(?, ''), start_date),
                reference_value = COALESCE(NULLIF(?, ''), reference_value)
            WHERE id = ?
            """,
            (
                start_date or "",
                reference_value or "",
                int(project_id),
            )
        )
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")


@project_cost_bp.route("/admin/project-costs/add-allocation", methods=["POST"])
def add_allocation():
    guard = require_admin()
    if guard:
        return guard

    project_id = request.form.get("project_id")
    role_id = request.form.get("role_id")
    allocation_percent = request.form.get("allocation_percent")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    if project_id and role_id and allocation_percent and start_date:
        conn = get_db()
        conn.execute(
            """
            INSERT INTO project_allocations
                (project_id, role_id, allocation_percent, start_date, end_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(project_id),
                int(role_id),
                float(allocation_percent),
                start_date,
                end_date or None,
            )
        )
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")


@project_cost_bp.route("/admin/project-costs/add-extra", methods=["POST"])
def add_extra_allocation():
    guard = require_admin()
    if guard:
        return guard

    project_id = request.form.get("project_id")
    role_id = request.form.get("role_id")
    allocation_percent = request.form.get("allocation_percent")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    if project_id and role_id and allocation_percent and start_date and end_date:
        conn = get_db()
        conn.execute(
            """
            INSERT INTO project_extra_allocations
                (project_id, role_id, allocation_percent, start_date, end_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(project_id),
                int(role_id),
                float(allocation_percent),
                start_date,
                end_date,
            )
        )
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")


@project_cost_bp.route("/admin/project-costs/delete-allocation", methods=["POST"])
def delete_allocation():
    guard = require_admin()
    if guard:
        return guard

    allocation_id = request.form.get("allocation_id")

    if allocation_id:
        conn = get_db()
        conn.execute("DELETE FROM project_allocations WHERE id = ?", (int(allocation_id),))
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")


@project_cost_bp.route("/admin/project-costs/delete-extra", methods=["POST"])
def delete_extra():
    guard = require_admin()
    if guard:
        return guard

    extra_id = request.form.get("extra_id")

    if extra_id:
        conn = get_db()
        conn.execute("DELETE FROM project_extra_allocations WHERE id = ?", (int(extra_id),))
        conn.commit()
        conn.close()

    return redirect("/admin/project-costs")


def build_options(rows, label_func, selected_id=None):
    html = '<option value="">Selecione</option>'

    for row in rows:
        row_id = int(row["id"])
        selected = "selected" if selected_id and int(selected_id) == row_id else ""
        html += f'<option value="{row_id}" {selected}>{escape(label_func(row))}</option>'

    return html


def build_delete_form(action, field_name, value, label):
    return f"""
        <form method="POST" action="{action}" style="display:inline;" onsubmit="return confirm('Confirmar exclusao?');">
            <input type="hidden" name="{field_name}" value="{int(value)}">
            <button type="submit" style="background:transparent;border:none;color:#ef4444;font-size:12px;font-weight:800;cursor:pointer;padding:0;margin-left:8px;">
                {escape(label)}
            </button>
        </form>
    """


@project_cost_bp.route("/admin/project-costs")
def project_costs_home():
    guard = require_admin()
    if guard:
        return guard

    from app.server import base_layout

    calculation_end_raw = request.args.get("end_date") or date.today().isoformat()
    calculation_end = parse_date(calculation_end_raw)

    conn = get_db()

    roles = conn.execute("""
        SELECT id, name, monthly_cost
        FROM cost_roles
        ORDER BY name
    """).fetchall()

    projects = conn.execute("""
        SELECT id, client_id, start_date, reference_value
        FROM projects
        ORDER BY start_date DESC, id DESC
    """).fetchall()

    allocations = conn.execute("""
        SELECT
            a.id,
            a.project_id,
            a.role_id,
            a.allocation_percent,
            a.start_date,
            a.end_date,
            r.name AS role_name,
            r.monthly_cost
        FROM project_allocations a
        JOIN cost_roles r ON r.id = a.role_id
        ORDER BY a.project_id, a.start_date, a.id
    """).fetchall()

    extras = conn.execute("""
        SELECT
            e.id,
            e.project_id,
            e.role_id,
            e.allocation_percent,
            e.start_date,
            e.end_date,
            r.name AS role_name,
            r.monthly_cost
        FROM project_extra_allocations e
        JOIN cost_roles r ON r.id = e.role_id
        ORDER BY e.project_id, e.start_date, e.id
    """).fetchall()

    conn.close()

    clients = load_clients()
    client_by_id = {int(c["id"]): c for c in clients}

    allocations_by_project = {}
    for item in allocations:
        allocations_by_project.setdefault(int(item["project_id"]), []).append(item)

    extras_by_project = {}
    for item in extras:
        extras_by_project.setdefault(int(item["project_id"]), []).append(item)

    client_options = build_options(
        clients,
        lambda c: c["name"],
    )

    role_options = build_options(
        roles,
        lambda r: f'{r["name"]} - {money(r["monthly_cost"])}',
    )

    project_options = build_options(
        projects,
        lambda p: f'{client_by_id.get(int(p["client_id"]), {"name": "Cliente ID " + str(p["client_id"])})["name"]} - inicio {p["start_date"]}',
    )

    roles_rows = ""
    for role in roles:
        role_id = int(role["id"])
        role_name = escape(role["name"])
        role_cost = role["monthly_cost"]

        roles_rows += f"""
            <tr>
                <td>
                    <form method="POST" action="/admin/project-costs/edit-role" style="display:grid; grid-template-columns: 1fr 150px 90px; gap:8px; align-items:center; margin:0;">
                        <input type="hidden" name="role_id" value="{role_id}">
                        <input name="name" value="{role_name}" required>
                        <input name="cost" type="number" step="0.01" value="{role_cost}" required>
                        <button type="submit">Salvar</button>
                    </form>
                </td>
                <td>{money(role_cost)}</td>
                <td>
                    <form method="POST" action="/admin/project-costs/delete-role" style="margin:0;" onsubmit="return confirm('Excluir esta funcao? Isso pode afetar alocacoes existentes.');">
                        <input type="hidden" name="role_id" value="{role_id}">
                        <button type="submit" style="color:#ef4444;">Excluir</button>
                    </form>
                </td>
            </tr>
        """

    if not roles_rows:
        roles_rows = '<tr><td colspan="3">Nenhuma funcao cadastrada.</td></tr>'

    project_rows = ""
    dashboard_cards = ""

    for project in projects:
        project_id = int(project["id"])
        client = client_by_id.get(int(project["client_id"]))
        client_name = client["name"] if client else f'Cliente ID {project["client_id"]}'

        project_cost = 0.0
        allocation_lines = ""

        project_allocations = allocations_by_project.get(project_id, [])
        project_extras = extras_by_project.get(project_id, [])

        if project_allocations:
            allocation_lines += '<div style="font-size:12px;color:#93c5fd;font-weight:900;margin-top:8px;">Alocacao base</div>'

        for allocation in project_allocations:
            cost, used_days = calculate_allocation_cost(
                allocation["monthly_cost"],
                allocation["allocation_percent"],
                allocation["start_date"],
                allocation["end_date"],
                project["start_date"],
                calculation_end,
            )
            project_cost += cost

            end_label = allocation["end_date"] if allocation["end_date"] else "em aberto"
            delete_form = build_delete_form(
                "/admin/project-costs/delete-allocation",
                "allocation_id",
                allocation["id"],
                "[excluir]",
            )

            allocation_lines += f"""
                <div style="font-size:12px;color:#cbd5e1;margin-top:4px;">
                    {escape(allocation["role_name"])} | {allocation["allocation_percent"]}% |
                    {escape(allocation["start_date"])} ate {escape(end_label)} |
                    {used_days} dias | {money(cost)}
                    {delete_form}
                </div>
            """

        if project_extras:
            allocation_lines += '<div style="font-size:12px;color:#facc15;font-weight:900;margin-top:10px;">Alocacao extra</div>'

        for extra in project_extras:
            cost, used_days = calculate_allocation_cost(
                extra["monthly_cost"],
                extra["allocation_percent"],
                extra["start_date"],
                extra["end_date"],
                project["start_date"],
                calculation_end,
            )
            project_cost += cost

            delete_form = build_delete_form(
                "/admin/project-costs/delete-extra",
                "extra_id",
                extra["id"],
                "[excluir]",
            )

            allocation_lines += f"""
                <div style="font-size:12px;color:#fbbf24;margin-top:4px;">
                    {escape(extra["role_name"])} | {extra["allocation_percent"]}% |
                    {escape(extra["start_date"])} ate {escape(extra["end_date"])} |
                    {used_days} dias | {money(cost)}
                    {delete_form}
                </div>
            """

        if not allocation_lines:
            allocation_lines = '<div style="font-size:12px;color:#94a3b8;">Sem alocacoes cadastradas.</div>'

        status = semaphore(project_cost, project["reference_value"])
        percent_label = "-" if status["percent"] is None else f'{status["percent"]:.1f}%'

        project_rows += f"""
            <tr>
                <td>{escape(client_name)}</td>
                <td>{escape(project["start_date"])}</td>
                <td>{money(project["reference_value"])}</td>
                <td>{money(project_cost)}</td>
                <td>{escape(status["label"])} ({percent_label})</td>
            </tr>
        """

        dashboard_cards += f"""
            <div class="cost-project-card cost-{escape(status["class"])}">
                <div class="cost-card-top">
                    <div>
                        <div class="cost-eyebrow">Projeto</div>
                        <h3>{escape(client_name)}</h3>
                    </div>
                    <div class="cost-badge">{escape(status["label"])}</div>
                </div>

                <div class="cost-metric">
                    <span>Custo calculado</span>
                    <strong>{money(project_cost)}</strong>
                </div>

                <div class="cost-metric">
                    <span>Valor referencia</span>
                    <strong>{money(project["reference_value"])}</strong>
                </div>

                <div class="cost-metric">
                    <span>Consumo</span>
                    <strong>{percent_label}</strong>
                </div>

                <div style="margin-top:10px;">
                    {allocation_lines}
                </div>
            </div>
        """

    if not project_rows:
        project_rows = '<tr><td colspan="5">Nenhum projeto cadastrado.</td></tr>'

    if not dashboard_cards:
        dashboard_cards = '<div class="card">Nenhum projeto cadastrado.</div>'

    html = f"""
    <style>
        .cost-grid {{
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
            gap:14px;
            margin-bottom:20px;
        }}

        .cost-project-card {{
            background:#111827;
            border:1px solid #243044;
            border-radius:16px;
            padding:16px;
            color:#f8fafc;
        }}

        .cost-card-top {{
            display:flex;
            justify-content:space-between;
            gap:12px;
            align-items:flex-start;
            margin-bottom:12px;
        }}

        .cost-card-top h3 {{
            color:#ffffff;
            margin:4px 0 0 0;
        }}

        .cost-eyebrow {{
            font-size:11px;
            font-weight:900;
            text-transform:uppercase;
            letter-spacing:.12em;
            color:#facc15;
        }}

        .cost-badge {{
            border-radius:999px;
            padding:6px 10px;
            font-size:12px;
            font-weight:900;
            color:#111827;
            background:#cbd5e1;
            white-space:nowrap;
        }}

        .cost-green .cost-badge {{ background:#86efac; }}
        .cost-yellow .cost-badge {{ background:#fde68a; }}
        .cost-red .cost-badge {{ background:#fca5a5; }}
        .cost-neutral .cost-badge {{ background:#cbd5e1; }}

        .cost-metric {{
            display:flex;
            justify-content:space-between;
            gap:12px;
            padding:8px 0;
            border-top:1px solid rgba(255,255,255,.08);
            font-size:13px;
        }}

        .cost-metric span {{
            color:#cbd5e1;
        }}

        .cost-metric strong {{
            color:#ffffff;
        }}

        .cost-form-grid {{
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
            gap:12px;
            align-items:end;
        }}

        .cost-section {{
            margin-bottom:24px;
        }}

        .cost-section-title {{
            color:#facc15;
            font-size:18px;
            font-weight:900;
            margin:0 0 8px 0;
        }}

        .cost-help {{
            background:#0f172a;
            color:#cbd5e1;
            border:1px solid #243044;
            border-radius:14px;
            padding:12px 14px;
            font-size:13px;
            margin-bottom:16px;
        }}
    </style>

    <div class="header">
        <div>
            <div class="eyebrow">Administracao financeira</div>
            <h1 title="Calculo: custo mensal / 30 * dias * percentual de alocacao">Custo de Projetos</h1>
            <p>Controle executivo de custos por projeto, funcao e alocacao.</p>
        </div>
    </div>

    <div class="cost-help">
        <strong>Como o calculo e feito:</strong>
        custo mensal da funcao / 30 * quantidade de dias considerados * percentual de alocacao.
        O total considera alocacao base + alocacao extra ate a data selecionada.
    </div>

    <div class="card">
        <form method="GET" action="/admin/project-costs">
            <label>Calcular ate</label>
            <div style="display:flex;gap:10px;align-items:end;max-width:420px;">
                <input type="date" name="end_date" value="{escape(calculation_end_raw)}">
                <button type="submit">Atualizar calculo</button>
            </div>
        </form>
    </div>

    <div class="cost-section">
        <div class="cost-section-title">Visao Executiva</div>
        <div class="cost-grid">
            {dashboard_cards}
        </div>

        <div class="card">
            <h2>Resumo dos projetos</h2>
            <table>
                <thead>
                    <tr>
                        <th>Projeto</th>
                        <th>Inicio</th>
                        <th>Referencia</th>
                        <th>Custo</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>{project_rows}</tbody>
            </table>
        </div>
    </div>

    <div class="cost-section">
        <div class="cost-section-title">Gestao de Projetos</div>

        <div class="card">
            <h2>Criar projeto</h2>
            <form method="POST" action="/admin/project-costs/add-project">
                <div class="cost-form-grid">
                    <div>
                        <label>Cliente / Projeto</label>
                        <select name="client_id" required>{client_options}</select>
                    </div>
                    <div>
                        <label>Data de inicio</label>
                        <input type="date" name="start_date" required>
                    </div>
                    <div>
                        <label>Valor referencia</label>
                        <input name="reference_value" type="number" step="0.01" placeholder="Ex: 50000">
                    </div>
                    <div>
                        <button type="submit">Criar projeto</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="card">
            <h2>Editar projeto</h2>
            <form method="POST" action="/admin/project-costs/edit-project">
                <div class="cost-form-grid">
                    <div>
                        <label>Projeto</label>
                        <select name="project_id" required>{project_options}</select>
                    </div>
                    <div>
                        <label>Nova data de inicio</label>
                        <input type="date" name="start_date">
                    </div>
                    <div>
                        <label>Novo valor referencia</label>
                        <input name="reference_value" type="number" step="0.01" placeholder="Deixe vazio para manter">
                    </div>
                    <div>
                        <button type="submit">Salvar alteracoes</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="card">
            <h2>Alocacao base</h2>
            <form method="POST" action="/admin/project-costs/add-allocation">
                <div class="cost-form-grid">
                    <div>
                        <label>Projeto</label>
                        <select name="project_id" required>{project_options}</select>
                    </div>
                    <div>
                        <label>Funcao</label>
                        <select name="role_id" required>{role_options}</select>
                    </div>
                    <div>
                        <label>% alocacao</label>
                        <input name="allocation_percent" type="number" min="0" max="100" step="0.01" required>
                    </div>
                    <div>
                        <label>Data inicio</label>
                        <input type="date" name="start_date" required>
                    </div>
                    <div>
                        <label>Data fim</label>
                        <input type="date" name="end_date">
                    </div>
                    <div>
                        <button type="submit">Adicionar base</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="card">
            <h2>Alocacao extra</h2>
            <form method="POST" action="/admin/project-costs/add-extra">
                <div class="cost-form-grid">
                    <div>
                        <label>Projeto</label>
                        <select name="project_id" required>{project_options}</select>
                    </div>
                    <div>
                        <label>Funcao</label>
                        <select name="role_id" required>{role_options}</select>
                    </div>
                    <div>
                        <label>% alocacao</label>
                        <input name="allocation_percent" type="number" min="0" max="100" step="0.01" required>
                    </div>
                    <div>
                        <label>Data inicio</label>
                        <input type="date" name="start_date" required>
                    </div>
                    <div>
                        <label>Data fim</label>
                        <input type="date" name="end_date" required>
                    </div>
                    <div>
                        <button type="submit">Adicionar extra</button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <div class="cost-section">
        <div class="cost-section-title">Configuracao de Custos</div>

        <div class="card">
            <h2>Funcoes e custos</h2>
            <form method="POST" action="/admin/project-costs/add-role">
                <div class="cost-form-grid">
                    <div>
                        <label>Funcao</label>
                        <input name="name" placeholder="Ex: Dev, Tech Lead, GP" required>
                    </div>
                    <div>
                        <label>Custo mensal</label>
                        <input name="cost" placeholder="Ex: 8000" type="number" step="0.01" required>
                    </div>
                    <div>
                        <button type="submit">Adicionar funcao</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="card">
            <h2>Funcoes cadastradas</h2>
            <table>
                <thead>
                    <tr>
                        <th>Editar funcao e custo</th>
                        <th>Custo atual</th>
                        <th>Acoes</th>
                    </tr>
                </thead>
                <tbody>{roles_rows}</tbody>
            </table>
        </div>
    </div>
    """

    return base_layout("Custo de Projetos", html)
