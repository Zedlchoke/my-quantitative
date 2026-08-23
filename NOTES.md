# GHI CHÚ DỰ ÁN — my-quantitative

> File này tổng hợp toàn bộ những gì đã làm và kế hoạch sắp tới.
> **Cập nhật lần cuối:** 2026-08-21 — Nautilus 1.230.0; universe Binance,
> transfer test 6 altcoin, shared-capital portfolio và TradFi gate ghi tại §13.

---

## 1. Hệ thống là gì

Bot giao dịch định lượng futures trên **NautilusTrader 1.230.0** (Python 3.12).

**Giả định chuẩn (đã chuẩn hoá):**


| Mục            | Giá trị                                       |
| -------------- | --------------------------------------------- |
| Sàn / sản phẩm | Binance **USD-M perpetual**                   |
| Mã mặc định    | `BTCUSDT-PERP`, `ETHUSDT-PERP` (multi-symbol) |
| Chế độ vị thế  | **one-way / netting** (`oms_type: NETTING`)   |
| Môi trường     | **Testnet / Demo — không tiền thật**          |
| Guard          | LIVE execution bị chặn; LIVE public data signal-only được phép |
| Khung dữ liệu  | 15 phút (`15-MINUTE-LAST-EXTERNAL`)           |


**USD-M ↔ COIN-M** là 1 nút config: đổi `market.account_type` → `COIN_FUTURES`
(+ `symbols`/`base_currency`).

---



## 2. Kiến trúc đã build

```
main.py                      CLI: download / backtest / live
strategy_base.py             base chung: risk, order, daily limits, shutdown
strategy.py                  EMA-ATR trend following
strategy_mean_reversion.py   Bollinger + RSI + VHF + Wyckoff gate/directional
strategy_regime_switch.py    VHF chọn trend vs mean-reversion
strategy_breakout.py         Donchian + ADX breakout (markup-only research)
regime.py                    ADX, VHF filter, HTF EMA200 tracker
regime_wyckoff.py            Wyckoff daily classifier + phase bias helpers
strategy_factory.py          build strategy theo strategy_type
config/
  settings.py                typed settings + YAML loader (+ BreakoutSettings)
  research.yaml              research EMA-ATR (default)
  research_mean_reversion_eth.yaml
  research_mean_reversion_eth_directional.yaml   MR + Wyckoff directional (PASS)
  research_breakout_eth.yaml
  live_eth_mean_reversion.yaml
  wyckoff_policy.yaml        hand-crafted phase → strategy/risk
  live.yaml                  live (Testnet/Demo)
research/
  optimize.py                grid-search optimizer (song song)
  oos_validate.py            hold-out OOS check (60d mặc định)
  regime_analysis.py         fold × ETH return × range metrics
  wyckoff_analysis.py        MR PnL theo Wyckoff phase
  wyckoff_markup_compare.py  EMA long vs MR trên markup days
  mr_directional_wf.py       WF baseline vs directional bias
  breakout_wf.py             WF breakout markup-only
  acceptance.py              meets_acceptance criteria
risk/
  limits.py                  RiskLimits + DailyRiskTracker + position sizing
```

**Cấu trúc phí/slippage trong backtest:**

- Phí: `maker_taker` (tier-0: maker 0.02%, taker 0.05%) hoặc `fixed`.
- Slippage: `one_tick_slippage` / `probabilistic` / `best_price`.

**Quản trị rủi ro (dùng chung cho research + live):**

- Vị thế = `min(risk_per_trade / ATR_stop_distance, max_notional / price)`
- Daily loss, max trades/day, cooldown sau lỗ — theo ngày UTC.

---



## 3. Ba strategy


| strategy_type    | Ý tưởng                                                          | Mạnh           | Yếu                   |
| ---------------- | ---------------------------------------------------------------- | -------------- | --------------------- |
| `ema_atr`        | EMA crossover + trend EMA 200 + ATR trailing stop                | trend mạnh     | cưa khi đi ngang      |
| `mean_reversion` | chạm Bollinger + RSI, range = VHF+ADX+volume, Wyckoff gate | đi ngang, transition | thua bear grind dài |
| `regime_switch`  | cùng bộ lọc range chọn trend vs mean-reversion           | bù cả 2 chế độ       | filter vẫn có thể trễ |
| `breakout`       | Donchian + ADX + volume; markup Wyckoff only (research)  | —                    | **WF FAIL** trên ETH |


---



## 4. Phát hiện quan trọng (bài học)



### 4.1 Win rate cao ≠ lợi nhuận

Mean-reversion win rate **55.6%** nhưng vẫn **lỗ ~4 USDT** vì:

```
Avg winner = +0.67 USDT
Avg loser  = -1.00 USDT
reward:risk = 0.67  (< 1)
expectancy = 0.556×0.67 − 0.444×1.00 = -0.073 USDT/lệnh
```

→ **Thắng nhỏ, thua lớn.** Tiêu chí đánh giá phải là **expectancy + profit
factor**, không phải win rate.

### 4.2 "Siết stop" làm tệ hơn (đã chứng minh bằng optimizer)

Kết quả grid-search 180 ngày × 2 mã:

```
stop=2.0, TP=2.5, vhf=0.25  → expectancy +0.183, PF 1.12   (tốt nhất)
stop=0.75 / 1.0 (siết)      → đều âm                       (tệ)
```

→ Stop **rộng (2.0) + TP cao (2.5)** thắng; siết stop bị quét nhiều hơn.
Điều này ngược với đề xuất "siết stop" ban đầu — optimizer đã sửa lại đúng.

### 4.3 Regime-switch chưa tự động tốt hơn

Tất cả combo regime-switch đều expectancy âm trên 180 ngày → VHF đơn lẻ chưa
đủ để chọn regime chính xác. Cần cải thiện bộ lọc (thêm ADX/volume) hoặc bỏ.

---



## 5. Dữ liệu

- Testnet Binance catalog hiện có **~70,079 bar ETH 15m** (2024-08-20 → 2026-08-20, ~2 năm).
- BTC + ETH đã tải nhiều giai đoạn; research ETH-focused dùng catalog `./catalog`.
- Tải thêm: `python main.py download --config config/research_mean_reversion_eth.yaml`
- Download **append** bar mới; trùng interval → skip (`non-disjoint` handled in `data/download.py`).
- **Không cần live 24/7** để validate: tải bar định kỳ + `oos_validate` = forward check đủ cho giai đoạn 1–2 tháng.

---



## 6. Kết quả hiện tại (để so sánh sau)



### 30 ngày (backtest đơn)


| Strategy                            | BTCUSDT PnL | Win rate |
| ----------------------------------- | ----------- | -------- |
| ema_atr                             | -3.73       | 34.5%    |
| mean_reversion (cũ: revert-to-mean) | -3.93       | 55.6%    |
| mean_reversion (TP 1.5R + stop 1.0) | -7.53       | ~44%     |




### Optimizer 180 ngày (2 mã, xếp theo expectancy)


| stop | TP  | vhf_max | trades | expectancy | PF   | positive_cells |
| ---- | --- | ------- | ------ | ---------- | ---- | -------------- |
| 2.0  | 2.5 | 0.25    | 259    | **+0.183** | 1.12 | 1/2            |
| 2.0  | 2.0 | 0.25    | 264    | +0.103     | 1.07 | 1/2            |
| 2.0  | 1.5 | 0.25    | 280    | +0.064     | 1.04 | 1/2            |


> ⚠️ `positive_cells 1/2` = chỉ 1 trong 2 mã dương → chưa vững, cần walk-forward.

---



## 7. Kế hoạch sắp tới



### Bước 1 — Walk-forward nhanh ✅ ĐÃ LÀM (261s, 288 backtest, 3 fold × 2 mã)

```bash
python -m research.optimize --config config/research_mean_reversion.yaml \
    --grid quick --folds 3 --min-trades 15
```

**Kết quả top combo** `stop=2.0 / TP=2.5 / vhf=0.25` **— chi tiết theo mã × fold:**


| Mã      | F0 (cũ nhất)     | F1                | F2 (mới nhất)     | Nhận xét           |
| ------- | ---------------- | ----------------- | ----------------- | ------------------ |
| BTCUSDT | +0.273 (PF 1.22) | **-0.189** (0.90) | **-0.201** (0.81) | chỉ thắng 1/3 fold |
| ETHUSDT | +0.591 (1.32)    | +0.403 (1.30)     | +0.302 (1.15)     | **dương 3/3 fold** |


**KẾT LUẬN BƯỚC 1:**

- Edge mean-reversion nằm ở **ETHUSDT** (ổn định 3/3 fold, PF 1.15–1.32).
- **BTCUSDT không vững** — chỉ thắng fold đầu, 2 fold sau âm.
- → **KHÔNG promote làm default chung.** Phải tách theo mã: dùng cho ETH,
hoặc cần thêm bằng chứng riêng cho BTC.



### Bước 2 — Mở rộng dữ liệu 12 tháng ✅ ĐÃ LÀM (35,039 bar/mã, 6 fold × 61 ngày)

Tải 365 ngày BTC + ETH, walk-forward 6 fold cho ETH (top-3 combo):

`stop=2.0 / TP=2.5 / vhf=0.25` **theo fold (ETHUSDT):**


