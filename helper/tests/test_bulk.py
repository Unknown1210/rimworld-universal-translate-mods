import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["RWTRANSLATE_HOME"] = tempfile.mkdtemp()

from rwtranslate import bulk, langdetect, models  # noqa: E402
from rwtranslate.engine import set_engine  # noqa: E402
from rwtranslate.paths import data_dir, models_dir  # noqa: E402

CALLS = []


class Fake:
    def __init__(self, src, tgt):
        self.src, self.tgt = src, tgt

    def translate_batch(self, texts):
        CALLS.extend((self.src, t) for t in texts)
        return [f"{t} ({self.tgt})" if self.src == "en" else f"{t} ({self.tgt} from {self.src})" for t in texts]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_mod(root, folder, pid, name, desc="", defs="", keyed="", extra=None):
    m = root / folder
    write(m / "About" / "About.xml", f"<ModMetaData><name>{name}</name><packageId>{pid}</packageId><description>{desc}</description></ModMetaData>")
    if defs:
        write(m / "Defs" / "Things.xml", f"<Defs>{defs}</Defs>")
    if keyed:
        write(m / "Languages" / "English" / "Keyed" / "k.xml", f"<LanguageData>{keyed}</LanguageData>")
    for rel, text in (extra or {}).items():
        write(m / rel, text)
    return m


def thing(name, label, desc=""):
    return f"<ThingDef><defName>{name}</defName><label>{label}</label>" + (f"<description>{desc}</description>" if desc else "") + "</ThingDef>"


