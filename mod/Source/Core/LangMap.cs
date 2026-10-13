using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;
using Verse;

namespace AutoTranslate
{
    /// <summary>RimWorld language names / Unity SystemLanguage -> ISO 639-1 code (what the helper's models use).</summary>
    public static class LangMap
    {
        // key: lowercase, no spaces/accents. Covers RimWorld folder names, native names and Unity SystemLanguage names.
        static readonly Dictionary<string, string> Table = new Dictionary<string, string>
        {
            {"english","en"},
            {"portuguese","pt-PT"},{"portugues","pt-PT"},{"portuguesebrazilian","pt-BR"},{"portuguesbrasileiro","pt-BR"},
            {"spanish","es"},{"spanishlatin","es"},{"espanol","es"},{"espanollatino","es"},
            {"french","fr"},{"francais","fr"},{"german","de"},{"deutsch","de"},{"italian","it"},{"italiano","it"},
            {"russian","ru"},{"russkij","ru"},{"polish","pl"},{"polski","pl"},{"turkish","tr"},{"turkce","tr"},
            {"ukrainian","uk"},{"czech","cs"},{"cestina","cs"},{"dutch","nl"},{"nederlands","nl"},
            {"hungarian","hu"},{"magyar","hu"},{"japanese","ja"},{"korean","ko"},
            {"chinesesimplified","zh"},{"chinese","zh"},{"chinesetraditional","zh"},
            {"danish","da"},{"finnish","fi"},{"swedish","sv"},{"norwegian","nb"},{"greek","el"},{"romanian","ro"},
            {"slovak","sk"},{"catalan","ca"},{"arabic","ar"},{"hebrew","he"},{"indonesian","id"},{"thai","th"},{"vietnamese","vi"},
        };

        static string Norm(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            string d = s.Normalize(NormalizationForm.FormD);
            var sb = new StringBuilder();
            foreach (char c in d)
                if (CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark && char.IsLetter(c)) sb.Append(char.ToLowerInvariant(c));
            return sb.ToString();
        }

        /// <summary>Canonical target code: "pt" (old settings), "pb" and "pt-br" become "pt-BR"; "pt-pt" becomes "pt-PT"; others are lowercased.</summary>
        public static string NormTarget(string code)
        {
            if (string.IsNullOrEmpty(code)) return code;
            string c = code.Trim().Replace('_', '-').ToLowerInvariant();
            if (c == "pt" || c == "pb" || c == "pt-br") return "pt-BR";
            if (c == "pt-pt") return "pt-PT";
            return c;
        }

        /// <summary>Language without region: pt-BR, pt-PT and pb are all "pt".</summary>
        public static string Family(string code)
        {
            if (string.IsNullOrEmpty(code)) return code;
            string b = code.Replace('_', '-').Split('-')[0].ToLowerInvariant();
            return b == "pb" ? "pt" : b;
        }

        /// <summary>Same language (the variants of Portuguese cannot be told apart in a text, so they count as one).</summary>
        public static bool Same(string a, string b) { return !string.IsNullOrEmpty(a) && !string.IsNullOrEmpty(b) && Family(a) == Family(b); }

        /// <summary>Code of the translation model: pt-BR -> pb, pt-PT -> pt, the rest unchanged (what the helper lists in /health).
        /// A plain "pt" is a SOURCE language and keeps its model "pt".</summary>
        public static string ModelCode(string code)
        {
            string c = (code ?? "").Replace('_', '-').ToLowerInvariant();
            return c == "pt-br" ? "pb" : c == "pt-pt" ? "pt" : code;
        }

        public static string FromName(string name)
        {
            string code;
            return Table.TryGetValue(Norm(name), out code) ? code : null;
        }

        public static string FromGameLanguage(LoadedLanguage lang)
        {
            if (lang == null) return null;
            string c = FromName(lang.folderName);
            if (c == null && lang.info != null) c = FromName(lang.info.friendlyNameEnglish) ?? FromName(lang.info.friendlyNameNative);
            return c;
        }

        public static string FromSystem()
        {
            string c = FromName(Application.systemLanguage.ToString());
            if (c != null && Family(c) == "pt")      // the region of the OS tells Brazil from Portugal; without one, Brazil
                return CultureInfo.CurrentUICulture.Name.StartsWith("pt-PT", StringComparison.OrdinalIgnoreCase) ? "pt-PT" : "pt-BR";
            if (c != null) return c;
            string two = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName;
            return string.IsNullOrEmpty(two) || two == "iv" ? null : two.ToLowerInvariant();
        }

        /// <summary>Folder names under Languages/ that count as "this mod already ships the target language".</summary>
        public static bool IsFolderOfLanguage(string folderName, string code)
        {
            return FromName(folderName) == code;
        }

        /// <summary>Target language chosen in the translator program (&lt;data&gt;/config.json, key "target"), or null.</summary>
        public static string ConfigTarget()
        {
            try
            {
                string f = Path.Combine(Paths.DataDir, "config.json");
                if (!File.Exists(f)) return null;
                var root = Json.Parse(File.ReadAllText(f, Encoding.UTF8)) as System.Collections.Generic.Dictionary<string, object>;
                object v;
                string t = root != null && root.TryGetValue("target", out v) ? v as string : null;
                return string.IsNullOrWhiteSpace(t) ? null : NormTarget(t);
            }
            catch (Exception e) { AtLog.Warn("config", "cannot read config.json (ignored)", e); return null; }
        }

        /// <summary>Settings value "auto" -> game language if not English, else OS language; otherwise the given code.</summary>
        public static string ResolveTarget(string setting, out string how)
        {
            if (!string.IsNullOrEmpty(setting) && !string.Equals(setting, "auto", StringComparison.OrdinalIgnoreCase))
            {
                how = "manual setting";
                return NormTarget(setting);
            }
            string chosen = ConfigTarget();                     // the player's choice in the translator program wins
            if (chosen != null) { how = "chosen in the translator program"; return chosen; }
            string g = FromGameLanguage(LanguageDatabase.activeLanguage);
            if (g != null && g != "en") { how = "game language"; return g; }
            string s = FromSystem();
            if (s != null && s != "en") { how = "system language"; return s; }
            how = "none (game and system are English)";
            return null;
        }
    }
}
