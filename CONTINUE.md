# CONTINUE.md — Handoff sau Sprint V6P→V6→V7 (2026-08-25)

> **Viết bởi:** A1 (Orca coordinator) lúc shutdown
> **Terminal outcomes:** `V6P_PASS_V6_AUTHORIZED` → `V6P_PASS_V6_CANDIDATE_FAIL` → `V6_TERMINAL_V7_SKIPPED_TIME_BUDGET`
> **Nguyên tắc:** không relabel V6; V7 spec đã hash, chưa wire; không S1; không live money; old worktrees read-only.

## 1. TRẠNG THÁI (đo được, không phải ý định)

- Primary: `/Users/hoangminhlong/my-quantitative`, branch main, HEAD `fbd2e9d…` + 1 commit shutdown cuối; **chưa push**.
- Uncommitted có khai báo (exempt): `research/audits/v6p/{baseline_root,a7_prelaunch_attestation}.json` — cặp provenance ghim nhau bằng hash-chain; commit ở đầu sprint mới nếu muốn.
- Worktrees vai trò: `/Users/hoangminhlong/my-quantitative-v6p-wt/{a2..a7}-*` nhánh `orca/v6p-*` từ bootstrap `b4a9da6`; A7 đã commit audit trên nhánh riêng (đã cherry-pick vào primary).
- Workers còn sống: **0** (sampler PID 22074 đã SIGTERM theo đúng pid).
- Scored budget: **4/8 dùng** (4 trial V6); V7 = 0.

## 2. KẾT QUẢ HỌC ĐƯỢC (taxonomy)

| Trial | PnL | PF | Kết luận |
|---|---|---|---|
| CARRY-1D | −5.680 | 0.978 | mechanism_failure |
| CARRY-3D | +2.076 | 1.012 | edge_too_weak (PF<1.10) |
| CARRY-7D | +20.581 | 1.157 | **top-fold 51.66%>50%** (FG3 concentration fail); MDD thực 8.84% PASS |
| REVERSE-3D | −20.103 | 0.870 | negative_control như kỳ vọng |

Pipeline surfaces VALID toàn bộ (XG0/XG1 measured, hashes CLEAN, repro full-surface all-match, matrix COMPLETE, append-only true). A7 audit PASS, 0 HIGH/CRIT.

## 3. VIỆC CHƯA LÀM & LÝ DO

- **V7 NOT_AUTHORIZED** vì: A04 (chưa wire dispatcher divergence — wire sau khi thấy V6 results sẽ phá blindness), A08 (chưa có attestation cho launch head V7), A10 (<180 phút còn lại). Module `research/funding_price_divergence.py` + 8 tests đã sẵn sàng và KHÔNG đổi sau khi thấy kết quả V6.
- `dsr_pbo_report`: DSR null trung thực (chuỗi fold n=3 không đủ), PBO = NOT_ENOUGH_CONFIGURATIONS.

## 4. SPRINT MỚI CẦN LÀM (theo thứ tự)

1. Wire nhánh dispatcher `funding_price_divergence` vào `_signal_family_dispatch` (pattern y hệt funding_carry) **trước** mọi results — khôi phục tính mù.
2. Freeze baseline mới (schema v2 đã có mẫu: source_head + coordination_head + manifest hash + spec hashes).
3. Xin A7 pre-launch attestation trên worktree `a7-independent-audit`.
4. Chạy đúng 4 trial V7 (price lookback 1D/3D/7D + reverse-3D control, funding lookback cố định 3D) với ngân sách còn lại 4/8.
5. Áp FG0–FG2, FG3-V7, FG4–FG7; scorecard ≥75 mới eligible; tối đa lock 1 candidate cross-family.

## 5. CẤM

Đọc/S1, live money, `git add -A`, reset/clean, đụng `results/**` cũ như evidence, relabel V6, RETRY2, push khi owner chưa yêu cầu.
