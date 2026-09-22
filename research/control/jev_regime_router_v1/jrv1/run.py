"""jrv1 runner CLI (S0 research; no external calls from this lane).

Subcommands:
  verify-freezes                     re-verify all 12 freeze digests
  census --asset btcusdt|spy         re-run the data census vs the freeze
  build-states --asset [--limit N]   write runtime/states_<asset>.jsonl
  mock-decisions --asset [--limit N] SMOKE-namespace mock decisions JSONL
  smoke --asset [--limit N]          end-to-end MOCK pipeline (MOCK_SMOKE)
  replay --asset [--limit N] [--mock]
                                     STRICT SEQUENTIAL per-state bulk loop
                                     (A7-1 F2): the ONLY legal bulk decision
                                     mechanism — prior_regime recomputed from
                                     persistence after every merged response,
                                     one TS-adapter subprocess per state,
                                     cache-first resume, progress JSON per
                                     100 states, hard fail on adapter error.
  prepare-requests --asset --fixtures-only
                                     request JSONL for the FROZEN SYNTHETIC
                                     CANARIES only (fixed priors, no
                                     persistence dependency); bulk use is
                                     REFUSED — provisional priors are
                                     unsound (A7-1 F2), use replay instead.
  ingest-responses --asset --file    validate + append decisions JSONL
  backtest --asset --arm A|B|C|D|E|F [--decisions FILE] [--mock] [--cost-mult X]
  report --asset                     json-only summary of available artifacts

All JSON output: sort_keys=True, indent=1. runtime/ artifacts are gitignored.
Smoke/mock artifacts are always labeled namespace=MOCK_SMOKE and live under
runtime/smoke/, runtime/mock/ or runtime/replay/ — they may KILL but never
select (P-15) and are never evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # direct script execution: python .../jrv1/run.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jrv1 import CYCLE_ID  # noqa: E402
from jrv1.arms import (  # noqa: E402
    AssetContext,
    ControlMatchingFailed,
    run_arm_A,
    run_arm_B,
    run_arm_C,
    run_arm_D,
    run_arm_E,
    run_arm_F,
)
from jrv1.data import (  # noqa: E402
    DAY,
    HOUR,
    load_btcusdt,
    load_spy,
)
from jrv1.decisions import (  # noqa: E402
    CacheProvider,
    DecisionStore,
    sequential_timeline,
)
from jrv1.engine import (  # noqa: E402
    CostModel,
    fold_partition_invariants,
    folds_from_regime_ts,
)
from jrv1.features import RegimeFeatures, build_states  # noqa: E402
from jrv1.freezes import Freezes  # noqa: E402
from jrv1.mock_adapter import MOCK_MODEL, MOCK_NAMESPACE, MockProvider  # noqa: E402
from jrv1.replay import REPLAY_MOCK_MODEL, run_replay  # noqa: E402
from jrv1.security import scan_package_source  # noqa: E402

BTC_15M_PERIOD_NS = 15 * 60 * 1_000_000_000
SPY_PERIOD_NS = DAY
PERIODS_PER_YEAR = {"btcusdt": 365.25 * 24 * 4.0, "spy": 252.0}

NODE_BIN = "/opt/homebrew/bin/node" if Path("/opt/homebrew/bin/node").exists() else "node"


def jdump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, indent=1)
        f.write("\n")


def runtime_dir(fz: Freezes) -> Path:
    d = fz.cycle_dir / "runtime"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fold_spans_ns(fz: Freezes, asset: str) -> list[tuple[int, int]]:
    import datetime as dt

    entry = fz.fold_contract[asset.upper() if asset != "spy" else "SPY"]
    spans = []
    for f in entry["folds"]:
        if asset == "btcusdt":
            a = int(dt.datetime.strptime(f["start"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp() * 1_000_000_000)
            b = int(dt.datetime.strptime(f["end"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp() * 1_000_000_000)
        else:
            a = int(dt.datetime.strptime(f["start"], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp() * 1_000_000_000)
            b = int(dt.datetime.strptime(f["end"], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp() * 1_000_000_000)
        spans.append((a, b))
    return spans


def cost_model(fz: Freezes, asset: str, mult: float = 1.0) -> CostModel:
    cc = fz.cost_contract
    if asset == "btcusdt":
        c = cc["BTCUSDT"]
        return CostModel(
            fee_bps=c["taker_fee_bps_per_side"] * mult,
            slip_bps=c["slippage_bps_per_side"] * mult,
            funding_rate=c["funding"]["rate_per_8h_on_signed_notional"],
            label=f"btcusdt_declared_bound_x{mult:g}",
        )
    c = cc["SPY"]
    return CostModel(
        fee_bps=c["cost_bps_per_fill"] * mult,
        slip_bps=0.0,
        funding_rate=0.0,
        label=f"spy_band_A_x{mult:g}",
    )


def load_asset(fz: Freezes, asset: str):
    if asset == "btcusdt":
        exec_bars, regime_bars, census = load_btcusdt(fz)
        period = HOUR
        return exec_bars, regime_bars, period, census
    if asset == "spy":
        exec_bars, dates, checks = load_spy(fz)
        return exec_bars, exec_bars, SPY_PERIOD_NS, checks
    raise SystemExit(f"unknown asset {asset}")


def build_context(fz: Freezes, asset: str, mult: float = 1.0) -> AssetContext:
    exec_bars, regime_bars, period, _ = load_asset(fz, asset)
    asset_key = "BTCUSDT" if asset == "btcusdt" else "SPY"
    raw_mapping = fz.mapping["mapping"]  # {label: {asset: strategy}}
    mapping = {label: m[asset_key] for label, m in raw_mapping.items()}
    spans = fold_spans_ns(fz, asset)
    folds_exec = folds_from_regime_ts(exec_bars, spans)
    # A7-1 F3 partition invariants: contiguous, complete over every exec bar
    # from the first governed (post-warmup) exec bar onward; gaps before
    # warmup excluded. The first post-warmup decision closes at regime bar
    # index `warmup`; every exec bar opening strictly after it must be folded.
    warmup = fz.fold_contract[asset_key]["warmup_regime_bars"]
    first_decision_ts = int(regime_bars.ts_close[warmup])
    first_required = next(
        (
            i
            for i, t in enumerate(exec_bars.ts_open.tolist())
            if t > first_decision_ts
        ),
        len(exec_bars.ts_close),
    )
    fold_partition_invariants(folds_exec, len(exec_bars.ts_close), first_required)
    return AssetContext(
        asset=asset,
        exec_bars=exec_bars,
        regime_period_ns=period,
        mapping=mapping,
        folds_exec=folds_exec,
        costs=cost_model(fz, asset, mult),
        periods_per_year=PERIODS_PER_YEAR[asset],
    )


def timeline_for(fz: Freezes, asset: str, ctx: AssetContext, decisions_file: Path | None, mock: bool, limit: int | None, request_sink=None):
    _, regime_bars, _, _ = load_asset(fz, asset)
    feats = RegimeFeatures(regime_bars)
    pinned = fz.model_pin.get("pinned_model")
    if mock:
        provider = MockProvider()
        model = MOCK_MODEL
        strict = True
    else:
        if decisions_file is None:
            raise SystemExit("arm E/F requires --decisions FILE (or --mock)")
        store = DecisionStore.load(decisions_file)
        provider = CacheProvider(store)
        model = pinned or "UNPINNED"
        strict = not mock
    tl = sequential_timeline(
        asset,
        fz,
        regime_bars,
        feats,
        provider,
        pinned_model=pinned if not mock else None,
        requested_model=model,
        strict=strict,
        request_sink=request_sink,
    )
    if limit is not None:
        tl.rows = tl.rows[:limit]
    return tl


# -- subcommands --------------------------------------------------------------


def cmd_verify_freezes(fz: Freezes, args) -> dict:
    rep = fz.verify()
    scan = scan_package_source()
    mapping_digest = fz.assert_mapping_digest()
    out = {
        "cycle": CYCLE_ID,
        "verified_freezes": rep["verified"],
        "mapping_digest": mapping_digest,
        "security_scan": {"files_scanned": scan["files_scanned"], "findings": scan["findings"]},
        "ok": not scan["findings"],
    }
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_census(fz: Freezes, args) -> dict:
    if args.asset == "btcusdt":
        _, _, census = load_btcusdt(fz)
        out = {"asset": "btcusdt", "census": census, "ok": True}
    else:
        _, dates, checks = load_spy(fz)
        out = {"asset": "spy", "census": checks, "ok": True}
    out["namespace"] = "EVIDENCE_CANDIDATE"
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_build_states(fz: Freezes, args) -> dict:
    exec_bars, regime_bars, _, _ = load_asset(fz, args.asset)
    feats = RegimeFeatures(regime_bars)
    # priors from any existing decision cache (cache-first, non-strict)
    store = DecisionStore.load(runtime_dir(fz) / f"decisions_{args.asset}.jsonl")
    tl = sequential_timeline(
        args.asset, fz, regime_bars, feats, CacheProvider(store),
        requested_model="UNPINNED", strict=False,
    )
    prior_by_index = {r["bar_index"]: r["persisted"] for r in tl.rows}
    prior_labels = [prior_by_index.get(t) for t in range(feats.T)]
    states = build_states(args.asset, fz, regime_bars, prior_labels)
    if args.limit:
        states = states[: args.limit]
    path = runtime_dir(fz) / f"states_{args.asset}.jsonl"
    with open(path, "wb") as f:
        for st in states:
            out = dict(st)
            if out["local_invalid"]:
                out["feature_vector"] = None
            f.write((json.dumps(out, sort_keys=True) + "\n").encode("utf-8"))
    out = {"path": str(path), "n_states": len(states)}
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_mock_decisions(fz: Freezes, args) -> dict:
    exec_bars, regime_bars, _, _ = load_asset(fz, args.asset)
    feats = RegimeFeatures(regime_bars)
    sink: list = []
    tl = sequential_timeline(
        args.asset, fz, regime_bars, feats, MockProvider(),
        requested_model=MOCK_MODEL, strict=True, request_sink=None,
    )
    rows = tl.rows[: args.limit] if args.limit else tl.rows
    path = runtime_dir(fz) / "mock" / f"decisions_{args.asset}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            line = {
                "schema": "jrv1_decision_io@1",
                "state_id": r["state_id"],
                "status": r["status"],
                "namespace": MOCK_NAMESPACE,
            }
            f.write(json.dumps(line, sort_keys=True) + "\n")
    out = {"path": str(path), "n": len(rows), "stats": tl.stats(), "namespace": MOCK_NAMESPACE}
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_smoke(fz: Freezes, args) -> dict:
    ctx = build_context(fz, args.asset)
    _, regime_bars, _, _ = load_asset(fz, args.asset)
    feats = RegimeFeatures(regime_bars)
    tl = sequential_timeline(
        args.asset, fz, regime_bars, feats, MockProvider(),
        requested_model=MOCK_MODEL, strict=True,
    )
    res_e, m_e, targets_e = run_arm_E(ctx, tl)
    res_d, m_d, _ = run_arm_D(ctx, regime_bars, fz.persistence_params())
    canary = run_canaries(fz)
    out = {
        "namespace": MOCK_NAMESPACE,
        "asset": args.asset,
        "timeline_stats": tl.stats(),
        "arm_E": {k: m_e[k] for k in ("net_pnl", "trades", "time_in_market")},
        "arm_D": {k: m_d[k] for k in ("net_pnl", "trades", "time_in_market")},
        "canaries": canary,
        "note": "MOCK_SMOKE: kill-only namespace, never evidence, never scored",
    }
    path = runtime_dir(fz) / "smoke" / args.asset / "smoke_result.json"
    jdump(path, out)
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def run_canaries(fz: Freezes) -> dict:
    from jrv1.mock_adapter import mock_rule

    results = []
    for fx in fz.canary_fixtures["fixtures"]:
        if fx["vector"] is None:
            results.append({"id": fx["id"], "status": "LOCAL_INVALID", "sent": False})
            continue
        label = mock_rule(fx["vector"])
        results.append(
            {
                "id": fx["id"],
                "label": label,
                "acceptable": label in fx["expected_acceptable"],
                "sent": True,
            }
        )
    ok = all(r.get("acceptable", True) for r in results)
    return {"ok": ok, "results": results}


def cmd_prepare_requests(fz: Freezes, args) -> dict:
    # A7-1 F2: batch preparation carries PROVISIONAL priors (f17 depends on
    # prior decisions, which depend on the calls) and is therefore UNSOUND for
    # bulk. The only legal bulk mechanism is the strict sequential loop
    # (`replay`). --fixtures-only serves the frozen synthetic canaries, whose
    # priors are fixed by the freeze (no persistence dependency).
    if not getattr(args, "fixtures_only", False):
        raise SystemExit(
            "REFUSED: batch prepare-requests is not a legal bulk mechanism "
            "(A7-1 F2: prior_regime would be provisional and the fixpoint "
            "re-call is impossible under one-call-per-state cache "
            "immutability). Use `jrv1 replay --asset <asset> [--mock]` for "
            "the strict sequential per-state loop, or pass --fixtures-only "
            "for the frozen synthetic canaries."
        )
    requested_model = fz.model_pin.get("pinned_model") or "UNPINNED"
    from jrv1.replay import fixture_request_lines

    lines = fixture_request_lines(fz, requested_model)
    path = runtime_dir(fz) / "fixtures_requests.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line, sort_keys=True) + "\n")
    out = {
        "path": str(path),
        "n_requests": len(lines),
        "mode": "fixtures_only",
        "note": "synthetic canary fixtures only; fixed priors per freeze; FIX6 (null vector) never serialized",
    }
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_replay(fz: Freezes, args) -> dict:
    """Strict sequential per-state bulk loop (A7-1 F2) through the TS adapter.

    --start-after-warmup is accepted explicitly and is always true: decision
    states exist only from the frozen warmup boundary onward, and replay
    iterates them STRICTLY in order.
    """
    _, regime_bars, _, _ = load_asset(fz, args.asset)
    feats = RegimeFeatures(regime_bars)
    pinned = fz.model_pin.get("pinned_model")
    rt = runtime_dir(fz)
    if args.mock:
        requested_model = REPLAY_MOCK_MODEL
        pinned_model = None
        sub = rt / "mock" / "replay" / args.asset
        namespace = MOCK_NAMESPACE
    else:
        if not pinned:
            raise SystemExit(
                "replay (live) requires a pinned_model in freezes/model_pin.json; "
                "use --mock for mock-namespace validation"
            )
        requested_model = pinned
        pinned_model = pinned
        sub = rt / "replay" / args.asset
        namespace = "EVIDENCE_CANDIDATE"

    def progress(p: dict) -> None:
        print(json.dumps(p, sort_keys=True))

    res = run_replay(
        fz,
        args.asset,
        regime_bars,
        feats,
        requested_model=requested_model,
        pinned_model=pinned_model,
        mock=args.mock,
        decisions_path=sub / f"decisions_{args.asset}.jsonl",
        adapter_cache_dir=sub / "adapter_cache",
        tmp_dir=sub,
        node_bin=NODE_BIN,
        limit=args.limit,
        progress=progress,
    )
    res["namespace"] = namespace
    res["runtime_dir"] = str(sub)
    print(json.dumps(res, sort_keys=True, indent=1))
    return res


def cmd_ingest_responses(fz: Freezes, args) -> dict:
    store = DecisionStore.load(runtime_dir(fz) / f"decisions_{args.asset}.jsonl")
    prior_incidents = len(store.incidents)
    added = 0
    with open(args.file, "rb") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            line = json.loads(raw.decode("utf-8"))
            sid = line.get("state_id")
            if sid in store.by_state_id:
                store.incidents.append({"type": "duplicate_request", "state_id": sid})
                continue
            store.append(runtime_dir(fz) / f"decisions_{args.asset}.jsonl", line)
            added += 1
    out = {
        "added": added,
        "total_cached": len(store.by_state_id),
        "new_incidents": store.incidents[prior_incidents:],
    }
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_backtest(fz: Freezes, args) -> dict:
    mult = args.cost_mult
    ctx = build_context(fz, args.asset, mult)
    fz.assert_mapping_digest()
    arm = args.arm.upper()
    out = {"asset": args.asset, "arm": arm, "cost_multiplier": mult}
    if arm == "A":
        res, m = run_arm_A(ctx)
    elif arm == "B":
        res, m = run_arm_B(ctx)
    elif arm == "C":
        res, m = run_arm_C(ctx)
    elif arm == "D":
        _, regime_bars, _, _ = load_asset(fz, args.asset)
        res, m, _ = run_arm_D(ctx, regime_bars, fz.persistence_params())
    elif arm in ("E", "F"):
        tl = timeline_for(
            fz, args.asset, ctx,
            Path(args.decisions) if args.decisions else None,
            args.mock, None,
        )
        if arm == "E":
            res, m, _ = run_arm_E(ctx, tl)
        else:
            try:
                f = run_arm_F(ctx, tl)
            except ControlMatchingFailed as e:
                out = {
                    "status": "NOT_RUN_CONTROL_MATCHING",
                    "namespace": MOCK_NAMESPACE if args.mock else "EVIDENCE_CANDIDATE",
                    "asset": args.asset,
                    "arm": "F",
                    "payload": e.payload,
                    "note": "fail-closed per controls contract: measured deltas disclosed",
                }
                sub = "mock" if args.mock else "decisions"
                path = runtime_dir(fz) / sub / f"backtest_{args.asset}_F.json"
                jdump(path, out)
                print(json.dumps(out, sort_keys=True, indent=1))
                return out
            out["arm_F"] = {
                k: f[k] for k in ("headline_seed", "median_net_pnl", "null_invalid_flag")
            }
            out["arm_F_seeds"] = [
                {"seed": s["seed"], "net_pnl": s["net_pnl"], "q11_moved": s["q11_moved"]}
                for s in f["seeds"]
            ]
            m = f["seeds"][[s["seed"] for s in f["seeds"]].index(f["headline_seed"])]["metrics"]
    else:
        raise SystemExit(f"unknown arm {arm}")
    out["metrics"] = m
    out["namespace"] = MOCK_NAMESPACE if args.mock else "EVIDENCE_CANDIDATE"
    sub = "mock" if args.mock else "decisions"
    path = runtime_dir(fz) / sub / f"backtest_{args.asset}_{arm}.json"
    jdump(path, out)
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def cmd_report(fz: Freezes, args) -> dict:
    out = {
        "asset": args.asset,
        "note": "json-only at this phase; markdown reports come at the scored phase",
        "runtime_files": sorted(
            p.name for p in (fz.cycle_dir / "runtime").rglob("*.json*")
        ),
    }
    print(json.dumps(out, sort_keys=True, indent=1))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="jrv1.run")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("verify-freezes")

    c = sub.add_parser("census")
    c.add_argument("--asset", required=True, choices=["btcusdt", "spy"])

    b = sub.add_parser("build-states")
    b.add_argument("--asset", required=True, choices=["btcusdt", "spy"])
    b.add_argument("--limit", type=int, default=None)

    m = sub.add_parser("mock-decisions")
    m.add_argument("--asset", required=True, choices=["btcusdt", "spy"])
    m.add_argument("--limit", type=int, default=None)

    s = sub.add_parser("smoke")
    s.add_argument("--asset", required=True, choices=["btcusdt", "spy"])
    s.add_argument("--mock", action="store_true", default=True)
    s.add_argument("--limit", type=int, default=None)

    pr = sub.add_parser("prepare-requests")
    pr.add_argument("--asset", required=True, choices=["btcusdt", "spy"])
    pr.add_argument("--limit", type=int, default=None)
    pr.add_argument(
        "--fixtures-only",
        action="store_true",
        help="emit request lines for the frozen synthetic canaries only "
        "(fixed priors, no persistence dependency); bulk use is refused",
    )

    ir = sub.add_parser("ingest-responses")
    ir.add_argument("--asset", required=True, choices=["btcusdt", "spy"])
    ir.add_argument("--file", required=True)

    rp2 = sub.add_parser(
        "replay",
        help="strict sequential per-state bulk loop through the TS adapter (A7-1 F2)",
    )
    rp2.add_argument("--asset", required=True, choices=["btcusdt", "spy"])
    rp2.add_argument("--limit", type=int, default=None)
    rp2.add_argument("--mock", action="store_true")
    rp2.add_argument(
        "--start-after-warmup",
        action="store_true",
        help="explicit affirmation (always true): replay iterates decision "
        "states strictly in order starting at the first post-warmup state",
    )

    bt = sub.add_parser("backtest")
    bt.add_argument("--asset", required=True, choices=["btcusdt", "spy"])
    bt.add_argument("--arm", required=True, choices=["A", "B", "C", "D", "E", "F"])
    bt.add_argument("--decisions", default=None)
    bt.add_argument("--mock", action="store_true")
    bt.add_argument("--cost-mult", type=float, default=1.0)

    rp = sub.add_parser("report")
    rp.add_argument("--asset", required=True, choices=["btcusdt", "spy"])

    args = p.parse_args(argv)
    fz = Freezes(_default_cycle_dir())
    fn = {
        "verify-freezes": cmd_verify_freezes,
        "census": cmd_census,
        "build-states": cmd_build_states,
        "mock-decisions": cmd_mock_decisions,
        "smoke": cmd_smoke,
        "prepare-requests": cmd_prepare_requests,
        "ingest-responses": cmd_ingest_responses,
        "replay": cmd_replay,
        "backtest": cmd_backtest,
        "report": cmd_report,
    }[args.cmd]
    fn(fz, args)
    return 0


def _default_cycle_dir():
    from jrv1.freezes import default_cycle_dir

    return default_cycle_dir()


if __name__ == "__main__":
    raise SystemExit(main())
