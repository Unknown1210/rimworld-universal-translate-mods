using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace AutoTranslate
{
    /// <summary>Minimal JSON writer/parser (RimWorld ships no JSON library).
    /// Parse returns Dictionary&lt;string,object&gt;, List&lt;object&gt;, string, double, bool or null.</summary>
    public static class Json
    {
        public static string Quote(string s)
        {
            var sb = new StringBuilder(s.Length + 2);
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
            return sb.ToString();
        }

        public static string StringArray(IList<string> items)
        {
            var sb = new StringBuilder("[");
            for (int i = 0; i < items.Count; i++)
            {
                if (i > 0) sb.Append(',');
                sb.Append(Quote(items[i]));
            }
            return sb.Append(']').ToString();
        }

        public static object Parse(string text)
        {
            var p = new Parser(text);
            object v = p.Value();
            p.SkipWs();
            if (p.Pos != text.Length) throw p.Error("trailing data");
            return v;
        }

        sealed class Parser
        {
            readonly string s;
            public int Pos;
            public Parser(string text) { s = text; }

            public Exception Error(string msg)
            {
                int line = 1, col = 1;
                for (int i = 0; i < Pos && i < s.Length; i++) { if (s[i] == '\n') { line++; col = 1; } else col++; }
                return new FormatException("JSON: " + msg + " at line " + line + ", column " + col);
            }

            public void SkipWs() { while (Pos < s.Length && char.IsWhiteSpace(s[Pos])) Pos++; }

            public object Value()
            {
                SkipWs();
                if (Pos >= s.Length) throw Error("unexpected end");
                char c = s[Pos];
                if (c == '{') return Obj();
                if (c == '[') return Arr();
                if (c == '"') return Str();
                if (Lit("true")) return true;
                if (Lit("false")) return false;
                if (Lit("null")) return null;
                return Num();
            }

            bool Lit(string w)
            {
                if (string.CompareOrdinal(s, Pos, w, 0, w.Length) != 0) return false;
                Pos += w.Length;
                return true;
            }

            object Num()
            {
                int st = Pos;
                while (Pos < s.Length && "+-0123456789.eE".IndexOf(s[Pos]) >= 0) Pos++;
                double d;
                if (Pos == st || !double.TryParse(s.Substring(st, Pos - st), NumberStyles.Float, CultureInfo.InvariantCulture, out d))
                    throw Error("bad value");
                return d;
            }

            string Str()
            {
                Pos++; // opening quote
                var sb = new StringBuilder();
                while (true)
                {
                    if (Pos >= s.Length) throw Error("unterminated string");
                    char c = s[Pos++];
                    if (c == '"') return sb.ToString();
                    if (c != '\\') { sb.Append(c); continue; }
                    if (Pos >= s.Length) throw Error("bad escape");
                    char e = s[Pos++];
                    switch (e)
                    {
                        case 'n': sb.Append('\n'); break;
                        case 'r': sb.Append('\r'); break;
                        case 't': sb.Append('\t'); break;
                        case 'b': sb.Append('\b'); break;
                        case 'f': sb.Append('\f'); break;
                        case 'u':
                            if (Pos + 4 > s.Length) throw Error("bad \\u escape");
                            sb.Append((char)Convert.ToInt32(s.Substring(Pos, 4), 16));
                            Pos += 4;
                            break;
                        default: sb.Append(e); break; // " \ /
                    }
                }
            }

            List<object> Arr()
            {
                Pos++;
                var list = new List<object>();
                SkipWs();
                if (Pos < s.Length && s[Pos] == ']') { Pos++; return list; }
                while (true)
                {
                    list.Add(Value());
                    SkipWs();
                    if (Pos >= s.Length) throw Error("unterminated array");
                    char c = s[Pos++];
                    if (c == ']') return list;
                    if (c != ',') { Pos--; throw Error("expected , or ]"); }
                }
            }

            Dictionary<string, object> Obj()
            {
                Pos++;
                var d = new Dictionary<string, object>();
                SkipWs();
                if (Pos < s.Length && s[Pos] == '}') { Pos++; return d; }
                while (true)
                {
                    SkipWs();
                    if (Pos >= s.Length || s[Pos] != '"') throw Error("expected string key");
                    string k = Str();
                    SkipWs();
                    if (Pos >= s.Length || s[Pos++] != ':') { Pos--; throw Error("expected :"); }
                    d[k] = Value();
                    SkipWs();
                    if (Pos >= s.Length) throw Error("unterminated object");
                    char c = s[Pos++];
                    if (c == '}') return d;
                    if (c != ',') { Pos--; throw Error("expected , or }"); }
                }
            }
        }
    }
}
