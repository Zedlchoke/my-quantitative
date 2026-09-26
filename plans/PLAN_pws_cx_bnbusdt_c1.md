# PLAN (DRAFT) — PWS-CX-BNBUSDT-C1 — Pair-child 2 track PWS-CX: tìm kiếm strategy identity trên BNBUSDT (Binance USDⓈ-M perp)

> **Status: `DRAFT_FOR_GO1_GATE — NOT REGISTERED, NOT EXECUTED.** Child cycle
> của `PWS-PROGRAM-V1` (master `plans/PLAN_pws_program_v1.md`) dưới umbrella
> `ECONOMIC-ROBUSTNESS-PROGRAM-V1`. Kế thừa nguyên văn: umbrella §§1–11;
> forex-program §3/§4/§5/§8; SRLV master §§2–11 + child SRLV-CX-C1 §2 (luật
> crypto); PWS master toàn bộ; child tiền lệ `PLAN_pws_cx_solusdt_c1.md`
> (C0–C6, freeze fields, cost law). Chỉ chặt hơn. Caps theo amendment Option A
> (hiệu lực, Q2 đã duyệt).
>
> Authored 2026-09-26 tối (discovery sprint có chặn
> `SPRINT_2026-09-26_evening.md`). BNBUSDT là pair-child #2 theo thứ tự Q3 đã
> duyệt (SOLUSDT → **BNBUSDT** → BTCUSDT → ETHUSDT); mở sau khi SOLUSDT được
> A7 terminal + two-half close (master §3.2). GO-1 được tiêu dưới standing
> delegation `OWNER_DELEGATED_DECISION_charter_and_go1_2026-09-26.json`
> (chuỗi GO của PWS-PROGRAM-V1; điều kiện cấu trúc tại gate).

## 0. Cycle identity

```text
cycle_id      PWS-CX-BNBUSDT-C1
parent        PWS-PROGRAM-V1 (master) / umbrella ECONOMIC-ROBUSTNESS-PROGRAM-V1
worktree      .worktrees/pws-cx-bnbusdt-c1/integration (branch
              orca/pws-cx-bnbusdt-c1-integration) — tạo qua researchctl/git
              CHỈ SAU GO-1 được tiêu tại gate
budget        ≤ 18 scored cells (≤3 identity × 4–6 arms × 1 home pair) +
              references; baseline set = MỘT arm slot (cash 0% + long BNB +
              TREND_LF); short-beta control = reference khi cơ chế có chiều
universe      BNBUSDT (USDⓈ-M perp, Binance) — single-pair; KHÔNG score pair
              khác trong cycle này
S1            SEALED_UNTOUCHED; không tiêu surface S1 của cycle đang sống
GO phrases    GO-1 `GO PWS CX BNBUSDT C1 COUNCIL AND FREEZE`;
              GO-2 `GO PWS CX BNBUSDT C1 SCORED EXECUTION`;
              GO-3 `GO PWS CX BNBUSDT C1 SEALED OOS AND REPLICATION`