| Fold     | Expectancy    | PF             | Win rate | n   |
| -------- | ------------- | -------------- | -------- | --- |
| F0       | +2.103        | 2.71           | 0.53     | 34  |
| F1       | **-0.889**    | 0.64           | 0.35     | 46  |
| F2       | **-1.145**    | 0.55           | 0.32     | 47  |
| F3       | +0.666        | 1.36           | 0.39     | 36  |
| F4       | +0.414        | 1.30           | 0.49     | 49  |
| F5       | +0.323        | 1.17           | 0.48     | 48  |
| **Tổng** | **4/6 dương** | avg exp +0.141 |          |     |


**KẾT LUẬN BƯỚC 2 — ETH cũng KHÔNG vững tuyệt đối:**

- 4/6 fold dương, nhưng có **2 fold liên tiếp âm nặng (F1, F2)** ở giữa giai đoạn.
- Trên 365 ngày, mean-reversion chỉ "ăn" ở một số giai đoạn, thua liên tục ~4 tháng
ở giữa. Đây đúng là đặc tính **phụ thuộc regime**: khi thị trường vào trend,
mean-reversion thua, và VHF 0.25 không lọc hết.
- → **Edge yếu, không đạt chuẩn "vững".** KHÔNG nên chạy live chỉ dựa vào mean-reversion.

**So sánh nhanh 3 combo (ETH, 6 fold):**


| stop | TP  | positive folds | avg exp |
| ---- | --- | -------------- | ------- |
| 2.0  | 2.5 | 4/6            | +0.141  |
| 2.0  | 2.0 | 4/6            | +0.183  |
| 1.5  | 2.5 | 3/6            | +0.206  |


Không combo nào đạt ≥ 5/6 fold dương → không có bộ tham số nào đủ vững để promote.

### Bước 3 — Tiêu chí "vững" (acceptance criteria)

Một bộ tham số chỉ được promote làm default khi **đồng thời**:

1. Expectancy dương trên **≥ 2/3 số fold**.
2. Dương trên **cả 2 mã** (hoặc tách riêng config theo mã nếu chỉ 1 mã vững).
3. **Profit factor > 1.1** ở đa số fold.
4. Lặp lại được trên **khung dữ liệu khác** (out-of-sample thật).



### Bước 4 — Hành động theo kết quả

- **Pass** → đặt vào config làm default (có thể tách `symbols: [ETHUSDT]` riêng).
- **Fail** → giữ default cũ, quay lại mở rộng grid / thêm bộ lọc regime (ADX, volume).

**Quyết định (walk-forward 3 fold, 365 ngày, filter VHF+ADX+volume): FAIL**


| Run                     | Accept pass | Best expectancy | Ghi chú                         |
| ----------------------- | ----------- | --------------- | ------------------------------- |
| MR quick (`mr_wf3_adx`) | 0/32        | -0.057          | ETH hơi dương, BTC âm cả 3 fold |
| EMA quick (`ema_wf3`)   | 0/12        | -0.157          | Mỗi mã thắng 1 fold khác nhau   |


**Đã làm theo nhánh Fail:**

1. **Giữ default** `ema_atr` — `config/research.yaml`, `config/live.yaml` không đổi
  `strategy_type`; không promote mean-reversion.
2. **Mở rộng grid** — chạy `--grid full --folds 3` (output `results/optimize/mr_full_wf3`,
  `ema_full_wf3`).
3. **Tách research theo mã** — thêm `config/research_mean_reversion_eth.yaml`
  (chỉ ETHUSDT) để kiểm tra nhánh "1 mã vững" mà **không** đụng default chung.
4. **Không live** mean-reversion cho đến khi `meets_acceptance=true`.

```bash
# Bước 4 — mở rộng grid (đang / sẽ chạy)
python -m research.optimize --config config/research_mean_reversion.yaml --grid full --folds 3 --workers 2 --output-dir results/optimize/mr_full_wf3 --no-resume
python -m research.optimize --config config/research.yaml --grid full --folds 3 --workers 2 --output-dir results/optimize/ema_full_wf3 --no-resume
python -m research.optimize --config config/research_mean_reversion_eth.yaml --grid full --folds 3 --workers 2 --output-dir results/optimize/mr_eth_full_wf3 --no-resume
```



### Bước 5 — Cải thiện đã làm (theo checklist bên dưới)

- [x] Thêm ADX + volume vào regime filter (không còn VHF đơn lẻ). Range chỉ khi
  ```
  `VHF ≤ vhf_max` **và** `ADX ≤ adx_max` **và** volume không spike.
  ```
- [x] Optimizer cho `ema_atr` (grid fast/slow EMA + ATR stop; bỏ combo `fast ≥ slow`).
- [x] Sharpe + max drawdown trên bảng xếp hạng optimizer.
- [x] Cache `results/optimize/cells*.jsonl` để resume (`--no-resume` để chạy lại).
- [x] Cột `meets_acceptance` đúng tiêu chí bước 3; **không** tự sửa YAML default.
- [x] Stop/TP mean-reversion đóng băng ATR lúc vào lệnh (1R thật, không trôi theo ATR bar sau).
- [x] Daily cooldown reset theo ngày UTC (cùng daily loss / max trades).
- [x] Unit tests: `python -m unittest discover -s tests`

Chưa promote bất kỳ combo mean-reversion nào. Chạy lại walk-forward với filter mới:

```bash
python -m research.optimize --config config/research_mean_reversion.yaml --grid quick --folds 3 --workers 2
python -m research.optimize --config config/research.yaml --grid quick --folds 3
```

Chỉ đổi default khi `meets_acceptance=true` **và** còn một cửa sổ OOS thật (tiêu chí 4).

### Bước 6 — ETH MR validated ✅ (quick grid + OOS + directional WF)

Walk-forward ETH-only quick grid (`results/optimize/_speed_test`): **4/32 pass acceptance**.
Top combo: stop **1.5**, TP **2.0**, vhf **0.25**, adx **20**, vol **1.8**.

**Phân tích regime 2 năm** (`python -m research.regime_analysis --folds 12`):

| Giai đoạn MR xấu (fold) | ETH return | Trạng thái thị trường |
| ----------------------- | ---------- | --------------------- |
| F2 (Dec'24–Feb'25) | **-26%** | Bear grind |
| F3 (Feb'25–Apr'25) | **-46%** | Crash liên tục |
| F7–F8 (Oct'25–Feb'26) | **-30%, -33%** | Bear (trùng bước 2 F1–F2) |

| Giai đoạn MR tốt | ETH return | Trạng thái |
| ---------------- | ---------- | ---------- |
| F1, F4, F5 (2024–2025 bull) | +45% → +62% | Bull mạnh |
| F9, F11 (2026) | +17%, +31% | Sideways / bull |

**Kết luận regime:**

- MR thua khi ETH **rơi mạnh liên tục** (−26% đến −46%/fold), không phải khi ADX cao.
- Filter VHF+ADX **không phân biệt** được bear crash vs range (range_ok ~10–15% ở cả good lẫn bad).
- **HTF EMA200 (1h)** chặn long dưới EMA → giảm “bắt dao rơi” trong bear.

**Risk management đã thêm (demo ETH):**

- `risk_pct_per_trade: 1.0` — 1% equity/lệnh (cap `max_risk_per_trade_usdt: 50`)
- `max_daily_loss_pct: 2.0` — max 2% equity/ngày
- `circuit_breaker_losses: 4` → pause 96 bar (24h) sau 4 lệnh thua liên tiếp
- `htf_trend_filter: true` — no long below 1h EMA200, no short above

**File config:**

- `config/research_mean_reversion_eth.yaml` — research + OOS
- `config/live_eth_mean_reversion.yaml` — demo Testnet
- `config/research_download_eth_prior_year.yaml` — tải thêm năm trước
- `research/regime_analysis.py` — phân tích fold/regime

**Quy trình demo:**

```bash
python -m research.regime_analysis --folds 12
python -m research.oos_validate --config config/research_mean_reversion_eth.yaml
python main.py live --config config/live_eth_mean_reversion.yaml
```

**Catalog mở rộng:** ~70,079 bar ETH (2024-08-20 → 2026-08-20, ~2 năm).

### Bước 7 — Wyckoff regime (accumulation / markup / distribution / markdown)

Classifier cố định trên **daily** bars (`regime_wyckoff.py`, ngưỡng **không tune ETH**):

```bash
python -m research.wyckoff_analysis
```

**Thời gian trong phase (672 ngày labeled):**

| Phase | % thời gian | ETH daily return | MR PnL (entry phase) |
| ----- | ----------- | ---------------- | -------------------- |
| accumulation | 5% | -0.19%/day | **-11.1** (5 lệnh, WR 20%) |
| markup | 14% | +1.08%/day | **+10.6** (6 lệnh, WR 67%) |
| distribution | 0.4% | +2.2%/day | 0 lệnh |
| markdown | 21% | **-0.94%/day** | **-13.2** (10 lệnh, WR 20%) |
| transition | 59% | +0.17%/day | **+12.2** (46 lệnh, WR 54%) |

**Year-split (anti-overfit):** cùng rule trên 2024 / 2025 / 2026 — phase mix thay đổi
(markup 55% năm 2024 bull, markdown 32% năm 2026 bear) → rule không “fit” một giai đoạn.

**Policy hand-crafted** (`config/wyckoff_policy.yaml`):

| Phase | Strategy | Risk |
| ----- | -------- | ---- |
| accumulation | MR long bias | 0.75% |
| markup | ema_atr long / flat MR | 0.5% |
| distribution | MR short bias | 0.75% |
| markdown | **flat** (no MR long) | 0.25% |
| transition | MR half size + HTF strict | 0.5% |

