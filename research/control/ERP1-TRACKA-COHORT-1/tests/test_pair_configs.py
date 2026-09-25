"""Fixture tests: probe-proven pair configs (plan §5.2 — pip/price-scale/
band DERIVED from probe ticks, never assumed; fail-closed consumers).

Runs GREEN only after probe_pair.py has written scripts/pair_configs.json
for both cohort pairs; before that the fail-closed loader raises, which is
itself the gate behavior (skip-with-reason keeps the suite honest pre-probe).
"""
import hashlib
import json
from pathlib import Path

import pytest

from pair_config import REGISTERED_GUARDS, load_pair_config

LANE = Path(__file__).resolve().parent.parent
CONFIG = LANE / "scripts" / "pair_configs.json"
DERIVED = LANE / "data_local" / "derived"

PAIRS = ["AUDUSD", "USDCAD"]


def _configs():
    if not CONFIG.exists():
        pytest.skip("pair_configs.json not yet written by probe_pair.py")
    return json.loads(CONFIG.read_text())


@pytest.mark.parametrize("symbol", PAIRS)
def test_config_proven_and_guard_validated(symbol):
    cfgs = _configs()
    if symbol not in cfgs:
        pytest.skip(f"{symbol} not yet probe-proven")
    cfg = load_pair_config(symbol)  # raises SystemExit if not proven/invalid
    assert cfg.derivation.get("proven") is True
    # byte-derived identity: pip == 10 x point, point == 1/price_scale
    assert cfg.pip == pytest.approx(10.0 / cfg.price_scale)
    # registered expectations (plan §5.2): band must cover the guard range
    g = REGISTERED_GUARDS[symbol]
    assert cfg.band_lo <= g["band_lo"]
    assert cfg.band_hi >= g["band_hi"]


@pytest.mark.parametrize("symbol", PAIRS)
def test_config_matches_probe_report(symbol):
    cfgs = _configs()
    if symbol not in cfgs:
        pytest.skip(f"{symbol} not yet probe-proven")
    rep_path = LANE / cfgs[symbol]["derivation"]["probe_report"]
    assert rep_path.exists()
    raw = rep_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == \
        cfgs[symbol]["derivation"]["probe_report_sha256"]
    rep = json.loads(raw)
    assert rep["verdict"] == "PROBE_PASS"
    d = rep["derivation"]
    assert cfgs[symbol]["price_scale"] == d["price_scale"]
    assert cfgs[symbol]["pip"] == d["pip_price_units"]
    bd = rep["band_derivation"]
    assert cfgs[symbol]["band_lo"] == bd["band_lo"]
    assert cfgs[symbol]["band_hi"] == bd["band_hi"]
    # exactly one scale candidate survived the guard-band uniqueness check
    assert rep["scale_candidates"]["accepted"] is not None
    assert len(rep["scale_candidates"]["all"]) == 1
    # tick-vs-candle cross-check was clean on both sides
    assert rep["crosscheck"]["mismatch_bid"] == 0
    assert rep["crosscheck"]["mismatch_ask"] == 0


def test_no_verdict_fields_in_configs():
    """Configs are data-gate artifacts only: no outcome/score fields may
    ever appear here (lane boundary)."""
    cfgs = _configs()
    banned = {"pnl", "net_pips", "score", "verdict", "arm", "signal"}
    for s, cfg in cfgs.items():
        for k in cfg:
            assert k.lower() not in banned, f"banned key {k} in {s}"
