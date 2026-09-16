"""FOREX-NG7 P0 golden tests (plan plans/PLAN_forex_ng7.md §4 F1-F7).

Golden coverage:
  - staging verification vs A2 member pins (match + fail-closed tamper)
  - OHLC integrity census detection
  - F3 clock + execution contract fixture (16:00-NY daily decision,
    entry t+1 first bookable price, exit knowable at t close executes
    t+1; no same-bar fill; fail-closed at series edge)
  - F5 anchor-state trigger-count fixtures on small synthetic series
    (fresh 20-bar close extreme + opposite 5-bar CLV-pressure slope,
    warmup 60; counts only)
  - folds.json exact first-session boundaries recomputed from the staged
    intersection calendar
  - re-pull contract ordering proof (frozen sha == committed file)
  - calendar census no-forward-fill invariant
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

P0_DIR = (
    Path(__file__).resolve().parents[1]
    / "research" / "control" / "forex_ng7_run" / "p0"
)
sys.path.insert(0, str(P0_DIR))

import p0_census_run as p0  # noqa: E402


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def make_rows(closes_with_clv, start: str = "2026-01-05"):
    """Build oldest-first TD-style rows. closes_with_clv: list of
    (close, clv) where clv in {+1, 0, -1} controls the H/L geometry:
    CLV=+1 -> H=C (a=0), L=C-1; CLV=-1 -> L=C, H=C+1; CLV=0 -> symmetric."""
    d = dt.date.fromisoformat(start)
    rows = []
    for close, clv_target in closes_with_clv:
        while d.weekday() >= 5:
            d += dt.timedelta(days=1)
        if clv_target == 1:
            high, low = f"{close:.5f}", f"{close - 1:.5f}"
        elif clv_target == -1:
            high, low = f"{close + 1:.5f}", f"{close:.5f}"
        else:
            high, low = f"{close + 0.5:.5f}", f"{close - 0.5:.5f}"
        rows.append(
            {
                "datetime": d.isoformat(),
                "open": f"{close:.5f}",
                "high": high,
                "low": low,
                "close": f"{close:.5f}",
            }
        )
        d += dt.timedelta(days=1)
    return rows


def flat(n, price=1.2000):
    return [(price, 0)] * n


def td_payload(rows):
    return {
        "meta": {"symbol": "T/T", "interval": "1day", "type": "Physical Currency"},
        "values": list(reversed(rows)),  # archived payloads are newest-first
        "status": "ok",
    }


# --------------------------------------------------------------------------
# staging verification + OHLC integrity
# --------------------------------------------------------------------------
def test_staging_verify_golden_match(tmp_path):
    rows = make_rows(flat(25))
    pins = {
        "EURUSD": {"member_sha256": None, "rows": 25,
                   "meta": {"symbol": "EUR/USD", "interval": "1day",
                            "type": "Physical Currency"},
                   "span": "x"},
    }
    path = tmp_path / "EURUSD.json"
    body = json.dumps(td_payload(rows)).encode()
    path.write_bytes(body)
    import hashlib

    pins["EURUSD"]["member_sha256"] = hashlib.sha256(body).hexdigest()
    out = p0.verify_staged_against_pins(tmp_path, pins)
    assert out["EURUSD"]["match"] is True


def test_staging_verify_fail_closed_on_tamper(tmp_path):
    rows = make_rows(flat(25))
    pins = {
        "EURUSD": {"member_sha256": "0" * 64, "rows": 25,
                   "meta": {"symbol": "EUR/USD", "interval": "1day",
                            "type": "Physical Currency"},
                   "span": "x"},
    }
    (tmp_path / "EURUSD.json").write_bytes(
        json.dumps(td_payload(rows)).encode()
    )
    with pytest.raises(p0.FailClosedError):
        p0.verify_staged_against_pins(tmp_path, pins)


def test_structural_census_records_ohlc_artifacts_verbatim():
    rows = make_rows(flat(5))
    rows[2]["high"] = "0.00001"  # high below open/close -> archived artifact
    data = {"meta": {"symbol": "EUR/USD", "interval": "1day",
                     "type": "Physical Currency"},
            "rows": rows, "dates": [dt.date.fromisoformat(r["datetime"])
                                    for r in rows]}
    pin = {"rows": 5, "meta": {"symbol": "EUR/USD", "interval": "1day",
                               "type": "Physical Currency"},
           "span": "x"}
    census = p0.structural_census("EURUSD", data, pin)
    # identity/shape are hard gates; OHLC artifacts are recorded verbatim,
    # never repaired (byte-pinned authority law)
    assert census["ohlc_integrity_violations"], "artifact must be recorded"
    assert census["ohlc_artifact_count"] == 1
    assert "fail" not in census
    assert "never repaired" in census["ohlc_artifact_disposition"]


def test_structural_census_hard_fails_on_row_count():
    rows = make_rows(flat(5))
    data = {"meta": {"symbol": "EUR/USD", "interval": "1day",
                     "type": "Physical Currency"},
            "rows": rows, "dates": [dt.date.fromisoformat(r["datetime"])
                                    for r in rows]}
    pin = {"rows": 4, "meta": {"symbol": "EUR/USD", "interval": "1day",
                               "type": "Physical Currency"},
           "span": "x"}
    census = p0.structural_census("EURUSD", data, pin)
    assert census.get("fail") is True


# --------------------------------------------------------------------------
# F3 clock + execution contract fixture (golden)
# --------------------------------------------------------------------------
def test_entry_fills_next_bar_first_bookable_price():
    rows = make_rows(
        [(1.2000, 0)] * 61 + [(1.1000, 1)]  # decision bar 60 (fresh low)
    )
    # A LONG decision on completed bar 60 must fill at bar 61's OPEN,
    # never at bar 60's close.
    fill = p0.next_bookable_price(rows, 60)
    assert fill == rows[61]["open"]
    assert fill == "1.10000"
    assert fill != rows[60]["close"]
    assert p0.decision_to_execution_index(60) == 61


def test_exit_knowable_at_t_close_executes_t_plus_1():
    rows = make_rows(flat(64))
    # Exit condition knowable at bar 40's close -> execution at bar 41 open
    assert p0.exit_execution_index(40) == 41
    assert p0.next_bookable_price(rows, 40) == rows[41]["open"]


def test_no_bookable_bar_at_series_edge_fails_closed():
    rows = make_rows(flat(3))
    with pytest.raises(p0.FailClosedError):
        p0.next_bookable_price(rows, len(rows) - 1)


# --------------------------------------------------------------------------
# F5 trigger-count fixtures (synthetic, counts only)
# --------------------------------------------------------------------------
def _descending_divergent_series():
    """flat(45) then 15 descending closes: bars 45-59 CLV=0, bars 60-64
    CLV=+1. Bars 60..64 are fresh 20-bar close LOWs with strictly positive
    5-bar pressure slope -> exactly 5 LONG firings, 0 SHORT."""
    series = flat(45)
    series += [(1.2000 - 0.001 * (i - 44), 0) for i in range(45, 60)]
    series += [(1.2000 - 0.001 * (i - 44), 1) for i in range(60, 65)]
    return series


def test_anchor_counts_engineered_long_divergence():
    rows = make_rows(_descending_divergent_series())
    firings = p0.anchor_firings(rows)
    assert [f["index"] for f in firings] == [60, 61, 62, 63, 64]
    assert all(f["direction"] == "LONG" for f in firings)
    # divergence guard: fresh low with NON-positive slope must NOT fire —
    # bars 45..59 are fresh lows with slope 0 and are correctly absent.
    assert all(f["index"] >= 60 for f in firings)


def test_anchor_counts_engineered_short_mirror():
    series = flat(45)
    series += [(1.2000 + 0.001 * (i - 44), 0) for i in range(45, 60)]
    series += [(1.2000 + 0.001 * (i - 44), -1) for i in range(60, 65)]
    rows = make_rows(series)
    firings = p0.anchor_firings(rows)
    assert [f["index"] for f in firings] == [60, 61, 62, 63, 64]
    assert all(f["direction"] == "SHORT" for f in firings)


def test_warmup_60_suppresses_pre_decision_bars():
    series = flat(30)
    series += [(1.2000 - 0.001 * (i - 29), 0) for i in range(30, 34)]
    # bar 34 strictly below bar 33: a fresh low + positive slope that WOULD
    # fire absent the warmup gate — suppressed here because 34 < warmup 60.
    series += [(1.2000 - 0.001 * (34 - 29), 1)]
    series += flat(31)
    rows = make_rows(series)
    # The divergence sits at bar 33 < warmup 60; nothing else qualifies.
    assert p0.anchor_firings(rows) == []


def test_confirming_slope_is_not_counted_anchor():
    """CONFIRMED extreme (fresh low + CONFIRMING negative slope) is the
    complement control state — the anchor census must NOT count it."""
    series = flat(45)
    series += [(1.2000 - 0.001 * (i - 44), 0) for i in range(45, 60)]
    series += [(1.2000 - 0.001 * (i - 44), -1) for i in range(60, 65)]
    rows = make_rows(series)
    # fresh lows but slope <= 0 (confirming) -> zero anchor firings
    assert p0.anchor_firings(rows) == []


# --------------------------------------------------------------------------
# committed-artifact golden checks (staged data + frozen contracts)
# --------------------------------------------------------------------------
def test_repull_contract_frozen_sha_matches_module():
    assert p0.CONTRACT_SHA256 == p0.sha256_file(p0.CONTRACT_PATH)
    contract = json.loads(p0.CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["frozen_before_pull"] is True
    assert contract["scope"]["legs"] == ["EURUSD", "NZDUSD"]
    assert contract["scope"]["bars_per_leg"] == 60


def test_folds_exact_first_session_boundaries():
    folds_doc = json.loads((P0_DIR / "folds.json").read_text(encoding="utf-8"))
    leg_data = {
        leg: p0.load_leg_payload(p0.STAGED_DIR / f"{leg}.json") for leg in p0.LEGS
    }
    intersection = sorted(
        set.intersection(*[set(d["dates"]) for d in leg_data.values()])
    )
    rebuilt = p0.build_folds(
        [dt.date.fromisoformat(x.isoformat()) for x in intersection]
    )
    assert rebuilt == folds_doc
    # exact boundaries + contiguity + chronological thirds
    fs = [folds_doc["folds"][k] for k in ("fold1", "fold2", "fold3")]
    assert fs[0]["first_session"] == intersection[0].isoformat()
    for a, b in zip(fs, fs[1:]):
        assert a["last_session"] < b["first_session"]
    assert fs[0]["sessions"] == fs[1]["sessions"]
    assert fs[2]["sessions"] >= fs[0]["sessions"]
    assert (
        fs[0]["sessions"] + fs[1]["sessions"] + fs[2]["sessions"]
        == len(intersection)
    )


def test_calendar_census_no_forward_fill():
    doc = json.loads(
        (P0_DIR / "staging_manifest.json").read_text(encoding="utf-8")
    )
    # manifest members byte-match the staged files (identity, not ffill)
    for leg, meta in doc["members"].items():
        assert p0.sha256_file(p0.STAGED_DIR / f"{leg}.json") == meta["sha256"]
        assert meta["rows"] == 5000


def test_staged_spans_and_rows_golden():
    manifest = json.loads(
        (P0_DIR / "staging_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["members"]["EURUSD"]["span"].startswith("2007-10-18")
    for leg in ("GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"):
        assert manifest["members"][leg]["span"].startswith("2007-11-16") or \
            manifest["members"][leg]["span"].startswith("2008-01-3")
    for leg in p0.LEGS:
        assert manifest["members"][leg]["rows"] == 5000


def test_census_counts_only_shape():
    doc = json.loads((P0_DIR / "census.json").read_text(encoding="utf-8"))
    for fold in doc["per_fold"].values():
        for leg in p0.LEGS:
            entry = fold["per_leg"][leg]
            assert set(entry) == {"LONG", "SHORT", "total"}
            assert entry["total"] == entry["LONG"] + entry["SHORT"]
    assert doc["totals"]["all"] == sum(
        f["total"] for f in doc["per_fold"].values()
    )


def test_repro_digest_file_exists_and_scoped():
    digest_txt = (P0_DIR / "p0_repro_digest.txt").read_text()
    lines = [ln for ln in digest_txt.splitlines() if ln.strip()]
    names = {ln.split(maxsplit=1)[1].strip() for ln in lines}
    assert names == {
        "census.json", "folds.json", "staging_manifest.json"
    }
    for ln in lines:
        digest, name = ln.split(maxsplit=1)
        assert digest == p0.sha256_file(P0_DIR / name.strip())