class Bulk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # never touch the network: a tiny local model index
        idx = Path(data_dir()) / "idx.json"
        idx.write_text(json.dumps([{"from_code": "en", "to_code": "pt", "package_version": "1", "links": ["x"]}]))
        models.INDEX_URL = "file://" + str(idx)
        models._index_mem["data"] = None
        cls._old_url = models.INDEX_URL
        cls._made = []
        for s, t in (("en", "pt"), ("zh", "pt")):
            set_engine(s, t, Fake(s, t))
            d = models_dir() / f"{s}_{t}"
            if not d.exists():
                d.mkdir(parents=True)
                (d / "ok").write_text("1")
                cls._made.append(d)               # removed afterwards: the data dir is shared with the other test modules

        cls.root = Path(tempfile.mkdtemp())
        r = cls.root
        make_mod(r, "A", "a.good", "Good Mod", "A short description of the mod.",
                 thing("Sword", "iron sword", "A sharp sword,\n        for fighting.   Very sharp."), "<Hello>Hello {0}!</Hello>")
        make_mod(r, "B", "b.chinese", "Chinese Mod", defs=thing("Zh", "铁剑", "一把锋利的铁剑，适合战斗。"))
        make_mod(r, "C", "c.portuguese", "Portuguese Mod", "O colono não pode usar esta arma porque ela é muito pesada para você.",
                 thing("Pt", "Espada de ferro", "Esta ação não está disponível para você, mas também não é necessária."))
        make_mod(r, "D", "d.partial", "Partial Mod", defs=thing("Covered", "covered item") + thing("Uncovered", "uncovered item"),
                 extra={"Languages/PortugueseBrazilian/DefInjected/ThingDef/x.xml": "<LanguageData><Covered.label>Item coberto</Covered.label></LanguageData>"})
        make_mod(r, "F", "f.japanese", "Japanese Mod", defs=thing("Ja", "鉄の剣です"))
        make_mod(r, "G", "g.broken", "Broken Mod", defs=thing("Fine", "fine label"), extra={"Defs/bad.xml": "<Defs><ThingDef><defName>X"})
        (r / "H").mkdir()                                  # a folder that is not a mod
        cls.dirs = [r]

    @classmethod
    def tearDownClass(cls):
        import shutil
        for d in cls._made:
            shutil.rmtree(d, ignore_errors=True)
        models.INDEX_URL = cls._old_url
        models._index_mem["data"] = None

    def setUp(self):
        CALLS.clear()

    def test_01_translates_everything_that_needs_it(self):
        events = []
        res = {x.package_id: x for x in bulk.run("pt", self.dirs, progress=events.append)}
        a = bulk.read_cache("pt", "a.good")
        self.assertEqual(a["iron sword"], "iron sword (pt)")
        self.assertEqual(a["A short description of the mod."], "A short description of the mod. (pt)")      # About description too
        self.assertEqual(a["Hello {0}!"], "Hello {0}! (pt)")                                                  # Keyed
        self.assertIn("A sharp sword,\nfor fighting. Very sharp.", a)                                         # key is NORMALIZED text
        self.assertEqual(bulk.read_cache("pt", "b.chinese")["铁剑"], "铁剑 (pt from zh)")
        self.assertEqual(res["c.portuguese"].texts, 0)                                                        # already Portuguese: nothing to do
        self.assertGreaterEqual(res["c.portuguese"].already_target, 3)
        self.assertFalse(bulk.cache_path("pt", "c.portuguese").exists())
        d = bulk.read_cache("pt", "d.partial")
        self.assertEqual(d, {"uncovered item": "uncovered item (pt)"})                                        # covered text is left to its translation
        self.assertEqual(res["d.partial"].covered, 1)
        self.assertEqual(res["f.japanese"].unsupported, ["ja->pt"])                                           # no model: reported, not crashed
        self.assertEqual(bulk.read_cache("pt", "f.japanese"), {})
        self.assertEqual(bulk.read_cache("pt", "g.broken"), {"fine label": "fine label (pt)"})                # broken XML ignored
        self.assertEqual([e["event"] for e in events if e["event"] in ("start", "finished")], ["start", "finished"])
        self.assertEqual(sum(1 for e in events if e["event"] == "mod_done"), 6)

    def test_02_cache_file_has_the_format_the_game_reads(self):
        raw = json.loads(bulk.cache_path("pt", "a.good").read_text(encoding="utf-8"))
        self.assertEqual((raw["format"], raw["target"]), (1, "pt"))
        self.assertIsInstance(raw["entries"], dict)

    def test_03_words_and_summary(self):
        st = bulk.state_load()["pt"]
        self.assertEqual(st["a.good"]["texts"], 4)
        self.assertEqual(st["a.good"]["words"], bulk.count_words("iron sword") + bulk.count_words("A sharp sword,\nfor fighting. Very sharp.")
                         + bulk.count_words("Hello {0}!") + bulk.count_words("A short description of the mod."))
        self.assertEqual(st["b.chinese"]["langs"], {"zh": 2})
        self.assertEqual(bulk.count_words("铁剑"), 2)

    def test_04_second_scan_finds_only_what_is_new_or_changed(self):
        status = {m.package_id: s for m, s, _r in bulk.plan("pt", self.dirs)}
        self.assertTrue(all(s == "ok" for pid, s in status.items() if pid != "f.japanese" or True), status)
        make_mod(self.root, "I", "i.new", "New Mod", defs=thing("Fresh", "fresh label"))                     # installed later
        write(self.root / "A" / "Defs" / "More.xml", f"<Defs>{thing('Axe', 'steel axe')}</Defs>")           # an existing mod was updated
        status = {m.package_id: s for m, s, _r in bulk.plan("pt", self.dirs)}
        self.assertEqual((status["i.new"], status["a.good"], status["b.chinese"]), ("new", "changed", "ok"))
        CALLS.clear()
        res = bulk.run("pt", self.dirs)
        self.assertEqual(sorted(r.package_id for r in res), ["a.good", "i.new"])                              # only the pending ones
        self.assertEqual(sorted(t for _s, t in CALLS), ["fresh label", "steel axe"])                          # and only the unseen texts (the rest came from cache)
        self.assertTrue(all(s == "ok" for _m, s, _r in bulk.plan("pt", self.dirs)))

    def test_05_force_retranslates_all_but_uses_the_cache(self):
        res = bulk.run("pt", self.dirs, force=True)
        self.assertGreaterEqual(len(res), 7)
        self.assertEqual(CALLS, [])                                                                           # everything was cached already

    def test_06_cancel_stops_before_saving_state(self):
        make_mod(self.root, "J", "j.cancel", "Cancel Mod", defs=thing("C1", "cancel label"))
        ev = threading.Event()
        ev.set()
        res = bulk.run("pt", self.dirs, cancel=ev)
        self.assertEqual(res, [])
        self.assertNotIn("j.cancel", bulk.state_load().get("pt", {}))

    def test_07_old_cache_entries_with_the_marker_are_dropped(self):
        bulk.write_cache("pt", "z.old", {"stone table": "▁mesa▁de▁pedra", "ok": "bom"})
        self.assertEqual(bulk.read_cache("pt", "z.old"), {"ok": "bom"})

    def test_08_normalization_matches_the_mod(self):
        for raw, expected in json.load(open(os.path.join(os.path.dirname(__file__), "norm_vectors.json"), encoding="utf-8")):
            self.assertEqual(bulk.normalize(raw), expected, raw)

    def test_09_file_names_match_the_mod(self):
        self.assertEqual(bulk.safe_file_name("falconne.BWM"), "falconne.BWM")
        self.assertEqual(bulk.safe_file_name('a<b>c:d"e/f\\g|h?i*j'), "a_b_c_d_e_f_g_h_i_j")


    def test_10_placeholder_translation_files_do_not_count_as_translations(self):
        """The reported case: a mod ships Languages/PortugueseBrazilian/DefInjected files whose text is still the ENGLISH original
        (the game's own tool writes them that way). That is not a translation: the text must be translated, not skipped."""
        make_mod(self.root, "M", "m.placeholder", "Misstall-like",
                 defs=thing("Armchair", "MF Armchair", "A large, soft, comfy seat.") + thing("Couch", "MF Couch", "A soft couch for two colonists.")
                 + thing("Bed", "MF Bed", "A simple bed."),
                 extra={"Languages/PortugueseBrazilian/DefInjected/ThingDef/f.xml":
                        "<LanguageData><Armchair.label>MF Armchair</Armchair.label>"                    # same as the original -> placeholder
                        "<Armchair.description>A large, soft, comfy seat.</Armchair.description>"       # same as the original -> placeholder
                        "<Couch.description>Um sofá macio para dois colonos.</Couch.description>"       # a real translation
                        "<Bed.description>一张简单的床。</Bed.description></LanguageData>"})             # another language: not Portuguese
        CALLS.clear()
        res = {r.package_id: r for r in bulk.run("pt", self.dirs)}
        r = res["m.placeholder"]
        cache = bulk.read_cache("pt", "m.placeholder")
        self.assertEqual(cache["A large, soft, comfy seat."], "A large, soft, comfy seat. (pt)")           # translated although a 'cover' existed
        self.assertEqual(cache["MF Armchair"], "MF Armchair (pt)")
        self.assertEqual(cache["A simple bed."], "A simple bed. (pt)")
        self.assertNotIn("A soft couch for two colonists.", cache)                                          # the real translation is respected
        self.assertEqual((r.covered, r.placeholders), (1, 3))
        reasons = {(x["reason"], x["detail"]) for x in r.skipped}
        self.assertIn(("covered", "Misstall-like"), reasons)                                                # and the reason is recorded for the details window
        saved = bulk.state_load()["pt"]["m.placeholder"]
        self.assertEqual(saved["placeholders"], 3)
        self.assertEqual([x["reason"] for x in saved["skipped"]], ["covered"])

    def test_11_is_placeholder_rules(self):
        P = bulk.is_placeholder
        self.assertTrue(P("MF Armchair", "MF Armchair", "pt"))                                              # identical to the original
        self.assertTrue(P("  Same   text ", "Same text", "pt"))                                            # identical after normalization
        self.assertTrue(P("一张简单的床。", "A simple bed.", "pt"))                                          # another script
        self.assertTrue(P("The colonist is carrying a heavy weapon that can not be used by you.", "x", "pt"))   # confidently English, target pt
        self.assertFalse(P("Um sofá macio para dois colonos.", "A soft couch", "pt"))                       # real translation
        self.assertFalse(P("Cama", "Bed", "pt"))                                                            # short but different: respected


