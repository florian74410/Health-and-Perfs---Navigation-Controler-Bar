"""RedBlack R2: keep real plugin geometry and clickable controls intact."""
import unittest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from healthbar.hud import HudCanvas
from healthbar.bottom_dock import _dock_control_metrics
from healthbar.config import Settings

class _Registry:
    def installed(self):
        return [{"slot":"cpu","name":"PROCESSEUR PERSONNALISÉ","enabled":True,"api_version":1}]

class R2Layout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication(["redblack-r2-layout"])

    def test_dock_buttons_never_shrink_under_25_px(self):
        for height in (62,70,84,100,130):
            margin,hit,glyph=_dock_control_metrics(height)
            self.assertGreaterEqual(hit,25)
            self.assertGreaterEqual(glyph,14)
            self.assertLess(glyph,hit)
            self.assertLessEqual(hit+2*margin,height)

    def test_plugin_rectangles_match_mouse_targets_at_any_height(self):
        canvas=HudCanvas(_Registry())
        self.assertIn("cpu",canvas.labels)
        for vertical,width,height in (
            (False,1600,72),(False,1200,150),(False,740,95),
            (False,360,60),(True,115,720),(True,85,430)
        ):
            canvas.vertical=vertical
            canvas.resize(width,height)
            canvas.slot_order=canvas.ORIGINAL.copy()+["power"]
            canvas.hidden_modules=[]
            areas=[]
            for slot in canvas.active_slots:
                area=canvas.module_rect(slot)
                self.assertGreater(area.width(),0,(slot,width,height))
                self.assertGreater(area.height(),0,(slot,width,height))
                self.assertEqual(canvas.active_slots[canvas.module_at(
                    QPointF(area.center()))],slot,(slot,width,height))
                icon=canvas.module_icon_rect(slot)
                self.assertTrue(area.contains(icon.center()),(slot,width,height))
                areas.append(area)
            for i,left in enumerate(areas):
                for right in areas[i+1:]:
                    self.assertFalse(left.intersects(right),(width,height,left,right))
        canvas.visual_timer.stop()
        canvas.close()

    def test_settings_keep_original_constraints(self):
        settings=Settings(theme="redblack-0822",thickness=50,bottom_dock_height=62)
        self.assertEqual(settings.validate().bottom_dock_height,62)

if __name__=="__main__":
    unittest.main()
