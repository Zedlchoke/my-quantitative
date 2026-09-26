# PLAN_REVISION_DIFF_1 — SRLV-PROGRAM-V1 — theo owner revision instruction 2026-09-26

- Baseline: bản bàn giao đầu (pre-revision, lưu /tmp/srlv_pre); post: bản sau revision (round 1: 3 điểm owner; round 2: 3 finding A7 — relabel ETH 15m row, G5→G8 numbering, snapshot count).
- Đã audit A7 fresh-context: PASS_WITH_FINDINGS (4 finding non-blocking; finding 4 = provenance note về VERDICT_session2.md lịch sử, không sửa — không SRLV artifact nào dựa vào suy luận minTick→all-in).

## diff plans/PLAN_srlv_program_v1.md
--- /tmp/srlv_pre/PLAN_srlv_program_v1.md	2026-09-26 14:09:36
+++ plans/PLAN_srlv_program_v1.md	2026-09-26 14:10:18
@@ -190,7 +190,7 @@
 | Reopener | Bằng chứng cần | Mở gì |
 |---|---|---|
 | **R2** nguồn bid/ask độc lập | TrueFX registration / OANDA v20 practice / Dukascopy written consent (owner action) + bytes on disk + license gate PASS + cross-source PIT seam check | observable tick-level event-time; nguồn thứ hai cho spread/cost authority; limb replication (iii) nguồn-độc-lập |
-| **R1** broker cost authority | two-sided market-data subscription + Flex statement (commission + overnight interest measured) | commission/swap measured book; hạ ceiling all-in;解锁 các cơ chế biên mỏng hiện chết F-5 |
+| **R1** broker cost authority | two-sided market-data subscription + Flex statement (commission + overnight interest measured) | commission/swap measured book; all-in được ĐO — có thể xác nhận CAO HƠN hoặc THẤP HƠN mọi ước tính hiện có (hiện executable spread NOT_SUBSCRIBED, commission NOT_RUN ⇒ all-in chưa đo); cơ chế chết F-5 chỉ được xét lại bằng số đo, không theo chiều định trước |
 | **R3** financing band | broker-grade swap data cited | class multi-day hold / carry (đang BLOCKED F4) |
 | **R5** information layer mới | artifact có authority (例: per-fill s_open non-PnL; depth collector đạt floors kiểu lane-C) | observable mới qua D2 |
 | **R4** (không phải reopener scoring) | một identity qua dev gates | slate amendment USDCHF/new pairs |
@@ -200,9 +200,12 @@
   kết quả đúng, không phải thất bại (Q-16).
 - Tái chạy cùng panel Dukascopy cũ (3 cặp exposed + 2 cặp dev-exposed) với
   cơ chế cùng skeleton/payer = bị F-0 kill ngay; không được gọi là discovery.
-- Ngưỡng cost đã pin (P3-A frozen ≤0.41 pip crossing @k=2.0) không re-derive;
-  chỉ được xét lại bằng nguồn/venue hợp lệ mới chứng minh TOÀN BỘ chi phí
-  thực thi dưới ngưỡng — không assume maker/mid/no-slippage.
+- Ngưỡng cost đã pin (P3-A frozen ≤0.41 pip crossing @k=2.0) không re-derive.
+  Lưu ý bằng chứng hiện tại: minTick 0.5 pip (đo 5 cặp) chỉ là fact hình học
+  tick — KHÔNG được suy ra executable spread hay all-in cost; all-in thực sự
+  CHƯA ĐO (two-sided NOT_SUBSCRIBED, commission NOT_RUN). R1 là bước đo;
+  kết quả có thể cao hơn hoặc thấp hơn, và cơ chế chỉ được xét lại bằng số đo
+  đó — không assume maker/mid/no-slippage ở cả hai chiều.
 
 ## 7. Hợp đồng cost (mỗi track; thiếu thành phần trọng yếu ⇒ fail-closed)
 
@@ -223,10 +226,12 @@
 
 ### 7.2 CRYPTO
 
