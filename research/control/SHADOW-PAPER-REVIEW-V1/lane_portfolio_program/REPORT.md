# REPORT — SHADOW-PAPER-REVIEW-V1 / lane_portfolio_program

- Vai trò: review CẤU TRÚC CHƯƠNG TRÌNH shadow paper (không review chi tiết
  từng strategy — 2 lane khác phụ trách).
- Đo tại: root checkout `/Users/hoangminhlong/my-quantitative`, branch `main`,
  HEAD `f0a8e800c47de1800011d20bccd9bcb2cc7e8546` (đo 2026-09-24, = dispatched
  base sha). Read-only: không viết registry/ledger, không heavy job, không
  commit, không ghi ngoài thư mục lane.
- Quy ước bằng chứng: mọi số đều cite path. Không đo được → ghi `NOT_RUN`.
  Các ước lượng thống kê đều ghi rõ công thức + giả định.

---

## TÓM TẮT 5 FINDING CẤU TRÚC LỚN NHẤT

1. **Chương trình 7 sleeve KHÔNG có luật promote/kill/time-stop
   preregistered về mặt thống kê.** Kế hoạch duy nhất có checkpoint là
   PROSPECTIVE-SHADOW-V1 (§7: 7 ngày/13 tuần/26 tuần/52 tuần — chỉ chẩn đoán,
   "no pass/promotion claim"; §13: pass không hồi sinh family, chỉ tạo
   "evidence for an owner decision"; §12 terminal cố ý không có
   `SURVIVOR/PRODUCTION_READY/LIVE_READY`). FX plan và XAUUSD plan: **không
   preregistered** cả promote lẫn kill (chi tiết §1 dưới). Kill duy nhất có
   sẵn là early-stop kỹ thuật (hư dữ liệu, leak, sai kế toán) — không có kill
   hiệu suất (vd "PF < x sau n trades"). Hệ quả: đến 52 tuần chương trình sẽ
   có dải bằng chứng nhưng không có quy tắc nào định trước việc đọc bằng chứng
   đó ra quyết định gì.
2. **Bốn sleeve hiện "vô hạn về mặt thông tin" hoặc dưới ngưỡng power ở tần
   suất hiện tại** (phép gần đúng `SE = σ/√n`, t = (μ/σ)·√n):
   - **BTC4H-BANDRIDGE: tốc độ thông tin = 0 theo cấu trúc** — 57 quyết định,
     0 fill, toàn bộ fail-closed vì guard tiền mặt (nguyên nhân gốc tới
     exception, A7 CONFIRM); mỗi H4 trôi qua không chọn A/B/C là một quan sát
     mất vĩnh viễn (forward-only).
   - **XAUUSD: gần vô hạn** — 75 hàng MARK_TO_MARKET, 0 entry; replay thật
     9 entry intents / 12,337 bar H1 ≈ 6.4 RT/năm → cần per-RT Sharpe ≥ 0.79
     để phát hiện ở 2σ sau 1 năm (thực tế không tồn tại edge bền như vậy);
     s=0.30 cần ~7 năm, s=0.20 ~16 năm.
   - **XAUUSD-card đã bị remove khỏi dashboard chính theo lệnh owner**
     (registry phase XAUUSD-SHADOW-V1) → sleeve này cũng không nằm trong view
     chương trình.
   - **BASISLV: 1/1 sự kiện weekly bị DATA_BLOCKED (0 fill)** — 286-bar hole
     của vendor đã tiêu thụ cả tuần thông tin (fail-closed đúng luật, không
     backfill). Nếu gap lặp lại theo kiểu này, effective event-rate giảm sâu.
   - ILLIQ/BASISLV weekly: 52 quyết định/năm → 2σ chỉ phát hiện được per-week
     Sharpe ≥ 0.277 (≈ Sharpe thường niên ≥ 2.0) — edge lớp lịch sử
     (PF 1.354841 ILLIQ / 1.360047 BASISLV, plan §3) nằm dưới ngưỡng này →
     cửa sổ 52 tuần under-power cho cả hai.
   - Chỉ FX (~350 RT/năm đo từ holdout lịch sử) và XSECT (daily, mép power)
     có tần suất đủ để tạo bằng chứng phân biệt trong 1 năm.
3. **Sleeve ILLIQ chạy prospective trên một cơ chế vừa bị đo là FALSIFIED
   (gate) và INVERTED (S0R 2024-08..2025-08).** ILLIQ-REG-V1 TERMINAL
   FALSIFIED (registry phase; gated ANCHOR net −0.345789 vs bar ≥ −0.2947
   FAIL); CRYPTO-HISTORICAL-REPLICATION-3F-V1 phase: "S0R ANCHOR −0.5631 /
   INV +0.5459 — mechanism INVERTED in 2024-08..2025-08". Shadow vẫn hợp lệ
   về luật (tracking đúng anchor form frozen, không retune) nhưng prior hiện
   tại âm mạnh, và chương trình không có luật nào preregistered cho trường
   hợp shadow xác nhận nghịch đảo → owner decision.
4. **7 sleeve = 6 tài khoản ảo × $100k = $600k (không phải $700k), equal
   notional ≠ equal risk, không có risk aggregation chủ động.** FX 2 pair
   chung MỘT tài khoản $100k (PLAN_fx_rangefade §3 "equity on $100,000 seed";
   OWNER_REPORT "1 TK $100k chung"). BANDRIDGE long-only BTC w=1.0 (amendment
   A1) có vol thường niên cao hơn hàng chục lần so với các sleeve long-short
   gross ≤ 1.0. Combined view chỉ là read-only equal-capital; G6 ghi rõ
   "combined exposure is measured but cannot alter isolated sleeves" — đo
   được nhưng không có cap beta-crypto tổng hay vol-target nào.
