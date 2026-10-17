"""Refresh missing license texts from each crate's exact published VCS commit."""
import concurrent.futures
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

metadata=json.loads(Path(sys.argv[1]).read_text())
active={n['id'] for n in metadata['resolve']['nodes']}
root=Path(__file__).resolve().parent/'notices'
names=['LICENSE','LICENSE.txt','LICENSE.md','LICENSE-MIT','LICENSE-APACHE','LICENSE.MIT','LICENSE.APACHE','LICENSE-CC0','UNLICENSE','COPYING','NOTICE']


def fetch(p):
    directory=Path(p['manifest_path']).parent
    if any(f.is_file() and re.match(r'(?i)^(licen[cs]e|copying|notice|copyright)',f.name) for f in directory.iterdir()) or p.get('license_file'):
        return
    vcs=json.loads((directory/'.cargo_vcs_info.json').read_text())
    commit=vcs['git']['sha1']
    match=re.match(r'https://github.com/([^/]+/[^/]+)',p['repository'])
    if not match or not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError(p['name'])
    repo=match[1].removesuffix('.git')
    dest=root/(p['name']+'-'+p['version']);dest.mkdir(parents=True,exist_ok=True)
    if (dest/'provenance.json').exists():return p['name'], 'cached exact-commit notices'
    found=[]
    for name in names:
        url=f'https://raw.githubusercontent.com/{repo}/{commit}/{name}'
        try:
            with urllib.request.urlopen(url,timeout=30) as response:data=response.read()
        except urllib.error.HTTPError as e:
            if e.code==404:continue
            raise
        (dest/name).write_bytes(data);found.append(dict(filename=name,url=url))
    if not found and p['license']=='CC0-1.0':
        url='https://raw.githubusercontent.com/spdx/license-list-data/v3.25.0/text/CC0-1.0.txt'
        with urllib.request.urlopen(url,timeout=30) as response:data=response.read()
        (dest/'CC0-1.0.txt').write_bytes(data)
        (dest/'DECLARATION.txt').write_text('Published crate declares CC0-1.0. Authors: '+', '.join(p['authors'])+'\nVCS commit: '+commit+'\nRepository: '+p['repository']+'\n')
        found=[dict(filename='CC0-1.0.txt',url=url),dict(filename='DECLARATION.txt',url='Cargo crate metadata, bound by Cargo.lock checksum')]
    if not found:raise ValueError('No authoritative notice found for '+p['name'])
    (dest/'provenance.json').write_text(json.dumps(dict(crate=p['name'],version=p['version'],vcs_commit=commit,license_expression=p['license'],files=found),indent=2)+'\n')
    return p['name'],len(found)

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    for result in pool.map(fetch,[p for p in metadata['packages'] if p['id'] in active and p['id'] not in metadata['workspace_members']]):
        if result:print(*result)