-1. Measured book: funding per-settlement path (native, while held) — dual
-   book với frozen constant; fee taker 5 bps + 1 adverse tick (anchor CHR3F)
-   tới khi validate vs fills; spread census theo giờ fill từ
-   bookTicker/aggTrades (coverage verify; thiếu ⇒ BLOCKED).
+1. Cost books tách lớp: funding = MEASURED (per-settlement path, native,
+   while held; dual book với frozen constant); fee 5 bps + 1 adverse tick =
+   DECLARED book (venue-published tier floor + convention tick, freeze từ
+   CHR3F; lên lớp measured chỉ khi validate vs fills — Q-8); spread census
+   theo giờ fill từ bookTicker/aggTrades (coverage verify; thiếu ⇒ BLOCKED).
+   Declared book không bao giờ override measured book.
 2. Funding-path stress: 24.7% settlements âm trong downtrend; worst
    −0.30%/8h ≈ 2.5 fee RT; miss-N-settlement + gap-reopen bất lợi (DECLARED).
 3. Gap/outage/latency/liquidity-in-stress: DECLARED bands + ×1.5/×2.0.

## diff plans/PLAN_srlv_fx_cohort_1.md
--- /tmp/srlv_pre/PLAN_srlv_fx_cohort_1.md	2026-09-26 14:09:36
+++ plans/PLAN_srlv_fx_cohort_1.md	2026-09-26 14:10:26
@@ -55,9 +55,11 @@
   (Dukascopy vs nguồn mới: clock, day-boundary, DST, scale; khác biệt ghi
   `SEAM_DISCLOSED` theo DATACOST critic condition 5).
 - Output: `FRONTIER_REOPENING_VERDICT.md` — nêu CHÍNH XÁC thông tin mới nào
-  mở lại frontier, cơ chế nào nó hợp lệ hóa, và ceiling cost mới nếu R1/R3
-  hạ. Không reopener ⇒ terminal `BLOCKED_FRONTIER_NOT_REOPENED` (first-class
-  close), báo owner, không mở council.
+  mở lại frontier, cơ chế nào nó hợp lệ hóa, và ceiling all-in được đo lại
+  nếu R1/R3 có số — kết quả đo có thể CAO HƠN hoặc THẤP HƠN mọi ước tính hiện
+  có; không chiều nào được định trước. Không reopener ⇒ terminal
+  `BLOCKED_FRONTIER_NOT_REOPENED` (first-class close), báo owner, không mở
+  council.
 
 ### Phase D1 — Data/license/PIT/cost/power gate per pair
 

## diff plans/PLAN_srlv_cx_cohort_1.md
--- /tmp/srlv_pre/PLAN_srlv_cx_cohort_1.md	2026-09-26 14:09:36
+++ plans/PLAN_srlv_cx_cohort_1.md	2026-09-26 14:20:33
@@ -59,34 +59,48 @@
 - Verify per pair × plane × window chống registry tại GO-1 (trackb §4.2
   precedent): BTC 1h 2020–2026-08 và 15m 2024-08–2026-08 outcome-exposed
   (CHR3F staged+scored); ETH 1h exposed (V1 terminal, V2 lane B); SOL/BNB 1h
-  baseline-exposed; plane 15m/1m chưa score = `OUTCOME_FREE_PLANE` (verify).
-- Dev evidence trên window exposed mang `ANCESTRY_EXPOSED_DEV` — dùng để KILL
-  và engineering, không bao giờ tự bằng chứng promote.
-- Sealed OOS của cohort: (a) window verify-chưa-tiêu trên plane mới (nếu còn
-  sau verification), HOẶC (b) **prospective accumulation sau freeze**
-  (decision-count gates umbrella §5.12 D13/D26/D52) — trackb §4.2 đo rằng
-  history BTCUSDT gần như trọn bị exposed; kỳ vọng thực tế là (b).
+  baseline-exposed; plane 15m/1m chưa stage = `ANCESTRY_EXPOSED_RECLK` —
+  CÙNG lịch sử giá đã outcome-exposed, đổi timeframe KHÔNG tạo surface
+  outcome-free (re-clock veto Q-3).
+- Dev evidence trên window exposed (kể cả plane 15m/1m) mang
+  `ANCESTRY_EXPOSED_DEV` — dùng để KILL và engineering, không bao giờ tự
+  bằng chứng promote.
+- Sealed OOS của cohort: một history window chỉ được dùng one-look nếu
+  verification chứng minh chính LỊCH SỬ GIÁ window đó chưa từng bị
+  search/score ở BẤT KỲ granularity nào (không phải vì đổi plane); với 4 cặp
+  này kỳ vọng thực tế là không còn ⇒ **prospective accumulation sau freeze**
+  (decision-count gates umbrella §5.12 D13/D26/D52) — trackb §4.2 precedent.
 - Không đụng: `ETHUSDT-OPEN-SEARCH-V2` (ACTIVE, chờ GO, S1 sealed — không
   tiêu phrase/surface của nó), `CRYPTO-HISTORICAL-REPLICATION-3F-V1` (đang
   scored; heavy lock machine-wide — chỉ dispatch khi FREE_PROVEN),
   `PROSPECTIVE-SHADOW-V1`/shadow workers (không restart, không sửa).
 
