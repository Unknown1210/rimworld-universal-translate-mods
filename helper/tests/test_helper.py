import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["RWTRANSLATE_HOME"] = tempfile.mkdtemp()

from rwtranslate import languages, models as models_mod, protect, server  # noqa: E402
from rwtranslate.engine import split_sentences, set_engine  # noqa: E402

DICT = {"The colonist": "O colono", " was hit by ": " foi atingido por ", "a raider": "um invasor",
        "Hello": "Olá", "Hello world.": "Olá mundo."}


def fake(texts):
    """Word-ish translator; leaves unknown text alone."""
    out = []
    for t in texts:
        for k, v in DICT.items():
            t = t.replace(k, v)
        out.append(t)
    return out


def mangling(texts):
    """Evil translator that destroys every [n] token."""
    return [protect._TOKEN_RE.sub("", fake([t])[0]) for t in texts]


class Protect(unittest.TestCase):
    def test_markers_survive_token_path(self):
        s = "The colonist {0} was hit by <color=#ff0000>a raider</color>."
        r = protect.translate_protected(s, fake)
        self.assertEqual(r, "O colono {0} foi atingido por <color=#ff0000>um invasor</color>.")

    def test_markers_survive_when_translator_mangles_tokens(self):
        s = "The colonist {0} was hit by <color=#ff0000>a raider</color>."
        r = protect.translate_protected(s, mangling)
        for m in ("{0}", "<color=#ff0000>", "</color>"):
            self.assertIn(m, r)
        self.assertIn("um invasor", r)

    def test_no_text_untouched(self):
        self.assertEqual(protect.translate_protected("{0}\\n{1}", fake), "{0}\\n{1}")
        self.assertEqual(protect.translate_protected("123", fake), "123")

    def test_source_with_token_like_text_uses_fallback(self):
        s = "Hello [0] {x}"
        self.assertIsNone(protect.to_tokens(s))
        self.assertEqual(protect.translate_protected(s, fake), "Olá [0] {x}")

    def test_whitespace_preserved(self):
        self.assertEqual(protect.translate_protected("  Hello  ", fake), "  Olá  ")

    def test_rimworld_color_tags_and_newlines(self):
        s = "(*Name)Hello(/Name)\nHello"
        r = protect.translate_protected(s, mangling)
        self.assertEqual(r, "(*Name)Olá(/Name)\nOlá")


