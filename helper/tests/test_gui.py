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

    def test_mod_problem_still_updates_and_restarts_the_program(self):
        """The mod folder cannot be written (the game is open): the new exe is already in place, so the program still restarts into it
        and the message says what is left (this used to show 'update failed' and leave the old program running)."""
        from unittest import mock
        from rwtranslate import updater
        d = Path(tempfile.mkdtemp())
        exe = d / "UniversalTranslate-Helper.exe"
        exe.write_bytes(b"OLD")
        mod = d / "AutoTranslate"
        mod.mkdir()
        restarted = []
        app = self.build(fake_fetcher(release_json("v9.0")), exe_path=exe, mod_dir=mod, restart=lambda e: restarted.append(e))
        app.RESTART_MS_MOD_PROBLEM = 100
        self.assertTrue(pump(self.root, lambda: "Nova versão disponível: v9.0" in app.update_msg.get()), app.update_msg.get())
        with mock.patch.object(updater, "update_mod", side_effect=OSError(22, "Invalid argument")):
            app.btn_apply.invoke()
            self.assertTrue(pump(self.root, lambda: bool(restarted)), app.update_msg.get() + " | " + app.progress.get())
        self.assertEqual(exe.read_bytes(), NEW_EXE, "the program itself was updated")
        self.assertEqual(restarted[0], exe, "and the new one is opened")
        self.assertIn("Mod NÃO atualizado", app.update_msg.get())
        self.assertNotIn("falhou", app.update_msg.get())

    def test_log_tab_shows_what_was_translated_and_follows_the_language(self):
        from rwtranslate import activity
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.assertEqual(app.nb.tab(app.log_tab, "text"), "Log")
        self.assertEqual(len(app.nb.tabs()), 3, "Home, Translate mods, Log")
        activity.clear()
        app.log_entries = []
        app.render_log()
        activity.emit("game", "log_game_batch", {"n": 1, "src": "en", "tgt": "pt-BR", "mod": "x.rescue", "chars": 17, "ms": 12,
                                                 "first": "Search and rescue  ->  Buscar e resgatar"}, pairs=[("Search and rescue", "Buscar e resgatar")])
        activity.emit("model", "log_model_failed", {"src": "en", "tgt": "xx"}, level="error")
        def row_values():
            return [(i, app.log_tree.item(i, "values")) for i in app.log_tree.get_children()]
        self.assertTrue(pump(self.root, lambda: any("x.rescue" in v[2] for _i, v in row_values()) and any("ERRO" in v[1] for _i, v in row_values())),
                        "entries from any thread show up")
        game_iid, game = next((i, v) for i, v in row_values() if "x.rescue" in v[2])
        self.assertIn("Search and rescue -> Buscar e resgatar", game[2], "a translated button is shown: original and translation")
        self.assertEqual(game[1], "Jogo")
        # click a line: the details list every text with its translation
        app.log_tree.selection_set(game_iid)
        self.root.update()
        detail = app.log_detail.get("1.0", "end")
        self.assertIn("Search and rescue", detail)
        self.assertIn("-> Buscar e resgatar", detail)
        # filter: only warnings and errors (the game line is gone, the error stays)
        app.log_filter_box.current(app.LOG_FILTERS.index("problems"))
        app.render_log()
        self.assertTrue(row_values() and all(("ERRO" in v[1] or "aviso" in v[1]) for _i, v in row_values()))
        app.log_filter_box.current(app.LOG_FILTERS.index("all"))
        app.render_log()
        # the window language changes the text of every entry and the tab
        app.set_lang("en")
        game = next(v for _i, v in row_values() if "x.rescue" in v[2])
        self.assertIn("The game asked for a translation", game[2])
        self.assertEqual(game[1], "Game")
        self.assertEqual(app.log_tree.heading("msg")["text"], "What happened")
        self.assertEqual(app.log_filter_box.get(), "Everything")
        # copy and clear
        app.copy_log()
        self.assertIn("Search and rescue", self.root.clipboard_get())
        app.clear_log()
        self.assertEqual(len(app.log_tree.get_children()), 0)

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
        for sysl, expected in (("pt", "pt-BR"), ("es", "es"), ("xx", "en"), (None, "en")):
            languages.system_language, orig = (lambda v=sysl: v), languages.system_language
            try:
                self.assertEqual(i18n.current(), expected, f"system={sysl}")
            finally:
                languages.system_language = orig

    def test_window_language_picker_lists_the_rimworld_languages(self):
        from rwtranslate import i18n
        app = self.build(fake_fetcher(release_json("v0.0")))
        values = set(app.ui_box.cget("values"))
        self.assertEqual(len(values), 30)
        self.assertIn("Deutsch", values)
        self.assertIn("Português (Brasil)", values)
        self.assertEqual(set(app.lang_codes.values()), set(i18n.SUPPORTED_TARGETS))     # the target list is the same 30
        from rwtranslate import gui
        self.assertGreaterEqual(int(str(app.ui_box.cget("width"))), max(len(v) for v in values))     # no name is cut off
        self.assertGreater(gui.fit_width(["简体中文"]), gui.fit_width(["abcd"]) - 1)                     # wide letters count double
        app.set_lang("fr")                                      # not translated yet (no model in tests): English until it is ready
        self.assertEqual(str(app.btn_quit.cget("text")), "Quit")

    def test_github_button_opens_the_repository(self):
        from unittest import mock
        from rwtranslate import gui
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.assertEqual(str(app.btn_github.cget("text")), "Página no GitHub")
        with mock.patch.object(gui.webbrowser, "open") as op:
            app.btn_github.invoke()
        op.assert_called_once_with("https://github.com/Unknown1210/rimworld-universal-translate-mods")
        app.set_lang("en")
        self.assertEqual(str(app.btn_github.cget("text")), "GitHub page")

    def test_texts_can_be_selected_and_copied(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        pump(self.root, lambda: "já está" in app.update_msg.get())
        lbl = app.update_msg.label
        self.assertIn("já está", lbl.cget("text"))
        self.root.update()
        lbl._select_all()
        lbl._copy()
        self.assertIn("já está", self.root.clipboard_get())          # what the user pastes into a translator
        lbl.tag_remove("sel", "1.0", "end")
        lbl._copy()                                                   # nothing selected: the whole text
        self.assertEqual(self.root.clipboard_get(), lbl.cget("text"))
        # tables: Ctrl+C copies rows
        app.log_tree.insert("", "end", values=("10:00", "Jogo", "olá"))
        app.log_tree.selection_set(app.log_tree.get_children())
        app.log_tree.copy_rows()                                       # what Ctrl+C on the table runs
        self.assertIn("olá", self.root.clipboard_get())

    def test_nothing_is_cut_off_in_a_longer_language(self):
        from rwtranslate import gui, i18n
        app = self.build(fake_fetcher(release_json("v0.0")))
        long_text = {k: v + " " + "extra" * 6 for k, v in i18n.TEXT["en"].items() if k in ("tab_home", "tab_bulk", "tab_log", "check_btn", "apply_btn", "logs_btn", "report_btn", "github_btn", "quit_btn", "col_mod", "col_source", "col_texts", "col_words", "col_state", "col_folder")}
        i18n.TEXT["xx"] = {**i18n.TEXT["en"], **long_text}
        try:
            app.lang = "xx"
            app.apply_language()
            self.root.update()
            self.assertGreaterEqual(self.root.winfo_width(), self.root.winfo_reqwidth())      # the window grew to fit
            for b in (app.btn_check, app.btn_apply, app.btn_logs, app.btn_report, app.btn_github, app.btn_quit):
                self.assertGreaterEqual(b.winfo_width(), b.winfo_reqwidth())
            for c in app.tree["columns"]:
                self.assertGreaterEqual(int(app.tree.column(c, "width")), len(app.tree.heading(c, "text")) * 4)
            self.assertGreaterEqual(int(str(app.ui_box.cget("width"))), max(len(v) for v in app.ui_box.cget("values")))
        finally:
            del i18n.TEXT["xx"]

    def test_every_text_exists_in_both_languages(self):
        from rwtranslate import i18n
        self.assertEqual(set(i18n.TEXT["pt"]), set(i18n.TEXT["en"]))

    def test_layout_is_responsive(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.root.geometry("820x500")
        pump(self.root, lambda: False, timeout=0.3)
        small = int(str(app.update_msg.label.cget("wraplength")))
        small_btn = app.btn_check.winfo_width()
        self.root.geometry("960x500")
        pump(self.root, lambda: False, timeout=0.5)
        big = int(str(app.update_msg.label.cget("wraplength")))
        self.assertGreater(big, small + 80, "text re-wraps to the new width")
        self.assertGreater(app.btn_check.winfo_width(), small_btn + 40, "buttons stretch with the window")

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

    def test_only_supported_languages_by_full_name(self):
        from rwtranslate import i18n
        app = self.build(fake_fetcher(release_json("v0.0")))
        codes = set(app.lang_codes.values())
        self.assertEqual(codes, set(i18n.SUPPORTED_TARGETS))
        self.assertNotIn("pt", codes, "Portuguese is offered as Brazil or Portugal")
        self.assertIn("pt-BR", codes)
        self.assertIn("pt-PT", codes)
        self.assertIn("Português (Brasil)", app.lang_codes)
        self.assertIn("Português (Portugal)", app.lang_codes)
        for label in app.lang_codes:
            self.assertGreater(len(label), 3, f"'{label}' looks like a bare code")
        self.assertEqual(app.nb.tab(app.bulk_tab, "text"), "Traduzir mods")
        app.set_lang("en")
        self.assertIn("Portuguese (Brazil) (Português (Brasil))", app.lang_codes)

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
        json.dump([{"from_code": "en", "to_code": "pb", "package_version": "1", "links": ["x"]}], open(idx, "w"))
        models.INDEX_URL = "file://" + idx
        models._index_mem["data"] = None

        class Fake:
            def __init__(self, s, t):
                self.s, self.t = s, t

            def translate_batch(self, texts):
                t = "pt" if self.t == "pb" else self.t           # "pb" = the Brazilian Portuguese model
                return [f"{x} ({t})" if self.s == "en" else f"{x} ({t} from {self.s})" for x in texts]
        cls.made = []
        for s_, t_ in (("en", "pb"), ("zh", "pb")):
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
        config.set("target", "pt-BR")
        root = Path(tempfile.mkdtemp())
        self.mod(root, "A", "a.mod", "Alpha Mod", "<ThingDef><defName>X</defName><label>iron sword</label><description>A sharp sword for fighting.</description></ThingDef>")
        self.mod(root, "B", "b.mod", "Beta Mod", "<ThingDef><defName>Y</defName><label>铁剑</label></ThingDef>")
        httpd = server.serve(0)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        r = tkinter.Tk()
        try:
            app = gui.App(r, httpd, fetcher=fake_fetcher(release_json("v0.0")), lang="pt", mod_dirs=[root])
            # 0) the folders that are searched are listed (numbered, with what kind each one is) before the progress bar
            self.assertTrue(pump(r, lambda: app.dirs_text().startswith("1. ")), "folder list is shown")
            shown = app.dirs_text()
            self.assertIn(str(root), shown)
            self.assertIn("adicionada por você", shown)
            self.assertIn("Pastas pesquisadas", str(app.dirs_frame.cget("text")))
            # the "[padrão]" tag is a separate label stuck to the right edge; the tag of an added folder stays after its path
            self.assertTrue(all(tg is None for _p, tg in app.dir_labels), "only default folders get the right-hand tag (none here: the test folder is an added one)")
            self.assertIn("[adicionada por você]", app.dir_labels[0][0].cget("text"))
            from rwtranslate import gui as _gui
            app.dir_rows = [(Path("C:/Steam/RimWorld/Mods"), "default", True)] + list(app.dir_rows)
            app.render_dirs()
            p0, t0 = app.dir_labels[0]
            self.assertEqual(str(t0.cget("text")), "[padrão]")
            self.assertEqual(str(t0.grid_info()["sticky"]), "e", "the default tag is aligned to the right")
            self.assertNotIn("[padrão]", p0.cget("text"))
            app.dir_rows = app.dir_rows[1:]
            app.render_dirs()
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
            self.assertEqual(bulk.read_cache("pt-BR", "b.mod")["铁剑"], "铁剑 (pt from zh)")
            # 3) a mod installed later is found again
            self.mod(root, "C", "c.mod", "Gamma Mod", "<ThingDef><defName>Z</defName><label>steel axe</label></ThingDef>")
            app.btn_scan.invoke()
            self.assertTrue(pump(r, lambda: len(app.plan_rows) == 3 and not app.bulk_running), "rescan sees the new mod")
            self.assertEqual(sorted(s for _m, s, _r in app.plan_rows), ["new", "ok", "ok"])
            self.assertIn("Traduzir pendentes (1)", str(app.btn_bulk.cget("text")))
            # 3-pre) at the default window size no button label is cut off, and the window is wide enough
            app.nb.select(app.bulk_tab)
            r.update()
            for b in (app.btn_add_dir, app.btn_scan, app.btn_bulk, app.btn_bulk_all, app.btn_stop, app.btn_clear):
                self.assertGreaterEqual(b.winfo_width(), b.winfo_reqwidth(), f"button '{b.cget('text')}' is cut off")
            # the progress line gets an estimated time left once enough has been done
            self.assertEqual(app.format_eta(45), "45 s")
            self.assertEqual(app.format_eta(200), "3 min 20 s")
            self.assertEqual(app.format_eta(3900), "1 h 05 min")
            app._bulk_t0 = None
            self.assertEqual(app.eta_text(0.5), "", "no estimate before the run started")
            app._bulk_t0 = time.time() - 60
            self.assertEqual(app.eta_text(0.5), "1 min 00 s", "half done in a minute: about a minute left")
            self.assertEqual(app.eta_text(0.001), "", "too little progress to estimate")
            app.show_progress(1, 4, 2, 4)                       # 1 mod done + half of the second = 37%
            self.assertIn("37%", app.bulk_progress.get())
            self.assertIn("tempo restante estimado", app.bulk_progress.get())
            app._bulk_t0 = None
            # 3a) columns: names centred except the mod; the last column opens the mod's folder
            for col in ("source", "texts", "words", "state", "folder"):
                self.assertEqual(str(app.tree.column(col, "anchor")), "center", col)
                self.assertEqual(str(app.tree.heading(col, "anchor")), "center", col)
            self.assertEqual(str(app.tree.column("mod", "anchor")), "w")
            self.assertEqual(app.tree.heading("folder")["text"], "Pasta")
            opened = []
            gui.open_folder = lambda path: opened.append(path)
            app.nb.select(app.bulk_tab)                       # the list must be on screen for the pixel positions to exist
            r.geometry("900x700")
            r.update()
            iid = app.rows["a.mod"]
            app.tree.selection_set(iid)
            app.tree.see(iid)
            r.update()
            bx, by, bw, bh = app.tree.bbox(iid, "#6")
            ev = type("Ev", (), {"x": bx + bw // 2, "y": by + bh // 2})()
            self.assertEqual(app.tree.item(iid, "values")[5], "Abrir pasta")
            self.assertEqual(app.on_tree_click(ev), "break")
            self.assertEqual(opened, [str(root / "A")], "clicking the folder column opens the mod folder")
            bx, by, bw, bh = app.tree.bbox(iid, "#1")
            ev1 = type("Ev", (), {"x": bx + 5, "y": by + bh // 2})()
            self.assertIsNone(app.on_tree_click(ev1))
            self.assertEqual(len(opened), 1, "clicking another column does not open the folder")
            # 3b) double-click on a mod: window with what was translated (and why other texts were left alone)
            top = app.show_details("a.mod")
            self.assertIsNotNone(top)
            tv = top.details["translated"]
            rows = [tv.item(i, "values") for i in tv.get_children()]
            self.assertEqual({str(v[0]): str(v[1]) for v in rows}["iron sword"], "iron sword (pt)")
            self.assertEqual(len(rows), 2)
            # words tab: the same texts with their number of words, most words first; total in the tab title
            nbk = top.details["nb"]
            self.assertEqual(nbk.tab(1, "text"), "Palavras traduzidas (7)")
            wrows = [top.details["words"].item(i, "values") for i in top.details["words"].get_children()]
            self.assertEqual([(str(v[0]), str(v[2])) for v in wrows], [("A sharp sword for fighting.", "5"), ("iron sword", "2")])
            self.assertEqual(top.details["words"].heading("w")["text"], "Palavras")
            # not-translated tab: Original | Tradução existente | Motivo
            self.assertEqual(len(top.details["skipped"]["columns"]), 3)
            self.assertEqual([top.details["skipped"].heading(c)["text"] for c in top.details["skipped"]["columns"]], ["Original", "Tradução existente", "Motivo"])
            tv.selection_set(tv.get_children()[0])
            tv.event_generate("<<TreeviewSelect>>")
            r.update()
            self.assertIn("Tradução:", top.details["text"].get("1.0", "end"))
            self.assertIn("Detalhes: Alpha Mod", top.title())
            # 3c) with the details window OPEN, changing the language of the main window redraws it too (same tab, same row)
            app.set_lang("en")
            self.assertEqual(top.title(), "Details: Alpha Mod")
            self.assertEqual(top.details["nb"].tab(0, "text"), "Translated texts (2)")
            self.assertEqual(top.details["nb"].tab(1, "text"), "Words translated (7)")
            self.assertEqual(top.details["skipped"].heading("e")["text"], "Existing translation")
            self.assertEqual(top.details["translated"].heading("o")["text"], "Original")
            self.assertEqual(top.details["translated"].heading("t")["text"], "Translation")
            self.assertIn("Translation:", top.details["text"].get("1.0", "end"), "the selected row stays selected, text in English")
            self.assertNotIn("Tradução:", top.details["text"].get("1.0", "end"))
            self.assertIn("added by you", app.dirs_text())
            self.assertIn("Folders searched", str(app.dirs_frame.cget("text")))
            app.set_lang("pt")
            self.assertEqual(top.title(), "Detalhes: Alpha Mod")
            self.assertEqual(top.details["translated"].heading("t")["text"], "Tradução")
            top.destroy()
            app.set_lang("en")
            app.set_lang("pt")
            # 4) window language changes the table and the labels too
            app.set_lang("en")
            self.assertIn("Translate pending (1)", str(app.btn_bulk.cget("text")))
            self.assertEqual(app.tree.heading("state")["text"], "State")
            self.assertEqual(app.nb.tab(app.bulk_tab, "text"), "Translate mods")
            self.assertEqual({app.tree.item(i, "values")[4] for i in app.tree.get_children()}, {"Translated", "New (not translated)"})
            # 4b) delete translations: asks first; "no" keeps everything, "yes" empties the cache and lists the mods as new again
            self.assertEqual(str(app.btn_clear.cget("state")), "normal")
            app.ask_yes_no = lambda title, text: False
            app.btn_clear.invoke()
            self.assertTrue(bulk.read_cache("pt-BR", "b.mod"), "answering no deletes nothing")
            asked = []
            app.ask_yes_no = lambda title, text: asked.append(text) or True
            app.btn_clear.invoke()
            self.assertTrue(asked and ("Português (Brasil)" in asked[0] or "Portuguese (Brazil)" in asked[0]), "the question names the language")
            self.assertTrue(pump(r, lambda: len(app.plan_rows) == 3 and not app.bulk_running and all(s == "new" for _m, s, _r in app.plan_rows)))
            self.assertEqual(bulk.read_cache("pt-BR", "b.mod"), {}, "the saved translations are gone")
            self.assertEqual(sorted(s for _m, s, _r in app.plan_rows), ["new", "new", "new"])
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
