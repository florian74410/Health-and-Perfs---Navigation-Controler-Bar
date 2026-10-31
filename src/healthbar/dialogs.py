from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox,
    QSpinBox, QSlider, QCheckBox, QDialogButtonBox, QPushButton, QFileDialog,
    QMessageBox, QListWidget, QHBoxLayout)
from . import __version__
from .autostart import set_enabled

STYLE = """
QDialog { background: #061224; color: #dfedff; }
QLabel, QCheckBox { color: #c4d9f7; font-size: 13px; }
QLabel#title { color: #31dcff; font-size: 25px; font-weight: 700; }
QPushButton, QComboBox, QSpinBox { color: #dcecff; background: #0b2440;
 border: 1px solid #17639b; border-radius: 6px; padding: 9px; }
QPushButton:hover { border-color: #00ddff; background: #123960; }
QPushButton:disabled { color: #65798c; border-color: #19314a; }
QListWidget { background: #040d1b; color: #dcecff; border: 1px solid #17639b; padding: 8px; }
QSlider::groove:horizontal { height: 4px; background: #17476c; }
QSlider::handle:horizontal { width: 16px; margin: -6px 0; background: #14d8ff; border-radius: 8px; }
QCheckBox { spacing: 12px; }
"""


class SettingsDialog(QDialog):
    def __init__(self, settings, screens, first_run=False, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Installation • Health & Perfs" if first_run else "Préférences • Health & Perfs")
        self.setStyleSheet(STYLE)
        self.setMinimumWidth(510)
        box = QVBoxLayout(self)
        box.setContentsMargins(30, 26, 30, 26)
        box.setSpacing(20)
        title = QLabel("BIENVENUE À BORD" if first_run else "VOTRE BARRE. VOS RÈGLES.")
        title.setObjectName("title")
        box.addWidget(title)
        intro = QLabel("Health & Perfs  /  Navigation Controller Bar  /  v"+__version__
            + "\nInstallation pour votre session utilisateur. Les autres comptes\nconservent leurs propres préférences et extensions.")
        intro.setWordWrap(True)
        box.addWidget(intro)
        form = QFormLayout()
        form.setVerticalSpacing(16)
        self.position = QComboBox()
        self.position.addItems(["Haut", "Bas", "Droite • verticale"])
        self.position.setCurrentIndex(("top", "bottom", "right").index(settings.position))
        form.addRow("Placement", self.position)
        self.screen = QComboBox()
        self.screen.addItems([f"Écran {i+1} • {s.name()}" for i, s in enumerate(screens)])
        self.screen.setCurrentIndex(min(settings.screen, len(screens)-1))
        form.addRow("Écran", self.screen)
        self.thickness = QSpinBox()
        self.thickness.setRange(120, 360)
        self.thickness.setValue(settings.thickness)
        self.thickness.setSuffix(" px")
        form.addRow("Épaisseur", self.thickness)
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.setValue(settings.opacity)
        self.opacity_label = QLabel(f"{settings.opacity} %")
        self.opacity.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v} %"))
        row = QHBoxLayout()
        row.addWidget(self.opacity)
        row.addWidget(self.opacity_label)
        form.addRow("Opacité des modules", row)
        self.auto_hide = QCheckBox("Rétracter après 15 s sans survol")
        self.auto_hide.setChecked(settings.auto_hide)
        form.addRow("Rétractation", self.auto_hide)
        self.autostart = QCheckBox("Lancer à l’ouverture de ma session")
        self.autostart.setChecked(settings.autostart)
        form.addRow("Démarrage", self.autostart)
        box.addLayout(form)
        note = QLabel("Les mesures affichées sont une maquette statique.\nAucun plugin matériel ni contrôle Turbo n’est activé dans cette version.")
        note.setWordWrap(True)
        box.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Installer et ouvrir" if first_run else "Enregistrer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)

    def save(self):
        from dataclasses import replace
        updated = replace(self.settings, position=("top", "bottom", "right")[self.position.currentIndex()],
            screen=self.screen.currentIndex(), thickness=self.thickness.value(), opacity=self.opacity.value(),
            auto_hide=self.auto_hide.isChecked(), hide_seconds=15,
            autostart=self.autostart.isChecked(), configured=True)
        try:
            set_enabled(updated.autostart)
            updated.save()
        except OSError as error:
            QMessageBox.warning(self, "Enregistrement impossible", str(error))
            return
        self.settings.__dict__.update(updated.__dict__)
        self.accept()


class PluginsDialog(QDialog):
    def __init__(self, registry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self.setWindowTitle("Extensions • Health & Perfs")
        self.setStyleSheet(STYLE)
        self.resize(650, 440)
        box = QVBoxLayout(self)
        box.setContentsMargins(26, 26, 26, 26)
        title = QLabel("DOCK D’EXTENSIONS")
        title.setObjectName("title")
        box.addWidget(title)
        note = QLabel("API v1 • Ajouter ou mettre à jour un paquet local .hbp\nSocle déclaratif : réserve et nomme les emplacements ; aucun code de plugin exécuté.")
        note.setWordWrap(True)
        box.addWidget(note)
        self.list = QListWidget()
        box.addWidget(self.list)
        row = QHBoxLayout()
        for label, callback in [("Importer / Mettre à jour", self.import_package),
                                ("Activer / Désactiver", self.toggle), ("Version précédente", self.rollback)]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            row.addWidget(button)
        box.addLayout(row)
        close = QPushButton("Fermer")
        close.clicked.connect(self.accept)
        box.addWidget(close)
        self.refresh()

    def refresh(self):
        self.list.clear()
        self.items = self.registry.installed()
        if not self.items:
            self.list.addItem("Aucune extension installée. Les six emplacements du HUD sont réservés.")
        for item in self.items:
            self.list.addItem(f"{'●' if item['enabled'] else '○'}  {item['name']}  /  {item['version']}  /  {item['slot']}")

    def selected(self):
        i = self.list.currentRow()
        return self.items[i] if 0 <= i < len(self.items) else None

    def import_package(self):
        from zipfile import BadZipFile
        path, _ = QFileDialog.getOpenFileName(self, "Ajouter une extension", "", "HealthBar package (*.hbp *.zip)")
        if not path:
            return
        try:
            manifest, digest = self.registry.inspect(path)
            answer = QMessageBox.question(self, "Installer cette extension ?",
                f"{manifest['name']} • {manifest['version']}\nEmplacement : {manifest['slot']}\n"
                f"SHA-256 : {digest}\n\nPaquet local déclaratif. Une copie de la version précédente sera conservée.")
            if answer == QMessageBox.StandardButton.Yes:
                self.registry.install(path, digest)
                self.refresh()
        except (OSError, ValueError, BadZipFile, RuntimeError) as error:
            QMessageBox.warning(self, "Paquet refusé", str(error))

    def toggle(self):
        item = self.selected()
        if item:
            try:
                self.registry.set_enabled(item["id"], not item["enabled"])
                self.refresh()
            except (OSError, ValueError) as error:
                QMessageBox.warning(self, "Modification impossible", str(error))

    def rollback(self):
        item = self.selected()
        if item:
            try:
                self.registry.rollback(item["id"])
                self.refresh()
            except (OSError, ValueError) as error:
                QMessageBox.warning(self, "Restauration impossible", str(error))