class Lang(unittest.TestCase):
    def test_game_names(self):
        self.assertEqual(languages.code_from_game_language("Português Brasileiro"), "pt-BR")
        self.assertEqual(languages.code_from_game_language("PortugueseBrazilian"), "pt-BR")
        self.assertEqual(languages.code_from_game_language("Português"), "pt-PT")
        self.assertEqual(languages.code_from_game_language("Portuguese"), "pt-PT")
        self.assertEqual(languages.code_from_game_language("Español Latino"), "es-419")
        self.assertEqual(languages.code_from_game_language("English"), "en")
        self.assertIsNone(languages.code_from_game_language("Klingon"))

    def test_suggest_rules(self):
        self.assertEqual(languages.suggest("Français", system="pt"), "fr")      # game wins
        self.assertEqual(languages.suggest("English", system="pt"), "pt-BR")    # english game -> system (Portuguese without a region: Brazil)
        self.assertEqual(languages.suggest("Portuguese"), "pt-PT")              # the game's own Portuguese is the European one
        self.assertIsNone(languages.suggest("English", system="en"))            # ask user
        self.assertEqual(languages.suggest(None, system="de"), "de")

    def test_portuguese_variants(self):
        self.assertEqual(languages.norm_target("pt"), "pt-BR")                  # old settings
        self.assertEqual(languages.norm_target("pt_br"), "pt-BR")
        self.assertEqual(languages.norm_target("PT-pt"), "pt-PT")
        self.assertEqual(languages.norm_target("JA"), "ja")
        self.assertEqual(languages.model_code("pt-BR"), "pb")
        self.assertEqual(languages.model_code("pt-PT"), "pt")
        self.assertEqual(languages.model_code("pt"), "pt", "a plain pt is a source language and keeps its model")
        self.assertEqual(languages.model_code("es"), "es")
        self.assertTrue(languages.same("pt", "pt-BR") and languages.same("pb", "pt-PT") and not languages.same("pt-BR", "es"))
        from rwtranslate import models
        idx = [{"from_code": "en", "to_code": "pb"}, {"from_code": "pb", "to_code": "en"}, {"from_code": "en", "to_code": "pt"}]
        self.assertEqual(models.plan("en", "pt-BR", idx), [("en", "pb")], "Brazil uses its own model")
        self.assertEqual(models.plan("en", "pt-PT", idx), [("en", "pt")])
        self.assertEqual(models.plan("pt", "pt-BR", idx), [], "same language: nothing to translate")
        self.assertEqual(models.available_targets(idx), ["pt-BR", "pt-PT"])

    def test_old_pt_settings_become_brazilian(self):
        from rwtranslate import config
        from rwtranslate.paths import data_dir
        old, new = data_dir() / "cache" / "pt", data_dir() / "translated mods" / "pt-BR"
        had_new = new.exists()
        old_target = config.get("target")
        try:
            if not had_new:
                old.mkdir(parents=True, exist_ok=True)
                (old / "m.json").write_text("{}")
                config.set("target", "pt")
                config.migrate_portuguese()
                self.assertTrue((new / "m.json").exists() and not old.exists(), "saved translations moved to pt-BR")
                self.assertEqual(config.get("target"), "pt-BR")
        finally:
            config.set("target", old_target)
            if not had_new and new.exists():
                import shutil
                shutil.rmtree(new, ignore_errors=True)

    def test_sentences(self):
        self.assertEqual(split_sentences("One. Two! Three?"), ["One.", "Two!", "Three?"])
        self.assertEqual(split_sentences("Value is 3.5 units"), ["Value is 3.5 units"])


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        set_engine("en", "pt", type("E", (), {"translate_batch": staticmethod(fake)})())
        cls.httpd = server.serve(0)
        cls.port = cls.httpd.server_address[1]
        cls.token = server.load_or_create_token()
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def call(self, path, body=None, token="default", headers=None):
        h = {"X-Token": self.token if token == "default" else token}
        h.update(headers or {})
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, headers=h)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def test_health_and_suggest(self):
        self.assertEqual(self.call("/health")[0], 200)
        c, j = self.call("/suggest?game=Fran%C3%A7ais")
        self.assertEqual(j["suggested"], "fr")

    def test_game_requests_are_written_to_the_activity_log(self):
        """The Log tab shows what the game asked for: the mod and every original text with its translation."""
        from rwtranslate import activity
        activity.clear()
        c, j = self.call("/translate", {"target": "pt", "mod": "somebody.searchandrescue", "texts": ["Search and rescue", "Rescue all"]})
        self.assertEqual(c, 200)
        games = [e for e in activity.snapshot() if e.kind == "game"]
        self.assertEqual(len(games), 1)
        e = games[0]
        self.assertEqual((e.key, e.args["mod"], e.args["n"], e.args["src"], e.args["tgt"]), ("log_game_batch", "somebody.searchandrescue", 2, "en", "pt"))
        self.assertEqual([a for a, _b in e.pairs], ["Search and rescue", "Rescue all"])
        self.assertEqual([b for _a, b in e.pairs], j["translations"], "each original is listed with its translation")
        self.assertIn("Search and rescue", e.detail_text())
        c, j = self.call("/translate", {"target": "pt", "texts": ["Hello"]})                  # an older mod version sends no mod name
        self.assertEqual([x for x in activity.snapshot() if x.kind == "game"][-1].args["mod"], "?")

    def test_translate(self):
        c, j = self.call("/translate", {"target": "pt", "texts": ["Hello", "The colonist {0} was hit by a raider"]})
        self.assertEqual(c, 200)
        self.assertEqual(j["translations"], ["Olá", "O colono {0} foi atingido por um invasor"])

    def test_requires_token(self):
        self.assertEqual(self.call("/health", token="wrong")[0], 401)
        self.assertEqual(self.call("/health", token="")[0], 401)

    def test_rejects_browser_origin(self):
        self.assertEqual(self.call("/health", headers={"Origin": "http://evil.example"})[0], 403)

    def test_rejects_foreign_host(self):
        self.assertEqual(self.call("/health", headers={"Host": "evil.example"})[0], 403)

    def test_source_language_and_same_language(self):
        set_engine("zh", "pt", type("E", (), {"translate_batch": staticmethod(lambda ts: [t + " <zh>" for t in ts])})())
        c, j = self.call("/translate", {"source": "zh", "target": "pt", "texts": ["你好"]})
        self.assertEqual((c, j["translations"]), (200, ["你好 <zh>"]))
        c, j = self.call("/translate", {"source": "pt", "target": "pt", "texts": ["Olá mundo"]})
        self.assertEqual(j["translations"], ["Olá mundo"])                       # same language: returned untouched
        self.assertEqual(self.call("/translate", {"source": "p1", "target": "pt", "texts": ["a"]})[0], 400)
        self.assertEqual(self.call("/health")[1]["protocol"], 2)

    def test_support_endpoint(self):
        c, j = self.call("/support?source=en&target=pt")                      # fake engine pair registered above
        self.assertEqual(c, 200)
        self.assertIn("supported", j)
        self.assertEqual(self.call("/support?source=e1&target=pt")[0], 400)

    def test_missing_model_and_bad_input(self):
        self.assertEqual(self.call("/translate", {"target": "zz", "texts": ["a"]})[0], 409)
        self.assertEqual(self.call("/translate", {"target": "pt", "texts": "a"})[0], 400)
        self.assertEqual(self.call("/translate", {"target": "pt", "texts": [1]})[0], 400)


if __name__ == "__main__":
    unittest.main()


try:
    import sentencepiece  # noqa: F401
    HAVE_SP = True
except ImportError:
    HAVE_SP = False


@unittest.skipUnless(HAVE_SP, "needs sentencepiece (pip install ./helper)")
class Detokenize(unittest.TestCase):
    """Regression: translations came back as "_mesa_elétrica_de_cortador..." (SentencePiece marker shown by the game)."""

    @classmethod
    def setUpClass(cls):
        import random
        import sentencepiece as spm
        random.seed(1)
        words = "mesa elétrica de cortador pedra uma trabalho avançada com serras para cortar blocos the table of stone".split()
        d = tempfile.mkdtemp()
        open(os.path.join(d, "c.txt"), "w").write("\n".join(" ".join(random.choice(words) for _ in range(8)) for _ in range(1500)))
        spm.SentencePieceTrainer.train(input=os.path.join(d, "c.txt"), model_prefix=os.path.join(d, "t"), vocab_size=100,
                                       model_type="unigram", hard_vocab_limit=False, minloglevel=2)
        cls.sp = spm.SentencePieceProcessor(model_file=os.path.join(d, "t.model"))

    def test_plain_pieces(self):
        from rwtranslate.engine import detokenize
        toks = self.sp.encode("mesa elétrica de cortador de pedra", out_type=str)
        self.assertEqual(detokenize(self.sp, toks), "mesa elétrica de cortador de pedra")

    def test_joined_piece_still_loses_the_marker(self):
        from rwtranslate.engine import detokenize
        toks = ["".join(self.sp.encode("mesa elétrica de pedra", out_type=str))]      # decode() would leave "▁mesa▁elétrica..."
        self.assertEqual(self.sp.decode(toks), "▁mesa▁elétrica▁de▁pedra")             # proves the original bug
        self.assertEqual(detokenize(self.sp, toks), "mesa elétrica de pedra")


