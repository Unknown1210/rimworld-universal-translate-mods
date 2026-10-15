using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Threading;
using HarmonyLib;
using UnityEngine;
using Verse;

namespace AutoTranslate
{
    public sealed class AutoTranslateMod : Mod
    {
        public const string PackageId = "unknown1210.autotranslate";
        public static AtSettings Settings;
        static string helperCheckResult = "";
        static float topHeight = 320f;        // height of the block above the mod list, measured while drawing (used on the next frame)
        static Vector2 topScroll;
        static bool showAdvanced;

        public AutoTranslateMod(ModContentPack content) : base(content)
        {
            AtLog.Init();
            CrashReporter.Install();
            Safe.Run("settings", () =>
            {
                Settings = GetSettings<AtSettings>();
                AtLog.DebugEnabled = Settings.debugLog;
            });
            if (Settings == null) Settings = new AtSettings(); // settings file unreadable: run with defaults, error is in the log
            Safe.Run("harmony", () =>
            {
                var harmony = new Harmony(PackageId);
                harmony.PatchAll(Assembly.GetExecutingAssembly());
                int n = 0;
                foreach (MethodBase m in harmony.GetPatchedMethods())
                {
                    n++;
                    AtLog.Info("harmony", "patched " + m.DeclaringType + "." + m.Name);
                }
                if (n == 0) AtLog.Error("harmony", "no method was patched: results from the helper will not be applied");
            });
        }

        public override string SettingsCategory() { return "Auto Translate"; }

        static string TargetLine()
        {
            string how;
            string t = Pipeline.Target ?? LangMap.ResolveTarget("auto", out how);
            if (t == null) return T.Get("AT_TargetNone");
            return T.Get(LangMap.ConfigTarget() != null ? "AT_TargetFromHelper" : "AT_TargetFromGame", LangNames.Label(t));
        }

        /// <summary>Button after the "Translating into ..." line: pick the language from those the translator program has already translated into.</summary>
        static void LanguageButton(Listing_Standard l)
        {
            List<string> cached = LangMap.CachedLanguages();
            if (cached.Count == 0) return;
            string how;
            string current = Pipeline.Target ?? LangMap.ResolveTarget("auto", out how);
            bool manual = !string.Equals(Settings.language, "auto", StringComparison.OrdinalIgnoreCase);
            string caption = T.Get("AT_BtnLang", current == null ? "-" : LangNames.Label(current)) + (manual ? "" : " (" + T.Get("AT_LangAutoShort") + ")");
            if (!l.ButtonText(caption)) return;
            var opts = new List<FloatMenuOption>();
            opts.Add(new FloatMenuOption(T.Get("AT_LangAuto"), () => Settings.language = "auto"));
            foreach (string code in cached)
            {
                string c = code;
                opts.Add(new FloatMenuOption(LangNames.Label(c), () => Settings.language = c));
            }
            Find.WindowStack.Add(new FloatMenu(opts));
        }

