using System;
using System.IO;

namespace AutoTranslate
{
    /// <summary>Shared folder used by the helper and the mod (identical on Windows and Linux).</summary>
    public static class Paths
    {
        public const string FolderName = "RimWorldAutoTranslate";

        public static string DataDir
        {
            get
            {
                string baseDir = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
                if (string.IsNullOrEmpty(baseDir))
                {
                    string xdg = Environment.GetEnvironmentVariable("XDG_DATA_HOME");
                    string home = Environment.GetEnvironmentVariable("HOME") ?? ".";
                    baseDir = !string.IsNullOrEmpty(xdg) ? xdg : Path.Combine(home, ".local", "share");
                }
                string o = Environment.GetEnvironmentVariable("RWTRANSLATE_HOME");
                return !string.IsNullOrEmpty(o) ? o : Path.Combine(baseDir, FolderName);
            }
        }

        public static string LogDir { get { return Path.Combine(Path.Combine(DataDir, "logs"), "mod"); } }
        public static string CacheDir { get { return Path.Combine(DataDir, "cache"); } }
        public static string OverridesDir { get { return Path.Combine(DataDir, "overrides"); } }

        public static string SafeFileName(string s)
        {
            foreach (char c in Path.GetInvalidFileNameChars()) s = s.Replace(c, '_');
            return s.Length == 0 ? "_" : s;
        }
    }
}
