"""A7 TERMINAL AUDIT recompute — BTC-H4-CONTINUATION-V2.

Fresh-context auditor script. Independent of forensics/forensics_driver.py:
this file re-imports the FROZEN PSV1 scored engine (cells / books / accounting)
READ-ONLY from the PSV1 integration worktree and re-derives the BTC_H4 arm's
fold nets + totals at 1.0x/1.5x/2.0x, then compares against the COMMITTED PSV1
scored_ledger.json (the authoritative target) AND against the V2 cycle's
reconciliation.json claims.

Also:
  * SMA200 entry-gate no-op arithmetic check (P2 branch 2): evaluates
    close > SMA200 at all 86 entry DECISION bars from the rebuilt panel.
  * min-hold spot-checks: 5 delayed trades re-verified against the rebuilt
    book's trade records.

Heavy-lock mode: the machine-wide heavy lock was found HELD by a foreign
worker (CRYPTO-HISTORICAL-REPLICATION-3F-V1 data-staging) at audit time, so
this run proceeds ONLY under the plan §8 LIGHT-JOB EXEMPTION with hard
ceilings (<300 s CPU, <2 GB peak RSS) measured via resource.getrusage —
aborts otherwise. Writes only into this audits/ directory.
"""
from __future__ import annotations

import json
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/hoangminhlong/my-quantitative")
V1_INT = REPO / ".worktrees/phase-strategy-v1/integration"
V1_SCORED = V1_INT / "research/control/phase_strategy_v1/scored"
V1_RUNTIME = V1_INT / "research/control/phase_strategy_v1/runtime/scored"
HERE = Path(__file__).resolve().parent

LIGHT_MAX_CPU_S = 300.0
LIGHT_MAX_RSS_B = 2 * 1024 ** 3

sys.path.insert(0, str(V1_SCORED))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

t0_wall = time.monotonic()
ru0 = resource.getrusage(resource.RUSAGE_SELF)

import cells  # frozen PSV1 scored cells (READ-ONLY import)  # noqa: E402
import books  # frozen PSV1 scored books (READ-ONLY import)  # noqa: E402
import accounting as acc  # frozen PSV1 scored accounting (READ-ONLY)  # noqa: E402

TIERS = [1.0, 1.5, 2.0]
ARM_KEY = "BTC_H4::PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION"
TOL_REL = 1e-6


def rel(meas: float, tgt: float) -> float:
    if meas == tgt:
        return 0.0
    d = abs(meas - tgt)
    return d / abs(tgt) if tgt else d


