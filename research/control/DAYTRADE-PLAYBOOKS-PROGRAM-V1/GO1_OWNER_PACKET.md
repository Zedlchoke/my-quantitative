# GO1_OWNER_PACKET — DAYTRADE-PLAYBOOKS-PROGRAM-V1 (2026-09-27)

> Bàn giao đầu tiên theo owner instruction 2026-09-27. **Dừng tại GO-1**:
> chưa đăng ký cycle nào, chưa chạy scored cell nào, chưa mở OOS/sealed,
> chưa đụng worker/dashboard/shadow, chưa đặt lệnh. Mọi thứ dưới đây là
> DRAFT chờ owner quyết Q1–Q5.

## 1. Re-measure (Phase-0, đo 2026-09-27)

- Root `main` @ `96d65aae…`, dirty tree chỉ là file untracked của các session
  khác + 3 draft này (bảo toàn, không sweep — P-10). Heavy lock
  `FREE_PROVEN`, không worker nặng. Không row nào của chương trình này trong
  `plans/CYCLE_REGISTRY.json`.
- 10 cycle ACTIVE_LIGHT lân cận (kể cả 2 shadow + CHR3F đang scored) — danh
  sách no-touch đóng băng ở master §1.2.
- Doctor: mọi HIGH đều artifact-drift của cycle TERMINAL cũ (V17/V8/V12) —
  không blocker cho cycle mới.
- Disk 6.2 GiB free (pin kèm timestamp; floor 5.0 GiB theo luật DFV1).
- DATA-FOUNDATION TERMINAL 2026-09-26: F2 crypto READY, F3 FX BLOCKED-R1.

## 2. Sản phẩm bàn giao (paths)

| Sản phẩm | Path |
|---|---|
| Master plan (DRAFT) | `plans/PLAN_daytrade_playbooks_program_v1.md` |
| Child plan pair CX đầu (DRAFT) | `plans/PLAN_dtp_cx_solusdt_c1.md` |
| Child plan FX đầu (DRAFT, DORMANT) | `plans/PLAN_dtp_fx_audusd_c1.md` |
| Taxonomy playbook + bảng collision | `research/control/DAYTRADE-PLAYBOOKS-PROGRAM-V1/PLAYBOOK_TAXONOMY.md` |
| A7 plan review r1 (AUTHORIZED_WITH_FINDINGS; F1–F11 đã remediate) | `.../plan_review/A7_PLAN_REVIEW_r1.md` |

## 3. Thứ tự pair đề xuất (freeze tại Q3 — trước MỌI PnL của chương trình)

- **CX: SOLUSDT → BTCUSDT → ETHUSDT → BNBUSDT.** SOL đầu vì plane đã verify
  (klines 1h gapless floor-exact 2020-09-14; funding 6,580 settlements
  bit-exact; spread census ĐO p50 0.469 bps), ancestry mỏng nhất cho class
  price-level intraday (`OUTCOME_EXPOSED_baseline`), gate rẻ nhất. BTC/ETH kế
  (cần spread census tại gate; ETH va chạm cycle ACTIVE — luật no-touch đã
  đóng). BNB cuối (spread census cần ~25GB, disk 6.2GiB ⇒ BLOCKED tới khi
  disk đỡ).
- **Công khai quyết định khó nhất (Q1):** PWS-CX-SOLUSDT-C1 và
  PWS-CX-BNBUSDT-C1 (chương trình anh em trên observable funding-run) đều đã
  đóng `NO_ELIGIBLE_PROPOSAL` 0/18 và stop-rule PWS §9(a) đã bắn. Mở
  DTP-CX-SOLUSDT-C1 chỉ hợp pháp nếu owner quyết: **taxonomy playbook
  price-level/session + lớp annotation mù outcome là "observable/giả thuyết
  payer mới CÓ BẰNG CHỨNG"** (đúng cái note A7/A1 của PWS đòi). Từ chối ⇒
  pair CX đầu chuyển thành BTCUSDT, hoặc track CX DORMANT như FX.
- **FX: DORMANT toàn track** cho tới khi một reopener R1 (broker cost
  authority: two-sided sub + Flex statement) / R2 (nguồn bid/ask độc lập) /
  R3 (financing band) / R5 (information layer mới) có bytes. Thứ tự đóng
  băng sẵn: AUDUSD → USDCAD (dev-cho-observable-mới + sealed 2026-H1 còn
  nguyên); EURUSD/GBPUSD/USDJPY chỉ ancestry/fixture/cost authority;
  USDCHF BLOCKED_DATA_LICENSE.

## 4. Taxonomy → family đã chết (tóm tắt; bảng đầy đủ trong PLAYBOOK_TAXONOMY.md)

| Playbook | Phán quyết tiền-council |
|---|---|
| Opening-range breakout / session compression→expansion | DEAD (FXFV2-A4-P1/P2 đo trực tiếp; PSV1/SPRINT/V17-ATTN crypto) |
| Break-and-retest | DEAD (retest = gate cosmetic; TRACKA2 RECLAIM-ABSORB vetoed) |
| Trend pullback (EMA/VWAP) | DEAD (momentum/continuation mọi cadence — VIABILITY; BTC-H4-CONTINUATION forensic) |
| Mức tròn / level reaction | DEAD (ROUNDNUM census-family; SRLV absorption đo chết cả 2 chiều) |
| Pivot-point systems | DEAD (PDHLOC census-family; RANGEFADE "sống" cũ bị chứng minh là PIT-seam artifact) |
| Range/VWAP-deviation fade | DEAD (3 lần chết độc lập: FXOS-04 holdout, TRACKA1 PIT-clean, V16) |
| Biến động sau tin | DEAD + DATA-GATED (event class chết mọi dạng; lịch PIT thiếu) |
| Exhaustion/failed-breakout reversal | DEAD (đảo nhãn của breakout — anti-variant) |
| Settlement/funding-adjacent | DEAD (CNG2-A5, SRLV M1, PWS funding-run) |
| Liquidation-cascade/OI-flush | BLOCKED (liquidation tape 404) + DEAD (OICASCADE) |
| **Cross-asset lead-lag intraday (BTC→SOL)** | **OPEN-KILLRISK** — không có kill đo trực tiếp; 3 kill-risk phải đo trước PnL (rho đại diện; ceiling×power ~11–13 bps RT; payer veto) |
| *(METHOD)* Discretionary annotated playbooks | Route hợp lệ theo đúng owner law (annotation mù outcome TRƯỚC score; nguồn dated; mỗi rule chịu F-0) |

