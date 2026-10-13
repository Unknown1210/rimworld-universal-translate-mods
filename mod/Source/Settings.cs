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
        public bool hidePseudo = true;         // hide the accent-marked "pseudo translation" the game shows in developer mode on texts without a translation
        public string hotkeyKey = "";          // KeyCode name of the shortcut that switches translations on/off ("" = no shortcut)
        public bool hotkeyShift, hotkeyCtrl, hotkeyAlt;   // modifiers that must be held with it
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
            Scribe_Values.Look(ref hidePseudo, "hidePseudo", true);
            Scribe_Values.Look(ref hotkeyKey, "hotkeyKey", "");
            Scribe_Values.Look(ref hotkeyShift, "hotkeyShift", false);
            Scribe_Values.Look(ref hotkeyCtrl, "hotkeyCtrl", false);
            Scribe_Values.Look(ref hotkeyAlt, "hotkeyAlt", false);
            if (hotkeyKey == null) hotkeyKey = "";
            Scribe_Collections.Look(ref modSource, "modSource", LookMode.Value, LookMode.Value);
            if (modSource == null) modSource = new Dictionary<string, string>();
            Scribe_Collections.Look(ref modModes, "modModes", LookMode.Value, LookMode.Value);
            if (modModes == null) modModes = new Dictionary<string, string>();
            if (string.IsNullOrWhiteSpace(language)) language = "auto";
        }

        public string Describe()
        {
            return "enabled=" + enabled + " language=" + language + " defs=" + translateDefs + " keyed=" + translateKeyed + " meta=" + translateMeta + " debugLog=" + debugLog + " hotkey=" + Hotkey.Label(this) + " perModOverrides=" + (modModes == null ? 0 : modModes.Count) + " sourceOverrides=" + (modSource == null ? 0 : modSource.Count);
        }
    }
}
