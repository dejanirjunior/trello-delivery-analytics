from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "cards_enriched.csv"
OUTPUT_FILE = DATA_DIR / "kanban_dataset.csv"


def classify_tipo(labels):
    if not isinstance(labels, str) or not labels.strip():
        return "GERAL"

    labels_upper = labels.upper()

    if "BUG" in labels_upper:
        return "BUG"
    if "BLOCK" in labels_upper:
        return "BLOCK"

    return "FEATURE" 


def normalize_status(lista):
    if not isinstance(lista, str):
        return None

    lista = lista.strip().lower()

    mapping = {
        "backlog": "To Do",
        "refinado": "To Do",
        "em dev": "Doing",
        "q.a.": "Doing",
        "qa": "Doing",
        "concluído": "Done",
        "concluido": "Done",
        "deploy": "Done",
    }

    if lista == "painel":
        return None

    return mapping.get(lista, "To Do")



def main():
   if not INPUT_FILE.exists():
       print("Arquivo cards_enriched.csv não encontrado")
       return


   df = pd.read_csv(INPUT_FILE)


   df["tipo"] = df["labels"].apply(classify_tipo)
   df["status_kanban"] = df["lista"].apply(normalize_status)


   df_kanban = df[[
       "card_id",
       "card_name",
       "status_kanban",
       "cliente_label",
       "is_block",
       "priority",
       "risk",
       "effort",
       "data_de_entrega",
       "last_activity",
       "tipo"
   ]].copy()


   df_kanban.rename(columns={
       "card_name": "titulo",
       "cliente_label": "cliente",
       "is_block": "bloqueado"
   }, inplace=True)


   df_kanban.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")


   print("\nDataset Kanban gerado:")
   print(OUTPUT_FILE)


   print("\nPrévia:")
   print(df_kanban.head())




if __name__ == "__main__":
   main()



