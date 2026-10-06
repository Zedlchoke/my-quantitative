# BÁO CÁO TIẾNG VIỆT — Gate-6 pre-GO hoàn thiện FUTURES-ES-PB1-V1 (2026-10-04)

## 1) Lỗi ledger tái hiện và sửa đúng luật
- **Tái hiện độc lập bởi controller TRƯỚC khi sửa** (không tin audit cũ):
  create + record + verify OK → mở lại bằng object mới → record ⇒
  **LedgerError "hash-chain break at line 2"** — đúng như audit mô tả.
  Nguyên nhân code: `_replay` L125 khôi phục con trỏ chuỗi từ
  `prev_row_sha` FIELD của hàng cuối thay vì hash CỦA hàng cuối.
- **FAIL artifact commit TRƯỚC fix** (`2291d562`, "NO fix in this
  commit"), sau đó fix đúng 1 dòng (`8c8c5020`): `_prev_sha = _row_sha(row)`.
- Suite tổng hợp sau fix: **33 PASS** (mở-lại ×5 phiên 9/9 + kiểm chứng
  bytes độc lập; prefix-bytes append-only 3/3 — không bao giờ sửa bytes
  cũ; tamper 4/4 — giữa/cuối/cắt dòng đều bị từ chối; torn-write
  fail-closed 4/4; duplicate/retry accounting 8/8; denominator giữ
  đúng). 2 FINDING ghi trung thực: L-F1 luật đóng băng im lặng về dòng
  cuối đứt (hành vi thực = fail-closed, không bịa); L-F2 verify() trên
  file chưa tồn tại raise FileNotFoundError (có từ trước, chứng minh
  pre-existing). Regression smoke gốc **28/28 xanh** không đổi.

## 2) Đường chạy scored thật
- **Audit toàn Gate-6: KHÔNG có runner nào tồn tại** → xây
  `gate6/runner/scored_runner.py` + **LAUNCH_CONTRACT_V2** (md+json) pin
  toàn bộ authority HIỆN HÀNH bằng sha đúng: operative freeze v3
  `0b0d269a` (== OPERATIVE_FREEZE_PIN), exclude v3 `b101f5c7`, builder v3
  `5a08c9fd`, A7-v3 `f8842e3d` (AUTHORIZED 0C/0H/0M), SPEC `445f7499`,
  **donor law theo trạng thái flagged** (DONOR_LAW_CARRYOVER đã-bác chỉ
  còn là history verified-withdrawn), 24 identity byte-exact, Variant A
  $2.25/side, eval 2,921, budget 24. Spec v1 cũ supersede-by-reference.
- Runner **tự đọc registry** (không tin boolean của caller), đòi GO
  nguyên văn từng chữ (paraphrase/delegation/early = chết chưa tiêu
  thụ), re-hash mọi pin, kiểm tra heavy-lock bằng đúng cây quyết định
  canonical (so sánh từng dòng với governance.heavy_lock.inspect).
  Đường thực thi hiện là STUB khai báo rõ (wiring thật là việc của lane
  post-GO).
- **Refusal matrix 14/14 PASS** (sau khi sửa V-1): no-GO/paraphrase/
  delegated/early GO/tampered-freeze/registry DIVERGED + LAG/flock
  thật (exit 75)/A7 missing — mỗi lần từ chối ghi dòng REFUSED ledger.
  **Runner TỪ CHỐI hôm nay** ở trạng thái thật (chưa có GO) — được
  chứng minh bằng chạy thật. Preflight wiring đầu vào thật: **19/19 sha
  MATCH + 8/8 freeze round-trips**, twin manifest **byte-identical**
  (`2e601747…`). Không tính outcome nào.

## 3) Gates & kiểm toán độc lập
- Gates bị ảnh hưởng đã chạy lại ở các wave trước (A7-v3, dry-run v3 —
  không đổi trong wave này; wave này chỉ gate-6 infra). **Verifier
  fresh-context tại đúng SHA cuối** (worktree `4c0c7504`, root
  `f2c59429`): **G1-G6 PASS — verdict GO_READY**; tự tái hiện lỗi cũ từ
  bytes git, tự re-run suite ledger (33 PASS) + smoke (28/28) + refusal
  (bắt V-1), re-hash 19 pin, so sánh lock-tree từng dòng, doctor 0
  finding ES, registry surgical. V-1 LOW đã sửa trong wave này
  (test_09 chấp nhận cả hai nhánh từ chối hợp pháp) → suite **14/14**.
- Registry reconcile qua researchctl CAS khi ROOT sạch; foreign
  NBA/NFL rows byte-identical (1 commit NFL của owner land giữa audit —
  xác nhận không đụng hàng ta).

## 4) Trạng thái & handoff
| Mục | Verdict |
|---|---|
| 1 Ledger reopen/append | **PASS** (FAIL-trước-fix `2291d562` → fix `8c8c5020`; 33+28+14 test xanh) |
| 2 Runner thật + contract v2 | **PASS** (refusals 14/14, preflight 19/19, refuses-today, twin byte-identical) |
| 3 Gates re-run + audit độc lập | **PASS** (verifier GO_READY tại SHA cuối; V-1 đã đóng) |
| 4 Handoff + báo cáo | **PASS** (handoff_LEDGER-FIX + handoff_RUNNER đúng schema/path) |

**Scored budget thực tế: 0/24.** Blocker còn lại: **KHÔNG CÒN blocker
pre-GO** — chỉ còn typed owner GO (key 2/2) + 1 dòng acknowledgment
D-A4/D-A5 (hình thức, nên ký kèm GO). Verdict: **GO_READY**. Không ai
tự gõ GO; prompt này không phải GO; 0 S1/lệnh/push/merge; không đụng
lane NBA/NFL/P3.

— Hết (bằng chứng: `gate6/fix/`, `gate6/runner/`,
`verify/gate6/VERIFY_GATE6.md`).
