"""Responsive layout recipes in eight-pixel units and the app's shared motion settings."""
from artwork import spring_curve


def rule(selector, **properties):
    declarations = ";".join(f"{key.replace('_', '-')}:{value}" for key, value in properties.items())
    return f"{selector}{{{declarations}}}"


def grid(columns, gap=2):
    return {"display": "grid", "grid_template_columns": columns, "gap": f"{gap*8}px"}


def styles():
    desktop = {
        ".showcase": grid("minmax(0,.66fr) minmax(0,1.4fr)", 6),
        ".proof": grid("minmax(0,1.5fr) repeat(2,minmax(0,1fr)) auto", 4),
        ".stoplist": grid("repeat(2,minmax(0,1fr))"),
        ".planner": grid("minmax(0,1fr)", 5),
        ".authgrid": grid("minmax(0,1fr) minmax(0,.85fr)", 8),
        ".routegrid": grid("minmax(0,1.2fr) minmax(0,1fr)", 4),
        ".benchgrid": grid("repeat(2,minmax(0,1fr))", 4),
        ".cards": grid("repeat(2,minmax(0,1fr))", 3),
        ".metrics": grid("repeat(3,minmax(0,1fr))"),
        ".formgrid": grid("2fr repeat(3,minmax(0,1fr))"),
        ".stoprow": grid("repeat(2,minmax(0,1fr))", 2),
        ".auth form": grid("minmax(0,1fr)"),
        ".stoprow label:first-child": {"grid_column": "1/-1"},
    }
    tablet = {
        ".authgrid": grid("repeat(2,minmax(0,1fr))", 3),
        ".showcase": grid("minmax(0,.85fr) minmax(0,1.2fr)", 3),
        ".proof": grid("repeat(2,minmax(0,1fr))", 3),
        ".proof>div:first-child": {"grid_column": "1/-1"},
    }
    phone = {
        ".benchgrid": grid("minmax(0,1fr)", 3),
        ".showcase,.authgrid,.routegrid,.stoplist": grid("minmax(0,1fr)", 3),
        ".formgrid,.stoprow": grid("repeat(2,minmax(0,1fr))", 1),
        ".metrics": grid("repeat(2,minmax(0,1fr))", 1),
        ".metric:first-child": {"grid_column": "1/-1"},
        ".cards": grid("minmax(0,1fr)"),
    }
    def render(recipes):
        return "".join(rule(selector, **recipe) for selector, recipe in recipes.items())
    layout = render(desktop)
    for width, recipes in ((880, tablet), (680, phone), (380, {".cards": grid("minmax(0,1fr)", 1)})):
        layout += f"@media(max-width:{width}px){{{render(recipes)}}}"

    stagger = []
    for selector in (".cards>.case", ".metrics>.metric", ".hero-copy>*", ".proof>div", ".timeline>li"):
        for position in range(1, 8):
            stagger.append(rule(f"{selector}:nth-child({position})", animation_delay=f"{44*position}ms"))
    spring = rule(":root", **{"--spring": spring_curve()})
    return spring + layout + component_styles() + motion_styles() + "@media(prefers-reduced-motion:no-preference){" + "".join(stagger) + "}"


def keyframes(name, stops):
    frames = "".join(rule(when, **properties) for when, properties in stops)
    return f"@keyframes {name}{{{frames}}}"


