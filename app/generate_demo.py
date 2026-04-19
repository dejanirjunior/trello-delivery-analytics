from pathlib import Path
import pandas as pd
import random
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = BASE_DIR / "demo"
DEMO_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = DEMO_DIR / "sample_kanban_dataset.csv"


clientes = ["Coca-Cola", "MSD", "Ambev", "Nestlé"]
status_list = ["To Do", "Doing", "Done"]
tipos = ["FEATURE", "BUG", "DEBITO TECNICO"]
prioridades = ["Alta", "Média", "Baixa"]
riscos = ["Alto", "Médio", "Baixo"]

cards = []

for i in range(40):
    status = random.choice(status_list)

    start_date = datetime.now() - timedelta(days=random.randint(1, 30))

    cards.append({
        "card_id": f"CARD-{1000+i}",
        "titulo": f"Demanda {i+1}",
        "status_kanban": status,
        "cliente": random.choice(clientes),
        "assigned_members": random.choice(["Priscila", "Ricardo"]),
        "member_count": 1,
        "bloqueado": random.choice([True, False, False]),
        "priority": random.choice(prioridades),
        "risk": random.choice(riscos),
        "effort": random.randint(2, 20),
        "total_horas_executado": random.randint(1, 20),
        "data_compromisso": (start_date + timedelta(days=7)).isoformat(),
        "due_date": (start_date + timedelta(days=10)).isoformat(),
        "last_activity": datetime.now().isoformat(),
        "created_date": start_date.isoformat(),
        "tipo": random.choice(tipos)
    })

df = pd.DataFrame(cards)
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"Dataset demo gerado em: {OUTPUT_FILE}")


