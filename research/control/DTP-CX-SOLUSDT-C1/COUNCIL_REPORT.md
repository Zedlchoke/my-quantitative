# COUNCIL_REPORT — DTP-CX-SOLUSDT-C1 (GO-1: council + data gate + falsifiers + freeze R1)

- A1 integration, 2026-09-27. GO-1 phrase tiêu verbatim (xem
  `research/control/DAYTRADE-PLAYBOOKS-PROGRAM-V1/GO_RECORD.md` tại root,
  commit main). **0 scored cell, 0 PnL, S1 SEALED, không worker/shadow bị
  đụng.** Dừng đúng phạm vi GO-1.

## Tổng hợp các lane (mọi handoff `zcode_orch_v3_handoff@1` tại `handoffs/`)

| Lane | Verdict | Điểm quyết định |
|---|---|---|
| DG (PIT/data auditor) | `PASS_WITH_DISCLOSURES` | inherit-verify 84/84 sha MATCH (12GB stream-hash 21s); staged 269.3MB (SOL 1m+15m+mark+index full-span 2020-09..2026-08, 288/288 CHECKSUM MATCH); PIT seam: mọi timestamp millisecond — không µs-migration; gap = đúng 2 cửa sổ bảo trì venue đã biết (7,200 phút 1m) + outages mark/index披露; 0 duplicate; cross-granularity 2024-06 CONSISTENT (2880/2880 + 720/720); quote coverage = MEASURED 6 tháng lấy mẫu (2023-05/07/09/11, 2024-01/03), còn lại DECLARED_BAND; aggTrades NOT_RUN_STAGE_BUDGET (probe: 130–529MB/tháng, full ~20GB) |
| COST (cost/execution auditor) | cost book `@draft` hoàn chỉnh | tái lập census tháng 2023-05 từ bytes: MATCH (max-spread bit-exact; p50 giờ bit-exact 16/24, còn lại ≤3.7e-5 bps); RT ladder taker 1m unlevered: **in-window measured 11.92 bps → ×1.5 = 17.88 → ×2.0 = 23.84**; out-window declared 12/18/24; ceiling×power grid template mechanical VETO; 9 blockers named (commission class, queue position, slippage-beyond-touch, 56/72 tháng spread UNKNOWN_WIDER…) |
| P1 (blind proposer) | 2 proposals + open-call | I001 protocol annotation đầy đủ (6 tiêu chí nguồn dated, truncation tại publication timestamp, 6 điều cấm); I002 đủ 10 trường §5.3 + nhánh BLOCKED_DATA khai báo sẵn; open-call slot 3 mở, deadline = trước tòa skeptic |
| SKP (skeptic, VETO) | tòa F-0 phán xong | xem dưới |

## Phán quyết tòa skeptic (chi tiết: `council/skeptic/SKEPTIC_COURT_REPORT.md` + `court_machine@1.json`)

- **I002 (BTC→SOL lead-lag diffusion) → `F0_KILLED` (K-F0 + K-COST + K-ANC, 3 luật độc lập, pre-PnL):**
  1. *Information test:* điều kiện trên sự kiện BTC (census full-span
     3,155,040 phút 1m; θ=10→315,579 sự kiện, θ=25→47,083, θ=50→6,909),
     SOL reprice NGAY TRONG phút tín hiệu (median 17.8→62.8 bps); cửa sổ
     capturable phút kế tiếp median −0.245..0.000 bps, mean thực thi được
     0.53–2.03 bps — thấp hơn fee-only 10 bps một bậc độ lớn. "SOL chưa
     adjust" là **measured-fictional** ở granularity bar.
  2. *Ceiling×power grid:* jointly EMPTY ở mọi θ × mọi multiplier × cả hai RT
     ladder × cả hai power base — net −9.97..−11.47 bps/RT @1.0×. Chết KHI CÓ
     ĐỦ power (≥100 RT mọi θ) — không lối thoát INCONCLUSIVE.
  3. *K-ANC:* rho đại diện trên decision grid one-shot committed: vs PWS-I001
     momentum sign-run rep **0.2341–0.5085 > 0.20 tại MỌI θ**; vs EOS1-E1
     SMA200 rep 0.1650→0.4108 vượt bar từ θ≥15.
  - Nhánh BLOCKED_DATA được xét trung thực: klines-only cho claim lag = proxy
    substitution cấm; bản giới hạn trong 6 tháng bookTicker chết y hệt
    in-window ⇒ **mở rộng ngân sách aggTrades KHÔNG hồi sinh I002**. Revival
    = đề xuất R5-class mới có series PIT quote/trade đo được staleness
    event-time dương trên ceiling.
- **I001 (outcome-blind annotated playbook corpus) → `ELIGIBLE_FOR_FREEZE`
  AS GENERATOR**, điều kiện ràng buộc C1–C6: corpus build chỉ sau protocol
  freeze + sau GO; MỖI rule codify qua F-0 + anti-variant merge riêng; chọn
  ≤3 theo two-of-three distinctness; PIT auditor verify truncation fixtures;
  recap/author-claim không bao giờ là premium evidence; per-RULE K-COST
  ceiling honesty. Skeleton/payer DEFERRED per-rule (đúng thiết kế).
- **Slot 3 open-call → SLATE_EMPTY** (0 submission trước khi tòa họp — hợp lệ).

## Freeze R1 (xem `FREEZE_R1.json`)

1. **I001-generator protocol FROZEN** (điều kiện C1–C6 nguyên văn);
   identity scored chưa có — Sinh ra từ corpus build (giai đoạn còn lại của
   phạm vi freeze GO-1, trước GO-2, 0 PnL).
2. **I002 F0_KILLED terminal** — ghi IDENTITY_REGISTRY program-level; không
   bao giờ re-open trong chương trình này trừ R5-class owner plan.
3. **Slot 3 trống.** Budget scored cells: **0/18 tiêu**. Trial ledger 0 rows.

## Còn lại trước GO-2 (không quyền mới — vẫn trong phạm vi freeze của GO-1)

- Corpus build theo protocol I001 (annotation mù outcome, nguồn dated) →
  codify rules → per-rule F-0 (skeptic) + anti-variant merge → **FREEZE R2:
  chốt ≤3 identity scored** (nếu 0 rule sống sót ⇒ freeze rỗng, child đóng
  slate-empty) → A7 prelaunch → **DỪNG chờ owner GO-2**
  (`GO DTP CX SOLUSDT C1 SCORED EXECUTION`).
