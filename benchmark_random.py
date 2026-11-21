"""Simulate a fixed, unfiltered ensemble and publish per-case and aggregate CSVs."""
import csv
from itertools import product
import math
from pathlib import Path
import random
import statistics

import routing

CASE_COUNT = 300
CASE_SEED = 20471
SPREADS = (0.5, 1.0, 1.5)
WEIGHTS = (0.0, routing.TAIL_WEIGHT, 0.7)
BASELINES = ("nearest", "nominal", "listed")


def generate_cases():
    rng = random.Random(CASE_SEED)
    for i in range(1, CASE_COUNT + 1):
        count = rng.randint(2, 5)
        deadline = rng.randint(55, 175)
        stops = []
        for index in range(count):
            distance = rng.uniform(0.25, 3.5)
            angle = rng.uniform(0, math.tau)
            opens = rng.choice((0, 0, rng.randint(5, deadline // 2)))
            closes = opens + rng.randint(20, deadline + 15)
            stops.append(routing.Stop(
                f"Stop {index + 1}", round(distance * math.cos(angle), 3),
                round(distance * math.sin(angle), 3), opens, closes,
                rng.randint(4, 18), rng.choice((1, 1, 2)),
            ))
        yield routing.Plan(f"Case {i:03}", 600, 600 + deadline, rng.choice(tuple(routing.TRAFFIC)), tuple(stops))


def run():
    for index, plan in enumerate(generate_cases(), start=1):
        routing.validate(plan)
        matrix = routing.travel_matrix(plan)
        for spread in SPREADS:
            settings = routing.choose_weighted_orders(plan, matrix, WEIGHTS, spread=spread,
                                                     seed=routing.TRAIN_SEED + index)
            days = tuple(routing.traffic_draws(matrix, plan.traffic, routing.TEST_DAYS,
                                              routing.TEST_SEED + index, spread=spread))
            counts = {}
            for weight, orders in settings.items():
                for order in orders.values():
                    if order not in counts:
                        counts[order] = sum(routing.success(routing.simulate(plan, order, day),
                                                           len(plan.stops)) for day in days)
                yield {
                    "case": index, "stops": len(plan.stops), "traffic": plan.traffic,
                    "spread": spread, "tail_weight": weight,
                    **{name: counts[order] for name, order in orders.items()},
                    "held_out_days": len(days),
                }


def summarize(rows):
    for spread, weight in product(SPREADS, WEIGHTS):
        subset = [row for row in rows if (row["spread"], row["tail_weight"]) == (spread, weight)]
        n = len(subset)
        for name in (*BASELINES, "all_baselines"):
            diffs = [row["robust"] - (max(row[b] for b in BASELINES) if name == "all_baselines" else row[name])
                     for row in subset]
            yield {
                "spread": spread, "tail_weight": weight, "comparator": name, "cases": n,
                "wins": sum(d > 0 for d in diffs), "ties": diffs.count(0),
                "losses": sum(d < 0 for d in diffs),
                "clear_wins_5pp": sum(d >= 0.05 * routing.TEST_DAYS for d in diffs),
                "clear_losses_5pp": sum(d <= -0.05 * routing.TEST_DAYS for d in diffs),
                "mean_lift_pp": round(100 * statistics.fmean(diffs) / routing.TEST_DAYS, 3),
            }


def write(path, rows):
    rows = list(rows)
    with path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    evidence = Path(__file__).resolve().parent / "evidence"
    results = list(run())
    write(evidence / "random_cases.csv", results)
    write(evidence / "sensitivity.csv", summarize(results))
