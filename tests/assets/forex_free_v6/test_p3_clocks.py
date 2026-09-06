"""FOREX-FREE-V6 P3 clocks builder — synthetic-fixture tests ONLY.

No authority file is read by these tests: every fixture below is synthetic.
The builder module is loaded by path; its real-input fail-closed checks run
when the builder itself is executed against the tree (see the build log),
never here.

Covers (dispatch scope):
1. DST boundary check on a tiny synthetic CA calendar (one EST date, one EDT date).
2. boundary_shift flag correctness for a synthetic 17:30-local row.
3. Determinism: build twice -> identical bytes.
4. S0-window edge clamping: a clock outside the window is excluded.
"""

import importlib.util
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = (
    REPO_ROOT / "research" / "control" / "forex_free_v6_run" / "p3_clocks_v6_builder.py"
)

_spec = importlib.util.spec_from_file_location("p3_clocks_v6_builder", BUILDER_PATH)
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)


def synth_ca_row(release_date: str, true_utc: str, sha: str,
                 local: str = "America/Toronto 08:30", nonstandard: bool = False):
    return {
        "release_date": release_date,
        "release_time_utc_display": [true_utc[:16]],
        "cpi_products": ["18100001"],
        "archive_path": f"cpi_calendar_archives/CA/wds/wds_changed_{release_date}.json",
        "archive_sha256": sha,
        "class": "EVIDENCED",
        "release_time_utc_true": true_utc,
        "release_time_local": local,
        "tz_conversion": "synthetic fixture",
        "nonstandard_wds_release_time": nonstandard,
    }


# ------------------------------------------------------- 1. DST boundary


def test_ny_decision_boundary_dst_instants():
    """16:00-NY is 21:00Z on EST days and 20:00Z on EDT days."""
    est = B.ny_decision_boundary_utc(date(2021, 1, 20))
    edt = B.ny_decision_boundary_utc(date(2021, 7, 21))
    assert est == datetime(2021, 1, 20, 21, 0, tzinfo=timezone.utc)
    assert edt == datetime(2021, 7, 21, 20, 0, tzinfo=timezone.utc)


def test_synthetic_ca_calendar_est_and_edt_0830_same_day():
    """Tiny synthetic CA calendar: one EST date + one EDT date, both scheduled
    08:30 local. 08:30 is before 16:00 NY in BOTH offsets -> same-day availability."""
    rows = [
        synth_ca_row("2021-01-20", "2021-01-20T13:30:00Z", "a" * 64),  # 08:30 EST
        synth_ca_row("2021-07-21", "2021-07-21T12:30:00Z", "b" * 64),  # 08:30 EDT
    ]
    out, ledger, stats, flips = B.ca_rows_core(rows)
    assert stats["in_s0"] == 2
    assert stats["same_day_available"] == 2
    assert stats["boundary_shifted"] == 0
    assert flips == set()
    assert ledger == []
    assert [r["available_for_daily_decision_date"] for r in out] == ["2021-01-20", "2021-07-21"]


def test_synthetic_row_exactly_on_boundary_is_same_day():
    """A print stamped exactly AT the 16:00-NY instant is available (<= semantics,
    identical to the P0b proof's boundary-side comparison)."""
    rows = [synth_ca_row("2021-07-21", "2021-07-21T20:00:00Z", "c" * 64)]
    out, ledger, stats, flips = B.ca_rows_core(rows)
    assert stats["same_day_available"] == 1 and flips == set() and ledger == []
    assert out[0]["available_for_daily_decision_date"] == "2021-07-21"


# ------------------------------------- 2. boundary_shift on 17:30-local row


def test_synthetic_1730_local_row_flags_boundary_shift():
    """17:30 EDT local = 21:30Z TRUE UTC, after the 20:00Z boundary -> the print
    is NOT conditionable at the release-date decision instant; it becomes
    conditionable at the NEXT decision instant (next trading day)."""
    rows = [synth_ca_row(
        "2021-07-23", "2021-07-23T21:30:00Z", "d" * 64,
        local="America/Toronto 17:30", nonstandard=True,
    )]
    out, ledger, stats, flips = B.ca_rows_core(rows)
    assert stats["boundary_shifted"] == 1 and flips == {"2021-07-23"}
    assert len(ledger) == 1
    led = ledger[0]
    assert led["decision_date"] == "2021-07-23"
    assert led["before_v2"]["stamp_utc"] == "2021-07-23T21:30:00Z"
    assert led["after_v3"]["stamp_utc"] == "2021-07-23T21:30:00Z"
    # Friday 2021-07-23 -> next weekday is Monday 2021-07-26 (FX 24/5, no holiday calendar).
    assert led["affected_decision_dates"]["available_for_daily_decision_date"] == "2021-07-26"
    assert out[0]["available_for_daily_decision_date"] == "2021-07-26"
    assert out[0]["decision_date"] == "2021-07-23"  # anchor stays the release date
    assert led["nonstandard_wds_release_time"] is True


