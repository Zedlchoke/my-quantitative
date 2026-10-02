# ACTION PACKET VÒNG 4 — successor_design_2026-10-02 (tiếng Việt, cho owner)

## Đã tính được gì (mới trong vòng này, đều từ journal đã commit, 0 PnL mới)

**1. Histogram dải chi phí của cost guard (deliverable B)** — mở khóa câu
hỏi J3 mà trước đó đánh dấu NOT ESTIMABLE: cả 627 lệnh DEFER đều nằm ở
r = spend/cap ∈ [1.00, 1.41] (POLICY n=331 median 1.03, max 1.20; B1 n=296
median 1.06, max 1.41; cap hằng số $2,836.97). **Không có dòng nào ≥ 1.5×
⇒ grid {1.5, 2.0, ∞} của RULE_SLATE là suy biến tĩnh** — cả ba node thừa
nhận đúng cùng 331/296 defer (0 defer thật, 8/8 fold đạt floor ≥3). Nếu
muốn grid phân biệt được phải hạ vào [1.00, 1.41] (m=1.1 giữ 5%/27% firing,
m=1.2 giữ 0%/15%) — kèm hai caveat: nội sinh (cap đối chứng làm đổi đường
spend và guard tự re-bind) và selection (r chỉ quan sát trên các defer đã
kích hoạt). Hoặc đơn giản hóa hypothesis thành binary: gỡ guard hay giữ ở
cap.

**2. Lỗi dấu swap trong docket A (phát hiện quantified)** — đẳng thức
excursion của docket A cộng nhầm swap (chi phí dương): "Σnet = fills +
swap" 602.9k/689.7k **đảo signs đúng là fills − swap** và khớp engine
`per_symbol_fold_records` tới **$0.000 trên cả 6 ô arm×symbol**
(600,082.92 / 687,284.31); "residual 2,860.19 (0.48%)" mà docket giải thích
là quy ước fold-edge **chính xác bằng 2×swap — không có residual**. Tác
động: mọi Σnet tuyệt đối USDJPY trong docket A (kể cả tổng W/L/B) cao hơn
thật 0.2–0.5%; phân loại W/L/B và mọi phát biểu tương đối KHÔNG đổi; các
file dossier/complementarity của packet đã dùng số engine đúng. Docket là
artifact đã commit 01-10 — không sửa; ROUND4_ADDENDUM +
forensics/verification_checks.json là bản đính chính của record.

**3. Đối chiếu DST/session (mô tả)** — bucket NY-long USDJPY 172 quyết
định (67 GMT / 105 BST = 61% vs 58% lịch) — không cô lập một pha DST nào;
đô London-close cho thấy bucket nằm +1..+5h sau close mùa đông nhưng
+2..+6h mùa hè (NY-local 11–16 vs 12–17) — **rule theo UTC trần là nhạy
phaa DST**, xác nhận yêu cầu session-mark suy deriv từ lịch (đã nằm trong
HN-1). Không claim nhân quả.

**4. Corrections C1–C5** áp đủ: Poisson = model-based estimate (không phải
bound, bất định hai chiều), denominator đóng băng theo estimand (không đổi
entry→decision hay per-leg→battery để lọt floor); pooled JPY/EUR chỉ là mô
tả (không cứu grid per-symbol, không chứng minh cơ chế chung); impact của
DAILY floor-lookahead = **IMPACT_ON_VERDICT_NOT_MEASURED** (verdict đứng
nguyên, reliability được ghi chú; không tự diễn giải directive, tách trục
PERMISSION vs EXPOSURE; erratum append-only cho DAILY được ĐỀ XUẤT, chưa
chạy); verifier ghi rõ giới hạn symbolic-ID (config uniqueness chỉ chứng
minh ở FREEZE-2 qua exact-arm dry-run, kèm luật sụp đổ J3=∞); B1S được
scope đúng (đo hygiene trên tập admitted; giá trị nghỉ hưu S017 so với
book gốc 12 chân do chương trình replay đo qua REPLAY_ORIG12); stress tĩnh
chỉ hợp khi path-invariant (rule gắn cost-state phải re-run full).

