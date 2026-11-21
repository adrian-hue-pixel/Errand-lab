"""ErrandLab WSGI application and local server."""
from dataclasses import asdict
from datetime import datetime, timezone
from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
import argparse
import csv
import hmac
import io
import json
import os
import re
import sys

from atmosphere import stylesheet
from layout import styles
import secrets
import workspace_ui as workspace
import routing
import store
import ui

CSS = (Path(__file__).with_name("style.css").read_text() + styles() + stylesheet()).encode()
MOTION = Path(__file__).with_name("motion.js").read_bytes()
RUN_PATH = re.compile(r"/run/([a-zA-Z0-9_-]{24})(?:/(edit|save|csv|json))?")
NEXT_PATH = re.compile(r"/(?:saved|run/[a-zA-Z0-9_-]{24})")
SECURE = os.environ.get("ERRANDLAB_HTTPS") == "1"
STATUSES = {
    200: "OK", 303: "See Other", 400: "Bad Request", 403: "Forbidden", 404: "Not Found",
    405: "Method Not Allowed", 413: "Content Too Large", 422: "Unprocessable Content", 429: "Too Many Requests",
}


ROOT = Path(__file__).resolve().parent
STATIC_FILES = {
    "/"+name:(ROOT/name,mime) for mime,names in {
        "text/javascript":("workspace.js","studio.js","motion.js","vendor/three/three.module.js","vendor/three/GLTFLoader.js","vendor/three/BufferGeometryUtils.js"),
        "image/jpeg":("media/town.jpg",),"video/webm":("media/sample-route.webm",),"video/mp4":("media/sample-route.mp4",),
        "application/json":("models/route.json",),"model/gltf-binary":("models/town.glb","models/vehicle.glb","models/capi.glb","models/sky.glb")
    }.items() for name in names
}


def static_response(environ,start,filename,mime):
    size=filename.stat().st_size
    requested=environ.get("HTTP_RANGE")
    if not requested or not mime.startswith("video/"):
        return send(start,filename.read_bytes(),mime=mime)
    match=re.fullmatch(r"bytes=(\d*)-(\d*)",requested)
    if not match or not any(match.groups()):
        return send(start,status=416,headers=[("Content-Range",f"bytes */{size}")])
    a,b=match.groups()
    left=int(a) if a else max(0,size-int(b))
    right=min(size-1,int(b)) if a and b else size-1
    if left>right:
        return send(start,status=416,headers=[("Content-Range",f"bytes */{size}")])
    with filename.open("rb") as handle:
        handle.seek(left)
        return send(start,handle.read(right-left+1),206,mime,[("Accept-Ranges","bytes"),("Content-Range",f"bytes {left}-{right}/{size}")])


STATUSES.update({206:"Partial Content",416:"Range Not Satisfiable"})


def time_minutes(value):
    if not re.fullmatch(r"[0-9]{2}:[0-9]{2}", value):
        raise ValueError("Use a valid time for every time field.")
    hour, minute = map(int, value.split(":"))
    if hour > 23 or minute > 59:
        raise ValueError("Use a valid time for every time field.")
    return hour * 60 + minute


def parse_plan(form, count):
    title = form.get("title", "").strip()
    if not 1 <= len(title) <= 60:
        raise ValueError("Enter an outing name of 1–60 characters.")
    start = time_minutes(form.get("start", ""))
    deadline = time_minutes(form.get("deadline", ""))
    stops = []
    for i in range(1, count+1):
        name = form.get(f"name{i}", "").strip()
        try:
            x = float(form[f"x{i}"])
            y = float(form[f"y{i}"])
            service = int(form[f"service{i}"])
            priority = int(form[f"priority{i}"])
        except (KeyError, ValueError):
            raise ValueError(f"Stop {i} needs two valid coordinates, a visit duration and a priority.") from None
        opens = time_minutes(form.get(f"open{i}", "")) - start
        closes = time_minutes(form.get(f"close{i}", "")) - start
        stops.append(routing.Stop(name, x, y, opens, closes, service, priority))
    plan = routing.Plan(title, start, deadline, form.get("traffic", ""), tuple(stops))
    routing.validate(plan)
    return plan


