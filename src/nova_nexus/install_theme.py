"""Reversible user-owned XFCE theme selection and title-control migration."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
from .desktop_theme import export_gtk_theme
from .xfwm4 import export_xfwm4_theme
from .theme_engine import get_default_theme
from healthbar.system_env import native_env

NAME = 'NOVA-NEXUS-HD'
CONTROLS = (
    ('xfwm4', '/general/button_layout', 'string', 'O|HMC'),
    ('xfwm4', '/general/titleless_maximize', 'bool', 'false'),
    ('xsettings', '/Gtk/DecorationLayout', 'string', 'menu:minimize,maximize,close'),
)


def _get(channel, prop):
    try:
        result = subprocess.run(['xfconf-query', '-c', channel, '-p', prop], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=native_env(), timeout=15)
    except FileNotFoundError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _set(channel, prop, kind, value):
    if value is None:
        if _get(channel, prop) is not None:
            subprocess.run(['xfconf-query', '-c', channel, '-p', prop, '-r'],
                           check=True, env=native_env(), timeout=15)
        return
    command = ['xfconf-query', '-c', channel, '-p', prop, '-s', value]
    if _get(channel, prop) is None:
        command += ['-n', '-t', kind]
    subprocess.run(command, check=True, env=native_env(), timeout=15)


def _state_path():
    return Path.home() / '.config/nova-nexus/xfce-theme-backup.json'


def _controls(previous):
    saved = previous.setdefault('controls', {})
    for channel, prop, kind, value in CONTROLS:
        key = channel + ':' + prop
        if key not in saved:
            saved[key] = _get(channel, prop)
    # Back up before any change, including a migration from pre-0.7.4.
    state = _state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(previous, indent=2) + '\n', encoding='utf-8')
    for channel, prop, kind, value in CONTROLS:
        _set(channel, prop, kind, value)


def refresh_selected_theme():
    """Upgrade only a theme already selected by the user; never opt them in."""
    if _get('xfwm4', '/general/theme') != NAME:
        return False
    state = _state_path()
    # Externally selected themes may have no restore snapshot. Do not invent one.
    if state.is_file():
        previous = json.loads(state.read_text(encoding='utf-8'))
        _controls(previous)
    # A different value emits a theme change even when the exported name is the same.
    # No restart of xfwm4 or loss of open windows is necessary.
    for channel, prop in (('xfwm4', '/general/theme'), ('xsettings', '/Net/ThemeName')):
        if _get(channel, prop) == NAME:
            _set(channel, prop, 'string', 'Default')
            _set(channel, prop, 'string', NAME)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description='Export or apply NOVA XFCE theme')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--apply', action='store_true')
    group.add_argument('--restore', action='store_true')
    args = parser.parse_args(argv)
    state = _state_path()
    if args.restore:
        if not state.exists():
            parser.error('No prior theme backup found')
        previous = json.loads(state.read_text(encoding='utf-8'))
        for channel, prop, kind, value in CONTROLS:
            key = channel + ':' + prop
            if key in previous.get('controls', {}) and _get(channel, prop) == value:
                _set(channel, prop, kind, previous['controls'][key])
        for channel, prop, key in (('xsettings', '/Net/ThemeName', 'gtk'),
                                    ('xfwm4', '/general/theme', 'xfwm4')):
            if _get(channel, prop) == NAME:
                _set(channel, prop, 'string', previous[key])
        state.unlink()
        print('Restored previous XFCE themes and title controls')
        return
    base = Path.home() / '.local/share/themes' / NAME
    export_gtk_theme(base, get_default_theme())
    export_xfwm4_theme(base, get_default_theme())
    if not args.apply:
        print('Exported NOVA theme to', base)
        return
    previous = json.loads(state.read_text(encoding='utf-8')) if state.exists() else {
        'gtk': _get('xsettings', '/Net/ThemeName'), 'xfwm4': _get('xfwm4', '/general/theme')}
    _controls(previous)
    for channel, prop in (('xsettings', '/Net/ThemeName'), ('xfwm4', '/general/theme')):
        _set(channel, prop, 'string', NAME)
    refresh_selected_theme()
    print('Applied NOVA themes with minimize, maximize/restore and close controls')


if __name__ == '__main__':
    main()
