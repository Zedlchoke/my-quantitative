# PLAN (DRAFT) — SRLV-CX-C1 — Cohort 1 track Crypto: Support/Resistance · Sweep · Volatility-state trên Binance perp (BTC/ETH/SOL/BNB)

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** Child
> cycle của `SRLV-PROGRAM-V1` (master `plans/PLAN_srlv_program_v1.md`) dưới
> umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`. KHÔNG phải Track B (delta-neutral
> carry — `ERP-TRACKB-PROGRAM-V1` vẫn là authority riêng của không gian đó);
> hai chương trình không trộn ledger/cost/verdict. Kế thừa nguyên văn:
> umbrella §§1–11; forex-program §3/§4/§5/§8 (cấu trúc cohort, R0–R6,
> roster, chuỗi GO); SRLV master §§2–11. Chỉ chặt hơn.
>
> Authored 2026-09-26. Frontier crypto KHÔNG đóng như FX — cohort có thể mở
> council sau data gate; nhưng mọi cơ chế sweep/zone mang nhãn
> `PROXY_NOT_ORDERBOOK` và qua fictional-counterparty veto; funding measured
> là cost bắt buộc; G5 fold-concentration đo là structurally unpassable cho
> BTC-long 2020–2026 ⇒ đọc §2.3.

## 0. Cycle identity

```text
cycle_id      SRLV-CX-C1
parent        SRLV-PROGRAM-V1 (master)
worktree      .worktrees/srlv-cx-c1/integration (branch
              orca/srlv-cx-c1-integration) — tạo qua researchctl tại GO-1
budget        ≤ 18 scored cells (3 cơ chế × 6 arms × 1 home pair) + references;
              holdout looks ledgered riêng
universe      BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT (USDⓈ-M perp, Binance)
              — candidate universe; per-pair gate; BLOCKED không thay
