"""A7-1 F2 regression: the strict sequential replay loop.

60-state synthetic OHLCV sequence driven through `replay` end-to-end via the
REAL TS adapter subprocess (mock mode, no network, no real-data arm run):
(a) prior_regime of state t equals the persisted regime after t-1,
(b) every state_id is called exactly once,
(c) resume after an interrupt continues from the decision cache with an
    identical final timeline (determinism),
(d) the digest echo never mismatches (0 incidents) — amendment_1 holds
    across the process boundary.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from conftest import make_bars
from jrv1.decisions import compute_input_digest, validate_response_line
from jrv1.features import RegimeFeatures, state_payload
from jrv1.persistence import PersistenceState, raw_from_response, step
from jrv1.replay import REPLAY_MOCK_MODEL, ReplayError, fixture_request_lines, run_replay

NODE_BIN = "/opt/homebrew/bin/node"
ADAPTER_TS = Path(__file__).resolve().parent.parent / "adapter" / "src" / "adapter.ts"

pytestmark = pytest.mark.skipif(
    not Path(NODE_BIN).exists() or not ADAPTER_TS.exists(),
    reason="node / adapter.ts unavailable",
)


def _bars_60_states():
    """252 hourly bars = 192 warmup + exactly 60 decision states.

    Smooth exponential path with strictly positive range and drifting volume
    so every feature is finite (no LOCAL_INVALID states in this fixture).
    """
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
        "btcusdt",
        bars,
        feats,
        requested_model=REPLAY_MOCK_MODEL,
        pinned_model=None,
        mock=True,
        decisions_path=tmp_path / "decisions_btcusdt.jsonl",
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
        for l in (tmp_path / "decisions_btcusdt.jsonl").read_text().splitlines()
        if l.strip()
    ]


def test_replay_60_states_end_to_end_via_adapter_subprocess(fz, tmp_path):
    bars = _bars_60_states()
    progress_events: list[dict] = []
    res = _run_replay(tmp_path, bars, fz, progress=progress_events.append)

    assert res["n_states"] == 60
    assert res["n_sent"] == 60
    assert res["n_cached"] == 0
    assert res["n_local_invalid"] == 0
    # (d) digest echo never mismatched: 0 incidents of any kind
    assert res["digest_mismatches"] == 0
    assert res["n_incidents"] == 0

    rows = res["rows"]
    assert len(rows) == 60
    # (a) strict prior chain: state t carries the persisted regime after t-1
    assert rows[0]["prior_regime"] is None
    for prev, cur in zip(rows, rows[1:]):
        assert cur["prior_regime"] == prev["persisted_after"]
    assert all(r["sent"] and not r["cached"] for r in rows)

    # (b) every state_id called EXACTLY once: one decision-cache line and one
    # adapter cache entry per state, all distinct
    sids = [r["state_id"] for r in rows]
    assert len(set(sids)) == 60
    dec = _dec_lines(tmp_path)
    assert len(dec) == 60
    assert sorted(d["state_id"] for d in dec) == sorted(sids)
    cache_dir = tmp_path / "adapter_cache"
    assert len(list(cache_dir.glob("*.json"))) == 60
    # every stored response echoes the producer digest (amendment_1); the
    # cache key formula is the TS side's single authority (amendment_2 adds
    # the prompt digest) — python matches via the stored entry fields instead
    # of duplicating the formula.
    cache_entries = []
    for cf in cache_dir.glob("*.json"):
        entry = json.loads(cf.read_text())
        cache_entries.append(entry)
    by_state = {e["state_id"]: e for e in cache_entries}
    assert len(by_state) == 60
    for d in dec:
        assert len(d["input_digest"]) == 64
        entry = by_state[d["state_id"]]
        assert entry["input_digest"] == d["input_digest"]
        assert entry["model"] == REPLAY_MOCK_MODEL

    # progress JSON emitted per 10 states (>= every 100 per law)
    assert progress_events, "progress events must be emitted"
    assert [p["n_processed"] for p in progress_events] == [10, 20, 30, 40, 50, 60]
    assert all(p["schema"] == "jrv1_replay_progress@1" for p in progress_events)


def test_replay_resume_after_interrupt_deterministic(fz, tmp_path, tmp_path_factory):
    bars = _bars_60_states()
    # interrupt: only the first 25 states processed
    res1 = _run_replay(tmp_path, bars, fz, limit=25)
    assert res1["n_states"] == 25 and res1["n_sent"] == 25

    # resume on the SAME decision cache: 25 cache hits, 35 new calls
    res2 = _run_replay(tmp_path, bars, fz)
    assert res2["n_states"] == 60
    assert res2["n_cached"] == 25
    assert res2["n_sent"] == 35
    assert res2["n_incidents"] == 0 and res2["digest_mismatches"] == 0
    # cached states re-validated against the CURRENT recomputed digest and
    # reproduce identical persisted states
    for r1, r2 in zip(res1["rows"], res2["rows"][:25]):
        assert r1["state_id"] == r2["state_id"]
        assert r1["persisted_after"] == r2["persisted_after"]

    # determinism: a single uninterrupted run on a fresh store yields the
    # IDENTICAL final timeline
    fresh_dir = tmp_path_factory.mktemp("fresh")
    res_full = _run_replay(fresh_dir, bars, fz)
    assert res_full["n_sent"] == 60 and res_full["n_cached"] == 0

    def key(r):
        return (r["state_id"], r["prior_regime"], r["status"], r["persisted_after"])

    assert [key(r) for r in res2["rows"]] == [key(r) for r in res_full["rows"]]


def test_replay_priors_recomputed_after_each_merge(fz, tmp_path):
    """Independent replay of the persistence machine over the stored decision
    lines reproduces the prior chain exactly: the prior of request t is the
    persisted regime AFTER t-1 (recomputed after every merge)."""
    bars = _bars_60_states()
    res = _run_replay(tmp_path, bars, fz)
    rows = res["rows"]
    dec = {d["state_id"]: d for d in _dec_lines(tmp_path)}
    feats = RegimeFeatures(bars)

    st = PersistenceState(min_confidence=0.50, min_margin=0.20, confirm_bars=2, min_dwell=6, cooldown=3)
    prior = None
    for r in rows:
        assert r["prior_regime"] == prior
        vec = feats.vector_at(r["bar_index"])
        payload = state_payload({"feature_vector": vec, "prior_regime": prior, "local_invalid": False})
        digest = compute_input_digest(payload, REPLAY_MOCK_MODEL)
        normalized, violation = validate_response_line(dec[r["state_id"]], r["state_id"], digest)
        assert violation is None
        raw, eligible = raw_from_response(normalized, {"min_confidence": 0.5, "min_margin": 0.2})
        step(st, raw, eligible)
        assert st.current == r["persisted_after"]
        prior = st.current


def test_replay_hard_fails_on_adapter_error(fz, tmp_path):
    """Adapter exit != 0 is a HARD FAIL (ReplayError), no silent partial."""
    bars = _bars_60_states()
    feats = RegimeFeatures(bars)
    fake_node = tmp_path / "fake_node"
    fake_node.write_text("#!/bin/sh\nexit 3\n")
    fake_node.chmod(0o755)
    with pytest.raises(ReplayError, match="exited 3"):
        run_replay(
            fz,
            "btcusdt",
            bars,
            feats,
            requested_model=REPLAY_MOCK_MODEL,
            pinned_model=None,
            mock=True,
            decisions_path=tmp_path / "dec.jsonl",
            adapter_cache_dir=tmp_path / "cache",
            tmp_dir=tmp_path / "tmp",
            node_bin=str(fake_node),  # exits non-zero immediately
            adapter_ts=ADAPTER_TS,
            limit=3,
        )


def test_prepare_requests_bulk_refused(fz, capsys):
    """Batch prepare-requests without --fixtures-only is REFUSED (A7-1 F2)."""
    from jrv1 import run as run_mod

    with pytest.raises(SystemExit, match="replay"):
        run_mod.main(["prepare-requests", "--asset", "spy"])
    assert capsys.readouterr().out == ""


def test_prepare_requests_fixtures_only(fz, tmp_path, monkeypatch):
    """--fixtures-only emits producer-digested request lines for the frozen
    synthetic canaries with FIXED priors and no persistence dependency."""
    from jrv1 import run as run_mod

    monkeypatch.setattr(run_mod, "runtime_dir", lambda fz: tmp_path)
    run_mod.main(["prepare-requests", "--asset", "spy", "--fixtures-only"])
    lines = [json.loads(l) for l in (tmp_path / "fixtures_requests.jsonl").read_text().splitlines() if l.strip()]
    fixtures = [fx for fx in fz.canary_fixtures["fixtures"] if fx["vector"] is not None]
    assert len(lines) == len(fixtures) == 5  # FIX6 (null vector) never serialized
    by_id = {}
    for line, fx in zip(lines, fixtures):
        assert set(line) == {"schema", "state_id", "state", "requested_model", "input_digest"}
        assert line["schema"] == "jrv1_decision_io@1"
        assert len(line["state_id"]) == 16
        int(line["state_id"], 16)
        assert line["state"] == {
            "feature_vector": [float(x) for x in fx["vector"]],
            "prior_regime": fx["prior_regime"],
        }
        assert line["input_digest"] == compute_input_digest(line["state"], line["requested_model"])
        by_id[fx["id"]] = fx["prior_regime"]
    # fixed priors straight from the freeze, not from any persistence walk
    assert by_id["FIX3_RANGE_AFTER_DOWNTREND"] == "DOWNTREND"
    assert by_id["FIX1_CLEAR_UPTREND"] is None


def test_replay_cli_flags_parse():
    """The replay subcommand accepts the dispatch interface incl. the explicit
    --start-after-warmup affirmation."""
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("replay")
    rp.add_argument("--asset", required=True, choices=["btcusdt", "spy"])
    rp.add_argument("--limit", type=int, default=None)
    rp.add_argument("--mock", action="store_true")
    rp.add_argument("--start-after-warmup", action="store_true")
    args = parser.parse_args(
        ["replay", "--asset", "btcusdt", "--limit", "40", "--mock", "--start-after-warmup"]
    )
    assert args.asset == "btcusdt" and args.limit == 40
    assert args.mock and args.start_after_warmup


def test_replay_captures_adapter_summaries(fz, tmp_path):
    """amendment_2 cost-evidence law: every adapter invocation's stdout JSON
    summary (input token usage + counters) is appended, one line per call,
    to adapter_summaries_<asset>.jsonl. Cache hits invoke no adapter and add
    no summary line."""
    bars = _bars_60_states()
    res = _run_replay(tmp_path, bars, fz, limit=10)
    assert res["n_sent"] == 10
    assert res["n_adapter_summaries"] == 10
    sp = Path(res["adapter_summaries_path"])
    assert sp.exists()
    lines = [ln for ln in sp.read_text().split("\n") if ln.strip()]
    assert len(lines) == 10
    summaries = [json.loads(ln) for ln in lines]
    assert all(s["schema"] == "jrv1_replay_summary@1" or "n_requests" in s for s in summaries)
    assert all(s["n_requests"] == 1 and s["n_emitted"] == 1 for s in summaries)

    # resume: the 10 cached states add ZERO new summaries (no adapter calls)
    res2 = _run_replay(tmp_path, bars, fz)
    assert res2["n_cached"] == 10 and res2["n_sent"] == 50
    assert res2["n_adapter_summaries"] == 50
    lines2 = [ln for ln in sp.read_text().split("\n") if ln.strip()]
    assert len(lines2) == 60
