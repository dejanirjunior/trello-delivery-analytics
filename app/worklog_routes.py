import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, date, timezone

import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app

from app.worklog_reader import load_cards

BASE_DIR = Path(__file__).resolve().parent.parent

WORKLOG_DB_PATH = Path(os.getenv("WORKLOG_DB_PATH", BASE_DIR / "data" / "worklog.db"))
AUTH_DB_PATH = Path(os.getenv("AUTH_DB_PATH", "/data/auth.db"))
SCHEMA_PATH = BASE_DIR / "app" / "worklog_schema.sql"
TRELLO_CSV_PATH = Path(os.getenv("TRELLO_CSV_PATH", "/app/data/cards_enriched.csv"))

DB_PATH = WORKLOG_DB_PATH

worklog_bp = Blueprint("worklog", __name__)


# =========================
# AUTH / USUÁRIO LOGADO
# =========================

def get_current_user():
    username = session.get("user")

    if not username or not AUTH_DB_PATH.exists():
        return None

    connection = sqlite3.connect(AUTH_DB_PATH)
    connection.row_factory = sqlite3.Row

    user = connection.execute(
        """
        SELECT id, username, role, active, worklog_developer_name
        FROM users
        WHERE username = ?
          AND active = 1
        """,
        (username,)
    ).fetchone()

    connection.close()

    return dict(user) if user else None


def require_login():
    user = get_current_user()

    if not user:
        return redirect("/login")

    if user["role"] not in ["admin", "internal"]:
        return "Acesso negado", 403

    return None


def get_current_developer():
    user = get_current_user()

    if not user:
        return None, None

    return user.get("worklog_developer_name"), user.get("role")


def enforce_developer_filter(selected_dev=""):
    dev, role = get_current_developer()

    if role == "admin":
        return selected_dev or "", role

    return dev or "", role


def render_worklog_template(title, template_name, **context):
    html = render_template(template_name, **context)

    base_layout = current_app.config.get("BASE_LAYOUT_FUNC")
    if base_layout:
        return base_layout(title, html)

    return html


# =========================
# DB
# =========================

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    if SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            connection.executescript(f.read())

    connection.commit()
    connection.close()


def conn():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


init_db()


# =========================
# DATAS / FORMATAÇÃO
# =========================

def parse_iso_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_date_br(iso_date: str):
    return parse_iso_date(iso_date).strftime("%d/%m/%Y")


def parse_any_date(value):
    if not value:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    candidates = [raw, raw[:10]]

    for item in candidates:
        try:
            return datetime.strptime(item, "%Y-%m-%d").date()
        except Exception:
            pass

    return None


def parse_any_datetime(value):
    if not value:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    try:
        if raw.endswith("Z"):
            raw = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(raw)
    except Exception:
        pass

    try:
        return datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


# =========================
# DESENVOLVEDORES
# =========================

def get_devs():
    devs = set()

    if TRELLO_CSV_PATH.exists():
        df = pd.read_csv(TRELLO_CSV_PATH, encoding="utf-8-sig")
        if "assigned_members" in df.columns:
            for value in df["assigned_members"].dropna():
                names = [x.strip() for x in str(value).split(",") if x.strip()]
                devs.update(names)

    if DB_PATH.exists():
        db = conn()
        rows = db.execute("SELECT DISTINCT developer_name FROM worklogs").fetchall()
        db.close()

        for row in rows:
            if row["developer_name"]:
                devs.add(row["developer_name"].strip())

    if AUTH_DB_PATH.exists():
        connection = sqlite3.connect(AUTH_DB_PATH)
        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(
                """
                SELECT DISTINCT worklog_developer_name
                FROM users
                WHERE worklog_developer_name IS NOT NULL
                  AND TRIM(worklog_developer_name) <> ''
                  AND active = 1
                """
            ).fetchall()

            for row in rows:
                devs.add(row["worklog_developer_name"].strip())
        except sqlite3.OperationalError:
            pass

        connection.close()

    for invalid in ["qa", "uat", "QA", "UAT", ""]:
        devs.discard(invalid)

    return sorted(devs)


# =========================
# WORKLOG
# =========================

