"""Entry point of the packaged .exe (the package uses relative imports, so cli.py cannot be the entry script).

The .exe is built WITHOUT a console window: double-click opens only the window. For command-line use
(`UniversalTranslate-Helper.exe update --check`) it attaches to the console it was started from.
If something fails while the window is hidden-console, a message box shows the error and the log folder."""
import sys
import traceback


def _attach_console():
    """Windowed exe started from a terminal with arguments: reuse that terminal for output (best effort)."""
    if sys.platform != "win32" or sys.stdout is not None:
        return
    try:
        import ctypes
        if ctypes.windll.kernel32.AttachConsole(-1):          # ATTACH_PARENT_PROCESS
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
            sys.stderr = sys.stdout
            sys.stdin = open("CONIN$", "r", encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _selftest(path):
    """`--selftest FILE`: write what a freshly built exe can load. Used by the release job (no console needed)."""
    lines = []
    from rwtranslate import __version__
    lines.append(f"version={__version__} frozen={bool(getattr(sys, 'frozen', False))}")
    for mod in ("tkinter", "ctranslate2", "sentencepiece", "rwtranslate.gui", "rwtranslate.bulk", "rwtranslate.updater"):
        try:
            __import__(mod)
            lines.append(f"{mod}=ok")
        except Exception as e:  # noqa: BLE001
            lines.append(f"{mod}=FAILED {type(e).__name__}: {e}")
    ok = all("FAILED" not in l for l in lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(("OK\n" if ok else "BAD\n") + "\n".join(lines) + "\n")
    return 0 if ok else 1


def _show_error():
    msg = traceback.format_exc()
    try:
        from rwtranslate.paths import logs_dir
        where = f"\n\nDetalhes / Details: {logs_dir()}"
    except Exception:  # noqa: BLE001
        where = ""
    if sys.stderr is not None:
        sys.stderr.write(msg + where + "\n")
    try:
        import tkinter
        from tkinter import messagebox
        r = tkinter.Tk()
        r.withdraw()
        messagebox.showerror("Universal Translate", msg[-1500:] + where)
        r.destroy()
    except Exception:  # noqa: BLE001
        pass


def _run():
    frozen = getattr(sys, "frozen", False)
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        sys.exit(_selftest(sys.argv[2]))
    if frozen and len(sys.argv) > 1:
        _attach_console()
    from rwtranslate.cli import main
    if frozen and len(sys.argv) == 1:
        # double-clicked .exe: open the window; fall back to the console only if no window is possible
        try:
            from rwtranslate import gui
            gui.main()
            return
        except Exception:  # noqa: BLE001 - ImportError (no tkinter) / TclError (no display)
            _show_error()
            return
    sys.exit(main())


if __name__ == "__main__":
    try:
        _run()
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except BaseException:  # noqa: BLE001
        _show_error()
        sys.exit(1)
