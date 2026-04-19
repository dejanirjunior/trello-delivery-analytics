import os
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
BASE_URL = "https://api.trello.com/1"


class TrelloAPIError(Exception):
    pass


def _validate_credentials():
    if not TRELLO_KEY or not TRELLO_TOKEN:
        raise TrelloAPIError("TRELLO_KEY ou TRELLO_TOKEN não encontrados no .env")

    if not TRELLO_BOARD_ID:
        raise TrelloAPIError("TRELLO_BOARD_ID não encontrado no .env")


def _get(endpoint, params=None):
    _validate_credentials()

    url = f"{BASE_URL}{endpoint}"
    default_params = {
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
    }

    if params:
        default_params.update(params)

    response = requests.get(url, params=default_params, timeout=30)

    if not response.ok:
        raise TrelloAPIError(
            f"Erro HTTP {response.status_code} ao consultar {url}\nResposta: {response.text}"
        )

    try:
        return response.json()
    except Exception as exc:
        raise TrelloAPIError(
            f"A resposta não veio em JSON válido.\nURL: {response.url}\nResposta: {response.text[:500]}"
        ) from exc


def get_actions(board_id, limit=1000):
    return _get(
        f"/boards/{board_id}/actions",
        params={
            "filter": "updateCard:idList",
            "limit": limit,
        },
    )


def main():
    board_id = TRELLO_BOARD_ID

    print(f"Usando board ID: {board_id}")
    print("Buscando movimentações de listas...")

    actions = get_actions(board_id)

    rows = []

    for action in actions:
        data = action.get("data", {})

        if "listAfter" in data and "listBefore" in data:
            rows.append({
                "action_id": action.get("id"),
                "card_id": data.get("card", {}).get("id"),
                "card_name": data.get("card", {}).get("name"),
                "from_list": data.get("listBefore", {}).get("name"),
                "to_list": data.get("listAfter", {}).get("name"),
                "date": action.get("date"),
                "member": action.get("memberCreator", {}).get("fullName"),
                "member_username": action.get("memberCreator", {}).get("username"),
            })

    df = pd.DataFrame(rows)

    output = DATA_DIR / "card_movements.csv"
    df.to_csv(output, index=False, encoding="utf-8-sig")

    print(f"\nMovimentações geradas: {output}")
    print(f"Total de movimentos capturados: {len(df)}")

    if not df.empty:
        print("\nPrévia:")
        print(df.head())


if __name__ == "__main__":
    main()


