# PACKET QUYẾT ĐỊNH CUỐI — FUTURES-ES-PB1-V1 (chờ owner ratification; KHÔNG phải GO)

- Trạng thái khi viết: worktree `1069b2da`, root `f7b38ac2`, registry head
  đồng bộ, lock FREE, doctor chỉ còn STALE_HEARTBEAT LOW (label-only).
  Scored thật **0/24**. Audit độc lập tại `1069b2da` đã xác nhận có phạm
  vi: GO giả + pin sai ⇒ exit 2 REFUSED_DRIFT chặn trước execution.
- **D-8 đã FIXED-WITH-EVIDENCE** (không còn waiver): lỗi enforcement pin
  được tái hiện tới completion, sửa theo FAIL-before-fix, verifier tái dựng
  cả pre-fix lẫn post-fix — owner KHÔNG bị yêu cầu chấp nhận lỗi kỹ thuật
  nào trong packet này.

## QUAN TRỌNG: "PASS" trong ledger nghĩa là gì?
**Ledger PASS/FAIL là trạng thái thực thi. Tiêu chí khoa học đã được
preregister tại SPEC §8; kết quả đánh giá hiện NOT_RUN và sẽ được
terminal A7 kiểm tra sau scored.** (Sửa theo chỉ thị owner 2026-10-05 —
thay cho câu sai trước đó "chưa có ngưỡng khoa học nào".) Bằng chứng
bytes — SPEC_PB1_ES §8 "Stage-A gates (pre-registered; per identity)":
G1 after-modeled-cost expectancy > 0 tại S2 (và S1) · G2 PF ≥ 1.10 tại
S2 · G3 ≥ 2/4 folds positive tại S2 · G4 K1 era-sign ổn định · G5 K4
D0/D30 không đổi dấu (họ P-A) · G6 K3 <80% đóng góp 2020-03..04 · G7 arm
vượt C2 và C1 về after-cost expectancy tại S2 · G8 repro byte-match ·
G9 A7 0 HIGH/CRITICAL unresolved; K2 family-kill (cả hai tay dưới sàn ⇒
dead, cấm re-tparam). Hai tầng tách bạch: tầng VẬN HÀNH (ledger) ghi
thực thi; tầng KHOA HỌC (G1-G9/K2) do terminal A7 đánh giá trên kết quả
scored — hiện NOT_RUN vì chưa có scored run. Kết quả âm là kết quả hợp
lệ, đếm đủ denominator; không ai được đọc số quarantine để quyết định gì
trước GO.

---

## D-1 — Ngữ nghĩa PASS/FAIL của 24 dòng ledger
- **Owner quyết**: nhận ngữ nghĩa `PASS = mechanics của identity chạy xong
  (có record)`, `FAIL = computation của identity raise`; các kiểm tra
  cost/warmup chạy như reconciliation cấp-run fail-closed (không phải
  verdict từng identity).
- **Khuyến nghị: RATIFY mặc định.** Căn cứ: hai tầng tách bạch —
  ledger ghi TRẠNG THÁI THỰC THI; tiêu chí KHOA HỌC đã preregister tại
  SPEC §8 (G1-G9 + K2), hiện NOT_RUN, sẽ do terminal A7 kiểm tra sau
  scored. Phân cấp này giữ denominator trung thực (24 kết quả đều được
  đếm) và không để tầng vận hành tự phong kết quả khoa học.
- **Alternatives**: (a) nhét tiêu chí khoa học vào ledger PASS — SAI TẦNG
  (G1-G9 đã đăng ký ở SPEC §8, thuộc terminal A7; trộn tầng sẽ khiến
  denominator lệch và mở cửa kết luận chọn lọc); (b) đổi tên trạng thái
  (DONE/ERROR) — thuần cosmetic, cần sửa ledger schema.
- **Tác động nếu đổi**: phân bố trạng thái 24 dòng terminal; accounting
  denominator không đổi; recovery không đổi.
- **Đang áp dụng/test**: F-suite (24 rows observed=24 exact); T4/T5.
- **Câu phê**: `FUTURES-ES-PB1-V1/D-1: RATIFY DEFAULT (PASS=mechanics-complete, FAIL=computation-raised; run-level reconciliation carries quality gates)`

## D-2 — File cấp-run khi publication failure
- **Owner quyết**: chấp nhận rằng khi write output fail (vd thư mục
  read-only), các file cấp-run (`trades_index.json`, `summary.json`) ghi
  nhận là publication failure (`identity_id: null`), pass vẫn chạy xong để
  twin + reconciliation chạy, và run **luôn kết thúc non-zero** (không
  tồn tại "thành công một phần").
- **Khuyến nghị: RATIFY.** Căn cứ: fail-closed toàn tuyến; denominator
  giữ (đã đếm thì không hoàn); twin vẫn có chứng cứ so sánh.
- **Alternatives**: dừng ngay khi publication fail đầu tiên — mất khả
  năng thu thập toàn bộ lỗi trong một run; hoặc coi publication fail là
  thành công — vi phạm luật fail-closed đã khóa.
