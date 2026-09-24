# LANE REPORT — lane_crypto_sleeves (SHADOW-PAPER-REVIEW-V1)

- Role: review-analyst, READ-ONLY. Cycle: SHADOW-PAPER-REVIEW-V1. Task: sprv1-crypto.
- Measured start (root checkout, branch main): HEAD `f0a8e800c47de1800011d20bccd9bcb2cc7e8546`.
- Ngày đo: 2026-09-24 (toàn bộ số trong report này đo từ byte artifact, có cite path).
- Phạm vi: 4 sleeve crypto của PROSPECTIVE-SHADOW-V1: XSECT-FUND-CARRY-7D,
  ILLIQ-AMIHUD-28D-W, BASISLV-PREMFADE-28D, BTC4H-BANDRIDGE.
- Không chạy heavy job, không đụng worker/registry/ledger, không commit.

---

## 0. measured head của worktree integration (bắt buộc bước A)

- Root plan `plans/PLAN_prospective_shadow_v1.md` = 30,644 byte (mtime 2026-09-24 07:35),
  có **AMENDMENT A1 (2026-09-24)** gắn sleeve 4 BTC4H-BANDRIDGE với vốn riêng $100k.
- Worktree copy `.worktrees/prospective-shadow-v1/integration/plans/PLAN_prospective_shadow_v1.md`
  = 28,668 byte (mtime 2026-09-14 18:01, commit `0d8b3008`) — **CHƯA có Amendment A1**,
  `git log -1 --format=%h` trên file đó đo được `0d8b3008`. Root là bản quyền (registry
  trỏ root plan); worktree plan STALE — đã ghi rõ, không tự sửa.
- Worktree integration HEAD đo được lúc review: **`236bf2f7bbbf87285e7e1e6c6767782ab48f69fb`**
  (branch `orca/prospective-shadow-v1-integration`, tree sạch). GATES.md của
  DASHBOARD-AND-SHADOW-RELIABILITY-V1 (`research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/GATES.md`,
  mục G0) ghi registry head `99e0026` STALE vs `a8062b1a` khi đó; tính đến lúc tôi đo,
  worktree đã tiến thêm tới `236bf2f7` (6 commit 302d5f52..236bf2f7, đúng như danh sách
  trong GATES.md "Task commits"). Registry head vẫn có khả năng STALE hơn số này —
  không đọc lại registry trong lane này (chỉ state đo được ở GATES.md + git).
- Diff root-plan vs worktree-plan = đúng 1 khối: AMENDMENT A1 (đo bằng `diff`).

## 1. Ledger nằm ở đâu (cảnh báo đường dẫn)

- `results/prospective_shadow_v1/` **KHÔNG tồn tại ở root checkout** (đo: root `results/`
  chỉ có account.csv/order_fills.csv/positions.csv/summary.json cũ 09-07).
- Toàn bộ ledger + valuation_marks + runtime nằm ở
  `.worktrees/prospective-shadow-v1/integration/results/prospective_shadow_v1/`.
- Byte-count đo lúc review (khớp heartbeat
  `.../results/prospective_shadow_v1/runtime/heartbeat.json`):
  BASISLV 1,292 | BANDRIDGE 70,298 | ILLIQ 3,922 | CARRY 27,727 byte.
- Worktree band-risk (computation home của sleeve 4 theo SPEC) có ledger riêng
  `.worktrees/btc-h4-band-risk-v1/integration/research/control/btc_h4_band_risk_v1/shadow_bandridge/ledger.jsonl`
  = **0 byte** (đo) — worker production chạy qua e-worker integration; ledger thật là
  `ledgers/BTC4H-BANDRIDGE.jsonl` (MOUNT NOTE trong SPEC.md ghi đúng cấu trúc này).

## 2. Identity & cost freeze (bước B) — tóm tắt đo được

Nguồn: `.worktrees/prospective-shadow-v1/integration/research/control/prospective_shadow_v1/identity/identity_recovery.json`
(38,098 byte; đã được A7 re-hash độc lập — `A7-RELIABILITY-AUDIT-2026-09-24.md` mục 2d, VERDICT CONFIRM).

