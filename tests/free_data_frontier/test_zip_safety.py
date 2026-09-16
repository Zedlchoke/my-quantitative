import hashlib
import json
import zipfile

import pytest

from research.free_data_frontier.ziputils import (
    ZipSafetyRefusal,
    extract_members,
    inspect_zip,
)


def _make_zip(path, entries):
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries:
            archive.writestr(name, data)


def test_inspect_zip_counts_entries_and_bytes(tmp_path):
    z = tmp_path / "a.zip"
    _make_zip(z, [("dir/file.xml", b"<x/>" * 10), ("b.txt", b"hello")])
    report = inspect_zip(z, max_total_uncompressed_bytes=1000, max_entries=10)
    assert report["entries"] == 2
    assert report["total_uncompressed_bytes"] == 40 + 5


def test_inspect_zip_refuses_oversize(tmp_path):
    z = tmp_path / "a.zip"
    _make_zip(z, [("big.bin", b"0" * 100)])
    with pytest.raises(ZipSafetyRefusal):
        inspect_zip(z, max_total_uncompressed_bytes=10, max_entries=10)


def test_inspect_zip_refuses_too_many_entries(tmp_path):
    z = tmp_path / "a.zip"
    _make_zip(z, [(f"f{i}.txt", b"x") for i in range(5)])
    with pytest.raises(ZipSafetyRefusal):
        inspect_zip(z, max_total_uncompressed_bytes=1000, max_entries=3)


@pytest.mark.parametrize(
    "name",
    ["../escape.txt", "/abs/path.txt", "a/../../out.txt"],
)
def test_unsafe_member_paths_refused(tmp_path, name):
    z = tmp_path / "evil.zip"
    _make_zip(z, [(name, b"x")])
    with pytest.raises(ZipSafetyRefusal):
        inspect_zip(z, max_total_uncompressed_bytes=1000, max_entries=10)
    with pytest.raises(ZipSafetyRefusal):
        extract_members(
            z, tmp_path / "out", max_total_uncompressed_bytes=1000, max_entries=10
        )
    assert not (tmp_path / "escape.txt").exists()


def test_extract_members_selects_only_named(tmp_path):
    z = tmp_path / "a.zip"
    _make_zip(z, [("keep.txt", b"keep-me"), ("skip.txt", b"skip-me")])
    out = extract_members(
        z,
        tmp_path / "out",
        ["keep.txt"],
        max_total_uncompressed_bytes=1000,
        max_entries=10,
    )
    assert (tmp_path / "out" / "keep.txt").read_bytes() == b"keep-me"
    assert not (tmp_path / "out" / "skip.txt").exists()
    assert len(out) == 1


def test_extract_refuses_member_larger_than_declared(tmp_path):
    z = tmp_path / "trunc.zip"
    # build a zip whose internal member size lies: craft via zip and truncate
    with zipfile.ZipFile(z, "w") as archive:
        archive.writestr("f.txt", b"0123456789" * 100)
    raw = z.read_bytes()
    z.write_bytes(raw[: len(raw) - 200])  # corrupt central/exit region
    with pytest.raises(Exception):
        extract_members(
            z, tmp_path / "out", ["f.txt"], max_total_uncompressed_bytes=10**6, max_entries=10
        )
