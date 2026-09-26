# PLAN (DRAFT) — SRLV-PROGRAM-V1 — Master plan: chương trình nghiên cứu hàng loạt Support/Resistance · Supply–Demand · Liquidity Sweep · Volatility (Forex + Crypto)

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** File
> này không đăng ký cycle, không spawn worker/lane, không download, không mở
> S1/sealed holdout, không đụng shadow/daemon/dashboard, không đặt lệnh,
> không tiêu GO nào. Nó nằm DƯỚI umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`
> (ACTIVE_LIGHT trong registry) — kế thừa toàn bộ luật umbrella §§1–11 và
> charter `ERP-FOREX-PROGRAM-V1` trừ khi child chặt hơn. Owner phê chuẩn
> charter này bằng quyết định ghi vào
> `research/control/SRLV-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md`.
>
> Authored 2026-09-26 bởi Lead từ owner instruction (verbatim intent: thiết kế
> và vận hành chương trình hàng loạt Forex + crypto về support/resistance,
> supply–demand, liquidity sweep, volatility; mục tiêu một cơ chế backtest
> PIT-clean, sau phí, tái lập được trên nhiều cặp; REJECT_ALL/NO_CANDIDATE là
> kết quả hợp lệ; không chạy vô hạn để ép ra winner; hai nhánh tách biệt
> không trộn ledger/cost/verdict; prompt này CHỈ cho khảo sát + lập kế hoạch,
> không thay thế GO-1/GO-2/GO-3).

## 0. Program identity

```text
program_id    SRLV-PROGRAM-V1 (master layer; scored cells = 0/0 — không bao
             giờ tự score; mọi scored surface thuộc child cohort)
parent        ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella, luật chung §§1–11)
tracks        SRLV-FX (6 cặp FX majors — cohort-series tiếp charter
              ERP-FOREX-PROGRAM-V1, chịu luật reopening R1–R5)
              SRLV-CX (4 cặp Binance perp — không gian cơ chế mới, tách biệt
              Track B delta-neutral carry)
separation    Hai track KHÔNG trộn ledger / cost book / verdict / GO phrase /
              worktree (§4)
goal          ≥1 strategy identity đạt BACKTEST_CANDIDATE_REPLICATED trên ≥2
              cặp cùng track (đủ cả limb replication §4 của forex-program
              charter), HOẶC kết luận NO_CANDIDATE / BLOCKED_<class> đúng gate
ledger        per-child trial_ledger.jsonl (append-only) + P-9 denominators;
              mọi outcome-viewed pair/timeframe/parameter = 1 trial row
S1            SEALED_UNTOUCHED ở mọi nơi; sealed OOS per-identity một lần,
              sau GO riêng
orders        NONE — mọi kết luận paper/backtest tier; shadow/live là GO riêng
stops         §11 (hết giả thuyết mới / hết data authority / hết OOS sạch /
              hết power / hết ngân sách ⇒ dừng đúng gate)
