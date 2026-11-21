"""Authentication, ownership, asset integration and visual-system checks."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import app
import atmosphere
import store
from test_errandlab import WebClient


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(setattr, store, "DATA",store.DATA)
        store.DATA = Path(temp.name)/"auth.sqlite"
        self.web = WebClient(app.create_app())

    def enter(self):
        self.web.request("/login")
        status,headers,_ = self.web.post("/demo")
        self.assertEqual(status,303)
        self.assertNotIn("Max-Age",headers["Set-Cookie"])
        self.web.request("/profile")

    def test_initial_gate_blocks_all_private_modules(self):
        for path in ("/","/sample","/saved","/settings","/profile","/lab","/evidence","/workspace.js",
                     "/models/sky.glb","/media/sample-route.webm","/studio.js","/models/route.json","/vendor/three/three.module.js","/benchmark.csv","/api/v1"):
            with self.subTest(path=path):
                self.assertEqual(self.web.request(path)[1]["Location"],"/login")
        html = self.web.request("/login")[2]
        self.assertIn("Demo quick sign-in",html)
        for element in ('id="capi-dialog"','class="rail"','class="utilities"','/workspace.js'):
            self.assertNotIn(element,html)

    def test_demo_identity_profile_preferences_and_logout(self):
        self.enter()
        self.assertEqual(self.web.post("/profile",display="A & B",avatar="Leaf",role="Student",bio="Researcher")[0],303)
        self.assertIn("A &amp; B",self.web.request("/profile")[2])
        self.assertIn("Save and test key",self.web.request("/settings")[2])
        self.assertIn("West 112th Street",self.web.request("/sample")[2])
        self.assertEqual(self.web.post("/logout")[1]["Location"],"/login")
        self.enter()
        self.assertNotIn("A &amp; B",self.web.request("/profile")[2])

    def test_email_validation_and_duplicate(self):
        self.web.request("/signup")
        fields=dict(username="invalid",password="long enough passphrase")
        self.assertEqual(self.web.post("/signup",**fields)[0],422)
        fields["username"]="student@example.org"
        self.assertEqual(self.web.post("/signup",**fields)[0],303)
        second=WebClient(app.application);second.request("/signup")
        self.assertEqual(second.post("/signup",**fields)[0],422)

    def test_palette_text_contrast(self):
        def luminance(hexvalue):
            channels=[int(hexvalue[i:i+2],16)/255 for i in (1,3,5)]
            scaled=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
            return sum(a*b for a,b in zip(scaled,(.2126,.7152,.0722)))
        for theme in (atmosphere.DARK,atmosphere.LIGHT):
            for fg,bg in [("ink","paper"),("tone","bg"),("accent","paper"),("ink","control"),
                          ("tone","select"),("onprimary","primary"),("errorink","errorbg")]:
                a,b=sorted([luminance(theme[fg]),luminance(theme[bg])])
                self.assertGreaterEqual((b+.05)/(a+.05),4.5,(fg,bg))

    def test_video_range_responses(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"unit.mp4";path.write_bytes(b"0123456789")
            def capture(status,headers):
                self.status=status;self.headers=dict(headers)
            for request,expected in (("bytes=3-5",b"345"),("bytes=-2",b"89"),("bytes=8-",b"89")):
                result=app.static_response({"HTTP_RANGE":request},capture,path,"video/mp4")
                self.assertEqual(result,[expected]);self.assertTrue(self.status.startswith("206"))
            app.static_response({"HTTP_RANGE":"bytes=12-"},capture,path,"video/mp4")
            self.assertTrue(self.status.startswith("416"))
