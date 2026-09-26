# C1_DATAGATE_VERDICT — SRLV-CX-C1 (Phase C1, per-pair)

- Measured 2026-09-26 bởi Lead (light job; heavy lock FREE_PROVEN, không chiếm).
- Corpus staged READ-ONLY-copy từ worktree `ethusdt-open-search-v2` (klines;
  nguồn gốc Binance Vision keyless) + `bear_opportunity_recon_2026-09/
  data_a2` (BTC funding fapi parquet + sha manifest) vào
  `research/control/SRLV-CX-C1/data_local/`. Không ghi đè corpus gốc.

## Klines 1h (census `CENSUS_1h_funding.json`)

| Pair | Bars | Window (UTC) | Hour-gaps | Verdict |
|---|---|---|---|---|
| BTCUSDT | 58,440 | 2020-01-01T00 .. 2026-08-31T23 | 0 | **PASS** (floor đúng map) |
| ETHUSDT | 58,440 | 2020-01-01T00 .. 2026-08-31T23 | 0 | **PASS** |
| SOLUSDT | 52,145 | 2020-09-14T07 .. 2026-08-31T23 | 2 (disclosed) | **PASS_WITH_DISCLOSURE** — rule tại freeze: bar thiếu = no-fill, fail-closed, không nội suy |
| BNBUSDT | 57,472 | 2020-02-10T08 .. 2026-08-31T23 | 0 | **PASS** |

`bad_zip_rows` 55–56/pair = dòng header CSV của monthly zip (không phải corrupt
bar) — đã skip, đếm lại bằng bar count khớp giờ lý thuyết.

## Funding (measured cost authority)

| Pair | Nguồn | Settlements | Window | Verdict |
|---|---|---|---|---|
| ETHUSDT | Vision fundingRate zips (local) | 7,305 | 2020-01-01 .. 2026-08-31 16:00 | **PASS** (floor-exact khớp ETH-V1/V2) |
| BTCUSDT | fapi events parquet (bear-recon, sha-pinned) | 7,643 | 2019-09-10 .. 2026-08-31 16:00 | **PASS** (khớp CHR3F; dual-source cross-check với Vision zip là việc của C3 cost lane nếu cơ chế giữ qua settlement) |
| SOLUSDT | — | — | — | **NOT_RUN_BLOCKED_PENDING_STAGING** (cần fapi pagination download — network job, xếp dưới heavy-lock discipline; conflict-rule symbol-month EXCLUDE giữ nguyên) |
| BNBUSDT | — | — | — | **NOT_RUN_BLOCKED_PENDING_STAGING** (như SOL) |

Hệ quả binding cho council/freeze: home pair phải có funding gate PASS
(BTCUSDT/ETHUSDT hôm nay) HOẶC cơ chế thiết kế **flat-by-settlement** (không
giữ vị thế qua mốc 8h ⇒ không cần funding series). SOL/BNB làm dev/
replication-transfer chỉ sau khi funding staged hoặc cơ chế flat-by-settlement.

## Spread/slippage census theo giờ fill

**NOT_RUN** — bookTicker/aggTrades chưa staged. Quyền của cost auditor tại
C3: cơ chế nào cần spread measured ⇒ BLOCKED tới khi staged; cơ chế dùng
fee-DECLARED book (5 bps + 1 adverse tick) phải ghi rõ lớp DECLARED.

## License posture

Vision/fapi = keyless public archive, posture `PIT_USABLE` kế thừa các cycle
tổ tiên (ETH-V1/V2, CHR3F); license text chưa capture — data gate posture
ghi nhận `DOCUMENTED_CANDIDATE → AUTHORIZED_INTERNAL_RESEARCH` theo P-25;
không commit raw bytes ngoài control namespace đã commit (klines zips ở
data_local worktree, không vào git).

**C1 verdict: PASS (BTC/ETH full; SOL klines-pass/funding-pending; BNB
klines-pass/funding-pending; spread census NOT_RUN).**
