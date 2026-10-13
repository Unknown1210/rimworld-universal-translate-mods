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

        public static void Draw(Rect rect)
        {
            if (!Safe.Run("settings-ui", () => DrawInner(rect), "mod list")) Widgets.Label(rect, "(...)");
        }

        static void DrawInner(Rect rect)
        {
            var mods = new List<ModState>();
            foreach (ModState m in Pipeline.Mods) if (!m.IsSelf) mods.Add(m);
            Widgets.Label(new Rect(rect.x, rect.y, rect.width, 26f), T.Get("AT_Mods", mods.Count) + "  -  " + T.Get("AT_ModsHint"));
            var outRect = new Rect(rect.x, rect.y + 28f, rect.width, Math.Max(40f, rect.height - 28f));
            var view = new Rect(0f, 0f, outRect.width - 18f, mods.Count * RowH);
            Widgets.BeginScrollView(outRect, ref scroll, view);
            float y = 0f;
            foreach (ModState ms in mods)
            {
                var row = new Rect(0f, y, view.width, RowH - 4f);
                Widgets.DrawHighlightIfMouseover(row);
                float w = view.width, split = w * 0.60f;
                Widgets.Label(new Rect(row.x + 4f, row.y, split - 8f, 24f), ms.Name + "  (" + ms.Id + ")");
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
