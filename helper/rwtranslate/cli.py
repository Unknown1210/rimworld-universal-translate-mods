"""rwtranslate command line: serve | install | suggest | status"""
import argparse
import sys
from pathlib import Path

from . import config, __version__, diagnostics, languages, logsetup, models, updater
from .server import DEFAULT_PORT, load_or_create_token, serve


ISSUES_URL = "https://github.com/Unknown1210/rimworld-universal-translate-mods/issues/new?labels=bug"


def _ask_language(suggested):
    avail = models.available_targets()
    shown = suggested if suggested in avail else None
    print("Idiomas disponíveis:", ", ".join(avail))
    prompt = f"Idioma de destino [{shown}]: " if shown else "Idioma de destino: "
    while True:
        a = (input(prompt).strip().lower() or (shown or ""))
        if a in avail:
            return a
        print("Código inválido.")


def _update(a):
    print(f"Versão atual: {__version__}. Procurando atualização no GitHub...")
    chk = updater.check()
    if chk.error:
        print(chk.error)
        return 1
    if not chk.available:
        print(f"Você já está na versão mais nova ({chk.current}).")
        return 0
    print(f"Nova versão disponível: {chk.latest}\n{chk.notes.split('### Como instalar')[0].strip()}\n")
    if a.check:
        return 0
    if not a.yes and input("Atualizar agora? [s/N] ").strip().lower() not in ("s", "sim", "y", "yes"):
        return 0
    try:
        if updater.is_frozen():
            updater.update_helper(chk.release, progress=print)
            print("Auxiliar atualizado.")
        else:
            print("Versão Python: atualize com `pip install --upgrade` a partir do ZIP novo do GitHub.")
        mod = Path(a.mod_dir) if a.mod_dir else updater.find_mod_dir()
        if mod:
            print(f"Mod atualizado ({updater.update_mod(chk.release, mod, progress=print)} arquivos) em {mod}.")
        else:
            print("Pasta do mod não encontrada (use --mod-dir). Zip salvo em:", updater.save_mod_zip(chk.release, progress=print))
    except updater.UpdateError as e:
        print("Falha:", e)
        return 1
    print("Pronto. Abra o programa novamente.")
    return 0


def main(argv=None):
    config.migrate_portuguese()
    ap = argparse.ArgumentParser(prog="rwtranslate")
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--debug", action="store_true", help="log nível DEBUG")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("serve", help="inicia o servidor local (padrão)")
    s.add_argument("--port", type=int, default=DEFAULT_PORT)
    i = sub.add_parser("install", help="baixa o modelo de um idioma (de inglês) ou de um par: install zh pt")
    i.add_argument("lang", nargs="?", help="idioma de destino (origem inglês) ou idioma de origem se houver um segundo código")
    i.add_argument("target", nargs="?", help="idioma de destino quando o primeiro é a origem")
    i.add_argument("--game-language", help="nome do idioma ativo no jogo, p/ sugestão")
    g = sub.add_parser("suggest", help="mostra o idioma sugerido")
    g.add_argument("--game-language")
    sub.add_parser("status", help="mostra modelos instalados")
    u = sub.add_parser("update", help="procura e instala a versão mais nova do GitHub")
    u.add_argument("--check", action="store_true", help="só verifica, não instala")
    u.add_argument("--yes", action="store_true", help="não pergunta")
    u.add_argument("--mod-dir", help="pasta RimWorld\\Mods\\AutoTranslate (se não for achada sozinha)")
    sub.add_parser("gui", help="abre a janela (padrão no .exe)")
    sub.add_parser("report", help="gera o .zip de diagnóstico e mostra o link para abrir um relatório no GitHub")
    sub.add_parser("diagnostics", help="gera um .zip com logs e ambiente para relatar um problema")
    a = ap.parse_args(argv)
    cmd = a.cmd or "serve"
    logsetup.setup(debug=a.debug, console=(cmd == "serve"))
    updater.cleanup_old()

    if cmd == "suggest":
        print(languages.suggest(a.game_language) or "indefinido")
    elif cmd == "status":
        print("Modelos instalados:", ", ".join(models.installed_pairs()) or "nenhum")
    elif cmd == "gui":
        from . import gui
        gui.main()
    elif cmd == "update":
        return _update(a)
    elif cmd == "report":
        z = diagnostics.make_bundle()
        print("Arquivo gerado:", z)
        print("1) Abra:", ISSUES_URL)
        print("2) Descreva o problema e arraste o arquivo acima para a página.")
    elif cmd == "diagnostics":
        print("Arquivo gerado:", diagnostics.make_bundle())
    elif cmd == "install":
        if a.lang and a.target:
            models.install(a.lang, a.target)      # explicit pair, e.g. "install zh pt"
        else:
            lang = a.lang or _ask_language(languages.suggest(a.game_language))
            models.install("en", lang)
    else:
        port = getattr(a, "port", DEFAULT_PORT)
        if not models.installed_pairs() and sys.stdin.isatty():
            print("Nenhum modelo instalado ainda.")
            models.install("en", _ask_language(languages.suggest()))
        httpd = serve(port)
        load_or_create_token()
        print(f"\nUniversal Translate (auxiliar) v{__version__} está rodando em 127.0.0.1:{httpd.server_address[1]}.")
        print("DEIXE ESTA JANELA ABERTA enquanto joga RimWorld. Para sair: Ctrl+C ou feche a janela.\n")
        import threading

        def _notice():
            chk = updater.check()
            if chk.available:
                print(f"\n>>> Nova versão disponível: {chk.latest}. Para atualizar, feche e rode:  rwtranslate update\n")
        threading.Thread(target=_notice, daemon=True, name="update-notice").start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    sys.exit(main())