| Sleeve | Tổ tiên | Verdict kế thừa (KHÔNG được ghi đè) | Nguồn byte |
|---|---|---|---|
| ILLIQ-AMIHUD-28D-W | A8-V11-ILLIQ-AMIHUD | `V11_FAMILY_REJECT` — fail duy nhất: largest positive-fold share 0.7055 > 0.50 | identity_recovery.json families[0]; commit `c97283e0…` / `df18f53d…` |
| BASISLV-PREMFADE-28D | A14-V14-A5-BASISLV-PREMFADE | `V14_FAMILY_REJECT` — fold share 0.51102 > 0.50; DSR 0.0022396 @146 trials; mệnh đề price-only failure đang binding (edge tổng dương chủ yếu do funding credit) | families[1]; commit `183554ad…` |
| XSECT-FUND-CARRY-7D | H-XSECT-FUNDING-CARRY-v1 | `CANDIDATE_FAIL` — top positive fold F1 51.66% > 50%; robustness XG4 INCONCLUSIVE; DSR unavailable | families[2]; WORKING_TREE_TRACKED (candidate.yaml + V6 closure addendum) |
| BTC4H-BANDRIDGE | PSV1 Donchian × ES1-C3-BAND | `POSTHOC_DISCOVERY_CANDIDATE (PSV1 arm G6-control-killed; ES1 C3 G5-killed; prospective observation only — never OOS, never live)` — label COMPOSITE, đã disclose `label_kind=composite` + byte-pin từng đoạn; **A7 prelaunch bị owner WAIVE** ("khỏi A7 lúc này", 2026-09-23) | families[3]; SPEC.md sha `3a7591fb…`; shadow_group_s0.json sha `c8f7efdd…` |

Cost book (frozen, `.../data_cost/cost_regime_manifest.json`):
CURRENT_CONSERVATIVE_COST = taker 0.05%/side (fallback DECLARED — trang fee public
UNAVAILABLE_FAIL_CLOSED, ghi rõ `evidence_class: UNAVAILABLE_FAIL_CLOSED_FALLBACK_DECLARED`),
maker 0.02%, slippage 1 tick bất lợi mỗi fill, funding settlement 8h book-1-lần, fill tại
bar 15m hoàn tất đầu tiên sau quyết định. `cost_regime_digest` khối = `ab524d0e…`;
ledger event của CARRY/BASISLV/BANDRIDGE mang `130d2e7e…`, ILLIQ mang `71ea4bd6…`
(book tick-size riêng cho universe 20 symbol — đo từ ledger records).

## 3. Bảng trạng thái 4 sleeve + số đo từ byte (bước C)

