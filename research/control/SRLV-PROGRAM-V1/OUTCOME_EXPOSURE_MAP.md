# OUTCOME_EXPOSURE_MAP — SRLV-PROGRAM-V1 (Forex + Crypto, theo cặp × nguồn × thời gian)

- Authored: 2026-09-26, bởi Lead từ owner instruction (survey-only; chưa đăng ký
  cycle, chưa score, chưa mở bất kỳ sealed window nào).
- Nguồn đo: `plans/CYCLE_REGISTRY.json`, `research/wayfinder/MAP.md`,
  `research/wayfinder/FAMILY_FAILURES.jsonl`,
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/
  LESSON_TO_GATE_MATRIX.md`, `forex_program/VIABILITY_cohort3_REPORT.md`,
  worktree manifests (chỉ đọc tên file/manifest, KHÔNG đọc nội dung data).
- Quy ức phân loại exposure:
  - `OUTCOME_EXPOSED` — window đã có scored outcome/holdout look từ cycle tổ
    tiên; chỉ được dùng cho ancestry disclosure, engine-parity fixture,
    spread-curve/cost authority (matrix L5, binding).
  - `OUTCOME_EXPOSED_<class>` — exposed cho một class cơ chế nhất định.
  - `SEALED-UNREAD` — window sealed, chưa bị identity nào nhìn; một-look OOS
    cho identity mới qua đủ dev gate, sau GO riêng, membership frozen.
  - `OUTCOME_FREE` — chưa từng có scored outcome; sạch cho dev/transfer.
  - `BLOCKED` — không có data hợp lệ/authority; cặp không được âm thầm thay.

## 1. FOREX — 6 cặp candidate universe

Nguồn duy nhất có authority hiện nay: **Dukascopy public M1 BID/ASK** với
`OWNER_DIRECTIVE_SOURCE_AUTHORIZATION + TCU_RISK_DISCLOSED` (posture EDQ1).
Nguồn độc lập (TrueFX / OANDA v20 practice / Dukascopy written consent) =
**0 bytes**, BLOCKED tới khi owner quyết R2 (EDQ1 packet 2026-09-22).

| Cặp | Nguồn | Window | Phân loại | Vai trò được phép trong SRLV |
|---|---|---|---|---|
| EURUSD | Dukascopy M1 bid/ask | 2021-01..2025-12 (dev) | `OUTCOME_EXPOSED` (EURUSD-OPEN-SEARCH-V1 48 trials; V2 dev; RANGEEXP-SCORED; census 12 họ: GAP, PDHLOC, DOW, ASIAFADE, SESSMA, H1TSMOM, H1DONCH, DAYMOM, RANGEEXP, STOCH, ROUNDNUM, HOURREV) | ancestry disclosure; engine-parity fixture; spread-curve/cost authority. KHÔNG BAO GIỜ evidence mới/OOS |
| EURUSD | Dukascopy M1 bid/ask | 2026-01..2026-06 (holdout) | `OUTCOME_EXPOSED` (V2 fresh holdout, one look, đã tiêu) | như trên — hết vai trò OOS |
| GBPUSD | Dukascopy M1 bid/ask | 2021-01..2026-06 (dev 6 folds 2022-07..2025-06 + holdout 2026-H1 run_count=1) | `OUTCOME_EXPOSED` (FX-MAJORS-SEARCH-V1 96/96; census 12 họ) | như EURUSD |
| USDJPY | Dukascopy M1 bid/ask | 2021-01..2026-06 (như GBPUSD) | `OUTCOME_EXPOSED` (FX-MAJORS 96/96; scale 1e-3 / pip 0.01 probe-proven) | như EURUSD |
| AUDUSD | Dukascopy M1 bid/ask | 2021-01..2025-12 (dev) | `OUTCOME_EXPOSED_range-fade-class` (ERP1-TRACKA-COHORT-1: R-ORIG/R-ANCHOR/R-NEIGH/placebos/baselines scored; PIT seam KILL) | dev cho observable MỚI (qua D2 adjudication); spread-curve/cost authority; ancestry |
| USDCAD | Dukascopy M1 bid/ask | 2021-01..2025-12 (dev) | `OUTCOME_EXPOSED_range-fade-class` (như AUDUSD) | như AUDUSD |
| AUDUSD | Dukascopy M1 bid/ask | **2026-01..2026-06** | **`SEALED-UNREAD`** (A7 terminal C-3; không arm nào của cohort-1/2 nhìn) | one-look OOS cho identity mới qua đủ dev gate, sau GO riêng, membership sha-frozen. **KHÔNG ĐỌC** |
| USDCAD | Dukascopy M1 bid/ask | **2026-01..2026-06** | **`SEALED-UNREAD`** | như AUDUSD |
| USDCHF | — (không corpus ở bất kỳ đâu) | — | `OUTCOME_FREE` nhưng `BLOCKED_DATA_LICENSE` | replication-transfer surface; download chỉ sau data gate + license posture; R4: chỉ có nghĩa sau khi một identity qua dev gates |
| (mọi cặp) | TrueFX tick | — | `BLOCKED` (0 bytes; owner R2) | replication limb nguồn-độc-lập khi mở |
| (mọi cặp) | OANDA v20 practice | — | `BLOCKED` (0 bytes; owner R2) | như TrueFX |
| (mọi cặp) | IBKR IDEALPRO | minTick 0.5 pip đo được 5 cặp (chỉ là fact hình học tick, KHÔNG phải đo executable spread/all-in) | `BLOCKED_BROKER_COST_AUTHORITY` (V2 two-sided NOT_SUBSCRIBED; commission/swap NOT_RUN ⇒ all-in chưa đo) | cost authority khi owner mở subscription + Flex; khi đó all-in được ĐO — có thể xác nhận cao hơn hoặc thấp hơn ước tính |
| EURUSD | TwelveData mid | sample | reconciliation-only (matrix L5) | không bao giờ evidence |

### 1.1 Cost authority hiện có (FX)

- Cost book đo được duy nhất: **Dukascopy session spread curves sha-pinned**
  (EURUSD p50 0.3 pip; GBPUSD 0.8; USDJPY 0.5; AUDUSD conditional crossing
  0.9–1.0; USDCAD 1.1–1.2; stressed RT 3.6/4.4 pips AUD/CA; USDCHF: chưa có).
- Commission/slippage-beyond-spread: `DECLARED_UNMEASURED` — mọi verdict FX
  mang `PAPER_TIER + SINGLE_SOURCE_PANEL + FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`.
- Ngưỡng đã pin (P3-A, frozen): all-in crossing ≤ 0.41 pip @k=2.0; không
  re-derive sau khi có số. minTick 0.5 pip (đo 5 cặp) chỉ là fact hình học
  tick — KHÔNG được suy ra thành executable spread hay all-in cost; executable
  spread đang NOT_SUBSCRIBED, commission/swap NOT_RUN ⇒ all-in thực sự CHƯA
  ĐO. R1 là bước đo; kết quả có thể cao hơn hoặc thấp hơn mọi ước tính hiện có.

## 2. CRYPTO — 4 cặp candidate universe (Binance USDⓈ-M)

Nguồn: Binance Vision keyless archives + fapi (posture PIT_USABLE của các
cycle tổ tiên; license text chưa capture — data gate từng nguồn bắt buộc).
**Không có** order book lịch sử / liquidation tape / OI đa-năm: mọi cơ chế
"liquidity sweep / supply-demand zone" trên klines là PROXY, mang nhãn
`PROXY_NOT_ORDERBOOK`.

| Cặp | Nguồn | Window | Phân loại | Vai trò được phép trong SRLV |
|---|---|---|---|---|
| BTCUSDT | Vision um klines 1h | 2020-01..2026-08 | `OUTCOME_EXPOSED` (BTC-H4 ×4 trên trục giá 2020-2026; PSV1 sleeves; ETH-V1/V2 E1 gate input; CHR3F baselines) | ancestry; fixture; cost/funding authority. Không phải OOS cho các họ đã chết |
| BTCUSDT | catalog 15m LAST | 2024-08..2026-08 | `OUTCOME_EXPOSED` (CHR3F staged + scored trên 2024-08-20..2026-08-21) | ancestry/fixture; verify lại tại GO-1 |
| ETHUSDT | Vision um klines 1h + funding | 2020-01..2026-08 | `OUTCOME_EXPOSED` (ETHUSDT-OPEN-SEARCH-V1 terminal 8 cells; V2 lane B 4 scored cells; ETHBTC ratio G6-killed) | ancestry; fixture; funding authority |
| ETHUSDT | catalog 15m LAST | 2024-08..2026-08 | `ANCESTRY_EXPOSED_RECLK` — cùng lịch sử giá 2024-08..2026-08 đã outcome-exposed ở 1h (V1 terminal, V2 lane B); đổi plane không tạo surface outcome-free | chỉ `ANCESTRY_EXPOSED_DEV` (kill/engineering); KHÔNG phải OOS |
| SOLUSDT | Vision um klines 1h | 2020-09..2026-08 (floor 2020-09-14) | `OUTCOME_EXPOSED_baseline` (chỉ xsect baselines V11/V14/funding-carry; không có search directional riêng) | dev cho identity mới với ancestry disclosure |
| BNBUSDT | Vision um klines 1h | 2020-02..2026-08 (floor 2020-02-10) | `OUTCOME_EXPOSED_baseline` (như SOL) | như SOL |
| (4 cặp) | Vision klines 15m / 1m (chưa stage) | 2020..2026-08 | `ANCESTRY_EXPOSED_RECLK` — CÙNG lịch sử giá đã outcome-exposed ở 1h; đổi timeframe KHÔNG tạo surface outcome-free (re-clock veto Q-3) | chỉ dev dạng `ANCESTRY_EXPOSED_DEV` (kill/engineering, không phải bằng chứng promote); KHÔNG được dùng làm OOS; OOS thật = prospective sau freeze |
| (4 cặp) | funding (fapi + Vision cross-check) | floor fapi 2020-07-18 (SOL 2020-09-13); conflict ⇒ symbol-month EXCLUDED | measured authority (BTC 11.798%/yr = 7.824× hằng số cũ; ETH 7,305 settlements floor-exact) | cost book measured bắt buộc |
| (4 cặp) | bookTicker / aggTrades (granary có sẵn một phần) | TBD | verify coverage tại data gate; thiếu ⇒ BLOCKED | spread/slippage census điều kiện theo giờ fill |
| (mọi cặp) | liquidationSnapshot / OI lịch sử | 404 / lookback ≈41.6h | `BLOCKED_UNCONSTRUCTIBLE` | không dùng làm observable; forced-flow phải là proxy có falsifier |
| (mọi cặp) | order book L2 lịch sử | — | `BLOCKED` (không tồn tại đa-năm PIT) | không được claim order-book liquidity |

### 2.1 Ghi chú va chạm cycle đang sống (binding)

- `ETHUSDT-OPEN-SEARCH-V2` ACTIVE_LIGHT, STOP-1 chờ owner GO, S1
  SEALED, zero scored headline. SRLV-CX KHÔNG được tiêu GO phrase hay surface
  S1 của cycle đó; không re-stage corpus của nó.
- `CRYPTO-HISTORICAL-REPLICATION-3F-V1` ACTIVE_LIGHT đang scored execution
  (BASISLV 8 cells dưới heavy lock). Heavy lock machine-wide: SRLV-CX chỉ
  dispatch khi `locks inspect` = FREE_PROVEN hoặc held by itself.
- `FX-RANGEFADE-2M-SHADOW-V1`, `PROSPECTIVE-SHADOW-V1` (shadow workers nhẹ):
  không đụng; không restart; không sửa dashboard.

## 3. Sealed assets còn lại (toàn chương trình)

| Asset | Trạng thái | Luật tiêu thụ |
|---|---|---|
| S1 (program-wide first holdout, mọi cycle) | `SEALED_UNTOUCHED` | umbrella §5.10: một shot per identity, GO riêng |
| AUDUSD 2026-H1 | `SEALED-UNREAD` | one-look OOS, membership sha-frozen, GO riêng (GO-3) |
| USDCAD 2026-H1 | `SEALED-UNREAD` | như trên; **một cửa sổ transfer = một look cấp chương trình** (matrix L5) |
| Cửa sổ transfer clean cho FX mới (USDCHF…) | outcome-free nhưng data BLOCKED | chỉ mở theo R4 sau khi identity qua dev gates |
| Crypto: 15m/1m planes chưa score + prospective sau freeze | unconsumed/prospective | verify tại GO-1; prospective = OOS thật duy nhất nếu history hết sạch (trackb §4.2 precedent) |

## 4. Hàng rào ancestry trực tiếp lên không gian cơ chế SRLV (đọc trước council)

1. `TRACKA1-M1-RANGEFADE-PIT` + `TRACKA2-C1C2C3-REGATED-RANGEFADE`: range-edge
   / prev-day-band fade + ANY gate (provenance, reclaim, probe-count, vol,
   session) — DEAD; C1/C2/C3 (PROV-ABSORB / RECLAIM-ABSORB / PROBE-DEPLETION)
   = VETO_VARIANT_SAME_FAMILY; "only a mechanism with a NEW payer + new
   information layer (F-0 three tests) can carry a range-adjacent trigger".
2. VIABILITY 12 dead classes (forex): range-edge fade mọi gate; momentum/
   continuation mọi cadence; quote/spread-state gates; quote-layer
   observables; fix-window/clock/calendar; cross-pair lead-lag; event/macro;
   carry/multi-day (BLOCKED no financing band); vol-state làm NGUỒN hướng;
   microstructure quantity/tape (UNCONSTRUCTIBLE trên Dukascopy M1);
   mean-reversion oscillators (FXOS-04 HOLDOUT_FAILURE_NO_RESCUE); new-pair
   transfer (không phải basis).
3. Crypto: EOS1-E1 (BTC-price-state gates cho ETH) + EOS1-E2 (ratio gates,
   kể cả symbol-swap) family-dead; PSV1-BTC_H4-Donchian continuation
   CONTROL_OUTEARNED_ANCHOR; fold-concentration 0.50 (số hiệu G5 ở cycle gốc,
   G8 trong bộ gate SRLV) đo là structurally unpassable cho BTC-long
   2020-2026; 11/11 crypto-ng proposals chết ở rho
   bar 0.20; BTC-BEAR: Confirmation-Lag Front-Run VETOED_FICTIONAL_
   COUNTERPARTY, Mark-Trigger Catch-Down VETOED ×3; V10 M01-AGGRESSOR-
   ABSORPTION-PANEL BLOCKED_PRELAUNCH.
4. Luật F-0 (owner 2026-09-26): "adding an observable is not a new mechanism"
   — skeleton/payer/information tests chạy TRƯỚC rho, TRƯỚC PnL.
