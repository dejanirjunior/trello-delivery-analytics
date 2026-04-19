import os
import json
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env", override=True)

TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")
TRELLO_BASE_URL = "https://api.trello.com/1"


class TrelloAPIError(Exception):
    """Erro customizado para problemas na API do Trello."""


def _validate_credentials() -> None:
    if not TRELLO_KEY or not TRELLO_TOKEN:
        raise TrelloAPIError("TRELLO_KEY ou TRELLO_TOKEN não encontrados no .env")

    if not TRELLO_BOARD_ID:
        raise TrelloAPIError("TRELLO_BOARD_ID não encontrado no .env")


def _get(endpoint: str, params: dict | None = None):
    _validate_credentials()

    url = f"{TRELLO_BASE_URL}{endpoint}"
    default_params = {
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
    }

    if params:
        default_params.update(params)

    try:
        response = requests.get(url, params=default_params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        raise TrelloAPIError(
            f"Erro HTTP ao consultar Trello: {response.status_code} - {response.text}"
        ) from exc
    except requests.RequestException as exc:
        raise TrelloAPIError(f"Erro de conexão com a API do Trello: {exc}") from exc


def save_json(data: dict | list, filename: str) -> None:
    output_path = DATA_DIR / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_field_name(name: str) -> str:
    normalized = (
        name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "")
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    return normalized


def get_lists(board_id):
    return _get(f"/boards/{board_id}/lists", params={"fields": "id,name"})


def get_board_custom_fields(board_id):
    return _get(f"/boards/{board_id}/customFields")


def get_cards_from_board(board_id):
    return _get(
        f"/boards/{board_id}/cards",
        params={
            "fields": "id,name,idList,labels,dateLastActivity,due,start,closed,idMembers,date",
            "customFieldItems": "true",
            "members": "true",
            "member_fields": "fullName,username",
        },
    )


def build_list_map(lists_data: list[dict]) -> dict:
    return {item["id"]: item["name"] for item in lists_data}


def build_custom_field_map(custom_fields: list[dict]) -> dict:
    field_map = {}

    for field in custom_fields:
        field_id = field["id"]
        field_map[field_id] = {
            "name": field["name"],
            "normalized_name": normalize_field_name(field["name"]),
            "type": field["type"],
            "options": {
                option["id"]: option["value"].get("text", "")
                for option in field.get("options", [])
            },
        }

    return field_map


def extract_custom_field_value(item: dict, field_meta: dict):
    field_type = field_meta["type"]
    value = item.get("value", {})

    if field_type == "text":
        return value.get("text")

    if field_type == "number":
        raw = value.get("number")
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            return raw

    if field_type == "date":
        return value.get("date")

    if field_type == "checkbox":
        checked = value.get("checked")
        if checked is None:
            return None
        return checked.lower() == "true"

    if field_type == "list":
        option_id = item.get("idValue")
        return field_meta["options"].get(option_id, option_id)

    return value


def process_cards(cards: list[dict], list_map: dict, custom_field_map: dict) -> list[dict]:
    processed = []

    for card in cards:
        labels = [label["name"] for label in card.get("labels", []) if label.get("name")]
        labels_upper = [lbl.upper() for lbl in labels]

        members = card.get("members", [])
        member_names = [m.get("fullName") for m in members if m.get("fullName")]

        row = {
            "card_id": card["id"],
            "card_name": card["name"],
            "lista": list_map.get(card["idList"], "N/A"),
            "labels": ", ".join(labels),
            "last_activity": card.get("dateLastActivity"),
            "created_date": card.get("date"),
            "due_date": card.get("due"),   # prazo nativo do Trello
            "start_date": card.get("start"),
            "closed": card.get("closed"),
            "assigned_members": ", ".join(member_names),
            "member_count": len(member_names),
        }

        row["is_block"] = "BLOCK" in labels_upper
        row["is_bug"] = "BUG" in labels_upper
        row["is_feature"] = "FEATURE" in labels_upper
        row["is_debito_tecnico"] = "DEBITOTECNICO" in labels_upper

        technical_labels = {"BLOCK", "BUG", "FEATURE", "DEBITOTECNICO"}
        business_labels = [lbl for lbl in labels if lbl.upper() not in technical_labels]
        row["cliente_label"] = business_labels[0] if business_labels else None

        for item in card.get("customFieldItems", []):
            field_id = item.get("idCustomField")
            field_meta = custom_field_map.get(field_id)

            if not field_meta:
                continue

            col_name = field_meta["normalized_name"]
            row[col_name] = extract_custom_field_value(item, field_meta)

        processed.append(row)

    return processed


def print_custom_fields_summary(custom_fields: list[dict]) -> None:
    print("\nCustom Fields encontrados no board:")
    if not custom_fields:
        print("- Nenhum custom field encontrado.")
        return

    for field in custom_fields:
        print(f"- {field['name']} ({field['type']})")


def main():
    board_id = TRELLO_BOARD_ID

    if not board_id:
        print("TRELLO_BOARD_ID não encontrado no .env")
        return

    print(f"Usando board ID: {board_id}")

    print("\nBuscando listas...")
    lists_data = get_lists(board_id)
    list_map = build_list_map(lists_data)

    print("Buscando custom fields do board...")
    custom_fields = get_board_custom_fields(board_id)
    custom_field_map = build_custom_field_map(custom_fields)
    print_custom_fields_summary(custom_fields)

    print("\nBuscando cards...")
    cards = get_cards_from_board(board_id)

    processed_cards = process_cards(cards, list_map, custom_field_map)
    df = pd.DataFrame(processed_cards)

    save_json(custom_fields, "custom_fields.json")
    save_json(cards, "cards_raw.json")

    output_csv = DATA_DIR / "cards_enriched.csv"
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("\nArquivos gerados em ./data:")
    print("- custom_fields.json")
    print("- cards_raw.json")
    print("- cards_enriched.csv")

    print("\nPrévia dos dados enriquecidos:")
    print(df.head())

    print("\nColunas geradas:")
    print(list(df.columns))


if __name__ == "__main__":
    main()