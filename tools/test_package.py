"""Packaging contracts using a synthetic PE header, never an executable runtime test."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from updater import install


class PackageTests(unittest.TestCase):
    def test_manifest_hashes_install_and_immutable_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = bytearray(256)
            binary[:2] = b'MZ'
            struct.pack_into('<I', binary, 0x3c, 128)
            binary[128:132] = b'PE\0\0'
            struct.pack_into('<H', binary, 132, 0x8664)
            (root/'fixture.exe').write_bytes(binary)
            (root/'fixture.dll').write_bytes(b'runtime-fixture')
            (root/'tests.json').write_text(json.dumps([{'command':'fixture test', 'result':'synthetic; not executable'}]))
            command = [sys.executable, str(Path(__file__).with_name('package.py')), '--binary', str(root/'fixture.exe'), '--tests', str(root/'tests.json'), '--output', str(root/'Build'), '--runtime-file', str(root/'fixture.dll')]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            archive = root/'Build'/'True-Engine-0.1.0-windows-x64.zip'
            checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertTrue(archive.with_suffix('.zip.sha256').read_text().startswith(checksum))
            with zipfile.ZipFile(archive) as z:
                m=json.loads(z.read('manifest.json'))
                self.assertEqual(m['migration'], 'none')
                self.assertEqual(m['files']['app/true-engine-viewport.exe'], hashlib.sha256(binary).hexdigest())
            self.assertIn('app/fixture.dll',m['files'])
            install(root/'installed', archive, checksum)
            self.assertEqual((root/'installed'/'Current'/'true-engine-viewport.exe').read_bytes(), binary)
            again=subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), checksum)

if __name__ == '__main__':
    unittest.main()
