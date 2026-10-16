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
        static bool cacheMigrated;

        /// <summary>The saved translations: &lt;data&gt;/translated mods/&lt;lang&gt;/&lt;packageId&gt;.json (called "cache" in older versions: the
        /// old folder is moved, or its files are moved in without overwriting when both exist). The helper program does the same.</summary>
        public static string CacheDir
        {
            get
            {
                string dir = Path.Combine(DataDir, "translated mods");
                if (!cacheMigrated)
                {
                    cacheMigrated = true;
                    try
                    {
                        string old = Path.Combine(DataDir, "cache");
                        if (Directory.Exists(old))
                        {
                            if (!Directory.Exists(dir)) Directory.Move(old, dir);
                            else
                            {
                                foreach (string f in Directory.GetFiles(old, "*", SearchOption.AllDirectories))
                                {
                                    string rel = f.Substring(old.Length).TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
                                    string dst = Path.Combine(dir, rel);
                                    if (File.Exists(dst)) continue;
                                    Directory.CreateDirectory(Path.GetDirectoryName(dst));
                                    File.Move(f, dst);
                                }
                            }
                        }
                    }
                    catch (Exception) { }
                }
                return dir;
            }
        }
        public static string OverridesDir { get { return Path.Combine(DataDir, "overrides"); } }

        public static string SafeFileName(string s)
        {
            foreach (char c in Path.GetInvalidFileNameChars()) s = s.Replace(c, '_');
            return s.Length == 0 ? "_" : s;
        }
    }
}