5. **Cost book "conservative" về fee tier nhưng OPTIMISTIC về slippage ở
   đúng những sleeve mỏng nhất.** Fee 0.05%/side là DECLARED (không đo được
   — `UNAVAILABLE_FAIL_CLOSED_FALLBACK_DECLARED`, cost_regime_manifest.json);
   slippage cố định 1 tick/fill là quá nhẹ cho chính các tên illiquid mà
   ILLIQ long và cho breakout BANDRIDGE; FX fill ở giá opposite của feed
   TrueFX indicative (top-of-book, mỏng hơn spread giao dịch được). Kèm
   không khớp văn bản luật: amendment A1 ghi BANDRIDGE "6 bps/side" nhưng
   production guard tính fee 0.0005 (5 bps) + 1 tick.

---

## 1. (Bước A) Luật gate/promotion/kill trong 3 plan — trích chính xác

### 1.1 PROSPECTIVE-SHADOW-V1 — `plans/PLAN_prospective_shadow_v1.md`

- **Không có tiêu chí promotion sang scored/forward preregistered.** Bằng
  chứng trích chữ:
  - §7 checkpoints: "13 weeks — early diagnostic; **no pass/promotion
    claim**"; "26 weeks — interim evidence; **still no promotion**";
    "52 weeks — first complete shadow evaluation over three chronological
    forward folds".
  - §13: "Passing these observations **does not resurrect a rejected
    family**. It creates **evidence for an owner decision** about whether to
    write a separate confirmatory plan. Failing them closes the observation
    without rescue."
  - §12 terminal outcomes: "There is deliberately **no `SURVIVOR`,
    `PRODUCTION_READY` or `LIVE_READY` terminal outcome** in this plan."
- **Không có kill hiệu suất.** §7: "Early stopping is allowed for **data
  corruption, leakage, accounting mismatch, identity drift, risk breach or
  broken controls**. Early profit is never a reason to stop and promote." —
  danh sách này thuần kỹ thuật/an toàn, không có ngưỡng PnL/PF/DD nào.
- **Kết luận: promotion và kill hiệu suất đều KHÔNG preregistered** (chỉ có
  quy trình hậu nghiệm: A7 tại 13/26/52 tuần → owner decision → plan mới).

### 1.2 FX-RANGEFADE-2M-SHADOW-V1 — `plans/PLAN_fx_rangefade_2m_shadow_v1.md`

- §0: "go_phrase: none registered (no scored surface at open; scored cells
  from the shadow journal **follow the program's later governance**)" —
  governance "sau này" **chưa tồn tại trong văn bản nào** (kiểm tra: không có
  mục promote/kill trong toàn plan).
- §4 boundaries: "any parameter change = new plan + re-registration" — chỉ có
  luật đóng băng, không có luật kết thúc.
- **Kết luận: không preregistered** (cả promote lẫn kill; không time-stop —
  journal accrues vô hạn định).

### 1.3 XAUUSD-SHADOW-V1 — `plans/PLAN_xauusd_shadow_v1.md`

- §1: "NOT a scored/research cycle ... shadow output is **OBSERVATION
  ONLY**"; §4: "**No Sharpe/PF publication gating is claimed**"; §6 phase E:
  "forward shadow (**indefinite**; weekly health checkpoints; WAITING_DATA if
  feed down — never FAIL for missing coverage)".
- §6b: "No terminal outcome is promised; honest states include WAITING_DATA,
  BLOCKED_SOURCE and SHADOW_RUNNING".
- **Kết luận: không preregistered**; thời gian chạy vô hạn định (indefinite)
  và entry cấu trúc hiếm (đo ở §3).

### 1.4 Ý nghĩa cấu trúc

Chương trình hiện là "máy thu thập bằng chứng" không có "máy ra quyết định"
định trước. Đây không phải vi phạm (các plan cố ý né promotion để tránh
outcome-bias), nhưng tới 2027-09 (checkpoint 52 tuần của PSV1) mọi quyết định
promote/kill sẽ được viết SAU khi đã thấy số → rơi đúng cái bẫy
outcome-exposed mà chương trình tự tránh (PSV1 §14 đã ghi 3 anchor là
"forbidden outcome-exposed ancestry"). Vùng hợp lý duy nhất để preregister
luật quyết định là **TRƯỚC khi dữ liệu tiếp tục tích lũy** (ngay bây giờ).

---

## 2. (Bước B) Bối cảnh reliability + registry + ILLIQ

- **Độ bền công cụ đã được kiểm toán độc lập:** A7 fresh-context VERDICT
  `CONFIRM` (`research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/
  A7-RELIABILITY-AUDIT-2026-09-24.md:224`): 56 fill toàn chương trình
  (CARRY 48 + ILLIQ 8) khớp đúng luật chi phí đóng băng, 0 event_id trùng,
  append-only nguyên vẹn, arithmetic dashboard 1,983/2,033 điểm khớp tuyệt
  đối, fail-closed hiển thị trung thực. GATES.md tổng gate PARTIAL (đúng —
  còn chờ thị trường/owner).
- **ILLIQ-REG-V1** (`plans/CYCLE_REGISTRY.json`, entry TERMINAL): "FALSIFIED
  (phase-1 falsification, S0R 2024-08-22..2025-08-21). Gated ANCHOR baseline
  net −0.345789 vs bar ≥ −0.2947 FAIL (margin −0.0511)"; "family
  A8-V11-ILLIQ-AMIHUD back to NOT_PROSPECTIVE diagnostics".
- **CRYPTO-HISTORICAL-REPLICATION-3F-V1** (registry phase): "ILLIQ SCORED
  COMPLETE: 4/4 cells (Y2024P ANCHOR +0.1377/INV −0.1501 — direction HELD;
  **S0R ANCHOR −0.5631/INV +0.5459 — mechanism INVERTED in
  2024-08..2025-08**)".
