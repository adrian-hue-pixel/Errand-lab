"""Server-rendered interface. All pages and data visualizations are authored in Python."""
import workspace_ui as workspace
from html import escape
from artwork import benchmark_figure, icon, itinerary_key, mascot, replay_panel, route_plot
from urllib.parse import urlencode
from routing import DISTANCE, POLICIES, PRESETS, RESEARCH, TRAFFIC, analyze, preset


def h(value):
    return escape(str(value), quote=True)


def page(title, current, content, session, *, bare=False):
    return workspace.shell(title,current,content,session,bare)


def csrf(session):
    return f'<input type="hidden" name="csrf" value="{h(session["csrf"])}">'


def button(label, url, secondary=False):
    style = "button quiet" if secondary else "button primary"
    return f'<a class="{style}" href="{h(url)}">{h(label)}</a>'


def notice(message, error=False):
    return f'<p class="notice{" error" if error else ""}" role="{"alert" if error else "status"}">{h(message)}</p>'


def intro(label, title, description):
    return f'<div class="pagehead"><p class="eyebrow">{h(label)}</p><h1>{h(title)}</h1><p class="lede">{h(description)}</p></div>'


def clock(value):
    hour, minute = divmod(round(value), 60)
    return f"{hour % 24:02}:{minute:02}" + (f" (+{hour // 24}d)" if hour >= 24 else "")


def percent(value):
    return f"{value:.1%}"


def pp(value):
    if abs(value) < 0.0005:
        return "0.0 pp"
    return f"{value*100:+.1f} pp"


def home(session):
    sample = preset("closing")
    data = analyze(sample)
    return page("Overview","Overview",workspace.dashboard(data,sample,session),session)


def field(name, label, value="", kind="text", extra=""):
    return f'<label for="{h(name)}">{h(label)}<input id="{h(name)}" name="{h(name)}" type="{h(kind)}" value="{h(value)}" {extra}></label>'


def select(name, label, value, options):
    items = "".join(
        f'<option value="{h(key)}"{" selected" if str(value)==str(key) else ""}>{h(text)}</option>'
        for key, text in options
    )
    return f'<label for="{h(name)}">{h(label)}<select id="{h(name)}" name="{h(name)}">{items}</select></label>'


def fields_from_plan(plan):
    values = {"title": plan.title, "start": clock(plan.start), "deadline": clock(plan.deadline), "traffic": plan.traffic}
    for i, s in enumerate(plan.stops, 1):
        values.update({
            f"name{i}": s.name, f"x{i}": s.x, f"y{i}": s.y, f"open{i}": clock(plan.start+s.opens),
            f"close{i}": clock(plan.start+s.closes), f"service{i}": s.service, f"priority{i}": s.priority,
        })
    return values


