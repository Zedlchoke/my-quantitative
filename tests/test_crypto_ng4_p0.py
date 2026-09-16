"""CRYPTO-NG4 P0 census goldens (plan plans/PLAN_crypto_ng4.md section 4).

Fixtures, all on recorded bytes (no live network in tests):
  1. digest verification       — pinned S4 panel + OI addresses re-hash to
                                 themselves in the CADS store, and the X1
                                 shadow-battery bytes pinned under
                                 x1_inventory/ are byte-equal to the git
                                 blobs on the NG1/NG3 branches.
  2. fold-span fail-closed     — a synthetic panel whose last bar is off by
                                 one hour MUST fail the span census (the
                                 NG3 2<4-class failure mode is reproduced
                                 in-test; boundaries are never shifted).
  3. SOL RV24 recompute        — the committed sol_rv24_constants.json is
                                 recomputed from the pinned SOL panel;
                                 P33.3/P66.7/P90 must agree, plus an
                                 independent numpy hand-check of P66.7.
  4. funding cadence           — the pinned BTCUSDT fapi sample re-proves:
                                 500 settlements, measured 8h cadence, no
                                 non-8h interval in the window, INCLUSIVE
                                 boundary rule recorded.

Run:  .venv/bin/python -m pytest tests/test_crypto_ng4_p0.py -q
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
P0_DIR = REPO / "research" / "control" / "crypto_ng4_run" / "p0"
X1_DIR = P0_DIR / "x1_inventory"
STORE_ROOT = os.environ.get(
    "CNG4_P0_STORE_ROOT",
    "/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store",
)

PANEL_ADDRESSES = {
    "BTCUSDT": "111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1",
    "ETHUSDT": "ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b",
    "SOLUSDT": "c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107",
}
OI_ADDRESS = "f26a61e45a0f79322140c66a1a8862b6d933e0a831d7559af459ef638fbefbd3"
NG1_BLOB = "6411e6854c422214a92e5bdd0a11d0413659c5c1"
NG1_BRANCH_PATH = (
    "orca/crypto-ng1-integration:"
    "research/control/crypto_ng1_run/d2/d2_novelty_panel_ng1.json"
)
NG3_BRANCH_PATH = (
    "orca/crypto-ng3-integration:"
    "research/control/crypto_ng3_run/d2/d2_verdict.json"
)


def _load_census_module():
    spec = importlib.util.spec_from_file_location(
        "cng4_p0_census_run", P0_DIR / "p0_census_run.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("cng4_p0_census_run", mod)
    spec.loader.exec_module(mod)
    return mod


census = _load_census_module()


def _panel_rows(address: str) -> list[dict]:
    import csv

    obj = Path(STORE_ROOT) / "objects" / address[:2] / address
    with open(obj, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _git_bytes(branch_path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(REPO), "show", branch_path],
        capture_output=True, check=True,
    ).stdout


# --------------------------------------------------------------------------- #
# Golden 1: digest verification
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("sym,address", sorted(PANEL_ADDRESSES.items()))
def test_s4_panel_digest_verification(sym, address):
    path = Path(STORE_ROOT) / "objects" / address[:2] / address
    assert path.is_file(), f"CADS object absent: {address}"
    assert census.sha256_file(path) == address


def test_s4_oi_series_digest_verification():
    path = Path(STORE_ROOT) / "objects" / OI_ADDRESS[:2] / OI_ADDRESS
    assert path.is_file(), f"CADS object absent: {OI_ADDRESS}"
    assert census.sha256_file(path) == OI_ADDRESS
    oi = json.loads(path.read_text(encoding="utf-8"))
    assert sorted(oi.keys()) == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def test_x1_ng1_inventory_repinned_byte_equal_and_29_shapes():
    pinned = X1_DIR / "d2_novelty_panel_ng1.json"
    assert pinned.is_file()
    git_bytes = _git_bytes(NG1_BRANCH_PATH)
    assert pinned.read_bytes() == git_bytes
    doc = json.loads(git_bytes)
    assert len(doc["veto_panel"]) == 29
    blob = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", NG1_BRANCH_PATH],
        capture_output=True, check=True, text=True,
    ).stdout.strip()
    assert blob == NG1_BLOB


def test_x1_ng3_verdict_repinned_byte_equal():
    pinned = X1_DIR / "d2_verdict.json"
    assert pinned.is_file()
    assert pinned.read_bytes() == _git_bytes(NG3_BRANCH_PATH)


def test_x1_manifest_digests_match_pinned_bytes():
    man = json.loads((X1_DIR / "manifest.json").read_text(encoding="utf-8"))
    for entry_key, file_name in (
        ("ng1_inventory", "d2_novelty_panel_ng1.json"),
        ("ng3_verdict", "d2_verdict.json"),
    ):
        entry = man[entry_key]
        assert entry["pinned_sha256"] == census.sha256_file(X1_DIR / file_name)
    assert man["x1_status"] == "REPINNED"


# --------------------------------------------------------------------------- #
# Golden 2: fold-span fail-closed fixture
# --------------------------------------------------------------------------- #

def _synthetic_panel(first: str, last: str, n: int) -> list[dict]:
    rows = [{"hour_utc": first, "symbol": "BTCUSDT", "last_price": "1.0"}]
    rows += [{"hour_utc": "", "symbol": "BTCUSDT", "last_price": "1.0"}
             for _ in range(n - 2)]
    rows.append({"hour_utc": last, "symbol": "BTCUSDT", "last_price": "1.0"})
    return rows


def test_fold_span_exact_fixture_passes():
    rows = _synthetic_panel("2025-08-22T00", "2026-08-21T23", 8760)
    report, ok = census.span_census(
        rows, census.EXPECTED_FIRST_HOUR, census.EXPECTED_LAST_HOUR
    )
    assert ok and report["span_exact"]


@pytest.mark.parametrize(
    "first,last,n",
    [
        ("2025-08-22T00", "2026-08-22T00", 8760),  # last bar shifted +1h
        ("2025-08-21T23", "2026-08-21T23", 8760),  # first bar shifted -1h
        ("2025-08-22T00", "2026-08-21T23", 8759),  # one row missing
        ("2025-08-22T01", "2026-08-21T23", 8760),  # start misaligned
    ],
)
def test_fold_span_fail_closed_fixture(first, last, n):
    """ANY boundary/row mismatch must fail the census; never shifted."""
    rows = _synthetic_panel(first, last, n)
    report, ok = census.span_census(
        rows, census.EXPECTED_FIRST_HOUR, census.EXPECTED_LAST_HOUR
    )
    assert not ok and not report["span_exact"]


def test_committed_span_census_is_exact_for_all_three_panels():
    man = json.loads((P0_DIR / "p0_manifest.json").read_text(encoding="utf-8"))
    span = man["f4_span_census"]
    assert sorted(span.keys()) == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    for sym, rep in span.items():
        assert rep["rows"] == 8760
        assert rep["first_hour"] == "2025-08-22T00"
        assert rep["last_hour"] == "2026-08-21T23"
        assert rep["span_exact"] is True


# --------------------------------------------------------------------------- #
# Golden 3: SOL RV24 constant recomputation
# --------------------------------------------------------------------------- #

def test_sol_rv24_constants_recompute_from_pinned_panel():
    import numpy as np

    committed = json.loads(
        (P0_DIR / "sol_rv24_constants.json").read_text(encoding="utf-8")
    )
    rows = _panel_rows(PANEL_ADDRESSES["SOLUSDT"])
    recomputed = census.sol_rv24_constants(rows)
    for key in ("n_returns", "n_rv", "rv_min", "rv_max"):
        assert recomputed[key] == committed[key], key
    for pk in ("P33.3", "P66.7", "P90"):
        assert recomputed["percentiles"][pk] == pytest.approx(
            committed["percentiles"][pk], abs=0.0, rel=1e-15
        ), pk
    assert recomputed["thresholds"] == {
        "LOW": committed["percentiles"]["P33.3"],
        "MID": committed["percentiles"]["P66.7"],
        "HIGH": committed["percentiles"]["P90"],
    }
    # Independent hand-check (numpy) of one value: P66.7.
    prices = [float(r["last_price"]) for r in rows[: 180 * 24 + 1]]
    rets = np.diff(np.log(np.array(prices)))
    rvs = np.sqrt(np.convolve(rets * rets, np.ones(24), mode="valid"))
    p667 = float(np.percentile(rvs, 66.7))
    assert p667 == pytest.approx(committed["percentiles"]["P66.7"], rel=1e-12)
    # Boundary semantics: the P90 threshold separates HIGH from STRESS.
    assert committed["percentiles"]["P90"] < committed["rv_max"]


def test_sol_rv24_percentile_impl_matches_math_on_known_series():
    vals = sorted([1.0, 2.0, 3.0, 4.0])
    assert census.percentile(vals, 0) == 1.0
    assert census.percentile(vals, 100) == 4.0
    assert census.percentile(vals, 50) == pytest.approx(2.5)
    assert census.percentile(vals, 33.3) == pytest.approx(1.999, rel=1e-9)


# --------------------------------------------------------------------------- #
# Golden 4: funding cadence on a recorded sample
# --------------------------------------------------------------------------- #

def test_funding_cadence_fixture_on_recorded_btcusdt_sample():
    sample = P0_DIR / "funding" / "BTCUSDT_funding_sample.json"
    assert sample.is_file(), "pinned funding sample absent"
    proof = census.funding_proof(sample.read_bytes())
    assert proof["settlements"] == 500
    assert proof["measured_cadence_hours_nominal"] == 8.0
    # No 4h/1h stress adjustment in this recorded window: every observed
    # interval is within 60s of 8h (millisecond stamp jitter only), so the
    # MATERIAL deviation bucket is empty.
    for interval_h, count in proof["interval_histogram_hours"].items():
        assert abs(float(interval_h) - 8.0) < 1e-3
        assert count >= 1
    assert proof["material_non_8h_interval_counts"] == {}
    assert "INCLUSIVE" in proof["boundary_rule"]


def test_funding_samples_pinned_for_all_three_series():
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        p = P0_DIR / "funding" / f"{sym}_funding_sample.json"
        assert p.is_file(), sym
        rows = json.loads(p.read_text(encoding="utf-8"))
        assert len(rows) == 500
        assert all(r["symbol"] == sym for r in rows)
        times = [int(r["fundingTime"]) for r in rows]
        assert times == sorted(times)
        span_ms = times[-1] - times[0]
        # 499 intervals x 8h nominal (ms offsets may add a few ms).
        assert abs(span_ms - 499 * 8 * 3_600_000) < 1000


def test_committed_funding_digests_match_pinned_samples():
    verdict = json.loads((P0_DIR / "p0_verdict.json").read_text(encoding="utf-8"))
    for sym, digest in verdict["f2_funding_digests"].items():
        p = P0_DIR / "funding" / f"{sym}_funding_sample.json"
        assert census.sha256_bytes(p.read_bytes()) == digest


# --------------------------------------------------------------------------- #
# Committed verdict / census consistency (F3, F5, F7) + F6 determinism
# --------------------------------------------------------------------------- #

def test_committed_verdict_passes_all_gates_and_census():
    verdict = json.loads((P0_DIR / "p0_verdict.json").read_text(encoding="utf-8"))
    assert verdict["verdict"] == "PASS"
    assert set(verdict["gates"].values()) == {"PASS"}
    assert verdict["x1_status"] == "REPINNED"
    assert verdict["f1_panels"] == PANEL_ADDRESSES
    assert verdict["f1_oi_address"] == OI_ADDRESS
    assert verdict["f3"]["n_pairs"] == 3
    assert sorted(verdict["f3"]["pairs"]) == [
        "BTCUSDT-ETHUSDT", "BTCUSDT-SOLUSDT", "ETHUSDT-SOLUSDT",
    ]
    assert verdict["f5_cost_kernel"] == "L-V14-0"
    assert verdict["f7_collectors_started"] is False
    assert verdict["incidents"] == []


def test_f5_cost_kernel_references_exist_with_digests():
    man = json.loads((P0_DIR / "p0_manifest.json").read_text(encoding="utf-8"))
    refs = man["f5_cost_kernel"]["references"]
    assert man["f5_cost_kernel"]["kernel"] == "L-V14-0"
    assert all(r["exists"] for r in refs)
    for r in refs:
        p = REPO / r["path"]
        assert census.sha256_file(p) == r["sha256"], r["path"]


def test_f6_rerun_is_byte_identical():
    deterministic = [
        P0_DIR / "p0_verdict.json",
        P0_DIR / "p0_manifest.json",
        P0_DIR / "sol_rv24_constants.json",
        X1_DIR / "manifest.json",
    ]
    before = {p: p.read_bytes() for p in deterministic}
    rc = subprocess.run(
        [sys.executable, str(P0_DIR / "p0_census_run.py")],
        capture_output=True,
    )
    assert rc.returncode == 0, rc.stderr.decode()
    for p, b in before.items():
        assert p.read_bytes() == b, f"rerun differs: {p.name}"
