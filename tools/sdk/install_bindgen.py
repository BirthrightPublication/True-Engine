"""Install the checksum-pinned official wasm-bindgen CLI into an SDK build folder."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request


VERSION = "0.2.129"
ROOT = Path(__file__).resolve().parents[2]
ARCHIVES = {
    "Linux": (
        "x86_64-unknown-linux-musl",
        "82d12bb940e2d4e72e0d5605387fc1b8ca179044e012b620f0ce4e7440e8320e",
        "wasm-bindgen",
    ),
    "Windows": (
        "x86_64-pc-windows-msvc",
        "79e348c169d0c10c0b287647f1e753d0985353ca96800bc29be8f4261baf13e6",
        "wasm-bindgen.exe",
    ),
}


def install(directory: Path) -> Path:
    system = platform.system()
    if system not in ARCHIVES or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise ValueError("Pinned SDK CLI archives support Linux x64 and Windows x64 build hosts")
    target, expected_hash, executable = ARCHIVES[system]
    archive_root = f"wasm-bindgen-{VERSION}-{target}"
    url = f"https://github.com/wasm-bindgen/wasm-bindgen/releases/download/{VERSION}/{archive_root}.tar.gz"
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".wasm-bindgen-", dir=directory.parent) as temporary:
        archive = Path(temporary) / "upstream.tar.gz"
        digest = hashlib.sha256()
        total = 0
        request = urllib.request.Request(url, headers={"User-Agent": "True-Engine-SDK-build"})
        with urllib.request.urlopen(request, timeout=90) as response, archive.open("xb") as stream:
            if not response.geturl().startswith("https://"):
                raise ValueError("CLI download must retain HTTPS")
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 128 * 1024 * 1024:
                    raise ValueError("CLI archive exceeds expected download limit")
                digest.update(chunk)
                stream.write(chunk)
        if digest.hexdigest() != expected_hash:
            raise ValueError("Official wasm-bindgen archive SHA-256 does not match the pinned value")
        # Never use extract()/extractall(): only a single exact regular member is
        # copied to a fixed destination, so archive paths cannot escape it.
        with tarfile.open(archive, "r:gz") as bundle:
            matches = [item for item in bundle.getmembers() if item.name == f"{archive_root}/{executable}"]
            if len(matches) != 1 or not matches[0].isfile() or not 0 < matches[0].size <= 128 * 1024 * 1024:
                raise ValueError("Expected exactly one regular wasm-bindgen executable in the verified archive")
            member_stream = bundle.extractfile(matches[0])
            if member_stream is None:
                raise ValueError("Cannot read verified wasm-bindgen executable")
            extracted = Path(temporary) / executable
            with member_stream, extracted.open("xb") as stream:
                shutil.copyfileobj(member_stream, stream)
        extracted.chmod(0o755)
        actual = subprocess.check_output([str(extracted), "--version"], text=True).strip()
        if actual != f"wasm-bindgen {VERSION}":
            raise ValueError("Verified CLI reports an unexpected version")
        destination = directory / executable
        extracted.replace(destination)
    return directory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "Build/toolchain/bin")
    arguments = parser.parse_args()
    print(install(arguments.output.resolve()))


if __name__ == "__main__":
    main()
