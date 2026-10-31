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
payload=root/"dist"/("HealthPerfsBar.app" if sys.platform=="darwin" else "HealthPerfsBar")
subprocess.run(common+["--name","CyberNexusInstaller","--osx-bundle-identifier","com.cybernexushud.installer",
    "--add-data",str(payload)+os.pathsep+"payload/"+payload.name,
    str(root/"scripts/installer_entrypoint.py")],cwd=root,check=True)
