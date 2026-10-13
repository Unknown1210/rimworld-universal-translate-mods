"""Protect RimWorld markup from the translator.

Markers that must survive translation unchanged:
  {0} {PAWN_nameDef} {1_labelShort}   - format arguments
  <color=#ff0000>...</color>, <b>, <i>, <size=..>  - rich text tags
  \\n and real newlines              - line breaks
  (*Name) (/Name)                   - RimWorld "(*Color)" colour tags
"""
import re

MARKER_RE = re.compile(
    r"\{[^{}]*\}"            # {0}, {PAWN_nameDef}
    r"|</?[A-Za-z][^<>]*>"   # <color=#fff>, </color>, <b>
    r"|\(\*[^()\s]*\)|\(/[^()\s]*\)"  # (*Name) (/Name)
    r"|\\n"                  # literal backslash-n
    r"|\r?\n"                # real newline
)

TOKEN_FMT = "[{}]"
_TOKEN_RE = re.compile(r"\[(\d+)\]")


def split_segments(text):
    """-> list of (is_marker, string), covering text exactly."""
    out, pos = [], 0
    for m in MARKER_RE.finditer(text):
        if m.start() > pos:
            out.append((False, text[pos:m.start()]))
        out.append((True, m.group(0)))
        pos = m.end()
    if pos < len(text):
        out.append((False, text[pos:]))
    return out


def has_text(segments):
    return any(not m and any(c.isalpha() for c in s) for m, s in segments)


def to_tokens(text):
    """Replace markers by numbered tokens. Returns (tokenized, markers) or None if unsafe."""
    if _TOKEN_RE.search(text):
        return None  # source already looks like our tokens: use the segment fallback
    markers, parts = [], []
    for is_marker, s in split_segments(text):
        if is_marker:
            parts.append(TOKEN_FMT.format(len(markers)))
            markers.append(s)
        else:
            parts.append(s)
    return "".join(parts), markers


def from_tokens(translated, markers):
    """Restore markers; None if the translator lost/duplicated/invented any token."""
    found = [int(n) for n in _TOKEN_RE.findall(translated)]
    if sorted(found) != list(range(len(markers))):
        return None
    return _TOKEN_RE.sub(lambda m: markers[int(m.group(1))], translated)


def translate_protected(text, translate_batch):
    """Translate one string keeping markers intact.

    translate_batch: callable list[str] -> list[str] (plain text, no markup).
    Strategy: tokenize + validate; on failure translate text segments separately.
    """
    segs = split_segments(text)
    if not has_text(segs):
        return text
    if all(not m for m, _ in segs):
        return _keep_space(text, translate_batch([text.strip()])[0])
    tok = to_tokens(text)
    if tok is not None:
        tokenized, markers = tok
        restored = from_tokens(translate_batch([tokenized])[0], markers)
        if restored is not None:
            return restored
    # Fallback: translate each text segment on its own (never corrupts markers).
    pieces = [s for m, s in segs if not m and any(c.isalpha() for c in s)]
    done = iter(translate_batch([p.strip() for p in pieces])) if pieces else iter(())
    out = []
    for is_marker, s in segs:
        if is_marker or not any(c.isalpha() for c in s):
            out.append(s)
        else:
            out.append(_keep_space(s, next(done)))
    return "".join(out)


def _keep_space(original, translated):
    lead = original[: len(original) - len(original.lstrip())]
    trail = original[len(original.rstrip()):]
    return lead + translated + trail


def clean_output(source, translated, target):
    """Last line of defence applied to every translation before it leaves the helper:
    no SentencePiece markers ("_" in game), no stray edge spaces, and the first letter keeps the SOURCE's case
    (RimWorld labels are lowercase in the XML and the game capitalises them itself; descriptions start uppercase)."""
    t = translated.replace("\u2581", " ")
    lead = t[: len(t) - len(t.lstrip())] if source[:1].isspace() else ""
    t = t.strip()
    s = source.lstrip()
    if not t or not s:
        return lead + t
    i = next((k for k, c in enumerate(t) if c.isalpha()), None)
    j = next((k for k, c in enumerate(s) if c.isalpha()), None)
    if i is not None and j is not None:
        if s[j].isupper() and t[i].islower():
            t = t[:i] + t[i].upper() + t[i + 1:]
        elif s[j].islower() and t[i].isupper() and target != "de" and not (len(t) > i + 1 and t[i + 1].isupper()):
            t = t[:i] + t[i].lower() + t[i + 1:]      # lowercase label; not for German nouns, not for acronyms ("HP")
    return lead + t
