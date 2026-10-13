using System;
using System.IO;
using System.Text;
using UnityEngine;

namespace AutoTranslate
{
    /// <summary>
    /// Writes crash-*.txt next to the logs for: unhandled .NET exceptions and Unity exception logs whose stack
    /// mentions this mod, and for any area tripped by Safe. Each report holds the exception chain, an environment
    /// snapshot (game, OS, mods, settings, helper, pipeline), per-area failure counters and the last log lines.
    /// </summary>
    public static class CrashReporter
    {
        static bool installed;
        static int reports;

        public static void Install()
        {
            if (installed) return;
            installed = true;
            try
            {
                AppDomain.CurrentDomain.UnhandledException += OnUnhandled;
                Application.logMessageReceivedThreaded += OnUnityLog;
                AtLog.Info("crash", "crash reporter installed");
            }
            catch (Exception ex) { AtLog.Error("crash", "could not install crash reporter", ex); }
        }

        static void OnUnhandled(object sender, UnhandledExceptionEventArgs e)
        {
            var ex = e.ExceptionObject as Exception;
            string text = ex != null ? ex.ToString() : Convert.ToString(e.ExceptionObject);
            if (text.IndexOf("AutoTranslate", StringComparison.Ordinal) < 0) return; // not ours
            AtLog.Fatal("crash", "UNHANDLED EXCEPTION (terminating=" + e.IsTerminating + ")", ex);
            WriteReport("unhandled" + (e.IsTerminating ? "-terminating" : ""), ex);
        }

        static void OnUnityLog(string condition, string stackTrace, LogType type)
        {
            try
            {
                if (type != LogType.Exception) return;
                if (condition != null && condition.StartsWith("[AutoTranslate]", StringComparison.Ordinal)) return; // avoid feedback loops
                string all = (condition ?? "") + (stackTrace ?? "");
                if (all.IndexOf("AutoTranslate", StringComparison.Ordinal) < 0) return;
                AtLog.Error("unity-exception", "Unity logged an exception that passes through this mod: " + condition + "\n" + stackTrace);
            }
            catch { }
        }

        public static string WriteReport(string kind, Exception ex)
        {
            try
            {
                if (++reports > 20) return null; // do not flood the disk
                Directory.CreateDirectory(Paths.LogDir);
                string path = Path.Combine(Paths.LogDir, "crash-" + DateTime.Now.ToString("yyyyMMdd-HHmmss-fff") + ".txt");
                var sb = new StringBuilder();
                sb.AppendLine("AUTOTRANSLATE CRASH REPORT (" + kind + ")");
                sb.AppendLine("time: " + DateTime.Now.ToString("o"));
                sb.AppendLine("session log: " + AtLog.LogFile);
                sb.AppendLine();
                sb.AppendLine("--- exception ---");
                sb.AppendLine(ex != null ? AtLog.Describe(ex) : "(none)");
                sb.AppendLine();
                sb.AppendLine("--- environment ---");
                sb.AppendLine(Diagnostics.Snapshot());
                sb.AppendLine();
                sb.AppendLine("--- last log lines ---");
                foreach (string l in AtLog.RecentLines()) sb.AppendLine(l);
                File.WriteAllText(path, sb.ToString(), new UTF8Encoding(false));
                AtLog.Info("crash", "crash report written: " + path);
                return path;
            }
            catch (Exception e)
            {
                try { Verse.Log.Warning("[AutoTranslate] could not write crash report: " + e.Message); } catch { }
                return null;
            }
        }
    }
}
