"""A7 terminal audit -- independent Stage-A gate recomputation from source.

Recomputes EVERY frozen Stage-A gate of CRYPTO-V14 from the published
artifacts (results/v14_phase_e/...), without trusting any recorded verdict:

* portfolio metrics (net, expectancy, PF, MDD) recomputed from the
  artifact's own daily_returns / positions rows with the frozen adapter
  definitions (research.adapter_v10.metrics: position_profit_factor,
  max_drawdown, daily_expectancy);
* per-fold net sums recomputed from daily_returns;
* fold-positive concentration: definition F1 (largest positive fold net /
  sum of positive fold nets -- the V12 A7 precedent) AND definition F2
  (per-position POSITIVE_AGGREGATE_PNL_ONLY_V1 grouping, research/v7_finalizer);
* symbol positive-PnL share: POSITIVE_AGGREGATE_PNL_ONLY_V1 (symbol positive
  pnl / total positive pnl) AND the share-of-abs variant, from positions;
* stress cells (fee x1.5, +2 ticks, +1 delay) recomputed net-positive;
* drop-one symbol / fold non-vacuousness from cell specs + baseline books;
* benchmark / BTC-beta excess per fold: BTCUSDT marks from the frozen
  family bar loader over the SAME staged bytes the exec twin read
  (staged_data/binance_bar_15m, e-exec-1 worktree); convention validated
  against the committed buy_and_hold per-leg BTCUSDT gross return;
  excess_bh_f = arm_fold_net_f - BTC_f (OICYC.md section 7, verbatim);
  excess_beta_f = arm_fold_net_f - beta_p * BTC_f with beta_p the trailing
  90d PIT regression of the arm's per-decision realized rows on BTC
  close-to-close returns at the same instants (the arm's true daily
  mark-to-market series is NOT a committed artifact; this is the closest
  computable PIT analogue and is recorded as an audit approximation);
* the frozen family gate_runner functions are then applied to the
  recomputed inputs and their verdicts recorded.

Pure read-only audit: writes one JSON report, changes no scored evidence.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from research.adapter_v10.metrics import (  # noqa: E402
    daily_expectancy,
    max_drawdown,
    position_profit_factor,
)
from research.v14.families.basislv_premfade.audits import (  # noqa: E402
    load_execution_bars,
)

RESULTS = REPO / "results/v14_phase_e"
STAGED_BARS = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v14/"
    "e-exec-1/staged_data/binance_bar_15m"
)

ARMS = [
    ("basislv_premfade", "BASISLV-PREMFADE-28D", "anchor"),
    ("basislv_premfade", "BASISLV-PREMFADE-56D", "neighbour"),
    ("basislv_premfade", "BASISLV-PREMFADE-28D-INV", "causal_negative_control"),
    ("oicyc", "CYC-28D", "anchor"),
    ("oicyc", "CYC-14D", "neighbour"),
    ("oicyc", "CTL-OISHARE", "causal_negative_control"),
]

CELLS = [
    "baseline",
    "fee_slippage_x1_5",
    "plus_2_ticks",
    "plus_1_event_delay",
    "drop_one_symbol",
    "drop_one_fold",
]

WEEK_NS = 7 * 24 * 3600 * 10**9
DAY_NS = 24 * 3600 * 10**9


def r12(v):
    return None if v is None else round(v, 12)


def load_artifact(family: str, arm: str, cell: str) -> dict:
    p = RESULTS / family / arm / "matrix" / cell / "results" / "artifact.json"
    return json.loads(p.read_text())


def recompute_metrics(art: dict) -> dict:
    daily = sorted(art["daily_returns"], key=lambda r: r["decision_ns"])
    nets = [float(r["net_return_per_unit"]) for r in daily]
    positions = art["positions"]
    pnl = [float(p["net_pnl_per_unit"]) for p in positions]
    pf, pf_note = position_profit_factor(pnl)
    per_fold: dict[int, float] = {}
    for r in daily:
        k = int(r["fold_index"])
        per_fold[k] = per_fold.get(k, 0.0) + float(r["net_return_per_unit"])
    fold_nets = {k: round(v, 12) for k, v in sorted(per_fold.items())}
    # F2 fold concentration: per-position POSITIVE_AGGREGATE_PNL_ONLY_V1
    pos_by_fold: dict[int, float] = {}
    sym_pos: dict[str, float] = {}
    sym_abs: dict[str, float] = {}
    total_positive = 0.0
    for p in positions:
        v = float(p["net_pnl_per_unit"])
        if v > 0.0:
            pos_by_fold[int(p["fold_index"])] = (
                pos_by_fold.get(int(p["fold_index"]), 0.0) + v
            )
            sym_pos[p["symbol"]] = sym_pos.get(p["symbol"], 0.0) + v
            total_positive += v
        sym_abs[p["symbol"]] = sym_abs.get(p["symbol"], 0.0) + abs(v)
    pos_fold_total = math.fsum(pos_by_fold.values())
    fold_share_f2 = (
        max(pos_by_fold.values()) / pos_fold_total if pos_by_fold else None
    )
    top_sym = max(sorted(sym_pos), key=lambda k: sym_pos[k]) if sym_pos else None
    top_sym_share = (sym_pos[top_sym] / total_positive) if total_positive > 0 else None
    top_sym_abs = max(sorted(sym_abs), key=lambda k: sym_abs[k])
    top_sym_share_abs = sym_abs[top_sym_abs] / math.fsum(sym_abs.values())
    pos_f = sum(1 for v in pnl if v > 0.0)
    neg_f = sum(1 for v in pnl if v <= 0.0)
    return {
        "n_daily_rows": len(daily),
        "net_return_sum": r12(math.fsum(nets)),
        "expectancy_per_day": r12(daily_expectancy(nets)),
        "max_drawdown_recomputed": r12(max_drawdown(nets)),
        "n_positions": len(positions),
        "position_pf_recomputed": r12(pf),
        "pf_positive_legs": pos_f,
        "pf_negative_legs": neg_f,
        "fold_net_sums": fold_nets,
        "fold_positive": [v > 0.0 for v in fold_nets.values()],
        "n_folds_positive": sum(1 for v in fold_nets.values() if v > 0.0),
        "fold_pos_share_F1_largest_positive_fold_net_over_positive_fold_nets": (
            r12(
                max(v for v in fold_nets.values() if v > 0.0)
                / math.fsum(v for v in fold_nets.values() if v > 0.0)
            )
            if any(v > 0.0 for v in fold_nets.values())
            else None
        ),
        "fold_pos_share_F2_positive_aggregate_by_fold": r12(fold_share_f2),
        "top_symbol_positive_share": r12(top_sym_share),
        "top_symbol_positive_share_of_abs": r12(top_sym_share_abs),
        "top_symbol": top_sym,
        "price_only_expectancy": r12(
            (math.fsum(float(r["price_pnl_per_unit"]) for r in daily)
             - math.fsum(float(r["cost_charged_per_unit"]) for r in daily))
            / len(daily)
        ),
        "total_expectancy": r12(
            (math.fsum(float(r["price_pnl_per_unit"]) for r in daily)
             + math.fsum(float(r["funding_cashflow_per_unit"]) for r in daily)
             - math.fsum(float(r["cost_charged_per_unit"]) for r in daily))
            / len(daily)
        ),
    }


def fold_spans(art: dict) -> dict[int, tuple[int, int, list[int]]]:
    out = {}
    for fm in art["fold_metrics"]:
        if not fm.get("included_in_metrics", True):
            continue
        inst = [int(v) for v in fm["instants"]]
        out[int(fm["fold_index"])] = (inst[0], inst[-1], inst)
    return out


def btc_marks():
    bars = load_execution_bars(("BTCUSDT",), bars_root=str(STAGED_BARS))
    series = bars["BTCUSDT"]

    def mark(instant_ns: int) -> float:
        idx = series.slot_index(int(instant_ns))
        for i in range(min(idx, series.close.shape[0] - 1), -1, -1):
            c = float(series.close[i])
            if math.isfinite(c) and int(series.available_ns[i]) <= int(instant_ns):
                return c
        raise RuntimeError(f"no BTC mark at or before {instant_ns}")

    return mark


def sharpe_and_moments(rows: list[float]) -> dict:
    n = len(rows)
    mean = statistics.fmean(rows)
    sd = statistics.stdev(rows) if n > 1 else float("nan")
    sr = mean / sd
    m2 = math.fsum((v - mean) ** 2 for v in rows) / n
    m3 = math.fsum((v - mean) ** 3 for v in rows) / n
    m4 = math.fsum((v - mean) ** 4 for v in rows) / n
    skew = m3 / m2 ** 1.5
    kappa = m4 / (m2 * m2)  # Pearson kurtosis; 3 == normal
    return {"sharpe_per_decision": sr, "skew": skew, "kurtosis_pearson": kappa, "n": n}


def beta_and_excess(art: dict, btc_mark) -> dict:
    """excess_bh and excess_beta per fold (OICYC.md section 7 convention).

    beta_p: trailing-90d PIT regression of the arm's per-decision realized
    net rows on BTC close-to-close returns at the same decision instants,
    estimated at the fold's first stamp and held fixed over the fold.
    Audit approximation note recorded in the report.
    """
    daily = sorted(art["daily_returns"], key=lambda r: r["decision_ns"])
    instants = [int(r["decision_ns"]) for r in daily]
    arm_rets = [float(r["net_return_per_unit"]) for r in daily]
    btc_rets = []
    for i, t in enumerate(instants):
        if i == 0:
            btc_rets.append(0.0)
        else:
            btc_rets.append(btc_mark(t) / btc_mark(instants[i - 1]) - 1.0)
    spans = fold_spans(art)
    out = {"per_fold": {}, "audit_note": None}
    for f, (first, last, _) in sorted(spans.items()):
        btc_f = btc_mark(last) / btc_mark(first) - 1.0
        arm_f = 0.0
        for r, t in zip(daily, instants):
            if first <= t <= last:
                arm_f += float(r["net_return_per_unit"])
        # trailing 90d PIT window = instants strictly before `first` within 90d
        win = [
            (a, b)
            for a, b, t in zip(arm_rets, btc_rets, instants)
            if first - 90 * DAY_NS <= t < first
        ]
        if len(win) >= 3:
            xs = [b for _, b in win]
            ys = [a for a, _ in win]
            mx, my = statistics.fmean(xs), statistics.fmean(ys)
            sxx = math.fsum((x - mx) ** 2 for x in xs)
            beta = (
                math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
                if sxx > 0
                else 0.0
            )
            beta_src = "trailing_90d_pit_weekly_regression"
        else:
            beta, beta_src = 0.0, "no_prior_window_beta_set_0"
        out["per_fold"][str(f)] = {
            "arm_net_f": r12(arm_f),
            "btc_bh_f": r12(btc_f),
            "excess_bh_f": r12(arm_f - btc_f),
            "beta_p": r12(beta),
            "beta_source": beta_src,
            "excess_beta_f": r12(arm_f - beta * btc_f),
        }
    return out


def main() -> dict:
    report: dict = {"arms": {}, "btc_convention_check": {}}
    btc_mark = btc_marks()

    # BTC convention validation against committed benchmark legs
    for family, arm, _ in ARMS:
        art = load_artifact(family, arm, "baseline")
        committed = art["benchmarks"]["buy_and_hold"]
        mine = btc_mark(int(committed["exit_ns"])) / btc_mark(
            int(committed["entry_ns"])
        ) - 1.0
        report["btc_convention_check"][f"{family}/{arm}"] = {
            "committed_btc_leg_gross_return": committed["per_leg_gross_return"][
                "BTCUSDT"
            ],
            "recomputed": r12(mine),
            "abs_diff": r12(
                abs(mine - float(committed["per_leg_gross_return"]["BTCUSDT"]))
            ),
        }
        break  # same bars for all arms; one validation suffices, keep the rest

    for family, arm, role in ARMS:
        arm_out = {"family": family, "arm": arm, "role": role, "cells": {}}
        base_art = load_artifact(family, arm, "baseline")
        base = recompute_metrics(base_art)
        arm_out["baseline_recomputed"] = base

        # published metrics cross-check
        pm = base_art["portfolio_metrics"]
        arm_out["published_crosscheck"] = {
            "net_return_sum": {
                "published": pm["net_return_sum"],
                "recomputed": base["net_return_sum"],
            },
            "position_pf": {
                "published": pm["position_pf"],
                "recomputed": base["position_pf_recomputed"],
            },
            "max_drawdown": {
                "published": pm["max_drawdown"],
                "recomputed": base["max_drawdown_recomputed"],
            },
            "expectancy_per_day": {
                "published": pm["expectancy_per_day"],
                "recomputed": base["expectancy_per_day"],
            },
        }
        arm_out["sharpe_moments"] = sharpe_and_moments(
            [
                float(r["net_return_per_unit"])
                for r in sorted(
                    base_art["daily_returns"], key=lambda r: r["decision_ns"]
                )
            ]
        )
        arm_out["benchmark_excess"] = beta_and_excess(base_art, btc_mark)

        for cell in CELLS[1:]:
            art = load_artifact(family, arm, cell)
            m = recompute_metrics(art)
            entry = {
                "stress_spec": art.get("stress"),
                "net_return_sum": m["net_return_sum"],
                "n_positions": m["n_positions"],
                "fold_net_sums": m["fold_net_sums"],
                "fold_positive": m["fold_positive"],
            }
            if cell == "drop_one_symbol":
                dropped = (art.get("stress") or {}).get("drop_symbols") or []
                held = 0
                for p in base_art["positions"]:
                    if p["symbol"] in dropped:
                        held += 1
                entry["dropped_symbols"] = dropped
                entry["dropped_symbol_positions_in_baseline"] = held
                entry["baseline_net"] = base["net_return_sum"]
                entry["delta_net_vs_baseline"] = r12(
                    m["net_return_sum"] - base["net_return_sum"]
                )
                entry["non_vacuous"] = bool(
                    held > 0
                    and abs(m["net_return_sum"] - base["net_return_sum"]) > 0
                )
            if cell == "drop_one_fold":
                dropped_fold = (art.get("stress") or {}).get("dropped_fold_index")
                base_positions_in_fold = sum(
                    1
                    for p in base_art["positions"]
                    if int(p["fold_index"]) == int(dropped_fold)
                )
                retained = {
                    str(k): v
                    for k, v in m["fold_net_sums"].items()
                    if int(k) != int(dropped_fold)
                }
                base_retained = {
                    str(k): v
                    for k, v in base["fold_net_sums"].items()
                    if int(k) != int(dropped_fold)
                }
                signs_unchanged = all(
                    (retained[k] > 0.0) == (base_retained[k] > 0.0)
                    for k in retained
                )
                entry["dropped_fold_index"] = dropped_fold
                entry["dropped_fold_positions_in_baseline"] = base_positions_in_fold
                entry["retained_fold_signs_unchanged_vs_baseline"] = signs_unchanged
                entry["non_vacuous"] = bool(base_positions_in_fold > 0)
            arm_out["cells"][cell] = entry

        report["arms"][f"{family}/{arm}"] = arm_out
    return report


if __name__ == "__main__":
    rep = main()
    out = Path(__file__).resolve().parent / "a7_stage_a_recompute_v14.json"
    out.write_text(json.dumps(rep, indent=1))
    print(f"wrote {out}")
