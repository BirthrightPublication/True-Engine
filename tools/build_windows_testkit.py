"""Repackage the existing 0.1.0 Windows binary without modifying engine code."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'True-Engine-0.1.0-windows11-testkit-r2'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def assemble(binary, old_payload):
    raw = binary.read_bytes()
    if len(raw) < 64 or raw[:2] != b'MZ':
        raise ValueError('Not a Windows executable')
    offset = struct.unpack_from('<I', raw, 0x3c)[0]
    if raw[offset:offset+4] != b'PE\0\0' or struct.unpack_from('<H', raw, offset+4)[0] != 0x8664:
        raise ValueError('Not an x64 Windows PE')
    trusted = old_payload.with_suffix('.zip.sha256').read_text().split()[0]
    if sha(old_payload.read_bytes()) != trusted:
        raise ValueError('Existing payload ZIP hash mismatch')
    files = {p.name:p.read_bytes() for p in (ROOT/'tools/windows-testkit').iterdir() if p.is_file()}
    files['App/true-engine-viewport.exe'] = raw
    with zipfile.ZipFile(old_payload) as z:
        original = json.loads(z.read('manifest.json'))
        for name, digest in original['files'].items():
            if sha(z.read(name)) != digest:
                raise ValueError('Existing payload file hash mismatch')
        if sha(raw) != original['files']['app/true-engine-viewport.exe']:
            raise ValueError('Expected the unchanged 0.1.0 binary; use a new application version for code changes')
        for name in ['libunwind.dll', 'LLVM-LICENSE.txt', 'COPYING.MinGW-w64-runtime.txt']:
            files['App/'+name] = z.read('app/'+name)
    for name in ['CHANGELOG.md', 'TEST_REPORT.md', 'KNOWN_ISSUES.md', 'ARCHITECTURE.md', 'NEXT_ITERATION.md']:
        files[name] = (ROOT/name).read_bytes()
    source_names = ['Cargo.toml','Cargo.lock','rust-toolchain.toml']
    source_names += [str(p.relative_to(ROOT)) for folder in ['crates','examples'] for p in (ROOT/folder).rglob('*') if p.is_file()]
    manifest = dict(engine_version='0.1.0', distribution_revision=2,
                    previous_distribution='0.1.0 windows-kit r1', sdk='0.1', project_schema=1,
                    status='Windows runtime qualification pending', architecture='x86_64',
                    target='x86_64-pc-windows-gnullvm', migration='none',
                    git_tag='v0.1.0', engine_binary_changed=False,
                    compatibility='Windows 11 x64; Windows PowerShell 5.1; UCRT and GPU drivers; libunwind.dll bundled',
                    runtime_dependencies_to_install=[], tests='TEST_REPORT.md', known_issues='KNOWN_ISSUES.md',
                    archive=NAME+'.zip', archive_sha256_sidecar=NAME+'.zip.sha256',
                    data_preservation='Side-by-side version and unique test data; existing Current/settings/projects/versions/root launcher preserved',
                    rollback='Close this kit and launch an earlier version; no migration or replacement',
                    changed_files=sorted(files), files={n:sha(b) for n,b in sorted(files.items())},
                    source_files={n:sha((ROOT/n).read_bytes()) for n in sorted(source_names)})
    return files, manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, default=ROOT/'target/x86_64-pc-windows-gnullvm/release/true-engine-viewport.exe')
    parser.add_argument('--existing-payload', type=Path, default=ROOT/'Build/True-Engine-0.1.0-windows-x64.zip')
    parser.add_argument('--stage', type=Path, help='Prepare an empty directory for script validation without publishing a ZIP')
    args = parser.parse_args()
    files, manifest = assemble(args.binary, args.existing_payload)
    data = json.dumps(manifest, indent=2).encode()
    if args.stage:
        args.stage.mkdir(parents=True, exist_ok=False)
        for name, content in {**files,'RELEASE_MANIFEST.json':data}.items():
            path = args.stage/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        print(args.stage)
    else:
        out = ROOT/'Build'
        archive = out/(NAME+'.zip')
        if archive.exists():
            raise FileExistsError('Preserving existing release: '+str(archive))
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
            for name, content in files.items():
                z.writestr(name, content)
            z.writestr('RELEASE_MANIFEST.json', data)
        checksum = sha(archive.read_bytes())
        archive.with_suffix('.zip.sha256').write_text(checksum+'  '+archive.name+'\n')
        (ROOT/'RELEASE_MANIFEST.json').write_bytes(data)
        print(archive)
        print(checksum)