def motion_styles():
    """All active motion lives behind the same user preference check."""
    frames = {
        "enter": [("from", dict(opacity="0", translate="0 18px")), ("to", dict(opacity="1", translate="0 0"))],
        "reveal": [("from", dict(opacity=".85", translate="0 20px")),
                   ("to", dict(opacity="1", translate="0 0"))],
        "draw": [("from", dict(transform="scaleX(0)")), ("to", dict(transform="scaleX(1)"))],
        "turn": [("from", dict(transform="rotate(-70deg)")), ("to", dict(transform="rotate(0deg)"))],
        "bob": [("50%", dict(transform="translateY(-3px)"))],
        "blink": [("0%,94%,98%,100%", dict(transform="scaleY(1)")), ("96%", dict(transform="scaleY(.12)"))],
        "cheer": [("40%", dict(transform="translateY(-8px) rotate(-3deg)"))],
        "think": [("to", dict(transform="translateY(2px) rotate(2deg)"))],
        "sweep": [("to", dict(background_position="-200%"))],
    }
    animations = {
        ".card,.hero-copy>*,.pagehead,.showcase,.proof>div,.timeline>li": "enter .62s var(--spring) both",
        ".barrow b": "draw .8s var(--spring) both",
        ".stopeditor[open] .disclosure-icon": "turn .35s var(--spring)",
        ".float": "bob 4s ease-in-out infinite",
        ".blink": "blink 4.5s infinite",
        ".success .float": "cheer .8s var(--spring) 1",
        ".loading .float": "think 1s ease-in-out infinite alternate",
        ".skeleton": "sweep 1.2s ease-in-out infinite",
        "details[open]>*:not(summary)": "enter .35s var(--spring)",
        "::view-transition-new(root)": "enter .35s var(--spring)",
    }
    states = {
        ".button,.case,.chip,nav a,.gaze,.stopeditor summary": dict(transition="transform .4s var(--spring),box-shadow .2s,background .2s"),
        ".button:active,.chip:active,.case:active": dict(transform="scale(.97)"),
        ".primary:is(:hover,:focus-visible)": dict(box_shadow="0 4px 16px #a5482438", background="#3a322a"),
        ".stopeditor summary:hover": dict(background="#eeede6"),
        ".playback:not([hidden])": dict(animation="enter .5s var(--spring) both"),
        ".case:hover": dict(transform="translateY(-4px)", box_shadow="0 8px 24px #33312416"),
        ".blink": dict(transform_box="fill-box", transform_origin="center"),
        "body:has(.primary:is(:hover,:focus-visible)) .gaze,.mascot:hover .gaze": dict(transform="translate(-2px,1px)"),
    }
    active = "@view-transition{navigation:auto}"
    active += "".join(rule(selector, animation=animation) for selector, animation in animations.items())
    active += "".join(rule(selector, **values) for selector, values in states.items())
    # Modern engines animate disclosure height in both directions. Native details remains
    # keyboard-operable in engines that do not support intrinsic size interpolation.
    disclosure = rule("details", interpolate_size="allow-keywords")
    disclosure += rule("details::details-content", block_size="0", overflow="clip",
                       transition="block-size .35s var(--spring),content-visibility .35s allow-discrete")
    disclosure += rule("details[open]::details-content", block_size="auto")
    active += "@supports (interpolate-size:allow-keywords){" + disclosure + "}"
    scroll = rule(".sample-outings,.next,.proof", animation="reveal linear both",
                  animation_timeline="view()", animation_range="entry 0% entry 80%")
    active += "@supports (animation-timeline:view()){" + scroll + "}"
    active += rule("#timeline .atlas", view_transition_name="route-map")
    active += rule("#timeline .timeline", view_transition_name="stop-sequence")
    active += "".join(keyframes(name, values) for name, values in frames.items())
    return "@media(prefers-reduced-motion:no-preference){" + active + "}"


