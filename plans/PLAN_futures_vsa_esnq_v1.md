# PLAN_futures_vsa_esnq_v1 — FUTURES-VSA-ESNQ-V1 (scored S0 screen, khóa trước outcome)

Trạng thái: PLAN đăng ký qua researchctl. Chưa GO. S1 (TEST 2023-01→2026-09) NIÊM PHONG.
Nền bằng chứng PREP: `research/control/PREP-FUTURES-VIDSWEEP-20261010/` (census, σ refit v2,
day-level USD, verifier R1/R2, audit 13) — PREP-ONLY, không PnL.

## 1. Câu hỏi + estimand (V7, đã sửa theo audit owner 2026-10-10)

VS-A (liquidity-sweep → 5m BOS/iFVG → (VS-A) nhịp 5m → 1m double-BOS trigger) trên ES và NQ
cho expectancy sau chi phí dương, ổn định theo fold, ở cấp NGÀY, đơn vị USD?

- **Per-symbol estimand**: tối đa 1 tín hiệu/ngày/mã (máy done sau entry đầu); direction do
  tín hiệu quyết định (pool LONG+SHORT); day-return USD = close(fill+H) − open(fill) trên
  chain contract − RT cost. Đơn vị độc lập = ngày.
- **KHÔNG có identity family** (SUM-portfolio UNDERPOWERED: MDE $54–97 > cost $43.6 trên
  110 ngày TRAIN — 07_FAMILY_ESTIMAND_USD.json; gói family ĐÃ RÚT theo audit owner).

## 2. Identity + budget (đóng băng, budget-max 8)

| # | Identity | Spec |
|---|---|---|
| 1 | ES-VSA-H15 | VS-A ES, hold 15m |
| 2 | ES-VSA-H30 | VS-A ES, hold 30m |
| 3 | ES-VSA-H60 | VS-A ES, hold 60m |
| 4 | NQ-VSA-H15 | VS-A NQ, hold 15m (power-prune: H30/H60 MDE $30.45/$39.25 > cost $23.50 — feasibility prune theo §14.4, moment-2, disclosure) |
| 5–8 | Controls | always-on cùng giờ (C3-class: confirm→trigger, không cần sweep) ES H15/H30/H60 + NQ H15 — scored, khai báo, không nơi chọn winner |

Signal/entry/exit/fill/cost/calendar: **verbatim** `03_RULEBOOK_AMBIGUITY.md` (R.0–R.4,
P1–P12) + `07_FAMILY_ESTIMAND_USD` conventions; chain T-5 PIT; population = phiên band pass
chain+X1 (ES 4,180 / NQ 3,933 ngày máy); CPI/NFP-fence X5. Cost RT S1 Variant A MODELED
(ES $42.00, NQ $23.50) — **RE-PIN bắt buộc trước GO** (điều kiện đăng ký; nếu re-pin làm
MDE > cost cho identity nào thì identity đó tự NOT_EVALUABLE, không bỏ ngưỡng).

## 3. Cửa sổ + S1

- S0 scored: TRAIN+VAL 2010-06→2022-12-31 (TRAIN đã moment-2-exposed — disclosure; VAL
  outcome-pristine tới thời điểm freeze).
- **S1 = TEST 2023-01→2026-09: NIÊM PHONG**, chỉ mở bằng plan/owner sau. External exposure
  yếu của TEST (video demo 5/2026) đã disclosure.

## 4. Gates (áp per-identity tại S0, sau cost; kế thừa SPEC_PB1_ES §8 shape)

G1 after-cost expectancy > 0 · G2 PF ≥ 1.10 · G3 ≥ 2/4 folds (2010-12/13-15/16-18/19-22)
positive · G4 không >70% PnL tập trung 1 fold · G5 day-concentration ≤ 0.50 · G6 vượt
always-on control cùng hold về after-cost expectancy · G7 repro byte-match (detached twin)
· G8 A7 prelaunch 0 HIGH/CRITICAL · G9 dry-run exact-arm non-vacuous, zero budget delta.
**K2 per-symbol**: một mã có tất cả identity primary FAIL ⇒ mã đó DEAD, cấm re-param; mã
kia độc lập. Không re-param sau khi nhìn PnL; mọi amendment = plan mới + owner.

## 5. Đăng ký + GO

- Registry: `FUTURES-VSA-ESNQ-V1` · branch `orca/vsa-esnq-v1-integration` · worktree
  `.worktrees/vsa-esnq-v1/integration` · budget-max 8 · lifecycle ACTIVE_LIGHT sau
  bootstrap. Ghi qua researchctl CAS khi lock FREE.
- **GO phrase (nguyên văn, chỉ typed tại gate của chính nó, P-8):**
  `GO FUTURES-VSA-ESNQ-V1 SCORED EXECUTION`
- scored chạy tuần tự dưới canonical heavy lock; ledger đủ 8 identity; reproduction twin;
  terminal A7; REJECT_ALL per-symbol là kết quả khoa học hợp lệ.

## 6. Terminal outcomes âm (quyết định TRƯỚC)

