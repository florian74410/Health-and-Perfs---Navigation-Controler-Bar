"""Optional, reversible Cyber Nexus skin for the existing Xfce 4 panel.

The panel is NEVER replaced: every original launcher, tray icon, plugin and
shortcut stays owned by xfce4-panel. We only add a clearly delimited GTK 3 CSS
block and change the selected panel's native auto-hide setting, with backup.
No panel thickness, position, plugin-ids or launcher list is modified.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .config import data_dir

START = "/* NOVABAR CYBER NEXUS PANEL SKIN BEGIN (managed) */"
END = "/* NOVABAR CYBER NEXUS PANEL SKIN END (managed) */"
PALETTES = {
    "blue-neon": ("#18dfff", "#1765bc", "24, 220, 245"),
    "cyber-futuriste": ("#18dfff", "#1765bc", "24, 220, 245"),
    "green-matrix": ("#43fa9a", "#137d59", "67, 250, 154"),
    "red-blood": ("#ff607d", "#96254e", "255, 96, 125"),
}
BOTTOM_POSITIONS = {4, 8, 10, 12}


def gtk_css_path():
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home()/".config"))) / "gtk-3.0/gtk.css"


def backup_path():
    return data_dir() / "xfce-panel-original.json"


def available():
    """Only native X11/Xfce sessions. Unsupported desktop remains unchanged."""
    return (sys.platform.startswith("linux") and bool(os.environ.get("DISPLAY"))
            and shutil.which("xfconf-query") is not None
            and shutil.which("xfce4-panel") is not None)


def _query(*arguments):
    try:
        response = subprocess.run(
            ["xfconf-query", "-c", "xfce4-panel", *arguments],
            check=False, capture_output=True, text=True, timeout=2)
        if response.returncode:
            return None
        return response.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None


def bottom_panel_id():
    """Find a bottom-anchored XFCE panel without presuming panel-0/panel-1."""
    output = _query("-lv")
    if not output:
        return None
    options = []
    for line in output.splitlines():
        match = re.match(r"^/panels/panel-(\d+)/position\s+p=(\d+);", line)
        if match and int(match.group(2)) in BOTTOM_POSITIONS:
            options.append(int(match.group(1)))
    return min(options) if options else None


def _property(panel_id, name):
    return f"/panels/panel-{panel_id}/{name}"


def panel_setting(panel_id, name):
    return _query("-p", _property(panel_id, name))


def _set_panel_setting(panel_id, name, value):
    prop = _property(panel_id, name)
    try:
        command = ["xfconf-query", "-c", "xfce4-panel", "-p", prop, "-s", str(value)]
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=2)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def render_css(theme="blue-neon", delay_seconds=10):
    primary, secondary, rgb = PALETTES.get(theme, PALETTES["blue-neon"])
    ms = max(1000, min(30000, int(delay_seconds)*1000))
    # GTK panel classes are scoped; desktop icon themes / native plugins stay intact.
    return f"""{START}
/* XFCE retains all launchers, Wi-Fi, notifications, tasklist and system tray.
   Only the shell/background/buttons are retinted. Never touch plugin-ids.
   XFCE GTK CSS popdown delay is expressed in milliseconds. */