**Ý nghĩa trung thực:** toàn bộ playbook kinh điển đều đã có bằng chứng chết
trong repo; kỳ vọng modal của chương trình là slate trống/REJECT_ALL và
`NO_CANDIDATE` — kết quả hợp lệ theo đúng chỉ thị. Không gian "chưa đo" còn
lại hẹp: lead-lag intraday crypto (chưa từng bị đo giết trực tiếp) và route
annotation (đo bằng chứng thay vì đồn đại).

## 5. Slate đề xuất pair đầu DTP-CX-SOLUSDT-C1 (≤3; quyết cuối thuộc council sau F-0)

- **I001 — OUTCOME-BLIND ANNOTATED PLAYBOOK CORPUS.** Payer: từng rule tự
  khai (kỳ vọng đa số rule = skeleton chết — đo được là sản phẩm). Thông tin
  lúc đặt lệnh: chỉ bar đóng + bộ annotation dated. Edge biến mất khi: nguồn
  playbook hết cập nhật/crowding. Control: skeleton-test từng rule + placebo
  clock + inverted + baseline. Falsifier: rho > 0.20 vs dead class ⇒ F0_KILLED.
- **I002 — INTRADAY BTC→SOL LEAD-LAG DIFFUSION (two-sided).** Payer/hypo:
  maker stale-quote trên SOL book bị adversely select bởi thông tin BTC
  (series đo: aggTrades + bookTicker SOL — phải qua gate, thiếu ⇒ BLOCKED_DATA).
  Edge biến mất khi: HFT closes lag; ceiling×power grid (RT ~11–13 bps
  declared) âm ⇒ VETO pre-PnL (P-29 một buổi chiều). Control: randomized
  entry-time placebo, inverted, beta-matched baseline; rho vs EOS1-E2/xsect
  shadows phải ≤ 0.20.
- **Slot 3: OPEN-CALL** (pattern blind open-call ERP1-TA-C2) — không nhồi
  cho đủ số.

## 6. Ngân sách đề xuất (Q2)

- Scored cells: CX ≤18/pair-child, ≤72 program; FX 0 (mở ≤18/pair, ≤36
  program bằng amendment SAU khi reopener có bytes). Kỳ vọng thực chạy theo
  base rate: 0–6 cells/pair.
- Identity ceiling: 60 program (trần khảo sát; ≥ nửa sống chết ở registry
  bằng kill pre-PnL — tiết kiệm cells/OOS).
- Mọi trial vào trial_ledger + P-9; DSR công khai N_registry; PBO chỉ khi
  ≥8 configs; không grid; không rescue.

## 7. A7 plan-review

`AUTHORIZED_WITH_FINDINGS` (0 vi phạm; 2 HIGH + 3 MEDIUM + 6 LOW, tất cả đã
remediate trong draft — xem remediation record cuối file review). 18/18 số
liệu quyết định re-check MATCH. Không gì được đăng ký/chạy.

## 8. GO phrases (Q5 — gõ đúng chữ tại đúng gate, P-8)

```
GO-1: GO DTP CX SOLUSDT C1 COUNCIL AND FREEZE      (register + council + data gate + falsifiers + freeze — RỒI DỪNG)
GO-2: GO DTP CX SOLUSDT C1 SCORED EXECUTION        (chỉ sau A7 prelaunch)
GO-3: GO DTP CX SOLUSDT C1 OOS ONE LOOK AND REPLICATION
FX (chỉ khi reopener có bytes): GO DTP FX AUDUSD C1 COUNCIL AND FREEZE / …
```

## 9. Quyết định owner (gõ/sửa bên dưới hoặc trả lời bằng số)

- **Q1** — Phê chuẩn charter `DAYTRADE-PLAYBOOKS-PROGRAM-V1`, bao gồm quyết
  định định nghĩa: taxonomy price-level/session + annotation mù outcome có
  phải là observable mới có bằng chứng để mở SOL sau stop-rule PWS-CX đã bắn?
  (Không ⇒ CX đầu = BTCUSDT hoặc CX DORMANT.)
- **Q2** — Duyệt caps: cells/identity ceiling như §6?
- **Q3** — Duyệt thứ tự pair §3?
- **Q4** — FX: giữ DORMANT chờ reopener, hay chủ động mở R1/R2/R3 (owner
  action: IBKR two-sided + Flex statement / nguồn độc lập / financing band)?
- **Q5** — Duyệt GO phrase GO-1 ở §8 (owner sẽ gõ tại gate của nó sau khi
  council packet của child sẵn sàng)?

*Lead khuyến nghị: Q1=DUYỆT (định nghĩa observable mới đứng vững vì class
price-level/session chưa từng được đo trên crypto và annotation layer là
thông tin dated mới), Q2/Q3/Q5=DUYỆT như đề xuất, Q4=giữ DORMANT.*
