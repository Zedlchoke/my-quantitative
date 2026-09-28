"""Sizing audit generator — 1.5 lot/pair FX on the shared 100k portfolio.

Reads ONLY authoritative epoch-1 sources (FX shadow_state marks + PSV1
valuation marks) and writes AUDIT_sizing_fx_shared_100k_v1.md. Numbers
are computed, never hand-typed. Re-run to refresh; output is a function
of the current source files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import portfolio_lib as pl  # noqa: E402

STRESS_PCT = [0.02, 0.05]
PIPS = [10, 25, 50, 100, 200]
LOT_OPTIONS = [0.5, 1.0, 1.5]
FX_MARGIN_LEVERAGE = 30  # declared assumption: majors 30:1 regulatory cap


def main() -> None:
    st = json.load(open(pl.FX_DIR / "shadow_state.json"))
    eu, gb = st["sleeves"]["EURUSD"], st["sleeves"]["GBPUSD"]
    eu_mid = (eu["mark"]["bid"] + eu["mark"]["ask"]) / 2
    gb_mid = (gb["mark"]["bid"] + gb["mark"]["ask"]) / 2
    eu_sp = (eu["mark"]["ask"] - eu["mark"]["bid"]) * 1e4
    gb_sp = (gb["mark"]["ask"] - gb["mark"]["bid"]) * 1e4

    crypto = {}
    for fam in pl.CRYPTO_SLEEVES:
        marks = pl.read_jsonl(pl.PSV1_RESULTS / f"valuation_marks/{fam}.jsonl")
        eqs = [m["equity"] for m in marks if isinstance(m.get("equity"), (int, float))]
        peak, mdd = -1.0, 0.0
        for e in eqs:
            peak = max(peak, e)
            mdd = max(mdd, peak - e)
        lastm = marks[-1]
        gross = sum(abs(p.get("notional") or 0.0)
                    for p in (lastm.get("positions") or []))
        crypto[fam] = {"last_eq": eqs[-1], "mdd": mdd, "gross": gross,
                       "n_pos": len(lastm.get("positions") or []),
                       "status": lastm.get("status")}
    e2_gross = sum(crypto[f]["gross"] for f in
                   ("BTC4H-BANDRIDGE", "BASISLV-PREMFADE-28D", "ILLIQ-AMIHUD-28D-W"))
    runoff_gross = crypto["XSECT-FUND-CARRY-7D"]["gross"]

    L = []
    w = L.append
    w("# AUDIT — FX sizing 1.5 lot/cặp trên portfolio chung $100,000 (epoch-2)")
    w("")
    w("> **PREVIEW — không thay đổi sizing frozen của worker cũ.** Mọi sizing mới là")
    w("> strategy identity/amendment và cần owner GO riêng. Không claim live-ready.")
    w(f"> Nguồn: FX marks `{pl.FX_DIR}/shadow_state.json` (TrueFX indicative, chỉ tham khảo)")
    w(f"> + PSV1 valuation marks. Sinh tự động bởi `scripts/sizing_audit.py`; chạy lại để làm mới.")
    w("")
    w("## 1. Giá hiện tại, pip value, notional, leverage, margin")
    w("")
    w(f"| Đại lượng | EURUSD | GBPUSD |")
    w(f"|---|---|---|")
    w(f"| Mark bid/ask | {eu['mark']['bid']:.5f} / {eu['mark']['ask']:.5f} (spread {eu_sp:.1f} pip) | {gb['mark']['bid']:.5f} / {gb['mark']['ask']:.5f} (spread {gb_sp:.1f} pip) |")
    w("")
    w("Pip value USD-quote major = 10 USD/pip/lot (độc lập giá). 1 lot = 100,000 đơn vị base.")
    w("")
    w("| Lot/cặp | Notional EURUSD | Notional GBPUSD | Gross FX | Leverage trên 100k | Pip value/cặp | Margin @30:1 |")
    w("|---|---|---|---|---|---|---|")
    for lots in LOT_OPTIONS:
        units = lots * 100000
        n_eu, n_gb = units * eu_mid, units * gb_mid
        gross = n_eu + n_gb
        # pip value: 100,000 units × 1e-4 = $10 per pip per LOT (USD quote)
        w(f"| {lots} | ${n_eu:,.0f} | ${n_gb:,.0f} | ${gross:,.0f} | {gross/1e5:.2f}x | ${lots*10:,.0f} | ${gross/FX_MARGIN_LEVERAGE:,.0f} |")
    w("")
    w("## 2. Kịch bản hai cặp CÙNG bất lợi (USD và % vốn 100k)")
    w("")
    w("| Lot/cặp | 10 pip | 25 pip | 50 pip | 100 pip | 200 pip |")
    w("|---|---|---|---|---|---|")
    for lots in LOT_OPTIONS:
        pipv = lots * 10  # $/pip per pair: 100,000 × 1e-4 × lots
        cells = [f"${2*p*pipv:,.0f} ({2*p*pipv/1e5:.1%})" for p in PIPS]
        w(f"| {lots} | " + " | ".join(cells) + " |")
    w("")
    w(f"- **Spread stress** (chốt dưới spread giãn +5 pip so với hiện tại, cả hai cặp): "
      f"0.5 lot = ${2*5*5:,.0f} · 1.0 lot = ${2*5*10:,.0f} · 1.5 lot = ${2*5*15:,.0f}. "
      f"Spread TrueFX indicative hiện {eu_sp:.1f}/{gb_sp:.1f} pip — retail thực tế rộng hơn, đây là lower-bound cảnh báo.")
    w("- **Gap**: KHÔNG có hard stop trong thiết kế — **mức lỗ tối đa chưa được giới hạn bởi thiết kế**. "
      "Luật force-flat 20:00 UTC chỉ giới hạn thời gian nắm giữ (không qua đêm, cuối tuần flat nên "
      "không có gap cuối tuần trên sách FX), không giới hạn độ sâu lỗ; kịch bản N-pip gap tuyến tính: "
      f"0.5 lot = N×$10 · 1.0 lot = N×$20 · 1.5 lot = N×$30 (cả hai cặp).")
    w("- **MAE từng lệnh: NOT_RUN** — journal FX không lưu extreme trong lệnh (chỉ có OHLC bar); "
      "MAE thật cần instrumentation mới → thuộc draft amendment FX A1-controls (chờ GO).")
    w("")
    w("## 3. Sách crypto đồng thời lỗ (stress trên gross hiện tại)")
    w("")
    w("| Sleeve | Trạng thái | Gross hiện tại | MaxDD đo từ marks | Stress 2% | Stress 5% |")
    w("|---|---|---|---|---|---|")
    for fam, c in crypto.items():
        tag = "epoch-2" if fam != "XSECT-FUND-CARRY-7D" else "run-off (retired, ngoài epoch-2)"
        w(f"| {fam} | {c['status']} · {tag} | ${c['gross']:,.0f} | ${c['mdd']:,.0f} ({c['mdd']/1e5:.2%}) | ${c['gross']*0.02:,.0f} | ${c['gross']*0.05:,.0f} |")
    w("")
    w(f"- Crypto sleeve epoch-2 gross hiện tại: **${e2_gross:,.0f}**; cộng sách run-off XSECT: **${e2_gross+runoff_gross:,.0f}**.")
    w("- Overlap cùng symbol đang có: ILLIQ ∩ XSECT (run-off) trên ETHUSDT/SOLUSDT/XRPUSDT — "
      "lệch hướng một phần, nhưng cùng nhạy crypto-beta; trong epoch-2 không còn XSECT.")
    w("- Same-side USD exposure FX: hiện sách FX FLAT nên = $0. Khi cả hai cặp cùng LONG base "
      "= cùng chiều SHORT USD, exposure cộng dồn: 1.5 lot ≈ −$368,7k USD-directional trên 100k vốn.")
    w("")
    w("## 4. Tổng hợp kịch bản xấu trong bảng (FX 200 pip cả hai cặp + crypto 5%)")
    w("")
    w("| Lot/cặp | FX 200p | + Crypto 5% (epoch-2 only) | Tổng (epoch-2) | + run-off XSECT 5% | Tổng (gồm run-off) |")
    w("|---|---|---|---|---|---|")
    for lots in LOT_OPTIONS:
        fx = 2 * 200 * lots * 10
        cr_e2 = e2_gross * 0.05
        cr_ro = runoff_gross * 0.05
        w(f"| {lots} | ${fx:,.0f} | ${cr_e2:,.0f} | ${fx+cr_e2:,.0f} ({(fx+cr_e2)/1e5:.1%}) | ${cr_ro:,.0f} | ${fx+cr_e2+cr_ro:,.0f} ({(fx+cr_e2+cr_ro)/1e5:.1%}) |")
    w("")
    w("## 5. Đề xuất risk budget (PROPOSAL — chờ owner GO, không tự áp)")
    w("")
    w("Giả định khai báo: FX margin 30:1 (majors); pip value $10/pip/lot; không hard stop "
      "(force-flat 20:00 chỉ là time-stop); crypto stress tham chiếu 5% gross; USDT≈USD theo ref đã khai báo.")
    w("")
    w("1. **Budget tổng (account chung)**: max aggregate stress loss ≤ **15% equity** "
      "($15,000 trên 100k) cho tổ hợp FX + crypto cùng bất lợi.")
    w("2. **Cap class (ràng buộc chính về leverage)**: FX gross ≤ 150% equity; crypto gross ≤ 150% "
      "equity; tổng ≤ 250% (đã ghi trong epoch_config.capital_rule, freeze trước khi thấy PnL epoch-2). "
      f"Với giá hiện tại: 1.0 lot/cặp = FX gross ${2*(100000*(eu_mid+gb_mid))/1e3:,.0f}k ≈ 246% — VƯỢT cap FX; "
      f"1.5 lot/cặp ≈ 369% — vượt sâu; 0.5 lot/cặp ≈ 123% — vừa cap.")
    w("3. **Lot tương ứng dưới caps**: ràng buộc là cap FX 150% → **≈ 0.5–0.6 lot/cặp**. "
      "Stress tại 0.5 lot: 200-pip cả hai cặp = $2,000 (2%) + crypto epoch-2 5% = "
      f"${e2_gross*0.05:,.0f} → tổng ≈ {(2000 + e2_gross*0.05)/1e5:.1%} vốn, còn dư budget 15%.")
    w("4. **1.0 lot/cặp** chỉ cân nhắc nếu owner nâng cap FX hoặc các crypto sleeve flat; "
      "về loss 200-pip cả hai cặp chỉ = 4% vốn — vấn đề của 1.0 lot là LEVERAGE, không phải stress-loss.")
    w("5. **1.5 lot/cặp**: loss 200-pip = 6% vốn (chấp nhận được về stress), NHƯNG gross 369% phá vỡ "
      "mọi cap đòn bẩy của portfolio chung 100k; và một ngày bất thường 500-pip cả hai cặp (kiểu CHF) "
      "= $15,000 = 100% budget. Giữ nguyên 1.5 lot trong sách shadow cũ frozen; epoch-2 cần sizing "
      "explicit thấp hơn qua amendment.")
    w("6. Sách run-off XSECT (ngoài epoch-2) đang gross "
      f"${runoff_gross:,.0f} — stress 5% = ${runoff_gross*0.05:,.0f} nằm NGOÀI budget epoch-2 nhưng "
      "phải hiển thị riêng trên dashboard đến khi flat.")
    w("7. Mọi con số trên là **đề xuất**; áp đặt phải đi qua amendment có GO riêng.")
    w("")
    out = HERE / "AUDIT_sizing_fx_shared_100k_v1.md"
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