- **Ý nghĩa cho sleeve ILLIQ-AMIHUD-28D-W prospective:** sleeve chạy đúng
  luật frozen (long illiquid / short liquid — plan §3.1) và việc tiếp tục
  track anchor form là hợp lệ; nhưng (i) prior từ 2 cycle mới nhất là cơ chế
  đã đảo chiều trên cửa sổ gần nhất, (ii) nếu shadow 52 tuần tới xác nhận
  nghịch đảo (kết quả có prior cao), chương trình không có luật định trước
  điều gì xảy ra với sleeve — chỉ còn owner decision hậu nghiệm. Chi phí cơ
  hội: 1/4 sức mạnh crypto shadow gắn vào anchor có prior âm mạnh nhất.
- **ILLIQ-LOSS-MECH-V1** PLANNED_NOT_STARTED (phase: 8 cell NOT_RUN do
  heavy-lock, chờ lock) — điều tra cơ chế loss chưa chạy, nên hiện chưa có
  giải thích nhân quả nào cho nghịch đảo; không nên đổi hướng sleeve trước
  khi điều tra này có kết quả (đổi = new identity theo PSV1 §4).

---

## 3. (Bước C) Thống kê sức mạnh quyết định — đo được + ước lượng

### 3.1 Số đo được từ ledger (byte, read-only)

Nguồn: `.worktrees/prospective-shadow-v1/integration/results/
prospective_shadow_v1/ledgers/*.jsonl` (tương đương byte-count heartbeat mà
A7 đã verify; root checkout không có tree này — ledgers nằm ở worktree
integration).

| Sleeve | Events | Fills | Trạng thái đo được |
|---|---|---|---|
| XSECT-FUND-CARRY-7D | 10 (daily 09-15..09-24) | 48 | equity 100,000 → **100,428.15** (+428.15, MTM); OWNER_REPORT ghi realized +3,936.27 (thành phần realized, khác cơ sở với equity MTM) |
| ILLIQ-AMIHUD-28D-W | 1 (weekly 09-21) | 8 | equity RUNNING 99,477.90 @08:55Z (OWNER_REPORT §1) |
| BASISLV-PREMFADE-28D | 1 (weekly 09-21) | 0 | DATA_BLOCKED — 286 bar thiếu, event đã tiêu thụ, không backfill |
| BTC4H-BANDRIDGE | 57 (H4) | **0** | 56 quyết định đầu UNAVAILABLE_FAIL_CLOSED (guard tiền mặt); 09-24T08:00Z OK dạng no-trade |
| EURUSD RANGEFADE-2M | H1 chạy từ 09-24 | 0 | 0 tín hiệu prospective (hợp lệ, mới 1 ngày) |
| GBPUSD RANGEFADE-2M | như trên | 0 | như trên |
| XAUUSD | 75 hàng MARK_TO_MARKET | 0 entry | `.worktrees/xauusd-shadow-v1/integration/results/xauusd_shadow_v1/ledger.jsonl` |

XSECT chi phí book được 10 ngày: fee 246.43 + slippage 56.40 + funding 4.60
(cộng từ 10 event — ledger trích ở §3.1) = **~30.3 bps/10 ngày ≈ ~11%/năm
cost drag** trên baseline 100k — so với edge lịch sử +20.6%/năm (plan §3.3)
thì cost book hiện hành ăn gần một nửa edge lớp lịch sử.

### 3.2 Công thức + giả định

- Gần đúng chuẩn: `SE(mean per-decision return) = σ/√n`;
  `t = (μ/σ)·√n = s·√n` với `s = μ/σ` là per-decision Sharpe; cần
  `n = (z/s)²` quan sát để đạt t = z. Dùng z = 1 (mức ~1σ, gợi ý) và z = 2
  (~95% hai phía, phân biệt edge thật vs 0).
- **Min detectable per-decision Sharpe sau n quan sát = z/√n.**
- Giả định: quan sát độc lập, per-decision return ~ Gauss, μ/σ của edge
  tương lai xấp xỉ bằng kỳ vọng tham chiếu (lịch sử/holdout). Đơn vị quan
  sát là QUYẾT ĐỊNH (hoặc round trip), không phải bar.

### 3.3 Bảng sức mạnh theo sleeve

Tần suất tham chiếu:
- XSECT: 365 quyết định/năm (daily, plan §3.3).
- ILLIQ/BASISLV: 52/năm (weekly Monday, plan §3.1/§3.2) — giảm nếu gap dữ
  liệu lặp (BASISLV hiện 0/1 sự kiện thành công).
- BANDRIDGE: ~18 RT/năm (S0: 123 entries / 2020-01→2026-09 ≈ 81 tháng,
  `.worktrees/btc-h4-band-risk-v1/integration/research/control/
  btc_h4_band_risk_v1/freezes/shadow_group_s0.json` `n_trades: 123`) —
  **hiện tại = 0 fill/số thông tin 0 theo cấu trúc**.
- FX 2 pair: ~350 RT/năm (holdout C3 EURUSD: 87 trades / 2,802 bar H1 ≈ 6
  tháng — `.worktrees/fx-majors-search-v1/integration/research/control/
  EURUSD-OPEN-SEARCH-V2/outcomes/holdout_check_v2.json`; ×2 pair ×12 tháng).
