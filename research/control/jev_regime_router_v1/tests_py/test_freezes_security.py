"""Freeze verification, mutation detection, S1 denial, no-venue-surface scan."""

from __future__ import annotations

import json
import shutil

import pytest

from jrv1.data import DataBlocked, parse_spy_records
from jrv1.freezes import (
    ALL_FREEZE_FILES,
    FREEZE_MANIFEST,
    FreezeViolation,
    Freezes,
    canonical_json,
)
from jrv1.security import SecurityViolation, assert_safe_path, safe_open, scan_package_source


def test_all_12_freezes_verify(fz):
    rep = fz.verify()
    assert sorted(rep["verified"]) == sorted(ALL_FREEZE_FILES)
    assert len(rep["verified"]) == 12


def test_mapping_digest_assertion(fz):
    d = fz.assert_mapping_digest()
    assert d == fz.manifest["files"]["regime_strategy_mapping_freeze.json"]


def test_mutation_detected(tmp_path, fz):
    """Zero post-freeze mutation law: tampering any freeze must hard-fail."""
    dst = tmp_path / "cycle" / "freezes"
    dst.mkdir(parents=True)
    for name in ALL_FREEZE_FILES + (FREEZE_MANIFEST,):
        shutil.copy(fz.freezes_dir / name, dst / name)
    mapping = json.loads((dst / "regime_strategy_mapping_freeze.json").read_text())
    mapping["mapping"]["UPTREND"]["SPY"] = "TREND_SHORT"  # remap after freeze
    (dst / "regime_strategy_mapping_freeze.json").write_text(json.dumps(mapping))
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
    c = fz.state_id("spy", 1755658800000000000)
    assert a == b and a != c
    assert len(a) == 16
    int(a, 16)  # 16-hex opaque
    # salt law: sha256('JRV1'||asset||data_sha256)[:16]
    import hashlib

    ident = fz.data_identity
    salt = hashlib.sha256(
        ("JRV1" + "btcusdt" + ident["BTCUSDT"]["file_sha256"]).encode()
    ).hexdigest()[:16]
    expect = hashlib.sha256((salt + "1755658800000000000").encode()).hexdigest()[:16]
    assert a == expect


def test_s1_path_denial(tmp_path):
    with pytest.raises(SecurityViolation):
        assert_safe_path("/somewhere/S1/evidence.parquet")
    with pytest.raises(SecurityViolation):
        assert_safe_path(str(tmp_path / "s1_leak.json.gz"))
    with pytest.raises(SecurityViolation):
        assert_safe_path("data/S1/x")
    p = assert_safe_path(str(tmp_path / "fine" / "file.json"))
    assert p.exists() is False  # path check only, nothing created


def test_safe_open_denies(tmp_path):
    sealed = tmp_path / "S1"
    sealed.mkdir()
    f = sealed / "x.json"
    f.write_text("{}")
    with pytest.raises(SecurityViolation):
        safe_open(f)


def test_broker_surface_scan_finds_none():
    rep = scan_package_source()
    assert rep["files_scanned"] >= 10
    assert rep["findings"] == [], rep["findings"]


def test_canonical_json_stable():
    assert canonical_json({"b": 1, "a": [1.0, 2]}) == '{"a":[1.0,2],"b":1}'


def test_spy_records_hand_check():
    """adjfactor = adjusted_close/close; adj series = raw * adjfactor."""
    recs = [
        {
            "date": "2020-01-03",
            "open": 200.0,
            "high": 220.0,
            "low": 180.0,
            "close": 210.0,
            "adjusted_close": 105.0,
            "volume": 1000,
        },
        {
            "date": "2020-01-02",
            "open": 100.0,
            "high": 110.0,
            "low": 90.0,
            "close": 105.0,
            "adjusted_close": 52.5,
            "volume": 2000,
        },
    ]
    bars, dates = parse_spy_records(recs)
    assert dates == ["2020-01-02", "2020-01-03"]  # sorted
    assert bars.open[0] == pytest.approx(50.0)
    assert bars.high[0] == pytest.approx(55.0)
    assert bars.low[0] == pytest.approx(45.0)
    assert bars.close[0] == pytest.approx(52.5)
    assert bars.volume[0] == 2000.0
    # one consistent vehicle: ratios preserved
    assert bars.open[1] == pytest.approx(100.0)  # f = 105/210 = 0.5
    from jrv1.data import DAY

    assert bars.ts_close[0] - bars.ts_open[0] == DAY
    assert bars.ts_open[1] - bars.ts_open[0] == DAY


def test_spy_duplicate_dates_blocked():
    recs = [
        {"date": "2020-01-02", "open": 1, "high": 1, "low": 1, "close": 1, "adjusted_close": 1, "volume": 1},
        {"date": "2020-01-02", "open": 1, "high": 1, "low": 1, "close": 1, "adjusted_close": 1, "volume": 1},
    ]
    with pytest.raises(DataBlocked):
        parse_spy_records(recs)
