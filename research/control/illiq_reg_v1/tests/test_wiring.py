"""M0 tests — wiring law (plan SS9/SS11): per-fold funding scan, +3d load end,
4-label invariant, and the live B2 coverage proof on the real staged scans
(READ-ONLY absolute paths; the checks read only the small funding.json files).
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

import wiring  # noqa: E402


# --- fold wiring map (B2 regression pin) ---------------------------------------

def test_s0r_must_wire_scan_2026_a():
    # The B2 incident: S0R wired to scan_2026 (coverage ends 2024-08-20).
    assert wiring.scan_id_for_fold("S0R") == wiring.SCAN_S0R_FWD
    assert wiring.scan_id_for_fold("FWD") == wiring.SCAN_S0R_FWD
    assert wiring.scan_id_for_fold("Y2021") == wiring.SCAN_PREWINDOW
    assert wiring.scan_id_for_fold("Y2024P") == wiring.SCAN_PREWINDOW


def test_fwd_catalog_unpinned_is_fail_closed():
    assert wiring.FOLD_WIRING["FWD"]["catalog"] is None
    with pytest.raises(wiring.WiringError):
        wiring.scan_id_for_fold("NOPE")


def test_s0r_window_matches_plan_ss5():
    assert wiring.FOLD_WINDOWS["S0R"] == ("2024-08-22T00:00:00Z",
                                          "2025-08-21T00:00:00Z")


# --- bars load law --------------------------------------------------------------

def test_bars_load_bounds_plus3d_and_pre125d():
    pre, ext = wiring.bars_load_bounds("2024-08-22T00:00:00Z",
                                       "2025-08-21T00:00:00Z")
    assert pre == "2024-04-19T00:00:00Z"
    assert ext == "2025-08-24T00:00:00Z"
    assert wiring.LOAD_END_PLUS_DAYS == 3


# --- funding coverage fail-closed ------------------------------------------------

def _fake_scan(tmp_path, rows_by_sym):
    for sym, rows in rows_by_sym.items():
        d = tmp_path / sym
        d.mkdir(parents=True, exist_ok=True)
        (d / "funding.json").write_text(json.dumps({"rows": rows}))
    return tmp_path


def _ms(iso):
    return int(dt.datetime.fromisoformat(iso).timestamp() * 1000)


W0, W1 = "2024-08-22T00:00:00Z", "2025-08-21T00:00:00Z"


def test_coverage_zero_rows_in_window_raises_b2(tmp_path):
    scan = _fake_scan(tmp_path, {
        "BTCUSDT": [{"fundingTime": _ms("2024-09-02T00:00:00Z"),
                     "fundingRate": "0.0001"}],
        "ETHUSDT": [{"fundingTime": _ms("2024-01-02T00:00:00Z"),
                     "fundingRate": "0.0001"}],  # outside window -> zero
    })
    with pytest.raises(wiring.WiringError, match="B2_FAIL_CLOSED.*ETHUSDT"):
        wiring.verify_funding_scan_coverage(scan, ["BTCUSDT", "ETHUSDT"],
                                            W0, W1)


def test_coverage_counts_in_window_rows(tmp_path):
    scan = _fake_scan(tmp_path, {
        "BTCUSDT": [{"fundingTime": _ms("2024-09-02T00:00:00Z"),
                     "fundingRate": "0.0001"},
                    {"fundingTime": _ms("2025-08-21T08:00:00Z"),
                     "fundingRate": "0.0002"}],  # == window end: excluded
        "ETHUSDT": [{"fundingTime": _ms("2025-08-20T00:00:00Z"),
                     "fundingRate": "0.0003"}],
    })
    counts = wiring.verify_funding_scan_coverage(scan, ["BTCUSDT", "ETHUSDT"],
                                                 W0, W1)
    assert counts == {"BTCUSDT": 1, "ETHUSDT": 1}


def test_coverage_missing_symbol_file_raises(tmp_path):
    with pytest.raises(wiring.WiringError, match="missing"):
        wiring.verify_funding_scan_coverage(tmp_path, ["BTCUSDT"], W0, W1)


def test_coverage_requires_explicit_window():
    with pytest.raises(wiring.WiringError):
        wiring.verify_funding_scan_coverage(Path("/nonexistent"), ["BTCUSDT"])


def test_non_required_symbol_zero_rows_is_allowed(tmp_path):
    # Pre-window folds: a not-yet-listed symbol legitimately has zero rows;
    # it must simply not be in the required set.
    scan = _fake_scan(tmp_path, {
        "BTCUSDT": [{"fundingTime": _ms("2024-09-02T00:00:00Z"),
                     "fundingRate": "0.0001"}],
    })
    counts = wiring.verify_funding_scan_coverage(scan, ["BTCUSDT"], W0, W1)
    assert counts == {"BTCUSDT": 1}


def test_listed_symbols_proxy_excludes_not_yet_listed(tmp_path):
    scan = _fake_scan(tmp_path, {
        "BTCUSDT": [{"fundingTime": _ms("2021-02-01T00:00:00Z"),
                     "fundingRate": "0.0001"}],
        "NEWUSDT": [{"fundingTime": _ms("2025-01-01T00:00:00Z"),
                     "fundingRate": "0.0001"}],  # first row after Y2021 end
        "GHOSTUSDT": [],                            # absent from scan
    })
    proxy = wiring.listed_symbols_proxy(scan, "2021-12-31T00:00:00Z",
                                        ["BTCUSDT", "NEWUSDT", "GHOSTUSDT"])
    assert proxy == {"BTCUSDT"}


# --- LIVE B2 proof on the real staged scans (read-only, small files) -------------

def test_live_s0r_scan_covers_all_20_symbols():
    counts = wiring.verify_funding_scan_coverage(
        wiring.FOLD_WIRING["S0R"]["funding_scan"], wiring.SYMS, W0, W1)
    assert len(counts) == 20 and all(v > 0 for v in counts.values())


def test_live_prewindow_scan_covers_pit_listed_subset():
    # Y2021 legitimately excludes not-yet-listed names (e.g. 1000PEPEUSDT,
    # listed 2023): coverage is required only for the in-window listed subset.
    for fold in ("Y2021", "Y2024P"):
        scan = wiring.FOLD_WIRING[fold]["funding_scan"]
        _, w1 = wiring.FOLD_WINDOWS[fold]
        required = sorted(wiring.listed_symbols_proxy(scan, w1))
        assert required, f"{fold}: empty listed proxy"
        counts = wiring.verify_funding_scan_coverage(
            scan, required, *wiring.FOLD_WINDOWS[fold])
        assert len(counts) == len(required)
        assert all(v > 0 for v in counts.values())


# --- 4-label invariant -----------------------------------------------------------

def test_labels_valid_row_passes():
    row = wiring.labels_for_row("S0R", wiring.SCAN_S0R_FWD)
    wiring.validate_labels(row)
    assert row["ANCESTRY"] == "OUTCOME_EXPOSED_ANCESTRY"
    assert row["NAMESPACE"] == "REPLICATION_NOT_PROSPECTIVE"
    assert row["scored"] is False
    assert row["FUNDING_WIRING"] == "funded(scan_2026_a)"
    wiring.validate_labels(wiring.labels_for_row(
        "Y2021", wiring.SCAN_PREWINDOW))


@pytest.mark.parametrize("drop", wiring.LABEL_KEYS)
def test_labels_missing_any_label_raises(drop):
    row = wiring.labels_for_row("S0R", wiring.SCAN_S0R_FWD)
    del row[drop]
    with pytest.raises(wiring.LabelError):
        wiring.validate_labels(row)


def test_labels_illegal_values_raise():
    bad_fold = wiring.labels_for_row("S0R-TEMPLATE", wiring.SCAN_S0R_FWD)
    with pytest.raises(wiring.LabelError):
        wiring.validate_labels(bad_fold)
    bad_scan = wiring.labels_for_row("S0R", "scan_9999")
    with pytest.raises(wiring.LabelError):
        wiring.validate_labels(bad_scan)
    scored_row = wiring.labels_for_row("S0R", wiring.SCAN_S0R_FWD)
    scored_row["scored"] = True
    with pytest.raises(wiring.LabelError):
        wiring.validate_labels(scored_row)
    nofund = dict(wiring.labels_for_row("S0R", wiring.SCAN_S0R_FWD))
    nofund["FUNDING_WIRING"] = "no-funding DIAG (B2)"
    wiring.validate_labels(nofund)  # the mandated B2 label is legal
