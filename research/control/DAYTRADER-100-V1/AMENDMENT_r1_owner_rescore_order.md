# DAYTRADER-100-V1 — AMENDMENT r1 (owner rescore order)

- recorded_utc: 2026-09-28 (this session)
- authority: owner instruction, verbatim, in-cycle:

> "đây là lệnh của tôi. Chạy toàn bộ ANCESTRY_VETOED và RUNNABLE_COHORT1"

## 1. Phân loại theo §2.5 (owner words are literal authority)

Lệnh trên là MỆNH LỆNH (không phải câu hỏi) và được ghi nhận với ba hệ quả:

1. **Scope authorization**: mở rộng phạm vi cycle từ "census + 1 cohort" thành
   "rescore toàn bộ 55 family ANCESTRY_VETOED + 1 family RUNNABLE_COHORT1" theo đúng
   yêu cầu. Plan §1/§7 ("out of scope: re-score vetoed families") được thay thế bởi
   amendment này — đây chính là "new owner plan" mà ledger-header law yêu cầu cho việc
   re-test một family đã chết.
2. **Ancestry relaxation BY OWNER EXPLICIT INSTRUCTION**: bar rho 0.20 "immovable" có
   tiền lệ owner-relax duy nhất là FOREX-SEARCH-V1 (0.20 → 0.30, disclose mọi result).
   Lệnh này relax mạnh hơn: các family AV được PHÉP re-score mà KHÔNG cần đo decorrelation
   trước. Hệ quả khoa học phải disclose trên TỪNG result row (không có ngoại lệ):
   `ANCESTRY_RELAXED_BY_OWNER_ORDER_2026-09-28` — trial này KHÔNG độc lập với kill của
   tổ tiên; mọi survivor phải qua decorrelation court (rho ≤ 0.20) TRƯỚC khi mang bất kỳ
   nhãn nào mạnh hơn `OWNER_ORDERED_RESCORE_POSITIVE`.
3. **KHÔNG phải GO phrase (P-8)**: câu lệnh không phải phrase đã đăng ký
   `GO DAYTRADER 100 V1 SCORED EXECUTION`, và gate (A7 prelaunch) chưa tồn tại tại thời
   điểm lệnh. Theo tiền lệ FOREX-FREE-V9 (owner GO pre-gate 2026-09-09 = INTENT,
   extinguished-unconsumed), lệnh này được ghi là **intent + scope authority**, không phải
   key-2. Scored cell chỉ chạy sau: G3 freeze → dry-run → A7 prelaunch AUTHORIZED →
   owner gõ phrase đúng nguyên văn tại gate.

## 2. Feasibility split của 56 family được lệnh chạy (đo từ bytes, không suy diễn)

### 2.1 RUNNABLE NOW (substrate in-tree, sha-pinned) — 27 families / 81 arms

Crypto — Binance Vision 1m BTCUSDT+SOLUSDT (2020-09..2026-08), 1h majors, 8h funding,
mark/index (worktrees nguồn: dtp-cx-solusdt-c1, ethusdt-open-search-v2, pws-cx-*):

| family_id | strategy (ma trận #) | substrate |
|---|---|---|
| DT100-C1-FORECASTFUND | #94/RC1 forecast-funding premiumIndex | premiumIndex fetch keyless (PS1 probe PASS; fetch tại staging — nếu fail → NOT_RUN_DATA) |
| DT100-01-ORB | #1 ORB 30' UTC | 1m klines |
| DT100-04-SQUEEZE | #4 VCP/squeeze breakout | 1m klines |
| DT100-16-RSI2 | #16 RSI-2 pullback | 1m klines |
| DT100-20-OVERNIGHTFADE | #20 UTC-hour clock fade | 1m klines |
| DT100-34-WEEKEND | #34 weekend clock | 1m klines |
| DT100-35-FUNDCONTRA | #35 funding z contrarian | 1m + funding 8h |
| DT100-56-PDHLSWEEP | #7/#56 prior-day H/L sweep reversal | 1m klines |
| DT100-60-DELTADIV | #60 klines taker-delta divergence | 1m klines (taker-buy col) |
| DT100-69-FHMOM | #69 first-hour momentum UTC | 1m klines |
| DT100-70-ONRET | #70 overnight-return conditioning | 1m klines |
| DT100-71-RVREGIME | #71 realized-vol regime switch | 1m klines |
| DT100-73-VOLAUTO | #73 vol-conditional autocorr | 1m klines |
| DT100-74-VOLTARGET | #74 vol-targeted TS momentum | 1m klines |
| DT100-75-PAIRMR | #75 SOL/BTC rolling-hedge pair MR | 1h klines ×2 |
| DT100-76-CORRBREAK | #76 majors 1h correlation regime | 1h majors panel |
| DT100-78-LEADLAG | #78 BTC→SOL 1m lead-lag | 1m klines ×2 |
| DT100-79-ETHBTC | #79 ETH/BTC ratio gauge | 1h ETH+BTC |
| DT100-80-TSMOMH | #80 1h TS momentum | 1h klines |
| DT100-83-FAILBRK | #83 failed-breakout reversal | 1m klines |
| DT100-87-FVG | #87 FVG/gap-void fill | 1m klines |

Forex — Dukascopy M1 bid/ask EURUSD+GBPUSD+USDJPY (2021-01-01..2026-09-23), cost bill =
per-bar spread đo từ chính bid/ask (worktrees nguồn: fx-rangefade-2m-shadow-v1,
fx-majors-search-v1):

| family_id | strategy (ma trận #) |
|---|---|
| DT100-07-PDHLSWEEPFX | #7/#56 FX version |
| DT100-09-ASIANRANGE | #9 Tokyo range → London |
| DT100-10-LONDONMOM | #10 London open momentum |
| DT100-13-VWAPMR | #13 VWAP MR |
| DT100-15-BOLLFADE | #15 Bollinger fade |
| DT100-31-JPYFADE | #31 Japan session fade |

### 2.2 ORDERED-BUT-BLOCKED (không có bytes — lệnh không thể tạo ra dữ liệu) — 28 families

Equity/CME/rates/options intraday, on-chain, L2/orderbook, liquidation/OI multi-năm,
multi-venue, news-timestamp PIT: các dòng ma trận #2,3,5,6,8,11,12,14,17-19,21-33,36-55
(trừ đã chạy ở 2.1), 57-59,61-68,77,81-82,84-86,88-93,95-100. Verdict tại scoring phase:
`NOT_RUN_DATA_BLOCKED_UNDER_OWNER_ORDER` — lệnh owner được ghi, thiếu substrate là bằng
chứng đo được (SNI/0-bytes/license, có ngày trong CENSUS_MATRIX_100.md).

## 3. Budget & folds

- budget_max raised 3 → **81** scored cells (27 families × 3 arms; controls = re-evaluations,
  zero cells). Nếu premiumIndex fetch fail → 78 và C1 verdict NOT_RUN_DATA.
- Folds giữ nguyên plan §3.1 (crypto) và §4 (FX) — ngày-tháng explicit, không đổi.

## 4. Disclosure đứng đầu mọi kết quả của cycle này

"Chương trình này re-score theo lệnh owner các family đã từng bị falsify. Nó là một
multiple-testing explosion theo thiết kế; denominate tăng theo từng cell; không survivor
nào trong chương trình này được coi là evidence độc lập cho đến khi qua decorrelation
court với tổ tiên đã chết của nó."
