# NOVA NEXUS HD 0.7.6 — unified visual and usability change request

Status: implementation workstream; NOT an installation release. Based on source branch
`fix/novabar-v075-terminal-scrollback`, retaining 0.7.5 scrollback and controls.

## User reference images (do not duplicate/rehost without assets permission)

- Control: small **square** with cut/electronic corner details, electric-blue metal/glass border, dark center, and precisely centered **red glyph**. Apply at actual 1x/2x rendered pixel sizes.
- PCB defect: dark, low-detail/muddy texture must be removed. Reuse the **same composited PCB layer and transparency parameters as NOVA Terminal Manager** — no alternative static texture or arbitrary bright pattern.

## One coordinated patch (four acceptance groups)

1. **Window control visual contract**
   - Close red `×`, maximize red `□`, minimize red `−`; all three inside same square blue cut-corner button, not circular.
   - Both Qt NOVA Terminal windows and real XFWM4 decorations of third-party apps must show all three buttons.
   - Preserve hit areas >= 28 logical pixels, keyboard accessibility, hover/press states; never remove WM fallback.
   - Validate layout `O|HMC` and valid XFWM4 XPM assets with rollback for unsupported frame dimensions.
2. **Unified PCB layer**
   - Share Terminal Manager render layer or style tokens across cockpit/panels/window controls; retain transparent dark substrate and fine cyan traces.
   - Don't paint PCB on top of text or impair legibility; keep compositing efficient on Macro.
3. **Retracted top HUD**
   - Entire raw data row visible inside the reduced height, with no clipped labels or midline text.
   - Hide icons, gauge shells and expanded PCB modules in compact mode; show readable small labels + real values + units.
   - Recalculate minimum compact bar height from font metrics, DPI and 2–4 px vertical padding; update workarea reserved height; test multiple monitor heights.
   - Keep CPU/RAM/net readouts and ping if available; show `—` where sensors unavailable, do not fabricate data.
4. **NEXUS and file shortcut context actions**
   - From Mint/NEXUS app launcher, add `Ajouter à la barre droite` in the application's context menu opened by **double-click** per user request, while avoiding the double-click's normal launch action.
   - For folder entries, add `Ajouter à la barre gauche`.
   - Validate .desktop entries against applications list and folder paths via Path.is_dir; persist separately from profiles in existing NovaBar shortcut registry, deduplicate, then refresh dock.
   - Keep standard context-menu open by right click as a fallback, ensure keyboard support (Shift+F10), and provide Remove from dock.
   - Never execute the shortcut while adding it, and don't modify system-wide .desktop files.

## Regression / release acceptance

- Test GTK3/Qt/Firefox/Thunar/XFCE terminal and regular windows on Macro X11.
- Test expanded/collapsed toolbar at several display scales, desktop workspaces and workarea behavior.
- Test launcher and folder shortcuts are reloaded after restart, survive Upgrade, and can be removed.
- Check no duplicate NEXUS activation / unintended double launch.
- Verify idle CPU draw does not regress. Keep original 0.7.5 scrollbars and terminal integration.
- Publish native installer only after code modifications, automated checks and on-Macro visual acceptance.
