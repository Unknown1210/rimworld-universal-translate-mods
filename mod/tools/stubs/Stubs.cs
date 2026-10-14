// COMPILE-CHECK STUBS ONLY. Mirrors the small part of the RimWorld/Unity/Harmony API this mod uses, as
// I understand it. NOT shipped. Passing here proves syntax/type consistency of the mod code, NOT that the
// real game API matches. The real build (AutoTranslate.csproj) references the game's own DLLs.
using System;
using System.Collections.Generic;
using System.Reflection;

namespace UnityEngine
{
    public struct Vector2 { public float x, y; }
    public struct Rect { public float x, y, width, height; public Rect(float x, float y, float w, float h) { this.x = x; this.y = y; width = w; height = h; } }
    public enum LogType { Error, Assert, Warning, Log, Exception }
    public enum SystemLanguage { English, Portuguese, Spanish }
    public enum RuntimePlatform { WindowsPlayer, LinuxPlayer }
    public static class GUIUtility { public static string systemCopyBuffer { get; set; } public static int keyboardControl { get { return 0; } } }
    public enum KeyCode { None, Tab, Escape, T, F1, LeftShift, RightShift, LeftControl, RightControl, LeftAlt, RightAlt }
    public enum EventType { Layout, Repaint, KeyDown, Used }
    public class Event { public static Event current; public EventType type; public KeyCode keyCode; public bool shift, control, alt; public void Use() { type = EventType.Used; } }
    public static class Input { public static bool GetKeyDown(KeyCode k) { return false; } public static bool GetKey(KeyCode k) { return false; } }
    public static class Application
    {
        public delegate void LogCallback(string condition, string stackTrace, LogType type);
        public static event LogCallback logMessageReceivedThreaded;
        public static event Action quitting;
        public static string unityVersion { get { return "2022"; } }
        public static RuntimePlatform platform { get { return RuntimePlatform.WindowsPlayer; } }
        public static SystemLanguage systemLanguage { get { return SystemLanguage.English; } }
        public static void OpenURL(string url) { }
    }
}

namespace HarmonyLib
{
    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Method, AllowMultiple = true)]
    public class HarmonyPatch : Attribute { public HarmonyPatch(Type t, string m) { } public HarmonyPatch() { } }
    public class Harmony
    {
        public Harmony(string id) { }
        public void PatchAll(Assembly a) { }
        public IEnumerable<MethodBase> GetPatchedMethods() { return new MethodBase[0]; }
    }
    public static class AccessTools
    {
        public static MethodInfo Method(Type t, string name) { return t.GetMethod(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static); }
        public static FieldInfo Field(Type t, string name) { return t.GetField(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static); }
    }
}

namespace RimWorld
{
    public class Designator_Build : Verse.Designator { }
    public static class MessageTypeDefOf { public static Verse.MessageTypeDef SilentInput = new Verse.MessageTypeDef(); }
    public static class VersionControl { public static string CurrentVersionString { get { return "1.6"; } } }
}

