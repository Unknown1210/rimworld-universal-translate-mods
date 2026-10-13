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

from rwtranslate import languages, protect, server  # noqa: E402
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
        self.assertEqual(languages.code_from_game_language("Español Latino"), "es")
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
        old, new = data_dir() / "cache" / "pt", data_dir() / "cache" / "pt-BR"
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

    def test_server_applies_it(self):
        set_engine("en", "pt", type("E", (), {"translate_batch": staticmethod(lambda ts: ["▁Mesa▁elétrica" for _ in ts])})())
        self.assertEqual(server.translate_texts("en", "pt", ["electric table"]), ["mesa elétrica"])
