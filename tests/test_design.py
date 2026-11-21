"""Accessibility and interaction contracts for the responsive Python interface."""
from html.parser import HTMLParser
import unittest
from xml.etree import ElementTree

import app
import artwork
import layout
import routing
import ui
import store
from tempfile import TemporaryDirectory
from pathlib import Path


SESSION = {"csrf": "test", "username": "tester"}


class PageElements(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.elements = []
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def matching(self, tag, **attributes):
        return [
            node for name, node in self.elements if name == tag and
            all(node.get(key) == value for key, value in attributes.items())
        ]


class DesignTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.addCleanup(setattr,store,"DATA",store.DATA)
        store.DATA = Path(temporary.name)/"design.sqlite"
        store.initialize()

    def test_empty_account_offers_a_working_next_action(self):
        empty = PageElements(ui.saved_page(SESSION, []))
        self.assertEqual(len(empty.matching("svg", **{"class": "mascot empty"})), 1)
        self.assertTrue(empty.matching("a", href="/lab"))
        full = PageElements(ui.saved_page(SESSION, [{"id": "abc", "title": "Market", "date": "Today"}]))
        self.assertFalse(full.matching("svg", **{"class": "mascot empty"}))
        self.assertTrue(full.matching("a", href="/run/abc"))

    def test_disclosures_expose_editing_errors_and_missing_stops(self):
        normal = PageElements(ui.lab(SESSION))
        stops = normal.matching("details", **{"class": "stopeditor"})
        self.assertEqual(len(stops), 4)
        self.assertEqual(sum("open" in stop for stop in stops), 1)
        failed = PageElements(ui.lab(SESSION, message="Fix an opening time."))
        self.assertTrue(all("open" in stop for stop in failed.matching("details", **{"class": "stopeditor"})))
        blank = PageElements(ui.lab(SESSION, "blank", 2, {}))
        self.assertTrue(all("open" in stop for stop in blank.matching("details", **{"class": "stopeditor"})))
        labels = {node["for"] for node in normal.matching("label")}
        controls = {node["id"] for tag, node in normal.elements if tag in ("input", "select", "textarea") and "id" in node}
        self.assertEqual(labels, controls)

    def test_pending_feedback_is_hidden_on_initial_render(self):
        fields = PageElements(ui.lab(SESSION))
        progress, = fields.matching("div", id="progress")
        self.assertIn("hidden", progress)
        self.assertEqual(progress["role"], "status")
        self.assertTrue(fields.matching("svg", **{"class": "mascot loading"}))
        self.assertTrue(fields.matching("script", src="/motion.js"))

    def test_plot_keeps_planned_numbers_when_a_stop_is_skipped(self):
        plan = routing.preset("closing")
        order = [1, 2, 3, 0]
        traversed = [1, 3, 0]
        svg = ElementTree.fromstring(artwork.route_plot(plan, order, visited=traversed))
        self.assertEqual(svg.attrib["viewBox"], "0 0 640 292")
        self.assertEqual(svg.attrib["aria-label"], "Home → Parcel counter → Tailor pickup → Grocery → Home")
        markers = {group.findtext("title"): group.findtext("text") for group in svg.findall("g") if group.find("title") is not None}
        self.assertEqual(markers["Tailor pickup"], "3")
        self.assertEqual(markers["Grocery"], "4")

    def test_spring_settles_and_motion_respects_user_preferences(self):
        easing = artwork.spring_curve()
        samples = [float(n) for n in easing.removeprefix("linear(").removesuffix(")").split(",")]
        self.assertEqual(samples[0], 0)
        self.assertGreater(max(samples), 1)
        self.assertEqual(samples[-1], 1)
        motion = layout.motion_styles()
        self.assertTrue(motion.startswith("@media(prefers-reduced-motion:no-preference){"))
        self.assertIn("details[open]", motion)
        for width in (880, 680, 380):
            self.assertIn(f"@media(max-width:{width}px)", app.CSS.decode())

    def test_benchmark_graph_matches_numeric_results(self):
        plan = routing.preset("relaxed")
        plot = artwork.benchmark_figure([(plan.title, routing.analyze(plan)["policies"])])
        self.assertEqual(plot.count("100.0%"), 3)
        self.assertIn("Relaxed Saturday", plot)
        self.assertIn('class="robust" style="width:100.000%"', plot)
