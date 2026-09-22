"""Freeze verification, mutation detection, S1 denial, V1 ISOLATION, scans."""

from __future__ import annotations

import hashlib
import json
import shutil

import pytest

from jrv2.data import DataBlocked, parse_spy_records
from jrv2.freezes import (
    ALL_FREEZE_FILES,
    FREEZE_MANIFEST,
    FreezeViolation,
    Freezes,
    canonical_json,
    sha256_file,
)
from jrv2.security import (
    SecurityViolation,
    assert_safe_path,
    safe_open,
    scan_package_source,
    scan_v1_references,
)


def test_all_10_freezes_verify(fz):
    rep = fz.verify()
    assert sorted(rep["verified"]) == sorted(ALL_FREEZE_FILES)
    assert len(rep["verified"]) == 10


def test_mapping_digest_assertion(fz):
    d = fz.assert_mapping_digest()
    assert d == fz.manifest["files"]["mapping_arms_freeze.json"]


def test_mutation_detected(tmp_path, fz):
    """Zero post-freeze mutation law: tampering any freeze must hard-fail."""
    dst = tmp_path / "cycle" / "freezes"
    dst.mkdir(parents=True)
    for name in ALL_FREEZE_FILES + (FREEZE_MANIFEST,):
        shutil.copy(fz.freezes_dir / name, dst / name)
    mapping = json.loads((dst / "mapping_arms_freeze.json").read_text())
    mapping["mapping"]["UPTREND"]["SPY"] = "TREND_SHORT"  # remap after freeze
    (dst / "mapping_arms_freeze.json").write_text(json.dumps(mapping))
    with pytest.raises(FreezeViolation):  # manifest digest of mapping is stale
        Freezes(tmp_path / "cycle")


def test_missing_freeze_detected(tmp_path, fz):
    dst = tmp_path / "cycle"
    shutil.copytree(fz.freezes_dir, dst / "freezes")
    (dst / "freezes" / "model_pin.json").unlink()
    with pytest.raises(FreezeViolation):
        Freezes(dst)


def test_exact_mapping_content(fz):
    """The mapping used by the engine equals the frozen file exactly."""
    m = fz.mapping["mapping"]
    assert m["ACCUMULATION"]["BTCUSDT"] == "MR_LONG"
    assert m["UPTREND"]["BTCUSDT"] == "TREND_LONG"
    assert m["DISTRIBUTION"]["BTCUSDT"] == "FLAT"
    assert m["DOWNTREND"]["BTCUSDT"] == "TREND_SHORT"
    assert m["TRANSITION_UNKNOWN"]["BTCUSDT"] == "FLAT"
    assert m["UPTREND"]["SPY"] == "TREND_LONG"
    assert m["DOWNTREND"]["SPY"] == "FLAT"  # long-only law
    assert m["ACCUMULATION"]["SPY"] == "MR_LONG"
    assert m["DISTRIBUTION"]["SPY"] == "FLAT"
    assert m["TRANSITION_UNKNOWN"]["SPY"] == "FLAT"


def test_persistence_params_frozen(fz):
    p = fz.persistence_params()
    assert p == {
        "min_confidence": 0.50,
        "min_margin": 0.20,
        "confirm_bars": 2,
        "min_dwell": 6,
        "cooldown": 3,
    }


def test_state_id_derivation_deterministic_and_opaque(fz):
    a = fz.state_id("btcusdt", 1755658800000000000)
    b = fz.state_id("btcusdt", 1755658800000000000)
    c = fz.state_id("btcusdt", 1755658800000000000 + 1)
    assert a == b
    assert a != c
    assert len(a) == 16
    int(a, 16)  # opaque hex
    # different assets differ even at the same bar ts
    assert fz.state_id("spy", 1755658800000000000) != a


def test_v2_salt_namespace_law(fz):
    """asset_salt = sha256('JRV2'||asset||data_sha)[:16] — pinned derivation."""
    data_sha = fz.data_identity["BTCUSDT"]["file_sha256"]
    want = hashlib.sha256(("JRV2" + "btcusdt" + data_sha).encode()).hexdigest()[:16]
    assert fz.asset_salt("btcusdt") == want


def test_v1_v2_salt_disjointness_for_same_bars(fz):
    """V1 isolation (mandatory collision test): V1-scheme and V2-scheme
    state_ids for identical (asset, data_sha, bar_ts) never collide."""
    v1_data_sha = fz.data_identity["BTCUSDT"]["file_sha256"]

    def v1_scheme_state_id(asset, ts):
        # V1 derivation: sha256('JRV1'||asset||data_sha)[:16] then
        # sha256(salt||str(ts))[:16]
        salt = hashlib.sha256(("JRV1" + asset + v1_data_sha).encode()).hexdigest()[:16]
        return hashlib.sha256((salt + str(ts)).encode()).hexdigest()[:16]

    bar_ts = 1755658800000000000
    for asset in ("btcusdt", "spy"):
        v1_id = v1_scheme_state_id(asset, bar_ts)
        v2_id = fz.state_id(asset, bar_ts)
        assert v1_id != v2_id
    # and the whole 16-hex state_id spaces are anchored by different salts
    assert fz.asset_salt("btcusdt") != hashlib.sha256(
        ("JRV1" + "btcusdt" + v1_data_sha).encode()
    ).hexdigest()[:16]


