"""Reproducible, small-instance routing with time windows and uncertain travel."""
from dataclasses import dataclass
from itertools import permutations
from functools import lru_cache
import math
import random
import statistics

RESEARCH = (
    "When errand closing times are tight, does delay-aware routing improve the chance "
    "of completing every stop and getting home on time compared with nearest-stop routing "
    "and an optimizer that assumes fixed travel times?"
)
POLICIES = {
    "robust": "Delay-aware", "nominal": "Fixed-time optimizer",
    "nearest": "Nearest stop", "listed": "Entered order",
}
TRAIN_DAYS = 48
TEST_DAYS = 600
TRAIN_SEED = 7427
TEST_SEED = 86741
MINUTES_PER_KM = 6
TRAFFIC = {"Low": (0.08, 0.06), "Moderate": (0.19, 0.13), "High": (0.34, 0.21)}
DISTANCE = "Straight-line model with a fixed detour factor. Use approximate offsets from home in kilometres."


@dataclass(frozen=True)
class Stop:
    name: str
    x: float
    y: float
    opens: int
    closes: int
    service: int
    priority: int = 1


@dataclass(frozen=True)
class Plan:
    title: str
    start: int
    deadline: int
    traffic: str
    stops: tuple[Stop, ...]


@dataclass(frozen=True)
class Visit:
    index: int
    arrival: float
    end: float
    wait: float
    completed: bool


@dataclass(frozen=True)
class Outcome:
    points: int
    completed: int
    elapsed: float
    driving: float
    on_time: bool
    visits: tuple[Visit, ...]


def preset(key):
    always = (0, 180)
    cases = {
        "closing": Plan("Closing time", 16*60, 16*60+108, "High", (
            Stop("Grocery", 0.65, 0.3, *always, 12),
            Stop("Parcel counter", 2.1, 0.7, 0, 36, 8, 2),
            Stop("Library returns", 1.4, 1.8, 0, 39, 7, 2),
            Stop("Tailor pickup", -0.65, 1.2, 30, 79, 8),
        )),
        "opening": Plan("Staggered openings", 10*60, 10*60+112, "Moderate", (
            Stop("Print shop", 1.1, 0.4, 24, 67, 9),
            Stop("Market", -1.25, 0.1, 0, 47, 14, 2),
            Stop("Repair desk", -0.65, 1.5, 17, 73, 9, 2),
            Stop("Bookshop", 1.65, 0.9, 45, 98, 8),
        )),
        "spread": Plan("Spread-out stops", 13*60, 13*60+158, "High", (
            Stop("Supermarket", 2.2, 0.1, *always, 17),
            Stop("Recycling point", -2.1, 0.2, 0, 77, 9),
            Stop("Pick-up locker", 0.2, 2.5, 18, 105, 6, 2),
            Stop("Service desk", -1, 0.5, 0, 39, 10, 2),
        )),
        "relaxed": Plan("Relaxed Saturday", 9*60, 9*60+210, "Low", (
            Stop("Bakery", 0.35, -0.6, *always, 7),
            Stop("Market", 1.4, 0.5, *always, 14),
            Stop("Library", -0.9, 0.45, *always, 10),
            Stop("Post box", 0, 1.55, *always, 4),
        )),
    }
    return cases[key]


PRESETS = {
    "closing": ("Closing time", "Reach a parcel counter before it shuts, then fit in three other stops."),
    "opening": ("Staggered openings", "Reduce waiting when shops open at different times."),
    "spread": ("Spread-out stops", "Fit four stops across town into a fixed afternoon."),
    "relaxed": ("Relaxed Saturday", "Check whether optimization helps when time is plentiful."),
}


def validate(plan):
    if not 2 <= len(plan.stops) <= 6:
        raise ValueError("Enter between two and six stops.")
    if not 0 <= plan.start < plan.deadline < 1440 or plan.deadline - plan.start > 360:
        raise ValueError("Choose a same-day return deadline up to six hours after departure.")
    if plan.traffic not in TRAFFIC:
        raise ValueError("Choose a traffic setting.")
    for stop in plan.stops:
        if not 1 <= len(stop.name) <= 42:
            raise ValueError("Give each stop a name of 1–42 characters.")
        if not all(math.isfinite(v) and -20 <= v <= 20 for v in (stop.x, stop.y)):
            raise ValueError("Each coordinate must be between −20 and 20 km.")
        if not -1440 <= stop.opens < stop.closes <= 1440 or not 1 <= stop.service <= 90:
            raise ValueError(f"{stop.name} needs a valid opening window and a duration of 1–90 minutes.")
        if stop.priority not in (1, 2):
            raise ValueError("Choose standard or high priority.")


def travel_matrix(plan):
    coords = [(0, 0), *((s.x, s.y) for s in plan.stops)]
    return tuple(tuple(
        round(1.2 * MINUTES_PER_KM * math.dist(a, b), 2) for b in coords
    ) for a in coords)


def traffic_draws(matrix, traffic, n, seed):
    """Mean-one lognormal multipliers, with shared daily and independent leg effects."""
    rng = random.Random(seed)
    day_sigma, leg_sigma = TRAFFIC[traffic]
    size = len(matrix)
    for _ in range(n):
        shared = math.exp(rng.gauss(0, day_sigma) - day_sigma**2/2)
        yield tuple(tuple(
            value * shared * math.exp(rng.gauss(0, leg_sigma) - leg_sigma**2/2)
            for value in matrix[i]
        ) for i in range(size))


