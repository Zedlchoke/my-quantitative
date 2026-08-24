# CONTINUE.md — Handoff sau Sprint V5R→V6 Orca (2026-08-24)

> **Viết bởi:** A1 (opencode, Orca coordinator) lúc 2026-08-24 ~12:0x UTC
> **Kết thúc sprint:** `V5_FAIL_V6_BLOCKED` (terminal, trung thực — xem
> `research/audits/v5r/master_transition.json`)
> **Nguyên tắc bất biến:** không sửa verdict legacy; không xoá/quên quarantine;
> không mở V6 khi chưa có transition hợp lệ; `.venv/bin/python` duy nhất;
> không S1; không live money; old worktrees read-only vĩnh viễn.

---

## 1. VERDICT BLOCK (đọc đầu tiên)

```text
ENGINEERING_VERDICT          = PASS (pipeline integrity đã phục hồi, chứng minh end-to-end)
SCIENTIFIC_AUDIT_VERDICT     = PASS (A6 độc lập, post-freeze, toàn dân số)
LEGACY V5                    = FAIL vĩnh viễn (5/26 PASS; C02,C19,C21,C25 FAIL; 17 NOT_TESTED)
V5R CLEAN LINEAGE            = FAIL (16/18 PASS; R06 data coverage/funding; R12 stress bị skip)
V6_TRANSITION                = V5_FAIL_V6_BLOCKED  ← terminal, KHÔNG mở V6
LOCKED_CANDIDATE             = NONE (momentum recalc: 3D −8.2k / 7D +9.5k PF1.048 / 14D −8.2k / control −27.3k)
S1_STATUS                    = NOT_STARTED
LIVE_MONEY_STATUS            = UNCHANGED_DISABLED
```

## 2. Trạng thái repo khi bàn giao

- Branch `main`, HEAD = commit freeze cuối (`git log --oneline -8`; freeze run =
  `e3d82ad`), tree sạch, **chưa push** (owner chưa yêu cầu).
- Toàn bộ evidence V5R nằm trong `research/audits/v5r/` (đã commit) và
  `results/{diagnostic_v5r,reproduction_v5r,matrix/v4_recalc_diagnostic_v5r}/`
  (gitignored — giữ nguyên, không xoá).
- Registry: 503 rows, append-only verified TRUE; diagnostics KHÔNG tăng trial count.
- Old worktrees `/Users/hoangminhlong/my-quantitative-wt/*`: READ-ONLY, 18 thư mục,
  đã inventory trong `worktree_inventory.json`.

## 3. Việc đã xong (sự thật đã đo, không phải claim)

1. Test contamination: root cause PROVEN (stale default-arg binding); fix
   late-bound + fixture redirect; pre/post recheck 1474 paths không đổi.
2. V5-C02: exact recovery NOT_FOUND (5,726 file + 445 git blob quét hết) → legacy FAIL.
3. Quarantine EXP-0001/0002 (metadata-only, immutable policy flags).
4. Phase D engineering: hashes-last finalization fail-closed; external-reader
   verify (4/4 CLEAN vs legacy 4/4 MISMATCH); reconciler schema v2 → COMPLETE,
   mismatches=[]; synthetic XG integrity constant REMOVED.
5. Baseline V5R frozen trước launch, A6 xác minh PASS; 4 diagnostic recalc chạy
   đúng lệnh đông lạnh; 4 reproduction all_match.
6. A6 audit post-freeze: 10/10 checks PASS; findings 2 MED (gross>1 semantics;
   XG0 funding-reason vs data-manifest conflict) + 2 LOW — chi tiết trong
   `challenge_memo_v5r.md`.

## 4. Tại sao V6 bị chặn (không được "thông cảm")

- **R06 FAIL**: XG0 đo được `coverage_below_declared` +
  `funding_coverage_insufficient` trên cả 4 run mới — dữ liệu không đủ so với
  window khai báo. Đây là điều kiện tiên quyết FG0 của V6.
- **R12 FAIL**: runner chỉ chạy stress/drop-one khi base edge PASS; plan yêu cầu
  thực thi vô điều kiện. Phải sửa code trước mọi lineage tương lai.

## 5. NEXT ACTIONS cho owner (theo thứ tự)

1. Sửa data coverage/funding cadence cho khớp window khai báo HOẶC đóng băng
   window nhỏ hơn trung thực. Không tune universe sau khi xem kết quả.
2. Sửa `portfolio_runner`: bỏ gating stress phía sau base edge (unconditional).
3. Quyết định 2 finding MED trong memo (gross_exposure >1 semantics; XG0 reason
   logic vs manifest).
4. Nếu muốn thử lại: tạo lineage MỚI (V6-pre validation) theo PLAN §12 — KHÔNG
   tái sử dụng verdict V5R, không relabel, baseline mới freeze trước launch.
5. Push/PR: chỉ khi owner yêu cầu rõ ràng.

## 6. Cấm tuyệt đối cho agent kế tiếp

Đọc `PLAN.md` (execution contract hiện hành) + `master_transition.json` trước.
Không: sửa `gate_ledger_*`/`*_transition.json` đã commit; dùng `git add -A`;
`reset --hard`/`clean`; chạm `results/stage_a_v3/EXP-0001/0002`; đọc S1; bật
live money; tạo PASS giả từ missing evidence. FAIL trung thực là kết quả hợp lệ.
