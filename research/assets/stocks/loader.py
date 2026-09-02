"""Local parquet bar/event loader with checksum manifest (owner: A3).

The only data path in this sprint is owner-supplied Parquet (PLAN_stocks.md
section 2, option 4) read through pyarrow.  Layout::

    <root>/<security_id>/bars_<YYYY>.parquet
    <root>/checksum_manifest.json     # {"schema": ..., "files": {relpath: sha256}}

Contract:

* every row carries BOTH an exchange timestamp (``ts_exchange``, tz-aware)
  and an ingest timestamp (``ts_ingest``); ``ts_ingest >= ts_exchange`` is
  validated per row;
* the loader is strictly read-only and verifies the sha256 of every partition
  it touches against the manifest BEFORE reading it;
* fail-closed on missing partitions (a window whose year partition file does
  not exist is an error, never a silent truncation), on unmanifested or
  tampered files, and on observation gaps beyond a DECLARED tolerance
  (``gap_tolerance_days``, a required constructor argument — there is no
  implicit tolerance).  When a session predicate is injected, gap accounting
  counts only days the predicate declares to be sessions; otherwise raw
  calendar days are counted.

Writing parquet/manifests is a data-preparation concern (and a test-fixture
concern); the helpers ``write_bars``/``write_checksum_manifest`` exist for
that and must only ever be pointed at prepared/staging locations.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Callable, Mapping

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from research.assets.common.contracts import require_token

MANIFEST_FILENAME = "checksum_manifest.json"
MANIFEST_SCHEMA = "stocks.bar_checksum_manifest"
MANIFEST_VERSION = 1

REQUIRED_BAR_COLUMNS = (
    "security_id",
    "ts_exchange",
    "ts_ingest",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

SessionPredicate = Callable[[date], bool]


class LoaderError(Exception):
    """Base error for the local bar/event loader."""


class MissingPartitionError(LoaderError):
    """A required partition file does not exist (fail-closed truncation guard)."""


class ChecksumError(LoaderError):
    """A file is unmanifested or its sha256 does not match the manifest."""


class SchemaError(LoaderError):
    """The parquet payload violates the bar/event schema contract."""


class GapError(LoaderError):
    """Observations are missing beyond the declared tolerance."""


def partition_relpath(security_id: str, year: int) -> str:
    """Relative partition path for one security-year."""
    require_token(security_id, "security_id")
    if not isinstance(year, int) or isinstance(year, bool) or not 1900 <= year <= 2200:
        raise ValueError(f"year must be a plausible calendar year, got {year!r}")
    return f"{security_id}/bars_{year:04d}.parquet"


def sha256_file(path: Path) -> str:
    """Chunked sha256 of a file (used for the manifest and verification)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_checksum_manifest(root: Path) -> dict[str, str]:
    """sha256 for every ``**/*.parquet`` under ``root`` (sorted, stable)."""
    root = Path(root)
    files = sorted(p for p in root.rglob("*.parquet") if p.is_file())
    return {
        p.relative_to(root).as_posix(): sha256_file(p)
        for p in files
    }


