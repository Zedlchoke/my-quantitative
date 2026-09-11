"""Query plane: deterministic read-only DuckDB over explicit manifests.

Implements the frozen V3 query-plane contract (plan section 5).  The plane:

1. accepts only an explicit ordered manifest-ID list (duplicates rejected);
2. verifies every named manifest entry's bytes against the entry's pinned
   sha256 *before* DuckDB sees it (MDP verification semantics);
3. maps manifest IDs to exact local files -- no glob discovery;
4. rejects URLs, direct file literals in SQL, extension install/load and
   auto-discovery readers;
5. opens derived databases read-only wherever supported;
6. uses bound parameters for values;
7. canonicalizes and hashes SQL plus parameters into a query identity;
8. enforces an output schema and a frozen deterministic order;
9. records row count, null census, min/max clock and a result digest;
10. returns NOT_EVALUABLE verdicts on missing/drifted evidence -- never an
    empty-success substitution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

import duckdb

from .canonical import canonical_digest, sha256_bytes, sha256_file

SCHEMA_VERSION = "v3_query_plane@1"

_ABS_PATH_LITERAL_RE = re.compile(r"'\s*/[^']*'")

#: SQL tokens forbidden inside the frozen query surface (lowercase).
FORBIDDEN_SQL = (
    "read_csv_auto", "read_json_auto", "read_text", "read_blob",
    "glob(", "http://", "https://", "s3://", "gs://", "azure://",
    "install ", "load ", "attach ", "pragma ", "copy ", "export ",
)

#: Direct file literals in SQL are rejected: verified views are the only
#: file surface, so a frozen query can never smuggle an unnamed file in.
FORBIDDEN_FILE_LITERALS = (".csv", ".parquet", ".json", ".duckdb", ".jsonl")

ORDER_BY_RE = re.compile(r"\border\s+by\b", re.IGNORECASE)

#: Canonical type-name aliases (contract names -> duckdb full names).
TYPE_ALIASES = {
    "TIMESTAMPTZ": "TIMESTAMP WITH TIME ZONE",
}


def _canonical_type(name: str) -> str:
    upper = (name or "").upper()
    return TYPE_ALIASES.get(upper, upper)


class QueryPlaneError(Exception):
    """Base class: the plane never substitutes an empty success."""


class ForbiddenSQL(QueryPlaneError):
    pass


class DuplicateManifestID(QueryPlaneError):
    pass


class PathEscape(QueryPlaneError):
    pass


@dataclass(frozen=True)
class ManifestEntry:
    """One explicitly named input file, pinned by content hash."""

    manifest_id: str
    path: str
    sha256: str


@dataclass(frozen=True)
class OutputColumn:
    name: str
    duckdb_type: str


@dataclass(frozen=True)
class FrozenQuery:
    """A query frozen at contract time: text + order + output schema."""

    name: str
    sql: str
    order_columns: Sequence[str]
    output_schema: Sequence[OutputColumn]
    clock_column: str | None = None


@dataclass
class QueryResult:
    verdict: str                      # SUCCESS | NOT_EVALUABLE
    reason: str | None
    identity: str | None = None
    rows: list[tuple] = field(default_factory=list)
    row_count: int = 0
    null_census: dict[str, int] = field(default_factory=dict)
    clock_min: str | None = None
    clock_max: str | None = None
    result_digest: str | None = None
    input_manifest_ids: list[str] = field(default_factory=list)


def _reject_forbidden_sql(sql: str) -> None:
    lowered = sql.lower()
    for token in FORBIDDEN_SQL:
        if token in lowered:
            raise ForbiddenSQL(f"forbidden SQL token: {token!r}")
    for literal in FORBIDDEN_FILE_LITERALS:
        if literal in lowered:
            raise ForbiddenSQL(
                f"direct file literal forbidden in SQL: {literal!r} "
                "(verified views are the only file surface)"
            )
    if _ABS_PATH_LITERAL_RE.search(sql):
        raise ForbiddenSQL(
            "absolute-path literal forbidden in SQL (verified views are "
            "the only file surface)"
        )


def _enforce_frozen_order(sql: str, order_columns: Sequence[str]) -> None:
    match = ORDER_BY_RE.search(sql)
    if not match:
        raise QueryPlaneError("query has no frozen order (missing ORDER BY)")
    tail = sql[match.end():].split("limit")[0].lower()
    for col in order_columns:
        if col.lower() not in tail:
            raise QueryPlaneError(
                f"frozen order column {col!r} not in ORDER BY clause"
            )


def _check_path(entry: ManifestEntry) -> str:
    path = entry.path
    if not path.startswith("/"):
        raise PathEscape(f"manifest path not absolute: {path!r}")
    if ".." in path.split("/"):
        raise PathEscape(f"manifest path escapes: {path!r}")
    return path


def _clock_utc(value: Any) -> str:
    """Canonicalize a clock value to UTC ISO-8601 (host-tz independent)."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


