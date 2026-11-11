import io
import json
import shutil
import tarfile
from pathlib import Path

import pytest

from scripts.verify_motion_sources import (
    InvalidSnapshot,
    _manifest,
    create_archive,
    read_archive,
    read_snapshot,
    restore_archive,
)

SOURCE = Path(__file__).resolve().parents[3] / "vendor/motion_sources/claude-video"


def test_snapshot_archive_restore_roundtrip(tmp_path):
    expected = read_snapshot(SOURCE)
    archive = tmp_path / "sources.tar"
    create_archive(SOURCE, archive)
    assert read_archive(archive) == expected
    restored = tmp_path / "restored"
    restore_archive(archive, restored)
    assert read_snapshot(restored) == expected
    with pytest.raises(FileExistsError):
        restore_archive(archive, restored)
    with pytest.raises(FileExistsError):
        create_archive(SOURCE, archive)


@pytest.mark.parametrize("change", ["corrupt", "missing", "extra", "link", "readme"])
def test_snapshot_rejects_changed_missing_extra_or_link(tmp_path, change):
    snapshot = tmp_path / "snapshot"
    shutil.copytree(SOURCE, snapshot)
    original = snapshot / "original/LICENSE"
    if change == "corrupt":
        original.write_bytes(b"different")
    elif change == "missing":
        original.unlink()
    elif change == "extra":
        (snapshot / "original/extra.txt").write_text("unexpected")
    elif change == "link":
        original.unlink()
        original.symlink_to(snapshot / "original/LICENSE-original.txt")
    else:
        (snapshot / "README.md").write_text("changed")
    with pytest.raises(InvalidSnapshot):
        read_snapshot(snapshot)


@pytest.mark.parametrize("path", ["../outside", "/absolute", "original/../outside", "original\\escape"])
def test_manifest_rejects_unsafe_paths(tmp_path, path):
    snapshot = tmp_path / "snapshot"
    shutil.copytree(SOURCE, snapshot)
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][0]["path"] = path
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(InvalidSnapshot):
        _manifest(manifest_path.read_bytes())
    with pytest.raises(InvalidSnapshot):
        read_snapshot(snapshot)


@pytest.mark.parametrize(
    "name,kind", [("../escape", "file"), ("original/link", "symlink"), ("original/link", "hardlink")]
)
def test_archive_rejects_unsafe_members_before_restore(tmp_path, name, kind):
    archive = tmp_path / "malicious.tar"
    with tarfile.open(archive, "w") as tar:
        member = tarfile.TarInfo(name)
        if kind != "file":
            member.type = tarfile.SYMTYPE if kind == "symlink" else tarfile.LNKTYPE
            member.linkname = "../../escape"
        else:
            member.size = 1
        tar.addfile(member, io.BytesIO(b"x") if kind == "file" else None)
    destination = tmp_path / "restored"
    with pytest.raises(InvalidSnapshot):
        restore_archive(archive, destination)
    assert not destination.exists()
    assert not (tmp_path / "escape").exists()


def test_archive_rejects_corrupt_and_duplicate_members(tmp_path):
    contents = read_snapshot(SOURCE)
    contents["original/LICENSE"] = b"changed"
    archive = tmp_path / "corrupt.tar"
    with tarfile.open(archive, "w") as tar:
        for name, data in contents.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
    with pytest.raises(InvalidSnapshot):
        read_archive(archive)
    duplicate = tmp_path / "duplicate.tar"
    with tarfile.open(duplicate, "w") as tar:
        for _ in range(2):
            tar.addfile(tarfile.TarInfo("README.md"), io.BytesIO())
    with pytest.raises(InvalidSnapshot):
        read_archive(duplicate)


def test_archive_must_not_be_written_inside_snapshot(tmp_path):
    snapshot = tmp_path / "snapshot"
    shutil.copytree(SOURCE, snapshot)
    with pytest.raises(InvalidSnapshot):
        create_archive(snapshot, snapshot / "archive.tar")
    assert not (snapshot / "archive.tar").exists()
