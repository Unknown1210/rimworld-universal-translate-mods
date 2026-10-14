"""Single words that a context-free translator gets wrong in RimWorld item names.

Labels are translated alone ("safe"), so the engine picks the adjective ("seguro") instead of the noun the game means
(a strongbox). Only whole-text matches are replaced; the first letter keeps the source's case (see clean_output)."""
from . import languages

# English source label -> {target language family: translation}
EN = {
    "safe": {"pt": "cofre", "es": "caja fuerte", "ca": "caixa forta", "fr": "coffre-fort", "it": "cassaforte",
             "de": "Tresor", "nl": "kluis", "pl": "sejf", "ro": "seif", "cs": "trezor", "sk": "trezor",
             "ru": "сейф", "uk": "сейф", "tr": "kasa"},
    "mine": {"pt": "mina", "es": "mina", "ca": "mina", "fr": "mine", "it": "miniera", "ro": "mină", "pl": "kopalnia",
             "cs": "důl", "sk": "baňa", "nl": "mijn", "ru": "шахта", "uk": "шахта", "tr": "maden"},
}


def lookup(source, target, text):
    """Return the glossary translation of `text` or None."""
    if languages.family(source) != "en":
        return None
    row = EN.get(" ".join(text.split()).lower())
    if not row:
        return None
    return row.get(languages.family(target))


def repair_entries(entries, target):
    """A saved cache ({normalized source: translation}) with the glossary words and the bare-label full stop fixed in place
    (translations saved by an older version). Returns how many entries changed."""
    from .protect import clean_output
    changed = 0
    for k, v in list(entries.items()):
        if not isinstance(v, str):
            continue
        g = lookup("en", target, k)
        new = clean_output(k, g if g is not None else v, target)
        if new and new != v:
            entries[k] = new
            changed += 1
    return changed
