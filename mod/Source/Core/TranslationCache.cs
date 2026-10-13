using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace AutoTranslate
{
    /// <summary>
    /// Persistent cache: &lt;data&gt;/cache/&lt;lang&gt;/&lt;mod packageId&gt;.json  {"format":1,"entries":{ "english source": "translation" }}.
    /// Keyed by the exact source text, so a mod update only re-translates the strings that changed.
    /// &lt;data&gt;/overrides/&lt;lang&gt;.json uses the same entries map; the user's manual fixes there always win.
    /// A damaged file is renamed to *.corrupt-* and replaced by an empty cache; it never breaks the game.
    /// </summary>
    public sealed class TranslationCache
    {
        sealed class Bucket { public Dictionary<string, string> Entries = new Dictionary<string, string>(); public bool Dirty; public string Path; }

        readonly string target;
        readonly object gate = new object();
        readonly Dictionary<string, Bucket> buckets = new Dictionary<string, Bucket>();
        Dictionary<string, string> overrides;

        public TranslationCache(string targetLang) { target = targetLang; }

        /// <summary>Cache key of a text. MUST match bulk.normalize in the helper (shared test vectors): the helper pre-translates mods
        /// from their XML files, the game finds those translations through this key even if whitespace or "\n" escapes differ.</summary>
        public static string Norm(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            s = s.Replace("\r\n", "\n").Replace('\r', '\n').Replace("\\n", "\n");
            s = Regex.Replace(s, "[ \t]*\n[ \t]*", "\n");
            s = Regex.Replace(s, "[ \t]{2,}", " ");
            return s.Trim();
        }

        static Dictionary<string, string> NormKeys(Dictionary<string, string> raw)
        {
            var d = new Dictionary<string, string>();
            foreach (var kv in raw) { string k = Norm(kv.Key); if (k.Length > 0 && !d.ContainsKey(k)) d[k] = kv.Value; }
            return d;
        }

        string BucketPath(string bucket) { return Path.Combine(Path.Combine(Paths.CacheDir, target), Paths.SafeFileName(bucket) + ".json"); }

        Bucket Load(string bucket)
        {
            Bucket b;
            if (buckets.TryGetValue(bucket, out b)) return b;
            b = new Bucket { Path = BucketPath(bucket) };
            buckets[bucket] = b;
            b.Entries = NormKeys(ReadEntries(b.Path, "cache"));
            return b;
        }

        static Dictionary<string, string> ReadEntries(string path, string area)
        {
            var d = new Dictionary<string, string>();
            try
            {
                if (!File.Exists(path)) return d;
                var root = Json.Parse(File.ReadAllText(path, Encoding.UTF8)) as Dictionary<string, object>;
                object e;
                var entries = root != null && root.TryGetValue("entries", out e) ? e as Dictionary<string, object> : null;
                if (entries == null) throw new FormatException("no 'entries' object");
                foreach (var kv in entries) { var s = kv.Value as string; if (s != null) d[kv.Key] = s; }
            }
            catch (Exception ex)
            {
                string bad = path + ".corrupt-" + DateTime.Now.ToString("yyyyMMdd-HHmmss");
                AtLog.Error(area, "cache file unreadable, moved to '" + bad + "' and starting empty: " + path, ex);
                try { File.Move(path, bad); } catch (Exception mv) { AtLog.Warn(area, "could not move corrupt file: " + mv.Message); }
                d.Clear();
            }
            return d;
        }

        public bool TryGet(string bucket, string source, out string translation)
        {
            source = Norm(source);
            lock (gate)
            {
                if (overrides == null) LoadOverrides();
                if (overrides.TryGetValue(source, out translation)) return true;
                if (!Load(bucket).Entries.TryGetValue(source, out translation)) return false;
                if (translation.IndexOf('\u2581') >= 0)       // old bad entry ("_" instead of spaces): treat as missing so it is translated again
                {
                    Load(bucket).Entries.Remove(source);
                    Load(bucket).Dirty = true;
                    translation = null;
                    return false;
                }
                return true;
            }
        }

        void LoadOverrides()
        {
            overrides = NormKeys(ReadEntries(Path.Combine(Paths.OverridesDir, target + ".json"), "cache-overrides"));
            if (overrides.Count > 0) AtLog.Info("cache", overrides.Count + " manual override(s) loaded for '" + target + "'");
        }

        public void Put(string bucket, string source, string translation)
        {
            source = Norm(source);
            lock (gate) { var b = Load(bucket); b.Entries[source] = translation; b.Dirty = true; }
        }

        public int Count(string bucket) { lock (gate) { return Load(bucket).Entries.Count; } }

        /// <summary>Atomic write (tmp + replace). Returns number of files written. Errors are reported, not thrown.</summary>
        public int SaveDirty()
        {
            var work = new List<Bucket>();
            lock (gate) { foreach (var b in buckets.Values) if (b.Dirty) work.Add(b); }
            int written = 0;
            foreach (Bucket b in work)
            {
                try
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(b.Path));
                    var sb = new StringBuilder("{\"format\":1,\"target\":" + Json.Quote(target) + ",\"entries\":{");
                    bool first = true;
                    lock (gate)
                    {
                        foreach (var kv in b.Entries)
                        {
                            if (!first) sb.Append(',');
                            first = false;
                            sb.Append('\n').Append(Json.Quote(kv.Key)).Append(':').Append(Json.Quote(kv.Value));
                        }
                        b.Dirty = false;
                    }
                    sb.Append("\n}}");
                    string tmp = b.Path + ".tmp";
                    File.WriteAllText(tmp, sb.ToString(), new UTF8Encoding(false));
                    if (File.Exists(b.Path)) File.Delete(b.Path);
                    File.Move(tmp, b.Path);
                    written++;
                }
                catch (Exception ex)
                {
                    lock (gate) { b.Dirty = true; }
                    Safe.Report("cache", ex, "saving '" + b.Path + "'");
                }
            }
            return written;
        }

        public static int ClearTarget(string targetLang)
        {
            string dir = Path.Combine(Paths.CacheDir, targetLang);
            int n = 0;
            if (Directory.Exists(dir))
            {
                foreach (string f in Directory.GetFiles(dir, "*.json")) { File.Delete(f); n++; }
            }
            AtLog.Info("cache", "cleared " + n + " cache file(s) for '" + targetLang + "'");
            return n;
        }
    }
}