```

## 1. Mục tiêu pair-child

Falsify trước PnL trên BNBUSDT với **information-novelty test tường minh**
(owner instruction sprint 2026-09-26 tối + khuyến nghị A1 của SOLUSDT verdict:
pair #2 chỉ nên mở kèm proposer angle có bằng chứng thông tin mới): mỗi
proposal phải chứng minh (i) information layer/payer/risk-shape khác ≥2/3 trục
so với TOÀN BỘ fence đã đo (SOLUSDT C3 fences là pair-agnostic trong lớp
observable giống hệt), HOẶC (ii) bằng chứng thông tin mới có authority
(R5-class) hoặc cost-regime break có ngày tháng. Cùng observables cũ (klines 1h
+ funding + spread) sinh lại dead family ⇒ F-0 kill / slate rỗng ⇒ đóng
`NO_ELIGIBLE_PROPOSAL` với ghi rõ no-new-information (master §9(a) ngôn ngữ),
KHÔNG chạy backtest cho chạy. Modal outcome kỳ vọng: slate rỗng.

## 2. Ràng buộc đặc thù (binding)

### 2.1 Data plane (Phase C1)

- Klines 1h: Vision monthly um klines, floor 2020-02-10 (DATACOST matrix);
  stage mới (chưa có corpus local); manifest + census sha-pinned tại C1. Plane
  15m/1m nếu council đề cử: stage riêng + mặc định
  `ANCESTRY_EXPOSED_RECLK` ⇒ chỉ `ANCESTRY_EXPOSED_DEV` (Q-3).
- Funding: fapi `/fapi/v1/fundingRate` pagination + Vision cross-check khi
  corpus sẵn; conflict ⇒ symbol-month EXCLUDED (precedent frozen). Funding PIT:
  một settlement chỉ available TẠI `fundingTime`.
- Spread census theo giờ fill từ bookTicker/aggTrades: **ràng buộc disk sprint**
  — yêu cầu ≥25GB trống trước khi stage (SOLUSDT tiền lệ ~12GB/6-tháng phân
  tầng); thiếu ⇒ `NOT_RUN_DISK_CONSTRAINT` ghi trung thực, cost gate
  **fail-closed** (K-COST/BLOCKED cho scoring; không điền số đẹp, không dùng
  census của pair khác thay thế).
- CẤM như SOL: liquidationSnapshot, OI lịch sử, order book L2 lịch sử, maker-
  fill assumption; mọi arm unlevered 1x.

### 2.2 Exposure & collision (Phase C0+C2)

- BNBUSDT 1h 2020-02..2026-08: `ELIGIBLE_DEV_BASELINE_EXPOSED` (DATACOST) —
  C2 phải đối chiếu registry + HYPOTHESIS_LEDGER + OUTCOME_EXPOSURE_MAP để
  xác nhận lại bằng bytes; mọi dev row mang `ANCESTRY_EXPOSED_DEV`.
- OOS: baseline exposure chiếm floor ⇒ mặc định OOS = prospective accumulation
  sau freeze; kết luận tối đa trong history =
  `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`.
- Không đụng: `ETHUSDT-OPEN-SEARCH-V2` (ACTIVE, S1 sealed); `CRYPTO-
  HISTORICAL-REPLICATION-3F-V1` (scored; heavy lock — chỉ dispatch khi
  FREE_PROVEN hoặc held by self); `PROSPECTIVE-SHADOW-V1` + shadow workers;
  worktree terminal của SOLUSDT (append-only evidence).

### 2.3 Concentration gate G8 (binding)

Tiền lệ BTC: không long book nào 2020–2026 qua fold-concentration 0.50; SOL
treated same-by-law. BNB: treated same-by-law — mọi cơ chế long-biased phải
(a) chứng minh short-capability trong anchor definition, (b) freeze
concentration-statistic thay thế có biện luận TRƯỚC outcome, hoặc (c) chỉ
định nghĩa kết luận trên prospective. Thanh 0.50 không hạ (K-CONC).

### 2.4 Cost law (tách lớp bằng chứng)

Funding = MEASURED per-settlement path (đo riêng BNB tại C1 — không kế thừa
hằng số SOL/BTC/ETH); fee 5 bps + 1 adverse tick = DECLARED book (CHR3F
precedent); spread = measured census (§2.1) else BLOCKED; gap/outage/latency =
DECLARED bands + ×1.5/×2.0. Ceiling âm hoặc thiếu thành phần trọng yếu ⇒ VETO
trước scoring (K-COST).

## 3. Phases & gates (như SOLUSDT child §3, thay đổi ghi rõ)

- **C0** control plane & collision: `researchctl cycle list/doctor/locks
  inspect`; lock-drift ⇒ BLOCKED; workers=0 cho child; đúng một Lead session.
- **C1** data plane: stage klines + funding; census + license posture; power
  analysis cho ứng viên (floors: ≥100 closed RT + ≥6 tháng).
- **C2** exposure verification: bảng pair×plane×window; dev folds đề xuất F1
  2020-02→2021-12, F2 2022-01→2023-06, F3 2023-07→2024-12, F4 2025-01→2026-08
  (pin trước outcome, chỉnh theo power).
- **C3** council outcome-blind + falsifiers + trial freeze (GO-1 rồi DỪNG):
  P1/P2 blind proposals với information-novelty test §1; skeptic VETO pre-PnL;
  anti-variant law; freeze ≤3 identity; PIT/intrabar pin nguyên văn master
  §6.2; shadow-array membership crypto pin riêng. Freeze artifact sha256 → A7
  prelaunch → DỪNG chờ GO-2. **Slate rỗng ⇒ đóng tại đây.**
- **C4** scored walk-forward (GO-2, heavy lock) — tối 2026-09-26: KHÔNG khả
  thi nếu spread census `NOT_RUN_DISK_CONSTRAINT` (cost fail-closed); chỉ chạy
  khi đủ điều kiện sprint (slate + A7 prelaunch PASS + ≥45' trước 23:59+07).
- **C5** OOS one-look (GO-3) — ngoài sprint.
- **C6** A7 terminal + two-half close.

## 4. Freeze fields bổ sung crypto

Như SOLUSDT child §4 nguyên văn (định nghĩa mức/vùng + `t_known` + N-bar pivot
confirm; funding treatment; clock twin block-shuffle/GMT-hour dummies;
sweep `PROXY_NOT_ORDERBOOK`; payer story encode bằng observable PIT hợp pháp).

## 5. Ngân sách / dừng

≤18 scored cells; ≤3 identity; program cap ≤96 (CX≤48) binding; **time-stop
sprint 23:30+07 2026-09-26** (chặt hơn luật 14 ngày — được phép, chỉ chặt hơn);
stop conditions master §9. Terminal vocabulary: umbrella §9 + master §11 +
`SINGLE_VENUE_PANEL`, `PROXY_NOT_ORDERBOOK`, `FUNDING_PATH_STRESSED`,
`ANCESTRY_EXPOSED_DEV`, `FILL_QUALITY_CLASS_<measured|declared>`,
`PAPER_TIER`. Mọi verdict âm là first-class close.
