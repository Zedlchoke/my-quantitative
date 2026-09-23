"""jrv2 runner CLI (S0 research; NO external calls from this lane).

Subcommands:
  verify-freezes                     re-verify all 10 freeze digests + scans
  census [--cell]                    re-run the data census vs the freeze
                                     (BTC H1 + H4 + SPY)
  build-states --cell [--limit N]    write runtime/states_<cell>.jsonl (named
                                     semantic states)
  mock-decisions --cell [--limit N]  MOCK-namespace deterministic decisions
  canary-synthetic [--mock|--live]   frozen synthetic canaries + acceptance
                                     (plumbing in this lane; LIVE refusi
                                     without a pinned model)
  preview [--mock|--live]            canary historical preview (100 BTC_H1
                                     states, classification-only, collapse
                                     check FAIL-STOPS with numbers)
  prepare-fixtures                   request JSONL for the frozen SYNTHETIC
                                     canaries only (fixed priors)
  replay --cell [--limit N] [--mock] STRICT SEQUENTIAL per-state loop (the
                                     only legal bulk mechanism); prior fields
                                     recomputed from persistence after every
                                     merged response; cache-first resume
  backtest                           QUARANTINED: refuses real-data arm
                                     backtests until the scored-phase GO
                                     token authority exists (see below)
  report                             json-only summary of runtime artifacts

BACKTEST QUARANTINE LAW (owner, this lane): NO arm backtest is executed on
real data in this lane. The backtest subcommand refuses UNLESS a
--scored-go-token is presented AND a scored-phase GO authority file
(SCORED_GO.json in the cycle dir, registered by the owner at STOP-2) exists
and pins the token's sha256. Neither exists yet -> the command ALWAYS
refuses today (fail-closed), including in mock mode for real data.

Runtime artifacts are namespaced: mock runs under runtime/mock/, replay
under runtime/replay/ (live) or runtime/mock/replay/ (mock). Mock artifacts
are namespace=MOCK — they may KILL but never select (P-15) and are never
evidence.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # direct script execution: python .../jrv2/run.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jrv2 import CELLS, CYCLE_ID  # noqa: E402
from jrv2.arms import (  # noqa: E402
    AssetContext,
    ControlMatchingFailed,
    run_always_on_mr,
    run_always_on_trend,
    run_buy_hold,
    run_confirmation_arm,
    run_deterministic_router,
    run_jev_only_router,
    run_random_matched,
)
from jrv2.canary import run_canary_synthetic  # noqa: E402
from jrv2.data import DAY, HOUR, load_btcusdt, load_cell, load_spy  # noqa: E402
from jrv2.engine import CostModel, fold_partition_invariants, folds_from_regime_ts  # noqa: E402
from jrv2.features import RegimeFeatures, semantic_state, state_payload  # noqa: E402
from jrv2.freezes import Freezes  # noqa: E402
from jrv2.mock_adapter import (  # noqa: E402
    MOCK_MODEL,
    MOCK_NAMESPACE,
    MockProvider,
    REPLAY_MOCK_MODEL,
)
from jrv2.questionio import (  # noqa: E402
    CacheProvider,
    DecisionStore,
    sequential_timeline,
)
from jrv2.replay import PreviewCollapse, run_preview, run_replay  # noqa: E402
from jrv2.security import scan_package_source, scan_v1_references  # noqa: E402

SPY_PERIOD_NS = DAY
PERIODS_PER_YEAR = {"BTC_H1": 365.25 * 24, "BTC_H4": 365.25 * 6, "SPY_D1": 252.0}

NODE_BIN = "/opt/homebrew/bin/node" if Path("/opt/homebrew/bin/node").exists() else "node"

SCORED_GO_AUTHORITY = "SCORED_GO.json"  # owner-registered at STOP-2; does not exist


def jdump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, indent=1)
        f.write("\n")


def runtime_dir(fz: Freezes) -> Path:
    d = fz.cycle_dir / "runtime"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fold_spans_ns(fz: Freezes, cell: str) -> list[tuple[int, int]]:
    entry = fz.fold_contract["cells"][cell]
    spans = []
    for f in entry["folds"]:
        if cell.startswith("BTC"):
            a = _iso_utc(f["start"])
            b = _iso_utc(f["end"])
        else:
            a = _date_utc(f["start"])
            b = _date_utc(f["end"])
        spans.append((a, b))
    return spans


def _iso_utc(s: str) -> int:
    return int(
        dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
        .replace(tzinfo=dt.timezone.utc)
        .timestamp()
        * 1_000_000_000
    )


def _date_utc(s: str) -> int:
    return int(
        dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()
        * 1_000_000_000
    )


def cost_model(fz: Freezes, asset: str, mult: float = 1.0) -> CostModel:
    c = fz.mapping["costs"]["BTCUSDT" if asset == "btcusdt" else "SPY"]
    if asset == "btcusdt":
        return CostModel(
            fee_bps=c["taker_fee_bps_per_side"] * mult,
            slip_bps=c["slippage_bps_per_side"] * mult,
            funding_rate=c["funding_per_8h_signed"],
            label=f"btcusdt_declared_bound_x{mult:g}",
        )
    return CostModel(
        fee_bps=c["cost_bps_per_fill"] * mult,
        slip_bps=0.0,
        funding_rate=0.0,
        label=f"spy_band_A_x{mult:g}",
    )


def build_context(fz: Freezes, cell: str, mult: float = 1.0) -> AssetContext:
    exec_bars, regime_bars, period = load_cell(fz, cell)
    asset = CELLS[cell]["asset"]
    asset_key = "BTCUSDT" if asset == "btcusdt" else "SPY"
    raw_mapping = fz.mapping["mapping"]
    mapping = {label: m[asset_key] for label, m in raw_mapping.items()}
    spans = fold_spans_ns(fz, cell)
    folds_exec = folds_from_regime_ts(exec_bars, spans)
    warmup = fz.warmup(cell)
    first_decision_ts = int(regime_bars.ts_close[warmup])
    first_required = next(
        (i for i, t in enumerate(exec_bars.ts_open.tolist()) if t > first_decision_ts),
        len(exec_bars.ts_close),
    )
    fold_partition_invariants(folds_exec, len(exec_bars.ts_close), first_required)
    return AssetContext(
        asset=asset,
        cell=cell,
        exec_bars=exec_bars,
        regime_period_ns=period,
        mapping=mapping,
        folds_exec=folds_exec,
        costs=cost_model(fz, asset, mult),
        periods_per_year=PERIODS_PER_YEAR[cell],
    )


# -- subcommands --------------------------------------------------------------


def cmd_verify_freezes(fz: Freezes, args) -> dict:
    rep = fz.verify()
    scan = scan_package_source()
    v1scan = scan_v1_references()
    mapping_digest = fz.assert_mapping_digest()
    out = {
        "cycle": CYCLE_ID,
        "verified_freezes": rep["verified"],
        "n_freezes": len(rep["verified"]),
        "mapping_digest": mapping_digest,
        "security_scan": {"files_scanned": scan["files_scanned"], "findings": scan["findings"]},
        "v1_isolation_scan": {"files_scanned": v1scan["files_scanned"], "findings": v1scan["findings"]},
        "ok": not scan["findings"] and not v1scan["findings"],
    }
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_census(fz: Freezes, args) -> dict:
    _, _, _, census = load_btcusdt(fz)
    _, dates, spy_checks = load_spy(fz)
    ident = fz.data_identity
    out = {
        "cycle": CYCLE_ID,
        "cells": {
            "BTC_H1": {
                "complete_h1": census["h1"]["complete"],
                "freeze_h1": ident["BTCUSDT"]["h1_census"]["complete"],
                "partial": census["h1"]["partial"],
                "interior_gaps": census["h1"]["interior_gaps"],
            },
            "BTC_H4": {
                "complete_h4": census["h4"]["complete"],
                "freeze_h4": ident["BTCUSDT"]["h4_census"]["complete"],
                "partial": census["h4"]["partial"],
                "interior_gaps": census["h4"]["interior_gaps"],
                "law": ident["BTCUSDT"]["h4_census"]["law"],
            },
            "SPY_D1": {
                "sessions": spy_checks["checks"]["records"],
                "first": spy_checks["checks"]["first_session"],
                "last": spy_checks["checks"]["last_session"],
            },
        },
        "rows_btc": census["rows"],
        "ok": True,
        "namespace": "EVIDENCE_CANDIDATE",
    }
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def _persistence_labels_for_states(fz, cell, regime_bars, feats, store, requested_model):
    """Cache-first persisted labels per regime-bar index (non-strict)."""
    from jrv2.safety import PersistenceState, effective_from_response, step

    params = fz.persistence_params()
    st = PersistenceState(**params)
    pinned = fz.model_pin.get("pinned_model")
    labels: list[str | None] = [None] * feats.T
    asset = CELLS[cell]["asset"]
    from jrv2.questionio import compute_input_digest, validate_response_line
    from jrv2.features import state_payload as _sp

    for t in range(fz.warmup(cell), feats.T):
        ts_close = int(regime_bars.ts_close[t])
        sid = fz.state_id(asset, ts_close)
        state = semantic_state(asset, fz, regime_bars, t, feats, labels[t - 1] if t > 0 else None)
        if state is None:
            labels[t] = st.current
            continue
        payload = _sp(state)
        digest = compute_input_digest(payload, requested_model)
        line = store.by_state_id.get(sid)
        if line is not None:
            normalized, _v = validate_response_line(line, sid, digest, pinned)
        else:
            normalized = None
        label, eligible, _r = effective_from_response(normalized, params)
        step(st, label, eligible)
        labels[t] = st.current
    return labels


def cmd_build_states(fz: Freezes, args) -> dict:
    exec_bars, regime_bars, _, _ = _load_cell_full(fz, args.cell)
    feats = RegimeFeatures(regime_bars)
    store = DecisionStore.load(runtime_dir(fz) / f"decisions_{args.cell}.jsonl")
    asset = CELLS[args.cell]["asset"]
    requested = fz.model_pin.get("pinned_model") or "UNPINNED"
    prior_by_index = _persistence_labels_for_states(fz, args.cell, regime_bars, feats, store, requested)
    states = []
    for t in range(fz.warmup(args.cell), feats.T):
        st = semantic_state(asset, fz, regime_bars, t, feats, prior_by_index[t - 1] if t > 0 else None)
        if st is None:
            states.append(
                {
                    "state_id": fz.state_id(asset, int(regime_bars.ts_close[t])),
                    "regime_bar_close_ns": int(regime_bars.ts_close[t]),
                    "bar_index": int(t),
                    "local_invalid": True,
                }
            )
            continue
        states.append(
            {
                "state_id": fz.state_id(asset, int(regime_bars.ts_close[t])),
                "regime_bar_close_ns": int(regime_bars.ts_close[t]),
                "bar_index": int(t),
                "state": state_payload(st),
                "local_invalid": False,
            }
        )
    if args.limit:
        states = states[: args.limit]
    path = runtime_dir(fz) / f"states_{args.cell}.jsonl"
    with open(path, "wb") as f:
        for st in states:
            f.write((json.dumps(st, sort_keys=True) + "\n").encode("utf-8"))
    out = {"path": str(path), "cell": args.cell, "n_states": len(states)}
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_mock_decisions(fz: Freezes, args) -> dict:
    _, regime_bars, _, _ = _load_cell_full(fz, args.cell)
    feats = RegimeFeatures(regime_bars)
    tl = sequential_timeline(
        args.cell, fz, regime_bars, feats, MockProvider(),
        requested_model=MOCK_MODEL, strict=True,
    )
    rows = tl.rows[: args.limit] if args.limit else tl.rows
    path = runtime_dir(fz) / "mock" / f"decisions_{args.cell}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            line = {
                "schema": "jrv2_question_io@1",
                "state_id": r["state_id"],
                "status": r["status"],
                "effective": r["effective"],
                "namespace": MOCK_NAMESPACE,
            }
            f.write(json.dumps(line, sort_keys=True) + "\n")
    out = {"path": str(path), "cell": args.cell, "n": len(rows), "stats": tl.stats(),
           "namespace": MOCK_NAMESPACE}
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def _load_cell_full(fz, cell):
    """(exec_bars, regime_bars, period, None) for a cell."""
    if CELLS[cell]["asset"] == "btcusdt":
        exec_bars, h1, h4, _ = load_btcusdt(fz)
        regime = h1 if CELLS[cell]["regime_clock"] == "H1" else h4
        return exec_bars, regime, HOUR if CELLS[cell]["regime_clock"] == "H1" else 4 * HOUR, None
    exec_bars, _, _ = load_spy(fz)
    return exec_bars, exec_bars, SPY_PERIOD_NS, None


def cmd_canary_synthetic(fz: Freezes, args) -> dict:
    if args.live:
        pinned = fz.model_pin.get("pinned_model")
        if not pinned:
            raise SystemExit(
                "canary-synthetic --live requires a pinned_model in "
                "freezes/model_pin.json (re-probed + re-frozen at G0); "
                "this lane is MOCK-ONLY"
            )
        requested_model, pinned_model = pinned, pinned
        live = True
    else:
        requested_model, pinned_model = MOCK_MODEL, None
        live = False
    from jrv2.canary import run_canary_synthetic

    result = run_canary_synthetic(
        fz, MockProvider(requested_model) if not live else _LiveProvider(fz, requested_model),
        requested_model, pinned_model, mock=not live,
    )
    sub = "mock" if not live else "live"
    path = runtime_dir(fz) / sub / "canary_synthetic_result.json"
    jdump(path, result)
    result["result_path"] = str(path)
    compact = {k: result[k] for k in ("schema", "namespace", "ok", "measured")}
    compact["checks"] = [
        {"criterion": c["criterion"], "pass": c["pass"], "measured": c["measured"]}
        for c in result["checks"]
    ]
    print(json.dumps(compact, sort_keys=True, indent=1))
    if not result["ok"]:
        return result
    return result


class _LiveProvider:  # A1 integration commit (post-lane, pin frozen at G0)
    """Live provider = one TS-adapter subprocess per state (same discipline as
    the sequential replay loop: maxRetries 0, cache-first via the adapter's own
    append-only cache, adapter summary JSON preserved as cost evidence)."""

    def __init__(self, fz, requested_model: str) -> None:
        import json as _json  # noqa: F401
        self.model = requested_model
        rt = runtime_dir(fz)
        self.cache = rt / "live" / "canary_cache"
        self.tmp = rt / "live" / "canary_tmp"
        for d in (self.cache, self.tmp):
            d.mkdir(parents=True, exist_ok=True)
        self.adapter_ts = fz.cycle_dir / "adapter" / "src" / "adapter.ts"
        self.summaries = rt / "live" / "canary_adapter_summaries.jsonl"

    def __call__(self, sid: str, state: dict) -> dict:
        import json as _json

        from .questionio import QUESTION_IO_SCHEMA, build_request_line
        from .replay import _invoke_adapter, safe_open

        line = build_request_line(sid, state, self.model)
        req = self.tmp / "req_1line.jsonl"
        out = self.tmp / "resp_1line.jsonl"
        with safe_open(req, "w") as f:
            f.write(_json.dumps(line, sort_keys=True) + "\n")
        if out.exists():
            out.unlink()
        stdout = _invoke_adapter(
            NODE_BIN, self.adapter_ts, req, out, self.cache, False, self.model
        )
        s = (stdout or "").strip()
        if s:
            with safe_open(self.summaries, "a") as f:
                f.write(s.split("\n")[0].strip() + "\n")
        rows = [ln for ln in out.read_text().split("\n") if ln.strip()]
        if len(rows) != 1:
            return {
                "schema": QUESTION_IO_SCHEMA,
                "state_id": sid,
                "status": "PROVIDER_ERROR",
                "error_class": "BAD_ADAPTER_OUTPUT",
                "answers": None,
                "model": None,
                "request_id": None,
                "usage": None,
                "input_digest": line["input_digest"],
                "prior_direction": state.get("prior_direction"),
                "latency_ms": 0.0,
            }
        return _json.loads(rows[0])


def cmd_preview(fz: Freezes, args) -> dict:
    cell = "BTC_H1"
    _, regime_bars, _, _ = _load_cell_full(fz, cell)
    feats = RegimeFeatures(regime_bars)
    rt = runtime_dir(fz)
    if args.mock:
        requested_model, pinned_model = REPLAY_MOCK_MODEL, None
        sub = rt / "mock" / "preview" / cell
        namespace = MOCK_NAMESPACE
    else:
        pinned = fz.model_pin.get("pinned_model")
        if not pinned:
            raise SystemExit(
                "preview (live) requires a pinned_model in freezes/model_pin.json "
                "(G0 re-probe + re-freeze); this lane is MOCK-ONLY"
            )
        requested_model, pinned_model = pinned, pinned
        sub = rt / "preview" / cell
        namespace = "EVIDENCE_CANDIDATE"
    try:
        res = run_preview(
            fz, regime_bars, feats, requested_model, pinned_model, args.mock,
            decisions_path=sub / f"decisions_{cell}.jsonl",
            adapter_cache_dir=sub / "adapter_cache",
            tmp_dir=sub,
            node_bin=NODE_BIN,
        )
    except PreviewCollapse as e:
        out = dict(e.payload)
        out["namespace"] = namespace
        out["STOP"] = (
            "COLLAPSE_CRITERIA_FIRED: STOP, no bulk, no prompt rescue beyond the "
            "preregistered revision budget"
        )
        path = sub / "preview_result_COLLAPSE.json"
        jdump(path, out)
        print(json.dumps({k: out[k] for k in ("schema", "collapsed", "collapse_checks",
                                              "effective_label_shares", "STOP")}, indent=1))
        return out
    res["namespace"] = namespace
    path = sub / "preview_result.json"
    jdump(path, res)
    compact = {k: res[k] for k in ("schema", "cell", "n_sampled", "effective_label_counts",
                                   "effective_label_shares", "usage_totals", "collapse_checks",
                                   "collapsed")}
    compact["namespace"] = namespace
    print(json.dumps(compact, sort_keys=True, indent=1))
    return res


def cmd_prepare_fixtures(fz: Freezes, args) -> dict:
    requested_model = fz.model_pin.get("pinned_model") or ("mock-pin-2" if args.mock else "UNPINNED")
    from jrv2.replay import fixture_request_lines

    lines = fixture_request_lines(fz, requested_model)
    path = runtime_dir(fz) / ("mock" if args.mock else "") / "fixtures_requests.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line, sort_keys=True) + "\n")
    out = {
        "path": str(path),
        "n_requests": len(lines),
        "mode": "fixtures_only",
        "note": "synthetic canary fixtures only; fixed priors per freeze; "
        "C8 (null state) never serialized",
    }
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_replay(fz: Freezes, args) -> dict:
    _, regime_bars, _, _ = _load_cell_full(fz, args.cell)
    feats = RegimeFeatures(regime_bars)
    rt = runtime_dir(fz)
    if args.mock:
        requested_model, pinned_model = REPLAY_MOCK_MODEL, None
        sub = rt / "mock" / "replay" / args.cell
        namespace = MOCK_NAMESPACE
    else:
        pinned = fz.model_pin.get("pinned_model")
        if not pinned:
            raise SystemExit(
                "replay (live) requires a pinned_model in freezes/model_pin.json "
                "(G0 re-probe + re-freeze); use --mock for mock-namespace validation"
            )
        requested_model, pinned_model = pinned, pinned
        sub = rt / "replay" / args.cell
        namespace = "EVIDENCE_CANDIDATE"

    def progress(p: dict) -> None:
        print(json.dumps(p, sort_keys=True))

    res = run_replay(
        fz, args.cell, regime_bars, feats,
        requested_model=requested_model,
        pinned_model=pinned_model,
        mock=args.mock,
        decisions_path=sub / f"decisions_{args.cell}.jsonl",
        adapter_cache_dir=sub / "adapter_cache",
        tmp_dir=sub,
        node_bin=NODE_BIN,
        limit=args.limit,
        progress=progress,
    )
    res["namespace"] = namespace
    res["runtime_dir"] = str(sub)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, sort_keys=True, indent=1))
    return res


def cmd_backtest(fz: Freezes, args) -> dict:
    """QUARANTINED — refuses real-data arm backtests in this lane.

    Fail-closed: requires --scored-go-token AND an owner-registered
    SCORED_GO.json authority pinning the token's sha256. The authority file
    does not exist yet, so the command refuses unconditionally today.
    """
    authority = fz.cycle_dir / SCORED_GO_AUTHORITY
    reason = None
    if not authority.exists():
        reason = (
            f"no scored-phase GO authority file {SCORED_GO_AUTHORITY} "
            "(registered by the owner at STOP-2 V2); the token does not exist yet"
        )
    else:
        import json as _json

        rec = _json.loads(authority.read_text())
        want = rec.get("scored_go_token_sha256")
        got = hashlib.sha256((args.scored_go_token or "").encode()).hexdigest()
        if not want or got != want:
            reason = "scored-go-token does not match the registered GO authority"
    if reason is not None:
        out = {
            "status": "REFUSED_BACKTEST_QUARANTINE",
            "cycle": CYCLE_ID,
            "reason": reason,
            "law": "NO arm backtest on real data until the scored-phase GO "
            "authority exists and the token matches (STOP-2 V2)",
        }
        if args.force_show_metrics:
            out["note"] = "--force-show-metrics cannot bypass the quarantine"
        print(json.dumps(out, sort_keys=True, indent=1))
        raise SystemExit(20)

    # scored-phase GO authority valid: run the 18 frozen cells atomically
    if args.cell or args.arm:
        print(json.dumps({
            "status": "REFUSED_BACKTEST_QUARANTINE",
            "reason": "the scored phase runs ALL cells x arms in ONE atomic run; per-cell/per-arm invocation is not the frozen path",
        }, sort_keys=True))
        raise SystemExit(20)
    from .scored import run_scored, ARMS, TIERS  # noqa: F401

    cells = ["BTC_H1", "BTC_H4", "SPY_D1"]
    out_root = runtime_dir(fz) / "scored"
    summary = run_scored(fz, cells, out_root)
    return summary


def cmd_report(fz: Freezes, args) -> dict:
    rt = runtime_dir(fz)
    out = {
        "cycle": CYCLE_ID,
        "note": "json-only at this phase; markdown reports come at the scored phase",
        "runtime_files": sorted(p.name for p in rt.rglob("*.json*")) if rt.exists() else [],
    }
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="jrv2.run")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("verify-freezes")

    c = sub.add_parser("census")
    c.add_argument("--cell", default=None, choices=list(CELLS) + [None])

    b = sub.add_parser("build-states")
    b.add_argument("--cell", required=True, choices=list(CELLS))
    b.add_argument("--limit", type=int, default=None)

    m = sub.add_parser("mock-decisions")
    m.add_argument("--cell", required=True, choices=list(CELLS))
    m.add_argument("--limit", type=int, default=None)

    cs = sub.add_parser("canary-synthetic")
    cs.add_argument("--mock", action="store_true", default=False)
    cs.add_argument("--live", action="store_true", default=False)

    pv = sub.add_parser("preview")
    pv.add_argument("--mock", action="store_true", default=False)
    pv.add_argument("--live", action="store_true", default=False)

    pf = sub.add_parser("prepare-fixtures")
    pf.add_argument("--mock", action="store_true", default=False)

    rp = sub.add_parser("replay")
    rp.add_argument("--cell", required=True, choices=list(CELLS))
    rp.add_argument("--limit", type=int, default=None)
    rp.add_argument("--mock", action="store_true")

    bt = sub.add_parser("backtest")
    bt.add_argument("--cell", default=None, choices=list(CELLS) + [None])
    bt.add_argument("--arm", default=None)
    bt.add_argument("--scored-go-token", default=None)
    bt.add_argument("--force-show-metrics", action="store_true", default=False)

    rep = sub.add_parser("report")

    args = p.parse_args(argv)
    fz = Freezes(_default_cycle_dir())
    fn = {
        "verify-freezes": cmd_verify_freezes,
        "census": cmd_census,
        "build-states": cmd_build_states,
        "mock-decisions": cmd_mock_decisions,
        "canary-synthetic": cmd_canary_synthetic,
        "preview": cmd_preview,
        "prepare-fixtures": cmd_prepare_fixtures,
        "replay": cmd_replay,
        "backtest": cmd_backtest,
        "report": cmd_report,
    }[args.cmd]
    fn(fz, args)
    return 0


def _default_cycle_dir():
    from jrv2.freezes import default_cycle_dir

    return default_cycle_dir()


if __name__ == "__main__":
    raise SystemExit(main())
