# DATA_GAP_MATRIX — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 (deliverable D2)

Consolidated from the 5 lane gap sections (full detail + falsifying
controls in each `LANE_REPORT.md`). Split per the owner directive:
**NEED-NOW** (fixes a recorded kill or a standing defect; free/cheap;
license-cleared) vs **ONLY-WITH-MECHANISM** (buy/signup-gated or serves a
hypothesis class not yet committed — acquire only when a specific
preregistered mechanism names it). Every OI/liquidation/L2 row carries the
law verbatim: **"Không suy ra order book hay forced flow từ nến"**.

## NEED-NOW (priority order)

| # | Gap | Asset | Why needed / kill it fixes | Hypothesis class opened | Falsifying control | Cost / volume | Unblocks via |
|---|---|---|---|---|---|---|---|
| N1 | Broker statement (spread/commission/**swap**) for FX majors | FX | 3 generations killed at cost authority; ERP1 floor 3.6/4.4-pip RT partitioned the space — financing data moves the FLOOR itself, new price history does not | Any net-of-cost intraday or multi-day FX book; carry-vs-alpha separation | MT5 collector spread distribution vs Dukascopy census (0.3 sess / 0.9 rollover pips); swap bands vs uniform 1.7 bps/night assumption | Owner session ~1h; output <10 MB | **Owner action R1** (IBKR statement + FX delayed data; TWS already installed & API proven) |
| N2 | EDGAR acceptance datetimes for earnings/filings | Stocks | STOCKS-NG3 E1 kill (earnings channel 403); Q-7: clock is most of event variance — no honest earnings family without publication timestamps | PEAD-class announcement-timing, revision drift, clock-conditioned events | Q-7 clock-only shadow; timing-state vs restatement-state decomposition | FREE + entitled; cohort-scoped probe ≈ thousands of light calls, <100 MB | A follow-up cycle probe (inside §8-class budgets) — no owner action needed |
| N3 | PIT corporate actions (action-date table) | Stocks | L-SAMV1-1 defect law: EODHD adjusted series is as-of-pull (lookahead by construction) contaminating all adjusted-price families | 52W-high / illiquidity / level-break state families become honestly backtestable | Rebuild adjusted series forward from action dates; compare vs served adjusted_close at ≥2 vintages; drift = detection | Derivation-only from entitled bytes already on disk (2,168+2,168 div/split files + 8-K) — ~1–2 days pipeline, no network | Follow-up cycle (no owner action) |
| N4 | Dated identity mapping ticker↔CIK↔CUSIP | Stocks | FRC→FRCB mutation measured; CUSIP reuse; FTD/Form-4/N-PORT joins are survivorship-prone without it | Every cross-dataset join becomes PIT-correct | Same-name join vs CUSIP join disagreement rate on a bounded window | Derivation from entitled artifacts (~1 day) | Follow-up cycle (no owner action) |
| N5 | Session/DST calendar authority | FX | Session conventions frozen ad hoc per cycle; owner list names "lịch phiên và DST" | Session-conditioned strategies with one citable calendar; audit-proof DST | exchange_calendars vs frozen master calendar (4,924 days, sha e511b7da) diffed on DST boundaries | pip install + ~20 asserts, ~0 disk | Follow-up cycle |
| N6 | BIS WS_CBPOL + ECB SDMX bulk (vintaged policy rates / HICP) | FX/macro | Never held (fixtures only); PIT macro conditioning beyond CPI | Rate-decision vintages; EMU HICP leg | ALFRED vintage dates vs BIS amendment dates join test (PIT battery) | ~10 MB + ~50 MB, free/keyless — within future probe budget | Follow-up cycle probe PS2-extended (license screen first: ruling PARTIAL, BIS UNVERIFIED) |
| N7 | BTC/ETH bookTicker spread census | Crypto | Only SOL measured (0.469 bps); BTC/ETH rest on DECLARED 5bps+1tick — the measured-beats-stated law (Q-8) is open exactly here | After-cost realism for every crypto cell (fee-dominated book confirmed) | 2-month census recomputed like SOL's; p50 ≫ 5 bps ⇒ cost book wrong | ≈2 GB/month/symbol compressed; **needs ≥25–40 GB disk freed first** | **Owner action R3** (free disk) then a follow-up cycle |
| N8 | forecast funding (premiumIndex history) | Crypto | ~~no premiumIndex history staged anywhere~~ **RESOLVED by PS1 probe this cycle: Vision `premiumIndexKlines` served keyless, sha-verified** (PS1_REPORT.md) | Funding-crowding: predictable component vs realized surprise | Realized premium at fundingTime == settled rate to tolerance; history floor <2 yr ⇒ cap the class | **~7 MB for 6 symbols × 6 years** — trivial follow-up staging | Follow-up cycle staging (no owner action) |
| N9 | Unpin repair: stocks-search-v1 staging SHA256SUMS | Stocks | 1.9 G cache effectively unpinned (6/111,322 records have shas) — identity defect, not new data | none (integrity) | n/a | ~2 min CPU, 0 network | Follow-up cycle (or fold into N3 work) |
| N10 | Consolidate duplicate EURUSD corpus (rangeexp ≡ eosv2) | FX | 35.4 MB duplicate; hygiene | none | n/a | archive-then-delete per P-13 | Follow-up cycle |

## ONLY-WITH-MECHANISM (blocked pending owner decision or a named mechanism)

| # | Gap | Asset | Blocker | What it would open | Cost shape | Owner action |
|---|---|---|---|---|---|---|
| O1 | Tradables/replication source for FX (TrueFX / OANDA v20 practice) | FX | BLOCKED_LICENSE pending owner license capture (EDQ1 packet); Dukascopy fresh TCU worsened | Replication of every Dukascopy-scored family; indicative-vs-tradable distinction | TrueFX ~2–4 GB/yr/pair; OANDA practice light | **R2** (choose one; links in runbook) |
| O2 | PIT OI / liquidation / L2 multi-year corpus | Crypto | No keyless path; needs vendor $ + license screen; **vốn lịch sử V14 đã mất** (P-13 drift I-1) | Forced-flow / cascade class (OILEV/OITD/OICYC verdicts are UNDETERMINED w.r.t. PIT data, not evidence of absence) | Vendor quote needed; own-capture ≈250 MB/day/market × years | **R4** (decision whether to solicit vendor quotes) |
| O3 | Trades/quotes (SIP/IEX) for equities | Stocks | BLOCKED_COST (IEX per-file $; SIP TB-scale) | Microstructure/execution families (all currently blocked) | Bounded slice 10–50 GB/yr + $ | **R5** (only if a mechanism names tape needs) |
| O4 | Borrow/short-fee history | Stocks | Broker/vendor account | Short-side families (fee-adjusted carry, squeeze) | account-gated | R6 |
| O5 | EODHD earnings-history entitlement upgrade | Stocks | BLOCKED_ACCOUNT (403 map) | Convenience alternative to N2 (N2 is free and preferred) | $ subscription tier | folded into R2-decision packet |
| O6 | Halts/auction calendar; real equity execution costs | Stocks | derives from O3 | event-window integrity; conditional cost book | with O3 | with R5 |
| O7 | CFTC CoT raw pulls re-fetch | FX | free/keyless, just never re-pulled after worktree cleanup | re-verify NG5 censuses from raw | small | fold into N6 probe cycle |

## Reading of the matrix (A1 synthesis)

1. The single highest-leverage owner action is **R1 (broker statement)**:
   it is the only item that can move the ERP1 cost floor itself and it
   unlocks 6/10 FX cost components with one export (machinery already
   written + audited).
2. The highest-value FREE frontier is **stocks EDGAR timestamps (N2) +
   PIT corporate actions (N3) + identity mapping (N4)** — all
   derivation/probe work on bytes already entitled, each fixing a recorded
   kill or defect law.
3. Crypto is the measured frontier (funding + SOL spread measured);
   its honest gaps are disk-gated (N7) and provider-gated (O2), not
   license-gated.