Kỳ quan sát: SHADOW_START `2026-09-14T23:48:01Z` (`.../activation/activation.json`) →
mark valuation cuối `2026-09-24T12:10:00Z` (valuation_marks/*). ~9.5 ngày.

| Chỉ số (nguồn: ledgers/*.jsonl + valuation_marks/*.jsonl, đo 2026-09-24) | CARRY-7D | ILLIQ-28D-W | PREMFADE-28D | BANDRIDGE |
|---|---|---|---|---|
| Decision events | 10 (09-15→09-24, daily) | 1 (09-21) | 1 (09-21) | 57 (09-15→09-24T08:00Z, H4) |
| OK / DATA_BLOCKED / UNAVAILABLE_FAIL_CLOSED | 10/0/0 | 1/0/0 | 0/1/0 | 1/0/56 |
| Fills | 48 | 8 | 0 | 0 |
| Σfee / Σslip / Σfunding (USDT) | 246.43 / 56.40 / **+4.60** | 50.00 / 13.21 / 0 | 0/0/0 | 0/0/0 |
| Booked net (Σtotal_pnl) | −298.22 | −63.21 | 0 | 0 |
| Equity theo mark: min / max / cuối | 95,443.05 / 100,507.00 / 99,662.87 | 97,125.21 / 101,620.29 / 100,083.70 | 100,000 / 100,000 / 100,000 | 100,000 / 100,000 / 100,000 |
| PnL vs seed 100k (mark cuối) | **−337.13 (−0.34%)** | **+83.70 (+0.08%)** | 0 | 0 |
| MDD theo mark (tự tính) | 4.825% | 3.732% | 0 | 0 |
| Mark DATA_BLOCKED (fail-closed) | 50/2,071 | 27/2,071 | 0 | 0/113 |
| Holding period | round-trip đóng: 16 cái, 24–48h (mean 34.5h); 5 chân còn mở | book mở 09-21, chưa đóng | — | — |
| Phí mỗi fill | ~5.13 USDT (TB) | 6.25 USDT (đúng 12.5%×0.05%) | — | — |
| Win-rate round-trip | **NOT_RUN** — ledger không có realized_pnl per fill | NOT_RUN (chưa có RT đóng) | — | — |
| Gross vs net tách được | CÓ (booked): net = −(fee+slip)+funding; MTM nằm trong equity (+726.37 unrealized tại 00:00Z 09-24) | CÓ (cùng luật) | — | — |

Đọc kỹ hơn từng sleeve:

### 3.1 XSECT-FUND-CARRY-7D — đang chạy đúng luật, đang bị chi phí ăn
- 10/10 sự kiện OK/OK; gross ~0.8004 mỗi ngày (target 0.80), net 0.0; 48 fill.
- Book: XRP long 9/10 ngày, DOGE short 9/10 ngày; 4 lật chiều / 40 (symbol,ngày)
  → book bền, turnover TB ~0.62x/ngày (Σ notional giao 492,853 USDT / 10 ngày / book 80k).
- Chi phí chạy 10 ngày: 302.83 USDT ≈ 30.3bps equity ≈ **~11%/năm run-rate**;
  funding thu được chỉ **+4.60 USDT (~1.7%/năm)** và đã có ngày âm (−1.73, −1.68).
  PnL equity thực tế (+428 tại mark 00:00Z, −337 tại mark 12:10Z) là **giá (MTM)**, không phải carry.
- Funding regime 2026-09: gần phẳng (từng ngày +4.71, +1.62, +1.62, −1.73, −1.68, +0.98, +0.94, −0.35 — ledger records).

### 3.2 ILLIQ-AMIHUD-28D-W — 1 quyết định, đúng luật, thiếu 1 sự kiện tuần
- Quyết định duy nhất 09-21T00:00Z: long 4 illiquid (APT, ATOM, ETC, OP) / short 4 liquid
  (BTC, ETH, SOL, XRP), ±0.125, gross 1.0006 (hơi >1.0 do quy ước sizing trên
  start-of-rebalance equity — documented `carried_conditions.gross_basis` trong activation.json), net 0.
- Chi phí mở book 63.21 USDT; mark 12:10Z: +83.70 net (chưa có lần rebalance nào để kết luận gì).
- **Phát hiện độ phủ**: activation.json khai `first_scheduled_events` = 09-15T00:00Z cho cả
  ILLIQ và BASISLV (weekly Monday), nhưng scheduler
  (`research/shadow_v1/scheduler.py::_first_decision_at_or_after`) neo từ mốc 00:00 của
  NGÀY start (09-14 là Monday, 00:00 < 23:48 start) nên nhảy thẳng tới 09-21 — heartbeat
  `loop_results: ILLIQ due:1` xác nhận. Hệ quả: **một quan sát tuần (09-15) bị mất mà
  không có record DATA_BLOCKED nào** — lệch với nghĩa vụ "mọi quyết định định lịch đều
  phát 1 record" (plan §8) và với chính activation.json. Daily CARRY thì nhận được 09-15
  (mốc daily là +1 ngày). Đây là lệch kế hoạch↔mã, không phải lỗi signal.
- 27/2,071 mark DATA_BLOCKED (1.3%) — fail-closed đúng luật.

### 3.3 BASISLV-PREMFADE-28D — đúng luật fail-closed, đang đốt quan sát tuần
- Quyết định 09-21 bị `DATA_BLOCKED`: thiếu 286 bar 15m hoàn tất trong
  (2026-08-22T23:00Z, 2026-09-20T23:30Z], gap đầu 2026-09-18T00:15Z (ledger record +
  GATES.md G2). Event_id tuần bị tiêu hao (không backfill — đúng luật forward-only).
- Nguồn đã hồi phục: GATES.md G2 đo 13/13 candidate × 30 ngày = 2,879 bar, 0 gap;
  quyết định kế 09-28 sẽ có window đủ.
- Sleeve phẳng 100,000; chưa có gì đo được về edge (0 fill).

### 3.4 BTC4H-BANDRIDGE — sleeve chưa thể quan sát gì; 3 câu hỏi luật mở
- 57 records: 56 `UNAVAILABLE_FAIL_CLOSED` = MOUNT_BACKFILL_ATTEMPTS (09-15T00Z→09-24T00Z,
  target {BTCUSDT:1.0}, 0 fill, equity đứng 100,000 — guard mark-gap + fail-closed chạy
  đúng, đây là bằng chứng luật forward-only hoạt động, KHÔNG phải performance, theo
  MOUNT NOTE trong `shadow_bandridge/SPEC.md`); 1 record OK đầu tiên 09-24T08:00Z:
  `band_gate_on=1.0, band_r=0.061486, donch_state=0.0` → gate ON nhưng không breakout → FLAT (no-trade hợp lệ).
- **0 fill từ khi mount.** Nguyên nhân không trade nào diễn ra được khi breakout bắn:
  sizing w=1.0 không thể fill dưới chi phí dương (cần ≈100,050.02 > cash 100,000 —
  `OWNER_DECISION_PACKET_bandridge_sizing_and_fill_law.md`; A7 audit mục 2b xác nhận
  lại từ code+ledger; regression test pin cả 2 hướng, commit `12540ebe`).
- 3 câu hỏi luật mở, đo được:
  1. **Sizing** (packet câu 1, A/B/C) — chưa owner-decision.
  2. **Fill law**: docstring adapter + SPEC hứa "fill ở NEXT H4 OPEN", executor fill ở
     bar 15m hoàn tất đầu tiên sau ranh giới (+1 tick) — FINDING đã ghi theo lệnh owner
     `.../findings/FINDING-2026-09-24-fill-timing-h4-open-vs-15m-bar.md` (commit a8062b1a,
     "recorded, not fixed"); packet câu 2 A/B.
  3. **Cost law (phát hiện MỚI của lane này)**: SPEC.md + identity manifest pin
     `fee_bps_per_side: 6.0` (6bps/side full stack) cho BANDRIDGE, nhưng executor
     production lấy `FEE_RATE_CURRENT = 0.0005` (5bps) + 1 tick
     (`e/shadow_worker.py` L180, L508–524; ledger records mang cost_regime_digest
     `130d2e7e…` giống CARRY). Chưa vật chất hoá (0 fill) nhưng **phải chốt trước khi
     fill đầu tiên**, nếu không PnL prospective đầu tiên của sleeve sẽ được ghi dưới
     một cost law chưa được owner chọn.

## 4. Phân tích "tính khoa học kinh tế" (bước E)

### 4.1 XSECT-FUND-CARRY-7D
- **Cơ chế**: funding perp là bảo hiểm mà bên đi long đòn bẩy trả cho bên cung cấp vị thế
  short ngược — carry = phí rủi ro squeeze + chi phí vận hành capital của arbitrageur.
  Ai bên kia: trader định hướng trả funding để giữ exposure; harvester nhận phí để
  chịu rủi ro squeeze và đãi trả vốn. Spec long bottom-funding/short top-funding =
  đứng về phía "cung bảo hiểm", thu premium khi đám đông chật vị thế.
- **Spec có còn đúng cơ chế không**: đúng luật hình thức (daily 00:00Z, gross 0.80,
  ±0.20/symbol, 24h rebalance — ledger khớp candidate.yaml byte-pin). NHƯNG về kinh tế,
  ở cost book hiện tại sleeve không còn là "carry": funding thu +4.60/10 ngày
  (~1.7%/năm) so với chi phí 302.83/10 ngày (~11%/năm run-rate). PnL đang là sách giá
  (momentum/mean-reversion 24h) với overlay carry âm biên. V6 lịch sử (net +20,580/năm,
  funding +2,277 ≈ 11% của lợi nhuận) được đo dưới chi phí lineage mềm hơn; nơi
  taker 5bps + 1 tick, edge cần lớn hơn ~2–3x mức funding quan sát được mới hòa chi phí giao dịch.
- **Nhất quán cơ chế trong ledger**: có — hướng book bám ranking funding, không trade
  vô luật; churn 0.62x/ngày nằm trong thiết kế 24h-rebalance (tức là spec TỰ CHO PHÉP
  turnover cao; đây là điểm yếu kinh tế của spec, không phải lỗi thực thi).
- **Rủi ro regime**: funding 2026-09 phẳng; trong pha bull 2024–25 funding cấu trúc
  dương cao hơn → thu nhập short-top-2 tốt hơn, nhưng squeeze (move giá ngắn, mạnh)
  đối xứng gây thiệt hại; 10 quyết định là quá nhỏ (9% của checkpoint 13 tuần) để nói gì.
- **Sample size**: 10 decisions, 16 round-trips. Mọi con số trên chỉ là sức khoẻ vận hành.

### 4.2 ILLIQ-AMIHUD-28D-W
- **Cơ chế**: Amihud |r|/dollar-volume cao = price impact lớn = hạn chế tham gia;
  premium bù thanh khoản phải trả cho người nắm tài sản kém thanh khoản. Sách
  long-illiquid/short-liquid, dollar+beta neutral tách premium khỏi beta.
- **Spec vs cơ chế**: mở book đúng quintile luật (20 symbol staged; 4 tên/quintile —
  phân tách yếu về mặt thống kê, nhưng đó là identity gốc, không được đụng). Sự kiện
  duy nhất không đủ đánh giá; chú ý historical reject đúng là **fold concentration**
  (0.7055) — loại rủi ro mà sample ngắn càng dễ trông "ổn" hoặc "rủi" giả tạo.
- **Nhất quán ledger**: ±0.125 đều, gross 1.0006 (quy ước documented), funding 0 booked
  (chưa tới settlement khi booking? — không đo được sâu hơn trong lane, ghi rõ).
- **Rủi ro regime**: universe 20 symbol staging cố định — nếu listing/liquidity thay
  đổi, quintile của 09-21 không so được với của 12-2026; điều này đúng với luật
  (PIT eligibility) nhưng làm premium đo được nhạy với thành phần universe.
- **Sample size**: 1/52 quyết định năm. NOT enough, theo thiết kế.

### 4.3 BASISLV-PREMFADE-28D
- **Cơ chế**: premium perp-index dương bền = đòn bẩy dài chật; fade của premium =
  arbitrage thu hẹp chênh lệch. Lịch sử đã tự bóc mẽ: mệnh đề price-only failure
  binding — kỳ vọng dương chủ yếu từ funding credit, tức cơ chế thực là **carry
  harvest**, không phải convergence giá (verbatim trong identity manifest). Vì vậy
  về kinh tế sleeve này trùng họ rủi ro với CARRY (thu premium đứng ngược đám đông
  đòn bẩy) — trùng không phải xấu, nhưng hai sleeve gần như là cùng một trade với
  hai mặt nạ (đã có cảnh báo "two similar crypto books" trong plan §5).
- **Trạng thái**: 1 event, DATA_BLOCKED fail-closed đúng; nguồn đã heal; 0 fill.
- **Sample size**: 0 quan sát hiệu lực. Mọi ý kiến chỉ dừng ở mức vận hành.

### 4.4 BTC4H-BANDRIDGE
- **Cơ chế**: trend-following / regime-switching — Donchian-30 breakout trong band
  SMA200×1.03 (hysteresis) = mua khi regime xác nhận, cắt khi hỏng. Premium kinh tế:
  bù cho việc đứng sau drawdown whipsaw; bên kia là mean-reversion fader. S0 đo được
  (`shadow_group_s0.json`, grid 1.0|measured): net +972,763 trên $100k 2020-01→2026-09,
  DD 24.94%; **GATE_SHUFFLE control +137,080** → timing mang thông tin thật (ratio ~7.1x),
  nhưng control cũng dương (bull beta 2020–2026 là thành phần lớn của lợi nhuận thô).
- **Nhất quán khoa học — điểm cần nói thẳng**: áp chính gate concentration đã giết
  3 sleeve tổ tiên lên S0 của BANDRIDGE: F3 = 641,776 / tổng fold dương
  (170,267+641,776+175,801 = 987,845) = **65% > 50%** — BANDRIDGE S0 sẽ FAIL cùng gate
  đó (đo từ shadow_group_s0.json fold_net). Mount là quyết định owner với label
  POSTHOC_DISCOVERY_CANDIDATE + A7 waived (ghi trong identity manifest) — hợp lệ về
  thẩm quyền, nhưng report này có nghĩa vụ giữ đối xứng nhận định: sleeve 4 KHÔNG
  được đối xử mềm hơn sleeve 1–3 về bằng chứng.
- **Funding cost**: tổ tiên BTC-H4-EDGE-SEARCH-V1 đo funding drag thực
  **11.798%/năm** vs hằng số frozen (`.../btc_h4_edge_search_v1/freezes/feasibility_census.json`,
  `annualized_mean_drag_pct: 11.798`); S0 grid cho thấy measured funding tốn 123,356
  vs constant 17,344 (7.1x) — law "measured funding per settlement" của SPEC là đúng
  hướng kinh tế (không underestimate cost như tổ tiên).
- **Sample size hiện tại**: 1 quyết định hợp lệ (no-trade), 0 fill. Sleeve chưa đo được
  gì. Mục tiêu duy nhất hợp lệ: hành vi forward từ ACTIVATION 2026-09-24T00:00Z.

## 5. Ý kiến cải thiện (bước F) — mỗi ý: cơ sở → kỳ vọng (chiều) → nhãn → rủi ro nếu làm sai

**Ý 1 — Chốt sizing BANDRIDGE: chọn B (cost-aware sizing).** [Packet câu 1]
- (1) Cơ sở lượng: cần ≈100,050.02 trên 100,000 cash (packet + A7 mục 2b đo lại từ
  accounting.apply_fill); phần thiếu hụt ≈ $50 = 5bps = đúng một taker fee của book
  frozen. Cùng họ lỗi với tail-short gross-1.0 của ILLIQ/PREMFADE
  (`e/handoff_shv1-e-worker.json` headline finding) — phía SHORT đã được remediate bằng
  SIZING_AND_CAP_BASIS (A7-accepted tại activation), phía BUY chưa từng có remediation
  tương đương → chọn B còn khôi phục đối xứng xử lý giữa 2 phía của cùng một lỗi luật.
- (2) Kỳ vọng: realized weight ≈0.99946 thay vì 0 — sleeve QUAN SÁT ĐƯỢC thay vì chết
  vô sinh; haircut ≤ ~$50/100k mỗi lần vào (5bps), ghi `realized_weights` cạnh
  `target_weights`. Không hứa số PnL.
- (3) Nhãn: **AMENDMENT_REQUIRED** (đụng executor sizing law = frozen spec/identity;
  packet đã ghi "CẦN amendment ghi rõ vào identity manifest"). Forward-only, preregister
  + test parity, áp dụng dạng tổng quát "affordability-aware sizing cho cả buy lẫn sell"
  thay vì patch riêng BANDRIDGE.
- (4) Rủi ro nếu làm sai: chọn A vĩnh viễn = sleeve 100k đứng yên, mất toàn bộ giá trị
  thông tin prospective mà owner đã cấp; chọn C (tolerance cho cash âm ~$50) = phá
  định thức no-leverage/cash≥0, mở tiền lệ "vay nội bộ" không được ghi trong bất kỳ
  identity nào; patch riêng từng family = law phân mảnh, không repro được.

**Ý 2 — Chốt fill law: chọn A (bar 15m hoàn tất đầu tiên là luật chính tắc, sửa doc).**
[Packet câu 2]
- (1) Cơ sở: đường thực thi đang chạy (đã A7 CONFIRM: 56 fill CARRY/ILLIQ khớp đúng
  luật chi phí frozen, 0 violation) là first-completed-15m-bar + 1 tick bất lợi; PIT
  hợp lệ, không look-ahead. Với sách momentum (BANDRIDGE), fill tham chiếu giá TRỄ 15
  phút nghiêng bất lợi cho bên mua breakout (giá đã chạy) → là lựa chọn **bảo thủ**,
  không phình edge. Option B (re-derive H4-open) đòi đổi executor/parity + preregister;
  với CARRY 48 fill đã book dưới luật 15m, đổi luật giờ = đụng ledger sống.
- (2) Kỳ vọng: 0 đổi PnL đã ghi; loại bỏ mâu thuẫn doc↔engine trước khi fill BANDRIDGE
  đầu tiên sinh tranh chấp diễn giải.
- (3) Nhãn: quyết định thuộc **OWNER_DECISION_REQUIRED** (packet để trống); triển khai
  phương án A là sửa tài liệu + re-pin hash SPEC/plan/adapter-docstring trong identity
  manifest (doc-only, không đụng code) → scope **AMENDMENT_REQUIRED** nhẹ (vì SPEC.md
  là file byte-pin `3a7591fb…`, sửa doc vẫn đổi hash pin và phải disclose).
- (4) Rủi ro nếu làm sai: giữ 2 luật song song = mọi PnL BANDRIDGE tương lai mang
  "fill mơ hồ"; re-derive ngược (B áp cho dữ liệu đã có) = vi phạm forward-only.

**Ý 3 — Chốt cost law BANDRIDGE: 6bps/side (SPEC) hay 5bps+tick (executor đang chạy)?**
[Phát hiện mới của lane]
- (1) Cơ sở: identity manifest pin `fee_bps_per_side: 6.0` cho BANDRIDGE;
  `e/shadow_worker.py` L180/L508–524 build cost book 0.0005+1tick cho mọi family;
  ledger records mang digest `130d2e7e…` = book chung, không có override 6bps. Đây là
  mâu thuẫn cùng loại với fill-law finding (plan/SPEC hứa X, executor làm Y).
- (2) Kỳ vọng: chênh lệch 1bps/side ≈ 2bps/round-trip trên toàn notional — với sách
  giữ trung bình nhiều ngày (min-hold 12 H4 = 2 ngày), ảnh hưởng nhỏ so với funding
  measured (11.8%/năm), nhưng phải đúng mới hạch toán được.
- (3) Nhãn: **OWNER_DECISION_REQUIRED** — gộp vào cùng amendment với Ý 1/Ý 2, chốt
  TRƯỚC fill đầu tiên (hiện 0 fill nên chưa tốn gì).
- (4) Rủi ro nếu làm sai: PnL BANDRIDGE đầu tiên được ghi dưới cost law chưa ai chọn →
  tranh chấp identity ngay từ record đầu tiên của sleeve.

**Ý 4 — Ghi nhận & Document hóa sự kiện tuần 09-15 bị bỏ qua cho ILLIQ/PREMFADE.**
- (1) Cơ sở: đo được — activation.json khai 09-15 weekly, scheduler neo tuần từ
  00:00 ngày start nên nhảy 09-21; không có record DATA_BLOCKED (plan §8).
- (2) Kỳ vọng: thu hẹp khoảng "kế hoạch nói gì" vs "mã làm gì"; không phục hồi quan sát
  đã mất (không được backfill).
- (3) Nhãn: **ENGINEERING_ALLOWABLE** cho việc ghi chú/pin hành vi scheduler vào
  activation/control tree (không đổi exposure). ĐỪNG sửa scheduler mid-run để "bù"
  09-15 — hành vi enumeration đổi = **AMENDMENT_REQUIRED** và nguy cơ sinh event retro.
- (4) Rủi ro nếu làm sai: sửa scheduler ngầm → chuỗi event_id đổi, repro tháng đầu
  (G7 monthly reproduction) lệch; backfill 09-15 = vi phạm forward-only.

**Ý 5 — Thêm realized_pnl per fill vào schema event tương lai (round-trip accounting).**
- (1) Cơ sở: hiện không tính được win-rate round-trip hay gross-vs-net per trade
  (NOT_RUN) vì event chỉ có tổng fee/slip/funding + equity MTM; với các gate
  concentration/fold của chương trình, đây là số sẽ bắt buộc ở đánh giá 13/26/52 tuần.
- (2) Kỳ vọng: cho phép win-rate, đặt tên winning symbol, đo gross PnL tách cost —
  phục vụ đúng các gate tổ tiên mà không đụng signal.
- (3) Nhãn: **ENGINEERING_ALLOWABLE** (chỉ áp prospective, không rewrite ledger cũ;
  ghi schema version mới).
- (4) Rủi ro nếu làm sai: backfill/recompute các event cũ = phá append-only; nếu gắn
  attribution sai (định giá fill bằng mark không cùng thời điểm) sẽ tạo số giả.

**Ý 6 — CARRY: thêm 1 book chẩn đoán maker-entry (0.02%)song song, KHÔNG đụng book chính.**
- (1) Cơ sở kinh tế: cơ chế carry không đòi taker; entry chờ lệnh (maker) phù hợp
  sách không thời-gian-critical (rebalance 00:00Z + khớp trong ngày). Chi phí 30bps/10
  ngày hiện tại là nguyên nhân số 1 biến carry thành sách giá. Chỉ 5bps→2bps đã giảm
  ~60% chi phí giao dịch.
- (2) Kỳ vọng: đo khoảng cách edge giữa hai cost view; nếu maker-view vẫn âm thì cơ
  chế thật sự đã hết (regime funding phẳng), nếu dương thì cost model là thứ giết sleeve.
- (3) Nhãn: **ENGINEERING_ALLOWABLE** với điều kiện: book chính CURRENT_CONSERVATIVE_COST
  giữ nguyên byte (plan §6 cấm move cost trong run; thêm book chẩn đoán song song
  không di chuyển book cũ, phải disclose là DIAGNOSTIC, không promotion được từ nó).
  Nếu owner muốn ĐỔI book chính → **AMENDMENT_REQUIRED** + cost-regime boundary mới.
- (4) Rủi ro nếu làm sai: ngầm hạ cost = chính là "lowering costs" mà plan §4 cấm;
  filler giả định maker khớp được tại 00:15 là optimistic fill — phải model thể hiện
  xác suất không khớp.

**Ý 7 — Đối xứng báo cáo: công bố BANDRIDGE S0 dưới cùng gate concentration với 3 sleeve tổ tiên.**
- (1) Cơ sở: F3-share 65% (đo từ shadow_group_s0.json) > 50% — chính lỗi đã reject
  3 sleeve. Owner có quyền mount (và đã mount) nhưng reviewer phải giữ tiêu chuẩn
  bằng chứng đối xứng.
- (2) Kỳ vọng: prevent "survivor bằng danh sách" — BANDRIDGE vẫn là POSTHOC candidate,
  chỉ forward observation mới có thể cải thiện bằng chứng.
- (3) Nhãn: **ENGINEERING_ALLOWABLE** (chỉ reporting).
- (4) Rủi ro nếu làm sai: nếu báo cáo trình BANDRIDGE "972k" mà không kèm fold-share,
  owner quyết định tiếp dựa trên mẫu survivorship — chính cái mà chương trình này
  tồn tại để chống.

**Ý 8 — PREMFADE/ILLIQ: probe hoàn chỉnh dữ liệu trước mốc quyết định (T−1h) để đỡ đốt quan sát tuần.**
- (1) Cơ sở: 1 event tuần bị DATA_BLOCKED (BASISLV 09-21) do vendor gap; nguồn heal
  trong ~3 ngày; mỗi event tuần chỉ có 52/năm — mỗi lần đốt mất ~1.9% sample năm.
- (2) Kỳ vọng: giảm xác suất đốt event (chiều tích cực lên data completeness); không
  đổi signal; event vẫn fail-closed nếu probe thấy thiếu (luật giữ nguyên).
- (3) Nhãn: **ENGINEERING_ALLOWABLE** (probe chỉ đọc, paced như PacedFetch hiện có).
- (4) Rủi ro nếu làm sai: nếu probe tự động retry/đổi window dữ liệu → đụng PIT;
  phải chỉ cảnh báo, không thay đổi nguồn sự kiện.

**Khuyến nghị gộp BANDRIDGE (trả lời trực tiếp packet, trống phần "Quyết định của owner"):**
- Câu hỏi 1 (sizing): **B — cost-aware sizing** (`qty = min(w*equity/ref, cash/(fill_price*(1+fee)))`),
  ghi `realized_weights` từng event, amendment identity manifest, forward-only.
- Câu hỏi 2 (fill law): **A — sửa doc cho khớp executor** (first-completed-15m-bar là
  luật chính tắc); KHÔNG re-derive ngược; kèm việc re-pin SPEC/plan wording vào identity
  manifest. Gộp thêm Ý 3 (chốt 5bps+tick hay 6bps — khuyến nghị kỹ thuật: giữ
  5bps+tick đang chạy vì đã audit, và sửa SPEC cho khớp, hoặc mount book riêng 6bps
  cho BANDRIDGE nếu owner muốn đúng nguyên văn SPEC; quyết định thuộc owner).
- Timeline: cả 3 chốt TRƯỚC khi breakout đầu tiên xảy ra (gate đang ON theo record
  08:00Z — `band_gate_on=1.0`, band_r 0.0615 > 0.03; điều kiện Donchian chưa tới,
  nhưng khoảng cách không lớn).

## 6. Giới hạn của review này (NOT_RUN/BLOCKED)

- Win-rate round-trip, gross PnL per trade: NOT_RUN (schema ledger hiện không có).
- Không đo được regime funding dài hạn từ ledger (9.5 ngày) — trích tổ tiên 11.798%/năm
  (feasibility_census.json) và S0 grid, không tự đo lại.
- Không đọc registry hiện hành (`plans/CYCLE_REGISTRY.json`) trong lane — mệnh đề
  "registry head STALE" dẫn từ GATES.md G0 (đo 2026-09-24) + HEAD đo được; trạng thái
  registry tại giờ review là NOT_RUN trong lane này.
- 09-15 weekly event của ILLIQ/PREMFADE: có tồn tại hay bị DATA_BLOCKED không thì
  không tra được từ byte hiện có (ledger không có record) — kết luận "không được sinh"
  dựa trên heartbeat `due:1` + logic scheduler, đã cite.
- Không chạy test suite (read-only review; các con số test dẫn từ A7/GATES artifacts).

— lane_crypto_sleeves, 2026-09-24.