def lab(session, key="closing", count=None, values=None, message=None):
    if values is None:
        values = fields_from_plan(preset(key))
    if count is None:
        count = len(preset(key).stops)
    tabs = "".join(f'<a class="chip" href="/lab?{urlencode({"preset": k})}"'
                   f'{" aria-current=page" if k==key else ""}>{h(t)}</a>'
                   for k,(t,_) in PRESETS.items())
    tabs += '<a class="chip" href="/lab?preset=blank"' + (' aria-current="page"' if key == "blank" else "") + '>Start blank</a>'
    rows = []
    for i in range(1, count+1):
        get = lambda key, default="": values.get(f"{key}{i}", default)
        expanded = i == 1 or bool(message) or not get("name")
        summary_name = get("name") or "Add stop details"
        rows.append(f"""<details class="stopeditor"{" open" if expanded else ""}>
<summary><span class="stopnum">{i}</span><strong>{h(summary_name)}</strong>
<small>{h(get("open","09:00"))}–{h(get("close","17:00"))}</small><span class="disclosure-icon" aria-hidden="true">+</span></summary>
<fieldset class="stop"><legend class="sr">Stop {i}</legend>
<div class="stoprow">
{field(f"name{i}", "Stop name", get("name"), extra='required maxlength="42" placeholder="e.g. Bakery"')}
{field(f"x{i}", "East / west (km)", get("x"), "number", 'required min="-20" max="20" step="any"')}
{field(f"y{i}", "North / south (km)", get("y"), "number", 'required min="-20" max="20" step="any"')}
{field(f"open{i}", "Opens", get("open", "09:00"), "time", "required")}
{field(f"close{i}", "Closes", get("close", "17:00"), "time", "required")}
{field(f"service{i}", "Visit (min)", get("service", 10), "number", 'required min="1" max="90"')}
{select(f"priority{i}", "Priority", get("priority", 1), [(1, "Standard"), (2, "High")])}
</div></fieldset></details>""")
    edits = (
        ('<button class="button quiet" name="action" value="add" formnovalidate>Add stop +</button>' if count < 6 else "")
        + ('<button class="button quiet" name="action" value="remove" formnovalidate>Remove last stop</button>' if count > 2 else "")
    )
    return page("Plan a route", "Plan a route", intro("Route planner", "Build your outing",
        "Start with a sample or enter your own stops. You’ll see which order best survives delays.") + f"""
<section class="presets" aria-label="Sample outings"><h2>Choose an outing</h2>
<div class="chips">{tabs}</div></section>
{notice(message, True) if message else ""}
<form class="planner" action="/lab" method="post">{csrf(session)}
<input type="hidden" name="count" value="{count}"><input type="hidden" name="preset" value="{h(key)}">
<section class="card schedule">
<div class="formtitle"><h2>Your time budget</h2>{mascot("idle",72)}</div><div class="formgrid">
{field("title","Outing name",values.get("title",""),extra='required maxlength="60"')}
{field("start","Leave home",values.get("start","09:00"),"time","required")}
{field("deadline","Back home by",values.get("deadline","11:00"),"time","required")}
{select("traffic","Traffic variability",values.get("traffic","Moderate"), [(t,t) for t in TRAFFIC])}
</div></section>
<section class="card stops-panel">
<h2>Stops</h2><p>Enter opening hours, location, and how long each errand takes.</p>
<div class="stoplist">{"".join(rows)}</div>
</section>
<div class="planner-actions">
<div><b>{count} stops to compare</b><small>Compare route orders across simulated traffic conditions.</small></div>
<div class="actions editor-actions"><button class="button primary" name="action" value="run">Compare routes →</button>{edits}</div>
</div>
</form>
<div id="progress" class="pending" role="status" hidden>{mascot("loading",64)}<div><b>Comparing route orders…</b><div class="skeleton"></div><div class="skeleton short"></div></div></div>
<details class="card details"><summary>How do I estimate locations?</summary><p>Home is (0, 0). Use negative numbers for west and south. A shop 800 m west and 300 m north would be −0.8 and 0.3. ErrandLab uses these offsets to estimate travel.</p></details>""", session)


