"""Streamlit Community Cloud entry point for the ErrandLab route planner."""
import csv
from datetime import time
import json
from pathlib import Path

import streamlit as st

from routing import POLICIES, PRESETS, TRAFFIC, Plan, Stop, analyze, preset

ROOT = Path(__file__).resolve().parent


def as_time(minutes):
    return time(minutes // 60, minutes % 60)


def minutes(value):
    return 60 * value.hour + value.minute


def report(plan, results):
    policies = results["policies"]
    robust = policies["robust"]
    full, duration, worst = st.columns(3)
    full.metric("Full success", f'{robust["all_on_time"]:.1%}')
    duration.metric("Median outing", f'{robust["median_elapsed"]:.1f} min')
    worst.metric("90th percentile", f'{robust["p90_elapsed"]:.1f} min')
    rows = []
    for key, label in POLICIES.items():
        result = policies[key]
        rows.append({
            "Strategy": label,
            "Stop order": " → ".join(plan.stops[i].name for i in result["order"]),
            "Full success": f'{result["all_on_time"]:.1%}',
            "Median outing": f'{result["median_elapsed"]:.1f} min',
        })
    st.table(rows)
    st.caption(f'{results["test_days"]} matched simulated traffic draws per strategy.')
    st.download_button("Download results JSON", json.dumps(results, indent=2),
                       "errandlab-results.json", "application/json")


def planner():
    labels = {name: text[0] for name, text in PRESETS.items()}
    key = st.selectbox("Starting itinerary", tuple(labels), format_func=labels.get)
    base = preset(key)
    count = st.number_input("Number of stops", 2, 6, len(base.stops), 1, key=f"{key}-count")
    with st.form(f"planner-{key}-{count}"):
        title = st.text_input("Outing name", base.title, max_chars=60)
        left, right = st.columns(2)
        start = minutes(left.time_input("Departure", as_time(base.start)))
        deadline = minutes(right.time_input("Return by", as_time(base.deadline)))
        options = tuple(TRAFFIC)
        traffic = st.selectbox("Traffic", options, index=options.index(base.traffic))
        st.caption("Use approximate east and north offsets from home in kilometres. Negative values mean west and south.")
        stops = []
        for i in range(count):
            stop = base.stops[i] if i < len(base.stops) else Stop(f"Stop {i + 1}", 0, 0, 0, 180, 10)
            with st.expander(f"Stop {i + 1} · {stop.name}"):
                name = st.text_input("Stop name", stop.name, max_chars=42, key=f"{key}-{i}-name")
                x_col, y_col = st.columns(2)
                x = x_col.number_input("East offset (km)", -20.0, 20.0, float(stop.x), 0.1, key=f"{key}-{i}-x")
                y = y_col.number_input("North offset (km)", -20.0, 20.0, float(stop.y), 0.1, key=f"{key}-{i}-y")
                open_col, close_col = st.columns(2)
                opens = minutes(open_col.time_input("Opens", as_time(base.start + stop.opens), key=f"{key}-{i}-opens"))
                closes = minutes(close_col.time_input("Closes", as_time(base.start + stop.closes), key=f"{key}-{i}-closes"))
                visit = st.number_input("Visit minutes", 1, 90, stop.service, 1, key=f"{key}-{i}-visit")
                high = st.checkbox("High priority", stop.priority == 2, key=f"{key}-{i}-priority")
                stops.append(Stop(name.strip(), x, y, opens - start, closes - start, visit, 2 if high else 1))
        submitted = st.form_submit_button("Compare routes", type="primary")
    if submitted:
        st.session_state.pop("result", None)
        plan = Plan(title.strip(), start, deadline, traffic, tuple(stops))
        try:
            with st.spinner("Comparing route orders…"):
                results = analyze(plan)
        except ValueError as err:
            st.error(str(err))
        else:
            st.session_state.result = (key, count, plan, results)
    result = st.session_state.get("result")
    if result and result[:2] == (key, count):
        report(*result[2:])


def evidence():
    with (ROOT / "evidence" / "sensitivity.csv").open(newline="") as source:
        rows = list(csv.DictReader(source))
    default = [row for row in rows if row["spread"] == "1.0" and row["tail_weight"] == "0.35"]
    st.subheader("300 simulated outings")
    st.table([{
        "Comparator": row["comparator"].replace("_", " ").title(),
        "Wins": row["wins"], "Ties": row["ties"], "Losses": row["losses"],
        "Mean lift (pp)": row["mean_lift_pp"],
    } for row in default])
    with (ROOT / "evidence" / "nhts_outings.csv").open(newline="") as source:
        outings = list(csv.DictReader(source))
    st.subheader("20 observed errand outings")
    st.caption("Comparison of travel diaries with a distance-based timing baseline. See the README for assumptions.")
    st.table(outings)
    st.download_button("Download observed outing comparison",
                       (ROOT / "evidence" / "nhts_outings.csv").read_bytes(), "nhts_outings.csv", "text/csv")


def main():
    st.set_page_config(page_title="ErrandLab", layout="wide")
    st.title("ErrandLab")
    if not st.session_state.get("demo_active"):
        st.write("Plan around closing times, traffic and a deadline to get home.")
        if st.button("Demo quick sign-in", type="primary"):
            st.session_state.demo_active = True
            st.rerun()
        return
    section = st.sidebar.radio("Workspace", ("Plan a route", "Research evidence", "Route cinema"))
    if st.sidebar.button("End demo"):
        st.session_state.pop("demo_active", None)
        st.session_state.pop("result", None)
        st.rerun()
    if section == "Plan a route":
        planner()
    elif section == "Research evidence":
        evidence()
    else:
        st.subheader("West 112th Street")
        st.video(str(ROOT / "media" / "sample-route.mp4"))


if __name__ == "__main__":
    main()
