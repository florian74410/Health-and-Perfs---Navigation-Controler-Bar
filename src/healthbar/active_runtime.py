"""A packaged launcher can delegate public commands to a newer activated runtime."""
import os
from pathlib import Path
import subprocess
import sys

INTERNAL_FLAGS={'--self-test','--expect-version','--nova-pty-child','--restore-xfce-after-pid'}


def newer_active_executable(arguments):
    if not getattr(sys,'frozen',False):return None
    if any(arg.split('=',1)[0] in INTERNAL_FLAGS for arg in arguments):return None
    from . import __version__
    from .install_engine import install_root,read_installed_state,version_tuple,payload_executable
    root=install_root()
    try:
        state=read_installed_state(root)
        if not state:return None
        version=version_tuple(state['version'])
        if version is None or version<=version_tuple(__version__):return None
        expected=payload_executable(root/'versions'/state['version'])
        executable=Path(state.get('executable',''))
        if expected is None or executable.resolve()!=expected.resolve():return None
        if executable.resolve()==Path(sys.executable).resolve():return None
        return executable
    except (OSError,ValueError,KeyError,TypeError):return None


def forward(arguments):
    executable=newer_active_executable(arguments)
    if executable is None:return None
    from .system_env import native_env
    environment=dict(native_env(),PYINSTALLER_RESET_ENVIRONMENT='1')
    command=[str(executable),*arguments]
    if sys.platform=='win32':return subprocess.call(command,env=environment)
    os.execve(str(executable),command,environment)
    return 0
