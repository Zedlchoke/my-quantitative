# PLAN (DRAFT) — DTP-CX-SOLUSDT-C1 — Child plan pair đầu: day-trading playbooks trên SOLUSDT (Binance USDⓈ-M perp)

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** Không
> đăng ký cycle, không spawn worker, không download, không score, không mở
> S1/sealed, không đụng shadow/dashboard/worker, không đặt lệnh. Hiệu lực khi
> owner gõ `GO DTP CX SOLUSDT C1 COUNCIL AND FREEZE` tại gate GO-1 của child
> này (P-8). Parent: `DAYTRADE-PLAYBOOKS-PROGRAM-V1` (mọi luật master binding).

## 1. Identity của child

```text
cycle_id   DTP-CX-SOLUSDT-C1
pair       SOLUSDT USDT-M perpetual (Binance)
track      DTP-CX (pair #1 theo thứ tự freeze tại GO-1 packet)
plane      dev = ANCESTRY_EXPOSED_DEV (1h `OUTCOME_EXPOSED_baseline` — chỉ
           xsect baselines, chưa có search directional riêng; 15m/1m là
           re-clock của cùng lịch sử giá ⇒ KHÔNG BAO GIỜ OOS); OOS =
           prospective accumulation sau freeze (GO-3), trừ khi owner cấp
           sealed window mới
budget     ≤18 scored cells (≤3 identity × 4–6 cells); 0 cell được chạm trước
           GO-2. Kỳ vọng trung thực theo base rate: khả cao 0–6 cells thực chạy
S1         SEALED_UNTOUCHED
orders     NONE
```

## 2. Data gate (chạy tại GO-1 sau khi GO được gõ; mọi mục ghi PASS/FAIL/NOT_RUN + bằng chứng)

1. **Re-verify plane có sẵn bằng bytes** (PWS-CX-SOLUSDT durable assets):
   klines 1h 2020-09-14..2026-08 gapless floor-exact; funding 6,580
   settlements bit-exact; inventory sha-pinned. FAIL ⇒ dừng, báo owner.
2. **Stage 1m + 15m klines** từ Vision monthly zips (keyless, posture
   PIT_USABLE kế thừa; license text chưa capture ⇒ data gate ghi posture
   từng nguồn). Ngân sách: ≤0.5 GB mới; abort nếu free <5.0 GiB
   (BLOCKED_STORAGE); manifest sha256 mọi byte.
3. **PIT seam check** trên plane mới: stamp-scale migration guard (L-TRACKB1-1
   — Vision đổi µs từ 2025; scale-normalize + verify grid endpoint), gap
   census, DST không áp dụng (UTC) nhưng verify UTC day boundary continuity.
4. **Cost census + thành phần gate bắt buộc (A7-F1/F8)**: spread theo giờ
   fill từ bookTicker (6-tháng census có sẵn — re-verify coverage; fill ngoài
   cửa sổ census được cost theo declared band ×1.5/×2.0 kèm nhãn
   `FILL_QUALITY_CLASS_declared` + coverage label, không tự ngoại suy
   measured); fee = DECLARED 5bps + 1 adverse tick (frozen CHR3F); funding =
   MEASURED dual-book (native path + frozen constant; SOL funding sign
   autocorr +0.853 — mọi identity funding-adjacent bị đại diện bởi
   level-window chết, P-29); **quote (bookTicker) + trade (aggTrades) +
   mark/index per contract: coverage-verify từng loại từ corpus granary —
   thiếu ⇒ BLOCKED**. Thiếu spread census ⇒ K-COST BLOCKED, không điền số đẹp.
5. **Power analysis** tại freeze: floors §6.5 master (≥100 RT; two-sided
   capability bắt buộc ghi rõ vì G5 precedent — dù đó là fence BTC, ghi trung
   thực cho SOL).

## 3. Council + slate (chạy sau GO-1)

Council roster §6.1 master (collector/definer, skeptic VETO, PIT auditor,
cost auditor, scorer, A7). Input bắt buộc: `PLAYBOOK_TAXONOMY.md` (frozen) —
council duyệt từng dòng, mở open-call cho skeleton mới (phải qua F-0).
**Slate đề xuất ban đầu (2 direction + 1 slot open-call; quyết định cuối
thuộc council sau F-0/F-1):**

