"""Authenticated navigation, profile, settings and the 3D study."""
from pathlib import Path
from html import escape as esc
import json
from artwork import mascot, icon, route_plot
import store

PAGES = [("Overview","/","Overview"),("Plan a route","/lab","Plan a route"),("Sample route","/sample","spread"),
         ("Evidence","/evidence","Evidence"),("Saved routes","/saved","Saved routes"),
         ("Settings","/settings","opening"),("Profile","/profile","relaxed")]
AVATARS = {"Capi":"◉","Leaf":"❧","Compass":"✥","Sun":"☼"}


def shell(title,current,content,session,bare):
    user=session["username"]
    head=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} · ErrandLab</title>
<link rel="stylesheet" href="/style.css"><script src="/theme.js"></script></head>'''
    brand=f'<a class="brand" href="/"><span class="mark">{icon("Plan a route")}</span>ErrandLab</a>'
    ambient='<div class="atmos" aria-hidden="true"><i></i><i></i></div>'
    if not user:
        return head+f'<body class="gate">{ambient}<main id="content">{content}</main></body></html>'
    profile=store.profile(user)
    name=esc(profile["display"] or ("Demo explorer" if user.startswith("demo:") else user.split("@")[0]))
    glyph=AVATARS.get(profile["avatar"],"◉")
    links="".join(f'<a href="{url}" title="{label}" aria-label="{label}"'+(' aria-current="page"' if label==current else '')+f'>{icon(sym)}<span>{label}</span></a>' for label,url,sym in PAGES)
    csrf=esc(session["csrf"])
    return head+f'''<body class="workspace" data-account="{esc(user,quote=True)}">{ambient}
<a class="skip" href="#content">Skip to content</a>
<aside class="rail">{brand}<button class="iconbtn collapse" aria-label="Collapse navigation" aria-expanded="true">⇤</button>
<nav aria-label="Main navigation">{links}</nav><div class="railfoot">ERRANDLAB / ROUTE ATLAS</div></aside>
<div class="desk"><header class="utilities"><button class="iconbtn mobilemenu" aria-label="Open navigation" aria-expanded="false">☰</button>
<b>{esc(current or title)}</b><div class="tools"><button class="iconbtn" data-theme-switch aria-label="Switch color theme">◐</button>
<details class="notify"><summary aria-label="Notifications">◌</summary><div><b>Workspace notifications</b><p id="notif-text">Your route workspace is ready.</p></div></details>
<a class="profilepill" href="/profile"><span>{glyph}</span>{name}</a></div></header>
<main class="container" id="content">{content}</main></div>
<button id="capi-launch" class="dock">{mascot("idle",52)}<span>Ask Capi</span></button>
<dialog id="capi-dialog" aria-labelledby="chat-title"><header><div>{mascot("idle",64)}<h2 id="chat-title">Capi</h2></div><button data-close aria-label="Close chat">×</button></header>
<p>Ask about your route, deadlines, or the benchmark.</p><div id="messages" role="log" aria-live="polite"></div>
<div class="starters"><button>Explain this route</button><button>How does traffic affect my chances?</button></div>
<form id="chat-form"><label for="chat-input">Message Capi</label><textarea id="chat-input" maxlength="1800" rows="2" required></textarea><button class="button primary">Send message ↗</button></form>
<a href="/settings">Manage Groq key</a></dialog>
<script src="/motion.js" defer></script><script src="/workspace.js" defer></script></body></html>'''


def gate(session,signup,target,error,username):
    verb="Create account" if signup else "Sign in"
    fieldtype="email" if signup else "text"
    other="/login" if signup else "/signup"
    token=f'<input type="hidden" name="csrf" value="{esc(session["csrf"])}"><input type="hidden" name="next" value="{esc(target,quote=True)}">'
    return f'''<div class="entry"><section class="entry-story"><div class="wordmark">{icon("Plan a route")} ErrandLab</div>
