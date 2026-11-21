"""Model and browser-contract acceptance tests using the real WSGI entry point."""
from dataclasses import replace
from http.cookies import SimpleCookie
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults
from wsgiref.validate import validator
import json
import re
import unittest

import app
import routing
import store
import ui


class WebClient:
    def __init__(self, wsgi):
        self.wsgi = validator(wsgi)
        self.cookie = ""
        self.csrf = ""

    def request(self, path, form=None, *, method=None):
        path, _, query = path.partition("?")
        payload = urlencode(form or {}).encode()
        env = {}
        setup_testing_defaults(env)
        env.update({
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "REQUEST_METHOD": method or ("POST" if form is not None else "GET"),
            "CONTENT_LENGTH": str(len(payload)), "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "HTTP_COOKIE": self.cookie, "wsgi.input": BytesIO(payload), "REMOTE_ADDR": "127.0.0.1",
        })
        response = {}

        def start(status, headers, exc_info=None):
            response.update(status=int(status.split()[0]), headers=dict(headers))
            return lambda value: None

        result = self.wsgi(env, start)
        try:
            text = b"".join(result).decode()
        finally:
            result.close()
        headers = response["headers"]
        if "Set-Cookie" in headers:
            self.cookie = "errandlab=" + SimpleCookie(headers["Set-Cookie"])["errandlab"].value
        token = re.search(r'name="csrf" value="([^"]+)"', text)
        if token:
            self.csrf = token[1]
        return response["status"], headers, text

    def post(self, path, **fields):
        return self.request(path, {"csrf": self.csrf, **fields})

    def form(self, key="closing", **fields):
        plan = routing.preset(key)
        return self.post("/lab", count=len(plan.stops), preset=key, **(ui.fields_from_plan(plan) | fields))


class RoutingTest(unittest.TestCase):
    def test_opening_wait_completion_and_return(self):
        plan = routing.Plan("Timing", 0, 22, "Low", (
            routing.Stop("Parcel", 0, 0, 7, 14, 3, 2),
            routing.Stop("Bakery", 0, 0, 0, 21, 4),
        ))
        leg = ((0, 5, 5), (5, 0, 3), (5, 3, 0))
        outcome = routing.simulate(plan, (0, 1), leg, trace=True)
        self.assertEqual((outcome.points, outcome.completed, outcome.elapsed), (3, 2, 22))
        self.assertEqual(outcome.visits[0].wait, 2)
        self.assertTrue(routing.success(outcome, 2))
        late = routing.simulate(replace(plan, deadline=21), (0, 1), leg)
        self.assertFalse(late.on_time)

    def test_late_arrival_still_costs_travel(self):
        plan = routing.Plan("Timing", 0, 22, "Low", (
            routing.Stop("Parcel", 0, 0, 0, 6, 3),
            routing.Stop("Bakery", 0, 0, 0, 21, 4),
        ))
        leg = ((0, 5, 5), (5, 0, 3), (5, 3, 0))
        outcome = routing.simulate(plan, (0, 1), leg, trace=True)
        self.assertFalse(outcome.visits[0].completed)
        self.assertEqual((outcome.completed, outcome.driving, outcome.elapsed), (1, 13, 17))

    def test_expired_stop_is_skipped_before_leaving(self):
        plan = routing.Plan("Timing", 0, 30, "Low", (
            routing.Stop("Expired", 0, 0, -20, -1, 3),
            routing.Stop("Open", 0, 0, 0, 21, 4),
        ))
        leg = ((0, 5, 5), (5, 0, 3), (5, 3, 0))
        outcome = routing.simulate(plan, (0, 1), leg, trace=True)
        self.assertEqual([v.index for v in outcome.visits], [1])
        self.assertEqual(outcome.driving, 10)

    def test_six_stops_and_720_orders(self):
        base = routing.preset("relaxed")
        plan = replace(base, stops=base.stops + (
            routing.Stop("Florist", .2, -.1, 0, 160, 4),
            routing.Stop("Café", .3, .2, 0, 160, 5),
        ))
        report = routing.analyze(plan)
        self.assertEqual(report["candidate_orders"], 720)
        for value in report["policies"].values():
            self.assertEqual(sorted(value["order"]), list(range(6)))
            self.assertLessEqual(value["median_elapsed"], value["p90_elapsed"])

    def test_seeded_comparison_and_null_case(self):
        report = routing.analyze(routing.preset("closing"))
        self.assertEqual(report["test_days"], 600)
        self.assertGreater(report["contrasts"]["nearest"]["interval"][0], 0.30)
        self.assertGreater(report["contrasts"]["nominal"]["interval"][0], 0.30)
        self.assertEqual(routing.analyze(routing.preset("relaxed"))["contrasts"]["nearest"]["lift"], 0)
        routing.analyze.cache_clear()
        self.assertEqual(report, routing.analyze(routing.preset("closing")))

    def test_reject_invalid_numeric_and_time_data(self):
        plan = routing.preset("opening")
        for invalid in (float("nan"), float("inf"), 21):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                routing.validate(replace(plan, stops=(replace(plan.stops[0], x=invalid), *plan.stops[1:])))
        with self.assertRaises(ValueError):
            app.time_minutes("12:72")


