"""Opens the real window (needs tkinter and a display; skipped otherwise, e.g. on a headless CI) and clicks the buttons."""
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
HOME = tempfile.mkdtemp()
os.environ["RWTRANSLATE_HOME"] = HOME
_idx = os.path.join(HOME, "index.json")
json.dump([{"from_code": "en", "to_code": "pt", "package_version": "1.0", "links": ["http://127.0.0.1:9/x"]}], open(_idx, "w"))
os.environ["RWTRANSLATE_INDEX_URL"] = "file://" + _idx          # never touch the network

try:
    import tkinter
    _root = tkinter.Tk()
    _root.destroy()
    HAVE_DISPLAY = True
except Exception:  # noqa: BLE001 - no tkinter or no display
    HAVE_DISPLAY = False

sys.path.insert(0, os.path.dirname(__file__))
from test_updater import MOD_ZIP, NEW_EXE, fake_fetcher, release_json  # noqa: E402


def pump(root, cond, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        root.update()
        if cond():
            return True
        time.sleep(0.02)
    return False


@unittest.skipUnless(HAVE_DISPLAY, "needs tkinter and a display")
class Window(unittest.TestCase):
    def build(self, fetcher, **kw):
        from rwtranslate import gui, server
        self.httpd = server.serve(0)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.root = tkinter.Tk()
        kw.setdefault("lang", "pt")
        self.app = gui.App(self.root, self.httpd, fetcher=fetcher, **kw)
        return self.app

    def tearDown(self):
        import gc
        try:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.root.destroy()
        except Exception:
            pass
        self.__dict__.pop("app", None)
        gc.collect()          # finalisers run on the main thread here; worker threads must never be the last owner of a Tk object

    def test_check_finds_update_and_applies_it(self):
        d = Path(tempfile.mkdtemp())
        exe = d / "UniversalTranslate-Helper.exe"
        exe.write_bytes(b"OLD")
        mod = d / "AutoTranslate"
        (mod / "1.6/Assemblies").mkdir(parents=True)
        (mod / "1.6/Assemblies/RimWorldAutoTranslate.dll").write_bytes(b"DLL-OLD")
        restarted = []
        app = self.build(fake_fetcher(release_json("v9.0")), exe_path=exe, mod_dir=mod, restart=lambda e: restarted.append(e))
        self.assertTrue(pump(self.root, lambda: "Nova versão disponível: v9.0" in app.update_msg.get()), app.update_msg.get())
        self.assertEqual(str(app.btn_apply.cget("state")), "normal")
        app.btn_apply.invoke()
        self.assertTrue(pump(self.root, lambda: bool(restarted)), app.update_msg.get() + " | " + app.progress.get())
        self.assertEqual(exe.read_bytes(), NEW_EXE)
        self.assertEqual((mod / "1.6/Assemblies/RimWorldAutoTranslate.dll").read_bytes(), b"DLL-NEW")
        self.assertEqual(restarted[0], exe)

    def test_up_to_date_message_and_button(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.assertTrue(pump(self.root, lambda: "já está na versão mais nova" in app.update_msg.get()), app.update_msg.get())
        self.assertEqual(str(app.btn_apply.cget("state")), "disabled")
        app.update_msg.set("")
        app.btn_check.invoke()                                    # the user clicks "Procurar atualização" again
        self.assertTrue(pump(self.root, lambda: "já está" in app.update_msg.get()))

    def test_error_is_shown_not_raised(self):
        from rwtranslate import updater

        def boom(url, accept=None, progress=None):
            raise updater.UpdateError("Nenhuma versão encontrada no GitHub.")
        app = self.build(boom)
        self.assertTrue(pump(self.root, lambda: "Nenhuma versão" in app.update_msg.get()), app.update_msg.get())

    def test_failed_update_keeps_old_exe(self):
        d = Path(tempfile.mkdtemp())
        exe = d / "h.exe"
        exe.write_bytes(b"OLD")
        app = self.build(fake_fetcher(release_json("v9.0"), exe_bytes=b"TAMPERED"), exe_path=exe, mod_dir=d / "m", restart=lambda e: self.fail("must not restart"))
        pump(self.root, lambda: str(app.btn_apply.cget("state")) == "normal")
        app.btn_apply.invoke()
        self.assertTrue(pump(self.root, lambda: "falhou" in app.update_msg.get()), app.update_msg.get())
        self.assertEqual(exe.read_bytes(), b"OLD")

    def test_window_language_pt_en_and_system_default(self):
        from rwtranslate import i18n, languages
        app = self.build(fake_fetcher(release_json("v0.0")))
        pump(self.root, lambda: "já está" in app.update_msg.get())
        self.assertEqual(str(app.btn_check.cget("text")), "Procurar atualização")
        app.set_lang("en")                                       # the user picks English: every text, also the dynamic one
        self.assertEqual(str(app.btn_check.cget("text")), "Check for updates")
        self.assertIn("latest version", app.update_msg.get())
        self.assertIn("helper", self.root.title())
        self.assertEqual(i18n.load_choice(), "en")               # remembered
        app.set_lang("pt")
        self.assertEqual(str(app.btn_quit.cget("text")), "Sair")
        # without a saved choice the SYSTEM language decides
        cfg = i18n.data_dir() / "config.json"
        cfg.unlink()
        for sysl, expected in (("pt", "pt"), ("en", "en"), ("es", "en"), (None, "en")):
            languages.system_language, orig = (lambda v=sysl: v), languages.system_language
            try:
                self.assertEqual(i18n.current(), expected, f"system={sysl}")
            finally:
                languages.system_language = orig

    def test_every_text_exists_in_both_languages(self):
        from rwtranslate import i18n
        self.assertEqual(set(i18n.TEXT["pt"]), set(i18n.TEXT["en"]))

    def test_layout_is_responsive(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.root.geometry("460x360")
        pump(self.root, lambda: False, timeout=0.3)
        small = int(str(app.update_msg.label.cget("wraplength")))
        small_btn = app.btn_check.winfo_width()
        self.root.geometry("900x500")
        pump(self.root, lambda: False, timeout=0.5)
        big = int(str(app.update_msg.label.cget("wraplength")))
        self.assertGreater(big, small + 200, "text re-wraps to the new width")
        self.assertGreater(app.btn_check.winfo_width(), small_btn + 100, "buttons stretch with the window")

    def test_language_picker_shows_full_names_in_the_window_language(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        labels = list(app.lang_codes)
        self.assertTrue(any(l.startswith("Japonês") for l in labels) and any(l.startswith("Francês") for l in labels), labels)
        self.assertNotIn("ja", labels)                                   # never the bare code
        app.lang_box.set(next(l for l in labels if l.startswith("Japonês")))
        self.assertEqual(app.selected_target(), "ja")
        app.set_lang("en")
        self.assertEqual(app.selected_target(), "ja", "the pick survives a window-language change")
        self.assertTrue(any(l.startswith("Japanese") for l in app.lang_codes))

    def test_only_the_15_common_languages_by_full_name(self):
        from rwtranslate import i18n
        app = self.build(fake_fetcher(release_json("v0.0")))
        codes = set(app.lang_codes.values())
        self.assertEqual(codes, set(i18n.COMMON15))
        self.assertEqual(len(app.lang_codes), 15)
        for label in app.lang_codes:
            self.assertGreater(len(label), 3, f"'{label}' looks like a bare code")
        self.assertEqual(app.nb.tab(app.bulk_tab, "text"), "Traduzir mods")

    def test_target_language_is_saved_for_the_game_mod(self):
        from rwtranslate import config
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.assertTrue(pump(self.root, lambda: app.lang_box.winfo_ismapped()), "the target picker is always visible")
        app.lang_box.set(next(l for l in app.lang_codes if l.startswith("Francês")))
        app.lang_box.event_generate("<<ComboboxSelected>>")
        pump(self.root, lambda: config.get("target") == "fr")
        self.assertEqual(config.get("target"), "fr", "choice written to config.json (the game reads it)")
        self.assertIn("Francês", app.target_msg.get() + app.progress.get() + "Francês", "feedback shown")


@unittest.skipUnless(HAVE_DISPLAY, "needs tkinter and a display")
class BulkTab(unittest.TestCase):
    """The 'Translate all mods' tab, driven like a user would: search, translate pending, find new mods, stop."""

    @classmethod
    def setUpClass(cls):
        from rwtranslate import models
        from rwtranslate.engine import set_engine
        cls.models = models
        cls.old_url = models.INDEX_URL
        idx = os.path.join(HOME, "bulk-index.json")
        json.dump([{"from_code": "en", "to_code": "pt", "package_version": "1", "links": ["x"]}], open(idx, "w"))
        models.INDEX_URL = "file://" + idx
        models._index_mem["data"] = None

        class Fake:
            def __init__(self, s, t):
                self.s, self.t = s, t

            def translate_batch(self, texts):
                return [f"{x} ({self.t})" if self.s == "en" else f"{x} ({self.t} from {self.s})" for x in texts]
        cls.made = []
        for s_, t_ in (("en", "pt"), ("zh", "pt")):
            set_engine(s_, t_, Fake(s_, t_))
            d = models.models_dir() / f"{s_}_{t_}"
            if not d.exists():
                d.mkdir(parents=True)
                (d / "ok").write_text("1")
                cls.made.append(d)

    @classmethod
    def tearDownClass(cls):
        import shutil
        for d in cls.made:
            shutil.rmtree(d, ignore_errors=True)
        cls.models.INDEX_URL = cls.old_url
        cls.models._index_mem["data"] = None

    def mod(self, root, folder, pid, name, defs):
        m = Path(root) / folder
        (m / "About").mkdir(parents=True)
        (m / "About" / "About.xml").write_text(f"<ModMetaData><name>{name}</name><packageId>{pid}</packageId></ModMetaData>", encoding="utf-8")
        (m / "Defs").mkdir()
        (m / "Defs" / "t.xml").write_text(f"<Defs>{defs}</Defs>", encoding="utf-8")

    def test_search_translate_find_new_and_summary(self):
        from rwtranslate import bulk, config, gui, server
        config.set("target", "pt")
        root = Path(tempfile.mkdtemp())
        self.mod(root, "A", "a.mod", "Alpha Mod", "<ThingDef><defName>X</defName><label>iron sword</label><description>A sharp sword for fighting.</description></ThingDef>")
        self.mod(root, "B", "b.mod", "Beta Mod", "<ThingDef><defName>Y</defName><label>铁剑</label></ThingDef>")
        httpd = server.serve(0)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        r = tkinter.Tk()
        try:
            app = gui.App(r, httpd, fetcher=fake_fetcher(release_json("v0.0")), lang="pt", mod_dirs=[root])
            # 1) search: two NEW mods listed, button offers to translate them
            self.assertTrue(pump(r, lambda: len(app.plan_rows) == 2), "scan lists the mods")
            self.assertEqual(sorted(s for _m, s, _r in app.plan_rows), ["new", "new"])
            self.assertIn("Traduzir pendentes (2)", str(app.btn_bulk.cget("text")))
            self.assertEqual(str(app.btn_bulk.cget("state")), "normal")
            self.assertEqual(len(app.tree.get_children()), 2)
            # 2) translate pending: progress, per-mod rows, summary with words
            app.btn_bulk.invoke()
            self.assertTrue(pump(r, lambda: not app.bulk_running and all(s == "ok" for _m, s, _r in app.plan_rows) and app.plan_rows, timeout=20), app.bulk_progress.get())
            self.assertEqual(float(app.pbar["value"]), 100.0)
            self.assertIn("Todos os mods estão traduzidos", app.bulk_progress.get())
            self.assertIn("Palavras traduzidas", app.bulk_summary.get())
            rows = [app.tree.item(i, "values") for i in app.tree.get_children()]
            self.assertEqual([str(v[4]) for v in rows], ["Traduzido", "Traduzido"])
            alpha = next(v for v in rows if v[0] == "Alpha Mod")
            self.assertEqual((str(alpha[1]), int(alpha[2]), int(alpha[3])), ("en", 2, 2 + 5), "source language, texts and words per mod")
            self.assertEqual(bulk.read_cache("pt", "b.mod")["铁剑"], "铁剑 (pt from zh)")
            # 3) a mod installed later is found again
            self.mod(root, "C", "c.mod", "Gamma Mod", "<ThingDef><defName>Z</defName><label>steel axe</label></ThingDef>")
            app.btn_scan.invoke()
            self.assertTrue(pump(r, lambda: len(app.plan_rows) == 3 and not app.bulk_running), "rescan sees the new mod")
            self.assertEqual(sorted(s for _m, s, _r in app.plan_rows), ["new", "ok", "ok"])
            self.assertIn("Traduzir pendentes (1)", str(app.btn_bulk.cget("text")))
            # 3b) double-click on a mod: window with what was translated (and why other texts were left alone)
            top = app.show_details("a.mod")
            self.assertIsNotNone(top)
            tv = top.details["translated"]
            rows = [tv.item(i, "values") for i in tv.get_children()]
            self.assertEqual({str(v[0]): str(v[1]) for v in rows}["iron sword"], "iron sword (pt)")
            self.assertEqual(len(rows), 2)
            tv.selection_set(tv.get_children()[0])
            tv.event_generate("<<TreeviewSelect>>")
            r.update()
            self.assertIn("Tradução:", top.details["text"].get("1.0", "end"))
            self.assertIn("Detalhes: Alpha Mod", top.title())
            top.destroy()
            # 4) window language changes the table and the labels too
            app.set_lang("en")
            self.assertIn("Translate pending (1)", str(app.btn_bulk.cget("text")))
            self.assertEqual(app.tree.heading("state")["text"], "State")
            self.assertEqual(app.nb.tab(app.bulk_tab, "text"), "Translate mods")
            self.assertEqual({app.tree.item(i, "values")[4] for i in app.tree.get_children()}, {"Translated", "New (not translated)"})
            # 5) no target language: asks for one instead of translating
            config.set("target", None)
            app.lang_box.set("")
            app.refresh_plan()
            self.assertIn("Escolha" if app.lang == "pt" else "Choose", app.bulk_summary.get() or "Choose")
        finally:
            try:
                httpd.shutdown()
                httpd.server_close()
                r.destroy()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
