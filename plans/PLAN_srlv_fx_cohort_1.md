# PLAN (DRAFT) — SRLV-FX-C1 — Cohort 1 track Forex: Support/Resistance · Sweep · Volatility-state

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** Child
> cycle của `SRLV-PROGRAM-V1` (master `plans/PLAN_srlv_program_v1.md`), tiếp
> charter `ERP-FOREX-PROGRAM-V1` dưới umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`.
> Kế thừa nguyên văn: umbrella §§1–11; forex-program §3 (kiến trúc cohort),
> §4 (R0–R6 BACKTEST_CANDIDATE_REPLICATED), §5 (roster), §8 (chuỗi GO);
> SRLV master §§2–11. Chỉ chặt hơn, không yếu hơn.
>
> **RÀNG BUỘC MỞ ĐẦU (frontier law):** cohort này KHÔNG THỂ mở council/scoring
> cho tới khi master §6 có MỘT reopener (R1/R2/R3/R5) với bằng chứng bytes +
> authority đo tại Phase D0. Không có ⇒ terminal
> `BLOCKED_FRONTIER_NOT_REOPENED`, 0 scored cell, 0 holdout look.

## 0. Cycle identity

```text
cycle_id      SRLV-FX-C1
parent        SRLV-PROGRAM-V1 (master) / ERP-FOREX-PROGRAM-V1 (charter FX)
worktree      .worktrees/srlv-fx-c1/integration (branch
              orca/srlv-fx-c1-integration) — tạo qua researchctl tại GO-1
budget        ≤ 18 scored cells (3 cơ chế × 6 arms × 1 home pair) + references;
              holdout looks ledgered riêng
home pairs    do council chọn tại freeze từ slate được phép (§2); USDCHF chỉ
              là transfer surface (R4)
