using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading;

namespace AutoTranslate
{
    public enum LogLevel { Debug, Info, Warn, Error, Fatal }

    /// <summary>
    /// File logger. One file per game session in &lt;data&gt;/logs/mod/. Line format:
    /// 2026-10-11 12:00:00.123 [ERROR] [T12] [area] message   (+ full exception chain)
    /// "area" names the part of the mod that was affected (bootstrap, harvest-defs, harvest-keyed,
    /// apply, worker, helper-client, cache, settings, harmony, crash ...).
    /// The logger never throws: if the file cannot be written it falls back to Verse.Log.
    /// </summary>
    public static class AtLog
    {
        const int KeepFiles = 10;
        const int RingSize = 300;
        static readonly object Gate = new object();
        static readonly Queue<string> Ring = new Queue<string>();
        static readonly Dictionary<string, int> Seen = new Dictionary<string, int>();
        static StreamWriter writer;
        static bool initDone;
        static bool fileFailedReported;

        public static string LogFile { get; private set; }
        public static bool DebugEnabled;
        public static int ErrorCount;
        public static int WarnCount;

        public static void Init()
        {
            lock (Gate)
            {
                if (initDone) return;
                initDone = true;
                try
                {
                    Directory.CreateDirectory(Paths.LogDir);
                    Rotate();
                    LogFile = Path.Combine(Paths.LogDir, "autotranslate-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".log");
                    var fs = new FileStream(LogFile, FileMode.Append, FileAccess.Write, FileShare.ReadWrite);
                    writer = new StreamWriter(fs, new UTF8Encoding(false)) { AutoFlush = true };
                }
                catch (Exception e)
                {
                    FallbackReport("cannot open log file in '" + Paths.LogDir + "': " + e.GetType().Name + ": " + e.Message);
                }
            }
        }

        static void Rotate()
        {
            var files = new List<string>(Directory.GetFiles(Paths.LogDir, "autotranslate-*.log"));
            files.Sort(StringComparer.Ordinal);
            for (int i = 0; i < files.Count - (KeepFiles - 1); i++)
            {
                try { File.Delete(files[i]); } catch { /* best effort */ }
            }
        }

        public static void Debug(string area, string msg) { if (DebugEnabled) Write(LogLevel.Debug, area, msg, null); }
        public static void Info(string area, string msg) { Write(LogLevel.Info, area, msg, null); }
        public static void Warn(string area, string msg, Exception ex = null) { Write(LogLevel.Warn, area, msg, ex); }
        public static void Error(string area, string msg, Exception ex = null) { Write(LogLevel.Error, area, msg, ex); }
        public static void Fatal(string area, string msg, Exception ex = null) { Write(LogLevel.Fatal, area, msg, ex); }

        /// <summary>Logs the same problem fully the first 3 times, then only every 100th occurrence (with a counter).</summary>
        public static void ErrorLimited(string area, string signature, string msg, Exception ex)
        {
            int n;
            lock (Gate)
            {
                Seen.TryGetValue(signature, out n);
                Seen[signature] = ++n;
            }
            if (n <= 3) Write(LogLevel.Error, area, msg + (n == 3 ? "  [further identical errors will be summarised]" : ""), ex);
            else if (n % 100 == 0) Write(LogLevel.Error, area, "(same error occurred " + n + " times) " + msg, null);
            else Interlocked.Increment(ref ErrorCount);
        }

        public static void Write(LogLevel level, string area, string msg, Exception ex)
        {
            try
            {
                if (level == LogLevel.Error || level == LogLevel.Fatal) Interlocked.Increment(ref ErrorCount);
                else if (level == LogLevel.Warn) Interlocked.Increment(ref WarnCount);

                var sb = new StringBuilder(256);
                sb.Append(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff")).Append(" [").Append(level.ToString().ToUpperInvariant())
                  .Append("] [T").Append(Thread.CurrentThread.ManagedThreadId).Append("] [").Append(area).Append("] ").Append(msg);
                if (ex != null) sb.Append('\n').Append(Describe(ex));
                string line = sb.ToString();
                lock (Gate)
                {
                    Ring.Enqueue(line);
                    while (Ring.Count > RingSize) Ring.Dequeue();
                    if (writer != null)
                    {
                        try { writer.WriteLine(line); }
                        catch (Exception we) { writer = null; FallbackReport("log write failed: " + we.Message + " | " + line); }
                    }
                    else if (!initDone || LogFile == null) FallbackReport(line);
                }
            }
            catch { /* logging must never throw */ }
        }

        static void FallbackReport(string text)
        {
            if (fileFailedReported) return;
            fileFailedReported = true;
            try { Verse.Log.Warning("[AutoTranslate] " + text); } catch { }
        }

        public static string[] RecentLines()
        {
            lock (Gate) { return Ring.ToArray(); }
        }

        /// <summary>Full description of an exception chain: type, message, source, target method, Data, stack, inner exceptions.</summary>
        public static string Describe(Exception ex)
        {
            var sb = new StringBuilder();
            int depth = 0;
            while (ex != null && depth < 8)
            {
                string indent = new string(' ', depth * 2);
                sb.Append(indent).Append(depth == 0 ? "EXCEPTION " : "CAUSED BY ").Append(ex.GetType().FullName).Append(": ").AppendLine(ex.Message);
                try
                {
                    if (ex.TargetSite != null)
                        sb.Append(indent).Append("  in method: ").Append(ex.TargetSite.DeclaringType).Append('.').AppendLine(ex.TargetSite.Name);
                }
                catch { }
                if (!string.IsNullOrEmpty(ex.Source)) sb.Append(indent).Append("  assembly/source: ").AppendLine(ex.Source);
                foreach (System.Collections.DictionaryEntry kv in ex.Data)
                    sb.Append(indent).Append("  data[").Append(kv.Key).Append("] = ").AppendLine(Convert.ToString(kv.Value));
                var rtl = ex as ReflectionTypeLoadException;
                if (rtl != null && rtl.LoaderExceptions != null)
                    foreach (Exception le in rtl.LoaderExceptions)
                        if (le != null) sb.Append(indent).Append("  loader exception: ").AppendLine(le.Message);
                var agg = ex as AggregateException;
                if (agg != null)
                    foreach (Exception ie in agg.InnerExceptions)
                        sb.Append(indent).Append("  aggregate member: ").AppendLine(ie.GetType().Name + ": " + ie.Message);
                if (ex.StackTrace != null) sb.AppendLine(indent + "  stack:").AppendLine(Indent(ex.StackTrace, indent + "    "));
                ex = ex.InnerException;
                depth++;
            }
            return sb.ToString().TrimEnd();
        }

        static string Indent(string text, string indent)
        {
            return indent + text.Replace("\r\n", "\n").Replace("\n", "\n" + indent);
        }

        public static string ModVersion
        {
            get { return typeof(AtLog).Assembly.GetName().Version.ToString(); }
        }
    }
}
