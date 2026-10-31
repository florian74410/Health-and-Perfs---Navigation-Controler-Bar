"""Run in tagged release CI after all runtime archives have been downloaded."""
import hashlib
import json
import re
import sys
from pathlib import Path
repo="florian74410/Health-and-Perfs---Navigation-Controler-Bar"
tag=sys.argv[1]
if not re.fullmatch(r"v\d+\.\d+\.\d+",tag):raise SystemExit("Release tags must be vMAJOR.MINOR.PATCH")
platforms={}
for path in Path('release').glob('NovaBar-runtime-*.zip'):
    key=path.name.removeprefix('NovaBar-runtime-').removesuffix('.zip')
    platforms[key]={"url":f"https://github.com/{repo}/releases/download/{tag}/{path.name}",
                    "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
required={"linux-x86_64","windows-x86_64","macos-arm64","macos-x86_64"}
if set(platforms)!=required:raise SystemExit("Runtime release set is incomplete")
Path('release/novabar-update-manifest.json').write_text(json.dumps({"schema_version":1,
    "version":tag[1:],"platforms":platforms},indent=2),encoding='utf-8')
