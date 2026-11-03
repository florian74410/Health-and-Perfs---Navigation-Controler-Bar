# NOVA 0.8.3 — Blue Neon Dark Night (development candidate)

This branch preserves the 0.8.2.2 functional base and adds a separate
`blue-night-083` theme. It DOES NOT replace the source of hardware telemetry,
application/window actions, shortcuts, plugins, or XFCE restoration.

## New native Qt graphics

- Dark graphite glass with electric blue/cyan borders.
- Subtle carbon-finish lines, not carbon as the primary surface.
- Animated low-intensity PCB currents, with the existing redraw timers.
- Independent render integration in HUD, Holo, settings, edge docks,
  cockpit and task buttons.
- Shared Qt stylesheet for inputs, toggles, scrollbars, tabs, dialogs and menus.
- Compartment borders and ARGB transparency preserved.
- Legacy Blue Neon, RedBlack, Matrix, Red Blood remain selectable.

## Assets provided by the owner

The *external* `Blue-Neon-Dark-Night-0.8.3-Assets.zip` contains 116
transparent-overlay PNG frames extracted from eight curated ElectroBlueNEON
animations, plus four reference sheets. The local pack installer only writes to
`~/.config/health-perfs-bar/Themes/blue-night-083/animations` (or
`HEALTHBAR_DATA_DIR` if set). It backs up the previous theme assets and does
not modify installed executables, active settings, wallpaper, or XFCE.

Optional assets: absence of external files does not prevent application startup.
Current renderer uses `holo_radar` and `neon_underline` effects sparingly;
other sequences are pre-extracted for future placement, not falsely claimed to
be fully integrated.

## Validation required before stable release

Run in a Python 3.10+ virtualenv with the project's dependencies:

```bash
python -m compileall -q src/healthbar
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p 'test_blue_night_083.py'
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests
```

Then run the built executable `--self-test` and verify the package version,
install a test package on Linux Mint XFCE/X11, and manually check:
- displays, transparent corners and startup/exit
- every native plugin and Holo open/close, telemetry and missing sensor data
- original click targets, drag/drop, application launches and system tray
- settings save/reload, opacity, theme switching, and all keyboard shortcuts
- multi-workspace overlay, dock auto-retract, window buttons, XFCE restore
- animation CPU usage, frame rate and dark/light wallpapers
- update/rollback with user configuration preserved

**This source branch is NOT certified stable.** No Linux .deb, Windows .exe
or macOS .dmg is asserted to have passed tests. Do not replace a working
NovaBar installation until desktop integration and CI are green.
