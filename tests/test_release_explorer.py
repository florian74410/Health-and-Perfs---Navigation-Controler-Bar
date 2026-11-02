import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from nova_nexus.explorer import run


class ExplorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_tabs_breadcrumbs_and_favorites(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,HEALTHBAR_DATA_DIR=tmp):
            root=Path(tmp).resolve();child=root/'folder';child.mkdir()
            window=run(root,embedded=True)
            try:
                window.add_tab(child)
                self.assertEqual(window.tabs.count(),2)
                self.assertEqual(window.address.text(),str(child))
                window.add_favorite()
                self.assertIn(str(child),window.favorites)
                window.tabs.setCurrentIndex(0)
                self.assertEqual(window.address.text(),str(root))
                self.assertGreater(window.crumb_layout.count(),1)
                window.close_tab(1)
                self.assertEqual(window.tabs.count(),1)
            finally:window.close()
