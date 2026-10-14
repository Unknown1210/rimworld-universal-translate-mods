"""Single words that a context-free translator gets wrong in RimWorld item names.

Labels are translated alone ("safe"), so the engine picks the adjective ("seguro") instead of the noun the game means
(a strongbox). Only whole-text matches are replaced; the first letter keeps the source's case (see clean_output)."""
from . import languages

# English source label -> {target language family: translation}
EN = {
    "safe": {"pt": "cofre", "es": "caja fuerte", "ca": "caixa forta", "fr": "coffre-fort", "it": "cassaforte",
             "de": "Tresor", "nl": "kluis", "pl": "sejf", "ro": "seif", "cs": "trezor", "sk": "trezor",
             "ru": "сейф", "uk": "сейф", "tr": "kasa"},
}


def lookup(source, target, text):
    """Return the glossary translation of `text` or None."""
    if languages.family(source) != "en":
        return None
    row = EN.get(" ".join(text.split()).lower())
    if not row:
        return None
    return row.get(languages.family(target))
