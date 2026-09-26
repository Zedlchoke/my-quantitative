# PLAN (DRAFT) — PWS-CX-SOLUSDT-C1 — Pair-child 1 track PWS-CX: tìm kiếm strategy identity trên SOLUSDT (Binance USDⓈ-M perp)

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** Child
> cycle của `PWS-PROGRAM-V1` (master `plans/PLAN_pws_program_v1.md`) dưới
> umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`. Kế thừa nguyên văn: umbrella
> §§1–11; forex-program §3/§4/§5/§8 (cấu trúc cohort, R0–R6, roster, chuỗi
> GO); SRLV master §§2–11 (F-0 court, PIT §3, cost §7, kill §10, stop §11)
> + child SRLV-CX-C1 §2 (luật crypto); PWS master toàn bộ. Chỉ chặt hơn.
> **Hiệu lực của caps theo amendment Option A đang chờ owner Q2** — nếu
> owner chọn Option B, chỉ đổi số program-cap ở master §4; budget của child
> này (≤18 cells, ≤3 identity) không đổi.
>
> Authored 2026-09-26, sau khi owner gõ intent GO-1 (xem OWNER_PACKET §0 —
> phrase được tiêu khi gõ LẠI tại gate đã dựng: Q1+Q2 ghi + A7 plan review
> child plan PASS). SOLUSDT là pair-child đầu tiên theo đề xuất master §3.2
> mà owner đã gọi tên trong intent.

## 0. Cycle identity

```text
cycle_id      PWS-CX-SOLUSDT-C1
parent        PWS-PROGRAM-V1 (master) / umbrella ECONOMIC-ROBUSTNESS-PROGRAM-V1
worktree      .worktrees/pws-cx-solusdt-c1/integration (branch
              orca/pws-cx-solusdt-c1-integration) — tạo qua researchctl
              CHỈ SAU GO-1 được tiêu tại gate
budget        ≤ 18 scored cells (≤3 identity × 4–6 arms × 1 home pair) +
              references; holdout/prospective looks ledgered riêng.
              Baseline set tính là MỘT arm slot per master §6.2 (cash 0% +
              long SOL + TREND_LF gói trong slot đó); baseline tham chiếu
              thêm (vd short-beta control khi cơ chế có chiều) là
              references, KHÔNG phải scored cells
universe      SOLUSDT (USDⓈ-M perp, Binance) — single-pair cohort theo
              luật pair-by-pair; KHÔNG score pair khác trong cycle này
S1            SEALED_UNTOUCHED; không tiêu surface S1 của cycle đang sống
GO phrases    GO-1 `GO PWS CX SOLUSDT C1 COUNCIL AND FREEZE` (đã được gõ
              2026-09-26T10:55Z — intent theo P-8, chờ gõ lại tại gate);
              GO-2 `GO PWS CX SOLUSDT C1 SCORED EXECUTION`;
              GO-3 `GO PWS CX SOLUSDT C1 SEALED OOS AND REPLICATION`
