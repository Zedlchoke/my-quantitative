# BÁO CÁO TIẾNG VIỆT — FUTURES-5SYM-PRESCORED-20261005 (2026-10-05)

> **Cập nhật wave-3 (đợt 2, cùng ngày):** xem mục "WAVE-3" ở cuối file. Báo cáo
> wave-2 bên dưới được giữ nguyên làm bằng chứng lịch sử; ERRATUM_1 thu hẹp câu
> kết luận "hoàn tất mọi PREP" của wave-2.

## Tóm tắt một dòng
Đã chuẩn bị xong toàn bộ PRE-SCORED cho NQ + 6E/6B/6J/6A (7 lane song song:
INTAKE / NQ / FXEB / FXJA / EXEC / HYPO / CALCOST + tổng hợp): readiness
matrix 5 mã × 9 chiều có bằng chứng, census giả thuyết 29 hàng outcome-blind
(0 PnL), SPEC/budget/cost/calendar/freeze-spec/runner-compat riêng từng mã,
runner v2 dùng chung đã fix 2 lớp bug finalize của ES và pass 42/42 test qua
đúng production path trên fixture tổng hợp — **chưa chạy scored nào, chưa gõ
GO, chưa đăng ký cycle; mọi cổng (PB2/PB3/D8/D9/D3/các trần) giữ nguyên chờ
owner**.

## Đã có gì (mỗi claim đều có path + sha trong lane tương ứng)
- **Authority matrix**: 12 mục owner-đã-phê / 28 pending / 11 chỉ-đề-xuất;
  5 mã × 9 chiều readiness, mỗi ô một verdict + bằng chứng (`intake/`).
- **NQ**: SPEC đầy đủ luật (cache_v3 re-hash 10/10 byte-exact; 66 rolls; 0
  cease-guard violations; cease-guard + canonical đang chờ ADOPT-D9), budget
  NQ-A 22 / NQ-B 29 / NQ-C 36 với 36 ID nháp, cost dual-variant A/B, lịch
  fail-closed (Good-Friday 2026 chỉ class-level 10/10) (`nq/`).
- **6E/6B**: 2 SPEC riêng, budget FX-A/B/C tách từng mã 22/33/48, cost
  6E 3.6-6.3bp / 6B 6.3-11.2bp, lưới holiday 6E 34/42 - 6B 0/42 (vắng cấu
  trúc, khai báo thẳng), mọi deliverable đóng dấu **CONDITIONAL-ON-PB2-LIFT**
  (`fx_eb/`).
- **6J/6A**: SPEC_6J PREP-READY-BLOCKED (hướng báo giá + cease-guard 2022-09-20
  tái chứng minh; RT $67.42 = 8.4499bp), SPEC_6A_CONTINGENCY giữ nguyên PB3
  PARK (tick-era $10→$5 @2020-11-20/23, không back-cast era-2; bảng contingency
  26 ID giữ nguyên văn) (`fx_ja/`).
- **Runner v2 dùng chung** (`exec/`): symbol-parameterized, 20 mã từ chối,
  lock lifecycle + post-acquire recheck, ledger append-only tách observed/
  published, reproduction twin, **finalization fail-closed — fix đúng 2 lớp
  BUG1/BUG2 mà chu kỳ ES đã ghi nhận (release-raises/handoff-raises ⇒ exit 0)**,
  42/42 test PASS qua CLI thật trên sandbox; chứng minh không ghi được vào
  governance/registry/GO thật. Số hợp đồng từng mã đang PLACEHOLDER chờ
  verifier đối chiếu — không tự coi là đã verify.
- **Census giả thuyết** (`hypo/`): 29 hàng + 2 chẩn đoán 0-ID; **0 family mới
  (honest zero — 11 ứng viên mới đều rơi vào trùng cơ chế/VOID/khóa dữ liệu)**;
  ancestry sạch với 173 hàng FAMILY_FAILURES; shortlist theo chất lượng gói
  (NQ-F1/F2 11; FX-F3/F1/F2 12 sau PB2; JF3 12; AF3 12 trong PARK).
- **Lịch/chi phí** (`cal_cost/`): 18/40 fetch permitted-route, đóng mới bằng
  capture chính thức: **BoE MPC 2026 đủ (còn 05-11, 17-12), BoJ MPM còn lại
  2026 (29-30/10, 17-18/12 — chỉ ngày, stamps vẫn NOT_IN_CORPUS), FOMC còn lại
  (27-28/10, 8-9/12), RBA 2026 đến 29-09**; 0 ô lưới product-level mới (tái
  xác minh proven-absent bằng CDX tươi); NQ holiday product-level 0/10 giữ
  NOT_OBTAINED; 3/3 file A7 re-hash MATCH.

