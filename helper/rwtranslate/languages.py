"""Language detection (system / game) and name -> ISO code mapping."""
import locale
import os
import sys
import unicodedata

# Languages for which Argos publishes an en->X model (checked against the index at runtime too).
# Keys: lowercase, accent-free names as RimWorld shows them (LanguageInfo.friendlyNameNative / folder name).
GAME_LANGUAGES = {
    "english": "en",
    "portugues brasileiro": "pt", "portuguese brazilian": "pt", "portuguesebrazilian": "pt",
    "portugues": "pt", "portuguese": "pt",
    "espanol": "es", "spanish": "es", "espanol latino": "es", "spanishlatin": "es",
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
    "chinese traditional": "zh", "chinesetraditional": "zh",
}


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
    if not tag or tag in ("C", "POSIX"):
        return None
    return tag.replace("_", "-").split(".")[0].split("-")[0].lower() or None


def suggest(game_language=None, system=None):
    """Suggested target language code.

    1) game language if it is not English; 2) system language if not English;
    3) None (ask the user).
    """
    g = code_from_game_language(game_language) if game_language else None
    if g and g != "en":
        return g
    s = system if system is not None else system_language()
    if s and s != "en":
        return s
    return None
