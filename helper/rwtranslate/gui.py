"""Window of the packaged .exe, two tabs:
  Home              - state of the helper, TARGET LANGUAGE (saved in config.json; the game mod follows it),
                      updates, logs, problem report.
  Translate all mods - translates every installed mod (even those not enabled in the game) with a progress bar,
                      a per-mod table and a summary; finds new/changed mods later.
Resizable: texts re-wrap and widgets stretch. Texts follow the system language (pt/en, see i18n).
The translation server runs in a background thread. Falls back to the console when no window can be opened."""
import os
import queue
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from . import __version__, activity, bulk, config, diagnostics, i18n, languages, logsetup, models, server, uitext, updater
from .paths import logs_dir

log = logsetup.get("gui")
ISSUES_URL = "https://github.com/Unknown1210/rimworld-universal-translate-mods/issues/new?labels=bug"
def ui_name(code):
    """Window language as the picker shows it: its own name first, the English name after it ("Deutsch - German")."""
    n = i18n.NAMES.get(code)
    if not n:
        return code
    return n[2] if n[2] == n[0] else f"{n[2]} - {n[0]}"


UI_NAMES = {c: ui_name(c) for c in i18n.UI_LANGS}
SUPPORTED_TARGETS = i18n.SUPPORTED_TARGETS


def open_folder(path):
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        log.exception("could not open folder %s", path)


class Field:
    """Text shown in a Label, remembered as (key, args) so it can be re-rendered when the window language changes.
    Plain Python object on purpose: tkinter's StringVar must be finalised by the main thread, and objects captured by
    worker threads can end up finalised there, which aborts the process on Windows
    ("Tcl_AsyncDelete: async handler deleted by the wrong thread"). Call from the main thread only."""

    def __init__(self, label, app):
        self.label, self.app = label, app
        self.value, self._key, self._kw = "", None, {}

    def set(self, text):
        self._key = None
        self.value = text
        self.label.configure(text=text)

    def set_key(self, key, **kw):
        self._key, self._kw = key, kw
        self.render()

    def render(self):
        if self._key is not None:
            self.value = self.app.t(self._key, **self._kw)
            self.label.configure(text=self.value)

    def get(self):
        return self.value


