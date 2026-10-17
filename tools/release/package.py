"""Deterministic standard release ZIP from a tagged build and actual test evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'tools/release'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pe_imports(data):
    """Inspect x64 PE headers and imports without executing the binary."""
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError('Expected Windows PE executable')
    pe = struct.unpack_from('<I', data, 60)[0]
    if data[pe:pe+4] != b'PE\0\0' or struct.unpack_from('<H', data, pe+4)[0] != 0x8664:
        raise ValueError('Expected Windows x64 PE')
    count = struct.unpack_from('<H', data, pe+6)[0]
    optional_size = struct.unpack_from('<H', data, pe+20)[0]
    optional = pe+24
    if struct.unpack_from('<H', data, optional)[0] != 0x20b:
        raise ValueError('Expected PE32+')
    sections = []
    for index in range(count):
        off = optional+optional_size+index*40
        virtual_size, address, raw_size, raw = struct.unpack_from('<IIII', data, off+8)
        sections.append((address, max(virtual_size, raw_size), raw))

    def offset(rva):
        for address, size, raw in sections:
            if address <= rva < address+size:
                return raw+rva-address
        raise ValueError('Invalid PE RVA')

    imports = set()
    rva = struct.unpack_from('<I', data, optional+112+8)[0]
    if rva:
        off = offset(rva)
        for _ in range(1000):
            record = struct.unpack_from('<IIIII', data, off)
            if not any(record):
                return imports
            name = offset(record[3])
            imports.add(data[name:data.index(b'\0', name)].decode('ascii').lower())
            off += 20
        raise ValueError('Unterminated PE imports')
    return imports


def collect_notices(metadata, rust_root):
    files = {}
    inventory = []
    active={node['id'] for node in metadata['resolve']['nodes']}
    for p in sorted(metadata['packages'], key=lambda p:(p['name'],p['version'])):
        if p['id'] in metadata['workspace_members'] or p['id'] not in active:
            continue
        directory = Path(p['manifest_path']).parent
        candidates = {f for f in directory.iterdir() if f.is_file() and re.match(r'(?i)^(licen[cs]e|copying|notice|copyright)',f.name)}
        if p.get('license_file'):
            candidates.add(directory/p['license_file'])
        cached=RELEASE/'notices'/(p['name']+'-'+p['version'])
        if not candidates and (cached/'provenance.json').exists():
            provenance=json.loads((cached/'provenance.json').read_text())
            vcs=json.loads((directory/'.cargo_vcs_info.json').read_text())
            if provenance['vcs_commit']!=vcs['git']['sha1'] or provenance['license_expression']!=p['license']:
                raise ValueError('Cached dependency notices do not match locked VCS/license')
            candidates={f for f in cached.iterdir() if f.is_file()}
        if not candidates or not p.get('license'):
            raise ValueError('Dependency license/notice review required: '+p['name']+' '+p['version'])
        entries = []
        for index, f in enumerate(sorted(candidates)):
            dest = f'app/notices/{p["name"]}-{p["version"]}/{index}-{f.name}'
            files[dest] = f.read_bytes()
            entries.append(dest)
        inventory.append(dict(name=p['name'],version=p['version'],declared_license=p['license'],notice_files=entries))
    for name in ['LICENSE-MIT','LICENSE-APACHE','COPYRIGHT']:
        files['app/notices/Rust/'+name] = (rust_root/'share/doc/rust'/name).read_bytes()
    files['app/notices/dependencies.json'] = json.dumps(dict(scope='Conservative entire resolved Cargo graph; may include unshipped target/build/dev components',project_license='Owner decision pending; no project license selected',packages=inventory),indent=2).encode()
    return files


def write_zip(path, files):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2025,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644 << 16
            archive.writestr(info,data)
    digest=sha(path.read_bytes())
    path.with_suffix(path.suffix+'.sha256').write_text(digest+'  '+path.name+'\n')
    return digest


def build(binary, version, evidence, metadata, rust_root, output, runtime_files=(), require_tag=True):
    if not re.fullmatch(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)',version):
        raise ValueError('Stable semantic version required')
    import tomllib
    if tomllib.loads((ROOT/'Cargo.toml').read_text())['workspace']['package']['version'] != version:
        raise ValueError('Tag/package version differs from Cargo version')
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if require_tag:
        tagged=subprocess.check_output(['git','rev-parse',f'v{version}^{{commit}}'],cwd=ROOT,text=True).strip()
        if tagged != commit:
            raise ValueError('Build must run at its exact tagged source')
        # Generated binaries/evidence are ignored; tracked source must be pristine.
        subprocess.run(['git','diff','--exit-code','HEAD'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    if not isinstance(evidence,list) or not evidence:
        raise ValueError('Actual test evidence required')
    if any(item.get('exit_code',0)!=0 for item in evidence):
        raise ValueError('Failed test evidence cannot be released')
    raw=binary.read_bytes()
    imports=pe_imports(raw)
    files={'app/true-engine-viewport.exe':raw}
    for name in ['Update-TrueEngine.ps1','Start-TrueEngine.ps1','Update True Engine.bat','Start True Engine.bat','README.txt']:
        files['app/'+name]=(RELEASE/name).read_bytes()
    for name in ['CHANGELOG.md','KNOWN_ISSUES.md','LICENSING.md']:
        files['app/'+name]=(ROOT/name).read_bytes()
    files['app/RELEASE_NOTES.md']=(ROOT/'docs'/f'RELEASE-{version}.md').read_bytes()
    files['app/TEST_REPORT.md']=('Actual build-time evidence\n\n'+json.dumps(evidence,indent=2)+'\n\nInteractive Windows GPU execution is NOT implied by CPU/installer tests.\n').encode()
    files.update(collect_notices(metadata,rust_root))
    for path in runtime_files:
        files['app/'+path.name]=path.read_bytes()
    for name, content in list(files.items()):
        if name.lower().endswith('.dll'):
            pe_imports(content)
    # System DLLs expected on Windows 11; third-party runtime DLLs must be bundled.
    system={'kernel32.dll','ntdll.dll','user32.dll','gdi32.dll','advapi32.dll','shell32.dll','ole32.dll','oleaut32.dll','bcrypt.dll','bcryptprimitives.dll','userenv.dll','ws2_32.dll','dwmapi.dll','imm32.dll','uxtheme.dll','d3dcompiler_47.dll','dxgi.dll','d3d12.dll','opengl32.dll','shlwapi.dll','comdlg32.dll','secur32.dll','setupapi.dll','version.dll','winmm.dll','ucrtbase.dll'}
    bundled={name[4:].lower() for name in files if name.lower().endswith('.dll')}
    for name, content in files.items():
        if name.lower().endswith('.dll'):
            imports.update(pe_imports(content))
    missing={name for name in imports if name not in system and not name.startswith(('api-ms-win-','ext-ms-win-')) and name not in bundled}
    if missing:
        raise ValueError('Unbundled non-system runtime DLLs: '+str(sorted(missing)))
    bootstrap={'Start True Engine.bat':(RELEASE/'Start True Engine.bat').read_bytes(),'Update True Engine.bat':(RELEASE/'Update True Engine.bat').read_bytes(),'TrueEngine-Bootstrap.ps1':(RELEASE/'Update-TrueEngine.ps1').read_bytes(),'README - FIRST TIME SETUP.txt':(RELEASE/'README.txt').read_bytes()}
    manifest=dict(format_version=1,version=version,sdk='0.1',schema=1,migration='none',source_commit=commit,source_tag='v'+version,platform='Windows 11 x64',pe_imports=sorted(imports),tests=evidence,changed_files=sorted(files),files={n:sha(b) for n,b in sorted(files.items())},bootstrap_files={n:sha(b) for n,b in bootstrap.items()})
    files['app/manifest.json']=json.dumps(manifest,indent=2).encode()
    files.update(bootstrap)
    package=output/f'True-Engine-v{version}-windows-x64.zip'
    checksum=write_zip(package,files)
    boot=output/f'True-Engine-v{version}-updater-bootstrap.zip'
    write_zip(boot,bootstrap)
    return package,checksum


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary',type=Path,required=True)
    p.add_argument('--version',required=True)
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--rust-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'Build')
    p.add_argument('--runtime-file',type=Path,action='append',default=[])
    p.add_argument('--candidate',action='store_true',help='Local untagged validation only; never used by release CI')
    a=p.parse_args()
    result=build(a.binary,a.version,json.loads(a.evidence.read_text(encoding='utf-8-sig')),json.loads(a.metadata.read_text(encoding='utf-8-sig')),a.rust_root,a.output,a.runtime_file,not a.candidate)
    print(result[0]);print(result[1])