def main() -> int:
    out: dict = {
        "schema": "v2_a7_recompute@1",
        "auditor": "A7 terminal fresh-context",
        "lock_state_at_audit": {
            "verdict": "HELD_PROVEN_FOREIGN",
            "holder": "CRYPTO-HISTORICAL-REPLICATION-3F-V1/data-staging pid 77456",
            "mode": "LIGHT_EXEMPTION_DISCLOSED",
            "ceilings": {"max_cpu_s": LIGHT_MAX_CPU_S, "max_peak_rss_bytes": LIGHT_MAX_RSS_B},
        },
    }

    # ---- rebuild (frozen engine, verbatim calls) ---------------------------
    cell = cells.load_btc_h4()
    book = books.l2_run_book(cell)
    fills = books.l2_fills_from_book(book)
    funding_mask = acc.btc_8h_boundary_mask(cell["open_ms"])
    open_, close = cell["open"], cell["close"]
    fold_ids = cell["fold_ids"]

    per_tier = {}
    for tier in TIERS:
        res = acc.run_accounting(open_, close, fills, fold_ids, cell["bps"],
                                 tier=tier, funding_mask=funding_mask,
                                 funding_rate=cell["funding_rate"])
        per_tier[tier] = res

    # ---- targets: COMMITTED PSV1 ledger (authoritative) --------------------
    ledger = json.loads((V1_RUNTIME / "scored_ledger.json").read_text())
    arm = ledger["arms"][ARM_KEY]

    recon: dict = {}
    max_rel = 0.0
    for tier in TIERS:
        tgt = arm["tiers"][f"{tier}x"]
        meas = per_tier[tier]
        checks = {
            "trades": rel(meas["trades"], tgt["trades"]),
            "per_fold_net::0": rel(meas["per_fold_net"][0], tgt["per_fold_net"]["0"]),
            "per_fold_net::1": rel(meas["per_fold_net"][1], tgt["per_fold_net"]["1"]),
            "per_fold_net::2": rel(meas["per_fold_net"][2], tgt["per_fold_net"]["2"]),
            "per_fold_net::3": rel(meas["per_fold_net"][3], tgt["per_fold_net"]["3"]),
            "net": rel(meas["net"], tgt["net"]),
            "gross": rel(meas["gross"], tgt["gross"]),
            "fees": rel(meas["fees"], tgt["fees"]),
            "funding": rel(meas["funding"], tgt["funding"]),
        }
        worst = max(checks.values())
        max_rel = max(max_rel, worst)
        recon[f"{tier}x"] = {"worst_rel_err": worst, "checks": checks,
                             "verdict": "PASS" if worst <= TOL_REL else "FAIL"}
        # cross-check vs the V2 cycle's own reconciliation.json values
        v2recon = json.loads((HERE.parent / "forensics" / "reconciliation.json").read_text())
        vt = v2recon["tiers"][f"{tier}x"]["checks"]
        for name, tval in (("net", "totals::net"), ("gross", "totals::gross"),
                           ("fees", "totals::fees"), ("funding", "totals::funding")):
            if per_tier[tier][name] != vt[tval]["measured"]:
                recon[f"{tier}x"]["verdict"] = "FAIL"
                recon[f"{tier}x"][f"v2_recon_mismatch::{tval}"] = {
                    "auditor_measured": per_tier[tier][name],
                    "v2_claimed_measured": vt[tval]["measured"]}
    out["recompute_vs_committed_psv1_ledger"] = recon
    out["max_rel_err_all_tiers"] = max_rel
    out["recompute_verdict"] = "PASS" if max_rel <= TOL_REL else "FAIL"

    # ---- SMA200 entry-gate no-op check (P2 branch 2 arithmetic) ------------
    close_s = pd.Series(close)
    sma200 = close_s.rolling(200, min_periods=200).mean().to_numpy()
    trades = [(f, tr) for f, trs in book["_trade_records"].items() for tr in trs]
    trades.sort(key=lambda x: x[1]["entry_bar"])
    n_entries = len(trades)
    # entry records carry the decision bar (events.py: decision_bar = t, fill = t+1)
    entry_recs = sorted(book["_entry_records"], key=lambda e: e["decision_bar"])
    assert len(entry_recs) == n_entries
    dec_bars = np.array([e["decision_bar"] for e in entry_recs], dtype=int)
    gate_pass = close[dec_bars] > sma200[dec_bars]
    dd200 = close[dec_bars] / pd.Series(close).rolling(200, min_periods=200).max().to_numpy()[dec_bars] - 1.0
    binds = [(i, int(dec_bars[i]), float(close[dec_bars[i]]),
              float(sma200[dec_bars[i]]), float(dd200[i]))
             for i in range(n_entries) if not gate_pass[i]]
    out["sma200_entry_gate_check"] = {
        "definition": "close[decision_bar] > SMA200(close, 200 bars incl. current)",
        "n_entries": n_entries,
        "n_gate_binds_would_exclude": len(binds),
        "binding_examples_first5": binds[:5],
        "dd200_at_entries": {"min": float(dd200.min()), "max": float(dd200.max()),
                             "n_below_minus1pct": int((dd200 < -0.01).sum())},
        "noop_conclusion": "VACUOUS (never binds)" if not binds
                           else f"BINDS AT {len(binds)} ENTRIES -> not a mathematical no-op",
    }

    # ---- min-hold spot-checks vs rebuilt book ------------------------------
    # P2/min_hold_audit delay_detail entries (fold, entry_fill_bar, exit_bar, reason)
    expected = [("F1", 1180, 1192, "DONCHIAN_STOP"),
                ("F2", 4509, 4521, "DONCHIAN_STOP"),
                ("F2", 5585, 5599, "DONCHIAN_STOP"),
                ("F3", 7505, 7536, "DONCHIAN_STOP"),
                ("F4", 12481, 12499, "DONCHIAN_STOP")]
    fnames = {0: "F1", 1: "F2", 2: "F3", 3: "F4"}
    spot = []
    for f, eb, xb, rs in expected:
        hit = [tr for ff, tr in trades
               if fnames[ff] == f and tr["entry_bar"] == eb and tr["exit_bar"] == xb]
        ok = len(hit) == 1 and hit[0]["exit_reason"] == rs
        spot.append({"fold": f, "entry_fill_bar": eb, "exit_bar": xb,
                     "expected_reason": rs,
                     "found": bool(hit), "reason": hit[0]["exit_reason"] if hit else None,
                     "hold_bars": hit[0]["bars_held"] if hit else None,
                     "ok": bool(ok)})
    out["min_hold_spot_checks"] = spot
    out["min_hold_spot_checks_verdict"] = ("PASS" if all(s["ok"] for s in spot) else "FAIL")

    # ---- resources ----------------------------------------------------------
    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    cpu_s = (ru1.ru_utime + ru1.ru_stime) - (ru0.ru_utime + ru0.ru_stime)
    wall_s = time.monotonic() - t0_wall
    peak_rss = ru1.ru_maxrss  # darwin: bytes already
    out["resources"] = {"cpu_s": round(cpu_s, 2), "wall_s": round(wall_s, 2),
                        "peak_rss_bytes": int(peak_rss),
                        "within_light_ceilings": bool(cpu_s < LIGHT_MAX_CPU_S
                                                      and peak_rss < LIGHT_MAX_RSS_B)}
    out["measured_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    (HERE / "a7_recompute_result.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("recompute_verdict", "max_rel_err_all_tiers",
                                          "sma200_entry_gate_check",
                                          "min_hold_spot_checks_verdict",
                                          "resources", "measured_at_utc")}, indent=1)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
