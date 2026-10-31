"""Build the runtime and an offline native installer containing that exact runtime."""
import os
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
common=[sys.executable,"-m","PyInstaller","--noconfirm","--clean","--windowed",
        "--paths",str(root/"src"),"--add-data",str(root/"src/healthbar/assets")+os.pathsep+"healthbar/assets"]
subprocess.run(common+["--name","HealthPerfsBar","--osx-bundle-identifier","com.healthperfs.bar",
    str(root/"scripts/entrypoint.py")],cwd=root,check=True)
subprocess.run([sys.executable,str(root/"scripts/package_runtime.py")],cwd=root,check=True)
sys.path.insert(0,str(root/"src"))
from healthbar.updates import platform_key
payload=root/("NovaBar-runtime-"+platform_key()+".zip")
# Embed an opaque ZIP: PyInstaller must not re-sign the inner macOS application.
subprocess.run(common+["--name","CyberNexusInstaller","--osx-bundle-identifier","com.cybernexushud.installer",
    "--add-data",str(payload)+os.pathsep+"payload",
    str(root/"scripts/installer_entrypoint.py")],cwd=root,check=True)