class CleanOutput(unittest.TestCase):
    def test_marker_and_edges_removed(self):
        self.assertEqual(protect.clean_output("stone table", "▁mesa▁de▁pedra", "pt"), "mesa de pedra")
        self.assertEqual(protect.clean_output("stone table", "  mesa de pedra ", "pt"), "mesa de pedra")

    def test_first_letter_follows_the_source(self):
        # lowercase label: the game capitalises it itself, so the model's capital must not leak mid-sentence
        self.assertEqual(protect.clean_output("electric stonecutter's table", "Mesa elétrica", "pt"), "mesa elétrica")
        # description starts uppercase: keep it uppercase
        self.assertEqual(protect.clean_output("An advanced work table.", "uma mesa avançada.", "pt"), "Uma mesa avançada.")
        # acronyms and German nouns are left alone
        self.assertEqual(protect.clean_output("hit points", "HP total", "pt"), "HP total")
        self.assertEqual(protect.clean_output("table", "Tisch", "de"), "Tisch")

    def test_bare_label_gets_no_full_stop(self):
        self.assertEqual(protect.clean_output("safe", "Seguro.", "pt"), "seguro")
        self.assertEqual(protect.clean_output("A safe.", "Um cofre.", "pt"), "Um cofre.")
        self.assertEqual(protect.clean_output("wait...", "espere...", "pt"), "espere...")

    def test_glossary_fixes_ambiguous_label(self):
        set_engine("en", "pt", type("E", (), {"translate_batch": staticmethod(lambda ts: ["Seguro." for _ in ts])})())
        self.assertEqual(server.translate_texts("en", "pt", ["safe", "Safe"]), ["cofre", "Cofre"])
        self.assertEqual(server.translate_texts("en", "pt-BR", ["safe"]), ["cofre"])
        self.assertEqual(server.translate_texts("en", "pt", ["safe room"]), ["seguro"])     # only whole-text matches

    def test_server_applies_it(self):
        set_engine("en", "pt", type("E", (), {"translate_batch": staticmethod(lambda ts: ["▁Mesa▁elétrica" for _ in ts])})())
        self.assertEqual(server.translate_texts("en", "pt", ["electric table"]), ["mesa elétrica"])


class WindowLanguages(unittest.TestCase):
    def setUp(self):
        from rwtranslate import i18n, uitext
        self.i18n, self.uitext = i18n, uitext
        uitext.forget()

    def test_the_window_offers_exactly_the_rimworld_languages(self):
        self.assertEqual(len(self.i18n.UI_LANGS), 26)                                    # the 30 of RimWorld minus the 4 with no usable model
        self.assertEqual(set(self.i18n.UI_LANGS), set(self.i18n.NAMES) - languages.NO_ENGLISH_MODEL)
        for c in ("cs", "da", "hu", "pl"):
            self.assertNotIn(c, self.i18n.UI_LANGS)
            self.assertNotIn(c, self.i18n.SUPPORTED_TARGETS)
            self.assertTrue(models_mod.is_unsupported("en", c))
            self.assertNotIn(c, models_mod.available_targets([{"from_code": "en", "to_code": c}]))
        self.assertEqual(self.i18n.SUPPORTED_TARGETS, list(self.i18n.UI_LANGS))
        for c in ("ca", "zh", "zh-Hant", "ko-FC", "nb", "es-419", "pt-PT", "pt-BR", "vi", "uk"):
            self.assertIn(c, self.i18n.UI_LANGS)
        for c in ("ar", "hi", "th", "he", "id", "fa"):                 # languages RimWorld does not offer
            self.assertNotIn(c, self.i18n.UI_LANGS)

    def test_every_language_offered_has_a_model(self):
        for c in self.i18n.UI_LANGS:
            self.assertTrue(c == "en" or languages.model_code(c) in languages.ARGOS_FROM_ENGLISH, f"{c} has no English -> {c} model")

    def test_variants_share_texts_and_models(self):
        self.assertEqual(self.i18n.text_source("pt-PT"), "pt")
        self.assertEqual(self.i18n.text_source("pt-BR"), "pt")
        self.assertEqual(self.i18n.text_source("es-419"), "es")
        self.assertEqual(self.i18n.text_source("ko-FC"), "ko")
        self.assertEqual(languages.model_code("zh-Hant"), "zt")
        self.assertEqual(languages.model_code("es-419"), "es")
        self.assertEqual(languages.norm_target("ZH-hant"), "zh-Hant")
        self.assertTrue(server._code_ok("zh-Hant") and server._code_ok("es-419") and server._code_ok("ko-FC"))

    def test_handwritten_languages_need_no_translation(self):
        self.assertEqual(self.i18n.tr("pt-BR", "quit_btn"), "Sair")
        self.assertEqual(self.i18n.tr("pt-PT", "quit_btn"), "Sair")
        self.assertEqual(self.i18n.tr("en", "quit_btn"), "Quit")

    def test_other_languages_are_translated_once_and_cached(self):
        calls = []

        def fake_de(texts):
            calls.append(len(texts))
            return ["DE:" + t for t in texts]
        set_engine("en", "de", type("E", (), {"translate_batch": staticmethod(fake_de)})())
        self.assertEqual(self.i18n.tr("de", "quit_btn"), "Quit")                       # not ready yet: English
        self.assertEqual(len(self.uitext.pending("de")), len(self.i18n.TEXT["en"]))
        n = self.uitext.translate_missing("de")
        self.assertEqual(n, len(self.i18n.TEXT["en"]))
        self.assertEqual(self.i18n.tr("de", "quit_btn"), "DE:Quit")
        # placeholders survive and are filled in
        self.assertIn("{n}", self.i18n.TEXT["en"]["det_tab_translated"])
        self.assertIn("(7)", self.i18n.tr("de", "det_tab_translated", n=7))
        # a second run, also after a restart (memory dropped), translates nothing
        self.uitext.forget()
        self.assertEqual(self.uitext.pending("de"), [])
        self.assertEqual(self.uitext.translate_missing("de"), 0)

    def test_html_entities_from_a_translation_become_real_characters(self):
        set_engine("en", "it", type("E", (), {"translate_batch": staticmethod(lambda ts: ["Langue&#160;:" for _ in ts])})())
        self.uitext.translate_missing("it")
        self.assertEqual(self.i18n.tr("it", "ui_lang"), "Langue\xa0:")
        self.assertIn("ui_no_model", self.i18n.TEXT["pt"])
        self.assertIn("ui_no_model", self.i18n.TEXT["en"])

    def test_a_careless_engine_cannot_break_placeholders(self):
        set_engine("en", "fr", type("E", (), {"translate_batch": staticmethod(lambda ts: ["x" for _ in ts])})())
        self.uitext.translate_missing("fr")
        txt = self.i18n.tr("fr", "det_tab_translated", n=3)           # the marker is protected from the engine, so formatting works
        self.assertTrue(txt.endswith("3)"), txt)


