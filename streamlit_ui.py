"""Presentation for the original ErrandLab interface on Streamlit."""
from html import escape
from pathlib import Path

import streamlit as st

from capi import PROMPTS, answer, groq_topic, local_topic

from layout import styles
from routing import PRESETS, RESEARCH, analyze, preset

ROOT = Path(__file__).resolve().parent
FILM = ROOT / "media" / "sample-route.mp4"
THEME = (ROOT / "style.css").read_text(encoding="utf-8") + styles()
CAPI_CSS = (ROOT / "capi_mascot.css").read_text(encoding="utf-8")
SECTIONS = ("Overview", "Plan a route", "Evidence", "Capi chat", "Settings")

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
[data-testid="stBaseButton-primary"] p { color: inherit; font-weight: 650; }
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
[data-testid="stMainBlockContainer"] .st-key-overview-capi { text-align: center; }
.st-key-overview-capi .capi-note {
    display: inline-block; padding: .45rem .9rem; background: var(--paper);
    border: 1px solid var(--line); border-radius: 15px; color: var(--tone); font-size: .85rem;
    box-shadow: var(--shadow);
}
.st-key-old-hero:has(.st-key-overview-capi) .hero { padding-top: .25rem; }
.st-key-old-hero:has(.st-key-overview-capi) { padding-top: clamp(32px,5vw,58px); }
.st-key-atlas-setup .stMarkdown h3, [data-testid="stForm"] .stMarkdown h3 { margin: 0; font-size: 1.4rem; }
.st-key-atlas-setup [data-testid="stCaptionContainer"] p,
[data-testid="stForm"] [data-testid="stCaptionContainer"] p { color: var(--tone); }
[data-testid="stForm"] input { background: transparent; border: 0; margin: 0; }
[data-testid="stForm"] [data-baseweb="base-input"], [data-testid="stForm"] [data-baseweb="select"] > div {
    background: #f7f5ef; border-radius: 10px;
}
[data-testid="stForm"] [data-testid="stExpander"] details { background: #f4f1e9; }
.st-key-evidence-simulation, .st-key-evidence-field, .st-key-capi-context,
.st-key-capi-settings, .st-key-capi-transcript {
    padding: clamp(1rem,3vw,1.85rem); background: var(--paper); border: 1px solid var(--line);
    border-radius: 24px; box-shadow: var(--shadow);
}
.st-key-evidence-simulation [data-testid="stMetric"],
.st-key-evidence-field [data-testid="stMetric"],
.st-key-capi-context [data-testid="stMetric"] {
    padding: .8rem; border-radius: 16px; background: #f4f1e9;
}
.st-key-capi-intro {
    padding: clamp(1.2rem,4vw,3rem); border-radius: 28px;
    background: radial-gradient(ellipse at 96% 8%, #edc3aa, transparent 60%), #f8e6dc;
    border: 1px solid #e4c8b4;
}
.st-key-capi-intro .pagehead { padding: 0; }
.st-key-capi-stage {
    text-align: center; padding: 1.25rem 1rem .65rem; border-radius: 24px;
    min-height: 230px; overflow: hidden; border: 1px solid #e4c8b4;
    background: radial-gradient(ellipse at 50% 67%, #f3c4a7 0%, transparent 55%),
        linear-gradient(#fff4e7 73%, #eac5a8 73%, #f3dbbe);
}
.st-key-capi-stage .capi-note {
    display: inline-block; background: var(--paper); padding: .45rem .9rem;
    border: 1px solid #e4c8b4; border-radius: 14px; font-size: .84rem; color: var(--ink);
}
.st-key-capi-stage .mascot-name { display: block; font-weight: 750; color: var(--ink); }
.st-key-capi-transcript [data-testid="stChatMessage"] { border-radius: 16px; background: #f6f4ee; }
.st-key-capi-transcript button p { color: inherit; }
.st-key-capi-context p, .st-key-capi-status p { color: var(--tone); }
.st-key-capi-status { border-left: 3px solid var(--accent); background: #f8ebe1; border-radius: 8px; padding: .6rem 1rem; }
.lift-row { display: grid; grid-template-columns: minmax(105px,1fr) minmax(65px,2.2fr) 68px; align-items:center; gap: 10px; margin: .75rem 0; font-size: .9rem; }
.lift-track { position:relative; height: 14px; border-radius: 8px; background:#eeeae2; }
.lift-track::after { content:""; position:absolute; left:50%; top:0; bottom:0; border-left: 1px solid #aa9f91; }
.lift-bar { position:absolute; top:2px; bottom:2px; border-radius:7px; background: #ac3921; }
.lift-bar.negative { background:#756451; }
.lift-row strong { text-align: right; font-variant-numeric: tabular-nums; }
.stApp:has(.motion-off) *, .stApp:has(.motion-off) *::before, .stApp:has(.motion-off) *::after {
    animation: none !important; transition: none !important;
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
    marker = '<span class="motion-off" hidden></span>' if not st.session_state.get("errand_motion", True) else ""
    st.html(f"<style>{THEME}{CSS}{CAPI_CSS}</style>{marker}")


def mascot(greeting, *, show_name=False):
    name = '<span class="mascot-name">Capi</span>' if show_name else ""
    st.html(f"""
    <div class="capi-avatar">
        <p class="capi-note">{escape(greeting)}</p>
        <span class="capi-figure" role="img" aria-label="Capi, a seated capybara with two front teeth and a rust bandanna">
            <span class="capi-glow"></span><span class="capi-shadow"></span>
            <span class="capi-character">
                <span class="capi-body"></span>
                <span class="capi-paw back"></span><span class="capi-paw front"></span><span class="capi-paw near"></span>
                <span class="capi-scarf"></span>
                <span class="capi-head">
                    <span class="capi-ear left"></span><span class="capi-ear right"></span>
                    <span class="capi-face"></span><span class="capi-shine"></span><span class="capi-cheek"></span>
                    <span class="capi-eyes"><span class="capi-eye left"></span><span class="capi-eye right"></span></span>
                    <span class="capi-muzzle"><span class="capi-nose"></span><span class="capi-smile"></span><span class="capi-teeth"></span></span>
                </span>
            </span>
        </span>
        {name}
    </div>
    """)

def wordmark():
    st.html('<div class="brand"><span class="atlas-mark" aria-hidden="true">↗</span>ErrandLab</div>')


def go(section):
    st.session_state.demo_active = True
    st.session_state.errand_section = section


def navigate():
    if st.session_state.errand_section != "Overview":
        st.session_state.demo_active = True


def masthead():
    with st.container(key="errand-masthead"):
        brand, menu, account = st.columns((2, 6, 2), vertical_alignment="center")
        with brand:
            wordmark()
        with menu:
            section = st.radio("Main navigation", SECTIONS, horizontal=True, key="errand_section",
                               label_visibility="collapsed", on_change=navigate)
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
        if st.session_state.get("errand_mascot", True):
            with st.container(key="overview-capi"):
                mascot("Hi, I’m Capi. Ready to head out?")
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
        "Capi chat": ("Your route companion", "A little help for the road.", "Ask Capi about your route, the benchmark, or how ErrandLab works."),
        "Settings": ("Preferences", "Make ErrandLab yours", "Choose how the app looks and how Capi connects."),
    }[section]
    st.html(f'<header class="pagehead"><p class="eyebrow">{label}</p>'
            f'<h1>{title}</h1><p class="lede">{description}</p></header>')


def settings():
    with st.container(key="capi-settings"):
        st.subheader("Appearance")
        if st.toggle("Show Capi illustrations", value=st.session_state.get("errand_mascot", True)):
            st.session_state.errand_mascot = True
        else:
            st.session_state.errand_mascot = False

        def update_motion():
            st.session_state.errand_motion = st.session_state.motion_setting

        st.toggle("Decorative motion", value=st.session_state.get("errand_motion", True),
                  key="motion_setting", on_change=update_motion)
        st.divider()
        st.subheader("Capi’s Groq connection")
        st.caption("Optional. A saved key is kept for this browser session. If you use Groq, Capi classifies your question with Groq. Your route results stay in ErrandLab.")
        with st.form("groq-key-form", clear_on_submit=True, border=False):
            candidate = st.text_input("Groq API key", type="password", max_chars=200)
            saved = st.form_submit_button("Save key")
        if saved:
            key = candidate.strip()
            if not key.startswith("gsk_") or not key[4:].isalnum():
                st.error("Enter a Groq key starting with gsk_.")
            else:
                st.session_state.errand_groq = key
                st.success("Key saved for this session.")
        if st.session_state.get("errand_groq"):
            if st.button("Remove saved key"):
                st.session_state.pop("errand_groq", None)
                st.rerun()
        st.markdown("[Get a key from Groq](https://console.groq.com/keys)")


def capi_chat():
    from urllib.error import URLError

    key = st.session_state.get("errand_groq")
    result = st.session_state.get("result")
    with st.container(key="capi-intro"):
        heading("Capi chat")
    with st.container(key="capi-status"):
        st.write("Groq key saved · ErrandLab questions only" if key else
                 "Built-in guidance is ready. Add a Groq key in Settings for broader question matching.")
    context, companion = st.columns((1.45, 1), gap="large")
    with context, st.container(key="capi-context"):
        st.subheader("Your outing")
        if result:
            plan, report = result[2:]
            metrics = report["policies"]["robust"]
            st.caption(f"{plan.title} · Delay-aware route")
            a, b, c = st.columns(3)
            a.metric("Stops", len(plan.stops))
            b.metric("Full success", f'{metrics["all_on_time"]:.1%}')
            c.metric("Median", f'{metrics["median_elapsed"]:.1f} min')
        else:
            st.write("Compare an outing to see its stops, success rate, and median time here.")
            st.button("Open the planner", on_click=go, args=("Plan a route",))
    if st.session_state.get("errand_mascot", True):
        with companion, st.container(key="capi-stage"):
            mascot("Ask me what to do next.", show_name=True)
    messages = st.session_state.setdefault("capi_messages", [])
    with st.container(key="capi-transcript"):
        title, clear = st.columns((3, 1))
        title.subheader("Chat with Capi")
        if clear.button("Clear chat"):
            messages.clear()
        choices = st.columns(4)
        selected = next((prompt for slot, prompt in zip(choices, PROMPTS) if slot.button(prompt)), None)
        with st.chat_message("assistant"):
            st.write("Hi, I’m Capi. Ask me about planning an outing or what your results mean.")
        for role, message in messages:
            with st.chat_message(role):
                if role == "user":
                    st.text(message)
                else:
                    st.markdown(message)
        typed = st.chat_input("Ask about ErrandLab", max_chars=450)
        question = selected or typed
        if question:
            question = question.strip()
        if question:
            with st.chat_message("user"):
                st.text(question)
            topic = local_topic(question)
            with st.chat_message("assistant"):
                if key and question not in PROMPTS:
                    try:
                        with st.spinner("Capi is thinking…"):
                            topic = groq_topic(question, key)
                    except (OSError, URLError, ValueError, TypeError, AttributeError, KeyError, IndexError):
                        st.caption("Groq is unavailable. Using built-in ErrandLab guidance.")
                reply = answer(topic, result)
                st.markdown(reply)
            messages.extend((("user", question), ("assistant", reply)))
            del messages[:-20]
