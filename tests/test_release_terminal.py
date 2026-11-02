import os
import sys
import time
import unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from nova_nexus.terminal import TerminalSession


class NativeTerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_native_shell_emits_output(self):
        session=TerminalSession()
        try:
            session.start()
            command=('echo NOVA_%COMSPEC:~0,0%NATIVE_READY\r' if sys.platform=='win32'
                     else "printf '\\116\\117\\126\\101_NATIVE_READY\\n'\r")
            session.write(command.encode())
            deadline=time.monotonic()+10
            while time.monotonic()<deadline:
                self.app.processEvents()
                if 'NOVA_NATIVE_READY' in '\n'.join(session.screen.display):break
                time.sleep(.02)
            else:self.fail('Native terminal did not execute the shell command')
            session.resize(80,24)
            self.assertEqual(session.screen.columns,80)
        finally:session.close()
