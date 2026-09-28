"""Chạy overfit 3 family (crypto/stocks/forex) — xem families_lib.py.

Output: out/family_results_<CLASS>.csv, out/top_trades_<CLASS>.csv,
FAMILY_OVERFIT_REPORT.md
"""
from __future__ import annotations

import itertools
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import families_lib as F

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
OOS_FRAC = 0.20

STOCKS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO",
          "AMD", "NFLX", "JPM", "V", "MA", "UNH", "LLY", "JNJ", "PG", "KO",
          "PEP", "COST", "WMT", "XOM", "CVX", "ABBV", "MRK", "HD", "MCD",
          "DIS", "BAC", "CSCO", "ORCL", "CRM", "ADBE", "ACN", "INTC", "TSM"]
FX_LEGS = {"EURUSD=X": 1e-4, "GBPUSD=X": 1e-4, "AUDUSD=X": 1e-4,
           "NZDUSD=X": 1e-4, "USDJPY=X": 1e-2, "USDCAD=X": 1e-4,
           "USDCHF=X": 1e-4}
CRYPTO = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def pct(x):
    return f"{x * 100:,.1f}%"


def bh_stock(df: pd.DataFrame) -> float:
    return df["close"].iloc[-1] / df["close"].iloc[0] - 1.0


# ------------------------------------------------------------- STOCKS

def run_stocks() -> tuple[list[dict], dict]:
    data = {}
    for s in STOCKS:
        try:
            data[s] = F.fetch_yahoo_daily(s)
        except Exception as exc:
            print(f"  skip {s}: {exc}")
    print(f"stocks universe: {len(data)} symbols")
    grids = [dict(K=K, H=H, range_thr=r, part_mult=p, reclaim_gap=g)
             for K, H, r, p, g in itertools.product(
                 (10, 21, 63, 126, 252), (3, 5, 10, 20, 40),
                 (0.3, 0.5, 0.7), (1.0, 1.5, 2.5, 4.0), (5, 10, 21))]
    # shared index: dùng calendar của AAPL làm chuẩn, IS/OOS split theo date
    ref = data[STOCKS[0]]["ts"]
    split_date = ref.iloc[int(len(ref) * (1 - OOS_FRAC))]
    rows = []
    for gi, g in enumerate(grids):
        is_r = pd.Series(0.0, index=ref)
        oos_r = pd.Series(0.0, index=ref)
        n_tr = 0
        for s, df in data.items():
            idx = df["ts"]
            trades = F.event_unwind_trades(
                df["open"].to_numpy(), df["high"].to_numpy(),
                df["low"].to_numpy(), df["close"].to_numpy(),
                df["volume"].to_numpy(), **g)
            n_tr += len(trades)
            for (a, b, net) in trades:
                if idx.iloc[a] < split_date:
                    is_r.loc[idx.iloc[a:b + 1]] += (1 + net) ** (1 / (b - a + 1)) - 1
                else:
                    oos_r.loc[idx.iloc[a:b + 1]] += (1 + net) ** (1 / (b - a + 1)) - 1
        n_slots = len(data)
        m_is = F.metrics_from_daily(is_r / n_slots)
        m_oos = F.metrics_from_daily(oos_r / n_slots)
        rows.append({"family": "EVENT-UNWIND", "params": json.dumps(g, separators=(",", ":")),
                     "is_total_return": m_is["total_return"], "is_cagr": m_is["cagr"],
                     "is_sharpe": m_is["sharpe"], "is_max_dd": m_is["max_dd"],
                     "n_trades": n_tr,
                     "oos_total_return": m_oos["total_return"],
                     "oos_sharpe": m_oos["sharpe"]})
        if gi % 100 == 0:
            print(f"  stocks grid {gi}/{len(grids)} ({time.strftime('%H:%M:%S')})")
    rows.sort(key=lambda r: r["is_total_return"], reverse=True)
    for i, r in enumerate(rows):
        r["is_rank"] = i + 1
    bh = float(np.mean([bh_stock(d) for d in data.values()]))
    return rows, {"bh_is": bh}


# ------------------------------------------------------------- FOREX

