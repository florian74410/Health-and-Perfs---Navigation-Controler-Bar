import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from healthbar.config import Settings, data_dir
from healthbar.plugins import PluginRegistry
from healthbar.autostart import desktop_quote


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, HEALTHBAR_DATA_DIR=str(self.root))
        self.env.start()
        self.registry = PluginRegistry(self.root / "plugins")

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def package(self, version="1.0.0", **changes):
        manifest = dict(id="test-slot", name="Test slot", slot="cpu", version=version,
                        api_version=1, kind="declarative")
        manifest.update(changes)
        path = self.root / (version + ".hbp")
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
        return path

    def test_update_preserves_activation_and_rollback_restores_version(self):
        first = self.package()
        _, digest = self.registry.inspect(first)
        self.registry.install(first, digest)
        self.assertFalse(self.registry.installed()[0]["enabled"])
        self.registry.set_enabled("test-slot", True)
        second = self.package("1.1.0")
        self.registry.install(second, self.registry.inspect(second)[1])
        self.assertTrue(self.registry.installed()[0]["enabled"])
        self.assertEqual(self.registry.installed()[0]["version"], "1.1.0")
        self.registry.rollback("test-slot")
        self.assertEqual(self.registry.installed()[0]["version"], "1.0.0")
        self.assertTrue(self.registry.installed()[0]["enabled"])

    def test_failed_update_leaves_current_version(self):
        first = self.package()
        self.registry.install(first, self.registry.inspect(first)[1])
        with self.assertRaises(ValueError):
            self.registry.install(first, "incorrect-digest")
        with self.assertRaises(ValueError):
            self.registry.install(first, self.registry.inspect(first)[1])
        self.assertEqual(self.registry.installed()[0]["version"], "1.0.0")

    def test_rejects_paths_executable_payloads_api_and_invalid_ids(self):
        archive = self.root / "unsafe.hbp"
        for member in ("../manifest.json", "/manifest.json", "folder\\manifest.json", "main.py"):
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr(member, "{}")
            with self.assertRaises(ValueError):
                self.registry.inspect(archive)
        for changes in ({"api_version": 2}, {"api_version": True}, {"id": "../escape"},
                        {"slot": "unknown"}, {"kind": "python"}):
            with self.assertRaises(ValueError):
                self.registry.inspect(self.package(**changes))
        self.assertEqual(self.registry.installed(), [])

    def test_rename_failure_restores_previous_installation(self):
        first = self.package()
        self.registry.install(first, self.registry.inspect(first)[1])
        second = self.package("1.1.0")
        original = Path.rename
        def fail_stage(path, destination):
            if path.parent.name.startswith(".stage-"):
                raise OSError("simulated disk error")
            return original(path, destination)
        with patch.object(Path, "rename", fail_stage):
            with self.assertRaises(OSError):
                self.registry.install(second, self.registry.inspect(second)[1])
        self.assertEqual(self.registry.installed()[0]["version"], "1.0.0")

    def test_preferences_and_corruption_recovery(self):
        s = Settings(opacity=53, position="bottom", configured=True)
        s.save()
        self.assertEqual(Settings.load(), s)
        (data_dir() / "settings.json").write_text('{"thickness": "bad"}')
        self.assertEqual(Settings.load(), Settings())
        with self.assertRaises(ValueError):
            Settings(opacity=101).save()

    def test_linux_autostart_quoting_and_remove(self):
        from healthbar import autostart
        with patch.dict(os.environ, XDG_CONFIG_HOME=str(self.root)), patch.object(autostart.sys, "platform", "linux"), patch.object(autostart, "launch_command", return_value=['/tmp/path with spaces/$x%`/python', '-m', 'healthbar']):
            autostart.set_enabled(True)
            desktop = self.root / "autostart/health-perfs-bar.desktop"
            content = desktop.read_text()
            self.assertIn('\\$x%%\\`', content)
            self.assertIn('"-m" "healthbar"', content)
            autostart.set_enabled(False)
            self.assertFalse(desktop.exists())


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QDialog
from healthbar.app import Bar
from healthbar.dialogs import SettingsDialog


class ShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, HEALTHBAR_DATA_DIR=self.temp.name)
        self.env.start()
        self.settings = Settings(configured=True, auto_hide=False)
        self.bar = Bar(self.settings)
        self.bar.show()
        self.app.processEvents()

    def tearDown(self):
        self.bar.hide_timer.stop()
        self.bar.edge_timer.stop()
        self.bar.tray.hide()
        self.bar.close()
        self.env.stop()
        self.temp.cleanup()

    def test_all_placements_and_resize_have_visible_commands(self):
        for position in ("top", "bottom", "right"):
            self.settings.position = position
            self.bar.apply_settings()
            self.app.processEvents()
            self.assertEqual(self.bar.canvas.vertical, position == "right")
            for i in range(self.bar.button_layout.count()):
                button = self.bar.button_layout.itemAt(i).widget()
                self.assertTrue(button.isVisible())
                self.assertTrue(self.bar.buttons.rect().contains(button.geometry()), (position, button.geometry(), self.bar.buttons.rect()))
            self.assertFalse(self.bar.grab().isNull())

    def test_compact_and_large_render(self):
        for width in (800, 1024, 1366, 2048):
            self.bar.resize(width, 200)
            self.app.processEvents()
            self.assertFalse(self.bar.grab().isNull())

    def test_background_is_clear_and_only_module_fills_follow_opacity(self):
        from PySide6.QtCore import QPoint
        for opacity in (0, 35, 100):
            self.settings.opacity = opacity
            self.bar.apply_settings()
            self.bar.resize(2048, 200)
            self.app.processEvents()
            image = self.bar.grab().toImage()
            canvas = self.bar.canvas
            inside = canvas.mapTo(self.bar, QPoint(int(80*canvas.width()/1580),
                                                   int(90*canvas.height()/200)))
            blank = self.bar.actions.mapTo(self.bar, QPoint(10, 150))
            button_fill = self.bar.turbo.mapTo(self.bar, QPoint(8, 40))
            self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
            self.assertEqual(image.pixelColor(blank).alpha(), 0)
            self.assertAlmostEqual(image.pixelColor(inside).alpha(), round(255*opacity/100), delta=1)
            self.assertAlmostEqual(image.pixelColor(button_fill).alpha(), round(255*opacity/100), delta=1)
            # Text remains visible even when the module background is completely clear.
            text_rect = QRect(int(100*canvas.width()/1580), int(98*canvas.height()/200),
                              int(48*canvas.width()/1580), int(26*canvas.height()/200))
            opaque_text = sum(image.pixelColor(canvas.mapTo(self.bar, QPoint(x, y))).alpha() == 255
                              for x in range(text_rect.left(), text_rect.right())
                              for y in range(text_rect.top(), text_rect.bottom()))
            self.assertGreater(opaque_text, 50)

    def test_retract_and_reveal_geometry(self):
        self.settings.auto_hide = True
        with patch('healthbar.app.QCursor.pos', return_value=self.bar.full_rect.bottomRight() * 10):
            for position in ("top", "bottom", "right"):
                self.settings.position = position
                self.bar.apply_settings()
                full = QRect(self.bar.full_rect)
                self.bar.retract()
                self.assertTrue(self.bar.retracted)
                self.bar.animation.setCurrentTime(260)
                hidden = self.bar.geometry()
                self.assertEqual(hidden.width(), full.width())
                self.assertEqual(hidden.height(), full.height())
                self.bar.reveal()
                self.bar.animation.setCurrentTime(260)
                self.assertEqual(self.bar.geometry(), full)

    def test_preferences_save_and_cancel(self):
        dialog = SettingsDialog(self.settings, self.app.screens(), first_run=True)
        dialog.opacity.setValue(42)
        dialog.reject()
        self.assertEqual(self.settings.opacity, 88)
        with patch('healthbar.dialogs.set_enabled') as register:
            dialog.save()
        register.assert_called_once_with(False)
        self.assertEqual(self.settings.opacity, 42)
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)


if __name__ == '__main__':
    unittest.main()
