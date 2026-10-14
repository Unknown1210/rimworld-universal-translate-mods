"""Translation engines. CT2Engine runs Argos/OpenNMT models fully offline on the CPU."""
import re
import threading
from pathlib import Path

from . import languages, logsetup
from .paths import models_dir

log = logsetup.get("engine")

_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


def split_sentences(text):
    parts = [p for p in _SENT_RE.split(text.strip()) if p]
    return parts or [text]


_WORD_RE = re.compile(r"[^\W\d_]+")
# Leading articles the model may add when a label is translated inside "the ..." (target language family -> pattern)
_ARTICLES = {
    "pt": r"(?:o|a|os|as|um|uma)", "es": r"(?:el|la|los|las|un|una)", "ca": r"(?:el|la|els|les|un|una|l')",
    "fr": r"(?:le|la|les|un|une|l')", "it": r"(?:il|lo|la|i|gli|le|un|uno|una|l')", "de": r"(?:der|die|das|ein|eine)",
    "nl": r"(?:de|het|een)",
}


def _norm_text(t):
    return " ".join(t.lower().split())


def retranslate_unchanged(sentences, outputs, run, family=None):
    """The model sometimes hands a phrase back untouched ("Advanced In Situ Road Resources Gatherer.", "Electric stonecutter's
    table"): Title Case or an unusual possessive makes it treat the phrase as a name. Those get a second try, in lower case and,
    for short labels, framed as "the ..." (the article is removed from the answer again). `run` translates a list of sentences.
    Only an answer that really differs from the source replaces the first one. Returns the new outputs."""
    outputs = list(outputs)

    def stuck():
        return [i for i, (s, o) in enumerate(zip(sentences, outputs)) if _norm_text(s) == _norm_text(o) and len(_WORD_RE.findall(s)) >= 2]
    idx = stuck()
    if idx:
        tries = run([sentences[i].lower() for i in idx])
        for i, t in zip(idx, tries):
            low = sentences[i].lower()
            if _norm_text(t) != _norm_text(low) and t.strip():
                outputs[i] = t
        idx = stuck()
    art = _ARTICLES.get(family or "")
    if idx and art:
        short = [i for i in idx if len(_WORD_RE.findall(sentences[i])) <= 6 and not re.search(r"[.!?:;]$", sentences[i].strip())]
        if short:
            tries = run(["the " + sentences[i].lower() for i in short])
            for i, t in zip(short, tries):
                t2 = re.sub(r"^" + art + r"\s+", "", t.strip(), flags=re.I) if t else t
                if t2 and not re.match(r"the\b", t2, re.I) and _norm_text(t2) != _norm_text(sentences[i]):      # "the ..." back = not translated
                    outputs[i] = t2
    return outputs


class EngineError(Exception):
    pass


SP_MARK = "\u2581"   # SentencePiece word-start marker; the game font draws it as "_"


def detokenize(sp, tokens):
    """Pieces -> text. sp.decode() is right when the pieces are plain; if the marker still comes through (pieces
    carrying it inside, or one joined piece) fall back to joining and turning the marker into a space."""
    try:
        text = sp.decode(list(tokens))
    except Exception:
        text = "".join(tokens)
    if SP_MARK in text:
        text = "".join(tokens).replace(SP_MARK, " ")
    return " ".join(text.split())          # no leading/trailing/double spaces


class EchoEngine:
    """Test engine: wraps text so tests can see it was 'translated'."""
    name = "echo"

    def __init__(self, target="xx"):
        self.target = target

    def translate_batch(self, texts):
        return [f"{t} ({self.target})" for t in texts]


class CT2Engine:
    name = "ctranslate2"

    def __init__(self, model_root: Path, threads: int = 0, family=None):
        self.family = family            # target language family (articles to strip when a label is retried), None = unknown
        try:
            import ctranslate2
            import sentencepiece
        except ImportError as e:  # pragma: no cover
            raise EngineError(f"missing dependency: {e}")
        from . import models
        model_bin, sp, sp_out = models.find_model_files(model_root)
        if model_bin is None or sp is None:
            what = models.listing(model_root)
            log.error("model files missing under %s (model.bin=%s tokenizer=%s). Contents: %s", model_root, model_bin, sp, what)
            raise EngineError(f"model files not found in {Path(model_root).name} (the folder has: {what})")
        import time
        t0 = time.perf_counter()
        self._lock = threading.Lock()
        try:
            self._tr = ctranslate2.Translator(str(model_bin.parent), device="cpu",
                                              inter_threads=1, intra_threads=threads)
            self._sp = sentencepiece.SentencePieceProcessor(model_file=str(sp))
            self._sp_out = self._sp if sp_out == sp else sentencepiece.SentencePieceProcessor(model_file=str(sp_out))
        except Exception as e:
            log.exception("failed to load model from %s", model_bin.parent)
            raise EngineError(f"failed to load model: {type(e).__name__}: {e}")
        log.info("model loaded from %s in %.1fs", model_bin.parent, time.perf_counter() - t0)

    def translate_batch(self, texts):
        # Flatten to sentences so long descriptions don't overflow the model.
        flat, owner = [], []
        for i, t in enumerate(texts):
            for s in split_sentences(t):
                flat.append(s)
                owner.append(i)
        try:
            outs = self._run(flat)
            outs = retranslate_unchanged(flat, outs, self._run, self.family)
        except Exception:
            log.error("translate_batch failed: %d texts, %d sentences, longest=%d chars, first=%r",
                      len(texts), len(flat), max((len(s) for s in flat), default=0), flat[:1])
            raise
        out = [[] for _ in texts]
        for i, o in zip(owner, outs):
            out[i].append(o)
        return [" ".join(p) for p in out]

    def _run(self, sentences):
        tokens = [self._sp.encode(s, out_type=str) for s in sentences]
        with self._lock:
            results = self._tr.translate_batch(tokens, beam_size=4, max_decoding_length=512)
        return [detokenize(self._sp_out, r.hypotheses[0]) for r in results]


class PivotEngine:
    """src -> English -> tgt, for pairs without a direct model."""
    name = "pivot"

    def __init__(self, first, second):
        self.first, self.second = first, second

    def translate_batch(self, texts):
        return self.second.translate_batch(self.first.translate_batch(texts))


_engines = {}
_engines_lock = threading.Lock()


def _load(src, tgt):
    key = (src, tgt)
    if key not in _engines:
        folder = models_dir() / f"{src}_{tgt}"
        try:
            _engines[key] = CT2Engine(folder, family=languages.family(tgt))
        except EngineError as e:
            if "model files not found" in str(e):
                import shutil
                shutil.rmtree(folder, ignore_errors=True)       # a broken install is removed: the next try downloads the model again
                log.warning("removed the incomplete model folder %s", folder)
            raise
    return _engines[key]


def get_engine(src, tgt):
    """Engine for src->tgt: direct model, or pivot through English; loads installed models on first use."""
    from . import languages
    src, tgt = languages.model_code(src), languages.model_code(tgt)
    with _engines_lock:
        if (src, tgt) in _engines:
            return _engines[(src, tgt)]
        from . import models
        steps = models.installed_plan(src, tgt)
        if steps is None:
            raise EngineError(f"model {src}->{tgt} is not installed")
        if len(steps) == 1:
            return _load(*steps[0])
        eng = PivotEngine(_load(*steps[0]), _load(*steps[1]))
        _engines[(src, tgt)] = eng
        log.info("using pivot %s->en->%s", src, tgt)
        return eng


def set_engine(src, tgt, engine):
    """Used by tests to inject a fake engine."""
    with _engines_lock:
        _engines[(src, tgt)] = engine