- **Tác động**: code (không đổi nếu ratify); accounting (đã đếm vẫn đếm);
  recovery (retry theo D-3); kết luận run (luôn non-zero khi có lỗi).
- **Đang áp dụng/test**: T4 (rc3, 24 rows vẫn observed, published=false
  trên 4 file).
- **Câu phê**: `FUTURES-ES-PB1-V1/D-2: RATIFY (run-level publication failures recorded identity_id=null; run always non-zero; no partial success)`

## D-3 — Retry khi output trước đó mất/không xác minh được
- **Owner quyết**: slot đã terminal mà bytes published trước đó MẤT hoặc
  không khớp `result_sha` ghi nhận ⇒ **KHÔNG tính lại** (luật budget
  thắng); run kết thúc `PRIOR_TERMINAL_OUTPUT_MISSING` fail-closed.
- **Khuyến nghị: RATIFY.** Căn cứ: luật budget đã khóa cấm tính lại
  identity đã terminal (chống chạy lại để "thử may" / né denominator);
  mất evidentiary closure là lỗi nghiêm trọng phải lộ ra, không phải lý
  do recompute.
- **Alternatives**: cho recompute khi output mất — **cần owner amendment
  riêng cho luật budget** (mở cửa selective-rerun risk); hoặc đánh dấu
  NOT_RUN — sai sự thật (đã compute).
- **Tác động**: nếu chọn recompute: thay đổi accounting law + code retry
  + phải chạy lại gate liên quan; ratify mặc định: không đổi gì.
- **Đang áp dụng/test**: D-3 implemented; T5 chứng minh retry skip
  terminal slots (5 skipped, observed=24).
- **Câu phê**: `FUTURES-ES-PB1-V1/D-3: RATIFY (missing/unverifiable prior output => PRIOR_TERMINAL_OUTPUT_MISSING fail-closed; NEVER recompute; budget law wins)`

## D-4 — Sandbox R0 dùng worktree THẬT cho git identity
- **Owner quyết**: luật isolation áp cho mọi đường dẫn authority
  INPUT/OUTPUT; riêng bước registry-check đọc **read-only** branch/HEAD của
  checkout thật để đối chiếu với bản COPY registry trong sandbox.
- **Khuyến nghị: RATIFY.** Căn cứ: đó là cách duy nhất sandbox kiểm được
  "head của row copy có phản ánh cây thật không" mà không ghi gì vào root;
  đọc read-only không vi phạm owner space.
- **Alternatives**: sandbox tự giả git identity — làm mất giá trị kiểm
  tra (sandbox sẽ không bao giờ bắt được drift thật).
- **Tác động**: chỉ ảnh hưởng test infrastructure; production không đổi.
- **Đang áp dụng/test**: P8/T10 (registry tamper ⇒ refuse).
- **Câu phê**: `FUTURES-ES-PB1-V1/D-4: RATIFY (sandbox registry check reads the real worktree read-only for git identity vs the sandbox row copy)`

## D-5 — Nơi chứa artifacts của run thật (post-GO)
- **Owner quyết**: mặc định output scored chạy thật nằm tại
  `<gate6/ledger>/runs/<run-label>/` (cạnh ledger thật).
- **Khuyến nghị: RATIFY.** Căn cứ: giữ evidentiary closure (output cạnh
  ledger cùng chuỗi sha); đơn giản cho terminal A7 và reproduction twin.
- **Alternatives**: thư mục riêng ngoài git worktree — cần contract
  amendment + đường dẫn pin mới; chấp nhận được nhưng không thêm giá trị.
- **Tác động**: chỉ đường dẫn; accounting/recovery không đổi.
- **Đang áp dụng/test**: cấu hình mặc định của executor; mọi suite dùng
  chính cấu trúc này trong sandbox.
- **Câu phê**: `FUTURES-ES-PB1-V1/D-5: RATIFY (production run artifacts default to <gate6/ledger>/runs/<run-label>/)`

## D-6 — Mã exit 3 gộp các trạng thái failure kỹ thuật
- **Owner quyết**: `TWIN_MISMATCH / PUBLICATION_FAILURE / COMPUTE_FAILURE
  / RECONCILIATION_FAILURE / ABORTED_SANDBOX_FAULT /
  PRIOR_TERMINAL_OUTPUT_MISSING` đều exit **3**, phân biệt bằng
  `terminal_state` trong manifest/handoff.
- **Khuyến nghị: RATIFY.** Căn cứ: một mã cho "technical failure" giữ
  CLI contract đơn giản; ngữ cảnh chính xác nằm trong artifact máy-đọc-được.
- **Alternatives**: mã riêng từng trạng thái — machine-friendly hơn nhưng
  phình bảng mã và không thêm năng lực phân biệt (artifact đã phân biệt).
