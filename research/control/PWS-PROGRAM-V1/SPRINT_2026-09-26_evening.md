# PWS-PROGRAM-V1 — Discovery sprint có chặn, tối 2026-09-26 (giới hạn 23:59 +07)

- **Owner instruction (verbatim intent, nhận ~2026-09-26T13:41Z / 20:41+07):** vận
  hành discovery sprint tự động, giới hạn đến 23:59 giờ Việt Nam hôm nay, nhằm
  tìm **tối đa 2** strategy identity khác cơ chế có backtest walk-forward dương
  sau đầy đủ chi phí. **Đây là mục tiêu tìm kiếm, không phải chỉ tiêu buộc phải
  đạt. Kết quả 0 hoặc 1 là hợp lệ; tuyệt đối không nới gate, thử vô hạn, đảo dấu
  strategy chết, chọn lại cửa sổ để đạt số 2.** Không tự giả lập owner GO.
- **Áp dụng đồng thời** standing delegation
  `OWNER_DELEGATED_DECISION_charter_and_go1_2026-09-26.json` (mục tiêu "đỉnh
  cao nhất" = bằng chứng mạnh nhất + trung thực nhất, không phải PnL dương bằng
  mọi giá) + master `plans/PLAN_pws_program_v1.md` + amendment Option A (hiệu
  lực theo Q2) + toàn bộ luật umbrella/SRLV/ERP kế thừa. Sprint này **không
  thêm, không sửa, không nới** bất kỳ luật/cap/fence nào.

## Phạm vi & nhịp thực thi (binding)

| Phase | Việc | Gate/điều kiện dừng |
|---|---|---|
| S0 | Re-measure state; đối soát SOLUSDT (1 identity F0-killed, slate trống, 0/18 scored — **KHÔNG nói "100 strategy đã bác bỏ"**) | xong 20:5x+07 |
| S1 | Sprint plan này | trước mọi score |
| S2 | Đóng PWS-CX-SOLUSDT-C1 đúng thủ tục: **A7 terminal fresh-context** + two-half close (registry TERMINAL, MAP bullet, IDENTITY_REGISTRY đã append-only 2 rows) | Bước bắt buộc TRƯỚC khi pair kế mở (master §3.2) |
| S3 | Pair kế theo thứ tự đã duyệt Q3: **BNBUSDT** — child plan + A7 plan review; tiêu GO-1 `GO PWS CX BNBUSDT C1 COUNCIL AND FREEZE` **theo ủy quyền chuỗi GO hiện hành** (điều kiện cấu trúc: child plan ✓ + A7 AUTHORIZED_FOR_GO1_GATE ✓ + đúng thứ tự Q3 ✓; ghi GO RECORD) | A7 REFUSED ⇒ dừng, gói owner packet |
| S4 | C0→C3: lane C1 data gate (klines 1h + funding fapi + spread census bookTicker, disk-check trước) song song council P1/P2 blind + skeptic F-0 (VETO pre-PnL). Điểm nhấn theo khuyến nghị A1 SOLUSDT + chỉ thị owner: proposer phải có **bằng chứng thông tin/cơ chế MỚI**; cùng observable cũ chỉ sinh lại dead family ⇒ đóng **NO_NEW_INFORMATION**, không chạy backtest | slate rỗng ⇒ close tại C3, 0 scored cells |
| S5 | (Điều kiện) GO-2 scored walk-forward **chỉ khi**: slate khác rỗng VÀ A7 prelaunch PASS VÀ còn ≥45' trước 23:59. Cost ×1/×1.5/×2, controls, DSR + N_registry disclosure, trial ledger mọi outcome view | thiếu 1 điều kiện ⇒ freeze-and-park + owner packet cho GO-2 |
| S6 | Báo cáo cuối + commits theo pathspec + registry. GO-3/shadow/orders: **NGOÀI sprint** | hard wrap 23:30+07 để còn báo cáo |

## Trial accounting & nhãn

- Không gì tối nay vào denominators scored trừ khi GO-2 thật sự được tiêu và
  cells được compute (P-9). Proposal vào IDENTITY_REGISTRY (N_registry ≤ 100);
  kill rows là assets.
- Mọi kết quả dương tối nay (nếu có) = **`BACKTEST_CANDIDATE_PENDING_OOS`**
  (paper-tier, `ANCESTRY_EXPOSED_DEV`, `SINGLE_VENUE_PANEL`,
  `FUNDING_PATH_STRESSED`, `FILL_QUALITY_CLASS_declared`,
  `PROXY_NOT_ORDERBOOK` khi áp dụng) — KHÔNG gọi là "strategy kiếm lời thật";
  OOS/prospective cần GO-3 riêng theo luật.
- S1 `SEALED_UNTOUCHED`; không đụng shadow workers/daemons; heavy lock
  machine-wide tôn trọng (một scored run tại một thời điểm); không
  push/merge/rewrite; root commits chỉ theo pathspec artifact PWS.

## Diễn giải quyền GO cho BNBUSDT GO-1 (ghi minh bạch)

Standing delegation ghi: "Ủy quyền này bao trùm **chuỗi GO của PWS-PROGRAM-V1**
(bắt đầu GO-1 PWS-CX-SOLUSDT-C1) với điều kiện gate từng bước như trên", và
boundary chỉ loại trừ slate change **ngoài thứ tự đã duyệt**. Q3 đã duyệt thứ
tự SOLUSDT → BNBUSDT → BTCUSDT → ETHUSDT. Do đó GO-1 của BNBUSDT nằm trong
ương quyền, tiêu khi đủ điều kiện cấu trúc (child plan + A7 review
AUTHORIZED_FOR_GO1_GATE), ghi GO RECORD trích dẫn delegation. Nếu owner không
đồng ý diễn giải này: mọi artifacts còn reversible (child plan DRAFT, registry
row có thể pause) — decision packet kèm báo cáo cuối.

## Ngân sách sprint (tự chặn)

- Thời gian: hard stop mọi lane 23:30+07; báo cáo cuối trước 23:59+07.
- Compute: bookTicker census chỉ chạy khi disk trống ≥25GB; nếu thiếu ⇒ ghi
  `NOT_RUN_DISK_CONSTRAINT`, cost-ceiling fail-closed theo luật (BLOCKED cho
  scoring, không điền số đẹp).
- Cells: 0 trừ khi GO-2 hợp lệ; program cap ≤96 (CX≤48) không bị chạm tới
  bởi bất kỳ điều gì tối nay ngoài scored cells thật.
