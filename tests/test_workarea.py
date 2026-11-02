"""Visible HUD reservation and graphite title controls across window states."""
import os,tempfile,unittest
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt,QRect,QPoint
from PySide6.QtWidgets import QApplication
from healthbar.workarea import top_strut
from healthbar.config import Settings
from healthbar.app import Bar
from nova_nexus.terminal_manager import open_manager

class WorkareaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_native_struts_include_only_visible_height_and_monitor_span(self):
        root=QRect(0,0,3840,1080)
        for height in (70,10,90):
            value=top_strut(QRect(1920,0,1920,height),root)
            self.assertEqual(value,[0,0,height,0,0,0,0,0,1920,3839,0,0])
        self.assertEqual(top_strut(QRect(0,1080,1920,70),QRect(0,0,1920,2160)),[0]*12)
        self.assertEqual(top_strut(QRect(-200,0,500,70),root)[8:10],[0,299])
        self.assertEqual(top_strut(QRect(0,0,0,70),root),[0]*12)

    def test_hud_retracts_to_ten_and_restores_configured_height(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=temp):
            bar=Bar(Settings(configured=True,thickness=70,auto_hide=False,retract_mode='manual',dock_left_enabled=False,dock_right_enabled=False,bottom_dock_enabled=False))
            try:
                if __import__("sys").platform.startswith("linux"):
                    self.assertTrue(bar.testAttribute(Qt.WidgetAttribute.WA_X11NetWmWindowTypeDock))
                bar.animation.setDuration(0);bar.show();self.app.processEvents()
                bar.retract(manual=True);self.app.processEvents()
                self.assertEqual(bar.height(),10)
                bar.reveal();self.app.processEvents();self.assertEqual(bar.height(),70)
            finally:bar.close()

    def test_title_controls_stay_inside_graphite_strip_and_modes_use_workarea(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=temp):
            manager=open_manager(start=False);window=manager.window
            def assert_header():
                self.app.processEvents()
                band=QRect(6,6,window.width()-12,39)
                for button in (window.minbtn,window.maxbtn,window.closebtn):
                    rect=QRect(button.mapTo(window,QPoint(0,0)),button.size())
                    self.assertTrue(band.contains(rect),(band,rect))
                    self.assertIs(button.parentWidget(),window.bar)
            try:
                for size in ((1100,700),(1920,1080),(900,1000)):
                    window.resize(*size);assert_header()
                manager.set_format('grid');self.app.processEvents()
                self.assertTrue(window.isMaximized());self.assertFalse(window.isFullScreen());assert_header()
                manager.toggle_fullscreen();self.app.processEvents();self.assertFalse(window.isMaximized());assert_header()
                # Even an external transition into real full screen cannot displace the controls.
                window.showFullScreen();assert_header()
                manager.toggle_fullscreen();self.app.processEvents();self.assertFalse(window.isFullScreen())
            finally:window.close()
