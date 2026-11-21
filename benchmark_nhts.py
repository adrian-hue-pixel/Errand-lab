"""Compare ErrandLab's distance-based timing with 2022 US NHTS travel diaries."""
import argparse
from collections import defaultdict
import csv
import io
from pathlib import Path
import random
import statistics
from zipfile import ZipFile

from routing import MINUTES_PER_KM

HOME = {1, 2}
ERRAND = {13, 14}
MILES_TO_KM = 1.609344
SERVICE_MINUTES = 12
SEED = 8051
SAMPLE_SIZE = 20


def minutes(value):
    hour, minute = divmod(int(value), 100)
    if not 0 <= hour < 24 or not 0 <= minute < 60:
        raise ValueError("Invalid time")
    return hour * 60 + minute


def summarize_tour(legs):
    stops = len(legs) - 1
    if not 2 <= stops <= 6 or any(int(leg["DRVR_FLG"]) != 1 for leg in legs):
        return None
    try:
        times = [(minutes(leg["STRTTIME"]), minutes(leg["ENDTIME"])) for leg in legs]
        miles = [float(leg["TRPMILES"]) for leg in legs]
    except ValueError:
        return None
    if (any(not 0 < m <= 15 for m in miles)
            or any(end <= start for start, end in times)
            or any(end > next_start for (_, end), (next_start, _) in zip(times, times[1:]))):
        return None
    observed = times[-1][1] - times[0][0]
    if observed > 360:
        return None
    distance = sum(miles) * MILES_TO_KM
    drive = distance * MINUTES_PER_KM
    return {
        "errand_stops": stops, "road_km": round(distance, 3),
        "predicted_drive_minutes": round(drive, 2),
        "observed_drive_minutes": sum(end - start for start, end in times),
        "predicted_total_minutes": round(drive + SERVICE_MINUTES * stops, 2),
        "observed_total_minutes": observed,
    }


def study(archive):
    groups = defaultdict(list)
    with ZipFile(archive) as source, source.open("tripv2pub.csv") as records:
        for row in csv.DictReader(io.TextIOWrapper(records, encoding="utf-8-sig")):
            groups[row["HOUSEID"], row["PERSONID"], row["TDAYDATE"]].append(row)
    by_household = {}
    for (household, _, _), legs in sorted(groups.items()):
        if household in by_household:
            continue
        candidate = []
        for leg in sorted(legs, key=lambda row: int(row["TRIPID"])):
            if int(leg["WHYFROM"]) in HOME:
                candidate = []
                if int(leg["WHYTO"]) in ERRAND:
                    candidate = [leg]
                continue
            if not candidate or int(leg["TRIPID"]) != int(candidate[-1]["TRIPID"]) + 1:
                candidate = []
                continue
            candidate.append(leg)
            if int(leg["WHYTO"]) in HOME:
                result = summarize_tour(candidate)
                if result:
                    by_household[household] = result
                    break
            if int(leg["WHYTO"]) not in ERRAND:
                candidate = []
    selected = random.Random(SEED).sample(list(by_household.values()), SAMPLE_SIZE)
    return len(by_household), [{"outing": i, **row} for i, row in enumerate(selected, 1)]


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("archive", type=Path)
    args = cli.parse_args()
    pool, rows = study(args.archive)
    target = Path(__file__).with_name("evidence") / "nhts_outings.csv"
    with target.open("w", newline="") as dest:
        writer = csv.DictWriter(dest, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{pool} eligible households. Selected {len(rows)} outings.")
    for kind in ("drive", "total"):
        errors = [row[f"predicted_{kind}_minutes"] - row[f"observed_{kind}_minutes"] for row in rows]
        print(f"{kind}: MAE {statistics.mean(map(abs, errors)):.2f}, "
              f"median AE {statistics.median(map(abs, errors)):.2f}, bias {statistics.mean(errors):+.2f}")