def get_worklogs(selected_date=None, selected_dev=None, start_date=None, end_date=None):
    db = conn()

    query = """
        SELECT
            id,
            work_date,
            developer_name,
            card_id,
            card_name,
            estimated_flag,
            hours,
            activity_type,
            comment,
            created_at
        FROM worklogs
        WHERE 1=1
    """
    params = []

    if selected_date:
        query += " AND work_date = ?"
        params.append(selected_date)

    if selected_dev:
        query += " AND developer_name = ?"
        params.append(selected_dev)

    if start_date:
        query += " AND work_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND work_date <= ?"
        params.append(end_date)

    query += " ORDER BY work_date DESC, created_at DESC, id DESC"

    rows = db.execute(query, params).fetchall()

    total_hours = sum(float(row["hours"]) for row in rows)

    db.close()

    return rows, total_hours


def get_card_lookup():
    lookup = {}

    for card in load_cards():
        card_id = card.get("card_id")
        if card_id:
            lookup[card_id] = card

    return lookup



def get_daily_saved_cards(dev, work_date):
    db = conn()

    plan = db.execute(
        """
        SELECT id
        FROM daily_plan
        WHERE developer_name = ?
          AND daily_date = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (dev, work_date)
    ).fetchone()

    if not plan:
        db.close()
        return []

    rows = db.execute(
        """
        SELECT
            card_id,
            card_name,
            client_name,
            source_type,
            blocker_text,
            trello_has_block_label
        FROM daily_plan_items
        WHERE daily_plan_id = ?
          AND is_selected = 1
        ORDER BY id
        """,
        (plan["id"],)
    ).fetchall()

    db.close()

    cards = []
    for row in rows:
        cards.append({
            "card_id": row["card_id"],
            "card_name": row["card_name"],
            "client_name": row["client_name"],
            "lista": "",
            "source_type": row["source_type"] or "daily",
            "has_block_label": row["trello_has_block_label"] or 0,
            "reason_text": "card salvo na Daily do dia",
            "score": "",
            "preselected": True,
            "existing_comment": row["blocker_text"] or ""
        })

    return cards


def get_worklog_candidate_cards(dev, work_date):
    saved_cards = get_daily_saved_cards(dev, work_date)

    if saved_cards:
        source_label = "daily_saved"
        suggested = saved_cards
    else:
        daily_data = build_daily_data(work_date, dev)
        source_label = "daily_suggestion"

        suggested = []
        if daily_data:
            for card in daily_data[0].get("suggested", []):
                item = dict(card)
                item["source_type"] = "suggested"
                item["preselected"] = True
                item["existing_comment"] = ""
                suggested.append(item)

    suggested_ids = {c.get("card_id") for c in suggested}

    additional = []
    for card in load_cards():
        if card.get("card_id") in suggested_ids:
            continue

        additional.append({
            "card_id": card.get("card_id", ""),
            "card_name": card.get("card_name", ""),
            "client_name": card.get("client_name", ""),
            "lista": card.get("lista", ""),
            "source_type": "manual",
            "has_block_label": card.get("has_block_label", 0),
            "reason_text": "seleção manual",
            "score": "",
            "preselected": False,
            "existing_comment": ""
        })

    additional.sort(key=lambda c: (c.get("client_name") or "", c.get("lista") or "", c.get("card_name") or ""))

    return suggested, additional, source_label



@worklog_bp.route("/registro-horas")
def index():
    guard = require_login()
    if guard:
        return guard

    developers = get_devs()

    selected_date = request.args.get("work_date", "").strip()
    selected_dev = request.args.get("developer_name", "").strip()

    selected_dev, role = enforce_developer_filter(selected_dev)

    if not selected_date:
        selected_date = date.today().isoformat()

    suggested_cards, additional_cards, suggestion_source = get_worklog_candidate_cards(
        selected_dev,
        selected_date
    )

    worklogs, total_hours = get_worklogs(
        selected_date=selected_date,
        selected_dev=selected_dev
    )

    return render_worklog_template(
        "Registro de Horas · Optaris",
        "worklog/registro_horas.html",
        today=selected_date,
        developers=developers,
        selected_dev=selected_dev,
        suggested_cards=suggested_cards,
        additional_cards=additional_cards,
        suggestion_source=suggestion_source,
        worklogs=worklogs,
        total_hours=round(total_hours, 2),
        role=role
    )


@worklog_bp.route("/save_worklog_batch", methods=["POST"])
def save_worklog_batch():
    guard = require_login()
    if guard:
        return guard

    work_date = request.form.get("work_date", "").strip()
    developer_name = request.form.get("developer_name", "").strip()

    developer_name, role = enforce_developer_filter(developer_name)

    if not work_date:
        work_date = date.today().isoformat()

    if not developer_name:
        return "Usuário sem desenvolvedor vinculado ao Worklog.", 400

    selected_cards = request.form.getlist("selected_cards")
    card_lookup = get_card_lookup()

    db = conn()

    for card_id in selected_cards:
        card = card_lookup.get(card_id, {})

        card_name = (
            request.form.get(f"card_name__{card_id}", "").strip()
            or card.get("card_name", "")
        )

        estimated_flag_raw = (
            request.form.get(f"estimated_flag__{card_id}", "").strip()
            or str(card.get("estimated_flag", 1))
        )

        try:
            estimated_flag = int(estimated_flag_raw)
        except Exception:
            estimated_flag = 1

        hours_raw = (
            request.form.get(f"hours__{card_id}", "").strip()
            or request.form.get("hours__generic", "").strip()
        )

        activity_type = (
            request.form.get(f"activity_type__{card_id}", "").strip()
            or request.form.get("activity_type__generic", "").strip()
        )

        comment = (
            request.form.get(f"comment__{card_id}", "").strip()
            or request.form.get("comment__generic", "").strip()
        )

        if not hours_raw:
            continue

        try:
            hours = float(hours_raw)
        except Exception:
            continue

        if hours <= 0 or not activity_type:
            continue

        db.execute(
            """
            INSERT INTO worklogs (
                work_date,
                developer_name,
                card_id,
                card_name,
                estimated_flag,
                hours,
                activity_type,
                comment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                work_date,
                developer_name,
                card_id,
                card_name,
                estimated_flag,
                hours,
                activity_type,
                comment
            )
        )

    db.commit()
    db.close()

    return redirect(url_for(
        "worklog.index",
        work_date=work_date,
        developer_name=developer_name
    ))


