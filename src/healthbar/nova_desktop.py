"""Reversible NOVA desktop activation on the existing XFCE session."""
import configparser
import json
import os
from pathlib import Path
import subprocess
from .config import Settings, data_dir
from .system_env import native_env

DESKTOP_ID = 'nova-nexus-explorer.desktop'
PANEL_KEYS = ('hud_enabled', 'dock_left_enabled', 'dock_right_enabled',
              'bottom_dock_enabled', 'xfce_skin_enabled', 'xfce_skin_offer_done')


def _mime(*args):
    return subprocess.check_output(['xdg-mime', *args], text=True,
                                   env=native_env(), timeout=15).strip()


def _restore_mime(previous):
    # Respect subsequent user changes to the preferred file manager.
    if _mime('query', 'default', 'inode/directory') != DESKTOP_ID:
        return
    if previous:
        _mime('default', previous, 'inode/directory')
    else:
        path=Path(os.getenv('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'mimeapps.list'
        parser=configparser.ConfigParser(interpolation=None,strict=False)
        parser.optionxform=str
        parser.read(path,encoding='utf-8')
        if parser.has_section('Default Applications'):
            parser.remove_option('Default Applications','inode/directory')
            with path.open('w',encoding='utf-8') as output:parser.write(output)


TERMINAL_HOTKEY = '/commands/custom/<Primary><Alt>t'


def _xfconf(*args):
    return subprocess.run(['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', *args],
                          text=True, capture_output=True, timeout=6, env=native_env())


def _install_terminal_hotkey(previous):
    """Replace only the user's Ctrl+Alt+T binding, retaining its prior value."""
    result=_xfconf('-p', TERMINAL_HOTKEY)
    previous['terminal_hotkey']={'exists': result.returncode == 0,
                                 'value': result.stdout.strip() if result.returncode == 0 else ''}
    command='novabar --nova-terminal'
    operation=['-p', TERMINAL_HOTKEY, '-s', command]
    if result.returncode != 0:
        operation=['-p', TERMINAL_HOTKEY, '-n', '-t', 'string', '-s', command]
    changed=_xfconf(*operation)
    if changed.returncode != 0:
        raise RuntimeError('Impossible de configurer Ctrl+Alt+T : '+changed.stderr.strip())


def _restore_terminal_hotkey(previous):
    """Do not overwrite a keyboard binding subsequently changed by the user."""
    saved=previous.get('terminal_hotkey')
    if not isinstance(saved,dict):
        return
    current=_xfconf('-p', TERMINAL_HOTKEY)
    if current.returncode != 0 or current.stdout.strip() != 'novabar --nova-terminal':
        return
    if saved.get('exists'):
        _xfconf('-p', TERMINAL_HOTKEY, '-s', saved.get('value',''))
    else:
        _xfconf('-p', TERMINAL_HOTKEY, '-r')

def activate(*, replace_file_manager=False):
    from .nova_components import install_components
    from nova_nexus.install_theme import main as theme_main
    settings=Settings.load()
    install_components(settings)
    state_path=data_dir()/'nova-desktop-backup.json'
    if state_path.exists():
        previous=json.loads(state_path.read_text())
    else:
        previous={'file_manager': _mime('query','default','inode/directory'),
                  'panels':{key:getattr(settings,key) for key in PANEL_KEYS}}
        state_path.parent.mkdir(parents=True,exist_ok=True)
        state_path.write_text(json.dumps(previous,indent=2)+'\n')
    try:
        theme_main(['--apply'])
        _install_terminal_hotkey(previous)
        state_path.write_text(json.dumps(previous,indent=2)+'\n')
        if replace_file_manager:
            _mime('default',DESKTOP_ID,'inode/directory')
        settings.hud_enabled=True
        settings.dock_left_enabled=True
        settings.dock_right_enabled=True
        settings.bottom_dock_enabled=True
        settings.xfce_skin_enabled=False
        settings.xfce_skin_offer_done=True
        settings.save()
    except Exception:
        try:
            _restore_terminal_hotkey(previous)
            _restore_mime(previous['file_manager'])
            theme_main(['--restore'])
        except Exception:
            pass
        raise


def restore():
    from nova_nexus.install_theme import main as theme_main
    state_path=data_dir()/'nova-desktop-backup.json'
    if not state_path.exists():
        # Compatibility with themes selected by the standalone foundation pack.
        theme_main(['--restore'])
        return
    previous=json.loads(state_path.read_text())
    _restore_terminal_hotkey(previous)
    _restore_mime(previous['file_manager'])
    theme_main(['--restore'])
    settings=Settings.load()
    for key,value in previous['panels'].items():
        if key in PANEL_KEYS:setattr(settings,key,value)
    settings.save()
    state_path.unlink()