Chưa auto-switch live — chỉ scale risk / tắt leg khi phase rõ (markdown).

**Đã wire vào live/backtest** (`wyckoff_gate: true`):

- **Markdown** → không mở lệnh MR mới (vẫn quản lý exit lệnh đang mở)
- **Transition** → risk ×0.5
- Phase đổi → log `Wyckoff phase → …` trên live

**Wyckoff directional bias** (`wyckoff_directional_bias: true`, research prototype):

| Phase | Long MR | Short MR |
| ----- | ------- | -------- |
| accumulation | ✓ | ✗ |
| transition | ✓ (×0.5 risk) | ✓ (×0.5 risk) |
| distribution | ✗ | **✓** (+ HTF below EMA200) |
| markup | ✗ | ✗ |
| markdown | ✗ (gate) | ✗ (gate) |

```bash
python -m research.mr_directional_wf --folds 3
python -m research.oos_validate --config config/research_mean_reversion_eth_directional.yaml
```

Config: `config/research_mean_reversion_eth_directional.yaml` — **WF PASS 3/3** (2026-03).

**So sánh WF 3 folds (gate-only vs directional):**

| Variant | F0 | F1 | F2 | Total PnL | avg exp |
| ------- | -- | -- | -- | --------- | ------- |
| Gate only | +10.2 | **−2.8** | +1.9 | +9.35 | +0.13 |
| **Directional** | +10.2 | **+0.7** | +1.9 | **+12.9** | **+0.18** |

F1 (bear-ish 2025) cải thiện nhờ **tắt long MR khi không phù hợp phase** + short bias distribution.
Đã bật `wyckoff_directional_bias: true` trên `live_eth_mean_reversion.yaml`.

**OOS 60 ngày (directional, `results/eth_oos_60d.json` cập nhật sau directional):**

| Metric | Gate-only (cũ) | Directional |
| ------ | -------------- | ----------- |
| Trades | 27 | 22 |
| Exp | +0.27 | +0.13 |
| PF | 1.30 | 1.15 |
| PnL | +7.3 USDT | +2.8 USDT |
| Pass | ✓ | ✓ |

OOS directional thấp hơn gate-only trên 60d gần nhất nhưng **WF 3/3 ổn định hơn** (F1 không âm).

**So sánh EMA long vs MR trên ngày markup** (`python -m research.wyckoff_markup_compare`):

| Strategy | Trades | PnL | Kết luận |
| -------- | ------ | --- | -------- |
| MR (markup entries) | 6 | **+10.6** | Giữ MR |
| EMA long (markup) | 100 | **−204** | **FAIL — không promote EMA** |

**Phân tích chi tiết WF 3 folds (directional) — tại sao F0 cao, F1/F2 thấp:**

| Fold | Thời gian | Lệnh | PnL | Exp | ETH return | Wyckoff mix (ước lượng) |
| ---- | --------- | ---- | --- | --- | ---------- | ------------------------ |
| **F0** | 2024-08 → 2025-04 | 17 | **+10.2** | **+0.60** | bull cuối 2024 | transition + bull thuận MR |
| F1 | 2025-04 → 2025-12 | 12 | +0.7 | +0.06 | bear grind 2025 | bear; directional cứu từ −2.8 |
| F2 | 2025-12 → 2026-08 | 43 | +1.9 | +0.04 | **−23.8%** | **61% transition, 32% markdown**, ~0% markup/distribution |

- **F0:** ít lệnh, exp cao — bull/range thuận; PnL ≈ lệnh × exp.
- **F1:** bear 2025 — gate + directional giữ dương mỏng.
- **F2:** nhiều lệnh nhất (43) nhưng **edge gần 0** — transition MR half-size trong bear −24%; PASS nhưng không mạnh.

**Trạng thái F2 cần để MR có edge thật:**

- Transition **không** kèm ETH −20%+ liên tục (sideways hơi lên, như F9/F11 +17/+31%).
- Hoặc có **markup / distribution** đủ lâu cho leg tương ứng — F2 gần như không có 2 phase này.

**Bear grind — strategy phù hợp (chưa pass WF):**

| Leg | Trạng thái | Ghi chú |
| --- | ---------- | ------- |
| MR long markdown | **−13.2** PnL | Đã gate tắt |
| MR + gate + directional | Sống sót, edge mỏng | ✓ đang dùng |
| EMA long @ markup | FAIL | Không làm lại |
| Breakout @ markup | FAIL WF | `strategy_breakout.py` giữ research |
| **Markdown short breakdown** | **Chưa code** | Ưu tiên tiếp theo: Donchian lower + HTF + Wyckoff markdown |
| MR short @ distribution | Có trong directional | Hiếm trong F2 (~0% thời gian) |

```bash
python main.py live --config config/live_eth_mean_reversion.yaml
```

### Cải thiện tiềm năng khác (chưa làm)

- [ ] Chạy trên nhiều core hơn (máy hiện chỉ 2 core).
- [x] Thêm giới hạn vốn/danh mục dùng chung (gross, risk, cluster, daily halt).
- [ ] Thêm Mô hình Xử lý Nhiễu & Tương quan.
- [ ] Thêm Mô hình Dự báo Biến động & Xác suất Rủi ro.
- [ ] Thêm Mô hình Xác suất Ẩn.
- [x] Scan universe + transfer test 6 altcoin; scan riêng Binance TradFi (§13).
- [ ] Phân chia ra nhiều danh mục Bot (Signal / Execution / Risk / Portfolio).

---

## 7b. Roadmap chiến lược — Later / Skip / Prototype

### Later (sau khi MR demo ổn định)

| # | Ý tưởng | Ghi chú |
| - | ------- | ------- |
| 1 | **ETH/BTC relative strength spread** | Long ETH khi outperform BTC; cần catalog BTC + spread logic |
| 2 | **Trend leg strict markup-only** | Không dùng default `ema_atr` — chỉ long khi Wyckoff = markup |
| 3 | **Session / funding-hour filter cho MR** | Tránh giờ funding spike; filter thời gian, không tune param |
| 4 | **Auto-switch MR ↔ breakout theo Wyckoff** | Sau khi cả hai leg pass WF riêng; policy `wyckoff_policy.yaml` |
| 5 | **Markdown short breakdown** | Donchian lower + HTF + Wyckoff markdown; bù bear F2 |
| 6 | **Full grid optimizer MR ETH** | Resume `results/optimize/mr_eth_full_wf3/` khi có máy nhiều core |

| # | Ý tưởng | Lý do |
| - | ------- | ----- |
| 1 | **Funding-rate strategy** | Cần adapter funding data Binance |
| 2 | **ML / multi-asset stocks** | Scope quá rộng; chưa có infra |
| 3 | **Promote default `ema_atr` / `regime_switch`** | EMA long markup **FAIL** (−204 vs MR +10.6) |
| 4 | **Full grid trên máy 2 core** | ~83% cache nhưng chậm; ưu tiên quick grid + OOS |
| 5 | **Auto-switch nhiều strategy live** | Chưa validate Testnet đủ lâu |
| 6 | **Đổi default `live.yaml` / `research.yaml`** | Giữ `ema_atr` global; ETH demo dùng config riêng |

### Prototype đã thử — Volatility breakout markup-only (**FAIL**)

**Mục tiêu:** leg trend bổ sung MR trong giai đoạn Wyckoff **markup** (~14% thời gian, MR +10.6 USDT).

**File:**

- `strategy_breakout.py` — Donchian(20) + ADX≥25 + volume spike; **long only**
- `config/research_breakout_eth.yaml` — params **cố định**, không grid ETH
- `research/breakout_wf.py` — walk-forward 3 folds

**Rules cố định (không tune ETH):**

| Param | Giá trị |
| ----- | ------- |
| donchian_period | 20 |
| adx_min | 25 |
| volume_min_ratio | 1.3 |
| atr_stop_multiple | 2.0 |
| take_profit_multiple | 2.0 |
| wyckoff_markup_only | true |

**Chạy research:**

```bash
python main.py backtest --config config/research_breakout_eth.yaml
python -m research.breakout_wf --folds 3
```

**Tiêu chí acceptance (WF):** ≥2/3 folds expectancy > 0 **và** weighted avg exp > 0.

**Kết quả WF 3 folds (2026-03):** **FAIL** — chỉ F1 có markup phase đủ dài;
22 lệnh tổng, PnL **−8.0 USDT**, exp **−0.36**. F0/F2: 0 lệnh (không có
markup+breakout trong cửa sổ OOS). Prototype giữ lại cho research; **không promote live**.

### Demo / validation 1–2 tháng (khuyến nghị thay live 24/7)

**Workflow hàng tuần** (không cần bật máy liên tục):

```bash
python main.py download --config config/research_mean_reversion_eth_directional.yaml
python -m research.oos_validate --config config/research_mean_reversion_eth_directional.yaml
python -m research.mr_directional_wf --folds 3   # tùy chọn, khi đủ data mới
```

**Live signal-only** (tùy chọn — kiểm pipeline WebSocket, không bắt buộc cho research):

```bash
python main.py live --config config/live_eth_mean_reversion.yaml
```

- `enable_trading: false` mặc định — chỉ log signal
- Wyckoff gate + directional bias đã bật
- Nhẹ máy (~200–600 MB); spike lúc tải history 220 ngày
- Cần `.env` với Binance Testnet API key

**Params MR ETH đang giữ cố định (không grid thêm):**