def component_styles():
    """Shared spacing and surface styles for editorial sections and the planner."""
    components = {
        ".hero": dict(text_align="center", padding="clamp(64px,10vw,120px) 0 clamp(64px,8vw,104px)"),
        ".hero-copy": dict(max_width="840px", margin="auto"),
        ".hero h1": dict(font_size="clamp(48px,8.2vw,108px)", line_height=".96", letter_spacing="-.071em"),
        ".hero .lede": dict(margin="24px auto 0", max_width="45ch", text_wrap="balance"),
        ".hero-copy .actions": dict(justify_content="center", margin="32px 0 0"),
        ".showcase": dict(background="#292a25", color="#f9f7ef",
                          padding="clamp(24px,4vw,48px)", border_radius="32px", align_items="center"),
        ".showcase h2": dict(font_size="clamp(32px,5vw,64px)", margin_top="16px"),
        ".showcase p": dict(color="#d6d6c9"),
        ".showcase .eyebrow": dict(color="#f1ae86"),
        ".showcase .key": dict(display="grid", gap="12px", margin="24px 0 0"),
        ".key li": dict(font_size="14px"),
        ".showcase .key span": dict(background="#46483e", color="#f7f4ea"),
        ".proof": dict(position="relative", padding="48px 0", align_items="center", border_bottom="1px solid var(--line)"),
        ".proof p": dict(max_width="38ch"),
        ".proof span": dict(display="block", font_size="14px"),
        ".proof strong": dict(font_size="clamp(38px,6vw,76px)", line_height="1", letter_spacing="-.06em",
                              font_variant_numeric="tabular-nums"),
        ".proof>div:nth-child(2) strong": dict(color="var(--accent)"),
        ".sample-outings,.next": dict(margin_top="clamp(56px,8vw,104px)"),
        ".case": dict(padding="clamp(24px,3vw,40px)", min_height="176px"),
        ".case h3": dict(font_size="clamp(21px,2.6vw,29px)"),
        ".caseicon": dict(margin_bottom="24px", width="48px", height="48px"),
        ".presets": dict(margin="32px 0"),
        ".presets h2": dict(font_size="20px"),
        ".planner h2,.results h2": dict(font_size="clamp(26px,3.5vw,36px)"),
        ".schedule,.stops-panel,.results,.question": dict(padding="clamp(24px,4vw,48px)"),
        ".schedule .formgrid": dict(margin_top="16px"),
        ".stops-panel .stoplist": dict(margin_top="24px", align_items="start"),
        ".stopeditor": dict(min_width="0", margin="0"),
        ".stopeditor summary": dict(border_radius="16px", min_height="64px"),
        ".stopeditor summary strong": dict(overflow_wrap="anywhere"),
        ".stopeditor summary small": dict(white_space="nowrap"),
        ".disclosure-icon": dict(font_size="16px", flex_shrink="0"),
        ".planner-actions": dict(display="flex", flex_wrap="wrap", align_items="center", justify_content="space-between",
                                gap="16px", border_radius="24px", background="#ecebe3", padding="24px"),
        ".planner-actions small": dict(display="block"),
        ".planner-actions .actions": dict(margin="0"),
        ".results": dict(margin="40px 0", scroll_margin_top="24px"),
        ".results>p,.question>p": dict(max_width="65ch"),
        ".routegrid": dict(align_items="start", margin_top="24px"),
        ".timeline": dict(padding_left="24px"),
        ".timeline li": dict(padding="12px 0"),
        ".benchgrid>section": dict(background="#f4f3ee", padding="24px", border_radius="16px"),
        ".route-player": dict(margin="0", min_width="0"),
        ".route-player figcaption": dict(display="flex", justify_content="space-between", align_items="center",
                                         flex_wrap="wrap", gap="8px", margin_top="16px", font_size="13px",
                                         color="var(--tone)"),
        ".showcase figcaption": dict(color="#d6d6c9"),
        ".showcase .playback": dict(color="#f9f7ef", background="#414239", box_shadow="none"),
        ".barrow b": dict(transform_origin="left"),
    }
    compact = {
        ".proof .mascot": dict(display="none"),
        ".proof": dict(padding="32px 0"),
        ".stopeditor summary": dict(padding="12px", gap="8px"),
        ".stopeditor summary small": dict(font_size="11px"),
        ".planner-actions .primary": dict(flex_grow="1"),
        ".benchgrid>section": dict(padding="16px"),
    }
    return "".join(rule(selector, **values) for selector, values in components.items()) + (
        "@media(max-width:680px){" +
        "".join(rule(selector, **values) for selector, values in compact.items()) + "}"
    )
