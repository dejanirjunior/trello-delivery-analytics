import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENTS_FILE = BASE_DIR / "config" / "clients.json"


def load_clients():
    if not CLIENTS_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {CLIENTS_FILE}")

    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    clients = data.get("clients", [])

    normalized = []
    for client in clients:
        name = client.get("name", "").strip()
        slug = client.get("slug", "").strip().lower()

        if not name or not slug:
            continue

        normalized.append({
            "name": name,
            "slug": slug
        })

    return normalized
