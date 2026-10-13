import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["RWTRANSLATE_HOME"] = tempfile.mkdtemp()

from rwtranslate import diagnostics, logsetup, models, server  # noqa: E402
from rwtranslate.engine import set_engine  # noqa: E402
from rwtranslate.paths import logs_dir  # noqa: E402


class Boom:
    def translate_batch(self, texts):
        raise RuntimeError("kaboom inside engine")


class LoggingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logsetup.setup(debug=True)
        set_engine("en", "bm", Boom())
        cls.httpd = server.serve(0)
        cls.port = cls.httpd.server_address[1]
        cls.token = server.load_or_create_token()
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def post(self, body, rid):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/translate", data=json.dumps(body).encode(),
                                     headers={"X-Token": self.token, "X-Request-Id": rid})
        try:
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def logtext(self):
        for h in logsetup.logging.getLogger("rwt").handlers:
            h.flush()
        return (logs_dir() / "helper.log").read_text(encoding="utf-8")

    def test_500_has_request_id_and_traceback_in_log(self):
        code, j = self.post({"target": "bm", "texts": ["Hello there"]}, "req-abc123")
        self.assertEqual(code, 500)
        self.assertEqual(j["request_id"], "req-abc123")
        self.assertEqual(j["type"], "RuntimeError")
        log = self.logtext()
        self.assertIn("[req-abc123] UNHANDLED POST /translate", log)
        self.assertIn("kaboom inside engine", log)
        self.assertIn("Traceback", log)

    def test_thread_crash_writes_report(self):
        def die():
            raise ValueError("thread died")
        t = threading.Thread(target=die, name="worker-x")
        t.start()
        t.join()
        reports = list(logs_dir().glob("crash-*.txt"))
        self.assertTrue(reports)
        text = reports[-1].read_text(encoding="utf-8")
        for needle in ("thread died", "worker-x", "--- environment ---", "--- last log lines ---"):
            self.assertIn(needle, text)

    def test_diagnostics_bundle_has_logs_but_no_token(self):
        z = diagnostics.make_bundle()
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
            blob = b"".join(zf.read(n) for n in names)
        self.assertIn("environment.json", names)
        self.assertTrue(any(n.startswith("logs/") for n in names))
        self.assertNotIn(self.token.encode(), blob)

    def test_failed_install_leaves_no_partial_model(self):
        index = [{"from_code": "en", "to_code": "qq", "package_version": "1.0",
                  "links": ["http://127.0.0.1:9/nope.argosmodel"]}]
        with self.assertRaises(Exception):
            models.install("en", "qq", progress=lambda m: None, index=index)
        self.assertFalse((models.models_dir() / "en_qq").exists())
        self.assertIn("model install FAILED en->qq", self.logtext())

    def test_support_answers(self):
        # language codes used only by this test, so models "installed" by other tests cannot interfere
        mk = lambda a, b: {"from_code": a, "to_code": b, "package_version": "1.0", "links": ["x"]}
        idx = [mk("qz", "en"), mk("en", "qa"), mk("en", "qz"), mk("qa", "en"), mk("en", "qj")]       # no qj->en
        direct = models.support("en", "qa", idx)
        self.assertEqual((direct["supported"], direct["installed"], direct["download"]), (True, False, ["en>qa"]))
        pivot = models.support("qz", "qa", idx)
        self.assertEqual((pivot["supported"], pivot["steps"], pivot["download"]), (True, ["qz>en", "en>qa"], ["qz>en", "en>qa"]))
        no = models.support("qj", "qa", idx)
        self.assertEqual((no["known"], no["supported"]), (True, False))                            # qj->en is missing: NO support
        self.assertTrue(models.support("qa", "qa", idx)["supported"])
        for a_, b_ in (("qz", "en"), ("en", "qa")):                                                # installed beats the index
            d = models.pair_dir(a_, b_); d.mkdir(parents=True, exist_ok=True); (d / "ok").write_text("1")
        got = models.support("qz", "qa", [])
        self.assertEqual((got["installed"], got["supported"], got["download"]), (True, True, []))

    def test_model_plans_direct_pivot_and_missing(self):
        mk = lambda a, b: {"from_code": a, "to_code": b, "package_version": "1.0", "links": ["x"]}
        idx = [mk("zh", "en"), mk("en", "pt"), mk("en", "zh"), mk("pt", "en"), mk("en", "es"), mk("ru", "en")]
        self.assertEqual(models.plan("en", "pt", idx), [("en", "pt")])             # direct
        self.assertEqual(models.plan("zh", "pt", idx), [("zh", "en"), ("en", "pt")])  # pivot through English
        self.assertEqual(models.plan("pt", "en", idx), [("pt", "en")])
        self.assertEqual(models.plan("pt", "pt", idx), [])
        with self.assertRaises(RuntimeError):
            models.plan("ru", "es", idx[:-1] + [mk("xx", "en")])                  # ru->en missing: no path
        # offline plan uses only what is installed
        for a, b in (("zh", "en"), ("en", "pt")):
            d = models.pair_dir(a, b); d.mkdir(parents=True, exist_ok=True); (d / "ok").write_text("1")
        self.assertEqual(models.installed_plan("zh", "pt"), [("zh", "en"), ("en", "pt")])
        self.assertIsNone(models.installed_plan("pt", "zh"))
        self.assertIn("zh>en", models.installed_pairs())


if __name__ == "__main__":
    unittest.main()