-### 2.3 G5 structural disclosure (binding)
+### 2.3 Concentration gate — G8 trong bộ gate cohort này (binding)
 
-BTC-H4-BAND-RISK đo: KHÔNG long book nào trên BTC 2020–2026 qua fold-
-concentration 0.50 (ALWAYS_ON 0.5348 / TREND_LF 0.7028 / C3 0.7117). Hệ quả:
+Tiền lệ đo được (từ BTC-H4-BAND-RISK, gate concentra historically gọi G5 ở
+cycle đó): KHÔNG long book nào trên BTC 2020–2026 qua fold-concentration
+0.50 (ALWAYS_ON 0.5348 / TREND_LF 0.7028 / C3 0.7117). Trong bộ gate
+G1–G8 của SRLV, concentration là G8. Hệ quả:
 mọi cơ chế long-biased trên BTC phải (a) chứng minh short-capability (hai
 chiều) trong anchor definition, HOẶC (b) freeze concentration-statistic
 thay thế có biện luận khoa học TRƯỚC outcome (umbrella §5.14), HOẶC (c) chỉ
 định nghĩa kết luận trên prospective (không claim từ history BTC-long).
+**Ranh giới không được vượt: thanh 0.50 KHÔNG bị hạ vì BTC-long fail** —
+việc BTC-long đã fail G5 là kết quả đã biết, nên mọi thay thế statistic phải
+tồn tại trong luật TRƯỚC outcome của identity đó (concession có sẵn từ
+umbrella §5.14, freeze cùng trial freeze, sha-pinned); thay sau khi thấy
+kết quả = parameter rescue, cấm (K-CONC + charter §1.2).
 
 ### 2.4 Funding cost law
 
-- Cost book measured bắt buộc: funding per-settlement theo path thật (BTC
-  11.798%/yr anchor = 7.824× hằng số cũ) + dual-book frozen constant để đối
-  chiếu; funding-path stress (24.7% settlements âm trong downtrend; worst
-  −0.30%/8h); fee taker 5 bps + 1 adverse tick tới khi validate vs fills;
-  mọi arm unlevered 1x (levered/borrow/liquidation BLOCKED).
+- Cost books tách lớp bằng chứng: funding = MEASURED (per-settlement theo
+  path thật; BTC 11.798%/yr anchor = 7.824× hằng số cũ; dual-book với frozen
+  constant để đối chiếu; funding-path stress 24.7% settlements âm trong
+  downtrend, worst −0.30%/8h); fee 5 bps + 1 adverse tick = DECLARED book
+  (venue-published tier floor + convention tick, freeze từ CHR3F; lên lớp
+  measured chỉ khi validate vs fills — Q-8); spread = measured census nếu dữ
+  liệu đủ, else BLOCKED. Declared không override measured; mọi arm unlevered
+  1x (levered/borrow/liquidation BLOCKED).
 
 ## 3. Phases & gates
 
@@ -105,8 +119,11 @@
 ### Phase C2 — Exposure verification
 
 - Đối chiếu registry + HYPOTHESIS_LEDGER: bảng pair × plane × window ⇒ phân
-  loại exposure; chọn home pair + dev folds + sealed/prospective OOS CHỈ từ
-  window verify-sạch; artifact `EXPOSURE_VERIFICATION_C1.md` sha-pinned.
+  loại exposure; plane 15m/1m mặc định `ANCESTRY_EXPOSED_RECLK` (không phải
+  outcome-free). Chọn home pair + dev folds từ dev được phép; OOS history
+  one-look chỉ với window chứng minh chưa-exposed ở cấp LỊCH SỬ GIÁ (không
+  phải đổi plane); else OOS = prospective; artifact
+  `EXPOSURE_VERIFICATION_C1.md` sha-pinned.
 
 ### Phase C3 — Council outcome-blind + falsifiers + trial freeze (GO-1, rồi DỪNG)
 
@@ -122,15 +139,17 @@
 ### Phase C4 — Scored walk-forward (GO-2, heavy lock)
 
 - Như D3 FX + funding-path accounting per settlement; gates G1–G8 +
