using System;
using System.Collections.Generic;
using System.Text;

namespace AutoTranslate
{
    /// <summary>
    /// Offline language detection, no dependencies.
    ///  - ScriptLang: non-Latin scripts are decisive per string (kana -> ja, hangul -> ko, han -> zh, Cyrillic -> ru/uk, ...).
    ///  - LatinLang: Latin-script languages are decided per MOD from a large sample of its texts (stop words +
    ///    language-specific letters). Short labels like "iron sword" carry no evidence, so a mod's sample is aggregated,
    ///    and if the evidence is weak the answer is English (by far the most common source language).
    /// </summary>
    public static class LangDetect
    {
        static readonly Dictionary<string, HashSet<string>> Stop = Build(new Dictionary<string, string>
        {
            {"en", "the of and to is that it for with as on be are this by or from your you can will an at not has have was were its their which"},
            {"pt", "de que o do da em um para com não uma os no se na por mais as dos como mas foi ao ele das tem seu sua ou ser quando muito há nos já está você também são pelo pela até isso"},
            {"es", "de la que el en y los del se las por un para con no una su al lo como más pero sus le ya este sí porque esta entre cuando muy sin sobre también me hasta hay donde son"},
            {"fr", "de la le les et des en un du une que est pour qui dans par au sur pas plus avec ce il ne se son sa ses ou sont mais comme nous vous cette être"},
            {"de", "der die und in den von zu das mit sich des auf für ist im dem nicht ein eine als auch es an werden aus er hat dass sie nach wird bei einer um am sind noch wie"},
            {"it", "di e il la che è per un in con non una sono le da del della si dei più come ma al ho gli lo anche questo nel alla"},
            {"nl", "de van het een en in is dat op te zijn voor met die niet aan er maar om ook als bij of uit"},
            {"pl", "i w nie na się z do to że jest jak po co ale za od przez czy dla tak już"},
            {"tr", "ve bir bu için ile da de çok olarak daha gibi en ama ne kadar"},
            {"cs", "a se na je že s v to z do o ale pro jako by si"},
            {"hu", "a az és hogy nem is egy meg de van"},
            {"sv", "och i att det som en på är av för med till den har"},
        });

        // Letters that (almost) only occur in one language: strong evidence.
        static readonly Dictionary<string, string> Marks = new Dictionary<string, string>
        {
            {"pt", "ãõ"}, {"es", "ñ¿¡"}, {"de", "ß"}, {"fr", "œê"}, {"pl", "ąćęłńśźż"}, {"tr", "ğşı"}, {"cs", "řěů"}, {"hu", "őű"},
        };

        static Dictionary<string, HashSet<string>> Build(Dictionary<string, string> src)
        {
            var d = new Dictionary<string, HashSet<string>>();
            foreach (var kv in src) d[kv.Key] = new HashSet<string>(kv.Value.Split(' '));
            return d;
        }

        /// <summary>ISO code if the text is mainly in a non-Latin script; null for Latin-script (or no letters).</summary>
        public static string ScriptLang(string text)
        {
            int letters = 0, han = 0, kana = 0, hangul = 0, cyr = 0, arabic = 0, hebrew = 0, thai = 0, greek = 0, deva = 0, ukr = 0;
            foreach (char c in text)
            {
                if (!char.IsLetter(c)) continue;
                letters++;
                if ((c >= 0x4E00 && c <= 0x9FFF) || (c >= 0x3400 && c <= 0x4DBF)) han++;
                else if ((c >= 0x3040 && c <= 0x30FF) || (c >= 0x31F0 && c <= 0x31FF)) kana++;
                else if ((c >= 0xAC00 && c <= 0xD7AF) || (c >= 0x1100 && c <= 0x11FF)) hangul++;
                else if (c >= 0x0400 && c <= 0x04FF) { cyr++; if ("іїєґІЇЄҐ".IndexOf(c) >= 0) ukr++; }
                else if (c >= 0x0600 && c <= 0x06FF) arabic++;
                else if (c >= 0x0590 && c <= 0x05FF) hebrew++;
                else if (c >= 0x0E00 && c <= 0x0E7F) thai++;
                else if (c >= 0x0370 && c <= 0x03FF) greek++;
                else if (c >= 0x0900 && c <= 0x097F) deva++;
            }
            if (letters == 0) return null;
            int nonLatin = han + kana + hangul + cyr + arabic + hebrew + thai + greek + deva;
            if (nonLatin * 10 < letters * 3) return null;               // mostly Latin
            if (kana > 0) return "ja";                                  // Japanese mixes kana with han
            if (hangul >= han && hangul >= cyr && hangul > 0) return "ko";
            if (han >= cyr && han >= arabic && han >= hebrew && han >= thai && han >= greek && han >= deva && han > 0) return "zh";
            if (cyr > 0 && cyr >= arabic && cyr >= hebrew && cyr >= thai && cyr >= greek && cyr >= deva) return ukr > 0 ? "uk" : "ru";
            if (arabic > 0 && arabic >= hebrew && arabic >= thai && arabic >= greek && arabic >= deva) return "ar";
            if (hebrew > 0 && hebrew >= thai && hebrew >= greek && hebrew >= deva) return "he";
            if (thai > 0 && thai >= greek && thai >= deva) return "th";
            if (greek > 0 && greek >= deva) return "el";
            return deva > 0 ? "hi" : null;
        }

        /// <summary>Dominant Latin-script language of a sample of texts. confident=false -> result is the default "en".</summary>
        public static string LatinLang(IEnumerable<string> texts, out bool confident, out string detail)
        {
            var score = new Dictionary<string, int>();
            foreach (string k in Stop.Keys) score[k] = 0;
            int words = 0;
            foreach (string text in texts)
            {
                if (ScriptLang(text) != null) continue;                  // belongs to a non-Latin language
                foreach (string w0 in Tokens(text))
                {
                    words++;
                    string w = w0.ToLowerInvariant();
                    foreach (var kv in Stop) if (kv.Value.Contains(w)) score[kv.Key]++;
                    foreach (var m in Marks)
                        foreach (char c in w) if (m.Value.IndexOf(c) >= 0) score[m.Key] += 2;
                }
            }
            string best = "en", second = null; int bs = -1, ss = -1;
            foreach (var kv in score)
            {
                if (kv.Value > bs) { second = best; ss = bs; best = kv.Key; bs = kv.Value; }
                else if (kv.Value > ss) { second = kv.Key; ss = kv.Value; }
            }
            var sb = new StringBuilder("words=" + words);
            foreach (var kv in score) if (kv.Value > 0) sb.Append(' ').Append(kv.Key).Append('=').Append(kv.Value);
            detail = sb.ToString();
            confident = bs >= 3 && bs * 10 >= Math.Max(ss, 0) * 14;       // enough evidence and a clear margin
            return confident ? best : "en";
        }

        static IEnumerable<string> Tokens(string text)
        {
            var sb = new StringBuilder();
            foreach (char c in text)
            {
                if (char.IsLetter(c)) sb.Append(c);
                else if (sb.Length > 0) { yield return sb.ToString(); sb.Length = 0; }
            }
            if (sb.Length > 0) yield return sb.ToString();
        }
    }
}
