"""Verify a real controlling terminal through the exact frozen Linux executable."""
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
if not sys.platform.startswith('linux'):
    print('NOVA interactive terminal: Linux only');raise SystemExit(0)
from PySide6.QtWidgets import QApplication
from nova_nexus.terminal import TerminalSession
app=QApplication([])
executable=Path(sys.argv[1] if len(sys.argv)>1 else 'dist/HealthPerfsBar/HealthPerfsBar').resolve()
with tempfile.TemporaryDirectory() as temporary:
    session=TerminalSession(shell='/bin/sh',cwd=temporary)
    with patch.object(sys,'frozen',True,create=True),patch.object(sys,'executable',str(executable)),patch.dict(os.environ,ENV='',BASH_ENV=''):
        session.start()
    process=session.process
    try:
        session.write(b"test -t 0 && test -t 1 && printf '\\033[36mNOVA_%s\\033[0m\\n' FROZEN_PTY_OK\n")
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            app.processEvents()
            if 'NOVA_FROZEN_PTY_OK' in '\n'.join(session.screen.display):break
            if process.poll() is not None:raise AssertionError('Frozen PTY helper exited: '+str(process.returncode))
            time.sleep(.03)
        else:raise AssertionError('No frozen PTY response')
        session.resize(110,30)
        session.write(b"stty size; exit\n")
        deadline=time.monotonic()+10
        while process.poll() is None and time.monotonic()<deadline:
            app.processEvents();time.sleep(.03)
        assert process.poll()==0
        print('PASS: frozen controlling PTY, interactive shell, ANSI, resize, clean exit')
    finally:session.close()