- **DTP-CX-SOLUSDT-I001 (direction) — OUTCOME-BLIND ANNOTATED PLAYBOOK
  CORPUS**: xây bộ annotation mù outcome từ nguồn day-trader dated (journal/
  video, ghi nguồn + thời điểm công bố, không chart biết kết quả) về setup
  intraday trên SOL/alt; codify các setup theo tần suất; MỖI rule codify chịu
  F-0 riêng. Payer: từng rule phải tự khai payer (kỳ vọng trung thực: đa số
  rule = skeleton #1–#11 taxonomy ⇒ collision kill — đo được điều đó chính là
  sản phẩm). Falsifier: skeleton test từng rule; representation rho > 0.20 so
  dead class ⇒ F0_KILLED; rule sống sót phải thắng placebo/inverted/baseline
  ở measured spread + funding + declared fee, two-sided.
- **DTP-CX-SOLUSDT-I002 (direction) — INTRADAY BTC→SOL LEAD-LAG DIFFUSION
  (two-sided)**: BTC move confirm trên 1m/5m (bar đóng) → vào SOL cùng chiều
  khi quote SOL chưa adjust. **Bề mặt đo độ trễ "chưa adjust" (A7-F1): trade
  tape aggTrades SOL (time-of-sale vs BTC kline confirm) + bookTicker quote
  sequence SOL — phải qua data gate với coverage đủ; không coverage hợp lệ ⇒
  identity vào F-0 với `BLOCKED_DATA`, không thay bằng proxy**.
  Payer/hypothesis: maker stale-quote trên SOL book bị adversely select bởi
  thông tin BTC; taker thu chọn lọc nghịch. Kill-risks phải đo trước: (a)
  K-ANC — representation rho vs `EOS1-E2` ratio-gates + xsect-momentum dead
  shadows; (b) K-COST — ceiling×power grid một dòng (P-29): RT declared ~
  2×(5bps fee) + 2×spread(~0.5bps) + 2 tick ≈ 11–13 bps; diffusion capture
  1m phải ≥ ceiling ở cả θ grid, không thì VETO pre-PnL; (c)
  fictional-counterparty veto nếu payer không encode được bằng observable PIT
  hợp pháp.
- **Slot 3: OPEN-CALL** cho skeleton mới qua F-0 (pattern P4 blind open-call
  của ERP1-TA-COHORT-2). Không nhồi identity cho đủ số — luật master §2.

## 4. Falsifier battery (trước PnL, mọi identity frozen; đánh số theo
umbrella — master §11 governs, F-4 beta/bloc và F-7 fixture bổ sung định
nghĩa tại freeze)

F-0 skeleton/payer/information (skeptic VETO); F-1 ancestry rho ≤0.20 trên
frozen representation (một-shot, committed, reproducible — bài học V9); F-2
PIT battery M-1..M-5 + future-mutation + delay-pair Q-4 (sub-hour); F-3
beta/bloc; F-5 cost-survivability ceiling (ceiling×power grid); F-6/Q-6
feasibility nearest-window; Q-12 concentration pre-check. Kill rules K-* §6.4
master.

## 5. Scored + OOS (chỉ sau GO-2/GO-3 riêng)

Walk-forward multi-fold force-flat; gates G1–G8 margin-to-fail; stress
×1.5/×2.0; per-fold/per-direction/concentration/trade-count/drawdown/
baseline/control báo đầy đủ; net sau phí ở cost chuẩn/1.5×/2×. Nhãn bắt buộc
mọi row: `ANCESTRY_EXPOSED_DEV`, `PROXY_NOT_ORDERBOOK` (khi liên quan),
`SINGLE_VENUE_PANEL`, `FUNDING_PATH_STRESSED`, `FILL_QUALITY_CLASS_declared`
(tới khi có fills). OOS: GO-3 `GO DTP CX SOLUSDT C1 OOS ONE LOOK AND
REPLICATION` — prospective accumulation sau freeze (identity frozen, membership
sha-pinned, evaluation pass duy nhất); replication đủ 3 limb R5 mới được viết
"replicated".

## 6. Artifacts

`research/control/DTP-CX-SOLUSDT-C1/`: council reports + handoffs
(`zcode_orch_v3_handoff@1`), data-gate verdict, annotation corpus manifest,
falsifier battery, freeze artifact (sha256), dry-run, scored cells, seam/
kill-law, DSR, repro twin, A7 prelaunch + terminal, trial_ledger.jsonl,
CYCLE_VERDICT.md.