namespace Verse
{
    public static class Translator { static string PseudoTranslated(string original) { return "~" + original + "~"; } }
    public static class Messages { public static void Message(string text, MessageTypeDef def, bool historical) { } }
    public class MessageTypeDef { }
    public static class Log { public static void Warning(string s) { } public static void Error(string s) { } }
    public class TaggedString
    {
        string v;
        public static implicit operator TaggedString(string s) { return new TaggedString { v = s }; }
        public override string ToString() { return v; }
    }
    public static class TranslatorFormattedStringExtensions
    {
        static string Look(LoadedLanguage l, string key)
        {
            LoadedLanguage.KeyedReplacement r;
            return l != null && l.keyedReplacements.TryGetValue(key, out r) ? r.value : null;
        }
        public static TaggedString Translate(this string key) { return Look(LanguageDatabase.activeLanguage, key) ?? Look(LanguageDatabase.defaultLanguage, key) ?? key; }
        public static TaggedString Translate(this string key, string arg) { string t = Translate(key).ToString(); return t.Replace("{0}", arg); }
        public static bool CanTranslate(this string key) { return Look(LanguageDatabase.activeLanguage, key) != null || Look(LanguageDatabase.defaultLanguage, key) != null; }
    }
    public enum GameFont { Tiny, Small, Medium }
    public static class Text { public static GameFont Font; }
    public class ModMetaData
    {
        string description = "", descriptionCached = ""; System.Collections.Generic.Dictionary<string, string> descriptionsByVersion = new System.Collections.Generic.Dictionary<string, string>();
        public string PackageId = "";
        public string Name = "";
        public string Description { get { return descriptionCached.Length > 0 ? descriptionCached : description; } }
        public void ForTest(string d) { description = d; descriptionCached = d; descriptionsByVersion["v1.6"] = d; }
    }
    public class StaticConstructorOnStartup : Attribute { }
    public static class Scribe_Values
    {
        public static void Look<T>(ref T value, string label, T defaultValue = default(T)) { }
    }
    public abstract class ModSettings { public abstract void ExposeData(); }
    public class ModAssemblyHandler { public List<System.Reflection.Assembly> loadedAssemblies = new List<System.Reflection.Assembly>(); }
    public abstract class Command { public string defaultLabel, defaultDesc; }
    public abstract class Designator : Command { }
    public class DesignationCategoryDef : Def { public List<Designator> designators = new List<Designator>(); public List<Designator> AllResolvedDesignators { get { return designators; } } }
    public static class DefDatabase<T> where T : Def { public static List<T> list = new List<T>(); public static List<T> AllDefsListForReading { get { return list; } } public static T GetNamedSilentFail(string defName) { return list.Find(x => x.defName == defName); } }
    public class ModContentPack
    {
        public ModAssemblyHandler assemblies = new ModAssemblyHandler();
        public string RootDir, Name, PackageIdPlayerFacing;
        public bool IsCoreMod, IsOfficialMod;
        public List<string> foldersToLoadDescendingOrder;
        public ModMetaData ModMetaData;
        public List<Def> defs = new List<Def>();
        public IEnumerable<Def> AllDefs { get { return defs; } }
    }
    public static class LoadedModManager { public static List<ModContentPack> RunningModsListForReading; }
    public class Def { public bool generated; public string defName, label, description; string cachedLabelCap = "CACHED"; public string CapForTest { get { return cachedLabelCap; } } }
    public class ThingDef : Def { }
    public class RecipeDef : Def { public string jobString; }
    public class LanguageInfo { public string friendlyNameEnglish, friendlyNameNative; }
    public class DefInjectionPackage
    {
        public Type defType;
        public Dictionary<string, DefInjection> injections = new Dictionary<string, DefInjection>();
        public class DefInjection { public string replacedString; }
    }
    public class LoadedLanguage
    {
        public List<DefInjectionPackage> defInjections = new List<DefInjectionPackage>();
        public string folderName;
        public LanguageInfo info;
        public Dictionary<string, KeyedReplacement> keyedReplacements = new Dictionary<string, KeyedReplacement>();
        public class KeyedReplacement { public string key, value, fileSource, fileSourceFullPath; }
    }
    public static class LanguageDatabase { public static LoadedLanguage activeLanguage, defaultLanguage; }
    public abstract class Mod
    {
        public Mod(ModContentPack content) { }
        protected T GetSettings<T>() where T : ModSettings, new() { return new T(); }
        public virtual string SettingsCategory() { return ""; }
        public virtual void DoSettingsWindowContents(UnityEngine.Rect inRect) { }
        public virtual void WriteSettings() { }
    }
    public enum LookMode { Value }
    public static class Scribe_Collections
    {
        public static void Look<K, V>(ref Dictionary<K, V> dict, string label, LookMode keyLook, LookMode valueLook) { }
    }
    public static class GenUI { public static UnityEngine.Rect ContractedBy(this UnityEngine.Rect r, float m) { return new UnityEngine.Rect(r.x + m, r.y + m, r.width - 2 * m, r.height - 2 * m); } }
    public static class Widgets
    {
        public static void Label(UnityEngine.Rect r, string s) { }
        public static bool ButtonText(UnityEngine.Rect r, string s) { return false; }
        public static void CheckboxLabeled(UnityEngine.Rect r, string label, ref bool checkOn) { }
        public static void DrawHighlightIfMouseover(UnityEngine.Rect r) { }
        public static void DrawMenuSection(UnityEngine.Rect r) { }
        public static void DrawLineHorizontal(float x, float y, float length) { }
        public static string TextField(UnityEngine.Rect rect, string text) { return text; }
        public static void BeginScrollView(UnityEngine.Rect outRect, ref UnityEngine.Vector2 pos, UnityEngine.Rect view) { }
        public static void EndScrollView() { }
    }
    public class FloatMenuOption { public FloatMenuOption(string label, Action action) { } }
    public class FloatMenu : Window { public FloatMenu(List<FloatMenuOption> opts) { } }
    public class Listing_Standard
    {
        public bool maxOneColumn;
        public float CurHeight { get { return 0f; } }
        public void Gap(float h) { }
        public void Begin(UnityEngine.Rect r) { }
        public void End() { }
        public void CheckboxLabeled(string label, ref bool checkOn) { }
        public void Label(string s) { }
        public string TextEntry(string t) { return t; }
        public bool ButtonText(string l) { return false; }
        public void GapLine() { }
        public UnityEngine.Rect GetRect(float h) { return new UnityEngine.Rect(0f, 0f, 100f, h); }
    }
    public class Window { }
    public class Dialog_MessageBox : Window
    {
        public static Dialog_MessageBox CreateConfirmation(TaggedString text, Action confirmedAct, bool destructive = false, string title = null) { return null; }
    }
    public class WindowStack { public void Add(Window w) { } }
    public static class Find { public static WindowStack WindowStack; }
    public class Root { public void Update() { } }
}