```

## 1. Mục tiêu pair-child

Falsify trước PnL trên SOLUSDT: council outcome-blind lấy từ
IDENTITY_REGISTRY các proposal cho pair này (đã qua F-0), freeze tối đa 3
identity, scored walk-forward dưới cost book đo/declared tách lớp, kết luận
per-identity theo R0–R6 (mức pair: R2 dev gates trên home pair; R4 one-look
nếu còn window sạch — xem §3 C5; R5 replication là việc của master, không
của child). Modal outcome kỳ vọng: REJECT_ALL / slate rỗng.

## 2. Ràng buộc đặc thù (binding)

### 2.1 Data plane (Phase C1)

- Klines 1h: Vision monthly um klines — corpus local, floor 2020-09-14;
  re-verify manifest + census tại C1 (sha-pinned). Plane 15m/1m nếu council
  đề cử: stage mới + data gate đầy đủ, và mặc định
  `ANCESTRY_EXPOSED_RECLK` (cùng lịch sử giá đã baseline-exposed ở 1h —
  không tạo surface outcome-free; Q-3) ⇒ chỉ dùng `ANCESTRY_EXPOSED_DEV`.
- Funding: fapi `/fapi/v1/fundingRate` pagination + Vision cross-check;
  floor 2020-09-13; conflict ⇒ symbol-month EXCLUDED (precedent frozen).
  Funding PIT: một settlement chỉ available TẠI `fundingTime`; rate interval
  kế = PREDICTED ≠ observable.
- Spread/slippage census theo giờ fill từ bookTicker/aggTrades granary —
  coverage verify tại C1; thiếu ⇒ BLOCKED (fail-closed, không điền số đẹp).
- CẤM: liquidationSnapshot (404), OI lịch sử (lookback ≈41.6h), order book
  L2 lịch sử, mọi maker-fill assumption; levered/borrow/liquidation-model
  ⇒ mọi arm unlevered 1x.

### 2.2 Exposure & collision (Phase C0+C2)

- SOLUSDT 1h 2020-09..2026-08: `OUTCOME_EXPOSED_baseline` (chỉ xsect
  baselines V11/V14/funding-carry) — identity mới được dev với ancestry
  disclosure; mọi dev row mang `ANCESTRY_EXPOSED_DEV` (dùng để KILL/
  engineering, không tự bằng chứng promote).
- OOS: window history chỉ one-look được nếu C2 chứng minh chính lịch sử giá
  window đó chưa từng bị search/score ở bất kỳ granularity nào. Baseline
  exposure chiếm toàn floor 2020-09+ ⇒ **kỳ vọng thực tế (và mặc định an
  toàn): OOS = prospective accumulation sau freeze** theo D13/D26/D52
  (D104 final per umbrella §5.12);
  kết luận tối đa trong history =
  `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`.
- Không đụng: `ETHUSDT-OPEN-SEARCH-V2` (ACTIVE, STOP-1 chờ GO, S1 sealed —
  không tiêu phrase/surface, không re-stage corpus);
  `CRYPTO-HISTORICAL-REPLICATION-3F-V1` (scored execution; heavy lock
  machine-wide — chỉ dispatch khi FREE_PROVEN hoặc held by self);
  `PROSPECTIVE-SHADOW-V1` + shadow workers (không restart, không sửa).

### 2.3 Concentration gate G8 (binding)

Tiền lệ đo: không long book nào trên BTC 2020–2026 qua fold-concentration
0.50. Không số đo tương tự cho SOL ⇒ treated same-by-law: mọi cơ chế
long-biased phải (a) chứng minh short-capability trong anchor definition,
HOẶC (b) freeze concentration-statistic thay thế có biện luận TRƯỚC outcome
(umbrella §5.14, sha-pinned cùng trial freeze), HOẶC (c) chỉ định nghĩa kết
  luận trên prospective. Thanh 0.50 không hạ (K-CONC).

### 2.4 Cost law (tách lớp bằng chứng)

Funding = MEASURED per-settlement path (native, while held; dual-book với
frozen constant; funding-path stress: 24.7% settlements âm trong downtrend
tiền lệ BTC/ETH — với SOL phải đo lại phân phối riêng tại C1, không kế
thừa hằng số venue khác); fee 5 bps + 1 adverse tick = DECLARED book (CHR3F
precedent; lên lớp measured chỉ khi validate vs fills — Q-8); spread =
measured census (§2.1) else BLOCKED; gap/outage/latency = DECLARED bands +
×1.5/×2.0. Declared không override measured. Ceiling: expected gross
premium/holding period ≥ full RT stress cost trên phân phối đo được — âm ⇒
VETO trước scoring (K-COST).

## 3. Phases & gates

### Phase C0 — Control plane & collision (sau GO-1)

`researchctl cycle list/doctor/locks inspect`; lock-drift ⇒ BLOCKED (P0-2);
doctor HIGH trên TERMINAL-archived cycles = accepted-historical (P0-3);
workers=0 cho child; đúng một Lead session sống.

### Phase C1 — Data plane (per-pair gate §2.1)

Stage + census + license posture capture từng nguồn; power analysis cho
ứng viên (floors: ≥100 closed RT sàn + ≥6 tháng; PF≈1.3 cần n≈236 — child
freeze n riêng sau power analysis, chỉ được nâng).

### Phase C2 — Exposure verification

Bảng pair × plane × window đối chiếu registry + HYPOTHESIS_LEDGER ⇒ phân
loại exposure; artifact `EXPOSURE_VERIFICATION_C1.md` sha-pinned; chọn dev
folds từ dev được phép (SOL floor 2020-09: đề xuất F1 2020-09→2021-12,
F2 2022-01→2023-06, F3 2023-07→2024-12, F4 2025-01→2026-08 — pin trước
outcome, điều chỉnh theo power analysis).

### Phase C3 — Council outcome-blind + falsifiers + trial freeze (GO-1, rồi DỪNG)

- Council lấy proposal SOLUSDT từ IDENTITY_REGISTRY (status FREEZE_
  ELIGIBLE) + gọi proposer lanes blind nếu thiếu; mỗi proposal đủ 10 trường
  umbrella §5.3 + F-0 ba test; skeptic VETO pre-PnL; anti-variant law master
  §2.3 (khác ≥2/3 payer/information/risk).
- Freeze ≤3 identity; mỗi identity 1 anchor + ≤2 neighbour + 1 causal
  control + 1 inverted control + 1 baseline set (cash 0% + long SOL cùng
  cost book + trend-following reference TREND_LF; short-beta control khi
  cơ chế có chiều). PIT/intrabar pin nguyên văn master §6.2 (SRLV §3):
  truncation byte-identical, future-mutation, fill open t+1, cấm thứ tự
  high/low trong bar (không tách được ⇒ `NOT_CONSTRUCTIBLE_INTRABAR`),
  cấm same-day statistic (P-18), delay-pair Q-4 cho sub-hour, dry-run
  non-vacuous + leak-scan.
- Falsifier battery F-0…F-7 (F-2 crypto: funding-settlement timing, kline
  clock alignment, M-class truncation cho mọi biến regime/vol-state);
  incrementality test cho vol-state; **ancestry rho ≤0.20 trên frozen
  representation với shadow-array membership pin riêng cho crypto**: shadow
  set phải là crypto failure-memory shadows (OUTCOME_EXPOSURE_MAP §4 +
  umbrella §5.4 Track C: EOS1-E1/E2, PSV1-BTC_H4 Donchian, BTC-BEAR double
  veto, V13 LIQEPIS/V17 OICASCADE, crypto-ng 11/11) HOẶC extension được
  biện luận của kỹ thuật
  47-shadow cohort-2 (tái sử dụng KỸ THUẬT; bộ 47 shadow FX KHÔNG dùng
  nguyên văn cho cơ chế crypto); membership + digests sha-pinned cùng
  trial freeze.
- Freeze artifact sha256 → A7 prelaunch audit → **DỪNG chờ GO-2**.

### Phase C4 — Scored walk-forward (GO-2, heavy lock)

Gates G1–G8 + margin-to-fail; funding-path accounting per settlement
(received/paid tách bạch Q-14); dual cost book song song; báo per-fold, per
direction, leave-one-fold-out; net @×1.0/×1.5/×2.0; controls theo freeze.
Trial ledger mọi outcome view (P-9); DSR terminal với N_registry disclosure
(master §6.3).

### Phase C5 — OOS one-look (GO-3, MỘT LẦN)

Mặc định: prospective accumulation sau freeze (D13/D26/D52; D104 final
per umbrella §5.12). Chỉ dùng history one-look nếu C2 chứng minh window
sạch ở cấp lịch sử giá (không phải đổi plane); membership sha-frozen; arm
chết không nhìn holdout. **Guardrail: việc tiêu GO-3 KHÔNG tự cấp quyền
replication và không tạo claim "replicated"** — nếu một identity sống sót
và R5 replication đến hạn, bề mặt transfer (thuộc pair-child khác) là
quyết định master/owner riêng với GO riêng (master §8).

### Phase C6 — A7 terminal + two-half close

Reproducer/A7 viết lại từ spec + raw planes (klines + settlement bytes),
không import engine implementer; recompute record-level; FAMILY_FAILURES/
MAP/LESSONS + IDENTITY_REGISTRY status flips; registry flip qua researchctl.

## 4. Freeze fields bổ sung crypto

Định nghĩa mức/vùng + `t_known` + N-bar pivot confirm; funding treatment
trong PnL; clock twin = block-shuffle/GMT-hour dummies (24/7, không
session); weekend/quiet-hour buckets disclosed; spread-conditioning của
fill theo giờ; sweep thuần hình học từ kline close/wick với nhãn
`PROXY_NOT_ORDERBOOK`; payer story phải encode bằng observable PIT hợp pháp
(fictional-counterparty veto).

## 5. Ngân sách / dừng

≤18 scored cells; ≤3 identity; holdout/prospective looks ledgered riêng;
program cap theo amendment (master §4); time-stop 14 ngày/gate; stop
conditions master §9. Terminal vocabulary: umbrella §9 + nhãn
`SINGLE_VENUE_PANEL`, `PROXY_NOT_ORDERBOOK`, `FUNDING_PATH_STRESSED`,
`ANCESTRY_EXPOSED_DEV`, `FILL_QUALITY_CLASS_<measured|declared>`,
`PAPER_TIER`. Mọi verdict âm là first-class close.
