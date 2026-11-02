"""Build a real full-replacement update descriptor from verified native artifacts."""
import json
from pathlib import Path
import sys
import zipfile
import hashlib


def build(tag, directory):
    directory=Path(directory)
    manifest=json.loads((directory/'novabar-update-manifest.json').read_text())
    descriptor={**manifest,'project':'Cyber-Neon Interactif – THEME 1.0',
                'brand':'NOVA NEXUS HD','application':'NovaBar',
                'release_tag':tag,'type':'full-runtime','source_min':'0.7.0',
                'source_max_exclusive':'1.0.0',
                'rollback':'Retain previous runtime and snapshot of settings, profiles and plugins',
                'trust':'Official repository over HTTPS; SHA-256 integrity. No independent manifest signing key configured.'}
    for key,asset in descriptor['platforms'].items():
        local=directory/asset['url'].rsplit('/',1)[-1]
        if not local.is_file():raise ValueError('Missing actual update: '+str(local))
        if hashlib.sha256(local.read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('Hash mismatch')
        asset.update(size=local.stat().st_size,type='full-runtime')
    target=directory/'nova-patch-to-v1.0.0-manifest.json'
    target.write_text(json.dumps(descriptor,indent=2,ensure_ascii=False)+'\n')
    with zipfile.ZipFile(directory/'NOVA-Patch-to-v1.0.0.zip','w',zipfile.ZIP_DEFLATED) as out:
        out.write(target,'Patch/to-v1.0.0/manifest.json')
        out.write(Path(__file__).resolve().parents[1]/'Patch/to-v1.0.0/README.md','Patch/to-v1.0.0/README.md')
    return descriptor


if __name__=='__main__':build(sys.argv[1],sys.argv[2])
