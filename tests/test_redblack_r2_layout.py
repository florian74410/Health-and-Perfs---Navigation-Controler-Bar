"""REDBLACK R2: preserve compact controls and plugin hitbox contract."""
import os
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF

class RedBlackR2Layout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application=QApplication.instance() or QApplication(["r2-layout-tests"])

    def test_no_min_heights_or_padding_in_hud_and_dock(self):
        from healthbar.redblack_shell import control_stylesheet
        for name in ("hud","dock"):
            style=control_stylesheet(name)
            self.assertIn("padding:0",style)
            self.assertIn("min-height:0",style)
            self.assertNotIn("min-height:18px",style)
            self.assertNotIn("padding:7px 12px",style)
            self.assertNotIn("QListWidget#settingsNavigation",style)
        self.assertIn("QListWidget#settingsNavigation",control_stylesheet())

    def test_hud_visual_does_not_change_hitboxes(self):
        from healthbar.hud import HudCanvas
        from healthbar.plugins import PluginRegistry
        from healthbar.ui_kit import set_theme
        from healthbar.redblack_shell import paint_hud
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtCore import QRect
        from unittest.mock import patch
        with patch.object(PluginRegistry, "installed",return_value=[]):
            hud=HudCanvas(PluginRegistry())
        hud.resize(900,90)
        set_theme("redblack-0822")
        original={slot:hud.module_rect(slot) for slot in hud.active_slots}
        icons={slot:hud.module_icon_rect(slot) for slot in hud.active_slots}
        image=QImage(900,90,QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter=QPainter(image)
        paint_hud(painter,hud)
        painter.end()
        for slot in hud.active_slots:
            self.assertEqual(original[slot],hud.module_rect(slot))
            self.assertEqual(icons[slot],hud.module_icon_rect(slot))
            if not icons[slot].isEmpty():
                self.assertTrue(original[slot].contains(icons[slot]))
        hud.deleteLater()

    def test_graphite_color_contract(self):
        from healthbar.redblack_shell import DEEP,PANEL,CRIMSON,HOT
        self.assertEqual(DEEP,"#0D1015")
        self.assertEqual(PANEL,"#151920")
        self.assertEqual(CRIMSON,"#D42B43")
        self.assertEqual(HOT,"#E75E71")

if __name__=="__main__":unittest.main()
