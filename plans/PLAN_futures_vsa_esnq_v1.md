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