-  margin-to-fail; G5 với §2.3 disclosure; dual cost book (measured path /
+  margin-to-fail; G8 (concentration) với §2.3 disclosure; dual cost book (measured path /
   frozen constant) báo song song; per-pair, per-fold, toàn panel,
   leave-one-out.
 
 ### Phase C5 — Sealed/prospective OOS one-look (GO-3, MỘT LẦN)
 
-- Nếu còn window verify-sạch: one-look như FX (membership sha-frozen).
-- Nếu không còn: prospective accumulation sau freeze theo D13/D26/D52; kết
-  luận tối đa trong history = `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`.
+- Nếu C2 chứng minh còn window chưa-exposed ở cấp lịch sử giá (không phải
+  bằng đổi plane): one-look như FX (membership sha-frozen).
+- Kỳ vọng thực tế (và mặc định an toàn): prospective accumulation sau freeze
+  theo D13/D26/D52; kết luận tối đa trong history =
+  `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`.
 
 ### Phase C6 — A7 terminal + two-half close
 

## diff research/control/SRLV-PROGRAM-V1/OUTCOME_EXPOSURE_MAP.md
--- /tmp/srlv_pre/OUTCOME_EXPOSURE_MAP.md	2026-09-26 14:09:36
+++ research/control/SRLV-PROGRAM-V1/OUTCOME_EXPOSURE_MAP.md	2026-09-26 14:20:41
@@ -37,7 +37,7 @@
 | USDCHF | — (không corpus ở bất kỳ đâu) | — | `OUTCOME_FREE` nhưng `BLOCKED_DATA_LICENSE` | replication-transfer surface; download chỉ sau data gate + license posture; R4: chỉ có nghĩa sau khi một identity qua dev gates |
 | (mọi cặp) | TrueFX tick | — | `BLOCKED` (0 bytes; owner R2) | replication limb nguồn-độc-lập khi mở |
 | (mọi cặp) | OANDA v20 practice | — | `BLOCKED` (0 bytes; owner R2) | như TrueFX |
-| (mọi cặp) | IBKR IDEALPRO | minTick 0.5 pip đo được 5 cặp | `BLOCKED_BROKER_COST_AUTHORITY` (V2 two-sided NOT_SUBSCRIBED; commission/swap NOT_RUN) | cost authority khi owner mở subscription + Flex |
+| (mọi cặp) | IBKR IDEALPRO | minTick 0.5 pip đo được 5 cặp (chỉ là fact hình học tick, KHÔNG phải đo executable spread/all-in) | `BLOCKED_BROKER_COST_AUTHORITY` (V2 two-sided NOT_SUBSCRIBED; commission/swap NOT_RUN ⇒ all-in chưa đo) | cost authority khi owner mở subscription + Flex; khi đó all-in được ĐO — có thể xác nhận cao hơn hoặc thấp hơn ước tính |
 | EURUSD | TwelveData mid | sample | reconciliation-only (matrix L5) | không bao giờ evidence |
 
 ### 1.1 Cost authority hiện có (FX)
@@ -47,8 +47,11 @@
   0.9–1.0; USDCAD 1.1–1.2; stressed RT 3.6/4.4 pips AUD/CA; USDCHF: chưa có).
 - Commission/slippage-beyond-spread: `DECLARED_UNMEASURED` — mọi verdict FX
   mang `PAPER_TIER + SINGLE_SOURCE_PANEL + FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`.
-- Ngưỡng đã pin (P3-A, frozen): all-in crossing ≤ 0.41 pip @k=2.0 — đo-chết
-  tại IBKR (minTick 0.5 pip); không re-derive sau khi có số.
+- Ngưỡng đã pin (P3-A, frozen): all-in crossing ≤ 0.41 pip @k=2.0; không
+  re-derive sau khi có số. minTick 0.5 pip (đo 5 cặp) chỉ là fact hình học
+  tick — KHÔNG được suy ra thành executable spread hay all-in cost; executable
+  spread đang NOT_SUBSCRIBED, commission/swap NOT_RUN ⇒ all-in thực sự CHƯA
+  ĐO. R1 là bước đo; kết quả có thể cao hơn hoặc thấp hơn mọi ước tính hiện có.
 
 ## 2. CRYPTO — 4 cặp candidate universe (Binance USDⓈ-M)
 