def simulate(plan, order, times, *, trace=False):
    """Visit in the given order. Skip expired stops and abandon arrivals too late for service."""
    elapsed = driving = 0.0
    position = points = completed = 0
    visits = []
    limit = plan.deadline - plan.start
    for index in order:
        stop = plan.stops[index]
        # Decisions only use the current clock and published hours.
        if elapsed >= limit or elapsed + stop.service > stop.closes:
            continue
        target = index + 1
        leg = times[position][target]
        arrival = elapsed + leg
        driving += leg
        position = target
        begin = max(arrival, stop.opens)
        finish = begin + stop.service
        done = finish <= min(stop.closes, limit)
        wait = begin - arrival if done else 0.0
        elapsed = finish if done else arrival
        if done:
            points += stop.priority
            completed += 1
        if trace:
            visits.append(Visit(index, arrival, elapsed, wait, done))
    leg = times[position][0]
    elapsed += leg
    return Outcome(points, completed, elapsed, driving + leg, elapsed <= limit, tuple(visits))


def nearest_order(matrix):
    remaining = set(range(len(matrix) - 1))
    order = []
    position = 0
    while remaining:
        index = min(remaining, key=lambda i: (matrix[position][i + 1], i))
        order.append(index)
        remaining.remove(index)
        position = index + 1
    return tuple(order)


def success(outcome, count):
    return outcome.on_time and outcome.completed == count


def choose_orders(plan, matrix):
    train = tuple(traffic_draws(matrix, plan.traffic, TRAIN_DAYS, TRAIN_SEED))
    n = len(plan.stops)
    best_robust = best_nominal = None
    robust_order = nominal_order = ()
    for order in permutations(range(n)):
        result = simulate(plan, order, matrix)
        score_nominal = (result.points - 2 * (not result.on_time), -result.elapsed)
        if best_nominal is None or score_nominal > best_nominal:
            best_nominal, nominal_order = score_nominal, order
        outcomes = [simulate(plan, order, day) for day in train]
        utility = sorted(out.points - 2 * (not out.on_time) for out in outcomes)
        tail = utility[: len(utility) // 5]
        score_robust = (
            statistics.fmean(utility) + 0.35 * statistics.fmean(tail),
            sum(success(out, n) for out in outcomes),
            -statistics.fmean(out.elapsed for out in outcomes),
        )
        if best_robust is None or score_robust > best_robust:
            best_robust, robust_order = score_robust, order
    return {
        "robust": robust_order, "nominal": nominal_order,
        "nearest": nearest_order(matrix), "listed": tuple(range(n)),
    }


def paired_interval(differences, seed=3127):
    """Percentile bootstrap over paired simulated days."""
    rng = random.Random(seed)
    trials = sorted(statistics.fmean(rng.choices(differences, k=len(differences))) for _ in range(600))
    return [trials[15], trials[584]]


def evaluate(plan, order, matrix, days):
    outputs = [simulate(plan, order, day) for day in days]
    success_flags = [success(out, len(plan.stops)) for out in outputs]
    elapsed = sorted(out.elapsed for out in outputs)
    nominal = simulate(plan, order, matrix, trace=True)
    real_trace = [{
        "index": v.index, "arrival": v.arrival, "end": v.end,
        "wait": v.wait, "completed": v.completed,
    } for v in nominal.visits]
    seen = {v.index for v in nominal.visits}
    return {
        "order": list(order),
        "all_on_time": statistics.fmean(success_flags),
        "home_on_time": statistics.fmean(out.on_time for out in outputs),
        "mean_completed": statistics.fmean(out.completed for out in outputs),
        "mean_drive": statistics.fmean(out.driving for out in outputs),
        "median_elapsed": statistics.median(elapsed),
        "p90_elapsed": elapsed[math.ceil(0.9 * len(elapsed)) - 1],
        "nominal_trace": real_trace, "skipped": [index for index in order if index not in seen],
        "nominal_elapsed": nominal.elapsed, "nominal_home_on_time": nominal.on_time,
    }, success_flags


@lru_cache(maxsize=64)
def analyze(plan):
    validate(plan)
    matrix = travel_matrix(plan)
    orders = choose_orders(plan, matrix)
    days = tuple(traffic_draws(matrix, plan.traffic, TEST_DAYS, TEST_SEED))
    measures, flags = {}, {}
    for policy, order in orders.items():
        measures[policy], flags[policy] = evaluate(plan, order, matrix, days)
    contrasts = {}
    for policy in ("nearest", "nominal", "listed"):
        diff = [int(a) - int(b) for a, b in zip(flags["robust"], flags[policy])]
        contrasts[policy] = {"lift": statistics.fmean(diff), "interval": paired_interval(diff)}
    return {"policies": measures, "contrasts": contrasts, "test_days": TEST_DAYS,
            "train_days": TRAIN_DAYS, "seed": TEST_SEED, "candidate_orders": math.factorial(len(plan.stops))}
