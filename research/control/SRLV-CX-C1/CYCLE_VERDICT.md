# CYCLE_VERDICT — SRLV-CX-C1 — REJECT_ALL (dev gates; 0 survivor; 0 OOS looks)

- Ngày: 2026-09-26. GO-2 `GO SRLV CX C1 SCORED EXECUTION` tiêu thụ tại gate;
  A7 prelaunch PASS trước đó; mọi scored computation dưới heavy lock
  (`heavy_lock.acquire`, role go2-scored-execution).
- Bằng chứng: `outcomes/FIXTURES_RUN1.json` (ALL PASS) + `outcomes/
  SCORED_RUN1.json` (status SCORED_COMPLETE) + `outcomes/RUN1_console.log`;
  engine + driver sha trong artifacts. 3 lần chạy giữ nguyên verdict REJECT
  qua các fix harness (disclosure §3).

## 1. Kết luận

**M1 SETTLE-RESOLVE — REJECT ở dev gates trên CẢ HAI pair (BTCUSDT,
ETHUSDT). Cohort đóng `REJECT_ALL`**: 1/1 cơ chế frozen bị kill; 2 slot council
đã để trống và đóng từ GO-1. **Không identity nào qua dev gates ⇒ không xin
GO-3 ⇒ sealed/prospective OOS KHÔNG bị tiêu; S1 untouched.** Tổng scored
cells: 6/18 (observed; PBO NOT_RUN <8 configs; DSR 0.0).

## 2. Số liệu quyết định (anchor N=6, base cost ×1.0)

| Metric | BTCUSDT | ETHUSDT |
|---|---|---|
| n (RT) | 1,482 (749 long / 733 short) | 1,518 (781 / 737) |
| Net @×1.0 | **−24,955.5 bps** (mean −16.8/trade) | **−33,514.9 bps** (−22.1) |
| PF | 0.651 | 0.634 |
| Net @×1.5 / ×2.0 | −32,417 / −39,878 | −41,250 / −48,986 |
| Folds F1..F4 | tất cả âm (−3,173/−9,874/−6,161/−5,747) | tất cả âm |
| Hai chiều | long −16,645 / short −8,311 | long −19,325 / short −14,190 |
| Gates FAIL | G1,G2,G3,G4,G6b,G7,G8,K-ANC | idem |
| Gates PASS | G5 (power), G6a/c/d (placebo — moot khi anchor chết) | idem |

## 3. Kill laws bắn (nguyên văn freeze)

1. **G1–G4**: net<0 @×1.0; PF<1.20; 0/4 folds positive; net<0 @×1.5 — cả hai
   pair. Không rescue theo luật.
2. **K-CTRL (G6b) — inverted out-earn anchor trên CẢ HAI pair**: BTC inverted
   −4,889 vs anchor −24,956; ETH inverted **+2,573 (PF 1.035)** vs anchor
   −33,515. Chiều continuation (P1-B ride) là chiều "đúng" hơn — đúng như
   skeptic tiên lượng (prior CNG2-A5 settlement-clock chết rho 0.4178/0.4872;
   PSV1-Donchian CONTROL_OUTEARNED_ANCHOR). Cơ chế "settlement forced-flow bị
   hấp thụ rồi đảo chiều" KHÔNG tồn tại trên dữ liệu này; dòng settlement
   adjacency nếu có thì thiên về continuation, không phải absorption.
3. **K-ANC — |rho| > 0.20**: BTC vs rev24 = 0.2483; ETH vs bandfade = 0.2565
   (còn lại ≤0.12). Daily-PnL correlation với dead-family representations vượt
   thanh immovable.
4. **G7**: baselines nghiền anchor (long-hold +64,758 / +114,166 bps; trend
   SMA720 +89,665 / +121,359 bps với funding measured trừ đúng).
5. G8 fail-closed: không có positive PnL để tập trung (concentration N/A).
6. Diagnostics nhất quán với cái chết: delay-1 cũng âm; ungated cũng âm;
   placebo ±4h (trùng nhau do chu kỳ 8h —披露: +4h ≡ −4h trên grid 8h) cũng
   âm; placebo-levels âm; block-shuffle p=1.0 (BTC); weekend/weekday đều âm;
   mọi giờ UTC đều ≈ âm (chỉ 2 bucket nhỏ dương — không đổi kết luận).
7. DSR = 0.0 (n_days 1,189/1,172; N=6 trials). Worst-settlement-inclusive:
   BTC −69,416 / ETH −87,601 bps.

## 4. Fixtures (tất cả PASS trước scored run — fail-closed đã chứng minh qua
2 lần chạy bị chặn trước đó)

F-GRID (8h đều, hour-aligned) · F-P1A-FLAT (0 vi phạm nắm settlement —
funding ≡ 0 đúng cấu trúc) · F-P1-OFFBYONE (trigger ≥ j+7) · F1 truncation
0/512 mismatch · F2 future-mutation 0/25 · F4 non-vacuity 4.06%/4.16% ≥ 2% ·
power ≥100/chiều/pair · F5 leak-scan.

## 5. Disclosure kỷ thuật (P-19)

1. Fixture harness được sửa 2 lần TRƯỚC scored run thành công (so exit-fields
   thay vì decision-fields — sai thiết kế test, engine đúng; hằng số warmup 35
   thay bound nguyên lý c_bar≥23). Cả hai lần scored run bị chặn fail-closed.
2. Bug nạp funding: ETH lấy nhầm cột interval (r[1]) và BTC chia đôi ms/ns —
   chỉ ảnh hưởng số baselines/diagnostic, KHÔNG ảnh hưởng PnL anchor (funding
   ≡ 0 theo pin-10, fixture chứng minh). Đã sửa và chạy lại sạch; verdict
   bất biến qua 3 lần chạy.
3. Pin-10 (pre-outcome): anchor = subset không nắm settlement nào — sửa mâu
   thuẫn nội tại proposal (entry literal có thể nắm qua S_k); biến thể literal
   + measured funding là diagnostic: cũng âm (BTC −28,826 / ETH −38,102 bps).
4. A4 ±4h trùng nhau trên grid 8h ([S+3,S+7] ≡ [S'−5,S'−1]) — một placebo,
   không phải hai.

## 6. Bài học mang sang failure memory (đề xuất A7 terminal)

- Settlement-window sweep-reclaim absorption (payer: carry-forced
  deleveraging) DEAD trên BTC/ETH 1h 2020-2026 sau phí DECLARED 5bps+1tick —
  đảo chiều inverted menos sai hơn nhưng ETH inverted chỉ PF 1.035 (~breakeven
  sau stress) — không phải entry point cho cohort sau (re-clock/re-label cấm).
- F-0 revival clause qua "settlement schedule = new information layer" đã
  được cho cơ hội trọn vẹn và chết ở measured outcome — lesson cho skeptic
  court: prior CNG2 đã đúng.
- Cohort tiếp theo chỉ mở với observable/nguồn/giả thuyết payer mới có bằng
  chứng; stop-condition (a) hai cohort liên tiếp áp dụng từ master §11 cho
  track CX khi cohort-2 (nếu có) cũng rỗng.
