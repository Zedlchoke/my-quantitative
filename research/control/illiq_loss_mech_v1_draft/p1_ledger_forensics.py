#!/usr/bin/env python
"""P1 ledger-level forensics for the FUNDED S0R ILLIQ baseline (ILLIQ-LOSS-MECH-V1 draft).

READ-ONLY on all evidence trees; the only writes are inside this namespace
(research/control/illiq_loss_mech_v1_draft/). No scored cell, no engine
mutation, no heavy lock needed (artifact aggregation only, precedent:
illiq_reg_gate_v1_draft/forensic_compute.py).

Inputs:
  CHR3F illiq_diag/S0R-ANCHOR-A5-funded/results/artifact.json  (primary ledger, funded)
  CHR3F illiq_diag/S0R-ANCHOR-A5/results/artifact.json         (no-funding B2 twin)
  CHR3F illiq_scored_out/*/results/artifact.json               (4 funded cells)
  CHR3F illiq_scored_summary.json                              (headline claims)
  catalog b20 + s0r first-bar timestamps                        (listing-age proxy)

Outputs: p1_forensics.json in this namespace + stdout summary.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

NS = Path("/Users/hoangminhlong/my-quantitative/research/control/illiq_loss_mech_v1_draft")
CHR3F = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1")
V11ROOT = CHR3F / "recovered" / "v11_root"

ART_FUNDED = CHR3F / "illiq_diag/S0R-ANCHOR-A5-funded/results/artifact.json"
ART_NOFUND = CHR3F / "illiq_diag/S0R-ANCHOR-A5/results/artifact.json"
SCORED_OUT = CHR3F / "illiq_scored_out"
SCORED_SUM = CHR3F / "illiq_scored_summary.json"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def payload_sha256(payload) -> str:
    """Byte-stable hash replicating research.adapter_v10.hashes.payload_sha256
    (canonical_repr: json.dumps sorted keys, compact, floats via repr)."""
    def to_canon(obj):
        import math
        from collections.abc import Mapping as _M
        if isinstance(obj, _M):
            return {str(k): to_canon(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [to_canon(v) for v in obj]
        if obj is None or isinstance(obj, (bool, int, str)):
            return obj
        if isinstance(obj, float):
            if obj != obj or obj in (float("inf"), float("-inf")):
                raise ValueError("non-finite float")
            return repr(obj)
        raise TypeError(f"cannot serialize {type(obj)!r}")
    text = json.dumps(to_canon(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).strftime("%Y-%m-%d")


def r6(x):
    return round(float(x), 6)


def main() -> int:
    out: dict = {"namespace": str(NS), "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    art = json.load(open(ART_FUNDED))
    pm = art["portfolio_metrics"]
    out["artifact_identity"] = {
        "path": str(ART_FUNDED),
        "file_sha256": file_sha256(ART_FUNDED),
        "result_sha256_recorded": art["hashes"]["result_sha256"],
        "scored": art["scored"],
        "window_first_decision": iso(art["schedule"]["first_decision_ns"]),
        "window_last_decision": iso(art["schedule"]["last_decision_ns"]),
        "n_stamps": art["schedule"]["n_instants"],
        "universe_n": len(art["universe"]),
        "engine_config": art["identity"]["config"],
        "metadata_window_caveat": "identity.window_*_iso carries frozen template values; real window from schedule.*_decision_ns (A7-r5 N6)",
    }

    # ---- 1. byte/ledger-level reproduction --------------------------------
    strip = lambda d, keys: {k: v for k, v in d.items() if k not in keys}
    recomputed = {
        "positions_sha256": payload_sha256(art["positions"]),
        "portfolio_payload_sha256": payload_sha256(art["portfolio_payload"]),
        "benchmarks_sha256": payload_sha256(art["benchmarks"]),
        "fold_metrics_sha256": payload_sha256(art["fold_metrics"]),
        "result_sha256": payload_sha256(strip(strip(art, ("hashes", "artifacts")), ())),
    }
    hash_checks = {}
    for k, v in recomputed.items():
        want = art["hashes"].get(k)
        hash_checks[k] = {"recomputed": v[:16], "recorded": (want or "")[:16], "match": (v == want)}
    out["hash_checks"] = hash_checks

    pos = art["positions"]
    sums = {
        "price": sum(p["price_pnl_per_unit"] for p in pos),
        "funding": sum(p["funding_cashflow_per_unit"] for p in pos),
        "cost": sum(p["cost_allocated_per_unit"] for p in pos),
        "net": sum(p["net_pnl_per_unit"] for p in pos),
    }
    ledger_recon = {
        "n_positions": len(pos),
        "ledger_sums": {k: r6(v) for k, v in sums.items()},
        "portfolio_metrics": {
            "price_pnl_sum": r6(pm["price_pnl_sum"]),
            "funding_sum": r6(pm["funding_sum"]),
            "cost_charged_sum": r6(pm["cost_charged_sum"]),
            "net_return_sum": r6(pm["net_return_sum"]),
        },
        "abs_diff": {
            "price": abs(sums["price"] - pm["price_pnl_sum"]),
            "funding": abs(sums["funding"] - pm["funding_sum"]),
            "cost": abs(sums["cost"] - pm["cost_charged_sum"]),
            "net": abs(sums["net"] - pm["net_return_sum"]),
            "identity_price+funding-cost=net": abs(sums["price"] + sums["funding"] - sums["cost"] - sums["net"]),
        },
    }
    ledger_recon["all_match_1e_9"] = all(v < 1e-9 for v in ledger_recon["abs_diff"].values())
    # MDD recompute (engine law: additive peak-to-trough on cumsum of boundary returns)
    rows = art["portfolio_payload"]["rows"]
    drs = art["daily_returns"]
    bret = [d["net_return_per_unit"] for d in drs]
    dec = [d["decision_ns"] for d in drs]
    eq, peak, mdd = 0.0, 0.0, 0.0
    for x in bret:
        eq += x
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
    ledger_recon["mdd_recomputed_additive"] = r6(mdd)
    ledger_recon["mdd_recorded"] = r6(pm["max_drawdown"])
    ledger_recon["mdd_match_1e_6"] = abs(mdd - pm["max_drawdown"]) < 1e-6
    out["ledger_reconciliation"] = ledger_recon

    # headline reconcile vs scored summary + registry claims
    summary = json.load(open(SCORED_SUM))
    claims = {"CHR3F-ILLIQ-S0R-ANCHOR": -0.563057513256, "CHR3F-ILLIQ-S0R-INV": 0.545920601572,
              "CHR3F-ILLIQ-Y2024P-ANCHOR": 0.137736325744, "CHR3F-ILLIQ-Y2024P-INV": -0.150149588578}
    cell_checks = {}
    for cell in summary:
        want = claims[cell["cell"]]
        cell_checks[cell["cell"]] = {
            "summary_net": r6(cell["net"]), "claim_net": r6(want),
            "match": abs(cell["net"] - want) < 1e-9,
            "artifact_sha256_16": file_sha256(SCORED_OUT / cell["cell"] / "results/artifact.json")[:16],
        }
    out["headline_claims_reconcile"] = cell_checks

    # no-funding B2 twin delta
    a2 = json.load(open(ART_NOFUND))
    out["funding_wiring_delta"] = {
        "nofund_net": r6(a2["portfolio_metrics"]["net_return_sum"]),
        "funded_net": r6(pm["net_return_sum"]),
        "delta_pts": r6((pm["net_return_sum"] - a2["portfolio_metrics"]["net_return_sum"]) * 100),
        "nofund_funding_sum": r6(a2["portfolio_metrics"]["funding_sum"]),
    }

    # ---- 2. decompositions -------------------------------------------------
    legs = {}
    for p in pos:
        leg = "SHORT" if p["signed_weight"] < 0 else "LONG"
        d = legs.setdefault(leg, {"n": 0, "price": 0.0, "funding": 0.0, "cost": 0.0, "net": 0.0, "wins": 0})
        d["n"] += 1
        d["price"] += p["price_pnl_per_unit"]
        d["funding"] += p["funding_cashflow_per_unit"]
        d["cost"] -= p["cost_allocated_per_unit"]
        d["net"] += p["net_pnl_per_unit"]
        d["wins"] += 1 if p["net_pnl_per_unit"] > 0 else 0
    out["by_leg"] = {k: {"n": v["n"], "price": r6(v["price"]), "funding": r6(v["funding"]),
                         "cost": r6(v["cost"]), "net": r6(v["net"]), "win_rate": r6(v["wins"] / v["n"])}
                     for k, v in legs.items()}
    total_net = sums["net"]
    out["by_leg"]["SHORT"]["share_of_total_net_pct"] = r6(100 * legs["SHORT"]["net"] / total_net)
    out["by_leg"]["LONG"]["share_of_total_net_pct"] = r6(100 * legs["LONG"]["net"] / total_net)

    folds = defaultdict(lambda: {"n": 0, "long_net": 0.0, "short_net": 0.0, "net": 0.0})
    for p in pos:
        f = folds[p["fold_label"]]
        f["n"] += 1
        f["net"] += p["net_pnl_per_unit"]
        f["long_net" if p["signed_weight"] > 0 else "short_net"] += p["net_pnl_per_unit"]
    fm = {m["fold_label"]: m for m in art["fold_metrics"]}
    out["by_fold"] = {k: {"window": fm[k].get("window", fm[k].get("window_iso", "")),
                          "n": v["n"], "net": r6(v["net"]), "long_net": r6(v["long_net"]),
                          "short_net": r6(v["short_net"]),
                          "mdd": r6(fm[k].get("max_drawdown", float("nan"))),
                          "pf": r6(fm[k].get("position_pf", float("nan")))}
                      for k, v in sorted(folds.items())}

    symleg = defaultdict(lambda: {"n": 0, "net": 0.0, "price": 0.0, "funding": 0.0})
    for p in pos:
        key = (p["symbol"], "SHORT" if p["signed_weight"] < 0 else "LONG")
        d = symleg[key]
        d["n"] += 1
        d["net"] += p["net_pnl_per_unit"]
        d["price"] += p["price_pnl_per_unit"]
        d["funding"] += p["funding_cashflow_per_unit"]
    out["by_symbol_leg"] = [
        {"symbol": s, "leg": l, "n": d["n"], "net": r6(d["net"]), "price": r6(d["price"]), "funding": r6(d["funding"])}
        for (s, l), d in sorted(symleg.items(), key=lambda kv: kv[1]["net"])
    ]

    months = defaultdict(lambda: {"n": 0, "net": 0.0})
    for p in pos:
        m = iso(p["entry_ns"])[:7]
        months[m]["n"] += 1
        months[m]["net"] += p["net_pnl_per_unit"]
    out["by_entry_month"] = {k: {"n": v["n"], "net": r6(v["net"])} for k, v in sorted(months.items())}

    # weekly boundary series + worst stamps
    wk = [{"date": iso(dec[i]), "net": r6(bret[i])} for i in range(len(bret))]
    out["weekly_boundary_returns"] = wk
    worst = sorted(range(len(bret)), key=lambda i: bret[i])[:5]
    out["worst_stamps"] = [{"date": iso(dec[i]), "net": r6(bret[i])} for i in worst]

    # owner-specified loss clusters, per leg
    def cluster(name, lo, hi):
        sel = [p for p in pos if lo <= p["entry_ns"] < hi]
        d = {"n": 0, "long_net": 0.0, "short_net": 0.0, "funding": 0.0, "cost": 0.0, "net": 0.0, "symbols": defaultdict(float)}
        for p in sel:
            d["n"] += 1
            d["net"] += p["net_pnl_per_unit"]
            d["funding"] += p["funding_cashflow_per_unit"]
            d["cost"] -= p["cost_allocated_per_unit"]
            leg = "long_net" if p["signed_weight"] > 0 else "short_net"
            d[leg] += p["net_pnl_per_unit"]
            d["symbols"][p["symbol"] + ":" + ("S" if p["signed_weight"] < 0 else "L")] += p["net_pnl_per_unit"]
        return {"n": d["n"], "net": r6(d["net"]), "long_net": r6(d["long_net"]), "short_net": r6(d["short_net"]),
                "funding": r6(d["funding"]), "cost": r6(d["cost"]),
                "top_losers": [{"k": k, "net": r6(v)} for k, v in sorted(d["symbols"].items(), key=lambda kv: kv[1])[:5]]}

    T = lambda s: int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp() * 1e9)
    out["clusters"] = {
        "late_2024_majors_meltup": cluster("late2024", T("2024-11-01"), T("2025-01-01")),
        "jan_2025_longleg_collapse": cluster("jan2025", T("2025-01-01"), T("2025-02-01")),
        "jul_aug_2025_ath_grind": cluster("julaug2025", T("2025-07-01"), T("2025-09-01")),
    }

    # book diagnostics by phase (pre-hedge beta = ex-ante majors/BTC sensitivity of the unhedged book)
    books = art["books"]
    def phase_beta(lo, hi):
        vals = [b["diagnostics"]["book_beta_pre_hedge"] for b in books
                if lo <= b["decision_ns"] < hi and b.get("status") == "OK"
                and isinstance(b.get("diagnostics"), dict)
                and b["diagnostics"].get("book_beta_pre_hedge") is not None]
        return {"n": len(vals), "mean": r6(sum(vals) / len(vals)) if vals else None,
                "min": r6(min(vals)) if vals else None, "max": r6(max(vals)) if vals else None}
    out["book_beta_pre_hedge"] = {
        "full_window": phase_beta(0, 2**62),
        "late_2024": phase_beta(T("2024-11-01"), T("2025-01-01")),
        "jan_2025": phase_beta(T("2025-01-01"), T("2025-02-01")),
        "jul_aug_2025": phase_beta(T("2025-07-01"), T("2025-09-01")),
    }

    # ---- 3. listing-age proxy (catalog first bar, b20 union s0r) -----------
    def first_bar(symbol: str):
        for cat in ("catalog_live_crypto_b20", "catalog_live_crypto_s0r"):
            d = CHR3F / cat / "data/binance_bar" / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
            if not d.is_dir():
                continue
            files = sorted(d.glob("*.parquet"))
            if not files:
                continue
            # filename head like 2024-03-16T12-30-00-000000000Z (dashes in time part)
            head = files[0].name.split("_")[0]
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})-(\d{2})", head)
            if not m:
                continue
            try:
                dt = datetime(*(int(g) for g in m.groups()), tzinfo=timezone.utc)
                return int(dt.timestamp() * 1e9), cat
            except Exception:
                continue
        return None, None

    universe = set(art["universe"]) | {s for b in books for s, _ in b.get("longs", []) + b.get("shorts", [])}
    listing = {}
    for s in sorted(universe):
        fb, cat = first_bar(s)
        if fb:
            listing[s] = {"first_bar_ns": fb, "first_bar": iso(fb), "catalog": cat}
    out["listing_first_bar_proxy"] = listing

    # long-leg net by listing-age bucket at entry
    age_buckets = defaultdict(lambda: {"n": 0, "net": 0.0})
    ages = []
    for p in pos:
        if p["signed_weight"] < 0 or p["symbol"] not in listing:
            continue
        age_d = (p["entry_ns"] - listing[p["symbol"]]["first_bar_ns"]) / 86400e9
        ages.append(age_d)
        b = "lt90" if age_d < 90 else "90-365" if age_d < 365 else "gt365"
        if listing[p["symbol"]]["catalog"] == "catalog_live_crypto_s0r":
            b = "censored_s0r_start"  # first bar = catalog start 2024-04; true age >= computed
        age_buckets[b]["n"] += 1
        age_buckets[b]["net"] += p["net_pnl_per_unit"]
    out["long_leg_by_listing_age_proxy"] = {k: {"n": v["n"], "net": r6(v["net"])} for k, v in sorted(age_buckets.items())}
    # same split restricted to F2 (the long-leg death fold)
    f2 = [p for p in pos if p["fold_label"] == "F2" and p["signed_weight"] > 0]
    out["f2_long_leg_symbols"] = sorted({p["symbol"] for p in f2})

    json.dump(out, open(NS / "p1_forensics.json", "w"), indent=1, ensure_ascii=False)

    # stdout digest
    print("hash_checks:", {k: v["match"] for k, v in hash_checks.items()})
    print("ledger_recon all_match:", ledger_recon["all_match_1e_9"], "mdd_match:", ledger_recon["mdd_match_1e_6"])
    print("headline_claims:", {k: v["match"] for k, v in cell_checks.items()})
    print("funding_wiring_delta_pts:", out["funding_wiring_delta"]["delta_pts"])
    print("by_leg:", json.dumps(out["by_leg"]))
    print("by_fold:", json.dumps(out["by_fold"]))
    print("worst_stamps:", json.dumps(out["worst_stamps"]))
    print("clusters:", json.dumps(out["clusters"], ensure_ascii=False))
    print("book_beta_pre_hedge:", json.dumps(out["book_beta_pre_hedge"]))
    print("long_leg_by_listing_age:", json.dumps(out["long_leg_by_listing_age_proxy"]))
    print("f2_long_symbols:", out["f2_long_leg_symbols"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
