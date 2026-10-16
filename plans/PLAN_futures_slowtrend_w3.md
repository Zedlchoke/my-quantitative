# PLAN — FUTURES-SLOWTREND-W3 (registered; prelaunch; STOP tại owner run/GO gate)

> Trạng thái: REGISTERED prelaunch cycle. Wave W3 của chương trình
> FUTURES-SLOWTREND (parent: FUTURES-SLOWTREND-PREP-V1, snapshot
> `prep/futures-slowtrend-prep-20261016` @ `494421c6`). **Prelaunch cycle:
> KHÔNG chạy forward-outcome/PnL trên dữ liệu thật trong prelaunch này.**
> Việc chạy 24 scored descriptive cells chỉ diễn ra sau owner GO typed tại
> gate riêng (P-8), phrase `GO FUTURES-SLOWTREND-W3 SCORED EVALUATION`
> (đăng ký, CHƯA consume). Prelaunch = freeze + implementation + synthetic
> dry-run + independent prelaunch audit.
>
> Authority: AUTH_W3.md (`research/control/FUTURES-SLOWTREND-PREP-V1/`) —
> owner directive verbatim 2026-10-16. Trục chính: "Trend có cải thiện
> lợi nhuận–rủi ro sau chi phí so với exposure đơn giản ở mức rủi ro tương
> đương không, hay chỉ tái tạo equity beta?"

## 1. Identity & phạm vi

- cycle_id: `FUTURES-SLOWTREND-W3`; asset: `futures`; branch
  `orca/futures-slowtrend-w3-integration`; worktree
  `.worktrees/futures-slowtrend-w3/integration` (base = PREP head 494421c6).
- ES primary; NQ replication khai báo trước — MỘT cụm, không cộng n, không
  dùng NQ cứu ES.
- Cửa sổ dữ liệu: series 2013-01→2022-12-31 (warmup feed 2013; decisions
  2014-01→2022-12); seal 2023+/S1 không đụng; 6A zero-read; FX outcome cấm
  (6E/6B/6J không vào).
- **Historical development đã expose** (FIRSTPASS/census/prescored cùng cửa
  sổ): W3 KHÔNG được gọi là untouched confirmation; mọi báo cáo mang nhãn
  `S0_EXPOSED_DEVELOPMENT`.
- Không thêm lookback/threshold/model/horizon. Không thêm universe.

## 2. Five frozen identities (operative definitions — từ `research/slowtrend/signals.py` @ prep 7b0f160d, KHÔNG suy từ tên)

| ID | Định nghĩa operative | Tham số |
|---|---|---|
| TD-M-L60 | `momentum_sign(close, lookback=60)`: sign(close_t/close_{t-60} − 1) | L=60 |
| TD-M-L120 | `momentum_sign(close, lookback=120)` | L=120 |
| TD-A-M50 | `ma_position(close, window=50)`: +1 nếu close>MA50 và MA50 tăng; −1 nếu close<MA50 và MA50 giảm; else 0 | M=50 |
| TD-A-M100 | `ma_position(close, window=100)` | M=100 |
| TD-D-N20 | `donchian_state(high, low, close, channel=20)`: close_t > max(high_{t-20..t-1}) → +1; < min(low) → −1; else giữ state trước | N=20 |

Decision law (L2): signal tại phiên t−1 → state áp dụng phiên t (decision sau
completed session, không fill tại close đã dùng tính signal). State ∈
{LONG, SHORT, FLAT}. Vol-target sizing toggle (B3-arm) là CÙNG identity,
không phải identity mới.

## 3. Windows & cells (R5-style: một arm × một window = một cell; mọi metrics/strata trong cell đó)

Windows (4): `FULL` 2014-01→2022-12; `E1` 2014–2016; `E2` 2017–2019; `E3`
2020–2022 (trùng era census; chỉ cắt cửa sổ báo cáo, không refit).

- **20 identity cells** = 5 identities × 4 windows. Mỗi cell chứa HAI arm:
  `RAW` (1 contract research representation) và `VOLTGT` (vol-target daily
  sizing — mọi trade rebalance được đếm), cùng bộ metrics.
- **4 baseline cells** = B1 constant-exposure × 4 windows (B1 vol-matched:
  scale để realized vol ≈ vol của VOLTGT arm trong cùng window — công thức
  trong BASELINE_AND_GATE_SPEC §3).
- B0 no-trade = mốc 0 chi phí, không cell. B2 static-trend = chính các
  identity (RAW arm) — không cell riêng, không baseline trùng.
- **Scored budget: {used: 0, max: 24}**. TRAIN-like fits: không có (không
  fitting trong W3). Reproduction recompute không tốn cell (không nhìn số
  mới). Failure/retry của một cell không mở slot mới (cellID bất biến,
  attempts ghi ledger).

## 4. Return / roll / execution contract (tóm tắt — chi tiết RETURN_ROLL_EXECUTION_SPEC)

- Chuỗi giá: per-contract 1m databento (digest pin PREP); daily aggregate
  theo luật census (Globex tdate ts+6h NY; dominant-contract OHLCV); roll law
  chấm điểm: **PIT_ROLL** (active(t) = dominant(t−1); forced roll đếm tường
  minh — census đo: ES 0, NQ 1 forced). DOM (full-session volume) chỉ dùng
  đối chiếu độ nhạy, không phải luật chấm.
