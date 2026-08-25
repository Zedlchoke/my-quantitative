# CONTINUE.md — Handoff cho Sprint V7P→V7 (viết lại bởi A2, 2026-08-25)

> **Viết bởi:** A2 (closure/provenance), worktree `/Users/hoangminhlong/my-quantitative-v7-wt/a2-closure`, branch `orca/v7-a2-closure`.
> **Bootstrap của sprint này:** `dd026c0` — *BOOTSTRAP: V7P→V7 execution contract (PLAN.md 20260825)*. Toàn bộ worktree A2–A7 sinh từ đúng bootstrap này; lineage đã verify `fbd2e9d` (final HEAD V6) là ancestor của `dd026c0` qua `merge-base --is-ancestor`.
> **Terminal truth V6:** `V6P_PASS_V6_AUTHORIZED` → `V6P_PASS_V6_CANDIDATE_FAIL` → **V7 NOT_RUN 0/4, NOT_AUTHORIZED**. Chi tiết đầy đủ: `research/wayfinder/evidence/v6-closure-addendum-20260825.md` (+ `.json`, có sha256 của mọi artifact nguồn).
> **Nguyên tắc:** không relabel V6; correction chỉ qua addendum có hash; không S1; không live money; worktree V6P cũ read-only.

## 1. TRẠNG THÁI HIỆN TẠI

- Sprint V7P chạy trên topology mới: `../my-quantitative-v7-wt/{a2-closure,a3-engine,a4-finalizer,a5-reproduction,a6-conformance,a7-audit}`, branch `orca/v7-*`, bootstrap chung `dd026c0`. Merge order do A1: A2 → A3 → A4 → A5 → A6; A7 audit sau integration commit.
- Primary `/Users/hoangminhlong/my-quantitative`: read-only với A2. Final HEAD tại đóng sổ V6: `fbd2e9d36b5349489ef29deec4cdeb8bca2b89ad` (clean tree); một commit shutdown `5638107…` thêm evidence cuối; rồi `dd026c0` bootstrap.
- Scored budget: **4/8 dùng** (toàn bộ 4 trial V6); V7 = 0/4 chưa chạy; locked candidates = 0.
- Workers: 0 còn sống (shutdown report terminal); S1 NOT_STARTED; live UNCHANGED_DISABLED.

## 2. SỰ THẬT V6 (đóng sổ, A7-agreed — đọc bảng, đừng đoán)

| Trial | Net PnL | PF | MDD | Funding | Fold PnLs | Kết luận |
|---|---:|---:|---:|---:|---|---|
| CARRY-1D | −5,679.96 | 0.9784 | 24.50% | +1,958.03 | +10,112 / +7,782 / −23,575 | Reject: mechanism_failure |
| CARRY-3D | +2,076.03 | 1.0116 | 15.18% | +2,129.47 | +6,949 / +8,704 / −13,578 | Reject: edge_too_weak (PF<1.10) |
| CARRY-7D | +20,580.87 | 1.1570 | 8.84% | +2,277.23 | +10,866 / +10,169 / −454 | Reject: top positive fold 51.66% > 50% |
| REVERSE-3D | −20,102.83 | 0.8699 | 28.52% | −1,677.84 | negative control | Failed as designed |

- **Bắt buộc:** 7D bị loại vì **concentration FG3** (F1 chiếm 51.66% pnl dương > 50%), KHÔNG phải MDD. MDD thật = **8.84% PASS** (≤10%). Con số 28.85% chỉ tồn tại trong rerun R2 dính env-bug đã bị supersede (A7 finding F-1, check A7-V6-2 PASS_WITH_CORRECTION).
- Reverse control thua best directional ⇒ trigger "reverse beats best" KHÔNG kích hoạt; CONTROL_ONLY, không bao giờ được promote.
- Pipeline surfaces VALID (hashes/repro/matrix/append-only clean); A7 v6 audit PASS, 0 HIGH/CRIT unresolved.
- `family_summary.json` thiếu concentration trong fg3 dict (finding F-2) và các status sidecar cũ ghi 0 scored — cả hai đã được supersede bởi closure addendum + sidecar sync trên branch này.

## 3. VIỆC CHƯA LÀM & LÝ DO

- **V7 0/4 NOT_RUN / NOT_AUTHORIZED** khi shutdown V6: A04 (dispatcher divergence chưa wire), A08 (chưa attestation cho launch head), A10 (<180 phút). Không được gọi V7 là "done/backtested/failed".
- DSR null trung thực (fold series n=3); PBO = NOT_ENOUGH_CONFIGURATIONS — cần contract mới theo PLAN §6.4–6.5.
- XG4/FG4 robustness chưa hoàn thiện ở gate level (A7 finding F-5) — forward requirement trước mọi eligibility.

## 4. NEXT COMMAND — proceed V7P-1 merges

Trạng thái hiện tại: A2 closure commit trên `orca/v7-a2-closure`. Bước tiếp theo theo PLAN §4:

1. A3/A4/A5/A6 hoàn thành phần việc trên branch tương ứng (engine dispatcher, finalizer+DSR/PBO, reproduction, conformance/golden) từ cùng bootstrap `dd026c0`.
2. A1 cherry-pick theo order **A2 → A3 → A4 → A5 → A6**, kiểm diff nằm trong allowed paths, targeted tests PASS sau từng merge.
3. Full suite + resolved_run_contract + baseline freeze tại integration SHA sạch.
4. A7 prelaunch audit trên integration SHA đó; 18/18 gates PLAN §7 phải PASS (còn ≥180 phút) thì mới launch V7 wave 1 (1D+3D) rồi wave 2 (7D+REV-3D).

## 5. CẤM

Đọc/S1, live money, `git add -A`, reset/clean, sửa `results/**` cũ như evidence, relabel V6, RETRY2 cứu candidate, tuning sau khi thấy fold, push khi owner chưa yêu cầu.

---
*A2 closure/provenance · 2026-08-25 · evidence: research/wayfinder/evidence/v6-closure-addendum-20260825.{md,json}*
