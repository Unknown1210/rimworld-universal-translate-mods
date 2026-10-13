using System;
using System.Collections.Generic;

namespace AutoTranslate
{
    /// <summary>
    /// Every entry point of the mod (patch, update tick, worker step, UI) runs through Safe.
    /// Guarantees: the mod never throws into the game; each failure is logged with area + context;
    /// an area that keeps failing is switched off (circuit breaker) so one bug cannot spam or slow the game.
    /// </summary>
    public static class Safe
    {
        public const int MaxFailuresPerArea = 8;

        sealed class AreaState { public int Failures; public bool Disabled; public string LastError; }

        static readonly object Gate = new object();
        static readonly Dictionary<string, AreaState> Areas = new Dictionary<string, AreaState>();

        public static bool Run(string area, Action action, string context = null)
        {
            if (IsDisabled(area)) return false;
            try { action(); return true; }
            catch (Exception ex) { Report(area, ex, context); return false; }
        }

        public static T Call<T>(string area, Func<T> func, T fallback, string context = null)
        {
            if (IsDisabled(area)) return fallback;
            try { return func(); }
            catch (Exception ex) { Report(area, ex, context); return fallback; }
        }

        public static bool IsDisabled(string area)
        {
            lock (Gate) { AreaState s; return Areas.TryGetValue(area, out s) && s.Disabled; }
        }

        public static void Reenable(string area)
        {
            lock (Gate) { Areas.Remove(area); }
            AtLog.Info("safe", "area '" + area + "' re-enabled");
        }

        /// <summary>Record a failure: log full details, count it, and trip the breaker when the area keeps failing.</summary>
        public static void Report(string area, Exception ex, string context)
        {
            bool tripped = false;
            int n;
            lock (Gate)
            {
                AreaState s;
                if (!Areas.TryGetValue(area, out s)) Areas[area] = s = new AreaState();
                n = ++s.Failures;
                s.LastError = ex.GetType().Name + ": " + ex.Message;
                if (n >= MaxFailuresPerArea && !s.Disabled) { s.Disabled = true; tripped = true; }
            }
            string top = FirstStackLine(ex);
            AtLog.ErrorLimited(area, area + "|" + ex.GetType().Name + "|" + top,
                "FAILURE #" + n + " in area '" + area + "'" + (context != null ? " | context: " + context : ""), ex);
            if (tripped)
            {
                AtLog.Fatal("safe", "AREA DISABLED: '" + area + "' failed " + n + " times; its feature is turned off for this session. Last error: "
                    + ex.GetType().Name + ": " + ex.Message + ". Log: " + AtLog.LogFile);
                try { Verse.Log.Error("[AutoTranslate] Feature '" + area + "' disabled after repeated errors. See " + AtLog.LogFile); } catch { }
                CrashReporter.WriteReport("area-disabled:" + area, ex);
            }
        }

        static string FirstStackLine(Exception ex)
        {
            string st = ex.StackTrace;
            if (string.IsNullOrEmpty(st)) return "";
            int i = st.IndexOf('\n');
            return (i < 0 ? st : st.Substring(0, i)).Trim();
        }

        public static Dictionary<string, string> Snapshot()
        {
            var d = new Dictionary<string, string>();
            lock (Gate)
            {
                foreach (var kv in Areas)
                    d[kv.Key] = kv.Value.Failures + " failure(s)" + (kv.Value.Disabled ? " [DISABLED]" : "") + "; last: " + kv.Value.LastError;
            }
            return d;
        }
    }
}
