# DAYTRADER-100-V1 — G1 census matrix (100 day-trader strategies)

- measured_at: 2026-09-28 (UTC)
- base HEAD: aa954939af9994731be2efaf173f9dde719c47cb (root main; owner untracked tree preserved)
- plan: plans/PLAN_daytrader_100_v1.md — budget 0/3, GO registered-not-consumed
- authorities: research/wayfinder/HYPOTHESIS_LEDGER.md; research/wayfinder/FAMILY_FAILURES.jsonl
  (139-140 rows); data census 2026-09-28 (Binance Vision panels, Dukascopy M1 estate, SNI/
  license blockers); LESSONS P-1..P-30, Q-1..Q-16.
- NO PnL was computed for any row of this file. Verdicts are bookkeeping on already-measured
  program evidence. A "would-be arm" sketch is recorded for every row (owner deliverable);
  only Cohort-1 arms are scheduled for scoring, behind two keys.

## Verdict codes

| code | meaning |
|---|---|
| RC1 | RUNNABLE_COHORT1 — never-tried mechanism + authorized multi-year substrate |
| AV  | ANCESTRY_VETOED — re-label/variant of a dated killed family; re-score = rescue (rho bar 0.20 immovable) |
| BD  | BLOCKED_DATA — substrate absent in-tree (0 bytes / not acquired) |
| BT  | BLOCKED_TRANSPORT — SNI-keyed network filter, measured |
| BC  | BLOCKED_COST — no citable financing/cost band (fail-closed) |
| BL  | BLOCKED_LICENSE/TERMS — entitlement or ToU refusal |

## Arm grammar by nhóm (anchor / N1 / N2 / CTRL cho mọi row)

- **Momentum/Breakout (A)** — A: rule như liệt kê; N1: cửa sổ x0.5; N2: cửa sổ x2; CTRL: clock-only shadow (cùng session/weekday, bỏ signal) + sign-flip.
- **Mean-reversion/Range (B)** — A: rule; N1: band 1.5σ; N2: band 2.5σ; CTRL: sham-entry permutation + clock shadow.
- **Session/Calendar (C)** — A: rule; N1: cửa sổ ±30'; N2: ±2h; CTRL: cùng-phút-khác-ngày (shadow đã giết RATES-NG1/COMMODITIES-NG1).
- **Event/News (D)** — A: event-window rule; N1: nửa window; N2: gấp đôi; CTRL: sham-calendar (ngày dịch +7d) + payload-removed.
- **Spread/Basis (E)** — A: ngưỡng vào; N1/N2: ngưỡng ±1SD; CTRL: unlevered hold + clock.
- **Orderflow (F)** — A: rule; N1/N2: percentile ±; CTRL: permuted-stamp + tape-only shadow.
- **Statistical (G)** — A: rule; N1/N2: tham số ±; CTRL: stale-rank / own-lag (những control đã giết trong repo).
- **Price action (H)** — A: pattern rule; N1/N2: kích thước pattern ±; CTRL: skeleton-collision court (DTP I001 method).
- **Vol (I)** — A: rule; N1/N2: ngưỡng ±; CTRL: vol-level shadow.
- **Crypto-native (J)** — A: rule; N1/N2: ngưỡng ±; CTRL: funding-level shadow (dead observable) + clock.

## Ma trận 100 strategy

