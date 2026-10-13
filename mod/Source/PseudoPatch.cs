using System.Reflection;
using HarmonyLib;
using Verse;

namespace AutoTranslate
{
    /// <summary>In developer mode RimWorld marks texts that have no translation in the game's language by running them through
    /// Translator.PseudoTranslated, which sprinkles accents on the letters ("Séàrçh ànd rèsçùè"). It is meant for translators, it is
    /// unreadable for players, and it hits every mod that lacks a translation. This patch hands back the original text instead
    /// (switchable in the advanced options). If the game has no such method (another version) the patch is simply not applied.</summary>
    [HarmonyPatch]
    public static class Patch_Translator_PseudoTranslated
    {
        static bool Prepare() { return AccessTools.Method(typeof(Translator), "PseudoTranslated") != null; }
        static MethodBase TargetMethod() { return AccessTools.Method(typeof(Translator), "PseudoTranslated"); }

        /// <summary>Returns false (skips the game's method) and gives back the original text, unless the player turned this off.</summary>
        public static bool Prefix(string original, ref string __result)
        {
            var s = AutoTranslateMod.Settings;
            if (s != null && !s.hidePseudo) return true;
            __result = original;
            return false;
        }
    }
}