<div class="entry-copy"><p class="eyebrow">Everyday route atlas</p><h1>One outing.<br><em>Every stop.</em></h1>
<p>Plan around closing times, explore your route in 3D, and see how it holds up when traffic changes.</p></div>
<div class="cartograph" aria-hidden="true"><svg viewBox="0 0 600 150"><path d="M0 113 Q70 150 125 88 T240 62 T360 93 T510 38 T620 10" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="6 6"/>
<g fill="#edb879"><circle cx="125" cy="88" r="7"/><circle cx="360" cy="93" r="7"/><circle cx="510" cy="38" r="7"/></g></svg>{mascot("idle",100)}</div></section>
<section class="auth card"><h2>{verb}</h2><p>{"Keep your routes and preferences together." if signup else "Open your personal route workspace."}</p>
{('<p class="notice error" role="alert">'+esc(error)+'</p>') if error else ''}
<form method="post" action="{"/signup" if signup else "/login"}">{token}
<label>{"Email address" if signup else "Email or existing username"}<input name="username" type="{fieldtype}" maxlength="254" value="{esc(username,quote=True)}" autocomplete="username" required></label>
<label>Password<input name="password" type="password" maxlength="128" {"minlength=12" if signup else ""} autocomplete="{"new-password" if signup else "current-password"}" required></label>
{"<small>Use at least 12 characters.</small>" if signup else ""}
<label class="check"><input type="checkbox" name="remember" value="yes">Remember me for seven days</label>
<button class="button primary">{verb} →</button></form>
<form method="post" action="/demo">{token}<button class="button quiet">Demo quick sign-in</button></form>
<a href="{other}?next={esc(target,quote=True)}">{"Already registered? Sign in" if signup else "Create an account"}</a></section></div>'''


def settings():
    return '''<div class="pagehead"><h1>Settings</h1><p>Choose how your workspace looks and how Capi connects.</p></div>
<section class="card prefs"><h2>Groq connection</h2><p>The key stays in this browser tab for this account. Testing the key contacts Groq. Chat sends your message, recent conversation, and any visible result metrics directly to Groq.</p>
<label for="api-key">Groq API key</label><div class="actions"><input id="api-key" type="password" autocomplete="off" spellcheck="false"><button id="reveal-key" class="button quiet">Show</button></div>
<div class="actions"><button id="check-key" class="button primary">Save and test key</button><button id="forget-key" class="button quiet">Remove key</button></div>
<output id="key-status" aria-live="polite"></output></section>
<section class="card prefs"><h2>Workspace preferences</h2>
<label>Appearance<select id="pref-theme"><option value="dark">Dark</option><option value="light">Light</option></select></label>
<label>Ambient motion<select id="pref-intensity"><option>Full</option><option>Subtle</option><option>Off</option></select></label>
<label class="check"><input type="checkbox" id="pref-mascot">Show Capi in the workspace</label>
<label class="check"><input type="checkbox" id="pref-notifications">Show route notifications</label>
<output id="pref-status" aria-live="polite"></output></section>'''


def profile_page(session, message=""):
    p=store.profile(session["username"])
    val=lambda key:esc(p[key],quote=True)
    token=f'<input type="hidden" name="csrf" value="{esc(session["csrf"])}">'
    avatars="".join(f'<option {"selected" if key==p["avatar"] else ""} value="{key}">{symbol} {key}</option>' for key,symbol in AVATARS.items())
    return f'''<div class="pagehead"><h1>Your profile</h1><p>Personalize your space and return to saved outings.</p></div>
