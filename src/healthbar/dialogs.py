from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox,
    QSpinBox, QSlider, QCheckBox, QDialogButtonBox, QPushButton, QFileDialog,
    QMessageBox, QListWidget, QHBoxLayout, QTabWidget, QWidget, QLineEdit)
from . import __version__
from .autostart import set_enabled
from .plugins import PluginRegistry

STYLE = """
QDialog { background: #061224; color: #dfedff; }
QTabWidget::pane { border: 1px solid #17639b; border-radius: 8px; padding: 15px; }
QTabBar::tab { color: #c6eaff; padding: 10px 13px; background: #091b32; border: 1px solid #17639b; }
QTabBar::tab:selected { background: #104377; color: #31dcff; border-bottom: 2px solid #21ceff; }
QLineEdit { color: #e4f2ff; background: #0b2440; border: 1px solid #17639b; padding: 8px; }
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
        self.setMinimumWidth(630)
        self.resize(710, 630)
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
        self.position.addItems(["Haut", "Bas", "Droite • verticale", "Gauche • verticale"])
        self.position.setCurrentIndex(("top", "bottom", "right", "left").index(settings.position))
        form.addRow("Placement", self.position)
        self.screen = QComboBox()
        self.screen.addItems([f"Écran {i+1} • {s.name()}" for i, s in enumerate(screens)])
        self.screen.setCurrentIndex(min(settings.screen, len(screens)-1))
        form.addRow("Écran", self.screen)
        self.thickness = QSpinBox()
        self.thickness.setRange(50, 150)
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
        if __import__("os").environ.get("NOVABAR_PACKAGED") == "flatpak":
            self.autostart.setEnabled(False)
            self.autostart.setToolTip("Démarrage automatique non géré dans cette édition Flatpak.")
        
        self.hide_seconds = QSpinBox()
        self.hide_seconds.setRange(3, 120)
        self.hide_seconds.setValue(settings.hide_seconds)
        self.hide_seconds.setSuffix(" secondes")
        form.addRow("Délai avant veille", self.hide_seconds)
        self.length_percent = QSpinBox()
        self.length_percent.setRange(25, 100)
        self.length_percent.setValue(settings.length_percent)
        self.length_percent.setSuffix(" % écran")
        form.addRow("Longueur", self.length_percent)
        self.alignment = QComboBox()
        self.alignment.addItems(["Left", "Middle", "Right"])
        self.alignment.setCurrentIndex(("left", "center", "right").index(settings.alignment))
        form.addRow("Alignement", self.alignment)
        tabs = QTabWidget()
        general = QWidget()
        general_form = QFormLayout(general)
        general_form.addRow("Démarrage", self.autostart)
        self.refresh_seconds = QSpinBox()
        self.refresh_seconds.setRange(1, 30)
        self.refresh_seconds.setSuffix(" s")
        self.refresh_seconds.setValue(settings.refresh_seconds)
        general_form.addRow("Actualisation", self.refresh_seconds)
        self.shell_dir = QLineEdit(settings.shell_dir)
        self.shell_dir.setPlaceholderText("~/Scripts/HardwareHealth")
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.shell_dir)
        browse = QPushButton("Parcourir")
        browse.clicked.connect(self.choose_script_folder)
        folder_row.addWidget(browse)
        general_form.addRow("Dossier Shell", folder_row)
        general_form.addRow("Thème actif", QLabel("CYBER-FUTURISTE • Electric Blue"))
        update_button = QPushButton("Mises à jour…")
        update_button.clicked.connect(self.open_updates)
        general_form.addRow("CYBER NEXUS HUD", update_button)
        from .help_links import WIKI_URL
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        wiki_button = QPushButton("📖 Ouvrir le Wiki NovaBar")
        wiki_button.setToolTip("Guide : installation, interface, capteurs, plugins, dépannage")
        wiki_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(WIKI_URL)))
        general_form.addRow("Documentation", wiki_button)
        installer_button = QPushButton("Profil, confidentialité et raccourcis…")
        installer_button.clicked.connect(self.open_installer)
        if __import__("os").environ.get("NOVABAR_PACKAGED") in ("deb", "flatpak"):
            installer_button.setEnabled(False)
            installer_button.setToolTip("Le paquet Linux gère les fichiers du programme ; utiliser les préférences et le gestionnaire de plugins.")
        general_form.addRow("NovaBar", installer_button)
        display = QWidget()
        display.setLayout(form)
        edit = QWidget()
        editor = QVBoxLayout(edit)
        editor.addWidget(QLabel("ÉDITION DU HUD • réglages rapides"))
        tip = QLabel("La présentation se compacte automatiquement lorsque la longueur diminue.")
        tip.setWordWrap(True)
        editor.addWidget(tip)
        reset = QPushButton("Rétablir l'affichage d'origine")
        reset.clicked.connect(self.reset_display)
        editor.addWidget(reset)
        editor.addStretch()
        extensions = QWidget()
        ext_layout = QVBoxLayout(extensions)
        ext_layout.addWidget(QLabel("Importer des ZIP v2, activer les plugins et restaurer une version."))
        open_ext = QPushButton("OUVRIR LE PLUGIN MANAGER")
        open_ext.clicked.connect(lambda: PluginsDialog(PluginRegistry(), self).exec())
        ext_layout.addWidget(open_ext)
        ext_layout.addStretch()
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        howto = QLabel("Bord de l'écran : révéler la barre\nCarré flèche : agrandir / réduire\nTurbo : disponible uniquement avec contrôleur certifié\nZIP : code jamais exécuté automatiquement")
        howto.setWordWrap(True)
        help_layout.addWidget(howto)
        help_layout.addStretch()
        for name, widget in (("Générale", general), ("Affichage", display),
                              ("Édition", edit), ("Extensions", extensions), ("Aide", help_tab)):
            tabs.addTab(widget, name)
        box.addWidget(tabs, 1)
        note = QLabel("Les mesures affichées sont une maquette statique.\nAucun plugin matériel ni contrôle Turbo n’est activé dans cette version.")
        note.setWordWrap(True)
        box.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Installer et ouvrir" if first_run else "Enregistrer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)

    def open_updates(self):
        from .updates import UpdateDialog
        UpdateDialog(self).exec()

    def open_installer(self):
        from .installer import InstallerWizard
        from .profiles import workspace_dir, current_profile
        import json
        wizard = InstallerWizard(self.settings, parent=self)
        path = workspace_dir() / "App/Profiles" / (current_profile() + ".json")
        if path.is_file():
            record = json.loads(path.read_text(encoding="utf-8"))
            identity = record.get("identity", {})
            wizard.email.setText(identity.get("email", ""))
            wizard.username.setText(identity.get("username", ""))
            wizard.share.setChecked(identity.get("share_experience", False))
        # Editing the profile uses the first page and preserves installed runtime files.
        def save_profile_settings():
            from .profiles import save_profile
            from dataclasses import asdict, replace
            if wizard.stack.currentIndex() == 0:
                wizard.advance()
                if wizard.stack.currentIndex() == 1:
                    wizard.next.setText("ENREGISTRER")
            elif wizard.stack.currentIndex() == 1:
                try:
                    changed = replace(self.settings, position=wizard.position.currentData(),
                        thickness=wizard.thickness.value(), length_percent=wizard.length.value(),
                        opacity=wizard.opacity.value(), auto_hide=wizard.auto_hide.isChecked(),
                        autostart=wizard.autostart.isChecked(), shortcuts=wizard.bindings()).validate()
                    set_enabled(changed.autostart)
                    changed.save()
                    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
                    save_profile(wizard.identity, asdict(changed), previous.get("installation"))
                    self.settings.__dict__.update(changed.__dict__)
                    wizard.accept()
                except (ValueError, OSError) as error:
                    QMessageBox.warning(wizard, "Profil", str(error))
        wizard.next.clicked.disconnect()
        wizard.next.clicked.connect(save_profile_settings)
        wizard.autostart.setChecked(self.settings.autostart)
        wizard.next.setText("VALIDER")
        if wizard.exec() == QDialog.DialogCode.Accepted:
            self.accept()

    def choose_script_folder(self):
        chosen = QFileDialog.getExistingDirectory(self, "Dossier de scripts Shell", self.shell_dir.text())
        if chosen:
            self.shell_dir.setText(chosen)

    def reset_display(self):
        self.length_percent.setValue(100)
        self.thickness.setValue(72)
        self.opacity.setValue(88)
        self.hide_seconds.setValue(15)

    def save(self):
        from dataclasses import replace
        updated = replace(self.settings, position=("top", "bottom", "right", "left")[self.position.currentIndex()],
            screen=self.screen.currentIndex(), thickness=self.thickness.value(), opacity=self.opacity.value(),
            auto_hide=self.auto_hide.isChecked(), hide_seconds=self.hide_seconds.value(),
            autostart=self.autostart.isChecked(), configured=True,
            length_percent=self.length_percent.value(),
            alignment=("left", "center", "right")[self.alignment.currentIndex()],
            refresh_seconds=self.refresh_seconds.value(), shell_dir=self.shell_dir.text().strip())
        try:
            set_enabled(updated.autostart)
            updated.save()
        except OSError as error:
            QMessageBox.warning(self, "Enregistrement impossible", str(error))
            return
        self.settings.__dict__.update(updated.__dict__)
        self.accept()


# Plugin Manager v0.3.3 uses one compact two-tab dialog, independent of the installer.
# Import here keeps the existing app/settings interface stable.
from .plugin_manager import PluginsDialog
