"""Texts of the helper window: Portuguese and English by hand, every other RimWorld language machine-translated (uitext.py). The language follows the system language
(pt* -> Portuguese, anything else -> English) unless the user picked one; the choice is remembered in config.json."""
from . import config, languages
from .paths import data_dir  # noqa: F401  (tests reach the data dir through this module)

# Window languages = the languages RimWorld itself offers (the same list as the target languages). "pt" and "en" are written by
# hand; every other one is machine-translated from the English texts on first use (see uitext.py) and cached.
GAME_LANGS = ["ca", "zh", "zh-Hant", "cs", "da", "nl", "en", "et", "fi", "fr", "de", "el", "hu", "it", "ja", "ko", "ko-FC", "nb",
              "pl", "pt-PT", "pt-BR", "ro", "ru", "sk", "es", "es-419", "sv", "tr", "uk", "vi"]
UI_LANGS = tuple(GAME_LANGS)
HANDWRITTEN = ("pt", "en")

TEXT = {
    "pt": {
        "title": "Universal Translate - auxiliar v{v}",
        "running": "Em execução (só neste computador, porta {port})",
        "models": "Modelos instalados: {models}",
        "none": "nenhum ainda",
        "target_lang": "Idioma de destino da tradução:",
        "download_model": "Baixar modelo",
        "downloading": "Baixando o modelo para '{lang}'... (pode demorar)",
        "model_failed": "Falha ao baixar o modelo: {err}",
        "model_ok": "Modelo instalado.",
        "checking": "Procurando atualização...",
        "check_btn": "Procurar atualização",
        "apply_btn": "Atualizar agora",
        "changelog_btn": "Ver changelog",
        "logs_btn": "Abrir pasta de logs",
        "data_folder_btn": "Abrir pasta de dados",
        "mod_folder_btn": "Abrir pasta do mod",
        "mod_folder_missing": "Não achei a pasta do mod Auto Translate Mods. Procurei em RimWorld\\Mods, na Oficina da Steam e nas pastas da aba Traduzir mods. Se ele estiver em outro lugar, adicione essa pasta na aba Traduzir mods.",
        "report_btn": "Relatório de problema",
        "github_btn": "Página no GitHub",
        "quit_btn": "Sair",
        "copy_text": "Copiar",
        "select_all": "Selecionar tudo",
        "opt1_title": "1) Jogue com este programa aberto",
        "opt1_body": "Deixe esta janela aberta enquanto joga RimWorld. O jogo pede e o programa traduz sozinho, mod por mod, e salva tudo. Serve para os mods ativados e para os textos que só existem durante o jogo.",
        "opt1_note": "É mais lento na primeira vez. Textos criados em código por alguns mods (como botões de ações da aba Ordens) só são traduzidos com o programa aberto: abra-o ANTES de iniciar o RimWorld. Quando tudo estiver traduzido, dá para jogar com o programa fechado.",
        "opt_or": "ou",
        "opt2_title": "2) Traduza tudo agora (mais rápido)",
        "opt2_body": "Na aba Traduzir mods, clique em Traduzir pendentes. O programa traduz todos os mods de uma vez, até os que estão desativados, antes de você abrir o jogo.",
        "opt2_note": "Quando você jogar, as traduções já estarão prontas.",
        "opt2_btn": "Ir para Traduzir mods",
        "bg_all": "Traduzir também os mods desativados, em segundo plano",
        "bg_locked": "Há uma tradução em andamento. Para mudar esta opção, pare a tradução na aba Traduzir mods (botão Parar).",
        "bg_note": "O jogo tem prioridade: os mods que ele está usando são traduzidos primeiro, e os outros em seguida.",
        "log_bulk_auto": "Traduzindo em segundo plano os mods que ainda faltam, mesmo os desativados (os do jogo têm prioridade).",
        "restart_note": "Se você traduzir ou atualizar os mods com o jogo aberto e não vir a tradução aplicada, reinicie o jogo.",
        "ui_lang": "Idioma da janela:",
        "ui_preparing": "Preparando...",
        "ui_prepare_failed": "Não deu para preparar este idioma: {err}",
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
        "tab_log": "Log",
        "log_hint": "Aqui aparece tudo o que o programa faz, inclusive o que o jogo pede (cada texto e a sua tradução). Clique em uma linha para ver os detalhes.",
        "log_col_time": "Hora",
        "log_col_kind": "Tipo",
        "log_col_msg": "O que aconteceu",
        "log_kind_game": "Jogo",
        "log_kind_bulk": "Lote",
        "log_kind_model": "Modelos",
        "log_kind_update": "Atualização",
        "log_kind_system": "Sistema",
        "log_filter": "Mostrar:",
        "log_filter_all": "Tudo",
        "log_filter_problems": "Só avisos e erros",
        "log_copy": "Copiar log",
        "log_clear": "Limpar",
        "log_copied": "Log copiado ({n} linhas).",
        "log_empty": "Nada aconteceu ainda.",
        "log_lvl_warning": "aviso",
        "log_lvl_error": "ERRO",
        "log_started": "Programa iniciado (versão {version}).",
        "log_game_batch": "O jogo pediu tradução: {n} texto(s) ({src} → {tgt}) do mod {mod}, {chars} caracteres, {ms} ms.  {first}",
        "log_model_asked": "O jogo pediu o modelo {src} → {tgt}.",
        "log_model_download": "Baixando o modelo {src} → {tgt} de {url}",
        "log_model_done": "Modelo {src} → {tgt} instalado.",
        "log_model_failed": "Falha ao instalar o modelo {src} → {tgt}.",
        "log_bulk_start": "Tradução em lote iniciada: {total} de {all} mod(s), idioma {target}.",
        "log_bulk_mod_start": "[{i}/{total}] {name}: começando ({status}).",
        "log_bulk_mod": "{name}: {texts} texto(s) a traduzir, {translated} traduzido(s) agora, {cache} do cache, {covered} já com tradução, {already} já no seu idioma, {failed} falha(s), {words} palavra(s); sem suporte: {unsupported}.",
        "log_bulk_mod_error": "{name}: erro: {err}",
        "log_bulk_cancelled": "Tradução em lote interrompida em {done} de {total}.",
        "log_bulk_finished": "Tradução em lote concluída ({total} mod(s)).",
        "log_update_check": "Procura de atualização: versão atual {current}, mais nova {latest}, há atualização: {available}.",
        "log_update_helper": "Programa atualizado para {tag}.",
        "log_update_mod": "Mod atualizado para {tag} ({n} arquivo(s)).",
        "target_saved": "Idioma de destino: {lang}. O jogo usa este idioma automaticamente.",
        "target_none": "Escolha o idioma de destino para traduzir os mods.",
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
        "bulk_progress_eta": "{done} de {total} mods ({pct}%) - tempo restante estimado: {eta}",
        "bulk_current": "Traduzindo: {name} ({done}/{total} textos) ({wdone}/{wtotal} palavras)",
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
        "st_game_running": "Traduzindo pelo jogo...",
        "st_game_done": "Traduzido pelo jogo",
        "st_nosupport": "Sem suporte: {pairs}",
        "st_failed": "{n} texto(s) falharam",
        "st_error": "Erro ao ler o mod",
        "det_title": "Detalhes: {name}",
        "det_summary": "Textos a traduzir: {texts}   Traduzidos agora: {translated}   Do cache: {cached}   Palavras: {words}\nJá tinham tradução de verdade: {covered}   Já no seu idioma: {already}   Sem suporte: {unsupported}   Falharam: {failed}",
        "det_placeholders": "{n} texto(s) tinham um arquivo de \"tradução\" com o texto igual ao original (ou em outro idioma); isso não é tradução, então eles foram traduzidos.",
        "det_tab_translated": "Textos traduzidos ({n})",
        "det_tab_skipped": "Não traduzidos pelo mod ({n})",
        "det_col_orig": "Original",
        "det_col_trans": "Tradução",
        "det_col_existing": "Tradução existente",
        "det_col_words": "Palavras",
        "det_tab_words": "Palavras traduzidas ({n})",
        "det_col_reason": "Motivo",
        "det_full_orig": "Original:",
        "det_full_trans": "Tradução:",
        "det_full_why": "Por que falhou:",
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
        "running": "Running (this computer only, port {port})",
        "models": "Installed models: {models}",
        "none": "none yet",
        "target_lang": "Translation target language:",
        "download_model": "Download model",
        "downloading": "Downloading the model for '{lang}'... (this can take a while)",
        "model_failed": "Could not download the model: {err}",
        "model_ok": "Model installed.",
        "checking": "Checking for updates...",
        "check_btn": "Check for updates",
        "apply_btn": "Update now",
        "changelog_btn": "View changelog",
        "logs_btn": "Open logs folder",
        "data_folder_btn": "Open data folder",
        "mod_folder_btn": "Open mod folder",
        "mod_folder_missing": "Could not find the Auto Translate Mods folder. I looked in RimWorld\\Mods, the Steam Workshop and the folders of the Translate mods tab. If it is somewhere else, add that folder in the Translate mods tab.",
        "report_btn": "Problem report",
        "github_btn": "GitHub page",
        "quit_btn": "Quit",
        "copy_text": "Copy",
        "select_all": "Select all",
        "opt1_title": "1) Play with this program open",
        "opt1_body": "Keep this window open while you play RimWorld. The game asks and the program translates by itself, mod by mod, and saves everything. It covers the enabled mods and the texts that only exist during the game.",
        "opt1_note": "It is slower the first time. Texts that some mods build in code (such as the action buttons of the Orders tab) are only translated with the program open: open it BEFORE starting RimWorld. When everything is translated you can play with the program closed.",
        "opt_or": "or",
        "opt2_title": "2) Translate everything now (faster)",
        "opt2_body": "In the Translate mods tab, click Translate pending. The program translates all the mods at once, even the disabled ones, before you open the game.",
        "opt2_note": "When you play, the translations are already done.",
        "opt2_btn": "Go to Translate mods",
        "bg_all": "Also translate the disabled mods, in the background",
        "bg_locked": "A translation is running. To change this option, stop it in the Translate mods tab (Stop button).",
        "bg_note": "The game comes first: the mods it is using are translated first, and the others right after.",
        "log_bulk_auto": "Translating the remaining mods in the background, even the disabled ones (the game's mods come first).",
        "restart_note": "If you translate or update mods while the game is open and you do not see the translation applied, restart the game.",
        "ui_lang": "Window language:",
        "ui_preparing": "Preparing...",
        "ui_prepare_failed": "Could not prepare this language: {err}",
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
        "tab_log": "Log",
        "log_hint": "Everything the program does shows up here, including what the game asks for (every text and its translation). Click a line to see the details.",
        "log_col_time": "Time",
        "log_col_kind": "Type",
        "log_col_msg": "What happened",
        "log_kind_game": "Game",
        "log_kind_bulk": "Batch",
        "log_kind_model": "Models",
        "log_kind_update": "Update",
        "log_kind_system": "System",
        "log_filter": "Show:",
        "log_filter_all": "Everything",
        "log_filter_problems": "Warnings and errors only",
        "log_copy": "Copy log",
        "log_clear": "Clear",
        "log_copied": "Log copied ({n} lines).",
        "log_empty": "Nothing has happened yet.",
        "log_lvl_warning": "warning",
        "log_lvl_error": "ERROR",
        "log_started": "Program started (version {version}).",
        "log_game_batch": "The game asked for a translation: {n} text(s) ({src} → {tgt}) from mod {mod}, {chars} characters, {ms} ms.  {first}",
        "log_model_asked": "The game asked for model {src} → {tgt}.",
        "log_model_download": "Downloading model {src} → {tgt} from {url}",
        "log_model_done": "Model {src} → {tgt} installed.",
        "log_model_failed": "Could not install model {src} → {tgt}.",
        "log_bulk_start": "Batch translation started: {total} of {all} mod(s), language {target}.",
        "log_bulk_mod_start": "[{i}/{total}] {name}: starting ({status}).",
        "log_bulk_mod": "{name}: {texts} text(s) to translate, {translated} translated now, {cache} from cache, {covered} already translated, {already} already in your language, {failed} failure(s), {words} word(s); no support: {unsupported}.",
        "log_bulk_mod_error": "{name}: error: {err}",
        "log_bulk_cancelled": "Batch translation stopped at {done} of {total}.",
        "log_bulk_finished": "Batch translation finished ({total} mod(s)).",
        "log_update_check": "Update check: current version {current}, latest {latest}, update available: {available}.",
        "log_update_helper": "Program updated to {tag}.",
        "log_update_mod": "Mod updated to {tag} ({n} file(s)).",
        "target_saved": "Target language: {lang}. The game uses it automatically.",
        "target_none": "Choose the target language to translate the mods.",
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
        "bulk_progress_eta": "{done} of {total} mods ({pct}%) - estimated time left: {eta}",
        "bulk_current": "Translating: {name} ({done}/{total} texts) ({wdone}/{wtotal} words)",
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
        "st_game_running": "Translating for the game...",
        "st_game_done": "Translated for the game",
        "st_nosupport": "No support: {pairs}",
        "st_failed": "{n} text(s) failed",
        "st_error": "Could not read the mod",
        "det_title": "Details: {name}",
        "det_summary": "Texts to translate: {texts}   Translated now: {translated}   From cache: {cached}   Words: {words}\nAlready had a real translation: {covered}   Already in your language: {already}   No support: {unsupported}   Failed: {failed}",
        "det_placeholders": "{n} text(s) had a \"translation\" file holding the same text as the original (or another language); that is not a translation, so they were translated.",
        "det_tab_translated": "Translated texts ({n})",
        "det_tab_skipped": "Not translated by the mod ({n})",
        "det_col_orig": "Original",
        "det_col_trans": "Translation",
        "det_col_existing": "Existing translation",
        "det_col_words": "Words",
        "det_tab_words": "Words translated ({n})",
        "det_col_reason": "Reason",
        "det_full_orig": "Original:",
        "det_full_trans": "Translation:",
        "det_full_why": "Why it failed:",
        "det_empty": "Nothing has been translated for this mod yet.",
        "det_close": "Close",
        "det_hint": "Double-click a mod to see what was translated.",
        "r_covered": "Already has a translation ({provider})",
        "r_already": "Already in your language",
        "r_unsupported": "No support: {pair}",
        "r_failed": "The translation failed",
    },
}


