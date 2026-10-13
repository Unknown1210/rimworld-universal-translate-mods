"""Translation engines. CT2Engine runs Argos/OpenNMT models fully offline on the CPU."""
import re
import threading
from pathlib import Path

from . import logsetup
from .paths import models_dir

log = logsetup.get("engine")

_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


def split_sentences(text):
    parts = [p for p in _SENT_RE.split(text.strip()) if p]
    return parts or [text]


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

    def __init__(self, model_root: Path, threads: int = 0):
        try:
            import ctranslate2
            import sentencepiece
        except ImportError as e:  # pragma: no cover
            raise EngineError(f"missing dependency: {e}")
        model_bin = next(model_root.rglob("model.bin"), None)
        sp = next(model_root.rglob("sentencepiece.model"), None)
        if model_bin is None or sp is None:
            listing = sorted(str(p.relative_to(model_root)) for p in model_root.rglob("*"))[:60]
            log.error("model files missing under %s (model.bin=%s sentencepiece.model=%s). Contents: %s",
                      model_root, model_bin, sp, listing)
            raise EngineError(f"model files not found under {model_root} (see helper.log)")
        import time
        t0 = time.perf_counter()
        self._lock = threading.Lock()
        try:
            self._tr = ctranslate2.Translator(str(model_bin.parent), device="cpu",
                                              inter_threads=1, intra_threads=threads)
            self._sp = sentencepiece.SentencePieceProcessor(model_file=str(sp))
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
            tokens = [self._sp.encode(s, out_type=str) for s in flat]
            with self._lock:
                results = self._tr.translate_batch(tokens, beam_size=4, max_decoding_length=512)
        except Exception:
            log.error("translate_batch failed: %d texts, %d sentences, longest=%d chars, first=%r",
                      len(texts), len(flat), max((len(s) for s in flat), default=0), flat[:1])
            raise
        out = [[] for _ in texts]
        for i, r in zip(owner, results):
            out[i].append(detokenize(self._sp, r.hypotheses[0]))
        return [" ".join(p) for p in out]


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
        _engines[key] = CT2Engine(models_dir() / f"{src}_{tgt}")
    return _engines[key]


def get_engine(src, tgt):
    """Engine for src->tgt: direct model, or pivot through English; loads installed models on first use."""
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
