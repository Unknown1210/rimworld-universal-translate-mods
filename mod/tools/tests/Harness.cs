using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using AutoTranslate;
using Verse;

public static class Harness
{
    static int fails;
    static void Check(bool ok, string what) { Console.WriteLine((ok ? "PASS " : "FAIL ") + what); if (!ok) fails++; }

    public static int Main()
    {
        string home = Environment.GetEnvironmentVariable("RWTRANSLATE_HOME");
        AtLog.Init(); AtLog.DebugEnabled = true;

        // ---- screen texts when the language files are missing: embedded English, never raw keys
        LanguageDatabase.activeLanguage = new LoadedLanguage { folderName = "English" };
        LanguageDatabase.defaultLanguage = LanguageDatabase.activeLanguage;
        Check(T.Get("AT_BtnOff") == "Turn translations OFF (compare with the original)" && T.Get("AT_Mods", 4) == "Mods (4)", "no language files: falls back to the English text embedded in the DLL");
        Check(T.Get("AT_DoesNotExist") == "AT_DoesNotExist", "unknown key: shown as is (no crash)");

        // ---- Json
        var j = (Dictionary<string, object>)Json.Parse("{\"a\":[\"x\\ny\\u00e9\",1.5,true,null],\"b\":{}}");
        Check(((List<object>)j["a"])[0] as string == "x\nyé", "json parses escapes/unicode");
        Check(Json.Quote("a\"b\\c\n") == "\"a\\\"b\\\\c\\n\"", "json quote");
        try { Json.Parse("{\"a\":"); Check(false, "json rejects truncated"); } catch (FormatException e) { Check(e.Message.Contains("line"), "json error has position: " + e.Message); }

        // ---- LangMap
        Check(LangMap.FromName("Português Brasileiro") == "pt-BR" && LangMap.FromName("Português") == "pt-PT", "LangMap pt-BR / pt-PT native names");
        Check(LangMap.FromName("PortugueseBrazilian") == "pt-BR" && LangMap.FromName("Portuguese") == "pt-PT" && LangMap.FromName("SpanishLatin") == "es", "LangMap folder names");
        Check(LangMap.NormTarget("pt") == "pt-BR" && LangMap.NormTarget("pt_br") == "pt-BR" && LangMap.NormTarget("PT-pt") == "pt-PT" && LangMap.NormTarget("JA") == "ja", "old \"pt\" setting becomes Brazilian Portuguese");
        Check(LangMap.Same("pt", "pt-BR") && LangMap.Same("pb", "pt-PT") && !LangMap.Same("pt-BR", "es") && LangMap.ModelCode("pt-BR") == "pb" && LangMap.ModelCode("pt-PT") == "pt" && LangMap.ModelCode("pt") == "pt", "Portuguese variants: same language, own model codes");
        Check(LangMap.FromName("Klingon") == null, "LangMap unknown");
        {
            string pr = null;
            bool run = Patch_Translator_PseudoTranslated.Prefix("Search and rescue", ref pr);
            Check(!run && pr == "Search and rescue", "developer-mode accent marks: the original text is handed back and the game's method is skipped");
            AutoTranslateMod.Settings = new AtSettings { hidePseudo = false };
            Check(Patch_Translator_PseudoTranslated.Prefix("x", ref pr), "with the option off the game's own method runs");
            AutoTranslateMod.Settings = new AtSettings();
        }

        // ---- LangDetect
        bool conf; string det;
        Check(LangDetect.ScriptLang("铁剑") == "zh" && LangDetect.ScriptLang("こんにちは世界") == "ja" && LangDetect.ScriptLang("안녕하세요") == "ko", "script: zh / ja (kana wins) / ko");
        Check(LangDetect.ScriptLang("Привет мир") == "ru" && LangDetect.ScriptLang("Привіт, їжак") == "uk" && LangDetect.ScriptLang("مرحبا بالعالم") == "ar", "script: ru / uk / ar");
        Check(LangDetect.ScriptLang("Iron sword") == null && LangDetect.ScriptLang("Espada de ferro") == null, "script: Latin text -> null");
        Check(LangDetect.LatinLang(new[] { "The colonist is carrying a heavy weapon that can not be used by you.", "This item will be consumed on use." }, out conf, out det) == "en" && conf, "latin: English");
        Check(LangDetect.LatinLang(new[] { "O colono não pode usar esta arma porque ela é muito pesada para você.", "Esta ação não está disponível." }, out conf, out det) == "pt" && conf, "latin: Portuguese");
        Check(LangDetect.LatinLang(new[] { "El colono no puede usar esta arma porque es demasiado pesada para usted.", "La acción no está disponible, también." }, out conf, out det) == "es" && conf, "latin: Spanish");
        Check(LangDetect.LatinLang(new[] { "Der Kolonist kann diese Waffe nicht benutzen, weil sie für ihn zu schwer ist.", "Die Aktion ist nicht verfügbar." }, out conf, out det) == "de" && conf, "latin: German");
        Check(LangDetect.LatinLang(new[] { "Le colon ne peut pas utiliser cette arme parce qu'elle est trop lourde pour lui.", "Cette action n'est pas disponible." }, out conf, out det) == "fr" && conf, "latin: French");
        Check(LangDetect.LatinLang(new[] { "iron sword", "wooden shield", "steel" }, out conf, out det) == "en" && !conf, "latin: short labels = no evidence -> default English, not confident");

        // ---- Safe circuit breaker
        int calls = 0;
        for (int i = 0; i < 20; i++) Safe.Run("t-area", () => { calls++; throw new InvalidOperationException("boom " + i); }, "ctx-" + i);
        Check(calls == Safe.MaxFailuresPerArea && Safe.IsDisabled("t-area"), "breaker opens after " + Safe.MaxFailuresPerArea + " failures (calls=" + calls + ")");
        Check(Safe.Call("ok-area", () => 5, -1) == 5, "Safe.Call returns value");

        // ---- Cache: corrupt file handling + roundtrip
        var c = new TranslationCache("zz");
        c.Put("m.one", "Hello", "Olá \"q\"\n2");
        Check(c.SaveDirty() == 1, "cache saved");
        var c2 = new TranslationCache("zz"); string tr;
        Check(c2.TryGet("m.one", "Hello", out tr) && tr == "Olá \"q\"\n2", "cache roundtrip incl. escapes");
        File.WriteAllText(Path.Combine(Path.Combine(Paths.CacheDir, "zz"), "m.bad.json"), "{ not json");
        var c3 = new TranslationCache("zz");
        Check(!c3.TryGet("m.bad", "x", out tr), "corrupt cache -> empty, no throw");
        Check(Directory.GetFiles(Path.Combine(Paths.CacheDir, "zz"), "m.bad.json.corrupt-*").Length == 1, "corrupt cache file quarantined");
        Directory.CreateDirectory(Paths.OverridesDir);
        File.WriteAllText(Path.Combine(Paths.OverridesDir, "zz.json"), "{\"entries\":{\"Hello\":\"MANUAL\"}}");
        Check(new TranslationCache("zz").TryGet("m.one", "Hello", out tr) && tr == "MANUAL", "manual override beats cache");

        // ---- HelperClient against the real Python helper
        var h = HelperClient.Health();
        Check(h.Protocol == 2 && h.HasPair("en", "pt-BR") && h.HasPair("zh", "pt-BR") && !h.HasPair("ja", "pt-BR"), "helper health: protocol " + h.Protocol + " models " + string.Join(",", h.Installed.ToArray()));
        string rid;
        var res = HelperClient.Translate("en", "pt-BR", new[] { "Iron sword", "Hit {0} with <b>force</b>" }, out rid);
        Check(res[0] == "Iron sword (pt)" && res[1] == "Hit {0} with <b>force</b> (pt)", "translate keeps markers: " + res[1]);
        try { HelperClient.Translate("en", "pt-BR", new[] { "EXPLODE now" }, out rid); Check(false, "engine failure should throw"); }
        catch (HelperException hx) { Check(hx.Status == 500 && hx.Body.Contains(hx.RequestId), "500 carries request id " + hx.RequestId); }
        try { HelperClient.Translate("en", "xx", new[] { "a" }, out rid); Check(false, "missing model should throw"); }
        catch (HelperException hx) { Check(hx.Status == 409, "missing model -> 409"); }

        // ---- Full pipeline: per-mod rules
        Pipeline.RetryDelayMs = 5;
        Scenario1_GameInTargetLanguage(home);
        Scenario2_GameInEnglish(home);
        Scenario3_Modes(home);
        Scenario4_CrashMarker(home);
        Scenario5_Bidirectional(home);
        Scenario6_LiveSwitchDescriptionsSupport(home);
        Scenario7_ScreenTextsAndCache(home);
        Scenario8_SharedConfigAndHelperCache(home);
        Scenario9_PlaceholderTranslationFiles(home);
        Scenario10_Designators(home);
        Scenario11_TranslationsWrittenWhileGameRuns(home);
        Scenario12_ModListTools(home);
        Scenario13_ReloadsKeepEverythingEnglishAsSource(home);
        Scenario14_GameGeneratedTextsDoNotDecideTheLanguage(home);

        // ---- Crash report + log content
        string crash = CrashReporter.WriteReport("test", new InvalidOperationException("outer", new ArgumentException("inner cause")));
        string ctext = File.ReadAllText(crash);
        foreach (string needle in new[] { "inner cause", "--- environment ---", "safe-areas", "t-area", "--- last log lines ---", "active mods" })
            Check(ctext.Contains(needle), "crash report contains '" + needle + "'");
        string log = File.ReadAllText(AtLog.LogFile);
        Check(log.Contains("[ERROR] [T") && log.Contains("[harvest-defs]") && log.Contains("FAILURE #1 in area 't-area'") && log.Contains("AREA DISABLED"), "session log has levels, areas, failure + breaker entries");
        Console.WriteLine(fails == 0 ? "ALL PASSED" : fails + " FAILED");
        return fails;
    }

