"""E1 enforcement + E6(e) determinism + R2-6 scanner tests."""
import json
import os

import pytest

from emv1 import config as C
from emv1.loaders import verify_all_digests, ForbiddenColumn, PANEL_FORBIDDEN_COLUMNS
from emv1.panel import load_name_bars
from emv1.nopnl import scan_object, scan_paths


def test_digests_fail_closed_pass():
    ev = verify_all_digests()
    assert ev["ok"] is True
    assert ev["a1_events_rows"] == C.PIN_A1_EVENTS_ROWS
    assert ev["form4_stream_rows"] == C.PIN_FORM4_STREAM_ROWS
    assert ev["panel"]["verified_ok"] == ev["panel"]["manifest_entries"]
    assert ev["eodhd_div"]["bad"] == 0
    assert ev["eodhd_splits"]["bad"] == 0


def test_adjusted_close_request_raises():
    with pytest.raises(ForbiddenColumn):
        load_name_bars("AAPL", columns=["date", "adjusted_close"])


def test_adjusted_close_never_extracted_even_with_full_allowlist():
    bars = load_name_bars("SPY")
    assert bars, "SPY panel present in NG6"
    assert set(bars[0].keys()) <= {"date", "open", "high", "low", "close", "volume"}
    assert "adjusted_close" not in bars[0]


def test_nopnl_scanner_catches_forbidden_keys():
    bad = {"a": {"pnl": 1.0}, "b": [{"expectancy": 3}]}
    v = scan_object(bad)
    assert len(v) == 2
    good = {"entry_price": 10.5, "exit_price": 11.0, "cost_entry_bps_x1": 33.5}
    assert scan_object(good) == []


def test_decision_records_and_evidence_pass_nopnl_scan():
    paths = []
    for root in (C.EVIDENCE_DIR, C.DRYRUN_DIR):
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if fn.endswith((".json", ".jsonl")):
                    paths.append(os.path.join(dirpath, fn))
    violations, n = scan_paths(sorted(paths))
    assert n > 0
    assert violations == [], violations[:5]


def test_determinism_small_rebuild_byte_identical():
    """Two builds from identical inputs produce byte-identical records."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "run"))
    from emv1.loaders import load_a1_events
    from emv1.panel import Panel
    from emv1.arms import build_a1_arms
    from emv1.book import summarize_populations

    a1_events, _ = load_a1_events()
    first12 = set(sorted({e["cik"] for e in a1_events})[:12])  # hoisted (O(n))
    subset = [e for e in a1_events if e["cik"] in first12][:400]
    outs = []
    for _ in range(2):
        panel = Panel(["SPY"] + sorted({e["ticker"] for e in subset}))
        recs, exs = build_a1_arms(subset, panel, {}, n4=None)
        outs.append((json.dumps(recs, sort_keys=True), json.dumps(exs, sort_keys=True),
                     json.dumps(summarize_populations(recs), sort_keys=True)))
    assert outs[0] == outs[1]