S1            SEALED_UNTOUCHED; AUDUSD/USDCAD 2026-H1 giữ SEALED-UNREAD
GO phrases    master §13 (FX cột) — gõ đúng chữ tại đúng gate
```

## 1. Mục tiêu cohort

Falsify tối đa 3 cơ chế S/R–sweep–vol-state TRƯỚC PnL; chỉ identity qua đủ
F-0…F-7 mới được scored walk-forward; chỉ identity qua đủ dev gates mới được
xin GO-3 nhìn sealed OOS MỘT lần. Modal outcome kỳ vọng: `REJECT_ALL` (2
cohort tổ tiên đều vậy; 12 dead classes phủ hầu hết không gian naïve).

## 2. Slate pair & vai trò (binding, từ OUTCOME_EXPOSURE_MAP)

| Cặp | Vai trò trong cohort này |
|---|---|
| EURUSD, GBPUSD, USDJPY | **KHÔNG phải dev/OOS** — ancestry disclosure, engine-parity fixture, spread-curve/cost authority |
| AUDUSD, USDCAD | **dev cho observable MỚI** (qua D2/F-0 court) — dev 2021-01..2025-12 |
| AUDUSD, USDCAD holdout 2026-01..06 | **SEALED — KHÔNG ĐỌC** tới GO-3, membership sha-frozen trước pass |
| USDCHF | `BLOCKED_DATA_LICENSE` — 0 bytes; chỉ mở làm transfer surface theo R4 SAU khi một identity qua dev gates + owner slate amendment + data gate đầy đủ |
| Nguồn độc lập (TrueFX/OANDA/…) | `BLOCKED_SOURCE_AUTHORITY` — 0 bytes; mở theo R2 (owner action) |

Slate froze tại GO-1; đổi slate = owner decision, không mid-cohort.

## 3. Phases & gates

### Phase D0 — Frontier reopening verification (gate, trước council)

- Input: bằng chứng reopener (R1/R2/R3/R5) owner đã hành động: bytes on disk +
  license gate PASS + (nếu nguồn mới) cross-source PIT seam check
  (Dukascopy vs nguồn mới: clock, day-boundary, DST, scale; khác biệt ghi
  `SEAM_DISCLOSED` theo DATACOST critic condition 5).
- Output: `FRONTIER_REOPENING_VERDICT.md` — nêu CHÍNH XÁC thông tin mới nào
  mở lại frontier, cơ chế nào nó hợp lệ hóa, và ceiling all-in được đo lại
  nếu R1/R3 có số — kết quả đo có thể CAO HƠN hoặc THẤP HƠN mọi ước tính hiện
  có; không chiều nào được định trước. Không reopener ⇒ terminal
  `BLOCKED_FRONTIER_NOT_REOPENED` (first-class close), báo owner, không mở
  council.

### Phase D1 — Data/license/PIT/cost/power gate per pair

- Cho mọi cặp trong slate (kể cả cặp BLOCKED — ghi row, không bỏ qua):
  probe OHLC/offset/scale/tick-crosscheck (fxm.probe@1 precedent), census
  spread theo session/rollover sha-pinned, DST/rollover fixtures, power
  analysis cho cơ chế ứng viên (n RT cần cho PF target @2σ).
- Nguồn mới (nếu R2): data gate riêng + license posture text capture
  (`DOCUMENTED_CANDIDATE → AUTHORIZED_INTERNAL_RESEARCH | UNAVAILABLE_FAIL_
  CLOSED | REJECTED_LICENSE`); free ≠ authorized.
- Fail-closed: thiếu census spread ⇒ cặp BLOCKED; không dùng hằng số vendor.

### Phase D2 — Council outcome-blind + falsifiers + trial freeze (GO-1, rồi DỪNG)

1. Blind proposers (không thấy outcome nào) nộp proposal 10 trường umbrella
   §5.3 + ba họ H1/H2/H3 master §2.1, trong đó:
   - **payer**: ai trả, vì sao BẮT PHẢI trả,premium kỳ vọng bps/period,
     persistence (cái gì xói mòn), risk ta nhận (tên đuôi), full cost ceiling
     tại ×1.0/×1.5/×2.0 TRƯỚC scoring;
   - **observable PIT**: định nghĩa mức/vùng + `t_known` + pivot confirmation
     lag; nếu R2 mở tick: event-time sequencing được phép tới tick granularity
     của nguồn (vẫn cấm order-book claim nếu nguồn không có depth);
   - **vol-state** (nếu dùng): đ колlateral incrementality test §2.4 master.
2. F-0 court (skeptic VETO) → F-1 ancestry rho (frozen representation, bar
   0.20) → F-2 PIT battery §3 master (M-1…M-5 + future-mutation + delay-pair
   Q-4) → F-3 clock-placebo non-vacuous → F-4 baseline/short-beta (+carry-beta
   nếu USDJPY có mặt ở bất kỳ vai trò nào) → F-5 cost-survivability ceiling
   trên phân phối đo được (K-COST) → F-6 feasibility nearest-window → F-7
   concentration pre-check.
3. Trial freeze (sha256 pin): ≤3 cơ chế; mỗi cơ chế 1 anchor + ≤2 neighbour +
   1 causal control + 1 inverted control + 1 baseline set; universe/clock/
   warmup/features/lags/entry/exit/fill law/cost tier/fold contract/thresholds
   + exclusion-zone logging; fold contract F1..F6 kiểu 2022-07..2025-06 trên
   dev window; force-flat mọi fold boundary.
4. A7 prelaunch (fresh context) kiểm freeze + fixtures; REFUSED = remediation.

### Phase D3 — Scored walk-forward (GO-2, heavy lock)

- Chạy đúng freeze; báo per-pair, per-fold, toàn panel, leave-one-out (master
  §8); gates G1–G8 với margin-to-fail (cohort-1 §9.2–9.4 mặc định):
  G1 net>0 @1.0; G2 PF ≥1.20; G3 ≥4/6 folds; G4 net>0 @1.5; G5 trades ≥
  power floor; G6 control-prediction bands (clock-placebo <0.5× anchor;
  inverted strictly below); G7 baseline beat biên ≥2×; G8 concentration ≤0.50.
- Kill rules master §10 bắn bất kỳ lúc nào; mọi cell vào observed denominator
  kể cả publication fail.

### Phase D4 — Sealed OOS one-look + replication (GO-3, MỘT LẦN)

- Điều kiện xin GO-3: một identity qua đủ dev gates trên home pair (R2 của
  charter). Membership artifact sha256 TRƯỚC pass; arm chết không nhìn.
- Sealed map: AUDUSD/USDCAD 2026-H1 (một look per pair; window transfer một
  look cấp chương trình — matrix L5). PASS = net>0 @×1.0 VÀ @×1.5; control
  phải KHÔNG tái tạo trên holdout.
- Replication 3 limb (charter R5): impl độc lập (A7 viết lại từ raw planes);
  thời gian chưa dùng để chọn; bề mặt độc lập = cặp outcome-free (chỉ
  USDCHF sau R4 + data gate) HOẶC nguồn độc lập (chỉ sau R2). Thiếu limb ⇒
  không viết "replicated".

### Phase D5 — A7 terminal + two-half close

- A7 recompute từ bytes; two-half close: registry flip + P-9 ledger +
  FAMILY_FAILURES/MAP/LESSONS + errata P-19 + CYCLE_VERDICT.md.

## 4. Mechanism-specific freeze fields (bổ sung cho 10 trường umbrella)

Mỗi proposal FX phải pin thêm: định nghĩa mức (công thức + tham số + N bar
xác nhận); `t_known` của từng loại mức; quy tắc nhiều mức chồng nhau (nearest/
strongest — chọn TRƯỚC outcome); hành động tại mức (fade/break/sweep-reclaim)
+ khung thời gian sống của tín hiệu; session filter (nếu có) + clock-only
twin; stop/target/time-exit; spread-conditioning của fill (cost theo phân phối
fill của cơ chế); short-beta/carry-beta control arm matching.

## 5. Ngân sách / dừng

- ≤18 scored cells; ≤2 holdout looks (1/pair sealed window); program cap chia
  theo master §9. Time-stop vận hành 14 ngày/cohort (master §11f).
- Cohort đóng: `REJECT_ALL` (modal), `NO_ELIGIBLE_PROPOSAL`,
  `BLOCKED_FRONTIER_NOT_REOPENED` (D0), `BLOCKED_DATA_OR_SELECTION`,
  `BLOCKED_SOURCE_OR_SCHEMA`, `BLOCKED_COST_AUTHORITY`,
  `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` (qua dev + OOS), và tối đa
  `BACKTEST_CANDIDATE_REPLICATED` khi đủ 7/7 R0–R6 (paper-tier bound).
