> Mise à jour 0.7.0 : les composants sont maintenant intégrés au runtime et au pack natif. Voir [le guide actuel](UPDATE_V070.md). Les limitations de notification et de compatibilité indiquées dans ce document restent à vérifier par composant.

# NOVA NEXUS HD — master plan (31 October 2026)

Status: **experimental foundation**, NOT an installable NOVA desktop release.

## Product direction

Transform the appearance of Linux Mint XFCE while preserving XFCE, Thunar, existing
panel, login mechanisms and reliable rollback. Visual references are straight-on
(front-facing) cockpit elements, never 3D tilted notifications.

## Visual contract

- Electric blue / cyan accents over graphite and midnight blue.
- Angular or square buttons with clipped corners; PCB tracks should be visible,
  with zig-zag turns, pads and subtle junction glow.
- Legible text on flat, dark surfaces; no illegible text on complex wallpaper.
- Configurable accent colors, glow, shadows, opacity, PCB contrast, borders,
  bevels, motion and reduced-motion mode.
- Iconography must remain recognizable and must not imitate security prompts.
- Effects should be performance-budgeted and optional.

## Selected components / implementation boundaries

1. **NOVA Windows:** XFWM4 decorations plus compatible GTK theme; XFWM4 does not
   support arbitrary Qt rendering on third-party titlebars.
2. **NOVA Dialogs:** Qt-native dialogs in NOVA apps; GTK-themed compatible system
   dialogs. Do not replace polkit/sudo prompts with untrusted custom overlays.
3. **NOVA Explorer:** Qt native file browser, folder/file operations, animations
   (hover, navigation transitions, selection, drag-drop), optional Thunar fallback.
   Use trash by default for deletion, ask for destructive actions.
4. **NOVA Notifications:** frontal, pixel-aligned to screen, optional native
   D-Bus notification daemon integration; ensure only one daemon owns
   org.freedesktop.Notifications at a time.
5. **NOVA Login and Lock Screen:** theme LightDM and the existing session
   locker separately; never replace PAM or password verification logic.
6. **NOVA Wallpapers:** static high-resolution PCB themed backgrounds first,
   with dark/low-contrast regions for desktop icons; animations optional.
7. **NOVA Context Menus:** own Qt menus and best-effort GTK styling. Not every
   third-party application accepts global menu overrides.
8. **NOVA Settings:** deferred GUI, but theme tokens exist from day one.

## Phase 1: code now

- `nova_nexus/theme_engine.py`: strict JSON schema v1, defaults, atomic save,
  Qt-compatible stylesheet helper. Does not change the user's theme by itself.
- `tests/test_nova_theme_engine.py`: basic config validation and roundtrip.
- No release installer from these sources until an integration build is tested.

## Roadmap and acceptance

### P0 — foundations, safety
- Preserve existing v0.6.11 update logic, configs, profiles and plugins.
- Create a distinctive PCB design language and selectable palettes.
- Validate UTF-8 JSON before displaying any theme.
- Support reversible opt-in activation, with backup and Restore XFCE action.
- Keep keyboard navigation, scaling and high-contrast accessibility.

### P1 — first desktop theme
- XFWM4 + GTK3 theme assets; test minimize/maximize/close/focus and scaling.
- NOVA dialogs and context menus in our own Qt apps.
- Run in XFCE X11 on a disposable account before wide deployment.

### P2 — desktop apps
- NOVA Explorer with real file operations and animation controls.
- Front-facing notification daemon, graceful fallback to xfce4-notifyd.
- Wallpapers generated and properly licensed/attributed if third-party.

### P3 — session personalization
- LightDM greeter + lock screen, separately validated and rollback-safe.
- Settings UI for saved themes and profiles.

## Compatibility / release checklist

- Do not modify live LightDM, locker or default file handler during install
  without user opt-in and rollback.
- Keep a previous installer available; run Qt tests and XFCE session smoke tests.
- Verify .deb package installation, Upgrade path, rollback and update manifest.
- Confirm repository release assets/checksums exist before announcing version.
- Do not ship this branch as a stable automatic update.