def write_checksum_manifest(root: Path, *, path: Path | None = None) -> Path:
    """Write the manifest for all parquet files under ``root`` (data prep only)."""
    root = Path(root)
    target = Path(path) if path is not None else root / MANIFEST_FILENAME
    payload = {
        "schema": MANIFEST_SCHEMA,
        "version": MANIFEST_VERSION,
        "files": build_checksum_manifest(root),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return target


def read_checksum_manifest(path: Path) -> dict[str, str]:
    """Read and validate a checksum manifest; returns ``{relpath: sha256}``."""
    path = Path(path)
    if not path.is_file():
        raise ChecksumError(f"checksum manifest not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ChecksumError(f"checksum manifest is not valid JSON: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != MANIFEST_SCHEMA:
        raise ChecksumError(f"unrecognized checksum manifest schema: {path}")
    files = payload.get("files")
    if not isinstance(files, dict) or not files:
        raise ChecksumError(f"checksum manifest has no files section: {path}")
    for relpath, digest in files.items():
        if not isinstance(relpath, str) or not isinstance(digest, str):
            raise ChecksumError(f"malformed manifest entry for {relpath!r}")
        if len(digest) != 64:
            raise ChecksumError(f"manifest digest for {relpath!r} is not sha256 hex")
    return dict(files)


def write_bars(root: Path, security_id: str, frame: pd.DataFrame) -> list[Path]:
    """Data-prep helper: write security-year partitions (caller-owned location).

    The frame must carry a ``year`` column; one partition is written per year
    present.  The manifest is NOT touched here (call
    ``write_checksum_manifest`` after all partitions exist).
    """
    root = Path(root)
    if "year" not in frame.columns:
        raise SchemaError("write_bars expects a 'year' column marking each partition")
    written: list[Path] = []
    for year, subframe in frame.groupby("year"):
        target = root / partition_relpath(security_id, int(year))
        target.parent.mkdir(parents=True, exist_ok=True)
        table = pa.Table.from_pandas(subframe.drop(columns=["year"]), preserve_index=False)
        pq.write_table(table, target)
        written.append(target)
    return written


class BarLoader:
    """Read-only, checksum-verified, gap-aware loader over local parquet."""

    def __init__(
        self,
        root: Path,
        *,
        gap_tolerance_days: int,
        manifest_path: Path | None = None,
        session_predicate: SessionPredicate | None = None,
        enforce_gaps: bool = True,
    ) -> None:
        self._root = Path(root)
        if not self._root.is_dir():
            raise LoaderError(f"loader root does not exist: {self._root}")
        if isinstance(gap_tolerance_days, bool) or not isinstance(gap_tolerance_days, int) \
                or gap_tolerance_days < 0:
            raise ValueError(
                "gap_tolerance_days must be a declared, non-negative int "
                "(no implicit tolerance is allowed)"
            )
        self._gap_tolerance_days = gap_tolerance_days
        self._manifest_path = (
            Path(manifest_path) if manifest_path is not None
            else self._root / MANIFEST_FILENAME
        )
        self._session_predicate = session_predicate
        self._enforce_gaps = enforce_gaps

    @property
    def root(self) -> Path:
        return self._root

    def load(
        self,
        security_id: str,
        start: date,
        end: date,
        *,
        allow_duplicate_timestamps: bool = False,
    ) -> pd.DataFrame:
        """Load bars/events for ``security_id`` in the inclusive date window.

        Fails closed on: missing partition files, unmanifested/tampered files,
        schema violations, empty windows, duplicate exchange timestamps
        (unless ``allow_duplicate_timestamps`` for event streams) and gaps
        beyond the declared tolerance.
        """
        require_token(security_id, "security_id")
        if not isinstance(start, date) or not isinstance(end, date):
            raise LoaderError("start/end must be datetime.date")
        if end < start:
            raise LoaderError("end precedes start")
        manifest = read_checksum_manifest(self._manifest_path)
        relpaths = []
        for year in range(start.year, end.year + 1):
            relpath = partition_relpath(security_id, year)
            path = self._root / relpath
            if not path.is_file():
                raise MissingPartitionError(
                    f"missing partition {relpath!r} required for window "
                    f"{start.isoformat()}..{end.isoformat()}"
                )
            if relpath not in manifest:
                raise ChecksumError(f"partition {relpath!r} is not in the manifest")
            actual = sha256_file(path)
            if actual != manifest[relpath]:
                raise ChecksumError(
                    f"checksum mismatch for {relpath!r}: manifest "
                    f"{manifest[relpath]} != actual {actual}"
                )
            relpaths.append((relpath, path))
        frames = []
        for _, path in relpaths:
            try:
                frames.append(pq.read_table(path).to_pandas())
            except Exception as exc:  # pragma: no cover - pyarrow-level corruption
                raise LoaderError(f"unreadable parquet partition: {path}") from exc
        frame = pd.concat(frames, ignore_index=True)
        self._validate_schema(frame, security_id)
        lower = pd.Timestamp(start, tz="UTC")
        upper = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
        frame = frame.loc[
            (frame["ts_exchange"] >= lower) & (frame["ts_exchange"] < upper)
        ]
        if frame.empty:
            raise LoaderError(
                f"no observations for {security_id!r} in "
                f"{start.isoformat()}..{end.isoformat()}; refusing to return an "
                "empty window"
            )
        if not allow_duplicate_timestamps and frame["ts_exchange"].duplicated().any():
            dupes = frame.loc[
                frame["ts_exchange"].duplicated(keep=False), "ts_exchange"
            ].iloc[:5].tolist()
            raise SchemaError(
                f"duplicate exchange timestamps for {security_id!r}: {dupes}"
            )
        if self._enforce_gaps:
            observed = sorted(set(frame["ts_exchange"].dt.date))
            self._assert_gaps(security_id, observed)
        return frame.sort_values("ts_exchange").reset_index(drop=True)

    def _validate_schema(self, frame: pd.DataFrame, security_id: str) -> None:
        missing = [c for c in REQUIRED_BAR_COLUMNS if c not in frame.columns]
        if missing:
            raise SchemaError(f"partition is missing required columns: {missing}")
        foreign = frame.loc[frame["security_id"] != security_id, "security_id"]
        if not foreign.empty:
            raise SchemaError(
                f"partition for {security_id!r} contains rows for "
                f"{sorted(set(foreign))[:5]}"
            )
        for column in ("ts_exchange", "ts_ingest"):
            try:
                frame[column] = pd.to_datetime(frame[column], utc=True, errors="raise")
            except (TypeError, ValueError) as exc:
                raise SchemaError(
                    f"column {column!r} is not a parsable timestamp"
                ) from exc
            if frame[column].dt.tz is None:
                raise SchemaError(f"column {column!r} must be tz-aware")
        late = frame.index[frame["ts_ingest"] < frame["ts_exchange"]]
        if len(late):
            raise SchemaError(
                f"{len(late)} rows have ts_ingest before ts_exchange "
                f"(first rows at index {late[:5].tolist()})"
            )
        for column in ("open", "high", "low", "close", "volume"):
            if not pd.api.types.is_numeric_dtype(frame[column]):
                raise SchemaError(f"column {column!r} must be numeric")

    def _assert_gaps(self, security_id: str, observed: list[date]) -> None:
        for previous, following in zip(observed, observed[1:]):
            span = (following - previous).days - 1
            if span <= 0:
                continue
            missing = [
                date.fromordinal(previous.toordinal() + offset)
                for offset in range(1, span + 1)
            ]
            if self._session_predicate is not None:
                missing = [d for d in missing if self._session_predicate(d)]
            if len(missing) > self._gap_tolerance_days:
                raise GapError(
                    f"{security_id!r}: {len(missing)} session day(s) missing "
                    f"between {previous.isoformat()} and {following.isoformat()} "
                    f"(declared tolerance {self._gap_tolerance_days}); first "
                    f"missing: {[d.isoformat() for d in missing[:5]]}"
                )