## Còn thiếu gì (fail-closed, không tự bịa)
- **Chữ ký owner** (gói đầy đủ trong `synth/OWNER_DECISION_PACKET_P5.md`, đã
  tái-namespace tránh đụng ID): D9 (cache_v3 + cease-guard) và trần NQ + D3
  cho NQ; PB2 + trần FX + fee-basis FX cho 6E/6B; trần 6J + BBO cho 6J; trần
  6A + D8 cho 6A (kèm PB3). Placebo/BBO/e.1-e.4 là các ô dùng chung.
- **Số hợp đồng runner**: PLACEHOLDER đến khi verifier đối chiếu với identity
  từng mã đã verify (việc A-class, không cần owner).
- **Ô NOT_OBTAINED còn lại**: NQ 2026 holiday product-level; 6B 2023Q1-24Q2 +
  holiday 0/42; 6J 2023 + 2 ô định-danh; 6A 2023Q1/Q2; 6E ECU26/ECZ26 + 8 cửa
  sổ aged-out; RBA Nov/Dec-2026; ABS/Trung Quốc. Tất cả đang loại fail-closed
  với ngày cụ thể trong các file CALENDAR_PIT_POLICY.

## Owner cần quyết gì (tối thiểu để mở đường scored NQ sớm nhất)
> "D9 = Option A. Trần NQ = [22|29|36] (NQ-A/B/C), clock-shadow [(a)|(b)].
> D3 = [A|B]."
Với 6E/6B/6J/6A: mỗi mã một dòng riêng (PB2 / trần 6J / gói 6A) — chi tiết
§2 của OWNER_DECISION_PACKET_P5. Không gì trong round này tự phê bất kỳ ô nào.

## Đã chứng minh vs chưa chạy (không kết luận GO_READY)
- Đã chứng minh: dữ liệu + luật từng mã đủ đóng gói freeze (khi chữ ký có);
  runner v2 fail-closed đúng trên production path (fixture); census + ancestry
  + budget arithmetic; lịch/pit policy fail-closed có ngày; reproduce các con
  số then chốt của các vòng trước (NQ 10/10 hash, 6J 67.42, A7 3/3).
- Chưa chạy (đúng luật): prelaunch A7, exact-arm dry-run, typed GO, scored,
  twin — toàn bộ lớp C; và NQ-F3 full-era rebuild (chạy sau D9).

## Verify độc lập toàn round (bổ sung sau audit)
`verify/VERIFY_REPORT.md` tại đúng SHA `ac5c4c18`: **VERIFIED_WITH_NOTES —
0 CRITICAL / 1 MAJOR / 4 MINOR / 4 NOTE**. Tái hiện độc lập: 74/74 outputs
re-hash byte-exact; NQ cache_v3 sample 8/8 khớp manifest adopt; A7 3/3 MATCH;
shasum -c 17/17; fetch_log 18≤40, ≤2 lần/URL, tool trắng; toàn bộ số then
chốt (6J 67.42=8.4499bp, 6A 104.92/54.92, identity 6E/6B, NQ 22/29/36, FX
22/33/48, J-A 29, census 29+2) tính lại EXACT; ancestry rows thật, 0 re-entry;
fix BUG1/BUG2 có thật trong code; **pytest 42/42 tái chạy tại SHA audit
(exit 0)**; governance dir sạch; CYCLE_REGISTRY không có entry FUTURES-5SYM;
không GO_RECORDED; zero stale-cost use-as-value; zero claim PnL dương; zero
tự-phê. **V-1 MAJOR disposition**: handoff FXJA gốc mang metadata stale-draft
(dispatch_sha không phải git-SHA) — controller đã re-issue record (chỉ sửa
metadata + re-stamp digests; 10/10 evidence outputs nguyên vẹn, lane files
byte-untouched); các MINOR/NOTE đều ghi nhận không cần sửa evidence.