| # | Strategy | Nhóm | Verdict | Bằng chứng (kill/blocker, ngày) |
|---|---|---|---|---|
| 1 | Opening Range Breakout | A | AV | Range-expansion/breakout class chết: EURUSD-OPEN-SEARCH-V1 (2026-09-23, 1/48 eligible, holdout fail −134.4 pips); PIT-seam ERP1-TRACKA-COHORT-1 (2026-09-26) |
| 2 | Pre-market high/low breakout | A | AV | Cùng class #1; DTP playbook corpus 11/11 chết skeleton (2026-09-27) |
| 3 | Donchian 20/55 intraday | A | AV | PHASE-STRATEGY-V1: DONCHIAN +177k bị control block-shuffle +190k vượt (2026-09-23) — phase timing không mang thông tin |
| 4 | VCP/Squeeze breakout | A | AV | SPRINT-CRYPTO H-VOLCOMP-BRKOUT (2026-08-24) + vol-level shadow class |
| 5 | NR7/inside-day breakout | A | AV | DTP-CX-SOLUSDT-C1 I001 folklore corpus death rate 100% (2026-09-27) |
| 6 | Gap fill / gap-and-go | C | AV | Clock/calendar class; FOREX-FREE-V5 sham-calendar out-earns (2026-09-06, FBxC #10) |
| 7 | PDH/PDL sweep-and-reverse | B | AV | Range-fade class: FX-MAJORS-SEARCH/RANGEEXP invalidated bởi PIT-seam (2026-09-26); SRLV sweep-absorption REJECT (2026-09-26) |
| 8 | Weekly open anchor | C | AV | Re-clock: DINV-1D day quote-gated continuation F-0/REJECT (2026-09-26) |
| 9 | Asian range breakout | C | AV | FOREX-FREE-V2 Tokyo-range→London (2026-09-04, break-even âm) |
| 10 | London open momentum | C | AV | FOREX-FREE-V1 (2026-09-04, −2.35/trade × 11,459 trades, cost-dominated) |
| 11 | NY open momentum | C | AV | ATTN-PHASE US-session G1 negative (CRYPTO-V17 D2, 2026-09-10) |
| 12 | Breakout retest entry | A | AV | Playbook skeleton (DTP I001, 2026-09-27) |
| 13 | VWAP mean reversion | B | AV | Range-fade/MR class (2026-09-26 PIT-seam); FX thêm BC (không cost band) |
| 14 | VWAP with-trend pullback | A | AV | Momentum re-clock; trend class chết đa asset |
| 15 | Bollinger 2σ fade FX | B | AV | FXOS-04 Bollinger fade — đúng family này — fail holdout (2026-09-23) |
| 16 | RSI-2 / Connors pullback | B | AV | Reversal re-clock; CNG2-A5-P1 diagnostic NET_NEGATIVE PF 0.51 (2026-09-22) |
| 17 | 3-bar pullback EMA20 | A | AV | Trend-pullback skeleton chết (DTP I001, 2026-09-27) |
| 18 | RSI divergence tại S/R | B | AV | MR skeleton (DTP I001, 2026-09-27) |
| 19 | Limit-up/down fade (commodity) | B | BT | CME/ICE estate 0 bytes, SNI-block (FX-FUTURES-FRONTIER-V1, 2026-09-17) |
| 20 | Overnight-hour fade crypto | C | AV | WKNDLIQ weekend book rho 0.5628 (CRYPTO-V17, 2026-09-10) |
| 21 | ES/NQ Z-score pairs intraday | G | BT | CME 0 bytes (2026-09-17); variant: BETDIS pair book rho-killed (CRYPTO-NG4, 2026-09-17) |
| 22 | Stale-quote fade altcoin | F | BD | Đa venue: venue-2 = 0 bytes (DTP-FX census, 2026-09-27) |
| 23 | Order-book imbalance fade | F | BD | L2 đa năm không có; SOL bookTicker chỉ 2023-05..2024-04 RETROSPECTIVE_ONLY |
| 24 | Overnight vs intraday split | C | AV | Clock class; equity chỉ có daily EODHD (không intraday) |
| 25 | Turn-of-month | C | AV | STOCKS-FREE-V3 TOM fail hard gates (2026-09-04) |
| 26 | Pre-FOMC drift | C | AV | CRYPTO-NG1 FOMC-instant ×2 rho 0.39-0.75 (2026-09-11); event-clock class |
| 27 | NFP first-minute momentum | D | AV | CRYPTO-NG2 BLS-instant veto (2026-09-12); FX CPI family exhausted NG1-NG4 (2026-09-11..12) |
| 28 | CPI post-news trend | D | AV | FOREX-NG1 scored REJECT_ALL: A5-P1 −9.81 PF 0.827; CTL-DGS10LEVEL +4.13 (2026-09-11, FBxC #15) |
| 29 | Friday close / Monday open | C | AV | Calendar/clock; FOREX-NG4 Friday geometry rho 0.888 (2026-09-12) |
| 30 | Pre-holiday drift | C | AV | Calendar class (STOCKS-FREE-V3 precedent) |
| 31 | Japan session fade JPY | C | AV | FOREX-FREE-V1/V2 session books (2026-09-04) |
| 32 | Power hour momentum | C | AV | Clock/session class chết cả hai plane |
| 33 | Settlement revert (WTI/Brent) | C | BT | Commodity intraday 0 bytes; fix-clock variant: DTP-FX A F0_KILLED vs FIXCERT-01 (2026-09-27) |
| 34 | BTC weekend effect | C | AV | WKNDLIQ rho 0.5628 (2026-09-10) |
| 35 | Funding-rate contrarian | J | AV | Funding-level gates ĐÓNG: ERP1-TRACKB rho 1.0000 = dead CARRY observable (2026-09-26) |
| 36 | News straddle (CPI/FOMC/NFP) | D | BD | Không có event-timestamp PIT machine-readable đa năm; event-clock class cũng đã chết (NG1/NG2) |
| 37 | Post-news momentum scaling | D | BD | Như #36 |
| 38 | Earnings open drive | D | BL | EODHD fundamentals/earnings 403 (STOCKS-NG3, 2026-09-15) |
| 39 | EIA inventory breakout (CL) | D | AV | COMMODITIES-NG1: bare release-clock control out-earns mọi anchor (2026-09-14, FBxC #17) |
| 40 | NatGas storage straddle | D | AV | Như #39 (release-clock) |
| 41 | WASDE ag straddle | D | BT | Ag futures intraday 0 bytes + release-clock precedent |
| 42 | BoJ intervention fade | D | BD | Không có intervention tape PIT |
| 43 | Exchange listing pump (perp) | D | BD | Listing announcements + cross-venue chưa acquired (owner data cycle) |
| 44 | Token unlock fade | D | BD | On-chain unlock lịch sử không có trong cây |
| 45 | BTC ETF flow momentum | D | BD | ETF flow chưa acquired — ledger ghi "separate data-authority cycle required" |
| 46 | Cash-and-carry funding harvest | E | AV | CARRY-7D fold-conc 51.66% (CRYPTO-V6, 2026-08-25); ERP1-TRACKB REJECT_ALL rho 1.0000 (2026-09-26) |
| 47 | Cross-exchange spread | E | BD | Venue-2 = 0 bytes (DTP-FX, 2026-09-27) |
| 48 | Triangular arbitrage | E | BD | Như #47 (đa venue) |
| 49 | Spot-quarterly calendar spread | E | AV | Basis class chết (BASISLV-PREMFADE, 2026-09-05); quarterly klines cũng chưa staging |
| 50 | ES/NQ relative strength | G | BT | CME 0 bytes SNI (2026-09-17) |
| 51 | Brent-WTI spread | E | BT | Như #50 |
| 52 | Gold-silver ratio intraday | E | BD | Metals intraday 0 bytes; XAU daily-only. Ghi chú: XAUUSD real-yield MR là reopening binding chờ owner cost authority (FOREX-NG6, 2026-09-16) |
| 53 | Crush/corn-wheat seasonality | E | BT | Ag intraday 0 bytes |
| 54 | Note-roll calendar spread (ZN/ZB) | E | BD | Rates intraday = 0 bytes program-wide (DTP-FX, 2026-09-27) |
| 55 | Stablecoin depeg fade | J | BD | Stablecoin pair panels không có |
| 56 | Stop-hunt fade tại swing level | B | AV | Range-fade/PIT-seam (2026-09-26) + SRLV sweep-absorption REJECT (2026-09-26) |
| 57 | Volume profile POC bounce | F | AV/BD | Klines-volume variant = orderflow re-label chết (V16, 2026-09-08); profile thật cần dữ liệu chưa có |
| 58 | LVN fade | F | BD | Như #57 |
| 59 | Footprint absorption reversal | F | AV | M01 aggressor absorption panel chết (CRYPTO-V10, 2026-08-27) |
| 60 | Cumulative delta divergence | F | AV | Orderflow class: V10/V15 taker-sat (2026-08-27..09-07) |
| 61 | Iceberg detection follow | F | BD | L2 đa năm 0 bytes; WS chỉ prospective từ 2026-09 |
| 62 | Book pressure ratio (top-5) | F | BD | Không có L2 lịch sử |
| 63 | VPIN toxicity filter | F | BD | Trade-flow tape đa năm không có |
| 64 | Queue-position scalping | F | BD | Latency + L2 ngoài phạm vi; gateway mới sống từ 2026-09-22 (5s marks) |
| 65 | Micro-anomaly fade (D-quote) | F | BD | Như #62-64 |
| 66 | Liquidation cascade fade | J | BD | liquidationSnapshot ZERO coverage (MAP R7) |
| 67 | OI spike + price stall | J | BD/AV | OI forest mất khỏi archive (R7); OI class chết (V11-V17, 2026-09-05..10) |
| 68 | Persistent-imbalance confirm | F | BD | L2 0 bytes |
| 69 | First-half-hour momentum | G | AV | Momentum class chết + equity intraday BD (EODHD daily-only) |
| 70 | Overnight-return signal intraday | G | AV | Clock re-clock (DINV-1D precedent) |
| 71 | RV-break regime switch | G | AV | Regime router: JEV V1/V2, phase, two-regime — NO_INCREMENTAL_VALUE (2026-09-23) |
| 72 | Hurst regime switch | G | AV | Như #71 |
| 73 | Vol-conditional autocorr | G | AV | Vol-level disguised — shadow class (STOCKS-FREE-V4, VOL-NG1) |
| 74 | GARCH vol targeting | G | AV | Vol-level shadow; VOL-NG1 cost-ceiling kill (2026-09-14) |
| 75 | Kalman pairs intraday | G | AV | BETDIS pair book rho-killed (CRYPTO-NG4, 2026-09-17) |
| 76 | Correlation breakdown trade | G | AV | Xsect reversal composite (NG4 20 veto rows) |
| 77 | Lead-lag ES→SPY→constituents | G | BD/BT | Equity intraday 0 bytes + CME SNI |
| 78 | BTC leads altcoins | G | AV | DTP-CX I002 BTC→SOL 1m lead-lag: SOL reprice trong đúng phút signal (2026-09-27) |
| 79 | ETH/BTC ratio risk gauge | G | AV | RELMOM re-label (STOCKS-NG5 rho 0.5107, 2026-09-16) |
| 80 | TSMOM hourly bars | A | AV | XSECT-TSTREND L14/L28 5/5 NOT_ELIGIBLE (CRYPTO-V9, 2026-09-04) |
| 81 | Pin bar rejection | H | AV | Playbook skeleton 100% death (2026-09-27) |
| 82 | Engulfing tại VWAP/level | H | AV | Như #81 |
| 83 | Failed breakout reversal | H | AV | Range-fade class (2026-09-26) |
| 84 | Three-drives exhaustion | H | AV | Như #81 |
| 85 | Inside bar tại confluence | H | AV | Như #81 |
| 86 | First pullback after BOS | H | AV | Trend-pullback skeleton (2026-09-27) |
| 87 | FVG/liquidity void fill | H | AV | DTP folklore corpus — đúng họ rule này (2026-09-27) |
| 88 | VIX term-structure roll | I | AV | VOL-NG1: COST_CEILING_FAMILY_KILL, mọi arm ≤0 sau Q-16 ladder (2026-09-14) |
| 89 | VIX spike mean reversion | I | AV | Vol-level shadow class |
| 90 | Vol ETP rebalance front-run | I | AV | VOL-NG1 ETP decay-path dead (2026-09-14) |
| 91 | GEX pinning | I | BD | Options chain 0 bytes; Deribit collectors chỉ prospective |
| 92 | Charm-flow Friday drift | I | BD | Như #91 |
| 93 | 0DTE straddle harvest | I | BD | Như #91 + decay-path precedent |
| 94 | Funding-skew directional | J | AV→RC1 | Bản funding-LEVEL chết (ERP1-TRACKB, 2026-09-26). Nhưng bản FORECAST-FUNDING (premiumIndex 1m) là never-tried có data — chính là Cohort-1 của cycle này |
| 95 | Perp/quarterly basis divergence | E | AV | Basis class (BASISLV, 2026-09-05) |
| 96 | SOPR extremes contrarian | J | BD | On-chain không acquired |
| 97 | MVRV z-score filter | J | BD | Như #96 |
| 98 | Exchange netflow signal | J | BD | Stablecoin issuer netflow đã chết trên tape-proxy (CRYPTO-NG3, 2026-09-15); dữ liệu on-chain thật 0 bytes |
| 99 | Mempool fee-spike fade | J | BD | Mempool không thu thập |
| 100 | Stablecoin dominance MR | J | BD | Không staged |

## Phán quyết tổng (đếm từ ma trận)

- **RC1 (chạy được, chưa từng thử): 1** — #44/#94-family: forecast-funding premiumIndex intraday
  (định nghĩa đầy đủ tại plan §3, arms A/N1/N2 + 4 CTRL re-evaluations).
- **AV (ancestry-vetoed): 55** — mọi nhóm momentum/MR/session/event-clock/carry-basis/
  orderflow/lead-lag/regime/vol-level/playbook đều có kill có ngày.
- **BD/BT/BC/BL (blocked): 44** — thiếu bytes (orderbook/L2, on-chain, liquidation, OI,
  multi-venue, options, rates/ag/commodity intraday), SNI-block (CME, Dukascopy re-download),
  cost-band fail-closed (FX Dukascopy M1 — có 2021-01..2026-09 nhưng không bill được),
  license (EODHD earnings 403, FINRA ToU).

## Cửa sổ thời gian (ngày tháng explicit)

- **Cohort-1 (crypto 1m, 2020-09-01..2026-08-31)**: warmup 2020-09-01..2021-03-31; GĐ1
  2021-04-01..2022-06-30; GĐ2 2022-07-01..2023-09-30; GĐ3 2023-10-01..2024-12-31; GĐ4
  2025-01-01..2026-08-31 (force-flat tại biên).
- **FX notional (Dukascopy M1, chỉ nếu owner cấp cost authority)**: warmup 2021-01-01..
  2021-03-31; P1 2021-04-01..2022-06-30; P2 2022-07-01..2023-09-30; P3 2023-10-01..
  2024-12-31; P4 2025-01-01..2026-09-23.
- Forward streams (không dùng cho backtest): LIVE-DATA-GATEWAY-V1 từ 2026-09-22;
  PROSPECTIVE-SHADOW-V1 forward-only từ 2026-09.

## Hành động owner mở khóa các nhóm blocked (theo thứ tự lợi ích)

1. Cost/financing band cho FX (broker statement) → mở lại 5.7 năm Dukascopy M1 (13 strategy FX intraday).
2. Network path tới *.cmegroup.com (+ *.dukascopy.com re-download) → mở futures/2 cặp FX còn lại.
3. Data cycle cho cross-venue/options/on-chain → mở #43-48, #61-68, #91-99.
4. EODHD entitlement earnings-history → mở PEAD intraday-adjacent (#38).
