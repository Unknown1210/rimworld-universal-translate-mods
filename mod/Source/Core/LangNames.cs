using System.Collections.Generic;

namespace AutoTranslate
{
    /// <summary>Language names in full ("Japonês (日本語)"), never bare codes. English or Portuguese names according to the game language.</summary>
    public static class LangNames
    {
        // code -> English, Portuguese, native
        static readonly Dictionary<string, string[]> Names = new Dictionary<string, string[]>
        {
            {"en", new[]{"English","Inglês","English"}}, {"pt", new[]{"Portuguese","Português","Português"}},
            {"pt-BR", new[]{"Portuguese (Brazil)","Português (Brasil)","Português (Brasil)"}}, {"pt-PT", new[]{"Portuguese (Portugal)","Português (Portugal)","Português (Portugal)"}},
            {"es", new[]{"Spanish","Espanhol","Español"}}, {"fr", new[]{"French","Francês","Français"}},
            {"de", new[]{"German","Alemão","Deutsch"}}, {"it", new[]{"Italian","Italiano","Italiano"}},
            {"ru", new[]{"Russian","Russo","Русский"}}, {"uk", new[]{"Ukrainian","Ucraniano","Українська"}},
            {"pl", new[]{"Polish","Polonês","Polski"}}, {"tr", new[]{"Turkish","Turco","Türkçe"}},
            {"cs", new[]{"Czech","Tcheco","Čeština"}}, {"nl", new[]{"Dutch","Holandês","Nederlands"}},
            {"hu", new[]{"Hungarian","Húngaro","Magyar"}}, {"sv", new[]{"Swedish","Sueco","Svenska"}},
            {"da", new[]{"Danish","Dinamarquês","Dansk"}}, {"fi", new[]{"Finnish","Finlandês","Suomi"}},
            {"nb", new[]{"Norwegian","Norueguês","Norsk"}}, {"el", new[]{"Greek","Grego","Ελληνικά"}},
            {"ro", new[]{"Romanian","Romeno","Română"}}, {"sk", new[]{"Slovak","Eslovaco","Slovenčina"}},
            {"ca", new[]{"Catalan","Catalão","Català"}}, {"ja", new[]{"Japanese","Japonês","日本語"}},
            {"ko", new[]{"Korean","Coreano","한국어"}}, {"zh", new[]{"Chinese","Chinês","中文"}},
            {"ar", new[]{"Arabic","Árabe","العربية"}}, {"he", new[]{"Hebrew","Hebraico","עברית"}},
            {"hi", new[]{"Hindi","Hindi","हिन्दी"}}, {"id", new[]{"Indonesian","Indonésio","Bahasa Indonesia"}},
            {"th", new[]{"Thai","Tailandês","ไทย"}}, {"vi", new[]{"Vietnamese","Vietnamita","Tiếng Việt"}},
        };

        public static string Label(string code, string uiLang)
        {
            string[] n;
            if (code == null || !Names.TryGetValue(code, out n)) return code ?? "?";
            string name = uiLang == "pt" ? n[1] : n[0];
            return name == n[2] ? name : name + " (" + n[2] + ")";
        }

        /// <summary>Label in the language of the game (the one the player reads the mod screen in).</summary>
        public static string Label(string code)
        {
            string ui = null;
            try { ui = LangMap.FromGameLanguage(Verse.LanguageDatabase.activeLanguage); } catch { }
            return Label(code, ui);
        }

        public static List<KeyValuePair<string, string>> Choices(string uiLang)
        {
            var list = new List<KeyValuePair<string, string>>();
            foreach (var kv in Names) list.Add(new KeyValuePair<string, string>(kv.Key, Label(kv.Key, uiLang)));
            list.Sort((a, b) => string.Compare(a.Value, b.Value, System.StringComparison.CurrentCultureIgnoreCase));
            return list;
        }
    }
}
