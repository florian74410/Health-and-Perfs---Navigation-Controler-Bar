"""NOVA theme installation helper — opt-in only, with reversible XFCE selection.

No sudo, no display manager modification, no package updates.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .desktop_theme import export_gtk_theme
from .xfwm4 import export_xfwm4_theme
from .theme_engine import get_default_theme
from healthbar.system_env import native_env


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export or apply NOVA XFCE theme (preview)")
    parser.add_argument("--apply", action="store_true", help="Opt in to set GTK and XFWM4")
    parser.add_argument("--restore", action="store_true", help="Restore saved previous themes")
    args = parser.parse_args(argv)
    base = Path.home() / ".local/share/themes/NOVA-NEXUS-HD"
    state = Path.home() / ".config/nova-nexus/xfce-theme-backup.json"
    if args.restore:
        if not state.exists():
            parser.error("No prior theme backup found")
        previous = json.loads(state.read_text(encoding="utf-8"))
        import subprocess
        for channel, prop, value in (
            ("xsettings", "/Net/ThemeName", previous["gtk"]),
            ("xfwm4", "/general/theme", previous["xfwm4"]),
        ):
            subprocess.run(["xfconf-query", "-c", channel, "-p", prop, "-s", value], check=True, env=native_env(), timeout=15)
        state.unlink()
        print("Restored previous XFCE themes")
        return
    export_gtk_theme(base, get_default_theme())
    export_xfwm4_theme(base, get_default_theme())
    print("Exported prototype to", base)
    if not args.apply:
        print("Not activated. Run with --apply to opt in; --restore to roll back.")
        return
    import subprocess
    def get(channel, prop):
        return subprocess.check_output(["xfconf-query", "-c", channel, "-p", prop], text=True, env=native_env(), timeout=15).strip()
    previous = {"gtk": get("xsettings", "/Net/ThemeName"),
                "xfwm4": get("xfwm4", "/general/theme")}
    state.parent.mkdir(parents=True, exist_ok=True)
    if not state.exists():
        state.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")
    for channel, prop in (("xsettings", "/Net/ThemeName"), ("xfwm4", "/general/theme")):
        subprocess.run(["xfconf-query", "-c", channel, "-p", prop, "-s", "NOVA-NEXUS-HD"], check=True, env=native_env(), timeout=15)
    print("Applied experimental NOVA themes. Roll back with --restore.")


if __name__ == "__main__":
    main()