def unpack(payload):
    data = json.loads(payload)
    props = data["plan"]
    plan = routing.Plan(props["title"], props["start"], props["deadline"], props["traffic"],
                        tuple(routing.Stop(**values) for values in props["stops"]))
    return plan, data["analysis"]


def cookie_value(raw):
    jars = SimpleCookie()
    try:
        jars.load(raw)
    except CookieError:
        return None
    if "errandlab" in jars:
        return jars["errandlab"].value
    return None


def session_cookie(token, session, remember=False):
    age = store.SESSION_LIFE if session["username"] else store.GUEST_LIFE
    lifetime = f"; Max-Age={age}" if remember else ""
    return f"errandlab={token}{lifetime}; Path=/; HttpOnly; SameSite=Lax" + ("; Secure" if SECURE else "")


def query_fields(data):
    return {key: values[-1] for key, values in parse_qs(data, keep_blank_values=True, max_num_fields=80).items()}


def send(start_response, content="", status=200, mime="text/html; charset=utf-8", headers=(), cookie=None):
    encoded = content if isinstance(content, bytes) else content.encode("utf-8")
    common = [
        ("Content-Type", mime), ("Content-Length", str(len(encoded))), ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"), ("Referrer-Policy", "no-referrer"), ("X-Frame-Options", "DENY"),
        ("Content-Security-Policy",
         "default-src 'none'; connect-src 'self' blob: https://api.groq.com; img-src 'self' blob: data:; media-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"),
    ]
    if cookie:
        common.append(("Set-Cookie", cookie))
    if SECURE:
        common.append(("Strict-Transport-Security", "max-age=31536000"))
    start_response(f"{status} {STATUSES[status]}", [*common, *headers])
    return [encoded]


def jump(start, target, cookie=None):
    return send(start, status=303, headers=[("Location", target)], cookie=cookie)


def json_response(start, payload, status=200):
    return send(start, json.dumps(payload, ensure_ascii=False, allow_nan=False), status,
                "application/json; charset=utf-8")


def csv_response(start, name, rows):
    output = io.StringIO()
    csv.writer(output).writerows(rows)
    return send(start, output.getvalue(), mime="text/csv; charset=utf-8",
                headers=[("Content-Disposition", f'attachment; filename="{name}.csv"')])


def comparison_rows(data):
    yield ("strategy", "full_success_rate", "home_on_time_rate", "mean_stops_completed",
           "median_outing_minutes", "p90_outing_minutes", "mean_driving_minutes")
    for key, name in routing.POLICIES.items():
        m = data["policies"][key]
        yield (name, m["all_on_time"], m["home_on_time"], m["mean_completed"],
               m["median_elapsed"], m["p90_elapsed"], m["mean_drive"])


def benchmark_rows():
    yield ("scenario", "test_days", "nearest_full_success", "fixed_time_full_success",
           "delay_aware_full_success", "lift_vs_nearest", "nearest_ci_lower", "nearest_ci_upper",
           "lift_vs_fixed", "fixed_ci_lower", "fixed_ci_upper")
    for key in routing.PRESETS:
        plan = routing.preset(key)
        data = routing.analyze(plan)
        p = data["policies"]
        near = data["contrasts"]["nearest"]
        nominal = data["contrasts"]["nominal"]
        yield (key, data["test_days"], p["nearest"]["all_on_time"], p["nominal"]["all_on_time"],
               p["robust"]["all_on_time"], near["lift"], *near["interval"], nominal["lift"], *nominal["interval"])


