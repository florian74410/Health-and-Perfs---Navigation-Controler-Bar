"""Native transparent PCB-style HUD with nonblocking read-only sensor polling."""
import argparse
import os
import sys
import time
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve, QLockFile
from PySide6.QtGui import (QColor, QCursor, QDesktopServices, QIcon, QPainter, QPen,
                          QPixmap, QPainterPath)
from PySide6.QtCore import QPointF, QRectF, QUrl
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QMenu, QSystemTrayIcon, QDialog, QMessageBox)
from .config import Settings, data_dir
from .dialogs import SettingsDialog, PluginsDialog, STYLE
from .plugins import PluginRegistry
from .hud import HudCanvas
from .telemetry import Telemetry


def button_icon(kind):
    pix = QPixmap(40, 40)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#24dbff"), 2))
    if kind == "terminal":
        p.drawLine(10, 11, 18, 19)
        p.drawLine(18, 19, 10, 27)
        p.drawLine(21, 28, 32, 28)
    elif kind == "folder":
        path = QPainterPath(QPointF(6, 31))
        for x, y in [(6, 10), (17, 10), (21, 14), (34, 14), (31, 31), (6, 31)]:
            path.lineTo(x, y)
        p.drawPath(path)
    elif kind == "grid":
        for x in (8, 23):
            for y in (8, 23):
                p.drawRoundedRect(QRectF(x, y, 10, 10), 1, 1)
    elif kind == "settings":
        p.drawEllipse(11, 11, 18, 18)
        p.drawEllipse(16, 16, 8, 8)
        for i in range(8):
            p.save()
            p.translate(20, 20)
            p.rotate(i*45)
            p.drawRect(QRectF(-2, -15, 4, 6))
            p.restore()
    elif kind == "expand":
        p.drawRect(8, 7, 24, 25)
        p.drawLine(20, 12, 20, 26)
        p.drawLine(13, 20, 20, 27)
        p.drawLine(20, 27, 27, 20)
    else:
        p.drawEllipse(9, 6, 23, 23)
        p.drawLine(10, 28, 5, 35)
        p.drawLine(16, 30, 11, 36)
        p.drawEllipse(18, 12, 7, 7)
    p.end()
    return QIcon(pix)


