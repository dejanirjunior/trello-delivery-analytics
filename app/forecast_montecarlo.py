from pathlib import Path
import pandas as pd
import random
import json
from statistics import median

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "forecast_dataset.csv"
OUTPUT_FILE = DATA_DIR / "forecast_montecarlo_summary.json"


def run_forecast(df, cliente=None, tipo=None):
    
    if cliente:
        df = df[df["cliente"] == cliente]

    if tipo:
        df = df[df["tipo"] == tipo]

    # resto do código igual


def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * p
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[int(k)]

    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def simulate_cards_until_finish(backlog_cards, historical_cycle_times, iterations=5000):
    """
    Simula quantos dias são necessários para concluir um backlog de cards,
    sorteando tempos históricos por card.
    """
    results = []

    if not backlog_cards or not historical_cycle_times:
        return results

    for _ in range(iterations):
        total_days = 0
        for _card in backlog_cards:
            sampled_time = random.choice(historical_cycle_times)
            total_days += sampled_time
        results.append(round(total_days, 2))

    return results


def simulate_story_points_until_finish(total_story_points, historical_story_point_rates, iterations=5000):
    """
    Simula quantos dias são necessários para concluir um backlog medido em Story Points.
    historical_story_point_rates = quantos story points são entregues por card/dia, conforme histórico.
    """
    results = []

    if total_story_points <= 0 or not historical_story_point_rates:
        return results

    for _ in range(iterations):
        remaining = total_story_points
        total_days = 0

        while remaining > 0:
            sampled_rate = random.choice(historical_story_point_rates)
            if sampled_rate <= 0:
                sampled_rate = 0.1
            remaining -= sampled_rate
            total_days += 1

        results.append(round(total_days, 2))

    return results


def simulate_effort_until_finish(total_effort, historical_effort_rates, iterations=5000):
    """
    Simula quantos dias são necessários para concluir um backlog medido em effort.
    historical_effort_rates = effort entregue por card/dia, conforme histórico.
    """
    results = []

    if total_effort <= 0 or not historical_effort_rates:
        return results

    for _ in range(iterations):
        remaining = total_effort
        total_days = 0

        while remaining > 0:
            sampled_rate = random.choice(historical_effort_rates)
            if sampled_rate <= 0:
                sampled_rate = 0.1
            remaining -= sampled_rate
            total_days += 1

        results.append(round(total_days, 2))

    return results


def simulate_extra_scope(total_sp, total_effort, extra_cards, sp_medio, effort_medio):
    
    total_sp += extra_cards * sp_medio
    total_effort += extra_cards * effort_medio

    return total_sp, total_effort


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
        "median": round(median(sim_results), 2),
        "p50": round(percentile(sim_results, 0.50), 2),
        "p70": round(percentile(sim_results, 0.70), 2),
        "p85": round(percentile(sim_results, 0.85), 2),
        "p95": round(percentile(sim_results, 0.95), 2),
    }


def main():
    if not INPUT_FILE.exists():
        print("Arquivo forecast_dataset.csv não encontrado")
        return

    df = pd.read_csv(INPUT_FILE)

    # Histórico concluído
    df_done = df[df["completion_type"].isin(["internal_done", "client_done"])].copy()

    # Backlog aberto
    df_open = df[df["completion_type"] == "open"].copy()

    # Base histórica para cycle time
    historical_cycle_times = (
        pd.to_numeric(df_done["cycle_time_days"], errors="coerce")
        .dropna()
        .tolist()
    )

    # Base histórica para story point rate
    story_rates = []
    for _, row in df_done.iterrows():
        sp = pd.to_numeric(pd.Series([row.get("story_point")]), errors="coerce").iloc[0]
        cycle = pd.to_numeric(pd.Series([row.get("cycle_time_days")]), errors="coerce").iloc[0]
        if pd.notna(sp) and pd.notna(cycle) and cycle > 0 and sp > 0:
            story_rates.append(round(sp / cycle, 4))

    # Base histórica para effort rate
    effort_rates = []
    for _, row in df_done.iterrows():
        eff = pd.to_numeric(pd.Series([row.get("effort")]), errors="coerce").iloc[0]
        cycle = pd.to_numeric(pd.Series([row.get("cycle_time_days")]), errors="coerce").iloc[0]
        if pd.notna(eff) and pd.notna(cycle) and cycle > 0 and eff > 0:
            effort_rates.append(round(eff / cycle, 4))

    backlog_cards = df_open["card_id"].dropna().tolist()
    total_story_points = pd.to_numeric(df_open["story_point"], errors="coerce").fillna(0).sum()
    total_effort = pd.to_numeric(df_open["effort"], errors="coerce").fillna(0).sum()

    sim_by_cards = simulate_cards_until_finish(backlog_cards, historical_cycle_times)
    sim_by_story_points = simulate_story_points_until_finish(total_story_points, story_rates)
    sim_by_effort = simulate_effort_until_finish(total_effort, effort_rates)

    result = {
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

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\nResumo Monte Carlo gerado:")
    print(OUTPUT_FILE)

    print("\nBacklog considerado:")
    print(result["backlog_snapshot"])

    print("\nForecast por cards:")
    print(result["forecast_by_cards"])

    print("\nForecast por story points:")
    print(result["forecast_by_story_points"])

    print("\nForecast por effort:")
    print(result["forecast_by_effort"])


if __name__ == "__main__":
    main()


