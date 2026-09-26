# TRIAL_FREEZE — SRLV-CX-C1 GO-1 (sha-pinned trước mọi scored computation)

- Freeze bởi Lead (A1) từ council verdicts 2026-09-26: PROPOSAL_P1/P2 +
  SKEPTIC_F0_C1_REPORT + COSTAUDIT_F5_C1_REPORT + PITAUDIT_F2_C1_REPORT +
  handoffs (schema zcode_orch_v3_handoff@1) trong `c3_council/`.
- Budget freeze: **6 scored cells** (1 cơ chế × 6 arms). Slot 2–3 **TRỐNG,
  đóng cho same-family replacement trong cohort này** (skeptic ruling).
  0 PnL đã được nhìn bởi bất kỳ lane nào trước freeze này.

## M1 — SRLV-CX-C1-M1 "SETTLE-RESOLVE" (từ P1-A; events P1-B = ride arm)

| Trường | Pin (frozen) |
|---|---|
| Loại | H3 sweep-then-absorb tại pivot levels,restricted settlement-adjacent windows; PROXY_NOT_ORDERBOOK |
| Universe | **BTCUSDT, ETHUSDT** (1h UTC klines). SOL/BNB arms BLOCKED cohort này (spread census + funding staging thiếu — COSTAUDIT) |
| Clock/bar label | 1h UTC, bar label = UTC open time (pin P0) |
| Level | Pivot swing confirmed: strict `low[j] < low[j+6]` (mirror high); N=6 closed bars; `t_known` = close j+6; trigger sớm nhất j+7 (off-by-one proven, F-P1-OFFBYONE) |
| Window | W_k = [S_k−1h, S_k+3h], S_k = grid 00/08/16 UTC (F-GRID verify trước scoring). DEFECT ghi nhận: W_k phủ 62.5% giờ (COSTAUDIT) — adjudicator là ungated-clock kill law (bên dưới), KHÔNG thu hẹp post-hoc |
| Entry | Cross-bar sequence: close-through level tại bar t (sweep), reclaim close inside tại t+1, fill open t+2; hai chiều (long/short mirror) |
| Exit | Time-stop 4 held bars; flat-by-settlement HARD (pin P1-1: exit open precompute; entry bị skip nếu exit open ≤ entry open); base book funding ≡ 0 |
| Arms (6 cells) | A1 anchor (two-sided); A2 neighbour-1 (N=4); A3 neighbour-2 (N=10); A4 causal control = settlement-shifted ±4h placebo windows; A5 inverted control (sign-flip; mirror break-acceptance events là ride-arm báo cáo kèm, không phải arm riêng); A6 baseline set (cash 0 / long-hold cùng cost book / trend reference) |
| F-1 shadows bắt buộc (bar 0.20, frozen representation) | CNG2-A5-P1 (0.4178), CNG2-A5-P2 (0.4872), PSV1-Donchian, Donchian-168 (P2-M2 làm shadow), PDHLOC/band-fade, displaced-fade |
| Kill laws thêm (skeptic 14-item, rút gọn) | (i) ungated-clock arm: nếu bản KHÔNG window cũng sống ⇒ KILL (window không mang thông tin); (ii) placebo windows ±4h tái tạo ≥0.5× ⇒ VETOED_FICTIONAL_COUNTERPARTY; (iii) placebo levels (relabel synthetic) sống ⇒ kill; (iv) block-shuffle + delay-1 (Q-4); (v) per-boundary-hour payer-label check; (vi) G8 per-direction folds; pooling: **per-pair primary**, pooled = diagnostic only (pin trước outcome) |
| Cost book | Fee = DECLARED 5 bps + 1 tick/side (tick đo: BTC 0.1, ETH 0.01 USDT — gcd klines); funding = MEASURED path (structural-zero base; stress arm BTC/ETH: BTC +11.80%/yr, worst −30.0bp; ETH +13.95%/yr, worst −35.63bp); RT bps base/×1.5/×2.0: BTC 10.06/15.08/20.11, ETH 10.24/15.35/20.47; worst-settlement-inclusive (BTC 50.19 / ETH 56.46) BÁO kèm, không phải gate base; ceiling convention PINNED = measured-distribution |
| Power | ≥100 closed RT/direction/pair; census upper bound 1,157–2,085 RT/dir/pair ⇒ khả thi; dưới floor ⇒ NOT_RUN_THIN, không relax |
| Folds | F1 2020-01..2021-04 · F2 2021-05..2022-12 · F3 2023-01..2024-12 · F4 2025-01..2026-08; force-flat mọi boundary; mọi số dev mang ANCESTRY_EXPOSED_DEV |
| Fixtures trước scored run | F1 truncation byte-identity (512 decision times) · F2 future-mutation · F3 delay-pair · F4 non-vacuity ≥2% + census vs 100-RT · F5 dry-run leak scan · F6 independent-impl record diff (A7) · F7 fold force-flat · per-mech: F-P1A/P1B-FLAT, F-P1-OFFBYONE, F-P1-PARTITION, F-ATR-INSTANT, F-GRID, F-GAP, F-WARMUP, F-PRECEDENCE |
| Nhãn | PAPER_TIER, SINGLE_VENUE_PANEL, ANCESTRY_EXPOSED_DEV, PROXY_NOT_ORDERBOOK, FILL_QUALITY_CLASS_DECLARED, FUNDING_PATH_STRESSED (stress arm) |

## Council verdicts (ledger rows)

| ID | Verdict | Lý do chính |
|---|---|---|
| P1-A SETTLE-SWEEP-ABSORB | FREEZABLE (conditional) → freeze thành M1 | revival clause: settlement schedule = measured exogenous new layer (FIXCERT precedent); skeleton gần dead class #1 — sống nhờ event×window interaction, battery fail-closed |
| P1-B SETTLE-BREAK-CASCADE | VETO_VARIANT_SAME_FAMILY (standalone) | Donchian skeleton + fenced cascade payer; sống làm ride-arm/inverted của M1 |
| P2-M1 PDSR | VETO_VARIANT_SAME_FAMILY | payer verbatim = "stop beyond visible extremes" (TRACKA2 fence); prior-day calendar band = PDHLOC |
| P2-M2 WSA | VETO_VARIANT_SAME_FAMILY | Donchian(168) re-parameterization |

## Trạng thái gate tiếp theo

1. **A7 prelaunch** (fresh context): audit freeze này + fixtures spec; REFUSED
   = remediation arc.
2. Triển khai fixtures + exact-arm dry-run (chưa PnL headline).
3. **DỪNG.** Scored run chỉ sau khi owner gõ
   `GO SRLV CX C1 SCORED EXECUTION` (GO-2, phrase đã đăng ký NOT consumed).