class App:
    RESTART_MS = 1200               # after a good update: time to read the message, then the new program opens
    RESTART_MS_MOD_PROBLEM = 9000  # the mod files could not be updated: more time to read why
    def __init__(self, root, httpd, fetcher=updater.fetch, exe_path=None, mod_dir=None, restart=None, lang=None, mod_dirs=None):
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.ttk = tk, ttk
        self.root, self.httpd, self.fetcher = root, httpd, fetcher
        self.exe_path, self.mod_dir_override = exe_path, mod_dir
        self.mod_dirs_override = mod_dirs                  # tests; None = detect Steam folders
        self.restart_fn = restart or self._restart
        self.lang = lang or i18n.current()
        self.ui_job = None                                 # language whose window texts are being prepared (translated) in the background
        self.q = queue.Queue()
        self.latest = None
        self.busy = False
        self.fields, self.static = [], []
        self.lang_codes = {}
        self.cancel = None
        self.bulk_running = False
        self.rows = {}
        self.plan_rows = []
        root.geometry("880x640")
        root.minsize(800, 520)
        root.protocol("WM_DELETE_WINDOW", self.quit)

        outer = ttk.Frame(root, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)
        self.outer = outer
        bar = ttk.Frame(outer)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)
        self.lbl_ui = ttk.Label(bar)
        self.lbl_ui.grid(row=0, column=1, padx=(0, 6))
        self.lbl_ui_note = ttk.Label(bar, foreground="#777777")
        self.lbl_ui_note.grid(row=0, column=0, sticky="e", padx=(0, 10))
        ui_values = sorted(UI_NAMES.values(), key=lambda n: n.lower())
        self.ui_box = ttk.Combobox(bar, width=28, state="readonly", values=ui_values)
        self.ui_box.set(UI_NAMES.get(self.lang, self.lang))
        self.ui_box.grid(row=0, column=2)
        self.ui_box.bind("<<ComboboxSelected>>", self.on_ui_lang)

        self.nb = ttk.Notebook(outer)
        self.nb.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.home = ttk.Frame(self.nb, padding=10)
        self.bulk_tab = ttk.Frame(self.nb, padding=10)
        self.log_tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.home, text="")
        self.nb.add(self.bulk_tab, text="")
        self.nb.add(self.log_tab, text="")
        self.build_home()
        self.build_bulk()
        self.build_log()

        root.bind("<Configure>", self.on_resize)
        self.apply_language()
        self.refresh_status()
        self._pump_id = self.root.after(100, self.pump)
        self._log_cb = lambda e: self.post(lambda: self.on_log_entry(e))        # entries come from other threads: hand them to this one
        activity.install_log_handler()
        activity.subscribe(self._log_cb)
        self.log_entries = list(activity.snapshot())
        self.render_log()
        self.start_check()
        self.refresh_plan()
        self.prepare_ui_texts()

    # ------------------------------------------------------------------ construction
    def field(self, parent, row, pady=(0, 2), color=None, sticky="ew"):
        lbl = self.ttk.Label(parent, anchor="center", justify="center", foreground=color or "")
        lbl.grid(row=row, column=0, sticky=sticky, pady=pady)
        f = Field(lbl, self)
        self.fields.append(f)
        return f

    def stretch(self, frame, buttons, uniform=True):
        """Buttons side by side filling the row. uniform=False: each one is at least as wide as its text (no cut-off labels)
        and the spare room is shared equally."""
        for i, b in enumerate(buttons):
            if uniform:
                frame.columnconfigure(i, weight=1, uniform="btn")
            else:
                frame.columnconfigure(i, weight=1)
            b.grid(row=0, column=i, sticky="ew", padx=3)

    def build_home(self):
        ttk, h = self.ttk, self.home
        h.columnconfigure(0, weight=1)
        h.rowconfigure(0, weight=1)
        h.rowconfigure(2, weight=1)
        content = ttk.Frame(h)
        content.grid(row=1, column=0, sticky="ew")
        content.columnconfigure(0, weight=1)
        self.content = content
        keep_box = ttk.Frame(content)
        keep_box.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        keep_box.columnconfigure(0, weight=1)
        self.lbl_keep = ttk.Label(keep_box, font=("TkDefaultFont", 11, "bold"), anchor="center", justify="center")
        self.lbl_keep.grid(row=0, column=0, sticky="ew")
        self.lbl_keep2 = ttk.Label(keep_box, foreground="#555555", anchor="center", justify="center")      # when it can be closed
        self.lbl_keep2.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.lbl_keep3 = ttk.Label(keep_box, foreground="#8a5a00", anchor="center", justify="center")      # texts only the running game can ask for
        self.lbl_keep3.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        self.lbl_keep4 = ttk.Label(keep_box, foreground="#555555", anchor="center", justify="center")      # restart if the game does not show new translations
        self.lbl_keep4.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        self.status = self.field(content, 1)
        self.status2 = self.field(content, 2, pady=(0, 8))

        # target language: the single place to choose it; the game mod reads config.json
        row = ttk.Frame(content)
        row.grid(row=3, column=0, pady=(0, 2))
        self.lbl_target = ttk.Label(row)
        self.lbl_target.grid(row=0, column=0, padx=(0, 6))
        self.lang_box = ttk.Combobox(row, width=26, state="readonly")
        self.lang_box.grid(row=0, column=1, padx=(0, 6))
        self.lang_box.bind("<<ComboboxSelected>>", self.on_target_selected)
        self.btn_model = ttk.Button(row, command=self.install_model)
        self.btn_model.grid(row=0, column=2)
        self.target_msg = self.field(content, 4, pady=(0, 6), color="#2a7a2a")
        self.set_lang_choices(SUPPORTED_TARGETS)

        ttk.Separator(content).grid(row=5, column=0, sticky="ew", pady=8)
        self.update_msg = self.field(content, 6)
        self.progress = self.field(content, 7, pady=(0, 8), color="#666666")
        row1 = ttk.Frame(content)
        row1.grid(row=8, column=0, sticky="ew", pady=3)
        self.btn_check = ttk.Button(row1, command=self.start_check)
        self.btn_apply = ttk.Button(row1, command=self.start_update, state="disabled")
        self.stretch(row1, [self.btn_check, self.btn_apply])
        row2 = ttk.Frame(content)
        row2.grid(row=9, column=0, sticky="ew", pady=3)
        self.btn_logs = ttk.Button(row2, command=lambda: open_folder(logs_dir()))
        self.btn_report = ttk.Button(row2, command=self.report)
        self.btn_quit = ttk.Button(row2, command=self.quit)
        self.stretch(row2, [self.btn_logs, self.btn_report, self.btn_quit])

    def build_bulk(self):
        ttk, b = self.ttk, self.bulk_tab
        b.columnconfigure(0, weight=1)
        b.rowconfigure(7, weight=1)
        self.bulk_intro = self.field(b, 0, pady=(0, 6))
        self.dirs_frame = ttk.LabelFrame(b, padding=6)
        self.dirs_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.dirs_frame.columnconfigure(0, weight=1)
        self.dir_labels = []                    # [(path label, tag label or None)] of the rows drawn by render_dirs
        self.dir_rows = []
        btns = ttk.Frame(b)
        btns.grid(row=2, column=0, sticky="ew", pady=3)
        self.btn_add_dir = ttk.Button(btns, command=self.add_dir)
        self.btn_scan = ttk.Button(btns, command=self.refresh_plan)
        self.btn_bulk = ttk.Button(btns, command=lambda: self.start_bulk(False), state="disabled")
        self.btn_bulk_all = ttk.Button(btns, command=lambda: self.start_bulk(True))
        self.btn_stop = ttk.Button(btns, command=self.stop_bulk, state="disabled")
        self.btn_clear = ttk.Button(btns, command=self.clear_translations)
        self.stretch(btns, [self.btn_add_dir, self.btn_scan, self.btn_bulk, self.btn_bulk_all, self.btn_stop, self.btn_clear], uniform=False)
        self.pbar = ttk.Progressbar(b, orient="horizontal", mode="determinate", maximum=100)
        self.pbar.grid(row=3, column=0, sticky="ew", pady=(8, 2))
        self.bulk_progress = self.field(b, 4, pady=(0, 0))
        self.bulk_current = self.field(b, 5, pady=(0, 4), color="#666666")
        self.bulk_summary = self.field(b, 6, pady=(0, 6))
        tf = ttk.Frame(b)
        tf.grid(row=7, column=0, sticky="nsew")
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)
        cols = ("mod", "source", "texts", "words", "state", "folder")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=8)
        # everything centred in its column, except the mod name (left); the last column opens the mod's folder when clicked
        for c, w, a in (("mod", 230, "w"), ("source", 80, "center"), ("texts", 70, "center"), ("words", 80, "center"),
                        ("state", 190, "center"), ("folder", 110, "center")):
            self.tree.column(c, width=w, anchor=a, stretch=(c in ("mod", "state")))
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", self.on_tree_double)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Motion>", self.on_tree_motion)
        self.row_mods = {}
        self.bulk_hint = self.field(b, 8, pady=(4, 0), color="#666666")

    LOG_FILTERS = ("all", "game", "bulk", "model", "update", "system", "problems")

    def build_log(self):
        ttk, lg = self.ttk, self.log_tab
        lg.columnconfigure(0, weight=1)
        lg.rowconfigure(2, weight=3)
        lg.rowconfigure(3, weight=2)
        self.log_msg = self.field(lg, 4, pady=(4, 0), color="#2a7a2a")
        self.log_entries = []
        self.log_rows = {}
        self.log_hint = self.field(lg, 0, pady=(0, 6), color="#666666")
        bar = ttk.Frame(lg)
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        bar.columnconfigure(3, weight=1)
        self.lbl_log_filter = ttk.Label(bar)
        self.lbl_log_filter.grid(row=0, column=0, padx=(0, 6))
        self.log_filter_box = ttk.Combobox(bar, state="readonly", width=24)
        self.log_filter_box.grid(row=0, column=1, padx=(0, 12))
        self.log_filter_box.bind("<<ComboboxSelected>>", lambda _e: self.render_log())
        self.btn_log_copy = ttk.Button(bar, command=self.copy_log)
        self.btn_log_copy.grid(row=0, column=2, padx=3)
        self.btn_log_clear = ttk.Button(bar, command=self.clear_log)
        self.btn_log_clear.grid(row=0, column=3, padx=3, sticky="w")
        self.btn_log_folder = ttk.Button(bar, command=lambda: open_folder(logs_dir()))
        self.btn_log_folder.grid(row=0, column=4, padx=3, sticky="e")
        tf = ttk.Frame(lg)
        tf.grid(row=2, column=0, sticky="nsew")
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)
        self.log_tree = ttk.Treeview(tf, columns=("time", "kind", "msg"), show="headings", height=10)
        for c, w, a, st in (("time", 70, "center", False), ("kind", 90, "center", False), ("msg", 600, "w", True)):
            self.log_tree.column(c, width=w, anchor=a, stretch=st)
        self.log_tree.tag_configure("warning", foreground="#a15c00")
        self.log_tree.tag_configure("error", foreground="#b00020")
        self.log_tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.log_tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log_tree.configure(yscrollcommand=sb.set)
        self.log_tree.bind("<<TreeviewSelect>>", self.on_log_select)
        df = ttk.Frame(lg)
        df.grid(row=3, column=0, sticky="nsew", pady=(6, 0))
        df.columnconfigure(0, weight=1)
        df.rowconfigure(0, weight=1)
        self.log_detail = self.tk.Text(df, height=8, wrap="word")
        self.log_detail.grid(row=0, column=0, sticky="nsew")
        dsb = ttk.Scrollbar(df, orient="vertical", command=self.log_detail.yview)
        dsb.grid(row=0, column=1, sticky="ns")
        self.log_detail.configure(yscrollcommand=dsb.set, state="disabled")

    def entry_text(self, e):
        """The message of a log entry in the current window language (raw technical entries are shown as they are)."""
        if e.key is None:
            return str(e.args.get("text", ""))
        try:
            return self.t(e.key, **e.args)
        except (KeyError, IndexError):
            return e.key

    def log_filter_key(self):
        i = self.log_filter_box.current()
        return self.LOG_FILTERS[i] if 0 <= i < len(self.LOG_FILTERS) else "all"

    def log_passes(self, e):
        f = self.log_filter_key()
        if f == "all":
            return True
        if f == "problems":
            return e.level in ("warning", "error")
        return e.kind == f

    def log_row_values(self, e):
        kind = self.t("log_kind_" + e.kind)
        if e.level in ("warning", "error"):
            kind += " (" + self.t("log_lvl_" + e.level) + ")"
        return (time.strftime("%H:%M:%S", time.localtime(e.when)), kind, " ".join(self.entry_text(e).split()))

    def add_log_row(self, e):
        iid = self.log_tree.insert("", "end", values=self.log_row_values(e), tags=(e.level,))
        self.log_rows[iid] = e
        return iid

    def render_log(self):
        """Draw the entries again (filter or window language changed); the selected entry stays selected."""
        sel = self.log_rows.get((self.log_tree.selection() or [None])[0])
        self.log_tree.delete(*self.log_tree.get_children())
        self.log_rows = {}
        keep = None
        for e in self.log_entries[-activity.MAX_ENTRIES:]:
            if self.log_passes(e):
                iid = self.add_log_row(e)
                if e is sel:
                    keep = iid
        if keep:
            self.log_tree.selection_set(keep)
        self.log_tree.yview_moveto(1.0)
        self.on_log_select()

    def on_log_entry(self, e):
        """An entry arrived from any thread: keep it, and show it if the filter allows (follow the end only if already at the end)."""
        self.log_entries.append(e)
        if len(self.log_entries) > activity.MAX_ENTRIES:
            del self.log_entries[: len(self.log_entries) - activity.MAX_ENTRIES]
        if self.log_passes(e):
            at_end = self.log_tree.yview()[1] >= 0.98
            iid = self.add_log_row(e)
            kids = self.log_tree.get_children()
            if len(kids) > activity.MAX_ENTRIES:
                self.log_rows.pop(kids[0], None)
                self.log_tree.delete(kids[0])
            if at_end:
                self.log_tree.see(iid)

    def on_log_select(self, _event=None):
        sel = self.log_tree.selection()
        e = self.log_rows.get(sel[0]) if sel else None
        self.log_detail.configure(state="normal")
        self.log_detail.delete("1.0", "end")
        if e is not None:
            body = e.detail_text()
            self.log_detail.insert("end", self.entry_text(e) + ("\n\n" + body if body else ""))
        elif not self.log_entries:
            self.log_detail.insert("end", self.t("log_empty"))
        self.log_detail.configure(state="disabled")

    def apply_log_language(self):
        t = self.t
        self.log_hint.set_key("log_hint")
        self.lbl_log_filter.configure(text=t("log_filter"))
        i = max(0, self.log_filter_box.current())
        self.log_filter_box.configure(values=[t("log_filter_" + k) if k in ("all", "problems") else t("log_kind_" + k) for k in self.LOG_FILTERS])
        self.log_filter_box.current(i)
        self.btn_log_copy.configure(text=t("log_copy"))
        self.btn_log_clear.configure(text=t("log_clear"))
        self.btn_log_folder.configure(text=t("logs_btn"))
        for col, key in (("time", "log_col_time"), ("kind", "log_col_kind"), ("msg", "log_col_msg")):
            self.log_tree.heading(col, text=t(key), anchor="center")
        self.render_log()

    def copy_log(self):
        lines = []
        for e in self.log_entries:
            if not self.log_passes(e):
                continue
            tm, kind, msg = self.log_row_values(e)
            lines.append(f"{tm} [{kind}] {msg}")
            body = e.detail_text()
            if body:
                lines += ["    " + ln for ln in body.split("\n")]
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(lines))
        self.log_msg.set_key("log_copied", n=len(lines))

    def clear_log(self):
        activity.clear()
        self.log_entries = []
        self.render_log()

    def on_resize(self, event):
        if event.widget is not self.root:
            return
        wrap = max(200, event.width - 90)
        for f in self.fields:
            f.label.configure(wraplength=wrap)
        self.lbl_keep.configure(wraplength=wrap)
        self.lbl_keep2.configure(wraplength=wrap)
        self.lbl_keep3.configure(wraplength=wrap)
        self.lbl_keep4.configure(wraplength=wrap)
        for path_lbl, _tag in self.dir_labels:
            path_lbl.configure(wraplength=max(150, wrap - 140))

    # ------------------------------------------------------------------ language of the window
    def t(self, key, **kw):
        if key == "title":
            kw.setdefault("v", __version__)
        return i18n.tr(self.lang, key, **kw)

    def apply_language(self):
        t = self.t
        self.root.title(t("title"))
        self.nb.tab(self.home, text=t("tab_home"))
        self.nb.tab(self.bulk_tab, text=t("tab_bulk"))
        self.nb.tab(self.log_tab, text=t("tab_log"))
        self.lbl_keep.configure(text=t("keep_open"))
        self.lbl_keep2.configure(text=t("keep_open2"))
        self.lbl_keep3.configure(text=t("keep_open3"))
        self.lbl_keep4.configure(text=t("keep_open4"))
        self.lbl_ui.configure(text=t("ui_lang"))
        self.lbl_target.configure(text=t("target_lang"))
        self.btn_model.configure(text=t("download_model"))
        self.btn_check.configure(text=t("check_btn"))
        self.btn_apply.configure(text=t("apply_btn"))
        self.btn_logs.configure(text=t("logs_btn"))
        self.btn_report.configure(text=t("report_btn"))
        self.btn_quit.configure(text=t("quit_btn"))
        self.btn_add_dir.configure(text=t("bulk_add_dir"))
        self.btn_scan.configure(text=t("bulk_scan"))
        self.btn_bulk_all.configure(text=t("bulk_start_all"))
        self.btn_stop.configure(text=t("bulk_stop"))
        self.btn_clear.configure(text=t("bulk_clear"))
        self.bulk_hint.set_key("det_hint")
        self.update_bulk_buttons()
        self.render_dirs()
        for col, key in (("mod", "col_mod"), ("source", "col_source"), ("texts", "col_texts"), ("words", "col_words"),
                         ("state", "col_state"), ("folder", "col_folder")):
            self.tree.heading(col, text=t(key), anchor="center")
        for f in self.fields:
            f.render()
        self.set_lang_choices(list(self.lang_codes.values()) or SUPPORTED_TARGETS)
        self.render_rows()
        self.apply_log_language()
        self.refresh_details_windows()

    def on_ui_lang(self, _event=None):
        name = self.ui_box.get()
        code = next((c for c, n in UI_NAMES.items() if n == name), self.lang)
        self.set_lang(code)

    def set_lang(self, code):
        self.lang = code
        i18n.save_choice(code)
        self.ui_box.set(UI_NAMES.get(code, code))
        self.apply_language()
        self.prepare_ui_texts()

    def prepare_ui_texts(self):
        """Window languages other than Portuguese/English are machine-translated from the English texts with the program's own
        models (downloaded first when needed) and cached. Meanwhile the window stays in English; it redraws when the texts are ready."""
        src = i18n.text_source(self.lang)
        if src in i18n.HANDWRITTEN or not uitext.pending(src):
            self.lbl_ui_note.configure(text="")
            return
        if self.ui_job == src:
            return
        self.ui_job = src
        lang = self.lang
        self.lbl_ui_note.configure(text=i18n.tr("en", "ui_preparing"))

        def work():
            models.install("en", src, progress=lambda m: None)
            return uitext.translate_missing(src)

        def done(n, err):
            self.ui_job = None
            if i18n.text_source(self.lang) != src:
                self.prepare_ui_texts()                    # the user already picked another language
                return
            if err is not None:
                log.warning("window texts for %s not prepared: %s", src, err)
                self.lbl_ui_note.configure(text=i18n.tr("en", "ui_prepare_failed"))
                return
            self.lbl_ui_note.configure(text="")
            self.apply_language()

        self.run_bg(work, done)

    # ------------------------------------------------------------------ thread -> UI plumbing
    def post(self, fn):
        self.q.put(fn)

    def pump(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        self._pump_id = self.root.after(100, self.pump)

    def run_bg(self, work, done):
        def target():
            try:
                res = work()
                self.post(lambda: done(res, None))
            except Exception as e:  # noqa: BLE001
                log.exception("background action failed")
                err = e                      # `e` is deleted when the except block ends; the queued callback needs its own reference
                self.post(lambda err=err: done(None, err))
        threading.Thread(target=target, daemon=True).start()

    # ------------------------------------------------------------------ Home: status and target language
    def refresh_status(self):
        port = self.httpd.server_address[1]
        pairs = models.installed_pairs()
        self.status.set_key("running", port=port)
        self.status2.set_key("models", models=", ".join(pairs) or self.t("none"))
        self.refresh_target_info()

    def set_lang_choices(self, codes):
        """Full names in the window language; the saved target (or a suggestion) stays selected."""
        keep = languages.norm_target(self.selected_target() or config.get("target") or languages.suggest())   # old settings say "pt"
        shown = {c for c in codes if c in i18n.NAMES}             # only languages that have a full name: never a bare code
        if keep in i18n.NAMES:
            shown.add(keep)
        choices = i18n.lang_choices(shown, self.lang)
        self.lang_codes = {label: code for label, code in choices}
        self.lang_box.configure(values=[label for label, _ in choices])
        label = next((l for l, c in choices if c == keep), "")
        self.lang_box.set(label)

    def selected_target(self):
        return self.lang_codes.get(self.lang_box.get()) if self.lang_codes else None

    def refresh_target_info(self):
        tgt = self.selected_target()
        if not tgt:
            self.target_msg.set_key("target_none")
            self.btn_model.grid_remove()
            return
        if config.get("target") != tgt:
            config.set("target", tgt)                       # the game mod reads this file
        label = i18n.lang_label(tgt, self.lang)
        ready = models.is_installed("en", tgt) or tgt == "en"
        if ready:
            self.target_msg.set_key("target_saved", lang=label)
            self.btn_model.grid_remove()
        else:
            self.target_msg.set_key("model_missing", lang=label)
            self.btn_model.grid()

    def on_target_selected(self, _event=None):
        tgt = self.selected_target()
        if not tgt:
            return
        config.set("target", tgt)
        log.info("target language set to %s in the helper window", tgt)
        self.refresh_target_info()
        self.refresh_plan()
        if not (models.is_installed("en", tgt) or tgt == "en"):
            self.install_model()

    def install_model(self):
        lang = self.selected_target()
        if not lang or lang == "en":
            return
        self.btn_model.configure(state="disabled")
        self.progress.set_key("downloading", lang=i18n.lang_label(lang, self.lang))
        self.run_bg(lambda: models.install("en", lang, progress=lambda m: None), self._model_done)

    def _model_done(self, _res, err):
        self.btn_model.configure(state="normal")
        if err:
            self.progress.set_key("model_failed", err=err)
        else:
            self.progress.set_key("model_ok")
        self.refresh_status()

    # ------------------------------------------------------------------ Home: updates
    def start_check(self):
        if self.busy:
            return
        self.update_msg.set_key("checking")
        self.btn_check.configure(state="disabled")
        self.run_bg(lambda: updater.check(self.fetcher), self._check_done)

    def _check_done(self, chk, err):
        self.btn_check.configure(state="normal")
        if err or chk is None:
            self.update_msg.set_key("check_failed", err=err)
            return
        if chk.error:
            self.update_msg.set(chk.error)
        elif chk.available:
            self.latest = chk.release
            self.update_msg.set(self.t("new_version", latest=chk.latest, current=chk.current) + "\n" + self._short(chk.notes))
            self.btn_apply.configure(state="normal")
        else:
            self.update_msg.set_key("up_to_date", current=chk.current)

    @staticmethod
    def _short(notes, n=300):
        notes = (notes or "").strip().split("### Como instalar")[0].strip()
        return notes if len(notes) <= n else notes[:n] + "..."

    def start_update(self):
        if self.busy or self.latest is None:
            return
        self.busy = True
        self.btn_apply.configure(state="disabled")
        self.btn_check.configure(state="disabled")
        rel = self.latest
        t = self.t

        def work():
            msgs = []
            prog = lambda m: self.post(lambda: self.progress.set(m))
            exe = updater.update_helper(rel, self.fetcher, prog, exe_path=self.exe_path) if (updater.is_frozen() or self.exe_path) else None
            msgs.append(t("py_update") if exe is None else t("helper_updated"))
            mod = self.mod_dir_override or updater.find_mod_dir()
            mod_ok = True
            try:
                if mod:
                    n = updater.update_mod(rel, mod, self.fetcher, prog)
                    msgs.append(t("mod_updated", n=n, path=mod))
                else:
                    p = updater.save_mod_zip(rel, self.fetcher, prog)
                    msgs.append(t("mod_zip_saved", path=p))
            except (updater.UpdateError, OSError) as e:      # the program itself is already updated: say what is left, still restart into it
                mod_ok = False
                log.exception("mod update failed")
                msgs.append(t("mod_not_updated", err=e))
            return exe, msgs, mod_ok

        self.run_bg(work, self._update_done)

    def _update_done(self, res, err):
        self.busy = False
        self.btn_check.configure(state="normal")
        if err:
            self.update_msg.set_key("update_failed", err=err)
            self.progress.set("")
            self.btn_apply.configure(state="normal")
            return
        exe, msgs, mod_ok = res
        self.update_msg.set("\n".join(msgs))
        if exe:
            # the new program opens and this one closes; when something went wrong with the mod files, leave time to read it first
            self.progress.set_key("restarting")
            self.root.after(self.RESTART_MS if mod_ok else self.RESTART_MS_MOD_PROBLEM, lambda: self.quit(restart_exe=exe))

    def report(self):
        try:
            z = diagnostics.make_bundle()
            open_folder(z.parent)
            webbrowser.open(ISSUES_URL)
            self.progress.set_key("report_saved", name=z.name)
        except Exception as e:  # noqa: BLE001
            log.exception("report failed")
            self.progress.set_key("report_failed", err=e)

    # ------------------------------------------------------------------ Translate all mods
    def dirs(self):
        return self.mod_dirs_override if self.mod_dirs_override is not None else bulk.mods_dirs()

    def load_dir_rows(self):
        if self.mod_dirs_override is not None:
            self.dir_rows = [(Path(d), "added", Path(d).is_dir()) for d in self.mod_dirs_override]
        else:
            self.dir_rows = bulk.dir_entries()

    def render_dirs(self):
        """List of every folder searched, numbered, in the window language (called again when the language changes).
        The "[default]" tag sits at the right edge of its row; the tag of a folder the user added (or that is missing) follows the path."""
        ttk, t = self.ttk, self.t
        self.dirs_frame.configure(text=t("bulk_dirs_title"))
        for child in self.dirs_frame.winfo_children():
            child.destroy()
        self.dir_labels = []
        self.dirs_frame.columnconfigure(0, weight=1)
        if not self.dir_rows:
            ttk.Label(self.dirs_frame, text=t("bulk_nodirs"), anchor="w").grid(row=0, column=0, sticky="ew")
            return
        for i, (d, kind, exists) in enumerate(self.dir_rows):
            tag = "[" + t("dir_missing" if not exists else "dir_default" if kind == "default" else "dir_added") + "]"
            right = exists and kind == "default"
            path_lbl = ttk.Label(self.dirs_frame, anchor="w", justify="left", text=f"{i + 1}. {d}" + ("" if right else f"   {tag}"))
            path_lbl.grid(row=i, column=0, sticky="ew")
            tag_lbl = None
            if right:
                tag_lbl = ttk.Label(self.dirs_frame, anchor="e", text=tag)
                tag_lbl.grid(row=i, column=1, sticky="e", padx=(8, 0))
            self.dir_labels.append((path_lbl, tag_lbl))

    def dirs_text(self):
        """The folder list as plain text (what is on screen), one line per folder; used by the tests."""
        return "\n".join(p.cget("text") + (("   " + t.cget("text")) if t is not None else "") for p, t in self.dir_labels)

    def add_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(parent=self.root)
        if d:
            cur = list(config.get("mods_dirs") or [])
            if d not in cur:
                config.set("mods_dirs", cur + [d])
            self.refresh_plan()

    def ask_yes_no(self, title, text):
        from tkinter import messagebox
        return messagebox.askyesno(title, text, parent=self.root, icon="warning", default="no")

    def clear_translations(self):
        """Delete every saved translation of the chosen language (after asking), then list the mods as new again."""
        tgt = self.selected_target()
        if not tgt or self.bulk_running:
            return
        label = i18n.lang_label(tgt, self.lang)
        if not self.ask_yes_no(self.t("bulk_clear_title"), self.t("bulk_clear_confirm", lang=label)):
            return
        try:
            n = bulk.clear_translations(tgt)
        except Exception as e:  # noqa: BLE001
            log.exception("clearing translations failed")
            self.bulk_summary.set_key("bulk_error", err=e)
            return
        self.pbar["value"] = 0
        self.refresh_plan()
        self.bulk_progress.set_key("bulk_cleared", n=n, lang=label)

    def update_bulk_buttons(self):
        pend = sum(1 for _m, s, _r in self.plan_rows if s != "ok")
        self.btn_bulk.configure(text=self.t("bulk_start_pending", n=pend))
        idle = not self.bulk_running
        self.btn_bulk.configure(state="normal" if idle and pend > 0 and self.selected_target() else "disabled")
        self.btn_bulk_all.configure(state="normal" if idle and self.plan_rows and self.selected_target() else "disabled")
        self.btn_scan.configure(state="normal" if idle else "disabled")
        self.btn_add_dir.configure(state="normal" if idle else "disabled")
        self.btn_stop.configure(state="disabled" if idle else "normal")
        self.btn_clear.configure(state="normal" if idle and self.selected_target() else "disabled")

    def refresh_plan(self):
        """Scan the mod folders and compare with what was translated before (new / changed / ok)."""
        if self.bulk_running:
            return
        tgt = self.selected_target()
        self.bulk_intro.set_key("bulk_intro")
        self.load_dir_rows()
        self.render_dirs()
        dirs = [d for d, _k, ok in self.dir_rows if ok]
        if not tgt:
            self.plan_rows = []
            self.render_rows()                       # (this rewrites the summary line, so the hint must come after it)
            self.bulk_summary.set_key("bulk_need_target")
            self.update_bulk_buttons()
            return
        self.bulk_current.set_key("bulk_scanning")
        self.run_bg(lambda: bulk.plan(tgt, dirs), self._plan_done)

    def _plan_done(self, rows, err):
        self.bulk_current.set("")
        if err:
            self.bulk_summary.set_key("bulk_error", err=err)
            return
        self.plan_rows = rows or []
        self.render_rows()
        self.update_bulk_buttons()
        if self.plan_rows and all(s == "ok" for _m, s, _r in self.plan_rows):
            self.bulk_progress.set_key("bulk_all_ok")
            self.pbar["value"] = 100

    def _with_folder(self, vals):
        """The five data cells plus the "open folder" cell of the last column."""
        return tuple(vals) + (self.t("folder_open"),)

    def _row_values(self, mod, status, saved, running=False):
        t = self.t
        if running:
            state = t("st_running")
        elif saved is None:
            state = t("st_new")
        elif status == "changed":
            state = t("st_changed")
        else:
            state = t("st_ok")
        texts = words = 0
        src = ""
        if saved:
            texts, words = saved.get("texts", 0), saved.get("words", 0)
            src = ", ".join(sorted(saved.get("langs", {})))
            if saved.get("unsupported"):
                state = t("st_nosupport", pairs=", ".join(saved["unsupported"]))
            elif saved.get("failed"):
                state += " - " + t("st_failed", n=saved["failed"])
        return (mod.name, src, texts, words, state)

    def render_rows(self):
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        self.row_mods = {}
        texts = words = 0
        for mod, status, saved in sorted(self.plan_rows, key=lambda r: r[0].name.lower()):
            vals = self._row_values(mod, status, saved)
            iid = self.tree.insert("", "end", values=vals + (self.t("folder_open"),))
            self.rows[mod.package_id] = iid
            self.row_mods[iid] = mod
            texts += vals[2]
            words += vals[3]
        pend = sum(1 for _m, s, _r in self.plan_rows if s != "ok")
        self.bulk_summary.set_key("bulk_summary", mods=len(self.plan_rows), pending=pend, texts=texts, words=words)

    def start_bulk(self, force):
        tgt = self.selected_target()
        if not tgt:
            self.bulk_summary.set_key("bulk_need_target")
            return
        if self.bulk_running:
            return
        self.bulk_running = True
        self.cancel = threading.Event()
        self.update_bulk_buttons()
        self.pbar["value"] = 0
        cancel, dirs = self.cancel, self.dirs()

        def work():
            return bulk.run(tgt, dirs, force=force, cancel=cancel,
                            progress=lambda e: self.post(lambda e=e: self.on_bulk_event(e)))

        self.run_bg(work, self._bulk_done)

    def stop_bulk(self):
        if self.cancel is not None:
            self.cancel.set()

    @staticmethod
    def format_eta(seconds):
        """'45 s', '3 min 20 s', '1 h 05 min' (the same in every language)."""
        sec = max(0, int(round(seconds)))
        if sec < 60:
            return f"{max(5, sec // 5 * 5) if sec else 0} s"
        if sec < 3600:
            return f"{sec // 60} min {sec % 60 // 5 * 5:02d} s"
        return f"{sec // 3600} h {sec % 3600 // 60:02d} min"

    def eta_text(self, frac):
        """Estimated time left from the time spent so far; '' while there is too little progress to tell."""
        t0 = getattr(self, "_bulk_t0", None)
        if t0 is None or frac < 0.02 or frac >= 1:
            return ""
        spent = time.time() - t0
        if spent < 8:
            return ""
        return self.format_eta(spent * (1 - frac) / frac)

    def show_progress(self, done_mods, total, cur_done=0, cur_total=0):
        """Progress bar and "X of N mods (P%)" line, with the estimated time left once there is enough to go on.
        The mod being translated counts for the part of its texts already done."""
        total = max(1, total)
        frac = min(1.0, (done_mods + (cur_done / cur_total if cur_total else 0)) / total)
        self.pbar["value"] = int(frac * 100)
        eta = self.eta_text(frac)
        if eta:
            self.bulk_progress.set_key("bulk_progress_eta", done=done_mods, total=total, pct=int(frac * 100), eta=eta)
        else:
            self.bulk_progress.set_key("bulk_progress", done=done_mods, total=total, pct=int(frac * 100))

    def on_bulk_event(self, e):
        ev = e.get("event")
        if ev == "start":
            self._total = e["total"]
            self._words = 0
            self._done_mods = 0
            self._bulk_t0 = time.time()
            self.bulk_progress.set_key("bulk_progress", done=0, total=e["total"], pct=0)
        elif ev == "model":
            self.bulk_current.set_key("bulk_model", pair=e["pair"])
        elif ev == "mod_start":
            self.bulk_current.set_key("bulk_current", name=e["name"], done=0, total=0)
            for pid, (m, s, r) in ((m.package_id, row) for row in self.plan_rows for m in [row[0]]):
                if m.name == e["name"] and pid in self.rows:
                    self.tree.item(self.rows[pid], values=self._with_folder(self._row_values(m, s, r, running=True)))
                    self.tree.see(self.rows[pid])
        elif ev == "mod_progress":
            self.bulk_current.set_key("bulk_current", name=e["name"], done=e["done"], total=e["total"])
            self.show_progress(getattr(self, "_done_mods", 0), getattr(self, "_total", 1), e["done"], e["total"])
        elif ev == "mod_done":
            r = e["result"]
            self._words += r.words
            self._done_mods = e["index"]
            self.show_progress(e["index"], e["total"])
            for m, s, _old in self.plan_rows:
                if m.package_id == r.package_id and m.package_id in self.rows:
                    saved = None if r.error else r.to_state(m.fingerprint)
                    vals = self._row_values(m, "ok", saved)
                    if r.error:
                        vals = (m.name, "", 0, 0, self.t("st_error"))
                    self.tree.item(self.rows[m.package_id], values=self._with_folder(vals))

    def _bulk_done(self, results, err):
        self.bulk_running = False
        self.bulk_current.set("")
        if err:
            self.bulk_summary.set_key("bulk_error", err=err)
            self.update_bulk_buttons()
            return
        cancelled = self.cancel is not None and self.cancel.is_set()
        words = sum(r.words for r in results or [])
        if cancelled:
            self.bulk_progress.set_key("bulk_cancelled")
        else:
            self.pbar["value"] = 100
            self.bulk_progress.set_key("bulk_done", mods=len(results or []), words=words)
        self.plan_rows = []
        self.update_bulk_buttons()
        self.refresh_plan()

    # ------------------------------------------------------------------ details of one mod (double-click)
    FOLDER_COL = "#6"                                     # the "folder" column (columns are numbered from 1)

    def on_tree_click(self, event):
        """A click on the folder column of a mod opens that mod's folder in the file explorer."""
        if self.tree.identify_region(event.x, event.y) != "cell" or self.tree.identify_column(event.x) != self.FOLDER_COL:
            return
        mod = self.row_mods.get(self.tree.identify_row(event.y))
        if mod is not None:
            open_folder(str(mod.path))
            return "break"                                # do not also select the row

    def on_tree_motion(self, event):
        over = self.tree.identify_region(event.x, event.y) == "cell" and self.tree.identify_column(event.x) == self.FOLDER_COL \
            and self.tree.identify_row(event.y) in self.row_mods
        self.tree.configure(cursor="hand2" if over else "")

    def on_tree_double(self, event):
        if self.tree.identify_column(event.x) == self.FOLDER_COL:
            return                                        # the click already opened the folder; the details window is for the other columns
        iid = self.tree.identify_row(event.y)
        for pid, row in self.rows.items():
            if row == iid:
                self.show_details(pid)
                return

    def show_details(self, package_id):
        """Window with what was translated for one mod, and why the other texts were left alone.
        It follows the window language: changing the language in the main window rebuilds every open details window."""
        tk, ttk = self.tk, self.ttk
        if self._details_entry(package_id) is None or not self.selected_target():
            return None
        top = tk.Toplevel(self.root)
        top.geometry("860x600")
        top.minsize(640, 420)
        top.columnconfigure(0, weight=1)
        top.rowconfigure(1, weight=1)
        top.package_id = package_id
        top.rebuild = lambda: self._fill_details(top)
        self.details_windows = getattr(self, "details_windows", [])
        self.details_windows.append(top)
        self._fill_details(top)
        return top

    def _details_entry(self, package_id):
        return next(((m, s, r) for m, s, r in self.plan_rows if m.package_id == package_id), None)

    def refresh_details_windows(self):
        """Redraw the open details windows in the current window language (selection and tab are kept)."""
        alive = []
        for top in getattr(self, "details_windows", []):
            try:
                if not top.winfo_exists():
                    continue
                top.rebuild()
                alive.append(top)
            except Exception:  # noqa: BLE001 - a window that cannot be redrawn must not break the language change
                log.exception("could not redraw a details window")
        self.details_windows = alive

    def _fill_details(self, top):
        tk, ttk, t = self.tk, self.ttk, self.t
        keep_tab, keep_sel = 0, None
        old = getattr(top, "details", None)
        if old:
            try:
                keep_tab = old["nb"].index(old["nb"].select())
                keep_sel = (keep_tab, old["tabs"][keep_tab].index(old["tabs"][keep_tab].selection()[0]))
            except Exception:  # noqa: BLE001 - nothing selected
                pass
        for child in top.winfo_children():
            child.destroy()
        entry = self._details_entry(top.package_id)
        tgt = self.selected_target()
        if entry is None or not tgt:
            top.destroy()
            return
        mod, _status, saved = entry
        saved = saved or {}
        cache = bulk.read_cache(tgt, top.package_id)
        skipped = saved.get("skipped", [])
        top.title(t("det_title", name=mod.name))
        head = ttk.Label(top, anchor="w", justify="left", wraplength=800, padding=8,
                         text=t("det_summary", texts=saved.get("texts", 0), translated=saved.get("translated", 0), cached=saved.get("from_cache", 0),
                                words=saved.get("words", 0), covered=saved.get("covered", 0), already=saved.get("already_target", 0),
                                unsupported=len(saved.get("unsupported", [])), failed=saved.get("failed", 0))
                         + (("\n" + t("det_placeholders", n=saved["placeholders"])) if saved.get("placeholders") else ""))
        head.grid(row=0, column=0, sticky="ew")
        nb = ttk.Notebook(top)
        nb.grid(row=1, column=0, sticky="nsew", padx=8)
        full = {}

        def make_tab(title, cols, rows):
            f = ttk.Frame(nb)
            f.columnconfigure(0, weight=1)
            f.rowconfigure(0, weight=1)
            tv = ttk.Treeview(f, columns=[c for c, _ in cols], show="headings")
            for c, h in cols:
                tv.heading(c, text=h)
                tv.column(c, width=300, anchor="w", stretch=True)
            sbar = ttk.Scrollbar(f, orient="vertical", command=tv.yview)
            tv.configure(yscrollcommand=sbar.set)
            tv.grid(row=0, column=0, sticky="nsew")
            sbar.grid(row=0, column=1, sticky="ns")
            for vals, texts in rows:
                full[tv.insert("", "end", values=[self._one_line(v) for v in vals])] = texts
            nb.add(f, text=title)
            return tv

        done = sorted(cache.items(), key=lambda kv: kv[0].lower())
        tv1 = make_tab(t("det_tab_translated", n=len(done)), [("o", t("det_col_orig")), ("t", t("det_col_trans"))],
                       [((k, v), (k, v)) for k, v in done])
        # words: the same translated texts, each with its number of words (what the "Words" column of the main table adds up), most words first
        counted = sorted(((bulk.count_words(k), k, v) for k, v in done), key=lambda x: (-x[0], x[1].lower()))
        tv3 = make_tab(t("det_tab_words", n=sum(c for c, _k, _v in counted)),
                       [("o", t("det_col_orig")), ("t", t("det_col_trans")), ("w", t("det_col_words"))],
                       [((k, v, str(c)), (k, v)) for c, k, v in counted])
        tv3.column("w", width=90, minwidth=70, stretch=False, anchor="center")
        tv3.heading("w", anchor="center")
        reasons = {"covered": lambda d: t("r_covered", provider=d), "already_target": lambda d: t("r_already"),
                   "unsupported": lambda d: t("r_unsupported", pair=d), "failed": lambda d: t("r_failed")}
        # not translated by us: the text, how it reads now (the translation that already exists, if any) and why it was left alone
        tv2 = make_tab(t("det_tab_skipped", n=len(skipped)), [("o", t("det_col_orig")), ("e", t("det_col_existing")), ("r", t("det_col_reason"))],
                       [((x["text"], x.get("translation", ""), reasons.get(x["reason"], lambda d: x["reason"])(x.get("detail", ""))),
                         (x["text"], x.get("translation", ""))) for x in skipped])
        # the selected row in full: descriptions are long
        box = ttk.Frame(top)
        box.grid(row=2, column=0, sticky="ew", padx=8, pady=6)
        box.columnconfigure(0, weight=1)
        txt = tk.Text(box, height=7, wrap="word")
        txt.grid(row=0, column=0, sticky="ew")
        txt.configure(state="disabled")

        def show_full(tv, iid):
            o, tr = full.get(iid, ("", ""))
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            txt.insert("end", t("det_full_orig") + "\n" + o + ("\n\n" + t("det_full_trans") + "\n" + tr if tr else ""))
            txt.configure(state="disabled")

        def on_select(event):
            sel = event.widget.selection()
            if sel:
                show_full(event.widget, sel[0])
        tv1.bind("<<TreeviewSelect>>", on_select)
        tv2.bind("<<TreeviewSelect>>", on_select)
        tv3.bind("<<TreeviewSelect>>", on_select)
        if not done and not skipped:
            txt.configure(state="normal")
            txt.insert("end", t("det_empty"))
            txt.configure(state="disabled")
        ttk.Button(top, text=t("det_close"), command=top.destroy).grid(row=3, column=0, pady=(0, 8))
        top.details = {"translated": tv1, "words": tv3, "skipped": tv2, "text": txt, "full": full, "nb": nb, "tabs": [tv1, tv3, tv2]}
        if keep_sel:                                           # same tab and same row as before the redraw
            try:
                nb.select(keep_sel[0])
                tv = top.details["tabs"][keep_sel[0]]
                iid = tv.get_children()[keep_sel[1]]
                tv.selection_set(iid)
                tv.see(iid)
                show_full(tv, iid)
            except Exception:  # noqa: BLE001 - the list got shorter
                pass

    @staticmethod
    def _one_line(s, n=160):
        s = " \u23ce ".join(str(s).split("\n"))
        return s if len(s) <= n else s[:n] + "..."

    # ------------------------------------------------------------------ lifecycle
    def _restart(self, exe):
        updater.restart(exe, [])

    def quit(self, restart_exe=None):
        if self.cancel is not None:
            self.cancel.set()
        activity.unsubscribe(getattr(self, "_log_cb", None))
        try:
            self.root.after_cancel(self._pump_id)
        except Exception:
            pass
        try:
            self.httpd.shutdown()
            self.httpd.server_close()
        except Exception:
            log.exception("error while stopping the server")
        if restart_exe:
            self.restart_fn(restart_exe)
        self.root.destroy()


def main():
    """Open the window with the server running. Raises ImportError/TclError if no window is possible."""
    import tkinter as tk
    root = tk.Tk()
    config.migrate_portuguese()
    activity.emit("system", "log_started", {"version": __version__})
    httpd = server.serve(server.DEFAULT_PORT)
    threading.Thread(target=httpd.serve_forever, daemon=True, name="http-server").start()
    App(root, httpd)
    root.mainloop()
