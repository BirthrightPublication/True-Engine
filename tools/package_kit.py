"""Bundle a staged Windows root; does not install or run on Windows."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--staging',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
files={name:(a.staging/name).read_bytes() for name in ['Update.cmd','Rollback.cmd','Launch.cmd','updater.py','Build/True-Engine-0.1.0-windows-x64.zip','Build/True-Engine-0.1.0-windows-x64.zip.sha256']}
for name in ['RELEASE-0.1.0.md','VALIDATION.md']:
    files['docs/'+name]=(root/'docs'/name).read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=dict(version='0.1.0',status='candidate; Windows runtime NOT RUN',sdk='0.1',schema=1,migration='none',compatibility='Windows 10+ x64 with UCRT, Python 3.10+; SDK 0.1/schema 1',changed_files=list(files),files={n:sha(b) for n,b in files.items()},tests='See docs/VALIDATION.md')
out=root/'Build';out.mkdir(exist_ok=True)
for name in ['True-Engine-0.1.0-windows-x64.zip','True-Engine-0.1.0-windows-x64.zip.sha256']:
    (out/name).write_bytes((a.staging/'Build'/name).read_bytes())
kit=out/'True-Engine-0.1.0-windows-kit.zip'
if kit.exists():raise FileExistsError(kit)
with zipfile.ZipFile(kit,'x',zipfile.ZIP_DEFLATED) as z:
    for name,data in files.items():z.writestr(name,data)
    z.writestr('kit-manifest.json',json.dumps(manifest,indent=2))
checksum=sha(kit.read_bytes());kit.with_suffix('.zip.sha256').write_text(checksum+'  '+kit.name+'\n')
print(kit);print(checksum)
