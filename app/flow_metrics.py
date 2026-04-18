from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "card_movements.csv"

OUT_BACKLOG_WEEK = DATA_DIR / "flow_backlog_refinado_weekly.csv"
OUT_BACKLOG_MONTH = DATA_DIR / "flow_backlog_refinado_monthly.csv"
OUT_LEADTIME = DATA_DIR / "lead_time_cards.csv"
OUT_THROUGHPUT = DATA_DIR / "throughput_weekly.csv"


# =========================
# UTIL
# =========================
def load_data():
    if not INPUT_FILE.exists():
        print("Arquivo card_movements.csv não encontrado")
        return None

    df = pd.read_csv(INPUT_FILE)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df


# =========================
# 1. BACKLOG -> REFINADO
# =========================
def backlog_to_refinado(df):
    df_filtered = df[
        (df["from_list"].str.lower() == "backlog") &
        (df["to_list"].str.lower() == "refinado")
    ].copy()

    df_filtered["week"] = df_filtered["date"].dt.to_period("W").astype(str)
    df_filtered["month"] = df_filtered["date"].dt.to_period("M").astype(str)

    weekly = (
        df_filtered.groupby(["member", "week"])
        .size()
        .reset_index(name="cards_puxados")
    )

    monthly = (
        df_filtered.groupby(["member", "month"])
        .size()
        .reset_index(name="cards_puxados")
    )

    weekly.to_csv(OUT_BACKLOG_WEEK, index=False, encoding="utf-8-sig")
    monthly.to_csv(OUT_BACKLOG_MONTH, index=False, encoding="utf-8-sig")

    print("\nBacklog -> Refinado (semanal e mensal) gerados")


# =========================
# 2. LEAD TIME
# =========================
def calculate_lead_time(df):
    cards = []

    for card_id, group in df.groupby("card_id"):
        group = group.sort_values("date")

        start = group[group["to_list"].str.lower() == "refinado"]
        end = group[group["to_list"].isin(["Concluído", "Deploy"])]

        if not start.empty and not end.empty:
            start_date = start.iloc[0]["date"]
            end_date = end.iloc[-1]["date"]

            lead_time_days = (end_date - start_date).total_seconds() / 86400

            cards.append({
                "card_id": card_id,
                "card_name": group.iloc[0]["card_name"],
                "start_refinado": start_date,
                "end_done": end_date,
                "lead_time_days": round(lead_time_days, 2)
            })

    df_lead = pd.DataFrame(cards)
    df_lead.to_csv(OUT_LEADTIME, index=False, encoding="utf-8-sig")

    print("Lead time por card gerado")


# =========================
# 3. THROUGHPUT
# =========================
def calculate_throughput(df):
    df_done = df[
        df["to_list"].isin(["Concluído", "Deploy"])
    ].copy()

    df_done["week"] = df_done["date"].dt.to_period("W").astype(str)

    throughput = (
        df_done.groupby("week")
        .size()
        .reset_index(name="cards_entregues")
    )

    throughput.to_csv(OUT_THROUGHPUT, index=False, encoding="utf-8-sig")

    print("Throughput semanal gerado")


# =========================
# MAIN
# =========================
def main():
    df = load_data()

    if df is None or df.empty:
        return

    backlog_to_refinado(df)
    calculate_lead_time(df)
    calculate_throughput(df)

    print("\nArquivos gerados:")
    print(f"- {OUT_BACKLOG_WEEK}")
    print(f"- {OUT_BACKLOG_MONTH}")
    print(f"- {OUT_LEADTIME}")
    print(f"- {OUT_THROUGHPUT}")


if __name__ == "__main__":
    main()


