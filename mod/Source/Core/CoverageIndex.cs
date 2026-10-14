using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Xml;
using Verse;

namespace AutoTranslate
{
    public sealed class Cover
    {
        public ModContentPack Provider;
        public string Value;
        public string File;
        public bool FilePlaceholder;      // the whole file is an untranslated copy: its texts together read as another language than the target
    }

    /// <summary>
    /// Which strings are ALREADY translated into the target language, and by which installed mod.
    /// Built by reading Languages/&lt;target&gt;/DefInjected and Keyed of every non-official mod, so it works whether or not the
    /// game currently runs in that language. Providers are kept in load order; the last one is what RimWorld uses.
    /// Provider == the mod itself -> "own translation"; any other mod -> "third-party translation".
    /// </summary>
    public sealed class CoverageIndex
    {
        public readonly Dictionary<string, List<Cover>> Defs = new Dictionary<string, List<Cover>>();
        public readonly Dictionary<string, List<Cover>> Keyed = new Dictionary<string, List<Cover>>();
        public int Files, Entries, BadFiles;
        string targetCode;
        List<Cover> fileCovers;           // the covers of the file being read
        public readonly List<string[]> BadFileList = new List<string[]>();   // {path, provider packageId, error}

        public static IEnumerable<string> ModFolders(ModContentPack mod)
        {
            var list = new List<string> { mod.RootDir };
            try
            {
                var f = typeof(ModContentPack).GetField("foldersToLoadDescendingOrder", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                var seq = f != null ? f.GetValue(mod) as System.Collections.IEnumerable : null;
                if (seq != null) foreach (object o in seq) { var s = o as string; if (s != null && !list.Contains(s)) list.Add(s); }
            }
            catch (Exception e) { AtLog.Warn("coverage", "cannot list load folders of " + mod.PackageIdPlayerFacing, e); }
            return list;
        }

        public static string DefKey(string defType, string defName, string field) { return defType + "/" + defName + "." + field; }

        public static CoverageIndex Build(string target, IList<ModContentPack> mods, ICollection<string> fieldWhitelist)
        {
            var idx = new CoverageIndex { targetCode = target };
            foreach (ModContentPack mod in mods)
            {
                ModContentPack m = mod;
                Safe.Run("coverage", () =>
                {
                    foreach (string root in ModFolders(m))
                    {
                        string langs = Path.Combine(root, "Languages");
                        if (!Directory.Exists(langs)) continue;
                        foreach (string dir in Directory.GetDirectories(langs))
                        {
                            if (!LangMap.IsFolderOfLanguage(Path.GetFileName(dir), target)) continue;
                            string di = Path.Combine(dir, "DefInjected");
                            if (Directory.Exists(di))
                                foreach (string f in Directory.GetFiles(di, "*.xml", SearchOption.AllDirectories))
                                    idx.ReadFile(f, m, di, true, fieldWhitelist);
                            string kd = Path.Combine(dir, "Keyed");
                            if (Directory.Exists(kd))
                                foreach (string f in Directory.GetFiles(kd, "*.xml", SearchOption.AllDirectories))
                                    idx.ReadFile(f, m, kd, false, fieldWhitelist);
                        }
                    }
                }, "indexing translations of mod " + m.PackageIdPlayerFacing);
            }
            AtLog.Info("coverage", "indexed " + idx.Files + " translation file(s): " + idx.Entries + " entries (" + idx.Defs.Count + " def fields, "
                + idx.Keyed.Count + " keys); " + idx.BadFiles + " unreadable file(s)");
            return idx;
        }

        void ReadFile(string file, ModContentPack provider, string baseDir, bool isDef, ICollection<string> whitelist)
        {
            try
            {
                string defType = null;
                if (isDef)
                {
                    string rel = file.Substring(baseDir.Length).TrimStart('/', '\\').Replace('\\', '/');
                    int slash = rel.IndexOf('/');
                    if (slash < 0) return; // DefInjected files must sit inside a def-type folder
                    defType = rel.Substring(0, slash);
                }
                var settings = new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, IgnoreComments = true, XmlResolver = null };
                Files++;
                fileCovers = new List<Cover>();
                using (var r = XmlReader.Create(file, settings))
                {
                    r.MoveToContent();
                    if (r.IsEmptyElement) return;
                    int depth = r.Depth;
                    r.Read();
                    while (!r.EOF && r.Depth > depth)
                    {
                        if (r.NodeType != XmlNodeType.Element) { r.Read(); continue; }
                        string name = r.Name;
                        string value = null;
                        if (r.IsEmptyElement) { r.Read(); continue; }
                        string inner = r.ReadInnerXml();               // consumes the element
                        if (inner.IndexOf('<') < 0) value = System.Net.WebUtility.HtmlDecode(inner).Trim(); // plain text (no <li> lists)
                        if (string.IsNullOrEmpty(value) || value == "TODO") continue;
                        if (isDef)
                        {
                            int dot = name.IndexOf('.');
                            if (dot <= 0) continue;
                            string field = name.Substring(dot + 1);
                            if (whitelist != null && !whitelist.Contains(field)) continue;
                            Add(Defs, DefKey(defType, name.Substring(0, dot), field), provider, value, file);
                        }
                        else Add(Keyed, name, provider, value, file);
                    }
                }
                JudgeFile();
            }
            catch (Exception e)
            {
                fileCovers = null;
                BadFiles++;
                BadFileList.Add(new[] { file, provider.PackageIdPlayerFacing, e.GetType().Name + ": " + e.Message });
                AtLog.Warn("coverage", "cannot read translation file (ignored): " + file + " from mod " + provider.PackageIdPlayerFacing, e);
            }
        }

