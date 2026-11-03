# NOVA Blue Neon — Graphite FX (prototype 0.8.2.2)

## Base

Branch: `work/novabar-blue-neon-graphite-fx-0822`.
Forked directly from `0.8.2.2REDBLACK` to keep recent functional changes;
**RedBlack remains optional** and is not the default Blue Neon design.
No replacement of the original settings, telemetry, shortcuts, docks, Holo,
window management, or XFCE behavior.

## Visual language

- Background: graphite black, about 75% of the visual mass.
- Primary accent: electric blue / cyan, not red.
- Red is reserved for existing semantic indicators and tiny navigation marks.
- No bright field that makes measurements harder to read.
- Real Qt painter animation (not simulated GIFs): travelling electric impulses,
  PCB junctions and breathing rail highlights.
- Transparent exterior, no global acrylic fill or wallpaper changes.
- Current integration: existing HUD module frames and lower cockpit frame.
- Holo, dialogs, lateral docks and settings need a separate visual pass.

## Implementation

`src/healthbar/blue_graphite_fx.py` is a stateless decorative painter.
The HUD reuses its existing periodic redraw; cockpit consumes its current
`phase` value. No independent QTimer, task, background thread, sensor calls
or changes to click/drag geometry were introduced. Disabled automatically for
all themes other than `blue-neon`.

## Development checks

```bash
python -m compileall -q src/healthbar
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p 'test_blue_graphite_fx.py'
```

Qt offscreen tests inspect transparency and basic rendering, **not** a live
XFCE desktop. Real desktop validation, resource measurement, packaging and a
Linux installer are still required before presenting this branch as stable.
Install only after building and validating a package; this branch does not
publish an installable release.
