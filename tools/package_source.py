"""Create a portable SDK source snapshot; never an executable release."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(['git', 'ls-files', '-c', '-o', '--exclude-standard', '-z'], cwd=root).decode().split('\0')
files = {p: (root / p).read_bytes() for p in sorted(set(paths)) if p and (root / p).is_file()}
sha = lambda data: hashlib.sha256(data).hexdigest()
manifest = dict(version='0.1.0', kind='source-only-unreleased', sdk='0.1', schema=1,
                compatibility='SDK 0.1, schema 1; platform qualification incomplete', migration='none',
                changed_files=list(files), files={p:sha(b) for p,b in files.items()},
                tests='See docs/VALIDATION.md; actual evidence, not cross-platform verification')
out = root / 'Build'
out.mkdir(exist_ok=True)
archive = out / 'True-Engine-0.1.0-source.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p,b in files.items():
        z.writestr('True-Engine/' + p,b)
    z.writestr('True-Engine/source-manifest.json',json.dumps(manifest,indent=2))
digest = sha(archive.read_bytes())
archive.with_suffix('.zip.sha256').write_text(digest + '  ' + archive.name + '\n')
print(archive)
print(digest)
