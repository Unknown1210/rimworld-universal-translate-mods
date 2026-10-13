using System;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using Verse;

namespace AutoTranslate
{
    /// <summary>Environment snapshot written at session start and inside every crash report.
    /// Each section is isolated: a failure in one prints "(unavailable: ...)" instead of losing the rest.</summary>
    public static class Diagnostics
    {
        public static string Snapshot()
        {
            var sb = new StringBuilder();
            Section(sb, "mod", () => "AutoTranslate " + AtLog.ModVersion + " | errors=" + AtLog.ErrorCount + " warnings=" + AtLog.WarnCount);
            Section(sb, "game", () => "RimWorld " + RimWorld.VersionControl.CurrentVersionString);
            Section(sb, "os", () => Environment.OSVersion + " | 64bit=" + Environment.Is64BitOperatingSystem + " | CLR " + Environment.Version);
            Section(sb, "unity", () => Application.unityVersion + " | platform=" + Application.platform + " | systemLanguage=" + Application.systemLanguage);
            Section(sb, "language", () => "game=" + (LanguageDatabase.activeLanguage != null ? LanguageDatabase.activeLanguage.folderName : "?")
                + " | target=" + (Pipeline.Target ?? "(not resolved)"));
            Section(sb, "settings", () => AutoTranslateMod.Settings == null ? "(not loaded)" : AutoTranslateMod.Settings.Describe());
            Section(sb, "pipeline", () => Pipeline.Describe());
            Section(sb, "helper", () => HelperClient.Describe());
            Section(sb, "safe-areas", () =>
            {
                var s = Safe.Snapshot();
                if (s.Count == 0) return "(no failures)";
                var lines = new List<string>();
                foreach (var kv in s) lines.Add("  " + kv.Key + ": " + kv.Value);
                return "\n" + string.Join("\n", lines.ToArray());
            });
            Section(sb, "active mods", () =>
            {
                var lines = new List<string>();
                foreach (ModContentPack m in LoadedModManager.RunningModsListForReading)
                    lines.Add("  " + m.PackageIdPlayerFacing + " | " + m.Name);
                return "(" + lines.Count + ")\n" + string.Join("\n", lines.ToArray());
            });
            return sb.ToString().TrimEnd();
        }

        static void Section(StringBuilder sb, string name, Func<string> f)
        {
            string v;
            try { v = f(); }
            catch (Exception e) { v = "(unavailable: " + e.GetType().Name + ": " + e.Message + ")"; }
            sb.Append(name).Append(": ").AppendLine(v);
        }

        public static void LogSessionHeader()
        {
            AtLog.Info("session", "=== AutoTranslate session ===\n" + Snapshot());
        }
    }
}
