# AUDIT — FX sizing 1.5 lot/cặp trên portfolio chung $100,000 (epoch-2)

> **PREVIEW — không thay đổi sizing frozen của worker cũ.** Mọi sizing mới là
> strategy identity/amendment và cần owner GO riêng. Không claim live-ready.
> Nguồn: FX marks `/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/shadow_state.json` (TrueFX indicative, chỉ tham khảo)
> + PSV1 valuation marks. Sinh tự động bởi `scripts/sizing_audit.py`; chạy lại để làm mới.

## 1. Giá hiện tại, pip value, notional, leverage, margin

| Đại lượng | EURUSD | GBPUSD |
|---|---|---|
| Mark bid/ask | 1.13694 / 1.13696 (spread 0.2 pip) | 1.32115 / 1.32117 (spread 0.2 pip) |

Pip value USD-quote major = 10 USD/pip/lot (độc lập giá). 1 lot = 100,000 đơn vị base.

| Lot/cặp | Notional EURUSD | Notional GBPUSD | Gross FX | Leverage trên 100k | Pip value/cặp | Margin @30:1 |
|---|---|---|---|---|---|---|
| 0.5 | $56,848 | $66,058 | $122,906 | 1.23x | $5 | $4,097 |
| 1.0 | $113,695 | $132,116 | $245,811 | 2.46x | $10 | $8,194 |
| 1.5 | $170,543 | $198,174 | $368,716 | 3.69x | $15 | $12,291 |

## 2. Kịch bản hai cặp CÙNG bất lợi (USD và % vốn 100k)

| Lot/cặp | 10 pip | 25 pip | 50 pip | 100 pip | 200 pip |
|---|---|---|---|---|---|
| 0.5 | $100 (0.1%) | $250 (0.2%) | $500 (0.5%) | $1,000 (1.0%) | $2,000 (2.0%) |
| 1.0 | $200 (0.2%) | $500 (0.5%) | $1,000 (1.0%) | $2,000 (2.0%) | $4,000 (4.0%) |
| 1.5 | $300 (0.3%) | $750 (0.8%) | $1,500 (1.5%) | $3,000 (3.0%) | $6,000 (6.0%) |

- **Spread stress** (chốt dưới spread giãn +5 pip so với hiện tại, cả hai cặp): 0.5 lot = $50 · 1.0 lot = $100 · 1.5 lot = $150. Spread TrueFX indicative hiện 0.2/0.2 pip — retail thực tế rộng hơn, đây là lower-bound cảnh báo.
- **Gap**: KHÔNG có hard stop trong thiết kế — **mức lỗ tối đa chưa được giới hạn bởi thiết kế**. Luật force-flat 20:00 UTC chỉ giới hạn thời gian nắm giữ (không qua đêm, cuối tuần flat nên không có gap cuối tuần trên sách FX), không giới hạn độ sâu lỗ; kịch bản N-pip gap tuyến tính: 0.5 lot = N×$10 · 1.0 lot = N×$20 · 1.5 lot = N×$30 (cả hai cặp).
- **MAE từng lệnh: NOT_RUN** — journal FX không lưu extreme trong lệnh (chỉ có OHLC bar); MAE thật cần instrumentation mới → thuộc draft amendment FX A1-controls (chờ GO).

## 3. Sách crypto đồng thời lỗ (stress trên gross hiện tại)

| Sleeve | Trạng thái | Gross hiện tại | MaxDD đo từ marks | Stress 2% | Stress 5% |
|---|---|---|---|---|---|
| BTC4H-BANDRIDGE | FLAT_OK · epoch-2 | $0 | $0 (0.00%) | $0 | $0 |
| BASISLV-PREMFADE-28D | FLAT_OK · epoch-2 | $0 | $0 (0.00%) | $0 | $0 |
| ILLIQ-AMIHUD-28D-W | RUNNING · epoch-2 | $104,166 | $3,792 (3.79%) | $2,083 | $5,208 |
| XSECT-FUND-CARRY-7D | RUNNING · run-off (retired, ngoài epoch-2) | $205,865 | $4,839 (4.84%) | $4,117 | $10,293 |