def result_page(session, row, payload, policy="robust", flash=""):
    plan, data = payload
    selected = data["policies"][policy]
    contrast = data["contrasts"]["nearest"]
    vs_fixed = data["contrasts"]["nominal"]
    link = f'/run/{row["id"]}'
    choices = "".join(
        f'<a class="chip" href="{link}?policy={key}#timeline"{" aria-current=page" if key==policy else ""}>{name}</a>'
        for key, name in POLICIES.items()
    )
    metric_rows = "".join(f"""
<tr{" class=current" if key==policy else ""}><th scope="row">{name}</th>
<td><span class="sr">{percent(m["all_on_time"])}</span><span aria-hidden="true">{percent(m["all_on_time"])}</span>
<meter aria-hidden="true" min="0" max="1" value="{m["all_on_time"]:.5f}"></meter></td>
<td>{m["mean_completed"]:.2f} / {len(plan.stops)}</td><td>{percent(m["home_on_time"])}</td>
<td>{m["median_elapsed"]:.1f} min</td><td>{m["p90_elapsed"]:.1f} min</td></tr>"""
        for key, name in POLICIES.items() for m in [data["policies"][key]]
    )
    trace = {v["index"]: v for v in selected["nominal_trace"]}
    steps = []
    for i in selected["order"]:
        s, visit = plan.stops[i], trace.get(i)
        if visit is None:
            timing, status = "Skipped before departure", "Skipped"
        elif not visit["completed"]:
            timing, status = f'{clock(plan.start + visit["arrival"])} arrival', "Missed"
        else:
            timing = f'{clock(plan.start + visit["arrival"])} → {clock(plan.start + visit["end"])}'
            if visit["wait"] >= 0.5:
                timing += f' · {round(visit["wait"])} min wait'
            status = "Complete"
        steps.append(f'<li><div><b>{h(s.name)}</b><small>{timing}</small></div><span class="tag">{status}</span></li>')
    returned = "On time" if selected["nominal_home_on_time"] else "Late"
    steps.append(f'<li><div><b>Return home</b><small>{clock(plan.start + selected["nominal_elapsed"])}</small></div>'
                 f'<span class="tag">{returned}</span></li>')
    if row["saved"]:
        saving = '<span class="tag">Saved to your account</span>'
    elif session["username"]:
        saving = (f'<form action="{link}/save" method="post">{csrf(session)}'
                  '<button class="button quiet">Save route</button></form>')
    else:
        saving = button("Sign in to save", "/login?" + urlencode({"next": link}), True)
    state = notice("Route saved to your account.") if flash and row["saved"] else ""
    return page(plan.title, "Plan a route", intro("Route results", plan.title,
        f"{len(plan.stops)} stops · {clock(plan.start)}–{clock(plan.deadline)} · {plan.traffic.lower()} traffic variability") + f"""
{state}
<div class="actions result-actions">{mascot("success",64)}{button("Edit inputs", link+"/edit",True)}{saving}{button("Download CSV",link+"/csv", True)}</div>
<section class="metrics" aria-label="Delay-aware results">
<div class="card metric"><small>All stops and home on time</small><strong>{percent(data["policies"]["robust"]["all_on_time"])}</strong></div>
<div class="card metric"><small>Change vs nearest stop</small><strong>{pp(contrast["lift"])}</strong>
<small>95% paired interval {pp(contrast["interval"][0])} to {pp(contrast["interval"][1])}</small></div>
<div class="card metric"><small>Simulated test days</small><strong>{data["test_days"]}</strong>
<small>{data["candidate_orders"]} candidate orders</small></div></section>
<section id="timeline" class="card results"><h2>Route and stop timeline</h2>
<p>The timeline shows what happens at typical travel times. Select a strategy to inspect its route.</p>
<div class="chips" aria-label="Route strategy">{choices}</div><div class="routegrid">
{replay_panel(route_plot(plan, selected["order"], visited=[v["index"] for v in selected["nominal_trace"]]))}
<ol class="timeline">{"".join(steps)}</ol></div></section>
<section class="card results"><h2>Compare route strategies</h2>
<p>Every strategy faced the same simulated days. A shorter route can mean fewer errands were completed.</p>
<p>Delay-aware vs fixed-time optimizer <b>{pp(vs_fixed["lift"])}</b> in full success (95% paired interval {pp(vs_fixed["interval"][0])} to {pp(vs_fixed["interval"][1])}).</p>
<details><summary>View the full comparison</summary><div class="table-scroll" tabindex="0" role="region" aria-label="Route comparison"><table>
<thead><tr><th scope="col">Strategy</th><th scope="col">Full success</th><th scope="col">Stops completed</th>
<th scope="col">Home on time</th><th scope="col">Median outing</th><th scope="col">90th percentile</th></tr></thead>
<tbody>{metric_rows}</tbody></table></div></details>
</section>
<p class="footnote">Results are estimates from a traffic model. {h(DISTANCE)} <a href="/evidence#method">See assumptions and limits</a>.</p>
""", session)