        public override void DoSettingsWindowContents(Rect inRect)
        {
            try
            {
                if (Hotkey.Capturing && Event.current != null && Event.current.type == EventType.KeyDown)
                {
                    Hotkey.Capture(Event.current);
                    Event.current.Use();
                }
                // The block above the mod list can be taller than the window (advanced options open, long error messages). It gets its own
                // scroll view, capped at 55% of the window, and the list takes what is left. One column only: a Listing that runs out of
                // height starts a second column, its height reads as tiny and the list used to be drawn on top of the first column.
                float cap = inRect.height * 0.55f;
                bool scrolls = topHeight > cap;
                float shown = Math.Min(topHeight, cap);
                var outRect = new Rect(inRect.x, inRect.y, inRect.width, shown);
                var viewRect = new Rect(0f, 0f, inRect.width - (scrolls ? 18f : 0f), topHeight);
                Widgets.BeginScrollView(outRect, ref topScroll, viewRect);
                var l = new Listing_Standard { maxOneColumn = true };
                l.Begin(new Rect(0f, 0f, viewRect.width, Math.Max(topHeight, 3000f)));
                // 1) the live switch: compare with the original texts without leaving the game
                bool off = Pipeline.Suspended;
                l.Label(off ? "<color=#ffb347>" + T.Get("AT_Off") + "</color>" : "<color=#88dd88>" + T.Get("AT_On") + "</color>");
                if (l.ButtonText(off ? T.Get("AT_BtnOn") : T.Get("AT_BtnOff"))) Safe.Run("switch", () => Pipeline.SetSuspended(!off));
                // the shortcut: one key plus optional Shift / Ctrl / Alt, switches the translations in real time while playing.
                // One row: the text on the left, "set" and "remove" side by side on the right (saves lines for the mod list).
                Rect hk = l.GetRect(30f);
                float bw = Math.Min(170f, hk.width * 0.26f);
                Widgets.Label(new Rect(hk.x, hk.y + 4f, hk.width - bw * 2f - 12f, hk.height - 4f),
                    Hotkey.Capturing ? "<color=#ffd966>" + T.Get("AT_HotkeyPress") + "</color>" : T.Get("AT_Hotkey", Hotkey.Label(Settings)));
                bool hasKey = !string.IsNullOrEmpty(Settings.hotkeyKey);
                if (Widgets.ButtonText(new Rect(hk.x + hk.width - bw * 2f - 6f, hk.y, bw, 28f), Hotkey.Capturing ? T.Get("AT_BtnHotkeyCancel") : T.Get("AT_BtnHotkeySet"))) Hotkey.Capturing = !Hotkey.Capturing;
                if (hasKey && Widgets.ButtonText(new Rect(hk.x + hk.width - bw, hk.y, bw, 28f), T.Get("AT_BtnHotkeyClear"))) Safe.Run("hotkey", Hotkey.Clear);
                l.Gap(2f);
                // 2) target language (chosen once, in the translator program) and 3) what is going on: one paragraph
                string status = TargetLine() + "  " + Pipeline.StatusUi;
                if (!string.IsNullOrEmpty(HelperClient.LastError) && Pipeline.StatusKey != "ready" && Pipeline.StatusKey != "done")
                {
                    string err = HelperClient.LastError.Replace("\r", " ").Replace("\n", " ").Trim();
                    if (err.Length > 90) err = err.Substring(0, 90).TrimEnd() + "...";      // the full text is in the log / "Check the translator" in the advanced options
                    status += "\n" + T.Get("AT_HelperProblem", err);
                }
                l.Label(status);
                LanguageButton(l);
                int problems = 0;
                foreach (ModState pm in Pipeline.Mods) if (pm.AutoDisabled) problems++;
                if (problems > 0) l.Label("<color=#ff6666>" + T.Get("AT_Banner", problems) + "</color>");
                if (Pipeline.SettingsChangedSinceStart()) l.Label("<color=#ffd966>" + T.Get("AT_ApplyOnClose") + "</color>");
                // 4) advanced options, hidden by default
                if (l.ButtonText(showAdvanced ? T.Get("AT_AdvancedHide") : T.Get("AT_Advanced"))) showAdvanced = !showAdvanced;
                if (showAdvanced)
                {
                    l.CheckboxLabeled(T.Get("AT_OptDefs"), ref Settings.translateDefs);
                    l.CheckboxLabeled(T.Get("AT_OptKeyed"), ref Settings.translateKeyed);
                    l.CheckboxLabeled(T.Get("AT_OptMeta"), ref Settings.translateMeta);
                    l.CheckboxLabeled(T.Get("AT_OptPseudo"), ref Settings.hidePseudo);
                    l.CheckboxLabeled(T.Get("AT_OptVerbose"), ref Settings.debugLog);
                    AtLog.DebugEnabled = Settings.debugLog;
                    if (helperCheckResult.Length > 0) l.Label(helperCheckResult);
                    if (l.ButtonText(T.Get("AT_BtnCheck")))
                    {
                        helperCheckResult = T.Get("AT_Checking");
                        ThreadPool.QueueUserWorkItem(_ =>
                        {
                            try { var h = HelperClient.Health(); helperCheckResult = T.Get("AT_HelperOk", h.Version, string.Join(", ", h.Installed.ToArray())); }
                            catch (Exception e) { helperCheckResult = T.Get("AT_HelperFail", e.Message); AtLog.Warn("settings", "helper check failed", e); }
                        });
                    }
                    if (l.ButtonText(T.Get("AT_BtnReport")))
                        Safe.Run("report", () =>
                        {
                            string rp = ReportBuilder.Build();
                            helperCheckResult = T.Get("AT_ReportSaved", Path.GetFileName(rp));
                            Application.OpenURL(Path.GetDirectoryName(rp));
                            Application.OpenURL(ReportBuilder.IssueUrl());
                        });
                    if (l.ButtonText(T.Get("AT_BtnLogs"))) Application.OpenURL(Paths.LogDir);
                    if (l.ButtonText(T.Get("AT_BtnCopy"))) GUIUtility.systemCopyBuffer = Diagnostics.Snapshot();
                    if (l.ButtonText(T.Get("AT_BtnClear")))
                        Find.WindowStack.Add(Dialog_MessageBox.CreateConfirmation(T.Get("AT_ClearConfirm", Pipeline.Target == null ? "?" : LangNames.Label(Pipeline.Target)),
                            () => Safe.Run("settings", Pipeline.ClearCacheForTarget), true));
                }
                topHeight = Math.Max(60f, l.CurHeight + 6f);
                l.End();
                Widgets.EndScrollView();
                float top = shown + 6f;
                ModListUI.Draw(new Rect(inRect.x, inRect.y + top, inRect.width, Math.Max(90f, inRect.height - top)));
            }
            catch (Exception ex) { Safe.Report("settings", ex, "drawing settings window"); }
        }

        public override void WriteSettings()
        {
            Hotkey.Capturing = false;
            base.WriteSettings();
            Safe.Run("settings", () => AtLog.Info("settings", "saved: " + Settings.Describe()));
            if (Pipeline.SettingsChangedSinceStart()) Safe.Run("reload", Pipeline.Reload);   // new language / options / per-mod choices take effect now, no restart
        }
    }

    [StaticConstructorOnStartup]
    public static class Bootstrap
    {
        static Bootstrap()
        {
            // Runs after all defs and languages are loaded.
            if (!Safe.Run("bootstrap", Pipeline.Start))
                AtLog.Fatal("bootstrap", "pipeline failed to start; automatic translation is inactive. Log: " + AtLog.LogFile);
        }
    }

    [HarmonyPatch(typeof(Root), nameof(Root.Update))]
    public static class Patch_Root_Update
    {
        public static void Postfix() { Pipeline.Tick(); Safe.Run("hotkey", Hotkey.Check); }
    }
}
