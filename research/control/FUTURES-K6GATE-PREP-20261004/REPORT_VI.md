# BÁO CÁO TIẾNG VIỆT — FUTURES-K6GATE-PREP-20261004 (2026-10-04)

## Tóm tắt một dòng
Vòng K6/anatomy đã chạy 4 lane trên dữ liệu đã commit (0 fetch, 0 PnL,
0 đăng ký, 0 dry-run/scored): **NQ-F1/F2-K6 PASS, NQ-F3 rebuild
precondition DONE, EXPWITCH chết tại gate ở CẢ HAI chân theo đúng điều
kịện khai báo trước (không chỉnh sau), FX-F1 census PASS ≥500, 6B gap-std
đo xong, tick constancy 6E/6B CONSTANT, RMM mode ledger đóng NOT_RUN,
6A D-2 audit交付** — kèm điều kiện bổ sung của owner: **packet check
fresh-context tại đúng HEAD 05e54939 → FAIL ban đầu (F-4/F-5/F-6: sót
stale-cost trong shortlist/ vòng trước) → đã xử append-only bằng
SHORTLIST_STALE_COST_ERRATUM, CYCLE-1 giữ BLOCKED_COST_FREEZE**; verify
độc lập toàn round: VERIFIED 4/4 + chain đóng, 0 CRITICAL/0 MAJOR.

## Kết quả gate (đầy đủ trong synth/SYNTHESIS_K6.md)
| Mã | Kết quả chính |
|---|---|
| NQ | F1-K6 PASS (2.230×/0.686×, n=85, vòng repair chấp 1 sự kiện 2020-04-29); F2-K6 PASS mọi era (4.51×; ô 2010-16 giờ đo được 4.39×; falsifier ngày-hủy sạch); **F3 rebuild precondition DONE** (series khớp nq_held_daily_v3 diff 0.0; DD 2020 32.28→34.12% = số addendum); **EXPWITCH-NQ leg FAIL** (35/66 phiên expiry-Friday có gap RTH 15-phút — vendor granularity era-chung, không phải tham số chỉnh được; part i vẫn PASS) |
| ES | F1-K6 PASS (2.646×/0.828, n=91); F2-K6 PASS cả 3 era (3.416/2.504/2.955; falsifier hủy-phiên 0.843/0.918); **F4-K6 NOT_RUN đúng luật** (điều kiện trên tín hiệu giá — cấm vòng này, disposition viết trước); **EXPWITCH-ES leg FAIL** (T3 1.220 < 1.25, sát ngưỡng −0.030; part ii PASS 61/61) — theo family law chân ES không bao giờ vào scoring, bảng margin công bố cho owner, KHÔNG chỉnh ngưỡng sau |
| 6E/6B | FX-F1 court census **PASS cả hai** (6E 1,362 / 6B 1,342 ≥ 500; MDE-at-n ≈3.5/4.2bp); FX-F4 census + **6B gap-std đo xong** (std 0.0304%/0.0400%; Sunday 317; không có ngưỡng nên không bịa); **phát hiện append-only M2c**: baseline "reopen-gap" mà FX_HYP §4.1 trích (0.3778%) thực chất là gap mở RTH 08:30 — gap reopen 17:00 thật nhỏ hơn 2.3-5×, ghi nhận không sửa; **tick constancy CONSTANT** (GCD 50k/100k mọi cửa sổ) — đóng D-2 bước (iii), chứng minh thay đổi lưới là đặc thù 6A |
| 6J/6A | JF1-K3 giao đủ (ANCHOR_INSENSITIVE_AT_45MIN, 7 biến thể, 54 ngày MPM; verify kiểm lại nhãn-phùng-số: nhất quán); **RMM D-1 mode ledger ĐÓNG** (6E 22/5, 6B 23/4, 6J 19/8 abrupt/gradual; 6A 21/6 tái lập; CEASE-SYNC 18/24 tuần abrupt khớp cả 4 mã ±1 tuần — mô tả, placebo block-shuffle giữ bên scored); **6A D-2 (i)+(ii)**: era-1 RT $104.92=15.18bp vs era-2 $54.92=8.20bp (MODELED) + step test 6A ×0.50 USD/tick vs 6J ×1.00 — xác nhận mô hình era-2 không được back-cast |

