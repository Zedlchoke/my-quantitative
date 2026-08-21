# GHI CHÚ DỰ ÁN — my-quantitative

> File này tổng hợp toàn bộ những gì đã làm và kế hoạch sắp tới.
> **Cập nhật lần cuối:** 2026-03 — MR ETH directional WF 3/3 PASS; kế hoạch forward-test
> 6–8 tuần + Testnet ghi tại §12.

---

## 1. Hệ thống là gì

Bot giao dịch định lượng crypto futures trên **NautilusTrader** (v1.231.0).

**Giả định chuẩn (đã chuẩn hoá):**


| Mục            | Giá trị                                       |
| -------------- | --------------------------------------------- |
| Sàn / sản phẩm | Binance **USD-M perpetual**                   |
| Mã mặc định    | `BTCUSDT-PERP`, `ETHUSDT-PERP` (multi-symbol) |
| Chế độ vị thế  | **one-way / netting** (`oms_type: NETTING`)   |
| Môi trường     | **Testnet / Demo — không tiền thật**          |
| Guard          | `LIVE` bị chặn cứng trong config              |
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
- [ ] Thêm Mô hình Tối ưu hóa Vốn & Danh mục.
- [ ] Thêm Mô hình Xử lý Nhiễu & Tương quan.
- [ ] Thêm Mô hình Dự báo Biến động & Xác suất Rủi ro.
- [ ] Thêm Mô hình Xác suất Ẩn.
- [ ] Phân tích nhiều mã, qua cả các mã cổ phiếu chứ không riêng BTC và ETH.
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
python -m unittest discover -s tests   # 29 tests pass
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
- **Không live tiền thật** — Testnet/Demo only; `LIVE` vẫn bị chặn cứng.

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
python main.py download --config config/research_mean_reversion_eth_directional.yaml
python -m research.oos_validate --config config/research_mean_reversion_eth_directional.yaml --holdout-days 60
```

**Ghi log hàng tuần** (NOTES hoặc bảng riêng):

| Tuần | Ngày chạy | Trades OOS | Exp | PF | PnL | Ghi chú thị trường |
| ---- | --------- | ---------- | --- | -- | --- | ------------------ |
| W1 | | | | | | |
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
- Hệ thống **chặn cứng** môi trường `LIVE`.

