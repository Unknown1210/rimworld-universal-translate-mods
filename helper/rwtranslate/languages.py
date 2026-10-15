"""Language detection (system / game) and name -> ISO code mapping."""
import locale
import os
import sys
import unicodedata

# Languages for which Argos publishes an en->X model (checked against the index at runtime too).
# Keys: lowercase, accent-free names as RimWorld shows them (LanguageInfo.friendlyNameNative / folder name).
GAME_LANGUAGES = {
    "english": "en",
    "portugues brasileiro": "pt-BR", "portuguese brazilian": "pt-BR", "portuguesebrazilian": "pt-BR",
    "portugues": "pt-PT", "portuguese": "pt-PT",
    "espanol": "es", "spanish": "es", "espanol castellano": "es", "spanishlatin": "es-419",
    "francais": "fr", "french": "fr",
    "deutsch": "de", "german": "de",
    "italiano": "it", "italian": "it",
    "russian": "ru", "russkij": "ru",
    "polski": "pl", "polish": "pl",
    "turkce": "tr", "turkish": "tr",
    "ukrainian": "uk",
    "cestina": "cs", "czech": "cs",
    "nederlands": "nl", "dutch": "nl",
    "magyar": "hu", "hungarian": "hu",
    "japanese": "ja", "korean": "ko",
    "chinese simplified": "zh", "simplified chinese": "zh", "chinesesimplified": "zh",
    "chinese traditional": "zh-Hant", "chinesetraditional": "zh-Hant",
    "spanish latin": "es-419", "espanol latinoamerica": "es-419", "espanol latino": "es-419",
    "korean fast channel": "ko-FC", "koreanfastchannel": "ko-FC",
    "norwegian": "nb", "norwegian bokmal": "nb", "norsk": "nb",
    "catalan": "ca", "danish": "da", "dansk": "da", "estonian": "et", "finnish": "fi", "greek": "el",
    "romanian": "ro", "slovak": "sk", "swedish": "sv", "vietnamese": "vi",
}


# Argos models "English -> X" that exist (checked in the Argos index; the window languages and the target languages must all be here).
ARGOS_FROM_ENGLISH = frozenset({"ar", "az", "bg", "bn", "ca", "de", "el", "eo", "es", "et", "eu", "fa", "fi", "fr", "ga", "gl", "he",
                                "hi", "id", "it", "ja", "ko", "ky", "lt", "lv", "ms", "nb", "nl", "pb", "pt", "ro", "ru", "sk", "sl",
                                "sq", "sv", "sw", "th", "tl", "tr", "uk", "ur", "vi", "zh", "zt"})


# English -> X models that cannot be used: the package is missing from the Argos index (Danish, Hungarian), or it uses a tokenizer
# format this program cannot read (Czech, Polish). Confirmed by running them. These languages are not offered as a target or a window language.
NO_ENGLISH_MODEL = frozenset({"cs", "da", "hu", "pl"})


# Target languages with regional variants. RimWorld has two Portuguese languages (folders "Portuguese" = Portugal and
# "PortugueseBrazilian" = Brazil) and Argos has a model for each: "pb" is Brazilian, "pt" is the general/European one.
FAMILY = {"pb": "pt"}          # model/detector codes that belong to the same language as another code


# Variants that share a model with another language: code -> Argos model code
MODEL_OF = {"zh-hant": "zt", "es-419": "es", "ko-fc": "ko"}
CANONICAL = {"zh-hant": "zh-Hant", "es-419": "es-419", "ko-fc": "ko-FC"}


def norm_target(code):
    """Canonical target code: "pt" (old settings) and "pt-br" become "pt-BR"; "pt-pt" becomes "pt-PT"; others are lowercased."""
    if not code:
        return code
    c = code.strip().replace("_", "-")
    low = c.lower()
    if low in ("pt", "pb", "pt-br"):
        return "pt-BR"
    if low == "pt-pt":
        return "pt-PT"
    return CANONICAL.get(low, low)


def model_code(code):
    """Code of the Argos model: pt-BR -> pb, pt-PT -> pt, everything else unchanged (a plain "pt" is a SOURCE language: model "pt")."""
    low = (code or "").replace("_", "-").lower()
    return "pb" if low == "pt-br" else "pt" if low == "pt-pt" else MODEL_OF.get(low, code)


def family(code):
    """Language without region or variant: pt-BR, pt-PT, pb and pt are all "pt"."""
    if not code:
        return code
    b = code.replace("_", "-").split("-")[0].lower()
    return FAMILY.get(b, b)


def same(a, b):
    """True when both codes are the same language (variants of Portuguese count as the same: text cannot be told apart)."""
    return bool(a) and bool(b) and family(a) == family(b)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().replace("_", " ").replace("-", " ").split())


def code_from_game_language(name: str):
    """Map a RimWorld language name (native or folder name) to an ISO code, or None."""
    if not name:
        return None
    n = _norm(name)
    if n in GAME_LANGUAGES:
        return GAME_LANGUAGES[n]
    return GAME_LANGUAGES.get(n.replace(" ", ""))


def system_language():
    """ISO 639-1 code of the OS UI/locale language, or None."""
    tag = _system_tag()
    if not tag or tag in ("C", "POSIX"):
        return None
    return tag.replace("_", "-").split(".")[0].split("-")[0].lower() or None


def _system_tag():
    """Raw locale tag of the OS (e.g. "pt-BR"), or None."""
    tag = None
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(85)
            if ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85):
                tag = buf.value  # e.g. pt-BR
        except Exception:
            tag = None
    if not tag:
        for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
            v = os.environ.get(var)
            if v:
                tag = v.split(":")[0]
                break
    if not tag:
        try:
            tag = locale.getlocale()[0] or locale.getdefaultlocale()[0]
        except Exception:
            tag = None
    return tag


def suggest(game_language=None, system=None):
    """Suggested target language code.

    1) game language if it is not English; 2) system language if not English;
    3) None (ask the user).
    """
    g = code_from_game_language(game_language) if game_language else None
    if g and g != "en":
        return g
    s = system if system is not None else system_language()
    if s == "pt":                                   # the OS region tells Brazil from Portugal; without one, Brazil
        tag = (_system_tag() or "") if system is None else ""
        return "pt-PT" if tag.replace("_", "-").upper().startswith("PT-PT") else "pt-BR"
    if s and s != "en":
        return s
    return None
