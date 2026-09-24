# REVIEW.md — SHADOW-PAPER-REVIEW-V1 (tổng hợp A1, 2026-09-24T12:25Z)

Cycle review-only: 0 scored cell, không đụng sleeve đang chạy, không heavy
job (lock máy bị CHR3F/data-staging giữ suốt phiên — không liên quan).
Nguồn: 3 lane report trong thư mục này (mọi số truy về artifact tại chỗ)
+ DASHBOARD-AND-SHADOW-RELIABILITY-V1 (đo sáng nay). Phạm vi "cải thiện"
= ý kiến theo tính khoa học kinh tế; KHÔNG gì được implement trong cycle
này.

## 1. Bảng trạng thái 7 sleeve (đo 2026-09-24 từ byte ledger)

| Sleeve | Nhân tố kinh tế | Trạng thái prospective | Vấn đề lớn nhất (mới đo) |
|---|---|---|---|
| XSECT-FUND-CARRY-7D (crypto, daily) | funding carry = premium nhận rủi ro hội tụ funding | 10/10 quyết định OK, 48 fill, booked **−298.22** (fee 246.43 + slip 56.40 vs funding +4.60), equity 99,662.87, MDD 4.83% | Cost drag run-rate ~11%/năm ăn gần hết carry (~1.7%/năm) → đang trả spread, không thu premium |
| ILLIQ-AMIHUD-28D-W (crypto, weekly) | premium phi thanh khoản (Amihud) | 1 quyết định (09-21), 8 fill, +0.08%, MDD 3.73% | Sự kiện tuần 09-15 **không bao giờ được sinh** (scheduler neo tuần từ 00:00 ngày start) — mất 1 quan sát, không có record; chạy prospective khi prior gating đã FALSIFIED + cơ chế INVERTED ở S0R 2024-08..2025-08 |
| BASISLV-PREMFADE-28D (crypto, weekly) | basis premium fade = limits-to-arbitrage / roll premium | 1 DATA_BLOCKED fail-closed đúng luật (gap vendor 286 bar), nguồn đã heal, kế 09-28 | 1 hole vendor = 1 tuần thông tin mất vĩnh viễn (event_id đã đốt) |
| BTC4H-BANDRIDGE (BTC, H4) | breakout/regime switching giữa band và bridge | 56 fail-closed (forward-only đúng) + 1 OK no-trade, **0 fill** | w=1.0 không fill được dưới chi phí dương (packet A/B/C chờ owner); **mới phát hiện: identity pin 6 bps/side nhưng executor tính 5 bps + 1 tick** — phải chốt TRƯỚC fill đầu |
| EURUSD RANGEFADE-2M (H1) | liquidity provision tại mép prior-day-range, chống stop-flow | RUNNING (LONG 1.5 lot từ 12:00Z, −$48 MTM), parity 22/22, 11 boots | **SHORT-BETA CONTROL CHƯA MOUNT** dù ancestor ghi MANDATORY (SHORT_ALWAYS +314 pips beat C3 trên cùng holdout) |
| GBPUSD RANGEFADE-2M (H1) | như trên | RUNNING (LONG 1.5 lot, −$31.5), mount ĐÚNG conviction config (digest khớp FX-MAJORS C3) | Cùng gap short-beta control; chung 1 tài khoản + nguồn TrueFX với EURUSD |
| XAUUSD swing (bar-driven) | momentum/vol-floor, chu kỳ nhiều năm | worker sống 2d23h, 75/75 MTM, 0 entry, 0 gap, FLAT 100k | Tần suất entry ~**1 lần/5.1 năm** (9 intents/12,337 bar replay) → sleeve prospective KHÔNG BAO GIỜ tự đủ bằng chứng keep/kill |

## 2. Phán xét cấu trúc chương trình (lane_portfolio_program)

1. **Không có luật promote/kill/time-stop nào được preregistered** ở cả 3
   plan (PSV1 §7 "no pass/promotion claim"; FX "later governance"; XAUUSD
   "indefinite"). Dữ liệu prospective đang tích lũy mà không có luật phán
   xét trước — mỗi ngày trôi là tăng rủi ro post-hoc khi owner buộc phải
   quyết bằng mắt.
2. **Sức mạnh thống kê**: cửa sổ 52 tuần chỉ phân biệt được edge Sharpe
   thường niên ≥ ~2.0 ở 2σ. ILLIQ/BASISLV (weekly, n≈52 quyết định) và
   BANDRIDGE (0 fill) nằm dưới ngưỡng power của lớp edge PF~1.3–1.5. Chỉ
   FX (~350 round trip/năm kỳ vọng) và XSECT (daily) có mật độ thông tin
   đủ để tự phán xét trong <1 năm.
3. **Portfolio thực tế = 6 tài khoản × $100k = $600k** (EURUSD+GBPUSD
   chung 1 TK), equal-notional ≠ equal-risk: 4/7 sleeve cùng nhân tố
   crypto (BANDRIDGE long-only BTC w≈1.0; XSECT hưởng funding credit cùng
   regime bull), 2 sleeve FX cùng nhân tố USD không cap same-side, không
   có risk aggregation, không per-sleeve Sharpe trên dashboard, XAUUSD
   out-of-view.
4. **Phụ thuộc dữ liệu single-source**: TrueFX 15s cho cả 2 sleeve FX
   (mất nguồn = 2 sleeve chết cùng lúc), Binance cho crypto; bài học
   BASISLV 286-bar gap. LIVE-DATA-GATEWAY-V1 đã qua 24h sạch, chờ owner
   G3 cutover.
