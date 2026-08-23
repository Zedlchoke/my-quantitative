"""Edge-stability analysis for scan-matrix near-miss combos (sprint agent A4).

Read-only research tool. It does NOT modify config/*.yaml, strategy_*.py,
backtest/ or risk/. All inputs are existing artifacts + the bar catalog.

What it does
------------
1. Load per-combo fold artifacts from a scan dir (results/scan_matrix/<stamp>).
2. Map every walk-forward fold to UTC quarters.
3. Label each UTC day with a Wyckoff phase using
   ``regime_wyckoff.classify_wyckoff_row`` and the frozen ``WyckoffConfig``.
   Day ``i`` is classified only from completed days ``< i`` (same semantics as
   ``WyckoffDailyTracker``, which updates phase on day rolls). Days before the
   frozen minimum history (max(ema_slow, range_lookback, return_lookback)+5
   daily bars) are reported as ``warmup`` instead of being force-labeled.
4. Classify each losing fold by dominant regime + quarter (concentration test).
5. Analytic slippage stress x1.5. The engine's fill model is Nautilus'
   compiled ``OneTickSlippageFillModel`` (deterministic 1 tick/fill, no
   magnitude parameter; scan_matrix CLI exposes no slippage flag), so there is
   no supported in-place rerun without editing files. Instead:

       extra_cost_per_roundtrip = (mult - 1) * n_fills * tick_size * qty
       qty_upper_bound          = max_notional / mean_close
       exp_stressed             = expectancy_after_funding - extra/n_fills... (per trade)

   Concretely, per trade:  d_exp = (mult-1) * 2 * tick_size * qty
   with qty = max_notional / P̄ (upper bound: notional always at cap, so the
   stress is deliberately conservative). Stressed metrics subtract trades*d_exp.

Usage:
    /path/to/python -m research.analyze_edge_stability \
        --scan-dir results/scan_matrix/20260823T051806Z \
        --catalog ./catalog_live_crypto [--max-notional 300] [--slippage-mult 1.5]

Output: markdown-ready tables on stdout. Numbers only.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

COMBOS: tuple[tuple[str, str], ...] = (
    ("reclaim_mr", "NEARUSDT"),
    ("reclaim_mr", "ETHUSDT"),  # cautionary example
    ("trend_pullback", "BOMEUSDT"),
    ("markdown_breakdown", "ADAUSDT"),
    ("reclaim_mr", "SOLUSDT"),
)

PHASES = ("accumulation", "markup", "distribution", "markdown", "transition")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def quarter_of(ts_ms: int | float) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return f"{dt.year}Q{(dt.month - 1) // 3 + 1}"


def _iso(ts_ms: int | float) -> str:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def load_combo(scan_dir: Path, strategy_type: str, symbol: str) -> dict:
    path = scan_dir / strategy_type / f"{symbol}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cells = sorted(data["cells"], key=lambda c: c["fold"])
    for cell in cells:
        cell["start_ts"] = int(datetime.fromisoformat(cell["start"]).timestamp() * 1000)
        cell["end_ts"] = int(datetime.fromisoformat(cell["end"]).timestamp() * 1000)
    return {"strategy_type": strategy_type, "symbol": symbol, "summary": data["symbol_summary"][0], "cells": cells}


# --------------------------------------------------------------------------- #
# daily Wyckoff labeling (frozen thresholds, no lookahead)
# --------------------------------------------------------------------------- #
def _ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def daily_series(bars) -> list[dict]:
    days: dict[str, dict] = {}
    from datetime import date as _date

    for bar in bars:
        day = datetime.utcfromtimestamp(bar.ts_event / 1e9).date()
        key = day.isoformat()
        o = bar.open.as_double()
        h = bar.high.as_double()
        l = bar.low.as_double()
        c = bar.close.as_double()
        v = bar.volume.as_double()
        if key not in days:
            days[key] = {"date": day, "open": o, "high": h, "low": l, "close": c, "volume": v}
        else:
            d = days[key]
            d["high"] = max(d["high"], h)
            d["low"] = min(d["low"], l)
            d["close"] = c
            d["volume"] += v
    return [days[k] for k in sorted(days)]


def label_daily_phases(days: list[dict]) -> list[str]:
    """Phase per day, computed only from completed prior days (no lookahead)."""
    from regime import AverageDirectionalIndex
    from regime_wyckoff import WyckoffConfig, classify_wyckoff_row

    cfg = WyckoffConfig()
    min_len = max(cfg.ema_slow, cfg.range_lookback_days, cfg.return_lookback_days) + 5

    closes = [d["close"] for d in days]
    highs = [d["high"] for d in days]
    lows = [d["low"] for d in days]

    ema50_full = _ema(closes, cfg.ema_fast)
    ema200_full = _ema(closes, cfg.ema_slow)
    adx = AverageDirectionalIndex(period=cfg.adx_period)

    labels: list[str] = []
    for i in range(len(days)):
        if i < min_len or not adx.initialized:
            labels.append("warmup")
            adx.update(high=highs[i], low=lows[i], close=closes[i])
            continue
        # indicators use completed days < i
        ema_fast = ema50_full[i - 1]
        ema_slow = ema200_full[i - 1]
        ret_pct = (closes[i - 1] / closes[i - 1 - cfg.return_lookback_days] - 1.0) * 100.0
        lo = min(lows[i - cfg.range_lookback_days : i])
        hi = max(highs[i - cfg.range_lookback_days : i])
        span = hi - lo
        range_pos = (closes[i - 1] - lo) / span if span > 0 else 0.5
        phase = classify_wyckoff_row(
            close=closes[i - 1],
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            return_pct=ret_pct,
            range_position=range_pos,
            adx=adx.value,
            cfg=cfg,
        )
        labels.append(phase.value)
        adx.update(high=highs[i], low=lows[i], close=closes[i])
    return labels


def fold_phase_mix(labels: list[str], days: list[dict], start_iso: str, end_iso: str) -> tuple[Counter, str, float]:
    """Phase mix inside [start,end]; dominant phase among labeled days."""
    mix: Counter = Counter()
    total = 0
    for label, day in zip(labels, days):
        if start_iso <= day["date"].isoformat() <= end_iso:
            mix[label] += 1
            total += 1
    labeled = sum(n for p, n in mix.items() if p != "warmup")
    if labeled == 0:
        return mix, "warmup", 0.0
    dom_phase, dom_n = max(((p, n) for p, n in mix.items() if p != "warmup"), key=lambda kv: kv[1])
    return mix, dom_phase, dom_n / labeled


# --------------------------------------------------------------------------- #
# slippage stress (analytic)
# --------------------------------------------------------------------------- #
def mean_close(bars) -> float:
    vals = [b.close.as_double() for b in bars]
    return sum(vals) / len(vals)


# --------------------------------------------------------------------------- #
# main analysis
# --------------------------------------------------------------------------- #
def analyze(scan_dir: Path, catalog_path: str, max_notional: float, slip_mult: float, out_path: Path) -> None:
    import warnings

    warnings.filterwarnings("ignore")
    from data.catalog import Catalog

    cat = Catalog(catalog_path)

    combos = [load_combo(scan_dir, st, sym) for st, sym in COMBOS]

    print("# A4 edge stability — scan", scan_dir.name)
    print(f"# catalog={catalog_path} max_notional={max_notional} slippage_mult={slip_mult}\n")

    # ---- section A: definition-of-edge gates -------------------------------- #
    print("## A. Edge-v2 gate screen (window-level)\n")
    print("| combo | exp_af | PF_af | folds+ | PnL_af | BH | PnL>BH |")
    print("|---|---|---|---|---|---|---|")
    for combo in combos:
        s = combo["summary"]
        pf_raw = s.get("profit_factor")
        pf_af = f"{pf_raw:.2f}" if isinstance(pf_raw, (int, float)) else (
            f"{sum(c['profit_factor'] * c['trades'] for c in combo['cells']) / max(1, sum(c['trades'] for c in combo['cells'])):.2f} (trade-wtd)"
        )
        bh = s["buy_hold_pnl_at_max_notional"]
        folds_pos = sum(1 for c in combo["cells"] if c["positive_after_funding"])
        print(
            f"| {combo['strategy_type']} {combo['symbol']} | {s['expectancy_after_funding']:+.3f} "
            f"| {pf_af} | {folds_pos}/6 | {s['pnl_after_funding']:+.2f} "
            f"| {bh:+.2f} | {'YES' if s['pnl_after_funding'] > bh else 'NO'} |"
        )
    print()

    # ---- sections B/C/D: folds x quarters x regimes -------------------------- #
    regime_rows: list[dict] = []
    for combo in combos:
        sym = combo["symbol"]
        bars = cat.bars(f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
        inst = cat.instrument(f"{sym}-PERP.BINANCE")
        tick = float(inst.price_increment)
        p_mean = mean_close(bars)
        qty_ub = max_notional / p_mean
        d_exp = (slip_mult - 1.0) * 2.0 * tick * qty_ub

        days = daily_series(bars)
        labels = label_daily_phases(days)
        from datetime import timedelta

        first_day = days[0]["date"]

        print(f"## B. {combo['strategy_type']} {sym} — fold x quarter x regime (PnL after funding)")
        print(f"<!-- tick={tick} mean_close={p_mean:.6g} qty_ub={qty_ub:.4f} slippage_stress_d_exp_per_trade={d_exp:.4f} -->\n")
        print("| fold | window | quarters spanned | mid-quarter | trades | pnl_af | exp_af | PF | WR | pos | dominant phase | phase mix (labeled %) | stressed exp |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for cell in combo["cells"]:
            qs, qe = quarter_of(cell["start_ts"]), quarter_of(cell["end_ts"])
            mid_q = quarter_of((cell["start_ts"] + cell["end_ts"]) / 2)
            mix, dom, share = fold_phase_mix(labels, days, cell["start"], cell["end"][:10])
            mix_str = " ".join(f"{p}:{mix[p]}" for p in PHASES + ("warmup",) if mix.get(p))
            stressed = cell["expectancy_after_funding"] - d_exp
            print(
                f"| F{cell['fold']} | {_iso(cell['start_ts'])}→{_iso(cell['end_ts'])} "
                f"| {qs}–{qe} | {mid_q} | {cell['trades']} | {cell['pnl_after_funding']:+.2f} "
                f"| {cell['expectancy_after_funding']:+.3f} | {cell['profit_factor']:.2f} "
                f"| {cell['win_rate']:.2f} | {'+' if cell['positive_after_funding'] else '-'} "
                f"| {dom} ({share:.0%}) | {mix_str} | {stressed:+.3f} |"
            )
            regime_rows.append(
                {
                    "combo": f"{combo['strategy_type']} {sym}",
                    "fold": cell["fold"],
                    "quarters": f"{qs}-{qe}",
                    "mid_quarter": mid_q,
                    "positive": cell["positive_after_funding"],
                    "dominant_phase": dom,
                    "phase_share": share,
                    "pnl_af": cell["pnl_after_funding"],
                }
            )
        # quarterly price stats for context (objective, not tuned)
        print("\nQuarterly context (price stats from same bars):")
        print("| quarter | ret% | maxDD% | days labeled non-warmup |")
        print("|---|---|---|---|")
        quarters: dict[str, list[dict]] = {}
        for day, lab in zip(days, labels):
            q = f"{day['date'].year}Q{(day['date'].month - 1) // 3 + 1}"
            quarters.setdefault(q, []).append({"day": day, "lab": lab})
        for q in sorted(quarters):
            rows = quarters[q]
            entry = rows[0]["day"]["close"]
            exit_ = rows[-1]["day"]["close"]
            peak = max(r["day"]["high"] for r in rows)
            trough = min(r["day"]["low"] for r in rows)
            dd = (trough / peak - 1.0) * 100.0 if peak > 0 else 0.0
            nlabeled = sum(1 for r in rows if r["lab"] != "warmup")
            print(f"| {q} | {(exit_ / entry - 1) * 100:+.1f} | {dd:.1f} | {nlabeled}/{len(rows)} |")
        print()

    # ---- losing-fold concentration ------------------------------------------ #
    print("## C. Losing-fold concentration test\n")
    print("| combo | losing folds | their mid-quarters | their dominant phases | distinct (quarter,phase) | concentrated<=2? |")
    print("|---|---|---|---|---|---|")
    verdict_concentration: dict[str, bool] = {}
    for combo in combos:
        name = f"{combo['strategy_type']} {combo['symbol']}"
        losers = [r for r in regime_rows if r["combo"] == name and not r["positive"]]
        keys = {(r["mid_quarter"], r["dominant_phase"]) for r in losers}
        verdict_concentration[name] = len(keys) <= 2 and len(losers) > 0
        print(
            f"| {name} | {[r['fold'] for r in losers]} "
            f"| {[r['mid_quarter'] for r in losers]} "
            f"| {[r['dominant_phase'] for r in losers]} "
            f"| {len(keys)} | {'YES' if verdict_concentration[name] else 'NO'} |"
        )
    print()

    # ---- slippage stress summary -------------------------------------------- #
    print("## D. Slippage x%.1f analytic stress (window level)\n" % slip_mult)
    print("Formula: d_exp_per_trade=(mult-1)*2*tick*qty, qty=max_notional/mean_close (upper bound).\n")
    print("| combo | trades | exp_af | stressed exp | pnl_af | stressed pnl | still>0? |")
    print("|---|---|---|---|---|---|---|")
    for combo in combos:
        sym = combo["symbol"]
        bars = cat.bars(f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
        inst = cat.instrument(f"{sym}-PERP.BINANCE")
        tick = float(inst.price_increment)
        d_exp = (slip_mult - 1.0) * 2.0 * tick * (max_notional / mean_close(bars))
        s = combo["summary"]
        se = s["expectancy_after_funding"] - d_exp
        sp = s["pnl_after_funding"] - d_exp * s["trades"]
        print(
            f"| {combo['strategy_type']} {sym} | {s['trades']} | {s['expectancy_after_funding']:+.4f} "
            f"| {se:+.4f} | {s['pnl_after_funding']:+.2f} | {sp:+.2f} | {'YES' if se > 0 else 'NO'} |"
        )
    print()

    # ---- machine-readable dump for memo ------------------------------------- #
    out = {
        "scan_dir": str(scan_dir),
        "combos": [
            {
                "strategy_type": c["strategy_type"],
                "symbol": c["symbol"],
                "summary": c["summary"],
                "losing_fold_concentration_le2": verdict_concentration[f"{c['strategy_type']} {c['symbol']}"],
            }
            for c in combos
        ],
        "regime_rows": regime_rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="A4 edge stability analysis (read-only)")
    ap.add_argument("--scan-dir", default="results/scan_matrix/20260823T051806Z")
    ap.add_argument("--catalog", default="./catalog_live_crypto")
    ap.add_argument("--max-notional", type=float, default=300.0)
    ap.add_argument("--slippage-mult", type=float, default=1.5)
    ap.add_argument(
        "--out",
        default="results/edge_stability/edge_stability_summary.json",
        help="where to write the machine-readable summary (worktree-local)",
    )
    args = ap.parse_args()
    analyze(Path(args.scan_dir), args.catalog, args.max_notional, args.slippage_mult, Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
