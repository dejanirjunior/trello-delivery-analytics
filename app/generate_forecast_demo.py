from pathlib import Path
import pandas as pd
import random
import json
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = BASE_DIR / "demo"
DEMO_DIR.mkdir(exist_ok=True)

OUTPUT_DATASET = DEMO_DIR / "forecast_dataset_demo.csv"
OUTPUT_SUMMARY = DEMO_DIR / "forecast_montecarlo_summary_demo.json"

random.seed(42)


CLIENTES = ["4Network", "Consigaz", "Realflex"]
RESPONSAVEIS = ["Priscila", "Ricardo"]
TIPOS = ["FEATURE", "BUG", "DEBITO TECNICO", "GERAL"]

STORY_POINT_OPTIONS = [1, 2, 3, 5, 8, 13]
STORY_POINT_WEIGHTS = [10, 20, 28, 22, 15, 5]


def weighted_story_point():
    return random.choices(STORY_POINT_OPTIONS, weights=STORY_POINT_WEIGHTS, k=1)[0]


def generate_effort_from_story_point(sp: int) -> float:
    base_map = {
        1: (1, 3),
        2: (2, 4),
        3: (3, 6),
        5: (5, 10),
        8: (8, 16),
        13: (14, 26),
    }
    low, high = base_map.get(sp, (2, 6))
    return round(random.uniform(low, high), 1)


def generate_hours_from_effort(effort: float) -> float:
    factor = random.uniform(0.8, 1.35)
    return round(effort * factor, 1)


def generate_cycle_time(sp: int, tipo: str) -> float:
    base = {
        1: (0.5, 1.2),
        2: (0.8, 1.8),
        3: (1.2, 2.8),
        5: (2.0, 4.5),
        8: (3.5, 6.5),
        13: (5.0, 9.5),
    }
    low, high = base.get(sp, (1.0, 3.0))

    if tipo == "BUG":
        high *= 0.9
    elif tipo == "DEBITO TECNICO":
        high *= 1.1
    elif tipo == "FEATURE":
        high *= 1.2

    return round(random.uniform(low, high), 2)


def maybe_none(value, chance=0.0):
    return None if random.random() < chance else value


def build_completed_card(index: int):
    cliente = random.choice(CLIENTES)
    responsavel = random.choice(RESPONSAVEIS)
    tipo = random.choices(TIPOS, weights=[35, 20, 20, 25], k=1)[0]
    sp = weighted_story_point()
    effort = generate_effort_from_story_point(sp)
    executed = generate_hours_from_effort(effort)
    cycle_time = generate_cycle_time(sp, tipo)

    created = datetime(2026, 1, 5) + timedelta(days=random.randint(0, 90))
    start_refinado = created + timedelta(days=random.randint(0, 3))
    start_dev = start_refinado + timedelta(days=random.randint(0, 2))

    internal_done = start_dev + timedelta(days=cycle_time)
    client_done = internal_done + timedelta(days=random.uniform(0.3, 2.5))

    completion_type = random.choices(
        ["internal_done", "client_done"],
        weights=[25, 75],
        k=1
    )[0]

    deploy_prd_date = client_done if completion_type == "client_done" else None
    done_date = internal_done

    return {
        "card_id": f"DEMO-{1000 + index}",
        "card_name": f"Demanda Demo {index}",
        "cliente": cliente,
        "tipo": tipo,
        "assigned_members": responsavel,
        "story_point": sp,
        "effort": effort,
        "total_horas_executado": executed,
        "created_date": created.isoformat(),
        "data_compromisso": (created + timedelta(days=random.randint(5, 18))).isoformat(),
        "due_date": (created + timedelta(days=random.randint(7, 22))).isoformat(),
        "start_refinado": start_refinado.isoformat(),
        "start_dev": start_dev.isoformat(),
        "done_date": done_date.isoformat(),
        "deploy_prd_date": deploy_prd_date.isoformat() if deploy_prd_date else None,
        "lead_time_days": round((done_date - start_refinado).total_seconds() / 86400, 2),
        "cycle_time_days": cycle_time,
        "completion_type": completion_type,
    }


def build_open_card(index: int):
    cliente = random.choice(CLIENTES)
    responsavel = random.choice(RESPONSAVEIS)
    tipo = random.choices(TIPOS, weights=[40, 18, 18, 24], k=1)[0]
    sp = weighted_story_point()
    effort = generate_effort_from_story_point(sp)

    created = datetime(2026, 4, 1) + timedelta(days=random.randint(0, 18))
    start_refinado = maybe_none(created + timedelta(days=random.randint(0, 2)), chance=0.15)
    start_dev = None

    if start_refinado and random.random() > 0.30:
        start_dev = pd.to_datetime(start_refinado) + timedelta(days=random.randint(0, 2))

    return {
        "card_id": f"DEMO-{2000 + index}",
        "card_name": f"Backlog Demo {index}",
        "cliente": cliente,
        "tipo": tipo,
        "assigned_members": responsavel,
        "story_point": sp,
        "effort": effort,
        "total_horas_executado": None,
        "created_date": created.isoformat(),
        "data_compromisso": (created + timedelta(days=random.randint(7, 20))).isoformat(),
        "due_date": (created + timedelta(days=random.randint(10, 25))).isoformat(),
        "start_refinado": start_refinado.isoformat() if start_refinado else None,
        "start_dev": start_dev.isoformat() if start_dev else None,
        "done_date": None,
        "deploy_prd_date": None,
        "lead_time_days": None,
        "cycle_time_days": None,
        "completion_type": "open",
    }


