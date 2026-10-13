"""Texts of the helper window in Portuguese and English. The language follows the system language
(pt* -> Portuguese, anything else -> English) unless the user picked one; the choice is remembered in config.json."""
from . import config, languages
from .paths import data_dir  # noqa: F401  (tests reach the data dir through this module)

UI_LANGS = ("pt", "en")

TEXT = {
    "pt": {
        "title": "Universal Translate - auxiliar v{v}",
        "keep_open": "Deixe esta janela aberta enquanto joga RimWorld.",
        "running": "Em execução (só neste computador, porta {port})",
        "models": "Modelos instalados: {models}",
        "none": "nenhum ainda",
        "target_lang": "Idioma de destino:",
        "download_model": "Baixar modelo",
        "downloading": "Baixando o modelo para '{lang}'... (pode demorar)",
        "model_failed": "Falha ao baixar o modelo: {err}",
        "model_ok": "Modelo instalado.",
        "checking": "Procurando atualização...",
        "check_btn": "Procurar atualização",
        "apply_btn": "Atualizar agora",
        "logs_btn": "Abrir pasta de logs",
        "report_btn": "Relatório de problema",
        "quit_btn": "Sair",
        "ui_lang": "Idioma da janela:",
        "check_failed": "Não foi possível verificar: {err}",
        "new_version": "Nova versão disponível: {latest} (você tem {current}).",
        "up_to_date": "Você já está na versão mais nova ({current}).",
        "py_update": "Auxiliar (versão Python): atualize com pip a partir do ZIP novo.",
        "helper_updated": "Auxiliar atualizado.",
        "mod_updated": "Mod atualizado ({n} arquivos) em {path}.",
        "mod_zip_saved": "Pasta do mod não encontrada. Zip novo salvo em {path}; extraia em RimWorld\\Mods.",
        "mod_not_updated": "Mod NÃO atualizado: {err}",
        "update_failed": "A atualização falhou: {err}",
        "restarting": "Reiniciando...",
        "report_saved": "Relatório salvo: {name}. Arraste-o para a página que abriu no navegador.",
        "report_failed": "Falha ao criar o relatório: {err}",
        "tab_home": "Início",
        "tab_bulk": "Traduzir mods",
        "target_saved": "Idioma de destino: {lang}. O jogo usa este idioma automaticamente.",
        "target_none": "Escolha o idioma de destino acima.",
        "model_ready": "Modelo pronto (inglês para {lang}).",
        "model_missing": "O modelo para {lang} ainda não foi baixado.",
        "bulk_intro": "Traduz todos os mods instalados, mesmo os que não estão ativados no jogo. Quando você jogar, as traduções já estarão prontas.",
        "bulk_nodirs": "Nenhuma pasta de mods encontrada. Clique em \"Adicionar pasta\".",
        "bulk_dirs_title": "Pastas pesquisadas (todas, sempre que você procurar mods)",
        "dir_default": "padrão",
        "dir_added": "adicionada por você",
        "dir_missing": "não encontrada",
        "bulk_add_dir": "Adicionar pasta...",
        "bulk_scan": "Procurar mods",
        "bulk_start_pending": "Traduzir pendentes ({n})",
        "bulk_start_all": "Refazer tudo",
        "bulk_stop": "Parar",
        "bulk_clear": "Excluir traduções",
        "bulk_clear_title": "Excluir traduções",
        "bulk_clear_confirm": "Excluir TODAS as traduções salvas em {lang}?\n\nOs mods voltam a aparecer como novos e serão traduzidos de novo se você mandar. Suas correções manuais (arquivo overrides) são mantidas. Isso não pode ser desfeito.",
        "bulk_cleared": "{n} arquivo(s) de tradução excluído(s) ({lang}).",
        "bulk_scanning": "Procurando mods...",
        "bulk_progress": "{done} de {total} mods ({pct}%)",
        "bulk_current": "Traduzindo: {name} ({done}/{total} textos)",
        "bulk_model": "Baixando o modelo {pair}... (pode demorar)",
        "bulk_summary": "Mods: {mods}   Pendentes: {pending}   Textos: {texts}   Palavras traduzidas: {words}",
        "bulk_done": "Concluído: {mods} mod(s) traduzido(s), {words} palavras. Se instalar mais mods, clique em \"Procurar mods\".",
        "bulk_cancelled": "Interrompido. O que já foi traduzido ficou salvo.",
        "bulk_all_ok": "Todos os mods estão traduzidos e atualizados.",
        "bulk_need_target": "Escolha o idioma de destino na aba Início.",
        "bulk_error": "Erro: {err}",
        "col_mod": "Mod",
        "col_source": "Origem",
        "col_texts": "Textos",
        "col_words": "Palavras",
        "col_state": "Estado",
        "col_folder": "Pasta",
        "folder_open": "Abrir pasta",
        "st_new": "Novo (não traduzido)",
        "st_changed": "Alterado (traduzir de novo)",
        "st_ok": "Traduzido",
        "st_running": "Traduzindo...",
        "st_nosupport": "Sem suporte: {pairs}",
        "st_failed": "{n} texto(s) falharam",
        "st_error": "Erro ao ler o mod",
        "det_title": "Detalhes: {name}",
        "det_summary": "Textos a traduzir: {texts}   Traduzidos agora: {translated}   Do cache: {cached}   Palavras: {words}\nJá tinham tradução de verdade: {covered}   Já no seu idioma: {already}   Sem suporte: {unsupported}   Falharam: {failed}",
        "det_placeholders": "{n} texto(s) tinham um arquivo de \"tradução\" com o texto igual ao original (ou em outro idioma); isso não é tradução, então eles foram traduzidos.",
        "det_tab_translated": "Traduzidos ({n})",
        "det_tab_skipped": "Não traduzidos por nós ({n})",
        "det_col_orig": "Original",
        "det_col_trans": "Tradução",
        "det_col_reason": "Motivo",
        "det_full_orig": "Original:",
        "det_full_trans": "Tradução:",
        "det_empty": "Ainda não há nada traduzido para este mod.",
        "det_close": "Fechar",
        "det_hint": "Dê dois cliques em um mod para ver o que foi traduzido.",
        "r_covered": "Já tem tradução ({provider})",
        "r_already": "Já está no seu idioma",
        "r_unsupported": "Sem suporte: {pair}",
        "r_failed": "A tradução falhou",
    },
    "en": {
        "title": "Universal Translate - helper v{v}",
        "keep_open": "Keep this window open while you play RimWorld.",
        "running": "Running (this computer only, port {port})",
        "models": "Installed models: {models}",
        "none": "none yet",
        "target_lang": "Target language:",
        "download_model": "Download model",
        "downloading": "Downloading the model for '{lang}'... (this can take a while)",
        "model_failed": "Could not download the model: {err}",
        "model_ok": "Model installed.",
        "checking": "Checking for updates...",
        "check_btn": "Check for updates",
        "apply_btn": "Update now",
        "logs_btn": "Open logs folder",
        "report_btn": "Problem report",
        "quit_btn": "Quit",
        "ui_lang": "Window language:",
        "check_failed": "Could not check: {err}",
        "new_version": "New version available: {latest} (you have {current}).",
        "up_to_date": "You already have the latest version ({current}).",
        "py_update": "Helper (Python version): update with pip from the new ZIP.",
        "helper_updated": "Helper updated.",
        "mod_updated": "Mod updated ({n} files) in {path}.",
        "mod_zip_saved": "Mod folder not found. New zip saved to {path}; extract it into RimWorld\\Mods.",
        "mod_not_updated": "Mod NOT updated: {err}",
        "update_failed": "The update failed: {err}",
        "restarting": "Restarting...",
        "report_saved": "Report saved: {name}. Drag it onto the page that opened in your browser.",
        "report_failed": "Could not create the report: {err}",
        "tab_home": "Home",
        "tab_bulk": "Translate mods",
        "target_saved": "Target language: {lang}. The game uses it automatically.",
        "target_none": "Choose the target language above.",
        "model_ready": "Model ready (English to {lang}).",
        "model_missing": "The model for {lang} has not been downloaded yet.",
        "bulk_intro": "Translates every installed mod, even those not enabled in the game. When you play, the translations are already done.",
        "bulk_nodirs": "No mod folder found. Click \"Add folder\".",
        "bulk_dirs_title": "Folders searched (all of them, every time you search for mods)",
        "dir_default": "default",
        "dir_added": "added by you",
        "dir_missing": "not found",
        "bulk_add_dir": "Add folder...",
        "bulk_scan": "Search for mods",
        "bulk_start_pending": "Translate pending ({n})",
        "bulk_start_all": "Redo all",
        "bulk_stop": "Stop",
        "bulk_clear": "Delete translations",
        "bulk_clear_title": "Delete translations",
        "bulk_clear_confirm": "Delete ALL saved translations in {lang}?\n\nThe mods show up as new again and will be translated again if you ask. Your manual corrections (the overrides file) are kept. This cannot be undone.",
        "bulk_cleared": "{n} translation file(s) deleted ({lang}).",
        "bulk_scanning": "Searching for mods...",
        "bulk_progress": "{done} of {total} mods ({pct}%)",
        "bulk_current": "Translating: {name} ({done}/{total} texts)",
        "bulk_model": "Downloading model {pair}... (this can take a while)",
        "bulk_summary": "Mods: {mods}   Pending: {pending}   Texts: {texts}   Words translated: {words}",
        "bulk_done": "Done: {mods} mod(s) translated, {words} words. If you install more mods, click \"Search for mods\".",
        "bulk_cancelled": "Stopped. What was already translated is saved.",
        "bulk_all_ok": "All mods are translated and up to date.",
        "bulk_need_target": "Choose the target language on the Home tab.",
        "bulk_error": "Error: {err}",
        "col_mod": "Mod",
        "col_source": "Source",
        "col_texts": "Texts",
        "col_words": "Words",
        "col_state": "State",
        "col_folder": "Folder",
        "folder_open": "Open folder",
        "st_new": "New (not translated)",
        "st_changed": "Changed (translate again)",
        "st_ok": "Translated",
        "st_running": "Translating...",
        "st_nosupport": "No support: {pairs}",
        "st_failed": "{n} text(s) failed",
        "st_error": "Could not read the mod",
        "det_title": "Details: {name}",
        "det_summary": "Texts to translate: {texts}   Translated now: {translated}   From cache: {cached}   Words: {words}\nAlready had a real translation: {covered}   Already in your language: {already}   No support: {unsupported}   Failed: {failed}",
        "det_placeholders": "{n} text(s) had a \"translation\" file holding the same text as the original (or another language); that is not a translation, so they were translated.",
        "det_tab_translated": "Translated ({n})",
        "det_tab_skipped": "Not translated by us ({n})",
        "det_col_orig": "Original",
        "det_col_trans": "Translation",
        "det_col_reason": "Reason",
        "det_full_orig": "Original:",
        "det_full_trans": "Translation:",
        "det_empty": "Nothing has been translated for this mod yet.",
        "det_close": "Close",
        "det_hint": "Double-click a mod to see what was translated.",
        "r_covered": "Already has a translation ({provider})",
        "r_already": "Already in your language",
        "r_unsupported": "No support: {pair}",
        "r_failed": "The translation failed",
    },
}


