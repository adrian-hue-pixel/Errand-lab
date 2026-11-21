"""Original vector art, navigation icons and data-driven route plots for ErrandLab."""
from html import escape
from math import cos, exp, sin
from random import Random


ICONS = {
    "Overview": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    "Plan a route": '<circle cx="5" cy="18" r="2.5"/><circle cx="19" cy="6" r="2.5"/><path d="M7.5 18H15a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7.5"/>',
    "Evidence": '<path d="M4 4v16h17M8 16v-4m5 4V8m5 8v-6"/>',
    "Saved routes": '<path d="M6 4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17l-6-4-6 4z"/>',
    "closing": '<path d="m3 7 9-4 9 4-9 4zM3 7v10l9 4 9-4V7m-9 4v10m-5-16 9 4"/>',
    "opening": '<path d="M3 10h18l-2-5H5zM5 11v9h14v-9m-10 9v-6h5v6"/>',
    "spread": '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15m6-12v15"/>',
    "relaxed": '<path d="M4 8h12v6a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zm12 1h2a3 3 0 0 1 0 6h-2M3 21h17M8 3v2m4-2v2"/>',
}


def icon(name):
    return (f'<svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true" '
            f'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" '
            f'stroke-linecap="round">{ICONS[name]}</svg>')


def mascot(state="idle", size=80):
    """Capi, a small capybara courier with a bandanna and a folded map."""
    mouth = ('M76 54q4 7 10 0' if state == "success" else
             'M78 54q3 3 7 0' if state != "loading" else 'M78 55h6')
    return f"""<svg class="mascot {state}" width="{size}" height="{size}" viewBox="0 0 112 100"
aria-hidden="true" focusable="false">
<ellipse cx="56" cy="91" rx="36" ry="4" fill="#292b29" opacity=".09"/>
<g class="float" stroke="#44362e" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M22 78q-8-8-1-21l12-15q6-9 16-10l3-11q2-7 8-4l5 8q7-2 13 0
q12 3 15 17l5 3q8 7 0 15-5 5-15 5l-2 16q0 6-7 6h-4l-1-8H44l-2 8H31q-4 0-4-7z"
fill="#c99d78"/>
<path class="ear" d="M58 28q-8-10-3-14 7-5 12 9" fill="#ad8063"/>
<path d="M82 44q7-4 14 1 8 7 0 14-6 5-18 1" fill="#dfbc97" stroke="none"/>
<g class="gaze" fill="#2e2723" stroke="none"><ellipse class="blink" cx="74" cy="37" rx="2.9" ry="3.7"/>
<circle cx="93" cy="47" r="2.4"/></g><path d="{mouth}" fill="none"/>
<path d="m43 40 28 20-4 5-28-21z" fill="#ed6947"/><path d="m63 60 7 12 2-13" fill="#c64c31"/>
<path d="m12 65 9-4 8 3 9-4 3 17-9 4-8-3-9 4z" fill="#fffbeb"/>
<path d="m21 62 3 15m5-13 3 15" stroke="#ada995" stroke-width="1.4"/>
</g></svg>"""


def spring_curve(damping=6.8, frequency=10.4, samples=32):
    """Sample the analytic response of an underdamped spring released from rest."""
    values = []
    for step in range(samples + 1):
        t = step / samples
        displacement = exp(-damping*t) * (cos(frequency*t) + damping/frequency*sin(frequency*t))
        values.append(f"{1-displacement:.4f}" if step != samples else "1")
    return "linear(" + ",".join(values) + ")"


def city_blocks():
    """A decorative street texture. Only overlaid markers represent model coordinates."""
    rng = Random(27)
    blocks = []
    for row in range(-2, 10):
        for col in range(-2, 11):
            x, y = col*68 + (row % 2)*13, row*46
            width = rng.randrange(48, 61)
            height = rng.randrange(29, 39)
            color = rng.choice(("#dddcd3", "#e2e0d8", "#deddd6", "#e6e3dc"))
            blocks.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="4" fill="{color}"/>')
            if (col + row) % 4 == 0:
                blocks.append(f'<path d="M{x+6} {y+height/2}h{width-12}" stroke="#eeede5" stroke-width="3"/>')
    return '<g transform="rotate(-15 320 160)">' + "".join(blocks) + "</g>"


BLOCKS = city_blocks()


def replay_panel(plot, label="Play route"):
    """A route remains readable before playback and in reduced-motion mode."""
    return f"""<figure class="route-player">{plot}
<figcaption><span>Illustrated route · approximate locations</span>
<button type="button" class="button quiet playback" hidden><span aria-hidden="true">▶</span>
<span data-play-label>{label}</span></button><span class="sr" role="status" data-play-status></span>
</figcaption></figure>"""


