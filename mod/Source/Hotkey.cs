using System;
using RimWorld;
using UnityEngine;
using Verse;

namespace AutoTranslate
{
    /// <summary>A keyboard shortcut (one key plus optional Shift / Ctrl / Alt) that switches the translations on and off while playing.
    /// It is chosen in the mod options, saved with the other settings, and checked every frame from Root.Update.</summary>
    public static class Hotkey
    {
        /// <summary>True while the options window waits for the player to press the new shortcut.</summary>
        public static bool Capturing;

        public static string Label(AtSettings s)
        {
            if (s == null || string.IsNullOrEmpty(s.hotkeyKey)) return T.Get("AT_HotkeyNone");
            return (s.hotkeyCtrl ? "Ctrl + " : "") + (s.hotkeyAlt ? "Alt + " : "") + (s.hotkeyShift ? "Shift + " : "") + s.hotkeyKey;
        }

        static bool IsModifier(KeyCode k)
        {
            return k == KeyCode.LeftShift || k == KeyCode.RightShift || k == KeyCode.LeftControl || k == KeyCode.RightControl
                || k == KeyCode.LeftAlt || k == KeyCode.RightAlt;
        }

        /// <summary>Called from the options window for key events while Capturing. Esc cancels; a lone modifier key keeps waiting.</summary>
        public static void Capture(Event e)
        {
            var s = AutoTranslateMod.Settings;
            if (s == null || e == null || e.keyCode == KeyCode.None || IsModifier(e.keyCode)) return;
            Capturing = false;
            if (e.keyCode == KeyCode.Escape) return;
            s.hotkeyKey = e.keyCode.ToString();
            s.hotkeyShift = e.shift; s.hotkeyCtrl = e.control; s.hotkeyAlt = e.alt;
            AtLog.Info("hotkey", "shortcut set to " + Label(s));
        }

        public static void Clear()
        {
            var s = AutoTranslateMod.Settings;
            if (s == null) return;
            s.hotkeyKey = ""; s.hotkeyShift = s.hotkeyCtrl = s.hotkeyAlt = false;
            Capturing = false;
            AtLog.Info("hotkey", "shortcut removed");
        }

        static bool Held(KeyCode a, KeyCode b) { return Input.GetKey(a) || Input.GetKey(b); }

        /// <summary>Every frame (main thread): the shortcut switches the translations on/off in real time, with a short message on screen.</summary>
        public static void Check()
        {
            var s = AutoTranslateMod.Settings;
            if (s == null || Capturing || string.IsNullOrEmpty(s.hotkeyKey)) return;
            KeyCode key;
            try { key = (KeyCode)Enum.Parse(typeof(KeyCode), s.hotkeyKey); }
            catch (ArgumentException) { return; }
            if (!Input.GetKeyDown(key)) return;
            // exactly the chosen modifiers: Tab alone must not fire a Shift + Tab shortcut and vice versa
            if (Held(KeyCode.LeftShift, KeyCode.RightShift) != s.hotkeyShift) return;
            if (Held(KeyCode.LeftControl, KeyCode.RightControl) != s.hotkeyCtrl) return;
            if (Held(KeyCode.LeftAlt, KeyCode.RightAlt) != s.hotkeyAlt) return;
            if (GUIUtility.keyboardControl != 0) return;            // the player is typing in a text box
            Pipeline.SetSuspended(!Pipeline.Suspended);
            Messages.Message(Pipeline.Suspended ? T.Get("AT_Off") : T.Get("AT_On"), MessageTypeDefOf.SilentInput, false);
        }
    }
}