def system_ui_lang():
    s = languages.system_language()
    return "pt" if s == "pt" else "en"


def load_choice():
    c = config.get("ui_lang")
    return c if c in UI_LANGS else None


def save_choice(code):
    config.set("ui_lang", code)


def current():
    return load_choice() or system_ui_lang()


def tr(_ui, key, **kw):
    """_ui is positional on purpose: texts may use a {lang} placeholder, which must not collide with this parameter."""
    text = TEXT.get(_ui, TEXT["en"]).get(key) or TEXT["en"][key]
    return text.format(**kw) if kw else text


# Target languages offered in the window: the ones that have a translation model (checked against the live Argos index
# when it can be reached; this is the list as of the last check). Portuguese is split into Brazil and Portugal.
SUPPORTED_TARGETS = ["pt-BR", "pt-PT", "en", "es", "fr", "de", "it", "ru", "pl", "tr", "uk", "zh", "ja", "ko", "nl", "cs",
                     "ar", "az", "bg", "bn", "ca", "da", "el", "eo", "et", "eu", "fa", "fi", "ga", "gl", "he", "hi", "hu", "id",
                     "ky", "lt", "lv", "ms", "nb", "ro", "sk", "sl", "sq", "sv", "sw", "th", "tl", "ur", "vi"]