## Điều kiện bổ sung của owner (packet check 05e54939) — xử lý xong
- **Kết quả: FAIL** (verify/PACKET_05e54939_CHECK/): chuỗi authority
  (ODP/ERRATUM/CYCLE_PROPOSAL/REPORT_VI) sạch 100% (C1/C3/C4/C5 PASS:
  3 lỗi câu chữ biến mất, 2 biến thể số học đúng từng ô, frozen zero-diff,
  SPEC sha khớp pin) — nhưng **shortlist/ vòng six-gate còn 2 CRITICAL +
  1 MINOR sót stale-cost** (F-4: "21.006/33.506/46.006 FROZEN Variant A
  binds until D3" không nhãn stale; F-5: "S2 33.506 floor" dùng làm số;
  F-6: liệt kê blocker thiếu chữ ký D3).
- **Xử lý theo luật owner (giữ BLOCKED + append-only)**:
  `synth/SHORTLIST_STALE_COST_ERRATUM.md` supersede-by-reference (không
  sửa file đã commit của vòng trước — six-gate worktree vẫn HEAD 05e54939
  sạch, verify E2 xác nhận); số hiệu chỉnh: S2 floor = 33.50 (A) / 33.49
  (B), delta 0.006 USD không đổi verdict MDE nào (ghi chú số học, không
  phải rescue); blocker PB1 dẫn đầu bằng chữ ký D3.
- **CYCLE-1 giữ nguyên BLOCKED_COST_FREEZE** chờ D3 — không có gì được
  nip mở vì packet check FAIL; erratum là correction of record cho mọi
  consumer sau.

## Verify độc lập toàn round
`verify/VERIFY_REPORT.md`: **VERIFIED 4/4 lane + synthesis +
packet-check-chain CLOSED — 0 CRITICAL / 0 MAJOR / 1 MINOR / 3 NOTE**.
Mọi số then chốt tính lại độc lập: NQ FOMC era rows bit-exact; ES T3
1.2204 tái tính đúng; census 6E 2026 exact; mode split 6J exact; cost
arithmetic 6A exact; rebuild diff 0.0; 6J bar-identical; σ 6E trong ~1%;
6 câu predeclaration trích verbatim khớp; FAILs đứng nguyên không chỉnh;
zero stale-fee use-as-value; handoffs chuẩn; P3 zero-touch. MINOR V-1:
mirror a1-recipe chứa aggregate return vô điều kiện (recipe-bắt-buộc để
đối chiếu a1 đã commit, không gate, đã khai báo) — ghi nhận, không sửa.

## Trạng thái scored-readiness (trial scored = 0)
| Mã | Còn chặn (phía owner) |
|---|---|
| ES | **D3 (BLOCKED_COST_FREEZE)** → registration → prelaunch A7 → GO |
| NQ | D9 + trần NQ → registration → A7 → GO (mọi gate PREP-legal có thể PASS đều PASS; EXPWITCH-NQ leg chết tại gate — không vào slate) |
| 6E/6B | PB2 lift + trần FX → registration → A7 → GO |
| 6J | Trần 6J + BBO/cost → registration → GO |
| 6A | PB3 lift + D8 (contingency) |

## Đề xuất thứ tự (bằng chứng hiện giữ nguyên)
**ES PB1 → NQ → FX**: ES PB1-only 24 ID vẫn là đường ngắn nhất (chỉ còn
D3 + registration + A7 + GO); NQ đã có đủ gate PREP PASS (chỉ còn D9 +
trần — đều là chữ ký); FX chờ PB2/ceiling. EXPWITCH chết cả 2 chân nên
không xuất hiện trong slate nào — census giả định không đổi (chưa từng
đăng ký).

## Bằng chứng & SHA
Branch `prep/futures-k6gate-20261004`: base 05e54939 → wave 1
`3645edd0` (4 lane + synthesis) → **final** (packet check + erratum +
verify + báo cáo này). Handoffs `zcode_orch_v3_handoff@1`:
`dispatch/handoff_{NQ-K6,ES-K6,FXEB-K6,FXJA-K6,VERIFY}.json`. Root không
đụng; heavy lock không cần (mọi phép đọc single-shot; NQ lane ghi lại
locks-inspect FREE).

— Hết REPORT_VI (đã verify).
