from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "cards_enriched.csv"
OUTPUT_FILE = DATA_DIR / "kanban_dataset.csv"

MODULE_LABELS = {
    "MOD_ORCAMENTO": "Orcamento",
    "MOD_SUPRIMENTOS": "Suprimentos",
    "MOD_CONTRATOS": "Contratos",
    "MOD_FORNECEDOR": "Fornecedor",
    "MOD_COMPRAS": "Compras",
    "MOD_CRM": "CRM",
}


def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_label_key(label):
    return (
        safe_text(label)
        .upper()
        .replace("Ó", "O")
        .replace("Ô", "O")
        .replace("Õ", "O")
        .replace("Á", "A")
        .replace("À", "A")
        .replace("Ã", "A")
        .replace("É", "E")
        .replace("Ê", "E")
        .replace("Í", "I")
        .replace("Ú", "U")
        .replace("Ç", "C")
        .replace(" ", "_")
        .replace("-", "_")
    )


def split_labels(labels):
    text = safe_text(labels)

    if not text:
        return []

    cleaned = (
        text.replace("[", "")
        .replace("]", "")
        .replace('"', "")
        .replace("'", "")
    )

    if "|" in cleaned:
        parts = cleaned.split("|")
    elif ";" in cleaned:
        parts = cleaned.split(";")
    else:
        parts = cleaned.split(",")

    return [p.strip() for p in parts if p.strip()]


def classify_tipo(labels):
    labels_upper = safe_text(labels).upper()

    if not labels_upper:
        return "GERAL"

    if "BUG" in labels_upper:
        return "BUG"
    if "BLOCK" in labels_upper:
        return "BLOCK"
    if "DEBITOTECNICO" in labels_upper or "DEBITO TECNICO" in labels_upper:
        return "DEBITO TECNICO"
    if "FEATURE" in labels_upper:
        return "FEATURE"

    return "GERAL"


def extract_modules(labels):
    modules = []

    for label in split_labels(labels):
        key = normalize_label_key(label)

        if key in MODULE_LABELS:
            modules.append(MODULE_LABELS[key])

    if not modules:
        return "Sem módulo informado"

    return " | ".join(sorted(set(modules)))


def normalize_status(lista, labels):
    labels_upper = safe_text(labels).upper()

    if "BLOCK" in labels_upper:
        return "Block"

    if not isinstance(lista, str):
        return None

    lista = lista.strip().lower()

    mapping = {
        "backlog": "To Do",
        "refinado": "To Do",

        "em dev": "Doing",
        "q.a.": "Doing",
        "qa": "Doing",
        "uat": "Doing",

        "concluído": "Done",
        "concluido": "Done",
        "deploy": "Done",
        "deploy prd": "Done",
    }

    if lista == "painel":
        return None

    return mapping.get(lista, "To Do")


def main():
    if not INPUT_FILE.exists():
        print("Arquivo cards_enriched.csv não encontrado")
        return

    df = pd.read_csv(INPUT_FILE)

    if "labels" not in df.columns:
        df["labels"] = ""

    df["tipo"] = df["labels"].apply(classify_tipo)
    df["modulos"] = df["labels"].apply(extract_modules)
    df["status_kanban"] = df.apply(
        lambda row: normalize_status(row.get("lista"), row.get("labels")),
        axis=1
    )

    df = df[df["status_kanban"].notna()]

    keep_cols = [
        "card_id",
        "card_name",
        "status_kanban",
        "cliente_label",
        "labels",
        "modulos",
        "assigned_members",
        "member_count",
        "is_block",
        "priority",
        "risk",
        "effort",
        "total_horas_executado",
        "data_compromisso",
        "due_date",
        "last_activity",
        "created_date",
        "tipo",
    ]

    existing_cols = [col for col in keep_cols if col in df.columns]
    df_kanban = df[existing_cols].copy()

    df_kanban.rename(
        columns={
            "card_name": "titulo",
            "cliente_label": "cliente",
            "is_block": "bloqueado",
        },
        inplace=True,
    )

    df_kanban.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("\nDataset Kanban gerado:")
    print(OUTPUT_FILE)

    print("\nPrévia:")
    print(df_kanban.head())

    print("\nColunas geradas:")
    print(list(df_kanban.columns))


if __name__ == "__main__":
    main()