class UntouchedPhrases(unittest.TestCase):
    """A model that hands a Title Case phrase or an odd possessive back unchanged gets a second try."""

    def run_fake(self, table):
        calls = []

        def run(sents):
            calls.append(list(sents))
            return [table.get(s, s) for s in sents]
        return run, calls

    def test_title_case_sentence_is_retried_in_lower_case(self):
        from rwtranslate.engine import retranslate_unchanged
        src = ["Advanced In Situ Road Resources Gatherer.", "Uses local resources to build roads."]
        outs = ["Advanced In Situ Road Resources Gatherer.", "Usa recursos locais para construir estradas."]
        run, calls = self.run_fake({"advanced in situ road resources gatherer.": "coletor avançado de recursos de estrada in situ."})
        fixed = retranslate_unchanged(src, outs, run, "pt")
        self.assertEqual(fixed[0], "coletor avançado de recursos de estrada in situ.")
        self.assertEqual(fixed[1], outs[1])                       # what was translated is never touched
        self.assertEqual(calls, [["advanced in situ road resources gatherer."]])

    def test_short_label_is_framed_with_the_and_the_article_removed(self):
        from rwtranslate.engine import retranslate_unchanged
        run, calls = self.run_fake({"the electric stonecutter's table": "A mesa elétrica do cortador de pedras"})
        fixed = retranslate_unchanged(["Electric stonecutter's table"], ["Electric stonecutter's table"], run, "pt")
        self.assertEqual(fixed, ["mesa elétrica do cortador de pedras"])

    def test_answer_that_is_still_the_source_changes_nothing(self):
        from rwtranslate.engine import retranslate_unchanged
        run, _ = self.run_fake({})
        self.assertEqual(retranslate_unchanged(["Wood Stove"], ["Wood Stove"], run, "pt"), ["Wood Stove"])
        self.assertEqual(retranslate_unchanged(["HP"], ["HP"], run, "pt"), ["HP"])          # one word: left alone, no second try

    def test_languages_without_article_table_skip_the_frame(self):
        from rwtranslate.engine import retranslate_unchanged
        run, calls = self.run_fake({})
        retranslate_unchanged(["wooden table"], ["wooden table"], run, "ja")
        self.assertEqual(calls, [["wooden table"]])               # only the lower-case retry


class RepairSavedTranslations(unittest.TestCase):
    def test_glossary_word_and_full_stop_are_fixed_in_a_saved_cache(self):
        from rwtranslate import bulk
        d = bulk.cache_path("pt-BR", "x.mod").parent
        d.mkdir(parents=True, exist_ok=True)
        bulk.write_cache("pt-BR", "x.mod", {"safe": "Seguro.", "mine": "Meu.", "iron sword": "espada de ferro.",
                                            "A safe place.": "Um lugar seguro.", "wood": "madeira"})
        self.assertEqual(bulk.repair_all("pt-BR"), 3)
        e = bulk.read_cache("pt-BR", "x.mod")
        self.assertEqual((e["safe"], e["mine"], e["iron sword"]), ("cofre", "mina", "espada de ferro"))
        self.assertEqual((e["A safe place."], e["wood"]), ("Um lugar seguro.", "madeira"))
        self.assertEqual(bulk.repair_all("pt-BR"), 0)             # nothing left to fix


