from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_FILE = DATA_DIR / "kanban_dataset.csv"


def load_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError("kanban_dataset.csv não encontrado")

    return pd.read_csv(DATA_FILE)


def filter_by_client(df, client):
    return df[df["cliente"].astype(str).str.lower() == client.lower()].copy()


def calculate_progress(df):
    total = len(df)
    done = len(df[df["status_kanban"] == "Done"])

    if total == 0:
        return 0

    return int((done / total) * 100)


def status_distribution(df):
    expected = ["To Do", "Doing", "Done", "Block"]
    counts = df["status_kanban"].value_counts().to_dict()
    return {status: int(counts.get(status, 0)) for status in expected}


def modules_distribution(df):
    if "modulos" not in df.columns or df.empty:
        return {}

    exploded = df.copy()
    exploded["modulos"] = exploded["modulos"].fillna("Sem módulo informado")
    exploded["modulos"] = exploded["modulos"].astype(str).str.split(r"\s\|\s")
    exploded = exploded.explode("modulos")

    return {
        str(k): int(v)
        for k, v in exploded["modulos"].value_counts().to_dict().items()
    }


def blocked_cards(df):
    return df[df["status_kanban"] == "Block"].copy()


def high_risk_cards(df):
    if "risk" not in df.columns:
        return pd.DataFrame()

    return df[df["risk"].astype(str).str.lower() == "high"].copy()


def overdue_cards(df):
    if "due_date" not in df.columns:
        return pd.DataFrame()

    temp = df.copy()
    temp["due_date"] = pd.to_datetime(temp["due_date"], errors="coerce", utc=True)

    today = pd.Timestamp.now(tz="UTC")

    return temp[
        temp["due_date"].notna()
        & (temp["due_date"] < today)
        & (temp["status_kanban"] != "Done")
    ].copy()


def build_executive_summary(client):
    df = load_data()
    df_client = filter_by_client(df, client)

    return {
        "client": client,
        "total_cards": int(len(df_client)),
        "progress": calculate_progress(df_client),
        "status": status_distribution(df_client),
        "modules": modules_distribution(df_client),
        "blocked": blocked_cards(df_client),
        "high_risk": high_risk_cards(df_client),
        "overdue": overdue_cards(df_client),
    }


if __name__ == "__main__":
    for client in ["4Network", "Consigaz"]:
        summary = build_executive_summary(client)

        print("\n=== RESUMO EXECUTIVO ===")
        print("Cliente:", summary["client"])
        print("Total cards:", summary["total_cards"])
        print("Progresso:", summary["progress"], "%")
        print("Status:", summary["status"])
        print("Módulos:", summary["modules"])
        print("Bloqueados:", len(summary["blocked"]))
        print("Risco alto:", len(summary["high_risk"]))
        print("Atrasados:", len(summary["overdue"]))
