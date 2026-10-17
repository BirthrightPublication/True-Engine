"""SDK archive integrity and evidence checks, independent of the Rust toolchain."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SDK = Path(__file__).resolve().parent
sys.path.insert(0, str(SDK))
spec = importlib.util.spec_from_file_location("true_engine_sdk_pack", SDK / "pack.py")
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)
build_spec = importlib.util.spec_from_file_location("true_engine_sdk_build", SDK / "build.py")
build = importlib.util.module_from_spec(build_spec)
build_spec.loader.exec_module(build)
sys.path.pop(0)


class SdkPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.stage = self.root / "stage"
        (self.stage / "package").mkdir(parents=True)
        self.state = {"source_commit": "a" * 40, "source_tree_sha256": "b" * 64, "source_dirty": False}
        self.files = {
            "package/true_engine_web_bg.wasm": b"\0asm\x01\0\0\0",
            "package/package.json": pack.json_bytes({"name": "@birthright/true-engine", "version": "0.1.3"}),
            "package/index.js": b"export const version = '0.1.3';\n",
            "example/index.html": b"<!doctype html><canvas></canvas>\n",
        }
        for name, data in self.files.items():
            target = self.stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        self.marker = {
            "version": "0.1.3", **self.state,
            "files": pack.hashes(self.files), "build_tools": {"rustc": "rustc 1.85.1"}, "build_platform": "linux"
        }
        (self.stage / pack.STAGE_MARKER).write_bytes(pack.json_bytes(self.marker))
        self.evidence = [{"command": "actual integration test command", "exit_code": 0, "platform": "test fixture"}]
        self.version_patch = patch.object(pack, "engine_version", return_value="0.1.3")
        self.source_patch = patch.object(pack, "source_state", return_value=self.state)
        self.version_patch.start()
        self.source_patch.start()

    def tearDown(self):
        self.source_patch.stop()
        self.version_patch.stop()
        self.temporary.cleanup()

    def test_deterministic_archive_manifest_and_checksum(self):
        first, digest = pack.package(self.stage, self.evidence, self.root / "first", candidate=True)
        second, second_digest = pack.package(self.stage, self.evidence, self.root / "second", candidate=True)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(digest, second_digest)
        self.assertEqual(first.with_suffix(".zip.sha256").read_text(), f"{digest}  {first.name}\n")
        with zipfile.ZipFile(first) as archive:
            self.assertIsNone(archive.testzip())
            manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(manifest["files"], self.marker["files"])
            for name, expected in manifest["files"].items():
                self.assertEqual(pack.sha256(archive.read(name)), expected)
            self.assertTrue(manifest["candidate"])
            self.assertFalse(manifest["windows_runtime_verified"])

    def test_evidence_requires_explicit_success_and_command(self):
        for evidence in [[], {}, [{"command": "test"}], [{"command": "test", "exit_code": 1}],
                         [{"command": "test", "exit_code": False}], [{"exit_code": 0}]]:
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                pack.package(self.stage, evidence, self.root / "out", candidate=True)

    def test_tampering_and_stale_source_are_rejected(self):
        (self.stage / "package/index.js").write_bytes(b"modified after tests")
        with self.assertRaisesRegex(ValueError, "Staged files changed"):
            pack.package(self.stage, self.evidence, self.root / "out", candidate=True)
        (self.stage / "package/index.js").write_bytes(self.files["package/index.js"])
        with patch.object(pack, "source_state", return_value={**self.state, "source_commit": "c" * 40}):
            with self.assertRaisesRegex(ValueError, "Source changed"):
                pack.package(self.stage, self.evidence, self.root / "out", candidate=True)

    def test_previous_archives_and_checksums_are_never_overwritten(self):
        archive, _ = pack.package(self.stage, self.evidence, self.root / "out", candidate=True)
        prior = archive.read_bytes()
        with self.assertRaises(FileExistsError):
            pack.package(self.stage, self.evidence, self.root / "out", candidate=True)
        self.assertEqual(archive.read_bytes(), prior)
        destination = self.root / "checksum-only/SDK.zip"
        destination.parent.mkdir()
        destination.with_suffix(".zip.sha256").write_text("existing checksum")
        with self.assertRaises(FileExistsError):
            pack.write_archive(destination, {"file": b"payload"})
        self.assertFalse(destination.exists())

    def test_release_requires_clean_exact_tag(self):
        with patch.object(pack, "output", return_value="different commit"):
            with self.assertRaisesRegex(ValueError, "exact version tag"):
                pack.package(self.stage, self.evidence, self.root / "out")
        dirty = {**self.state, "source_dirty": True}
        (self.stage / pack.STAGE_MARKER).write_bytes(pack.json_bytes({**self.marker, **dirty}))
        with patch.object(pack, "source_state", return_value=dirty):
            with self.assertRaisesRegex(ValueError, "clean source tree"):
                pack.package(self.stage, self.evidence, self.root / "out")

    def test_dependency_notice_references_follow_sdk_relocation(self):
        notices = {
            "app/notices/example-1.0/LICENSE": b"example notice",
            "app/notices/dependencies.json": pack.json_bytes({
                "scope": "original graph",
                "packages": [{"name": "example", "notice_files": ["app/notices/example-1.0/LICENSE"]}],
            }),
        }
        mapped = build.remap_notices(notices)
        inventory = json.loads(mapped["package/notices/dependencies.json"])
        self.assertIn("wasm32-unknown-unknown", inventory["scope"])
        for dependency in inventory["packages"]:
            for name in dependency["notice_files"]:
                self.assertIn(name, mapped)

    def test_webgpu_bridge_patch_is_narrow_and_fails_closed(self):
        generated = (
            "export function unrelated() { return 1; }\n"
            "function request_device(arg0, arg1) {\n"
            "    const ret = arg0.requestDevice(arg1);\n"
            "    return ret;\n}\n"
        )
        patched = build.patch_webgpu_bridge(generated)
        self.assertTrue(patched.startswith("import {requestDeviceCompat} from './webgpu-compat.js';\n"))
        self.assertIn("const ret = requestDeviceCompat(arg0, arg1);", patched)
        self.assertIn("export function unrelated() { return 1; }", patched)
        self.assertNotIn("arg0.requestDevice(arg1)", patched)
        for invalid in ["", generated + generated,
                        generated.replace("arg0.requestDevice(arg1)", "arg0.requestDevice(arg2)"),
                        generated.replace("requestDevice(arg1)", "requestDevice( arg1 )"), patched]:
            with self.subTest(source=invalid), self.assertRaisesRegex(ValueError, "exactly one unpatched"):
                build.patch_webgpu_bridge(invalid)


if __name__ == "__main__":
    unittest.main()