    // ---------------------------------------------------------------- scenario helpers
    static void WriteXml(string path, string body)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        File.WriteAllText(path, "<?xml version=\"1.0\" encoding=\"utf-8\"?><LanguageData>" + body + "</LanguageData>");
    }

    sealed class World
    {
        public ModContentPack A, B, C, D, Core;
        public LoadedLanguage En, Pt, Active;
        public ThingDef Sword, Shield, Zh, Covered, Uncovered, Fine, X1, X2, X3, X4;
    }

    // A=a.good (no translation), B=b.partial (own pt for 'Covered'), C=c.provider (third-party pt for A's Shield + A's keyed),
    // D=d.bad (strings that make the translator fail), Core=official.
    static World Build(string home, string tag, bool gameInPt)
    {
        string root = Path.Combine(home, "mods-" + tag);
        var w = new World();
        w.A = new ModContentPack { RootDir = Path.Combine(root, "a"), Name = "Good Mod", PackageIdPlayerFacing = "a.good" };
        w.B = new ModContentPack { RootDir = Path.Combine(root, "b"), Name = "Partial Mod", PackageIdPlayerFacing = "b.partial" };
        w.C = new ModContentPack { RootDir = Path.Combine(root, "c"), Name = "Third Party Translator", PackageIdPlayerFacing = "c.provider" };
        w.D = new ModContentPack { RootDir = Path.Combine(root, "d"), Name = "Bad Mod", PackageIdPlayerFacing = "d.bad" };
        w.Core = new ModContentPack { RootDir = Path.Combine(root, "core"), Name = "Core", PackageIdPlayerFacing = "ludeon.rimworld", IsCoreMod = true };
        foreach (var m in new[] { w.A, w.B, w.C, w.D, w.Core }) Directory.CreateDirectory(m.RootDir);
        Directory.CreateDirectory(Path.Combine(w.D.RootDir, "About"));
        File.WriteAllText(Path.Combine(w.D.RootDir, "About", "About.xml"), "<ModMetaData><name>Bad Mod</name><packageId>d.bad</packageId></ModMetaData>");
        File.WriteAllText(Path.Combine(w.D.RootDir, "Languages-note.txt"), "x");

        WriteXml(Path.Combine(w.B.RootDir, "Languages/PortugueseBrazilian/DefInjected/ThingDef/x.xml"), "<Covered.label>Item coberto</Covered.label>");
        WriteXml(Path.Combine(w.C.RootDir, "Languages/PortugueseBrazilian/DefInjected/ThingDef/y.xml"), "<Shield.label>escudo de madeira</Shield.label>");
        WriteXml(Path.Combine(w.C.RootDir, "Languages/PortugueseBrazilian/Keyed/k.xml"), "<Good_Greeting>Olá {0}! (terceiros)</Good_Greeting>");
        WriteXml(Path.Combine(w.C.RootDir, "Languages/PortugueseBrazilian/DefInjected/ThingDef/broken.xml"), "<Oops.label>unterminated");  // must not break anything

        w.Sword = new ThingDef { defName = "Sword", label = "iron sword", description = "A {0} sword." };
        w.Shield = new ThingDef { defName = "Shield", label = gameInPt ? "escudo de madeira" : "wooden shield" }; // game already applied C's text when in pt
        w.Zh = new ThingDef { defName = "Zh", label = "铁剑", description = "中文描述" };
        w.A.defs.AddRange(new[] { w.Sword, w.Shield, w.Zh });
        w.Covered = new ThingDef { defName = "Covered", label = gameInPt ? "Item coberto" : "covered item" };
        w.Uncovered = new ThingDef { defName = "Uncovered", label = "uncovered item" };
        w.B.defs.AddRange(new[] { w.Covered, w.Uncovered });
        w.Fine = new ThingDef { defName = "Fine", label = "fine text one" };
        w.X1 = new ThingDef { defName = "X1", label = "EXPLODE one" }; w.X2 = new ThingDef { defName = "X2", label = "EXPLODE two" };
        w.X3 = new ThingDef { defName = "X3", label = "EXPLODE three" }; w.X4 = new ThingDef { defName = "X4", label = "EXPLODE four" };
        w.D.defs.AddRange(new[] { w.Fine, w.X1, w.X2, w.X3, w.X4 });
        LoadedModManager.RunningModsListForReading = new List<ModContentPack> { w.Core, w.A, w.B, w.C, w.D };

        w.En = new LoadedLanguage { folderName = "English" };
        w.En.keyedReplacements["Good_Greeting"] = new LoadedLanguage.KeyedReplacement { key = "Good_Greeting", value = "Hello {0}!", fileSourceFullPath = w.A.RootDir + "/Languages/English/Keyed/k.xml" };
        w.En.keyedReplacements["Core_Key"] = new LoadedLanguage.KeyedReplacement { key = "Core_Key", value = "Core text here", fileSourceFullPath = w.Core.RootDir + "/Languages/English/Keyed/k.xml" };
        w.Pt = new LoadedLanguage { folderName = "PortugueseBrazilian" };
        if (gameInPt) w.Pt.keyedReplacements["Good_Greeting"] = new LoadedLanguage.KeyedReplacement { key = "Good_Greeting", value = "Olá {0}! (terceiros)" };
        LanguageDatabase.defaultLanguage = w.En;
        LanguageDatabase.activeLanguage = w.Active = gameInPt ? w.Pt : w.En;
        return w;
    }

    static void Run(string lang)
    {
        StateStore.ResetForTests();                      // like a fresh process: reload persisted flags from disk
        AutoTranslateMod.Settings.language = lang;
        Pipeline.Start();
        var sw = System.Diagnostics.Stopwatch.StartNew();
        WaitWorker(sw);
        Console.WriteLine("  pipeline: " + Pipeline.Describe());
        foreach (var m in Pipeline.Mods) Console.WriteLine("  - " + m.Id + " [" + m.Mode + "] " + m.StatusText());
    }

    static void WaitWorker(System.Diagnostics.Stopwatch sw)
    {
        while (!Pipeline.WorkerFinished && sw.Elapsed.TotalSeconds < 40) { Thread.Sleep(30); Pipeline.Tick(); }
        Thread.Sleep(60); Pipeline.Tick();
    }

    static ModState Mod(string id) { return Pipeline.Mods.First(m => m.Id == id); }

    static void Scenario1_GameInTargetLanguage(string home)
    {
        Console.WriteLine("== scenario 1: game already in Portuguese");
        AutoTranslateMod.Settings = new AtSettings();
        var w = Build(home, "s1", true);
        Run("auto");
        Check(Pipeline.Target == "pt-BR" && Pipeline.GameIsTarget, "target pt-BR from game language");
        Check(!Pipeline.Mods.Any(m => m.Id == "ludeon.rimworld"), "official mod not tracked");
        Check(w.Sword.label == "iron sword (pt)" && w.Sword.description == "A {0} sword. (pt)", "uncovered strings translated, markers kept");
        Check(w.Shield.label == "escudo de madeira", "string covered by THIRD-PARTY mod left to the translator mod (not retranslated)");
        Check(Mod("a.good").Third >= 2 && Mod("a.good").ProviderCounts.ContainsKey("Third Party Translator"), "third-party coverage detected and attributed to provider (" + Mod("a.good").Third + ")");
        Check(w.Pt.keyedReplacements["Good_Greeting"].value == "Olá {0}! (terceiros)", "keyed covered by third-party untouched");
        Check(w.Covered.label == "Item coberto" && Mod("b.partial").Native == 1, "mod's OWN translation detected, left alone");
        Check(w.Uncovered.label == "uncovered item (pt)", "partial mod: only the uncovered string is auto-translated");
        Check(w.Zh.label == "铁剑 (pt from zh)" && w.Zh.description == "中文描述 (pt from zh)" && Mod("a.good").SourceCounts.ContainsKey("zh"), "Chinese text inside the mod detected per string and translated zh->pt");
        Check(!w.Pt.keyedReplacements.ContainsKey("Core_Key"), "official keyed ignored");

        var d = Mod("d.bad");
        Check(d.AutoDisabled && d.DisableReason.Contains("translate"), "bad mod auto-disabled after " + ModState.FailureLimit + " failures: " + d.DisableReason);
        Check(w.Fine.label == "fine text one" && w.X1.label == "EXPLODE one", "bad mod's changes reverted (back to original)");
        Check(StateStore.GetDisabledReason("d.bad") != null, "disable persisted to disk");
        Check(!Mod("a.good").AutoDisabled && !Mod("b.partial").AutoDisabled, "other mods unaffected by the bad one");
        Check(File.Exists(Path.Combine(Paths.CacheDir, "pt-BR/a.good.json")) && File.Exists(Path.Combine(Paths.CacheDir, "pt-BR/b.partial.json")), "one cache file per mod");
        string aCache = File.ReadAllText(Path.Combine(Paths.CacheDir, "pt-BR/a.good.json"));
        Check(aCache.Contains("iron sword") && !aCache.Contains("wooden shield"), "cache has only what was translated (not covered strings)");
        Check(Directory.GetFiles(Paths.LogDir, "crash-*.txt").Any(f => File.ReadAllText(f).Contains("mod-disabled:d.bad")), "report file written when a mod is disabled");

        // problem report (what a player sends on GitHub)
        string rp = ReportBuilder.Build();
        string rt = File.ReadAllText(rp);
        Check(rt.Contains("# AutoTranslate problem report") && rt.Contains("### Bad Mod (`d.bad`)"), "report names the suspect mod");
        Check(rt.Contains("<ModMetaData><name>Bad Mod</name>") && rt.Contains("About.xml sha256"), "report embeds the suspect's About.xml + hash");
        Check(rt.Contains("EXPLODE") && rt.Contains("translate:"), "report lists the failing strings");
        Check(rt.Contains("Unreadable translation files") && rt.Contains("broken.xml") && rt.Contains("<Oops.label>unterminated"), "report includes the broken XML file from the other mod with a snippet");
        Check(rt.Contains("## Mod log (tail of this session)") && rt.Contains("## Helper log (tail)") && rt.Contains("TRANSLATION DISABLED for mod 'Bad Mod'") && rt.Contains("[rwt.server]"), "report includes mod log tail and helper log tail");
        Check(!rt.Contains(Environment.GetEnvironmentVariable("HOME") ?? "\u0001"), "home path redacted in report");
        string url = ReportBuilder.IssueUrl();
        Check(url.StartsWith(ReportBuilder.RepoUrl + "/issues/new?") && url.Length < 7001 && url.Contains("d.bad"), "issue URL prefilled and within limits (" + url.Length + " chars)");
    }

    static void Scenario2_GameInEnglish(string home)
    {
        Console.WriteLine("== scenario 2: game in English, target pt (restart => d.bad stays disabled)");
        AutoTranslateMod.Settings = new AtSettings();
        var w = Build(home, "s2", false);
        Run("pt");
        Check(!Pipeline.GameIsTarget, "game is not in target language");
        Check(w.Shield.label == "escudo de madeira", "third-party translation PREVAILS: applied from the translator mod's file (" + w.Shield.label + ")");
        Check(w.En.keyedReplacements["Good_Greeting"].value == "Olá {0}! (terceiros)", "third-party keyed text applied");
        Check(w.Covered.label == "Item coberto", "mod's own translation applied from its file");
        Check(w.Uncovered.label == "uncovered item (pt)" && w.Sword.label == "iron sword (pt)", "rest auto-translated");
        Check(w.Sword.label == "iron sword (pt)" && Mod("a.good").FromCache >= 1, "second run served from cache (" + Mod("a.good").FromCache + ")");
        Check(Mod("d.bad").AutoDisabled && Mod("d.bad").DisableReason.Contains("previous session") && w.Fine.label == "fine text one", "auto-disable survives restart; mod untouched");
    }

    static void Scenario3_Modes(string home)
    {
        Console.WriteLine("== scenario 3: per-mod modes");
        AutoTranslateMod.Settings = new AtSettings();
        AutoTranslateMod.Settings.modModes["a.good"] = ModMode.Mine;      // ignore third-party, use my translation
        AutoTranslateMod.Settings.modModes["b.partial"] = ModMode.Native; // only the mod's own text
        var w = Build(home, "s3", false);
        Run("pt");
        Check(w.Shield.label == "wooden shield (pt)", "'mine': automatic translation even though a third-party one exists (" + w.Shield.label + ")");
        Check(w.Covered.label == "Item coberto" && w.Uncovered.label == "uncovered item", "'native': own text only, uncovered stays English");
        Pipeline.SetMode(Mod("a.good"), ModMode.Off);
        Check(w.Shield.label == "wooden shield" && w.Sword.label == "iron sword" && w.En.keyedReplacements["Good_Greeting"].value == "Hello {0}!", "switching a mod off reverts it immediately");
        Check(AutoTranslateMod.Settings.modModes["a.good"] == ModMode.Off, "choice stored in settings");

        // 'mine' while the game runs in pt and a translation exists: English cannot be recovered in this stub -> must not guess
        AutoTranslateMod.Settings = new AtSettings();
        AutoTranslateMod.Settings.modModes["a.good"] = ModMode.Mine;
        w = Build(home, "s3b", true);
        Run("pt");
        Check(w.Shield.label == "escudo de madeira" && Mod("a.good").EnglishUnavailable >= 1, "'mine' over an existing translation without recoverable English: left as is and reported");
    }

    sealed class Bidir { public ModContentPack Zh, Pt, Ja; public ThingDef ZhLabel, ZhDesc, PtLabel, PtDesc, PtDesc2, JaLabel; public LoadedLanguage En; }

    static Bidir BuildBidir(string home, string tag)
    {
        var b = new Bidir();
        b.Zh = new ModContentPack { RootDir = Path.Combine(home, "bi-" + tag, "zh"), Name = "Chinese Mod", PackageIdPlayerFacing = "e.chinese" };
        b.Pt = new ModContentPack { RootDir = Path.Combine(home, "bi-" + tag, "pt"), Name = "Portuguese Mod", PackageIdPlayerFacing = "f.portuguese" };
        b.Ja = new ModContentPack { RootDir = Path.Combine(home, "bi-" + tag, "ja"), Name = "Japanese Mod", PackageIdPlayerFacing = "j.japanese" };
        b.ZhLabel = new ThingDef { defName = "ZhLabel", label = "铁剑", description = "一把锋利的铁剑，适合战斗。" };
        b.Zh.defs.Add(b.ZhLabel);
        b.PtLabel = new ThingDef { defName = "PtLabel", label = "Espada de ferro", description = "O colono não pode usar esta arma porque ela é muito pesada para você." };
        b.PtDesc2 = new ThingDef { defName = "PtDesc2", label = "Escudo", description = "Esta ação não está disponível para você, mas também não é necessária." };
        b.Pt.defs.AddRange(new[] { b.PtLabel, b.PtDesc2 });
        b.JaLabel = new ThingDef { defName = "JaLabel", label = "鉄の剣です" };
        b.Ja.defs.Add(b.JaLabel);
        foreach (var m in new[] { b.Zh, b.Pt, b.Ja }) Directory.CreateDirectory(m.RootDir);
        LoadedModManager.RunningModsListForReading = new List<ModContentPack> { b.Zh, b.Pt, b.Ja };
        b.En = new LoadedLanguage { folderName = "English" };
        LanguageDatabase.defaultLanguage = b.En; LanguageDatabase.activeLanguage = b.En;
        return b;
    }

    static void Scenario5_Bidirectional(string home)
    {
        Console.WriteLine("== scenario 5: any source language -> any target");
        // (a) target Portuguese, game in English
        AutoTranslateMod.Settings = new AtSettings();
        var b = BuildBidir(home, "a");
        Pipeline.PollMs = 20;
        Run("pt");
        Check(b.ZhLabel.label == "铁剑 (pt from zh)" && b.ZhLabel.description.EndsWith("(pt from zh)"), "Chinese mod translated zh->pt (via the zh>pt model)");
        Check(Mod("e.chinese").SourceCounts.ContainsKey("zh") && !Mod("e.chinese").SourceCounts.ContainsKey("en"), "Chinese mod: detected source = zh");
        Check(Mod("f.portuguese").LatinLang == "pt" && Mod("f.portuguese").LatinConfident, "Portuguese mod detected as pt");
        Check(b.PtLabel.label == "Espada de ferro" && b.PtLabel.description.StartsWith("O colono não pode") && Mod("f.portuguese").AlreadyTarget >= 3, "Portuguese mod with Portuguese target: left untouched (" + Mod("f.portuguese").AlreadyTarget + " already in target)");
        Check(b.JaLabel.label == "鉄の剣です" && Mod("j.japanese").UnsupportedPair >= 1 && !Mod("j.japanese").AutoDisabled, "no ja->pt model: left as is, reported, mod NOT blamed");
        Check(Mod("j.japanese").StatusText().Contains("No model for ja->pt"), "status explains the missing model");

        // (b) the player says the Portuguese mod is really Spanish
        AutoTranslateMod.Settings = new AtSettings();
        AutoTranslateMod.Settings.modSource["f.portuguese"] = "es";
        b = BuildBidir(home, "b");
        Run("pt");
        Check(b.PtLabel.label == "Espada de ferro (pt from es)" && Mod("f.portuguese").SourceOverride == "es", "manual source language override honoured (es->pt)");

        // (c) target English: Portuguese and Chinese mods are translated INTO English
        AutoTranslateMod.Settings = new AtSettings();
        b = BuildBidir(home, "c");
        Run("en");
        Check(Pipeline.Target == "en", "English is accepted as a target");
        Check(b.PtLabel.label == "Espada de ferro (en from pt)" && b.PtDesc2.description.EndsWith("(en from pt)"), "Portuguese mod translated pt->en");
        Check(b.ZhLabel.label == "铁剑 (en from zh)", "Chinese mod translated zh->en");
    }

    static Bidir BuildFull(string home, string tag, out ModContentPack self, out ModMetaData meta)
    {
        var b = BuildBidir(home, tag);
        meta = new ModMetaData { PackageId = "e.chinese", Name = "Chinese Mod" };
        meta.ForTest("A long description of the mod, explained for the player.");
        b.Zh.ModMetaData = meta;
        // this mod itself, pointing at the REAL Languages folder: its own English/Portuguese texts are what T.Get reads
        string modDir = Environment.GetEnvironmentVariable("AT_MOD_DIR");
        self = new ModContentPack { RootDir = modDir, Name = "Auto Translate", PackageIdPlayerFacing = "unknown1210.autotranslate" };
        var list = new List<ModContentPack>(LoadedModManager.RunningModsListForReading) { self };
        LoadedModManager.RunningModsListForReading = list;
        string xml = Path.Combine(modDir, "Languages", "English", "Keyed", "AutoTranslate.xml");
        foreach (var el in System.Xml.Linq.XDocument.Load(xml).Root.Elements())
            b.En.keyedReplacements[el.Name.LocalName] = new LoadedLanguage.KeyedReplacement { key = el.Name.LocalName, value = el.Value, fileSourceFullPath = xml };
        return b;
    }

    static void Scenario6_LiveSwitchDescriptionsSupport(string home)
    {
        Console.WriteLine("== scenario 6: live ON/OFF, mod descriptions, support, language switch without restart");
        AutoTranslateMod.Settings = new AtSettings();
        ModContentPack self; ModMetaData meta;
        var b = BuildFull(home, "full", out self, out meta);
        Check(T.Get("AT_Mods", 5) == "Mods (5)" && T.Get("AT_Enabled") == "Enabled", "T.Get reads the language files and fills {0}");
        Pipeline.Suspended = false;
        Run("pt");
        Check(!Pipeline.Mods.Any(m => m.Id == "unknown1210.autotranslate" && !m.IsSelf) && Pipeline.Mods.Any(m => m.IsSelf), "this mod is tracked as 'self' (hidden in the list)");
        Check(meta.Description == "A long description of the mod, explained for the player. (pt)", "mod description (Mods screen) translated: '" + meta.Description + "'");
        Check(T.Get("AT_BtnOff") == "Desativar traduções (comparar com o original)", "the mod's own screen follows the chosen language (Portuguese)");
        Check(T.Get("AT_Mods", 3) == "Mods (3)", "placeholders still filled in the translated screen");

        // live switch: OFF shows the originals, ON brings the translations back, no restart
        Pipeline.SetSuspended(true);
        Check(b.ZhLabel.label == "铁剑" && meta.Description == "A long description of the mod, explained for the player.", "OFF: labels and descriptions are the originals");
        Check(T.Get("AT_BtnOn") == "Ativar traduções", "OFF: this mod's own screen stays translated");
        Pipeline.SetSuspended(false);
        Check(b.ZhLabel.label == "铁剑 (pt from zh)" && meta.Description.EndsWith("(pt)"), "ON: translations are back");
        Pipeline.SetSuspended(true);
        Pipeline.SetSuspended(true);                      // idempotent
        Pipeline.SetSuspended(false);
        Check(b.ZhLabel.label == "铁剑 (pt from zh)", "toggling many times keeps a consistent state");

        // support per mod
        string ja = Mod("j.japanese").StatusTextUi(), zh = Mod("e.chinese").StatusTextUi();
        Check(ja.Contains("SEM SUPORTE"), "Japanese -> Portuguese shown as NO SUPPORT: " + ja);
        Check(zh.Contains("com suporte") && !zh.Contains("SEM SUPORTE"), "Chinese -> Portuguese shown as supported: " + zh);

        // new target language without restarting the game
        AutoTranslateMod.Settings.language = "en";
        Check(Pipeline.SettingsChangedSinceStart(), "a changed language is noticed");
        Pipeline.Reload();
        WaitWorker(System.Diagnostics.Stopwatch.StartNew());
        Check(Pipeline.Target == "en" && b.ZhLabel.label == "铁剑 (en from zh)", "Reload: Chinese now translated into English (" + b.ZhLabel.label + ")");
        Check(b.PtLabel.label == "Espada de ferro (en from pt)", "Reload: Portuguese mod now translated into English");
        Check(meta.Description == "A long description of the mod, explained for the player.", "Reload: English description needs no translation into English (restored)");
        Check(!Pipeline.SettingsChangedSinceStart(), "settings and running pipeline agree again");
    }

    static void Scenario7_ScreenTextsAndCache(string home)
    {
        Console.WriteLine("== scenario 7: old cache entries and output cleaning");
        Check(Pipeline.CleanTranslation("\u2581mesa\u2581de\u2581pedra ") == "mesa de pedra", "marker \u2581 becomes a space, edges trimmed");
        var cache = new TranslationCache("pt");
        cache.Put("m.cleanup", "stone table", "\u2581mesa\u2581de\u2581pedra");
        cache.Put("m.cleanup", "good", "boa");
        cache.SaveDirty();
        var again = new TranslationCache("pt"); string tr;
        Check(!again.TryGet("m.cleanup", "stone table", out tr) && tr == null, "old cached translation with '_' markers is ignored (will be translated again)");
        Check(again.TryGet("m.cleanup", "good", out tr) && tr == "boa", "normal cached translations are kept");
        again.SaveDirty();
        Check(!File.ReadAllText(Path.Combine(Paths.CacheDir, "pt/m.cleanup.json")).Contains("stone table"), "the bad entry is removed from the file on the next save");
    }

    static void Scenario8_SharedConfigAndHelperCache(string home)
    {
        Console.WriteLine("== scenario 8: target language chosen in the translator program; cache shared with its bulk translation");
        // key normalization is defined twice (C# and Python): the same vectors must give the same answers
        string vec = Path.Combine(Environment.GetEnvironmentVariable("AT_MOD_DIR"), "..", "helper", "tests", "norm_vectors.json");
        var list = (List<object>)Json.Parse(File.ReadAllText(vec));
        int bad = 0;
        foreach (object o in list) { var pair = (List<object>)o; if (TranslationCache.Norm((string)pair[0]) != (string)pair[1]) { bad++; Console.WriteLine("  mismatch: " + pair[0]); } }
        Check(bad == 0, "cache key normalization matches the helper's (" + list.Count + " shared vectors)");
        // a cache file written by the helper's bulk translation (Python) is found by the game (C#), whatever the whitespace
        var c = new TranslationCache("pt-BR"); string tr;
        Check(c.TryGet("py.written", "A long\n      description   with spaces", out tr) && tr == "Uma descrição longa", "cache written by the helper is found with a differently formatted source text");
        c.Put("m.norm", "  Hello   world \r\n again ", "Olá");
        Check(c.TryGet("m.norm", "Hello world\nagain", out tr) && tr == "Olá", "put and get agree on the normalized key");

        string cfg = Path.Combine(Paths.DataDir, "config.json");
        File.WriteAllText(cfg, "{\"target\":\"ja\"}");
        string how;
        Check(LangMap.ResolveTarget("auto", out how) == "ja" && how.Contains("translator program"), "target chosen in the translator program is used (" + how + ")");
        Check(LangMap.ResolveTarget("fr", out how) == "fr", "a manual setting still wins");
        File.WriteAllText(cfg, "{ not json");
        LangMap.ResolveTarget("auto", out how);
        Check(true, "a broken config.json does not crash (" + how + ")");

        // live change while the game is running
        AutoTranslateMod.Settings = new AtSettings();
        File.WriteAllText(cfg, "{\"target\":\"pt\"}");
        var b = BuildBidir(home, "cfg");
        Pipeline.TargetPollMs = 0;
        Run("auto");
        Check(Pipeline.Target == "pt-BR" && b.ZhLabel.label == "铁剑 (pt from zh)", "auto target follows the translator program (pt): " + b.ZhLabel.label);
        File.WriteAllText(cfg, "{\"target\":\"en\"}");
        Pipeline.Tick();
        WaitWorker(System.Diagnostics.Stopwatch.StartNew());
        Check(Pipeline.Target == "en" && b.ZhLabel.label == "铁剑 (en from zh)" && b.PtLabel.label == "Espada de ferro (en from pt)",
            "changing the language in the translator program reloads the translations without restarting the game");
        File.Delete(cfg);
        Pipeline.TargetPollMs = 3000;
    }

    static void Scenario9_PlaceholderTranslationFiles(string home)
    {
        Console.WriteLine("== scenario 9: translation files that only repeat the original text (the Misstall's Furniture case)");
        AutoTranslateMod.Settings = new AtSettings();
        var mod = new ModContentPack { RootDir = Path.Combine(home, "ph", "m"), Name = "Placeholder Mod", PackageIdPlayerFacing = "p.place" };
        WriteXml(Path.Combine(mod.RootDir, "Languages/PortugueseBrazilian/DefInjected/ThingDef/f.xml"),
            "<Armchair.label>MF Armchair</Armchair.label><Armchair.description>A large, soft, comfy seat.</Armchair.description>"
            + "<Couch.description>Um sofá macio para dois colonos.</Couch.description><Bed.description>一张简单的床。</Bed.description>");
        // the game runs in Portuguese and has ALREADY applied those files: the fields hold the file's text
        var armchair = new ThingDef { defName = "Armchair", label = "MF Armchair", description = "A large, soft, comfy seat." };
        var couch = new ThingDef { defName = "Couch", label = "MF Couch", description = "Um sofá macio para dois colonos." };
        var bed = new ThingDef { defName = "Bed", label = "MF Bed", description = "一张简单的床。" };
        mod.defs.AddRange(new[] { armchair, couch, bed });
        LoadedModManager.RunningModsListForReading = new List<ModContentPack> { mod };
        var en = new LoadedLanguage { folderName = "English" };
        var pt = new LoadedLanguage { folderName = "PortugueseBrazilian" };
        // what the game remembers when it injects a translation: the ORIGINAL text of each field
        var pkg = new DefInjectionPackage { defType = typeof(ThingDef) };
        pkg.injections["Armchair.label"] = new DefInjectionPackage.DefInjection { replacedString = "MF Armchair" };
        pkg.injections["Armchair.description"] = new DefInjectionPackage.DefInjection { replacedString = "A large, soft, comfy seat." };
        pkg.injections["Couch.description"] = new DefInjectionPackage.DefInjection { replacedString = "A soft couch for two colonists." };
        pkg.injections["Bed.description"] = new DefInjectionPackage.DefInjection { replacedString = "A simple bed." };
        pt.defInjections.Add(pkg);
        LanguageDatabase.defaultLanguage = en; LanguageDatabase.activeLanguage = pt;
        Run("pt");
        Check(Pipeline.GameIsTarget, "game runs in the target language");
        Check(armchair.description == "A large, soft, comfy seat. (pt)" && armchair.label == "MF Armchair (pt)", "a 'translation' identical to the original is translated anyway: '" + armchair.description + "'");
        Check(couch.description == "Um sofá macio para dois colonos.", "a real translation file is respected and left alone");
        Check(bed.description == "A simple bed. (pt)", "a file in another language is not a Portuguese translation; the ORIGINAL English is translated: " + bed.description);
        Check(Mod("p.place").Placeholders == 3 && Mod("p.place").Native == 1, "counted: 3 placeholders, 1 real own translation (" + Mod("p.place").StatusText() + ")");
        Check(Mod("p.place").StatusTextUi().Contains("repetem o original") || Mod("p.place").StatusTextUi().Contains("only repeat"), "the mod row explains it");
        Pipeline.SetSuspended(true);
        Check(armchair.description == "A large, soft, comfy seat." && couch.description == "Um sofá macio para dois colonos.", "OFF restores exactly what the game had");
        Pipeline.SetSuspended(false);
    }

    sealed class TestDesignator : Designator { }

    static void Scenario10_Designators(string home)
    {
        Console.WriteLine("== scenario 10: buttons built in code by a mod (Orders tab), created before the mod runs");
        AutoTranslateMod.Settings = new AtSettings();
        var mod = new ModContentPack { RootDir = Path.Combine(home, "ds", "m"), Name = "Designator Mod", PackageIdPlayerFacing = "g.designators" };
        mod.assemblies.loadedAssemblies.Add(typeof(TestDesignator).Assembly);
        var core = new ModContentPack { RootDir = Path.Combine(home, "ds", "core"), Name = "Core", PackageIdPlayerFacing = "ludeon.rimworld", IsCoreMod = true };
        LoadedModManager.RunningModsListForReading = new List<ModContentPack> { core, mod };
        var rescue = new TestDesignator { defaultLabel = "Search and rescue", defaultDesc = "Rescue all downed colonists." };
        var built = new RimWorld.Designator_Build { defaultLabel = "Wooden pallet" };
        var already = new TestDesignator { defaultLabel = "铁剑" };
        var empty = new TestDesignator();
        var cat = new DesignationCategoryDef { defName = "Orders" };
        cat.designators.AddRange(new Designator[] { rescue, built, already, empty });
        DefDatabase<DesignationCategoryDef>.list.Clear();
        DefDatabase<DesignationCategoryDef>.list.Add(cat);
        LanguageDatabase.defaultLanguage = new LoadedLanguage { folderName = "English" };
        LanguageDatabase.activeLanguage = new LoadedLanguage { folderName = "PortugueseBrazilian" };
        Run("pt");
        Check(rescue.defaultLabel == "Search and rescue (pt)" && rescue.defaultDesc == "Rescue all downed colonists. (pt)", "button text built in code is translated: '" + rescue.defaultLabel + "' / '" + rescue.defaultDesc + "'");
        Check(built.defaultLabel == "Wooden pallet", "buildings are left to the def translation (not touched here)");
        Check(already.defaultLabel == "铁剑 (pt from zh)", "a Chinese button is translated from Chinese: '" + already.defaultLabel + "'");
        Check(empty.defaultLabel == null, "an empty label is left alone");
        Pipeline.SetSuspended(true);
        Check(rescue.defaultLabel == "Search and rescue" && rescue.defaultDesc == "Rescue all downed colonists.", "OFF restores the original button text");
        Pipeline.SetSuspended(false);
        DefDatabase<DesignationCategoryDef>.list.Clear();
    }

    static void Scenario11_TranslationsWrittenWhileGameRuns(string home)
    {
        Console.WriteLine("== scenario 11: the translator program writes translations while the game is open (applied live, mod by mod)");
        AutoTranslateMod.Settings = new AtSettings();
        var mod = new ModContentPack { RootDir = Path.Combine(home, "lv", "m"), Name = "Live Mod", PackageIdPlayerFacing = "h.live" };
        var other = new ModContentPack { RootDir = Path.Combine(home, "lv", "o"), Name = "Other Mod", PackageIdPlayerFacing = "h.other" };
        var table = new ThingDef { defName = "Table", label = "electric table", description = "An advanced work table." };
        var chair = new ThingDef { defName = "Chair", label = "wooden chair", description = "A plain chair." };
        mod.defs.Add(table); other.defs.Add(chair);
        LoadedModManager.RunningModsListForReading = new List<ModContentPack> { mod, other };
        LanguageDatabase.defaultLanguage = new LoadedLanguage { folderName = "English" };
        LanguageDatabase.activeLanguage = new LoadedLanguage { folderName = "PortugueseBrazilian" };
        Run("pt");
        Check(table.label == "electric table (pt)" && chair.label == "wooden chair (pt)", "first run: translated by the (fake) helper: " + table.label);
        int applied = Pipeline.Applied;
        string flag = Path.Combine(Paths.DataDir, "bulk-running.flag");
        string f = Path.Combine(Path.Combine(Paths.CacheDir, Pipeline.Target), "h.live.json");
        int oldPoll = Pipeline.CachePollMs, oldIdle = Pipeline.IdlePollMs;
        Pipeline.CachePollMs = 40; Pipeline.IdlePollMs = 40;
        Action<double> pump = secs => { var w = System.Diagnostics.Stopwatch.StartNew(); while (w.Elapsed.TotalSeconds < secs) { Thread.Sleep(20); Pipeline.Tick(); } };
        // 1) the program writes the cache file of ONE mod, but is NOT translating (no flag): the game does not even look at the files
        File.WriteAllText(f, "{\"format\":1,\"entries\":{\"electric table\":\"mesa elétrica\",\"An advanced work table.\":\"Uma mesa avançada.\"}}", new System.Text.UTF8Encoding(false));
        File.SetLastWriteTimeUtc(f, DateTime.UtcNow.AddMinutes(5));
        pump(0.4);
        Check(table.label == "electric table (pt)", "idle (no flag): the cache folder is not checked, nothing changes: '" + table.label + "'");
        // 2) the program starts translating (flag): the game now looks, and applies live, mod by mod
        File.WriteAllText(flag, "x");
        var sw = System.Diagnostics.Stopwatch.StartNew();
        while (table.label != "mesa elétrica" && sw.Elapsed.TotalSeconds < 8) { Thread.Sleep(20); Pipeline.Tick(); }
        Check(table.label == "mesa elétrica" && table.description == "Uma mesa avançada.", "while the program translates, new translations show up live, no restart, no reload: '" + table.label + "'");
        Check(chair.label == "wooden chair (pt)", "other mods are not touched");
        Check(Pipeline.Applied - applied == 2, "only the 2 changed texts were applied (" + (Pipeline.Applied - applied) + ")");
        // 3) the last mod is written and the flag goes away at once: one FINAL look still catches it, then the game goes quiet
        pump(0.2);
        File.WriteAllText(f, "{\"format\":1,\"entries\":{\"electric table\":\"mesa elétrica final\"}}", new System.Text.UTF8Encoding(false));
        File.SetLastWriteTimeUtc(f, DateTime.UtcNow.AddMinutes(8));
        File.Delete(flag);
        sw.Restart();
        while (table.label != "mesa elétrica final" && sw.Elapsed.TotalSeconds < 8) { Thread.Sleep(20); Pipeline.Tick(); }
        Check(table.label == "mesa elétrica final", "after the flag is gone one final check applies the last files: '" + table.label + "'");
        File.WriteAllText(f, "{\"format\":1,\"entries\":{\"electric table\":\"nunca aplicada\"}}", new System.Text.UTF8Encoding(false));
        File.SetLastWriteTimeUtc(f, DateTime.UtcNow.AddMinutes(9));
        pump(0.5);
        Check(table.label == "mesa elétrica final", "and then it stops checking until the program translates again");
        // 4) a flag nobody refreshes (the program crashed) is ignored
        File.WriteAllText(flag, "x");
        File.SetLastWriteTimeUtc(flag, DateTime.UtcNow.AddMinutes(-5));
        pump(0.5);
        Check(table.label == "mesa elétrica final", "a stale flag (crashed program) is not a reason to keep checking");
        File.Delete(flag);
        // 5) translations switched off: the new text waits and comes back with the switch
        Pipeline.SetSuspended(true);
        Check(table.label == "electric table", "OFF restores the original");
        File.WriteAllText(flag, "x");
        pump(0.3);
        Check(table.label == "electric table", "while OFF the original stays on screen");
        Pipeline.SetSuspended(false);
        Check(table.label == "nunca aplicada", "ON again: the newest translation (it arrived while OFF): '" + table.label + "'");
        File.Delete(flag);
        Pipeline.CachePollMs = oldPoll; Pipeline.IdlePollMs = oldIdle;
    }

    static void Scenario12_ModListTools(string home)
    {
        Console.WriteLine("== scenario 12: diagnostic of one mod, one translation source for many mods, defs the game generated itself");
        AutoTranslateMod.Settings = new AtSettings();
        var a = new ModContentPack { RootDir = Path.Combine(home, "mt", "a"), Name = "Mod A", PackageIdPlayerFacing = "t.moda" };
        var b = new ModContentPack { RootDir = Path.Combine(home, "mt", "b"), Name = "Mod B", PackageIdPlayerFacing = "t.modb" };
        var gatherer = new ThingDef { defName = "Gatherer", label = "gatherer", description = "Uses local resources when building roads." };
        var made = new RecipeDef { defName = "MakeThing", label = "Fazer ISR2G", description = "Fazer um ISR2G", generated = true };   // a recipe the game made, in its own language
        var plain = new ThingDef { defName = "Plain", label = "plain bench",
            description = "Esta bancada serve para fabricar componentes e também ajuda muito os colonos que trabalham aqui, porque não é necessário muito espaço para usar." };   // a long text already in Portuguese inside an English mod
        a.defs.AddRange(new Def[] { gatherer, made }); b.defs.Add(plain);
        for (int k = 1; k <= 4; k++)       // a realistic English mod: several English texts around the one long Portuguese description
            b.defs.Add(new ThingDef { defName = "Bench" + k, label = "work bench " + k, description = "A sturdy workbench that is used to make things for the colony, and it can be built with the materials that you have." });
        LoadedModManager.RunningModsListForReading = new List<ModContentPack> { a, b };
        LanguageDatabase.defaultLanguage = new LoadedLanguage { folderName = "English" };
        LanguageDatabase.activeLanguage = new LoadedLanguage { folderName = "PortugueseBrazilian" };
        Run("pt");
        Check(gatherer.label == "gatherer (pt)", "normal def translated");
        Check(plain.label == "plain bench (pt)" && plain.description.StartsWith("Esta bancada serve") && !plain.description.EndsWith("(pt)"),
              "a long text already in Portuguese is NOT translated again, the short English label of the same mod is: '" + plain.description + "'");
        Check(made.label == "Fazer ISR2G" && made.description == "Fazer um ISR2G", "a def the game generated in the target language is left alone (it used to become 'Fazenda ISR2G'): '" + made.label + "'");
        ModState ma = Mod("t.moda");
        string diag = Pipeline.DiagnoseMod(ma);
        Check(diag.Contains("t.moda") && diag.Contains("translated and applied: 2") && diag.Contains("waiting: 0") && diag.Contains("Translation file:"), "diagnostic report of a healthy mod:\n" + diag);
        // a text waiting although the translation file has it (the case to look for)
        var it = Pipeline.Mods.Find(m => m.Id == "t.modb");
        Check(Pipeline.DiagnoseMod(it).Contains("waiting: 0"), "second mod healthy too");
        // one translation source for all shown mods: mods the player turned off or that were disabled are left alone
        Pipeline.SetMode(Mod("t.modb"), ModMode.Off);
        int n = Pipeline.SetModeForAll(Pipeline.Mods.FindAll(m => !m.IsSelf), ModMode.Mine);
        Check(n == 1 && Mod("t.moda").Mode == ModMode.Mine && Mod("t.modb").Mode == ModMode.Off, "apply-to-all changes the active mods only (" + n + " changed)");
        Check(AutoTranslateMod.Settings.modModes["t.moda"] == ModMode.Mine && !AutoTranslateMod.Settings.modModes.ContainsKey("t.nothing"), "and it is saved with the settings");
        n = Pipeline.SetModeForAll(Pipeline.Mods.FindAll(m => !m.IsSelf), ModMode.Auto);
        Check(n == 1 && Mod("t.moda").Mode == ModMode.Auto && !AutoTranslateMod.Settings.modModes.ContainsKey("t.moda"), "back to automatic: nothing stored for it");
        Check(Pipeline.SettingsChangedSinceStart(), "the change applies when the settings window closes");
        string allText = Pipeline.DiagnoseAll(Pipeline.Mods.FindAll(m => !m.IsSelf));
        Check(allText.Contains("SUMMARY") && allText.Contains("t.moda") && allText.Contains("t.modb") && allText.Contains("FULL REPORTS"), "diagnostic of all mods: summary and every report");
        string saved = Pipeline.SaveDiagnosticFile(allText);
        Check(File.Exists(saved) && saved.Contains("diagnostics") && File.ReadAllText(saved) == allText, "and it is saved as a .txt in the mod's own folder: " + Path.GetFileName(saved));
    }

    static void Scenario13_ReloadsKeepEverythingEnglishAsSource(string home)
    {
        Console.WriteLine("== scenario 13: reloading (settings window, language change) must never make the game's own translated texts the SOURCE of a new translation");
        AutoTranslateMod.Settings = new AtSettings();
        var mod = new ModContentPack { RootDir = Path.Combine(home, "rl", "m"), Name = "Reload Mod", PackageIdPlayerFacing = "r.reload" };
        const string desc = "A workbench equipped with advanced tools to produce components, and it can be built with the materials that you have at hand.";
        var bench = new ThingDef { defName = "Bench", label = "assembly bench", description = desc };
        var cab = new ThingDef { defName = "Cab", label = "drug cabinet", description = "Increases work speed when placed near a drug lab. One workbench links up to two drug cabinets." };
        mod.defs.AddRange(new Def[] { bench, cab });
        var meta = new ModMetaData { PackageId = "r.reload", Name = "Reload Mod" };
        meta.ForTest("Vanilla Furniture Expanded - Production module is an ideal mod to fill that late game hole in production, and it adds a whole new layer to the workstations.");
        mod.ModMetaData = meta;
        LoadedModManager.RunningModsListForReading = new List<ModContentPack> { mod };
        LanguageDatabase.defaultLanguage = new LoadedLanguage { folderName = "English" };
        LanguageDatabase.activeLanguage = new LoadedLanguage { folderName = "PortugueseBrazilian" };
        Run("pt");
        Check(bench.label == "assembly bench (pt)" && cab.label == "drug cabinet (pt)" && bench.description.EndsWith("(pt)"), "first run: names and descriptions translated: " + bench.label + " / " + cab.label);
        string translatedMeta = meta.Description;
        Check(translatedMeta.EndsWith("(pt)"), "the mod description is translated too");
        for (int round = 1; round <= 3; round++)
        {
            Pipeline.Reload();
            WaitWorker(System.Diagnostics.Stopwatch.StartNew());
            Check(bench.label == "assembly bench (pt)" && cab.label == "drug cabinet (pt)" && cab.description.EndsWith("(pt)"), "after reload " + round + ": still translated, names included: " + bench.label + " / " + cab.label);
        }
        string path = Path.Combine(Path.Combine(Paths.CacheDir, Pipeline.Target), "r.reload.json");
        string json = File.ReadAllText(path);
        Check(!json.Contains("(pt)\":") , "no translated text was ever used as a source in the cache file");
        Check(Mod("r.reload").AlreadyTarget == 0, "nothing was taken for 'already in the target language': " + Mod("r.reload").AlreadyTarget);
        // the window language switch: back to English and again to Portuguese
        Pipeline.SetSuspended(true);
        Check(bench.label == "assembly bench" && meta.Description.StartsWith("Vanilla Furniture"), "OFF restores names, descriptions and the mod description");
        Pipeline.SetSuspended(false);
    }

    static void Scenario14_GameGeneratedTextsDoNotDecideTheLanguage(string home)
    {
        Console.WriteLine("== scenario 14: blueprints, frames and recipes the game generated in Portuguese must not make the whole English mod look Portuguese");
        AutoTranslateMod.Settings = new AtSettings();
        var mod = new ModContentPack { RootDir = Path.Combine(home, "gn", "m"), Name = "Generated Mod", PackageIdPlayerFacing = "g.generated" };
        var cab = new ThingDef { defName = "DrugCab", label = "drug cabinet", description = "Increases work speed when placed near a drug lab. One workbench links up to two drug cabinets." };
        var butcher = new ThingDef { defName = "Butcher", label = "electric butcher", description = "A motorized table with a rotating saw blade. Consumes a lot of power." };
        var stone = new ThingDef { defName = "Stone", label = "electric stonecutter's table" };
        mod.defs.AddRange(new Def[] { cab, butcher, stone });
        string[] english = {
            "A refined turret with military-grade stabilization, targeting routines, and hardened casing. Requires steel to refurbish its barrel after heavy use.",
            "An advanced work table with electrical saws and holders for cutting stone chunks into usable blocks in shorter duration of time on an assembly line.",
            "A large size manufacturing workbench with several tools for designers and a sewing machine for rapid tailoring of clothes.",
            "Increases work speed when placed near a tailoring table. One workbench links up to two tailor cabinets.",
            "A workbench equipped with containers, heaters, and measurement devices for producing various drugs with more efficiency.",
            "A wood-fueled station for smelting. Extracts usable metal from slag chunks and other mixed metal items.",
            "A long, narrow ditch dug into the ground. Crossing it requires climbing up and down, therefore it slows down movement speed.",
            "A powerful, manned artillery cannon designed for long-range bombardment, ideal for precise strikes against enemy structures." };
        for (int k = 0; k < english.Length; k++)
            mod.defs.Add(new ThingDef { defName = "Eng" + k, label = "military item " + k, description = english[k] });
        // what the game makes from every building, in ITS language (Portuguese): lots of it, with the words that give Portuguese away
        for (int k = 1; k <= 14; k++)
            mod.defs.Add(new ThingDef { defName = "Frame" + k, generated = true, label = "estrutura " + k + " (construção)",
                description = "Esta construção ainda não está pronta, por isso não pode ser usada para nada e é preciso terminar o trabalho de construção " + k + "." });
        LoadedModManager.RunningModsListForReading = new List<ModContentPack> { mod };
        LanguageDatabase.defaultLanguage = new LoadedLanguage { folderName = "English" };
        LanguageDatabase.activeLanguage = new LoadedLanguage { folderName = "PortugueseBrazilian" };
        Run("pt");
        Check(Mod("g.generated").LatinLang == "en", "the mod is English: its own texts decide, not the generated ones (" + Mod("g.generated").LatinLang + ")");
        Check(cab.label == "drug cabinet (pt)" && butcher.label == "electric butcher (pt)" && stone.label == "electric stonecutter's table (pt)", "names are translated, short ones included: '" + cab.label + "' / '" + butcher.label + "' / '" + stone.label + "'");
        Check(cab.description.EndsWith("(pt)") && butcher.description.EndsWith("(pt)"), "descriptions are translated too");
    }

    static void Scenario4_CrashMarker(string home)
    {
        Console.WriteLine("== scenario 4: game died while applying a mod");
        AutoTranslateMod.Settings = new AtSettings();
        var w = Build(home, "s4", false);
        StateStore.Clear("d.bad");
        File.WriteAllText(Path.Combine(Paths.DataDir, "state/applying.txt"), "a.good");
        StateStore.ClearSuspects();
        Run("pt");
        Check(Mod("a.good").AutoDisabled && Mod("a.good").DisableReason.Contains("ended while"), "mod suspected after a crash during apply: " + Mod("a.good").DisableReason);
        Check(w.Sword.label == "iron sword", "suspected mod not touched");
        Check(StateStore.GetDisabledReason("a.good") == null, "the FIRST time it is off for this session only: nothing is saved (a closed or killed game must not cost the translation for good)");
        Check(!File.Exists(Path.Combine(Paths.DataDir, "state/applying.txt")), "marker cleaned up");
        File.WriteAllText(Path.Combine(Paths.DataDir, "state/applying.txt"), "a.good");           // and again, with no clean quit in between
        Run("pt");
        Check(StateStore.GetDisabledReason("a.good") != null, "the SECOND time in a row it is saved: " + StateStore.GetDisabledReason("a.good"));
        Pipeline.Reenable(Mod("a.good"));
        Check(StateStore.GetDisabledReason("a.good") == null, "re-enable clears the flag");
        File.WriteAllText(Path.Combine(Paths.DataDir, "state/applying.txt"), "a.good");           // a clean quit in between resets the count
        Run("pt");
        StateStore.ClearSuspects();                                                                 // (what OnQuit does)
        File.WriteAllText(Path.Combine(Paths.DataDir, "state/applying.txt"), "a.good");
        Run("pt");
        Check(StateStore.GetDisabledReason("a.good") == null, "after a clean quit the count starts again: still not saved");
        Pipeline.Reenable(Mod("a.good"));
    }
}
