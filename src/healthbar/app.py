"""Native transparent shell. Hardware providers are intentionally absent in v0.1."""
import argparse
import os
import sys
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


class Bar(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.registry = PluginRegistry()
        self.retracted = False
        self.expanded = False
        self.busy = False
        self.setWindowTitle("Health & Perfs • Prototype")
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
        self.expand_button = QPushButton()
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

    def make_button(self, kind, tooltip, callback):
        button = QPushButton()
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
        self.root.setDirection(QHBoxLayout.Direction.TopToBottom if vertical else QHBoxLayout.Direction.LeftToRight)
        self.actions.setFixedWidth(thickness-12 if vertical else min(400, max(290, g.width()//5)))
        if vertical:
            self.button_layout.setDirection(QHBoxLayout.Direction.TopToBottom)
            self.actions.setFixedHeight(410)
            self.buttons.setFixedHeight(320)
            self.turbo.setFixedSize(min(125, thickness-30), 48)
            self.full_rect = QRect(g.right()-thickness+1, g.top(), thickness, g.height())
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
            self.full_rect = QRect(g.left(), y, g.width(), thickness)
        self.setGeometry(self.full_rect)
        self.update()
        self.arm_hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor("#020b1c")
        bg.setAlpha(round(255*self.settings.opacity/100))
        p.fillRect(self.rect(), bg)
        p.setPen(QPen(QColor("#008dff"), 1))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 14, 14)
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
        box = QMessageBox(self)
        box.setWindowTitle("Console • emplacement réservé")
        box.setText("La console sera apportée par une future extension.\nAucune commande système n’est exécutée par cette maquette.")
        self.run_dialog(box)

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
