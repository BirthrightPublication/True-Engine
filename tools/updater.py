"""Offline updater. Expected SHA-256 must come from a trusted release channel."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import uuid
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def install(root, package, expected):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise ValueError("A trusted SHA-256 is required")
    raw = Path(package).read_bytes()
    if digest(raw) != expected.lower():
        raise ValueError("Package SHA-256 mismatch")
    lock = root / ".update-lock"
    lock.mkdir()  # fail closed for simultaneous updates or interrupted operations
    stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=root))
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = archive.namelist()
            if len(names) != len(set(n.casefold() for n in names)):
                raise ValueError("Duplicate package path")
            if sum(i.file_size for i in archive.infolist()) > 512 * 1024 * 1024:
                raise ValueError("Package too large")
            for item in archive.infolist():
                path = PurePosixPath(item.filename)
                if (path.is_absolute() or path.as_posix() != item.filename or not path.parts or any(p in ("..", ".") for p in path.parts)
                        or "\\" in item.filename or ":" in item.filename
                        or any(p.endswith((".", " ")) or any(ord(c) < 32 for c in p)
                               or p.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]} for p in path.parts)
                        or (item.external_attr >> 16) & 0o170000 == 0o120000):
                    raise ValueError("Unsafe package path")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest["sdk"] != "0.1" or manifest["schema"] != 1 or manifest["migration"] != "none":
                raise ValueError("Incompatible SDK/schema/migration")
            files = manifest["files"]
            if set(names) != set(files) | {"manifest.json"}:
                raise ValueError("Unlisted payload")
            for name, checksum in files.items():
                if not name.startswith("app/"):
                    raise ValueError("Only app/ files may be replaced")
                data = archive.read(name)
                if digest(data) != checksum:
                    raise ValueError("Payload checksum mismatch")
                dest = stage.joinpath(*PurePosixPath(name).parts[1:])
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            if not (stage / "true-engine-viewport.exe").is_file():
                raise ValueError("Missing viewport")
            (stage / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        current = root / "Current"
        backups = root / "Backups"
        backups.mkdir(exist_ok=True)
        backup = backups / uuid.uuid4().hex
        # Data is outside Current; never enumerate, delete or migrate it.
        if current.exists():
            current.rename(backup)
        try:
            stage.rename(current)
        except BaseException:
            if backup.exists():
                backup.rename(current)
            raise
        return backup if backup.exists() else None
    finally:
        if stage.exists():
            shutil.rmtree(stage)
        lock.rmdir()


def rollback(root, backup_name):
    root = Path(root).resolve()
    if not re.fullmatch(r"[0-9a-f]{32}", backup_name):
        raise ValueError("Invalid backup ID")
    backup = root / "Backups" / backup_name
    if not backup.is_dir():
        raise ValueError("Backup missing")
    lock = root / ".update-lock"
    lock.mkdir()
    current = root / "Current"
    displaced = root / "Backups" / uuid.uuid4().hex
    try:
        if current.exists():
            current.rename(displaced)
        try:
            backup.rename(current)
        except BaseException:
            if displaced.exists():
                displaced.rename(current)
            raise
    finally:
        lock.rmdir()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=r"B:\True Engine")
    parser.add_argument("--package")
    parser.add_argument("--sha256")
    parser.add_argument("--rollback")
    args = parser.parse_args()
    if args.rollback:
        rollback(args.root, args.rollback)
    elif args.package and args.sha256:
        print("Backup:", install(args.root, args.package, args.sha256))
    else:
        parser.error("Use --package and --sha256, or --rollback BACKUP_ID")
