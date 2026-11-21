"""Atlas presentation for the Streamlit workspace."""
from pathlib import Path

import streamlit as st

from atmosphere import DARK

WELCOME_ART = Path(__file__).with_name("media") / "atlas-welcome.png"

COLORS = ":root{" + ";".join(f"--atlas-{name}:{value}" for name, value in DARK.items()) + "}"
CSS = """
.stApp {
    background-color: var(--atlas-bg);
    background-image: radial-gradient(ellipse at 85% 0%, #327d6240, transparent 48%),
        radial-gradient(ellipse at 0% 90%, #327d6225, transparent 50%),
        linear-gradient(#83998e0d 1px, transparent 1px),
        linear-gradient(90deg, #83998e0d 1px, transparent 1px);
    background-size: auto, auto, 48px 48px, 48px 48px;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1224px; padding-top: clamp(4rem, 8vh, 7rem); }
[data-testid="stSidebar"] {
    background: var(--atlas-deep); border-right: 1px solid #70888055;
}
.stApp :is(h1,h2,h3) { letter-spacing: -.045em; }
.atlas-brand {
    display: flex; align-items: center; gap: .7rem; font-size: 1.3rem;
    font-weight: 750; letter-spacing: -.05em; color: var(--atlas-ink);
}
.atlas-mark {
    display: grid; place-items: center; width: 38px; height: 38px; border-radius: .75rem;
    background: var(--atlas-primary); color: var(--atlas-onprimary); font-size: 1.2rem;
}
.atlas-eyebrow {
    color: var(--atlas-accent); font: 650 .73rem/1.5 monospace;
    letter-spacing: .17em; text-transform: uppercase; margin: 0 0 .8rem;
}
.atlas-entry h1 {
    margin: 0; padding: 0; font-size: clamp(3.45rem, 8vw, 6.85rem);
    line-height: .94; letter-spacing: -.075em; color: var(--atlas-ink);
}
.atlas-entry h1 em { color: var(--atlas-accent); font-style: normal; }
.atlas-entry > p:last-child, .atlas-heading > p:last-child {
    max-width: 47ch; color: var(--atlas-tone); margin: 1rem 0 0;
    font-size: 1.06rem; line-height: 1.62;
}
.st-key-atlas-sign-in, .st-key-atlas-setup, [data-testid="stForm"], [data-testid="stMetric"] {
    border: 1px solid #70888070; border-radius: 18px; padding: 1.4rem;
    background: var(--atlas-glass); box-shadow: 0 20px 52px -36px #041210bf;
}
.st-key-atlas-sign-in { margin-top: clamp(0px, 10vh, 100px); padding: clamp(1.5rem, 4vw, 3rem); }
.st-key-atlas-sign-in h2 { padding-top: 0; }
.atlas-heading { margin-bottom: 1.3rem; }
.atlas-heading h1 { margin: 0; padding: 0; font-size: clamp(2.7rem, 6vw, 5rem); line-height: 1; }
[data-testid="stMetricLabel"] { color: var(--atlas-tone); }
[data-testid="stMetricValue"] { color: var(--atlas-accent); font-weight: 710; }
[data-testid="stExpander"] details { border-radius: 12px; background: var(--atlas-control); }
:where([data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"]) {
    border-radius: 12px;
}
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primary"]:focus-visible {
    background-color: var(--atlas-primary);
    color: var(--atlas-onprimary);
    border-color: var(--atlas-primary);
    font-weight: 700;
}
.stApp :is(button,input,summary,[role="combobox"]):focus-visible {
    outline: 2px solid var(--atlas-accent); outline-offset: 3px;
}
[data-testid="stVideo"] { border-radius: 18px; overflow: hidden; }
@media (prefers-reduced-motion: no-preference) {
    .st-key-atlas-art { animation: atlas-appear .5s ease-out both; }
    @keyframes atlas-appear { from { opacity: 0; transform: translateY(6px); } }
}
@media (max-width: 760px) {
    [data-testid="stMainBlockContainer"] { padding-top: 3.5rem; }
    .st-key-atlas-sign-in { margin-top: 0; }
}
"""


def apply_theme():
    st.html(f"<style>{COLORS}{CSS}</style>")


def wordmark():
    st.html('<div class="atlas-brand"><span class="atlas-mark" aria-hidden="true">↗</span>ErrandLab</div>')

def entry_art():
    wordmark()
    st.html("""<section class="atlas-entry">
        <p class="atlas-eyebrow">Everyday route atlas</p>
        <h1>One outing.<br><em>Every stop.</em></h1>
        <p>Plan around closing times, traffic and a deadline to get home.</p>
    </section>""")
    with st.container(key="atlas-art"):
        st.image(str(WELCOME_ART), width=510)

def heading(section):
    eyebrow, title, description = {
        "Plan a route": ("Route workspace", "Build your outing", "Choose your stops and compare which route gets you home on time."),
        "Research evidence": ("Research", "What the numbers say", "Explore the route comparisons and observed outing times."),
        "Route cinema": ("Route studio", "West 112th Street", "Follow the Transit from the tunnel to Capi’s corner."),
    }[section]
    st.html(f'<header class="atlas-heading"><p class="atlas-eyebrow">{eyebrow}</p>'
            f'<h1>{title}</h1><p>{description}</p></header>')