@worklog_bp.route("/worklog_history")
def worklog_history():
    guard = require_login()
    if guard:
        return guard

    developers = get_devs()

    selected_dev = request.args.get("developer_name", "").strip()
    selected_dev, role = enforce_developer_filter(selected_dev)

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    if not start_date:
        today = date.today()
        start_date = today.replace(day=1).isoformat()

    if not end_date:
        end_date = date.today().isoformat()

    rows, total_hours = get_worklogs(
        selected_dev=selected_dev,
        start_date=start_date,
        end_date=end_date
    )

    return render_worklog_template(
        "Histórico de Horas · Optaris",
        "worklog/worklog_history.html",
        developers=developers,
        selected_dev=selected_dev,
        start_date=start_date,
        end_date=end_date,
        worklogs=rows,
        total_hours=round(total_hours, 2),
        role=role
    )


# =========================
# DAILY
# =========================

def get_recent_cards(dev, base_date_iso):
    db = conn()

    rows = db.execute(
        """
        SELECT card_id, card_name, SUM(hours) AS h
        FROM worklogs
        WHERE developer_name = ?
          AND work_date BETWEEN date(?, '-2 day') AND date(?)
        GROUP BY card_id, card_name
        ORDER BY h DESC, card_name ASC
        """,
        (dev, base_date_iso, base_date_iso)
    ).fetchall()

    db.close()
    return rows


