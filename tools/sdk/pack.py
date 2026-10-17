"""Package a tested SDK stage without overwriting any existing release archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import zipfile

from shared import ROOT, STAGE_MARKER, engine_version, hashes, json_bytes, output, payload, sha256, source_state


def validate_evidence(evidence: object) -> list[dict]:
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("Nonempty actual test evidence array is required")
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get("command"), str) or not item["command"].strip():
            raise ValueError("Each test evidence entry must name its actual command")
        if type(item.get("exit_code")) is not int or item["exit_code"] != 0:
            raise ValueError("Each released test must have an explicit successful exit_code: 0")
    return evidence


def write_archive(destination: Path, files: dict[str, bytes]) -> str:
    checksum_path = destination.with_suffix(destination.suffix + ".sha256")
    if destination.exists() or checksum_path.exists():
        raise FileExistsError(f"Release assets are immutable: {destination.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    created = False
    created_checksum = False
    try:
        with destination.open("xb") as stream:
            created = True
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for name, data in sorted(files.items()):
                    item = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
                    item.create_system = 3
                    item.external_attr = 0o100644 << 16
                    item.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(item, data, compresslevel=9)
        digest = sha256(destination.read_bytes())
        with checksum_path.open("x", encoding="utf-8", newline="\n") as stream:
            created_checksum = True
            stream.write(f"{digest}  {destination.name}\n")
        return digest
    except BaseException:
        # Remove only our incomplete new archive; never touch a prior asset.
        if created:
            destination.unlink(missing_ok=True)
        if created_checksum:
            checksum_path.unlink(missing_ok=True)
        raise


def package(stage: Path, evidence: object, destination: Path, candidate: bool = False) -> tuple[Path, str]:
    evidence = validate_evidence(evidence)
    marker = json.loads((stage / STAGE_MARKER).read_text(encoding="utf-8"))
    version = engine_version()
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
        raise ValueError("Stable semantic engine version required")
    if marker.get("version") != version:
        raise ValueError("Staged SDK version differs from source version")
    state = source_state()
    for key, value in state.items():
        if marker.get(key) != value:
            raise ValueError("Source changed after staging; rebuild and retest the SDK")
    tag = None
    if not candidate:
        if state["source_dirty"]:
            raise ValueError("Release packaging requires a clean source tree")
        tag = f"v{version}"
        tag_commit = output(["git", "rev-parse", f"{tag}^{{commit}}"])
        if tag_commit != state["source_commit"]:
            raise ValueError("Release packaging requires HEAD at its exact version tag")
    files = payload(stage)
    if hashes(files) != marker.get("files"):
        raise ValueError("Staged files changed after build; rebuild and retest before packaging")
    if not files.get("package/true_engine_web_bg.wasm", b"").startswith(b"\0asm\x01\0\0\0"):
        raise ValueError("SDK must contain an actual WebAssembly version 1 binary")
    package_json = json.loads(files["package/package.json"])
    if package_json.get("version") != version or package_json.get("name") != "@birthright/true-engine":
        raise ValueError("Staged npm package version/name mismatch")
    manifest = {
        "format_version": 1,
        "version": version,
        "sdk": "0.1",
        "schema": 1,
        "browser_document_format": "true-engine-web-project",
        "browser_document_version": 1,
        "migration": "none",
        "candidate": candidate,
        "source_tag": tag,
        **state,
        "build_tools": marker["build_tools"],
        "build_platform": marker["build_platform"],
        "webgpu_bridge_patch_version": marker.get("webgpu_bridge_patch_version"),
        "tests": evidence,
        "verification_scope": "Only the commands/platforms/backends named in actual test evidence are verified",
        "windows_runtime_verified": False,
        "files": hashes(files),
    }
    files["manifest.json"] = json_bytes(manifest)
    archive = destination / f"True-Engine-SDK-v{version}-web.zip"
    return archive, write_archive(archive, files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=ROOT / "Build/sdk-web")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "Build")
    parser.add_argument("--candidate", action="store_true", help="Untargeted/dirty local build; never label it a tagged release")
    arguments = parser.parse_args()
    evidence = json.loads(arguments.evidence.read_text(encoding="utf-8-sig"))
    archive, digest = package(arguments.stage.resolve(), evidence, arguments.output.resolve(), arguments.candidate)
    print(archive)
    print(digest)


if __name__ == "__main__":
    main()