| Param | Giá trị |
| ----- | ------- |
| stop | 1.5 × ATR |
| TP | 2.0 × stop |
| vhf_max | 0.25 |
| adx_max | 20 |
| volume_max_ratio | 1.8 |
| wyckoff_gate | true |
| wyckoff_directional_bias | true |
| htf_trend_filter | true (1h EMA200) |

---

## 8. Cách chạy

```bash
# Tải dữ liệu (mọi mã trong market.symbols)
python main.py download

# Backtest (phí + slippage), report ra results/<SYMBOL>/
python main.py backtest
python main.py backtest --config config/research_mean_reversion.yaml
python main.py backtest --config config/research_regime_switch.yaml

# Live (Testnet/Demo, signal-only hoặc enable_trading)
python main.py live

# Optimizer (grid-search, xếp theo expectancy)
python -m research.optimize --config config/research.yaml --grid quick
python -m research.optimize --config config/research_mean_reversion.yaml --grid quick --folds 3 --workers 2
python -m research.mr_directional_wf --folds 3
python -m research.oos_validate --config config/research_mean_reversion_eth_directional.yaml
python -m research.regime_analysis --folds 12
python -m research.wyckoff_analysis
python -m research.wyckoff_markup_compare

# Unit tests
python -m unittest discover -s tests
```

---

## 11. Tổng hợp research — bảng quyết định

### Chiến lược / experiment — kết quả

| # | Experiment | Kết quả | File kết quả | Promote? |
| - | ---------- | ------- | ------------ | -------- |
| 1 | MR quick grid ETH 3-fold | 4/32 pass; top stop 1.5 TP 2.0 vhf 0.25 adx 20 vol 1.8 | `results/optimize/_speed_test/` | Params cố định ✓ |
| 2 | MR BTC+ETH quick grid | BTC âm 2/3 fold; ETH 3/3 | `results/optimize/mr_wf3_adx/` | Không BTC |
| 3 | EMA quick grid | 0/12 pass | `results/optimize/ema_wf3/` | Không |
| 4 | MR ETH 6-fold 365d | 4/6 pass; F1/F2 âm nặng | NOTES bước 2 | Không đủ vững |
| 5 | MR ETH OOS 60d (gate) | 27 lệnh, exp +0.27, PF 1.30, +7.3 USDT | `results/eth_oos_60d.json` | ✓ pass |
| 6 | Wyckoff phase × MR PnL | markdown −13.2; transition +12.2; markup +10.6 | `research/wyckoff_analysis.py` | Gate policy |
| 7 | EMA long vs MR @ markup | EMA −204 vs MR +10.6 | `research/wyckoff_markup_compare.py` | **Không EMA** |
| 8 | Wyckoff gate only WF 3-fold | 2/3 pass; F1 −2.8 | `mr_directional_wf3.json` baseline | Thay bằng directional |
| 9 | **Wyckoff directional WF 3-fold** | **3/3 pass**; total +12.9; exp +0.18 | `results/optimize/mr_directional_wf3.json` | **✓ config chính** |
| 10 | Breakout markup-only WF | FAIL; 22 lệnh exp −0.36 | `results/optimize/breakout_wf3.json` | Không |
| 11 | Full grid MR ETH | ~83% cache, aborted (2 core chậm) | `results/optimize/mr_eth_full_wf3/` | Skip for now |

### Config đang dùng (ETH MR)

| Mục đích | File |
| -------- | ---- |
| Research + OOS + download | `config/research_mean_reversion_eth_directional.yaml` |
| Live Testnet (signal-only mặc định) | `config/live_eth_mean_reversion.yaml` |
| Baseline gate-only (so sánh) | `config/research_mean_reversion_eth.yaml` |
| Breakout research | `config/research_breakout_eth.yaml` |
| Global default (không đổi) | `config/live.yaml`, `config/research.yaml` → `ema_atr` |

### Bài học regime (đã xác nhận bằng data)

1. **Win rate ≠ lợi nhuận** — expectancy + PF quan trọng hơn.
2. **Stop rộng + TP cao** thắng stop chặt (optimizer 180d).
3. **VHF+ADX+volume** không phân biệt bear crash vs range.
4. **HTF EMA200** giảm long trong bear.
5. **Wyckoff markdown gate** tránh MR long tệ nhất.
6. **Wyckoff directional** cải thiện F1 bear; F2 vẫn edge mỏng.
7. **Trend EMA long** không thay MR trên markup.
8. **Breakout long @ markup** không có edge trên ETH với params cố định.
9. **Bear grind** cần leg short riêng (markdown breakdown) — chưa implement.

### Tiếp theo (ưu tiên)

→ Chi tiết đầy đủ: **§12 Kế hoạch tiếp theo**.

Tóm tắt: forward-test 6–8 tuần → live signal-only → Testnet size nhỏ → markdown short leg.

### Unit tests

```bash
python -m unittest discover -s tests   # 44 tests pass (2026-08-21)
```

Coverage: `risk_limits`, `regime`, `acceptance`, `wyckoff` (+ directional bias).

---

## 12. Kế hoạch tiếp theo (góc nhìn trader — ETHUSDT)

> Giai đoạn hiện tại: **đã tìm được strategy hợp lý** (MR + Wyckoff directional, WF 3/3,
> OOS pass). Không tune thêm param. Việc kế tiếp là **chứng minh edge còn sống forward**
> và **kiểm execution**, rồi mới thêm leg bear.

**Nguyên tắc:**

- **Đóng băng params** — không grid, không đổi stop/TP/vhf/adx/vol.
- **Một leg mới mỗi chu kỳ** — không code markdown short + ETH/BTC spread cùng lúc.
- **Forward > backtest** — backtest thêm ít giá trị hơn 6 tuần OOS rolling.
- **Không live tiền thật** — Testnet/Demo execution only. `LIVE` chỉ được phép
  cho public market data khi `enable_trading: false`.

**Config cố định suốt kế hoạch:**

- Research / OOS / download: `config/research_mean_reversion_eth_directional.yaml`
- Live Testnet: `config/live_eth_mean_reversion.yaml`

**Params không đổi:**

| Param | Giá trị |
| ----- | ------- |
| stop | 1.5 × ATR |
| TP | 2.0 × stop |
| vhf_max | 0.25 |
| adx_max | 20 |
| volume_max_ratio | 1.8 |
| wyckoff_gate | true |
| wyckoff_directional_bias | true |
| htf_trend_filter | true (1h EMA200) |
| risk_pct_per_trade | 1.0% (cap 50 USDT) |
| max_daily_loss_pct | 2.0% |
| circuit_breaker | 4 losses / pause 96 bar |

---

### Giai đoạn 1 — Forward-test 6–8 tuần (ưu tiên cao nhất)

**Mục tiêu:** chứng minh edge trên **data chưa dùng lúc tune**, không cần máy 24/7.

**Mỗi tuần (cùng config, không đổi param):**

```bash
# Nghi thức 1 lệnh (khuyến nghị, tự xử lý disjoint tail):
./scripts/weekly_forward_test.sh

# Hoặc thủ công:
python main.py download --config config/research_mean_reversion_eth_directional.yaml
python -m research.oos_validate --config config/research_mean_reversion_eth_directional.yaml --holdout-days 60
```

> ⚠️ **Bẫy đã gặp W1 (2026-08-23):** `main.py download` bị skip im lặng khi cửa
> sổ request overlap catalog hiện có → ETH đứng ở 2026-08-21 dù đã chạy download.
> Fix: chỉ fetch đoạn sau bar cuối cùng (+16 phút buffer) như script trên.
> Artifact OOS lưu `results/forward_test/<ngày>.json`.

**Ghi log hàng tuần** (NOTES hoặc bảng riêng):

| Tuần | Ngày chạy | Trades OOS | Exp | PF | PnL | Ghi chú thị trường |
| ---- | --------- | ---------- | --- | -- | --- | ------------------ |
| W1 | 2026-08-23 | 11 | −0.4038 | 0.75 | −4.44 | ETH +45% trong window (bull markup); MR flat đúng directional bias, ít lệnh transition lỗ nhẹ; window dịch +2 ngày so run đầu cùng ngày (13 lệnh, +2.17) — ghi nhận run mới nhất, KHÔNG tune |
| W2 | | | | | | |
| … | | | | | | |

**Tiêu chí PASS giai đoạn 1 (để sang giai đoạn 2):**

- [ ] ≥ **4/6 tuần** OOS có expectancy > 0
- [ ] Không có **3 tuần liên tiếp** PF < 0.8
- [ ] Hiểu tuần thua do bear grind (F1/F2-style) — **không panic tune**
- [ ] Params YAML **không đổi** suốt giai đoạn

**Không làm trong giai đoạn 1:**

- Grid optimizer / full grid 2 core
- Strategy mới (breakout, EMA, spread)
- Tăng size / leverage
- Promote `live.yaml` / `research.yaml` default

---

### Giai đoạn 2 — Live signal-only 2 tuần (kiểm hạ tầng)

**Mục tiêu:** xác nhận pipeline live (WebSocket, clock, log phase) — **không** kiếm tiền.

```bash
python main.py live --config config/live_eth_mean_reversion.yaml
```

(`enable_trading: false` — mặc định)

**Không bắt buộc 24/7:** mở vài giờ/ngày hoặc VPS rẻ khi cần.

**Checklist 3 câu:**

- [ ] Bar 15m Testnet đến đúng giờ?
- [ ] Log `Wyckoff phase -> …` hợp lý vs backtest?
- [ ] Hướng signal live vs backtest cùng ngày có khớp?