def get_week_summary_for_dev(dev, base_date_iso):
    base = parse_iso_date(base_date_iso)
    monday = base - timedelta(days=base.weekday())
    friday = monday + timedelta(days=4)

    days_map = {
        (monday + timedelta(days=i)).isoformat(): 0.0
        for i in range(5)
    }

    db = conn()

    rows = db.execute(
        """
        SELECT work_date, SUM(hours) AS total_hours
        FROM worklogs
        WHERE developer_name = ?
          AND work_date BETWEEN ? AND ?
        GROUP BY work_date
        ORDER BY work_date
        """,
        (dev, monday.isoformat(), friday.isoformat())
    ).fetchall()

    db.close()

    for row in rows:
        if row["work_date"] in days_map:
            days_map[row["work_date"]] = float(row["total_hours"])

    total = sum(days_map.values())

    return {
        "monday_br": monday.strftime("%d/%m/%Y"),
        "friday_br": friday.strftime("%d/%m/%Y"),
        "days": [
            ("Seg", days_map[(monday + timedelta(days=0)).isoformat()]),
            ("Ter", days_map[(monday + timedelta(days=1)).isoformat()]),
            ("Qua", days_map[(monday + timedelta(days=2)).isoformat()]),
            ("Qui", days_map[(monday + timedelta(days=3)).isoformat()]),
            ("Sex", days_map[(monday + timedelta(days=4)).isoformat()])
        ],
        "total": total,
        "difference": total - 40
    }


def compute_card_score(card, dev, base_date, recent_hours_map):
    score = 0.0
    reasons = []

    card_id = card.get("card_id", "")
    recent_hours = recent_hours_map.get(card_id, 0.0)

    if recent_hours > 0:
        score += min(recent_hours * 6, 36)
        reasons.append(f"histórico recente ({recent_hours}h)")

    if dev in card.get("assigned_members", []):
        score += 14
        reasons.append("atribuído ao dev")

    lista = (card.get("lista") or "").strip()
    lista_weight = {
        "UAT": 16,
        "Q.A.": 14,
        "Em dev": 12,
        "Refinado": 8,
        "Concluído": -50
    }.get(lista, 0)

    score += lista_weight

    if lista_weight > 0:
        reasons.append(f"etapa {lista}")

    priority = (card.get("priority") or "").strip().lower()

    if priority == "high":
        score += 22
        reasons.append("prioridade alta")
    elif priority == "medium":
        score += 10
        reasons.append("prioridade média")
    elif priority == "low":
        score += 2

    risk = (card.get("risk") or "").strip().lower()

    if risk in ("high", "alto"):
        score += 10
        reasons.append("risco alto")
    elif risk in ("medium", "médio", "medio"):
        score += 4

    due_date = parse_any_date(card.get("due_date"))
    compromisso_date = parse_any_date(card.get("data_compromisso"))

    chosen_date = None
    chosen_label = None

    if compromisso_date:
        chosen_date = compromisso_date
        chosen_label = "data de compromisso"
    elif due_date:
        chosen_date = due_date
        chosen_label = "due date"

    if chosen_date:
        delta = (chosen_date - base_date).days

        if delta < 0:
            score += 34
            reasons.append(f"{chosen_label} vencida")
        elif delta == 0:
            score += 32
            reasons.append(f"{chosen_label} hoje")
        elif delta == 1:
            score += 26
            reasons.append(f"{chosen_label} amanhã")
        elif delta <= 3:
            score += 18
            reasons.append(f"{chosen_label} próxima")
        elif delta <= 7:
            score += 10
            reasons.append(f"{chosen_label} esta semana")

    if card.get("has_block_label") == 1:
        score -= 15
        reasons.append("card bloqueado")

    if card.get("estimated_flag") == 0:
        score -= 3

    return score, reasons


def get_inactive_cards_for_dev(dev, base_date, all_cards):
    inactive_cards = []

    for card in all_cards:
        if dev not in card.get("assigned_members", []):
            continue

        lista = card.get("lista", "")

        if lista not in ["Refinado", "Em dev", "Q.A.", "UAT", "Concluído"]:
            continue

        dt = parse_any_datetime(card.get("last_activity"))
        if not dt:
            dt = parse_any_datetime(card.get("created_date"))

        if not dt:
            continue

        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

        inactive_days = (datetime.combine(base_date, datetime.min.time()) - dt).days

        if inactive_days > 10:
            inactive_cards.append({
                "card_id": card.get("card_id", ""),
                "card_name": card.get("card_name", ""),
                "client_name": card.get("client_name", ""),
                "lista": card.get("lista", ""),
                "inactive_days": inactive_days
            })

    inactive_cards.sort(key=lambda c: (-c["inactive_days"], c["card_name"]))
    return inactive_cards[:6]


