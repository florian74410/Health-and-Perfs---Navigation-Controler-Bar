"""NovaBar edge docks: user folders and desktop application launchers.

One process, independent dock windows. No shell evaluation, no untrusted
.desktop parsing for arbitrary execution; GIO handles desktop launchers.
"""
from __future__ import annotations
import configparser
import os
import subprocess
import sys
import math
from pathlib import Path

from PySide6.QtCore import QRect, Qt, QTimer, QUrl, QPoint, QPointF, QRectF, Signal, QFileInfo, QSize
from PySide6.QtGui import (QCursor, QDesktopServices, QIcon, QPainter, QPen,
                            QColor, QPolygonF, QPainterPath, QLinearGradient)
from PySide6.QtWidgets import (QMessageBox, 
    QApplication, QAbstractItemView, QFileIconProvider, QFrame,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QMenu, QFileDialog, QVBoxLayout, QWidget,
)

from .system_env import native_env
from .overlay import apply_priority, apply_all_workspaces
from .xfce_panel_skin import PALETTES


def xdg_folder(name: str) -> Path:
    """Discover localized XDG paths such as Téléchargements, without a shell."""
    if sys.platform.startswith("linux"):
        try:
            result = subprocess.run(["xdg-user-dir", name], text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=native_env(),
                                    timeout=1, check=False)
            candidate = Path(result.stdout.strip()).expanduser()
            if result.returncode == 0 and candidate.is_dir():
                return candidate
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
    names = {
        "DOCUMENTS": ("Documents",),
        "DOWNLOAD": ("Téléchargements", "Downloads"),
        "PICTURES": ("Images", "Pictures"),
        "MUSIC": ("Musique", "Music"),
        "VIDEOS": ("Vidéos", "Videos"),
        "DESKTOP": ("Bureau", "Desktop"),
        "TEMPLATES": ("Modèles", "Templates"),
        "PUBLICSHARE": ("Public",),
    }
    for folder in names.get(name, (name.title(),)):
        candidate = Path.home() / folder
        if candidate.is_dir():
            return candidate
    return Path.home() / names.get(name, (name.title(),))[0]


def default_folders() -> list[str]:
    items = [str(Path.home())]
    for key in ("DOCUMENTS", "DOWNLOAD", "PICTURES", "MUSIC", "VIDEOS", "DESKTOP"):
        path = xdg_folder(key)
        if path.is_dir() and str(path) not in items:
            items.append(str(path))
    items.append("recent:///")
    return items


def desktop_apps() -> list[str]:
    """Discover user desktop launchers (Linux, Windows or macOS)."""
    directory = xdg_folder("DESKTOP")
    if not directory.is_dir():
        return []
    suffixes = (".lnk", ".url") if sys.platform == "win32" else (".app",) if sys.platform == "darwin" else (".desktop",)
    return [str(path) for path in sorted(directory.iterdir(), key=lambda p: p.name.casefold())
            if path.suffix.lower() in suffixes and (path.is_file() or path.is_dir() and sys.platform == "darwin")
            and (path.suffix.lower() != ".desktop" or launcher_metadata(path) is not None)]


def normalized_drop(paths, kind):
    """Only valid absolute folder paths or existing .desktop launchers."""
    accepted = []
    for path in paths:
        p = Path(path).expanduser()
        if kind == "folders" and p.is_dir():
            value = str(p.resolve())
        elif kind == "apps" and (
                p.is_file() and p.suffix.lower() in ((".lnk", ".url") if sys.platform == "win32" else (".desktop",))
                or sys.platform == "darwin" and p.is_dir() and p.suffix.lower() == ".app"):
            value = str(p.resolve())
        else:
            continue
        if value not in accepted:
            accepted.append(value)
    return accepted


def launcher_metadata(path: Path):
    display = path.stem
    icon_name = "application-x-executable"
    try:
        config = configparser.ConfigParser(interpolation=None, strict=False)
        config.read(path, encoding="utf-8")
        entry = config["Desktop Entry"]
        if entry.get("Type", "") != "Application" or entry.getboolean("Hidden", False) or entry.getboolean("NoDisplay", False):
            return None
        display = entry.get("Name[fr]", entry.get("Name", display))
        icon_name = entry.get("Icon", icon_name)
    except (OSError, KeyError, ValueError, configparser.Error):
        return None
    return display, icon_name