def run_forex() -> tuple[list[dict], dict]:
    data = {}
    for s, pip in FX_LEGS.items():
        try:
            data[s] = (F.fetch_yahoo_daily(s), pip)
        except Exception as exc:
            print(f"  skip {s}: {exc}")
    print(f"forex legs: {len(data)}")
    grids = [dict(ext_win=e, p_win=20, slope_win=k, hold=h, div_thr=d)
             for e, k, h, d in itertools.product(
                 (10, 20, 40), (5, 10), (1, 3, 5, 10),
                 (0.0, -2.0, 0.5))]
    ref = data[list(data)[0]][0]["ts"]
    split_date = ref.iloc[int(len(ref) * (1 - OOS_FRAC))]
    rows = []
    for gi, g in enumerate(grids):
        # dict-accumulator: calendar mỗi leg khác nhau, không .loc trên ref
        is_acc: dict = {}
        oos_acc: dict = {}
        n_tr = 0
        for s, (df, pip) in data.items():
            idx = df["ts"]
            trades = F.clv_absorb_trades(
                df["open"].to_numpy(), df["high"].to_numpy(),
                df["low"].to_numpy(), df["close"].to_numpy(),
                pip=pip, fee_pips=1.0, **g)
            n_tr += len(trades)
            for (a, b, net) in trades:
                seg = idx.iloc[a:b + 1]
                if len(seg) == 0:
                    continue
                contrib = (1 + net) ** (1 / len(seg)) - 1
                acc = is_acc if idx.iloc[a] < split_date else oos_acc
                for d in seg:
                    acc[d] = acc.get(d, 0.0) + contrib
        n_slots = len(data)
        is_r = pd.Series([is_acc.get(d, 0.0) for d in ref], index=ref)
        oos_r = pd.Series([oos_acc.get(d, 0.0) for d in ref], index=ref)
        m_is = F.metrics_from_daily(is_r / n_slots)
        m_oos = F.metrics_from_daily(oos_r / n_slots)
        rows.append({"family": "DIVERGENT-CLV", "params": json.dumps(g, separators=(",", ":")),
                     "is_total_return": m_is["total_return"], "is_cagr": m_is["cagr"],
                     "is_sharpe": m_is["sharpe"], "is_max_dd": m_is["max_dd"],
                     "n_trades": n_tr,
                     "oos_total_return": m_oos["total_return"],
                     "oos_sharpe": m_oos["sharpe"]})
    rows.sort(key=lambda r: r["is_total_return"], reverse=True)
    for i, r in enumerate(rows):
        r["is_rank"] = i + 1
    bh = float(np.mean([df["close"].iloc[-1] / df["close"].iloc[0] - 1.0
                        for df, _ in data.values()]))
    return rows, {"bh_is": bh}


# ------------------------------------------------------------- CRYPTO

def run_crypto() -> tuple[list[dict], dict]:
    data = {}
    for s in CRYPTO:
        df = pd.read_parquet(HERE / "data" / f"{s}_15m.parquet")
        data[s] = df
    print(f"crypto: {len(data)} symbols 15m")
    space = [dict(bb_period=bp, bb_k=bk, squeeze_lb=sl, squeeze_pct=sp,
                  vol_ratio=vr, donch=dc, atr_mult=am, tp_mult=tp, max_hold=mh)
             for bp, bk, sl, sp, vr, dc, am, tp, mh in itertools.product(
                 (14, 20, 30), (1.5, 2.0, 2.5), (96, 192, 384),
                 (10, 20, 30, 40), (1.2, 1.5, 2.0, 3.0), (48, 96, 192),
                 (1.0, 1.5, 2.0), (1.5, 2.0, 3.0, None), (96, 192, 384))]
    rng = np.random.default_rng(42)
    pick = rng.choice(len(space), size=min(800, len(space)), replace=False)
    grids = [space[i] for i in sorted(pick)]
    split = {s: int(len(df) * (1 - OOS_FRAC)) for s, df in data.items()}
    rows = []
    for gi, g in enumerate(grids):
        is_tot, oos_tot, n_tr = [], [], 0
        for s, df in data.items():
            trades = F.volcomp_trades(
                df["open"].to_numpy(), df["high"].to_numpy(),
                df["low"].to_numpy(), df["close"].to_numpy(),
                df["volume"].to_numpy(), **g)
            n_tr += len(trades)
            sp = split[s]
            eq_is = float(np.prod([1 + t[2] for t in trades if t[0] < sp])) \
                if any(t[0] < sp for t in trades) else 1.0
            eq_oos = float(np.prod([1 + t[2] for t in trades if t[0] >= sp])) \
                if any(t[0] >= sp for t in trades) else 1.0
            is_tot.append(eq_is)
            oos_tot.append(eq_oos)
        rows.append({"family": "VOLCOMP-BRKOUT",
                     "params": json.dumps(g, separators=(",", ":")),
                     "is_total_return": float(np.mean(is_tot) - 1.0),
                     "is_cagr": np.nan, "is_sharpe": np.nan, "is_max_dd": np.nan,
                     "n_trades": n_tr,
                     "oos_total_return": float(np.mean(oos_tot) - 1.0),
                     "oos_sharpe": np.nan})
        if gi % 100 == 0:
            print(f"  crypto grid {gi}/{len(grids)} ({time.strftime('%H:%M:%S')})")
    rows.sort(key=lambda r: r["is_total_return"], reverse=True)
    for i, r in enumerate(rows):
        r["is_rank"] = i + 1
    bh = float(np.mean([df["close"].iloc[-1] / df["close"].iloc[0] - 1.0
                        for df in data.values()]))
    return rows, {"bh_is": bh, "note": "IS/OOS theo entry; equity = trung bình 3 symbol; chưa tính Sharpe/DD path-level"}