S1            SEALED_UNTOUCHED; không tiêu surface S1 của các cycle đang sống
GO phrases    master §13 (CX cột)
```

## 1. Mục tiêu cohort

Như SRLV-FX-C1 §1 (falsify trước PnL, ≤3 cơ chế, modal REJECT_ALL), với hai
điểm khác crypto: (i) dữ liệu funding/fee measured mạnh hơn FX (cost book
chặt hơn được); (ii) KHÔNG có order-book/liq/OI lịch sử — mọi cơ chế sweep/
absorption là proxy hình học với payer story phải kiểm nổi bằng chính proxy
(fictional-counterparty veto nếu payer chỉ tồn tại trong narrative).

## 2. Ràng buộc đặc thù crypto (binding)

### 2.1 Data plane (Phase C1)

- Klines: Vision monthly um klines — plane do council chọn (1h có sẵn local
  cho 4 cặp; 15m/1m cần stage mới). Mọi plane mới chạy data gate đầy đủ
  (probe/census/UTC calendar/license posture capture). Floor data: SOL
  2020-09-14, BNB 2020-02-10, BTC/ETH 2020-01 (per exposure map).
- Funding: fapi `/fapi/v1/fundingRate` pagination + Vision cross-check; floor
  fapi 2020-07-18 (SOL 2020-09-13); **quy tắc conflict: lệch bất kỳ ⇒
  symbol-month EXCLUDED** (frozen precedent). Funding PIT: một settlement chỉ
  available TẠI `fundingTime`; rate interval kế tiếp là PREDICTED ≠ observable.
- Spread/slippage: census theo giờ fill từ bookTicker/aggTrades granary —
  coverage verify tại C1; thiếu ⇒ BLOCKED, không điền số đẹp.
- CẤM dùng: liquidationSnapshot (404), OI lịch sử (lookback ≈41.6h), order
  book L2 lịch sử, bất kỳMaker-fill assumption nào.

### 2.2 Exposure & collision (Phase C0+C2)

- Verify per pair × plane × window chống registry tại GO-1 (trackb §4.2
  precedent): BTC 1h 2020–2026-08 và 15m 2024-08–2026-08 outcome-exposed
  (CHR3F staged+scored); ETH 1h exposed (V1 terminal, V2 lane B); SOL/BNB 1h
  baseline-exposed; plane 15m/1m chưa stage = `ANCESTRY_EXPOSED_RECLK` —
  CÙNG lịch sử giá đã outcome-exposed, đổi timeframe KHÔNG tạo surface
  outcome-free (re-clock veto Q-3).
- Dev evidence trên window exposed (kể cả plane 15m/1m) mang
  `ANCESTRY_EXPOSED_DEV` — dùng để KILL và engineering, không bao giờ tự
  bằng chứng promote.
- Sealed OOS của cohort: một history window chỉ được dùng one-look nếu
  verification chứng minh chính LỊCH SỬ GIÁ window đó chưa từng bị
  search/score ở BẤT KỲ granularity nào (không phải vì đổi plane); với 4 cặp
  này kỳ vọng thực tế là không còn ⇒ **prospective accumulation sau freeze**
  (decision-count gates umbrella §5.12 D13/D26/D52) — trackb §4.2 precedent.
- Không đụng: `ETHUSDT-OPEN-SEARCH-V2` (ACTIVE, chờ GO, S1 sealed — không
  tiêu phrase/surface của nó), `CRYPTO-HISTORICAL-REPLICATION-3F-V1` (đang
  scored; heavy lock machine-wide — chỉ dispatch khi FREE_PROVEN),
  `PROSPECTIVE-SHADOW-V1`/shadow workers (không restart, không sửa).

### 2.3 Concentration gate — G8 trong bộ gate cohort này (binding)

Tiền lệ đo được (từ BTC-H4-BAND-RISK, gate concentra historically gọi G5 ở
cycle đó): KHÔNG long book nào trên BTC 2020–2026 qua fold-concentration
0.50 (ALWAYS_ON 0.5348 / TREND_LF 0.7028 / C3 0.7117). Trong bộ gate
G1–G8 của SRLV, concentration là G8. Hệ quả:
mọi cơ chế long-biased trên BTC phải (a) chứng minh short-capability (hai
chiều) trong anchor definition, HOẶC (b) freeze concentration-statistic
thay thế có biện luận khoa học TRƯỚC outcome (umbrella §5.14), HOẶC (c) chỉ
định nghĩa kết luận trên prospective (không claim từ history BTC-long).
**Ranh giới không được vượt: thanh 0.50 KHÔNG bị hạ vì BTC-long fail** —
việc BTC-long đã fail G5 là kết quả đã biết, nên mọi thay thế statistic phải
tồn tại trong luật TRƯỚC outcome của identity đó (concession có sẵn từ
umbrella §5.14, freeze cùng trial freeze, sha-pinned); thay sau khi thấy
kết quả = parameter rescue, cấm (K-CONC + charter §1.2).

### 2.4 Funding cost law

- Cost books tách lớp bằng chứng: funding = MEASURED (per-settlement theo
  path thật; BTC 11.798%/yr anchor = 7.824× hằng số cũ; dual-book với frozen
  constant để đối chiếu; funding-path stress 24.7% settlements âm trong
  downtrend, worst −0.30%/8h); fee 5 bps + 1 adverse tick = DECLARED book
  (venue-published tier floor + convention tick, freeze từ CHR3F; lên lớp
  measured chỉ khi validate vs fills — Q-8); spread = measured census nếu dữ
  liệu đủ, else BLOCKED. Declared không override measured; mọi arm unlevered
  1x (levered/borrow/liquidation BLOCKED).

## 3. Phases & gates

### Phase C0 — Control plane & collision check

- `researchctl cycle list/doctor/locks inspect`; lock-drift ⇒ BLOCKED (P0-2);
  doctor HIGH trên TERMINAL-archived cycles = accepted-historical (P0-3);
  workers=0 cho child; xác nhận không Lead session sống khác cho cycle này.

### Phase C1 — Data plane per pair (per-pair gate)

- Stage plane(s) council đề cử + funding + spread census; license posture
  capture từng nguồn; census sha-pinned; BLOCKED rows ghi rõ. Power analysis
  cho cơ chế ứng viên (floors: ≥100 RT sàn; 15m child freeze n riêng).

### Phase C2 — Exposure verification

- Đối chiếu registry + HYPOTHESIS_LEDGER: bảng pair × plane × window ⇒ phân
  loại exposure; plane 15m/1m mặc định `ANCESTRY_EXPOSED_RECLK` (không phải
  outcome-free). Chọn home pair + dev folds từ dev được phép; OOS history
  one-look chỉ với window chứng minh chưa-exposed ở cấp LỊCH SỬ GIÁ (không
  phải đổi plane); else OOS = prospective; artifact
  `EXPOSURE_VERIFICATION_C1.md` sha-pinned.

### Phase C3 — Council outcome-blind + falsifiers + trial freeze (GO-1, rồi DỪNG)

- Như SRLV-FX-C1 D2 với thay thế crypto: baseline set = cash 0% + long
  BTC/ETH cùng cost book + trend-following reference (TREND_LF precedent);
  short-beta control khi cơ chế có chiều; các falsifier F-0…F-7 (F-2 gồm:
  funding-settlement timing, kline clock alignment, truncation proofs M-class
  cho mọi biến regime/vol-state; delay-pair Q-4 cho sub-hour); incrementality
  test vol-state §2.4 master; freeze fold contract kiểu F1 2020-01→2021-04,
  F2 2021-05→2022-12, 2023-01→2024-12, 2025-01→end (điều chỉnh theo floor
  data từng pair, pin trước outcome).

### Phase C4 — Scored walk-forward (GO-2, heavy lock)

- Như D3 FX + funding-path accounting per settlement; gates G1–G8 +
  margin-to-fail; G8 (concentration) với §2.3 disclosure; dual cost book (measured path /
  frozen constant) báo song song; per-pair, per-fold, toàn panel,
  leave-one-out.

### Phase C5 — Sealed/prospective OOS one-look (GO-3, MỘT LẦN)

- Nếu C2 chứng minh còn window chưa-exposed ở cấp lịch sử giá (không phải
  bằng đổi plane): one-look như FX (membership sha-frozen).
- Kỳ vọng thực tế (và mặc định an toàn): prospective accumulation sau freeze
  theo D13/D26/D52; kết luận tối đa trong history =
  `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`.

### Phase C6 — A7 terminal + two-half close

- Như D5 FX. Reproducer/A7 viết lại engine funding-settlement accounting từ
  raw settlement bytes (trackb §6 law), không import engine implementer.

## 4. Mechanism-specific freeze fields (crypto bổ sung)

Định nghĩa mức/vùng + `t_known` + N-bar pivot confirm; khung sống tín hiệu;
funding treatment trong PnL (received/paid tách bạch Q-14); session không có
(24/7) ⇒ clock twin = block-shuffle/GMT-hour dummies; weekend/quiet-hour
buckets disclosed; spread-conditioning của fill theo giờ; liquidation-adjacent
narrative CẤM (không data) — sweep được định nghĩa thuần hình học từ kline
close/wick với nhãn PROXY_NOT_ORDERBOOK.

## 5. Ngân sách / dừng

- ≤18 scored cells; holdout/prospective looks ledgered riêng; program cap
  master §9; time-stop 14 ngày/cohort; stop conditions master §11. Terminal
  vocabulary như SRLV-FX-C1 §5 + nhãn `SINGLE_VENUE_PANEL`,
  `PROXY_NOT_ORDERBOOK`, `FUNDING_PATH_STRESSED`,
  `ANCESTRY_EXPOSED_DEV` (dev rows), `FILL_QUALITY_CLASS_<measured|declared>`.