- **Tác động**: scripts gọi runner phải đọc terminal_state cho chi tiết.
- **Đang áp dụng/test**: T3 (TWIN_MISMATCH rc3), T4 (rc3).
- **Câu phê**: `FUTURES-ES-PB1-V1/D-6: RATIFY (all terminal technical-failure states exit 3, distinguished by terminal_state in the manifest/handoff)`

## D-7 — Luật finalization-failure (+ exit 4 + v2.2/v2.3 re-pins)
- **Owner quyết**: nhận cả gói luật: mọi lỗi finalization (ledger-summary/
  lock-release/runtime-restore/handoff-write) ⇒ trạng thái
  `FINALIZATION_FAILURE` + **exit 4** (phân biệt exit 3); danh sách
  `finalization_failures[]` gom MỌI bước hỏng (không che lỗi gốc);
  `computation_complete` ghi riêng (computation xong + finalization hỏng
  = THẤT BẠI, không bao giờ EXECUTION_COMPLETE); luật bằng chứng lock
  (release raise ⇒ `UNVERIFIED_RELEASE_RAISED` + canonical inspect,
  không bao giờ claim released, không force-unlock/kill); run đã fail
  giữ nguyên terminal state gốc. **Kèm theo: các re-pin v2.2/v2.3 của
  contract (executor/runner hiện hành) có hiệu lực cùng phê quyết này.**
- **Khuyến nghị: RATIFY.** Căn cứ: plan không có vocabulary terminal cho
  executor (SPEC §9 là tầng A7, runner không được chọn); gói luật này là
  dạng chuẩn nhất của fail-closed evidentiary closure và đã được chứng
  minh bằng behavioral tests (F-suite).
- **Alternatives**: vocabulary khác/tách mã khác — thuần danh pháp, cần
  sửa code + re-pin + re-test toàn bộ F-suite; hoặc bỏ exit 4 gộp vào 3 —
  mất khả năng phân biệt máy (computation-complete-but-unclosed).
- **Tác động**: đây là luật vận hành của mọi scored run thật; ratify =>
  không đổi code (đã implement + test); từ chối => chỉ định thay thế,
  sẽ sửa + re-pin + chạy lại gates theo plan.
- **Đang áp dụng/test**: F-suite 10/10 (BUG1/BUG2 reproduction flip; F4
  release-raise-after-unlock; F6 no-masking; F8 retry).
- **Câu phê**: `FUTURES-ES-PB1-V1/D-7: RATIFY (FINALIZATION_FAILURE law + exit 4 + evidence laws + v2.2/v2.3 contract re-pins take effect)`

---

## Mục tùy chọn (formality, nên ký kèm nhưng không phải lỗi)
- **D-A4/D-A5 acknowledgment**: cả hai đã có authority dispositive trong
  SPEC (chuỗi trích dẫn nguyên văn tại `pins2/DA45_DECISION_PACKET.md`);
  một dòng xác nhận của owner khép lại vĩnh viễn:
  `FUTURES-ES-PB1-V1/DA45: ACKNOWLEDGE AUTHORITY (chain-wide strict-past donor windows; USD-line costs + fill-anchored TP/SL per SPEC)`

## Kiểm tra tính đầy đủ của packet (không che quyết định load-bearing)
- Đã quét: mọi [IMPLEMENTATED-DEFAULT-PENDING-RATIFICATION] trong
  EXEC_BUILD_REPORT §7 = đúng 7 mục D-1..D-7 ở trên; D-8 đã chuyển
  FIXED-WITH-EVIDENCE (không còn trong danh sách chờ). Pins
  D-A1/A2/A3 đã được owner phê trước đây (auth/PREGO_REPAIR_RECORDED).
  Không có quyết định load-bearing nào khác đang treo ở tầng implementation.
- Lỗi kỹ thuật nào phát sinh sau này sẽ được xử lý trong phạm vi PRE-GO
  theo FAIL-before-fix + audit độc lập — **không** biến thành mục owner
  chấp nhận.

## Checklist SAU khi owner ratify (controller sẽ thực hiện)
1. Ghi nguyên văn quyết định owner vào `auth/` (schema
   owner_decision_record@1, kèm quote + thời điểm + SHA hiện hành).
2. Nếu quyết định làm thay đổi implementation (khác mặc định): sửa code
   theo luật, re-pin contract, chạy lại gates bị ảnh hưởng theo plan.
3. Nếu ratify đúng mặc định: cập nhật contract ghi trạng thái ratified
   (append-only) — không đổi bytes implementation.
4. Audit độc lập tại committed SHA cuối; reconcile registry qua
   researchctl CAS khi ROOT_DIRTY=0 (hard-stop nếu bẩn).
5. Kiểm tra fresh state (registry head == HEAD, doctor sạch ES, lock
   FREE, pins 100%) — khi đó mới đề nghị owner gõ typed GO:
   `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` (owner only, tại gate của
   cycle; paraphrase chết chưa tiêu thụ).

— Hết packet. Chờ owner ratification; KHÔNG tự phê mục nào.
