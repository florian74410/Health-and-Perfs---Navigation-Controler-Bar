# NOVA Explorer V2 — Macro visual acceptance

The V2 preview is opt-in. It does not replace Thunar or change XFCE default applications.

## Run

```bash
cd ~/NOVA-DEV/Health-and-Perfs---Navigation-Controler-Bar
git pull --ff-only origin feature/nova-nexus-hd-foundation
source .venv/bin/activate
python3 -m compileall -q nova_nexus
python3 -m nova_nexus.explorer
```

## Check on Linux Mint XFCE

- Open folders with double-click; test back, forward, parent and Home.
- Test both icon grid and list view, navigation animations and search filter.
- Right-click a file, check correct selection and properties.
- Create a *disposable test directory* and test copy, cut, paste, rename and trash.
- Check menu/controls at smaller window sizes and 125%/150% scaling.
- Test folders with inaccessible permissions; no sudo or privilege escalation.
- Test that the existing NovaBar and Thunar are unchanged.

## Known limitations

- V2 uses normal Qt main window chrome, not yet the full irregular beveled
  glass border displayed in concept art.
- File search is a name filter, not full-text indexed search.
- Context menu action operations are prototype-level and should not be
  trusted for valuable data before filesystem regression tests.
- No test execution / graphical validation from Macro has yet been reported.
