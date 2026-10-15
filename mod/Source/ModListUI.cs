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
            // A card of its own, set apart from the options above it
            Widgets.DrawMenuSection(rect);
            Rect inner = rect.ContractedBy(10f);
            GameFont old0 = Text.Font;
            Text.Font = GameFont.Medium;
            string title = T.Get("AT_Mods", q.Length == 0 ? all.ToString() : mods.Count + "/" + all) + ":";
            float titleW = Text.CalcSize(title).x + 6f;
            Widgets.Label(new Rect(inner.x, inner.y, titleW, 30f), title);
            Text.Font = GameFont.Tiny;
            // the hint sits right after the title, on the same line (its baseline close to the big text)
            Widgets.Label(new Rect(inner.x + titleW, inner.y + 9f, Math.Max(0f, inner.width - titleW), 22f), T.Get("AT_ModsHint"));
            Text.Font = old0;
            // one toolbar line: search on the left, the two bulk buttons on the right, all the same height
            float ty = inner.y + 38f, th = 28f;
            Widgets.Label(new Rect(inner.x, ty + 2f, 110f, th), T.Get("AT_Search"));
            search = Widgets.TextField(new Rect(inner.x + 112f, ty, Math.Min(230f, inner.width * 0.32f), th), search ?? "");
            float left = 112f + Math.Min(230f, inner.width * 0.32f) + 12f;
            float avail = Math.Max(0f, inner.width - left);
            float applyW = Math.Max(120f, avail * 0.56f), diagW = Math.Max(110f, avail - applyW - 8f);
            float rx = inner.x + inner.width;
            if (Widgets.ButtonText(new Rect(rx - diagW, ty, diagW, th), T.Get("AT_DiagAll")))
            {
                var shownForReport = new List<ModState>(mods);
                Safe.Run("diagnose-all", () =>
                {
                    string report = Pipeline.DiagnoseAll(shownForReport);
                    string file = Pipeline.SaveDiagnosticFile(report);
                    GUIUtility.systemCopyBuffer = report;
                    Messages.Message(T.Get("AT_DiagAllSaved", shownForReport.Count, file), RimWorld.MessageTypeDefOf.SilentInput, false);
                    try { Application.OpenURL(System.IO.Path.GetDirectoryName(file)); } catch { }
                });
            }
            if (Widgets.ButtonText(new Rect(rx - diagW - 8f - applyW, ty, applyW, th), T.Get("AT_ApplyAll", mods.Count)))
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
            Widgets.DrawLineHorizontal(inner.x, ty + th + 6f, inner.width);
            float top = ty + th + 12f;
            var outRect = new Rect(inner.x, top, inner.width, Math.Max(40f, inner.y + inner.height - top));
            var view = new Rect(0f, 0f, outRect.width - 18f, mods.Count * RowH);
            Widgets.BeginScrollView(outRect, ref scroll, view);
            float y = 0f;
            foreach (ModState ms in mods)
            {
                var row = new Rect(0f, y, view.width, RowH - 4f);
                Widgets.DrawHighlightIfMouseover(row);
                float w = view.width, split = w * 0.58f;
                Widgets.Label(new Rect(row.x + 4f, row.y, split - 8f, 24f), ms.Name + "  (" + ms.Id + ")");
                GameFont old = Text.Font;
                Text.Font = GameFont.Tiny;
                Widgets.Label(new Rect(row.x + 4f, row.y + 24f, split - 8f, RowH - 28f), ms.StatusTextUi());
                Text.Font = old;

                float bx = row.x + split + 8f, bw = w - split - 14f;
                float modeW = bw * 0.62f, diagW2 = bw - modeW - 4f;
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
                    if (Widgets.ButtonText(new Rect(bx, row.y + 30f, modeW, 26f), T.Get("AT_Reenable"))) Pipeline.Reenable(ms);
                }
                else if (ms.Mode != ModMode.Off)
                {
                    ModState cur = ms;
                    if (Widgets.ButtonText(new Rect(bx, row.y + 30f, modeW, 26f), ModMode.Label(ms.Mode)))
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
                if (Widgets.ButtonText(new Rect(bx + modeW + 4f, row.y + 30f, diagW2, 26f), T.Get("AT_BtnDiag")))
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
                y += RowH;
            }
            Widgets.EndScrollView();
        }
    }
}