- PnL trên hợp đồng THỰC: excess return close-to-close của contract đang
  nắm; KHÔNG dùng adjusted level tính return. Roll diễn ra tại biên quyết
  định (đóng contract cũ + mở contract mới tại close(r−1) + slippage) → +
  1 round-trip cost mỗi roll. Excess return ≠ total return: collateral
  interest KHÔNG mô hình (khai báo); không log giá vô định nghĩa.
- Chi phí, evidence class (khóa TRƯỚC outcome):
  - Commission: SOURCED (artifact 10SYMS cost notes, timestamp 2026-10-02:
    ES all-in doc $2.24/side; NQ theo cùng nguồn).
  - Spread: MODELED (ES 1.0 tick = $12.5; NQ 6.5 tick = $32.5 — số đo
    10SYMS; micro MES/MNQ NOT_MEASURED → loại khỏi W3 PnL).
  - Slippage: MODELED 0.25 tick base; STRESS scenario ×2 trên spread+
    slippage. Scenario khóa: `BASE`, `STRESS` — không thêm sau khi nhìn.
- Integer position: RAW = 1 contract khi state ≠ FLAT. VOLTGT = target vol
  10%/năm, size_i = min(cap 3.0, target/realized_vol_i) × 1 contract, làm
  tròn XUỐNG integer, floor 0 (NO_TRADE khi size < 1); mọi thay đổi size là
  1 trade rebalance đếm cost. Signal churn không được dùng thay execution
  turnover (hai số báo cáo riêng).
- Missing sessions/gaps: phiên thiếu → position giữ, PnL 0 ngày đó (không
  nội suy giá), gap>10 ngày → cell mang cờ `GAP_RISK_UNMODELED`; stale
  signal: state tuổi > 250 phiên không bị reset (law cố định).

## 5. Baselines, primary contrast, multiplicity (chi tiết BASELINE_AND_GATE_SPEC)

- Primary contrast (mỗi identity, ES): **net excess return/vol (risk-matched)
  của arm VOLTGT − B1 vol-matched**, SAME window, cùng cost scenario.
- ES là primary; NQ replication: bắt buộc CÙNG hướng dấu (không độc lập).
- Multiplicity: 5 identities → hiệu chỉnh Bonferroni α = 0.05/5 = 0.01 cho
  CI mỗi identity; selection law: KHÔNG chọn best identity; cả 5 đều báo
  cáo; overall PASS ⇒ ≥2/5 identities đạt primary ở mức đã hiệu chỉnh VÀ NQ
  cùng hướng VÀ K-DRIFT/K-COST sạch; ngược lại FAIL / NO_ELIGIBLE_IDENTITY /
  UNTRADEABLE_CAPITAL.
- **MATERIALITY: PENDING_OWNER_PIN** — 3 lựa chọn kỹ thuật trình owner tại
  gate (BASELINE_AND_GATE_SPEC §5); controller không tự chốt.

## 6. Gates & terminal law (khóa trước)

- K-DRIFT: CI của primary contrast chứa 0 toàn bộ window ⇒ identity chết
  (drift-only).
- K-COST: net ≤ 0 ở cả BASE và STRESS ⇒ COST_DEAD (không phụ thuộc thống
  kê primary).
- Concentration: một era đóng góp >70% net PnL dương ⇒ cờ CONCENTRATED
  (không auto-kill, báo cáo bắt buộc).
- Sample floor: episodes < 20 trong window ⇒ cell `NOT_EVALUABLE` (vẫn tốn
  cell, outcome ghi NOT_EVALUABLE).
- Negative scientific verdict (REJECT/NO_ELIGIBLE) tách biệt data/
  implementation failure (BLOCKED/NOT_RUN_*).
- Không nới gate sau khi thấy kết quả. Mọi cell observed được đếm kể cả
  publication fail (P-9).

## 7. Implementation & prelaunch (đang làm trong cycle này)

- Runner `research/slowtrend_w3/run_w3.py` trên frozen core; synthetic tests
  phủ: decision lag, daily sizing, roll PIT, costs, missing data, long/short
  transitions, integer sizing, gaps, risk-matched baseline, no-lookahead,
  ledger/retry/failure/finalization, sealed-file refusal.
- Dry-run synthetic end-to-end non-vacuous (có nhánh NOT_EVALUABLE + refusal
  + no-GO), KHÔNG dùng historical forward outcomes.
- Independent prelaunch verifier fresh-context audit-only ⇒ AUTHORIZED/REFUSED.
- EXACT_RUN_PACKET pin: panel digest, split hashes, driver sha, registry
  head, lock state, GO phrase (đăng ký, chưa consume).

## 8. Denominators & accounting

- 24 scored cells (khóa). Observed = mọi cell driver ghi outcome (kể cả
  NOT_EVALUABLE). Published = cells vào report owner. Mỗi compute failure =
  attempt row trong trial ledger, không mở cell.
- Baseline evaluations: 4 (B1×window). Symbol/fold/scenario: 2 symbols ×
  4 windows × 5 identities (+2 scenarios cost trong cùng cell — scenario
  là strata của cell, không phải cell mới).
- Registry budget CAS sau publish: used = số cell đã ghi outcome.

## 9. Stop conditions prelaunch

A7 verifier REFUSED · drift gate fail · lock HELD (NOT_RUN_RESOURCE_CONFLICT)
· registry head mismatch · bất kỳ forward-outcome byte thật nào bị đọc trước
GO ⇒ dừng, trình owner. KHÔNG typed GO; KHÔNG viết GO_RECORDED; không push/
merge; không đụng lane/cycle khác.
