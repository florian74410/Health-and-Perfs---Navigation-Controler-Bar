"""Small release archive containing runtime only, never user profiles or plugins."""
import os
import platform
import stat
import sys
import zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/"src"))
from healthbar.updates import platform_key
payload=root/"dist"/("HealthPerfsBar.app" if sys.platform=="darwin" else "HealthPerfsBar")
out=root/("NovaBar-runtime-"+platform_key()+".zip")
with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=4) as package:
    for path in sorted(payload.rglob("*")):
        if not path.is_file():continue
        # Follow Qt library symlinks into regular files so the updater never creates links.
        name=path.relative_to(payload.parent).as_posix()
        info=zipfile.ZipInfo(name)
        info.external_attr=(stat.S_IFREG | (0o755 if path.stat().st_mode&0o111 else 0o644))<<16
        info.compress_type=zipfile.ZIP_DEFLATED
        package.writestr(info,path.read_bytes())
print(out.name)