def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * p
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[int(k)]

    return values[f] * (c - k) + values[c] * (k - f)


def simulate_cards_until_finish(backlog_cards, historical_cycle_times, iterations=5000):
    results = []
    if not backlog_cards or not historical_cycle_times:
        return results

    for _ in range(iterations):
        total_days = 0
        for _card in backlog_cards:
            total_days += random.choice(historical_cycle_times)
        results.append(round(total_days, 2))

    return results


def simulate_story_points_until_finish(total_story_points, historical_story_point_rates, iterations=5000):
    results = []
    if total_story_points <= 0 or not historical_story_point_rates:
        return results

    for _ in range(iterations):
        remaining = total_story_points
        total_days = 0
        while remaining > 0:
            sampled_rate = random.choice(historical_story_point_rates)
            sampled_rate = max(sampled_rate, 0.1)
            remaining -= sampled_rate
            total_days += 1
        results.append(round(total_days, 2))

    return results


def simulate_effort_until_finish(total_effort, historical_effort_rates, iterations=5000):
    results = []
    if total_effort <= 0 or not historical_effort_rates:
        return results

    for _ in range(iterations):
        remaining = total_effort
        total_days = 0
        while remaining > 0:
            sampled_rate = random.choice(historical_effort_rates)
            sampled_rate = max(sampled_rate, 0.1)
            remaining -= sampled_rate
            total_days += 1
        results.append(round(total_days, 2))

    return results


def build_summary(sim_results):
    if not sim_results:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "avg": None,
            "median": None,
            "p50": None,
            "p70": None,
            "p85": None,
            "p95": None,
        }

    return {
        "count": len(sim_results),
        "min": round(min(sim_results), 2),
        "max": round(max(sim_results), 2),
        "avg": round(sum(sim_results) / len(sim_results), 2),
        "median": round(pd.Series(sim_results).median(), 2),
        "p50": round(percentile(sim_results, 0.50), 2),
        "p70": round(percentile(sim_results, 0.70), 2),
        "p85": round(percentile(sim_results, 0.85), 2),
        "p95": round(percentile(sim_results, 0.95), 2),
    }


def build_demo_dataset():
    rows = []

    for i in range(1, 91):
        rows.append(build_completed_card(i))

    for i in range(1, 41):
        rows.append(build_open_card(i))

    df = pd.DataFrame(rows)

    numeric_cols = [
        "story_point",
        "effort",
        "total_horas_executado",
        "lead_time_days",
        "cycle_time_days",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["effort_por_story_point"] = df["effort"] / df["story_point"]

    return df


def build_demo_forecast_summary(df: pd.DataFrame):
    df_done = df[df["completion_type"].isin(["internal_done", "client_done"])].copy()
    df_open = df[df["completion_type"] == "open"].copy()

    historical_cycle_times = (
        pd.to_numeric(df_done["cycle_time_days"], errors="coerce")
        .dropna()
        .tolist()
    )

    story_rates = []
    for _, row in df_done.iterrows():
        sp = row.get("story_point")
        cycle = row.get("cycle_time_days")
        if pd.notna(sp) and pd.notna(cycle) and sp > 0 and cycle > 0:
            story_rates.append(round(sp / cycle, 4))

    effort_rates = []
    for _, row in df_done.iterrows():
        effort = row.get("effort")
        cycle = row.get("cycle_time_days")
        if pd.notna(effort) and pd.notna(cycle) and effort > 0 and cycle > 0:
            effort_rates.append(round(effort / cycle, 4))

    backlog_cards = df_open["card_id"].dropna().tolist()
    total_story_points = pd.to_numeric(df_open["story_point"], errors="coerce").fillna(0).sum()
    total_effort = pd.to_numeric(df_open["effort"], errors="coerce").fillna(0).sum()

    sim_by_cards = simulate_cards_until_finish(backlog_cards, historical_cycle_times)
    sim_by_story_points = simulate_story_points_until_finish(total_story_points, story_rates)
    sim_by_effort = simulate_effort_until_finish(total_effort, effort_rates)

    return {
        "backlog_snapshot": {
            "open_cards": len(backlog_cards),
            "total_story_points": round(float(total_story_points), 2),
            "total_effort": round(float(total_effort), 2),
        },
        "historical_base": {
            "completed_cards": int(len(df_done)),
            "cycle_time_samples": len(historical_cycle_times),
            "story_point_rate_samples": len(story_rates),
            "effort_rate_samples": len(effort_rates),
        },
        "forecast_by_cards": build_summary(sim_by_cards),
        "forecast_by_story_points": build_summary(sim_by_story_points),
        "forecast_by_effort": build_summary(sim_by_effort),
        "raw_samples": {
            "cards": sim_by_cards[:300],
            "story_points": sim_by_story_points[:300],
            "effort": sim_by_effort[:300],
        }
    }


def main():
    df = build_demo_dataset()
    df.to_csv(OUTPUT_DATASET, index=False, encoding="utf-8-sig")

    summary = build_demo_forecast_summary(df)
    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\nDataset demo de forecast gerado:")
    print(OUTPUT_DATASET)

    print("\nResumo demo Monte Carlo gerado:")
    print(OUTPUT_SUMMARY)

    print("\nPrévia do dataset demo:")
    print(df.head())

    print("\nResumo do backlog demo:")
    print(summary["backlog_snapshot"])

    print("\nForecast demo por cards:")
    print(summary["forecast_by_cards"])

    print("\nForecast demo por story points:")
    print(summary["forecast_by_story_points"])

    print("\nForecast demo por effort:")
    print(summary["forecast_by_effort"])


if __name__ == "__main__":
    main()

