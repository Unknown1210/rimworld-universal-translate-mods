"""Offline language detection, a faithful port of the mod's LangDetect.cs (same word lists, same rules), so the helper
and the game decide the same way. Non-Latin scripts per string; Latin-script languages per mod from many texts;
weak evidence -> English."""
import re

_STOP = {k: set(v.split()) for k, v in {
    "en": "the of and to is that it for with as on be are this by or from your you can will an at not has have was were its their which",
    "pt": "de que o do da em um para com não uma os no se na por mais as dos como mas foi ao ele das tem seu sua ou ser quando muito há nos já está você também são pelo pela até isso",
    "es": "de la que el en y los del se las por un para con no una su al lo como más pero sus le ya este sí porque esta entre cuando muy sin sobre también me hasta hay donde son",
    "fr": "de la le les et des en un du une que est pour qui dans par au sur pas plus avec ce il ne se son sa ses ou sont mais comme nous vous cette être",
    "de": "der die und in den von zu das mit sich des auf für ist im dem nicht ein eine als auch es an werden aus er hat dass sie nach wird bei einer um am sind noch wie",
    "it": "di e il la che è per un in con non una sono le da del della si dei più come ma al ho gli lo anche questo nel alla",
    "nl": "de van het een en in is dat op te zijn voor met die niet aan er maar om ook als bij of uit",
    "pl": "i w nie na się z do to że jest jak po co ale za od przez czy dla tak już",
    "tr": "ve bir bu için ile da de çok olarak daha gibi en ama ne kadar",
    "cs": "a se na je že s v to z do o ale pro jako by si",
    "hu": "a az és hogy nem is egy meg de van",
    "sv": "och i att det som en på är av för med till den har",
}.items()}

_MARKS = {"pt": "ãõ", "es": "ñ¿¡", "de": "ß", "fr": "œê", "pl": "ąćęłńśźż", "tr": "ğşı", "cs": "řěů", "hu": "őű"}


def script_lang(text):
    """ISO code if the text is mainly in a non-Latin script; None for Latin-script text (or no letters)."""
    letters = han = kana = hangul = cyr = arabic = hebrew = thai = greek = deva = ukr = 0
    for c in text:
        if not c.isalpha():
            continue
        letters += 1
        o = ord(c)
        if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
            han += 1
        elif 0x3040 <= o <= 0x30FF or 0x31F0 <= o <= 0x31FF:
            kana += 1
        elif 0xAC00 <= o <= 0xD7AF or 0x1100 <= o <= 0x11FF:
            hangul += 1
        elif 0x0400 <= o <= 0x04FF:
            cyr += 1
            if c in "іїєґІЇЄҐ":
                ukr += 1
        elif 0x0600 <= o <= 0x06FF:
            arabic += 1
        elif 0x0590 <= o <= 0x05FF:
            hebrew += 1
        elif 0x0E00 <= o <= 0x0E7F:
            thai += 1
        elif 0x0370 <= o <= 0x03FF:
            greek += 1
        elif 0x0900 <= o <= 0x097F:
            deva += 1
    if letters == 0:
        return None
    nonlatin = han + kana + hangul + cyr + arabic + hebrew + thai + greek + deva
    if nonlatin * 10 < letters * 3:
        return None
    if kana > 0:
        return "ja"
    if hangul >= han and hangul >= cyr and hangul > 0:
        return "ko"
    if han > 0 and han >= max(cyr, arabic, hebrew, thai, greek, deva):
        return "zh"
    if cyr > 0 and cyr >= max(arabic, hebrew, thai, greek, deva):
        return "uk" if ukr > 0 else "ru"
    if arabic > 0 and arabic >= max(hebrew, thai, greek, deva):
        return "ar"
    if hebrew > 0 and hebrew >= max(thai, greek, deva):
        return "he"
    if thai > 0 and thai >= max(greek, deva):
        return "th"
    if greek > 0 and greek >= deva:
        return "el"
    return "hi" if deva > 0 else None


def latin_lang(texts):
    """-> (language, confident, detail). Not confident means the answer is the default "en"."""
    score = {k: 0 for k in _STOP}
    words = 0
    for text in texts:
        if script_lang(text) is not None:
            continue
        for w in re.findall(r"[^\W\d_]+", text):
            words += 1
            w = w.lower()
            for k, stop in _STOP.items():
                if w in stop:
                    score[k] += 1
            for k, marks in _MARKS.items():
                score[k] += 2 * sum(1 for ch in w if ch in marks)
    ranked = sorted(score.items(), key=lambda kv: -kv[1])
    best, bs = ranked[0]
    ss = ranked[1][1] if len(ranked) > 1 else 0
    confident = bs >= 3 and bs * 10 >= max(ss, 0) * 14
    detail = f"words={words} " + " ".join(f"{k}={v}" for k, v in score.items() if v > 0)
    return (best if confident else "en"), confident, detail
