using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading;
using HarmonyLib;
using UnityEngine;
using Verse;

namespace AutoTranslate
{
    /// <summary>
    /// Per-mod translation pipeline.
    ///  1. For every installed non-official mod build a ModState and a coverage index of what is ALREADY translated
    ///     (mod's own files, or another mod acting as translator; the latter prevails).
    ///  2. Decide per string (see Decide) what to do according to the mod's mode.
    ///  3. Apply cache hits immediately, translate the rest in a worker thread through the helper (batches never mix mods).
    ///  4. Any problem is charged to the one mod involved; after ModState.FailureLimit problems that mod alone is switched
    ///     off, its changes are reverted, and the reason is saved.
    /// </summary>
    public static class Pipeline
    {
        const int BatchMax = 40, BatchChars = 6000, ApplyPerFrame = 300;

        public sealed class Binding { public Action<string> Apply; public Action Revert; public bool Applied; }

        public sealed class Item
        {
            public ModState Mod;
            public string Source, Origin;
            public string SourceLang;                 // detected language of Source
            public string Text;                       // the translation currently assigned (kept while translations are switched off)
            public bool Preset;                       // Source is already the final text (taken from a translation file)
            public List<Binding> Bindings = new List<Binding>();
        }

        // Def fields we translate (string fields with exactly these names).
        public static readonly string[] DefFieldNames =
        {
            "label", "description", "labelShort", "labelPlural", "labelNoun", "jobString", "reportString",
            "gerundLabel", "pawnLabel", "adjective", "labelMale", "labelFemale"
        };

        public static int RetryDelayMs = 2000, PollMs = 5000;   // tests lower these
        public static string Target, TargetHow;
        static Dictionary<string, bool> pairState = new Dictionary<string, bool>();   // "src>tgt" -> usable (worker thread only)
        public static bool GameIsTarget;
        public static volatile string StatusKey = "notstarted";
        public static volatile object[] StatusArgs = new object[0];
        /// <summary>For logs and diagnostics (stable, English-free): "key(args)".</summary>
        public static string Status { get { return StatusKey + (StatusArgs.Length > 0 ? "(" + string.Join(", ", Array.ConvertAll(StatusArgs, a => Convert.ToString(a))) + ")" : ""); } }
        /// <summary>For the screen: in the player's language.</summary>
        public static string StatusUi { get { return T.Get("AT_St_" + StatusKey, StatusArgs); } }
        static void SetStatus(string key, params object[] args) { StatusArgs = args; StatusKey = key; }
        public static volatile bool WorkerFinished = true;   // background work of the current run is over (tests and UI use it)
        public static volatile bool Suspended;       // session-only switch: translations OFF to compare with the originals
        static bool snapDefs, snapKeyed, snapMeta; static string snapLang;   // settings as of the last Start, to know when a reload is needed
        public static volatile bool NeedsReload;
        public static List<ModState> Mods = new List<ModState>();
        public static int Found, FromCache, Translated, Failed, Applied;

        static readonly Dictionary<string, ModState> byId = new Dictionary<string, ModState>(StringComparer.OrdinalIgnoreCase);
        static TranslationCache cache;
        static CoverageIndex index;
        public static CoverageIndex Index { get { return index; } }
        static readonly Dictionary<string, Item> items = new Dictionary<string, Item>();
        static readonly List<Item> presets = new List<Item>();
        static Dictionary<ModState, List<Item>> pendingByMod = new Dictionary<ModState, List<Item>>();
        sealed class Result { public Item It; public string Text; public int Gen; }
        static ConcurrentQueue<Result> results = new ConcurrentQueue<Result>();
        static readonly ConcurrentQueue<ModState> disabledQueue = new ConcurrentQueue<ModState>();
        static readonly Dictionary<Type, FieldInfo[]> fieldCache = new Dictionary<Type, FieldInfo[]>();
        static FieldInfo cachedLabelCapField;
        static bool resetFieldWarned, quitHooked;
        static int generation;
        static volatile bool stop;
        static string markerMod;
        static bool started;

        // ------------------------------------------------------------------ start

        public static void Start()
        {
            var sw = Stopwatch.StartNew();
            generation++;
            WorkerFinished = true;
            ResetState();
            var s = AutoTranslateMod.Settings;
            if (!started) { started = true; Diagnostics.LogSessionHeader(); }
            if (s == null || !s.enabled) { SetStatus("disabled"); AtLog.Info("pipeline", Status); return; }

            Target = LangMap.ResolveTarget(s.language, out TargetHow);
            AtLog.Info("pipeline", "target language: " + (Target ?? "none") + " (" + TargetHow + ")");
            if (Target == null) { SetStatus("idle"); return; }
            GameIsTarget = LangMap.FromGameLanguage(LanguageDatabase.activeLanguage) == Target;

            cache = new TranslationCache(Target);
            if (!quitHooked) { Application.quitting += OnQuit; quitHooked = true; }

            BuildRegistry(s);
            var scan = new List<ModContentPack>();
            foreach (ModContentPack m in LoadedModManager.RunningModsListForReading) if (!IsOfficialOrSelf(m)) scan.Add(m);   // includes this mod: its own pt/en files count as native
            index = CoverageIndex.Build(Target, scan, DefFieldNames);

            foreach (ModState ms in Mods)
            {
                ModState m = ms;
                if (!m.Active) continue;
                if (s.translateDefs && !m.IsSelf) Safe.Run("harvest-defs", () => HarvestDefs(m), "mod " + m.Id);
                if (s.translateMeta && !m.IsSelf) Safe.Run("harvest-meta", () => HarvestMeta(m), "mod " + m.Id);
                // a harvest crash for one mod must not affect others: HarvestDefs reports per mod itself
            }
            if (s.translateKeyed) Safe.Run("harvest-keyed", HarvestKeyed);
            Safe.Run("language-detect", AssignLanguages);

            ApplyInitial();
            LogModTable();
            AtLog.Info("pipeline", "start finished in " + sw.ElapsedMilliseconds + " ms. " + Describe());

            snapLang = s.language; snapDefs = s.translateDefs; snapKeyed = s.translateKeyed; snapMeta = s.translateMeta; NeedsReload = false;
            int pend = 0;
            foreach (var l in pendingByMod.Values) pend += l.Count;
            if (pend > 0) SetStatus("translating", pend); else SetStatus("ready");
            int gen = generation;
            bool need = pend > 0;
            var mods = Mods; var pending = pendingByMod;      // this run's collections (a reload replaces them)
            WorkerFinished = false;
            var t = new Thread(() => WorkerMain(gen, need, mods, pending)) { IsBackground = true, Name = "AutoTranslate-Worker" };
            t.Start();
        }

