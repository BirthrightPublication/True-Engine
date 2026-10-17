import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location('standard_release',Path(__file__).parent/'release/package.py')
release=importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class StandardReleaseTests(unittest.TestCase):
    def test_deterministic_zip_sidecar_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);files={'app/demo.exe':b'payload','app/settings-template.txt':b'not user settings'}
            a=root/'a.zip';b=root/'b.zip'
            release.write_zip(a,files);release.write_zip(b,dict(reversed(list(files.items()))))
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertEqual(a.with_suffix('.zip.sha256').read_text().split()[0],release.sha(a.read_bytes()))
            with self.assertRaises(FileExistsError):release.write_zip(a,{'other':b'overwrite'})
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with zipfile.ZipFile(a) as z:self.assertEqual(z.read('app/demo.exe'),b'payload')

    def test_notice_inventory_filters_target_and_retains_license_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);crate=root/'crate';crate.mkdir();(crate/'Cargo.toml').write_text('[package]')
            (crate/'LICENSE-MIT').write_text('Copyright fixture author; fixture license text')
            rust=root/'rust/share/doc/rust';rust.mkdir(parents=True)
            for name in ['LICENSE-MIT','LICENSE-APACHE','COPYRIGHT']:(rust/name).write_text('Rust notice fixture')
            metadata={'workspace_members':['engine'],'resolve':{'nodes':[{'id':'engine'},{'id':'dependency'}]},'packages':[{'id':'engine','name':'engine','version':'0.1.1'},dict(id='dependency',name='fixture',version='1.0',manifest_path=str(crate/'Cargo.toml'),license='MIT',license_file=None),dict(id='other-platform',name='not-shipped',version='1.0')]}
            files=release.collect_notices(metadata,root/'rust')
            inventory=json.loads(files['app/notices/dependencies.json'])
            self.assertEqual([p['name'] for p in inventory['packages']],['fixture'])
            self.assertTrue(any(b'fixture author' in data for data in files.values()))
            (crate/'LICENSE-MIT').unlink()
            with self.assertRaises(ValueError):release.collect_notices(metadata,root/'rust')

    def test_failed_evidence_cannot_be_packaged(self):
        import tomllib
        version=tomllib.loads((release.ROOT/'Cargo.toml').read_text())['workspace']['package']['version']
        with self.assertRaisesRegex(ValueError,'Failed test evidence'):
            release.build(Path('never-read.exe'),version,[{'command':'failing test','exit_code':1}],{},Path('.'),Path('.'),require_tag=False)

if __name__=='__main__':unittest.main()
