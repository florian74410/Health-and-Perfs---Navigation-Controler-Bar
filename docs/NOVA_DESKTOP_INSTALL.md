# NOVA desktop integration — experimental

This branch does **not** install a release or replace XFCE components automatically.

## Preview

With Python 3 and PySide6 installed:

```sh
python3 -m nova_nexus.preview
python3 -m nova_nexus.explorer
```

PyGObject/Gio are required for the explorer's safe *Move to Trash* operation.
If unavailable, deletion fails safely rather than permanently removing files.

## GTK skeleton export

```sh
python3 -c 'from nova_nexus.desktop_theme import export_gtk_theme; export_gtk_theme("~/.local/share/themes/NOVA-NEXUS-HD")'
```

The theme is not activated automatically and only provides a GTK3 CSS prototype.
To restore your original appearance, select your previous GTK theme in
XFCE Appearance settings.

## Not yet implemented

- Tested full XFWM4 window-decoration theme (requires actual compatible pixmaps)
- Freedesktop D-Bus notification daemon / history
- LightDM greeter and xflock4-specific lock theme
- Native packaging and updater manifest / signature/checksums
- XFCE live-session acceptance tests

Never replace PAM, disable authentication, or auto-switch the login theme.
