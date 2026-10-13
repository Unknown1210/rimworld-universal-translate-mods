using System.Collections.Generic;
using Verse;

namespace AutoTranslate
{
    public sealed class AtSettings : ModSettings
    {
        public bool enabled = true;
        public string language = "auto";      // "auto" or an ISO code such as pt, es, fr
        public bool translateDefs = true;
        public bool translateKeyed = true;
        public bool translateMeta = true;      // mod descriptions shown on the Mods screen
        public bool debugLog = false;
        public Dictionary<string, string> modSource = new Dictionary<string, string>(); // packageId -> source language code (absent = detect)
        public Dictionary<string, string> modModes = new Dictionary<string, string>(); // packageId -> auto|native|third|mine|off (absent = auto)

        public override void ExposeData()
        {
            Scribe_Values.Look(ref enabled, "enabled", true);
            Scribe_Values.Look(ref language, "language", "auto");
            Scribe_Values.Look(ref translateDefs, "translateDefs", true);
            Scribe_Values.Look(ref translateKeyed, "translateKeyed", true);
            Scribe_Values.Look(ref translateMeta, "translateMeta", true);
            Scribe_Values.Look(ref debugLog, "debugLog", false);
            Scribe_Collections.Look(ref modSource, "modSource", LookMode.Value, LookMode.Value);
            if (modSource == null) modSource = new Dictionary<string, string>();
            Scribe_Collections.Look(ref modModes, "modModes", LookMode.Value, LookMode.Value);
            if (modModes == null) modModes = new Dictionary<string, string>();
            if (string.IsNullOrWhiteSpace(language)) language = "auto";
        }

        public string Describe()
        {
            return "enabled=" + enabled + " language=" + language + " defs=" + translateDefs + " keyed=" + translateKeyed + " meta=" + translateMeta + " debugLog=" + debugLog + " perModOverrides=" + (modModes == null ? 0 : modModes.Count) + " sourceOverrides=" + (modSource == null ? 0 : modSource.Count);
        }
    }
}