**Tiêu chí PASS:** cả 3 câu OK → sang giai đoạn 3.

---

### Giai đoạn 3 — Testnet trading size nhỏ (học phí thật)

**Mục tiêu:** slippage, fill, funding, cảm xúc — **không** tối đa hóa PnL.

**Chỉ bật sau khi giai đoạn 1 + 2 pass.**

Trong `config/live_eth_mean_reversion.yaml`:

```yaml
enable_trading: true   # chỉ khi đã review checklist
```

**Giữ size nhỏ (không tăng dù thắng 2 tuần):**

- `risk_pct_per_trade: 1.0`, `max_risk_per_trade_usdt: 50`
- `max_daily_loss_pct: 2.0`
- `circuit_breaker_losses: 4`, `circuit_breaker_pause_bars: 96`

**Tiêu chí PASS:**

- [ ] ≥ **20 lệnh** Testnet thật
- [ ] Slippage / fill chấp nhận được vs backtest
- [ ] Không vượt daily loss cap / circuit breaker ngoài dự kiến
- [ ] Ghi nhận tuần bear — bot **ngồi ngoài** hoặc edge mỏng (chấp nhận)

---

### Giai đoạn 4 — Leg bear: markdown short breakdown (sau giai đoạn 1)

**Chỉ bắt đầu khi giai đoạn 1 forward-test xong** (6–8 tuần). Không song song với tune MR.

**Mục tiêu:** bù giai đoạn bear grind (F2: ETH −24%, 32% markdown) — MR hiện chỉ sống sót.

**Rules cố định (không tune ETH):**

- Wyckoff phase = **markdown**
- Close **dưới** 1h EMA200
- Break Donchian **lower** (20) + volume spike
- Stop ATR chặt, TP 1.5–2R, long-only MR vẫn flat trong markdown

**Validation:**

```bash
python -m research.<markdown_short_wf> --folds 3   # sau khi implement
```

**Tiêu chí promote leg:** WF ≥2/3 folds exp > 0, không degrade MR directional trên cùng folds.

**Sau giai đoạn 4 (nếu pass):** cân nhắc ETH/BTC spread — **không** trước đó.

---

### Việc KHÔNG làm (cả 4 giai đoạn)

| Việc | Lý do |
| ---- | ----- |
| Grid thêm param MR | Overfit; đã WF pass params cố định |
| Promote EMA / breakout / regime_switch | Đã FAIL có số liệu |
| Full grid trên máy 2 core | Chậm; cache `mr_eth_full_wf3` tạm bỏ |
| Trade BTC cùng logic ETH | BTC âm 2/3 fold |
| Tăng size sau F0 (+10 USDT) | F0 bull — không đại diện |
| Live tiền thật | Chưa đủ forward + Testnet execution |
| Auto-switch nhiều strategy live | Chưa validate từng leg riêng |

---

### Checklist “ready for next level”

```
[ ] Giai đoạn 1 — 6 tuần OOS rolling, mostly positive
[ ] Giai đoạn 2 — live signal-only pipeline OK
[ ] Giai đoạn 3 — 20+ lệnh Testnet, slippage OK
[ ] Biết khi nào ngồi ngoài (bear grind / F2-like)
[ ] Giai đoạn 4 — markdown short WF pass (optional)
[ ] Chỉ khi đó: cân nhắc risk 1.5–2% hoặc thêm symbol
```

---

### Tóm tắt một dòng

**Đừng tìm strategy mới — hãy forward-test MR directional 6–8 tuần, Testnet nhỏ, rồi mới bù bear bằng markdown short.**

---



## 9. Ghi chú kỹ thuật đã xử lý

- **Volume precision mismatch:** Binance kline volume có 3 chữ số thập phân trong
khi instrument `size_precision=4` → matching engine từ chối. Đã fix bằng cách
chuẩn hoá volume khi load trong `data/catalog.py`.
- **Path chứa dấu cách (Windows):** `DataCatalogConfig.as_catalog()` mã hoá `%20`
→ đăng ký `ParquetDataCatalog` trực tiếp thay vì qua config.
- **Download engine:** kernel clock = 0 + instrument provider chưa load → set clock
  - `load_ids()` thủ công trước khi request.
- **Windows Unicode:** ký tự `→` trong print gây lỗi cp1252 → dùng `->` trong CLI output.
- **Wyckoff WF warmup:** walk-forward cần `history_days` bar trước OOS window; metrics lọc positions đóng trong cửa sổ OOS (`breakout_wf.py`, `mr_directional_wf.py`).
- **Tốc độ optimizer:** cache bars mỗi mã + chạy song song (`--workers`, mặc định
= số core). Máy 2 core chỉ nhanh tối đa ~2x.

---



## 10. Lưu ý an toàn

- API key trong `.env` là **testnet** — không bao giờ đặt key live.
- `.env`, `catalog/`, `results/` đã được gitignore.
- Hệ thống **chặn LIVE execution**. Production public market data chỉ chạy
  signal-only (`enable_trading: false`).

---

## 13. Research đa mã Binance — triển khai 2026-08-21

### 13.1 Môi trường và compatibility

- Pin chính thức: `nautilus_trader==1.230.0`, Python 3.12.14.
- Nautilus 1.230 có Rust logger process-global: `log_level: OFF` vẫn init logger
  nếu không đặt `bypass_logging=true`. Đã sửa `backtest/engine.py` để các
  walk-forward nhiều engine không panic.
- Portfolio backtest CLI dùng logging OFF để tránh sinh hàng trăm nghìn dòng log.
- Tài liệu đối chiếu:
  - Binance API catalog: https://developers.binance.com/en/docs/catalog
  - Binance USD-M common definitions: https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/common-definition
  - Nautilus Binance integration: https://nautilustrader.io/docs/latest/integrations/binance/

### 13.2 Phase A — universe point-in-time ✅

Snapshot lưu cả accepted/rejected để không vô tình chỉ backtest các mã còn sống:

| Universe | Filter | Kết quả |
| -------- | ------ | ------- |
| Crypto USD-M | ≥365 ngày, volume ≥50M USDT/24h, ≥10k trades/24h | **49/872** eligible |
| TradFi USD-M | history gate 0 ngày, volume ≥1M, ≥1k trades | **113/872** eligible |

Artifacts local:

- `research_snapshots/binance_usdm_20260821.json`
- `research_snapshots/binance_tradfi_20260821.json`

Cohort transfer cố định, chọn trước khi xem kết quả:
`SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT`.

### 13.3 Phase B — frozen ETH-rule transfer 6 folds ✅ FAIL

Không optimizer, không thay params ETH directional MR. Mỗi mã có **70.079 bar
15m**, cùng cửa sổ 2024-08-21 → 2026-08-21.

| Symbol | Positive folds | Trades | Expectancy | PF | Screen |
| ------ | -------------- | ------ | ---------- | -- | ------ |
| ADAUSDT | 3/6 | 109 | −0.0548 | 0.91 | FAIL |
| BNBUSDT | 1/6 | 111 | −0.3320 | 0.73 | FAIL |
| DOGEUSDT | 2/6 | 97 | −0.0621 | 1.08 | FAIL |
| LINKUSDT | 1/6 | 116 | −0.6986 | 0.69 | FAIL |
| SOLUSDT | 3/6 | 104 | −0.0552 | 1.01 | FAIL |
| XRPUSDT | 1/6 | 124 | −0.2042 | 1.07 | FAIL |

Artifact: `results/altcoin_transfer/transfer_wf_20260821.json`.

**Quyết định:** ETH directional MR **không transfer** sang cohort altcoin. Không
tune riêng từng mã sau khi thấy kết quả vì đó là selection bias.

### 13.4 Phase C — shared-capital portfolio ✅ FAIL

Một account 100.000 USDT, 6 strategy instances, bars sắp theo một global
timeline, portfolio risk/cluster dùng chung:

| Metric | Kết quả |
| ------ | ------- |
| Positions | 608 |
| PnL | **−105,29 USDT** |
| Expectancy | **−0,1732** |
| Profit factor | **0,8460** |
| Sharpe | **−0,6265** |
| Win rate | 36,02% |

Artifact: `results/altcoin_transfer/portfolio/summary.json`.

Kết luận portfolio xác nhận failure không chỉ do chia vốn từng mã. Portfolio
risk giảm concentration, nhưng không thể biến edge âm thành edge dương.

### 13.5 Phase D — derivatives context 30 ngày ✅

Đã tải cho cả 6 mã: 90 funding settlements, 2.880 mark-price bars và 2.880 OI
points/mã (~720 giờ). Downloader OI đã sửa pagination ngược theo `endTime`;
trước fix chỉ có 500 điểm (~125 giờ).

| Symbol | Avg funding (bps/settlement) | Funding dương | Mark return | OI value change |
| ------ | ---------------------------- | ------------- | ----------- | --------------- |
| ADA | 0,312 | 70,0% | +25,00% | +18,37% |
| BNB | 0,417 | 72,2% | +19,07% | +22,33% |
| DOGE | 0,497 | 77,8% | +15,89% | +23,15% |
| LINK | 0,593 | 88,9% | +32,14% | +75,99% |
| SOL | 0,303 | 67,8% | +17,60% | +8,17% |
| XRP | 0,281 | 74,4% | +24,59% | +20,58% |

Đây là snapshot bullish/crowded ngắn hạn, **không phải bằng chứng nhân quả** cho
failure 2 năm. Funding phải được đưa vào cashflow backtest trước khi dùng để
promote strategy.