@@ -63,10 +66,10 @@
 | BTCUSDT | Vision um klines 1h | 2020-01..2026-08 | `OUTCOME_EXPOSED` (BTC-H4 ×4 trên trục giá 2020-2026; PSV1 sleeves; ETH-V1/V2 E1 gate input; CHR3F baselines) | ancestry; fixture; cost/funding authority. Không phải OOS cho các họ đã chết |
 | BTCUSDT | catalog 15m LAST | 2024-08..2026-08 | `OUTCOME_EXPOSED` (CHR3F staged + scored trên 2024-08-20..2026-08-21) | ancestry/fixture; verify lại tại GO-1 |
 | ETHUSDT | Vision um klines 1h + funding | 2020-01..2026-08 | `OUTCOME_EXPOSED` (ETHUSDT-OPEN-SEARCH-V1 terminal 8 cells; V2 lane B 4 scored cells; ETHBTC ratio G6-killed) | ancestry; fixture; funding authority |
-| ETHUSDT | catalog 15m LAST | 2024-08..2026-08 | verify tại GO-1 (chưa thấy scored outcome trên plane này) | khả năng dev cho identity mới (sau verify) |
+| ETHUSDT | catalog 15m LAST | 2024-08..2026-08 | `ANCESTRY_EXPOSED_RECLK` — cùng lịch sử giá 2024-08..2026-08 đã outcome-exposed ở 1h (V1 terminal, V2 lane B); đổi plane không tạo surface outcome-free | chỉ `ANCESTRY_EXPOSED_DEV` (kill/engineering); KHÔNG phải OOS |
 | SOLUSDT | Vision um klines 1h | 2020-09..2026-08 (floor 2020-09-14) | `OUTCOME_EXPOSED_baseline` (chỉ xsect baselines V11/V14/funding-carry; không có search directional riêng) | dev cho identity mới với ancestry disclosure |
 | BNBUSDT | Vision um klines 1h | 2020-02..2026-08 (floor 2020-02-10) | `OUTCOME_EXPOSED_baseline` (như SOL) | như SOL |
-| (4 cặp) | Vision klines 15m / 1m (chưa stage) | 2020..2026-08 | `OUTCOME_FREE_PLANE` (chưa có scored outcome — verify tại GO-1) | dev plane mới; KHÔNG tự động là OOS cho họ đã tiêu 1h |
+| (4 cặp) | Vision klines 15m / 1m (chưa stage) | 2020..2026-08 | `ANCESTRY_EXPOSED_RECLK` — CÙNG lịch sử giá đã outcome-exposed ở 1h; đổi timeframe KHÔNG tạo surface outcome-free (re-clock veto Q-3) | chỉ dev dạng `ANCESTRY_EXPOSED_DEV` (kill/engineering, không phải bằng chứng promote); KHÔNG được dùng làm OOS; OOS thật = prospective sau freeze |
 | (4 cặp) | funding (fapi + Vision cross-check) | floor fapi 2020-07-18 (SOL 2020-09-13); conflict ⇒ symbol-month EXCLUDED | measured authority (BTC 11.798%/yr = 7.824× hằng số cũ; ETH 7,305 settlements floor-exact) | cost book measured bắt buộc |
 | (4 cặp) | bookTicker / aggTrades (granary có sẵn một phần) | TBD | verify coverage tại data gate; thiếu ⇒ BLOCKED | spread/slippage census điều kiện theo giờ fill |
 | (mọi cặp) | liquidationSnapshot / OI lịch sử | 404 / lookback ≈41.6h | `BLOCKED_UNCONSTRUCTIBLE` | không dùng làm observable; forced-flow phải là proxy có falsifier |
@@ -109,8 +112,9 @@
    transfer (không phải basis).
 3. Crypto: EOS1-E1 (BTC-price-state gates cho ETH) + EOS1-E2 (ratio gates,
    kể cả symbol-swap) family-dead; PSV1-BTC_H4-Donchian continuation
-   CONTROL_OUTEARNED_ANCHOR; G5 fold-concentration 0.50 đo là structurally
-   unpassable cho BTC-long 2020-2026; 11/11 crypto-ng proposals chết ở rho
+   CONTROL_OUTEARNED_ANCHOR; fold-concentration 0.50 (số hiệu G5 ở cycle gốc,
+   G8 trong bộ gate SRLV) đo là structurally unpassable cho BTC-long
+   2020-2026; 11/11 crypto-ng proposals chết ở rho
    bar 0.20; BTC-BEAR: Confirmation-Lag Front-Run VETOED_FICTIONAL_
    COUNTERPARTY, Mark-Trigger Catch-Down VETOED ×3; V10 M01-AGGRESSOR-
    ABSORPTION-PANEL BLOCKED_PRELAUNCH.

