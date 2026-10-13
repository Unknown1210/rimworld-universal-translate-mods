import logging
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rwtranslate import activity  # noqa: E402


class Activity(unittest.TestCase):
    def setUp(self):
        activity.clear()

    def test_entries_keep_key_arguments_and_pairs(self):
        e = activity.emit("game", "log_game_batch", {"n": 1}, detail="free text", pairs=[("a", "b"), ("c", "d")])
        self.assertEqual(activity.snapshot(), [e])
        self.assertEqual(e.detail_text(), "free text\na\n   -> b\nc\n   -> d")
        self.assertEqual((e.kind, e.level, e.key), ("game", "info", "log_game_batch"))

    def test_listeners_are_told_and_a_broken_one_does_not_break_anything(self):
        seen = []
        bad = lambda e: 1 / 0  # noqa: E731
        activity.subscribe(bad)
        activity.subscribe(seen.append)
        try:
            activity.emit("bulk", "log_bulk_finished", {"total": 1})
        finally:
            activity.unsubscribe(bad)
            activity.unsubscribe(seen.append)
        self.assertEqual(len(seen), 1)
        activity.emit("bulk", "log_bulk_finished", {"total": 2})
        self.assertEqual(len(seen), 1, "unsubscribed listeners hear nothing")

    def test_only_the_most_recent_entries_are_kept(self):
        for i in range(activity.MAX_ENTRIES + 25):
            activity.emit("system", None, {"text": str(i)})
        snap = activity.snapshot()
        self.assertEqual(len(snap), activity.MAX_ENTRIES)
        self.assertEqual(snap[-1].args["text"], str(activity.MAX_ENTRIES + 24))

    def test_warnings_and_errors_of_other_loggers_show_up_with_the_traceback(self):
        activity.install_log_handler()
        lg = logging.getLogger("rwt.test-activity")
        lg.setLevel(logging.DEBUG)
        lg.info("just information")
        lg.warning("careful %s", "now")
        try:
            raise ValueError("boom")
        except ValueError:
            lg.error("it broke", exc_info=True)
        got = [e for e in activity.snapshot() if e.kind == "system"]
        self.assertEqual([(e.level, e.args["text"]) for e in got], [("warning", "[rwt.test-activity] careful now"), ("error", "[rwt.test-activity] it broke")])
        self.assertIn("ValueError: boom", got[1].detail)

    def test_every_message_key_exists_in_both_languages(self):
        from rwtranslate import i18n
        import re
        src = open(os.path.join(os.path.dirname(__file__), "..", "rwtranslate", "i18n.py"), encoding="utf-8").read()
        used = set()
        for f in ("server.py", "models.py", "bulk.py", "updater.py", "gui.py"):
            used |= set(re.findall(r'"(log_[a-z_]+)"', open(os.path.join(os.path.dirname(__file__), "..", "rwtranslate", f), encoding="utf-8").read()))
        for lang in ("pt", "en"):
            missing = sorted(k for k in used if k not in i18n.TEXT[lang] and not k.startswith(("log_kind_", "log_filter_", "log_lvl_")))
            self.assertEqual(missing, [], lang)


if __name__ == "__main__":
    unittest.main()