class WebTest(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        old = store.DATA
        self.addCleanup(setattr, store, "DATA", old)
        store.DATA = Path(tmp.name) / "test.sqlite"
        self.server = app.create_app()
        self.client = WebClient(self.server)

    def enter_demo(self, client=None):
        client = client or self.client
        client.request("/login")
        response = client.post("/demo")
        self.assertEqual(response[0], 303)
        client.request("/")

    def test_overview_evidence_and_json_api(self):
        self.enter_demo()
        self.assertIn("Your outing atlas", self.client.request("/")[2])
        self.assertIn("Staggered openings", self.client.request("/evidence")[2])
        self.assertEqual(self.client.request("/style.css")[1]["Content-Type"], "text/css; charset=utf-8")
        status, _, body = self.client.request("/api/v1/benchmark/closing")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["analysis"]["test_days"], 600)
        self.assertEqual(self.client.request("/api/v1/benchmark/typo")[0], 404)
        self.assertEqual(self.client.request("/health")[2], '{"status": "ok"}')
        self.assertIn("lift_vs_fixed", self.client.request("/benchmark.csv")[2])

    def test_demo_plan_results_switch_edit_and_exports(self):
        self.enter_demo()
        status, _, page = self.client.request("/lab")
        self.assertEqual(status, 200)
        self.assertIn("Parcel counter", page)
        status, headers, _ = self.client.form()
        self.assertEqual(status, 303)
        route = headers["Location"]
        status, _, body = self.client.request(route)
        self.assertEqual(status, 200)
        self.assertIn("Compare route strategies", body)
        self.assertIn("Save route", body)
        self.assertIn('href="' + route + '?policy=nearest#timeline" aria-current=page',
                      self.client.request(route + "?policy=nearest")[2])
        self.assertIn("Parcel counter", self.client.request(route + "/edit")[2])
        self.assertIn("median_outing_minutes", self.client.request(route + "/csv")[2])
        self.assertEqual(json.loads(self.client.request(route + "/json")[2])["plan"]["title"], "Closing time")
        self.assertEqual(WebClient(self.server).request(route)[1]["Location"], "/login")

    def test_bad_input_is_recoverable_and_output_is_escaped(self):
        self.enter_demo()
        self.client.request("/lab")
        status, _, body = self.client.form(x1="nan", title="<script>oops</script>")
        self.assertEqual(status, 422)
        self.assertIn("Each coordinate", body)
        self.assertIn("&lt;script&gt;oops&lt;/script&gt;", body)
        self.assertNotIn("<script>oops</script>", body)
        self.assertEqual(self.client.form(action="add")[2].count('class="stop"'), 5)
        self.assertEqual(self.client.form(action="remove")[2].count('class="stop"'), 3)
        self.assertEqual(self.client.request("/lab?preset=blank")[2].count('class="stop"'), 3)

    def test_signup_save_logout_login_and_isolation(self):
        self.client.request("/signup")
        before = self.client.cookie
        status, headers, _ = self.client.post("/signup", username="tester@example.com", password="demo-only passphrase", remember="yes")
        self.assertEqual((status, headers["Location"]), (303, "/"))
        self.assertNotEqual(self.client.cookie,before)
        self.assertIn("Max-Age=604800",headers["Set-Cookie"])
        self.client.request("/lab")
        route=self.client.form()[1]["Location"]
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("Save route", self.client.request(route)[2])
        self.assertEqual(self.client.post(route + "/save")[0], 303)
        self.assertIn("Closing time", self.client.request("/saved")[2])
        self.assertEqual(self.client.post("/logout")[0], 303)
        self.assertEqual(self.client.request(route)[1]["Location"], "/login")
        self.client.request("/login")
        self.assertEqual(self.client.post("/login", username="tester@example.com", password="wrong")[0], 422)
        self.assertEqual(self.client.post("/login", username="tester@example.com", password="demo-only passphrase")[0], 303)
        self.assertIn("Closing time", self.client.request("/saved")[2])
        other = WebClient(self.server)
        other.request("/signup")
        other.post("/signup", username="other@example.com", password="other-only passphrase")
        self.assertEqual(other.request(route)[0], 404)
        other.request("/profile")
        self.assertEqual(other.post(route + "/save")[0], 404)

    def test_csrf_redirect_and_method_handling(self):
        self.client.request("/login")
        self.assertEqual(self.client.request("/login", {"csrf": "wrong"})[0], 403)
        self.assertEqual(self.client.post("/login", csrf="é")[0], 403)
        status, headers, _ = self.client.post("/signup", username="tester@example.com", password="test-only passphrase", next="//example.org")
        self.assertEqual((status, headers["Location"]), (303, "/"))
        self.assertEqual(self.client.request("/login", method="PUT")[0], 405)


if __name__ == "__main__":
    unittest.main()
