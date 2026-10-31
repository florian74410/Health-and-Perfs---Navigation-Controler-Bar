"""Installer completeness, directory routing, shell execution and layout persistence."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from healthbar.config import Settings
from healthbar.nova_components import component_manifest,verify_components
from nova_nexus.terminal import TerminalSession,TerminalView
from nova_nexus.terminal_manager import open_manager,FORMATS

class UnifiedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,HEALTHBAR_DATA_DIR=str(self.root/'data'))
        self.env.start()
    def tearDown(self):
        self.app.processEvents();self.env.stop();self.temp.cleanup()
    def wait(self,predicate,seconds=12):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            self.app.processEvents()
            if predicate():return
            time.sleep(.03)
        self.fail('Timed out waiting for interactive terminal')
    def test_components_render_and_list_eight_current_plugins(self):
        from scripts.build_plugins import build
        from healthbar.bundled_plugins import seed_bundled_plugins
        from healthbar.plugins import PluginRegistry
        plugins=self.root/'bundled';build(plugins)
        with patch('healthbar.bundled_plugins.bundled_archives',return_value=sorted(plugins.glob('*.zip'))):
            manifest=verify_components()
            self.assertEqual(len(manifest['plugins']),8)
            seed_bundled_plugins(Settings())
            registry=PluginRegistry();installed={p['id']:p for p in registry.installed()}
            self.assertEqual(len(installed),8)
            registry.set_enabled('network-viewer',False)
            seed_bundled_plugins(Settings())
            self.assertFalse(next(p for p in registry.installed() if p['id']=='network-viewer')['enabled'])
            self.assertEqual(installed['cpu-manager-viewer']['version'],'2.1.0')
    def test_only_matching_older_builtin_is_updated_custom_plugin_survives(self):
        from scripts.build_plugins import build
        from healthbar.plugins import PluginRegistry
        from healthbar.bundled_plugins import seed_bundled_plugins
        directory=self.root/'bundled';build(directory)
        source=next(directory.glob('network-*.zip'))
        def older(path,custom=False):
            with zipfile.ZipFile(source) as inp,zipfile.ZipFile(path,'w') as out:
                for name in inp.namelist():
                    contents=inp.read(name)
                    if name=='manifest.json':
                        declaration=json.loads(contents);declaration['version']='1.0.0'
                        if custom:declaration['description']='User custom network'
                        contents=json.dumps(declaration).encode()
                    out.writestr(name,contents)
        registry=PluginRegistry();old=self.root/'old.zip';older(old)
        registry.install(old,registry.inspect(old)[1])
        with patch('healthbar.bundled_plugins.bundled_archives',return_value=[source]):
            seed_bundled_plugins(Settings())
        self.assertEqual(registry.installed()[0]['version'],'1.1.0')
        other=PluginRegistry(self.root/'custom');older(old,True);other.install(old,other.inspect(old)[1])
        with patch('healthbar.bundled_plugins.PluginRegistry',return_value=other),patch('healthbar.bundled_plugins.bundled_archives',return_value=[source]):seed_bundled_plugins(Settings())
        self.assertEqual(other.installed()[0]['description'],'User custom network')
    def test_folder_click_opens_nova_without_browser(self):
        from healthbar.edge_docks import launch_item
        with patch('healthbar.nova_components.open_explorer',return_value=True) as opener,patch('healthbar.edge_docks.QDesktopServices.openUrl') as browser:
            self.assertTrue(launch_item(str(self.root),'folders'))
            opener.assert_called_once_with(str(self.root));browser.assert_not_called()
    def test_smaller_height_and_old_profile_defaults(self):
        self.assertEqual(Settings().bottom_dock_height,round(88*.8))
        Settings(bottom_dock_height=92).save();self.assertEqual(Settings.load().bottom_dock_height,92)
        for invalid in (0,59,113,True):
            with self.assertRaises(ValueError):Settings(bottom_dock_height=invalid).validate()
    def test_formats_keep_sessions_and_text_settings_persist(self):
        manager=open_manager(start=False)
        try:
            space=manager.workspace();first=space.panes[0].session
            space.set_format('grid');sessions=[p.session for p in space.panes]
            for format,(label,count) in FORMATS.items():
                space.set_format(format);self.app.processEvents()
                self.assertIs(space.panes[0].session,first)
                self.assertEqual(len(space.panes),4)
                self.assertEqual([p.session for p in space.panes],sessions)
                self.assertEqual(sum(not p.isHidden() for p in space.panes),count)
            manager.text.update(font='DejaVu Sans Mono',size=14,foreground='#88E8FF')
            manager.save_text()
            self.assertEqual(json.loads((self.root/'data/nova-terminal.json').read_text())['size'],14)
            self.assertEqual(space.panes[0].view.font().pointSize(),14)
            self.assertIn('Formats',[a.text() for a in manager.edit_menu.actions()])
            self.assertIn('Texte',[a.text() for a in manager.edit_menu.actions()])
        finally:manager.window.close()
    @unittest.skipUnless(sys.platform.startswith('linux'),'Linux PTY')
    def test_real_shell_tty_resize_ansi_unicode_interrupt_and_exit(self):
        session=TerminalSession(shell='/bin/bash',cwd=self.root)
        view=TerminalView(session);view.resize(900,500);view.show()
        session.start();process=session.process
        try:
            session.write(b"test -t 0 && test -t 1 && printf 'NOVA_%s\\n' PTY_OK\n")
            self.wait(lambda:'NOVA_PTY_OK' in '\n'.join(session.screen.display))
            session.resize(90,24)
            session.write("printf '\\033[31mCOULEUR_%s\\033[0m\\n' 'écran'; stty size\n".encode())
            self.wait(lambda:'COULEUR_écran' in '\n'.join(session.screen.display))
            self.wait(lambda:'24 90' in '\n'.join(session.screen.display))
            self.assertTrue(any(c.fg=='red' for row in session.screen.buffer.values() for c in row.values()))
            session.write(b'sleep 30\n');self.app.processEvents();time.sleep(.15)
            self.app.sendEvent(view,QKeyEvent(__import__("PySide6.QtCore",fromlist=["QEvent"]).QEvent.KeyPress,Qt.Key_C,Qt.ControlModifier))
            session.write(b"printf 'INTERRUPT_%s\\n' OK\n")
            self.wait(lambda:'INTERRUPT_OK' in '\n'.join(session.screen.display))
            session.write(b'exit\n');self.wait(lambda:process.poll() is not None)
        finally:session.close();view.close()
    def test_xfce_activation_and_restore_preserve_settings_and_file_manager(self):
        from healthbar import nova_desktop as desktop
        Settings(dock_left_enabled=False,dock_right_enabled=False,bottom_dock_enabled=False,opacity=63).save()
        mime={'value':'org.xfce.Thunar.desktop'}
        def mime_command(*args):
            if args[0]=='query':return mime['value']
            mime['value']=args[1];return ''
        with patch('healthbar.nova_components.install_components'),patch('nova_nexus.install_theme.main') as theme,patch.object(desktop,'_mime',side_effect=mime_command):
            desktop.activate()
            self.assertEqual(mime['value'],desktop.DESKTOP_ID)
            self.assertTrue(Settings.load().dock_left_enabled)
            desktop.restore()
            self.assertEqual(mime['value'],'org.xfce.Thunar.desktop')
            self.assertFalse(Settings.load().bottom_dock_enabled)
            self.assertEqual(Settings.load().opacity,63)
            self.assertFalse((self.root/'data/nova-desktop-backup.json').exists())
