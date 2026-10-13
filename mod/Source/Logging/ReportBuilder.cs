using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using Verse;

namespace AutoTranslate
{
    /// <summary>
    /// Builds ONE self-contained text report for a bug report (&lt;data&gt;/reports/report-*.md): environment, every mod with a
    /// problem (metadata, About.xml, file list + SHA-256 so the exact version can be identified, failing XML snippets),
    /// crash reports and the tail of the mod and helper logs. Personal paths/user name are redacted.
    /// It does not copy the mods themselves (other authors' content, often huge); hashes identify them instead.
    /// Nothing is uploaded: the player attaches the file to a GitHub issue (see IssueUrl).
    /// </summary>
    public static class ReportBuilder
    {
        public const string RepoUrl = "https://github.com/Unknown1210/rimworld-universal-translate-mods";
        const int AboutMax = 20000, SnippetMax = 1500, HashMaxBytes = 2 * 1024 * 1024, ListMax = 80;
        public static string LastReport;

        public static string BuildSafe()
        {
            try { return Build(); }
            catch (Exception ex) { AtLog.Error("report", "could not build the problem report", ex); return null; }
        }

        public static string Build()
        {
            string dir = Path.Combine(Paths.DataDir, "reports");
            Directory.CreateDirectory(dir);
            string path = Path.Combine(dir, "report-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".md");
            var sb = new StringBuilder();
            sb.AppendLine("# AutoTranslate problem report");
            sb.AppendLine("version: " + AtLog.ModVersion + " | created: " + DateTime.Now.ToString("o"));
            sb.AppendLine();
            sb.AppendLine("## Environment");
            sb.AppendLine("```");
            sb.AppendLine(Section(Diagnostics.Snapshot));
            sb.AppendLine("```");

            sb.AppendLine();
            sb.AppendLine("## Mods with problems");
            var suspects = new List<ModContentPack>();
            foreach (ModState ms in Pipeline.Mods)
            {
                if (!ms.AutoDisabled && ms.Failures == 0) continue;
                suspects.Add(ms.Pack);
                sb.AppendLine();
                sb.AppendLine("### " + ms.Name + " (`" + ms.Id + "`)");
                sb.AppendLine("- state: " + ms.StatusText());
                sb.AppendLine("- mode: " + ms.Mode + " | failures: " + ms.Failures + " | auto-disabled: " + ms.AutoDisabled
                    + (ms.DisableReason != null ? " (" + ms.DisableReason + ")" : ""));
                lock (ms.FailureLog) foreach (string f in ms.FailureLog) sb.AppendLine("  - " + f);
                sb.AppendLine(Section(() => ModInfo(ms.Pack)));
            }
            var idx = Pipeline.Index;
            if (idx != null && idx.BadFileList.Count > 0)
            {
                sb.AppendLine();
                sb.AppendLine("### Unreadable translation files from other mods (" + idx.BadFileList.Count + ")");
                foreach (string[] b in idx.BadFileList)
                {
                    sb.AppendLine("- `" + b[0] + "` (mod `" + b[1] + "`): " + b[2]);
                    sb.AppendLine("```xml");
                    sb.AppendLine(Section(() => Head(b[0], SnippetMax)));
                    sb.AppendLine("```");
                }
            }
            if (suspects.Count == 0 && (idx == null || idx.BadFileList.Count == 0))
                sb.AppendLine("(no mod was flagged; see the logs below)");

            sb.AppendLine();
            sb.AppendLine("## Crash reports");
            sb.AppendLine(Section(() => CrashFiles(Paths.LogDir, 3)));
            sb.AppendLine();
            sb.AppendLine("## Mod log (tail of this session)");
            sb.AppendLine("```");
            sb.AppendLine(Section(() => Tail(AtLog.LogFile, 400)));
            sb.AppendLine("```");
            sb.AppendLine();
            sb.AppendLine("## Helper log (tail)");
            sb.AppendLine("```");
            sb.AppendLine(Section(() => Tail(Path.Combine(Path.Combine(Paths.DataDir, "logs"), "helper.log"), 300)));
            sb.AppendLine("```");
            sb.AppendLine(Section(() => CrashFiles(Path.Combine(Paths.DataDir, "logs"), 2, "helper crash reports")));

            File.WriteAllText(path, Redact(sb.ToString()), new UTF8Encoding(false));
            LastReport = path;
            AtLog.Info("report", "problem report written: " + path);
            return path;
        }

        static string Section(Func<string> f)
        {
            try { return f(); }
            catch (Exception e) { return "(unavailable: " + e.GetType().Name + ": " + e.Message + ")"; }
        }

        // ------------------------------------------------------------------ pieces

        static string ModInfo(ModContentPack pack)
        {
            var sb = new StringBuilder();
            string root = pack.RootDir;
            string folder = Path.GetFileName(root.TrimEnd('/', '\\'));
            bool workshop = folder.Length > 0 && folder.Trim().Length == folder.Length && IsDigits(folder);
            sb.AppendLine("- folder: `" + root + "`" + (workshop ? " (Steam Workshop id " + folder + ": https://steamcommunity.com/sharedfiles/filedetails/?id=" + folder + ")" : " (local mod)"));
            string about = Path.Combine(Path.Combine(root, "About"), "About.xml");
            if (File.Exists(about))
            {
                sb.AppendLine("- About.xml sha256: `" + Hash(about) + "`");
                sb.AppendLine("```xml");
                sb.AppendLine(Head(about, AboutMax));
                sb.AppendLine("```");
            }
            int files = 0; long bytes = 0;
            var langs = new List<string>(); var dlls = new List<string>(); var top = new List<string>();
            foreach (string d in Directory.GetDirectories(root)) top.Add(Path.GetFileName(d) + "/");
            foreach (string f in Directory.GetFiles(root, "*", SearchOption.AllDirectories))
            {
                files++;
                var fi = new FileInfo(f);
                bytes += fi.Length;
                string rel = f.Substring(root.Length).TrimStart('/', '\\').Replace('\\', '/');
                if (files > 20000) break;
                if (rel.StartsWith("Languages/", StringComparison.OrdinalIgnoreCase) || rel.IndexOf("/Languages/", StringComparison.OrdinalIgnoreCase) >= 0)
                { if (langs.Count < ListMax) langs.Add("  - " + rel + " (" + fi.Length + " B, sha256 " + Hash(f) + ")"); }
                else if (rel.EndsWith(".dll", StringComparison.OrdinalIgnoreCase)) dlls.Add("  - " + rel + " (" + fi.Length + " B, sha256 " + Hash(f) + ")");
            }
            sb.AppendLine("- files: " + files + ", total " + (bytes / 1024) + " KB; top-level: " + string.Join(", ", top.ToArray()));
            sb.AppendLine("- code assemblies: " + (dlls.Count == 0 ? "none (content-only mod)" : "\n" + string.Join("\n", dlls.ToArray())));
            sb.AppendLine("- language files (" + langs.Count + (langs.Count >= ListMax ? "+" : "") + "):" + (langs.Count == 0 ? " none" : "\n" + string.Join("\n", langs.ToArray())));
            return sb.ToString();
        }

        static bool IsDigits(string s) { foreach (char c in s) if (c < '0' || c > '9') return false; return true; }

        static string Hash(string file)
        {
            var fi = new FileInfo(file);
            if (fi.Length > HashMaxBytes) return "(file too large to hash)";
            using (var sha = SHA256.Create())
            using (var fs = File.OpenRead(file))
            {
                byte[] h = sha.ComputeHash(fs);
                var sb = new StringBuilder();
                foreach (byte b in h) sb.Append(b.ToString("x2"));
                return sb.ToString().Substring(0, 16);   // first 64 bits are enough to match versions
            }
        }

        static string Head(string file, int max)
        {
            string t = File.ReadAllText(file);
            return t.Length <= max ? t : t.Substring(0, max) + "\n... (truncated, " + t.Length + " chars)";
        }

        static string Tail(string file, int lines)
        {
            if (file == null || !File.Exists(file)) return "(no file)";
            string[] all;
            using (var fs = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            using (var sr = new StreamReader(fs, Encoding.UTF8)) all = sr.ReadToEnd().Replace("\r\n", "\n").Split('\n');
            int from = Math.Max(0, all.Length - lines);
            return string.Join("\n", all, from, all.Length - from);
        }

        static string CrashFiles(string dir, int newest, string title = null)
        {
            if (!Directory.Exists(dir)) return "(none)";
            var files = new List<string>(Directory.GetFiles(dir, "crash-*.txt"));
            files.Sort(StringComparer.Ordinal);
            if (files.Count == 0) return "(none)";
            var sb = new StringBuilder(title != null ? "### " + title + "\n" : "");
            sb.AppendLine(files.Count + " crash report(s) on disk; newest " + Math.Min(newest, files.Count) + " follow:");
            for (int i = Math.Max(0, files.Count - newest); i < files.Count; i++)
            {
                sb.AppendLine("#### " + Path.GetFileName(files[i]));
                sb.AppendLine("```");
                sb.AppendLine(Head(files[i], 20000));
                sb.AppendLine("```");
            }
            return sb.ToString();
        }

        // ------------------------------------------------------------------ privacy + issue link

        public static string Redact(string text)
        {
            foreach (string p in new[] { Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), Environment.GetEnvironmentVariable("HOME"),
                                         Environment.GetEnvironmentVariable("USERPROFILE") })
            {
                if (string.IsNullOrEmpty(p) || p.Length < 4) continue;
                text = text.Replace(p, "<home>").Replace(p.Replace('\\', '/'), "<home>");
            }
            string user = Environment.UserName;
            if (!string.IsNullOrEmpty(user) && user.Length >= 3) text = text.Replace(user, "<user>");
            return text;
        }

        /// <summary>Prefilled "new issue" page. The report file itself must be attached by the player (drag &amp; drop).</summary>
        public static string IssueUrl()
        {
            var names = new List<string>();
            foreach (ModState ms in Pipeline.Mods) if (ms.AutoDisabled || ms.Failures > 0) names.Add(ms.Name + " (" + ms.Id + ")");
            string title = "[Report] v" + AtLog.ModVersion + (names.Count > 0 ? " - " + Short(string.Join(", ", names.ToArray()), 80) : " - problem");
            string body = "**Version:** " + AtLog.ModVersion + "\n**Game:** RimWorld " + Safe.Call("report", () => RimWorld.VersionControl.CurrentVersionString, "?")
                + "\n**Language:** " + (Pipeline.Target ?? "?") + "\n**Mods with problems:** " + (names.Count > 0 ? string.Join("; ", names.ToArray()) : "none flagged")
                + "\n\n**What happened:**\n(describe)\n\n**Attach the report file here (drag & drop):**\n" + (LastReport != null ? Redact(Path.GetFileName(LastReport)) : "(create it in the mod settings first)");
            string url = RepoUrl + "/issues/new?labels=bug&title=" + Uri.EscapeDataString(title) + "&body=" + Uri.EscapeDataString(body);
            return url.Length > 7000 ? RepoUrl + "/issues/new?labels=bug" : url;
        }

        static string Short(string s, int n) { return s.Length <= n ? s : s.Substring(0, n) + "..."; }
    }
}