def test_next_weekday_fx_24_5_convention():
    assert B.next_weekday(date(2021, 7, 23)) == date(2021, 7, 26)  # Fri -> Mon
    assert B.next_weekday(date(2021, 7, 24)) == date(2021, 7, 26)  # Sat -> Mon
    assert B.next_weekday(date(2021, 7, 25)) == date(2021, 7, 26)  # Sun -> Mon
    assert B.next_weekday(date(2021, 7, 26)) == date(2021, 7, 27)  # Mon -> Tue


# ------------------------------------------------------------ 3. determinism


def _synthetic_doc_once():
    """Rebuilds an identical synthetic document from scratch (pure function)."""
    return {
        "schema": B.SCHEMA_CLOCKS,
        "measured_at_utc": "2026-09-06T00:00:00Z",
        "producer": B.PRODUCER,
        "rule": B.V5_RULE_VERBATIM,
        "S0_window": {"start": B.S0_START, "end": B.S0_END, "frozen": True},
        "clocks": [
            synth_ca_row("2021-07-23", "2021-07-23T22:56:00Z", "e" * 64,
                         local="America/Toronto 18:56", nonstandard=True),
        ],
        "total": 1,
    }


def test_dump_json_bytes_deterministic_build_twice_identical():
    """Build the same synthetic document twice -> byte-identical output;
    dump carries no wall-clock or iteration-order dependence."""
    first = B.dump_json_bytes(_synthetic_doc_once())
    second = B.dump_json_bytes(_synthetic_doc_once())
    assert first == second
    # deepcopy/re-dump must not change bytes either.
    assert B.dump_json_bytes(deepcopy(_synthetic_doc_once())) == first
    # and the no-trailing-newline publication convention holds
    assert not first.endswith(b"\n")


def test_write_deterministic_guard_rejects_divergent_bytes(tmp_path):
    """The idempotence guard fails closed when an existing publication would
    change bytes (append-only publication)."""
    p = tmp_path / "doc.json"
    B.write_deterministic(p, b"AAA")
    B.write_deterministic(p, b"AAA")  # identical re-write is fine
    try:
        B.write_deterministic(p, b"BBB")
    except SystemExit as e:
        assert "DETERMINISM GUARD" in str(e)
    else:
        raise AssertionError("divergent re-write did not fail closed")
    assert p.read_bytes() == b"AAA"


# --------------------------------------------------- 4. S0 window clamping


def test_s0_window_edge_clamping_excludes_outside_clocks():
    """Window is inclusive of both edges [2018-04-04, 2025-07-24]; anything
    outside is excluded and counted as dropped."""
    rows = [
        synth_ca_row("2018-04-03", "2018-04-03T18:30:00Z", "f" * 64),  # before start
        synth_ca_row("2018-04-04", "2018-04-04T18:30:00Z", "0" * 64),  # == start (in)
        synth_ca_row("2025-07-24", "2025-07-24T18:30:00Z", "1" * 64),  # == end (in)
        synth_ca_row("2025-07-25", "2025-07-25T18:30:00Z", "2" * 64),  # after end
    ]
    out, ledger, stats, flips = B.ca_rows_core(rows)
    assert stats["in_s0"] == 2
    assert stats["dropped_out_of_window"] == 2
    assert [r["decision_date"] for r in out] == ["2018-04-04", "2025-07-24"]


def test_next_trading_day_outside_window_asserts():
    """A boundary-shifted clock whose next trading day would fall outside the
    (parametrized) window must fail closed, never publish an out-of-window
    conditioning date."""
    rows = [synth_ca_row(
        "2025-07-24", "2025-07-24T21:30:00Z", "3" * 64,
        local="America/Toronto 17:30", nonstandard=True,
    )]  # Fri; next weekday 2025-07-25 > window end
    try:
        B.ca_rows_core(rows)
    except AssertionError as e:
        assert "outside frozen S0 window" in str(e)
    else:
        raise AssertionError("out-of-window next trading day did not fail closed")


def test_non_utc_v3_stamp_rejected():
    """P-1: a stamp that is not UTC-qualified can never enter the publication."""
    bad = synth_ca_row("2021-07-21", "2021-07-21T08:30:00", "4" * 64)
    bad["release_time_utc_true"] = "2021-07-21T08:30:00"  # no Z
    try:
        B.ca_rows_core([bad])
    except AssertionError as e:
        assert "not UTC-qualified" in str(e)
    else:
        raise AssertionError("non-UTC stamp did not fail closed")
