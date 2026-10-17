import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import zipfile
import json
from updater import install, rollback, digest

class UpdateTests(unittest.TestCase):
    def package(self, folder, content=b'MZfixture', extra=None, bad_payload=False):
        archive=folder/'test.zip'
        files={'app/true-engine-viewport.exe':content}
        manifest=dict(sdk='0.1',schema=1,migration='none',files={n:digest(b) for n,b in files.items()})
        if bad_payload: manifest['files']['app/true-engine-viewport.exe']='0'*64
        with zipfile.ZipFile(archive,'w') as z:
            for n,b in files.items():z.writestr(n,b)
            z.writestr('manifest.json',json.dumps(manifest))
            if extra:z.writestr(extra,'bad')
        return archive,digest(archive.read_bytes())
    def test_install_preserve_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'Engine';(root/'Data').mkdir(parents=True);(root/'Data'/'project.json').write_text('mine')
            p,h=self.package(base);install(root,p,h)
            p,h=self.package(base,b'MZsecond');backup=install(root,p,h)
            self.assertEqual((root/'Current'/'true-engine-viewport.exe').read_bytes(),b'MZsecond')
            rollback(root,backup.name)
            self.assertEqual((root/'Current'/'true-engine-viewport.exe').read_bytes(),b'MZfixture')
            self.assertEqual((root/'Data'/'project.json').read_text(),'mine')
    def test_reject_hash_and_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            p,h=self.package(base)
            with self.assertRaises(ValueError):install(base/'root',p,'0'*64)
            for name in ['../escape','app/../../escape','app\\escape','C:/escape', 'app/CON', 'app/alias./file', 'app//file']:
                p,h=self.package(base,extra=name)
                with self.assertRaises(ValueError):install(base/'root',p,h)
            p,h=self.package(base,bad_payload=True)
            with self.assertRaises(ValueError):install(base/'root',p,h)
            self.assertFalse((base/'root'/'Current').exists())
    def test_activation_failure_restores_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'root';p,h=self.package(base);install(root,p,h)
            p,h=self.package(base,b'MZnew')
            original=Path.rename
            def fail_stage(source,dest):
                if source.name.startswith('.stage-'):
                    raise OSError('simulated locked application')
                return original(source,dest)
            with patch.object(Path,'rename',fail_stage):
                with self.assertRaises(OSError):install(root,p,h)
            self.assertEqual((root/'Current'/'true-engine-viewport.exe').read_bytes(),b'MZfixture')
            self.assertFalse((root/'.update-lock').exists())
    def test_lock_blocks_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'root';(root/'.update-lock').mkdir(parents=True)
            p,h=self.package(base)
            with self.assertRaises(FileExistsError):install(root,p,h)

if __name__=='__main__':unittest.main()
