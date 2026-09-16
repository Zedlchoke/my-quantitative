"""ZIP safety: path traversal refusal and bounded extraction."""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional

from .contract import ContractError, SchemaRefusal


class ZipSafetyRefusal(ContractError):
    """A zip member is unsafe or the archive is unbounded."""


def inspect_zip(
    zip_path: Path,
    *,
    max_total_uncompressed_bytes: int,
    max_entries: int,
) -> Dict[str, Any]:
    """Read the central directory only; refuse archives beyond bounds or with
    unsafe member paths. No bytes are extracted."""
    with zipfile.ZipFile(zip_path) as archive:
        infos = archive.infolist()
        if len(infos) > max_entries:
            raise ZipSafetyRefusal(
                f"{len(infos)} entries exceeds cap {max_entries}"
            )
        total = sum(info.file_size for info in infos)
        if total > max_total_uncompressed_bytes:
            raise ZipSafetyRefusal(
                f"total uncompressed {total} exceeds cap {max_total_uncompressed_bytes}"
            )
        members = []
        for info in infos:
            pure = PurePosixPath(info.filename)
            if pure.is_absolute() or ".." in pure.parts:
                raise ZipSafetyRefusal(f"unsafe member path: {info.filename!r}")
            if info.filename.endswith("/"):
                continue
            members.append({"name": info.filename, "size": info.file_size})
    return {"entries": len(infos), "total_uncompressed_bytes": total, "members": members}


def extract_members(
    zip_path: Path,
    dest_dir: Path,
    member_names: Optional[List[str]] = None,
    *,
    max_total_uncompressed_bytes: int,
    max_entries: int,
) -> List[Path]:
    """Extract selected (or all safe) members under caps; refusal otherwise."""
    inspection = inspect_zip(
        zip_path,
        max_total_uncompressed_bytes=max_total_uncompressed_bytes,
        max_entries=max_entries,
    )
    wanted = set(member_names) if member_names is not None else None
    extracted: List[Path] = []
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in inspection["members"]:
            if wanted is not None and member["name"] not in wanted:
                continue
            pure = PurePosixPath(member["name"])
            target = dest_dir.joinpath(*pure.parts)
            if not target.resolve().is_relative_to(dest_dir.resolve()):
                raise ZipSafetyRefusal(f"resolved path escapes dest: {member['name']!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member["name"]) as src, target.open("wb") as out:
                remaining = member["size"]
                while remaining > 0:
                    chunk = src.read(min(1024 * 512, remaining))
                    if not chunk:
                        raise SchemaRefusal(
                            f"member {member['name']!r} truncated inside archive"
                        )
                    out.write(chunk)
                    remaining -= len(chunk)
            extracted.append(target)
    return extracted