### 13.6 Phase E — Binance TradFi / cổ phiếu ⏳ DATA ACCUMULATION

Binance hiện trả `TRADIFI_PERPETUAL` trong cùng USD-M API. Snapshot ví dụ:

| Symbol | History tại snapshot | Volume 24h | Trades 24h | Quyết định |
| ------ | -------------------- | ---------- | ---------- | ---------- |
| SPYUSDT | ~137 ngày | 44,5M | 55k | Chờ dữ liệu |
| QQQUSDT | ~137 ngày | 121,1M | 160k | Chờ dữ liệu |
| NVDAUSDT | ~148 ngày | 112,6M | 208k | Chờ dữ liệu |
| TSLAUSDT | ~205 ngày | 95,5M | 268k | Chờ dữ liệu |

Chưa mã nào đạt history gate 365 ngày, nên **không chạy/publish walk-forward**.
Trading schedule `/fapi/v1/tradingSchedule` chỉ là cửa sổ rolling quanh hiện tại;
live gate dùng schedule thật và fail-closed. Historical backtest chưa được phép
giả lập holiday/early-close bằng lịch tuần đơn giản rồi gọi đó là kết quả chuẩn.

### 13.7 Thứ tự triển khai tiếp theo

1. **Giữ ETH directional MR riêng ETH**, tiếp tục forward-test §12; không mở sang altcoin.
2. ✅ **Đã tích hợp funding cashflow vào backtest accounting** và rerun ETH + cohort;
   kết quả chi tiết ở §14. Funding vẫn chưa được dùng làm signal.
3. **Baseline mới độc lập cho altcoin:** time-series momentum / markdown short,
   params cố định theo asset class; so với buy-and-hold và flat, không reuse MR.
4. **TradFi data accumulation:** snapshot universe + trading schedule hàng ngày/tuần;
   chỉ nghiên cứu SPY/QQQ/NVDA/TSLA khi đủ history hoặc dùng dataset nguồn chính
   thức khác có lịch phiên/holiday đầy đủ.
5. Với mọi candidate: single-symbol WF → frozen transfer → shared-capital portfolio
   → funding/session/slippage stress → signal-only. Fail ở gate nào thì dừng ở đó.

**Trạng thái promote:** không có symbol/strategy mới nào được promote sau research
2026-08-21. Default global và live execution giữ nguyên.

---

## 14. Funding accounting và rerun — 2026-08-21

### 14.1 Cách tính và audit contract

- Dữ liệu lịch sử lấy theo Binance USD-M funding endpoint, lưu bundle riêng từng
  symbol cùng `requested_start_ms`, `requested_end_ms` và toàn bộ rows để audit.
- Một settlement chỉ áp dụng khi `ts_opened <= fundingTime < ts_closed`.
- Notional tại settlement = `peak_qty × markPrice`. Funding dương: long trả,
  short nhận; funding âm đảo chiều cashflow.
- Pipeline fail-closed nếu thiếu bundle, thiếu coverage thời gian, timestamp không
  hợp lệ, entry không phải `BUY/SELL`, hoặc quantity/mark price không dương.
- Báo cáo sinh thêm `funding_cashflows.csv`,
  `positions_funding_adjusted.csv` và block `funding_adjustment` trong `summary.json`.

Tài liệu đối chiếu:

- Nautilus Binance integration: https://nautilustrader.io/docs/latest/integrations/binance/
- Binance funding-rate history: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History

### 14.2 Kết quả ETH directional — fresh 365 ngày

Run production-public data mới, 35.039 bar 15m, 39 positions:

| Metric | Trước funding | Sau funding |
| ------ | ------------- | ------------ |
| PnL | −5,3549 USDT | **−5,5359 USDT** |
| Expectancy | −0,1373 | **−0,1419** |
| Position-PnL PF | 0,8782 | **0,8743** |
| Win rate | 41,03% | 41,03% |

Funding paid 0,2061, received 0,0251, net **−0,1810 USDT** qua 22 settlements
trên 16 positions. Artifact:
`results/funding_eth_directional/ETHUSDT/summary.json`.

Run này là full-window 365 ngày, **không phải** walk-forward 3 folds. Nó không
xóa kết quả WF lịch sử, nhưng là bằng chứng mới hơn rằng edge hiện tại không đủ
để promote; forward gate ở §12 vẫn giữ nguyên.

### 14.3 Kết quả cohort altcoin shared-capital

| Metric | Trước funding | Sau funding |
| ------ | ------------- | ------------ |
| PnL | −105,2901 USDT | **−110,4007 USDT** |
| Expectancy | −0,1732 | **−0,1816** |
| Position-PnL PF | 0,8902 | **0,8851** |
| Win rate | 36,02% | 36,02% |

Funding paid 5,7355, received 0,6249, net **−5,1106 USDT** qua 308 settlements
trên 266/608 positions. Cả 6 symbol có coverage đầy đủ. Artifact:
`results/altcoin_transfer/portfolio/summary.json`.

`stats_returns.Profit Factor` của Nautilus (return series) và
`funding_adjustment.profit_factor_*` (realized PnL từng position) dùng mẫu số
khác nhau; chỉ so sánh trước/sau trong cùng họ metric.

### 14.4 Kết luận và giới hạn

Funding làm cả hai kết quả xấu thêm, nhưng không phải nguyên nhân chính: cả ETH
fresh run và cohort đã âm trước carry cost. Không promote strategy/symbol mới.

Đây là **post-trade accounting**: funding được cộng vào report sau khi engine
đóng vị thế, chưa debit/credit intrarun equity nên chưa tác động position sizing,
daily-loss gate hoặc compounding. Trước khi tăng quy mô hoặc nghiên cứu strategy
nhạy với margin, cần phase tiếp theo dùng funding event native trong engine (hoặc
cash-account event tương đương) và kiểm tra parity với audit này.

Catalog cũ `./catalog` dùng standard precision không tương thích build high
precision hiện tại của Nautilus 1.230. Không xóa dữ liệu cũ; config fresh run dùng
`./catalog_live_crypto` để tránh trộn hai định dạng.

**Bước research kế tiếp:** baseline altcoin độc lập (time-series momentum /
markdown short), params frozen theo asset class; single-symbol WF trước, sau đó
frozen transfer và shared-capital theo đúng gate §13.7.

---

## 15. Market behavior hypotheses và strategy theo phase — 2026-08-21

Phần này là **giả thuyết research**, chưa phải tín hiệu giao dịch hay quyết định
promote. Tôi tách phase Wyckoff khỏi một trục thứ hai là crowding của perpetual:
giá, thay đổi open interest và funding rate.

### 15.1 Những hành vi đã thấy trong dữ liệu hiện có

1. **ETH có bất đối xứng theo phase.** MR directional tránh được phần lớn lỗi ở
   markdown, nhưng dữ liệu phase cho thấy MR trong markdown lỗ −13,2 USDT với WR
   20%; transition có +12,2 nhưng F2 transition trong bear −23,8% chỉ còn edge
   gần 0. Vì vậy nhãn `transition` không đủ để bật full risk.
2. **ETH trend phase không đồng nghĩa breakout có edge.** Cả EMA long và
   Donchian/ADX breakout markup-only đều FAIL trong nghiên cứu cũ. Markup nên
   được xem là bối cảnh để tìm pullback/retest, không phải lý do tự động mua đuổi.
3. **ETH MR không transfer sang altcoin.** SOL/ADA là nhóm “ít xấu nhất” (3/6
   folds dương, PF quanh 1), DOGE/XRP có PF tổng >1 nhưng PnL vẫn âm và fold
   instability cao. BNB và LINK là failure rõ hơn; không được chọn lại params sau
   khi đã xem kết quả.
4. **Snapshot derivatives 30 ngày là bullish/crowded đồng loạt:** funding dương
   67,8–88,9% số settlement, mark return +15,9% đến +32,1%, OI value tăng +8,2%
   đến +76,0%. LINK là outlier: funding bình quân 5,93 bps/settlement và OI
   +76,0%. Đây là bằng chứng crowding/carry trong một cửa sổ bullish, **không** là
   bằng chứng funding gây ra giá hay giá chắc chắn đảo chiều.
5. **BTC là beta anchor, không phải ETH clone.** Research cũ cho thấy cùng MR
   logic âm 2/3 fold trên BTC; BTC nên được dùng làm market-state/hedge feature
   trước khi xem như một candidate độc lập.

