import os
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from nova_nexus.notification_center import NotificationCenter


class NotificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_quiet_history_is_persistent_and_bounded(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=tmp):
            center=NotificationCenter();center.set_quiet(True)
            for i in range(205):center.notify(str(i),'message')
            self.assertEqual(len(center.history),200)
            self.assertEqual(center.active,{})
            restored=NotificationCenter()
            self.assertTrue(restored.quiet)
            self.assertEqual(restored.history[-1]['title'],'204')
    def test_replacement_keeps_one_popup_and_position_is_configurable(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=tmp):
            center=NotificationCenter()
            identifier=center.notify('Initial','message',timeout=0)
            replacement=center.notify('Updated','message',replace=identifier,timeout=0)
            self.assertEqual(identifier,replacement)
            self.assertEqual(len(center.active),1)
            center.set_position('bottom-left')
            self.app.processEvents()
            self.assertIn(identifier,center.active)
            center.dismiss(identifier)
            self.app.processEvents()
            self.assertEqual(center.active,{})
