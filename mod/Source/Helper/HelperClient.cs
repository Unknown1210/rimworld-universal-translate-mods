using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;

namespace AutoTranslate
{
    public sealed class HelperException : Exception
    {
        public int Status;
        public string Url;
        public string RequestId;
        public string Body;
        public HelperException(string message, string url, string rid, int status, string body, Exception inner = null)
            : base(message, inner)
        {
            Url = url; RequestId = rid; Status = status; Body = body;
            Data["url"] = url; Data["requestId"] = rid; Data["httpStatus"] = status; Data["body"] = body;
        }
    }

    public sealed class SupportInfo
    {
        public bool Known, Supported, Installed;          // Known=false: the helper could not tell (older helper / index unreachable)
        public List<string> Download = new List<string>();
    }

    public sealed class HealthInfo
    {
        public string Version;
        public int Protocol;
        public List<string> Installed = new List<string>();
        public string InstallState; // e.g. "en>pt=running"

        /// <summary>Installed models are pairs like "en>pt". A pair works if installed directly or via English.</summary>
        public bool HasPair(string src, string tgt)
        {
            if (src == tgt) return true;
            return Installed.Contains(src + ">" + tgt) || (Installed.Contains(src + ">en") && Installed.Contains("en>" + tgt));
        }
    }

    /// <summary>HTTP client for the local helper (127.0.0.1 only). Runs on worker threads, never on the game thread.
    /// Port and token are read from the shared data folder written by the helper.</summary>
    public static class HelperClient
    {
        public const int ExpectedProtocol = 2;
        const int DefaultPort = 18765;
        public static string LastError;
        public static string LastSuccess;
        static int counter;

        static int Port()
        {
            try
            {
                string f = Path.Combine(Paths.DataDir, "port");
                int p;
                if (File.Exists(f) && int.TryParse(File.ReadAllText(f).Trim(), out p) && p > 0) return p;
            }
            catch (Exception e) { AtLog.Warn("helper-client", "cannot read port file, using default " + DefaultPort, e); }
            return DefaultPort;
        }

        static string Token()
        {
            string f = Path.Combine(Paths.DataDir, "token");
            if (!File.Exists(f))
                throw new HelperException("helper token file not found at '" + f + "'. Is the helper installed and has it been started once?", f, "-", 0, null);
            return File.ReadAllText(f).Trim();
        }

        static string Request(string method, string path, string body, int timeoutMs, out string rid)
        {
            rid = "m" + (++counter).ToString("x") + "-" + Guid.NewGuid().ToString("N").Substring(0, 6);
            string url = "http://127.0.0.1:" + Port() + path;
            var started = DateTime.UtcNow;
            try
            {
                var req = (HttpWebRequest)WebRequest.Create(url);
                req.Method = method;
                req.Proxy = null;                 // never route localhost through a system proxy
                req.Timeout = timeoutMs;
                req.ReadWriteTimeout = timeoutMs;
                req.KeepAlive = false;
                req.Headers["X-Token"] = Token();
                req.Headers["X-Request-Id"] = rid;
                if (body != null)
                {
                    byte[] data = new UTF8Encoding(false).GetBytes(body);
                    req.ContentType = "application/json; charset=utf-8";
                    req.ContentLength = data.Length;
                    using (Stream s = req.GetRequestStream()) s.Write(data, 0, data.Length);
                }
                using (var resp = (HttpWebResponse)req.GetResponse())
                using (var sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8))
                {
                    string text = sr.ReadToEnd();
                    LastSuccess = DateTime.Now.ToString("HH:mm:ss");
                    AtLog.Debug("helper-client", method + " " + path + " [" + rid + "] -> " + (int)resp.StatusCode + " in " + (int)(DateTime.UtcNow - started).TotalMilliseconds + " ms");
                    return text;
                }
            }
            catch (WebException we)
            {
                int status = 0;
                string text = null;
                var r = we.Response as HttpWebResponse;
                if (r != null)
                {
                    status = (int)r.StatusCode;
                    try { using (var sr = new StreamReader(r.GetResponseStream(), Encoding.UTF8)) text = sr.ReadToEnd(); } catch { }
                }
                string why = r != null ? "HTTP " + status : "connection problem (" + we.Status + ")";
                var hx = new HelperException(method + " " + path + " failed: " + why + ": " + we.Message + (text != null ? " | body: " + Trim(text, 300) : ""),
                    url, rid, status, text, we);
                LastError = hx.Message;
                throw hx;
            }
            catch (HelperException hx) { LastError = hx.Message; throw; }
            catch (Exception e)
            {
                var hx = new HelperException(method + " " + path + " failed: " + e.GetType().Name + ": " + e.Message, url, rid, 0, null, e);
                LastError = hx.Message;
                throw hx;
            }
        }

