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
        from rwtranslate import config
        config.set("targets", None)                  # (one language unless the test ticks more: tests share the settings file)
        from unittest import mock
        self.notices = []                            # the small "new version" window must never block a test: it is recorded instead
        self._notice_patch = mock.patch("tkinter.messagebox.showinfo", side_effect=lambda *a, **k: self.notices.append(a))
        self._notice_patch.start()
        self.httpd = server.serve(0)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.root = tkinter.Tk()
        kw.setdefault("lang", "pt")
        self.app = gui.App(self.root, self.httpd, fetcher=fetcher, **kw)
        return self.app

    def tearDown(self):
        import gc
        if hasattr(self, "_notice_patch"):
            self._notice_patch.stop()
        try:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.root.destroy()
        except Exception:
            pass
        self.__dict__.pop("app", None)
        gc.collect()          # finalisers run on the main thread here; worker threads must never be the last owner of a Tk object

    def test_log_bar_widgets_have_the_same_height(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.root.geometry("900x700")
        self.root.update()
        app.nb.select(app.log_tab)
        self.root.update()
        heights = {w.winfo_height() for w in (app.log_filter_box, app.btn_log_copy, app.btn_log_clear, app.btn_log_folder)}
        self.assertEqual(len(heights), 1, heights)
        self.assertGreater(heights.pop(), 10)

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

    def test_a_small_window_tells_about_a_new_version_when_the_program_opens(self):
        app = self.build(fake_fetcher(release_json("v9.0")))
        self.assertTrue(pump(self.root, lambda: bool(self.notices)))
        self.assertEqual(len(self.notices), 1)
        self.assertIn("v9.0", self.notices[0][1])
        self.assertIn("Atualizar agora", self.notices[0][1])
        app.start_check()                                            # a later check by hand only updates the line on the Home tab
        self.assertTrue(pump(self.root, lambda: "Nova versão disponível" in app.update_msg.get()))
        self.assertEqual(len(self.notices), 1)

    def test_no_window_when_the_program_is_up_to_date(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.assertTrue(pump(self.root, lambda: "mais nova" in app.update_msg.get()))
        self.assertEqual(self.notices, [])

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
        self.assertEqual(len(app.nb.tabs()), 4, "Home, Translate mods, Log, Help")
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
        self.assertEqual(len(values), 26)          # RimWorld's 30 minus Czech, Danish, Hungarian and Polish (no usable model)
        self.assertIn("Deutsch", values)
        self.assertIn("Português (Brasil)", values)
        self.assertEqual(set(app.lang_codes.values()), set(i18n.SUPPORTED_TARGETS))     # the target list is the same 26
        from rwtranslate import gui
        self.assertGreaterEqual(int(str(app.ui_box.cget("width"))), max(len(v) for v in values))     # no name is cut off
        self.assertGreater(gui.fit_width(["简体中文"]), gui.fit_width(["abcd"]) - 1)                     # wide letters count double
        app.set_lang("fr")                                      # not translated yet (no model in tests): English until it is ready
        self.assertEqual(str(app.btn_quit.cget("text")), "Quit")

    def test_background_translation_of_all_mods_waits_for_the_game_and_can_be_switched_off(self):
        import time
        from unittest import mock
        from rwtranslate import config, models, server
        app = self.build(fake_fetcher(release_json("v0.0")))
        mod = type("M", (), {"package_id": "x.mod", "name": "X"})()
        app.plan_rows = [(mod, "new", None)]
        config.set("target", "pt-BR")
        app.set_lang_choices(["pt-BR", "en"])
        with mock.patch.object(models, "is_installed", return_value=True):
            server.LAST_GAME_REQUEST = 0.0
            self.assertFalse(app.should_auto_bulk(), "the program has only just opened: wait 30 seconds first")
            app._opened_at = time.time() - 31
            self.assertTrue(app.should_auto_bulk(), "pending mods, model there, the game is quiet: translate them (even the disabled ones)")
            server.LAST_GAME_REQUEST = time.time()
            self.assertFalse(app.should_auto_bulk(), "the game is asking right now: its mods come first")
            server.LAST_GAME_REQUEST = 0.0
            app.plan_rows = [(mod, "ok", {})]
            self.assertFalse(app.should_auto_bulk(), "nothing left to translate")
            app.plan_rows = [(mod, "new", None)]
            app._auto_pause_until = time.time() + 60                    # the player pressed Stop
            self.assertFalse(app.should_auto_bulk())
            app._auto_pause_until = 0
            config.set("background_all", False)
            self.assertFalse(app.should_auto_bulk(), "switched off in the window")
            config.set("background_all", True)
            with mock.patch.object(app, "start_bulk") as sb:
                app.auto_bulk_tick()
            sb.assert_called_once_with(False, polite=True)
        self.assertTrue(app.chk_bg.instate(["selected"]))
        app.chk_bg.state(["!selected"])
        app.on_bg_toggle()
        self.assertFalse(app.bg_enabled())
        config.set("background_all", True)

    def test_log_buttons_sit_together_on_the_left(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        cols = {str(app.btn_log_copy.grid_info()["column"]), str(app.btn_log_clear.grid_info()["column"]), str(app.btn_log_folder.grid_info()["column"])}
        self.assertEqual(cols, {"2", "3", "4"})
        self.assertEqual(str(app.btn_log_folder.grid_info().get("sticky", "")), "", "not pushed to the right edge")

    def test_mods_table_sorts_by_the_clicked_heading(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        app.tree.delete(*app.tree.get_children())
        for vals in (("beta", "en", 10, 50, "Traduzido", "x"), ("Alpha", "zh", 2, 5, "Novo (não traduzido)", "x"),
                     ("gamma", "", 30, 7, "Traduzido pelo jogo", "x"), ("delta", "en", 4, 70, "Traduzido - 2 texto(s) falharam", "x")):
            app.tree.insert("", "end", values=("",) + vals)

        def column(i):
            return [str(app.tree.item(k, "values")[i + 1]) for k in app.tree.get_children()]       # (the first cell is the tick box)
        app.tree.heading("mod", "command")                                    # the heading is clickable
        app.sort_by("mod")
        self.assertEqual(column(0), ["Alpha", "beta", "delta", "gamma"], "A to Z, ignoring upper/lower case")
        self.assertIn("\u25b2", app.tree.heading("mod")["text"])
        app.sort_by("mod")
        self.assertEqual(column(0), ["gamma", "delta", "beta", "Alpha"], "second click: Z to A")
        self.assertIn("\u25bc", app.tree.heading("mod")["text"])
        app.sort_by("texts")
        self.assertEqual(column(2), ["2", "4", "10", "30"], "numbers are sorted as numbers, not as text")
        self.assertNotIn("\u25b2", app.tree.heading("mod")["text"], "only the sorted column has the arrow")
        app.sort_by("words")
        app.sort_by("words")
        self.assertEqual(column(3), ["70", "50", "7", "5"])
        app.sort_by("state")
        self.assertEqual(column(4)[0], "Novo (não traduzido)")
        self.assertEqual(column(4)[-1], "Traduzido pelo jogo")
        app.sort_by("state")
        self.assertEqual(column(4)[0], "Traduzido pelo jogo")
        app.set_lang("en")                                                      # the arrow survives a change of window language
        self.assertIn("\u25bc", app.tree.heading("state")["text"])

    def test_target_and_background_option_are_locked_while_a_translation_runs(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.assertFalse(app.chk_bg.instate(["disabled"]))
        self.assertEqual(str(app.lang_box.cget("state")), "readonly")
        app.bulk_running = True
        app.update_bulk_buttons()
        self.assertTrue(app.chk_bg.instate(["disabled"]), "can not be changed while translating: stop the run first")
        self.assertEqual(str(app.lang_box.cget("state")), "disabled", "the target language is locked too")
        self.assertIn("Parar", app.lbl_bg_note.cget("text"))
        app.bulk_running = False
        app.update_bulk_buttons()
        self.assertFalse(app.chk_bg.instate(["disabled"]))
        self.assertEqual(str(app.lang_box.cget("state")), "readonly")
        self.assertNotIn("Parar", app.lbl_bg_note.cget("text"))

    def test_automatic_translation_box_is_a_real_tick_at_launch(self):
        from rwtranslate import config
        config.set("background_all", True)
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.root.update()
        self.assertTrue(app.chk_bg.instate(["selected"]))
        self.assertFalse(app.chk_bg.instate(["alternate"]), "a tick, not the \"-\" of the third state")
        app.chk_bg.invoke()                                                  # one click switches it off (it used to take two)
        self.assertFalse(app.chk_bg.instate(["selected"]))
        self.assertFalse(app.chk_bg.instate(["alternate"]))
        self.assertFalse(config.get("background_all"))
        app.chk_bg.invoke()
        self.assertTrue(app.chk_bg.instate(["selected"]))
        self.assertTrue(config.get("background_all"))

    def test_saved_window_sizes_are_used_only_when_they_make_sense(self):
        from rwtranslate import gui
        self.build(fake_fetcher(release_json("v0.0")))
        w = self.root
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        self.assertEqual(gui.usable_geometry(w, "900x700+20+30", 800, 520), "900x700+20+30")
        self.assertEqual(gui.usable_geometry(w, "900x700", 800, 520), "900x700")
        self.assertEqual(gui.usable_geometry(w, "100x100+20+30", 800, 520), "800x520+20+30", "never smaller than the minimum")
        self.assertEqual(gui.usable_geometry(w, f"900x700+{sw + 500}+30", 800, 520), "900x700", "a position outside the screen is dropped")
        self.assertEqual(gui.usable_geometry(w, "900x700+20+-300", 800, 520), "900x700")
        self.assertEqual(gui.usable_geometry(w, f"{sw + 4000}x{sh + 4000}", 800, 520), f"{sw}x{sh}", "never bigger than the screen")
        self.assertIsNone(gui.usable_geometry(w, "garbage", 800, 520))
        self.assertIsNone(gui.usable_geometry(w, None, 800, 520))

    def test_the_sizes_the_player_chose_come_back_next_time(self):
        from rwtranslate import bulk, config, gui
        config.set("layout", {"main": "930x690+15+25", "cols_mods": {"mod": 333, "state": 222}, "cols_log": {"msg": 555},
                              "details": "720x540+40+40", "details_sash": 260})
        try:
            app = self.build(fake_fetcher(release_json("v0.0")))
            self.root.update()
            self.assertTrue(self.root.geometry().endswith("x690+15+25"), self.root.geometry())          # (the width can grow to fit the texts)
            self.assertEqual(int(app.tree.column("mod", "width")), 333)
            self.assertEqual(int(app.tree.column("state", "width")), 222)
            self.assertEqual(int(app.log_tree.column("msg", "width")), 555)
            # the details window: the size, and the height between the table and the boxes
            config.set("target", "pt-BR")
            app.lang_codes = {"Português (Brasil)": "pt-BR"}
            app.lang_box.configure(values=["Português (Brasil)"])
            app.lang_box.set("Português (Brasil)")
            pump(self.root, lambda: app.bulk_current.get() == "")
            app.refresh_plan = lambda: None
            mod = type("M", (), {"package_id": "l.mod", "name": "L", "path": "x"})()
            app.plan_rows = [(mod, "ok", {"texts": 1, "words": 2})]
            app.render_rows()
            bulk.write_cache("pt-BR", "l.mod", {"Medkit": "Kit médico"})
            try:
                top = app.show_details("l.mod")
                top.update()
                self.assertTrue(top.geometry().startswith("720x540"), top.geometry())
                top.geometry("760x560+50+50")                                   # the player resizes it: it is remembered a moment later
                self.assertTrue(pump(self.root, lambda: str(config.get("layout").get("details", "")).startswith("760x560"), timeout=4))
                top.destroy()
            finally:
                bulk.cache_path("pt-BR", "l.mod").unlink(missing_ok=True)
        finally:
            config.set("layout", {})

    def test_help_tab_lists_the_questions_and_filters_them(self):
        from rwtranslate import i18n
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.assertEqual(app.nb.tab(app.faq_tab, "text"), "Ajuda (FAQ)")
        text = app.faq_text.get("1.0", "end")
        self.assertIn("Do que eu preciso para as traduções funcionarem no jogo?", text)
        self.assertEqual(i18n.faq_count(), 14)
        for i in range(1, i18n.faq_count() + 1):                    # every question has its answer, in both handwritten languages
            for lang in ("pt", "en"):
                self.assertTrue(i18n.TEXT[lang][f"faq_q{i}"].strip() and i18n.TEXT[lang][f"faq_a{i}"].strip())
        app.faq_filter.insert(0, "reporto")
        app.render_faq()
        text = app.faq_text.get("1.0", "end")
        self.assertIn("Como reporto um problema?", text)
        self.assertNotIn("Do que eu preciso", text)
        app.faq_filter.delete(0, "end")
        app.faq_filter.insert(0, "zzzz nothing")
        app.render_faq()
        self.assertIn("Nenhuma pergunta encontrada.", app.faq_text.get("1.0", "end"))
        app.faq_filter.delete(0, "end")
        app.set_lang("en")                                          # follows the window language
        self.assertEqual(app.nb.tab(app.faq_tab, "text"), "Help (FAQ)")
        self.assertIn("What do I need for the translations to work in the game?", app.faq_text.get("1.0", "end"))
        app.set_lang("pt")

    def test_card_1_is_greyed_when_the_automatic_translation_is_off(self):
        from rwtranslate import config
        config.set("background_all", True)
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.root.update()
        grid = app.chk_bg.grid_info()
        self.assertEqual(int(grid["row"]), 0, "the switch is the first thing in the card")
        self.assertLess(int(grid["row"]), int(app.lbl_opt1_body.grid_info()["row"]))
        on_color = str(app.lbl_opt1_body.cget("foreground"))
        app.chk_bg.invoke()
        self.assertFalse(app.bg_enabled())
        self.assertNotEqual(str(app.lbl_opt1_body.cget("foreground")), on_color, "the text of card 1 is greyed")
        app.chk_bg.invoke()
        self.assertTrue(app.bg_enabled())
        self.assertEqual(str(app.lbl_opt1_body.cget("foreground")), on_color, "and comes back when it is switched on again")

    def _app_with_mods(self, languages=("pt-BR",)):
        from rwtranslate import config, targets
        app = self.build(fake_fetcher(release_json("v0.0")))
        config.set("target", languages[0])
        targets.set_selected(list(languages), languages[0])
        app.lang_codes = {"Português (Brasil)": "pt-BR", "Espanhol": "es", "Japonês": "ja"}
        app.lang_box.configure(values=list(app.lang_codes))
        app.lang_box.set("Português (Brasil)")
        pump(self.root, lambda: app.bulk_current.get() == "")
        app.refresh_plan = lambda: None
        a = type("M", (), {"package_id": "a.mod", "name": "A", "path": "x", "fingerprint": "1"})()
        b = type("M", (), {"package_id": "b.mod", "name": "B", "path": "x", "fingerprint": "2"})()
        app.plan_rows = [(a, "ok", {"texts": 2, "words": 4}), (b, "new", None)]
        return app

    def test_languages_window_is_the_same_list_as_the_home_tab(self):
        from rwtranslate import config, targets
        app = self._app_with_mods(("pt-BR",))
        self.assertIn("1 idioma", str(app.btn_langs.cget("text")))
        dlg = app.open_languages_dialog()
        self.root.update()
        self.assertIs(app.open_languages_dialog(), dlg, "one window only")
        self.assertTrue(dlg.checks["pt-BR"].instate(["selected"]))
        self.assertFalse(dlg.checks["es"].instate(["selected"]))
        self.root.setvar(str(dlg.checks["es"]), 1)               # tick Spanish
        self.root.setvar(str(dlg.checks["ja"]), 1)
        dlg.apply_choice()
        self.assertEqual(targets.selected(), ["pt-BR", "es", "ja"])
        self.assertEqual(config.get("target"), "pt-BR", "the game still uses the one language")
        self.assertIn("3 idiomas", str(app.btn_langs.cget("text")), "the Home tab follows")
        self.assertIn("(3)", str(app.btn_bulk_langs.cget("text")), "and so does the button of the Translate mods tab")
        # the other way round: a change made on the Home tab shows in the window
        targets.set_selected(["pt-BR"], "pt-BR")
        app.on_targets_changed()
        self.assertFalse(dlg.checks["es"].instate(["selected"]))
        # the language the game uses is chosen in the window too
        self.root.setvar(str(dlg.checks["es"]), 1)
        dlg.apply_choice("es")
        self.assertEqual(config.get("target"), "es")
        self.assertEqual(app.lang_box.get(), "Espanhol", "the box of the Home tab shows the language of the game")
        # everything can be unticked: nothing is selected, and the game keeps its language
        for c in ("pt-BR", "es"):
            self.root.setvar(str(dlg.checks[c]), 0)
        dlg.apply_choice()
        self.assertEqual(targets.selected(), [])
        self.assertEqual(config.get("target"), "es")
        self.assertIn("(0)", str(app.btn_bulk_langs.cget("text")))
        self.assertNotIn("...", str(app.btn_bulk_langs.cget("text")))
        self.assertIn("Nenhum idioma", [w for w in dlg.winfo_children() if w.winfo_class() == "TLabel" and "Nenhum" in str(w.cget("text"))][0].cget("text"))
        from unittest import mock
        with mock.patch("rwtranslate.bulk.run") as run:
            app.start_bulk(False)
        run.assert_not_called()
        self.assertIn("Nenhum idioma", app.bulk_summary.get())
        self.root.setvar(str(dlg.checks["ja"]), 1)
        dlg.apply_choice()
        self.assertEqual(targets.selected(), ["ja"])
        dlg.destroy()
        config.set("targets", None)

    def test_languages_cannot_be_changed_while_a_translation_runs(self):
        from rwtranslate import targets
        app = self._app_with_mods(("pt-BR",))
        dlg = app.open_languages_dialog()
        app.bulk_running = True
        app.update_bulk_buttons()
        self.assertEqual(str(app.btn_langs.cget("state")), "disabled")
        self.assertEqual(str(app.btn_bulk_langs.cget("state")), "disabled")
        dlg.refresh()
        self.assertTrue(dlg.checks["es"].instate(["disabled"]))
        self.root.setvar(str(dlg.checks["es"]), 1)
        dlg.apply_choice()
        self.assertEqual(targets.selected(), ["pt-BR"], "nothing changes while it runs")
        app.bulk_running = False
        app.update_bulk_buttons()
        self.assertEqual(str(app.btn_langs.cget("state")), "normal")
        dlg.destroy()

    def test_several_languages_are_translated_one_after_the_other_and_the_table_follows_the_game_language(self):
        from unittest import mock
        from rwtranslate import bulk
        app = self._app_with_mods(("pt-BR", "es", "ja"))
        app.render_rows()
        runs = []

        class R:
            def __init__(self, pid):
                self.package_id, self.words, self.error = pid, 5, None

            def to_state(self, fp):
                return {"fingerprint": fp, "texts": 1, "words": 5}

        def fake_run(lang, dirs, **kw):
            runs.append(lang)
            kw["progress"]({"event": "start", "total": 1, "all": 2})
            a = app.plan_rows[1][0]
            kw["progress"]({"event": "mod_start", "index": 0, "total": 1, "name": a.name, "status": "new"})
            kw["progress"]({"event": "mod_done", "index": 1, "total": 1, "result": R(a.package_id)})
            return [R(a.package_id)]
        asked = []
        with mock.patch("rwtranslate.bulk.run", side_effect=fake_run), \
                mock.patch.object(app, "ask_yes_no", side_effect=lambda t, m: asked.append(m) or True), \
                mock.patch.object(app, "run_bg", side_effect=lambda work, done: done(work(), None)):
            app.start_bulk(False)
        while not app.q.empty():
            app.q.get_nowait()()
        self.assertEqual(runs, ["pt-BR", "es", "ja"], "the game's language first, then the others")
        self.assertEqual(len(asked), 1, "it asks once, before starting")
        self.assertIn("3 idiomas", asked[0])
        self.assertFalse(app.bulk_running)

    def test_it_does_not_start_when_the_player_says_no(self):
        from unittest import mock
        app = self._app_with_mods(("pt-BR", "es"))
        with mock.patch("rwtranslate.bulk.run") as run, mock.patch.object(app, "ask_yes_no", return_value=False):
            app.start_bulk(False)
        run.assert_not_called()
        self.assertFalse(app.bulk_running)

    def test_one_language_does_not_ask_anything(self):
        from unittest import mock
        app = self._app_with_mods(("pt-BR",))
        with mock.patch("rwtranslate.bulk.run", return_value=[]) as run, mock.patch.object(app, "ask_yes_no") as ask, \
                mock.patch.object(app, "run_bg", side_effect=lambda work, done: done(work(), None)):
            app.start_bulk(False)
        ask.assert_not_called()
        self.assertEqual([c.args[0] for c in run.call_args_list], ["pt-BR"])

    def test_the_automatic_translation_only_does_the_game_language(self):
        from unittest import mock
        app = self._app_with_mods(("pt-BR", "es", "ja"))
        with mock.patch("rwtranslate.bulk.run", return_value=[]) as run, mock.patch.object(app, "ask_yes_no") as ask, \
                mock.patch.object(app, "run_bg", side_effect=lambda work, done: done(work(), None)):
            app.start_bulk(False, polite=True)
        ask.assert_not_called()
        self.assertEqual([c.args[0] for c in run.call_args_list], ["pt-BR"])

    def test_the_state_column_says_in_how_many_languages_a_mod_is_translated(self):
        app = self._app_with_mods(("pt-BR", "es", "ja", "fr"))
        a, b = app.plan_rows[0][0], app.plan_rows[1][0]
        app.lang_done = {"a.mod": 4, "b.mod": 2}
        saved = {"texts": 1, "words": 2}
        self.assertEqual(app._row_values(a, "ok", saved)[4], "Traduzido em todos os 4 idiomas")
        self.assertEqual(app._row_values(b, "ok", saved)[4], "Traduzido em 2 de 4 idiomas")
        app.lang_done = {"a.mod": 4, "b.mod": 0}
        self.assertEqual(app._row_values(b, "ok", saved)[4], "Traduzido", "none yet: the usual text")
        # pending counts the languages that are missing, not only the mods that are new
        app.render_rows()
        app.lang_done = {"a.mod": 3, "b.mod": 4}
        app.update_bulk_buttons()
        self.assertIn("(2)", str(app.btn_bulk.cget("text")), "a mod missing a language is still pending")

    def test_missing_models_are_downloaded_one_by_one_with_progress(self):
        from unittest import mock
        from rwtranslate import models
        app = self._app_with_mods(("pt-BR", "es", "ja"))
        got = []

        def fake_install(src, tgt, progress=print, index=None):
            got.append(tgt)
            progress("  50% (10 MB)")
        with mock.patch.object(models, "is_installed", return_value=False), mock.patch.object(models, "install", side_effect=fake_install), \
                mock.patch.object(app, "run_bg", side_effect=lambda work, done: done(work(), None)):
            self.assertEqual(app.missing_models(), ["pt-BR", "es", "ja"])
            app.install_missing_models()
        self.assertEqual(got, ["pt-BR", "es", "ja"])
        msgs = []
        while not app.q.empty():
            app.q.get_nowait()()
        self.assertFalse(getattr(app, "_models_job", False))

    def test_choosing_a_language_never_downloads_a_model_by_itself(self):
        from unittest import mock
        from rwtranslate import models
        app = self.build(fake_fetcher(release_json("v0.0")))
        app.lang_codes = {"Japanese": "ja"}
        app.lang_box.configure(values=["Japanese"])
        app.lang_box.set("Japanese")
        with mock.patch.object(models, "is_installed", return_value=False), \
                mock.patch.object(models, "install") as inst, mock.patch.object(app, "run_bg") as bg, \
                mock.patch.object(app, "refresh_plan"):
            app.on_target_selected()
            bg.assert_not_called()
            inst.assert_not_called()
            self.assertTrue(app.btn_model.winfo_manager(), "the Download model button is offered")
            app.install_model()                                         # only the button downloads
            bg.assert_called_once()

    def test_download_shows_the_percentage(self):
        from unittest import mock
        from rwtranslate import models
        app = self.build(fake_fetcher(release_json("v0.0")))
        app.lang_codes = {"Japanese": "ja"}
        app.lang_box.configure(values=["Japanese"])
        app.lang_box.set("Japanese")
        seen = {}

        def fake_install(src, tgt, progress=print, index=None):
            progress("  37% (42 MB)")
        with mock.patch.object(models, "install", side_effect=fake_install), \
                mock.patch.object(app, "run_bg", side_effect=lambda work, done: work()):
            app.install_model()
        while not app.q.empty():
            app.q.get_nowait()()                                       # what the worker handed to the window thread
        self.assertIn("37%", app.target_msg.get())                      # shown right under the target language
        self.assertIn("42 MB", app.target_msg.get())

    def test_ticked_mods_are_the_only_ones_translated(self):
        from unittest import mock
        app = self.build(fake_fetcher(release_json("v0.0")))
        a = type("M", (), {"package_id": "a.mod", "name": "A", "path": "x"})()
        b = type("M", (), {"package_id": "b.mod", "name": "B", "path": "x"})()
        c = type("M", (), {"package_id": "c.mod", "name": "C", "path": "x"})()
        app.plan_rows = [(a, "new", None), (b, "new", None), (c, "ok", {"texts": 1, "words": 1})]
        app.render_rows()
        app.update_bulk_buttons()
        self.assertIn("(2)", str(app.btn_bulk.cget("text")))                    # nothing ticked: all the pending ones
        iid_a = app.rows["a.mod"]
        app.toggle_selected(iid_a)
        self.assertEqual(app.selected_ids(), {"a.mod"})
        self.assertEqual(app.tree.item(iid_a, "values")[0], app.BOX_ON)
        self.assertIn("Traduzir selecionados (1)", str(app.btn_bulk.cget("text")))
        self.assertIn("Refazer selecionados (1)", str(app.btn_bulk_all.cget("text")))
        app.toggle_all_selected()
        self.assertEqual(app.selected_ids(), {"a.mod", "b.mod", "c.mod"})
        self.assertIn("Traduzir selecionados (2)", str(app.btn_bulk.cget("text")))     # c is already done
        app.toggle_all_selected()
        self.assertEqual(app.selected_ids(), set())
        app.toggle_selected(app.rows["b.mod"])
        config_target = "pt-BR"
        app.lang_codes = {"X": config_target}
        app.lang_box.configure(values=["X"])
        app.lang_box.set("X")
        with mock.patch("rwtranslate.bulk.run", return_value=[]) as run, mock.patch.object(app, "run_bg", side_effect=lambda work, done: work()):
            app.start_bulk(False)
        self.assertEqual(run.call_args.kwargs["only"], {"b.mod"})
        self.assertIn("Português", app.bulk_title.get())

    def test_details_table_filter_wrap_and_selection(self):
        import tkinter
        from rwtranslate import gui
        self.build(fake_fetcher(release_json("v0.0")))
        f = tkinter.Toplevel(self.root)
        f.geometry("700x400")
        tbl = gui.text_table_class()(f, ["o", "t"])
        tbl.heading("o", text="Original")
        tbl.heading("t", text="Tradução")
        tbl.pack(fill="both", expand=True)
        long_text = "word " * 80
        a = tbl.insert("", "end", values=[long_text, "tradução longa " * 20])
        b = tbl.insert("", "end", values=["Medkit", "Kit médico"])
        c = tbl.insert("", "end", values=["Repair kit", "Kit de reparo"])
        self.root.update()
        got = []
        tbl.bind("<<TreeviewSelect>>", lambda e: got.append(e.widget.selection()))
        # nothing wraps by default: every row has the same height; wrapping makes the long row taller
        tbl._relayout_now()
        one_line = tbl._heights[0]
        self.assertEqual(len(set(tbl._heights)), 1)
        tbl.set_wrap(True)
        self.assertGreater(tbl._heights[0], one_line)
        self.assertEqual(tbl._heights[1], one_line)
        tbl.set_wrap(False)
        # the filter shows only the rows that contain the text (any column, any case)
        tbl.set_filter("KIT")
        self.assertEqual(tbl.get_children(), (b, c))                       # "kit", whatever the case
        tbl.set_filter("repair")
        self.assertEqual(tbl.get_children(), (c,))
        tbl.set_filter("médico")
        self.assertEqual(tbl.get_children(), (b,))
        tbl.set_filter("nothing like this")
        self.assertEqual(tbl.get_children(), ())
        tbl.set_filter("")
        self.assertEqual(len(tbl.get_children()), 3)
        # a click selects the row and tells the window
        tbl.update()
        y = tbl._tops[1] + 5
        ev = type("Ev", (), {"x": 10, "y": y})()
        tbl._click(ev)
        self.assertEqual(tbl.selection(), (b,))
        self.assertEqual(got[-1], (b,))
        tbl._move(1)
        self.assertEqual(tbl.selection(), (c,))
        f.destroy()

    def test_clicking_a_row_shows_that_row_in_every_tab(self):
        from rwtranslate import bulk, config
        app = self.build(fake_fetcher(release_json("v0.0")))
        config.set("target", "pt-BR")
        app.lang_codes = {"Português (Brasil)": "pt-BR"}
        app.lang_box.configure(values=["Português (Brasil)"])
        app.lang_box.set("Português (Brasil)")
        pump(self.root, lambda: app.bulk_current.get() == "")
        app.refresh_plan = lambda: None
        mod = type("M", (), {"package_id": "y.mod", "name": "Y", "path": "x"})()
        app.plan_rows = [(mod, "ok", {"texts": 6, "words": 20})]
        app.render_rows()
        texts = {"aa one": "A1", "bb two words here": "B2", "cc three words here now": "C3", "dd four": "D4", "ee five words": "E5", "ff six": "F6"}
        bulk.write_cache("pt-BR", "y.mod", texts)
        try:
            top = app.show_details("y.mod")
            d = top.details
            for key in ("translated", "words"):                       # the words tab is ordered by word count: another order than the first tab
                tv = d[key]
                for iid in tv.get_children():
                    tv.selection_set(iid)
                    tv.event_generate("<<TreeviewSelect>>")
                    top.update()
                    shown_orig = d["orig"].get("1.0", "end").strip()
                    shown_trans = d["trans"].get("1.0", "end").strip()
                    self.assertEqual(texts[shown_orig], shown_trans, f"{key}: row {iid}")
                    self.assertEqual(shown_orig, tv.item(iid, "values")[0], f"{key}: the clicked row is the one shown")
            top.destroy()
        finally:
            bulk.cache_path("pt-BR", "y.mod").unlink(missing_ok=True)

    def test_the_confirmation_counts_only_the_mods_that_will_be_done(self):
        from unittest import mock
        app = self._app_with_mods(("pt-BR", "es", "ja"))
        app.render_rows()
        app.sel_ids = {"b.mod"}                                     # one mod ticked out of two
        asked = []
        with mock.patch("rwtranslate.bulk.run", return_value=[]), \
                mock.patch.object(app, "ask_yes_no", side_effect=lambda t, m: asked.append(m) or True), \
                mock.patch.object(app, "run_bg", side_effect=lambda work, done: done(work(), None)):
            app.start_bulk(True)
        self.assertEqual(len(asked), 1)
        self.assertIn("1 mod", asked[0])
        self.assertNotIn("2 mods", asked[0])

    def test_export_button_writes_the_ticked_mods_in_the_ticked_languages(self):
        from unittest import mock
        app = self._app_with_mods(("pt-BR", "ja"))
        app.render_rows()
        app.update_bulk_buttons()
        self.assertEqual(str(app.btn_export.cget("state")), "normal")
        self.assertEqual(app.btn_export.cget("text"), "Exportar traduções")
        app.sel_ids = {"b.mod"}
        calls = []

        def fake_export(mods, langs, dest):
            calls.append(([m.package_id for m in mods], list(langs), str(dest)))
            return {"mods": 1, "files": 3, "texts": 9, "languages": ["pt-BR", "ja"], "folder": str(dest)}
        with mock.patch("rwtranslate.export.export_all", side_effect=fake_export), \
                mock.patch.object(app, "choose_export_folder", return_value="/tmp/out-x"), \
                mock.patch("rwtranslate.gui.open_folder") as opened, \
                mock.patch.object(app, "run_bg", side_effect=lambda work, done: done(work(), None)):
            app.export_translations()
        self.assertEqual(calls, [(["b.mod"], ["pt-BR", "ja"], "/tmp/out-x")], "only the ticked mod, in every ticked language")
        self.assertIn("2 idioma(s)", app.bulk_progress.get())
        opened.assert_called_once()
        # nothing chosen: nothing happens
        with mock.patch("rwtranslate.export.export_all") as exp, mock.patch.object(app, "choose_export_folder", return_value=None):
            app.export_translations()
        exp.assert_not_called()

    def test_languages_window_has_the_buttons_under_the_game_language_and_the_wheel_works_anywhere(self):
        app = self._app_with_mods(("pt-BR", "es"))
        top = app.open_languages_dialog()
        top.update()
        row = {int(w.grid_info()["row"]): w for w in top.grid_slaves() if w.grid_info()}
        self.assertEqual(row[1].winfo_children()[0].cget("text"), app.t("dlg_game"), "the game language comes first")
        self.assertEqual(row[2].grid_info()["sticky"], "e", "the tick-all buttons are at the right, below it")
        self.assertTrue(top.bind("<MouseWheel>"), "the wheel is handled by the whole window, not only by the bar")
        top.destroy()

    def test_details_window_shows_one_language_and_edits_only_that_language(self):
        from rwtranslate import bulk, config
        app = self._app_with_mods(("pt-BR", "ja"))
        mod = type("M", (), {"package_id": "l.mod", "name": "L", "path": "x"})()
        app.plan_rows = [(mod, "ok", {"texts": 1, "words": 2})]
        bulk.write_cache("pt-BR", "l.mod", {"Medkit": "Kit médico"})
        bulk.write_cache("ja", "l.mod", {"Medkit": "医療キット"})
        files = [bulk.overrides_path("pt-BR"), bulk.overrides_path("ja")]
        had = [f.exists() for f in files]
        try:
            top = app.show_details("l.mod")
            top.update()
            self.assertEqual(top.det_lang, "pt-BR", "the game's language is shown first")
            self.assertEqual(len(top.lang_box.cget("values")), 2, "every language that has this mod translated is offered")
            top.det_lang = "ja"
            app._fill_details(top)
            top.update()
            tv = top.details["translated"]
            self.assertEqual([v[1] for v in tv.shown_values()], ["医療キット"])
            tv.selection_set(tv.get_children()[0])
            tv.event_generate("<<TreeviewSelect>>")
            top.update()
            top.details["trans"].delete("1.0", "end")
            top.details["trans"].insert("end", "メディキット")
            top.details["trans"].focus_force()
            top.update()
            top.details["trans"].event_generate("<KeyRelease>", when="now")
            top.update()
            top.details["save"].invoke()
            self.assertEqual(bulk.read_cache("ja", "l.mod")["Medkit"], "メディキット")
            self.assertEqual(bulk.read_overrides("ja")["Medkit"], "メディキット")
            self.assertEqual(bulk.read_cache("pt-BR", "l.mod")["Medkit"], "Kit médico", "the other language is untouched")
            self.assertNotIn("Medkit", bulk.read_overrides("pt-BR"))
            self.assertEqual(top.det_lang, "ja", "and the window stays on the language being edited")
            top.destroy()
        finally:
            bulk.cache_path("pt-BR", "l.mod").unlink(missing_ok=True)
            bulk.cache_path("ja", "l.mod").unlink(missing_ok=True)
            for f, h in zip(files, had):
                if not h:
                    f.unlink(missing_ok=True)

    def test_details_window_can_edit_save_and_restore_a_translation(self):
        from unittest import mock
        from rwtranslate import bulk, config
        app = self.build(fake_fetcher(release_json("v0.0")))
        config.set("target", "pt-BR")
        app.lang_codes = {"Português (Brasil)": "pt-BR"}
        app.lang_box.configure(values=["Português (Brasil)"])
        app.lang_box.set("Português (Brasil)")
        pump(self.root, lambda: app.bulk_current.get() == "")
        app.refresh_plan = lambda: None
        mod = type("M", (), {"package_id": "e.mod", "name": "E", "path": "x"})()
        app.plan_rows = [(mod, "ok", {"texts": 2, "words": 4})]
        app.render_rows()
        bulk.write_cache("pt-BR", "e.mod", {"Tend Self": "Tenda-se a si mesmo", "Medkit": "Kit médico"})
        ov_file = bulk.overrides_path("pt-BR")
        had_ov = ov_file.exists()
        try:
            top = app.show_details("e.mod")
            d = top.details
            tv = d["translated"]
            row = next(i for i in tv.get_children() if tv.item(i, "values")[0] == "Tend Self")
            tv.selection_set(row)
            tv.event_generate("<<TreeviewSelect>>")
            top.update()
            self.assertEqual(str(d["save"].cget("state")), "disabled", "nothing changed yet")
            self.assertEqual(str(d["restore"].cget("state")), "disabled", "nothing to restore yet")
            d["trans"].delete("1.0", "end")
            d["trans"].insert("end", "Cure-se a si mesmo")
            d["trans"].focus_force()
            top.update()
            d["trans"].event_generate("<KeyRelease>", when="now")
            top.update()
            self.assertEqual(str(d["save"].cget("state")), "normal")
            d["save"].invoke()
            self.assertEqual(bulk.read_cache("pt-BR", "e.mod")["Tend Self"], "Cure-se a si mesmo", "the saved translations of the mod have it")
            self.assertEqual(bulk.read_overrides("pt-BR")["Tend Self"], "Cure-se a si mesmo", "and it is a manual correction the mod keeps")
            self.assertTrue(bulk.has_override("pt-BR", "Tend Self"))
            self.assertIn("Cure-se", [v[1] for v in top.details["translated"].shown_values() if v[0] == "Tend Self"][0])
            # the row stays selected after the redraw and the restore button is available now
            top.details["translated"].selection_set(next(i for i in top.details["translated"].get_children() if top.details["translated"].item(i, "values")[0] == "Tend Self"))
            top.details["translated"].event_generate("<<TreeviewSelect>>")
            top.update()
            self.assertEqual(str(top.details["restore"].cget("state")), "normal")
            # restore: the correction goes away and the text is translated again by the program
            with mock.patch("rwtranslate.server.translate_texts", return_value=["Tenda-se a si mesmo (auto)"]), \
                    mock.patch.object(app, "run_bg", side_effect=lambda work, done: done(work(), None)):
                top.details["restore"].invoke()
            self.assertFalse(bulk.has_override("pt-BR", "Tend Self"))
            self.assertEqual(bulk.read_cache("pt-BR", "e.mod")["Tend Self"], "Tenda-se a si mesmo (auto)")
            top.destroy()
        finally:
            bulk.cache_path("pt-BR", "e.mod").unlink(missing_ok=True)
            if not had_ov:
                ov_file.unlink(missing_ok=True)

    def test_a_short_list_starts_at_the_top_of_the_table(self):
        import tkinter
        from rwtranslate import gui
        self.build(fake_fetcher(release_json("v0.0")))
        f = tkinter.Toplevel(self.root)
        f.geometry("700x500")
        tbl = gui.text_table_class()(f, ["o", "t"])
        tbl.heading("o", text="Original")
        tbl.heading("t", text="Tradução")
        tbl.pack(fill="both", expand=True)
        for i in range(5):
            tbl.insert("", "end", values=[f"text {i}", f"texto {i}"])
        self.root.update()
        tbl._flush()
        self.root.update()
        self.assertEqual(tbl._canvas.canvasy(0), 0, "the view starts at the first row, not centred or at the bottom of a taller window")
        tbl.set_wrap(True)
        self.root.update()
        self.assertEqual(tbl._canvas.canvasy(0), 0)
        f.geometry("700x700")                                         # a taller window: still at the top
        self.root.update()
        self.assertEqual(tbl._canvas.canvasy(0), 0)
        self.assertGreaterEqual(tbl._region_h, tbl._canvas.winfo_height())
        f.destroy()

    def test_details_window_has_filter_and_wrap_switch(self):
        from rwtranslate import bulk, config
        app = self.build(fake_fetcher(release_json("v0.0")))
        config.set("target", "pt-BR")
        app.lang_codes = {"Português (Brasil)": "pt-BR"}
        app.lang_box.configure(values=["Português (Brasil)"])
        app.lang_box.set("Português (Brasil)")
        pump(self.root, lambda: app.bulk_current.get() == "")                  # the scan started at launch must finish first (it replaces plan_rows)
        app.refresh_plan = lambda: None                                          # ...and no new scan may wipe the fake mod below
        mod = type("M", (), {"package_id": "z.mod", "name": "Z", "path": "x"})()
        app.plan_rows = [(mod, "ok", {"texts": 2, "words": 4})]
        app.render_rows()
        bulk.write_cache("pt-BR", "z.mod", {"Iron sword": "Espada de ferro", "Medkit": "Kit médico"})
        try:
            top = app.show_details("z.mod")
            d = top.details
            self.assertEqual(len(d["translated"].get_children()), 2)
            top.update()
            d["filter"].focus_force()
            top.update()
            d["filter"].insert(0, "iron")
            d["filter"].event_generate("<KeyRelease>", when="now")
            self.assertEqual(len(d["translated"].get_children()), 1)
            self.assertEqual(d["nb"].tab(0, "text"), "Textos traduzidos (1/2)")
            self.assertEqual(top.filter_text, "iron")
            app.set_lang("en")                                              # the filter survives a redraw in another language
            self.assertEqual(len(top.details["translated"].get_children()), 1)
            self.assertEqual(top.details["filter"].get(), "iron")
            app.set_lang("pt")
            top.details["wrap"].invoke()
            self.assertTrue(top.details["translated"].wrap)
            self.assertTrue(config.get("details_wrap"))
            self.assertEqual(top.details["wrap"]._style, "blue", "pressed look while on")
            top.details["wrap"].invoke()
            self.assertFalse(top.details["translated"].wrap)
            self.assertEqual(top.details["wrap"]._style, "neutral")
            top.destroy()
        finally:
            bulk.cache_path("pt-BR", "z.mod").unlink(missing_ok=True)
            config.set("details_wrap", False)

    def test_justified_text_fills_every_line_and_copies_as_plain_text(self):
        import tkinter.font as tkfont
        from rwtranslate import gui
        self.build(fake_fetcher(release_json("v0.0")))
        import tkinter
        Sel = gui.selectable_label_class()
        frame = tkinter.Frame(self.root, width=380, height=260)           # a fixed-width box: the number of lines does not depend on the window
        frame.pack_propagate(False)
        frame.place(x=0, y=0)
        text = ("Deixe esta janela aberta enquanto joga RimWorld. O jogo pede e o programa traduz sozinho, mod por mod, e salva tudo. "
                "Serve para os mods ativados e para os textos que só existem durante o jogo.\n\nSegundo parágrafo curto.")
        lab = Sel(frame, text=text, anchor="w", justify="fill")
        lab.pack(fill="x", padx=10, pady=10)
        for _ in range(8):
            self.root.update()
        font = tkfont.nametofont("TkDefaultFont")
        avail = lab.winfo_width() - 2
        lines = lab.get("1.0", "end-1c").split("\n")
        self.assertGreater(len(lines), 3)
        body = lines[:lines.index("")]                                        # the first paragraph
        for ln in body[:-1]:
            self.assertAlmostEqual(font.measure(ln), avail, delta=4, msg="a justified line is as wide as the box: " + ln)
        self.assertLess(font.measure(body[-1]), avail - 20, "the last line of a paragraph is not stretched")
        self.assertEqual(int(str(lab.cget("height"))), len(lines))
        lab._select_all()
        lab._copy()
        self.assertEqual(self.root.clipboard_get(), text, "what you paste is the plain text, in a single paragraph")
        lab.destroy()
        frame.destroy()

    def test_polite_run_waits_while_the_game_is_asking(self):
        import time
        from rwtranslate import bulk, server
        old = bulk.POLITE_QUIET_S
        try:
            bulk.POLITE_QUIET_S = 0.3
            bulk._polite = True
            server.LAST_GAME_REQUEST = time.time()
            t0 = time.time()
            bulk._wait_for_game(None)
            self.assertGreaterEqual(time.time() - t0, 0.25, "waited for the game to go quiet")
            t0 = time.time()
            bulk._wait_for_game(None)
            self.assertLess(time.time() - t0, 0.2, "no wait when the game is quiet")
            bulk._polite = False
            server.LAST_GAME_REQUEST = time.time()
            t0 = time.time()
            bulk._wait_for_game(None)
            self.assertLess(time.time() - t0, 0.2, "a run started by the player never waits")
        finally:
            bulk.POLITE_QUIET_S = old
            bulk._polite = False
            server.LAST_GAME_REQUEST = 0.0

    def test_changelog_button_opens_github_and_the_update_message_has_no_notes(self):
        from unittest import mock
        from rwtranslate import gui
        app = self.build(fake_fetcher(release_json("v9.0")))
        self.assertTrue(pump(self.root, lambda: "Nova versão disponível: v9.0" in app.update_msg.get()), app.update_msg.get())
        self.assertNotIn("\n", app.update_msg.get().strip(), "only the version line: the notes are on GitHub")
        self.assertEqual(str(app.btn_changelog.cget("text")), "Ver changelog")
        with mock.patch.object(gui.webbrowser, "open") as op:
            app.btn_changelog.invoke()
        op.assert_called_once_with("https://github.com/Unknown1210/rimworld-universal-translate-mods/blob/main/CHANGELOG.md")

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
        long_text = {k: v + " " + "extra" * 6 for k, v in i18n.TEXT["en"].items() if k in ("tab_home", "tab_bulk", "tab_log", "check_btn", "apply_btn", "data_folder_btn", "mod_folder_btn", "report_btn", "github_btn", "quit_btn", "col_mod", "col_source", "col_texts", "col_words", "col_state", "col_folder")}
        i18n.TEXT["xx"] = {**i18n.TEXT["en"], **long_text}
        try:
            app.lang = "xx"
            app.apply_language()
            self.root.update()
            self.assertGreaterEqual(self.root.winfo_width(), self.root.winfo_reqwidth())      # the window grew to fit
            for b in (app.btn_check, app.btn_apply, app.btn_data, app.btn_modfolder, app.btn_report, app.btn_github, app.btn_quit):
                self.assertGreaterEqual(b.winfo_width(), b.winfo_reqwidth())
            for c in app.tree["columns"]:
                self.assertGreaterEqual(int(app.tree.column(c, "width")), len(app.tree.heading(c, "text")) * 4)
            self.assertGreaterEqual(int(str(app.ui_box.cget("width"))), max(len(v) for v in app.ui_box.cget("values")))
        finally:
            del i18n.TEXT["xx"]

    def test_folder_buttons_open_the_data_folder_and_the_installed_mod(self):
        from unittest import mock
        from rwtranslate import gui
        d = Path(tempfile.mkdtemp())
        mods = d / "workshop" / "294100"
        ours = mods / "123456789"
        (ours / "About").mkdir(parents=True)
        (ours / "About" / "About.xml").write_text("<ModMetaData><packageId>unknown1210.autotranslate</packageId></ModMetaData>")
        other = mods / "555"
        (other / "About").mkdir(parents=True)
        (other / "About" / "About.xml").write_text("<ModMetaData><packageId>someone.else</packageId></ModMetaData>")
        app = self.build(fake_fetcher(release_json("v0.0")), mod_dirs=[str(mods)])
        self.assertEqual(str(app.btn_data.cget("text")), "Abrir pasta de dados")
        self.assertFalse(hasattr(app, "btn_data2"))                                      # the folder buttons are on the Home tab only
        self.assertFalse(hasattr(app, "btn_logs"))                                      # the logs button of the Home tab was replaced
        with mock.patch.object(gui, "open_folder") as op:
            app.btn_data.invoke()
            self.assertEqual(op.call_args_list[0][0][0], gui.data_dir())
            app.btn_modfolder.invoke()                                                    # found in the Workshop-like folder
            self.assertEqual(Path(op.call_args_list[1][0][0]), ours)
        app.mod_dirs_override = []
        with mock.patch("tkinter.messagebox.showinfo") as info, mock.patch.object(gui, "open_folder") as op:
            app.btn_modfolder.invoke()
            self.assertEqual(op.call_count, 0)
            self.assertIn("Auto Translate Mods", info.call_args[0][1])                    # told, not silent

    def test_every_text_exists_in_both_languages(self):
        from rwtranslate import i18n
        self.assertEqual(set(i18n.TEXT["pt"]), set(i18n.TEXT["en"]))

    def test_layout_is_responsive(self):
        app = self.build(fake_fetcher(release_json("v0.0")))
        self.root.geometry("900x500")                             # (the window can not be narrower than its widgets need)
        pump(self.root, lambda: False, timeout=0.3)
        small = int(str(app.update_msg.label.cget("wraplength")))
        small_btn = app.btn_check.winfo_width()
        self.root.geometry("1100x500")
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

    def test_game_translations_show_up_in_the_mods_table(self):
        """The game translates by itself (the mod asks this program, saves the result in the cache): the table must follow."""
        from rwtranslate import activity, bulk, config, gui, server
        config.set("target", "pt-BR")
        root = Path(tempfile.mkdtemp())
        self.mod(root, "A", "a.mod", "Alpha Mod", "<ThingDef><defName>X</defName><label>iron sword</label><description>A sharp sword for fighting.</description></ThingDef>")
        httpd = server.serve(0)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        r = tkinter.Tk()
        try:
            app = gui.App(r, httpd, fetcher=fake_fetcher(release_json("v0.0")), lang="pt", mod_dirs=[root])
            self.assertTrue(pump(r, lambda: len(app.plan_rows) == 1), "scan lists the mod")
            iid = app.rows["a.mod"]
            self.assertEqual(str(app.tree.item(iid, "values")[3]), "0")                       # nothing translated yet: zeroed, as before
            self.assertEqual(str(app.tree.item(iid, "values")[5]), "Novo (não traduzido)")
            bulk.write_cache("pt-BR", "a.mod", {"iron sword": "espada de ferro", "A sharp sword for fighting.": "Uma espada afiada para lutar."})
            activity.emit("game", "log_game_batch", {"n": 2, "src": "en", "tgt": "pt-BR", "mod": "A.Mod", "chars": 38, "ms": 5, "first": ""},
                          pairs=[("iron sword", "espada de ferro"), ("A sharp sword for fighting.", "Uma espada afiada para lutar.")])
            self.assertTrue(pump(r, lambda: "jogo" in str(app.tree.item(iid, "values")[5])), "the row follows the game")
            vals = [str(v) for v in app.tree.item(iid, "values")]
            self.assertEqual((vals[2], vals[3], vals[4]), ("en", "2", "7"))                    # source language, texts, words (2 + 5)
            self.assertEqual(vals[5], "Traduzindo pelo jogo...")
            self.assertIn("Palavras traduzidas: 7", app.bulk_summary.get())                                 # the summary line adds it up too
            app.game_live[("pt-BR", "a.mod")]["last"] -= 100                                    # the game goes quiet
            app.refresh_live_rows()
            self.assertEqual(str(app.tree.item(iid, "values")[5]), "Traduzido pelo jogo")
            # a mod translated by the game in an earlier run (nothing live): the numbers come from its saved translations
            app.game_live.clear()
            app.render_rows()
            vals = [str(v) for v in app.tree.item(app.rows["a.mod"], "values")]
            self.assertEqual((vals[3], vals[4], vals[5]), ("2", "7", "Traduzido pelo jogo"))
            # and the details window shows what was translated
            top = app.show_details("a.mod")
            tv = top.details["translated"]
            self.assertEqual(len(tv.get_children()), 2)
            top.destroy()
        finally:
            bulk.cache_path("pt-BR", "a.mod").unlink(missing_ok=True)                            # the next test uses a mod with the same id
            httpd.shutdown()
            r.destroy()

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
            # every tag ("[padrão]", "[adicionada por você]", "[não encontrada]") is a separate label stuck to the right edge
            self.assertTrue(all(tg is not None and str(tg.grid_info()["sticky"]) == "e" for _p, tg in app.dir_labels))
            self.assertEqual(str(app.dir_labels[0][1].cget("text")), "[adicionada por você]")
            self.assertNotIn("[adicionada por você]", app.dir_labels[0][0].cget("text"))
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
            self.assertEqual([str(v[5]) for v in rows], ["Traduzido", "Traduzido"])
            alpha = next(v for v in rows if v[1] == "Alpha Mod")
            self.assertEqual((str(alpha[2]), int(alpha[3]), int(alpha[4])), ("en", 2, 2 + 5), "source language, texts and words per mod")
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
            bx, by, bw, bh = app.tree.bbox(iid, "#7")
            ev = type("Ev", (), {"x": bx + bw // 2, "y": by + bh // 2})()
            self.assertEqual(app.tree.item(iid, "values")[6], "Abrir pasta")
            self.assertEqual(app.on_tree_click(ev), "break")
            self.assertEqual(opened, [str(root / "A")], "clicking the folder column opens the mod folder")
            bx, by, bw, bh = app.tree.bbox(iid, "#2")
            ev1 = type("Ev", (), {"x": bx + 5, "y": by + bh // 2})()
            self.assertIsNone(app.on_tree_click(ev1))
            self.assertEqual(len(opened), 1, "clicking another column does not open the folder")
            bx, by, bw, bh = app.tree.bbox(iid, "#1")                                  # the first column ticks the mod
            tick = type("Ev", (), {"x": bx + bw // 2, "y": by + bh // 2})()
            self.assertEqual(app.on_tree_click(tick), "break")
            self.assertEqual(app.selected_ids(), {"a.mod"})
            self.assertEqual(app.tree.item(iid, "values")[0], app.BOX_ON)
            app.toggle_all_selected()
            app.toggle_all_selected()
            app.sel_ids.clear()
            app.update_selection_ui()
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
            self.assertIn("sword", top.details["orig"].get("1.0", "end"))
            self.assertIn("(pt)", top.details["trans"].get("1.0", "end"))
            self.assertIn("Detalhes: Alpha Mod", top.title())
            # a text that failed: red row on top, the window opens on that tab and says why it failed
            entry = app._details_entry("a.mod")
            saved = dict(entry[2] or {})
            saved["failed"] = 1
            saved["skipped"] = list(saved.get("skipped", [])) + [{"text": "broken text", "reason": "failed", "detail": "EngineError: boom"}]
            real_rows = app.plan_rows
            app.plan_rows = [(m, st, (saved if m.package_id == "a.mod" else rr)) for m, st, rr in app.plan_rows]
            top2 = app.show_details("a.mod")
            sk = top2.details["skipped"]
            first = sk.get_children()[0]
            self.assertIn("failed", sk.item(first, "tags"), "the failed text is a red row, on top")
            self.assertEqual(top2.details["nb"].index(top2.details["nb"].select()), 2, "the window opens on the tab with the failures")
            self.assertIn("EngineError: boom", top2.details["why"].get("1.0", "end"))
            self.assertIn("\u26a0", top2.details["nb"].tab(2, "text"))
            top2.destroy()
            app.details_windows = [w for w in app.details_windows if w is not top2]
            app.plan_rows = real_rows
            # 3c) with the details window OPEN, changing the language of the main window redraws it too (same tab, same row)
            app.set_lang("en")
            self.assertEqual(top.title(), "Details: Alpha Mod")
            self.assertEqual(top.details["nb"].tab(0, "text"), "Translated texts (2)")
            self.assertEqual(top.details["nb"].tab(1, "text"), "Words translated (7)")
            self.assertEqual(top.details["skipped"].heading("e")["text"], "Existing translation")
            self.assertEqual(top.details["translated"].heading("o")["text"], "Original")
            self.assertEqual(top.details["translated"].heading("t")["text"], "Translation")
            self.assertIn("(pt)", top.details["trans"].get("1.0", "end"), "the selected row stays selected after the language change")
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
            self.assertEqual({app.tree.item(i, "values")[5] for i in app.tree.get_children()}, {"Translated", "New (not translated)"})
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