class BatchedTranslation(unittest.TestCase):
    def test_many_texts_reach_the_model_in_one_call(self):
        calls = []

        class Fake:
            def translate_batch(self, texts):
                calls.append(list(texts))
                return [f"<{t}>" for t in texts]
        from unittest import mock
        with mock.patch.object(server, "get_engine", lambda s, t: Fake()):
            out = server.translate_texts("en", "de", ["iron sword", "wooden shield", "A {0} of steel", "iron sword"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(out[0], out[3])
        self.assertTrue(all(o for o in out))


class FakeResult:
    def __init__(self, toks):
        self.hypotheses = [toks]


class FakeSP:
    def encode(self, s, out_type=str):
        return s.split()


class TargetLanguagesList(unittest.TestCase):
    def setUp(self):
        from rwtranslate import config
        self.config = config
        config.set("target", None)
        config.set("targets", None)

    def tearDown(self):
        self.config.set("target", None)
        self.config.set("targets", None)

    def test_the_game_language_is_always_in_the_list_and_first(self):
        from rwtranslate import targets
        self.assertEqual(targets.selected(), [])
        self.assertEqual(targets.set_selected(["ja", "pt-BR", "es"], "pt-BR"), ["pt-BR", "ja", "es"])
        self.assertEqual(self.config.get("target"), "pt-BR", "the game still reads ONE language")
        self.assertEqual(targets.set_selected(["ja", "es"], "es"), ["es", "ja"])
        self.assertEqual(self.config.get("target"), "es")
        # the game language was not ticked: the first ticked one is used
        self.assertEqual(targets.set_selected(["fr", "de"]), ["fr", "de"])
        self.assertEqual(self.config.get("target"), "fr")

    def test_unknown_duplicate_and_unusable_languages_are_dropped(self):
        from rwtranslate import targets
        self.assertEqual(targets.set_selected(["ja", "ja", "xx", "cs", "da", "hu", "pl", 5, None, "zh-Hant"], "ja"), ["ja", "zh-Hant"])
        self.assertEqual(targets.set_selected([]), [], "an empty list is allowed: nothing selected")
        self.assertEqual(targets.selected(), [])
        self.assertEqual(self.config.get("target"), "ja", "the game keeps its language")

    def test_picking_the_game_language_alone_adds_it_to_the_list(self):
        from rwtranslate import targets
        targets.set_selected(["pt-BR", "ja"], "pt-BR")
        self.assertEqual(targets.set_game_language("fr"), ["fr", "pt-BR", "ja"])
        self.assertEqual(self.config.get("target"), "fr")
        self.assertEqual(targets.set_game_language("ja"), ["ja", "fr", "pt-BR"])

    def test_old_settings_with_only_a_target_still_work(self):
        from rwtranslate import targets
        self.config.set("target", "pt")                     # an old setting: "pt" meant Brazilian Portuguese
        self.assertEqual(targets.selected(), ["pt-BR"])
        self.assertEqual(targets.primary(), "pt-BR")


class OneDownloadPerModel(unittest.TestCase):
    """The "Download model" button and the window language can ask for the same model at the same moment: one download, not two."""

    def test_two_callers_share_one_download_and_one_progress(self):
        import threading
        import time
        from pathlib import Path
        from unittest import mock
        from rwtranslate import models
        index = [{"from_code": "en", "to_code": "qq", "package_version": "1.0", "links": ["http://x/qq.argosmodel"]}]
        downloads, seen = [], []

        def fake_download(url, tmp, dest, progress):
            downloads.append(url)
            progress("  26% (20 MB)")
            time.sleep(0.4)
            Path(dest).mkdir(parents=True, exist_ok=True)
            (Path(dest) / "model.bin").write_text("x")
            (Path(dest) / "sentencepiece.model").write_text("x")
            progress("  100% (80 MB)")
        errors = []

        def call(tag):
            try:
                models.install("en", "qq", progress=lambda m: seen.append((tag, m)), index=index)
            except Exception as e:  # noqa: BLE001
                errors.append(e)
        try:
            with mock.patch.object(models, "_download_and_unpack", fake_download):
                t1 = threading.Thread(target=call, args=("first",))
                t1.start()
                time.sleep(0.1)
                t2 = threading.Thread(target=call, args=("second",))                     # asks while the first one is still downloading
                t2.start()
                t1.join(10)
                t2.join(10)
                self.assertEqual(errors, [])
                self.assertEqual(len(downloads), 1, "a single download")
                self.assertTrue(models.is_installed("en", "qq"))
                self.assertTrue(any(tag == "second" and "26%" in m for tag, m in seen), "the second caller hears the progress too")
                models.install("en", "qq", progress=lambda m: seen.append(("third", m)), index=index)        # already there: nothing to do
                self.assertEqual(len(downloads), 1, "an installed model is never downloaded again")
        finally:
            import shutil
            shutil.rmtree(models.pair_dir("en", "qq"), ignore_errors=True)

    def test_a_failed_download_fails_for_everyone_waiting(self):
        import threading
        import time
        from unittest import mock
        from rwtranslate import models
        index = [{"from_code": "en", "to_code": "qr", "package_version": "1.0", "links": ["http://x/qr.argosmodel"]}]

        def failing(url, tmp, dest, progress):
            time.sleep(0.3)
            raise OSError("network down")
        errors = []

        def call():
            try:
                models.install("en", "qr", progress=lambda m: None, index=index)
            except Exception as e:  # noqa: BLE001
                errors.append(type(e).__name__)
        with mock.patch.object(models, "_download_and_unpack", failing):
            ts = [threading.Thread(target=call) for _ in range(2)]
            ts[0].start()
            time.sleep(0.1)
            ts[1].start()
            for t in ts:
                t.join(10)
        self.assertEqual(errors, ["OSError", "OSError"])
        self.assertFalse(models._jobs, "nothing is left marked as downloading")


class WindowLanguageIsPreparedInGroups(unittest.TestCase):
    def test_the_window_texts_go_to_the_model_in_a_few_calls_with_progress(self):
        from rwtranslate import i18n, uitext
        calls, steps = [], []

        def fake(texts):
            calls.append(len(texts))
            return ["SV:" + t for t in texts]
        set_engine("en", "sv", type("E", (), {"translate_batch": staticmethod(fake)})())
        uitext.forget()
        total = len(uitext.pending("sv"))
        n = uitext.translate_missing("sv", progress=lambda d, t: steps.append((d, t)))
        self.assertEqual(n, total)
        self.assertLessEqual(len(calls), -(-total // uitext.CHUNK) + 2, f"{len(calls)} model calls for {total} texts (it used to be one call per text)")
        self.assertEqual(steps[-1], (total, total))
        self.assertTrue(all(b - a > 0 for a, b in zip([0] + [d for d, _t in steps], [d for d, _t in steps])), "progress only moves forward")
        self.assertEqual(i18n.tr("sv", "quit_btn"), "SV:Quit")


class GameFlagAfterAManualCorrection(unittest.TestCase):
    def test_the_flag_the_game_watches_is_kept_alive_a_few_seconds_then_removed(self):
        import time
        from rwtranslate import bulk
        flag = bulk.data_dir() / bulk.FLAG_NAME
        flag.unlink(missing_ok=True)
        bulk.pulse_game_flag(seconds=0.3, step=0.1)
        time.sleep(0.15)
        self.assertTrue(flag.exists(), "the game sees the flag while the correction is applied")
        time.sleep(0.8)
        self.assertFalse(flag.exists(), "and it goes away afterwards (the game then looks one last time)")

    def test_saving_a_correction_pulses_the_flag(self):
        from unittest import mock
        from rwtranslate import bulk
        with mock.patch.object(bulk, "pulse_game_flag") as pulse:
            bulk.save_edit("zz", "p.mod", "Hello", "Olá")
            pulse.assert_called_once()
            bulk.restore_default("zz", "p.mod", "Hello", translate=lambda t: "Olá!")
            self.assertEqual(pulse.call_count, 2)
        for f in (bulk.cache_path("zz", "p.mod"), bulk.overrides_path("zz")):
            f.unlink(missing_ok=True)


class ExportForModders(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        self.tmp = Path(tempfile.mkdtemp())
        self.mod = self.tmp / "mods" / "CoolMod"
        (self.mod / "About").mkdir(parents=True)
        (self.mod / "About" / "About.xml").write_text("<ModMetaData><packageId>a.cool</packageId><name>Cool</name></ModMetaData>", encoding="utf-8")
        (self.mod / "Defs").mkdir()
        (self.mod / "Defs" / "Things.xml").write_text(
            "<Defs><ThingDef><defName>Chair</defName><label>wooden chair</label><description>A chair.\nSit.</description></ThingDef>"
            "<ThingDef><defName>Table</defName><label>table</label></ThingDef></Defs>", encoding="utf-8")
        (self.mod / "1.6" / "Languages" / "English" / "Keyed").mkdir(parents=True)
        (self.mod / "1.6" / "Languages" / "English" / "Keyed" / "Keys.xml").write_text(
            "<LanguageData><Hello>Hello &amp; welcome</Hello></LanguageData>", encoding="utf-8")
        from rwtranslate import bulk
        self.bulk = bulk
        self.info = bulk.scan([self.tmp / "mods"])[0]
        bulk.write_cache("pt-BR", "a.cool", {"wooden chair": "cadeira de madeira", "A chair.\nSit.": "Uma cadeira.\nSente.", "Hello & welcome": "Olá & bem-vindo"})
        bulk.write_cache("ja", "a.cool", {"wooden chair": "木の椅子"})
        self.files = [bulk.cache_path("pt-BR", "a.cool"), bulk.cache_path("ja", "a.cool")]

    def tearDown(self):
        for f in self.files:
            f.unlink(missing_ok=True)
        self.bulk.overrides_path("pt-BR").unlink(missing_ok=True)

    def test_writes_rimworld_language_files_for_every_language(self):
        import xml.etree.ElementTree as ET
        from rwtranslate import export
        out = self.tmp / "out"
        res = export.export_mod(self.info, ["pt-BR", "ja", "fr"], out)
        self.assertEqual(res["languages"], ["pt-BR", "ja"], "a language with no translation writes nothing")
        pt = out / "CoolMod" / "Languages" / "PortugueseBrazilian"
        root = ET.parse(pt / "DefInjected" / "ThingDef" / "Things.xml").getroot()
        self.assertEqual({e.tag: e.text for e in root}, {"Chair.label": "cadeira de madeira", "Chair.description": "Uma cadeira.\\nSente."})
        ja = ET.parse(out / "CoolMod" / "Languages" / "Japanese" / "DefInjected" / "ThingDef" / "Things.xml").getroot()
        self.assertEqual({e.tag: e.text for e in ja}, {"Chair.label": "木の椅子"})
        keyed = out / "CoolMod" / "1.6" / "Languages" / "PortugueseBrazilian" / "Keyed" / "Keys.xml"
        self.assertEqual([(e.tag, e.text) for e in ET.parse(keyed).getroot()], [("Hello", "Olá & bem-vindo")], "the folders of the mod (1.6) are kept")
        self.assertTrue((out / "CoolMod" / "README.txt").exists())

    def test_the_players_corrections_are_exported(self):
        import xml.etree.ElementTree as ET
        from rwtranslate import export
        self.bulk.save_edit("pt-BR", "a.cool", "wooden chair", "cadeira rústica")
        out = self.tmp / "out2"
        export.export_all([self.info], ["pt-BR"], out)
        root = ET.parse(out / "CoolMod" / "Languages" / "PortugueseBrazilian" / "DefInjected" / "ThingDef" / "Things.xml").getroot()
        self.assertEqual(root.find("Chair.label").text, "cadeira rústica")

    def test_nothing_is_written_without_translations(self):
        from rwtranslate import export
        res = export.export_all([self.info], ["fr"], self.tmp / "out3")
        self.assertEqual((res["mods"], res["files"]), (0, 0))
        self.assertFalse((self.tmp / "out3").exists())

    def test_language_folders_have_the_names_of_rimworld(self):
        from rwtranslate import export
        self.assertEqual([export.game_folder(c) for c in ("pt-BR", "pt-PT", "es-419", "zh", "zh-Hant", "ja")],
                         ["PortugueseBrazilian", "Portuguese", "SpanishLatin", "ChineseSimplified", "ChineseTraditional", "Japanese"])


class FaqPage(unittest.TestCase):
    def test_faq_md_is_the_help_tab(self):
        import importlib.util
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        spec = importlib.util.spec_from_file_location("make_faq", os.path.join(root, "tools", "make_faq.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with open(os.path.join(root, "FAQ.md"), encoding="utf-8") as f:
            self.assertEqual(f.read(), mod.build(), "FAQ.md is out of date: run python tools/make_faq.py")
        with open(os.path.join(root, "README.md"), encoding="utf-8") as f:
            self.assertIn('href="FAQ.md"', f.read(), "the README has the FAQ button")


class ExeVersionInfo(unittest.TestCase):
    def test_version_file_for_the_exe_is_valid_and_has_the_project_version(self):
        import importlib.util
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        spec = importlib.util.spec_from_file_location("make_version_info", os.path.join(root, "tools", "make_version_info.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        text = mod.build("0.039")

        class Rec:                              # stand-ins for the PyInstaller classes: the file is Python that builds them
            def __init__(self, *a, **k):
                self.a, self.k = a, k
        names = {n: Rec for n in ("VSVersionInfo", "FixedFileInfo", "StringFileInfo", "StringTable", "StringStruct", "VarFileInfo", "VarStruct")}
        info = eval(text, names)
        self.assertEqual(info.k["ffi"].k["filevers"], (0, 39, 0, 0))
        self.assertIn("'0.039.0'", text)
        self.assertIn("UniversalTranslate-Helper.exe", text)


class VanillaStaysVanilla(unittest.TestCase):
    """The base game is called "Vanilla": never "Baunilha" / "vainilla"."""

    def test_the_word_is_protected_from_the_translator(self):
        from rwtranslate.protect import translate_protected
        seen = []

        def engine(batch):
            seen.extend(batch)
            return [b.replace("Furniture", "Móveis").replace("furniture", "móveis").replace("Expanded", "Expandido") for b in batch]
        self.assertEqual(translate_protected("Vanilla", engine), "Vanilla")                                    # nothing to translate
        self.assertEqual(translate_protected("Vanilla Furniture Expanded", engine), "Vanilla Móveis Expandido")
        self.assertEqual(translate_protected("Better than vanilla furniture", engine), "Better than vanilla móveis")

    def test_a_translation_that_still_says_baunilha_is_fixed(self):
        from rwtranslate.protect import clean_output
        self.assertEqual(clean_output("Vanilla Furniture Expanded", "Baunilha Móveis Expandido", "pt-BR"), "Vanilla Móveis Expandido")
        self.assertEqual(clean_output("a vanilla bed", "uma cama de baunilha", "pt-BR"), "uma cama de vanilla")
        self.assertEqual(clean_output("Vanilla Expanded", "Vainilla Ampliado", "es"), "Vanilla Ampliado")
        self.assertEqual(clean_output("Vanilla Expanded", "Vanille Étendu", "fr"), "Vanilla Étendu")
        # the real flavour in a source that does not say "vanilla" is not touched; nor another word that contains it
        self.assertEqual(clean_output("Ice cream", "Sorvete de baunilha", "pt-BR"), "Sorvete de baunilha")

    def test_saved_translations_of_older_versions_are_repaired(self):
        from rwtranslate import glossary
        entries = {"Vanilla Expanded": "Baunilha Expandida", "Steel": "Aço"}
        self.assertEqual(glossary.repair_entries(entries, "pt-BR"), 1)
        self.assertEqual(entries, {"Vanilla Expanded": "Vanilla Expandida", "Steel": "Aço"})


class ModelsFolder(unittest.TestCase):
    def test_old_models_folder_is_moved_not_downloaded_again(self):
        import tempfile
        from pathlib import Path
        from unittest import mock
        from rwtranslate import paths
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "models" / "en_pt").mkdir(parents=True)
            (base / "models" / "en_pt" / "ok").write_text("1")
            with mock.patch.object(paths, "data_dir", return_value=base):
                new = paths.models_dir()
            self.assertEqual(new.name, "translation models")
            self.assertTrue((new / "en_pt" / "ok").exists())
            self.assertFalse((base / "models").exists())


class CacheFolder(unittest.TestCase):
    def test_old_cache_folder_becomes_translated_mods(self):
        import tempfile
        from pathlib import Path
        from unittest import mock
        from rwtranslate import paths
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "cache" / "pt-BR").mkdir(parents=True)
            (base / "cache" / "pt-BR" / "a.mod.json").write_text("old")
            with mock.patch.object(paths, "data_dir", return_value=base):
                new = paths.cache_dir()
                self.assertEqual(new.name, "translated mods")
                self.assertEqual((new / "pt-BR" / "a.mod.json").read_text(), "old")
                self.assertFalse((base / "cache").exists())
                # both folders (an older mod wrote into "cache" again): the files are moved in, nothing is overwritten
                (base / "cache" / "pt-BR").mkdir(parents=True)
                (base / "cache" / "pt-BR" / "a.mod.json").write_text("stale")
                (base / "cache" / "pt-BR" / "b.mod.json").write_text("new file")
                paths.cache_dir()
                self.assertEqual((new / "pt-BR" / "a.mod.json").read_text(), "old")
                self.assertEqual((new / "pt-BR" / "b.mod.json").read_text(), "new file")


class ProgressLine(unittest.TestCase):
    def test_line_shows_texts_and_words(self):
        from rwtranslate import i18n
        for lang in ("pt", "en"):
            line = i18n.TEXT[lang]["bulk_current"].format(name="X", done=1, total=2, wdone=3, wtotal=4)
            self.assertIn("1/2", line)
            self.assertIn("3/4", line)


class EngineSafety(unittest.TestCase):
    """Speed must never cost correctness: loops are caught, the stop button works, big requests are cut in chunks."""

    def make(self, answer):
        from rwtranslate import engine as eng
        e = eng.CT2Engine.__new__(eng.CT2Engine)
        e._lock = threading.Lock()
        e._sp = e._sp_out = FakeSP()
        calls = []

        class Tr:
            def translate_batch(self, toks, **kw):
                calls.append((len(toks), kw))
                return [FakeResult(answer(t, kw)) for t in toks]
        e._tr = Tr()
        old = eng.detokenize
        eng.detokenize = lambda sp, toks: " ".join(toks)
        self.addCleanup(setattr, eng, "detokenize", old)
        return e, calls

    def test_degenerate_detection(self):
        from rwtranslate.engine import degenerate
        self.assertTrue(degenerate(["a", "b"], "相相相相相相相相"))
        self.assertTrue(degenerate(["a"] * 3, " ".join(["ok"] * 20)))
        self.assertFalse(degenerate(["a", "b", "c"], "Olá mundo, tudo bem?"))

    def test_loop_is_retried_then_original_kept(self):
        e, calls = self.make(lambda t, kw: ["xxxxxxxxxxx"])      # always loops
        self.assertEqual(e._run(["hello world"]), ["hello world"])
        e, calls = self.make(lambda t, kw: ["ok"] if kw.get("no_repeat_ngram_size") else ["yyyyyyyyyyy"])
        self.assertEqual(e._run(["hello world"]), ["ok"])

    def test_decoding_length_follows_the_source(self):
        e, calls = self.make(lambda t, kw: ["a"])
        e._run(["one two three"])
        self.assertLessEqual(calls[0][1]["max_decoding_length"], 2 * 3 + 16)

    def test_chunks_and_order_preserved(self):
        from rwtranslate import engine as eng
        e, calls = self.make(lambda t, kw: [w.upper() for w in t])
        texts = [("w " * (i % 5 + 1)).strip() + f" n{i}" for i in range(30)]
        outs = e._run(texts)
        self.assertEqual(outs, [t.upper() for t in texts])
        self.assertGreater(len(calls), 1)
        self.assertTrue(all(n <= eng.CHUNK_SENTENCES for n, _ in calls))

    def test_stop_between_chunks(self):
        from rwtranslate import engine as eng
        e, calls = self.make(lambda t, kw: ["a"])
        ev = threading.Event()
        ev.set()
        eng.set_cancel(ev)
        try:
            with self.assertRaises(eng.Cancelled):
                e._run(["a b"] * 40)
        finally:
            eng.set_cancel(None)
        self.assertEqual(calls, [])


class UnsupportedPackages(unittest.TestCase):
    def test_bpe_only_pairs_are_not_offered(self):
        index = [{"from_code": "hu", "to_code": "en"}, {"from_code": "cs", "to_code": "en"}, {"from_code": "de", "to_code": "en"}]
        self.assertEqual(models_mod.available_pairs(index), [("de", "en")])
        self.assertFalse(models_mod.support("hu", "pb", index)["supported"])

    def test_a_download_without_a_readable_tokenizer_is_marked_unsupported(self):
        import io
        import zipfile
        from unittest import mock
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("pkg/model/model.bin", "x")
            z.writestr("pkg/bpe.model", "x")

        def fake_unpack(url, tmp, dest, progress):
            zipfile.ZipFile(buf).extractall(dest)
        index = [{"from_code": "xx", "to_code": "en", "package_version": "1.0", "links": ["u"]}]
        with mock.patch.object(models_mod, "_download_and_unpack", fake_unpack):
            with self.assertRaises(RuntimeError):
                models_mod._install_pair("xx", "en", lambda m: None, index)
        self.assertTrue(models_mod.is_unsupported("xx", "en"))
        self.assertFalse(models_mod.pair_dir("xx", "en").exists())

    def test_english_sentences_are_not_taken_for_czech_or_hungarian(self):
        from rwtranslate import langdetect
        for t in ["A fake tree similar to a palm tree, made to be a pleasing decoration.",
                  "Make a pleasing, aromatic beverage to be sold by the traders."]:
            self.assertEqual(langdetect.latin_lang([t])[0], "en", t)


class ModelFiles(unittest.TestCase):
    def test_finds_the_usual_and_the_split_tokenizer_layouts(self):
        import pathlib
        d = pathlib.Path(tempfile.mkdtemp())
        (d / "model").mkdir()
        (d / "model" / "model.bin").write_text("x")
        (d / "sentencepiece.model").write_text("x")
        b, e, o = models_mod.find_model_files(d)
        self.assertTrue(b.name == "model.bin" and e.name == o.name == "sentencepiece.model")
        d2 = pathlib.Path(tempfile.mkdtemp())
        (d2 / "model.bin").write_text("x")
        (d2 / "source.spm").write_text("x")
        (d2 / "target.spm").write_text("x")
        b, e, o = models_mod.find_model_files(d2)
        self.assertEqual((e.name, o.name), ("source.spm", "target.spm"))
        d3 = pathlib.Path(tempfile.mkdtemp())
        (d3 / "readme.txt").write_text("x")
        self.assertEqual(models_mod.find_model_files(d3), (None, None, None))
        self.assertIn("readme.txt", models_mod.listing(d3))

    def test_a_folder_without_model_files_is_reported_and_removed(self):
        from rwtranslate import engine
        from rwtranslate.paths import models_dir
        d = models_dir() / "en_zz"
        d.mkdir(parents=True, exist_ok=True)
        (d / "ok").write_text("1")
        (d / "weird.bin").write_text("x")
        engine._engines.pop(("en", "zz"), None)
        with self.assertRaises(engine.EngineError) as cm:
            engine._load("en", "zz")
        msg = str(cm.exception)
        self.assertTrue("ctranslate2" in msg or ("model files not found" in msg and "weird.bin" in msg), msg)