def text_source(code):
    """Which set of texts a window language uses: Portuguese (Brazil and Portugal) share the handwritten Portuguese,
    Latin American Spanish shares Spanish, Korean Fast Channel shares Korean."""
    return {"pt-BR": "pt", "pt-PT": "pt", "es-419": "es", "ko-FC": "ko"}.get(code, code)


def normalize_choice(code):
    """Old settings stored "pt": that is Brazil now."""
    return "pt-BR" if code == "pt" else code


def system_ui_lang():
    tag = (languages._system_tag() or "").replace("_", "-").split(".")[0]
    if tag.upper().startswith("PT-PT"):
        return "pt-PT"
    s = languages.system_language()
    if s == "pt":
        return "pt-BR"
    if s == "zh":
        return "zh-Hant" if tag.lower().startswith(("zh-tw", "zh-hk", "zh-hant")) else "zh"
    return s if s in UI_LANGS else "en"


def load_choice():
    c = normalize_choice(config.get("ui_lang"))
    return c if c in UI_LANGS else None


def save_choice(code):
    config.set("ui_lang", code)


def current():
    return load_choice() or system_ui_lang()


def tr(_ui, key, **kw):
    """_ui is positional on purpose: texts may use a {lang} placeholder, which must not collide with this parameter."""
    src = text_source(_ui)
    text = TEXT[src].get(key) if src in TEXT else None
    if text is None and src not in HANDWRITTEN:
        from . import uitext
        text = uitext.lookup(src, key)
    text = text or TEXT["en"][key]
    if not kw:
        return text
    try:
        return text.format(**kw)
    except (KeyError, IndexError, ValueError):
        return TEXT["en"][key].format(**kw)         # a machine translation that lost a placeholder never breaks the window


