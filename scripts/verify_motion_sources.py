"""Verify a source snapshot, make a tar, or restore it without extracting tar paths.

The manifest is an integrity inventory, not a signature or an independent backup.
"""

import argparse
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
from pathlib import Path, PurePosixPath

MAX_FILE = 4 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_FILES = 128
SPECIAL = {"README.md", "manifest.json"}
MANIFEST_SHA256 = "b1fbf3b7eba1aaaf28e0a513763648ebf5c54621f5e7655dccc5cbb7f1af4883"
README_SHA256 = "abd8f70a062bf8faf7dd70843a254cf11a33fa1c6893984fb1f9948f69f2886c"


class InvalidSnapshot(ValueError):
    """A snapshot or archive violates the expected format or hashes."""


def _name(name: object) -> str:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise InvalidSnapshot("invalid path")
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts) or str(PurePosixPath(name)) != name:
        raise InvalidSnapshot("invalid path")
    if name not in SPECIAL and (parts[0] != "original" or len(parts) < 2):
        raise InvalidSnapshot("path outside original")
    return name


def _manifest(data: bytes) -> dict[str, tuple[int, str, str]]:
    try:
        obj = json.loads(data)
        entries = obj["files"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES:
            raise InvalidSnapshot("invalid manifest entries")
        result = {}
        folded = set()
        total = 0
        for entry in entries:
            name = _name(entry["path"])
            size, sha, blob = entry["bytes"], entry["sha256"], entry["git_blob_sha1"]
            if name in SPECIAL or name.casefold() in folded:
                raise InvalidSnapshot("duplicate path")
            if type(size) is not int or not 0 <= size <= MAX_FILE:
                raise InvalidSnapshot("invalid size")
            if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
                raise InvalidSnapshot("invalid SHA-256")
            if not isinstance(blob, str) or not re.fullmatch(r"[0-9a-f]{40}", blob):
                raise InvalidSnapshot("invalid blob hash")
            total += size
            if total > MAX_TOTAL:
                raise InvalidSnapshot("snapshot too large")
            folded.add(name.casefold())
            result[name] = (size, sha, blob)
        return result
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidSnapshot("invalid manifest") from exc


def _check(contents: dict[str, bytes]) -> None:
    if not SPECIAL <= contents.keys():
        raise InvalidSnapshot("missing manifest or README")
    if hashlib.sha256(contents["manifest.json"]).hexdigest() != MANIFEST_SHA256:
        raise InvalidSnapshot("manifest integrity mismatch")
    if hashlib.sha256(contents["README.md"]).hexdigest() != README_SHA256:
        raise InvalidSnapshot("README integrity mismatch")
    entries = _manifest(contents["manifest.json"])
    if len(entries) != 16:
        raise InvalidSnapshot("unexpected source count")
    if set(contents) != set(entries) | SPECIAL:
        raise InvalidSnapshot("missing or unexpected files")
    for name, (size, sha, blob) in entries.items():
        data = contents[name]
        git_blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if len(data) != size or hashlib.sha256(data).hexdigest() != sha or git_blob != blob:
            raise InvalidSnapshot("source integrity mismatch")


def read_snapshot(root: Path) -> dict[str, bytes]:
    if root.is_symlink() or not root.is_dir():
        raise InvalidSnapshot("snapshot is not a directory")
    contents = {}
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise InvalidSnapshot("links are not allowed")
        if path.is_dir():
            continue
        if not path.is_file():
            raise InvalidSnapshot("not a regular file")
        name = _name(path.relative_to(root).as_posix())
        size = path.stat().st_size
        total += size
        if size > MAX_FILE or total > MAX_TOTAL or len(contents) >= MAX_FILES + len(SPECIAL):
            raise InvalidSnapshot("snapshot too large")
        contents[name] = path.read_bytes()
    _check(contents)
    return contents


def create_archive(root: Path, archive: Path) -> None:
    contents = read_snapshot(root)
    if archive.resolve().is_relative_to(root.resolve()):
        raise InvalidSnapshot("archive must be outside snapshot")
    with archive.open("xb") as target, tarfile.open(fileobj=target, mode="w") as tar:
        for name, data in sorted(contents.items()):
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = 0o644
            tar.addfile(entry, io.BytesIO(data))


def read_archive(archive: Path) -> dict[str, bytes]:
    contents = {}
    total = 0
    try:
        if archive.stat().st_size > MAX_TOTAL + 1024 * 1024:
            raise InvalidSnapshot("archive too large")
        with tarfile.open(archive, mode="r:") as tar:
            for member in tar:
                name = _name(member.name)
                if not member.isfile() or name in contents:
                    raise InvalidSnapshot("invalid archive member")
                total += member.size
                if not 0 <= member.size <= MAX_FILE or total > MAX_TOTAL or len(contents) >= MAX_FILES + len(SPECIAL):
                    raise InvalidSnapshot("archive too large")
                stream = tar.extractfile(member)
                if stream is None:
                    raise InvalidSnapshot("archive member unavailable")
                contents[name] = stream.read()
    except (tarfile.TarError, OSError) as exc:
        raise InvalidSnapshot("invalid archive") from exc
    _check(contents)
    return contents


def restore_archive(archive: Path, destination: Path) -> None:
    contents = read_archive(archive)
    destination.mkdir()  # Exclusive: never replace an existing destination.
    try:
        for name, data in contents.items():
            target = destination.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(data)
    except BaseException:
        shutil.rmtree(destination)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("snapshot", type=Path)
    pack = sub.add_parser("archive")
    pack.add_argument("snapshot", type=Path)
    pack.add_argument("archive", type=Path)
    restore = sub.add_parser("restore")
    restore.add_argument("archive", type=Path)
    restore.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "verify":
            read_snapshot(args.snapshot)
        elif args.command == "archive":
            create_archive(args.snapshot, args.archive)
        else:
            restore_archive(args.archive, args.destination)
    except (InvalidSnapshot, OSError) as exc:
        print(f"Falha de verificação: {exc}", file=sys.stderr)
        return 1
    print("Verificado. O manifesto não é assinatura nem backup independente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