## Hypothesis nào đủ mẫu / thiếu mẫu (tổng kết matrix + cập nhật vòng 4)

- **Đủ mẫu trên validation 6×26w:** HN-1-JPY (55–68 pooled), LOL 8/11 chân
  (≥98%), HN-2 với lõi 4 chân vote-carrying, J3 dạng binary hoặc grid trong
  [1.00,1.41] (số quyết định dồi dào; giá trị biên chỉ đo được bằng replay).
- **Biên giới:** HN-1-EUR (24–32% rủi ro trượt floor sổ — pre-type
  NOT_RUN_THIN branch), HN-3/S014 (33–65% theo đơn vị entry — đơn vị đánh
  giá đóng băng tại FREEZE-1).
- **Cấu trúc thiếu mẫu (pre-typed, không nới floor):** S017-refutation
  (P≈0.03%), LOL∖S023 (≈0.0005%), LOL∖VC2-JPY (17%), cả hai LEARN grid
  HN-1 (70–100% trượt).

## Bước exploratory cụ thể kế tiếp — mỗi bước cần gate gì

| bước | nội dung | gate kế tiếp (chưa có gì chạy) |
|---|---|---|
| 1 | **TB-LABELS producer** theo `tblabels/TB_LABELS_EXECUTION_PREP.md` (barrier theo file:line, luật AMBIGUOUS_ORDER không đoán thứ tự, quote-side/fill-lag theo FILL_ACCOUNTING_SPEC, DST-aware, censoring; skeleton đã có và từ chối chạy) | owner review spec → đăng ký cycle analysis-only nhỏ → chạy trên vùng TRAIN/EXPOSED của panel đã commit; rate ambiguous >20% là gate NOT_RUN_TOUCH_RESOLUTION |
| 2 | **EXPLORATORY-REPLAY-V1** theo `EXPLORATORY_REPLAY_LAUNCH_DRAFT.md`: 13 identities/104 rows full-path trên fold đã expose — ưu tiên Q1 xung đột dấu S014 (delta toàn-path là cách đo hợp pháp duy nhất), Q2 blend S026, Q3 nghỉ hưu S017 so book gốc (REPLAY_ORIG12 — comparator mà battery chính thiếu) | owner duyệt draft → plan → đăng ký (FREEZE-1: manifest 13 arm + luật INF/ECO + tolerance đối chiếu engine với B1 PC12A) → implement + T1–T4 → freeze → A7 → GO → chạy; kết quả = PRIOR cho bầu cử membership ở FREEZE-1 của cycle chính |
| 3 | (tuỳ chọn) cặp guard exploratory trong replay program — chỉ sau khi chọn grid mới trong [1.00,1.41] hoặc dạng binary (từ finding 1) | cùng gate bước 2; cần khai báo path-dependent cho stress |
| 4 | Erratum append-only phía DAILY (3 chỗ ghi "S1 SEALED_UNTOUCHED" mâu thuẫn journal) | owner action D-1a (ratify/erratum) — packet chỉ đề xuất |

Không gì phải chờ 2029/2030: bước 1–2 chạy trên dữ liệu đã expose với
budget riêng của mình; mọi kết quả là hypothesis-generating, không bao giờ
là independent validation; các acceptance bar của cycle chính không đổi.

## Trạng thái đóng gói

Commit vòng 4 gồm: corrections C1–C4 (matrix/protocol/design/register/
manifest — verifier vẫn ALL TOTALS MATCH), ROUND4_ADDENDUM, replay draft
(13/104), tblabels/ (spec + skeleton), sửa census theo đính chính swap,
cập nhật header index; forensics/ đã land từ commit lane `c081ac16`.
HANDOFF pointer commit thứ hai ghi full SHA thật của commit work (C5).
Giới hạn giữ nguyên: 0 scored, 0 S1/sealed bytes, 0 orders, không đụng
owner dirty tree và futures lane.

— hết action packet vòng 4 —
