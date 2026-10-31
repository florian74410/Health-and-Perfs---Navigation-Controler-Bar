"""One-command source installation into a persistent per-user virtual environment."""
import os
import plistlib
import shutil
import subprocess
import sys
import venv
from pathlib import Path


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 ou plus récent est nécessaire.")
    source = Path(__file__).resolve().parents[1]
    if sys.platform == "win32":
        root = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "HealthPerfsBar"
        python = root / "venv/Scripts/pythonw.exe"
        pip_python = root / "venv/Scripts/python.exe"
    elif sys.platform == "darwin":
        root = Path.home() / "Library/Application Support/HealthPerfsBar/runtime"
        python = pip_python = root / "venv/bin/python"
    else:
        root = Path.home() / ".local/share/health-perfs-bar"
        python = pip_python = root / "venv/bin/python"
    root.mkdir(parents=True, exist_ok=True)
    print("Création de l’environnement privé…", flush=True)
    venv.EnvBuilder(with_pip=True).create(root / "venv")
    print("Installation de Health & Perfs…", flush=True)
    subprocess.run([str(pip_python), "-m", "pip", "install", str(source)], check=True)
    # Installed wheel, not an editable checkout: the downloaded source can be removed.
    if sys.platform == "darwin":
        app = Path.home() / "Applications/Health & Perfs Bar.app"
        mac = app / "Contents/MacOS"
        mac.mkdir(parents=True, exist_ok=True)
        launcher = mac / "HealthBar"
        import shlex
        launcher.write_text("#!/bin/sh\nexec " + shlex.quote(str(python)) + " -m healthbar \"$@\"\n", encoding="utf-8")
        launcher.chmod(0o755)
        (app / "Contents/Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "HealthBar", "CFBundleIdentifier": "com.healthperfs.bar",
            "CFBundleName": "Health & Perfs Bar", "CFBundlePackageType": "APPL", "LSUIElement": True}))
    elif sys.platform == "win32":
        # PowerShell arguments are passed through environment variables, never evaluated as code.
        programs = Path(os.getenv("APPDATA", str(Path.home()))) / "Microsoft/Windows/Start Menu/Programs"
        programs.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, HEALTHBAR_PYTHON=str(python), HEALTHBAR_LINK=str(programs / "Health & Perfs Bar.lnk"))
        subprocess.run(["powershell.exe", "-NoProfile", "-Command",
            "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($env:HEALTHBAR_LINK); "
            "$s.TargetPath=$env:HEALTHBAR_PYTHON; $s.Arguments='-m healthbar'; $s.Save()"], env=env, check=True)
    else:
        sys.path.insert(0, str(source / "src"))
        from healthbar.autostart import desktop_quote
        apps = Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "applications"
        apps.mkdir(parents=True, exist_ok=True)
        launcher = apps / "health-perfs-bar.desktop"
        launcher.write_text("[Desktop Entry]\nType=Application\nName=Health & Perfs Bar\nComment=Transparent desktop HUD\nExec="
                            + desktop_quote(str(python)) + " -m healthbar\nTerminal=false\nCategories=System;Monitor;\n", encoding="utf-8")
        launcher.chmod(0o755)
    print("Installation terminée. Ouverture des préférences…", flush=True)
    subprocess.Popen([str(python), "-m", "healthbar", "--setup"], cwd=root)


if __name__ == "__main__":
    main()