budget cap    §9: program ≤ 96 scored cells; ≤ 3 cohort / track
```

## 1. Mục tiêu / không-mục-tiêu

### 1.1 Mục tiêu

Tìm kiếm theo cơ chế (mechanism-first) trong không gian: (a) phản ứng giá tại
mức đã biết trước; (b) phá mức do cụm stop / forced flow; (c) quét thanh
khoản (sweep) rồi hấp thụ/đảo chiều; (d) volatility làm BIẾN TRẠNG THÁI (không
bao giờ nguồn hướng — §2.4). Mỗi cohort: council outcome-blind chọn tối đa 3
giả thuyết, falsify TRƯỚC PnL, score dưới cost book đo được, bảo toàn sealed
OOS, replication độc lập. Chuẩn không hạ để có số dương: `REJECT_ALL` /
`NO_CANDIDATE` hợp lệ và được kỳ vọng là kết quả modal (Track A: 2/2 cohort
REJECT_ALL; crypto ng: 11/11 chết ở rho bar).

### 1.2 Không-mục-tiêu

- Không cứu bất kỳ family đã chết bằng đổi ngưỡng/đảo dấu/đổi tên/đổi
  timeframe/thêm indicator/đổi session/đổi cặp (umbrella §6; Q-3; F-0 court).
- Không tái chạy panel FX cũ rồi gọi là discovery (owner instruction nguyên
  văn; VIABILITY: zero remainder trên authorized space hiện có).
- Không hạ gate, không nới power, không "thử lại" sau khi một identity fail
  OOS; không parameter rescue sau khi PnL xuất hiện.
- Không claim live-readiness (umbrella §1.3); không đụng shadow/dashboard/
  worker đang chạy; không push/merge; không mở sealed OOS.
- Mass test KHÔNG PHẢI mass selection: cùng một identity frozen áp toàn
  panel; báo từng cặp / từng năm-fold / toàn panel / leave-one-out; cấm tối
  ưu riêng từng cặp rồi gọi là replication (§8.4).

## 2. Không gian cơ chế và luật đặc thù

### 2.1 Ba họ giả thuyết (định nghĩa sườn, council mới đóng chi tiết)

- **H1 Reaction-at-known-levels**: mức hình thành từ dữ liệu ĐÃ HOÀN TẤT tại
  thời điểm quyết định (prior-day/week high–low, round numbers, anchored
  levels). Mức phải tồn tại TRƯỚC bar quyết định (§3).
- **H2 Break-by-forced-flow**: phá mức được CƠ CHẾ epilogue (ai bị ép trả
  tiền). Stop-cluster/forced-flow KHÔNG quan sát được trực tiếp trên kline —
  payer story phải được mã hóa bằng observable PIT hợp pháp (proxy) và có
  falsifier riêng; nếu payer chỉ tồn tại trong narrative ⇒ `VETOED_FICTIONAL_
  COUNTERPARTY` (BTC-BEAR precedent).
- **H3 Sweep-then-absorb**: quét qua mức rồi hấp thụ/đảo chiều. Trên dữ liệu
  OHLC/M1: mọi "sweep"/"zone" là **proxy hình học**, bắt buộc nhãn
  `PROXY_NOT_ORDERBOOK`; không được gọi là order-book liquidity nếu không có
  order-book PIT (owner instruction nguyên văn).

### 2.2 Mapping sang ancestry fence (đọc trước council, binding)

- FX: H1 với prior-day band + any gate = class #1 DEAD (TRACKA2 fence); H2/H3
  với payer "stop beyond visible extremes" = S1/C1/C2 payer verbatim đã chết
  — chỉ sống lại với NEW payer + new information layer (F-0 ba test);
  vol-as-direction = class #9 DEAD; microstructure tape = class #10
  UNCONSTRUCTIBLE trên Dukascopy M1.
- Crypto: EOS1-E1/E2 fences; PSV1-Donchian CONTROL_OUTEARNED; BTC-BEAR double
  veto; V10 absorption BLOCKED; 11/11 ng proposals chết ở |rho| 0.20.

### 2.3 F-0 court (chạy trước rho, trước PnL — P-27)

Mỗi đề xuất bị hỏi ba test: (1) **skeleton test** — bỏ mechanism-specific
observable, giữ trigger/direction/exit shape, còn edge không? (cùng shape =
cùng family chết); (2) **payer test** — ai trả, vì sao họ BẮT PHẢI trả chứ
không chỉ "thường trả", họ có tự arbitrage đi không; (3) **information
test** — thông tin gì trong observable chưa có trong clock/trend/spread
(Q-7). Skeptic lane có VETO pre-PnL tại F-0.

### 2.4 Hợp đồng volatility-as-state (binding)

- Chỉ được dùng làm biến trạng thái (gating/sizing/regime), KHÔNG BAO GIỜ
  nguồn hướng (VIABILITY class #9; Q-7 direction 0/96 hai lần).
- Phải tính từ dữ liệu ĐÃ HOÀN TẤT tại thời điểm quyết định: trailing
  realized vol trên các bar ĐÃ ĐÓNG; cấm same-day full-range percentile
  (RANGEFADE PIT seam — P-18), cấm high–low của bar chưa đóng, cấm percentile
  cả ngày.
- **Incrementality test bắt buộc trước scoring**: nested comparison vs
  (i) clock-only, (ii) trend baseline, (iii) spread-state — volatility state
  phải thêm thông tin NGOÀI ba control đó (例: regime occupancy có cải thiện
  out-of-sample ranking/expectancy của chính anchor không — metric frozen tại
  trial freeze). Fail ⇒ bỏ biến volatility, KHÔNG phải bỏ cơ chế nếu cơ chế
  đứng được không cần nó (freeze phải định nghĩa cả hai hình thức anchor
  before outcome).
- Mỗi đề xuất dùng vol-state mang clock-only shadow control (Q-11 non-vacuous).

## 3. Kỷ luật PIT / intrabar (đóng băng trước mọi PnL — danh sách cấm của owner, vận hành hóa)

Trước khi bất kỳ PnL nào được tính, trial freeze phải pin nguyên văn:

1. **Thuật toán xác định vùng/mức**: công thức mức/vùng + code digest sha256;
   mức chỉ được dùng từ thời điểm `t_known` — bar ĐẦU TIÊN mà mọi dữ liệu đầu
   vào của mức đã đóng.
2. **Độ trễ xác nhận pivot** ≥ 1 bar đóng (pivot chỉ tồn tại sau N bar xác
   nhận; không dùng future swing high/low).
3. **Luật fill**: quyết định trên bar t đã đóng ⇒ fill tại open bar t+1 theo
   quote ngược chiều (engine law `v2_lib.py:27-28` kế thừa); CẤM same-bar
   confirm rồi fill ngược thời gian.
4. **CẤM giả định thứ tự high/low trong một OHLC bar** — mọi logic "sweep
   trước rồi reclaim trong cùng bar" phải viết thành chuỗi bar (sweep hoàn
   tất tại close bar t; quyết định tại t+1) hoặc dùng event-time M1 sequence;
   nếu không tách được ⇒ cơ chế không constructible trên plane đó, ghi
   `NOT_CONSTRUCTIBLE_INTRABAR`, không bend luật.
5. **Cấm**: high–low của bar chưa đóng; percentile cả ngày; same-day statistic
   cho biến regime ngày (P-18); day-d full range tại day start.
6. **Ba lớp bắt lookahead độc lập** (owner instruction): (i) panel-truncation
   replay — chạy lại signal code trên panel cắt tại mỗi decision time, output
   phải byte-identical (M-5); (ii) future-mutation — sửa dữ liệu tương lai
   sau decision time, output không được đổi; (iii) independent implementation
   — reproducer/A7 viết lại từ spec + raw planes, đối chiếu record-level.
7. **Delay-pair (Q-4)**: mọi edge sub-hour phải quote delay-0 VÀ delay-1 cạnh
   clairvoyant control; thông tin bay mất sau 1 bar = market-maker
   compensation ⇒ kill.
8. **Dry-run exact-arm non-vacuous + leak-scan** trước scored run.

## 4. Luật tách hai track (không trộn — owner instruction nguyên văn)

| Khía cạnh | SRLV-FX | SRLV-CX |
|---|---|---|
| Child cycle | SRLV-FX-C1… (worktree/branch theo registry) | SRLV-CX-C1… (riêng) |
| Ledger | trial_ledger.jsonl riêng | riêng |
| Cost book | FX book §7.1 | crypto book §7.2 (funding, v.v.) |
| Verdict vocabulary | umbrella §9 + BACKTEST_CANDIDATE_REPLICATED | như FX + nhãn crypto riêng |
| GO phrase | riêng từng gate, không dùng chéo | riêng |
| Data plane | Dukascopy M1 (+nguồn mới nếu R mở) | Binance Vision/fapi |
| Kết luận một track KHÔNG BAO GIỜ trích sang track kia làm bằng chứng | — | — |

Shared code phải prove compatibility (CLAUDE.md); mọi module dùng chung được
pin digest trong freeze của cả hai child nếu dùng.

## 5. Candidate universe & per-pair gate (không score-all)

- Universe khai báo: FX = EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF;
  CX = BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT. Đây là **candidate universe**,
  không phải lệnh score tất cả.
- Mỗi cặp qua gate riêng tại GO-1 của child: data (probe/census/DST/
  rollover/scale fixtures), license, PIT, cost, power. Trạng thái đo sẵn:
  `research/control/SRLV-PROGRAM-V1/DATACOST_FEASIBILITY_MATRIX.md`.
- Cặp thiếu nguồn hợp lệ ⇒ ghi `BLOCKED_<reason>` vào freeze artifact; KHÔNG
  âm thầm thay cặp; thay slate = owner decision riêng.
- Vai trò từng cặp theo `OUTCOME_EXPOSURE_MAP.md` (binding): cặp
  outcome-exposed chỉ phục vụ ancestry/fixture/cost authority; dev mới chỉ
  trên bề mặt được phép; sealed không đọc.

## 6. Frontier reopening law — SRLV-FX (trả lời trực tiếp yêu cầu owner)

Forex đang `NO_CANDIDATE` trên frontier cũ (VIABILITY 2026-09-26, 12 dead
classes, "zero remainder" trên authorized space). **Thông tin mới mở lại
frontier phải là MỘT trong các mục dưới, với bằng chứng bytes + authority đo
được tại GO-1 của SRLV-FX-C1 — và KHÔNG có hình thức nào khác:**

| Reopener | Bằng chứng cần | Mở gì |
|---|---|---|
| **R2** nguồn bid/ask độc lập | TrueFX registration / OANDA v20 practice / Dukascopy written consent (owner action) + bytes on disk + license gate PASS + cross-source PIT seam check | observable tick-level event-time; nguồn thứ hai cho spread/cost authority; limb replication (iii) nguồn-độc-lập |
| **R1** broker cost authority | two-sided market-data subscription + Flex statement (commission + overnight interest measured) | commission/swap measured book; all-in được ĐO — có thể xác nhận CAO HƠN hoặc THẤP HƠN mọi ước tính hiện có (hiện executable spread NOT_SUBSCRIBED, commission NOT_RUN ⇒ all-in chưa đo); cơ chế chết F-5 chỉ được xét lại bằng số đo, không theo chiều định trước |
| **R3** financing band | broker-grade swap data cited | class multi-day hold / carry (đang BLOCKED F4) |
| **R5** information layer mới | artifact có authority (例: per-fill s_open non-PnL; depth collector đạt floors kiểu lane-C) | observable mới qua D2 |
| **R4** (không phải reopener scoring) | một identity qua dev gates | slate amendment USDCHF/new pairs |

- Nếu KHÔNG reopener nào có bằng chứng: SRLV-FX-C1 đóng
  `BLOCKED_FRONTIER_NOT_REOPENED` với 0 scored cell, 0 holdout look — đó là
  kết quả đúng, không phải thất bại (Q-16).
- Tái chạy cùng panel Dukascopy cũ (3 cặp exposed + 2 cặp dev-exposed) với
  cơ chế cùng skeleton/payer = bị F-0 kill ngay; không được gọi là discovery.
- Ngưỡng cost đã pin (P3-A frozen ≤0.41 pip crossing @k=2.0) không re-derive.
  Lưu ý bằng chứng hiện tại: minTick 0.5 pip (đo 5 cặp) chỉ là fact hình học
  tick — KHÔNG được suy ra executable spread hay all-in cost; all-in thực sự
  CHƯA ĐO (two-sided NOT_SUBSCRIBED, commission NOT_RUN). R1 là bước đo;
  kết quả có thể cao hơn hoặc thấp hơn, và cơ chế chỉ được xét lại bằng số đo
  đó — không assume maker/mid/no-slippage ở cả hai chiều.

## 7. Hợp đồng cost (mỗi track; thiếu thành phần trọng yếu ⇒ fail-closed)

### 7.1 FOREX

1. Measured book: event-time session/rollover spread curve tại fill-bar ×
   k ∈ {1.0, 1.5, 2.0} — sha-pinned census per pair; spread giãn lúc phá mức
   được lấy theo PHÂN PHỐI FILL CỦA CƠ CHẾ (Q-2/Q-8), không global median.
2. Declared book (rõ nhãn, không override measured): commission
   (DECLARED_UNMEASURED tới R1), slippage/adverse-selection
   (DECLARED_UNMEASURABLE_ON_M1_BIDASK), maker = cấm assume.
3. Financing: structural-zero bằng force-flat fixture (flat trước rollover +
   weekend; V1 pandas-bug precedent). Multi-day hold chỉ khi R3.
4. Ceiling: expected gross premium/holding period ≥ full RT stress cost, xét
   TRÊN PHÂN PHỐI ĐO ĐƯỢC; ceiling âm ⇒ VETO trước scoring (K-COST).
5. Mọi verdict mang `PAPER_TIER + SINGLE_SOURCE_PANEL +
   FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` (tới khi nguồn mới mở).

### 7.2 CRYPTO

1. Cost books tách lớp: funding = MEASURED (per-settlement path, native,
   while held; dual book với frozen constant); fee 5 bps + 1 adverse tick =
   DECLARED book (venue-published tier floor + convention tick, freeze từ
   CHR3F; lên lớp measured chỉ khi validate vs fills — Q-8); spread census
   theo giờ fill từ bookTicker/aggTrades (coverage verify; thiếu ⇒ BLOCKED).
   Declared book không bao giờ override measured book.
2. Funding-path stress: 24.7% settlements âm trong downtrend; worst
   −0.30%/8h ≈ 2.5 fee RT; miss-N-settlement + gap-reopen bất lợi (DECLARED).
3. Gap/outage/latency/liquidity-in-stress: DECLARED bands + ×1.5/×2.0.
4. Maker-only assumption CẤM tới khi queue-position đo được; levered/borrow/
   liquidation-model BLOCKED ⇒ mọi arm unlevered 1x.
5. Ceiling như 7.1.4 (đơn vị bps/thời gian giữ).

## 8. Mass test ≠ mass selection (binding)

1. **Một identity duy nhất** frozen (thuật toán mức, tham số, entry/exit,
   cost book, universe) áp cho TOÀN panel được phép của cohort; báo từng cặp,
   từng năm/fold, toàn panel, leave-one-out (bỏ từng cặp một).
2. Neighbour configs (≤2) cũng chạy nguyên panel — không per-pair tuning;
   mọi per-pair biến thể = trial mới trong ledger và PHÁ replication.
3. Trial ledger: mọi lần xem outcome của pair/timeframe/parameter (kể cả
   exploratory có số) ghi 1 row; observed vs published tách (P-9); smoke/
   dry-run chỉ kill-được, không select-được, không vào denominator.
4. DSR trên TOÀN trial ledger chương trình tại mỗi terminal; PBO chỉ khi
   ≥8 configs (else NOT_RUN).
5. Replication (định nghĩa 3 limb — forex-program charter R5 nguyên văn):
   (i) impl độc lập; (ii) thời gian chưa dùng để chọn; (iii) bề mặt độc lập
   (cặp outcome-free HOẶC nguồn độc lập có authority). Cửa sổ transfer =
   MỘT look cấp chương trình. Thiếu limb ⇒ không viết "replicated".

## 9. Ngân sách trial

- **Program cap: ≤ 96 scored cells** tổng (FX ≤ 48, CX ≤ 48), chia:
  ≤ 3 cơ chế × ≤ 6 arms (1 anchor + ≤2 neighbour + 1 causal control + 1
  inverted control + 1 baseline) × 1 home surface = ≤ 18 cells/cohort;
  ≤ 3 cohort/track. Tham chiếu: FX-MAJORS 96/96 toàn campaign; EURUSD
  open-search 1/48 sống sót rồi chết holdout — denominator là luật.
- Holdout/sealed looks: ledgered riêng, KHÔNG cộng vào cell cap, nhưng vào
  observed denominator.
- Mọi cặp thêm vào slate (R4) không tăng cap — chỉ phân phối lại trong cap.
- Hết cap ⇒ dừng đúng §11, không gia hạn không có owner decision.

## 10. Kill rules (preregistered; bắn bất kỳ cái nào = terminal cho identity)

- **K-F0** skeptic VETO tại F-0 (skeleton/payer/information fail; same-family
  variant; fictional counterparty).
- **K-ANC** ancestry |rho| > 0.20 trên frozen representation (P-12), hoặc trúng
  class veto (re-clock, calendar geometry, displaced-fade, nominal-level,
  vol-level, premium-fade, EOS1-E1/E2…).
- **K-PIT** bất kỳ lỗi §3: truncation không byte-identical; future-mutation
  đổi output; same-bar fill ngược thời gian; intrabar order assumption;
  same-day regime statistic; delay-1 edge bay mất (Q-4).
- **K-COST** ceiling âm hoặc cost auditor BLOCKED vì thiếu thành phần trọng
  yếu (fail-closed, không điền số đẹp).
- **K-CTRL** clock-only/placebo tái tạo ≥0.5× anchor; inverted out-earn
  anchor; baseline (trend/beta-matched; FX thêm short-beta/carry-beta theo
  pair) bị beat thiếu biên ≥2× theo freeze.
- **K-VOL** volatility state fail incrementality (§2.4) ⇒ rơi biến vol;
  identity không đứng nổi không cần vol ⇒ kill cả identity.
- **K-CONC** top fold/contribution > 50% positive PnL.
- **K-POWER** dưới floors §DATACOST 4 (child chỉ được nâng).
- **K-OOS** sealed one-look fail ⇒ terminal identity, không rescue; ancestry
  registry ghi lại; không thử lại cặp/window khác.
- **K-THIN** regime/occupancy floors fail ⇒ NOT_RUN_THIN (không relax).

## 11. Điều kiện dừng / stop conditions (fail-safe, không chạy vô hạn)

Dừng và báo owner khi bất kỳ: (a) 2 cohort liên tiếp của MỘT track đóng
REJECT_ALL/slate rỗng ⇒ viability council của track; không cohort mới không
có observable/nguồn/giả thuyết payer mới CÓ BẰNG CHỨNG (owner note cohort-2
nguyên văn); (b) hết data authority (mọi nguồn §5/§6 blocked, owner chưa
mở); (c) sealed map trống (không còn cửa sổ sạch; crypto: chỉ còn
prospective); (d) power không đạt với ngân sách còn lại; (e) hết 96 cells
hoặc hết 3 cohort/track; (f) một cohort vượt 14 ngày lịch mà không qua gate
kế tiếp (time-stop vận hành — báo owner, không treo). Kết luận `NO_CANDIDATE`
(đã tìm trong không gian được cấp quyền) hoặc `BLOCKED_<class>` — cả hai đều
thành phẩm (Q-16).

## 12. Roster lane (mỗi cohort; mù outcome theo ranh giới)

Kế thừa nguyên văn bảng roster `PLAN_erp_forex_program_v1.md` §5: A1
controller; **PIT/data auditor** (FAIL ngay nếu leak, không xem PnL);
**economic skeptic** (VETO pre-PnL tại F-0); **cost/execution auditor**
(BLOCKED khi thiếu nguồn); **blind proposers P1..Pn** (packet phi-outcome);
**independent reproducer/A7** (viết lại từ spec, không kế thừa verdict
implementer; REFUSED = remediation arc). Mỗi lane: dispatch packet + worktree
đúng registry + handoff `zcode_orch_v3_handoff@1` tại đúng `handoff_path`.
Sau mỗi cohort: A7 terminal fresh-context + two-half close (registry + P-9
ledger + FAMILY_FAILURES/MAP/LESSONS + errata P-19).

## 13. Chuỗi GO và GO phrase (gõ đúng chữ tại đúng gate; P-8: gõ trước = intent chết)

| Gate | Hành động được phép sau GO | GO phrase |
|---|---|---|
| Charter approval | ghi quyết định owner vào OWNER_PACKET (không cần registry row — umbrella là cycle quản trị) | quyết định ghi, không phrase |
| **GO-1 (FX)** | register child + council + data gate + falsifiers + trial freeze — RỒI DỪNG | `GO SRLV FX C1 COUNCIL AND FREEZE` *(chỉ có hiệu lực khi §6 reopener đã có bằng chứng)* |
| **GO-2 (FX)** | scored dev walk-forward dưới heavy lock | `GO SRLV FX C1 SCORED EXECUTION` |
| **GO-3 (FX)** | sealed OOS one-look + replication pass MỘT LẦN | `GO SRLV FX C1 SEALED OOS AND REPLICATION` |
| **GO-1 (CX)** | register + data plane + council + freeze — RỒI DỪNG | `GO SRLV CX C1 COUNCIL AND FREEZE` |
| **GO-2 (CX)** | scored dev walk-forward | `GO SRLV CX C1 SCORED EXECUTION` |
| **GO-3 (CX)** | sealed/prospective OOS one-look + replication | `GO SRLV CX C1 SEALED OOS AND REPLICATION` |

A7 prelaunch đứng giữa GO-1→GO-2 và sau dev trước GO-3 (forex-program §8).
Shadow promotion / nguồn mới / slate change / mở S1 program-wide = owner
decision riêng ngoài chuỗi trên. Prompt 2026-09-26 KHÔNG PHẢI GO nào cả.

## 14. Artifacts & nhãn terminal

Per-child: council reports + handoffs, data-gate verdict per pair (kể cả
BLOCKED rows), falsifier battery (F-0…F-7), freeze artifact (membership,
arm digests, thresholds, seeds, pins — sha256), dry-run, scored cells +
margin-to-fail, seam/kill-law files, DSR (per-period series persisted —
P-11), repro twin, A7 prelaunch + terminal, trial_ledger.jsonl,
CYCLE_VERDICT.md. Nhãn bắt buộc: track (FX/CX), `PAPER_TIER`,
`SINGLE_SOURCE_PANEL` (FX) / `SINGLE_VENUE_PANEL` (CX),
`ANCESTRY_EXPOSED_DEV` (dev rows), `PROXY_NOT_ORDERBOOK` (mọi cơ chế
sweep/zone), `FUNDING_PATH_STRESSED` (CX), `FILL_QUALITY_CLASS_<measured|
declared>`. Terminal vocabulary: umbrella §9 + `NO_CANDIDATE` +
`BACKTEST_CANDIDATE_REPLICATED` (paper-tier bound, 7/7 điều kiện R0–R6 của
forex-program charter). Mọi verdict âm là first-class close.

## 15. Quyết định owner đang chờ (xem OWNER_PACKET_program_open_2026-09-26.md)

1. Phê chuẩn charter SRLV-PROGRAM-V1 + hai child draft.
2. FX frontier: chọn hành động R1/R2/R3 (đều là owner-only: subscription,
   đăng ký nguồn, broker statement) — hoặc xác nhận giữ NO_CANDIDATE.
3. CX: duyệt mở GO-1 sau khi child plan được duyệt (crypto không bị chặn
   frontier, chỉ bị chặn bởi data gate + collisions).
