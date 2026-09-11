"""V3 query-plane contract tests (plan section 5 mandatory negatives)."""

import os

import pytest

from research.platform_v3.query_plane import (
    DuplicateManifestID,
    ForbiddenSQL,
    FrozenQuery,
    ManifestEntry,
    OutputColumn,
    PathEscape,
    QueryPlane,
    QueryPlaneError,
)

CSV_A = "mid,ts,val\n1,2026-01-01T00:00:00Z,10\n2,2026-01-02T00:00:00Z,20\n"
CSV_A_DRIFT = "mid,ts,val\n1,2026-01-01T00:00:00Z,99\n"


def _sha(b: bytes):
    import hashlib
    return hashlib.sha256(b).hexdigest()


def _make_plane(tmp_path, csv_bytes: bytes = CSV_A.encode()):
    p = tmp_path / "a.csv"
    p.write_bytes(csv_bytes)
    entries = {
        "m:1": ManifestEntry(manifest_id="m:1", path=str(p),
                             sha256=_sha(csv_bytes)),
    }
    plane = QueryPlane(entries)
    plane.register_views({"m:1": "v_a"})
    return plane, entries, str(p)


FROZEN = FrozenQuery(
    name="q_sum",
    sql="SELECT mid, ts, val FROM v_a ORDER BY mid",
    order_columns=["mid"],
    output_schema=[OutputColumn("mid", "BIGINT"),
                   OutputColumn("ts", "TIMESTAMPTZ"),
                   OutputColumn("val", "BIGINT")],
    clock_column="ts",
)


def test_happy_path_deterministic(tmp_path):
    plane, _, _ = _make_plane(tmp_path)
    r = plane.run(FROZEN, ["m:1"])
    assert r.verdict == "SUCCESS"
    assert r.row_count == 2
    assert [r0[0] for r0 in r.rows] == [1, 2]
    assert [r0[2] for r0 in r.rows] == [10, 20]
    from datetime import datetime, timezone
    assert all(isinstance(r0[1], datetime) for r0 in r.rows)
    assert r.null_census == {"mid": 0, "ts": 0, "val": 0}
    assert r.clock_min == "2026-01-01T00:00:00+00:00"
    digest1 = r.result_digest
    r2 = plane.run(FROZEN, ["m:1"])
    assert r2.result_digest == digest1
    plane.close()


def test_manifest_absent_is_not_evaluable(tmp_path):
    plane, _, _ = _make_plane(tmp_path)
    r = plane.run(FROZEN, ["m:missing"])
    assert r.verdict == "NOT_EVALUABLE"
    assert "manifest absent" in r.reason
    assert r.rows == []  # never an empty-success substitution
    plane.close()


def test_hash_drift_is_not_evaluable(tmp_path):
    plane, entries, path = _make_plane(tmp_path)
    # mutate the file after view registration -> drift
    path_obj = tmp_path / "a.csv"
    path_obj.write_bytes(CSV_A_DRIFT.encode())
    r = plane.run(FROZEN, ["m:1"])
    assert r.verdict == "NOT_EVALUABLE"
    assert "MANIFEST_HASH_DRIFT" in r.reason
    plane.close()


def test_duplicate_manifest_ids_rejected(tmp_path):
    plane, _, _ = _make_plane(tmp_path)
    with pytest.raises(DuplicateManifestID):
        plane.run(FROZEN, ["m:1", "m:1"])
    plane.close()


def test_path_escape_rejected(tmp_path):
    entries = {"m:1": ManifestEntry(
        "m:1", str(tmp_path / ".." / "a.csv"), "0" * 64)}
    plane = QueryPlane(entries)
    with pytest.raises(QueryPlaneError):
        plane.run(FROZEN, ["m:1"])
    plane.close()


