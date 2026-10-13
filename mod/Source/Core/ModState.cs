using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using Verse;

namespace AutoTranslate
{
    public static class ModMode
    {
        public const string Auto = "auto";       // native > third-party > automatic translation (recommended)
        public const string Native = "native";   // only the mod's own translation
        public const string Third = "third";     // only a translation supplied by another mod
        public const string Mine = "mine";       // always the automatic translation, even if the mod/others have one
        public const string Off = "off";         // do not touch this mod

        public static readonly string[] All = { Auto, Native, Third, Mine, Off };

        public static string Label(string m) { return T.Get("AT_Mode_" + (Array.IndexOf(All, m) >= 0 && m != Off ? m : Auto)); }
    }

    /// <summary>Everything the mod knows and does for ONE installed mod. Failures, counters, cache file and
    /// the "disabled" switch are all per mod, so a problem in one mod can never affect another.</summary>
    public sealed class ModState
    {
        public const int FailureLimit = 3;

        public ModContentPack Pack;
        public string Id, Name;
        public string Mode = ModMode.Auto;
        public volatile bool AutoDisabled;
        public string DisableReason;
        public int Failures;
        public string LastFailure;
        public readonly List<string> FailureLog = new List<string>();   // last 20 failures, for the problem report

        // counters (strings)
        public int Found, FromCache, Translated, Failed, Native, Third, ProviderApplied, AlreadyTarget, UnsupportedPair, EnglishUnavailable, Applied, Placeholders;
        public bool IsSelf;                      // this mod itself: only its own Keyed texts are translated; hidden in the list
        readonly Dictionary<string, SupportInfo> Support = new Dictionary<string, SupportInfo>();
        public void SetSupport(string lang, SupportInfo s) { lock (Support) Support[lang] = s; }
        public SupportInfo GetSupport(string lang) { lock (Support) { SupportInfo s; return Support.TryGetValue(lang, out s) ? s : null; } }
        public readonly HashSet<Pipeline.Item> AppliedSet = new HashSet<Pipeline.Item>();   // source language -> can it be translated to the target?
        public string SourceOverride;            // from settings, null = detect
        public string LatinLang = "en";          // detected language of this mod's Latin-script texts
        public bool LatinConfident;
        public readonly Dictionary<string, int> SourceCounts = new Dictionary<string, int>();   // source language -> strings
        public readonly List<string> UnsupportedPairs = new List<string>();
        public readonly Dictionary<string, int> ProviderCounts = new Dictionary<string, int>(); // third-party mod name -> strings
        public readonly List<Pipeline.Item> AppliedItems = new List<Pipeline.Item>();
        public bool PendingRevert;

        public bool Active { get { return !AutoDisabled && Mode != ModMode.Off; } }

        public void CountProvider(string providerName)
        {
            int n; ProviderCounts.TryGetValue(providerName, out n); ProviderCounts[providerName] = n + 1;
        }

        /// <summary>Record a problem attributed to this mod. After FailureLimit problems its translation is switched off
        /// (and later reverted on the game thread), the reason is persisted and a report file is written.</summary>
        public void Fail(string kind, string message, Exception ex)
        {
            int n = Interlocked.Increment(ref Failures);
            LastFailure = kind + ": " + message;
            lock (FailureLog) { if (FailureLog.Count < 20) FailureLog.Add(DateTime.Now.ToString("HH:mm:ss") + " " + kind + ": " + message + (ex != null ? " | " + ex.GetType().Name + ": " + ex.Message : "")); }
            string area = "mod:" + Id + "/" + kind;
            if (ex != null) Safe.Report(area, ex, message);
            else AtLog.Error(area, message);
            if (n >= FailureLimit && !AutoDisabled) Disable("repeated " + kind + " problems (last: " + Short(message) + ")", ex);
        }

