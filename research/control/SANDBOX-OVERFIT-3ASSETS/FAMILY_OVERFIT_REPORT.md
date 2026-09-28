# FAMILY OVERFIT — 1 family đã research × mỗi lớp tài sản

> SANDBOX, KHÔNG phải evidence. Family lấy nguyên từ corpus owner đã research (không sáng tạo mới); grid nới rộng vượt grid frozen của cycle gốc để overfit tối đa; chọn theo IS net return; OOS 20% cuối chỉ chẩn đoán.

## CRYPTO · H-VOLCOMP-BRKOUT-v1

Baseline B&H (trung bình universe, toàn bộ 15 năm/khung): IS **8.3%**

| # | Tham số | IS Net | IS CAGR | IS Sharpe | IS MaxDD | Trades | **OOS Net** | OOS Sharpe |
|---|---|---|---|---|---|---|---|---|
| 1 | `{"bb_period":20,"bb_k":1.5,"squeeze_lb":96,"squeeze_pct":10,"vol_ratio":3.0,"donch":192,"atr_mult":2.0,"tp_mult":null,"max_hold":384}` | **6.1%** | — | — | — | 334 | **19.0%** | — |
| 2 | `{"bb_period":30,"bb_k":1.5,"squeeze_lb":192,"squeeze_pct":10,"vol_ratio":3.0,"donch":192,"atr_mult":1.5,"tp_mult":null,"max_hold":192}` | **5.1%** | — | — | — | 455 | **14.3%** | — |
| 3 | `{"bb_period":30,"bb_k":2.0,"squeeze_lb":192,"squeeze_pct":10,"vol_ratio":3.0,"donch":192,"atr_mult":1.5,"tp_mult":null,"max_hold":192}` | **5.1%** | — | — | — | 455 | **14.3%** | — |
| 4 | `{"bb_period":30,"bb_k":2.0,"squeeze_lb":192,"squeeze_pct":10,"vol_ratio":3.0,"donch":192,"atr_mult":1.5,"tp_mult":null,"max_hold":96}` | **4.9%** | — | — | — | 477 | **9.6%** | — |
| 5 | `{"bb_period":20,"bb_k":1.5,"squeeze_lb":384,"squeeze_pct":20,"vol_ratio":3.0,"donch":192,"atr_mult":1.5,"tp_mult":null,"max_hold":192}` | **4.4%** | — | — | — | 533 | **-0.1%** | — |
| 6 | `{"bb_period":30,"bb_k":2.5,"squeeze_lb":192,"squeeze_pct":20,"vol_ratio":3.0,"donch":192,"atr_mult":1.5,"tp_mult":null,"max_hold":384}` | **1.7%** | — | — | — | 487 | **8.3%** | — |
| 7 | `{"bb_period":14,"bb_k":2.5,"squeeze_lb":96,"squeeze_pct":10,"vol_ratio":3.0,"donch":192,"atr_mult":1.5,"tp_mult":2.0,"max_hold":384}` | **1.3%** | — | — | — | 515 | **-4.8%** | — |
| 8 | `{"bb_period":30,"bb_k":1.5,"squeeze_lb":96,"squeeze_pct":10,"vol_ratio":3.0,"donch":192,"atr_mult":2.0,"tp_mult":3.0,"max_hold":96}` | **1.1%** | — | — | — | 392 | **2.5%** | — |
| 9 | `{"bb_period":20,"bb_k":2.5,"squeeze_lb":192,"squeeze_pct":40,"vol_ratio":3.0,"donch":192,"atr_mult":1.5,"tp_mult":null,"max_hold":96}` | **0.5%** | — | — | — | 596 | **7.0%** | — |
| 10 | `{"bb_period":20,"bb_k":1.5,"squeeze_lb":384,"squeeze_pct":40,"vol_ratio":3.0,"donch":192,"atr_mult":1.5,"tp_mult":null,"max_hold":96}` | **0.1%** | — | — | — | 599 | **6.7%** | — |

## STOCKS · EVENT-UNWIND (NG6 anchor)

Baseline B&H (trung bình universe, toàn bộ 15 năm/khung): IS **3,614.6%**