@pytest.mark.parametrize("sql", [
    "SELECT * FROM read_csv_auto('/x.csv') ORDER BY 1",
    "SELECT * FROM 'https://evil.example/x.parquet' ORDER BY 1",
    "INSTALL httpfs; LOAD httpfs;",
    "ATTACH '/tmp/x.duckdb' ASxdb",
    "SELECT * FROM v_a, '/etc/passwd' ORDER BY 1",
])
def test_forbidden_sql_rejected(tmp_path, sql):
    plane, _, _ = _make_plane(tmp_path)
    frozen = FrozenQuery("bad", sql, ["1"],
                         [OutputColumn("x", "VARCHAR")])
    with pytest.raises(ForbiddenSQL):
        plane.run(frozen, ["m:1"])
    plane.close()


def test_unordered_query_rejected(tmp_path):
    plane, _, _ = _make_plane(tmp_path)
    frozen = FrozenQuery(
        "unordered", "SELECT mid, ts, val FROM v_a",
        ["mid"],
        [OutputColumn("mid", "BIGINT"), OutputColumn("ts", "TIMESTAMPTZ"),
         OutputColumn("val", "BIGINT")],
    )
    with pytest.raises(QueryPlaneError):
        plane.run(frozen, ["m:1"])
    plane.close()


def test_row_order_drift_changes_digest(tmp_path):
    plane, _, _ = _make_plane(tmp_path)
    r_asc = plane.run(FROZEN, ["m:1"])
    frozen_desc = FrozenQuery(
        "q_sum_desc", "SELECT mid, ts, val FROM v_a ORDER BY mid DESC",
        ["mid"],
        FROZEN.output_schema, clock_column="ts")
    r_desc = plane.run(frozen_desc, ["m:1"])
    assert r_asc.result_digest != r_desc.result_digest
    plane.close()


def test_output_schema_drift_rejected(tmp_path):
    plane, _, _ = _make_plane(tmp_path)
    frozen = FrozenQuery(
        "q_bad", "SELECT mid, ts FROM v_a ORDER BY mid", ["mid"],
        [OutputColumn("mid", "BIGINT"), OutputColumn("ts", "TIMESTAMPTZ"),
         OutputColumn("val", "BIGINT")],
    )
    r = plane.run(frozen, ["m:1"])
    assert r.verdict == "NOT_EVALUABLE"
    assert "arity" in r.reason
    plane.close()


def test_decimal_not_coerced_to_float(tmp_path):
    csv = "mid,amt\n1,0.1000000001\n"
    p = tmp_path / "d.csv"
    p.write_text(csv)
    entries = {"m:d": ManifestEntry("m:d", str(p), _sha(csv.encode()))}
    plane = QueryPlane(entries)
    plane.register_views({"m:d": "v_d"})
    frozen = FrozenQuery(
        "q_dec",
        "SELECT mid, CAST(amt AS DECIMAL(38,10)) AS amt FROM v_d "
        "ORDER BY mid",
        ["mid"],
        [OutputColumn("mid", "BIGINT"),
         OutputColumn("amt", "DECIMAL(38,10)")],
    )
    r = plane.run(frozen, ["m:d"])
    assert r.verdict == "SUCCESS", r.reason
    from decimal import Decimal
    assert isinstance(r.rows[0][1], Decimal)
    assert r.rows[0][1] == Decimal("0.1000000001")
    plane.close()


def test_newer_file_not_named_is_invisible(tmp_path):
    plane, _, _ = _make_plane(tmp_path)
    (tmp_path / "newer.csv").write_text("mid,ts,val\n9,x,9\n")
    r = plane.run(FROZEN, ["m:1"])
    assert r.verdict == "SUCCESS"
    assert r.row_count == 2  # the unnamed newer file never appears
    plane.close()


def test_query_identity_changes_with_any_input(tmp_path):
    plane, _, _ = _make_plane(tmp_path)
    r1 = plane.run(FROZEN, ["m:1"])
    r2 = plane.run(FROZEN, ["m:1"], params=[])
    assert r1.identity == r2.identity
    frozen2 = FrozenQuery(
        "q_sum_v2", "SELECT mid, ts, val FROM v_a ORDER BY mid",
        ["mid"], FROZEN.output_schema, clock_column="ts")
    r3 = plane.run(frozen2, ["m:1"])
    assert r3.identity != r1.identity  # query text change -> new identity
    plane.close()