## diff research/control/SRLV-PROGRAM-V1/DATACOST_FEASIBILITY_MATRIX.md
--- /tmp/srlv_pre/DATACOST_FEASIBILITY_MATRIX.md	2026-09-26 14:09:36
+++ research/control/SRLV-PROGRAM-V1/DATACOST_FEASIBILITY_MATRIX.md	2026-09-26 14:09:59
@@ -16,7 +16,7 @@
 | AUDUSD | OK — 2021-01..2026-06 (2,007 files/side, sha manifest); dev exposed cho range-fade class | như trên | PARTIAL — như trên; observable MỚI phải qua D2 | PARTIAL — conditional crossing đo 0.9/1.0 pip; stressed RT 3.6; ceiling law: band phải rõi ~2× stressed RT (~7 pips) | NOT_RUN | `ELIGIBLE_DEV_FOR_NEW_OBSERVABLE` — dev được cho identity mới; holdout 2026-H1 SEALED |
 | USDCAD | OK — như AUDUSD | như trên | như AUDUSD | PARTIAL — crossing 1.1/1.2; stressed RT 4.4 | NOT_RUN | `ELIGIBLE_DEV_FOR_NEW_OBSERVABLE` (như AUDUSD) |
 | USDCHF | BLOCKED — không có corpus ở bất kỳ worktree nào; data gate chưa từng chạy | NOT_RUN — cần posture quyết (Dukascopy owner-directive mở rộng hay TrueFX/OANDA) | NOT_RUN | BLOCKED — không có spread curve đo | NOT_RUN | `BLOCKED_DATA_LICENSE` — replication-transfer surface; mở theo R4 (sau khi một identity qua dev gates) + data gate đầy đủ |
-| (nguồn độc lập mọi cặp) | BLOCKED — TrueFX/OANDA/consent = 0 bytes | NOT_RUN — owner R2 | — | BLOCKED — IBKR: two-sided NOT_SUBSCRIBED, commission/swap NOT_RUN, minTick 0.5 pip đo | — | `BLOCKED_SOURCE_AUTHORITY` — đúng các reopening condition R1/R2/R3 |
+| (nguồn độc lập mọi cặp) | BLOCKED — TrueFX/OANDA/consent = 0 bytes | NOT_RUN — owner R2 | — | BLOCKED — IBKR: two-sided NOT_SUBSCRIBED, commission/swap NOT_RUN ⇒ all-in CHƯA ĐO (minTick 0.5 pip chỉ là fact hình học tick, không suy ra được all-in) | — | `BLOCKED_SOURCE_AUTHORITY` — đúng các reopening condition R1/R2/R3 |
 
 **Kết luận FX (frontier):** trên panel hiện có (Dukascopy M1, 3 cặp exposed
 trọn window + 2 cặp exposed-dev + USDCHF trống), KHÔNG có nguồn/bề mặt mới
@@ -29,11 +29,11 @@
 
 | Cặp | D | L | PIT | C | P | Verdict sơ bộ |
 |---|---|---|---|---|---|---|