        public void Disable(string reason, Exception ex)
        {
            lock (this)
            {
                if (AutoDisabled) return;
                AutoDisabled = true;
                DisableReason = reason;
                PendingRevert = true;
            }
            AtLog.Fatal("mod:" + Id, "TRANSLATION DISABLED for mod '" + Name + "' (" + Id + "): " + reason
                + ". Its automatic translations are being reverted. Re-enable it in the Auto Translate settings after the cause is fixed.", ex);
            StateStore.SetDisabled(Id, reason);
            CrashReporter.WriteReport("mod-disabled:" + Id, ex ?? new InvalidOperationException(reason));
            Pipeline.NotifyDisabled(this);
            string report = ReportBuilder.BuildSafe();
            if (report != null) AtLog.Info("report", "problem report ready: " + report + " (send it with the button in the mod settings)");
        }

        static string Short(string s) { return s != null && s.Length > 120 ? s.Substring(0, 120) + "..." : s; }

        /// <summary>Row text in the player's language, including whether each detected language can be translated.</summary>
        public string StatusTextUi()
        {
            if (AutoDisabled) return T.Get("AT_R_AutoDisabled", DisableReason);
            if (Mode == ModMode.Off) return T.Get("AT_R_Disabled");
            var parts = new List<string>();
            if (Native > 0) parts.Add(T.Get("AT_R_Own", Native));
            if (Third > 0) parts.Add(T.Get("AT_R_Third", string.Join(", ", new List<string>(ProviderCounts.Keys).ToArray()), Third));
            if (Found > 0)
            {
                string a = T.Get("AT_R_Auto", Translated + FromCache, Found);
                var extra = new List<string>();
                if (Failed > 0) extra.Add(T.Get("AT_R_Failed", Failed));
                if (FromCache > 0) extra.Add(T.Get("AT_R_Cache", FromCache));
                parts.Add(extra.Count > 0 ? a + " (" + string.Join(", ", extra.ToArray()) + ")" : a);
            }
            if (AlreadyTarget > 0) parts.Add(T.Get("AT_R_Already", AlreadyTarget));
            if (Placeholders > 0) parts.Add(T.Get("AT_R_Placeholder", Placeholders));
            if (EnglishUnavailable > 0) parts.Add(T.Get("AT_R_Unavail", EnglishUnavailable));
            foreach (string lang in SourceCounts.Keys) parts.Add(SupportLine(lang));
            return parts.Count == 0 ? T.Get("AT_R_Nothing") : string.Join("   |   ", parts.ToArray());
        }

        string SupportLine(string lang)
        {
            string a = LangNames.Label(lang), b = LangNames.Label(Pipeline.Target);
            SupportInfo s;
            bool have;
            lock (Support) have = Support.TryGetValue(lang, out s);
            if (!have) return T.Get("AT_R_Checking", a, b);
            if (!s.Known) return T.Get("AT_R_SupportUnknown", a, b);
            if (!s.Supported) return "<color=#ff7777>" + T.Get("AT_R_NoSupport", a, b) + "</color>";
            return "<color=#88dd88>" + T.Get(s.Download.Count > 0 ? "AT_R_SupportDownload" : "AT_R_Support", a, b) + "</color>";
        }

        public string StatusText()
        {
            if (AutoDisabled) return "Auto-disabled: " + DisableReason;
            if (Mode == ModMode.Off) return "Disabled by you";
            var sb = new StringBuilder();
            if (Native > 0) sb.Append("Own translation: " + Native + " | ");
            if (Third > 0) sb.Append("Third-party (" + string.Join(", ", new List<string>(ProviderCounts.Keys).ToArray()) + "): " + Third + " | ");
            if (Found > 0)
                sb.Append("Auto: " + (Translated + FromCache) + "/" + Found + (Failed > 0 ? " (" + Failed + " failed)" : "")
                    + (FromCache > 0 ? " [" + FromCache + " from cache]" : "") + " | ");
            if (SourceCounts.Count > 0)
            {
                var l = new List<string>();
                foreach (var kv in SourceCounts) l.Add(kv.Key + " " + kv.Value);
                sb.Append("Source: " + string.Join(", ", l.ToArray()) + (SourceOverride != null ? " (set by you)" : "") + " | ");
            }
            if (AlreadyTarget > 0) sb.Append("Already in target language: " + AlreadyTarget + " | ");
            if (UnsupportedPair > 0) sb.Append("No model for " + string.Join(", ", UnsupportedPairs.ToArray()) + ": " + UnsupportedPair + " left as is | ");
            if (EnglishUnavailable > 0) sb.Append("English source unavailable: " + EnglishUnavailable + " | ");
            if (sb.Length == 0) return "Nothing to translate";
            return sb.ToString().TrimEnd(' ', '|');
        }
    }

