"""Add shortcuts through the live host when available, otherwise persist settings."""
from .config import Settings
from .edge_docks import normalized_drop, default_folders, desktop_apps


def add_shortcut(path, kind):
    clean = normalized_drop([str(path)], kind)
    if not clean: raise ValueError('Raccourci invalide')
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    host = next((w for w in app.topLevelWidgets() if callable(getattr(w, 'save_dock_entries', None))), None) if app else None
    settings = host.settings if host else Settings.load()
    attr = 'dock_folder_paths' if kind == 'folders' else 'dock_app_paths'
    existing = getattr(settings, attr)
    if existing is None: existing = default_folders() if kind == 'folders' else desktop_apps()
    values = list(dict.fromkeys([*existing, *clean]))[:128]
    if host: host.save_dock_entries(kind, values)
    else:
        setattr(settings, attr, values); settings.save()
    return values