def replay_overlay(points, path):
    """Use a shared SVG duration so the moving marker and traced leg stay in sync."""
    commands = " L ".join(f"{points[index][0]:.1f} {points[index][1]:.1f}" for index in path)
    seconds = 3.2
    return f"""
<path class="replay-ink" d="M {commands}" pathLength="1" fill="none" stroke="#fbbd58"
      stroke-width="7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1"
      stroke-dashoffset="1">
  <animate data-replay-start="" attributeName="stroke-dashoffset" from="1" to="0"
           dur="{seconds}s" begin="indefinite" fill="remove"/>
</path>
<circle class="replay-dot" r="8" fill="#fff9e8" stroke="#ad4329" stroke-width="3" opacity="0">
  <animateMotion data-replay-start="" path="M {commands}" dur="{seconds}s" begin="indefinite"/>
  <animate data-replay-start="" attributeName="opacity" values="1;1;0" keyTimes="0;.93;1"
           dur="{seconds}s" begin="indefinite"/>
</circle>"""


def route_plot(plan, order, *, visited=None):
    """Fit the route to a fixed viewBox so SVG holds its geometry at any screen size."""
    coords = [(0, 0)] + [(stop.x, stop.y) for stop in plan.stops]
    xs, ys = zip(*coords)
    dx, dy = max(xs)-min(xs), max(ys)-min(ys)
    scale = min(422/max(dx, .1), 191/max(dy, .1))
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    points = [(320+(x-cx)*scale, 146-(y-cy)*scale) for x,y in coords]
    traveled = order if visited is None else visited
    path = [0, *(i+1 for i in traveled), 0]
    line = " ".join(f"{points[i][0]:.1f},{points[i][1]:.1f}" for i in path)
    names = ["Home"] + [s.name for s in plan.stops]
    markers = []
    for i,(x,y) in enumerate(points):
        place = "H" if i == 0 else str(order.index(i-1)+1) if i-1 in order else "·"
        fill = "#292b28" if i == 0 else "#ae3b22" if i-1 in traveled else "#6b695f"
        markers.append(f'<g transform="translate({x:.1f} {y:.1f})"><title>{escape(names[i])}</title>'
                       f'<circle cy="2" r="17" fill="#252525" opacity=".14"/><circle r="16" fill="{fill}" '
                       f'stroke="#fffdf7" stroke-width="3"/><text y="5" text-anchor="middle" fill="white" '
                       f'font-size="15" font-weight="750">{place}</text></g>')
    accessible = escape(" → ".join(names[i] for i in path), quote=True)
    return f"""<svg class="atlas" viewBox="0 0 640 292" role="img" aria-label="{accessible}">
<rect width="640" height="292" fill="#f3f1e9"/>{BLOCKS}
<path d="M-20 294Q93 192 93 113T180-24" fill="none" stroke="#cad7d0" stroke-width="26"/>
<path d="M-20 294Q93 192 93 113T180-24" fill="none" stroke="#dce5df" stroke-width="16"/>
<polyline points="{line}" fill="none" stroke="#fffdf7" stroke-width="11" stroke-linejoin="round"/>
<polyline points="{line}" fill="none" stroke="#d85836" stroke-width="5" stroke-linejoin="round"/>
{replay_overlay(points, path)}{"".join(markers)}<g transform="translate(604 28)"><circle r="16" fill="#fffdf7"/>
<path d="m0-10 5 14-5-3-5 3z" fill="#434339"/></g></svg>"""


def itinerary_key(plan, order):
    """Connect stop numbers to destinations without placing labels on top of one another."""
    items = []
    for position, index in enumerate(order, 1):
        name = escape(plan.stops[index].name)
        items.append(f'<li><span aria-hidden="true">{position}</span>{name}</li>')
    return '<ol class="key" aria-label="Example stop order">' + "".join(items) + '</ol>'


def benchmark_figure(cases):
    """Small multiple charts share a 0–100% scale. Exact values are printed beside each bar."""
    body = []
    for title, policies in cases:
        rows = []
        for key, name in (("nearest", "Nearest"), ("nominal", "Fixed-time"), ("robust", "Delay-aware")):
            value = policies[key]["all_on_time"]
            rows.append(f'<div class="barrow"><span>{name}</span><i aria-hidden="true">'
                        f'<b class="{key}" style="width:{100*value:.3f}%"></b></i>'
                        f'<strong>{value:.1%}</strong></div>')
        body.append('<section><h3>' + escape(title) + '</h3>' + "".join(rows) + '</section>')
    return '<div class="benchgrid">' + "".join(body) + '</div>'