## Bằng chứng & SHA
Branch `prep/futures-5sym-prescored-20261005`: base `ffed828f` → `b051d61e`
(3 lane) → `059c0665` (HYPO+NQ) → `fe250465` (EXEC+CALCOST) → synth commit
(này). Handoffs `zcode_orch_v3_handoff@1` đủ 7 lane + VERIFY (sau) tại
`dispatch/`. 0 scored/PnL/S1/GO/registration/push/merge; root owner space
không đụng; heavy lock không cần (mọi phép đọc single-shot; suite pytest 4s);
ES finalize cycle chỉ đọc qua `git show`. Incident đã khai báo: 3 lane chết
vì rate-limit hạ tầng (đã chạy lại thành công); CALCOST chết trước khi viết
handoff (completion pass viết lại, sửa dispatch_sha cho đúng); EXEC tự phát
hiện bản đầu viết nhầm 1 file vào governance dir thật (artifact của chính nó,
đã xóa, runner đã sửa, test T16 chứng minh luật không-ghi).

— Hết REPORT_VI (chờ VERIFY độc lập ở commit kế tiếp).

## WAVE-3 (đợt 2 — đóng mục A + adapter machinery + freeze/wiring; sau ERRATUM_1)

**Tóm tắt một dòng:** 7 lane (CONTRACTS, MEAS-FX, MEAS-NQ, ADAPT-NQ, ADAPT-FXEB,
ADAPT-FXJA, FREEZE-WIRING) đã đóng mọi mục WORK_QUEUE loại A trong phạm vi cho
phép, triển khai **19 adapter family thật** (không còn placeholder bar-up/bar-down
trong đường chạy: runner tiêu thụ spec-packet do adapter biên dịch qua
spec_compiler) với **262 test adapter/wiring PASS (exit 0)** + 39/39 check harness
NQ-F3, mọi cổng owner vẫn fail-closed trong code — **0 scored/PnL/GO/registration;
A đã hết việc, không kết luận "chỉ còn owner ký" cho phần nào chưa làm hết.**

**Đã có gì mới (mỗi mục: command/exit/artifact trong handoff tương ứng):**
- **CONTRACTS** (67 MATCH/1 MISMATCH/4 PENDING trên 72 đơn vị hợp đồng): mọi số
  runner tiêu thụ MATCH đủ 6 mã (6A era verbatim vs 6a_tick_adjudication.json;
  6J hướng; 6E/6B GCD int-nano; NQ 3-nguồn). MISMATCH NQ rth đã sửa evidence-
  backed; 4 ô FX rth PENDING fail-closed (P5-NEW-4).
- **Đo mô tả**: FX-F5 ngưỡng rho **vintage-dependent** (+0.9097 latest vs −0.1068
  as-of; 1/27 flip); FX-F6 harness 4/4 synthetic (real-run owner-gated); AF2
  machinery proven — **0/16 vintage coverage, cần acquisition DFF**; FX-F4
  **POWER-DEAD ở thang M2c** (r 15–36, p95 gap dưới sàn RT); NQ session-σ
  **defect-INVARIANT ở median** (285/285 tái hiện bit-identical; chỉ năm-2020
  +1.27pp), phân rã RTH/Globex/break mới; MDE refresh F2 27.96bp / F3 ≥4.84bp.
- **Adapter machinery từng family (đủ 5 mã, PROPOSED, synthetic-only):**
  NQ F1/F2/F3 đầy đủ luật + F4 machinery-only + EXPWITCH refusal không-thể-chuyển-
  PASS (65/65); 6E/6B F1..F4 + F5/F6 overlay machinery + RMM, cả hai cửa sổ F4
  code riêng theo erratum M2c, DST-proof anchor MPC (86/86); 6J JF1/JF3 + JF2/RMM
  machinery + 6A contingency AF1/AF3/AF4 + RMM-6A với **luật hướng 6J và luật era
  6A là refusal-code được test** (90/90). Mọi slot owner (P5-*)=None fail-closed,
  một số refuse cả trên synthetic (RMM-6J, AF4).
- **Freeze-builder + wiring**: builder GATE-0/GATE-1 từng mã với ~10 mã từ chối
  riêng (NQ-D9 21, PB2 23, 6J-ceiling 26, chuỗi 6A 24→25→21, drift 27/30/31...),
  bundle deterministic byte-identical; **spec_compiler nối 19 adapter vào runner
  v2 KHÔNG sửa file runner**; 21/21 proof synthetic qua đường thật: PIT 2 tầng
  (adapter + compiled) byte-identical khi truncate; cease-guard lệch đúng ngày
  vi phạm; NQ-F1 end-to-end 9 identity, TRIAL==bảng, observed==published,
  DUPLICATE_RETRY không đếm đôi, twin match; 6J sign đúng luật; era 6A 10/5USD
  + refusal cost-model chéo; publication-failure giữ observed; real governance +
  registry byte-identical suốt suite. CANONICAL_INTEGRATION ghi rõ sandbox flock
  KHÔNG phải bằng chứng canonical lock; lock/registry/GO thật NOT_RUN.