-| BTCUSDT | OK — Vision um 1h 2020-01..2026-08 (80 zips); catalog 15m 2024-08..2026-08 (CHR3F đã score) | PARTIAL — keyless public archive, posture PIT_USABLE kế thừa; license text chưa capture ⇒ data gate phải ghi posture từng nguồn | PARTIAL — kline event-time OK; funding PIT theo settlement; KHÔNG order-book/liq/OI ⇒ sweep/zone = PROXY_NOT_ORDERBOOK | PARTIAL-STRONG — funding measured (11.798%/yr BTC); fee anchor 5 bps + 1 tick (CHR3F frozen); spread/slippage cần census theo giờ fill từ bookTicker/aggTrades (verify coverage); thiếu ⇒ BLOCKED | NOT_RUN | `ELIGIBLE_DEV_ANCESTRY_EXPOSED` — dev được với ancestry disclosure; KHÔNG phải OOS |
+| BTCUSDT | OK — Vision um 1h 2020-01..2026-08 (80 zips); catalog 15m 2024-08..2026-08 (CHR3F đã score) | PARTIAL — keyless public archive, posture PIT_USABLE kế thừa; license text chưa capture ⇒ data gate phải ghi posture từng nguồn | PARTIAL — kline event-time OK; funding PIT theo settlement; KHÔNG order-book/liq/OI ⇒ sweep/zone = PROXY_NOT_ORDERBOOK | PARTIAL — funding MEASURED (11.798%/yr BTC); fee 5 bps + 1 adverse tick = DECLARED book (venue-published tier floor + convention tick, freeze từ CHR3F; chưa validate vs fills — Q-8); spread/slippage cần census theo giờ fill từ bookTicker/aggTrades (verify coverage); thiếu ⇒ BLOCKED | NOT_RUN | `ELIGIBLE_DEV_ANCESTRY_EXPOSED` — dev được với ancestry disclosure; KHÔNG phải OOS |
 | ETHUSDT | OK — 1h + funding 2020-01..2026-08 (ETH archive local, 7,305 settlements floor-exact); 15m catalog 2024-08+ (verify exposure) | như trên | như BTC | PARTIAL-STRONG — funding measured; ETH-V1 đã đo funding floor-exact | NOT_RUN | `ELIGIBLE_DEV_ANCESTRY_EXPOSED` — VA CHẠM: ETHUSDT-OPEN-SEARCH-V2 đang ACTIVE chờ GO; không tiêu surface S1 của nó |
 | SOLUSDT | OK — 1h 2020-09..2026-08 (floor 2020-09-14); funding floor 2020-09-13 | như trên | như BTC | PARTIAL — funding measured qua fapi (conflict ⇒ exclude symbol-month); spread census NOT_RUN | NOT_RUN | `ELIGIBLE_DEV_BASELINE_EXPOSED` — exposure chỉ ở mức xsect baselines; identity mới được dev với disclosure |
 | BNBUSDT | OK — 1h 2020-02..2026-08 (floor 2020-02-10) | như trên | như BTC | như SOL | NOT_RUN | `ELIGIBLE_DEV_BASELINE_EXPOSED` (như SOL) |
-| (4 cặp, plane 15m/1m mới) | PARTIAL — Vision có monthly zips mọi gran; local chưa stage; download = data gate mới | như trên | như trên | spread census NOT_RUN | NOT_RUN | `ELIGIBLE_NEW_PLANE_PENDING_DATAGATE` — surface sạch hơn 1h nhưng phải verify exposure từng window tại GO-1; không tự động là OOS |
+| (4 cặp, plane 15m/1m mới) | PARTIAL — Vision có monthly zips mọi gran; local chưa stage; download = data gate mới | như trên | như trên | spread census NOT_RUN | NOT_RUN | `ELIGIBLE_RECLK_ANCESTRY_EXPOSED` — cùng lịch sử giá đã outcome-exposed ở 1h; plane mới chỉ dùng làm `ANCESTRY_EXPOSED_DEV` (re-clock veto Q-3); KHÔNG phải OOS |
 
 **Kết luận CX:** frontier KHÔNG đóng như FX, nhưng (i) mọi cơ chế
 sweep/absorption bắt buộc nhãn `PROXY_NOT_ORDERBOOK` và qua fictional-
@@ -61,8 +61,10 @@
    nếu ceiling âm ⇒ VETO trước scoring (VOL-NG1 precedent).
 
 ### 3.2 CRYPTO (mỗi cặp, mỗi cơ chế)
-1. Fee: taker 5 bps + 1 adverse tick (measured anchor CHR3F) làm measured
-   book; venue tier bảng công bố = DECLARED tới khi validate vs fills.
+1. Fee: **DECLARED book** — taker 5 bps + 1 adverse tick là frozen declared
+   book của CHR3F (venue-published tier floor + convention tick; Q-8: giá
+   công bố = DECLARED cho tới khi đối chiếu fills); chỉ lên lớp MEASURED khi
+   có bằng chứng fills. Không ghi "measured anchor".
 2. Funding: measured per-settlement path (native, while held); dual-book với
    frozen constant; funding-path stress (24.7% settlements âm trong downtrend;
    worst −0.30%/8h ≈ 2.5 fee RT).

## diff research/control/SRLV-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md
--- /tmp/srlv_pre/OWNER_PACKET_program_open_2026-09-26.md	2026-09-26 14:09:36
+++ research/control/SRLV-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md	2026-09-26 14:20:33
@@ -6,9 +6,12 @@
 
 ## 1. Đã khảo sát (Bước 0, bằng chứng đo được)
 
