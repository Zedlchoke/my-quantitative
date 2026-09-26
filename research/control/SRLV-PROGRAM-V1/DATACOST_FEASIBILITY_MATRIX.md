# DATACOST_FEASIBILITY_MATRIX — SRLV-PROGRAM-V1 (per-pair, đo tại survey 2026-09-26)

- Mục đích: input cho data/license/PIT/cost/power gate **riêng từng cặp**
  (owner instruction 2026-09-26). Cặp thiếu nguồn hợp lệ ⇒ `BLOCKED_<reason>`,
  không âm thầm thay cặp, không "tạm dùng" nguồn khác.
- Ký hiệu cột: D=data có sẵn; L=license; PIT=observable constructible;
  C=cost book; P=power. Mỗi ô ghi `OK | PARTIAL | BLOCKED | NOT_RUN` + dẫn chứng.

## 1. FOREX

| Cặp | D (source, bid/ask, coverage) | L (license) | PIT | C (cost) | P (power) | Verdict sơ bộ |
|---|---|---|---|---|---|---|
| EURUSD | OK — Dukascopy M1 BID+ASK 2021-01..2026-06 (2,007 files/side, 0 missing) | OK-with-posture (OWNER_DIRECTIVE + TCU_RISK_DISCLOSED) | PARTIAL — M1 event-time OK; KHÔNG có tick/order-book; mọi sweep/zone = proxy | PARTIAL — spread curve đo (p50 0.3 pip); commission/slippage DECLARED_UNMEASURED | NOT_RUN — phải chạy power analysis tại freeze | `ELIGIBLE_RESTRICTED` — chỉ ancestry/fixture/cost authority (outcome-exposed toàn window). KHÔNG phải dev/OOS |
| GBPUSD | OK — 2021-01..2026-09 (2,092 files/side, manifest fxm.m1_manifest@1) | như trên | như EURUSD | PARTIAL — spread p50 0.8 pip; phần còn lại DECLARED | NOT_RUN | `ELIGIBLE_RESTRICTED` (như EURUSD) |
| USDJPY | OK — như GBPUSD; scale 1e-3/pip 0.01 probe-proven | như trên | như EURUSD | PARTIAL — spread p50 0.5 pip; carry-beta control MANDATORY (tiền lệ FX-MAJORS) | NOT_RUN | `ELIGIBLE_RESTRICTED` (như EURUSD) |
| AUDUSD | OK — 2021-01..2026-06 (2,007 files/side, sha manifest); dev exposed cho range-fade class | như trên | PARTIAL — như trên; observable MỚI phải qua D2 | PARTIAL — conditional crossing đo 0.9/1.0 pip; stressed RT 3.6; ceiling law: band phải rõi ~2× stressed RT (~7 pips) | NOT_RUN | `ELIGIBLE_DEV_FOR_NEW_OBSERVABLE` — dev được cho identity mới; holdout 2026-H1 SEALED |
| USDCAD | OK — như AUDUSD | như trên | như AUDUSD | PARTIAL — crossing 1.1/1.2; stressed RT 4.4 | NOT_RUN | `ELIGIBLE_DEV_FOR_NEW_OBSERVABLE` (như AUDUSD) |
| USDCHF | BLOCKED — không có corpus ở bất kỳ worktree nào; data gate chưa từng chạy | NOT_RUN — cần posture quyết (Dukascopy owner-directive mở rộng hay TrueFX/OANDA) | NOT_RUN | BLOCKED — không có spread curve đo | NOT_RUN | `BLOCKED_DATA_LICENSE` — replication-transfer surface; mở theo R4 (sau khi một identity qua dev gates) + data gate đầy đủ |
| (nguồn độc lập mọi cặp) | BLOCKED — TrueFX/OANDA/consent = 0 bytes | NOT_RUN — owner R2 | — | BLOCKED — IBKR: two-sided NOT_SUBSCRIBED, commission/swap NOT_RUN ⇒ all-in CHƯA ĐO (minTick 0.5 pip chỉ là fact hình học tick, không suy ra được all-in) | — | `BLOCKED_SOURCE_AUTHORITY` — đúng các reopening condition R1/R2/R3 |