**Ma trận 5 mã (code/evidence/tests đã xong | blocker còn lại):**
| Mã | Adapter ready | Tests | Blocker (owner) |
|---|---|---|---|
| NQ | F1/F2/F3 + F4 machinery + EXPWITCH-refusal | 65/65 | D9 (P5-NQ1), trần (P5-NQ2), D3 (P5-NQ3) |
| 6E | F1..F4 + F5/F6/RMM machinery (PB2-conditional) | 86/86 | PB2, trần FX (OD2/OD3), D3/e.1-e.4 |
| 6B | F1..F4 + F5/RMM machinery (PB2-conditional) | 86/86 | PB2, trần FX, D3/e.1-e.4; +lưới holiday 0/42 cấu-trúc |
| 6J | JF1/JF3 + JF2/RMM machinery | 90/90 | Trần 6J (P5-FXJA-D1), BBO (D3'), fee (D4') |
| 6A | AF1/AF3/AF4 + RMM contingency (PARK) | 90/90 | PB3+D8+D9+fee+ABS/China (P5-FXJA-D5) |

**Còn thiếu / NOT_RUN trung thực:** chạy thật mọi adapter (chờ chữ ký); FX-F5
vintage-as-of + AF2 DFF (acquisition owner); 4 ô FX rth bằng chứng; §b1.1 1m
anatomy (OD11); NQ-F3 rebuild thật (post-D9); prelaunch A7/dry-run/GO/scored
(toàn bộ lớp C). Chi tiết: WORK_QUEUE_V2 + OWNER_DECISION_PACKET_P5_V2 (có K/N
từng mục + câu phê tối thiểu).

**SHA chuỗi wave-3:** b2d086ca (erratum+manifest) → 8e03e0bd (CONTRACTS/MEAS-FX/
MEAS-NQ) → ccf0835a (ADAPT-NQ/FXEB) → 2aea1d7a (ADAPT-FXJA) → 890fbfa6
(FREEZE-WIRING) → synth commit (file này + WORK_QUEUE_V2 + PACKET_V2). Scored
thật/PnL thật/S1/GO vẫn **0**.

— Hết phần WAVE-3 (chờ VERIFY wave-3 độc lập ở commit kế tiếp).

## WAVE-4 (sửa compiler/wiring + canonical integration trước scored)
Owner-audit tại d938e9a5 phát hiện 2 khiếm khuyết → đã xử đúng luật:
1. **Lỗi mixed-direction tái hiện qua production path và ghi FAIL TRƯỚC fix**
   (commit f1f69c8e: repro 2 intent cùng identity Long+Short → 1 trade; ERRATUM_2
   thu hẹp claim "19 adapter wired hoàn chỉnh" và positional encoding).
2. **WIRING-FIX**: intent-mode mở rộng runner (schema intent_packet@1, cùng
   CLI/authority/lock/twin/ledger/finalization; accounting dùng lại nguyên bản);
   positional compiler giữ lại nhưng dán nhãn ACCOUNTING-TEST-ONLY và từ chối
   nhóm >1-intent. Test: exec 42 (không sửa test nào) + wiring 33 (3 điều chỉnh
   có khai báo, không nới lỏng) + intent seam 12; repro giờ PASS (2 trades, giữ
   nguyên identity/denominator). Đủ 10 bài test yêu cầu: parity với số học SPEC
   độc lập (không mirror), PIT prefix, fold/warmup, era 6A, hướng 6J, zero-trade
   anchor hợp lệ, retry idempotent, mọi failure path.
3. **CANONICAL-CODE**: production_exec.py bọc đúng canonical APIs của repo
   (governance.heavy_lock + registry CAS + GO two-key), 14/14 test sandbox qua
   cùng code path + read-only real-state checks; real lock/registry/GO từ chối
   hard-compiled (PREP_BUILD) — CANONICAL_INTEGRATION_V2 phân biệt rõ
   đã-làm/thời-tài-liệu.
Chuỗi wave-4: f1f69c8e (FAIL+erratum) → c12e6a5a (fix+canonical) → synth commit
này. 0 scored/PnL/S1/GO/registration; root/ES không đụng; registry không có
entry 5SYM (một foreign owner-write ES-PB1 giữa lane đã quy cho owner).
— Hết WAVE-4 (chờ VERIFY-WAVE4 ở commit kế tiếp).
