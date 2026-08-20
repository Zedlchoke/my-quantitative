# GHI CHÚ DỰ ÁN — my-quantitative

> File này tổng hợp toàn bộ những gì đã làm và kế hoạch sắp tới.
> Cập nhật lần cuối: sau khi build xong 3 strategy + optimizer + multi-symbol.

---

## 1. Hệ thống là gì

Bot giao dịch định lượng crypto futures trên **NautilusTrader** (v1.231.0).

**Giả định chuẩn (đã chuẩn hoá):**

| Mục | Giá trị |
|---|---|
| Sàn / sản phẩm | Binance **USD-M perpetual** |
| Mã mặc định | `BTCUSDT-PERP`, `ETHUSDT-PERP` (multi-symbol) |
| Chế độ vị thế | **one-way / netting** (`oms_type: NETTING`) |
| Môi trường | **Testnet / Demo — không tiền thật** |
| Guard | `LIVE` bị chặn cứng trong config |
| Khung dữ liệu | 15 phút (`15-MINUTE-LAST-EXTERNAL`) |

**USD-M ↔ COIN-M** là 1 nút config: đổi `market.account_type` → `COIN_FUTURES`
(+ `symbols`/`base_currency`).

---

## 2. Kiến trúc đã build

```
main.py                      CLI: download / backtest / live
strategy_base.py             base chung: risk, order, daily limits, shutdown
strategy.py                  EMA-ATR trend following
strategy_mean_reversion.py   Bollinger + RSI + VHF (mean-reversion)
strategy_regime_switch.py    VHF chọn trend vs mean-reversion
strategy_factory.py          build strategy theo strategy_type
config/
  settings.py                typed settings + YAML loader
  research.yaml              research EMA-ATR (default)
  research_mean_reversion.yaml
  research_regime_switch.yaml
  live.yaml                  live (Testnet/Demo)
data/
  catalog.py                 ParquetDataCatalog wrapper (BinanceBar)
  download.py                pipeline tải lịch sử (multi-symbol)
backtest/
  engine.py                  backtest engine (phí + slippage, multi-symbol)
reports/
  performance.py             summary + CSV/JSON (mỗi mã 1 thư mục)
research/
  optimize.py                grid-search optimizer (song song)
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

| strategy_type | Ý tưởng | Mạnh | Yếu |
|---|---|---|---|
| `ema_atr` | EMA crossover + trend EMA 200 + ATR trailing stop | trend mạnh | cưa khi đi ngang |
| `mean_reversion` | chạm Bollinger + RSI quá bán/mua, trong chế độ ranging (VHF) | đi ngang | thua khi breakout |
| `regime_switch` | VHF chọn trend vs mean-reversion | bù cả 2 chế độ | VHF chưa đủ chính xác |

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

- Testnet Binance có **~2 năm** dữ liệu lịch sử.
- Hiện đã tải **180 ngày** (≈ 17,279 bar 15m) cho `BTCUSDT` + `ETHUSDT` vào `./catalog`.
- Để mở rộng: sửa `data.lookback_days` trong research config rồi `python main.py download`.

---

## 6. Kết quả hiện tại (để so sánh sau)

### 30 ngày (backtest đơn)
| Strategy | BTCUSDT PnL | Win rate |
|---|---|---|
| ema_atr | -3.73 | 34.5% |
| mean_reversion (cũ: revert-to-mean) | -3.93 | 55.6% |
| mean_reversion (TP 1.5R + stop 1.0) | -7.53 | ~44% |

### Optimizer 180 ngày (2 mã, xếp theo expectancy)
| stop | TP | vhf_max | trades | expectancy | PF | positive_cells |
|---|---|---|---|---|---|---|
| 2.0 | 2.5 | 0.25 | 259 | **+0.183** | 1.12 | 1/2 |
| 2.0 | 2.0 | 0.25 | 264 | +0.103 | 1.07 | 1/2 |
| 2.0 | 1.5 | 0.25 | 280 | +0.064 | 1.04 | 1/2 |

> ⚠️ `positive_cells 1/2` = chỉ 1 trong 2 mã dương → chưa vững, cần walk-forward.

---

## 7. Kế hoạch sắp tới

### Bước 1 — Walk-forward nhanh ✅ ĐÃ LÀM (261s, 288 backtest, 3 fold × 2 mã)
```bash
python -m research.optimize --config config/research_mean_reversion.yaml \
    --grid quick --folds 3 --min-trades 15
