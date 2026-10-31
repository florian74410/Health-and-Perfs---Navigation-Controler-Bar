"""Build native portable app on each target OS; no cross-compilation."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
    "--name", "HealthPerfsBar", "--paths", str(root / "src"),
    "--osx-bundle-identifier", "com.healthperfs.bar", str(root / "scripts/entrypoint.py")], cwd=root, check=True)