- Crypto sleeve epoch-2 gross hiện tại: **$104,166**; cộng sách run-off XSECT: **$310,030**.
- Overlap cùng symbol đang có: ILLIQ ∩ XSECT (run-off) trên ETHUSDT/SOLUSDT/XRPUSDT — lệch hướng một phần, nhưng cùng nhạy crypto-beta; trong epoch-2 không còn XSECT.
- Same-side USD exposure FX: hiện sách FX FLAT nên = $0. Khi cả hai cặp cùng LONG base = cùng chiều SHORT USD, exposure cộng dồn: 1.5 lot ≈ −$368,7k USD-directional trên 100k vốn.

## 4. Tổng hợp kịch bản xấu trong bảng (FX 200 pip cả hai cặp + crypto 5%)

| Lot/cặp | FX 200p | + Crypto 5% (epoch-2 only) | Tổng (epoch-2) | + run-off XSECT 5% | Tổng (gồm run-off) |
|---|---|---|---|---|---|
| 0.5 | $2,000 | $5,208 | $7,208 (7.2%) | $10,293 | $17,502 (17.5%) |
| 1.0 | $4,000 | $5,208 | $9,208 (9.2%) | $10,293 | $19,502 (19.5%) |
| 1.5 | $6,000 | $5,208 | $11,208 (11.2%) | $10,293 | $21,502 (21.5%) |

## 5. Đề xuất risk budget (PROPOSAL — chờ owner GO, không tự áp)

Giả định khai báo: FX margin 30:1 (majors); pip value $10/pip/lot; không hard stop (force-flat 20:00 chỉ là time-stop); crypto stress tham chiếu 5% gross; USDT≈USD theo ref đã khai báo.

1. **Budget tổng (account chung)**: max aggregate stress loss ≤ **15% equity** ($15,000 trên 100k) cho tổ hợp FX + crypto cùng bất lợi.
2. **Cap class (ràng buộc chính về leverage)**: FX gross ≤ 150% equity; crypto gross ≤ 150% equity; tổng ≤ 250% (đã ghi trong epoch_config.capital_rule, freeze trước khi thấy PnL epoch-2). Với giá hiện tại: 1.0 lot/cặp = FX gross $492k ≈ 246% — VƯỢT cap FX; 1.5 lot/cặp ≈ 369% — vượt sâu; 0.5 lot/cặp ≈ 123% — vừa cap.
3. **Lot tương ứng dưới caps**: ràng buộc là cap FX 150% → **≈ 0.5–0.6 lot/cặp**. Stress tại 0.5 lot: 200-pip cả hai cặp = $2,000 (2%) + crypto epoch-2 5% = $5,208 → tổng ≈ 7.2% vốn, còn dư budget 15%.
4. **1.0 lot/cặp** chỉ cân nhắc nếu owner nâng cap FX hoặc các crypto sleeve flat; về loss 200-pip cả hai cặp chỉ = 4% vốn — vấn đề của 1.0 lot là LEVERAGE, không phải stress-loss.
5. **1.5 lot/cặp**: loss 200-pip = 6% vốn (chấp nhận được về stress), NHƯNG gross 369% phá vỡ mọi cap đòn bẩy của portfolio chung 100k; và một ngày bất thường 500-pip cả hai cặp (kiểu CHF) = $15,000 = 100% budget. Giữ nguyên 1.5 lot trong sách shadow cũ frozen; epoch-2 cần sizing explicit thấp hơn qua amendment.
6. Sách run-off XSECT (ngoài epoch-2) đang gross $205,865 — stress 5% = $10,293 nằm NGOÀI budget epoch-2 nhưng phải hiển thị riêng trên dashboard đến khi flat.
7. Mọi con số trên là **đề xuất**; áp đặt phải đi qua amendment có GO riêng.