-- Root checkout `main` @ `e4e3b915`; dirty tree = toàn owner paths + draft
-  plans (giữ nguyên, không stage); heavy lock `FREE_PROVEN`; 70 cycle rows
-  (3 ACTIVE_LIGHT + ERP cohorts TERMINAL).
+- Root checkout `main` @ `e4e3b915` lúc survey (A7 đo lại ở audit: HEAD đã
+  tiến tới `75d5f72a` do commit của lane khác ngoài SRLV); dirty tree = toàn
+  owner paths + draft plans (giữ nguyên, không stage); heavy lock lúc survey
+  `FREE_PROVEN`, lúc A7 audit `HELD_PROVEN` bởi ERP1-TRACKB-COHORT-1 (worker
+  ngoại hợp lệ, SRLV không giữ/chờ); registry: 71 cycle rows, 9 ACTIVE_LIGHT
+  (đo bởi A7 2026-09-26; con số theo registry tại thời điểm đo).
 - Đọc: CLAUDE.md, handbook (headings + luật qua ERP plans), MAP.md, LESSONS.md
   (đầy đủ qua lane Explore), FAMILY_FAILURES.jsonl (134 entries), charter
   ERP-FOREX-PROGRAM-V1, ERP-TRACKB-PROGRAM-V1, VIABILITY_cohort3_REPORT,
@@ -35,9 +38,13 @@
    SRLV-FX-C1 có **Phase D0 bắt buộc**: một reopener (R1/R2/R3/R5) với bằng
    chứng bytes, không có ⇒ `BLOCKED_FRONTIER_NOT_REOPENED`.
 2. **Chi phí là lỗi giết chính**: conditional crossing đo 0.9–1.2 pips
-   (AUD/CA), stressed RT 3.6/4.4 pips; ngưỡng pin P3-A ≤0.41 pip @k=2.0 bị
-   minTick 0.5 pip IBKR đo-chết. Cơ chế FX intraday cần band premium rõi
-   ~7–9 pips để non-fragile — council phải trả lời được trước scoring.
+   (AUD/CA), stressed RT 3.6/4.4 pips; ngưỡng pin P3-A ≤0.41 pip @k=2.0 còn
+   nguyên. Lưu ý lớp bằng chứng: minTick 0.5 pip (IBKR, 5 cặp) chỉ là fact
+   hình học tick — KHÔNG suy ra được executable spread/all-in; executable
+   spread đang NOT_SUBSCRIBED, commission NOT_RUN ⇒ all-in thực sự CHƯA ĐO;
+   R1 sẽ đo, kết quả có thể cao hơn hoặc thấp hơn. Cơ chế FX intraday cần
+   band premium rõi ~7–9 pips để non-fragile — council phải trả lời được
+   trước scoring.
 3. **Crypto mở được nhưng phải trung thực về proxy**: không có order-book/
    liquidation/OI lịch sử ⇒ sweep/zone = `PROXY_NOT_ORDERBOOK`; payer story
    phải nổi fictional-counterparty veto. Funding measured (BTC 11.798%/yr)
@@ -57,7 +64,7 @@
 |---|---|---|
 | **Q1** | Phê chuẩn charter SRLV-PROGRAM-V1 + 2 child draft (ghi quyết định vào packet này). Sau phê chuẩn: Lead commit drafts + đăng ký child cycles qua researchctl khi gate tương ứng mở | Không phê chuẩn ⇒ chương trình không mở, các file ở dạng draft |
 | **Q2 (chọn ≥1 hoặc giữ nguyên)** | **R2** — nguồn bid/ask độc lập: đăng ký TrueFX (free) / OANDA v20 practice / xin Dukascopy written consent — owner-only (đăng ký/tài khoản) | Mở SRLV-FX-C1 Phase D0→D2 (council được phép trên observable mới; nguồn thứ hai cho cost authority) |
-| | **R1** — IBKR: two-sided market data subscription + Flex statement (commission + overnight interest) | Commission/swap measured; các cơ chế biên mỏng được xét lại ceiling |
+| | **R1** — IBKR: two-sided market data subscription + Flex statement (commission + overnight interest) | Commission/swap measured; all-in được ĐO — có thể xác nhận cao hơn hoặc thấp hơn ước tính hiện tại; cơ chế chết F-5 chỉ xét lại bằng số đo |
 | | **R3** — financing band broker-grade | Mở class multi-day hold (đang BLOCKED F4) |
 | | **Không chọn cái nào** | SRLV-FX-C1 đóng `BLOCKED_FRONTIER_NOT_REOPENED` (first-class close); track FX nghỉ tới khi owner mở |
 | **Q3** | Duyệt mở **GO-1 SRLV-CX-C1** (`GO SRLV CX C1 COUNCIL AND FREEZE`) sau khi duyệt child plan — crypto không bị chặn frontier | CX chạy C0→C3 rồi DỪNG chờ GO-2 |