def test_s1_path_denial():
    with pytest.raises(SecurityViolation):
        assert_safe_path("/some/path/S1/thing.json")
    with pytest.raises(SecurityViolation):
        assert_safe_path("/some/path/s1_evidence/thing.json")
    assert_safe_path("/normal/path/thing.json")  # no raise


def test_v1_isolation_runtime_guard():
    """Any path containing the V1 cycle directory is refused at open time."""
    v1_marker = "jev_regime_router_v" + "1"
    bad = f"/Users/x/research/control/{v1_marker}/runtime/decisions.jsonl"
    with pytest.raises(SecurityViolation, match="V1 isolation"):
        assert_safe_path(bad)
    with pytest.raises(SecurityViolation, match="V1 isolation"):
        safe_open(bad, "rb")
    # the data_local copy of the V1 worktree is equally refused; v2 reads its
    # OWN data_local copy (same frozen bytes)
    with pytest.raises(SecurityViolation, match="V1 isolation"):
        assert_safe_path(f"/Users/x/research/control/{v1_marker}/data_local/SPY.json.gz")


def test_no_venue_surface_scan():
    scan = scan_package_source()
    assert scan["files_scanned"] > 0
    assert scan["findings"] == []


def test_no_v1_runtime_reference_scan():
    """Static proof: no jrv2 source references a V1 runtime path."""
    scan = scan_v1_references()
    assert scan["files_scanned"] > 0
    assert scan["findings"] == [], scan["findings"]


def test_canary_contract_frozen_shape(fz):
    cfg = fz.canary_contract
    ids = [fx["id"] for fx in cfg["synthetic_fixtures"]]
    assert ids == [
        "C1_CLEAR_UPTREND",
        "C2_CLEAR_DOWNTREND",
        "C3_RANGE_AFTER_DOWNTREND",
        "C4_RANGE_AFTER_UPTREND",
        "C5_HIGH_VOL_CONFLICT",
        "C6_LOW_VOL_RANGE",
        "C7_NOISY_CONTRADICTORY",
        "C8_MISSING_STALE",
    ]
    classes = [fx["class"] for fx in cfg["synthetic_fixtures"]]
    assert classes.count("clear") == 4
    assert classes.count("ambiguous") == 4
    assert cfg["perturbations"]["jitter"] == 0.1
    assert cfg["perturbations"]["n_per_clear_fixture"] == 8
    assert cfg["historical_preview"]["max_states"] == 100
    assert cfg["historical_preview"]["cell"] == "BTC_H1"


def test_question_contract_forced_choice(fz):
    q = fz.question_contract["questions"]
    assert q["structure"]["options"] == ["TREND", "RANGE"]
    assert q["direction"]["options"] == ["UP", "DOWN", "NEUTRAL"]
    assert q["phase"]["options"] == ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"]
    # the freeze itself declares the forced-choice law
    assert "TRANSITION_UNKNOWN is NOT an option" in q["phase"]["law"]
    assert fz.question_contract["io_schema"] == "jrv2_question_io@1"


def test_model_pin_state(fz):
    """CANDIDATE_UNVERIFIED (null pin) until G0; VERIFIED_LIVE thereafter.
    The G0 freeze landed 2026-09-22: pin = jev-1.13.0 (expected value)."""
    pin = fz.model_pin
    if pin["status"] == "CANDIDATE_UNVERIFIED":
        assert pin["pinned_model"] is None
        assert pin["expected"] == "jev-1.13.0"
    else:
        assert pin["status"] == "VERIFIED_LIVE"
        assert pin["pinned_model"] == "jev-1.13.0"


def test_canonical_json_is_sorted_and_compact():
    obj = {"b": 1, "a": {"d": 2, "c": 3}}
    assert canonical_json(obj) == '{"a":{"c":3,"d":2},"b":1}'


def test_spy_records_parse_hand_check():
    recs = [
        {"date": "2015-01-02", "open": 100.0, "high": 101.0, "low": 99.0,
         "close": 100.0, "adjusted_close": 90.0, "volume": 1000.0},
        {"date": "2015-01-05", "open": 90.5, "high": 91.0, "low": 89.0,
         "close": 90.0, "adjusted_close": 90.0, "volume": 1100.0},
    ]
    bars, dates = parse_spy_records(recs)
    assert dates == ["2015-01-02", "2015-01-05"]
    # adjfactor day1 = 0.9; adj_open = 90.0
    assert float(bars.open[0]) == pytest.approx(90.0)
    assert float(bars.close[0]) == pytest.approx(90.0)
    assert float(bars.close[1]) == pytest.approx(90.0)
