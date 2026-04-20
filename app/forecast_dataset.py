from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CARDS_FILE = DATA_DIR / "cards_enriched.csv"
LEAD_FILE = DATA_DIR / "lead_time_cards.csv"
MOVEMENTS_FILE = DATA_DIR / "card_movements.csv"
OUTPUT_FILE = DATA_DIR / "forecast_dataset.csv"


def safe_read_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def get_stage_entry(group: pd.DataFrame, stage_name: str):
    stage_rows = group[group["to_list"] == stage_name]
    if stage_rows.empty:
        return None
    return stage_rows.sort_values("date").iloc[0]["date"]


def get_last_stage_entry(group: pd.DataFrame, stage_name: str):
    stage_rows = group[group["to_list"] == stage_name]
    if stage_rows.empty:
        return None
    return stage_rows.sort_values("date").iloc[-1]["date"]


def detect_tipo(card: pd.Series) -> str:
    if bool(card.get("is_bug", False)):
        return "BUG"
    if bool(card.get("is_block", False)):
        return "BLOCK"
    if bool(card.get("is_feature", False)):
        return "FEATURE"
    if bool(card.get("is_debito_tecnico", False)):
        return "DEBITO TECNICO"
    return "GERAL"


def main():
    if not CARDS_FILE.exists():
        print("Arquivo cards_enriched.csv não encontrado")
        return

    df_cards = pd.read_csv(CARDS_FILE)
    df_lead = safe_read_csv(LEAD_FILE)
    df_moves = safe_read_csv(MOVEMENTS_FILE)

    if not df_moves.empty:
        df_moves["date"] = pd.to_datetime(df_moves["date"], utc=True, errors="coerce")

    forecast_rows = []

    for _, card in df_cards.iterrows():
        card_id = card.get("card_id")
        card_name = card.get("card_name")

        move_group = pd.DataFrame()
        if not df_moves.empty:
            move_group = df_moves[df_moves["card_id"] == card_id].copy()

        start_refinado = None
        start_dev = None
        done_date = None
        deploy_prd_date = None

        if not move_group.empty:
            start_refinado = get_stage_entry(move_group, "Refinado")
            start_dev = get_stage_entry(move_group, "Em dev")
            done_date = get_last_stage_entry(move_group, "Concluído")
            deploy_prd_date = get_last_stage_entry(move_group, "Deploy PRD")

        lead_time_days = None
        if not df_lead.empty:
            lead_row = df_lead[df_lead["card_id"] == card_id]
            if not lead_row.empty:
                lead_time_days = lead_row.iloc[0].get("lead_time_days")

        cycle_time_days = None
        if start_dev is not None:
            final_date = deploy_prd_date if deploy_prd_date is not None else done_date
            if final_date is not None:
                cycle_time_days = round(
                    (pd.to_datetime(final_date) - pd.to_datetime(start_dev)).total_seconds() / 86400,
                    2
                )

        if deploy_prd_date is not None:
            completion_type = "client_done"
        elif done_date is not None:
            completion_type = "internal_done"
        else:
            completion_type = "open"

        forecast_rows.append({
            "card_id": card_id,
            "card_name": card_name,
            "cliente": card.get("cliente_label"),
            "tipo": detect_tipo(card),
            "assigned_members": card.get("assigned_members"),
            "story_point": card.get("story_point"),
            "effort": card.get("effort"),
            "total_horas_executado": card.get("total_horas_executado"),
            "created_date": card.get("created_date"),
            "data_compromisso": card.get("data_compromisso"),
            "due_date": card.get("due_date"),
            "start_refinado": start_refinado,
            "start_dev": start_dev,
            "done_date": done_date,
            "deploy_prd_date": deploy_prd_date,
            "lead_time_days": lead_time_days,
            "cycle_time_days": cycle_time_days,
            "completion_type": completion_type,
        })

    df_forecast = pd.DataFrame(forecast_rows)

    # normalizações numéricas
    for col in ["story_point", "effort", "total_horas_executado", "lead_time_days", "cycle_time_days"]:
        if col in df_forecast.columns:
            df_forecast[col] = pd.to_numeric(df_forecast[col], errors="coerce")

    # métrica derivada útil para análises futuras
    if "story_point" in df_forecast.columns and "effort" in df_forecast.columns:
        df_forecast["effort_por_story_point"] = (
            df_forecast["effort"] / df_forecast["story_point"]
        )

    df_forecast.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("\nDataset de forecast gerado:")
    print(OUTPUT_FILE)

    print("\nPrévia:")
    print(df_forecast.head())

    print("\nColunas geradas:")
    print(list(df_forecast.columns))


if __name__ == "__main__":
    main()