- ES cả 3 identity FAIL gates ⇒ ES DEAD_K2 (không rescue; không mở S1).
- NQ identity duy nhất FAIL ⇒ NQ DEAD_K2.
- Cả hai dead ⇒ cycle TERMINAL REJECT_ALL — kết quả hợp lệ, không tạo cycle nối tiếp trừ
  khi owner preregister.
- Dry-run FAIL/leak ⇒ TECHABORT, không scored.
- Cost re-pin làm MDE > cost ⇒ identity NOT_EVALUABLE (không bị tính là PASS).

## 7. Điều kiện effectiveness của plan

Đăng ký chỉ effective khi: (i) A7 prelaunch độc lập PASS 0 HIGH/CRITICAL tại committed
SHA; (ii) dry-run exact-arm non-vacuous PASS; (iii) cost re-pin hoàn tất; (iv) registry
reconcile --verify PASS. Owner GO typed riêng.

## ERRATUM 2026-10-10 (audit pre-GO — 14_AUDIT_GO_READY / 14_NQ_AMENDMENT_PACKET)

1. **NQ cost unit (F1)**: §2 bảng cost ghi NQ $23.50 — ĐÚNG THEO authority là **PER SIDE**
   (PLAN_futures_nq_v1 §Cost); RT = **$47.00 = 9.4t**. ES $42.00 RT không đổi
   (13_COMPUTE_SIGMA_BUDGET@74831a2c L95 "ticks RT"). Engine + MDE đã re-pin
   (COST_PIN.json; 07_FAMILY_ESTIMAND_USD v2).
2. **Hệ quả NQ-VSA-H15**: MDE post-X5 day-level $22.40 ≪ $47 ⇒ UNDERPOWERED ⇒ identity 4
   **chờ amendment owner** (14_NQ_AMENDMENT_PACKET: A bỏ block NQ [khuyến nghị, budget 8→6]
   / B giữ khai báo underpowered / C re-scope = từ chối). Cycle KHÔNG GO_READY cho tới khi
   amendment được owner chọn.
3. Cost tier: VERIFIED_VS_ACCOUNT = NOT_RUN (trung thực) — re-pin tiếp chỉ khi owner cấp
   quyền account evidence.

## ERRATUM-2 2026-10-10 (sửa ERRATUM-1 — công khai theo §39.5)

ERRATUM-1 kết luận "NQ-VSA-H15 UNDERPOWERED ở cost $47" là **SAI chiều đọc**: MDE $22.40
≤ cost $47 nghĩa là phép đo ĐỦ nhạy để phát hiện effect cỡ cost (n_needed ≈ 67 ngày ≪ 293
ngày) ⇒ **NQ-VSA-H15 POWERED ở RT $47**. Family ES+NQ SUM vẫn UNDERPOWERED (MDE $53–99 >
$43) — withdrawal giữ nguyên. Hệ quả: amendment "bỏ NQ" KHÔNG còn bắt buộc bởi power;
khuyến nghị mặc định = giữ NQ block (budget 8 nguyên). Owner vẫn quyết định cuối.

## ERRATUM-3 2026-10-10 (round-3 audit — 15_AUDIT_GO_ROUND3)

1. **Sửa sai số học (F4)**: mọi câu nói kiểu "NQ 30/60m MDE $31.8/$41.5 > $47" là SAI —
   $31.8 và $41.5 đều **< $47** ⇒ với RT $47, NQ powered-to-detect-cost-floor ở CẢ 3 hold
   (post-X5 day-level: $22.4/$31.8/$41.5, 293 ngày). Giữ nguyên identity NQ-VSA-H15.
2. **Ngữ nghĩa "powered" (F4)**: "MDE ≤ cost" CHỈ nghĩa phép đo đủ nhạy phát hiện một
   effect giả định bằng mức chi phí — KHÔNG phải bằng chứng net edge, KHÔNG tuyên bố có
   lợi nhuận, KHÔNG đổi identity/budget. Cost pin NQ $47 RT giữ (authority
   PLAN_futures_nq_v1 per-side ×2); VERIFIED_VS_ACCOUNT=NOT_RUN; fill/BBO chưa xác minh.
3. **14_NQ_AMENDMENT_PACKET (F4)**: tiền đề "UNDERPOWERED" của packet đã bị ERRATUM-2 hủy
   ⇒ các phương án A/B/C MOOT. Giữ làm hồ sơ lịch sử; owner không cần chọn A/B/C để GO;
   NQ block GIỮ (ERRATUM-2), owner quyền quyết cuối nếu muốn re-scope sau.
4. **F1**: registry head đã repair qua CAS tới SHA đo được (39589687, cat-file=commit,
   40-char) — previous head là SHA gõ tay không tồn tại; governance note: researchctl nên
   cat-file verify head trước ghi (gợi ý improvement, ngoài scope cycle).
5. **F2/F3**: scored production giờ bắt buộc --twin + twin.match True + accounting.complete
   True + publish/handoff thành công mới EXECUTION_COMPLETE; --fault-inject hooks cho
   fault tests (sandbox-only). Đã kiểm: fault suite 17/17 PASS.