class QueryPlane:
    """Frozen-surface DuckDB runner.  Derived DBs are opened read-only."""

    def __init__(self, entries: Mapping[str, ManifestEntry],
                 derived_db_path: str | None = None):
        self._entries = dict(entries)
        self._derived_db_path = derived_db_path
        self.con = self._connect()

    def _connect(self) -> "duckdb.DuckDBPyConnection":
        if self._derived_db_path:
            con = duckdb.connect(self._derived_db_path, read_only=True)
        else:
            con = duckdb.connect(":memory:")
        con.execute("SET autoinstall_known_extensions=false")
        con.execute("SET autoload_known_extensions=false")
        return con

    # ------------------------------------------------------------------ #
    def register_views(self, view_name_by_manifest_id: Mapping[str, str]
                       ) -> None:
        """Register verified inputs as views (exact bytes only).

        CSV inputs go through read_csv with explicit header=true; parquet
        inputs are referenced directly.  Bytes are re-verified here before
        the view exists.
        """
        for mid, view in view_name_by_manifest_id.items():
            entry = self._entries[mid]
            path = _check_path(entry)
            digest = sha256_file(path)
            if digest != entry.sha256:
                raise QueryPlaneError(
                    f"MANIFEST_HASH_DRIFT: {mid} expected {entry.sha256}, "
                    f"got {digest}"
                )
            if path.endswith(".csv"):
                self.con.execute(
                    f"CREATE VIEW {view} AS SELECT * FROM read_csv("
                    f"'{path}', header=true)"
                )
            else:
                self.con.execute(
                    f"CREATE VIEW {view} AS SELECT * FROM '{path}'"
                )

    def run(self, frozen: FrozenQuery,
            manifest_ids: Sequence[str],
            params: Sequence[Any] = ()) -> QueryResult:
        ids = list(manifest_ids)
        if len(ids) != len(set(ids)):
            raise DuplicateManifestID("duplicate input manifest IDs")
        for mid in ids:
            if mid not in self._entries:
                return QueryResult(
                    verdict="NOT_EVALUABLE",
                    reason=f"manifest absent: {mid}",
                    input_manifest_ids=ids,
                )

        _reject_forbidden_sql(frozen.sql)
        _enforce_frozen_order(frozen.sql, frozen.order_columns)

        # verify input bytes BEFORE DuckDB sees them
        for mid in ids:
            entry = self._entries[mid]
            path = _check_path(entry)
            digest = sha256_file(path)
            if digest != entry.sha256:
                return QueryResult(
                    verdict="NOT_EVALUABLE",
                    reason=f"MANIFEST_HASH_DRIFT: {mid}",
                    identity=self.identity(frozen, ids, params),
                    input_manifest_ids=ids,
                )

        identity = self.identity(frozen, ids, params)
        try:
            cur = self.con.execute(frozen.sql, list(params))
            description = cur.description
            rows = cur.fetchall()
        except duckdb.Error as exc:  # malformed db / cache surfaces here
            return QueryResult(
                verdict="NOT_EVALUABLE", reason=f"duckdb error: {exc!r}",
                identity=identity, input_manifest_ids=ids,
            )

        # output schema enforcement (names + types, exact)
        got = [(d[0], _canonical_type(str(d[1]))) for d in description]
        want = [(c.name, _canonical_type(c.duckdb_type))
                for c in frozen.output_schema]
        if len(got) != len(want):
            return QueryResult(
                verdict="NOT_EVALUABLE",
                reason=f"output schema arity {len(got)} != frozen {len(want)}",
                identity=identity, input_manifest_ids=ids,
            )
        for (gname, gtype), (wname, wtype) in zip(got, want):
            if gname != wname or gtype != wtype:
                return QueryResult(
                    verdict="NOT_EVALUABLE",
                    reason=(f"output schema drift: got {(gname, gtype)} "
                            f"want {(wname, wtype)}"),
                    identity=identity, input_manifest_ids=ids,
                )

        names = [w[0] for w in want]
        null_census = {
            names[i]: sum(1 for r in rows if r[i] is None)
            for i in range(len(names))
        }
        clock_min = clock_max = None
        if frozen.clock_column is not None:
            idx = names.index(frozen.clock_column)
            present = [r[idx] for r in rows if r[idx] is not None]
            canonical = [_clock_utc(v) for v in present]
            clock_min = min(canonical) if canonical else None
            clock_max = max(canonical) if canonical else None

        return QueryResult(
            verdict="SUCCESS",
            reason=None,
            identity=identity,
            rows=rows,
            row_count=len(rows),
            null_census=null_census,
            clock_min=clock_min,
            clock_max=clock_max,
            result_digest=sha256_bytes(repr(rows).encode("utf-8")),
            input_manifest_ids=ids,
        )

    # ------------------------------------------------------------------ #
    def identity(self, frozen: FrozenQuery, manifest_ids: Sequence[str],
                 params: Sequence[Any]) -> str:
        return canonical_digest({
            "schema_version": SCHEMA_VERSION,
            "duckdb_version": duckdb.__version__,
            "frozen_query_name": frozen.name,
            "sql_canonical": " ".join(frozen.sql.split()),
            "params_digest": canonical_digest(list(params)),
            "ordered_manifest_ids": list(manifest_ids),
        })

    def close(self) -> None:
        self.con.close()
