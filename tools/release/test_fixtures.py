"""Synthetic PE/ZIP fixtures for updater tests. Never execute these fake binaries."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

RELEASE=Path(__file__).resolve().parent


def make(output,version,sdk='0.1',unsafe=False,conflict=False):
    data=bytearray(512);data[:2]=b'MZ';struct.pack_into('<I',data,60,128)
    data[128:132]=b'PE\0\0';struct.pack_into('<H',data,132,0x8664)
    struct.pack_into('<H',data,148,240);struct.pack_into('<H',data,152,0x20b)
    data[400:400+len(version)]=version.encode()
    files={'app/true-engine-viewport.exe':bytes(data)}
    for name in ['Update-TrueEngine.ps1','Start-TrueEngine.ps1','Update True Engine.bat','Start True Engine.bat']:
        files['app/'+name]=(RELEASE/name).read_bytes()
    if conflict:files['app/private-setting.json']=b'new managed file colliding with user data'
    bootstrap={'Start True Engine.bat':(RELEASE/'Start True Engine.bat').read_bytes(),'Update True Engine.bat':(RELEASE/'Update True Engine.bat').read_bytes(),'TrueEngine-Bootstrap.ps1':(RELEASE/'Update-TrueEngine.ps1').read_bytes(),'README - FIRST TIME SETUP.txt':b'Synthetic test fixture; not a runnable application.'}
    sha=lambda b:hashlib.sha256(b).hexdigest()
    manifest=dict(format_version=1,version=version,sdk=sdk,schema=1,migration='none',files={n:sha(b) for n,b in files.items()},bootstrap_files={n:sha(b) for n,b in bootstrap.items()})
    files.update(bootstrap);files['app/manifest.json']=json.dumps(manifest).encode()
    if unsafe:files['app/../../escape.txt']=b'bad'
    output.mkdir(parents=True,exist_ok=True)
    package=output/f'True-Engine-v{version}-windows-x64.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    package.with_suffix('.zip.sha256').write_text(sha(package.read_bytes())+'  '+package.name+'\n')
    return package


if __name__=='__main__':
    out=Path(sys.argv[1])
    for version in ['0.1.0','0.1.1','0.1.2']:make(out/version,version)
    make(out/'unsafe','0.1.2',unsafe=True)
    make(out/'sdk','0.1.2',sdk='0.2')
    make(out/'conflict','0.1.2',conflict=True)