**Kết luận FX (frontier):** trên panel hiện có (Dukascopy M1, 3 cặp exposed
trọn window + 2 cặp exposed-dev + USDCHF trống), KHÔNG có nguồn/bề mặt mới
nào chưa bị tiêu. Việc chạy scoring cho bất kỳ cơ chế S/R–sweep–vol nào trên
panel cũ = tái chạy không gian đã đóng (VIABILITY: NO_CANDIDATE, "zero
remainder"). **SRLV-FX chỉ mở scoring khi một trong R1–R5 có bằng chứng bytes
+ authority** (master plan §6).

## 2. CRYPTO

| Cặp | D | L | PIT | C | P | Verdict sơ bộ |
|---|---|---|---|---|---|---|
| BTCUSDT | OK — Vision um 1h 2020-01..2026-08 (80 zips); catalog 15m 2024-08..2026-08 (CHR3F đã score) | PARTIAL — keyless public archive, posture PIT_USABLE kế thừa; license text chưa capture ⇒ data gate phải ghi posture từng nguồn | PARTIAL — kline event-time OK; funding PIT theo settlement; KHÔNG order-book/liq/OI ⇒ sweep/zone = PROXY_NOT_ORDERBOOK | PARTIAL — funding MEASURED (11.798%/yr BTC); fee 5 bps + 1 adverse tick = DECLARED book (venue-published tier floor + convention tick, freeze từ CHR3F; chưa validate vs fills — Q-8); spread/slippage cần census theo giờ fill từ bookTicker/aggTrades (verify coverage); thiếu ⇒ BLOCKED | NOT_RUN | `ELIGIBLE_DEV_ANCESTRY_EXPOSED` — dev được với ancestry disclosure; KHÔNG phải OOS |
| ETHUSDT | OK — 1h + funding 2020-01..2026-08 (ETH archive local, 7,305 settlements floor-exact); 15m catalog 2024-08+ (verify exposure) | như trên | như BTC | PARTIAL-STRONG — funding measured; ETH-V1 đã đo funding floor-exact | NOT_RUN | `ELIGIBLE_DEV_ANCESTRY_EXPOSED` — VA CHẠM: ETHUSDT-OPEN-SEARCH-V2 đang ACTIVE chờ GO; không tiêu surface S1 của nó |
| SOLUSDT | OK — 1h 2020-09..2026-08 (floor 2020-09-14); funding floor 2020-09-13 | như trên | như BTC | PARTIAL — funding measured qua fapi (conflict ⇒ exclude symbol-month); spread census NOT_RUN | NOT_RUN | `ELIGIBLE_DEV_BASELINE_EXPOSED` — exposure chỉ ở mức xsect baselines; identity mới được dev với disclosure |
| BNBUSDT | OK — 1h 2020-02..2026-08 (floor 2020-02-10) | như trên | như BTC | như SOL | NOT_RUN | `ELIGIBLE_DEV_BASELINE_EXPOSED` (như SOL) |
| (4 cặp, plane 15m/1m mới) | PARTIAL — Vision có monthly zips mọi gran; local chưa stage; download = data gate mới | như trên | như trên | spread census NOT_RUN | NOT_RUN | `ELIGIBLE_RECLK_ANCESTRY_EXPOSED` — cùng lịch sử giá đã outcome-exposed ở 1h; plane mới chỉ dùng làm `ANCESTRY_EXPOSED_DEV` (re-clock veto Q-3); KHÔNG phải OOS |

**Kết luận CX:** frontier KHÔNG đóng như FX, nhưng (i) mọi cơ chế
sweep/absorption bắt buộc nhãn `PROXY_NOT_ORDERBOOK` và qua fictional-
counterpayer veto; (ii) funding measured là cost book bắt buộc (dual-book:
frozen constant + measured path); (iii) G5 fold-concentration 0.50 đo là
structurally unpassable cho BTC-long 2020-2026 ⇒ cơ chế long-biased phải
chứng minh short-capability hoặc chỉ định nghĩa trên prospective; (iv)
S1 mọi cycle sealed — OOS thật có thể chỉ còn prospective accumulation
sau freeze (verify tại GO-1).

## 3. Thành phần cost bắt buộc theo track (thiếu ⇒ fail-closed)

### 3.1 FOREX (mỗi cặp, mỗi cơ chế)
1. Spread event-time: session/rollover spread curve đo được tại fill-bar ×
   k ∈ {1.0, 1.5, 2.0} (sha-pinned census; không global median).
2. Spread giãn lúc phá mức: cost curve điều kiện THEO PHÂN PHỐI FILL CỦA CHÍNH
   CƠ CHẾ (Q-2/Q-8; range-edge fade fill đúng lúc spread giãn — P3-A precedent).
3. Commission: hiện `DECLARED_UNMEASURED` — chỉ được vào "declared book",
   không bao giờ override measured book; mở measured khi R1 Flex statement có.
4. Slippage/adverse selection: `DECLARED_UNMEASURABLE_ON_M1_BIDASK` — named
   class, stress-covered, không assume maker/mid.
5. Financing: structural-zero bằng force-flat fixture (flat trước rollover,
   weekend); nếu R3 mở financing band measured ⇒ multi-day hold class mới.
6. Ceiling: expected gross premium/holding period vs full RT stress cost —
   nếu ceiling âm ⇒ VETO trước scoring (VOL-NG1 precedent).

### 3.2 CRYPTO (mỗi cặp, mỗi cơ chế)
1. Fee: **DECLARED book** — taker 5 bps + 1 adverse tick là frozen declared
   book của CHR3F (venue-published tier floor + convention tick; Q-8: giá
   công bố = DECLARED cho tới khi đối chiếu fills); chỉ lên lớp MEASURED khi
   có bằng chứng fills. Không ghi "measured anchor".
2. Funding: measured per-settlement path (native, while held); dual-book với
   frozen constant; funding-path stress (24.7% settlements âm trong downtrend;
   worst −0.30%/8h ≈ 2.5 fee RT).
3. Spread: census theo giờ fill từ bookTicker/aggTrades; NOT_RUN ⇒ BLOCKED,
   không điền số đẹp.
4. Gap/outage: weekend không có nhưng venue outage có (418 precedent 2026-09-21);
   miss-N-settlement + gap-reopen bất lợi = DECLARED band.
5. Latency/liquidity trong biến động mạnh: DECLARED band + stress ×1.5/×2.0.
6. Maker-only assumption: CẤM trong cost book tới khi queue-position đo được.
7. Levered/borrow/liquidation-model: BLOCKED (không data) ⇒ mọi arm unlevered 1x.

## 4. Power floors kế thừa (umbrella §5.14; child chỉ được nâng)

- FX intraday: ≥100 closed RT + ≥6 tháng; PF≈1.3 cần n≈236 (power analysis
  tại freeze, không hạ).
- Crypto H4/daily: ≥100 closed trades + ≥2 vol regimes với occupancy floors
  (TWO-REGIME precedent: floors 20/3/100 fail ⇒ NOT_RUN_THIN).
- 15m crypto: child freeze n riêng sau power analysis; sàn ≥100 RT.
- Mọi positive sub-power = `INCONCLUSIVE`, không bao giờ PASS.
