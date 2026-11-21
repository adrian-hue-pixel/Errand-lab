"""Presentation for the original ErrandLab interface on Streamlit."""
from pathlib import Path

import streamlit as st

from layout import styles
from routing import PRESETS, RESEARCH, analyze, preset

ROOT = Path(__file__).resolve().parent
FILM = ROOT / "media" / "sample-route.mp4"
THEME = (ROOT / "style.css").read_text(encoding="utf-8") + styles()
SECTIONS = ("Overview", "Plan a route", "Evidence", "Route cinema")

CSS = """
.stApp {
    background: var(--bg);
    color: var(--ink);
    font-family: Inter, Geist, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stHeader"] { background: var(--paper); }
[data-testid="stMainBlockContainer"] {
    max-width: 1248px;
    padding: 4rem clamp(1rem, 4vw, 2rem) 4rem;
}
.stApp h1, .stApp h2, .stApp h3 { color: var(--ink); }
.stApp em { font-style: normal; }
.st-key-errand-masthead {
    border-bottom: 1px solid var(--line);
    padding: 0 0 1rem;
}
.st-key-errand-masthead [data-testid="stRadio"] [role="radiogroup"] {
    background: #eaeae4;
    border-radius: 16px;
    padding: 4px 6px;
    gap: .25rem;
}
.st-key-errand-masthead [data-testid="stRadio"] label {
    border-radius: 12px; padding: .5rem .75rem;
}
.st-key-errand-masthead [data-testid="stRadio"] label:has(input:checked) {
    background: var(--paper); box-shadow: var(--shadow);
}
.atlas-mark {
    display: inline-grid; place-items: center; width: 32px; height: 32px;
    border-radius: 10px; background: var(--ink); color: white; margin-right: 8px;
}
.st-key-old-hero .hero { padding-bottom: 0; }
.st-key-old-hero .hero h1 { padding-top: 0; }
.st-key-old-hero .hero .lede { color: var(--tone); }
.st-key-old-hero [data-testid="stHorizontalBlock"] { max-width: 420px; margin: auto; }
.st-key-old-hero { margin-bottom: clamp(48px, 7vw, 96px); }
.st-key-old-showcase {
    padding: clamp(24px,4vw,48px); border-radius: 32px; background: #292a25;
}
.st-key-old-showcase h2 { color: #f9f7ef; font-size: clamp(32px,5vw,64px); }
.st-key-old-showcase p { color: #d6d6c9; }
.st-key-old-showcase .eyebrow { color: #f1ae86; }
.st-key-old-showcase [data-testid="stVideo"], [data-testid="stVideo"] video {
    border-radius: 16px; overflow: hidden;
}
.st-key-old-presets [data-testid="stColumn"] { align-self: stretch; }
.st-key-old-presets .case { height: 100%; }
.st-key-old-presets .case h3 { margin-top: 0; }
.st-key-old-presets .caseicon { font-weight: 750; }
.st-key-atlas-setup, [data-testid="stForm"], [data-testid="stMetric"] {
    background: var(--paper); border: 1px solid var(--line);
    border-radius: 24px; padding: clamp(1rem, 3vw, 2rem); box-shadow: var(--shadow);
}
[data-testid="stMetricValue"] { letter-spacing: -.06em; font-weight: 735; }
[data-testid="stExpander"] details { border-radius: 16px; background: #f4f3ee; }
[data-testid="stBaseButton-primary"] {
    border-radius: 12px; background: var(--ink); color: white; border-color: var(--ink);
}
[data-testid="stBaseButton-primary"]:is(:hover,:focus-visible) {
    background: #3a322a; color: white;
}
[data-testid="stBaseButton-secondary"] {
    border-radius: 12px; background: var(--paper); color: var(--ink);
    border: 1px solid var(--line); box-shadow: var(--shadow);
}
.stApp :is(button,input,summary,[role="combobox"]):focus-visible {
    outline: 3px solid var(--accent); outline-offset: 2px;
}
@media (prefers-reduced-motion: no-preference) {
    .st-key-old-showcase, .st-key-atlas-setup, [data-testid="stMetric"] {
        animation: enter .62s var(--spring) both;
    }
    .stApp [data-testid="stButton"] button {
        transition: transform .4s var(--spring), box-shadow .2s, background .2s;
    }
    .stApp [data-testid="stButton"] button:active { transform: scale(.97); }
}
@media (max-width: 680px) {
    .st-key-errand-masthead [data-testid="stRadio"] [role="radiogroup"] { flex-wrap: wrap; }
    .st-key-old-hero .hero { padding-top: 44px; }
    .st-key-old-hero [data-testid="stHorizontalBlock"] { max-width: 100%; }
}
"""


