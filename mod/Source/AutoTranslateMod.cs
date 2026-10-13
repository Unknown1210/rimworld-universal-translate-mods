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

        public override void DoSettingsWindowContents(Rect inRect)
        {
            try
            {
                if (Hotkey.Capturing && Event.current != null && Event.current.type == EventType.KeyDown)
                {
                    Hotkey.Capture(Event.current);
                    Event.current.Use();
                }
                var l = new Listing_Standard();
                l.Begin(inRect);
                // 1) the live switch: compare with the original texts without leaving the game
                bool off = Pipeline.Suspended;
                l.Label(off ? "<color=#ffb347>" + T.Get("AT_Off") + "</color>" : "<color=#88dd88>" + T.Get("AT_On") + "</color>");
                if (l.ButtonText(off ? T.Get("AT_BtnOn") : T.Get("AT_BtnOff"))) Safe.Run("switch", () => Pipeline.SetSuspended(!off));
                // the shortcut: one key plus optional Shift / Ctrl / Alt, switches the translations in real time while playing
                l.Label(Hotkey.Capturing ? "<color=#ffd966>" + T.Get("AT_HotkeyPress") + "</color>" : T.Get("AT_Hotkey", Hotkey.Label(Settings)));
                if (l.ButtonText(Hotkey.Capturing ? T.Get("AT_BtnHotkeyCancel") : T.Get("AT_BtnHotkeySet"))) Hotkey.Capturing = !Hotkey.Capturing;
                if (!string.IsNullOrEmpty(Settings.hotkeyKey) && l.ButtonText(T.Get("AT_BtnHotkeyClear"))) Safe.Run("hotkey", Hotkey.Clear);
                l.Gap(4f);
                // 2) the target language is chosen once, in the translator program
                l.Label(TargetLine());
                // 3) what is going on
                l.Label(Pipeline.StatusUi);
                if (!string.IsNullOrEmpty(HelperClient.LastError) && Pipeline.StatusKey != "ready" && Pipeline.StatusKey != "done")
                    l.Label(T.Get("AT_HelperProblem", HelperClient.LastError));
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
                float top = l.CurHeight + 6f;
                l.End();
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
