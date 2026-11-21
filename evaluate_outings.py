"""Compare a prediction recorded before departure with observed outing duration."""
import argparse
import csv
import math
from pathlib import Path
import statistics


def evaluate(path):
    errors = []
    seen = set()
    skipped = 0
    with path.open(newline="") as handle:
        rows = csv.DictReader(handle)
        fields = {"outing_id", "predicted_minutes", "actual_minutes", "followed_planned_order"}
        if not fields.issubset(rows.fieldnames or []):
            raise ValueError("Use the column headings in evidence/real_outings_template.csv.")
        for line, row in enumerate(rows, 2):
            name = (row["outing_id"] or "").strip()
            followed = (row["followed_planned_order"] or "").strip().lower()
            if not name or name in seen or followed not in {"yes", "no"}:
                raise ValueError(f"Row {line} needs a unique outing ID and yes or no for planned order.")
            seen.add(name)
            try:
                predicted, actual = (float(row[col]) for col in ("predicted_minutes", "actual_minutes"))
            except (TypeError, ValueError):
                raise ValueError(f"Row {line} needs a prediction and an observed duration.") from None
            if not all(math.isfinite(value) and value > 0 for value in (predicted, actual)):
                raise ValueError(f"Row {line} needs positive, finite durations.")
            if followed == "yes":
                errors.append(predicted - actual)
            else:
                skipped += 1
    return errors, skipped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    try:
        errors, skipped = evaluate(args.csv)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"{len(errors)} comparable outings. {skipped} followed a different order.")
    if errors:
        absolute = [abs(error) for error in errors]
        print(f"Mean absolute error: {statistics.fmean(absolute):.1f} min")
        print(f"Median absolute error: {statistics.median(absolute):.1f} min")
        print(f"Mean bias (predicted minus actual): {statistics.fmean(errors):+.1f} min")
    else:
        print("No comparable observations available.")
