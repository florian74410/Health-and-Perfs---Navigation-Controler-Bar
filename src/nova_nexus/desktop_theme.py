"""Safe opt-in desktop theme exporter for XFCE GTK and XFWM4.

Exports ordinary user-owned theme files. Does NOT activate, touch /etc,
change a login/lock screen or replace a desktop daemon.
"""
from __future__ import annotations
import html
from pathlib import Path
from .theme_engine import get_default_theme, validate_theme


def render_gtk_css(theme=None):
    t = validate_theme(theme or get_default_theme())
    c = t["colors"]
    return """
/* NOVA NEXUS HD GTK3 overlay — only GTK widgets honoring user themes */
@define-color theme_bg_color %s;
@define-color theme_fg_color %s;
@define-color theme_selected_bg_color %s;
@define-color theme_selected_fg_color %s;
window, dialog, .background { background-color: %s; color: %s; }
button { border-radius: 0; border: 1px solid %s; background: %s; color: %s; }
button:hover { border-color: %s; background: %s; }
entry { border-radius: 0; border: 1px solid %s; background: %s; color: %s; }
menu, menuitem, popover { background: %s; color: %s; }
menuitem:hover { background: %s; }
""" % (c["background"], c["text"], c["secondary"], c["text"],
       c["background"], c["text"], c["primary"], c["surface_raised"], c["text"],
       c["primary"], c["secondary"], c["secondary"], c["surface"], c["text"],
       c["surface"], c["text"], c["surface_raised"])


def export_gtk_theme(destination, theme=None):
    """Export a standalone GTK theme skeleton to an explicit destination."""
    t = validate_theme(theme or get_default_theme())
    target = Path(destination).expanduser()
    directory = target / "gtk-3.0"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "gtk.css").write_text(render_gtk_css(t), encoding="utf-8")
    (target / "index.theme").write_text(
        "[Desktop Entry]\nType=X-GNOME-Metatheme\nName=NOVA NEXUS HD\n"
        "Comment=Experimental NOVA theme\n", encoding="utf-8")
    return target