<section class="card prefs"><h2>Profile details</h2><p role="status">{esc(message)}</p>
<form method="post" action="/profile">{token}<label>Display name<input required name="display" maxlength="48" value="{val("display")}"></label>
<label>Avatar<select name="avatar">{avatars}</select></label><label>Role<input name="role" maxlength="64" value="{val("role")}"></label>
<label>Bio<textarea name="bio" maxlength="320">{val("bio")}</textarea></label><button class="button primary">Save profile</button></form></section>
<section class="card prefs"><h2>Saved routes</h2><p>{store.saved_count(session["username"])} saved in your workspace.</p>
<a class="button quiet" href="/saved">Open saved routes</a></section><form method="post" action="/logout" class="logout">{token}<button class="button quiet">Sign out</button></form>'''


def sample_page():
    root=Path(__file__).resolve().parent
    have_models=all((root/"models"/(name+".glb")).is_file() for name in ("town","vehicle","capi","sky"))
    film=next(("/media/"+name for name in ("sample-route.mp4","sample-route.webm") if (root/"media"/name).is_file()), "")
    config=esc(json.dumps({"models":have_models,"video":film}),quote=True)
    from routing import preset, analyze
    sample=preset("closing")
    preview="" if have_models or film else '<div class="waiting"><div>'+route_plot(sample,analyze(sample)["policies"]["robust"]["order"])+'</div><b>Route mapped. Models pending.</b><p>The 3D tour will open here once your scene assets arrive.</p></div>'
    return f'''<div class="pagehead"><p class="eyebrow">Route studio</p><h1>West 112th Street</h1>
<p>Follow the Transit past the brick shopfronts to Capi’s corner. Watch the street film or take the camera yourself.</p></div>
<section class="card studio"><div class="actions"><button class="button primary" id="mode-live" aria-pressed="true">Interactive 3D</button><button class="button quiet" id="mode-film" aria-pressed="false">Cinema</button></div>
<div class="stage" id="stage" data-assets="{config}">{preview}<canvas tabindex="0" id="world" aria-label="3D town. Drag to orbit, scroll to zoom, or use the camera buttons."></canvas>
<video poster="/media/town.jpg" id="film" hidden playsinline preload="metadata"></video></div>
<div class="studio-controls"><button id="play" class="button primary">Play route</button><label>Route progress<input id="scrub" type="range" min="0" max="1000" step="1" value="0"></label>
<button id="orbit" class="button quiet">Rotate</button><button id="zoom-in" class="button quiet">Zoom in</button><button id="zoom-out" class="button quiet">Zoom out</button></div>
<button class="button quiet" id="record-route" type="button" hidden>Record route</button>
<p id="studio-status" role="status">Loading the town…</p><div class="telemetry"><div><small>Route distance traveled</small><strong id="distance">0.0 m</strong></div>
<div><small>Time left in replay</small><strong id="eta">12 s</strong></div><div><small>Next waypoint</small><strong id="waypoint">Shopfronts</strong></div></div></section>
<script type="module" src="/studio.js"></script>'''


def dashboard(data,plan,session):
    d=data["policies"]["robust"]
    cards=[("All errands on time",f'{d["all_on_time"]:.1%}',"Closing time · simulation","/evidence"),
           ("Median outing",f'{d["median_elapsed"]:.0f} min',"Inspect the route inputs","/lab"),
           ("Saved routes",str(store.saved_count(session["username"])),"Open your collection","/saved")]
    metrics="".join(f'<a class="card dash-metric" href="{url}"><small>{label}</small><strong>{value}</strong><span>{detail} ↗</span></a>' for label,value,detail,url in cards)
    return f'''<div class="pagehead"><p class="eyebrow">Route workspace</p><h1>Your outing atlas</h1><p>Choose a route, test your timing, and see the trip before you leave.</p></div>
<section class="card featured"><div><p class="eyebrow">Featured study · 4 stops</p><h2>Closing time</h2><p>One tight parcel deadline changes the order of the entire afternoon.</p>
<div class="actions"><a class="button primary" href="/sample">Open route studio ↗</a><a class="button quiet" href="/lab">Plan an outing</a></div></div>
<a href="/sample" aria-label="Open the 3D route studio">{route_plot(plan,d["order"])}</a></section>
<section class="dash-metrics">{metrics}</section>'''