def _bh_baselines() -> dict:
    out = {}
    for tag, syms, src in (("CRYPTO", CRYPTO, "binance"),
                           ("STOCKS", STOCKS, "yahoo"),
                           ("FOREX", list(FX_LEGS), "yahoo")):
        vals = []
        for s in syms:
            try:
                if src == "binance":
                    df = pd.read_parquet(HERE / "data" / f"{s}_15m.parquet")
                else:
                    df = F.fetch_yahoo_daily(s)
                vals.append(df["close"].iloc[-1] / df["close"].iloc[0] - 1.0)
            except Exception:
                continue
        out[tag] = float(np.mean(vals)) if vals else float("nan")
    return out


def assemble_report() -> None:
    bh = _bh_baselines()
    names = {"CRYPTO": "CRYPTO · H-VOLCOMP-BRKOUT-v1",
             "STOCKS": "STOCKS · EVENT-UNWIND (NG6 anchor)",
             "FOREX": "FOREX · SWING-EXTREME ABSORPTION / DIVERGENT CLV (FNG7-A2-P1)"}
    report = [
        "# FAMILY OVERFIT — 1 family đã research × mỗi lớp tài sản",
        "",
        "> SANDBOX, KHÔNG phải evidence. Family lấy nguyên từ corpus owner đã "
        "research (không sáng tạo mới); grid nới rộng vượt grid frozen của cycle "
        "gốc để overfit tối đa; chọn theo IS net return; OOS 20% cuối chỉ chẩn đoán.",
        "",
    ]
    for tag in ("CRYPTO", "STOCKS", "FOREX"):
        path = OUT / f"family_results_{tag}.csv"
        if not path.exists():
            continue
        rows = pd.read_csv(path).sort_values("is_rank").to_dict("records")
        report += [f"## {names[tag]}", "",
                   f"Baseline B&H (trung bình universe, toàn bộ 15 năm/khung): IS **{pct(bh[tag])}**", "",
                   "| # | Tham số | IS Net | IS CAGR | IS Sharpe | IS MaxDD | Trades | **OOS Net** | OOS Sharpe |",
                   "|---|---|---|---|---|---|---|---|---|"]
        for r in rows[:10]:
            def fmt(v, kind="pct"):
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    return "—"
                if not np.isfinite(v):
                    return "—"
                return pct(v) if kind == "pct" else f"{v:.2f}"
            report.append(
                f"| {r['is_rank']} | `{r['params']}` | **{fmt(r['is_total_return'])}** | "
                f"{fmt(r.get('is_cagr'))} | {fmt(r.get('is_sharpe'), 'f')} | "
                f"{fmt(r.get('is_max_dd'))} | {r['n_trades']} | "
                f"**{fmt(r['oos_total_return'])}** | {fmt(r.get('oos_sharpe'), 'f')} |")
        report += [""]
    report += [
        "---",
        "",
        "## Cảnh báo",
        "",
        "1. Overfit cố ý: chọn config đẹp nhất IS từ hàng trăm/nghìn cấu hình — số IS là trần trên của may mắn.",
        "2. Cột OOS = chẩn đoán suy giảm; chênh IS→OOS là thước đo độ ảo.",
        "3. Chi phí xấp xỉ: crypto 6bp/side + funding 1bp/8h; stocks 3bp/side (chưa có impact theo size); FX 1 pip/side.",
        "4. Yahoo close là split-adjusted (chưa gồm cổ tức); Binance 15m là last-trade.",
        "5. Family giữ đúng anchor của corpus gốc nhưng **grid rộng hơn hẳn** grid frozen của cycle tương ứng — kết quả không liên quan đến gates/registry của các cycle đó.",
        "",
        "Đầy đủ: `out/family_results_{CRYPTO,STOCKS,FOREX}.csv`.",
    ]
    (HERE / "FAMILY_OVERFIT_REPORT.md").write_text("\n".join(report) + "\n")
    print("report → FAMILY_OVERFIT_REPORT.md")


def main() -> None:
    import sys
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only"):
            only = {x.strip().lower() for x in a.split("=", 1)[1].split(",")} \
                if "=" in a else {"forex"}
    if only is None:
        only = {"crypto", "stocks", "forex"}
    t0 = time.time()
    runners = {"crypto": (run_crypto, "CRYPTO"),
               "stocks": (run_stocks, "STOCKS"),
               "forex": (run_forex, "FOREX")}
    for key in ("crypto", "stocks", "forex"):
        if key not in only:
            continue
        fn, tag = runners[key]
        print(f"== {key} ==")
        rows, _extra = fn()
        pd.DataFrame(rows).to_csv(OUT / f"family_results_{tag}.csv", index=False)
        print(f"saved {len(rows)} rows → family_results_{tag}.csv")
    assemble_report()
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