def build_daily_data(base_date_iso, selected_dev=None):
    devs = get_devs()

    if selected_dev:
        devs = [d for d in devs if d == selected_dev]

    all_cards = load_cards()
    base_date = parse_iso_date(base_date_iso)
    is_friday = base_date.weekday() == 4

    result = []

    for index, dev in enumerate(devs):
        recent = get_recent_cards(dev, base_date_iso)
        recent_hours_map = {}
        recent_lookup = {}

        for row in recent:
            recent_hours_map[row["card_id"]] = float(row["h"])
            recent_lookup[row["card_id"]] = float(row["h"])

        scored_cards = []

        for card in all_cards:
            lista = card.get("lista", "")

            if lista == "Concluído":
                continue

            score, reasons = compute_card_score(card, dev, base_date, recent_hours_map)

            scored_cards.append({
                "card_id": card.get("card_id", ""),
                "card_name": card.get("card_name", ""),
                "client_name": card.get("client_name", ""),
                "lista": card.get("lista", ""),
                "hours_recent": recent_lookup.get(card.get("card_id", ""), 0.0),
                "has_block_label": card.get("has_block_label", 0),
                "is_assigned_to_dev": dev in card.get("assigned_members", []),
                "score": round(score, 1),
                "reason_text": ", ".join(reasons[:3]) if reasons else "sem contexto forte"
            })

        scored_cards.sort(
            key=lambda c: (
                -c["score"],
                0 if c["is_assigned_to_dev"] else 1,
                c["client_name"] or "",
                c["card_name"] or ""
            )
        )

        suggested = scored_cards[:3]
        suggested_ids = {c["card_id"] for c in suggested}

        additional_cards = [
            card for card in scored_cards
            if card["card_id"] not in suggested_ids
        ]

        weekly_summary = get_week_summary_for_dev(dev, base_date_iso) if is_friday else None
        inactive_cards = get_inactive_cards_for_dev(dev, base_date, all_cards)

        result.append({
            "dev": dev,
            "color": f"dev-color-{index % 4}",
            "suggested": suggested,
            "additional_cards": additional_cards[:40],
            "weekly_summary": weekly_summary,
            "inactive_cards": inactive_cards
        })

    return result


@worklog_bp.route("/daily")
def daily():
    guard = require_login()
    if guard:
        return guard

    selected_date = request.args.get("date", "").strip()
    selected_dev = request.args.get("developer_name", "").strip()

    selected_dev, role = enforce_developer_filter(selected_dev)

    if not selected_date:
        selected_date = date.today().isoformat()

    all_devs = get_devs()

    return render_worklog_template(
        "Daily · Optaris",
        "worklog/daily.html",
        today_iso=selected_date,
        today_br=format_date_br(selected_date),
        is_friday=parse_iso_date(selected_date).weekday() == 4,
        data=build_daily_data(selected_date, selected_dev if selected_dev else None),
        developers=all_devs,
        selected_dev=selected_dev,
        role=role
    )


