"""E-phase worker config tests (offline; NO network).

Contract under test (tests must stay offline: the synthetic feed is
never called because a future SHADOW_START_UTC leaves nothing due):
- build_executors constructs all FOUR production ForwardExecutors
  against the REAL identity manifest (identity pinning active through
  every adapter's validate_config);
- the per-symbol tick mapping resolves from the ARCHIVED exchangeInfo
  (sha256 verified first, fail closed on mismatch); an unknown symbol
  falls back to tick_size_default = 0.10 (BTCUSDT tick, conservative);
- the frozen scheduler constants: two weekly-Monday-00Z families, one
  daily-00Z family and one H4-00Z family (BTC4H-BANDRIDGE);
- --once with a synthetic feed + a FUTURE shadow-start performs exactly
  one loop, writes a heartbeat with every required key, and writes ZERO
  prospective ledger events (nothing can be due yet);
- the worker refuses to start without --shadow-start (PROSPECTIVE
  fail-closed rule).
"""
import importlib.util
import json
import os
from pathlib import Path

import pytest

from research.shadow_v1 import (
    data_feed,
    ledger,
    scheduler,
    start_guard,
)
from research.shadow_v1.families import (
    FAMILY_BANDRIDGE,
    FAMILY_CARRY,
    FAMILY_ILLIQ,
    FAMILY_PREMFADE,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = (
    REPO_ROOT
    / "research"
    / "control"
    / "prospective_shadow_v1"
    / "e"
    / "shadow_worker.py"
)
IDENTITY_PATH = (
    REPO_ROOT
    / "research"
    / "control"
    / "prospective_shadow_v1"
    / "identity"
    / "identity_recovery.json"
)
ARCHIVE_PATH = (
    REPO_ROOT
    / "research"
    / "control"
    / "prospective_shadow_v1"
    / "data_cost"
    / "raw"
    / "cross"
    / "exchangeInfo_fapi.json"
)


def _load_worker_module():
    assert WORKER_PATH.is_file(), f"missing worker module: {WORKER_PATH}"
    spec = importlib.util.spec_from_file_location("shv1_shadow_worker", WORKER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shadow_worker = _load_worker_module()


class _ForbiddenFeed:
    """A feed that must NEVER be fetched in these offline tests."""

    def __getattr__(self, name):
        raise AssertionError(
            f"offline test tried to fetch via feed.{name}; nothing may be "
            "due under a future SHADOW_START_UTC"
        )


def _future_shadow_start() -> str:
    return "2030-01-07T00:00:00Z"  # a Monday far in the future


def _archive_ticks_verbatim() -> dict:
    raw = ARCHIVE_PATH.read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    ticks = {}
    for symbol in doc["symbols"]:
        if symbol.get("quoteAsset") != "USDT":
            continue
        for entry in symbol.get("filters", []):
            if entry.get("filterType") == "PRICE_FILTER":
                ticks[symbol["symbol"]] = entry["tickSize"]
    return ticks


# ----------------------------------------------------------------------
# executor construction against the REAL identity manifest
# ----------------------------------------------------------------------
def test_build_executors_constructs_all_mounted_families(tmp_path):
    executors = shadow_worker.build_executors(
        str(tmp_path), _future_shadow_start(), feed=_ForbiddenFeed()
    )
    assert tuple(executors.keys()) == (
        FAMILY_ILLIQ, FAMILY_PREMFADE, FAMILY_CARRY, FAMILY_BANDRIDGE,
    )
    for family_id, executor in executors.items():
        assert executor.family_id == family_id
        assert executor.arm_id == family_id
        assert executor.namespace == start_guard.NAMESPACE_PROSPECTIVE
        assert executor.shadow_start_utc == _future_shadow_start()
        assert executor.feature_cutoff_offset_seconds == 900.0  # C6 pin
        assert executor.primary_book == "CURRENT_CONSERVATIVE_COST"
        assert set(executor.cost_books_cfg) == {
            "CURRENT_CONSERVATIVE_COST",
            "LINEAGE_COST",
        }
        assert executor.code_freeze_sha == shadow_worker.CODE_FREEZE_SHA
        # identity pinning: the adapter validated against the manifest
        assert executor.adapter.FAMILY_ID == family_id
        assert executor.caps.family_id == family_id
        # PROSPECTIVE ledgers live under the namespace-separated root
        assert os.path.join("ledgers") in executor.ledger_file
    # verbatim cap values (identity manifest)
    carry_caps = executors[FAMILY_CARRY].caps.as_dict()
    assert carry_caps["target_gross"] == 0.80
    assert carry_caps["hard_gross_cap"] == 1.00
    assert carry_caps["hard_abs_net_cap"] == 0.10
    assert carry_caps["max_abs_weight"] == 0.20
    premfade_caps = executors[FAMILY_PREMFADE].caps.as_dict()
    assert premfade_caps["target_gross"] == 1.0
    assert premfade_caps["hard_gross_cap"] == 1.0
    assert premfade_caps["hard_abs_net_cap"] == 0.0
    assert premfade_caps["dollar_neutral"] is True
    assert premfade_caps["min_abs_weight"] == 0.125
    assert premfade_caps["max_abs_weight"] == 0.30
    illiq_caps = executors[FAMILY_ILLIQ].caps.as_dict()
    assert illiq_caps["dollar_neutral"] is True
    assert illiq_caps["btc_beta_neutral"] is True
    # snapshot specs honour the executor contract per family kind
    assert set(executors[FAMILY_ILLIQ].snapshot_spec) == {"bars"}
    assert set(executors[FAMILY_PREMFADE].snapshot_spec) == {"basis_buckets"}
    assert set(executors[FAMILY_CARRY].snapshot_spec) == {"funding_settlements"}
    for family_id in (FAMILY_ILLIQ, FAMILY_PREMFADE):
        spec = executors[family_id].snapshot_spec
        kind = next(iter(spec))
        assert spec[kind]["interval"] == "15m"
        assert spec[kind]["lookback_seconds"] == 29 * 86400 + 3600
    carry_spec = executors[FAMILY_CARRY].snapshot_spec["funding_settlements"]
    assert carry_spec["lookback_seconds"] == 7 * 86400
    assert sorted(carry_spec["symbols"]) == sorted(shadow_worker.CARRY_TRADED_UNIVERSE)
    assert executors[FAMILY_CARRY].fill_symbols == list(
        shadow_worker.CARRY_TRADED_UNIVERSE
    )
    # sleeve 4 (BTC4H-BANDRIDGE, mounted 2026-09-24): long-only 1.0,
    # no neutrality, 60d of 15m BTCUSDT bars behind the H4 clock
    band_caps = executors[FAMILY_BANDRIDGE].caps.as_dict()
    assert band_caps["target_gross"] == 1.0
    assert band_caps["hard_gross_cap"] == 1.0
    assert band_caps["hard_abs_net_cap"] == 1.0
    assert band_caps["max_abs_weight"] == 1.0
    assert band_caps.get("dollar_neutral") is not True
    assert set(executors[FAMILY_BANDRIDGE].snapshot_spec) == {"bars"}
    band_spec = executors[FAMILY_BANDRIDGE].snapshot_spec["bars"]
    assert band_spec == {
        "symbols": ["BTCUSDT"],
        "interval": "15m",
        "lookback_seconds": float(60 * 86400),
    }


def test_build_executors_refuses_prospective_without_shadow_start(tmp_path):
    with pytest.raises(start_guard.StartGuardError):
        shadow_worker.build_executors(str(tmp_path), None, feed=_ForbiddenFeed())


def test_worker_main_refuses_missing_shadow_start(tmp_path, capsys):
    exit_code = shadow_worker.main(
        ["--runtime-root", str(tmp_path), "--once"]
    )
    assert exit_code == 2
    assert "REFUSED" in capsys.readouterr().err


# ----------------------------------------------------------------------
# tick mapping from the archived exchangeInfo
# ----------------------------------------------------------------------
def test_tick_mapping_resolves_from_verified_archive(tmp_path):
    # verify the archive sha256 pin FIRST (fail closed on mismatch)
    import hashlib

    digest = hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest()
    assert digest == shadow_worker.EXCHANGE_INFO_SHA256
    verbatim = _archive_ticks_verbatim()

    executors = shadow_worker.build_executors(
        str(tmp_path), _future_shadow_start(), feed=_ForbiddenFeed()
    )
    carry = executors[FAMILY_CARRY]
    # every family-3 traded symbol resolves to the archived verbatim tick
    for symbol in shadow_worker.CARRY_TRADED_UNIVERSE:
        assert symbol in carry.tick_size_map
        assert carry.tick_size_map[symbol] == float(verbatim[symbol])
        assert carry._resolve_tick(symbol) == float(verbatim[symbol])
    # families 1-2: covering mapping for every declared candidate,
    # each resolved to the archived verbatim tick (cost_regime_manifest
    # tick_size_roles.family1_family2 rule)
    candidates = set(
        shadow_worker.ILLIQ_CANDIDATE_UNIVERSE
        + shadow_worker.PREMFADE_CANDIDATE_UNIVERSE
    )
    for family_id in (FAMILY_ILLIQ, FAMILY_PREMFADE):
        mapping = executors[family_id].tick_size_map
        assert candidates <= set(mapping)
        for symbol, expected in mapping.items():
            assert expected == float(verbatim[symbol])
        # the cost-regime manifest's measured pin set is covered
        assert set(shadow_worker.MEASURED_TICK_SYMBOLS) <= set(mapping)
        # sub-dollar candidates must never price at the 0.10 default
        for sub_dollar in ("OPUSDT", "APTUSDT", "DOGEUSDT", "TRXUSDT"):
            if sub_dollar in mapping:
                assert mapping[sub_dollar] < 0.001
    # an unknown symbol falls back to tick_size_default = 0.10
    for family_id, executor in executors.items():
        assert executor.tick_size_default == 0.10
        assert executor._resolve_tick("DEFINITELY_NOT_A_SYMBOL_USDT") == 0.10


def test_tick_loader_fails_closed_on_archive_mismatch(tmp_path, monkeypatch):
    real_path = shadow_worker.EXCHANGE_INFO_ARCHIVE_PATH
    tampered = tmp_path / "exchangeInfo_fapi.json"
    tampered.write_bytes(ARCHIVE_PATH.read_bytes() + b" ")
    monkeypatch.setattr(shadow_worker, "EXCHANGE_INFO_ARCHIVE_PATH", str(tampered))
    with pytest.raises(shadow_worker.WorkerConfigError, match="sha256 mismatch"):
        shadow_worker.load_archived_symbol_info()
    monkeypatch.setattr(shadow_worker, "EXCHANGE_INFO_ARCHIVE_PATH", real_path)


# ----------------------------------------------------------------------
# paced transport (transient 429 must not burn a weekly event_id)
# ----------------------------------------------------------------------
def test_paced_fetch_retries_rate_limit_then_succeeds():
    import urllib.error

    attempts = {"n": 0}

    class _FakeHeaders(dict):
        def get(self, key, default=None):  # pragma: no cover - trivial
            return super().get(key, default)

    def rate_limited_then_ok(url):
        attempts["n"] += 1
        if attempts["n"] < 3:
            err = urllib.error.HTTPError(
                url, 429, "rate limited", _FakeHeaders({"Retry-After": "0"}), None
            )
            raise err
        return b"[1,2,3]"

    sleeps = []
    paced = shadow_worker.PacedFetch(
        min_gap_seconds=0.0,
        clock=lambda: 0.0,
        sleeper=sleeps.append,
        transport=rate_limited_then_ok,
    )
    payload = paced("https://fapi.binance.com/fapi/v1/klines?x=1")
    assert payload == b"[1,2,3]"
    assert attempts["n"] == 3
    assert paced.retries_made == 2
    assert sleeps, "a 429 retry must back off via the injected sleeper"


def test_paced_fetch_exhaustion_raises_data_blocked():
    import urllib.error

    class _FakeHeaders(dict):
        pass

    def always_429(url):
        raise urllib.error.HTTPError(
            url, 429, "rate limited", _FakeHeaders({"Retry-After": "0"}), None
        )

    paced = shadow_worker.PacedFetch(
        min_gap_seconds=0.0,
        max_attempts=3,
        clock=lambda: 0.0,
        sleeper=lambda s: None,
        transport=always_429,
    )
    with pytest.raises(data_feed.DataBlocked, match="exhausted 3 attempts"):
        paced("https://fapi.binance.com/fapi/v1/klines?x=1")


def test_default_feed_uses_paced_transport(tmp_path, monkeypatch):
    # build_executors' default feed injects the paced transport
    captured = {}
    real_client = shadow_worker.KeylessBinanceFuturesClient

    def spy_client(*args, **kwargs):
        captured["fetch_fn"] = kwargs.get("fetch_fn")
        return real_client(*args, **kwargs)

    monkeypatch.setattr(shadow_worker, "KeylessBinanceFuturesClient", spy_client)
    shadow_worker.build_executors(str(tmp_path), _future_shadow_start())
    assert isinstance(captured["fetch_fn"], shadow_worker.PacedFetch)


# ----------------------------------------------------------------------
# frozen schedules
# ----------------------------------------------------------------------
def test_schedule_constants_two_weekly_one_daily_one_h4(tmp_path):
    executors = shadow_worker.build_executors(
        str(tmp_path), _future_shadow_start(), feed=_ForbiddenFeed()
    )
    assert executors[FAMILY_ILLIQ].schedule == scheduler.SCHEDULE_WEEKLY_MONDAY_0000Z
    assert executors[FAMILY_PREMFADE].schedule == scheduler.SCHEDULE_WEEKLY_MONDAY_0000Z
    assert executors[FAMILY_CARRY].schedule == scheduler.SCHEDULE_DAILY_0000Z
    assert executors[FAMILY_BANDRIDGE].schedule == scheduler.SCHEDULE_H4_0000Z
    # and they match the frozen scheduler map for every family
    for family_id, executor in executors.items():
        assert executor.schedule == scheduler.FAMILY_SCHEDULES[family_id]


# ----------------------------------------------------------------------
# --once loop with a future shadow-start: one heartbeat, zero events
# ----------------------------------------------------------------------
def test_once_loop_writes_heartbeat_and_zero_ledger_events(tmp_path):
    runtime_root = tmp_path / "runtime_shv1_worker"
    executors = shadow_worker.build_executors(
        str(runtime_root), _future_shadow_start(), feed=_ForbiddenFeed()
    )
    exit_code = shadow_worker.run_loop(
        executors,
        str(runtime_root),
        interval_seconds=300.0,
        once=True,
    )
    assert exit_code == 0

    heartbeat_path = runtime_root / "runtime" / "heartbeat.json"
    assert heartbeat_path.is_file(), "heartbeat.json must exist after one loop"
    payload = json.loads(heartbeat_path.read_text())
    for key in (
        "pid",
        "loop_count",
        "last_loop_utc",
        "next_decision_per_family",
        "last_completed",
        "ledger_byte_counts",
        "heartbeat_inode_vs_path_check",
        "last_error",
    ):
        assert key in payload, f"heartbeat missing required key {key!r}"
    assert payload["pid"] == os.getpid()
    assert payload["loop_count"] == 1
    assert payload["last_error"] is None
    assert payload["heartbeat_inode_vs_path_check"]["match"] is True
    assert set(payload["next_decision_per_family"]) == set(executors)
    # nothing due under a future shadow-start: no prospective ledger events
    for family_id, executor in executors.items():
        assert ledger.scan_events(executor.ledger_file) == []
        assert payload["ledger_byte_counts"][family_id] == 0
    # the next decision is the first Monday/daily stamp at-or-after now,
    # never before the shadow start (forward-only rule)
    for family_id, stamp in payload["next_decision_per_family"].items():
        assert stamp is not None
        executor = executors[family_id]
        start_guard.assert_forward(stamp, executor.shadow_start_utc, executor.namespace)


def test_identity_manifest_present_and_pinned():
    manifest = json.loads(IDENTITY_PATH.read_text())
    families = {entry["family_id"]: entry for entry in manifest["families"]}
    for family_id in (FAMILY_ILLIQ, FAMILY_PREMFADE, FAMILY_CARRY):
        assert family_id in families
        entry = families[family_id]
        # verdict labels are NOT rewritable (identity manifest policy)
        expected_labels = {
            FAMILY_ILLIQ: "V11_FAMILY_REJECT",
            FAMILY_PREMFADE: "V14_FAMILY_REJECT",
            FAMILY_CARRY: "CANDIDATE_FAIL",
        }
        assert entry["historical_verdict_label"] == expected_labels[family_id]
        assert entry["score_affecting_parameters"]
