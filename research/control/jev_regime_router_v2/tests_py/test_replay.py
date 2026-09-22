"""A7-1 F2 regression carried into V2: the strict sequential replay loop.

60-state synthetic OHLCV sequence driven through `replay` end-to-end via the
REAL TS adapter subprocess (mock mode, no network, no real-data arm run):
(a) prior fields of state t equal the persisted regime after t-1,
(b) every state_id is called exactly once,
(c) resume after an interrupt continues from the decision cache with an
    identical final timeline (determinism),
(d) the digest echo never mismatches (0 incidents),
(e) the preview sampling rule reproduces the frozen preview_indices.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from conftest import make_bars
from jrv2.features import RegimeFeatures
from jrv2.replay import (
    REPLAY_RESULT_SCHEMA,
    ReplayError,
    preview_indices_rule,
    run_replay,
)
from jrv2.mock_adapter import REPLAY_MOCK_MODEL

NODE_BIN = "/opt/homebrew/bin/node"
ADAPTER_TS = Path(__file__).resolve().parent.parent / "adapter" / "src" / "adapter.ts"

pytestmark = pytest.mark.skipif(
    not Path(NODE_BIN).exists() or not ADAPTER_TS.exists(),
    reason="node / adapter.ts unavailable",
)


def _bars_60_states():
    """252 hourly bars = 192 warmup + exactly 60 decision states."""
    n = 252
    close = 100.0 * np.exp(np.linspace(0.0, 0.6, n))
    high = close * 1.004
    low = close * 0.996
    vol = np.linspace(1.0, 2.0, n)
    return make_bars(close, high, low, close, vol, step_ns=3_600 * 10**9)


def _run_replay(tmp_path, bars, fz, limit=None, progress=None):
    feats = RegimeFeatures(bars)
    return run_replay(
        fz,
        "BTC_H1",
        bars,
        feats,
        requested_model=REPLAY_MOCK_MODEL,
        pinned_model=None,
        mock=True,
        decisions_path=tmp_path / "decisions_BTC_H1.jsonl",
        adapter_cache_dir=tmp_path / "adapter_cache",
        tmp_dir=tmp_path / "tmp",
        node_bin=NODE_BIN,
        adapter_ts=ADAPTER_TS,
        limit=limit,
        progress_every=10,
        progress=progress,
    )


def _dec_lines(tmp_path):
    return [
        json.loads(l)
        for l in (tmp_path / "decisions_BTC_H1.jsonl").read_text().splitlines()
        if l.strip()
    ]


def test_replay_60_states_end_to_end_via_adapter_subprocess(fz, tmp_path):
    bars = _bars_60_states()
    progress_events: list[dict] = []
    res = _run_replay(tmp_path, bars, fz, progress=progress_events.append)

    assert res["schema"] == REPLAY_RESULT_SCHEMA
    assert res["cell"] == "BTC_H1"
    assert res["n_states"] == 60
    assert res["n_sent"] == 60
    assert res["n_cached"] == 0
    assert res["n_local_invalid"] == 0
    assert res["digest_mismatches"] == 0
    assert res["n_incidents"] == 0

    # (a) prior law: prior_direction of state t is the map of persisted after
    # t-1; the first state carries the null maps
    rows = res["rows"]
    assert rows[0]["prior_structure"] == "none"
    assert rows[0]["prior_direction"] == "none"
    for prev, cur in zip(rows, rows[1:]):
        want = {
            "UPTREND": "UP",
            "DOWNTREND": "DOWN",
            "ACCUMULATION": "DOWN",
            "DISTRIBUTION": "UP",
            "TRANSITION_UNKNOWN": "NEUTRAL",
        }[prev["persisted_after"]]
        assert cur["prior_direction"] == want
        assert cur["prior_structure"] == {"UPTREND": "TREND_UP", "DOWNTREND": "TREND_DOWN"}.get(
            prev["persisted_after"], "RANGE"
        )

    # (b) every state called exactly once: 60 distinct state_ids
    sids = [r["state_id"] for r in rows]
    assert len(set(sids)) == 60

    # decision cache: one append-only line per state, in order
    lines = _dec_lines(tmp_path)
    assert [l["state_id"] for l in lines] == sids
    # response lines carry the three typed answers + usage (persisted)
    for l in lines:
        assert set(l["answers"].keys()) == {"structure", "direction", "phase"}
        assert set(l["usage"].keys()) == {"input_tokens", "output_tokens"}

    # progress events emitted every 10 states
    assert any(p["n_processed"] == 10 for p in progress_events)
    assert progress_events[0]["schema"] == "jrv2_replay_progress@1"


def test_replay_resume_from_cache_is_deterministic(fz, tmp_path):
    bars = _bars_60_states()
    full = _run_replay(tmp_path / "a", bars, fz)
    # interrupt at 25 states, then resume: cache-first, never re-calls
    part = _run_replay(tmp_path / "b", bars, fz, limit=25)
    assert part["n_sent"] == 25
    resumed = _run_replay(tmp_path / "b", bars, fz)
    assert resumed["n_cached"] == 25  # cache-first: the first 25 never re-call
    assert resumed["n_sent"] == 35  # only the remainder is sent
    # identical final timeline
    assert [r["persisted_after"] for r in full["rows"]] == [r["persisted_after"] for r in resumed["rows"]]
    assert [r["effective"] for r in full["rows"]] == [r["effective"] for r in resumed["rows"]]


def test_replay_adapter_hard_fail_aborts(fz, tmp_path):
    """Adapter exit != 0 is a HARD FAIL (no silent partial bulk)."""
    bars = _bars_60_states()
    fake_node = tmp_path / "fake_node"
    fake_node.write_text("#!/bin/sh\nexit 3\n")
    fake_node.chmod(0o755)
    feats = RegimeFeatures(bars)
    with pytest.raises(ReplayError, match="adapter exited 3"):
        run_replay(
            fz, "BTC_H1", bars, feats,
            requested_model=REPLAY_MOCK_MODEL, pinned_model=None, mock=True,
            decisions_path=tmp_path / "d.jsonl",
            adapter_cache_dir=tmp_path / "ac",
            tmp_dir=tmp_path / "t",
            node_bin=str(fake_node),
            adapter_ts=ADAPTER_TS,
            limit=5,
        )


def test_preview_sampling_rule_reproduces_frozen_indices(fz):
    """The preregistered rule i_k = floor(k*8567/100) reproduces the frozen
    preview_indices EXACTLY (determinism law)."""
    frozen = fz.canary_contract["historical_preview"]["preview_indices"]
    assert len(frozen) == 100
    assert preview_indices_rule(8567, 100) == sorted(frozen)
    # spot-check the endpoints
    assert frozen[0] == 0 and frozen[-1] == 8481


def test_preview_mock_runs_classification_only(fz, tmp_path):
    """preview (mock): 100 BTC_H1 states, classification-only, collapse check
    runs and reports measured shares; no PnL anywhere in the payload."""
    from jrv2.replay import run_preview

    _, regime_bars, _, _ = _load_h1(fz)
    feats = RegimeFeatures(regime_bars)
    sub = tmp_path / "preview"
    res = run_preview(
        fz, regime_bars, feats, REPLAY_MOCK_MODEL, None, True,
        decisions_path=sub / "decisions_BTC_H1.jsonl",
        adapter_cache_dir=sub / "adapter_cache",
        tmp_dir=sub,
        node_bin=NODE_BIN,
        adapter_ts=ADAPTER_TS,
    )
    assert res["n_sampled"] == 100
    assert res["classification_only"] is True
    assert abs(sum(res["effective_label_shares"].values()) - 1.0) < 1e-9
    for c in res["collapse_checks"]:
        assert "fired" in c and "measured" in c
    assert "net_pnl" not in json.dumps(res)


def _load_h1(fz):
    from jrv2.data import load_btcusdt

    exec_bars, h1, h4, _ = load_btcusdt(fz)
    return exec_bars, h1, h4, None
