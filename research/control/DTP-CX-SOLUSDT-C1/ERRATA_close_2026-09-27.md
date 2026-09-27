# ERRATA — DTP-CX-SOLUSDT-C1 two-half close (per A7 terminal F-1..F-4, 2026-09-27)

- A7 terminal verdict: `CONFIRM_WITH_FINDINGS` — KHÔNG finding nào chặn
  verdict `NO_ELIGIBLE_PROPOSAL`; 18/18 số quyết định recompute MATCH exact.
  Báo cáo: `audits_a7/A7_TERMINAL_REPORT.md`.

## E1 (A7 F-1, MEDIUM) — clock-note: timestamp khai báo vs commit đo được

Các artifact khai báo UTC stamp bằng ước lượng chưa đo; git commit timestamps
là authority. Đo tại close:

| Artifact | Stamp khai báo | Commit thật (đo) |
|---|---|---|
| FREEZE_R1.json frozen_at_utc | 2026-09-27T06:40:00Z (ước lượng) | commit `e23ff983` **06:34:25Z** |
| FREEZE_R2.json frozen_at_utc | 2026-09-27T08:05:00Z (ước lượng) | commit `03d685ef` **07:41:01Z** |
| court_r2_machine@1.json | 09:30Z (ước lượng, lane ghi) | commit `03d685ef` **07:41:01Z** |

Toàn vẹn nội dung KHÔNG bị ảnh hưởng: mọi sha pin verify, chuỗi thứ tự tồn
tại được chứng minh độc lập bằng cross-pins (A7 section F/G PASS). Nguyên
nhân gốc: lane/A1 ghi stamp ước lượng thay vì đo `date -u` tại lúc ghi — bài
học mang đi: **mọi stamp trong artifact phải đo, không ước lượng**.

## E2 (A7 F-2, LOW) — scope sentence: 1 glyph em-dash vs hyphen

Câu scope trong FREEZE_R2 dùng "—" nơi bản chuẩn trong báo cáo tòa dùng "-";
không đổi ngữ nghĩa. Bản canonical đưa vào CYCLE_VERDICT.md (dưới đây) là
bản chuẩn.

## E3 (A7 F-3, LOW) — "45 distinct family_id citations" trong artifact skp-r2

Số đúng: **38 family_id khác nhau** (union, mỗi row FAMILY_FAILURES xuất hiện
đúng 1 lần — A7 verify 38/38); "45" là số LƯỢT cite theo class_verdict. Bản
đính chính: death ledger có 38 distinct citations.

## E4 (A7 F-4, LOW) — giới hạn cố hữu: blindness của annotator

"No panel ever loaded" chỉ chứng minh được từ artifacts (FETCH_LOG, manifest,
handoff) — không thể chứng minh bằng cách khác đối với lane đã kết thúc. Chấp
nhận như giới hạn cố hữu, disclose trong CYCLE_VERDICT.

## Kết quả re-review (A7 cùng lane, sau remediation)

- `A7 RE-REVIEW: CONFIRM_CLOSE` — (a) errata ghi đúng F-1..F-4, commit-times
  đo được khớp git; (b) mọi claim trong CYCLE_VERDICT nằm trong evidence của
  audit; (c) không finding nào còn chưa xử lý, không remediation nào mạnh hơn
  bằng chứng. Close được xác nhận.
