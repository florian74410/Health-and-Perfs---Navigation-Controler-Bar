"""Window controls, complete XFWM exports and reversible existing-theme migration."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from shiboken6 import isValid
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6 import QtCore as C, QtWidgets as W
from nova_nexus import install_theme as install
from nova_nexus.chrome_v3 import make_dialog
from nova_nexus.explorer import run
from nova_nexus.terminal_manager import open_manager
from nova_nexus.xfwm4 import export_xfwm4_theme
from nova_nexus.desktop_theme import export_gtk_theme


class WindowControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = W.QApplication.instance() or W.QApplication([])

    def test_nova_windows_have_working_maximize_restore_minimize_close(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, HEALTHBAR_DATA_DIR=temp):
            manager = open_manager(start=False)
            for window in (manager.window, run(temp, embedded=True), make_dialog('Test', 'Contrôles')):
                try:
                    window.show(); self.app.processEvents()
                    normal = window.size()
                    window.maxbtn.click(); self.app.processEvents()
                    self.assertTrue(window.isMaximized())
                    self.assertEqual(window.maxbtn.accessibleName(), 'Restaurer')
                    window.maxbtn.click(); self.app.processEvents()
                    self.assertFalse(window.isMaximized())
                    self.assertEqual(window.size(), normal)
                    self.assertEqual(window.maxbtn.accessibleName(), 'Maximiser')
                    window.resize(730, 480); self.app.processEvents()
                    resized = window.size()
                    window.showMaximized(); self.app.processEvents()
                    window.maxbtn.click(); self.app.processEvents()
                    self.assertEqual(window.size(), resized)
                    window.minbtn.click(); self.app.processEvents()
                    self.assertTrue(window.isMinimized())
                    window.showNormal(); self.app.processEvents()
                    window.closebtn.click(); self.app.processEvents()
                    self.assertTrue(not isValid(window) or not window.isVisible())
                finally:
                    if isValid(window): window.close()

    def test_native_theme_all_title_segments_states_and_red_symbols(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = export_xfwm4_theme(temp)
            for state in ('active', 'inactive'):
                for part in range(1, 6):
                    self.assertTrue((directory / f'title-{part}-{state}.xpm').is_file())
            for state in ('active', 'inactive', 'prelight', 'pressed'):
                for name in ('hide', 'maximize', 'close', 'maximize-toggled'):
                    content = (directory / f'{name}-{state}.xpm').read_text()
                    self.assertIn('s c #FF526A', content)
                    self.assertIn('b c #00CBF3', content)
            self.assertNotEqual((directory/'maximize-active.xpm').read_text(),
                                (directory/'maximize-toggled-active.xpm').read_text())
            directory = export_gtk_theme(temp) / 'gtk-3.0'
            for name in ('close', 'maximize', 'restore', 'minimize'):
                self.assertIn('#FF526A', (directory/'assets'/f'{name}.svg').read_text())

    def test_migration_and_restore_keeps_original_theme_and_control_preferences(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(Path, 'home', return_value=Path(temp)):
            state = {('xfwm4', '/general/theme'): install.NAME,
                     ('xsettings', '/Net/ThemeName'): install.NAME,
                     ('xfwm4', '/general/button_layout'): 'CMH|O',
                     ('xfwm4', '/general/titleless_maximize'): 'true'}
            def set_value(channel, prop, kind, value):
                if value is None: state.pop((channel, prop), None)
                else: state[channel, prop] = value
            backup = install._state_path(); backup.parent.mkdir(parents=True)
            backup.write_text(json.dumps({'gtk': 'Mint-Y', 'xfwm4': 'Mint-Y-Dark'}))
            with patch.object(install, '_get', side_effect=lambda c,p:state.get((c,p))), patch.object(install, '_set', side_effect=set_value):
                self.assertTrue(install.refresh_selected_theme())
                self.assertTrue(install.refresh_selected_theme())
                self.assertEqual(state['xfwm4','/general/button_layout'], 'O|HMC')
                self.assertEqual(state['xfwm4','/general/titleless_maximize'], 'false')
                # A later user preference must survive rollback.
                state['xsettings','/Gtk/DecorationLayout'] = ':close'
                install.main(['--restore'])
            self.assertEqual(state['xfwm4','/general/theme'], 'Mint-Y-Dark')
            self.assertEqual(state['xfwm4','/general/button_layout'], 'CMH|O')
            self.assertEqual(state['xfwm4','/general/titleless_maximize'], 'true')
            self.assertEqual(state['xsettings','/Gtk/DecorationLayout'], ':close')

    def test_unselected_theme_is_never_activated_by_upgrade(self):
        with patch.object(install, '_get', return_value='Mint-Y'), patch.object(install, '_set') as setter:
            self.assertFalse(install.refresh_selected_theme())
            setter.assert_not_called()