- XAUUSD: ~6.4 RT/năm (9 entry intents / 12,337 bar H1 ≈ 1.4 năm — registry
  phase XAUUSD-SHADOW-V1: "12,337-bar real replay ... 9 historical entry
  intents"; giả định replay window đại diện — chỉ là xấp xỉ).

Min detectable per-decision Sharpe (z/√n):

| Sleeve | n/năm | 1σ | 2σ |
|---|---|---|---|
| XSECT daily | 365 | 0.052 | 0.105 |
| FX 2-pair | ~350 | 0.053 | 0.107 |
| ILLIQ/BASISLV weekly | 52 | 0.139 | 0.277 |
| BANDRIDGE (nếu fill, ~18 RT) | 18 | 0.236 | 0.471 |
| XAUUSD (~6.4 RT) | 6.4 | 0.395 | **0.791** |

Số năm để đạt t = 2 với edge thật s (n = (2/s)², theo n/năm):

| s (per-decision Sharpe) | XSECT | FX | ILLIQ/BASISLV | BANDRIDGE | XAUUSD |
|---|---|---|---|---|---|
| 0.05 | 4.4y | 4.6y | 30.8y | 88.9y | 250y |
| 0.10 | 1.1y | 1.1y | 7.7y | 22.2y | 62.5y |
| 0.20 | 0.3y | 0.3y | 1.9y | 5.6y | 15.6y |
| 0.30 | 0.1y | 0.1y | 0.9y | 2.5y | 6.9y |

Đối chiếu với edge lớp lịch sử của từng sleeve:
- XSECT: +20.6%/năm, MDD 8.8% (plan §3.3) ⇒ Sharpe thường niên ~1 ⇒ per-day
  s ≈ 0.05 ⇒ 2σ cần ~4 năm, 1σ ~1.1 năm → **cửa sổ 52 tuần chỉ vừa đủ ở 1σ**.
  (10 ngày đo được của chúng tôi: μ $42.82/ngày, σ $916.78 — s=0.047, khớp
  quy mô này, nhưng n=10 không có ý nghĩa chân lý.)
- ILLIQ/BASISLV: PF lịch sử 1.35/1.36 (plan §3.1/§3.2) ⇒ per-week s ước
  ~0.1–0.3 (σ tuần NOT_RUN từ ledger — chỉ 1 event) ⇒ **52 tuần dưới power ở
  2σ; chỉ edge đầu lớp s≈0.3 mới đạt ~0.9 năm**.
- FX C3 holdout: +274 pips/87 RT, hit 0.5977, PF 1.31 (holdout_check_v2.json)
  ⇒ per-RT s ≈ 0.1–0.15 (ước lượng; σ per-RT NOT_RUN vì chưa có series fill
  prospective) ⇒ t ≈ 2.1–2.8/năm cho 2 pair → **sleeve có mật độ thông tin
  cao nhất chương trình**.
- BANDRIDGE: S0 POSTHOC fold-concentrated (measured: F3 +641,776 trên tổng
  +972,763; F2 −15,081 — shadow_group_s0.json `1.0|measured`) ⇒ không dùng
  được làm prior edge; tần suất thật ~18 RT/năm ⇒ dù fill bình thường,
  **2σ/năm đòi per-RT s ≥ 0.47 — rất hiếm edge bền đạt**.
- XAUUSD: **vô hạn về mặt thông tin ở tần suất hiện tại** (bảng trên);
  rarity là property của frozen spec (registry phase: "RARITY IS A PROPERTY
  OF THE FROZEN SPEC, disclosed to the owner").

### 3.4 Kết luận C

1. Quy luật tổng quát: ở bất kỳ cadence nào, cửa sổ 1 năm chỉ phân biệt được
   edge có **Sharpe thường niên ≥ ~2.0 ở 2σ (≈1.0 ở 1σ)** — vì mọi sleeve có
   n/năm khác nhau nên cùng một quy luật `2/√(số năm)`.
2. Sleeve xếp theo mật độ thông tin hiện tại: **FX > XSECT > ILLIQ ≈ BASISLV
   > BANDRIDGE (0, bị khóa owner packet) > XAUUSD (~0.16 RT/tháng)**.
3. Bốn sleeve vô hạn/thấp-cực-độ về thông tin: XAUUSD (rarity cấu trúc),
   BANDRIDGE (fail-closed chờ owner), BASISLV (gap tiêu thụ sự kiện),
   FX-hiện-tại (mới 1 ngày, nhưng mật độ tiềm năng cao — không phải vô hạn
   nếu tiếp tục chạy).
4. Checkpoint theo TUẦN LỊCH (13/26/52 tuần) của PSV1 bất công với sleeve
   hiếm: nên chuyển sang checkpoint theo n-quyết-định-tích-lũy (xem §7-G1).

---

## 4. (Bước D) Cấu trúc portfolio

### 4.1 Đo được

- **Không phải 7×$100k.** Cấu trúc vốn thực: 4 tài khoản crypto cách ly
  $100k (plan PSV1 §5 + amendment A1 "own virtual capital $100,000") +
  **1 tài khoản FX $100k chung cho 2 pair** (PLAN_fx §3 "equity on
  $100,000 seed, per-pair sleeve"; OWNER_REPORT §2 Phorec "1 TK $100k
  chung") + 1 tài khoản XAUUSD $100k (plan §2) = **6 tài khoản × $100k =
  $600k paper**, 7 sleeve chiến lược.
- **Equal notional ≠ equal risk:** BANDRIDGE khi band ON + breakout giữ
  long BTC w=1.0 (amendment A1; caps `max_abs_weight: 1.0` — A7 §2a) —
  vol thường niên BTC ~40–60% ⇒ 1σ năm ≈ $40–60k/tài khoản; trong khi
  XSECT gross cap 0.80/net cap 0.10/weight cap 0.20 (plan §3.3), BASISLV
  gross 1.0 long-short tercile (plan §3.2), ILLIQ dollar-neutral
  BTC-beta-neutral (plan §3.1) — các book trung hòa có vol thấp hơn
  hàng chục lần; FX 1.5 lot/pair (≈$150k notional/pair, vol EURUSD ~0.5%/ngày
  ⇒ ~0.75% TK/ngày). Không sleeve nào được vol-target.
- **Chồng lấn nhân tố (đánh giá kinh tế):**
  - 4/7 sleeve crypto cùng dựa giá/funding Binance: BANDRIDGE = long BTC
    thuần (directional); XSECT = carry harvest long-short alt (gross 0.8);
    BASISLV = basis-premium fade long-short (gross 1.0); ILLIQ = long-short
    liquidity (beta-neutral theo luật nhưng tail-beta crypto vẫn dương khi
    stress). Ba book long-short cùng chạy tín hiệu 15m trên cùng universe
    Binance ⇒ tương quan cross-section cao khi "thị trường xoay tên".
  - XSECT và BANDRIDGE đều hưởng funding/bull-regime: XSECT nhận funding
    credit khi short tên funding cao (thường là memo-bull), BANDRIDGE long
    trend bull ⇒ chồng lấn regime "crypto bull" giữa 2 sleeve danh nghĩa
    khác họ.
  - FX: EURUSD + GBPUSD cùng họ USD-legs, same-strategy same-side: khi tín
    hiệu cùng chiều USD, 3 lot gross rủi ro USD-một-phía gấp đôi per-pair;
    plan không có cap same-side aggregate (chỉ cap 1.5 lot/pair). Correlation
    EURUSD-GBPUSD thực tế cao (cùngEUR/GBP vs USD) — đây là 2 sleeve của 1
    nhân tố, không phải 2 quan sát độc lập.
  - XAUUSD: uncorrelated với cả 2 khối trên (điểm cộng đa dạng hóa) nhưng
    0 activity (§3) ⇒ đa dạng hóa giấy.
- **Không có risk aggregation chủ động:** PSV1 G6: "combined exposure is
  measured but **cannot alter isolated sleeves**" (plan §10-G6); combined
  view chỉ hiển thị (§5). Đúng thiết kế shadow, nhưng nghĩa là chương trình
  không học được gì về rủi ro tổ hợp thực (drawdown tổng, beta tổng) —
  dashboard có contributions từng family (A7 §4: per-family contributions
  khớp 1,983 điểm) nhưng **chưa có Sharpe per sleeve** (grep dashboard:
  không có metric sharpe — chỉ có trong research/ legacy), và XAUUSD card
  đã bị remove khỏi dashboard chính (registry phase XAUUSD — lệnh owner) ⇒
  **view chương trình đang thiếu 1/3 cycle** (crypto dashboard + Phorec có,
  XAUUSD chỉ còn overlay riêng 127.0.0.1:8790).

### 4.2 Khung đề xuất (ý kiến, không thi hành)

1. **Vol-target per sleeve tại thời điểm promote** (không đổi shadow đang
   chạy): scale notional sao cho vol đóng góp đồng đều; tại shadow chỉ cần
   ĐO (hiển thị vol realized per sleeve trên dashboard) — ENGINEERING_ALLOWABLE
   (hiển thị read-only).
2. **Cap aggregate crypto beta / crypto gross cho pha sau-shadow**: khi có
   sleeve nào được promote, portfolio thật cần cap tổng (vd crypto net beta
   ≤ x·NAV tổng) — OWNER_DECISION_REQUIRED (thay đổi không gian vốn; tiền lệ
   shared-equity đã bị owner rút nên phải là quyết định owner).
3. **FX: đo và hiển thị exposure USD-net tổng 2 pair** (read-only) thay vì
   chỉ per-pair — ENGINEERING_ALLOWABLE.
4. **Contribution per sleeve**: bổ sung per-sleeve Sharpe + %PnL tích lũy +
   drawdown riêng trên dashboard crypto (số liệu đã có trong marks bytes) —
   ENGINEERING_ALLOWABLE.

---

## 5. (Bước E) Phụ thuộc dữ liệu

### 5.1 Bản đồ phụ thuộc (đo được)

| Plane | Nguồn | Sleeve phụ thuộc | Rủi ro đơn-nguồn |
|---|---|---|---|
| Crypto marks/funding/bars | Binance public REST (`premiumIndex` @5min valuation — GATES §G2; `fundingRate`, klines 15m; exchangeInfo — cost_regime_manifest.json:76-88) | **cả 4 crypto sleeve** | 1 vendor — API keyless bị rate-limit/thay đổi schema ⇒ 4 sleeve chết cùng lúc |
| FX live marks | TrueFX indicative, poll 15s (PLAN_fx §2) | **cả 2 FX sleeve** | mất TrueFX = 2 sleeve chết cùng lúc; indicative ≠ spread giao dịch được (§6-F) |
| FX seed | Dukascopy M1 (PLAN_fx §2) | 2 FX sleeve | chỉ seed, rủi ro thấp |
| XAUUSD | EODHD intraday, key sẵn có (plan §3) | 1 sleeve | 1 key entitlement; hết quota = sleeve WAITING_DATA |
| Gateway | LIVE-DATA-GATEWAY-V1 (registry ACTIVE_LIGHT) | — | **chưa cutover**: GO `REGISTERED_NOT_CONSUMED`; G3 canary PASS (registry phase; plan §14-G3) nhưng sleeve vẫn đọc nguồn riêng — gateway đang là sidecar, chưa phải redundancy thực |

### 5.2 Bài học đã đo

- **BASISLV 286-bar gap**: hole vendor từ 2026-09-18T00:15Z ⇒ toàn bộ sự kiện
  weekly 09-21 thành DATA_BLOCKED, event_id tiêu thụ, KHÔNG backfill
  (GATES §G2; ledger BASISLV event 0). Fail-closed đúng luật forward-only,
  nhưng về thông tin: **1 hole ~vài giờ của vendor xóa 1 tuần quan sát**
  (≈1/52 năm của sleeve). Nguồn đã lành (probe 13/13 symbol, 0 gap —
  GATES §G2) nhưng luật không có cơ chế "gap nhỏ trong tuần → cảnh báo sớm
  trước mốc quyết định".
- **FX daemon chết 4 thế hệ crash-loop** trước khi bị phát hiện (GATES §G4;
  A7 §1) — độ bền worker đã sửa (f8bb2b73) nhưng cho thấy mọi sleeve chỉ
  mạnh bằng 1 daemon đơn-nhánh.

### 5.3 Đề xuất tầng dự phòng (ý kiến)

1. **Hoàn tất cutover LIVE-DATA-GATEWAY-V1** (GO đang chờ) rồi cho sleeve
   crypto dùng gateway làm canonical marks — biến sidecar thành redundancy
   thật — OWNER_DECISION_REQUIRED (GO là của owner; plan gateway §14-STOP).
2. **Gap-telemetry sớm cho weekly sleeve**: heartbeat cảnh báo khi cửa sổ
   28 ngày của BASISLV/ILLIQ có hole trước mốc Monday 00:00Z (để kịp fetch
   lại trong tuần, không phải tiêu thụ event) — ENGINEERING_ALLOWABLE
   (thêm telemetry, không đổi luật fill).
3. **Nguồn FX thứ hai** (feed dự phòng keyless khác TrueFX) — cần owner
   quyết định nguồn mới — OWNER_DECISION_REQUIRED (nguồn dữ liệu là quyền
   owner theo tiền lệ TCU_RISK_DISCLOSED).
4. Giữ nguyên fail-closed làm luật nền — mọi phương án fallback KHÔNG được
   imputed data (đúng luật hiện hành PSV1 §8, plan XAUUSD §2 fills).

---

## 6. (Bước F) Cost realism

### 6.1 Cost book hiện hành (cite file:line)

- **4 crypto sleeve**: `CURRENT_CONSERVATIVE_COST` primary
  (`research/control/prospective_shadow_v1/e/shadow_worker.py:505-519`
  `cost_books_for()`; constants `FEE_RATE_CURRENT = 0.0005`,
  `SLIPPAGE_TICKS_CURRENT = 1.0` tại `shadow_worker.py:180-181`); áp dụng:
  `executor.py:321-326` (BookCostParams), fill/slippage/fee:
  `accounting.py:354-356` (`fill_price = ref ± 1 tick adverse; fee =
  qty·ref·fee_rate`), guard tiền mặt `accounting.py:417-423` (nguyên nhân
  fail-closed BANDRIDGE, A7 §2b xác nhận). ILLIQ lineage book = 1.5×fee +
  2 ticks (`shadow_worker.py:184-185`), các family khác LINEAGE mirror
  current (shadow_worker.py:511-519, disclosed).
- **Freeze manifest**: `research/control/prospective_shadow_v1/data_cost/
  cost_regime_manifest.json:39-48` — taker 0.05%/maker 0.02%,
  `evidence_class: UNAVAILABLE_FAIL_CLOSED_FALLBACK_DECLARED` (trang fee
  không truy được — fee là **DECLARED, không đo**), `measured_bytes: null`;
  slippage cố định 1 tick/fill (dòng 101-108); funding **measured** từng
  settlement 8h từ `fundingRate` (dòng 109-124); immutability có dated-boundary
  law (dòng 125-128). Digest `ab524d0e...` (dòng 131).
- **FX**: fill tại quote opposite của TrueFX tại thời điểm fill, không swap,
  flat 20:00 UTC (PLAN_fx §1-§2) — spread "đo tại fill" nhưng từ feed
  **indicative** (top-of-book mỏng hơn spread giao dịch được).
- **XAUUSD**: 4.0 bps round-trip hằng số, tự nhãn
  "UNMEASURED-CONSERVATIVE; components UNMEASURED" (PLAN_xauusd §2 costs).
- **BANDRIDGE**: amendment A1 (plan PSV1 cuối file) ghi luật "6 bps/side";
  production guard đang tính fee 0.0005 (5 bps) + 1 tick (A7 §2b: needed
  ≈ 100,050.02). **Không khớp văn bản luật vs sách hiện hành** (6 bps vs
  5 bps + tick) — cần reconciliation khi owner chọn A/B/C.

### 6.2 Đối chiếu 2 bài học đo được

- **BTC-H4-EDGE-SEARCH-V1** (registry TERMINAL phase): "measured BTC funding
  **11.798%/yr = 7.824× the frozen constant** — TREND_LF −44% under measured
  law". Bài học: hằng số funding frozen là rủi ro bậc nhất. **PSV1 đã hấp
  thụ bài học này đúng chỗ**: funding của shadow là measured per settlement
  (manifest dòng 109-124) — điểm mạnh.
- **FOREX-SEARCH-V1** (registry TERMINAL phase): "financed expectancy
  −9.40/−9.86/−9.56 bps per round trip at **stress 2.0**, price-only already
  −6.00/−6.46/−6.15" — margin cost FX mỏng, stress ×2 lật dấu. RANGEFADE-2M
  là dòng C3 khác (holdout vẫn dương ở k=2.0: +218.4 pips —
  holdout_check_v2.json) nhưng bài học giữ nguyên: **edge FX tồn tại hay
  không phụ thuộc gần như hoàn toàn vào spread thực** — mà shadow đang fill
  trên indicative feed ⇒ bằng chứng promote của FX sẽ lạc quan hơn khả thi.

### 6.3 Đánh giá "conservative còn đúng nghĩa?"

| Thành phần | Trạng thái | Đánh giá |
|---|---|---|
| Taker fee 0.05% | DECLARED (không đo được, manifest dòng 40-48) | Conservative-đúng về tier, nhưng là giả định không bằng chứng |
| Slippage 1 tick cố định | frozen | **OPTIMISTIC** cho ILLIQ (chính sleeve này long các tên illiquid — 1 tick không mô tả depth impact) và cho BANDRIDGE breakout (market order khi breakout). Không "conservative" đúng nghĩa tại 2 sleeve quan trọng nhất cần kiểm chứng |
| Funding | measured per settlement | Đã hấp thụ bài học 7.8×; đúng nghĩa |
| FX spread | measured-at-fill trên indicative | Lạc quan hệ thống; cần book stress ×2 (tiền lệ FOREX-SEARCH) |
| XAUUSD 4 bps RT | tự nhãn UNMEASURED | Trung thực về trạng thái; sleeve 0 activity nên chưa tác động |
| Cost drag thực tế đo được | XSECT ~30.3 bps/10 ngày ≈ ~11%/năm (§3.1) | Cost book + daily churn ăn ~1/2 edge lịch sử (+20.6%/năm) — bằng chứng 52 tuần của XSECT sẽ khó phân biệt edge thật vs chi phí |

**Kết luận F**: tên "CURRENT_CONSERVATIVE_COST" conservative về fee tier và
funding, nhưng slippage/spread là mắt xích yếu — đặc biệt vì nó bất đối xứng
giữa các sleeve (thiệt hại thông tin tập trung vào ILLIQ/BANDRIDGE/FX).
Đề xuất: thêm book diagnostic thứ ba (stress-slippage: k×spread/hoặc k×ATR
theo nhóm thanh khoản; FX stress ×2) — ADDITIVE, không đụng primary book
(hợp lệ theo dated-boundary law: book mới ≠ rewrite) — ENGINEERING_ALLOWABLE;
nếu muốn đưa vào primary phải là amendment + new frozen hash —
AMENDMENT_REQUIRED.

---

## 7. (Bước G) Ý kiến cải thiện chương trình

Mỗi ý: cơ sở → nhãn → rủi ro.

### Nhóm 1 — Luật thống kê quyết định (quan trọng nhất)

- **G1.1 Preregister bộ luật promote/kill/time-stop cho TOÀN chương trình
  shadow TRƯỚC khi dữ liệu tiếp tục tích lũy.** Cơ sở: §1 (không preregistered)
  + §3 (52 tuần chỉ đủ power cho Sharpe ≥ 2 ở 2σ) — không luật thì tới hạn
  sẽ quyết định hậu nghiệm trên dữ liệu đã thấy (outcome-exposed). Hình thức
  gợi ý: SPRT hai phía hoặc ngưỡng Bayes-factor trên per-decision return,
  với **time-stop theo số quyết định tích lũy** (n) thay vì tuần lịch:
  ví dụ kill khi posterior P(μ>0) < 10% sau n ≥ n_min; promote khi P(μ>μ_min)
  > 90%. — **OWNER_DECISION_REQUIRED** (đổi governance; các plan hiện hành
  cấm sửa sau khi thấy kết quả nên phải làm NGAY). Rủi ro nếu không làm:
  quyết định 2027 bị outcome-bias; sleeve hiếm chạy vô hạn định không tiêu
  chí kết thúc.
- **G1.2 Quyết định trạng thái sleeve ILLIQ** (tiếp tục frozen-anchor /
  hạ ưu tiên / chờ ILLIQ-LOSS-MECH-V1 có kết quả cơ chế rồi xem lại). Cơ sở:
  §2 (FALSIFIED + S0R INVERTED). — **OWNER_DECISION_REQUIRED**. Rủi ro: giữ
  nguyên = 1/4 crypto shadow gắn prior âm mạnh; đổi hướng = vi phạm frozen
  law (phải new identity + new plan).
- **G1.3 Chốt packet A/B/C của BANDRIDGE (sizing + fill-law) trước phiên H4
  có breakout đầu tiên.** Cơ sở: 57 quyết định 0 fill — info = 0 theo cấu
  trúc (§3.3); packet đã mở
  (`research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/
  OWNER_DECISION_PACKET_bandridge_sizing_and_fill_law.md`). —
  **OWNER_DECISION_REQUIRED** (đã pending). Rủi ro chậm: mỗi tuần trôi là
  ~0.35 RT/18 RT-năm mất vĩnh viễn; và khi breakout nổ giữa chừng, quyết định
  sẽ fail-closed tiếp (OWNER_REPORT §5).
- **G1.4 Checkpoint theo n-quyết-định thay vì tuần lịch** cho các kỳ đánh
  giá tương lai (13/26/52 tuần → n=45/90/180 quyết định XAUUSD là không bao
  giờ tới — phải theo đơn vị thông tin). — **AMENDMENT_REQUIRED** (sửa
  checkpoint law của PSV1-class plans) hoặc áp dụng cho chương trình kế
  tiếp. Rủi ro: không đổi thì 52 tuần sẽ "kết thúc" các sleeve hiếm mà không
  hề có enough n.

### Nhóm 2 — Cấu trúc portfolio/risk

- **G2.1 Hiển thị (read-only) vol realized + Sharpe + %PnL per sleeve và
  USD-net exposure tổng của FX trên dashboard.** Cơ sở: §4.1 (không có
  Sharpe metric; XAUUSD out of view). — **ENGINEERING_ALLOWABLE**. Rủi ro:
  thấp (chỉ đọc marks có sẵn).
- **G2.2 Khung phân bổ theo rủi cho pha sau-shadow: vol-target + cap
  aggregate crypto beta + quy tắc gộp FX same-factor thành 1 đơn vị rủi ro.**
  Cơ sở: §4.1 (equal-notional lệch risk hàng chục lần; 4/7 sleeve crypto;
  2 FX pair 1 nhân tố). — **OWNER_DECISION_REQUIRED** (thay đổi không gian
  vốn/risk aggregation bị cấm ở tầng sleeve hiện tại). Rủi ro: áp dụng sớm
  lên shadow sẽ phá thiết kế cách ly (PSV1 §5: sleeve không được tiêu nhau
  của risk allowance).
- **G2.3 Đưa XAUUSD trở lại một view chương trình hợp nhất** (hoặc một
  "program page" đọc 3 tree riêng). Cơ sở: §4.1 — view owner hiện thiếu
  1/3 cycle. — **ENGINEERING_ALLOWABLE** (view-only; card trước đây bị
  remove theo lệnh owner nên việc trả lại cần xác nhận owner — nếu owner
  giữ nguyên lệnh cũ thì nhãn chuyển thành OWNER_DECISION_REQUIRED).

### Nhóm 3 — Độ bền data plane

- **G3.1 Cutover gateway (G3.1 = chờ GO) + harden single-vendor.** Cơ sở:
  §5.1-§5.2 (4 sleeve crypto trên 1 vendor; 2 FX sleeve trên 1 feed;
  gateway chưa phải redundancy). — Cutover: **OWNER_DECISION_REQUIRED**;
  telemetry gap-tuần (cảnh báo hole trong cửa sổ 28 ngày trước mốc Monday)
  và heartbeat daemon-liveness alarm: **ENGINEERING_ALLOWABLE**. Rủi ro:
  không làm thì lặp lại mất mát kiểu BASISLV (1 hole = 1 tuần info).
- **G3.2 Luật "gap tài" cho weekly sleeve**: nếu hole được vá TRƯỚC mốc
  quyết định (nguồn hồi phục như probe 09-24), sự kiện vẫn chạy — hiện luật
  chỉ fail-closed tại mốc; không backfill sau mốc (giữ nguyên). Cần amendment
  nhỏ về "pre-decision re-fetch trong tuần". — **AMENDMENT_REQUIRED** (đụng
  PIT/fill law). Rủi ro: nếu không viết lại rõ, dễ bị hiểu là backfill —
  phải freeze thời điểm re-fetch hợp lệ ≤ decision cutoff.

### Nhóm 4 — Cost book

- **G4.1 Thêm `STRESS_COST` book thứ ba** (slippage = k×ATR-15m hoặc theo
  bucket thanh khoản cho ILLIQ/BANDRIDGE; FX spread ×2). Cơ sở: §6.3. —
  **ENGINEERING_ALLOWABLE** (additive book, primary không đổi). Rủi ro: nếu
  vô tình ghi đè primary → vi phạm immutability (manifest dòng 125-128).
- **G4.2 Reconcile 6 bps/side (amendment A1) vs 5 bps + 1 tick (production
  guard) cho BANDRIDGE** trong cùng packet A/B/C. — **AMENDMENT_REQUIRED**
  (văn bản luật không khớp code đang chạy). Rủi ro: promote-sau-này sẽ đọc
  cost nào không rõ.
- **G4.3 Đo thay vì khai báo fee taker** khi trang fee truy được lại (đặt
  dated cost-regime boundary mới theo luật). — **ENGINEERING_ALLOWABLE**
  (đúng protocol immutability). Rủi ro: thấp.

### Nhóm 5 — Vệ sinh đo lường

- **G5.1 BANDRIDGE fail-closed là "chi phí của chọn A (chậm)"**: fail-closed
  trung thực nhưng mỗi H4 khóa là info=0; tổng chi phí chương trình của việc
  chờ owner packet là 57/57 quyết định không fill (§3.1). Ghi nhận chính
  thức vào ledger-level reporting: "thông tin mất do pending-owner" tách
  khỏi "không có tín hiệu". — **ENGINEERING_ALLOWABLE** (nhãn hiển thị).
- **G5.2 Fill-timing BANDRIDGE (docstring "next H4 open" vs first completed
  15m bar) phải chốt TRƯỚC fill đầu tiên** (đã recorded-not-fixed theo lệnh
  owner — a8062b1a; GATES §G3). Sau fill đầu tiên, đổi luật = đụng bằng chứng
  prospective. — **OWNER_DECISION_REQUIRED** (cùng packet). Rủi ro nếu trễ:
  toàn bộ RT của sleeve gắn mốc fill gây tranh cãi.
- **G5.3 Tách "realized" vs "equity MTM" trong mọi con số trình bày owner**
  (OWNER_REPORT +3,936.27 realized vs equity +428.15 MTM — §3.1): cùng một
  sleeve, hai cơ sở. Đề xuất dashboard quy ước in cả hai với nhãn rõ. —
  **ENGINEERING_ALLOWABLE**. Rủi ro: không tách thì owner có thể đọc nhầm
  realized thành tổng.

---

## 8. Những gì lane này KHÔNG đo được (NOT_RUN)

- Per-trade σ của ILLIQ/BASISLV/FX/XAUUSD/BANDRIDGE: **NOT_RUN** (0–1 sự
  kiện fill per sleeve; chỉ XSECT có series 10 ngày).
- Sharpe thường niên lịch sử chính xác từng family (chỉ có PF/MDD/net trong
  plan §3 — không đủ để tính σ per-decision): **NOT_RUN** (ngoài phạm vi
  read-only nhẹ; là phạm vi 2 lane còn lại).
- Thống kê trên valuation_marks đầy đủ 2,033 điểm: A7 đã làm arithmetic
  verification (cite §2); lane này không lặp lại mà chỉ cite.
- Tần suất tín hiệu FX prospective: **NOT_RUN** — mới 1 ngày chạy (ước lượng
  ~350 RT/năm lấy từ holdout lịch sử, đã ghi giả định ở §3.3).

---

## 9. Kết luận một câu

Chương trình shadow hiện **thu thập bằng chứng tốt và trung thực
(fail-closed đúng mọi nơi đã đo) nhưng chưa có máy ra quyết định
preregistered, đang đốt thời gian quan sát ở 4/7 sleeve có mật độ thông tin
bằng 0 hoặc gần 0, và chạy equal-notional trên một cấu trúc nhân tố mà 4/7
sleeve là cùng crypto + 2/7 là cùng nhân tố USD** — ba hạng mục sửa có giá
trị nhất: (1) preregister luật promote/kill/time-stop theo n-quyết-định
NGAY, (2) chốt packet BANDRIDGE + trạng thái ILLIQ, (3) stress-cost book +
redundancy data plane.

— lane_portfolio_program, SHADOW-PAPER-REVIEW-V1, 2026-09-24.