def launch_item(value: str, kind: str) -> bool:
    """Use native open handlers; desktop files only via GIO, never shell=True."""
    if kind == "folders":
        from .nova_components import open_explorer
        return open_explorer(value)
    target = Path(value)
    if sys.platform == "win32":
        if not target.is_file() or target.suffix.lower() not in (".lnk", ".url"):
            return False
        try:
            os.startfile(str(target))
            return True
        except OSError:
            return False
    if sys.platform == "darwin":
        if not target.is_dir() or target.suffix.lower() != ".app":
            return False
        try:
            subprocess.Popen(["open", str(target)], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True, env=native_env())
            return True
        except OSError:
            return False
    if not target.is_file() or target.suffix.lower() != ".desktop" or launcher_metadata(target) is None:
        return False
    if sys.platform.startswith("linux"):
        from .terminal_launchers import is_nova_terminal_shortcut
        if is_nova_terminal_shortcut(target):
            from .nova_components import open_terminal
            try:
                open_terminal()
                return True
            except (OSError,ValueError) as error:
                QMessageBox.warning(None,"NOVA Terminal",str(error))
                return False
        try:
            subprocess.Popen(["gio", "launch", str(target)], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True, env=native_env())
            return True
        except OSError:
            return False
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))


class DockItems(QListWidget):
    changed = Signal(list)

    def __init__(self, kind, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setIconSize(QSize(30, 30))
        self.model().rowsMoved.connect(lambda *args: self.changed.emit(self.values()))

    def values(self):
        return [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            found = normalized_drop([url.toLocalFile() for url in event.mimeData().urls()
                                     if url.isLocalFile()], self.kind)
            if found:
                values = self.values()
                insert = self.indexAt(event.position().toPoint()).row()
                if insert < 0: insert = len(values)
                for value in found:
                    if value in values:
                        existing = values.index(value)
                        values.pop(existing)
                        if existing < insert: insert -= 1
                    values.insert(insert, value)
                    insert += 1
                self.changed.emit(values)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            super().dropEvent(event)


class DockGrip(QLabel):
    """Drag the dock title from one edge to the other; no native window dragging."""
    switch_requested = Signal()
    def __init__(self, side, parent=None):
        super().__init__("⠿  DÉPLACER  ↔", parent)
        self.side = side
        self.origin = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Glisser cette poignée vers l'autre moitié de l'écran pour déplacer le dock")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.globalPosition().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.origin is not None:
            final = event.globalPosition().toPoint()
            screen = QApplication.screenAt(final) or QApplication.primaryScreen()
            if (final - self.origin).manhattanLength() > 80 and screen:
                mid = screen.geometry().center().x()
                if (self.side == "left" and final.x() > mid or
                    self.side == "right" and final.x() < mid):
                    self.switch_requested.emit()
        self.origin = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)


def dock_colors(theme):
    primary, secondary, _rgb = PALETTES.get(theme, PALETTES["blue-neon"])
    return primary, secondary


def dock_stylesheet(theme):
    accent, secondary = dock_colors(theme)
    return f"""
        QFrame#dockBody {{ background: transparent; border: none; }}
        QFrame#dockBody QLabel {{ color: #d9edfa; font-size: 11px; background: transparent; }}
        QFrame#dockBody QPushButton {{
            background: rgba(8,29,48,185); color: #e7fbff;
            border: 1px solid {secondary}; border-radius: 3px; padding: 4px;
        }}
        QFrame#dockBody QPushButton:hover {{
            background: rgba(18,63,83,220); border-color: {accent};
        }}
        QFrame#dockBody QListWidget {{
            background: rgba(3,13,26,184); border: 1px solid {secondary};
            border-radius: 3px; color: #e7f5ff; outline: none;
            font-size: 11px; padding: 3px;
        }}
        QFrame#dockBody QListWidget::item {{
            min-height: 45px; border-bottom: 1px solid #16344d;
            margin: 2px; padding: 4px; border-radius: 2px;
        }}
        QFrame#dockBody QListWidget::item:hover {{
            background: rgba(34,95,111,190); border-left: 2px solid {accent};
        }}
        QFrame#dockBody QListWidget::item:selected {{
            background: rgba(16,77,104,210); border-left: 2px solid {accent};
        }}
    """


class PCBDockFrame(QFrame):
    """Cut-corner circuit board body, painted beneath real clickable widgets."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.phase = 0.0
        self.setObjectName("dockBody")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if w < 40 or h < 30:
            p.end()
            return
        accent_text, secondary_text = dock_colors(self.settings.theme)
        accent = QColor(accent_text)
        secondary = QColor(secondary_text)
        shell = QPainterPath()
        shell.addPolygon(QPolygonF([
            QPointF(2, 18), QPointF(18, 2), QPointF(w-23, 2),
            QPointF(w-2, 23), QPointF(w-2, h-25),
            QPointF(w-23, h-2), QPointF(17, h-2), QPointF(2, h-17)]))
        shell.closeSubpath()
        p.setPen(QPen(accent, 1.8))
        p.setBrush(QColor(4, 14, 29, 237))
        p.drawPath(shell)
        p.setClipPath(shell)
        p.setPen(QPen(secondary, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        inner = shell.toFillPolygon()
        p.drawLine(QPointF(24, 10), QPointF(w-28, 10))
        p.drawLine(QPointF(19, h-10), QPointF(w-27, h-10))
        # Two tall PCI-style conductors run along the outside of the controls.
        for side in (9, w-10):
            for y in range(34, h-30, 42):
                shift = 11 if side < w/2 else -11
                p.setPen(QPen(secondary, 1))
                p.drawLine(QPointF(side, y), QPointF(side, y+12))
                p.drawLine(QPointF(side, y+12), QPointF(side+shift, y+21))
                p.setPen(QPen(accent, 1))
                p.drawEllipse(QPointF(side+shift, y+21), 1.7, 1.7)
        # Animated microprocessor blocks, live traces, and small LEDs.
        pulse_y = 36 + self.phase * max(1, h-72)
        for side in (9, w-10):
            p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 65), 4))
            p.drawLine(QPointF(side, max(15,pulse_y-32)), QPointF(side, pulse_y))
            p.setPen(QPen(accent, 2.1))
            p.drawEllipse(QPointF(side, pulse_y), 2.6, 2.6)
        for x in range(39, w-28, 33):
            p.setPen(QPen(secondary, .8))
            p.drawLine(QPointF(x, 13), QPointF(x+9, 13))
            p.drawLine(QPointF(x+9, 13), QPointF(x+13, 18))
            p.drawLine(QPointF(x+13, 18), QPointF(x+21, 18))
            if int(self.phase*15+x/7)%3 == 0:
                p.setPen(QPen(accent, 1.5))
                p.drawEllipse(QPointF(x+21, 18), 1.5, 1.5)
        p.end()


class EdgeDock(QWidget):
    """Independent 3-second auto-hiding top-level panel, preserving the edge trigger."""
    moved_to_other_side = Signal(str)
    entries_changed = Signal(str, list)
    settings_requested = Signal()

    def __init__(self, side: str, kind: str, settings, parent=None):
        super().__init__(None)
        assert side in ("left", "right")
        assert kind in ("folders", "apps")
        self.side = side
        self.kind = kind
        self.settings = settings
        self.collapsed = True
        self.edge_width = 10
        self.panel_width = 250
        self.full_rect = None
        self.setWindowTitle(f"NovaBar • {kind} • {side}")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)
        self.content = PCBDockFrame(settings)
        self.content.setStyleSheet(dock_stylesheet(settings.theme))
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(7, 9, 7, 8)
        layout.setSpacing(6)
        title = QHBoxLayout()
        self.grip = DockGrip(side)
        self.grip.switch_requested.connect(lambda: self.moved_to_other_side.emit(self.side))
        title.addWidget(self.grip, 1)
        self.swap = QPushButton("↔")
        self.swap.setToolTip("Échanger la position des docks")
        self.swap.setFixedWidth(28)
        self.swap.clicked.connect(lambda: self.moved_to_other_side.emit(self.side))
        title.addWidget(self.swap)
        self.options = QPushButton("⚙")
        self.options.setToolTip("Préférences NovaBar")
        self.options.setFixedWidth(27)
        self.options.clicked.connect(self.settings_requested.emit)
        title.addWidget(self.options)
        layout.addLayout(title)
        self.heading = QLabel("DOSSIERS" if kind == "folders" else "APPLICATIONS")
        self.heading.setStyleSheet(f"color: {dock_colors(settings.theme)[0]}; "
                                   "font-size: 13px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(self.heading)
        self.items = DockItems(kind)
        self.items.itemClicked.connect(self.open_item)
        self.items.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.items.customContextMenuRequested.connect(self.show_item_menu)
        self.items.changed.connect(lambda values: self.entries_changed.emit(self.kind, values))
        layout.addWidget(self.items, 1)
        tip = QLabel("Déposez des dossiers ici" if kind == "folders" else "Déposez vos raccourcis .desktop ici")
        tip.setStyleSheet("color: #91adbf; font-size: 10px;")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        self.root.addWidget(self.content)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(3000)
        self.hide_timer.timeout.connect(self.collapse)
        self.pointer_timer = QTimer(self)
        self.pointer_timer.setInterval(120)
        self.pointer_timer.timeout.connect(self.check_pointer)
        self.pointer_timer.start()
        self.fx_timer = QTimer(self)
        self.fx_timer.setInterval(70)
        self.fx_timer.timeout.connect(self.animate_circuit)
        self.items_list = []
        self.set_items(self.default_items())
        self.place()

    def animate_circuit(self):
        if self.isVisible() and not self.collapsed:
            self.content.phase = (self.content.phase + .012) % 1
            self.content.update()
        else:
            self.fx_timer.stop()

    def apply_theme(self):
        """Repaint every neon surface when the global HUD palette changes."""
        self.content.settings = self.settings
        self.content.setStyleSheet(dock_stylesheet(self.settings.theme))
        self.heading.setStyleSheet(
            f"color: {dock_colors(self.settings.theme)[0]}; "
            "font-size: 13px; font-weight: bold; letter-spacing: 1px;")
        self.content.update()
        self.update()

    def default_items(self):
        saved = self.settings.dock_folder_paths if self.kind == "folders" else self.settings.dock_app_paths
        return list(saved) if saved is not None else (default_folders() if self.kind == "folders" else desktop_apps())

    def set_items(self, values):
        paths = []
        for value in values:
            if value == "recent:///" and self.kind == "folders":
                paths.append(value)
            elif value in normalized_drop([value], self.kind):
                paths.append(value)
        self.items.clear()
        provider = QFileIconProvider()
        for value in dict.fromkeys(paths):
            if value == "recent:///":
                label, ico = "Récents", QIcon.fromTheme("document-open-recent")
            elif self.kind == "folders":
                p = Path(value)
                label, ico = ("Dossier personnel" if p == Path.home() else p.name), provider.icon(QFileInfo(str(p)))
            else:
                p = Path(value)
                if p.suffix.lower() == ".desktop":
                    metadata = launcher_metadata(p)
                    if metadata is None:
                        continue
                    label, icon_name = metadata
                    ico = QIcon(icon_name) if icon_name.startswith("/") else QIcon.fromTheme(icon_name)
                    if ico.isNull(): ico = provider.icon(QFileInfo(str(p)))
                else:
                    label, ico = p.stem, provider.icon(QFileInfo(str(p)))
            item = QListWidgetItem(ico, label)
            item.setData(Qt.ItemDataRole.UserRole, value)
            item.setToolTip(value)
            self.items.addItem(item)

    def open_item(self, item):
        launch_item(item.data(Qt.ItemDataRole.UserRole), self.kind)
        self.hide_timer.start(3000)

    def show_item_menu(self, pos):
        menu = QMenu(self.items)
        add = menu.addAction("Ajouter un raccourci…")
        selected = self.items.itemAt(pos)
        remove = menu.addAction("Retirer ce raccourci") if selected else None
        action = menu.exec(self.items.mapToGlobal(pos))
        if action == add:
            if self.kind == "folders":
                chosen = QFileDialog.getExistingDirectory(self, "Ajouter un dossier", str(Path.home()))
            else:
                filters = "Raccourcis (*.desktop)" if sys.platform.startswith("linux") else (
                    "Raccourcis (*.lnk *.url)" if sys.platform == "win32" else "Applications (*.app)")
                chosen, _ = QFileDialog.getOpenFileName(self, "Ajouter une application", str(xdg_folder("DESKTOP")), filters)
            if chosen:
                self.entries_changed.emit(self.kind, self.items.values() + [chosen])
        elif remove is not None and action == remove:
            values = self.items.values()
            values.remove(selected.data(Qt.ItemDataRole.UserRole))
            self.entries_changed.emit(self.kind, values)

    def place(self):
        screens = QApplication.screens()
        if not screens: return
        screen = screens[min(self.settings.screen, len(screens)-1)]
        bounds = screen.geometry()
        # Sidebars stay below a top HUD and above a bottom HUD when enabled.
        top = bounds.top() + (self.settings.thickness if self.settings.hud_enabled and self.settings.position == "top" else 0)
        bottom = bounds.bottom() - (self.settings.thickness if self.settings.hud_enabled and self.settings.position == "bottom" else 0)
        if getattr(self.settings, "bottom_dock_enabled", False):
            from .bottom_dock import bottom_height
            bottom -= bottom_height(self.settings)
        height = max(120, bottom-top+1)
        x = bounds.left() if self.side == "left" else bounds.right()-self.panel_width+1
        self.full_rect = (x, top, self.panel_width, height)
        self.collapse()
        if self.isVisible():
            from .overlay import schedule_all_workspaces
            schedule_all_workspaces(self)

    def expand(self):
        if not self.collapsed or not self.full_rect: return
        self.collapsed = False
        self.hide_timer.stop()
        # Release the edge-only width constraint before showing the content.
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        self.setGeometry(*self.full_rect)
        self.content.show()
        self.show()
        self.fx_timer.start()
        self.update()

    def collapse(self):
        if not self.full_rect: return
        self.collapsed = True
        self.hide_timer.stop()
        x, y, width, height = self.full_rect
        self.content.hide()
        self.fx_timer.stop()
        # QWidget layout hints can otherwise keep a 170+ px invisible dock
        # even after the entire body has been hidden.
        self.setFixedWidth(self.edge_width)
        self.setGeometry(x if self.side == "left" else x+width-self.edge_width, y, self.edge_width, height)
        self.hide()
        self.update()

    def edge_trigger_rect(self):
        if not self.full_rect:
            return QRect()
        x, y, width, height = self.full_rect
        return QRect(x if self.side == "left" else x+width-10, y, 10, height)

    def check_pointer(self):
        if not self.full_rect:
            return
        if QApplication.activePopupWidget() is not None:
            self.hide_timer.stop()
            return
        inside = (self.edge_trigger_rect() if self.collapsed else self.geometry()).contains(QCursor.pos())
        if self.collapsed:
            if inside:
                self.expand()
        elif inside:
            self.hide_timer.stop()
        elif not self.hide_timer.isActive():
            self.hide_timer.start(3000)

    def enterEvent(self, event):
        if self.collapsed: self.expand()
        self.hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.collapsed: self.hide_timer.start(3000)
        super().leaveEvent(event)

    def paintEvent(self, event):
        # A collapsed dock is hidden. No painted grip and no input-catching strip.
        pass

    def showEvent(self, event):
        super().showEvent(event)
        if self.settings.always_on_top:
            from .overlay import mark_desktop_panel
            mark_desktop_panel(self)
        apply_priority(self, self.settings.always_on_top)
        from .overlay import schedule_all_workspaces
        schedule_all_workspaces(self)

    def closeEvent(self, event):
        self.hide_timer.stop()
        self.pointer_timer.stop()
        self.fx_timer.stop()
        super().closeEvent(event)