5. **Cost book**: CURRENT_CONSERVATIVE_COST (fee 0.05%, slip 1 tick) là
   "declared" chứ chưa phải "measured-stress" — bài học funding measured
   11.798%/năm = 7.8× frozen constant (BTC-H4-EDGE-SEARCH-V1).

## 3. Ý kiến cải thiện theo tính khoa học kinh tế

### 3.1 OWNER_DECISION_REQUIRED (chặn thông tin / đổi luật)

- **O1 — Chốt packet BANDRIDGE**: khuyến nghị **sizing B (cost-aware,
  realized ≈0.99946)** + **fill law A (doc hóa bar 15m hoàn tất đầu
  tiên)**. Chọn A(sizing) = sleeve $100k đứng yên vĩnh viễn = informational
  suicide; chọn C = phá định thức no-leverage. BANDRIDGE hiện là sleeve
  "info = 0 theo cấu trúc".
- **O2 — Reconcile identity 6 bps vs executor 5 bps + 1 tick** (mới phát
  hiện, lane_crypto §spec) — phải chốt một bên và re-pin TRƯỚC fill đầu
  tiên, nếu không mọi PnL prospective sau này gắn nhầm cost law.
- **O3 — XAUUSD sample-size law**: đề xuất KILL_UNFUNDABLE nếu 0
  TARGET_INTENT đến 2028-09-21 + checkpoint tuần study-side replay
  (identity-identical, không đổi sleeve). Kinh tế học: vốn $100k cơ hội
  bằng 0 với P(≥1 entry/năm) ≈ 17.8% — sleeve này cần luật thời gian,
  không đợi thống kê trades.
- **O4 — Preregister promote/kill/time-stop theo n-quyết-định (SPRT /
  Bayes posterior)** cho mọi sleeve NGAY bây giờ, trước khi dữ liệu tích
  thêm — đây là bước chống post-hoc rẻ nhất chương trình.
- **O5 — Quyết định trạng thái ILLIQ**: gating ancestor FALSIFIED +
  inversion S0R — nếu shadow xác nhận đảo chiều, family này cần luật định
  trước (không phải "xong rồi tính").
- **O6 — Gateway cutover** (LIVE-DATA-GATEWAY-V1 đã sạch 24h) — giảm
  single-source risk Binance cho 4 sleeve crypto.

### 3.2 AMENDMENT_REQUIRED (đụng identity/frozen spec, không đổi exposure)

- **A1 — Mount short-beta control arm cho FX RANGEFADE** (ancestor ghi
  MANDATORY; hiện CHƯA có — không thể tách edge range-fade khỏi short-beta
  USD; đây là gap compliance lớn nhất phía FX).
- **A2 — Giảm turnover XSECT carry**: entry/exit hysteresis theo ngưỡng
  funding differential (chỉ rebalance khi |Δfunding| vượt band) — cơ chế:
  carry premium quy mô ~vài bps/ngày không sống nổi cost 2×(fee+slip)
  mỗi lần xoay; đây là改进 cấu trúc, không phải tweak.
- **A3 — Scheduler tuần cho 2 sleeve weekly**: neo epoch thay vì 00:00
  ngày start + probe dữ liệu T−1h trước giờ quyết định (đỡ đốt event_id
  như BASISLV).
- **A4 — Back-port daily re-freeze vào plan XAUUSD** (code đang chạy
  daily, plan vẫn ghi 1h bars — doc-drift identity).

### 3.3 ENGINEERING_ALLOWABLE (không đổi exposure)

- **E1 — Thêm per-fill realized_pnl vào schema ledger** (win-rate
  round-trip hiện là NOT_RUN vì không tách được).
- **E2 — STRESS_COST book song song** (slippage đo được cho ILLIQ/BANDRIDGE,
  FX spread ×2) — hiển thị kên declared cost, không thay cost chính.
- **E3 — Gap-telemetry weekly** cho mọi nguồn (bài học BASISLV), banner
  sources-health trên dashboard.
- **E4 — Per-sleeve Sharpe/PnL-attribution + aggregate crypto-beta cap
  hiển thị** trên dashboard (việc CAP thật là owner).
- **E5 — Registry hygiene**: PSV1 head 99e0026 và FX 4bdfd0e đã STALE vs
  measured — A1-side update.
- **E6 — Assert độ dài history khi fetch_daily_bars(last_n=300)** (EODHD
  ignore param, trả 12.5k bar — silent divergence).

## 4. Thứ tự hành động đề xuất (theo giá trị thông tin/tổng chi phí)

1. O1+O2 (mở khóa BANDRIDGE, chốt cost identity) — sleeve từ info=0 →
   observable ngay mốc H4 kế tiếp.
2. O4 (preregister luật phán xét) — rẻ nhất, chống post-hoc cho toàn bộ.
3. A1 (short-beta control FX) — không có nó, mọi PnL FX/month không diễn
   giải được nhân tố.
4. A2 (turnover carry) — sleeve duy nhất đang "đo cost thay vì đo edge".
5. O3 (XAUUSD time-law) + A3/A4 + E1..E6 theo lịch kỹ thuật.

## 5. Giới hạn trung thực

- Review dựa trên artifact có tại 2026-09-24T12:2xZ; sleeve đang chạy nên
  các số là ảnh chụp.
- Verify độc lập replay 9-intent của XAUUSD: NOT_RUN trong lane (thiếu
  EODHD_API_KEY trong môi trường lane) — dùng số audit có sẵn.
- Cycle này không tính lại scored cell nào của bất kỳ ancestor nào; mọi
  verdict ancestor giữ nguyên theo registry.