@worklog_bp.route("/save_daily", methods=["POST"])
def save_daily():
    guard = require_login()
    if guard:
        return guard

    daily_date = request.form.get("date", "").strip() or date.today().isoformat()

    form_developer = request.form.get("developer_name", "").strip()
    forced_dev, role = enforce_developer_filter(form_developer)

    db = conn()

    dev_keys = [
        key.split("::", 1)[1]
        for key in request.form
        if key.startswith("dev::")
    ]

    if not dev_keys and forced_dev:
        dev_keys = [forced_dev]

    for dev in dev_keys:
        if role != "admin" and dev != forced_dev:
            continue

        cursor = db.execute(
            """
            INSERT INTO daily_plan (
                daily_date,
                developer_name,
                notes,
                absence_type,
                absence_detail
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                daily_date,
                dev,
                request.form.get(f"note::{dev}", request.form.get("notes", "")).strip(),
                request.form.get(f"absence_type::{dev}", "").strip(),
                request.form.get(f"absence_detail::{dev}", "").strip()
            )
        )

        daily_plan_id = cursor.lastrowid

        for form_key in request.form:
            if form_key.startswith(f"item::{dev}::"):
                parts = request.form[form_key].split("|")
                card_id = parts[0] if len(parts) > 0 else ""
                card_name = parts[1] if len(parts) > 1 else ""
                client_name = parts[2] if len(parts) > 2 else ""
                source_type = parts[3] if len(parts) > 3 else "manual"
                has_block_label = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0

                blocker_text = request.form.get(f"blocker_item::{dev}::{card_id}", "").strip()
                needs_block_label_mark = 1 if blocker_text and has_block_label == 0 else 0

                db.execute(
                    """
                    INSERT INTO daily_plan_items (
                        daily_plan_id,
                        card_id,
                        card_name,
                        client_name,
                        source_type,
                        is_selected,
                        blocker_text,
                        trello_has_block_label,
                        needs_block_label_mark
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        daily_plan_id,
                        card_id,
                        card_name,
                        client_name,
                        source_type,
                        1,
                        blocker_text,
                        has_block_label,
                        needs_block_label_mark
                    )
                )

        for extra_value in request.form.getlist(f"add_card::{dev}"):
            if not extra_value:
                continue

            parts = extra_value.split("|")
            card_id = parts[0] if len(parts) > 0 else ""
            card_name = parts[1] if len(parts) > 1 else ""
            client_name = parts[2] if len(parts) > 2 else ""
            source_type = "manual"
            has_block_label = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0

            if not card_id:
                continue

            blocker_text = request.form.get(f"blocker_extra::{dev}", "").strip()
            needs_block_label_mark = 1 if blocker_text and has_block_label == 0 else 0

            db.execute(
                """
                INSERT INTO daily_plan_items (
                    daily_plan_id,
                    card_id,
                    card_name,
                    client_name,
                    source_type,
                    is_selected,
                    blocker_text,
                    trello_has_block_label,
                    needs_block_label_mark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    daily_plan_id,
                    card_id,
                    card_name,
                    client_name,
                    source_type,
                    1,
                    blocker_text,
                    has_block_label,
                    needs_block_label_mark
                )
            )

    db.commit()
    db.close()

    return redirect(url_for(
        "worklog.daily",
        date=daily_date,
        developer_name=forced_dev
    ))


@worklog_bp.route("/daily_history")
def daily_history():
    guard = require_login()
    if guard:
        return guard

    selected_dev = request.args.get("developer_name", "").strip()
    selected_dev, role = enforce_developer_filter(selected_dev)

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    all_devs = get_devs()

    db = conn()

    base_query = """
        SELECT
            id,
            daily_date,
            developer_name,
            notes,
            absence_type,
            absence_detail,
            created_at
        FROM daily_plan
        WHERE 1=1
    """
    params = []

    if selected_dev:
        base_query += " AND developer_name = ?"
        params.append(selected_dev)

    if start_date:
        base_query += " AND daily_date >= ?"
        params.append(start_date)

    if end_date:
        base_query += " AND daily_date <= ?"
        params.append(end_date)

    base_query += " ORDER BY daily_date DESC, developer_name ASC, id DESC"

    plan_rows = db.execute(base_query, params).fetchall()

    item_rows = db.execute(
        """
        SELECT
            daily_plan_id,
            card_name,
            client_name,
            source_type,
            blocker_text,
            trello_has_block_label,
            needs_block_label_mark
        FROM daily_plan_items
        ORDER BY daily_plan_id, id
        """
    ).fetchall()

    db.close()

    cards_by_plan = {}

    for row in item_rows:
        cards_by_plan.setdefault(row["daily_plan_id"], []).append(row)

    history = []

    for plan in plan_rows:
        history.append({
            "id": plan["id"],
            "daily_date": plan["daily_date"],
            "daily_date_br": format_date_br(plan["daily_date"]),
            "developer_name": plan["developer_name"],
            "notes": plan["notes"],
            "absence_type": plan["absence_type"],
            "absence_detail": plan["absence_detail"],
            "plan_cards": cards_by_plan.get(plan["id"], [])
        })

    return render_worklog_template(
        "Histórico da Daily · Optaris",
        "worklog/daily_history.html",
        history=history,
        developers=all_devs,
        selected_dev=selected_dev,
        start_date=start_date,
        end_date=end_date,
        role=role
    )