        static void ResetState()
        {
            Mods = new List<ModState>(); byId.Clear(); items.Clear(); presets.Clear();
            pendingByMod = new Dictionary<ModState, List<Item>>(); pairState = new Dictionary<string, bool>();
            ModState d; while (disabledQueue.TryDequeue(out d)) { }
            results = new ConcurrentQueue<Result>();
            Found = FromCache = Translated = Failed = Applied = 0;
            replaced = null; replacedTried = false; markerMod = null; stop = false;
            SetStatus("starting");
        }

        static void OnQuit()
        {
            stop = true;
            Safe.Run("cache", () => { if (cache != null) cache.SaveDirty(); });
            StateStore.ClearApplying();
            AtLog.Info("pipeline", "game quitting. Final: " + Describe());
        }

        // ------------------------------------------------------------------ registry

        static bool Flag(object o, string name)
        {
            try
            {
                var t = o.GetType();
                var p = t.GetProperty(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (p != null) return (bool)p.GetValue(o, null);
                var f = t.GetField(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (f != null) return (bool)f.GetValue(o);
            }
            catch (Exception e) { AtLog.Warn("registry", "cannot read " + name + " on " + o.GetType().Name + ": " + e.Message); }
            return false;
        }

        static bool IsSelf(ModContentPack m)
        {
            return string.Equals(m.PackageIdPlayerFacing, AutoTranslateMod.PackageId, StringComparison.OrdinalIgnoreCase);
        }

        static bool IsOfficialOrSelf(ModContentPack m)
        {
            return Flag(m, "IsCoreMod") || Flag(m, "IsOfficialMod");
        }

        static void BuildRegistry(AtSettings s)
        {
            string stale = StateStore.TakeStaleApplying();
            foreach (ModContentPack m in LoadedModManager.RunningModsListForReading)
            {
                if (IsOfficialOrSelf(m) || byId.ContainsKey(m.PackageIdPlayerFacing)) continue;
                var ms = new ModState { Pack = m, Id = m.PackageIdPlayerFacing, Name = m.Name, IsSelf = IsSelf(m) };
                string mode;
                if (s.modModes != null && s.modModes.TryGetValue(ms.Id, out mode) && Array.IndexOf(ModMode.All, mode) >= 0) ms.Mode = mode;
                string reason = StateStore.GetDisabledReason(ms.Id);
                if (reason != null) { ms.AutoDisabled = true; ms.DisableReason = reason + " (from a previous session)"; }
                Mods.Add(ms);
                byId[ms.Id] = ms;
            }
            Mods.Sort((a, b) => string.Compare(a.Name, b.Name, StringComparison.OrdinalIgnoreCase));
            if (stale != null)
            {
                ModState sm;
                if (byId.TryGetValue(stale, out sm) && !sm.AutoDisabled)
                    sm.Disable("the previous game session ended while this mod's translation was being applied (suspected cause)", null);
                else AtLog.Warn("registry", "previous session ended while applying '" + stale + "', which is not tracked/active now");
            }
            AtLog.Info("registry", Mods.Count + " mod(s) tracked");
        }

        static ModState StateOf(ModContentPack pack)
        {
            ModState ms;
            return pack != null && byId.TryGetValue(pack.PackageIdPlayerFacing, out ms) && ReferenceEquals(ms.Pack, pack) ? ms : null;
        }

        // ------------------------------------------------------------------ decide

        static bool Eligible(string v, ModState ms)
        {
            if (string.IsNullOrWhiteSpace(v) || v.Length > 20000) return false;
            int letters = 0;
            foreach (char c in v) if (char.IsLetter(c)) letters++;
            return letters >= 2;      // language is decided afterwards (AssignLanguages)
        }

        /// <summary>Decide each mod's source language(s): per string for non-Latin scripts, per mod for Latin-script text.
        /// Strings already in the target language are dropped (nothing to translate).</summary>
        static void AssignLanguages()
        {
            var settings = AutoTranslateMod.Settings;
            var byMod = new Dictionary<ModState, List<KeyValuePair<string, Item>>>();
            foreach (var kv in items)
            {
                List<KeyValuePair<string, Item>> l;
                if (!byMod.TryGetValue(kv.Value.Mod, out l)) byMod[kv.Value.Mod] = l = new List<KeyValuePair<string, Item>>();
                l.Add(kv);
            }
            var drop = new List<string>();
            foreach (var entry in byMod)
            {
                ModState ms = entry.Key;
                string over;
                ms.SourceOverride = settings.modSource != null && settings.modSource.TryGetValue(ms.Id, out over) && !string.IsNullOrEmpty(over) ? over : null;
                if (ms.SourceOverride == null)
                {
                    var texts = new List<string>();
                    foreach (var kv in entry.Value) texts.Add(kv.Value.Source);
                    string detail;
                    ms.LatinLang = LangDetect.LatinLang(texts, out ms.LatinConfident, out detail);
                    AtLog.Info("language-detect", "mod '" + ms.Id + "': Latin-script texts look " + ms.LatinLang
                        + (ms.LatinConfident ? " (confident" : " (weak evidence, assuming English as default") + "; " + detail + ")");
                }
                foreach (var kv in entry.Value)
                {
                    Item it = kv.Value;
                    string lang = ms.SourceOverride ?? LangDetect.ScriptLang(it.Source) ?? ms.LatinLang;
                    if (lang == Target) { ms.AlreadyTarget++; drop.Add(kv.Key); continue; }
                    it.SourceLang = lang;
                    int n; ms.SourceCounts.TryGetValue(lang, out n); ms.SourceCounts[lang] = n + 1;
                }
            }
            foreach (string k in drop) items.Remove(k);
        }

        /// <summary>A "translation" entry that is not one: the same text as the original (the game's translation-writing tool copies
        /// the English text into the files), or text confidently in another language than the target. Such entries must not stop us
        /// from translating (this is why a mod with an untranslated Portuguese folder stayed in English).</summary>
        static bool IsPlaceholder(ModState ms, Cover c, string original)
        {
            string v = TranslationCache.Norm(c.Value);
            if (original != null && v == TranslationCache.Norm(original)) return true;
            string known;
            if (original == null && cache != null && cache.TryGet(ms.Id, c.Value, out known)) return true;   // already translated as an ORIGINAL text before (e.g. by the helper's bulk run)
            string sl = LangDetect.ScriptLang(v);
            if (sl != null) return sl != Target;
            bool conf; string det;
            string lat = LangDetect.LatinLang(new[] { v }, out conf, out det);
            return conf && lat != Target;
        }

        /// <summary>The heart of the "only translate what has no support" rule, per string and per mode.</summary>
        static void Decide(ModState ms, List<Cover> covers, Func<string> english, string origin, Binding b)
        {
            if (covers != null && covers.Count > 0)
            {
                string orig = english();
                var real = new List<Cover>();
                Cover lastPlaceholder = null;
                foreach (Cover c in covers) { if (!ms.IsSelf && IsPlaceholder(ms, c, orig)) lastPlaceholder = c; else real.Add(c); }   // (this mod's own screen texts are exempt: "Mods" is "Mods" in Portuguese too)
                if (lastPlaceholder != null)
                {
                    ms.Placeholders++;
                    if (orig == null) orig = lastPlaceholder.Value;        // the placeholder IS the original text
                    string o = orig;
                    english = () => o;
                }
                covers = real.Count > 0 ? real : null;
            }
            Cover own = null, third = null, effective = null;
            if (covers != null && covers.Count > 0)
            {
                effective = covers[covers.Count - 1];                // what RimWorld uses (last loaded wins)
                foreach (Cover c in covers) { if (ReferenceEquals(c.Provider, ms.Pack)) own = c; else third = c; }
            }
            switch (ms.Mode)
            {
                case ModMode.Off:
                    return;
                case ModMode.Native:
                    if (own != null) UseCover(ms, own, effective, origin, b);
                    return;
                case ModMode.Third:
                    if (third != null) UseCover(ms, third, effective, origin, b);
                    return;
                case ModMode.Mine:
                    {
                        string en = english();
                        if (en == null) { ms.EnglishUnavailable++; return; }
                        QueueTranslation(ms, en, origin, b);
                        return;
                    }
                default: // Auto: own/third-party translation if any (third-party prevails by load order), else translate
                    if (effective != null) { UseCover(ms, effective, effective, origin, b); return; }
                    QueueTranslation(ms, english(), origin, b);
                    return;
            }
        }

        static void UseCover(ModState ms, Cover chosen, Cover effective, string origin, Binding b)
        {
            if (ReferenceEquals(chosen.Provider, ms.Pack)) ms.Native++;
            else { ms.Third++; ms.CountProvider(chosen.Provider.Name); }
            // The game already shows 'effective' when it runs in the target language; only act when we must change it.
            if (!GameIsTarget || !ReferenceEquals(chosen, effective))
            {
                var it = new Item { Mod = ms, Source = chosen.Value, Origin = origin, Preset = true };
                it.Bindings.Add(b);
                presets.Add(it);
            }
        }

        static void QueueTranslation(ModState ms, string source, string origin, Binding b)
        {
            if (!Eligible(source, ms)) return;
            string k = ms.Id + "\u0000" + source;
            Item it;
            if (!items.TryGetValue(k, out it)) items[k] = it = new Item { Mod = ms, Source = source, Origin = origin };
            it.Bindings.Add(b);
        }

        // ------------------------------------------------------------------ harvest

        static FieldInfo[] FieldsFor(Type t)
        {
            FieldInfo[] r;
            if (fieldCache.TryGetValue(t, out r)) return r;
            var list = new List<FieldInfo>();
            foreach (string n in DefFieldNames)
            {
                for (Type c = t; c != null && c != typeof(object); c = c.BaseType)
                {
                    var f = c.GetField(n, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly);
                    if (f != null && f.FieldType == typeof(string)) { list.Add(f); break; }
                }
            }
            return fieldCache[t] = list.ToArray();
        }

        static void HarvestDefs(ModState ms)
        {
            int defs = 0;
            foreach (Def def in ms.Pack.AllDefs)
            {
                Def d = def;
                defs++;
                try
                {
                    foreach (FieldInfo f0 in FieldsFor(d.GetType()))
                    {
                        FieldInfo f = f0;
                        string cur = f.GetValue(d) as string;
                        if (string.IsNullOrWhiteSpace(cur)) continue;
                        var covers = index.ForDefField(d.GetType(), d.defName, f.Name);
                        string orig = cur;
                        var b = new Binding
                        {
                            Apply = t => { f.SetValue(d, t); ResetDefCaches(d); },
                            Revert = () => { f.SetValue(d, orig); ResetDefCaches(d); }
                        };
                        Func<string> english = () => covers != null && GameIsTarget ? ReplacedEnglish(d.GetType(), d.defName, f.Name) : cur;
                        Decide(ms, covers, english, d.GetType().Name + ":" + d.defName + "." + f.Name, b);
                        if (!ms.Active) return;
                    }
                }
                catch (Exception e) { ms.Fail("harvest", "def " + d.GetType().Name + ":" + d.defName, e); if (!ms.Active) return; }
            }
            AtLog.Debug("harvest-defs", "mod " + ms.Id + ": scanned " + defs + " defs");
        }

        static void ResetDefCaches(Def d)
        {
            if (cachedLabelCapField == null && !resetFieldWarned)
            {
                cachedLabelCapField = AccessTools.Field(typeof(Def), "cachedLabelCap");
                if (cachedLabelCapField == null)
                {
                    resetFieldWarned = true;
                    AtLog.Warn("apply", "Def.cachedLabelCap not found in this game version; capitalised labels may stay in English until restart");
                }
            }
            if (cachedLabelCapField != null) cachedLabelCapField.SetValue(d, null);
        }

        // English text of a def field that the game already replaced by a translation (needed for "My translation" over an existing one).
        static Dictionary<string, string> replaced;
        static bool replacedTried;

        static string ReplacedEnglish(Type defClass, string defName, string field)
        {
            if (!replacedTried) { replacedTried = true; replaced = BuildReplaced(); }
            if (replaced == null) return null;
            for (Type t = defClass; t != null && t != typeof(object); t = t.BaseType)
            {
                string v;
                if (replaced.TryGetValue(CoverageIndex.DefKey(t.Name, defName, field), out v)) return v;
            }
            return null;
        }

        static Dictionary<string, string> BuildReplaced()
        {
            try
            {
                var f = AccessTools.Field(typeof(LoadedLanguage), "defInjections");
                var pkgs = f != null ? f.GetValue(LanguageDatabase.activeLanguage) as IEnumerable : null;
                if (pkgs == null) { AtLog.Warn("harvest-defs", "LoadedLanguage.defInjections not found: cannot recover English text under an existing translation"); return null; }
                var map = new Dictionary<string, string>();
                foreach (object pkg in pkgs)
                {
                    var tf = pkg.GetType().GetField("defType", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                    var inf = pkg.GetType().GetField("injections", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                    var type = tf != null ? tf.GetValue(pkg) as Type : null;
                    var dict = inf != null ? inf.GetValue(pkg) as IDictionary : null;
                    if (type == null || dict == null) { AtLog.Warn("harvest-defs", "DefInjectionPackage layout unexpected; English recovery unavailable"); return null; }
                    foreach (DictionaryEntry e in dict)
                    {
                        string path = e.Key as string;
                        var rf = e.Value.GetType().GetField("replacedString", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                        string rs = rf != null ? rf.GetValue(e.Value) as string : null;
                        if (path == null || string.IsNullOrEmpty(rs)) continue;
                        int dot = path.IndexOf('.');
                        if (dot > 0) map[CoverageIndex.DefKey(type.Name, path.Substring(0, dot), path.Substring(dot + 1))] = rs;
                    }
                }
                AtLog.Info("harvest-defs", "recovered English text for " + map.Count + " already-translated def fields");
                return map;
            }
            catch (Exception e) { AtLog.Warn("harvest-defs", "English recovery failed", e); return null; }
        }

        static string Norm(string p) { return p.Replace('\\', '/'); }

        static void HarvestKeyed()
        {
            FieldInfo dictField = AccessTools.Field(typeof(LoadedLanguage), "keyedReplacements");
            if (dictField == null) { AtLog.Error("harvest-keyed", "LoadedLanguage.keyedReplacements not found: Keyed translation unavailable in this game version"); return; }
            var active = dictField.GetValue(LanguageDatabase.activeLanguage) as IDictionary;
            var dflt = dictField.GetValue(LanguageDatabase.defaultLanguage) as IDictionary;
            if (active == null || dflt == null) { AtLog.Error("harvest-keyed", "keyedReplacements dictionaries are null (language data not loaded yet?)"); return; }

            var roots = new List<KeyValuePair<string, ModContentPack>>();
            foreach (ModContentPack m in LoadedModManager.RunningModsListForReading)
                roots.Add(new KeyValuePair<string, ModContentPack>(Norm(m.RootDir) + "/", m));
            roots.Sort((a, b) => b.Key.Length.CompareTo(a.Key.Length));

            bool sameDict = ReferenceEquals(active, dflt);
            int seen = 0, noOwner = 0, official = 0;
            FieldInfo valueF = null, pathF = null;
            foreach (DictionaryEntry e in dflt)
            {
                var key = e.Key as string;
                object obj = e.Value;
                if (key == null || obj == null) continue;
                if (valueF == null)
                {
                    valueF = obj.GetType().GetField("value", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                    pathF = obj.GetType().GetField("fileSourceFullPath", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                    if (valueF == null || pathF == null)
                    {
                        AtLog.Error("harvest-keyed", "KeyedReplacement fields not found (value=" + (valueF != null) + ", fileSourceFullPath=" + (pathF != null) + "); Keyed translation disabled");
                        return;
                    }
                }
                seen++;
                string english = valueF.GetValue(obj) as string;
                string path = pathF.GetValue(obj) as string;
                ModContentPack owner = null;
                if (!string.IsNullOrEmpty(path))
                {
                    string np = Norm(path);
                    foreach (var r in roots) if (np.StartsWith(r.Key, StringComparison.OrdinalIgnoreCase)) { owner = r.Value; break; }
                }
                if (owner == null) { noOwner++; continue; }
                ModState ms = StateOf(owner);
                if (ms == null) { official++; continue; }
                if (!ms.Active) continue;

                var covers = index.ForKey(key);
                if (Target == "en" && covers != null)
                {
                    ModContentPack own = owner;
                    covers = covers.FindAll(c => !ReferenceEquals(c.Provider, own));   // its own English folder is the source text
                    if (covers.Count == 0) covers = null;
                }
                if (covers == null && !sameDict && active.Contains(key)) continue;   // provided by something we cannot attribute
                string k = key; object o = obj; FieldInfo vf = valueF;
                object prev = !sameDict && active.Contains(key) ? active[key] : null;
                string origValue = english;
                var b = new Binding
                {
                    Apply = t => SetKeyed(active, k, o, vf, t, sameDict),
                    Revert = () =>
                    {
                        if (sameDict) vf.SetValue(o, origValue);
                        else if (prev != null) active[k] = prev;
                        else active.Remove(k);
                    }
                };
                try { Decide(ms, covers, () => english, "Keyed:" + key, b); }
                catch (Exception ex) { ms.Fail("harvest", "keyed " + key, ex); }
            }
            AtLog.Info("harvest-keyed", "examined " + seen + " keyed entries; " + official + " official, " + noOwner + " with no identifiable mod owner");
        }

        static void SetKeyed(IDictionary active, string key, object original, FieldInfo valueField, string translated, bool sameDict)
        {
            if (sameDict) { valueField.SetValue(original, translated); return; }
            object clone = typeof(object).GetMethod("MemberwiseClone", BindingFlags.NonPublic | BindingFlags.Instance).Invoke(original, null);
            valueField.SetValue(clone, translated);
            active[key] = clone;
        }

        // ------------------------------------------------------------------ apply (game thread)

        static void ApplyInitial()
        {
            var byMod = new Dictionary<ModState, List<Item>>();
            foreach (Item it in presets) AddTo(byMod, it);
            foreach (Item it in items.Values) AddTo(byMod, it);
            try
            {
                foreach (ModState ms in Mods)
                {
                    List<Item> list;
                    if (!byMod.TryGetValue(ms, out list)) continue;
                    SetMarker(ms);
                    foreach (Item it in list)
                    {
                        if (!ms.Active) break;
                        if (it.Preset) { ms.ProviderApplied++; ApplyItem(it, it.Source); continue; }
                        string tr;
                        if (cache.TryGet(ms.Id, it.Source, out tr)) { ms.FromCache++; FromCache++; ApplyItem(it, tr); }
                        else
                        {
                            ms.Found++;
                            List<Item> p;
                            if (!pendingByMod.TryGetValue(ms, out p)) pendingByMod[ms] = p = new List<Item>();
                            p.Add(it);
                        }
                    }
                    ms.Found += ms.FromCache;     // Found = every string of this mod that needed our translation
                }
            }
            finally { SetMarker(null); }
            foreach (ModState ms in Mods) Found += ms.Found;
        }

        static void AddTo(Dictionary<ModState, List<Item>> d, Item it)
        {
            List<Item> l;
            if (!d.TryGetValue(it.Mod, out l)) d[it.Mod] = l = new List<Item>();
            l.Add(it);
        }

        static void SetMarker(ModState ms)
        {
            string id = ms == null ? null : ms.Id;
            if (id == markerMod) return;
            markerMod = id;
            if (id == null) StateStore.ClearApplying(); else StateStore.SetApplying(id);
        }

        static void ApplyItem(Item it, string text)
        {
            ModState ms = it.Mod;
            it.Text = text;
            if (Suspended && !ms.IsSelf)        // translations are switched OFF: keep the text for when they come back
            {
                if (ms.AppliedSet.Add(it)) ms.AppliedItems.Add(it);
                return;
            }
            bool any = false;
            foreach (Binding b in it.Bindings)
            {
                if (!ms.Active) return;
                try { b.Apply(text); b.Applied = true; any = true; Applied++; ms.Applied++; }
                catch (Exception ex) { ms.Fail("apply", it.Origin + " <- '" + Clip(text, 80) + "'", ex); }
            }
            if (any && ms.AppliedSet.Add(it)) ms.AppliedItems.Add(it);
        }

        /// <summary>Undo every change we made to one mod (game thread).</summary>
        public static void RevertMod(ModState ms)
        {
            int n = 0;
            for (int i = ms.AppliedItems.Count - 1; i >= 0; i--)
                foreach (Binding b in ms.AppliedItems[i].Bindings)
                {
                    if (!b.Applied) continue;
                    Binding bb = b;
                    if (Safe.Run("revert:" + ms.Id, bb.Revert, ms.Id)) n++;
                    b.Applied = false;
                }
            ms.AppliedItems.Clear();
            ms.AppliedSet.Clear();
            ms.PendingRevert = false;
            AtLog.Info("pipeline", "reverted " + n + " change(s) of mod '" + ms.Id + "'");
        }

        public static void NotifyDisabled(ModState ms) { disabledQueue.Enqueue(ms); }

        /// <summary>Called from the settings UI (game thread).</summary>
        public static void SetMode(ModState ms, string mode)
        {
            ms.Mode = mode;
            var s = AutoTranslateMod.Settings;
            if (s.modModes == null) s.modModes = new Dictionary<string, string>();
            if (mode == ModMode.Auto) s.modModes.Remove(ms.Id); else s.modModes[ms.Id] = mode;
            AtLog.Info("settings", "mod '" + ms.Id + "' mode -> " + mode + (mode == ModMode.Off ? " (reverted now)" : " (applies when the settings window closes)"));
            if (mode == ModMode.Off) RevertMod(ms); else NeedsReload = true;
        }

        /// <summary>Force a mod's source language (null/"auto" = detect). Takes effect on next start.</summary>
        public static void SetSourceLang(ModState ms, string code)
        {
            var s = AutoTranslateMod.Settings;
            if (s.modSource == null) s.modSource = new Dictionary<string, string>();
            if (string.IsNullOrEmpty(code) || code == "auto") s.modSource.Remove(ms.Id); else s.modSource[ms.Id] = code;
            AtLog.Info("settings", "mod '" + ms.Id + "' source language -> " + (string.IsNullOrEmpty(code) ? "auto" : code) + " (takes effect on next start)");
        }

        public static void Reenable(ModState ms)
        {
            ms.AutoDisabled = false; ms.DisableReason = null; ms.Failures = 0;
            StateStore.Clear(ms.Id);
            NeedsReload = true;
            AtLog.Info("settings", "mod '" + ms.Id + "' re-enabled (applies when the settings window closes)");
        }

        public static int TargetPollMs = 3000;      // tests lower this
        static int lastPoll;

        /// <summary>The player may change the target language in the translator program while the game runs: notice it and reload.</summary>
        static void PollTarget()
        {
            var s = AutoTranslateMod.Settings;
            if (s == null || !s.enabled || !string.Equals(s.language, "auto", StringComparison.OrdinalIgnoreCase)) return;
            string how;
            string t = LangMap.ResolveTarget("auto", out how);
            if (t != null && t != Target)
            {
                AtLog.Info("pipeline", "target language is now '" + t + "' (" + how + "); reloading");
                Reload();
            }
        }

        public static void Tick()
        {
            int now = Environment.TickCount;
            if (unchecked(now - lastPoll) >= TargetPollMs) { lastPoll = now; Safe.Run("poll", PollTarget); }
            if (disabledQueue.IsEmpty && results.IsEmpty) return;
            try
            {
                ModState dm;
                while (disabledQueue.TryDequeue(out dm)) RevertMod(dm);
                Result kv;
                int n = 0;
                while (n++ < ApplyPerFrame && results.TryDequeue(out kv))
                {
                    if (kv.Gen != generation || !kv.It.Mod.Active) continue;      // stale run, or the mod got switched off meanwhile
                    SetMarker(kv.It.Mod);
                    ApplyItem(kv.It, kv.Text);
                }
                if (results.IsEmpty) SetMarker(null);
            }
            catch (Exception ex) { Safe.Report("apply", ex, "Tick"); }
        }

        // ------------------------------------------------------------------ live switch, reload, support

        /// <summary>Translations OFF/ON without restarting: reverts or re-applies every change (this mod's own screen texts stay).</summary>
        public static void SetSuspended(bool off)
        {
            if (Suspended == off) return;
            Suspended = off;
            int n = 0;
            foreach (ModState ms in Mods)
            {
                if (ms.IsSelf) continue;
                foreach (Item it in ms.AppliedItems)
                    foreach (Binding b in it.Bindings)
                    {
                        Binding bb = b;
                        try
                        {
                            if (off && bb.Applied) { bb.Revert(); bb.Applied = false; n++; }
                            else if (!off && !bb.Applied && it.Text != null && ms.Active) { bb.Apply(it.Text); bb.Applied = true; n++; }
                        }
                        catch (Exception ex) { Safe.Report("suspend:" + ms.Id, ex, (off ? "reverting " : "re-applying ") + it.Origin); }
                    }
            }
            AtLog.Info("pipeline", "translations switched " + (off ? "OFF" : "ON") + " by the player (" + n + " change(s))");
        }

        /// <summary>Undo everything and run the whole pipeline again (new target language, options changed).</summary>
        public static void Reload()
        {
            AtLog.Info("pipeline", "reloading (settings changed)");
            foreach (ModState ms in Mods) RevertMod(ms);
            Start();
        }

        /// <summary>True when the settings now differ from what the running pipeline was started with.</summary>
        public static bool SettingsChangedSinceStart()
        {
            var s = AutoTranslateMod.Settings;
            return NeedsReload || s.language != snapLang || s.translateDefs != snapDefs || s.translateKeyed != snapKeyed || s.translateMeta != snapMeta;
        }

        static HealthInfo HealthOnce()
        {
            try { return HelperClient.Health(); } catch { return null; }
        }

        static void CheckSupportAll(int gen, List<ModState> mods)
        {
            var known = new Dictionary<string, SupportInfo>();
            foreach (ModState ms in mods)
            {
                foreach (string lang in new List<string>(ms.SourceCounts.Keys))
                {
                    if (!Alive(gen)) return;
                    SupportInfo info;
                    if (!known.TryGetValue(lang, out info))
                    {
                        try { info = HelperClient.Support(lang, Target); }
                        catch (Exception e)
                        {
                            AtLog.Warn("worker", "support check " + lang + "->" + Target + " failed: " + e.Message);
                            info = new SupportInfo { Known = false };
                        }
                        known[lang] = info;
                        AtLog.Info("worker", "support " + lang + "->" + Target + ": known=" + info.Known + " supported=" + info.Supported
                            + " installed=" + info.Installed + (info.Download.Count > 0 ? " download=" + string.Join(",", info.Download.ToArray()) : ""));
                    }
                    ms.SetSupport(lang, info);
                }
            }
        }

        // ------------------------------------------------------------------ mod descriptions (Mods screen)

        static bool metaWarned;

        static void HarvestMeta(ModState ms)
        {
            ModMetaData meta = ms.Pack.ModMetaData;
            if (meta == null) return;
            string text = meta.Description;
            if (!Eligible(text, ms)) return;
            var backup = SaveMeta(meta);
            var b = new Binding { Apply = t => SetMetaText(meta, t), Revert = () => RestoreMeta(meta, backup) };
            Decide(ms, null, () => text, "ModMeta:description", b);
        }

        static readonly string[] MetaStringFields = { "description", "descriptionCached" };

        static Dictionary<string, object> SaveMeta(ModMetaData m)
        {
            var d = new Dictionary<string, object>();
            foreach (string n in MetaStringFields)
            {
                FieldInfo f = AccessTools.Field(typeof(ModMetaData), n);
                if (f != null && f.FieldType == typeof(string)) d[n] = f.GetValue(m);
            }
            FieldInfo fv = AccessTools.Field(typeof(ModMetaData), "descriptionsByVersion");
            var dict = fv != null ? fv.GetValue(m) as IDictionary : null;
            if (dict != null)
            {
                var copy = new Dictionary<object, object>();
                foreach (DictionaryEntry e in dict) copy[e.Key] = e.Value;
                d["descriptionsByVersion"] = copy;
            }
            return d;
        }

        static void SetMetaText(ModMetaData m, string text)
        {
            foreach (string n in MetaStringFields)
            {
                FieldInfo f = AccessTools.Field(typeof(ModMetaData), n);
                if (f != null && f.FieldType == typeof(string)) f.SetValue(m, text);
            }
            FieldInfo fv = AccessTools.Field(typeof(ModMetaData), "descriptionsByVersion");
            var dict = fv != null ? fv.GetValue(m) as IDictionary : null;
            if (dict != null)
            {
                var keys = new List<object>();
                foreach (object k in dict.Keys) keys.Add(k);
                foreach (object k in keys) if (dict[k] is string) dict[k] = text;
            }
            if (m.Description != text && !metaWarned)
            {
                metaWarned = true;
                AtLog.Warn("harvest-meta", "the Mods screen still shows the original description for '" + m.PackageId + "': this game version reads it from somewhere else. Descriptions will not be translated.");
            }
        }

        static void RestoreMeta(ModMetaData m, Dictionary<string, object> backup)
        {
            foreach (string n in MetaStringFields)
            {
                FieldInfo f = AccessTools.Field(typeof(ModMetaData), n);
                object v;
                if (f != null && backup.TryGetValue(n, out v)) f.SetValue(m, v);
            }
            FieldInfo fv = AccessTools.Field(typeof(ModMetaData), "descriptionsByVersion");
            var dict = fv != null ? fv.GetValue(m) as IDictionary : null;
            object saved;
            if (dict != null && backup.TryGetValue("descriptionsByVersion", out saved))
                foreach (var kv in (Dictionary<object, object>)saved) dict[kv.Key] = kv.Value;
        }

        // ------------------------------------------------------------------ worker thread

        static void WorkerMain(int gen, bool needTranslation, List<ModState> mods, Dictionary<ModState, List<Item>> pending)
        {
            try
            {
                WorkerBody(gen, needTranslation, mods, pending);
            }
            finally { if (gen == generation) WorkerFinished = true; }
        }

        static void WorkerBody(int gen, bool needTranslation, List<ModState> mods, Dictionary<ModState, List<Item>> pending)
        {
            try
            {
                // Translating needs the helper (wait for it); only checking support must not nag when everything is cached.
                HealthInfo h = needTranslation ? WaitForHelperOnline(gen) : HealthOnce();
                if (h == null)
                {
                    if (!needTranslation) foreach (ModState m in mods) foreach (string l in new List<string>(m.SourceCounts.Keys)) m.SetSupport(l, new SupportInfo { Known = false });
                    return;
                }
                CheckSupportAll(gen, mods);
                if (!needTranslation) { LogModTable(); return; }
                var sw = Stopwatch.StartNew();
                DateTime lastSave = DateTime.UtcNow;
                foreach (ModState ms in mods)
                {
                    List<Item> list;
                    if (!pending.TryGetValue(ms, out list)) continue;
                    // batches never mix mods nor source languages
                    var langs = new List<string>();
                    foreach (Item it in list) if (!langs.Contains(it.SourceLang)) langs.Add(it.SourceLang);
                    foreach (string lang in langs)
                    {
                        if (!ms.Active || !Alive(gen)) break;
                        var group = list.FindAll(i => i.SourceLang == lang);
                        SetStatus("prepmodel", LangNames.Label(lang), LangNames.Label(Target));
                        SupportInfo sup = ms.GetSupport(lang);
                        bool usable = !(sup != null && sup.Known && !sup.Supported) && EnsurePair(lang, gen);
                        if (!usable)
                        {
                            if (!Alive(gen)) break;
                            ms.UnsupportedPair += group.Count;
                            ms.UnsupportedPairs.Add(lang + "->" + Target);
                            AtLog.Error("worker", "no usable model " + lang + "->" + Target + ": " + group.Count + " string(s) of mod '" + ms.Id + "' left untranslated");
                            continue;
                        }
                        int idx = 0;
                        while (idx < group.Count && ms.Active && Alive(gen))
                        {
                            var batch = new List<Item>();
                            int chars = 0;
                            while (idx < group.Count && batch.Count < BatchMax && chars < BatchChars) { batch.Add(group[idx]); chars += group[idx].Source.Length; idx++; }
                            SetStatus("translatingmod", ms.Name, LangNames.Label(lang), LangNames.Label(Target));
                            TranslateBatch(ms, batch, lang, gen);
                            if ((DateTime.UtcNow - lastSave).TotalSeconds > 10) { cache.SaveDirty(); lastSave = DateTime.UtcNow; }
                        }
                    }
                    cache.SaveDirty();   // each mod has its own cache file
                }
                cache.SaveDirty();
                if (Failed > 0) SetStatus("donefail", Failed); else SetStatus("done");
                AtLog.Info("worker", "finished in " + sw.Elapsed.TotalSeconds.ToString("0.0") + " s. " + Describe());
                LogModTable();
            }
            catch (Exception ex)
            {
                SetStatus("crash", ex.GetType().Name + ": " + ex.Message);
                Safe.Report("worker", ex, "worker main loop; " + Describe());
                CrashReporter.WriteReport("worker-crash", ex);
                try { cache.SaveDirty(); } catch { }
            }
        }

        static bool Alive(int gen) { return !stop && gen == generation; }

        /// <summary>Blocks until the helper answers. Returns its health, or null if the session ended.</summary>
        static HealthInfo WaitForHelperOnline(int gen)
        {
            bool warned = false;
            DateTime lastWarn = DateTime.MinValue;
            while (Alive(gen))
            {
                try
                {
                    HealthInfo h = HelperClient.Health();
                    if (warned) AtLog.Info("worker", "helper is online again (v" + h.Version + ")");
                    else AtLog.Info("worker", "helper online: v" + h.Version + ", protocol " + h.Protocol + ", models: " + string.Join(",", h.Installed.ToArray()));
                    return h;
                }
                catch (Exception e)
                {
                    SetStatus("waithelper");
                    if (!warned || (DateTime.UtcNow - lastWarn).TotalMinutes >= 5)
                    {
                        AtLog.Warn("worker", "helper not reachable: " + e.Message + "  -> start the helper (see README). Retrying every 10 s.");
                        warned = true; lastWarn = DateTime.UtcNow;
                    }
                    Thread.Sleep(10000);
                }
            }
            return null;
        }

        /// <summary>Make sure a model for src->Target exists (direct, or through English). Downloads it if needed.
        /// false = this pair cannot be used (no model exists, download failed); the result is remembered.</summary>
        static bool EnsurePair(string src, int gen)
        {
            if (src == Target) return true;
            string key = src + ">" + Target;
            bool known;
            if (pairState.TryGetValue(key, out known)) return known;
            HealthInfo h = WaitForHelperOnline(gen);
            if (h == null) return false;
            if (h.HasPair(src, Target)) return pairState[key] = true;

            AtLog.Info("worker", "model " + src + "->" + Target + " not installed; asking the helper to download it");
            SetStatus("download", LangNames.Label(src), LangNames.Label(Target));
            try { HelperClient.StartModelInstall(src, Target); }
            catch (Exception e) { Safe.Report("worker", e, "starting model install " + key); return pairState[key] = false; }
            DateTime deadline = DateTime.UtcNow.AddMinutes(90);
            while (Alive(gen) && DateTime.UtcNow < deadline)
            {
                Thread.Sleep(PollMs);
                try
                {
                    h = HelperClient.Health();
                    if (h.HasPair(src, Target)) { AtLog.Info("worker", "model " + src + "->" + Target + " installed"); return pairState[key] = true; }
                    if (h.InstallState != null && (h.InstallState.Contains(key + "=error")))
                    {
                        AtLog.Error("worker", "helper reports model install failure: " + h.InstallState + " (details in helper.log in " + Path.Combine(Paths.DataDir, "logs") + ")");
                        return pairState[key] = false;
                    }
                }
                catch (Exception e) { AtLog.Warn("worker", "lost helper while waiting for model: " + e.Message); }
            }
            if (Alive(gen)) AtLog.Error("worker", "model " + key + " not ready after 90 minutes");
            return false;
        }

        // A short text per language so the health probe stays in the source language.
        static readonly Dictionary<string, string> Canary = new Dictionary<string, string>
        {
            {"en","Hello."},{"pt","Olá."},{"es","Hola."},{"fr","Bonjour."},{"de","Hallo."},{"it","Ciao."},{"ru","Привет."},
            {"zh","你好。"},{"ja","こんにちは。"},{"ko","안녕하세요."},{"uk","Привіт."},{"pl","Cześć."},{"tr","Merhaba."},
        };

        /// <summary>Is the translator working at all? Tells "this mod's text is the problem" from "the helper is broken".</summary>
        static bool CanaryOk(string src)
        {
            try
            {
                string text; if (!Canary.TryGetValue(src, out text)) text = "Hello.";
                string rid; var r = HelperClient.Translate(src, Target, new[] { text }, out rid);
                return r.Count == 1 && !string.IsNullOrWhiteSpace(r[0]);
            }
            catch (Exception e) { AtLog.Warn("worker", "canary translation failed: " + e.Message); return false; }
        }

        static void TranslateBatch(ModState ms, List<Item> batch, string src, int gen)
        {
            var texts = new List<string>();
            foreach (Item it in batch) texts.Add(it.Source);
            int reconnects = 0;
            for (int attempt = 1; attempt <= 3 && Alive(gen) && ms.Active; attempt++)
            {
                string rid = "-";
                try
                {
                    List<string> res = HelperClient.Translate(src, Target, texts, out rid);
                    for (int i = 0; i < batch.Count; i++) Accept(ms, batch[i], res[i], rid, gen);
                    return;
                }
                catch (HelperException hx)
                {
                    AtLog.Error("worker", "mod '" + ms.Id + "': batch of " + batch.Count + " (" + src + "->" + Target + ") failed (attempt " + attempt + "/3, request " + hx.RequestId + ", HTTP " + hx.Status
                        + "). First text: '" + Clip(texts[0], 120) + "'", hx);
                    if (hx.Status == 0 && reconnects++ < 20) { attempt--; SetStatus("helperlost"); if (WaitForHelperOnline(gen) == null) return; continue; }
                    if (hx.Status == 409)
                    {
                        pairState.Remove(src + ">" + Target); SetStatus("modelnotready");
                        if (!EnsurePair(src, gen)) return;
                        continue;
                    }
                    Thread.Sleep(RetryDelayMs * attempt);
                }
                catch (Exception ex)
                {
                    Safe.Report("worker", ex, "mod " + ms.Id + ": translating batch of " + batch.Count + ", first text '" + Clip(texts[0], 120) + "'");
                    break;
                }
            }
            if (!Alive(gen) || !ms.Active) return;
            if (batch.Count > 1)
            {
                AtLog.Warn("worker", "mod '" + ms.Id + "': retrying the failed batch one string at a time to isolate the problem");
                foreach (Item it in batch)
                {
                    if (!ms.Active || !Alive(gen)) return;
                    TranslateBatch(ms, new List<Item> { it }, src, gen);
                }
                return;
            }
            // A single string keeps failing. Blame the mod only if the translator itself is healthy.
            if (!CanaryOk(src))
            {
                AtLog.Error("worker", "translator is failing even for a trivial text, so mod '" + ms.Id + "' is NOT blamed; string left untranslated this session");
                SetStatus("unhealthy");
                return;
            }
            Failed++; ms.Failed++;
            ms.Fail("translate", "string from " + batch[0].Origin + " (" + src + "): '" + Clip(batch[0].Source, 300) + "'", null);
        }

        static void Accept(ModState ms, Item it, string translation, string rid, int gen)
        {
            if (gen != generation) return;      // result of a previous run (target changed / reload): drop it
            if (string.IsNullOrWhiteSpace(translation))
            {
                Failed++; ms.Failed++;
                ms.Fail("translate", "[" + rid + "] empty translation for " + it.Origin + ": '" + Clip(it.Source, 200) + "'", null);
                return;
            }
            translation = CleanTranslation(translation);
            cache.Put(ms.Id, it.Source, translation);
            results.Enqueue(new Result { It = it, Text = translation, Gen = gen });
            Interlocked.Increment(ref Translated); ms.Translated++;
            AtLog.Debug("worker", "[" + rid + "] " + it.Origin + ": '" + Clip(it.Source, 60) + "' -> '" + Clip(translation, 60) + "'");
        }

        /// <summary>No SentencePiece markers (the game draws them as "_") and no edge spaces.</summary>
        public static string CleanTranslation(string t)
        {
            return t == null ? null : t.Replace('\u2581', ' ').Trim();
        }

        static string Clip(string s, int n)
        {
            if (s == null) return "";
            s = s.Replace("\n", "\\n");
            return s.Length <= n ? s : s.Substring(0, n) + "...";
        }

        static void LogModTable()
        {
            var sb = new StringBuilder("per-mod summary:");
            foreach (ModState ms in Mods)
                sb.Append("\n  ").Append(ms.Id).Append(" [").Append(ms.Mode).Append("] ").Append(ms.StatusText());
            AtLog.Info("pipeline", sb.ToString());
        }

        public static string Describe()
        {
            return "status='" + Status + "' target=" + (Target ?? "-") + " gameIsTarget=" + GameIsTarget + " mods=" + Mods.Count
                + " found=" + Found + " fromCache=" + FromCache + " translated=" + Translated + " failed=" + Failed + " applied=" + Applied;
        }

        public static void ClearCacheForTarget()
        {
            if (Target != null) TranslationCache.ClearTarget(Target);
        }
    }
}
