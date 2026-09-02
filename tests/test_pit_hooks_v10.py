"""A6 PIT hook tests (PLAN.md section 6 H07-data).

Synthetic fixtures only — a tiny fake catalog tree (CSV files) is written
inside tmp dirs; no real catalog data is read or written here. Coverage:

* :class:`research.pit_hooks_v10.HashPinnedCatalog` — lazy one-time pin
  verification (hash computed exactly once across many reads), refusal on
  expected-merkle mismatch that stays refused, immutable completed-bar
  snapshots sorted by close stamp with strict upper/lower clipping;
* multi-file union reads through the real-layout default reader
  (``data/binance_bar/<SYM>-PERP.../``) including duplicate-close-stamp
  detection;
* :func:`research.pit_hooks_v10.pit_join` — decision time =
  bar_close + lag; selects the LATEST info published at/before the decision
  time; pre-publication bars keep None info; boundary case: info published
  exactly at the decision time IS usable; negative lag refused;
* :func:`research.pit_hooks_v10.assert_no_lookahead` — hand-built leaky
  join raises :class:`LookaheadError`; the correctly-lagged join passes;
* determinism — :func:`research.pit_hooks_v10.canonical_repr` yields
  byte-identical output for equal inputs regardless of dict insertion
  order, and rejects non-finite floats.
"""

from __future__ import annotations

import csv
import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import research.pit_hooks_v10 as pit_hooks
from research.data_audit_v10 import INTERVAL_NS, catalog_hash

BASE_NS = int(
    datetime(2025, 8, 21, tzinfo=timezone.utc).timestamp()
) * 1_000_000_000


def grid_stamps(count: int, start_ns: int = BASE_NS,
                step_ns: int = INTERVAL_NS) -> list[int]:
    return [start_ns + i * step_ns for i in range(count)]


def bar_row(ts_close: int, px: float = 100.0) -> dict:
    return {
        "ts_event_ns": ts_close,
        "ts_open_ns": ts_close - INTERVAL_NS,
        "open": px,
        "high": px + 1,
        "low": px - 1,
        "close": px,
        "volume": 3.0,
    }


