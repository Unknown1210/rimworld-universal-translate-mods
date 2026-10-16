"""The languages to translate into.

config.json keeps two things: "target" (the one language the game uses, exactly as before: the game mod reads it) and "targets" (every
language the player wants translated, as a list). The target is always part of the list, and the list never holds a language that has no
translation model. The list can be empty (the player unticked everything: nothing is translated until a language is ticked; the game
keeps using "target"). The Home tab and the Translate mods tab are two views of the same setting."""
from . import config, i18n, languages


def _clean(codes):
    out = []
    for c in codes or []:
        if not isinstance(c, str):
            continue
        c = languages.norm_target(c)
        if c in i18n.SUPPORTED_TARGETS and c not in out:
            out.append(c)
    return out


def primary():
    """The language the game uses (None if none was chosen yet)."""
    c = config.get("target")
    c = languages.norm_target(c) if isinstance(c, str) and c else None
    return c if c in i18n.SUPPORTED_TARGETS else None


def selected():
    """Every language to translate into: the one the game uses first, then the others in the order they were ticked."""
    raw = config.get("targets")
    p = primary()
    if not isinstance(raw, list):                      # never saved (older versions): just the language the game uses
        return [p] if p else []
    langs = _clean(raw)
    if p and p in langs:
        langs = [p] + [c for c in langs if c != p]
    return langs


def set_selected(codes, game_language=None):
    """Save the list. `game_language` is the one the game uses; it must be in the list (when it is not, or is None, the current one is
    kept if it is still ticked, else the first ticked language). An empty list is saved as it is (nothing ticked; "target" stays)."""
    langs = _clean(codes)
    if not langs:
        config.set("targets", [])
        return []
    p = languages.norm_target(game_language) if game_language else primary()
    if p not in langs:
        p = langs[0]
    ordered = [p] + [c for c in langs if c != p]
    config.set("targets", ordered)
    if config.get("target") != p:
        config.set("target", p)
    return ordered


def set_game_language(code):
    """The game language was chosen on its own (the box on the Home tab): it joins the list if it was not in it."""
    code = languages.norm_target(code)
    return set_selected(selected() + [code], code)