        void Add(Dictionary<string, List<Cover>> map, string key, ModContentPack provider, string value, string file)
        {
            List<Cover> l;
            if (!map.TryGetValue(key, out l)) map[key] = l = new List<Cover>(1);
            var c = new Cover { Provider = provider, Value = value, File = file };
            l.Add(c);
            if (fileCovers != null) fileCovers.Add(c);
            Entries++;
        }

        /// <summary>A "translation" file the author never translated (the game's tool copies the English text into it): short labels cannot
        /// be judged one by one ("MF Bed"), but the whole file read as one text is plainly English. All its entries then count as placeholders.</summary>
        void JudgeFile()
        {
            var covers = fileCovers;
            fileCovers = null;
            if (covers == null || covers.Count < 2 || targetCode == null) return;
            var texts = new List<string>();
            int chars = 0, foreign = 0, scripted = 0;
            foreach (Cover c in covers)
            {
                string v = TranslationCache.Norm(c.Value);
                texts.Add(v);
                chars += v.Length;
                string sl = LangDetect.ScriptLang(v);
                if (sl != null) { scripted++; if (!LangMap.Same(sl, targetCode)) foreign++; }
            }
            bool untranslated;
            if (scripted * 2 > covers.Count) untranslated = foreign * 2 > scripted;
            else
            {
                if (chars < 60) return;
                bool conf; string det;
                string lat = LangDetect.LatinLang(texts, out conf, out det);
                untranslated = conf && !LangMap.Same(lat, targetCode);
            }
            if (untranslated) foreach (Cover c in covers) c.FilePlaceholder = true;
        }

        /// <summary>Covers of a def field, trying the def class and its base classes (and the legacy plural folder name).</summary>
        public List<Cover> ForDefField(Type defClass, string defName, string field)
        {
            for (Type t = defClass; t != null && t != typeof(object); t = t.BaseType)
            {
                List<Cover> l;
                if (Defs.TryGetValue(DefKey(t.Name, defName, field), out l)) return l;
                if (Defs.TryGetValue(DefKey(t.Name + "s", defName, field), out l)) return l;
            }
            return null;
        }

        public List<Cover> ForKey(string key)
        {
            List<Cover> l;
            return Keyed.TryGetValue(key, out l) ? l : null;
        }
    }
}
