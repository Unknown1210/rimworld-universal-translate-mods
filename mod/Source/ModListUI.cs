using System;
using System.Collections.Generic;
using UnityEngine;
using Verse;

namespace AutoTranslate
{
    /// <summary>One row per installed mod: name, what the mod does (incl. whether the chosen language is supported),
    /// an Enabled switch and the translation to use. The source language is detected; the target is chosen once, above.</summary>
    public static class ModListUI
    {
        const float RowH = 72f;
        static Vector2 scroll;
        static string search = "";

        public static void Draw(Rect rect)
        {
            if (!Safe.Run("settings-ui", () => DrawInner(rect), "mod list")) Widgets.Label(rect, "(...)");
        }

        static void DrawInner(Rect rect)
        {
            var mods = new List<ModState>();
            int all = 0;
            string q = (search ?? "").Trim();
            foreach (ModState m in Pipeline.Mods)
            {
                if (m.IsSelf) continue;
                all++;
                if (q.Length == 0 || m.Name.IndexOf(q, StringComparison.CurrentCultureIgnoreCase) >= 0 || m.Id.IndexOf(q, StringComparison.CurrentCultureIgnoreCase) >= 0) mods.Add(m);
            }
            Widgets.Label(new Rect(rect.x, rect.y, rect.width, 26f), T.Get("AT_Mods", q.Length == 0 ? all.ToString() : mods.Count + "/" + all) + "  -  " + T.Get("AT_ModsHint"));
            // search box (filters the list below) and the "apply to all shown" menu
            float sw = Math.Min(260f, rect.width * 0.4f);
            Widgets.Label(new Rect(rect.x, rect.y + 28f, 130f, 26f), T.Get("AT_Search"));
            search = Widgets.TextField(new Rect(rect.x + 130f, rect.y + 28f, sw, 26f), search ?? "");
            float aw = Math.Min(320f, rect.width - sw - 150f);
            if (aw > 120f && Widgets.ButtonText(new Rect(rect.x + rect.width - aw, rect.y + 28f, aw, 26f), T.Get("AT_ApplyAll", mods.Count)))
            {
                var shown = new List<ModState>(mods);
                var opts = new List<FloatMenuOption>();
                foreach (string mode in ModMode.All)
                {
                    if (mode == ModMode.Off) continue;
                    string md = mode;
                    opts.Add(new FloatMenuOption(T.Get("AT_ApplyAllTo", ModMode.Label(md), shown.Count), () => Pipeline.SetModeForAll(shown, md)));
                }
                var disabledShown = shown.FindAll(m => m.AutoDisabled);
                if (disabledShown.Count > 0)
                    opts.Add(new FloatMenuOption(T.Get("AT_ReenableAll", disabledShown.Count), () => { foreach (ModState dm in disabledShown) Pipeline.Reenable(dm); }));
                Find.WindowStack.Add(new FloatMenu(opts));
            }
            var outRect = new Rect(rect.x, rect.y + 58f, rect.width, Math.Max(40f, rect.height - 58f));
            var view = new Rect(0f, 0f, outRect.width - 18f, mods.Count * RowH);
            Widgets.BeginScrollView(outRect, ref scroll, view);
            float y = 0f;
            foreach (ModState ms in mods)
            {
                var row = new Rect(0f, y, view.width, RowH - 4f);
                Widgets.DrawHighlightIfMouseover(row);
                float w = view.width, split = w * 0.60f;
                Widgets.Label(new Rect(row.x + 4f, row.y, split - 108f, 24f), ms.Name + "  (" + ms.Id + ")");
                if (Widgets.ButtonText(new Rect(row.x + split - 100f, row.y + 1f, 96f, 22f), T.Get("AT_BtnDiag")))
                {
                    ModState dm = ms;
                    Safe.Run("diagnose", () =>
                    {
                        string report = Pipeline.DiagnoseMod(dm);
                        GUIUtility.systemCopyBuffer = report;
                        AtLog.Info("diagnose", report);
                        Messages.Message(T.Get("AT_DiagCopied", dm.Name), RimWorld.MessageTypeDefOf.SilentInput, false);
                    });
                }
                GameFont old = Text.Font;
                Text.Font = GameFont.Tiny;
                Widgets.Label(new Rect(row.x + 4f, row.y + 24f, split - 8f, RowH - 28f), ms.StatusTextUi());
                Text.Font = old;

                float bx = row.x + split + 8f, bw = w - split - 14f;
                bool on = ms.Active, was = on;
                Widgets.CheckboxLabeled(new Rect(bx, row.y, bw, 26f), T.Get("AT_Enabled"), ref on);
                if (on != was)
                {
                    if (!on) Pipeline.SetMode(ms, ModMode.Off);
                    else if (ms.AutoDisabled) Pipeline.Reenable(ms);
                    else Pipeline.SetMode(ms, ModMode.Auto);
                }
                if (ms.AutoDisabled)
                {
                    if (Widgets.ButtonText(new Rect(bx, row.y + 30f, bw, 26f), T.Get("AT_Reenable"))) Pipeline.Reenable(ms);
                }
                else if (ms.Mode != ModMode.Off)
                {
                    ModState cur = ms;
                    if (Widgets.ButtonText(new Rect(bx, row.y + 30f, bw, 26f), ModMode.Label(ms.Mode)))
                    {
                        var opts = new List<FloatMenuOption>();
                        foreach (string mode in ModMode.All)
                        {
                            if (mode == ModMode.Off) continue;
                            string m = mode;
                            opts.Add(new FloatMenuOption(ModMode.Label(m), () => Pipeline.SetMode(cur, m)));
                        }
                        Find.WindowStack.Add(new FloatMenu(opts));
                    }
                }
                y += RowH;
            }
            Widgets.EndScrollView();
        }
    }
}
