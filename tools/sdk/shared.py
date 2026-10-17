"""Shared, standard-library-only SDK provenance and packaging helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[2]
STAGE_MARKER = ".true-engine-sdk-stage.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def output(command: list[str], root: Path = ROOT) -> str:
    return subprocess.check_output(command, cwd=root, text=True, encoding="utf-8").strip()


def source_state(root: Path = ROOT) -> dict:
    """Hash publishable source, including new files, without including ignored builds."""
    names = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root
    ).split(b"\0")
    digest = hashlib.sha256()
    for raw in sorted(set(names)):
        if not raw:
            continue
        path = root / raw.decode("utf-8")
        if not path.is_file():
            # Missing tracked files are part of the source state too.
            digest.update(raw + b"\0missing\0")
            continue
        digest.update(raw + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return {
        "source_commit": output(["git", "rev-parse", "HEAD"], root),
        "source_tree_sha256": digest.hexdigest(),
        "source_dirty": bool(output(["git", "status", "--porcelain", "--untracked-files=all"], root)),
    }


def engine_version(root: Path = ROOT) -> str:
    with (root / "Cargo.toml").open("rb") as stream:
        return tomllib.load(stream)["workspace"]["package"]["version"]


def tool_versions(root: Path = ROOT) -> tuple[str, str]:
    with (root / "rust-toolchain.toml").open("rb") as stream:
        rust_version = tomllib.load(stream)["toolchain"]["channel"]
    with (root / "Cargo.lock").open("rb") as stream:
        versions = {
            p["version"] for p in tomllib.load(stream)["package"] if p["name"] == "wasm-bindgen"
        }
    if len(versions) != 1:
        raise ValueError("Cargo.lock must resolve exactly one wasm-bindgen version")
    return rust_version, versions.pop()


def payload(stage: Path) -> dict[str, bytes]:
    files = {}
    for path in sorted(stage.rglob("*")):
        if path.is_symlink():
            raise ValueError("SDK staging directory must not contain symbolic links")
        if path.is_file() and path.name != STAGE_MARKER:
            files[path.relative_to(stage).as_posix()] = path.read_bytes()
    return files


def hashes(files: dict[str, bytes]) -> dict[str, str]:
    return {name: sha256(data) for name, data in sorted(files.items())}


def compatibility(version: str, source: dict) -> dict:
    return {
        "format_version": 1,
        "engine_version": version,
        "sdk_package": "@birthright/true-engine",
        "sdk_package_version": version,
        "native_rust_sdk_contract": "0.1",
        "native_project_schema": 1,
        "browser_document": {"format": "true-engine-web-project", "version": 1},
        "javascript_module_format": "ES modules with wasm-bindgen web bindings",
        "delivery": "Precompiled WebAssembly; Rust and Python are not application runtime dependencies",
        "renderer": "Existing True Engine wgpu renderer; WebGPU or WebGL2 backend selected at initialization",
        "recommended_initial_consumer_backend": "webgl2",
        "webgpu_qualification": "Experimental until target-platform presentation checks pass; cloud software presentation failed, see SDK validation notes",
        "browser_requirements": [
            "Modern browser with WebAssembly and an available WebGPU or WebGL2 adapter",
            "HTTP(S) server serving .wasm as application/wasm",
            "Secure context for WebGPU (HTTPS or localhost)",
        ],
        "object_identifiers": "positive unsigned 32-bit integers",
        "mesh_format": "Indexed triangle positions; procedural primitives also supported",
        "consumer_repository": "BirthrightPublication/License-Plate-Obfuscation",
        "consumer_dependency_policy": "Pin this SDK version or exact release archive SHA-256; do not duplicate engine source",
        "application_specific_logic": "Owned by the consuming application",
        "migration": "none; existing native schema 1 projects and Rust SDK 0.1 remain unchanged",
        "document_interchange": "Browser documents carry custom meshes separately; they are not native schema 1 project files",
        "platform_verification": "Only explicit test evidence in manifest.json establishes tested platforms/backends",
        "windows_execution": "No Windows runtime verification is implied by a Linux-built WebAssembly package",
        **source,
    }
