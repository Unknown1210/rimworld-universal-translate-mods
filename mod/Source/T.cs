using System;
using System.Collections.Generic;
using System.Xml;
using Verse;

namespace AutoTranslate
{
    /// <summary>The mod's own screen texts live in Languages/&lt;lang&gt;/Keyed/AutoTranslate.xml (English + Portuguese written by hand;
    /// any other language is translated by this very mod like any other mod's texts). {0}, {1}... are filled here.
    /// If a key cannot be found in the game's language data (files missing), the English text embedded in the DLL is used,
    /// so the screen never shows raw keys.</summary>
    public static class T
    {
        static Dictionary<string, string> embedded;

        public static string Get(string key, params object[] args)
        {
            string s = null;
            try { if (key.CanTranslate()) s = key.Translate().ToString(); }
            catch { s = null; }
            if (s == null) s = Embedded(key) ?? key;
            for (int i = 0; i < args.Length; i++) s = s.Replace("{" + i + "}", Convert.ToString(args[i]));
            return s;
        }

        static string Embedded(string key)
        {
            if (embedded == null)
            {
                var d = new Dictionary<string, string>();
                try
                {
                    using (var st = typeof(T).Assembly.GetManifestResourceStream("AutoTranslate.English.xml"))
                    {
                        if (st != null)
                            using (var r = XmlReader.Create(st))
                            {
                                r.MoveToContent();
                                r.Read();
                                while (!r.EOF)
                                {
                                    if (r.NodeType == XmlNodeType.Element) { string k = r.Name; d[k] = r.ReadElementContentAsString(); }
                                    else r.Read();
                                }
                            }
                    }
                }
                catch (Exception e) { AtLog.Warn("i18n", "cannot read the embedded English texts", e); }
                embedded = d;
            }
            string v;
            return embedded.TryGetValue(key, out v) ? v : null;
        }
    }
}