def write_bar_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture()
def catalog_tree(tmp_path):
    """Fake tree: two CSV parts under the real Nautilus-style directory."""
    stamps = grid_stamps(8)
    part_dir = (
        tmp_path / "data" / "binance_bar"
        / "XYZ-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )
    part_dir.mkdir(parents=True)
    write_bar_csv(part_dir / "part1.csv", [bar_row(t) for t in stamps[:5]])
    write_bar_csv(part_dir / "part2.csv", [bar_row(t) for t in stamps[5:]])
    return tmp_path, stamps


def pinned_catalog(root, expected=None):
    return pit_hooks.HashPinnedCatalog(
        root, expected_merkle=expected, reader=pit_hooks.nautilus_catalog_reader
    )


# --------------------------------------------------------------------------- #
# HashPinnedCatalog pinning + laziness
# --------------------------------------------------------------------------- #
def test_pin_verified_once_lazily_and_reads_work(catalog_tree, monkeypatch):
    root, stamps = catalog_tree
    calls = {"n": 0}
    real = pit_hooks.catalog_hash

    def counting(arg):
        calls["n"] += 1
        return real(arg)

    monkeypatch.setattr(pit_hooks, "catalog_hash", counting)
    merkle = real(root)["merkle_root_hex"]

    cat = pinned_catalog(root, expected=merkle)
    assert not cat.verified                      # lazy: nothing hashed yet
    assert calls["n"] == 0

    bars = cat.read_bars("XYZ", BASE_NS, BASE_NS + 8 * INTERVAL_NS)
    assert calls["n"] == 1                       # verified exactly once
    assert len(bars) == 8

    _ = cat.read_bars("XYZ", BASE_NS, BASE_NS + INTERVAL_NS)
    _ = cat.merkle_root_hex
    assert calls["n"] == 1                       # never re-hashed
    assert cat.hash_report["file_count"] == 2


def test_pin_mismatch_refused_fail_closed_and_stays_refused(catalog_tree):
    root, _stamps = catalog_tree
    cat = pinned_catalog(root, expected="f" * 64)
    with pytest.raises(pit_hooks.CatalogHashMismatch):
        cat.read_bars("XYZ", BASE_NS, BASE_NS + INTERVAL_NS)
    with pytest.raises(pit_hooks.CatalogHashMismatch):   # still refused
        cat.read_bars("XYZ", BASE_NS, BASE_NS + INTERVAL_NS)
    assert not cat.verified
    with pytest.raises(pit_hooks.CatalogNotVerified):
        _ = cat.merkle_root_hex


# --------------------------------------------------------------------------- #
# read_bars completed-bar semantics + immutability
# --------------------------------------------------------------------------- #
def test_read_bars_clips_completed_bars_and_sorts(catalog_tree):
    root, stamps = catalog_tree
    cat = pinned_catalog(root, expected=catalog_hash(root)["merkle_root_hex"])

    # End mid-bar: a bar closing after `end` must be dropped even though its
    # open precedes the end (strict completed-bar semantics).
    end = stamps[4] + INTERVAL_NS // 2
    bars = cat.read_bars("XYZ", BASE_NS, end)
    assert isinstance(bars, tuple)
    assert [b.ts_event_ns for b in bars] == stamps[:5]
    assert all(b.ts_event_ns <= end for b in bars)

    lower = cat.read_bars("XYZ", stamps[6], stamps[-1])
    assert [b.ts_event_ns for b in lower] == stamps[6:]

    first = bars[0]
    assert first.symbol == "XYZ"
    assert first.ts_open_ns == first.ts_event_ns - INTERVAL_NS
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.close = 42.0                        # immutable snapshot


def test_read_bars_rejects_duplicate_close_stamps(tmp_path):
    stamps = grid_stamps(3)
    bar_dir = tmp_path / "data" / "binance_bar" / "DUP-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    write_bar_csv(bar_dir / "a.csv", [bar_row(t) for t in stamps])
    write_bar_csv(bar_dir / "b.csv", [bar_row(stamps[1], px=101.0)])  # dup close
    cat = pit_hooks.HashPinnedCatalog(tmp_path,
                                      reader=pit_hooks.nautilus_catalog_reader)
    with pytest.raises(pit_hooks.DataIntegrityError, match="duplicate close stamp"):
        cat.read_bars("DUP", BASE_NS, stamps[-1])


# --------------------------------------------------------------------------- #
# pit_join / assert_no_lookahead
# --------------------------------------------------------------------------- #
def make_bars(stamps):
    return tuple(
        pit_hooks.BarSnapshot("XYZ", ts, ts - INTERVAL_NS, 1.0, 2.0, 0.5, 1.5, 9.0)
        for ts in stamps
    )


def test_pit_join_selects_latest_info_at_or_before_decision_time(catalog_tree):
    _root, stamps = catalog_tree
    info = [
        (stamps[0] + INTERVAL_NS, 0.01),           # decision time of bar 0 (lag=1)
        (stamps[1] + INTERVAL_NS, 0.02),           # decision time of bars 1-2
        (stamps[3] + INTERVAL_NS, 0.03),           # decision time of bar 3 only
    ]
    rows = pit_hooks.pit_join(make_bars(stamps[:4]), info, info_lag_bars=1)
    assert [r.info_publish_ts_ns for r in rows] == [
        info[0][0], info[1][0], info[1][0], info[2][0],
    ]
    assert [r.info_value for r in rows] == [0.01, 0.02, 0.02, 0.03]
    assert all(r.decision_time_ns == r.ts_event_ns + INTERVAL_NS for r in rows)
    pit_hooks.assert_no_lookahead(rows)            # must not raise


def test_pit_join_pre_publication_none_and_boundary_inclusive():
    bars = make_bars(grid_stamps(3))
    publish_at = bars[1].ts_event_ns               # lag=0 => decision == close
    rows = pit_hooks.pit_join(bars, [(publish_at, 7.0)], info_lag_bars=0)
    assert rows[0].info_value is None and rows[0].info_publish_ts_ns is None
    assert rows[1].info_publish_ts_ns == publish_at               # inclusive
    assert rows[2].info_value == 7.0                              # carried forward
    pit_hooks.assert_no_lookahead(rows)


def test_pit_join_accepts_mappings_pairs_and_refuses_negative_lag():
    bars = make_bars(grid_stamps(1))
    mapped = pit_hooks.pit_join(
        bars,
        [{"publish_ts_ns": BASE_NS, "value": 0.5, "kind": "funding"}],
        info_lag_bars=0,
    )
    pairs = pit_hooks.pit_join(bars, [(BASE_NS - 5, 0.25)], info_lag_bars=0)
    assert mapped[0].info_kind == "funding" and mapped[0].info_value == 0.5
    assert pairs[0].info_value == 0.25
    with pytest.raises(ValueError):
        pit_hooks.pit_join(bars, [(BASE_NS, 1.0)], info_lag_bars=-1)


def test_assert_no_lookahead_raises_on_leaky_join():
    ts = BASE_NS
    leaky = (
        pit_hooks.JoinedRow(
            symbol="S", ts_event_ns=ts, decision_time_ns=ts,
            close=1.0, info_publish_ts_ns=ts + INTERVAL_NS,
            info_value=0.9, info_kind="oi", info_lag_bars=0,
        ),
    )
    with pytest.raises(pit_hooks.LookaheadError, match="lookahead"):
        pit_hooks.assert_no_lookahead(leaky)


def test_normalize_info_series_rejects_duplicate_publications():
    with pytest.raises(pit_hooks.DataIntegrityError):
        pit_hooks.normalize_info_series([(100, 1.0), (100, 2.0)])


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_canonical_repr_deterministic_byte_identical():
    row = pit_hooks.BarSnapshot("X", 5, 4, 1.0, 2.0, 0.5, 1.5, 9.0)
    j1 = pit_hooks.pit_join((row,), [(4, 0.5)], info_lag_bars=0)[0]
    j2 = pit_hooks.pit_join((row,), [(4, 0.5)], info_lag_bars=0)[0]
    assert pit_hooks.canonical_repr(j1).encode() == pit_hooks.canonical_repr(j2).encode()

    d1 = {"b": 1, "a": {"y": 2, "x": 3}}
    d2 = {"a": {"x": 3, "y": 2}, "b": 1}
    assert pit_hooks.canonical_repr(d1) == pit_hooks.canonical_repr(d2)

    payload = pit_hooks.canonical_repr(j1)
    assert json.loads(payload)["ts_event_ns"] == 5

    with pytest.raises(ValueError):
        pit_hooks.canonical_repr({"inf": float("inf")})