def evidence(session):
    rows = []
    cases = []
    for key, (title, _) in PRESETS.items():
        data = analyze(preset(key))
        p = data["policies"]
        cases.append((title, p))
        near = data["contrasts"]["nearest"]
        rows.append(f'<tr><th scope="row"><a href="/lab?preset={key}">{h(title)}</a></th>'
                    f'<td>{percent(p["nearest"]["all_on_time"])}</td><td>{percent(p["nominal"]["all_on_time"])}</td>'
                    f'<td>{percent(p["robust"]["all_on_time"])}</td><td>{pp(near["lift"])}</td>'
                    f'<td>{pp(near["interval"][0])} to {pp(near["interval"][1])}</td></tr>')
    return page("Evidence", "Evidence", intro("Research evidence", "Will the route hold up?",
        "An experiment you can rerun with the same inputs and seeds.") + f"""
<section class="card question"><p class="eyebrow">Research question</p><h2>{h(RESEARCH)}</h2>
<p>Success means completing every errand within its window and returning home by the chosen deadline.</p></section>
<section class="card results"><h2>Four modeled outings</h2>
<p>These hand-designed cases stress different failure modes. Closing time was tuned during development to expose a trade-off with fixed-time routing. The cases are illustrative and do not estimate the population-wide benefit.</p>
{benchmark_figure(cases)}
<details><summary>Full results and paired intervals</summary><div class="table-scroll" tabindex="0" role="region" aria-label="Benchmark comparisons"><table><thead><tr>
<th scope="col">Scenario</th><th scope="col">Nearest first</th><th scope="col">Fixed-time</th><th scope="col">Delay-aware</th>
<th scope="col">Change vs nearest</th><th scope="col">95% paired interval</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></details>
<div class="actions">{button("Download benchmark CSV","/benchmark.csv",True)}</div></section>
<section id="method" class="card results"><h2>Method and limitations</h2>
<ol class="method"><li><b>Model the outing.</b> Uses a distance grid, a 1.2 detour factor, six minutes per detoured kilometre, fixed visit durations and known opening windows. Traffic includes a shared daily slowdown and independent leg variation.</li>
<li><b>Pick a route.</b> Exhaustive search checks up to 720 orders. The delay-aware objective rewards completed priority points, penalizes late returns and gives extra weight to the lowest-scoring fifth of 48 training days. The fixed-time optimizer uses the same reward on one nominal day. Nearest stop uses travel time alone.</li>
<li><b>Test it separately.</b> All routes face the same 600 held-out simulated days per scenario. The interval resamples paired day-level differences. It measures simulation sampling uncertainty under these assumptions.</li>
<li><b>Check the model against reality.</b> Real roads, opening-hour changes, service overruns and live traffic can move results. A next study would log actual outings, lock the scenarios in advance and measure completion and total time in the field.</li></ol>
<p><a href="https://developers.google.com/optimization/routing/vrptw">Background on routing with time windows ↗</a></p>
<details><summary>See model notes</summary><p>Capybara field note · Always leave time for the trip home.</p></details></section>""", session)


def account_page(session, signup=False, target="", error=None, username=""):
    return page("Create account" if signup else "Sign in","",workspace.gate(session,signup,target,error,username),session,bare=True)


def saved_page(session, rows):
    items = "".join(
        f'<li><a href="/run/{r["id"]}">{h(r["title"])}</a><span>{h(r["date"])}</span></li>' for r in rows
    )
    content = (
        f'<ul class="saved">{items}</ul>' if items else
        f'{mascot("empty",96)}<h2>Your first route goes here</h2><p>Compare an outing, then choose Save route on its results page.</p>{button("Plan an outing →","/lab")}'
    )
    return page("Saved routes", "Saved routes", intro("Your account", "Saved routes",
        f"Signed in as {session['username']}.") + f'<section class="card results">{content}</section>', session)


def error_page(session, status, message):
    return page(status, "", intro(status, message, "You can return to the planner and start another route.")
                + button("Open route planner", "/lab"), session)
