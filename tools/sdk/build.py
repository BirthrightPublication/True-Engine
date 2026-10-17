"""Build and stage the real browser SDK using pinned Rust/wasm-bindgen tools."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from shared import ROOT, STAGE_MARKER, compatibility, engine_version, hashes, json_bytes, output, payload, source_state, tool_versions


WEBGPU_BRIDGE_PATCH_VERSION = 1


def patch_webgpu_bridge(javascript: str) -> str:
    """Route the single pinned generated requestDevice stub through our helper.

    Reject generator drift rather than silently shipping an unpatched or partly
    patched binding. This does not alter browser globals or implement an adapter.
    """
    original = "const ret = arg0.requestDevice(arg1);"
    import_line = "import {requestDeviceCompat} from './webgpu-compat.js';"
    if javascript.count(original) != 1 or import_line in javascript:
        raise ValueError("Expected exactly one unpatched wasm-bindgen requestDevice stub")
    return import_line + "\n" + javascript.replace(original, "const ret = requestDeviceCompat(arg0, arg1);", 1)


def verify_tools() -> dict:
    rust, bindgen = tool_versions()
    actual_rust = output(["rustc", "--version"])
    actual_bindgen = output(["wasm-bindgen", "--version"])
    if actual_rust.split()[1] != rust:
        raise ValueError(f"Rust {rust} is required, found {actual_rust}")
    if actual_bindgen != f"wasm-bindgen {bindgen}":
        raise ValueError(f"wasm-bindgen {bindgen} is required, found {actual_bindgen}")
    if not Path(output(["rustc", "--print", "target-libdir", "--target", "wasm32-unknown-unknown"])).is_dir():
        raise ValueError(f"Install the target first: rustup target add wasm32-unknown-unknown --toolchain {rust}")
    return {"rustc": actual_rust, "cargo": output(["cargo", "--version"]), "wasm_bindgen": actual_bindgen}


def cargo_metadata() -> dict:
    return json.loads(output([
        "cargo", "metadata", "--format-version", "1", "--locked", "--filter-platform", "wasm32-unknown-unknown"
    ]))


def dependency_notices(metadata: dict) -> dict[str, bytes]:
    spec = importlib.util.spec_from_file_location("true_engine_release_package", ROOT / "tools/release/package.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    collected = module.collect_notices(metadata, Path(output(["rustc", "--print", "sysroot"])))
    return remap_notices(collected)


def remap_notices(collected: dict[str, bytes]) -> dict[str, bytes]:
    """Move both license files and inventory references into the SDK package."""
    def sdk_path(name: str) -> str:
        if not name.startswith("app/notices/"):
            raise ValueError("Unexpected shared notice path")
        return "package/" + name.removeprefix("app/")

    mapped = {sdk_path(name): data for name, data in collected.items()}
    inventory_path = "package/notices/dependencies.json"
    inventory = json.loads(mapped[inventory_path])
    inventory["scope"] = (
        "Conservative resolved workspace Cargo graph filtered to wasm32-unknown-unknown; "
        "may include unshipped build/dev/example components; not a linked-binary SBOM"
    )
    for dependency in inventory["packages"]:
        dependency["notice_files"] = [sdk_path(name) for name in dependency["notice_files"]]
    mapped[inventory_path] = json_bytes(inventory)
    return mapped


def copy_required(source: Path, destination: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"Missing regular SDK input: {source.relative_to(ROOT)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def build(stage: Path) -> dict:
    tools = verify_tools()
    version = engine_version()
    package_json = json.loads((ROOT / "sdk/web/package.json").read_text(encoding="utf-8"))
    if package_json.get("name") != "@birthright/true-engine" or package_json.get("version") != version:
        raise ValueError("Browser package name/version must match @birthright/true-engine and Cargo workspace version")
    if stage.exists() and not (stage / STAGE_MARKER).is_file():
        raise ValueError("Refusing to replace an existing directory without the SDK staging marker")
    state = source_state()
    metadata = cargo_metadata()
    subprocess.run([
        "cargo", "build", "--release", "-p", "true-engine-web", "--target", "wasm32-unknown-unknown", "--locked"
    ], cwd=ROOT, check=True)
    stage.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".true-engine-sdk-build-", dir=stage.parent) as temporary:
        staged = Path(temporary) / "sdk"
        (staged / "package").mkdir(parents=True)
        subprocess.run([
            "wasm-bindgen", str(Path(metadata["target_directory"]) / "wasm32-unknown-unknown/release/true_engine_web.wasm"),
            "--target", "web", "--out-name", "true_engine_web", "--out-dir", str(staged / "package")
        ], cwd=ROOT, check=True)
        generated_javascript = staged / "package/true_engine_web.js"
        generated_javascript.write_text(
            patch_webgpu_bridge(generated_javascript.read_text(encoding="utf-8")),
            encoding="utf-8", newline="\n",
        )
        for name in ["index.js", "index.d.ts", "package.json", "webgpu-compat.js"]:
            copy_required(ROOT / "sdk/web" / name, staged / "package" / name)
        for name in ["index.html", "app.js", "style.css"]:
            copy_required(ROOT / "examples/browser-sdk" / name, staged / "example" / name)
        for name in ["BROWSER_SDK_API.md", "SDK_WINDOWS_BUILD.md"]:
            copy_required(ROOT / "docs" / name, staged / "docs" / name)
        for name in ["PLATE_STUDIO_INTEGRATION.md", "SDK-0.1.md"]:
            if (ROOT / "docs" / name).is_file():
                copy_required(ROOT / "docs" / name, staged / "docs" / name)
        for name in [f"SDK_VALIDATION-{version}.md", f"RELEASE-{version}.md"]:
            copy_required(ROOT / "docs" / name, staged / "docs" / name)
        copy_required(ROOT / "CHANGELOG.md", staged / "docs/CHANGELOG.md")
        copy_required(ROOT / "LICENSING.md", staged / "docs/LICENSING.md")
        copy_required(ROOT / "LICENSING.md", staged / "package/LICENSING.md")
        for name, data in dependency_notices(metadata).items():
            destination = staged / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        (staged / "compatibility.json").write_bytes(json_bytes(compatibility(version, state)))
        if source_state() != state:
            raise ValueError("Source changed during SDK build; rerun after edits finish")
        marker = {
            "format_version": 1,
            "version": version,
            **state,
            "build_tools": tools,
            "build_platform": sys.platform,
            "webgpu_bridge_patch_version": WEBGPU_BRIDGE_PATCH_VERSION,
            "files": hashes(payload(staged)),
        }
        (staged / STAGE_MARKER).write_bytes(json_bytes(marker))
        if stage.exists():
            shutil.rmtree(stage)
        shutil.move(str(staged), str(stage))
    return marker


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=ROOT / "Build/sdk-web")
    arguments = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or newer is required")
    marker = build(arguments.stage.resolve())
    print(f"Staged True Engine SDK {marker['version']} at {arguments.stage}")
    print("Run browser integration tests, then pack.py with their actual evidence JSON.")


if __name__ == "__main__":
    main()