# Target languages offered in the window: the ones that have a translation model (checked against the live Argos index
# when it can be reached; this is the list as of the last check). Portuguese is split into Brazil and Portugal.
SUPPORTED_TARGETS = list(GAME_LANGS)

# Language names: code -> (English, Portuguese, native), as RimWorld's own language list names them.
NAMES = {
    "ca": ("Catalan", "Catalão", "Català"),
    "zh": ("Chinese (Simplified)", "Chinês (Simplificado)", "简体中文"),
    "zh-Hant": ("Chinese (Traditional)", "Chinês (Tradicional)", "繁體中文"),
    "cs": ("Czech", "Tcheco", "Čeština"),
    "da": ("Danish", "Dinamarquês", "Dansk"),
    "nl": ("Dutch", "Holandês", "Nederlands"),
    "en": ("English", "Inglês", "English"),
    "et": ("Estonian", "Estoniano", "Eesti"),
    "fi": ("Finnish", "Finlandês", "Suomi"),
    "fr": ("French", "Francês", "Français"),
    "de": ("German", "Alemão", "Deutsch"),
    "el": ("Greek", "Grego", "Ελληνικά"),
    "hu": ("Hungarian", "Húngaro", "Magyar"),
    "it": ("Italian", "Italiano", "Italiano"),
    "ja": ("Japanese", "Japonês", "日本語"),
    "ko": ("Korean", "Coreano", "한국어"),
    "ko-FC": ("Korean (Fast Channel)", "Coreano (Fast Channel)", "한국어 (Fast Channel)"),
    "nb": ("Norwegian (Bokmål)", "Norueguês (Bokmål)", "Norsk bokmål"),
    "pl": ("Polish", "Polonês", "Polski"),
    "pt-PT": ("Portuguese (Portugal)", "Português (Portugal)", "Português (Portugal)"),
    "pt-BR": ("Portuguese (Brazil)", "Português (Brasil)", "Português (Brasil)"),
    "ro": ("Romanian", "Romeno", "Română"),
    "ru": ("Russian", "Russo", "Русский"),
    "sk": ("Slovak", "Eslovaco", "Slovenčina"),
    "es": ("Spanish (Castilian)", "Espanhol (Castelhano)", "Español (Castellano)"),
    "es-419": ("Spanish (Latin America)", "Espanhol (América Latina)", "Español (Latinoamérica)"),
    "sv": ("Swedish", "Sueco", "Svenska"),
    "tr": ("Turkish", "Turco", "Türkçe"),
    "uk": ("Ukrainian", "Ucraniano", "Українська"),
    "vi": ("Vietnamese", "Vietnamita", "Tiếng Việt"),
}


def lang_label(code, ui):
    """'Japonês (日本語)' in a Portuguese window, 'Japanese (日本語)' in an English one; unknown codes are shown as-is."""
    n = NAMES.get(code)
    if not n:
        return code
    name = n[1] if text_source(ui) == "pt" else n[0]
    return name if name == n[2] else f"{name} ({n[2]})"


def lang_choices(codes, ui):
    """[(label, code)] sorted by label."""
    return sorted(((lang_label(c, ui), c) for c in codes), key=lambda x: x[0].lower())
