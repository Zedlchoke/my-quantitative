"""Run SANDBOX-OVERFIT-3ASSETS: fetch data, grid-search, report.

Usage: .venv/bin/python run_search.py
Outputs: out/results_all.csv, out/top_equity_<SYM>.csv,
         out/equity_<SYM>.svg, SANDBOX_OVERFIT_REPORT.md
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import sandbox_lib as L

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "out"
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
START_MS = int(pd.Timestamp("2024-09-01", tz="UTC").timestamp() * 1000)


def load_symbol(sym: str) -> pd.DataFrame:
    cache = DATA / f"{sym}_15m.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = L.fetch_klines(sym, START_MS, int(time.time() * 1000))
    df.to_parquet(cache, index=False)
    return df


def svg_equity(ts: pd.Series, eq: np.ndarray, split_idx: int, title: str) -> str:
    w, h = 720, 200
    x = np.arange(len(eq))
    if len(eq) < 2:
        return ""
    ymin, ymax = float(eq.min()), float(eq.max())
    pad = max(ymax - ymin, 1e-9) * 0.05
    ymin, ymax = ymin - pad, ymax + pad
    px = (x / (len(x) - 1) * (w - 40) + 20)
    py = (h - 30) - (eq - ymin) / (ymax - ymin) * (h - 50)
    pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(px, py))
    sx = px[split_idx]
    grid = ""
    for frac, lab in ((1.0, ""), (2.0, ""), (3.0, "")):
        yy = (h - 30) - (frac - ymin) / (ymax - ymin) * (h - 50)
        if ymin <= frac <= ymax:
            grid += (f'<line x1="20" y1="{yy:.0f}" x2="{w-20}" y2="{yy:.0f}" '
                     f'stroke="#ddd" stroke-dasharray="3,3"/>'
                     f'<text x="22" y="{yy-3:.0f}" font-size="10" fill="#666">x{frac}</text>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'font-family="monospace">{grid}'
        f'<text x="20" y="14" font-size="12" fill="#333">{title}</text>'
        f'<line x1="{sx:.0f}" y1="20" x2="{sx:.0f}" y2="{h-30}" stroke="#c66" '
        f'stroke-dasharray="4,2"/>'
        f'<text x="{sx+3:.0f}" y="32" font-size="10" fill="#c66">OOS</text>'
        f'<polyline fill="none" stroke="#247" stroke-width="1.2" points="{pts}"/>'
        f'</svg>')


def fmt_pct(v: float) -> str:
    return f"{v * 100:,.1f}%"


def main() -> None:
    grid = L.build_grid()
    print(f"grid configs: {len(grid)} x lev {L.LEVERAGES} = {len(grid) * len(L.LEVERAGES)} per asset")
    all_rows: list[dict] = []
    report: list[str] = [
        "# SANDBOX OVERFIT — 3 tài sản (BTC/ETH/SOL perp, 15m, ~2 năm)",
        "",
        "> **Trạng thái: SANDBOX, KHÔNG phải evidence.** Chọn cấu hình theo lợi "
        "nhuận **in-sample thuần** (có phí taker 5bp + trượt 1bp + funding ~1bp/8h), "
        "overfit cố ý theo chỉ đạo owner. Cột OOS là chẩn đoán 'thật sự còn lại "
        "bao nhiêu' — **không** dùng để chọn. Đòn bẩy L không mô hình liquidation.",
        "",
    ]
    for sym in SYMBOLS:
        t0 = time.time()
        df = load_symbol(sym)
        close = df["close"].to_numpy()
        rows = L.search_asset(close, grid)
        for r in rows:
            r["symbol"] = sym
        all_rows.extend(rows)
        bh = L.buyhold_metrics(close)
        top = rows[:10]
        best = rows[0]
        print(f"{sym}: {len(df)} bars {df['ts'].iloc[0].date()}→{df['ts'].iloc[-1].date()} "
              f"({time.time() - t0:.1f}s) best IS {best['is_total_return']*100:,.0f}% "
              f"({best['family']} {best['params']} L{best['lev']:.0f}) | "
              f"B&H IS {bh['is_total_return']*100:,.0f}%")
        report += [
            f"## {sym} — {len(df)} nến 15m, {df['ts'].iloc[0].date()} → {df['ts'].iloc[-1].date()}",
            "",
            f"Buy & Hold: IS {fmt_pct(bh['is_total_return'])} | "
            f"OOS {fmt_pct(bh['oos_total_return'])}",
            "",
            "| # | Họ | Tham số | L | IS Net | IS CAGR | IS Sharpe | IS MaxDD | "
            "Trades | Win% | **OOS Net** | OOS Sharpe |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for i, r in enumerate(top, 1):
            wr = f"{r['is_win_rate']*100:.0f}%" if np.isfinite(r["is_win_rate"]) else "—"
            report.append(
                f"| {i} | {r['family']} | `{r['params']}` | {r['lev']:.0f} | "
                f"{fmt_pct(r['is_total_return'])} | {fmt_pct(r['is_cagr'])} | "
                f"{r['is_sharpe']:.2f} | {r['is_max_dd']*100:.1f}% | "
                f"{r['is_n_trades']} | {wr} | **{fmt_pct(r['oos_total_return'])}** | "
                f"{r['oos_sharpe']:.2f} |")
        # top-1 equity curve csv + svg
        fam, params = best["family"], json.loads(best["params"])
        for name, p, f in grid:
            if name == fam and p == params:
                sig = f(close)
                break
        eq = L.equity_curve(close, sig, best["lev"])
        split = int(len(close) * (1 - L.OOS_FRACTION))
        eq.assign(ts=df["ts"]).to_csv(OUT / f"top_equity_{sym}.csv", index=False)
        (OUT / f"equity_{sym}.svg").write_text(
            svg_equity(df["ts"], eq["equity"].to_numpy(), split,
                       f"{sym} — {fam} {params} L{best['lev']:.0f} (equity, net)"))
        report += ["", f"![{sym} equity](out/equity_{sym}.svg)", ""]
    res = pd.DataFrame(all_rows)
    res.to_csv(OUT / "results_all.csv", index=False)
    report += [
        "---",
        "",
        "## Lời cảnh báo (đọc trước khi 'kiểm tra' gì đó với những con số này)",
        "",
        "1. **Overfit cố ý**: mỗi tài sản chạy "
        f"{len(grid) * len(L.LEVERAGES)} cấu hình, chọn 1 cái đẹp nhất IS — "
        "số IS gần như chắc chắn không lặp lại tương lai.",
        "2. **OOS cột** cho thấy khoảng cách: đây là byproduct có ý nghĩa nhất "
        "của sandbox — chênh IS vs OOS = thước đo mức 'khủng' là ảo.",
        "3. Chi phí xấp xỉ, **không có funding thực theo thời gian**, không "
        "liquidation với L>1, không slippage theo depth.",
        "4. Không fold discipline / DSR / PBO / trial accounting — cố tình, "
        "để so sánh với quy trình evidence-first của factory.",
        "5. Không đăng ký `CYCLE_REGISTRY.json`; không đụng ledger của cycle nào.",
        "",
        f"Tổng số cấu hình đã thử (đếm thử nghiệm): {len(all_rows)} "
        f"({len(grid)} signal × {len(L.LEVERAGES)} đòn bẩy × {len(SYMBOLS)} tài sản).",
        "",
        "Đầy đủ: `out/results_all.csv`; equity top-1 từng mã: `out/top_equity_*.csv`.",
    ]
    (HERE / "SANDBOX_OVERFIT_REPORT.md").write_text("\n".join(report) + "\n")
    print("done →", OUT / "results_all.csv", "& SANDBOX_OVERFIT_REPORT.md")


if __name__ == "__main__":
    main()
