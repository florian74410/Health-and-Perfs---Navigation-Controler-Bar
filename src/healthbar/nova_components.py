"""NOVA NEXUS HD components shared by installer, runtime and Upgrade."""
import json
import os
import subprocess
import sys
from pathlib import Path
from . import __version__

_windows = []


def component_manifest():
    from .bundled_plugins import bundled_archives
    from .plugins import PluginRegistry
    registry = PluginRegistry()
    return {
        'product': 'NOVA NEXUS HD', 'version': __version__,
        'source_components': {'novabar': '6423f0f899a8c45d131c6dd1a017651c95c63439',
                              'nova_foundation': '2d62c194d953c391881b234792c6d40b159b0e97'},
        'components': ['HUD et Holo', 'Panneaux latéraux', 'Cockpit inférieur',
                       'NEXUS applications', 'NOVA Explorer', 'NOVA Terminal (Linux)', 'Thème GTK3 et XFWM4',
                       'Fond PCB', 'Aperçu des notifications', 'Upgrade'],
        'plugins': [{k: manifest[k] for k in ('id', 'version')} for manifest, _ in
                    (registry.inspect(path) for path in bundled_archives())],
        'notifications': 'preview; XFCE daemon preserved',
        'native_cockpit': 'Linux X11 / XFCE',
    }


def verify_components():
    """Run inside the staged executable before activation; no user writes."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtSvg import QSvgRenderer
    from nova_nexus.explorer import run
    from nova_nexus.chrome_v3 import make_dialog
    from nova_nexus.theme_engine import get_default_theme, validate_theme
    from nova_nexus.desktop_theme import render_gtk_css
    from nova_nexus import theme_pack
    validate_theme(get_default_theme())
    if not render_gtk_css():
        raise ValueError('GTK theme missing')
    for name in ('nova_pcb_overlay.svg', 'nova-electric-blue-pcb.svg'):
        asset = Path(theme_pack.__file__).parent / 'assets' / name
        if not asset.is_file() or not QSvgRenderer(str(asset)).isValid():
            raise ValueError('NOVA asset missing or invalid: ' + name)
    window = run(Path.home(), embedded=True)
    QApplication.processEvents()
    if window.grab().isNull():
        raise ValueError('NOVA Explorer failed to render')
    window.close()
    dialog = make_dialog('NOVA / VÉRIFICATION', 'Composants disponibles')
    dialog.close()
    from nova_nexus.terminal_manager import open_manager
    manager = open_manager(start=False)
    terminal = manager.window
    pane = manager.workspace().panes[0]
    pane.session.stream.feed(b'\x1b[36mNOVA Terminal\x1b[0m')
    pane.view.render_screen()
    QApplication.processEvents()
    if terminal.grab().isNull():
        raise ValueError('NOVA Terminal failed to render')
    terminal.close()
    manifest = component_manifest()
    if getattr(sys, 'frozen', False) and len(manifest['plugins']) != 8:
        raise ValueError('The complete runtime requires eight bundled plugins')
    return manifest


def open_explorer(value):
    """Open a directory within NOVA; never send a directory URI to a browser."""
    from nova_nexus.explorer import run
    path = Path.home() if str(value) == 'recent:///' else Path(value).expanduser()
    if not path.is_dir():
        return False
    window = run(path, embedded=True)
    _windows.append(window)
    from PySide6.QtCore import Qt
    window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    window.destroyed.connect(lambda *_: _windows.remove(window) if window in _windows else None)
    mark_application_window(window)
    return True


def install_components(settings):
    """Install app-owned user assets once per version, preserving GTK selection."""
    from .bundled_plugins import seed_bundled_plugins
    seed_bundled_plugins(settings)
    if not sys.platform.startswith('linux'):
        return
    from .config import data_dir
    from nova_nexus.theme_pack import install_user_pack, desktop_entry, terminal_entry
    marker = data_dir() / 'nova-components.json'
    try:
        previous = json.loads(marker.read_text())
    except (OSError, ValueError):
        previous = {}
    # A selected/customized theme is retained as a sibling before a new export.
    if previous.get('version') != __version__:
        import shutil
        theme = Path.home() / '.local/share/themes/NOVA-NEXUS-HD'
        backup = theme.with_name('NOVA-NEXUS-HD.previous-' + __version__)
        if theme.is_dir() and not backup.exists():
            shutil.copytree(theme, backup, symlinks=True)
        install_user_pack(python=sys.executable, root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1],
                          frozen=getattr(sys, 'frozen', False))
        marker.parent.mkdir(parents=True, exist_ok=True)
        temporary = marker.with_suffix('.tmp')
        temporary.write_text(json.dumps(component_manifest(), ensure_ascii=False, indent=2)+'\n')
        temporary.replace(marker)
    else:
        # Upgrade may move the active executable while this version stays the same.
        desktop = Path.home()/'.local/share/applications/nova-nexus-explorer.desktop'
        if desktop.is_file() and 'NOVA NEXUS HD experimental file manager' in desktop.read_text():
            desktop.write_text(desktop_entry(sys.executable, Path(sys.executable).parent,
                                            frozen=getattr(sys, 'frozen', False)))
        terminal = Path.home()/'.local/share/applications/nova-nexus-terminal.desktop'
        if terminal.is_file() and 'X-NOVA-Owned=true' in terminal.read_text():
            terminal.write_text(terminal_entry(sys.executable,Path(sys.executable).parent,
                                               frozen=getattr(sys,'frozen',False)))


def configure_theme(action):
    if not sys.platform.startswith('linux'):
        raise ValueError('Le thème XFCE nécessite Linux')
    if action == 'install':
        from .config import Settings
        install_components(Settings.load())
    else:
        from . import nova_desktop
        getattr(nova_desktop, "activate" if action == "apply" else "restore")()


def mark_application_window(window):
    if not sys.platform.startswith('linux'):
        return
    from PySide6.QtWidgets import QApplication
    if QApplication.platformName() != 'xcb':return
    from Xlib import Xatom,display
    connection=display.Display()
    try:
        target=connection.create_resource_object('window',int(window.winId()))
        target.change_property(connection.intern_atom('_NOVABAR_APPLICATION'),Xatom.CARDINAL,32,[1])
        connection.flush()
    finally:connection.close()


def open_terminal(directory=None):
    from nova_nexus.terminal_manager import open_manager
    return open_manager(cwd=directory)