```
**Kết quả top combo `stop=2.0 / TP=2.5 / vhf=0.25` — chi tiết theo mã × fold:**

| Mã | F0 (cũ nhất) | F1 | F2 (mới nhất) | Nhận xét |
|---|---|---|---|---|
| BTCUSDT | +0.273 (PF 1.22) | **-0.189** (0.90) | **-0.201** (0.81) | chỉ thắng 1/3 fold |
| ETHUSDT | +0.591 (1.32) | +0.403 (1.30) | +0.302 (1.15) | **dương 3/3 fold** |

**KẾT LUẬN BƯỚC 1:**
- Edge mean-reversion nằm ở **ETHUSDT** (ổn định 3/3 fold, PF 1.15–1.32).
- **BTCUSDT không vững** — chỉ thắng fold đầu, 2 fold sau âm.
- → **KHÔNG promote làm default chung.** Phải tách theo mã: dùng cho ETH,
  hoặc cần thêm bằng chứng riêng cho BTC.

### Bước 2 — Mở rộng dữ liệu 12 tháng ✅ ĐÃ LÀM (35,039 bar/mã, 6 fold × 61 ngày)
Tải 365 ngày BTC + ETH, walk-forward 6 fold cho ETH (top-3 combo):

**`stop=2.0 / TP=2.5 / vhf=0.25` theo fold (ETHUSDT):**

| Fold | Expectancy | PF | Win rate | n |
|---|---|---|---|---|
| F0 | +2.103 | 2.71 | 0.53 | 34 |
| F1 | **-0.889** | 0.64 | 0.35 | 46 |
| F2 | **-1.145** | 0.55 | 0.32 | 47 |
| F3 | +0.666 | 1.36 | 0.39 | 36 |
| F4 | +0.414 | 1.30 | 0.49 | 49 |
| F5 | +0.323 | 1.17 | 0.48 | 48 |
| **Tổng** | **4/6 dương** | avg exp +0.141 | | |

**KẾT LUẬN BƯỚC 2 — ETH cũng KHÔNG vững tuyệt đối:**
- 4/6 fold dương, nhưng có **2 fold liên tiếp âm nặng (F1, F2)** ở giữa giai đoạn.
- Trên 365 ngày, mean-reversion chỉ "ăn" ở một số giai đoạn, thua liên tục ~4 tháng
  ở giữa. Đây đúng là đặc tính **phụ thuộc regime**: khi thị trường vào trend,
  mean-reversion thua, và VHF 0.25 không lọc hết.
- → **Edge yếu, không đạt chuẩn "vững".** KHÔNG nên chạy live chỉ dựa vào mean-reversion.

**So sánh nhanh 3 combo (ETH, 6 fold):**

| stop | TP | positive folds | avg exp |
|---|---|---|---|
| 2.0 | 2.5 | 4/6 | +0.141 |
| 2.0 | 2.0 | 4/6 | +0.183 |
| 1.5 | 2.5 | 3/6 | +0.206 |

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

### Cải thiện tiềm năng khác (chưa làm)
- [ ] Thêm ADX/volume vào regime filter (thay VHF đơn lẻ).
- [ ] Optimizer cho `ema_atr` (grid fast/slow/trend EMA).
- [ ] Thêm chỉ số drawdown / Sharpe vào bảng xếp hạng optimizer.
- [ ] Cache kết quả optimizer ra CSV để resume giữa chừng.
- [ ] Chạy trên nhiều core hơn (máy hiện chỉ 2 core).
- [ ] Thêm Mô hình Tối ưu hóa Vốn & Danh mục.
- [ ] Thêm Mô hình Xử lý Nhiễu & Tương quan.
- [ ] Thêm Mô hình Dự báo Biến động & Xác suất Rủi ro.
- [ ] Thêm Mô hình Xác suất Ẩn.
- [ ] Phân tích nhiều mã, qua cả các mã cổ phiếu chứ không riêng BTC và ETH.
- [ ] Phân chia ra nhiều danh mục Bot cho nhiều việc khác nhau(Nhóm Bot Tìm kiếm Tín hiệu, Nhóm Bot Thực thi lệnh (Execution Bots), Hệ thống Quản trị Rủi ro (Risk Management), Hệ thống Tối ưu Danh mục (Portfolio System)). Mỗi bot sẽ có một mô hình toán học khác nhau ưu việt nhất để xử lý thông tin.
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
python -m research.optimize --config config/research_mean_reversion.yaml --grid quick
python -m research.optimize --config config/research_mean_reversion.yaml --grid quick --folds 3 --workers 2
```

---

## 9. Ghi chú kỹ thuật đã xử lý

- **Volume precision mismatch:** Binance kline volume có 3 chữ số thập phân trong
  khi instrument `size_precision=4` → matching engine từ chối. Đã fix bằng cách
  chuẩn hoá volume khi load trong `data/catalog.py`.
- **Path chứa dấu cách (Windows):** `DataCatalogConfig.as_catalog()` mã hoá `%20`
  → đăng ký `ParquetDataCatalog` trực tiếp thay vì qua config.
- **Download engine:** kernel clock = 0 + instrument provider chưa load → set clock
  + `load_ids()` thủ công trước khi request.
- **Tốc độ optimizer:** cache bars mỗi mã + chạy song song (`--workers`, mặc định
  = số core). Máy 2 core chỉ nhanh tối đa ~2x.

---

## 10. Lưu ý an toàn

- API key trong `.env` là **testnet** — không bao giờ đặt key live.
- `.env`, `catalog/`, `results/` đã được gitignore.
- Hệ thống **chặn cứng** môi trường `LIVE`.