    /// <summary>Persistent per-mod flags (auto-disabled mods) and the "currently applying" marker used to blame
    /// the right mod if the game dies while a translation is being applied.</summary>
    public static class StateStore
    {
        static readonly object Gate = new object();
        static string Dir { get { return Path.Combine(Paths.DataDir, "state"); } }
        static string File_ { get { return Path.Combine(Dir, "modstates.json"); } }
        static string Marker { get { return Path.Combine(Dir, "applying.txt"); } }
        static Dictionary<string, string> disabled; // id -> reason

        static Dictionary<string, string> Load()
        {
            if (disabled != null) return disabled;
            disabled = new Dictionary<string, string>();
            try
            {
                if (!File.Exists(File_)) return disabled;
                var root = Json.Parse(File.ReadAllText(File_, Encoding.UTF8)) as Dictionary<string, object>;
                object m;
                var mods = root != null && root.TryGetValue("disabled", out m) ? m as Dictionary<string, object> : null;
                if (mods != null) foreach (var kv in mods) disabled[kv.Key] = Convert.ToString(kv.Value);
            }
            catch (Exception ex) { AtLog.Error("state", "cannot read " + File_ + " (treated as empty)", ex); }
            return disabled;
        }

        static void Save()
        {
            try
            {
                Directory.CreateDirectory(Dir);
                var sb = new StringBuilder("{\"disabled\":{");
                bool first = true;
                foreach (var kv in Load()) { if (!first) sb.Append(','); first = false; sb.Append(Json.Quote(kv.Key)).Append(':').Append(Json.Quote(kv.Value)); }
                File.WriteAllText(File_, sb.Append("}}").ToString(), new UTF8Encoding(false));
            }
            catch (Exception ex) { AtLog.Error("state", "cannot write " + File_, ex); }
        }

        public static string GetDisabledReason(string id) { lock (Gate) { string r; return Load().TryGetValue(id, out r) ? r : null; } }
        public static void SetDisabled(string id, string reason) { lock (Gate) { Load()[id] = reason; Save(); } }
        public static void Clear(string id) { lock (Gate) { if (Load().Remove(id)) Save(); } }
        public static void ResetForTests() { lock (Gate) { disabled = null; } }

        public static void SetApplying(string id)
        {
            try { Directory.CreateDirectory(Dir); File.WriteAllText(Marker, id, new UTF8Encoding(false)); }
            catch (Exception ex) { AtLog.Warn("state", "cannot write applying marker", ex); }
        }

        public static void ClearApplying()
        {
            try { if (File.Exists(Marker)) File.Delete(Marker); } catch (Exception ex) { AtLog.Warn("state", "cannot clear applying marker", ex); }
        }

        /// <summary>If the previous session ended while applying a mod's translation, return that mod id.</summary>
        public static string TakeStaleApplying()
        {
            try
            {
                if (!File.Exists(Marker)) return null;
                string id = File.ReadAllText(Marker).Trim();
                File.Delete(Marker);
                return id.Length == 0 ? null : id;
            }
            catch (Exception ex) { AtLog.Warn("state", "cannot read applying marker", ex); return null; }
        }
    }
}