Nghiên cứu bên ngoài cũng ủng hộ việc tách theo liquidity: bằng chứng cross-section
cho thấy coin kém thanh khoản dễ có short-term reversal, còn nhóm lớn/thanh khoản
cao có daily momentum; intraday crypto có thể chứa cả momentum và reversal tùy
liquidity, jump và event. Đây là lý do không dùng một strategy cho toàn bộ universe.
[Zaremba et al. (2021)](https://doi.org/10.1016/j.irfa.2021.101908),
[Wen et al. (2022)](https://doi.org/10.1016/j.najef.2022.101733).

### 15.2 Trục crowding cần thêm vào phase

| Giá | OI | Funding | Diễn giải giả thuyết | Hành động nghiên cứu |
| --- | --- | --- | --- | --- |
| Tăng | Tăng | Dương | Trend có đòn bẩy/crowding long | Không fade mù; chỉ pullback continuation, giảm size và trừ carry |
| Tăng | Giảm | Thấp/giảm | Spot-led hoặc short-covering | Có thể giữ trend lâu hơn, nhưng cần xác nhận volume |
| Giảm | Tăng | Âm | Crowding short/liquidation risk | Không đuổi short; chờ breakdown-retest và stop ngắn |
| Giảm | Giảm | Bất kỳ | Deleveraging/forced unwind | Flat hoặc size nhỏ sau impulse; tránh MR bắt dao rơi |

Funding/OI phải được lấy theo timestamp và đưa vào accounting trước. Binance công
bố riêng funding history, open interest, basis, mark price và trading schedule;
Nautilus ánh xạ funding lịch sử thành `FundingRateUpdate`, nên có thể nâng cấp từ
post-trade audit hiện tại sang event trong engine sau khi baseline pass.
[Binance USDⓈ-M market-data API](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data),
[Nautilus Binance funding data](https://nautilustrader.io/docs/latest/integrations/binance/).

### 15.3 Strategy đề xuất theo Wyckoff phase

| Phase | Strategy candidate | Điều kiện bắt buộc | Risk policy |
| ----- | ------------------ | ------------------ | ----------- |
| Accumulation | **Reclaim + MR long**, không blind lower-band | Range ADX thấp, breakdown thất bại, reclaim mid-range; funding không quá đắt | 0,5–0,75R; không short |
| Markup | **Trend pullback/retest**, chưa dùng breakout hiện tại | 1h/4h trend cùng hướng, pullback giữ EMA, OI không sụp; funding cap | 0,5R; không chase nến mở rộng |
| Distribution | **MR short sau rejection** hoặc flat | Range ở đỉnh, rejection xác nhận, funding/OI crowding; sample phải đủ | 0,5R; không short chỉ vì giá “cao” |
| Markdown | **Lower-Donchian breakdown + retest short** | Daily/HTF dưới EMA200, breakdown có volume, retest fail; funding cost stress | 0–0,25R; circuit breaker; không MR long |
| Transition | **MR half-size hoặc flat** | Chỉ bật khi 20d slope không âm mạnh và volatility không jump | 0,25–0,5R; max holding ngắn |

Điểm cần giữ nguyên: markdown short là candidate mới phải chạy single-symbol WF;
không được suy ra là có edge chỉ vì MR long thất bại. Tương tự, accumulation và
distribution có rất ít quan sát ETH nên chưa được gọi là validation.

### 15.4 Mapping theo mã đang research

| Mã/nhóm | Hành vi hiện thấy | Ưu tiên strategy research |
| ------- | ----------------- | ------------------------- |
| ETH | Phase gate có ích; markdown là vùng nguy hiểm; fresh 365d run vẫn âm trước funding | Giữ MR directional signal-only; tiếp theo test markdown short độc lập |
| BTC | Beta anchor; không pass cùng MR ETH | Market-regime filter, trend/pullback riêng; dùng làm hedge feature trước |
| SOL | Cohort ít xấu nhất cùng ADA; OI 30d chỉ +8,2% | Reclaim/MR và pullback trend, frozen params, chưa promote |
| ADA | 3/6 folds dương nhưng PF 0,91 | Reclaim + liquidity filter; phải cải thiện sau funding/fee |
| XRP | PF 1,07 nhưng PnL âm, kết quả phụ thuộc fold | Event/impulse filter hoặc relative-strength test; không dùng PF đơn độc |
| DOGE | Funding 4,97 bps, OI +23,2%; jump/crowding nhạy | Short-horizon momentum sau breakout xác nhận; tránh giữ khi carry cao |
| BNB | Frozen MR failure rõ (PF 0,73) | Không trade candidate hiện tại; chỉ test trend/pullback riêng nếu có thesis |
| LINK | OI +76,0%, funding 5,93 bps, mark +32,1%; crowding outlier | Không fade mù và không chase; chỉ xem xét continuation có OI/basis filter |
| SPY/QQQ perpetual | Chưa đủ history; hành vi gắn phiên Mỹ, gap và holiday | Session-aware pullback/gap strategy; flat ngoài phiên và kiểm schedule thật |
| NVDA/TSLA perpetual | Chưa đủ history; single-name/event gap risk cao | Opening-range/event breakout, earnings blackout, slippage stress; chưa backtest |

### 15.5 Thứ tự kiểm chứng

1. Tạo feature snapshot theo từng bar: BTC beta, basis, funding percentile,
   OI change, mark/index spread, taker imbalance và liquidation proxy.
2. Implement ba baseline độc lập, params frozen: `reclaim_mr`,
   `trend_pullback`, `markdown_breakdown`; TradFi có pipeline session riêng.
3. Mỗi baseline đi qua single-symbol WF → frozen transfer → shared capital →
   funding/session/slippage stress. Gate tối thiểu: expectancy dương sau chi phí,
   PF > 1 trong cùng một định nghĩa PnL, không phụ thuộc một fold duy nhất.
4. Chỉ sau khi một leg pass mới nối vào portfolio; không auto-switch nhiều leg live
   trong cùng release.

---

## 16. Independent baseline backtest — 2026-08-21

Đã implement ba baseline độc lập, không grid/tune sau khi xem kết quả:

- `reclaim_mr`: chỉ vào sau khi giá reclaim Bollinger band trong range yếu; phase
  gate cho accumulation/transition long và distribution/transition short.
- `trend_pullback`: EMA20/50/200 + ADX + volume, vào khi giá reclaim EMA20 trong
  markup/transition hoặc markdown/transition.
- `markdown_breakdown`: short-only, lower Donchian + ADX + volume + EMA200 trong
  Wyckoff markdown.

Code/config:

- `strategy_reclaim_mr.py`, `strategy_trend_pullback.py`,
  `strategy_markdown_breakdown.py`
- `research/baseline_wf.py`
- `config/research_baseline_eth.yaml`
- `config/research_baseline_altcoin.yaml`

Runner dùng cùng Nautilus 1.230, maker/taker fee, one-tick slippage, risk limits,
global timeline và funding post-trade accounting như các phase trước. Mỗi cell WF
là một run độc lập với history warmup; `PASS` bên dưới chỉ là screening per-symbol,
chưa phải portfolio acceptance.

### 16.1 Walk-forward 3 folds — ETH

| Baseline | Trades | Positive folds sau funding | PnL sau funding | Expectancy sau funding | Screen |
| -------- | ------ | -------------------------- | --------------- | ---------------------- | ------ |
| reclaim_mr | 93 | **2/3** | **+5,6694** | **+0,0610** | PASS sơ bộ |
| trend_pullback | 460 | 0/3 | −136,5700 | −0,2969 | FAIL |
| markdown_breakdown | 224 | 1/3 | −36,8103 | −0,1643 | FAIL |

Full-window ETH report (35.039 bars): `reclaim_mr` có 92 positions, PnL
**+4,1123 USDT** sau funding, position-PnL PF 1,0294; đây là tín hiệu yếu, chưa
đủ thay thế ETH directional MR đang forward-test.

Artifacts:

- `results/baselines/reclaim_mr_eth_wf3.json`
- `results/baselines/trend_pullback_eth_wf3.json`
- `results/baselines/markdown_breakdown_eth_wf3.json`
- `results/baselines/reclaim_mr_eth_full/ETHUSDT/summary.json`

### 16.2 Walk-forward 3 folds — altcoin transfer screen

| Baseline | Symbols đạt 2/3 folds dương | Kết quả đáng chú ý |
| -------- | --------------------------- | ------------------ |
| reclaim_mr | **SOL (2/3)** | SOL PnL +6,6810, exp +0,0373; 5 mã còn lại FAIL |
| trend_pullback | **DOGE (2/3)** | DOGE PnL +18,9337, exp +0,0245; edge rất mỏng |
| markdown_breakdown | **ADA (2/3)** | ADA PnL +13,6365, exp +0,0392; 5 mã còn lại FAIL |

Mỗi symbol được screening `2/3 folds`; chỉ SOL/DOGE/ADA tương ứng đạt điều kiện
trong baseline của chúng. Điều đó không có nghĩa toàn cohort pass; không mã nào
đạt gate transfer toàn cohort.

Artifacts:

- `results/baselines/reclaim_mr_altcoin_wf3.json`
- `results/baselines/trend_pullback_altcoin_wf3.json`
- `results/baselines/markdown_breakdown_altcoin_wf3.json`

Mỗi WF cell cũng lưu `buy_hold_pnl_at_max_notional` và `flat_pnl=0`. ETH long
buy-and-hold cố định 300 USDT trong ba folds là **−150,6625 USDT**, trong khi
reclaim-MR là +5,6694 sau funding. Với altcoin, tổng long buy-and-hold theo từng
symbol/fold là **+652,7390 USDT**, nhưng đây là benchmark per-symbol không chia sẻ
vốn nên không so trực tiếp với portfolio −498,3117; nó chỉ cho biết các baseline
đã không bắt được một phần lớn drift tăng của cửa sổ này.

### 16.3 Shared-capital portfolio — gate cuối

Một account 100.000 USDT, sáu symbol, cùng global timeline và portfolio-risk:

| Baseline | Positions | PnL trước funding | Funding net | PnL sau funding | Engine PF | Quyết định |
| -------- | --------- | ----------------- | ----------- | --------------- | --------- | ---------- |
| reclaim_mr | 976 | −491,8332 | −6,4785 | **−498,3117** | 0,6863 | FAIL |
| trend_pullback | 3.810 | −878,1052 | −11,7486 | **−889,8537** | 0,7481 | FAIL |
| markdown_breakdown | 1.414 | −337,3395 | +3,5052 | **−333,8343** | 0,8512 | FAIL |

Các kết quả per-symbol dương của SOL/DOGE/ADA không sống được trong shared
capital. Do đó không được thêm leg nào vào portfolio/live. Funding chỉ cải thiện
markdown nhẹ vì short nhận carry trong snapshot này; không biến expectancy âm thành
dương.

### 16.4 Quyết định research

- **Không tune lại** ba baseline sau khi xem kết quả; làm vậy sẽ biến screening
  thành selection bias.
- `reclaim_mr` được giữ như candidate research riêng ETH/SOL, nhưng phải forward
  test và chạy portfolio nhỏ lại ở một cửa sổ mới trước khi cân nhắc.
- `trend_pullback` và `markdown_breakdown` bị dừng ở portfolio gate; chưa có quyền
  live/testnet.
- ETH directional MR cũ vẫn là leg duy nhất đang forward-test; default global và
  execution policy không đổi.
- Bước kế tiếp hợp lý là bổ sung feature crowding (basis, BTC beta, OI change,
  funding percentile, liquidation proxy) rồi kiểm tra **một** baseline mới trên
  cửa sổ dữ liệu mới; không mở thêm strategy đồng thời.

Unit tests sau implementation: **54/54 PASS**. `compileall`, 15 YAML cũ + 2 YAML
baseline, `pip check` và `git diff --check` đều phải giữ sạch trước khi deliver.

---

## 17. Wayfinder research map — 2026-08-22

Đã cài skill `wayfinder` và tạo local decision map tại
`research/wayfinder/MAP.md`. Map này chỉ lập route research, chưa tự động triển
khai strategy mới. Frontier hiện tại bắt đầu bằng việc chốt profitability gate,
data snapshot/split và crowding-funding contract; các quyết định ETH, altcoin,
TradFi, portfolio và forward-test bị block cho tới khi các ticket nền tảng được
giải quyết.

---

## 18. Multi-symbol scan matrix + TradFi tracker — 2026-08-23

### 18.1 Scan matrix top-20 crypto — **0/60 PASS**

Pipeline mới: `research/scan_matrix.py` (setup / run / report).

- Universe: top-20 thanh khoản trong snapshot 2026-08-21, lọc `onboard >= 700d`
  (BTC, ETH, XRP, SOL, ZEC, ONG, DOGE, ENA, BNB, 1000PEPE, BOME, SUI, ADA,
  LINK, ACE, WLD, BCH, NEAR, AVAX, AAVE).
- Dữ liệu: 15m ~70k bars/mã (2024-08 → 2026-08) trong `./catalog_live_crypto`;
  ETH đã backfill đủ 2 năm (fix tz-naive bug tại `data/download.py`).
- Funding bundles riêng cho scan: `funding_data/scan_2026` (20 mã × 730 ngày).
- WF: 3 baselines frozen × 20 mã × 6 folds = 360 backtest (~20 phút, 2 workers).
- Gates: folds dương ≥5/6, exp sau funding > 0, PF > 1.1, PnL > buy-and-hold,
  **BH-FDR q ≤ 0.10** trên sign-test từng combo (58 combos testable).

**Kết quả: không combo nào qua gate.** Top theo p-value:

| Combo | Folds+ | Exp sau funding | PF | PnL | Buy&Hold | p | q |
| ----- | ------ | -------------- | -- | --- | -------- | - | - |
| reclaim_mr NEARUSDT | 4/6 | +0.148 | 1.46 | +26.95 | −152.43 | 0.344 | 1.0 |
| trend_pullback BOMEUSDT | 4/6 | +0.128 | 3.35 | +99.72 | −51.84 | 0.344 | 1.0 |
| markdown_breakdown ADAUSDT | 4/6 | +0.039 | 1.14 | +13.64 | +228.03 | 0.344 | 1.0 |
| reclaim_mr SOLUSDT | 3/6 | +0.037 | 1.18 | +6.68 | −36.33 | 0.656 | 1.0 |

Đọc kỹ kết quả:

1. Ba "PASS sơ bộ" cũ (SOL reclaim, ADA markdown, DOGE pullback ở 3-fold cũ)
   **không giữ được** trên cửa sổ 2 năm + gate chặt → xác nhận chúng là noise
   level, đúng cảnh báo multiple-testing.
2. ETH reclaim_mr **âm** trên window mới (exp −0.15 vs +0.065 run trước) vì fold
   composition khác (full 2024–2026). Edge ETH mỏng phụ thuộc giai đoạn.
3. ZEC buy-and-hold +3068 USDT cho thấy benchmark BH quan trọng: nhiều "lãi"
   nhỏ vẫn thua xa chỉ cần hold.
4. Không promote gì thêm; default global và ETH directional MR forward-test
   (§12) giữ nguyên.

Artifacts: `results/scan_matrix/20260823T051806Z/` (`index.json`, `report.json`,
per-combo JSONs), config `config/research_scan_top20.yaml`.

Quy trình chạy lại khi có data mới:

```bash
python -m research.scan_matrix setup --top 20          # refresh universe/config
python main.py download --config config/research_scan_top20.yaml
python -m research.download_funding <symbols...> --output-dir funding_data/scan_2026
python -m research.scan_matrix run --config config/research_scan_top20.yaml --folds 6 --workers 2
python -m research.scan_matrix report --scan-dir results/scan_matrix/<stamp>
```

### 18.2 TradFi accumulation tracker ✅

`research/tradfi_accumulate.py` — chạy hàng tuần, append vào
`research_snapshots/tradfi_history.csv` + snapshot JSON per ngày.

Lần đầu (2026-08-23): **71 eligible TradFi perps, 0 sẵn sàng research**
(gate 365 ngày). Gần nhất:

| Symbol | Còn thiếu | Volume 24h |
| ------ | --------- | ---------- |
| XAUUSDT (vàng) | ~110d | $173M |
| XAGUSDT (bạc) | ~137d | $83M |
| TSLAUSDT | ~158d | $10M |
| MSTRUSDT | ~170d | $56M |
| COINUSDT | ~170d | $13M |

→ Sẵn sàng research cổ phiếu/vàng-bạc trên Binance từ khoảng cuối 2026.
Khi đủ gate: chạy đúng pipeline §18.1 (frozen baselines, session gate fail-closed).

```bash
python -m research.tradfi_accumulate   # weekly
```

---

## 19. Sprint 24h — Quant Research Loop (2026-08-23, A1 verdict)

**Sprint verdict: `PIPELINE_PASS_CANDIDATE_FAIL`** — pipeline end-to-end chạy được,
tái lập được; 0/77 combo PASS Stage A → hệ thống loại đúng false edge.

### Đã hoàn thành
- Contracts freeze (`contracts/`): manifest 29 trường, canonical metrics
  null+reason (hết bug dd=0 mặc định), gates G0–G5 machine-readable,
  scorecard 100 điểm, budget ≤3 hypotheses/≤2 strategy/≤16 combo/≤2 iterations.
- Matrix resumable (`research/matrix_runner.py`): Tier0 + Tier1, cell fail
  cô lập, REUSED theo identity hash.
- **77/77 cells COMPLETED, 0 PIPELINE_ERROR**: 49 cells (7 frozen strategies ×
  7 mã S0) + 28 cells (H-VOLCOMP-BRKOUT-v1: squeeze→Donchian breakout, 4 combo).
- Registry append-only `results/registry/experiments.jsonl`: 79 entries.
- Reproducibility: rerun markdown_breakdown ADAUSDT khớp tuyệt đối
  (139 trades, PnL 10.863531 sau funding, digest folds identical) → G2 PASS.
- LIVE guard: giữ nguyên; audit 13 đường dẫn + 11 test; 2 lỗ hổng P0 documented
  (chưa fix — ngoài scope).

### Kết quả nghiên cứu (đều sau funding, S0 1 năm, 3 fold chronological)
- 0/77 PASS Gate Stage A. Không có survivor → không có portfolio/Tier 2.
- Best existing: markdown_breakdown ADAUSDT exp +0.078 / PF 1.36 / 139 trades
  nhưng FAIL `fold_concentration_high`; breakout BNBUSDT exp +0.321 nhưng chỉ
  47 trades và concentration FAIL.
- H-VOLCOMP-BRKOUT-v1: **REJECTED** — 26/28 exp âm; 2 cells BNB dương nhờ 1 fold
  duy nhất. Negative result được lưu nguyên vẹn (candidate.yaml state=REJECTED).
- Iteration 2 không mở: insight từ fold S0 dùng để gate lại chính S0 = in-sample;
  chờ capture S1 untouched.

### Bài học sprint
1. `fold_concentration_high` là lý do FAIL phổ biến nhất — xác nhận thiết kế
   gate chống "một kỳ may" là đúng và cần đọc kỹ trước khi tin bất kỳ exp dương.
2. Bug metric mặc định 0.0 (drawdown) đã bị test hồi quy chặn — mọi metric thiếu
   phải là null + reason code.
3. Silent-skip download (bẫy W1) giờ fail-loud có reason `catalog_not_current`.

### Backlog
P0: fix 2 LIVE-guard holes · capture S1 · P1: two-tick slippage + delayed-fill
model, BTC-beta-neutral benchmark · P2: native intrarun funding, DSR/PBO.

Artifacts: `research/wayfinder/evidence/sprint-24h-20260823.md`,
`results/stage_a/`, `results/matrix/`, `results/registry/experiments.jsonl`.