| # | Tham số | IS Net | IS CAGR | IS Sharpe | IS MaxDD | Trades | **OOS Net** | OOS Sharpe |
|---|---|---|---|---|---|---|---|---|
| 1 | `{"K":10,"H":40,"range_thr":0.3,"part_mult":1.0,"reclaim_gap":10}` | **201.1%** | 7.6% | 7.26 | 14.9% | 2034 | **32.9%** | 3.68 |
| 2 | `{"K":10,"H":40,"range_thr":0.3,"part_mult":1.0,"reclaim_gap":21}` | **196.2%** | 7.5% | 7.03 | 15.9% | 2094 | **35.7%** | 3.59 |
| 3 | `{"K":10,"H":40,"range_thr":0.5,"part_mult":1.0,"reclaim_gap":10}` | **189.1%** | 7.3% | 7.07 | 15.3% | 1986 | **28.3%** | 3.67 |
| 4 | `{"K":10,"H":40,"range_thr":0.3,"part_mult":1.0,"reclaim_gap":5}` | **177.4%** | 7.1% | 6.83 | 13.7% | 1910 | **29.1%** | 3.17 |
| 5 | `{"K":10,"H":40,"range_thr":0.5,"part_mult":1.0,"reclaim_gap":21}` | **172.4%** | 6.9% | 6.47 | 16.7% | 2056 | **32.9%** | 3.63 |
| 6 | `{"K":10,"H":40,"range_thr":0.7,"part_mult":1.0,"reclaim_gap":21}` | **161.0%** | 6.6% | 6.51 | 15.1% | 1977 | **32.6%** | 3.56 |
| 7 | `{"K":10,"H":40,"range_thr":0.5,"part_mult":1.0,"reclaim_gap":5}` | **160.4%** | 6.6% | 6.59 | 13.1% | 1840 | **28.0%** | 3.12 |
| 8 | `{"K":10,"H":40,"range_thr":0.7,"part_mult":1.0,"reclaim_gap":10}` | **152.8%** | 6.4% | 6.59 | 13.5% | 1875 | **29.3%** | 3.44 |
| 9 | `{"K":21,"H":40,"range_thr":0.3,"part_mult":1.0,"reclaim_gap":21}` | **143.0%** | 6.1% | 6.26 | 13.5% | 1677 | **36.6%** | 4.47 |
| 10 | `{"K":21,"H":40,"range_thr":0.5,"part_mult":1.0,"reclaim_gap":21}` | **137.2%** | 5.9% | 6.31 | 13.5% | 1648 | **35.1%** | 4.39 |

## FOREX · SWING-EXTREME ABSORPTION / DIVERGENT CLV (FNG7-A2-P1)

Baseline B&H (trung bình universe, toàn bộ 15 năm/khung): IS **6.7%**

| # | Tham số | IS Net | IS CAGR | IS Sharpe | IS MaxDD | Trades | **OOS Net** | OOS Sharpe |
|---|---|---|---|---|---|---|---|---|
| 1 | `{"ext_win":20,"p_win":20,"slope_win":10,"hold":5,"div_thr":0.5}` | **17.2%** | 1.0% | 1.06 | 6.3% | 1728 | **5.6%** | 1.08 |
| 2 | `{"ext_win":20,"p_win":20,"slope_win":10,"hold":10,"div_thr":0.5}` | **15.5%** | 0.9% | 1.17 | 8.3% | 1317 | **5.3%** | 1.04 |
| 3 | `{"ext_win":10,"p_win":20,"slope_win":10,"hold":5,"div_thr":0.5}` | **10.8%** | 0.7% | 0.62 | 8.2% | 2291 | **9.2%** | 1.29 |
| 4 | `{"ext_win":20,"p_win":20,"slope_win":10,"hold":10,"div_thr":0.0}` | **9.3%** | 0.6% | 0.71 | 8.8% | 1392 | **4.5%** | 0.86 |
| 5 | `{"ext_win":20,"p_win":20,"slope_win":5,"hold":3,"div_thr":0.0}` | **9.3%** | 0.6% | 0.58 | 4.6% | 2187 | **-2.7%** | -0.47 |
| 6 | `{"ext_win":40,"p_win":20,"slope_win":10,"hold":5,"div_thr":0.5}` | **9.1%** | 0.6% | 0.69 | 4.3% | 1133 | **3.3%** | 0.70 |
| 7 | `{"ext_win":20,"p_win":20,"slope_win":10,"hold":5,"div_thr":0.0}` | **8.6%** | 0.5% | 0.52 | 7.7% | 1859 | **4.4%** | 0.80 |
| 8 | `{"ext_win":20,"p_win":20,"slope_win":10,"hold":3,"div_thr":0.5}` | **8.6%** | 0.5% | 0.61 | 2.8% | 2001 | **1.4%** | 0.26 |
| 9 | `{"ext_win":20,"p_win":20,"slope_win":10,"hold":3,"div_thr":0.0}` | **7.5%** | 0.5% | 0.49 | 3.2% | 2162 | **1.1%** | 0.19 |
| 10 | `{"ext_win":20,"p_win":20,"slope_win":10,"hold":10,"div_thr":-2.0}` | **7.1%** | 0.4% | 0.51 | 10.1% | 1562 | **0.4%** | 0.07 |

---

## Cảnh báo

1. Overfit cố ý: chọn config đẹp nhất IS từ hàng trăm/nghìn cấu hình — số IS là trần trên của may mắn.
2. Cột OOS = chẩn đoán suy giảm; chênh IS→OOS là thước đo độ ảo.
3. Chi phí xấp xỉ: crypto 6bp/side + funding 1bp/8h; stocks 3bp/side (chưa có impact theo size); FX 1 pip/side.
4. Yahoo close là split-adjusted (chưa gồm cổ tức); Binance 15m là last-trade.
5. Family giữ đúng anchor của corpus gốc nhưng **grid rộng hơn hẳn** grid frozen của cycle tương ứng — kết quả không liên quan đến gates/registry của các cycle đó.

Đầy đủ: `out/family_results_{CRYPTO,STOCKS,FOREX}.csv`.