def application(environ, start):
    method = environ["REQUEST_METHOD"]
    path = environ.get("PATH_INFO", "/")
    if method not in {"GET", "POST"}:
        return send(start, "Method not allowed.", 405, "text/plain; charset=utf-8", [("Allow", "GET, POST")])
    if method == "GET":
        if path == "/theme.js":
            return send(start, (ROOT/"theme.js").read_bytes(), mime="text/javascript")
        if path == "/style.css":
            return send(start, CSS, mime="text/css; charset=utf-8")
        if path == "/health":
            return json_response(start, {"status": "ok"})
    session = store.get_session(cookie_value(environ.get("HTTP_COOKIE", "")))
    cookie = None
    if session is None:
        token, session = store.new_session()
        cookie = session_cookie(token, session)

    def html(content, status=200):
        return send(start, content, status, cookie=cookie)

    if not session["username"] and path not in ("/login","/signup","/demo"):
        return jump(start, "/login", cookie)
    if method == "GET" and session["username"]:
        if path in STATIC_FILES:
            filename,mime = STATIC_FILES[path]
            if filename.is_file():
                return static_response(environ,start,filename,mime)
            return send(start,"Missing asset",404,"text/plain")
        if path == "/api/v1":
            return json_response(start, {"app": "ErrandLab", "version": 1,
                                         "benchmarks": {k: f"/api/v1/benchmark/{k}" for k in routing.PRESETS},
                                         "research": routing.RESEARCH, "health": "/health"})
        if path.startswith("/api/v1/benchmark/"):
            key = path.rsplit("/", 1)[-1]
            if key not in routing.PRESETS:
                return json_response(start, {"error": "Unknown preset."}, 404)
            plan = routing.preset(key)
            return json_response(start, {"plan": asdict(plan), "analysis": routing.analyze(plan)})
        if path == "/benchmark.csv":
            return csv_response(start, "errandlab-benchmark", benchmark_rows())
    try:
        query = query_fields(environ.get("QUERY_STRING", ""))
    except ValueError:
        return html(ui.error_page(session, "400", "The request has too many fields."), 400)
    if method == "POST":
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
            if length < 0 or length > 16_384:
                return html(ui.error_page(session, "413", "The form is too large."), 413)
            if environ.get("CONTENT_TYPE", "").split(";", 1)[0] != "application/x-www-form-urlencoded":
                raise ValueError("Unsupported form type")
            form = query_fields(environ["wsgi.input"].read(length).decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return html(ui.error_page(session, "400", "The form could not be read."), 400)
        if not hmac.compare_digest(form.get("csrf", "").encode(), session["csrf"].encode()):
            return html(ui.error_page(session, "403", "This form expired. Open it again and retry."), 403)
        if path == "/demo" and not session["username"]:
            if store.throttle(environ.get("REMOTE_ADDR", "unknown")):
                return html(ui.account_page(session,error="Too many attempts. Try again in five minutes."),429)
            token, active = store.new_session("demo:"+secrets.token_hex(12),session)
            return jump(start,"/",session_cookie(token,active))
        if path == "/profile":
            try:
                store.update_profile(session["username"],form)
            except ValueError as error:
                return html(ui.page("Profile","Profile",workspace.profile_page(session,str(error)),session),422)
            return jump(start,"/profile?saved=1")
        if path == "/logout":
            token, guest = store.new_session(previous=session)
            return send(start,status=303,headers=[("Location","/login"),("Clear-Site-Data",'"cache"')],cookie=session_cookie(token,guest))
        if path in ("/login", "/signup"):
            return auth_post(start, environ, html, session, path, form)
        if path == "/lab":
            return plan_post(start, html, session, form)
        match = RUN_PATH.fullmatch(path)
        if match and match[2] == "save":
            report_id = match[1]
            route = f"/run/{report_id}"
            if not session["username"]:
                return jump(start, f"/login?next={route}")
            if store.save(session, report_id):
                return jump(start, route + "?saved=1")
    else:
        if path == "/":
            return html(ui.home(session))
        if path == "/sample":
            return html(ui.page("Sample route","Sample route",workspace.sample_page(),session))
        if path == "/settings":
            return html(ui.page("Settings","Settings",workspace.settings(),session))
        if path == "/profile":
            return html(ui.page("Profile","Profile",workspace.profile_page(session,"Profile saved." if query.get("saved") else ""),session))
        if path == "/lab":
            key = query.get("preset", "closing")
            if key == "blank":
                return html(ui.lab(session, key, 3, {"title": "My outing"}))
            return html(ui.lab(session, key if key in routing.PRESETS else "closing"))
        if path == "/evidence":
            return html(ui.evidence(session))
        if path in ("/login", "/signup"):
            target = allowed_next(query.get("next", ""))
            if session["username"]:
                return jump(start, target or "/", cookie)
            return html(ui.account_page(session, path == "/signup", target))
        if path == "/saved":
            if not session["username"]:
                return jump(start, "/login?next=/saved", cookie)
            rows = [
                {"id": r["id"], "title": r["title"],
                 "date": datetime.fromtimestamp(r["created"], timezone.utc).strftime("%d %b %Y")}
                for r in store.saved_reports(session)
            ]
            return html(ui.saved_page(session, rows))
        match = RUN_PATH.fullmatch(path)
        if match:
            report_id, action = match.groups()
            row = store.report(session, report_id)
            if row and action != "save":
                plan, data = unpack(row["payload"])
                if action == "edit":
                    return html(ui.lab(session, "custom", len(plan.stops), ui.fields_from_plan(plan)))
                if action == "csv":
                    return csv_response(start, "errandlab-route", comparison_rows(data))
                if action == "json":
                    return json_response(start, {"plan": asdict(plan), "analysis": data})
                policy = query.get("policy", "robust")
                if policy not in routing.POLICIES:
                    policy = "robust"
                return html(ui.result_page(session, row, (plan, data), policy, query.get("saved")))
    return html(ui.error_page(session, "404", "This page or route is unavailable."), 404)


def allowed_next(target):
    return target if NEXT_PATH.fullmatch(target) else ""


def auth_post(start, environ, html, session, path, form):
    signup = path == "/signup"
    target = allowed_next(form.get("next", ""))
    username, password = form.get("username", ""), form.get("password", "")
    if session["username"]:
        return jump(start, target or "/")
    if store.throttle(environ.get("REMOTE_ADDR", "unknown")):
        return html(ui.account_page(session, signup, target, "Too many attempts. Try again in five minutes.", username), 429)
    try:
        user = store.register(username, password) if signup else store.authenticate(username, password)
        if not user:
            raise ValueError("The username or password is incorrect.")
    except ValueError as error:
        return html(ui.account_page(session, signup, target, str(error), username), 422)
    token, active = store.new_session(user, session)
    return jump(start, target or "/", session_cookie(token, active, form.get("remember")=="yes"))


def plan_post(start, html, session, form):
    key = form.get("preset", "custom")
    key = key if key in (*routing.PRESETS, "blank", "custom") else "custom"
    try:
        count = int(form.get("count", ""))
        if not 2 <= count <= 6:
            raise ValueError
    except ValueError:
        return html(ui.lab(session, message="Use between two and six stops."), 422)
    action = form.get("action", "run")
    if action in {"add", "remove"}:
        return html(ui.lab(session, key, min(6, count+1) if action == "add" else max(2, count-1), form))
    try:
        plan = parse_plan(form, count)
        data = routing.analyze(plan)
    except ValueError as error:
        return html(ui.lab(session, key, count, form, str(error)), 422)
    report_id = store.create_report(session, plan.title, {"plan": asdict(plan), "analysis": data})
    return jump(start, f"/run/{report_id}")


def create_app():
    store.initialize()
    return application


def main():
    parser = argparse.ArgumentParser(description="Run ErrandLab on your computer.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8501")))
    opts = parser.parse_args()
    with make_server(opts.host, opts.port, create_app()) as server:
        print(f"ErrandLab is ready at http://{opts.host}:{opts.port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def launch():
    """Support existing Cloud deployments that still point at app.py."""
    if "streamlit" in sys.modules:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx(suppress_warning=True) is not None:
            from streamlit_app import main as streamlit_main

            streamlit_main()
            return
    main()


if __name__ == "__main__":
    launch()