        static string Trim(string s, int n) { return s.Length <= n ? s : s.Substring(0, n) + "..."; }

        public static HealthInfo Health()
        {
            string rid;
            var root = Json.Parse(Request("GET", "/health", null, 4000, out rid)) as Dictionary<string, object>;
            if (root == null) throw new HelperException("health: unexpected response", "/health", rid, 0, null);
            var info = new HealthInfo();
            object v;
            if (root.TryGetValue("version", out v)) info.Version = v as string;
            if (root.TryGetValue("protocol", out v) && v is double) info.Protocol = (int)(double)v;
            var inst = root.TryGetValue("installed", out v) ? v as List<object> : null;
            if (inst != null) foreach (object o in inst) { var s = o as string; if (s != null) info.Installed.Add(s); }
            var st = root.TryGetValue("installing", out v) ? v as Dictionary<string, object> : null;
            if (st != null)
            {
                var parts = new List<string>();
                foreach (var kv in st) parts.Add(kv.Key + "=" + kv.Value);
                info.InstallState = string.Join(", ", parts.ToArray());
            }
            if (info.Protocol != ExpectedProtocol)
                AtLog.Warn("helper-client", "helper protocol " + info.Protocol + " differs from the mod's " + ExpectedProtocol + " (helper " + info.Version + "). Update the helper or the mod.");
            return info;
        }

        /// <summary>Is there a model path for src->tgt (installed, or available to download)?</summary>
        public static SupportInfo Support(string src, string tgt)
        {
            string rid, raw;
            try { raw = Request("GET", "/support?source=" + Uri.EscapeDataString(src) + "&target=" + Uri.EscapeDataString(tgt), null, 30000, out rid); }
            catch (HelperException hx)
            {
                if (hx.Status == 404 || hx.Status == 400) return new SupportInfo { Known = false };   // older helper without /support
                throw;
            }
            var root = Json.Parse(raw) as Dictionary<string, object>;
            var info = new SupportInfo();
            object v;
            if (root == null) return info;
            info.Known = root.TryGetValue("known", out v) && v is bool && (bool)v;
            info.Supported = root.TryGetValue("supported", out v) && v is bool && (bool)v;
            info.Installed = root.TryGetValue("installed", out v) && v is bool && (bool)v;
            var dl = root.TryGetValue("download", out v) ? v as List<object> : null;
            if (dl != null) foreach (object o in dl) { var s = o as string; if (s != null) info.Download.Add(s); }
            return info;
        }

        public static void StartModelInstall(string source, string target)
        {
            string rid;
            Request("POST", "/install", "{\"source\":" + Json.Quote(source) + ",\"target\":" + Json.Quote(target) + "}", 5000, out rid);
            AtLog.Info("helper-client", "asked helper to install model " + source + "->" + target + " [" + rid + "]");
        }

        /// <summary>Translate a batch. Returns translations in the same order; throws HelperException (with request id) on failure.</summary>
        public static List<string> Translate(string source, string target, IList<string> texts, out string requestId)
        {
            string body = "{\"source\":" + Json.Quote(source) + ",\"target\":" + Json.Quote(target) + ",\"texts\":" + Json.StringArray(texts) + "}";
            string raw = Request("POST", "/translate", body, 180000, out requestId);
            var root = Json.Parse(raw) as Dictionary<string, object>;
            object v;
            var list = root != null && root.TryGetValue("translations", out v) ? v as List<object> : null;
            if (list == null || list.Count != texts.Count)
                throw new HelperException("translate: expected " + texts.Count + " translations, got " + (list == null ? "none" : list.Count.ToString()),
                    "/translate", requestId, 200, Trim(raw, 300));
            var res = new List<string>(list.Count);
            foreach (object o in list) res.Add(o as string ?? "");
            return res;
        }

        public static string Describe()
        {
            return "port=" + Port() + " dataDir=" + Paths.DataDir + " lastOk=" + (LastSuccess ?? "never") + " lastError=" + (LastError ?? "none");
        }
    }
}
