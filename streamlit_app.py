"""Streamlit Community Cloud entry point for the ErrandLab route planner."""
import csv
from datetime import time
import json
from statistics import fmean
from pathlib import Path

import streamlit as st

from routing import POLICIES, PRESETS, TRAFFIC, Plan, Stop, analyze, preset
from streamlit_ui import apply_theme, capi_chat, heading, masthead, overview, settings

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
    with st.container(key="atlas-setup"):
        st.markdown("### 1. Choose a starting point")
        scenario_col, count_col = st.columns((2, 1))
        key = scenario_col.selectbox("Starting itinerary", tuple(labels), format_func=labels.get,
                                     key="errand_preset")
        base = preset(key)
        count = count_col.number_input("Number of stops", 2, 6, len(base.stops), 1, key=f"{key}-count")
    with st.form(f"planner-{key}-{count}"):
        schedule, visits = st.columns((1, 1.45), gap="large")
        with schedule:
            st.markdown("### 2. Set your schedule")
            title = st.text_input("Outing name", base.title, max_chars=60)
            left, right = st.columns(2)
            start = minutes(left.time_input("Departure", as_time(base.start)))
            deadline = minutes(right.time_input("Return by", as_time(base.deadline)))
            options = tuple(TRAFFIC)
            traffic = st.selectbox("Traffic", options, index=options.index(base.traffic))
            st.caption("Traffic controls how much travel time can vary in the simulation.")
        with visits:
            st.markdown("### 3. Edit your stops")
            st.caption("Offsets are in kilometres from home. Use negatives for west or south.")
            stops = []
            for i in range(count):
                stop = base.stops[i] if i < len(base.stops) else Stop(f"Stop {i + 1}", 0, 0, 0, 180, 10)
                with st.expander(f"{i + 1:02d} · {stop.name}", expanded=i == 0):
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
    comparisons = {**POLICIES, "all_baselines": "Best baseline per case"}
    with st.container(key="evidence-simulation"):
        st.subheader("300 simulated outings")
        st.caption("Average difference in full success for delay-aware routing, in percentage points. The midpoint represents a tie.")
        bars = []
        maximum = max(abs(float(row["mean_lift_pp"])) for row in default) or 1
        for row in default:
            value = float(row["mean_lift_pp"])
            width = 49 * abs(value) / maximum
            left = 50 - width if value < 0 else 50
            tone = "negative" if value < 0 else "positive"
            label = comparisons[row["comparator"]]
            bars.append(f'<div class="lift-row"><span>{label}</span><span class="lift-track" aria-hidden="true">'
                        f'<span class="lift-bar {tone}" style="width:{width:.2f}%;left:{left:.2f}%"></span></span>'
                        f'<strong>{value:+.2f} pp</strong></div>')
        st.html("".join(bars))
        with st.expander("See wins, ties and losses"):
            st.table([{
                "Comparison": comparisons[row["comparator"]],
                "Wins": row["wins"], "Ties": row["ties"], "Losses": row["losses"],
            } for row in default])
    path = ROOT / "evidence" / "nhts_outings.csv"
    with path.open(newline="") as source:
        outings = list(csv.DictReader(source))
    with st.container(key="evidence-field"):
        st.subheader("20 observed errand outings")
        st.caption("Travel diaries show how far off the timing estimate can be on an individual trip.")
        differences = [float(row["predicted_total_minutes"]) - float(row["observed_total_minutes"]) for row in outings]
        left, right = st.columns(2)
        left.metric("Typical size of error (mean absolute)", f"{fmean(map(abs, differences)):.1f} min")
        right.metric("Average bias (predicted minus observed)", f"{fmean(differences):+.1f} min")
        with st.expander("See the 20 outing records"):
            titles = {"outing":"Outing", "errand_stops":"Stops", "road_km":"Road km",
                      "predicted_drive_minutes":"Estimated drive (min)", "observed_drive_minutes":"Observed drive (min)",
                      "predicted_total_minutes":"Estimated total (min)", "observed_total_minutes":"Observed total (min)"}
            st.dataframe([{titles[field]: float(row[field]) for field in titles} for row in outings], hide_index=True)
        st.download_button("Download observed outing comparison", path.read_bytes(), path.name, "text/csv")


def main():
    st.set_page_config(page_title="ErrandLab", layout="wide")
    apply_theme()
    section = masthead()
    if section == "Overview":
        overview()
        return
    if section == "Capi chat":
        capi_chat()
        return
    heading(section)
    if section == "Plan a route":
        planner()
    elif section == "Evidence":
        evidence()
    else:
        settings()


if __name__ == "__main__":
    main()