class LangDetectPy(unittest.TestCase):
    def test_same_verdicts_as_the_mod(self):
        L = langdetect
        self.assertEqual((L.script_lang("铁剑"), L.script_lang("こんにちは世界"), L.script_lang("안녕하세요")), ("zh", "ja", "ko"))
        self.assertEqual((L.script_lang("Привет мир"), L.script_lang("Привіт, їжак"), L.script_lang("مرحبا بالعالم")), ("ru", "uk", "ar"))
        self.assertIsNone(L.script_lang("Iron sword"))
        for texts, exp in ((["The colonist is carrying a heavy weapon that can not be used by you.", "This item will be consumed on use."], "en"),
                           (["O colono não pode usar esta arma porque ela é muito pesada para você.", "Esta ação não está disponível."], "pt"),
                           (["El colono no puede usar esta arma porque es demasiado pesada para usted.", "La acción no está disponible, también."], "es"),
                           (["Der Kolonist kann diese Waffe nicht benutzen, weil sie für ihn zu schwer ist.", "Die Aktion ist nicht verfügbar."], "de"),
                           (["Le colon ne peut pas utiliser cette arme parce qu'elle est trop lourde pour lui.", "Cette action n'est pas disponible."], "fr")):
            lang, conf, _ = L.latin_lang(texts)
            self.assertEqual((lang, conf), (exp, True))
        lang, conf, _ = L.latin_lang(["iron sword", "wooden shield", "steel"])
        self.assertEqual((lang, conf), ("en", False))


if __name__ == "__main__":
    unittest.main()