class NeonButton(QPushButton):
    """Paint the background ourselves, avoiding opaque native Windows QPushButton fills."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.panel_opacity = 88
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        background = QColor("#061020")
        background.setAlpha(round(255 * self.panel_opacity / 100))
        edge = QColor("#33dfff" if self.underMouse() else "#068cff")
        p.setBrush(background)
        p.setPen(QPen(edge, 1.6))
        panel = QRectF(self.rect()).adjusted(1.2, 1.2, -1.2, -1.2)
        p.drawRoundedRect(panel, 9, 9)
        icon = self.icon()
        if not icon.isNull():
            size = min(32, max(18, min(self.width(), self.height()) - 14))
            x = 8 if self.text() else (self.width() - size)//2
            icon.paint(p, QRect(x, (self.height()-size)//2, size, size))
        if self.text():
            p.setPen(QColor("#e7f3ff"))
            p.setFont(self.font())
            p.drawText(QRect(43, 0, max(0, self.width()-45), self.height()),
                       Qt.AlignmentFlag.AlignVCenter, self.text())
        p.end()


class Bar(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.registry = PluginRegistry()
        self.retracted = False
        self.expanded = False
        self.busy = False
        self.setWindowTitle("NovaBar • Hardware Health Controller")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(STYLE + """
            QPushButton#nav { border: 1px solid #008fff; border-radius: 9px;
                background: rgba(2,15,34,170); padding: 3px; }
            QPushButton#nav:hover { border: 2px solid #48eaff; background: #0b345a; }
            QMenu { background: #061427; color: #e2efff; border: 1px solid #009dff; padding: 6px; }
            QMenu::item { padding: 12px 22px; }
            QMenu::item:selected { background: #114fe3; border-radius: 5px; }
            QMenu::item:disabled { color: #6986a3; }
        """)
        self.root = QHBoxLayout(self)
        self.root.setContentsMargins(4, 4, 8, 4)
        self.root.setSpacing(8)
        self.canvas = HudCanvas(self.registry)
        self.canvas.slot_order = (settings.slot_order or self.canvas.ORIGINAL).copy()
        self.canvas.layout_changed.connect(self.save_layout)
        self.root.addWidget(self.canvas, 1)
        self.actions = QWidget()
        self.action_layout = QVBoxLayout(self.actions)
        self.action_layout.setContentsMargins(8, 16, 4, 8)
        self.action_layout.setSpacing(10)
        self.buttons = QWidget()
        self.button_layout = QHBoxLayout(self.buttons)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        self.turbo = self.make_button("turbo", "Turbo • prévu dans une prochaine version", self.turbo_menu)
        self.turbo.setText("TURBO⌄")
        self.turbo.setFixedWidth(125)
        self.make_button("terminal", "Console • emplacement réservé", self.console_info)
        self.make_button("folder", "Ouvrir le dossier de configuration", self.open_folder)
        self.make_button("grid", "Extensions • ajouter et mettre à jour", self.plugins)
        self.make_button("settings", "Préférences / installation", self.preferences)
        self.action_layout.addWidget(self.buttons)
        self.expand_button = NeonButton()
        self.expand_button.setObjectName("nav")
        self.expand_button.setIcon(button_icon("expand"))
        self.expand_button.setFixedSize(34, 29)
        self.expand_button.setToolTip("Agrandir / réduire la hauteur")
        self.expand_button.clicked.connect(self.toggle_expand)
        self.action_layout.addWidget(self.expand_button, 0, Qt.AlignmentFlag.AlignRight)
        self.action_layout.addStretch()
        self.root.addWidget(self.actions)
        self.animation = QPropertyAnimation(self, b"geometry", self)
        self.animation.setDuration(260)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.retract)
        self.edge_timer = QTimer(self)
        self.edge_timer.setInterval(120)
        self.edge_timer.timeout.connect(self.check_edge)
        self.edge_timer.start()
        self.tray = QSystemTrayIcon(button_icon("settings"), self)
        self.tray.setToolTip("Health & Perfs Bar • Prototype")
        tray_menu = QMenu(self)
        tray_menu.addAction("Afficher", self.reveal)
        tray_menu.addAction("Préférences", self.preferences)
        tray_menu.addAction("Extensions", self.plugins)
        tray_menu.addSeparator()
        tray_menu.addAction("Quitter", QApplication.instance().quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(lambda reason: self.reveal() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        app = QApplication.instance()
        app.screenAdded.connect(lambda screen: self.apply_settings())
        app.screenRemoved.connect(lambda screen: self.apply_settings())
        for screen in app.screens():
            screen.geometryChanged.connect(lambda rect: self.apply_settings())
        self.apply_settings()
        self.sensors = Telemetry()
        self.sensor_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="novabar-sensors")
        self.sensor_future = None
        self.last_sensor_request = 0.0
        self.sensor_timer = QTimer(self)
        self.sensor_timer.setInterval(250)
        self.sensor_timer.timeout.connect(self.poll_sensors)
        self.sensor_timer.start()

    def poll_sensors(self):
        if self.sensor_future is not None and self.sensor_future.done():
            try:
                self.canvas.set_telemetry(self.sensor_future.result())
            except (OSError, RuntimeError, ValueError):
                pass
            self.sensor_future = None
        now = time.monotonic()
        if self.sensor_future is None and now - self.last_sensor_request >= self.settings.refresh_seconds:
            self.last_sensor_request = now
            self.sensor_future = self.sensor_worker.submit(self.sensors.sample)

    def closeEvent(self, event):
        self.sensor_timer.stop()
        self.sensor_worker.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)

    def save_layout(self, order):
        self.settings.slot_order = order
        try:
            self.settings.save()
            folder = data_dir() / "App" / "Repports" / "NovaBar"
            folder.mkdir(parents=True, exist_ok=True)
            with (folder / "layout.log").open("a", encoding="utf-8") as log:
                log.write(f"{datetime.now().isoformat()} | {', '.join(order)}\n")
        except OSError as error:
            QMessageBox.warning(self, "Enregistrement", str(error))

    def make_button(self, kind, tooltip, callback):
        button = NeonButton()
        button.setObjectName("nav")
        button.setIcon(button_icon(kind))
        from PySide6.QtCore import QSize
        button.setIconSize(QSize(34, 34))
        button.setFixedSize(56, 58)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.clicked.connect(callback)
        self.button_layout.addWidget(button)
        return button

    def apply_settings(self):
        self.animation.stop()
        self.retracted = False
        screens = QApplication.screens()
        screen = screens[min(self.settings.screen, len(screens)-1)]
        g = screen.geometry()
        vertical = self.settings.position == "right"
        thickness = min(self.settings.thickness * (1.5 if self.expanded else 1),
                        g.width() if vertical else g.height())
        thickness = int(thickness)
        self.canvas.vertical = vertical
        self.canvas.module_opacity = self.settings.opacity
        self.canvas.update()
        for child in self.buttons.findChildren(NeonButton):
            child.panel_opacity = self.settings.opacity
            child.update()
        self.expand_button.panel_opacity = self.settings.opacity
        self.expand_button.update()
        alpha = round(255*self.settings.opacity/100)
        self.actions.setStyleSheet(f"""
            QPushButton#nav {{ background: rgba(2,15,34,{alpha}); }}
            QPushButton#nav:hover {{ background: rgba(11,52,90,{alpha}); }}
        """)
        self.root.setDirection(QHBoxLayout.Direction.TopToBottom if vertical else QHBoxLayout.Direction.LeftToRight)
        self.actions.setFixedWidth(thickness-12 if vertical else min(400, max(290, g.width()//5)))
        if vertical:
            self.button_layout.setDirection(QHBoxLayout.Direction.TopToBottom)
            self.actions.setFixedHeight(410)
            self.buttons.setFixedHeight(320)
            self.turbo.setFixedSize(min(125, thickness-30), 48)
            length = max(200, round(g.height()*self.settings.length_percent/100))
            shift = {"left": 0, "center": (g.height()-length)//2,
                     "right": g.height()-length}[self.settings.alignment]
            self.full_rect = QRect(g.right()-thickness+1, g.top()+shift, thickness, length)
        else:
            self.button_layout.setDirection(QHBoxLayout.Direction.LeftToRight)
            self.buttons.setFixedHeight(58)
            self.actions.setMinimumHeight(0)
            self.actions.setMaximumHeight(16777215)
            width = self.actions.width()
            turbo_width = 105 if width < 360 else 125
            size = max(28, min(56, (width-52-turbo_width)//4))
            for i in range(1, self.button_layout.count()):
                self.button_layout.itemAt(i).widget().setFixedSize(size, 58)
            self.turbo.setFixedSize(turbo_width, 58)
            y = g.top() if self.settings.position == "top" else g.bottom()-thickness+1
            length = max(250, round(g.width()*self.settings.length_percent/100))
            shift = {"left": 0, "center": (g.width()-length)//2,
                     "right": g.width()-length}[self.settings.alignment]
            self.full_rect = QRect(g.left()+shift, y, length, thickness)
        self.setGeometry(self.full_rect)
        self.update()
        self.arm_hide()

    def paintEvent(self, event):
        p = QPainter(self)
        # Clear every pixel outside the modules; no shared panel or outer rectangle.
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)
        p.end()

    def arm_hide(self):
        self.hide_timer.stop()
        if self.settings.auto_hide and not self.busy and not self.retracted:
            self.hide_timer.start(self.settings.hide_seconds*1000)

    def enterEvent(self, event):
        self.hide_timer.stop()
        self.reveal()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.arm_hide()
        super().leaveEvent(event)

    def retract(self):
        if self.busy or self.geometry().contains(QCursor.pos()) or QApplication.activePopupWidget():
            self.arm_hide()
            return
        if not self.settings.auto_hide:
            return
        rect = QRect(self.full_rect)
        if self.settings.position == "top":
            rect.translate(0, -rect.height()+4)
        elif self.settings.position == "bottom":
            rect.translate(0, rect.height()-4)
        else:
            rect.translate(rect.width()-4, 0)
        self.retracted = True
        self.animate(rect)

    def animate(self, rect):
        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(rect)
        self.animation.start()

    def reveal(self):
        if self.retracted:
            self.retracted = False
            self.animate(self.full_rect)
        self.show()
        self.arm_hide()

    def check_edge(self):
        if self.retracted and self.geometry().contains(QCursor.pos()):
            self.reveal()

    def toggle_expand(self):
        self.expanded = not self.expanded
        self.apply_settings()

    def run_dialog(self, dialog):
        self.busy = True
        self.hide_timer.stop()
        try:
            return dialog.exec()
        finally:
            self.busy = False
            self.arm_hide()

    def preferences(self):
        if self.run_dialog(SettingsDialog(self.settings, QApplication.screens(), parent=self)) == QDialog.DialogCode.Accepted:
            self.apply_settings()

    def plugins(self):
        self.run_dialog(PluginsDialog(self.registry, self))
        self.canvas.refresh_plugins()

    def open_folder(self):
        data_dir().mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir())))

    def console_info(self):
        folder = Path(self.settings.shell_dir).expanduser() if self.settings.shell_dir else (
            Path.home() / "Scripts" / "HardwareHealth")
        folder.mkdir(parents=True, exist_ok=True)
        allowed = {".py", ".sh", ".command"} if os.name != "nt" else {
            ".py", ".bat", ".cmd", ".ps1"}
        files = [p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in allowed]
        menu = QMenu(self)
        if not files:
            menu.addAction("Aucun script • sélectionnez un dossier dans Générale").setEnabled(False)
        for script in files[:40]:
            menu.addAction(script.name, lambda checked=False, p=script: self.run_script(p))
        menu.addSeparator()
        menu.addAction("Ouvrir le dossier", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))))
        self.busy = True
        self.hide_timer.stop()
        try:
            menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft())
                      if isinstance(self.sender(), QWidget) else QCursor.pos())
        finally:
            self.busy = False
            self.arm_hide()

    def run_script(self, path):
        root = Path(self.settings.shell_dir).expanduser() if self.settings.shell_dir else (
            Path.home() / "Scripts" / "HardwareHealth")
        path = Path(path).resolve()
        if root.resolve() != path.parent or not path.is_file():
            QMessageBox.warning(self, "Script refusé", "Le script doit être directement dans le dossier autorisé.")
            return
        confirm = QMessageBox.question(self, "Exécuter le script local ?", 
            f"Fichier : {path.name}\n\nCe script s'exécutera avec les droits de votre compte.\nContinuer ?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        if path.suffix.lower() == ".py":
            args = [sys.executable, str(path)]
        elif os.name == "nt":
            if path.suffix.lower() == ".ps1":
                args = ["powershell", "-NoProfile", "-File", str(path)]
            else:
                args = ["cmd", "/c", str(path)]
        else:
            args = ["/bin/sh", str(path)]
        folder = data_dir() / "App" / "Repports" / "NovaBar"
        folder.mkdir(parents=True, exist_ok=True)
        log = folder / ("shell-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
        try:
            with log.open("wb") as output:
                subprocess.Popen(args, cwd=path.parent, stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=subprocess.STDOUT,
                                 start_new_session=(os.name != "nt"))
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Exécution impossible", str(error))

    def turbo_menu(self):
        self.busy = True
        self.hide_timer.stop()
        menu = QMenu(self)
        for name in ("Activer", "Désactiver", "Mode Auto", "Paramètres…"):
            action = menu.addAction(name)
            action.setEnabled(False)
        menu.addSeparator()
        label = menu.addAction("Prototype • plugin Turbo à venir")
        label.setEnabled(False)
        try:
            menu.exec(self.turbo.mapToGlobal(self.turbo.rect().bottomLeft()))
        finally:
            self.busy = False
            self.arm_hide()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Préférences", self.preferences)
        menu.addAction("Extensions", self.plugins)
        menu.addAction("Quitter", QApplication.instance().quit)
        self.busy = True
        try:
            menu.exec(event.globalPos())
        finally:
            self.busy = False
            self.arm_hide()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="Reopen installation preferences")
    parser.add_argument("--preview", metavar="PNG", help="Render static HUD offscreen without changing user settings")
    args = parser.parse_args()
    if args.preview:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication(sys.argv[:1])
    app.setApplicationName("HealthPerfsBar")
    app.setOrganizationName("HealthPerfs")
    if args.preview:
        settings = Settings(configured=True, auto_hide=False)
    else:
        data_dir().mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(data_dir() / "session.lock"))
        if not lock.tryLock(100):
            QMessageBox.information(None, "Health & Perfs", "Une instance est déjà ouverte dans cette session.")
            return 0
        settings = Settings.load()
        if args.setup or not settings.configured:
            dialog = SettingsDialog(settings, app.screens(), first_run=not settings.configured)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return 0
    bar = Bar(settings)
    bar.show()
    if args.preview:
        bar.setGeometry(0, 0, 2048, 205)
        bar.actions.setFixedWidth(400)
        app.processEvents()
        if not bar.grab().save(args.preview):
            raise OSError("Impossible d’enregistrer l’aperçu")
        return 0
    return app.exec()
