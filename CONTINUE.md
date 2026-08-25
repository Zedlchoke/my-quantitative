# CONTINUE.md — sau Sprint V7P→V7 (2026-08-25)

Terminal: **V7_REJECT_ALL_CANDIDATE** · V8: **NOT_STARTED_PREP_GATES_T12_T13_T14_FAIL**
Budget scored: **8/8 dùng hết** (V6:4 + V7:4). Locked: NONE. S1: NOT_STARTED. Live: DISABLED.

## Trạng thái
- HEAD = commit shutdown cuối; tree sạch; CHƯA push.
- results/portfolio_v7 (4 trial CLEAN hashes), reproduction_v7 4/4 all-match,
  matrix v7 COMPLETE append-only true.
- V8 prereg ĐÃ FREEZE an toàn: research/hypotheses/H-XSECT-REVERSAL-v2/* +
  research/audits/v8p/v8_spec_freeze.json (hash pins trong baseline).
- Worktrees: ../my-quantitative-v7-wt/{a2..a7} (orca/v7-*) + exec-r1..r4 @b061b55.

## Blocker V8 (đúng §17.3)
T12 six-alt 2y data audit CHƯA chạy; T13 weekly-reversal engine/golden chưa implement;
T14 attestation phụ thuộc T13. → V8 bị chặn chuẩn bị, KHÔNG phải vì thiếu thời gian đơn thuần.

## Next sprint (thứ tự)
1. A2: six-alt two-year data/PIT audit (T12).
2. A3: weekly Monday-00:00 reversal dispatcher + golden e2e (T13) — spec đã freeze, không chỉnh tham số.
3. A6: resolved contract mới + baseline; A7 attest (T14).
4. Chạy đúng 4 trial WREV-3D/7D/14D + WMOM-7D-CONTROL với FG §17.6.
5. Không S1/live; không tuning từ PnL V6/V7; budget V8 riêng theo spec.

## Cấm
S1/paper/live · git add -A · reset/clean · sửa artifact lịch sử · RETRY2 · push khi chưa được yêu cầu.
