"""Regression tests for the NOVA BlackRed overlay system."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from healthbar.theme_packs import (
    get_pack, list_packs, known_theme, asset_path, recolor_qss,
)


class BlackRedPackTests(unittest.TestCase):
    def tearDown(self):
        get_pack.cache_clear()
        asset_path.cache_clear()

    def test_builtin_pack_and_assets(self):
        pack = get_pack("blackred-neon")
        self.assertIsNotNone(pack)
        self.assertEqual(pack["palette"]["primary"], "#FF233E")
        self.assertIn("blackred-neon", list_packs())
        self.assertTrue(known_theme("blackred-neon"))
        for role in ("pcb", "frame", "button", "notification", "wallpaper"):
            self.assertTrue(asset_path("blackred-neon", role).is_file())

    def test_retint_never_changes_semantic_red_green_or_alpha(self):
        text = "A{background:rgba(8,32,62,210);color:rgba(39,239,125,255);border:rgba(255,40,70,170)}"
        converted = recolor_qss(text, "blackred-neon")
        self.assertNotIn("rgba(8,32,62,210)", converted)
        self.assertIn("210)", converted)
        self.assertIn("rgba(39,239,125,255)", converted)
        self.assertIn("rgba(255,40,70,170)", converted)
        self.assertEqual(recolor_qss(text, "blue-neon"), text)

    def test_external_skin_remains_in_user_profile(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"HEALTHBAR_DATA_DIR": tmp}):
            folder = Path(tmp) / "Themes" / "blackred-studio"
            folder.mkdir(parents=True)
            (folder / "pcb.svg").write_text("<svg/>", encoding="utf-8")
            manifest = {"id":"blackred-studio","name":"BlackRed Studio","version":"1",
                "palette":{"primary":"#FE1234","secondary":"#740C25","background":"#050506",
                           "surface":"#170A0D","text":"#F3F3F3"},
                "assets":{"pcb":"pcb.svg"}}
            (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            get_pack.cache_clear()
            asset_path.cache_clear()
            self.assertEqual(get_pack("blackred-studio")["name"], "BlackRed Studio")
            self.assertTrue(known_theme("blackred-studio"))
            self.assertEqual(asset_path("blackred-studio","pcb").parent,folder)
            manifest["assets"]["pcb"] = "../unsafe.svg"
            (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            get_pack.cache_clear()
            self.assertIsNone(get_pack("blackred-studio"))
            manifest["assets"]["pcb"] = "pcb.svg"
            manifest["palette"]["primary"] = "red"
            (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            get_pack.cache_clear()
            self.assertIsNone(get_pack("blackred-studio"))

    def test_config_rejects_unknown_theme_without_losing_existing(self):
        from healthbar.config import Settings
        self.assertEqual(Settings(theme="blackred-neon").validate().theme,"blackred-neon")
        with self.assertRaises(ValueError):
            Settings(theme="../../other").validate()


class TransparentWindowTests(unittest.TestCase):
    @unittest.skipUnless(os.getenv("QT_QPA_PLATFORM") == "offscreen", "Offscreen Qt QA only")
    def test_settings_corners_are_actually_transparent(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtCore import Qt
        from healthbar.settings_visual import PCBSettingsDialog
        app = QApplication.instance() or QApplication([])
        dialog = PCBSettingsDialog()
        dialog.resize(600, 420)
        dialog.use_pcb_theme("blackred-neon")
        image = QImage(600,420,QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        dialog.render(painter)
        painter.end()
        self.assertEqual(image.pixelColor(0,0).alpha(),0)
        self.assertEqual(image.pixelColor(599,0).alpha(),0)
        self.assertGreater(image.pixelColor(300,210).alpha(),0)
        dialog.close()


if __name__ == "__main__":
    unittest.main()
