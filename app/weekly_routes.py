from collections import defaultdict
from html import escape

from app.weekly_service import (
    compare_weeklies,
    create_weekly,
    get_weekly_detail,
    is_blocked,
    is_high_risk,
    is_highest_risk, get_card_stage,
    list_weeklies,
    load_cards_for_client,
)


def safe(value):
    return escape(str(value or ""))


def register_weekly_routes(app, deps):
    base_layout = deps["base_layout"]
    require_login = deps["require_login"]
    get_current_user = deps["get_current_user"]
    user_has_client_access = deps["user_has_client_access"]
    request = deps["request"]
    redirect = deps["redirect"]

    def can_create_weekly(user):
        return bool(user and user["role"] in ["admin", "internal"])

    def is_done(card):
        status = (card.get("lista") or "").strip().lower()
        return status in ["concluído", "concluido", "done", "deploy"]

    def is_doing(card):
        status = (card.get("lista") or "").strip().lower()
        return status in ["em dev", "q.a.", "qa", "uat", "doing"]


    def card_status(card):
        return (card.get("lista") or "Sem status").strip() or "Sem status"


    def count_done(cards):
        return sum(1 for c in cards if card_status(c).lower() in ["done", "concluído", "concluido"])


    def count_doing(cards):
        doing_terms = ["doing", "em dev", "q.a.", "qa", "uat", "em andamento"]
        return sum(1 for c in cards if card_status(c).lower() in doing_terms)

    def weekly_css():
        return """
        <style>
            .weekly-hero {
                display:grid;
                grid-template-columns: repeat(5, minmax(120px, 1fr));
                gap:12px;
                margin:18px 0;
            }

            .weekly-kpi {
                border:1px solid rgba(255,255,255,0.10);
                background:rgba(255,255,255,0.04);
                border-radius:18px;
                padding:16px;
            }

            .weekly-kpi-label {
                font-size:12px;
                opacity:0.72;
                text-transform:uppercase;
                letter-spacing:.08em;
                margin-bottom:8px;
            }

            .weekly-kpi-value {
                font-size:30px;
                font-weight:900;
                line-height:1;
            }

            .weekly-kpi-danger {
                border-color:rgba(240,101,101,0.45);
                background:rgba(240,101,101,0.10);
            }

            .weekly-kpi-warning {
                border-color:rgba(250,176,5,0.45);
                background:rgba(250,176,5,0.10);
            }

            .weekly-actions {
                display:flex;
                gap:8px;
                flex-wrap:wrap;
                margin-top:12px;
            }

            .weekly-section-title {
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:12px;
                margin-bottom:12px;
            }

            .weekly-section-title h2 {
                margin:0;
            }

            .weekly-card {
                border:1px solid rgba(255,255,255,0.10);
                border-radius:16px;
                padding:14px;
                margin:10px 0;
                background:rgba(255,255,255,0.035);
            }

            .weekly-card.blocked {
                border-color:rgba(240,101,101,0.45);
                background:rgba(240,101,101,0.08);
            }

            .weekly-card.high-risk {
                border-color:rgba(250,176,5,0.45);
                background:rgba(250,176,5,0.07);
            }

            .weekly-card-title {
                font-weight:900;
                font-size:16px;
                margin-bottom:10px;
            }

            .weekly-card-meta {
                display:flex;
                gap:8px;
                flex-wrap:wrap;
                font-size:13px;
                opacity:0.96;
            }

            .weekly-pill {
                display:inline-flex;
                align-items:center;
                border-radius:999px;
                padding:4px 9px;
                background:rgba(255,255,255,0.06);
                border:1px solid rgba(255,255,255,0.08);
                font-size:12px;
                font-weight:700;
            }

            .badge {
                display:inline-block;
                border-radius:999px;
                padding:4px 9px;
                font-size:12px;
                font-weight:900;
                letter-spacing:.03em;
            }

            .badge.danger {
                background:rgba(240,101,101,0.18);
                color:#ff8787;
                border:1px solid rgba(240,101,101,0.42);
            }

            .badge.warning {
                background:rgba(250,176,5,0.18);
                color:#ffd43b;
                border:1px solid rgba(250,176,5,0.42);
            }

            .weekly-comment {
                margin-top:10px;
                padding:10px 12px;
                border-left:3px solid rgba(255,255,255,0.20);
                background:rgba(0,0,0,0.12);
                border-radius:10px;
                font-size:14px;
                opacity:0.92;
            }

            .weekly-comment strong {
                display:block;
                margin-bottom:4px;
            }

            .weekly-status-group {
                margin:16px 0;
                border-top:1px solid rgba(255,255,255,0.08);
                padding-top:12px;
            }

            .weekly-status-heading {
                font-size:15px;
                font-weight:900;
                opacity:0.90;
                margin-bottom:8px;
            }

            textarea {
                width:100%;
                min-height:82px;
            }

            .critical-form-card {
                border:1px solid rgba(255,255,255,0.12);
                border-radius:14px;
                padding:14px;
                margin:12px 0;
                background:rgba(255,255,255,0.03);
            }

            @media (max-width: 900px) {
                .weekly-hero {
                    grid-template-columns: repeat(2, minmax(120px, 1fr));
                }
            }
        </style>
        """

    def make_badges(card):
        badges = ""

        if is_blocked(card):
            badges += '<span class="weekly-pill danger" style="background:#dc2626!important;color:#ffffff!important;border:1px solid #ef4444!important;">BLOCK</span> '

        if is_highest_risk(card):
            badges += '<span class="weekly-pill danger" style="background:#991b1b!important;color:#ffffff!important;border:1px solid #ef4444!important;">RISCO MÁXIMO</span> '
        elif is_high_risk(card):
            badges += '<span class="weekly-pill warning" style="background:#f59e0b!important;color:#111827!important;border:1px solid #fbbf24!important;">Risco alto</span> '

        if is_done(card):
            badges += '<span class="weekly-pill ok">Finalizado</span> '

        return badges

    def card_class(card):
        classes = ["weekly-card"]

        if is_blocked(card):
            classes.append("blocked")
        elif is_high_risk(card):
            classes.append("high-risk")

        return " ".join(classes)

    def render_card_summary(card):
        comments = card.get("_comments", {})

        block_comment = comments.get("block_comment", "")
        risk_comment = comments.get("risk_comment", "")
        next_step = comments.get("next_step", "")

        comments_html = ""

        if block_comment:
            comments_html += f"""
            <div class="weekly-muted"><strong>Comentário de bloqueio:</strong> {safe(block_comment)}</div>
            """

        if risk_comment:
            comments_html += f"""
            <div class="weekly-muted"><strong>Comentário de risco:</strong> {safe(risk_comment)}</div>
            """

        if next_step:
            comments_html += f"""
            <div class="weekly-muted"><strong>Próximo passo:</strong> {safe(next_step)}</div>
            """

        return f"""
        <div class="{card_class(card)}">
            <div class="weekly-card-title">{safe(card.get("card_name"))}</div>
            <div class="weekly-card-meta">
                {make_badges(card)}
                <span class="weekly-pill">Status: {safe(card.get("lista"))}</span>
                <span class="weekly-pill">Responsável: {safe(card.get("assigned_members") or "Não informado")}</span>
                <span class="weekly-pill">Prioridade: {safe(card.get("priority") or "Não informada")}</span>
                <span class="weekly-pill">Risco: {safe(card.get("risk") or "Não informado")}</span>
                <span class="weekly-pill">Última atividade: {safe(card.get("last_activity") or "Não informada")}</span>
            </div>
            {comments_html}
        </div>
        """

    def render_cards_section(title, cards, empty_message):
        if not cards:
            cards_html = f"<p>{safe(empty_message)}</p>"
        else:
            cards_html = "".join(render_card_summary(card) for card in cards)

        return f"""
        <div class="card">
            <div class="weekly-section-title">
                <h2>{safe(title)}</h2>
                <span class="weekly-pill">{len(cards)} cards</span>
            </div>
            {cards_html}
        </div>
        """

    def render_grouped_cards(cards):
        groups = defaultdict(list)

        for card in cards:
            groups[card.get("lista") or "Sem status"].append(card)

        order = ["Painel", "Backlog", "Refinado", "Em dev", "Q.A.", "UAT", "Concluído", "Deploy"]

        html = ""

        for status in order:
            if status in groups:
                html += f"""
                <div class="weekly-status-group">
                    <div class="weekly-status-heading">{safe(status)} ({len(groups[status])})</div>
                    {"".join(render_card_summary(card) for card in groups[status])}
                </div>
                """

        for status, status_cards in groups.items():
            if status not in order:
                html += f"""
                <div class="weekly-status-group">
                    <div class="weekly-status-heading">{safe(status)} ({len(status_cards)})</div>
                    {"".join(render_card_summary(card) for card in status_cards)}
                </div>
                """

        return html or "<p>Nenhum card capturado.</p>"

    def render_kpis(cards, blocked_cards, high_risk_cards):
        total = len(cards)
        doing = len([c for c in cards if is_doing(c)])
        done = len([c for c in cards if is_done(c)])

        return f"""
        <div class="weekly-summary-grid">
            <div class="weekly-kpi">
                <div class="weekly-kpi-label">Total de cards</div>
                <div class="weekly-kpi-value">{total}</div>
            </div>
            <div class="weekly-kpi">
                <div class="weekly-kpi-label">Bloqueados</div>
                <div class="weekly-kpi-value">{len(blocked_cards)}</div>
            </div>
            <div class="weekly-kpi">
                <div class="weekly-kpi-label">Risco alto</div>
                <div class="weekly-kpi-value">{len(high_risk_cards)}</div>
            </div>
            <div class="weekly-kpi">
                <div class="weekly-kpi-label">Em andamento</div>
                <div class="weekly-kpi-value">{doing}</div>
            </div>
            <div class="weekly-kpi">
                <div class="weekly-kpi-label">Finalizados</div>
                <div class="weekly-kpi-value">{done}</div>
            </div>
        </div>
        """

    @app.route("/weekly/<slug>")
    def weekly_list(slug):
        guard = require_login()
        if guard:
            return guard

        if not user_has_client_access(slug):
            return "Acesso negado", 403

        user = get_current_user()
        rows = list_weeklies(slug)

        create_button = ""
        if can_create_weekly(user):
            create_button = f"""
            <a class="btn btn-primary" href="/weekly/create/{safe(slug)}">Nova Weekly</a>
            """

        items = ""

        for r in rows:
            items += f"""
            <div class="card">
                <div class="weekly-section-title">
                    <div>
                        <h3>Weekly de {safe(r["date"])}</h3>
                        <p>Criado por: {safe(r["created_by"])} em {safe(r["created_at"])}</p>
                    </div>
                    <a class="btn btn-secondary" href="/weekly/view/{r["id"]}">Ver cena da Weekly</a>
                </div>
            </div>
            """

        if not items:
            items = """
            <div class="card">
                <p>Nenhuma Weekly registrada para este cliente.</p>
            </div>
            """

        return base_layout("Weekly · Optaris", f"""
            {weekly_css()}

            <div class="header">
                <div>
                    <div class="eyebrow">Histórico semanal</div>
                    <h1>Weekly - {safe(slug)}</h1>
                    <p>Consulte snapshots históricos do delivery, bloqueios e riscos discutidos com o cliente.</p>
                </div>
                <div>{create_button}</div>
            </div>

            {items}
        """)

    @app.route("/weekly/create/<slug>", methods=["GET", "POST"])
    def weekly_create(slug):
        guard = require_login()
        if guard:
            return guard

        user = get_current_user()

        if not can_create_weekly(user):
            return "Acesso negado", 403

        if not user_has_client_access(slug):
            return "Acesso negado", 403


        cards = load_cards_for_client(slug)

        refined_cards = [c for c in cards if get_card_stage(c) == "refinado"]
        backlog_cards = [c for c in cards if get_card_stage(c) == "backlog"]

        critical_cards = [
            c for c in cards
            if is_blocked(c) or is_high_risk(c)
        ]

        if request.method == "POST":
            date = request.form.get("date", "")
            risks = request.form.get("risks", "")
            next_steps = request.form.get("next_steps", "")
            notes = request.form.get("notes", "")

            card_comments = {}

            for card in critical_cards:
                card_id = card.get("card_id") or ""

                block_comment = request.form.get(f"block_comment_{card_id}", "")
                risk_comment = request.form.get(f"risk_comment_{card_id}", "")
                next_step = request.form.get(f"next_step_{card_id}", "")

                if block_comment or risk_comment or next_step:
                    card_comments[card_id] = {
                        "block_comment": block_comment,
                        "risk_comment": risk_comment,
                        "next_step": next_step
                    }

            weekly_id = create_weekly(
                slug,
                date,
                user["username"],
                risks,
                next_steps,
                notes,
                card_comments
            )

            return redirect(f"/weekly/view/{weekly_id}")

        critical_html = ""

        for card in critical_cards:
            card_id = card.get("card_id") or ""
            extra_class = "blocked" if is_blocked(card) else "high-risk"

            critical_html += f"""
            <div class="critical-form-card {extra_class}">
                <h3>{safe(card.get("card_name"))}</h3>
                <p>
                    {make_badges(card)}
                    <span class="weekly-pill">Status: {safe(card.get("lista"))}</span>
                    <span class="weekly-pill">Responsável: {safe(card.get("assigned_members") or "Não informado")}</span>
                    <span class="weekly-pill">Risco: {safe(card.get("risk") or "Não informado")}</span>
                    <span class="weekly-pill">Prioridade: {safe(card.get("priority") or "Não informada")}</span>
                </p>

                <label>Comentário sobre bloqueio</label>
                <textarea name="block_comment_{safe(card_id)}" placeholder="Explique o bloqueio deste card, se aplicável."></textarea>

                <label>Comentário sobre risco</label>
                <textarea name="risk_comment_{safe(card_id)}" placeholder="Explique o risco deste card, se aplicável."></textarea>

                <label>Próximo passo deste card</label>
                <textarea name="next_step_{safe(card_id)}" placeholder="Informe o próximo passo combinado."></textarea>
            </div>
            """

        if not critical_html:
            critical_html = "<p>Não há cards bloqueados ou com risco alto neste momento.</p>"

        return base_layout("Criar Weekly · Optaris", f"""
            {weekly_css()}

            <div class="header">
                <div>
                    <div class="eyebrow">Snapshot semanal</div>
                    <h1>Criar Weekly - {safe(slug)}</h1>
                    <p>A Weekly salva a cena atual dos cards para consulta histórica.</p>
                </div>
                <div>
                    <a class="btn btn-secondary" href="/weekly/{safe(slug)}">Voltar</a>
                </div>
            </div>

            <div class="card">
                <form method="POST">
                    <label>Data da reunião</label>
                    <input name="date" type="date" required>

                    <label>Riscos gerais da reunião</label>
                    <textarea name="risks" placeholder="Resumo dos riscos discutidos na reunião."></textarea>

                    <label>Próximos passos gerais</label>
                    <textarea name="next_steps" placeholder="Resumo dos próximos passos combinados."></textarea>

                    <label>Observações gerais</label>
                    <textarea name="notes" placeholder="Observações adicionais da reunião."></textarea>

                    <h2>Cards críticos da reunião</h2>
                    <p>Preencha comentários por card quando houver bloqueio, risco alto/máximo ou encaminhamento específico.</p>

                    {critical_html}

                    <button type="submit">Salvar cena da Weekly</button>
                </form>
            </div>
        """)

    @app.route("/weekly/view/<int:weekly_id>")
    def weekly_view(weekly_id):
        guard = require_login()
        if guard:
            return guard

        detail = get_weekly_detail(weekly_id)

        if not detail:
            return "Weekly não encontrada", 404

        weekly = detail["weekly"]
        notes = detail["notes"]
        cards = detail["cards"]
        blocked_cards = detail["blocked_cards"]
        high_risk_cards = detail["high_risk_cards"]

        refined_cards = [c for c in cards if get_card_stage(c) == "refinado"]
        backlog_cards = [c for c in cards if get_card_stage(c) == "backlog"]

        if not user_has_client_access(weekly["client_slug"]):
            return "Acesso negado", 403

        notes_html = f"""
        <div class="card">
            <h2>Resumo da reunião</h2>

            <h3>Riscos gerais</h3>
            <p>{safe(notes["risks"] if notes else "")}</p>

            <h3>Próximos passos gerais</h3>
            <p>{safe(notes["next_steps"] if notes else "")}</p>

            <h3>Observações gerais</h3>
            <p>{safe(notes["notes"] if notes else "")}</p>
        </div>
        """

        grouped_snapshot = f"""
        <div class="card">
            <div class="weekly-section-title">
                <h2>Snapshot completo por status</h2>
                <span class="weekly-pill">{len(cards)} cards</span>
            </div>
            {render_grouped_cards(cards)}
        </div>
        """

        return base_layout("Cena da Weekly · Optaris", f"""
            {weekly_css()}

            <div class="header">
                <div>
                    <div class="eyebrow">Cena histórica da operação</div>
                    <h1>Weekly {safe(weekly["date"])} - {safe(weekly["client_slug"])}</h1>
                    <p>Criado por {safe(weekly["created_by"])} em {safe(weekly["created_at"])}.</p>
                </div>
                <div>
                    <a class="btn btn-primary" href="/weekly/pdf/{weekly["id"]}">Exportar PDF</a>
                    <a class="btn btn-primary" href="/weekly/compare/{weekly["id"]}">Comparar com anterior</a>
                    <a class="btn btn-secondary" href="/weekly/{safe(weekly["client_slug"])}">Voltar ao histórico</a>
                </div>
            </div>

            {render_kpis(cards, blocked_cards, high_risk_cards)}

            {notes_html}

            {render_cards_section("Cards bloqueados", blocked_cards, "Nenhum card bloqueado nesta Weekly.")}

            {render_cards_section("Cards com risco alto ou máximo", high_risk_cards, "Nenhum card com risco alto ou máximo nesta Weekly.")}

            {render_cards_section("🔵 Próximos a serem iniciados (Refinados)", refined_cards, "Nenhum card refinado disponível.")}

            {grouped_snapshot}

            {render_cards_section("⚪ Backlog (baixa prioridade)", backlog_cards, "Nenhum card em backlog.")}
        """)
