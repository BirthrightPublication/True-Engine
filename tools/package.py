"""Package an already built Windows executable; never labels cross-platform tests as run."""
import argparse
from pathlib import Path
import json
import re
import struct
import zipfile
from updater import digest

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--version", default="0.1.0")
    p.add_argument("--runtime-file", type=Path, action="append", default=[], help="DLL or dependency notice to retain beside the executable")
    p.add_argument("--tests", type=Path, required=True, help="JSON array of actual commands and results")
    p.add_argument("--output", type=Path, default=Path(r"B:\True Engine\Build"))
    a = p.parse_args()
    binary = a.binary.read_bytes()
    if len(binary) < 64 or binary[:2] != b"MZ":
        p.error("Expected a Windows PE executable")
    pe = struct.unpack_from("<I", binary, 0x3c)[0]
    if pe + 24 > len(binary) or binary[pe:pe+4] != b"PE\0\0" or struct.unpack_from("<H", binary, pe+4)[0] != 0x8664:
        p.error("Expected an x64 Windows PE executable")
    if not re.fullmatch(r"0\.1\.[0-9]+", a.version):
        p.error("Only the approved 0.1 release line is supported")
    tests = json.loads(a.tests.read_text(encoding="utf-8-sig"))
    if not isinstance(tests, list) or not tests:
        p.error("Actual test evidence is required")
    payload = {"app/true-engine-viewport.exe": binary}
    for runtime in a.runtime_file:
        name = "app/" + runtime.name
        if name.casefold() in {key.casefold() for key in payload}:
            p.error("Duplicate runtime payload name")
        payload[name] = runtime.read_bytes()
    manifest = dict(version=a.version, sdk="0.1", schema=1, migration="none",
                    compatibility="SDK 0.1; schema 1; Windows 10+ x64 with UCRT; Python 3.10+ updater",
                    changed_files=list(payload), tests=tests,
                    files={n: digest(b) for n, b in payload.items()})
    a.output.mkdir(parents=True, exist_ok=True)
    dest = a.output / f"True-Engine-{a.version}-windows-x64.zip"
    if dest.exists():
        raise FileExistsError(f"Preserving existing release: {dest}")
    for name in ["updater.py", "Update.cmd", "Rollback.cmd", "Launch.cmd"]:
        target = a.output.parent / name
        if target.exists() and target.read_bytes() != Path(__file__).with_name(name).read_bytes():
            raise FileExistsError(f"Preserving existing file: {target}")
    with zipfile.ZipFile(dest, "x", zipfile.ZIP_DEFLATED) as z:
        for name, data in payload.items():
            z.writestr(name, data)
        z.writestr("manifest.json", json.dumps(manifest, indent=2))
    (dest.with_suffix(".zip.sha256")).write_text(digest(dest.read_bytes()) + "  " + dest.name + "\n")
    for name in ["updater.py", "Update.cmd", "Rollback.cmd", "Launch.cmd"]:
        target = a.output.parent / name
        if target.exists() and target.read_bytes() != Path(__file__).with_name(name).read_bytes():
            raise FileExistsError(f"Preserving existing file: {target}")
        target.write_bytes(Path(__file__).with_name(name).read_bytes())
    print(dest)