def apply_theme():
    st.html(f"<style>{THEME}{CSS}</style>")


def wordmark():
    st.html('<div class="brand"><span class="atlas-mark" aria-hidden="true">↗</span>ErrandLab</div>')


def go(section):
    st.session_state.demo_active = True
    st.session_state.errand_section = section


def masthead():
    with st.container(key="errand-masthead"):
        brand, menu, account = st.columns((2, 6, 2), vertical_alignment="center")
        with brand:
            wordmark()
        with menu:
            if st.session_state.get("demo_active"):
                section = st.radio("Main navigation", SECTIONS, horizontal=True,
                                   key="errand_section", label_visibility="collapsed")
            else:
                section = "Overview"
        with account:
            if st.session_state.get("demo_active"):
                if st.button("Sign out"):
                    st.session_state.clear()
                    st.rerun()
            else:
                st.button("Sign in ↗", on_click=go, args=("Plan a route",),
                          help="Open an isolated demo workspace")
    return section


def overview():
    with st.container(key="old-hero"):
        st.html("""<section class="hero"><div class="hero-copy">
            <h1>Make the stops.<br><em>Beat the clock.</em></h1>
            <p class="lede">Find the best order for your errands, even when traffic changes and shops are about to close.</p>
        </div></section>""")
        start, evidence = st.columns((1, 1))
        start.button("Plan a route →", type="primary", width="stretch", on_click=go, args=("Plan a route",))
        evidence.button("See the benchmark", width="stretch", on_click=go, args=("Evidence",))
    with st.container(key="old-showcase"):
        copy, video = st.columns((.66, 1.4), gap="large", vertical_alignment="center")
        with copy:
            st.html("""<div class="showcase-copy">
                <p class="eyebrow">Sample route</p><h2>Closing time</h2>
                <p>Reach the parcel counter before it closes, then work your way home.</p>
                <p>Watch the route film with Capi in West 112th Street.</p>
            </div>""")
        with video:
            st.video(str(FILM))
    stats = analyze(preset("closing"))["policies"]
    st.html(f"""<section class="proof" aria-label="Simulated closing-time results">
        <div><h2>Everything done.<br>Home on time.</h2><p>Share of simulated outings that finished every stop within its window and returned home on time.</p></div>
        <div><strong>{stats["robust"]["all_on_time"]:.1%}</strong><span>Delay-aware route</span></div>
        <div><strong>{stats["nearest"]["all_on_time"]:.1%}</strong><span>Nearest stop first</span></div>
    </section>""")
    with st.container(key="old-presets"):
        st.subheader("Sample outings")
        for offset in (0, 2):
            columns = st.columns(2, gap="large")
            for column, (key, (title, description)) in zip(columns, list(PRESETS.items())[offset:offset + 2]):
                column.html(f'<article class="card case"><span class="caseicon" aria-hidden="true">↗</span>'
                            f'<h3>{title}</h3><p>{description}</p></article>')
                column.button(f"Open {title}", key=f"open-{key}", on_click=open_preset, args=(key,))
    st.html(f'<section class="next card"><div><h2>Which route holds up in traffic?</h2><p>{RESEARCH}</p></div></section>')
    st.button("Read the methodology →", on_click=go, args=("Evidence",))


def open_preset(key):
    st.session_state.errand_preset = key
    go("Plan a route")


def heading(section):
    label, title, description = {
        "Plan a route": ("Route planner", "Build your outing", "Choose an outing or enter your own stops, then compare route orders."),
        "Evidence": ("Research", "Which route holds up in traffic?", "Compare simulated success rates and observed outing times."),
        "Route cinema": ("Sample route", "West 112th Street", "Watch the Transit from the tunnel to Capi’s corner."),
    }[section]
    st.html(f'<header class="pagehead"><p class="eyebrow">{label}</p>'
            f'<h1>{title}</h1><p class="lede">{description}</p></header>')