# Language names: code -> (English, Portuguese, native). Shown in full, in the window language, with the native name.
NAMES = {
    "en": ("English", "Inglês", "English"), "pt": ("Portuguese", "Português", "Português"),
    "pt-BR": ("Portuguese (Brazil)", "Português (Brasil)", "Português (Brasil)"),
    "pt-PT": ("Portuguese (Portugal)", "Português (Portugal)", "Português (Portugal)"),
    "az": ("Azerbaijani", "Azerbaijano", "Azərbaycanca"), "bg": ("Bulgarian", "Búlgaro", "Български"),
    "bn": ("Bengali", "Bengali", "বাংলা"), "eo": ("Esperanto", "Esperanto", "Esperanto"),
    "et": ("Estonian", "Estoniano", "Eesti"), "eu": ("Basque", "Basco", "Euskara"),
    "fa": ("Persian", "Persa", "فارسی"), "ga": ("Irish", "Irlandês", "Gaeilge"),
    "gl": ("Galician", "Galego", "Galego"), "ky": ("Kyrgyz", "Quirguiz", "Кыргызча"),
    "lt": ("Lithuanian", "Lituano", "Lietuvių"), "lv": ("Latvian", "Letão", "Latviešu"),
    "ms": ("Malay", "Malaio", "Bahasa Melayu"), "sl": ("Slovenian", "Esloveno", "Slovenščina"),
    "sq": ("Albanian", "Albanês", "Shqip"), "sw": ("Swahili", "Suaíli", "Kiswahili"),
    "tl": ("Tagalog", "Tagalo", "Tagalog"), "ur": ("Urdu", "Urdu", "اردو"),
    "es": ("Spanish", "Espanhol", "Español"), "fr": ("French", "Francês", "Français"),
    "de": ("German", "Alemão", "Deutsch"), "it": ("Italian", "Italiano", "Italiano"),
    "ru": ("Russian", "Russo", "Русский"), "uk": ("Ukrainian", "Ucraniano", "Українська"),
    "pl": ("Polish", "Polonês", "Polski"), "tr": ("Turkish", "Turco", "Türkçe"),
    "cs": ("Czech", "Tcheco", "Čeština"), "nl": ("Dutch", "Holandês", "Nederlands"),
    "hu": ("Hungarian", "Húngaro", "Magyar"), "sv": ("Swedish", "Sueco", "Svenska"),
    "da": ("Danish", "Dinamarquês", "Dansk"), "fi": ("Finnish", "Finlandês", "Suomi"),
    "nb": ("Norwegian", "Norueguês", "Norsk"), "el": ("Greek", "Grego", "Ελληνικά"),
    "ro": ("Romanian", "Romeno", "Română"), "sk": ("Slovak", "Eslovaco", "Slovenčina"),
    "ca": ("Catalan", "Catalão", "Català"), "ja": ("Japanese", "Japonês", "日本語"),
    "ko": ("Korean", "Coreano", "한국어"), "zh": ("Chinese", "Chinês", "中文"),
    "ar": ("Arabic", "Árabe", "العربية"), "he": ("Hebrew", "Hebraico", "עברית"),
    "hi": ("Hindi", "Hindi", "हिन्दी"), "id": ("Indonesian", "Indonésio", "Bahasa Indonesia"),
    "th": ("Thai", "Tailandês", "ไทย"), "vi": ("Vietnamese", "Vietnamita", "Tiếng Việt"),
}


def lang_label(code, ui):
    """'Japonês (日本語)' in a Portuguese window, 'Japanese (日本語)' in an English one; unknown codes are shown as-is."""
    n = NAMES.get(code)
    if not n:
        return code
    name = n[1] if ui == "pt" else n[0]
    return name if name == n[2] else f"{name} ({n[2]})"


def lang_choices(codes, ui):
    """[(label, code)] sorted by label."""
    return sorted(((lang_label(c, ui), c) for c in codes), key=lambda x: x[0].lower())