#XfcePanelWindow {{
  -XfcePanelWindow-popup-delay: 150;
  -XfcePanelWindow-popdown-delay: {ms};
}}
.xfce4-panel.background {{
  background-color: rgba(4, 13, 27, 0.91);
  background-image: linear-gradient(to bottom,
    rgba({rgb}, 0.16), rgba(5, 14, 30, 0.91) 38%,
    rgba(2, 10, 21, 0.95) 86%, rgba({rgb}, 0.09));
  border-style: solid;
  border-width: 1px 0;
  border-color: {secondary};
  box-shadow: inset 0 1px rgba({rgb}, 0.26);
}}
.xfce4-panel.background button {{
  color: #e3f6ff;
  border: 1px solid transparent;
  border-radius: 5px;
  background-color: transparent;
  background-image: none;
  box-shadow: none;
  padding: 1px;
}}
.xfce4-panel.background button:hover {{
  border-color: {primary};
  background-color: rgba({rgb}, 0.17);
  box-shadow: inset 0 0 3px rgba({rgb}, 0.28);
}}
.xfce4-panel.background button:checked {{
  background-color: rgba({rgb}, 0.22);
  border-color: {secondary};
}}
{END}"""


def with_managed_block(original, block):
    """Replace only our owned segment; never wipe existing user's GTK theme."""
    start, end = original.find(START), original.find(END)
    if (start == -1) != (end == -1):
        raise ValueError("Marqueur NovaBar GTK incomplet : aucune modification")
    if start != -1:
        if end <= start or original.count(START) != 1 or original.count(END) != 1:
            raise ValueError("Marqueurs GTK NovaBar ambigus : aucune modification")
        original = original[:start] + original[end+len(END):]
    result = original.rstrip("\n")
    if block:
        result = (result + "\n\n" if result else "") + block + "\n"
    elif result:
        result += "\n"
    return result


def _atomic_text(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".novabar-tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _reload_panel():
    """Panel restart only when GTK CSS changes: preserve every plugin and size."""
    try:
        subprocess.Popen(["xfce4-panel", "--restart"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        pass


def apply_skin(theme, delay_seconds=10):
    if not available():
        return False, "Habillage XFCE disponible uniquement sur une session XFCE X11."
    target = bottom_panel_id()
    if target is None:
        return False, "Aucun panneau XFCE ancré en bas détecté : rien n'a été modifié."
    backup = backup_path()
    css_file = gtk_css_path()
    previous = css_file.read_text(encoding="utf-8") if css_file.exists() else ""
    next_css = with_managed_block(previous, render_css(theme, delay_seconds))
    saved = None
    if backup.is_file():
        try:
            saved = json.loads(backup.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False, "Sauvegarde du panneau illisible : modification refusée."
    if saved is not None and saved.get("panel_id") != target:
        return False, "Le panneau XFCE a changé : restaurez d'abord l'ancien habillage."
    original_autohide = panel_setting(target, "autohide-behavior")
    if original_autohide is None:
        return False, "Impossible de lire l'état du panneau XFCE : modification annulée."
    if saved is None:
        saved = {"panel_id": target, "original_autohide": original_autohide}
        _atomic_text(backup, json.dumps(saved, ensure_ascii=False, indent=2)+"\n")
    if not _set_panel_setting(target, "autohide-behavior", 2):
        return False, "Impossible d'activer le repli natif XFCE."
    if next_css != previous:
        _atomic_text(css_file, next_css)
        _reload_panel()
    return True, "Habillage XFCE actif ; icônes et épaisseur d'origine conservées."


def remove_skin():
    """Restore pre-NovaBar panel auto-hide and remove only NovaBar GTK CSS."""
    backup = backup_path()
    if not backup.is_file():
        return False, "Aucune sauvegarde d'habillage XFCE à restaurer."
    try:
        info = json.loads(backup.read_text(encoding="utf-8"))
        panel = info["panel_id"]
        old_autohide = info["original_autohide"]
        css_file = gtk_css_path()
        previous = css_file.read_text(encoding="utf-8") if css_file.is_file() else ""
        updated = with_managed_block(previous, "")
        if not _set_panel_setting(panel, "autohide-behavior", old_autohide):
            return False, "Impossible de restaurer le repli original du panneau."
        if updated != previous:
            _atomic_text(css_file, updated)
            _reload_panel()
        backup.unlink()
        return True, "Panneau XFCE restauré sans toucher à ses icônes."
    except (KeyError, OSError, ValueError, TypeError) as exc:
        return False, f"Restauration du panneau impossible : {exc}"
