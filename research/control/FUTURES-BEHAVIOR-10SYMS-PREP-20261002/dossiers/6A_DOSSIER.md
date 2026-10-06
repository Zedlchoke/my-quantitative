# 6A_DOSSIER — Australian Dollar Futures (CME 6A)

> **ERRATUM 2026-10-02 (Lead, co-owner-fix round; found by STRATEGY-CONFIGS
> coverage check):** this dossier claims HG copper is "in own raw corpus
> (OBSERVED available)" (§2 driver rows 3 and 10; §5 H2 "both in raw corpus —
> HG measurable…"; §6 row framing "HG copper proxy in corpus"). Measured
> fact: the raw corpus contains ZERO `HG_*` files (verified
> `ls ~/.my-quantitative-data/futures-10syms-v1/raw/ | grep -c '^HG'` → 0;
> coverage manifest has no HG entry; SI dossier independently states "HG
> copper NOT in 10-symbol snapshot"). All HG-availability claims are
> therefore **NOT_IN_CORPUS / NOT_RUN**, not OBSERVED. Consequences: §5 H2's
> HG-leg is BLOCKED_NONDATA (needs HG added to a future vendor request or
> another lawful source — owner decision); §2 rows 3/10 data columns read
> "HG NOT in corpus"; §6 iron-ore/HG row's "$0 for HG version" is void.
> Mechanism reasoning (POSTULATED) unchanged. Superseded wording preserved
> verbatim below in the affected rows.

- Symbol: 6A (CME, tradingClass `6A`; IB `symbol=AUD`; NOT the E-micro M6A and not the
  A6 continuous code used by some vendors)
- Exchange: CME (Globex); vendor endpoint IB TWS API, timezone US/Central
- Generated_utc: 2026-10-02 (lane local; all web access dates below are 2026-10-02)
- Author lane: SYMBOL-DOSSIER-6A, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (PREP ONLY —
  no scored runs, no PnL/event-studies/sweeps, no GO)
- Inputs:
  - owner_framework/6A_RESEARCH_FRAMEWORK.md sha256
    `6f1e14133d6d5e30ee05f88e5966081c7389d8fc25a1f6b5c7aaf6c29a3cbf82`
    (owner_framework/SHA256SUMS.txt); 00_MASTER_FRAMEWORK.md sha256
    `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`
  - research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md sha256
    `9722d3a123da7e3bc1546293705c241aab7eb938fed38a08f2f07600926e4260` (untracked snapshot,
    read-only) + S1_IDENTITY.json `d217ab9dcd865765e1bcae8f8131dee2f7f200cd90c07403280134da32b05822`,
    S6_VALIDATION.json `0dd3e76b649cd6f403cebeaa4fe5bca5c5922823c70f199bbe06b4b0e38a700c`,
    S6_FRONT_SPREADS.json `3724a6333bef26cff265cae7ee0c2e544803554f812990a397df1b18bbe59511`,
    S9_INDEPENDENT_VERIFY.md `cb5c916992f9f45971d1cac4b1863e1482d464d8b7412745520ee4c22a678e00`,
    HANDOFF.json `4d79f0424b3a7467d2fb5c9a22f3f8298560993018b55206bff019a6866a55f6`,
    costs/SPECS_MARGINS_PUBLIC_2026-10-02.md
    `e8174857f463821e85d0352335c06368939ab65b1784509956cd6339952330a3`,
    costs/IBKR_futures_commissions_2026-10-02.json
    `44829cbdab8e4d747257aa7bc427db68a10ec031c95a1ed8a36d8c22b4b4950f`
  - Raw (read-only): ~/.my-quantitative-data/futures-10syms-v1/raw/ files `6A_*`
    (20 contracts × 5 job types = 100 files + 3 probe subsets)
  - Analysis (this lane): analysis/6A_descriptives.py → analysis/6A_descriptives.json
    (descriptive only, strict past/rolling windows; methodology follows the sibling
    ES/NQ/CL/GC/NG dossiers and analysis/6E_descriptives.py — same roll-gap measurement
    approach, same serial-gap executability check GC introduced)
- Claims taxonomy used everywhere below: FACT (sourced) / OBSERVED (raw+script+window) /
  POSTULATED (mechanism, unmeasured) / NOT_RUN (default; never inferred PASS).

## 1. Mechanics

- Underlying exposure: AUD 100,000 vs USD, quoted in USD per 1 AUD (AUD/USD direction,
  NOT inverted), physically delivered at expiry. [OBSERVED: S1_IDENTITY.json 6A —
  multiplier "100000", minTick 5e-05, currency USD, longName "Australian dollar",
  validExchanges CME,QBALGO, uniform on all resolved contracts] [FACT-secondary for the
  contract unit: AMP "100K AUD" and ITG "AUD 100,000", fetched by the data lane 2026-10-02,
  costs/SPECS_MARGINS_PUBLIC_2026-10-02.md]. Scale check: raw daily closes across all 6A
  files span 0.598 (2025-04-08, 6AZ5) → 0.7426 (2021-10-20, 6AU6) USD/AUD — reciprocal
  AUD/USD-spot-equivalent 1.347–1.672; recent front closes 0.6457–0.6984 match the
  FINAL_REPORT band. No 6J-style inversion risk. [OBSERVED: analysis
  `quote_convention_check`]
- Tick/multiplier/quote convention: minTick 5e-05 USD/AUD × AUD 100,000 = **$5.00/tick**
  (S1 broker secdef, uniform). CONFLICT flagged by the data lane: ITG/TradingCharts
  legacy show 0.0001 = $10.00; official CME adjudication CME_BLOCKED_TRANSPORT
  (HTTP 403 re-verified by the data lane 2026-10-02). Numbers reported, not reconciled.
  [OBSERVED + FACT-secondary]
- Participants: hedgers = Australian commodity exporters (iron ore/coal/LNG receivables),
  importers, AUD-funded corporates and banks; speculators = macro funds, CTAs, carry
  traders, asset managers; MMs/arbitrageurs link 6A to AUD/USD spot and forwards
  (covered-interest-parity basis) and to the BBSW/SOFR rate differential. [POSTULATED:
  participant map per owner framework §core; not measured here]
- Sessions & DST: CME Globex FX week Sun 17:00 → Fri 16:00 US/Central with a daily
  16:00–17:00 CT maintenance break (S1 `tradingHours` e.g. "20260930:1700-20261001:1600");
  liquid (RTH) window 08:30–16:00 CT per S1 `liquidHours`. Raw daily/hourly/1-min files
  are useRTH=true → **only 08:30–16:00 CT is measurable**; Sydney/Tokyo (6A's home
  session) and London are entirely outside the recorded bars. DST was verified correct at
  bar date by S9 on the shared method (50/50 files, incl. 6J same family). [OBSERVED:
  S1 + raw metadata + S9]
- Holidays: exchange holidays absent from the raw calendar (e.g. no 6A bar 2025-12-25);
  the expiry-rule check's 3 "mismatches" (6AF7/6AG7/6AF8 LTD 3 days earlier than the
  Mon–Fri approximation) are exactly MLK/Presidents-Day Mondays, i.e. the IMM rule holds
  once holidays are counted. [OBSERVED: analysis `expiry_rule_check`]
- Delivery/first-notice/expiry/last trade: physically delivered FX future; trading ceases
  09:16 CT (10:16 ET) on the second business day before the third Wednesday of the
  delivery month (every 6A contract's `lastTradeTime` = 09:16 in S1; e.g. front 6AV6
  lastTradeDate 2026-10-19 = Fri before 3rd Wed 2026-10-21). Delivery/value date = third
  Wednesday (IMM convention). First-notice-day: not applicable to FX futures (no FND
  concept), CME-specific delivery text CME_BLOCKED_TRANSPORT. Price limits: NOT_RUN (no
  primary/secondary source fetched — do not assume "none"). [OBSERVED S1; FACT-secondary
  ITG/Wikipedia for the rule wording; NOT_RUN where marked]
- Listed months & liquid maturities: quarterly H,M,U,Z are the liquidity backbone (20
  quarterlies listed per broker mirrors); serial (non-HMUZ) months are also listed — the
  current S1 front is itself a serial (6AV6, Oct-2026; next 6AX6, Nov-2026) — and the
  resolved chain shows listed serials out to 2028-01. Liquid maturity = nearest HMUZ
  contract, NOT the nearest expiry: measured last-40-session median volumes are
  6AZ5 32,516 / 6AH6 47,285 / 6AM6 43,190 / 6AU6 27,981 / 6AZ6 1,680→66,731 (Oct) vs
  serial fronts **6AV6 = 8 and 6AX6 = 1** — serials trade 3–4 orders of magnitude below
  quarterlies. [OBSERVED: analysis `quarterly_vs_serial`; S1 chain; FACT-secondary for
  listing-cycle wording]
- Liquidity migration front→next [OBSERVED on the quarterly chain, analysis
  `liquidity_migration_quarterly`]: at each roll the OLD quarterly still prints
  front-scale volume on the declared roll date (6AZ5 16.3k, 6AH6 63.3k, 6AM6 64.4k,
  6AU6 28.8k on their respective roll dates) while the NEW quarterly is still thin
  (60–385) — because the raw files of expired contracts are truncated at the fetch
  boundary (day-1 of expiry month), the old-side decay AFTER the roll date and the exact
  old-vs-new crossover are NOT observable in this snapshot. The NEW quarterly first
  reaches front scale 6–11 sessions AFTER the roll date (6AH6 2025-12-10, 6AM6
  2026-03-10, 6AU6 2026-06-10, 6AZ6 2026-09-10 for v≥10k) — i.e. liquidity does NOT
  migrate pre-roll as it does on GC; it builds in the new contract in the first two weeks
  of its front window. Old-contract Sep-2026 behavior invisible (6AU6 file ends
  2026-08-31 although last trade was 2026-09-14). [OBSERVED + disclosed boundary]
- PIT contract selection + roll rule: baseline = data lane's declared rule — hold until
  the last session BEFORE day-1 of the delivery month, roll to the next listed contract
  at that close (months listed years ahead → PIT-legal, no lookahead) [FACT: FINAL_REPORT
  §roll rule]. **Executability defect found by this lane (GC-style check, explicitly
  requested)** [OBSERVED, analysis `serial_gap_executability`]: the LITERAL rule ("next
  listed contract", which includes serial months) is NOT executable on this snapshot for
  the span 2025-11-28 → 2026-08-31: it needs the serial contracts **6AF6 (2026-01),
  6AG6 (2026-02), 6AJ6 (2026-04), 6AK6 (2026-05), 6AN6 (2026-07), 6AQ6 (2026-08) — all
  six absent from the raw set** (the data lane's expired-walk resolved only quarterlies
  back to 2025-12 + the two near serials 6AV6/6AX6; S1 deepest_resolved = 202512). The
  executable approximation rolls quarterly→quarterly (HMUZ targets), which is also the
  market's liquidity chain (§liquid maturities). The literal rule becomes executable
  again only at 2026-08-31 (6AU6→6AV6 leg measured: gap −8 ticks = −$40, 6AV6 volume at
  roll only 22 lots) and would hold a 17-lot/median serial book for Sep-2026 —
  economically un-executable at any size. Note: whether the missing 2026 serials were
  listed on their roll dates cannot be adjudicated from this corpus (CME product calendar
  transport-blocked); the defect reported is snapshot non-executability, not non-listing.
  Alternatives: (a) volume/OI roll — OI not in raw; volume crossover not observable
  (truncation above); (b) fetch the 6 missing serials — all six are still inside the
  ~1y expired-resolve wall TODAY, but 6AF6/6AG6 age out around Jan–Mar 2027, so the
  re-fetch is time-critical (cheapest fix, same entitlement, no purchase). Roll cost:
  observable as adjacent-contract close gaps (measured below §3) but NOT_COMPUTED as a
  tradable cost. [OBSERVED; FACT for the rule]
- Continuous reconstruction reproducibility: localSymbol `6A{monthcode}{yeardigit}`
  (6AV6 = Oct-2026 …), conId per contract in S1/raw filenames; raw per-contract files
  stored; roll tables derivable (4 effective quarterly rolls measured); no
  back-adjustment performed anywhere (description-only mandate). [OBSERVED]

## 2. Causal driver map

Master-framework buckets covered for 6A: Macro (rates differential, USD, risk appetite),
Fundamental (terms of trade/commodities — the "physical" analogue for an FX contract),
Cross-asset, Positioning, Term structure, Microstructure, Event-driven. Evidence class
marks the *measurement* status in this prep.

| # | Driver (bucket) | Source variable → mechanism | Predicted sign / horizon | Regime dependency | Confounders | Falsification test | PIT data source (primary, access date) | Class |
|---|---|---|---|---|---|---|---|---|
| 1 | RBA–Fed policy differential (Macro) | RBA cash-rate path vs Fed funds path → covered/uncovered interest parity → AUD forwards discount/premium and spot drift | Higher AUD differential → AUD up (carry bid); hawkish RBA surprise → AUD up within minutes | Dominant in rate-cycle regimes; swamped by global risk-off (2008/2020-style) | USD leg moves with global rates; carry proxies co-move with risk appetite | RBA-hawkish-surprise days with no AUD same-day appreciation | RBA decision + SMP (rba.gov.au, FACT fetched 2026-10-02: 2026 meetings 2–3 Feb, 16–17 Mar, 4–5 May, 15–16 Jun, 10–11 Aug, 28–29 Sep, 2–3 Nov, 7–8 Dec; 14:30 Sydney announcement); Fed side FOMC calendar FACT (federalreserve.gov, fetched by sibling GC lane same date); surprise/consensus series NOT in corpus | Calendar FACT; response NOT_RUN |
| 2 | China growth / credit impulse (Fundamental-for-AUD) | China demand → Australian export volumes/prices (iron ore, coal, LNG) → terms of trade → AUD | China surprise ↑ → AUD ↑ over minutes-days | Strongest when commodity prices confirm; weak during China-specific policy shocks that hit commodities and AUD differently | AUD is also pure risk/USD beta; commodity prices co-move with global growth | China-surprise days with no AUD move after controlling for USD leg (6E/6B same-day) | Caixin PMI embargo 09:45 CST/01:45 UTC (pmi.spglobal.com press releases, FACT 2026-10-02); NBS PMI 09:30 CST convention (secondary, primary NOT_FETCHED); China trade/credit schedules NOT verified (NOT_RUN) | Timing FACT(partial); mechanism POSTULATED; response NOT_RUN |
| 3 | Iron ore / copper / terms of trade (Fundamental) | Bulk-commodity price ↑ → Australian export receipts ↑ → current-account and AUD demand ↑ | Positive, days-weeks | Regime-dependent: matters most when ToT trend is persistent | Iron ore is itself China-demand driven (collinearity with #2); USD pricing effect | Rolling AUD-vs-HG beta sign flips vs ToT trend | HG copper futures in own raw corpus (OBSERVED available); iron-ore price primary sources (Platts/SGX — licensed) NOT in corpus | Data availability OBSERVED; mechanism POSTULATED; measurement NOT_RUN |
| 4 | Global risk appetite / equity beta (Macro, cross-asset) | Risk-on → AUD buys (high-beta FX); risk-off → AUD sold vs USD/JPY | Positive co-move with ES/NQ, minutes-weeks | Beta rises in risk-on regimes (framework §15); AUD falls hardest in liquidity stress | Same macro news drives both (no lead/lag claim) | Rolling AUD–ES beta instability across vol regimes | ES/NQ in own raw corpus (OBSERVED available); VIX NOT in corpus | Data availability OBSERVED; mechanism POSTULATED; measurement NOT_RUN |
| 5 | USD cycle / DXY (Macro) | USD ↑ → AUD/USD ↓ mechanically (quote convention) | Negative vs dollar index, contemporaneous | Near-mechanical in calm regimes; idiosyncratic AUD drivers (RBA/China) decouple it | AUD idiosyncratic legs; rates differential co-drives USD | Weeks where 6A and 6E/6B diverge vs their dollar common factor | 6E/6B in own raw corpus (OBSERVED); DXY official (ICE) NOT fetched | OBSERVED data available; measurement NOT_RUN |
| 6 | Australian inflation / labour market (Macro, event) | Hot AU CPI/labour → RBA repricing → AUD up (and vice versa) | Event-day, minutes-hours | Matters most when RBA is in play (meeting-adjacent windows) | RBA forward guidance may already price the print | Post-CPI AUD move vs consensus surprise | ABS calendar FACT (abs.gov.au future-releases, fetched 2026-10-02: Labour Force Sep-ref Thu 2026-10-15 11:30 AEDT; quarterly CPI Sep-qtr Wed 2026-10-28 11:30 AEDT; all ABS releases 11:30 Canberra); consensus data MISSING | Calendar FACT; response NOT_RUN |
| 7 | CoT positioning (Positioning) | Leveraged-fund net extreme → squeeze/crowding risk; asset-manager real-money flows | Contrarian at extremes, weeks | Works in trending regimes, fails in crisis extension | CoT = Tue positions, Fri 15:30 ET release (≠ trade date); lumpiness | Extremes with no reversal | CFTC CoT incl. AUD futures: weekly, Fri 15:30 ET, as-of prior Tuesday, not revised [FACT: cftc.gov, fetched by sibling GC lane 2026-10-02]; series NOT fetched | Release rule FACT; use NOT_RUN |
| 8 | Term structure / carry (Term structure) | Rate differential → calendar slope; AUD-vs-USD policy gap sets 6A near/far spread | Roll gap sign tracks differential; horizon = roll cycle | Flips with relative policy moves | Settlement-derived deep bars; 91-day gaps | Measured quarterly roll gaps vs rate differential sign — done descriptively §3 | own raw panel (OBSERVED §3) | OBSERVED (descriptive) |
| 9 | Roll-window microstructure (Microstructure) | Liquidity concentration in quarterlies; serial months near-dead → selection-rule risk | Execution effect, not direction | Always; worst when literal roll lands on a serial | vendor truncation hides post-roll old-side decay | §1 measured volumes | own raw panel (OBSERVED §1) | OBSERVED |
| 10 | Related markets: 6E, 6B, 6J, HG, ES/NQ, China equities (Cross-asset) | Common-dollar + risk factors vs idiosyncratic AUD (China/ToT) | Correlative, days | Divergence itself is the China/ToT signal candidate | common drivers (see #4/#5) | rolling beta / lead-lag stability | 6E/6B/6J/ES/NQ/HG in own raw corpus (OBSERVED available); China equity indices NOT in corpus | OBSERVED available; measurement NOT_RUN |
| 11 | Scheduled macro events (Event-driven) | RBA/FOMC/AU-CPI/NFP/Caixin surprises → immediate repricing | Event-window, minutes-hours | First reaction vs drift split unknown | non-synchronous RTH window (all AU/China events fall OUTSIDE recorded hours — §3/§4) | event-time returns vs surprise sign | calendars FACT (§4); intraday depth ~10 months only; surprise data MISSING | Calendar FACT; response NOT_RUN |

## 3. Behavior (measured where legal)

All statistics: analysis/6A_descriptives.py → 6A_descriptives.json, computed from the raw
6A files; returns are within-contract daily simple returns on the unadjusted quarterly
chain (roll-date return belongs to the OLD contract; no stitched jumps); thresholds use
strictly-prior rolling windows; ex-post labels are description-only. No PnL/performance
metrics anywhere. useRTH=true: every "daily" bar covers only 08:30–16:00 CT.

- **What window is actually measurable**: 20 contracts in the raw set, per-contract daily
  depth back to 2021-09 (6Y fetch truncation), but 61–100% of each contract's bars are
  settlement-derived (v=0, O=H=L=C). The pre-2025-12 quarterlies (6AU5 and earlier) are
  absent entirely (expired-secdef wall). Real-volume (v>0) bars exist on 11 contracts;
  the executable quarterly chain carries **front-scale volume (≥10k lots/day) only from
  2025-09-10 → 2026-10-01 (241 sessions)**; before that the constructed chain tracks a
  deferred quarterly (6AU6 2021-09→2022-11 ~4y out; 6AZ5 2022-11→2025-09 ~3y→0y out),
  so full-chain stats are a movable-curve-point reference, settlement-derived — same
  construction caveat as the GC dossier, disclosed. Single-contract full-depth files
  (6AU6 2021-09→2026-08 n=1262; 6AZ6 2021-12→2026-10 n=1218) give clean long-horizon
  *reference* stats without stitching. [OBSERVED: `front_scale_era`,
  `single_contract_long_refs`]
- **Volatility (level and regime)**: annualized daily vol by year, quarterly chain
  (settlement-derived pre-2025): 2022 13.6% (post-Fed-hike USD surge peak), 2023 10.0%,
  2024 8.0%, 2025 9.8%, 2026 Jan–Sep 8.0%; single-contract 6AU6/6AZ6 confirm (13.5/13.6
  → 7.8/7.8 → 8.1/8.0). Front-scale real-volume era: σ = 0.469%/day → **7.45%
  annualized**, rolling-63-session vol range 0.37–1.06%/day (median 0.58%) full-chain.
  This is a structurally low-vol contract (vs GC 30.7% in 2026) — cost-as-vol-friction
  matters relatively more. Worst real-era day **−1.43% (2026-03-05)**; best **+1.29%
  (2026-03-10)**; worst overnight gap in the whole chain −3.53% (2025-04-04,
  tariff-shock week, pre-front-scale era on the deferred chain point). [OBSERVED]
- **Distribution / day asymmetry**: front-scale era n=241: mean +0.027%/day, median
  +0.043%/day (up-days outnumber down-days), σ=0.47%, q05/q95 = −0.81/+0.73%, skew ≈
  −0.01 (symmetric); full-chain (settlement era) skew −0.26. |r| lag-1 autocorr 0.036
  (front-scale) / 0.096 (full) — essentially no daily vol clustering at lag-1, unlike
  equities. [OBSERVED]
- **Trend persistence**: share of days whose return sign matches the prior-50-session
  mean sign = **49.4%** (n=267) — coin-flip; no exploitable daily trend persistence at
  this horizon in this window. [OBSERVED, description-only]
- **Large-move frequency (strict past threshold)**: days with |r| above the 95th
  percentile of the prior 126 sessions' |r|: 16 of ~250 evaluated, clustered in
  Jan–Feb 2026 (5), Mar 2026 (6), Apr–Jun 2026 (4), Sep 2026 (1) — vol arrives in
  bursts around macro weeks. [OBSERVED, description-only]
- **Seasonality (description-only)**: full-chain mean |r| by calendar month is flat
  (5.5–8.7 bp/day band, Apr highest 0.87%, Aug lowest 0.55%); weekday means
  (front-scale era, n≤56/cell) drift from Mon +8.3bp through Wed +3.9bp to Thu
  −8.0bp / Fri −1.8bp — NOT a signal. Australia-specific fiscal/seasonal patterns
  unmeasured. [OBSERVED, tiny buckets]

> **ERRATUM (2026-10-02, round co-owner-review-fix-1, lane HANDOFF-RESEARCH)
> — units and statistic-label correction to the Seasonality bullet above.**
> Two errors in the superseded wording (preserved verbatim above):
> (1) **10× unit slip**: "0.87%" and "0.55%" of price per day are **87 bp/day
> and 55 bp/day**, so the monthly band is **55–87 bp/day**, not "5.5–8.7
> bp/day". (2) **Wrong statistic label**: those monthly numbers are the
> **daily-return volatility (σ) by calendar month** (6A_descriptives.json
> `seasonality.by_calendar_month_full_chain[*].vol`: Apr σ = 0.866%/day =
> 86.6 bp, the highest; Aug σ = 0.545%/day = 54.5 bp, the lowest; all 12
> months within 54.5–86.6 bp/day), NOT "mean |r|" — the per-month mean
> SIGNED returns are far smaller (−6.1 to +5.3 bp/day:
> `seasonality.by_calendar_month_full_chain[*].mean`). The weekday numbers
> (+8.3/+5.3/+3.9/−8.0/−1.8 bp Mon–Fri, front-scale era) were already stated
> in bp and are correct as written (they are mean signed returns;
> `by_weekday_front_scale_era[*].mean`). Conclusion unchanged: flat, NOT a
> signal.
- **Term structure / roll gaps (measured, descriptive)**: quarterly-chain roll-session
  adjacent-contract close gaps (new−old): 6AZ5→6AH6 **+4 ticks (+$20)**, 6AH6→6AM6
  **−11 ticks (−$55)**, 6AM6→6AU6 **−27 ticks (−$135)**, 6AU6→6AZ6 **−23 ticks
  (−$115)**; annualized +0.12% (Nov-2025 roll) then −0.31% to −0.75% across the three
  2026 rolls (deferred cheaper = mild backwardation, direction consistent with AUD
  short rates below USD for most of 2026 — linkage POSTULATED, not tested). Literal
  serial leg 6AU6→6AV6 measured at −8 ticks (−$40). Gaps are 3–5× the median front
  spread — real but second-order vs daily vol. Gap ≠ tradable cost (crossing both legs
  costs more; roll cost NOT_COMPUTED as tradable). [OBSERVED:
  `declared_rule_rolls_*`]
- **Curve snapshot (2026-10-01)**: quarterly ladder 6AZ6 0.69170 / 6AH7 0.69095 /
  6AM7 0.69040 / 6AU7 0.68995 / 6AZ7 0.68975 — monotonic discount of ~0.28% from Dec-26
  to Dec-27 (~0.07%/quarter; the Mar/Jun/Sep-27 marks are settlement-derived v=0 that
  day, description only). Serials 6AV6 0.6923 / 6AX6 0.6920 sit marginally ABOVE the Dec
  quarterly (near-flat to it, on thin 8-lot/4-lot books). [OBSERVED, settlement-derived
  deferred caveat]
- **Session behavior — US RTH only**: pooled hourly bars of the current chain front
  6AZ6 (2026-08-20→2026-10-01, 240 bars, 30 sessions): volume share peaks in the
  **09:00–10:00 CT hour (23.3%)**, then 10:00 (18.3%), a secondary bump 13:00 CT
  (15.8%, the FOMC/settlement-adjacent hour), decaying to 15:00 (3.4%); the 08:30–09:00
  US-open stub carries 9.3%. **Sydney/Tokyo/London behavior: NOT_RUN** — useRTH=True
  files contain no overnight bars, and for 6A the home session is where RBA/AU/China
  events land (§4), so the intraday information-leadership question is unanswerable
  from this corpus. [OBSERVED / NOT_RUN]
- **Hidden-session (overnight) gap**: RTH-open vs prior-RTH-close gap, quarterly chain:
  front-scale era median **+0.5 pips** (≈ zero), σ 0.38%, q05/q95 −0.56/+0.65%, max
  +1.66%; 12.0% of all days gap ≥2× trailing-20d mean |ret|. Biggest gaps cluster on
  known macro mornings (2025-04-04 −224 pips tariff week; 2022-11-04 +196 pips; 2022
  CPI-era dates). This gap is the ONLY legal window on the Sydney/London/US-data part
  of the day in this corpus. [OBSERVED]
- **1-minute behavior: NOT_RUN** — 1-min files are 2-day RTH-only snapshots (900 bars
  2026-09-30→2026-10-01, 08:30–15:59 CT, offsets −05:00 DST-correct) plus a 30-bar
  settlement-hour probe; unsuitable for distributional statements.
- **Spread/cost observations**: daily BID/ASK closes (non-synchronous → NOT an
  executable spread): quarterly-chain front days (n=241) median **2 ticks = $10**,
  p90 $10; all-chain days median 2 ticks $10, p90 $40; 0 crossed days. The S1 serial
  front 6AV6 itself: median **4 ticks = $20** (n=95 days) — reconciles exactly with
  S6_FRONT_SPREADS 6A (4.0 ticks, $20, n=20); the deferred Nov serial 6AX6 shows
  median 265 ticks ($1,325) quote-rot. Commission: IBKR $0.85/side + exchange fee
  NOT_FETCHED (only the ES $1.38 official example exists); slippage
  NOT_RUN_NO_DECLARED_VALUE; margins (public broker pages, 2026-10-02): initial
  $2,090, maintenance $1,900/contract (NinjaTrader) vs $1,925 maintenance (AMP) —
  broker-class, not CME SPAN (blocked). [OBSERVED + FACT-secondary per costs/]
- **Volume-recording consistency**: hourly sums equal daily volumes exactly on the three
  dates checked (6AZ6 2026-09-15/21/28: 27,692/22,100/46,592 both ways) — no per-symbol
  vendor scaling artifact of the GC V-month type detected; deferred/serial thinness is
  real book depth, not recording. [OBSERVED, spot check]

## 4. Event calendar

Scheduled events relevant to 6A, with UTC + exchange-tz (CT) timing. Release calendars
are FACT (official sources, access date 2026-10-02). Response measurement of 6A to any
event: NOT_RUN (no intraday depth outside RTH — see the tz map — and no
surprise/consensus data in corpus).

| Event | 2026 remaining dates | Release time (source tz) | UTC | CT (exchange tz) | PIT properties | Source (access 2026-10-02) |
|---|---|---|---|---|---|---|
| RBA cash-rate decision (8 meetings/yr) | Nov 3, Dec 8 (held: Feb 3, Mar 17, May 5, Jun 16, Aug 11, Sep 29) — meetings 2–3 Nov, 7–8 Dec | 14:30 Sydney (AEDT Nov/Dec) | 03:30 UTC (04:30 UTC in AEST months) | 22:30 CT prior calendar day | Statement + SoMP quarterly (Nov SoMP); minutes +2 weeks; decision not revised | rba.gov.au/media-releases/2025/mr-25-02.html (primary, fetched); announcement-time text on rba.gov.au/monetary-policy/int-rate-decisions/ (primary, fetched) |
| ABS quarterly CPI (Sep qtr) | Wed Oct 28 | 11:30 Canberra (AEDT) | 00:30 UTC | 19:30 CT prior day | first print is tradeable vintage; seasonal revision later | abs.gov.au/release-calendar/future-releases (primary, fetched) |
| ABS Labour Force (Sep ref) | Thu Oct 15 | 11:30 Canberra (AEDT) | 00:30 UTC | 19:30 CT prior day | monthly, revised; sample rotation | abs.gov.au/release-calendar/future-releases (primary, fetched) |
| ABS other (WPI, AWE, trade) | Oct 2026: Building Approvals Oct 7, OAD Oct 13, national accounts Oct 23, PPI Oct 30 | 11:30 Canberra | 00:30 UTC | 19:30 CT prior day | — | abs.gov.au future-releases calendar (primary, fetched; Nov/Dec pages not yet listed) |
| Caixin China General Manufacturing PMI (Oct ref) | first business day of Nov (Sep print moved to Sep 30 due to Golden Week) | 09:45 China Standard Time, embargoed | 01:45 UTC | 20:45 CT prior day | private-survey print, no revision; co-published Caixin/S&P Global | pmi.spglobal.com press-release embargo text + release calendar (primary, fetched via search-visible release hub); convention corroborated by spglobal release list |
| China NBS official PMI | last day of reference month | 09:30 CST (convention) | 01:30 UTC | 20:30 CT prior day | official, sometimes delayed | stats.gov.cn NOT_FETCHED this session (secondary convention only — treat timing as unverified) |
| China trade balance (GACC) | ~7th–13th of following month, no fixed date | morning Beijing, embargo shifts | NOT verified | — | RMB-denominated vs USD versions differ | customs.gov.cn NOT_RUN (not fetched) |
| China credit/aggregate financing (PBOC) | no fixed schedule, 10th–15th window | — | — | — | revised, pre-announced window only | NOT_RUN |
| FOMC decision | Oct 27–28; Dec 8–9 (2026 meetings incl. Jan 27-28, Mar 17-18, Apr 28-29, Jun 16-17, Jul 28-29, Sep 15-16) | statement day-2 (conventionally 14:00 ET, not confirmed on page) | ~18:00/19:00 UTC | 13:00 CT (INSIDE measured RTH) | minutes +3 weeks; SEP quarterly | federalreserve.gov/monetarypolicy/fomccalendars.htm (primary; fetched by sibling lane SYMBOL-DOSSIER-GC this task, same access date 2026-10-02) |
| US CPI (BLS) | Oct 14, Nov 10, Dec 10 | 08:30 ET | 12:30/13:30 UTC | 07:30 CT (1h BEFORE RTH open — lands in the opening gap) | first print tradeable; SA series revised | bls.gov/schedule/news_release/cpi.htm (primary; sibling GC lane, same date) |
| US Employment/NFP (BLS) | Oct 2, Nov 6, Dec 4 | 08:30 ET | 12:30/13:30 UTC | 07:30 CT (pre-RTH) | payrolls revised twice + annual benchmark | bls.gov/schedule/news_release/empsit.htm (primary; sibling GC lane, same date) |
| CFTC CoT (financial futures incl. 6A) | weekly Fridays 15:30 ET | 15:30 ET | 19:30/20:30 UTC | 14:30 CT (inside RTH tail) | positions as-of PRIOR Tuesday; not revised; release ≠ position date | cftc.gov Commitments of Traders (primary; sibling GC lane, same date) |
| 6A roll/expiry (contract events) | declared-roll sessions ahead: 2026-10-30 (6AZ6, Dec delivery; also literal 6AV6→6AX6 serial roll 2026-09-30 already occurred), last-trade dates from S1: 6AV6 2026-10-19, 6AX6 2026-11-16, 6AZ6 2026-12-14 | 09:16 CT cessation on last-trade day | — | — | listing calendar known years ahead (PIT-legal roll decisions) | OBSERVED: S1_IDENTITY.json chain + raw bars |

Effective vs available vs retrieved (general PIT rule for this dossier): the times above
are the *available* times; nothing has been *retrieved* into a PIT store this cycle; any
hypothesis using macro/consensus series must store vintage/first-release values, else
treat as unsuitable for strict PIT tests. **Timezone asymmetry (critical for this
corpus)**: every AU/China event lands 19:30–22:30 CT of the prior calendar day — inside
the Globex session but OUTSIDE the recorded RTH bars; US events land 07:30 CT (pre-RTH
open) except FOMC (13:00 CT, inside RTH). Event-day reactions are therefore measurable
only through the next RTH open/close and the hidden-session gap statistic.

## 5. Hypotheses (3–5, ranked by testability × causal plausibility — NOT by PnL)

Reuse disclosure: corpus-1200 is outside this lane's read scope — idea-line/ID mapping
**NOT_RUN**. The owner framework's §15 hypotheses (commodity-confirmation of AUD trend,
China-surprise × commodity confirmation, AUD equity-beta regime dependence,
rate-differential weakening in China shocks) are treated as HYPOTHESES to specify, not
validated results. Transferring any AUD/USD **spot** corpus idea to 6A futures is a
hypothesis with basis (futures≈CIP-forward, roll gaps OBSERVED −0.3…−0.75% ann.),
serial-month liquidity (§1) and cost ($10–20 spread + unfetch-fee commissions)
differences — never "already valid".

**H1 — RBA-decision hidden-session reaction (rank 1: the only event family fully in
legal daily data, mechanism crisp).**
When the RBA surprises hawkish (dove) at 14:30 AEDT (22:30 CT prior day), the 6A front's
next RTH session open should gap in the decision direction more than non-event days,
because AUD is the direct policy asset and the decision hits the home session where 6A
liquidity actually lives (unmeasured by our RTH bars, captured by the open).
- PIT condition: RBA decision timestamp (calendar known years ahead, FACT) + a
  hawkish/dovish classification defined ex-ante from market-based pricing (e.g. AUD/USD
  spot 5-min move at 14:30 Sydney — NOT in corpus → PARAM-GAP; cash-rate change vs
  prior-meeting market pricing is a weaker observable proxy available from RBA media
  releases FACT).
- Predicted move: |gap| on 8 RBA days/yr exceeds the non-event typical scale
  (front-scale q05/q95 = −0.56%/+0.65% of level; median signed gap +0.5 pips);
  horizon: overnight → first RTH session.
- Mechanism: policy-rate path repricing → carry/flow rebalancing.
- Strongest regime: active easing/tightening cycles (2026 has cuts in play); weakest:
  hold-streak meetings priced at ~100%.
- Entry/exit/TP/SL/time: descriptive first (no trade): event-day vs non-event-day gap
  distribution comparison only; entry realism for any later trade version requires
  Globex data at 22:30 CT — NOT in corpus (PARAM-GAP).
- Direction: conditional (hawkish→long); universe = 6A quarterly front (declared roll,
  quarterly adaptation — serials un-executable §1); sizing n/a (measurement); cost model
  = 2-tick median front spread ($10) for any future execution version; invalidation =
  RBA-day gap distribution indistinguishable from non-event days over ≥16 meetings;
  counter-hypothesis = RBA decisions are fully pre-priced (long hold streaks) → no gap;
  failure = classification of surprise requires consensus data not in corpus;
  data floor: HAVE daily RTH opens around all 8 meetings/yr + gap machinery; NEED
  5-min AUD/USD or Globex M1 at decision time (vendor, owner decision); budget: $0 for
  the daily-data version.

**H2 — Commodity/China confirmation of AUD trend state (rank 2: framework §15 idea 1,
partially measurable on own corpus daily data).**
When HG copper (and/or an iron-ore proxy) trends up over the prior 63 sessions while the
6A quarterly front also trends, AUD trend persistence should exceed its ~49.4%
unconditional coin-flip persistence; when commodities diverge (down while AUD up),
persistence should collapse, because AUD trend durability depends on the terms-of-trade
channel sustaining flows.
- PIT condition: prior-63-session sign of 6A front return and of HG front return
  (strict past windows; both in raw corpus — HG measurable settlement-era deep + 2025+
  real volume).
- Predicted: sign-match persistence > 60% in confirmed regimes vs < 40% in divergent
  (numbers are pre-registration targets, not results — NOT_RUN until measured).
- Mechanism: ToT channel → exporter hedging asymmetry → order-flow persistence.
- Strongest regime: China stimulus/recovery phases; weakest: USD-shock-dominated phases
  (2022-style) where commodities and AUD both fall with the dollar regardless of China.
- Entry/exit/holding: PARAM-GAP (deliberate: specifying thresholds now with only ~13
  months of overlap-era real-volume data would be ex-post tuning on 2026 only);
  direction long/short 6A front conditional; roll = quarterly adaptation; sizing 1
  contract baseline; costs = 2-tick spread + commission NOT_FETCHED; invalidation =
  persistence differential ≤ 0 in confirmed regimes over ≥ 8 rolling quarters;
  counter-hypothesis: HG-6A relation is pure common-USD beta, not ToT (control: run same
  test on 6E/6B — if identical, USD beta is the explanation); failure = deep-era
  settlement bars understate true vol pre-2025 making persistence estimates unreliable;
  data floor: HAVE both series daily (settlement-era caveat); NEED iron-ore primary
  price (licensed) for the real ToT driver — owner decision; budget $0 for HG version.

**H3 — Quarterly-roll execution vs the thin-serial trap (rank 3: fully measured on data
in hand, execution-economics hypothesis).**
Holding the literal declared rule (next listed incl. serials) through Sep–Oct 2026 would
have parked position-keeping in a 17-lot/median book (6AV6) paying 4-tick spreads ($20)
while the market's liquidity chain (6AZ6) printed 27–67k lots at 2-tick spreads ($10) —
the hypothesis: a quarterly-target roll variant strictly dominates the literal rule on
execution cost and capacity with essentially identical exposure (measured roll gap
differences: −8 vs −23 ticks at the same roll date).
- PIT condition: none (contract-selection rule choice, decided ex-ante).
- Predicted effect: ~½ spread saving per side + 3 orders of magnitude more depth; drift
  between the two chain variants since the 2026-08-31 roll ≈ +0.10% (serial roll gap
  −5.6bp vs quarterly −16.0bp of level at the same date).
- Mechanism: liquidity-provider inventory costs in dying/thin serials.
- Strongest/weakest regime: always (structural), worst when literal rule lands on a
  serial following a quarterly with 5 weeks to expiry.
- Rules: switch roll target to next HMUZ; everything else identical to declared rule;
  direction none; sizing capacity: serial book ~17 lots/day median (max 79) vs
  quarterly ~35k/day median; cost model measured (§3); invalidation = serial books
  later deepen (check deferred serial volumes each quarter); counter-hypothesis =
  calendar-risk: skipping serials changes delivery-month exposure vs hedging needs
  (serial months are deliverable too); failure = none measured; data floor: HAVE;
  budget $0.
- NOTE: this is an execution-design finding already 95% OBSERVED (§1/§3); the residual
  hypothesis is only the forward claim.

**H4 — AUD equity-beta regime dependence (rank 4: framework §15 idea 3, data-gated).**
AUD's beta to ES/NQ should rise in risk-on (defined ex-ante by trailing-vol quantile of
ES below its prior-year median) and flip/narrow in stress, because AUD is a long-risk
carry currency. Testable on daily closes already in raw (both symbols, same RTH
convention). PARAM-GAP on the regime-tagging threshold (must be fixed a priori in a
later spec to avoid tuning on 2026); invalidation = rolling beta unstable within-regime
year-by-year; counter = beta is just USD-beta in disguise (control 6E); data floor HAVE;
budget $0. Mechanism POSTULATED; measurement NOT_RUN.

**H5 — Rate-differential carry sign vs roll-gap sign (rank 5: crisp macro check, data
half-missing).**
The 6A calendar-slope sign (measured: −0.3% to −0.75% annualized at 2026 rolls) should
track the AUD-vs-USD short-rate differential sign with a lag, per CIP; when the
differential flips (RBA hiking while Fed cuts), roll gaps should turn positive. Requires
PIT rate histories (RBA cash rate FACT media releases; Fed funds target FACT) + roll
gaps (HAVE, only 4 effective rolls in real-volume era — sample floor NOT met, need ≥8).
Everything directional per driver-map row 1/8; explicitly NOT_RUN beyond the four
measured gaps.

## 6. Missing data table

| Need | Have | Source (primary first) | Period | Schema | PIT properties | License / cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Real-volume daily per-contract ≥24 months incl. pre-2025 quarterlies (6AU5…) AND the 6 missing serials (6AF6/6AG6/6AJ6/6AK6/6AN6/6AQ6) | 2025-09-10→2026-10-01 real-volume on quarterlies only | current IB entitlement first (serials 2026 still within ~1y expired-resolve window — cheap NOW); else Databento/CME DataMine (owner decision) | 2019→ | per-contract OHLCV daily | timestamps CT, PIT | $0 now / vendor $ owner | expired-secdef ~1y wall; serials never fetched | re-fetch 6 serials immediately (they age out of the resolve window from Jan-2027); pre-2025 quarterlies need vendor |
| Overnight/full-session intraday (M1 or 5-min incl. Sydney 22:00–06:00 CT, London, 07:30 CT US block, 22:30 CT RBA window) | 30-D RTH-only hourly, 2-D RTH 1-min | vendor (Databento glbx.mdxp3-style, full 23h) | 2019→ | 1-min OHLCV full session | UTC-stamped | $ owner decision | entitlement vintage wall ~10 months + RTH-only recording | owner vendor decision via DATA-PIT-ACQUISITION-PREP lane spec |
| Macro surprise/consensus (RBA pricing, AU CPI, Caixin, US CPI/NFP) | release CALENDARS only (FACT) | RBA/ABS/BLS official + consensus vendor | 2019→ | event time, consensus, actual, prior | first-print vintage | consensus licensed ($ owner) | no consensus source in corpus | owner budget decision; until then H1/H2/H4 stay partially PARAM-GAP |
| Iron-ore primary price (ToT driver) | none (HG copper proxy in corpus) | Platts/S&P or SGX TIO official | 2019→ | daily/weekly assessment timestamps | assessment publication time | licensed ($ owner) | not in corpus | add to vendor spec only if H2 advances |
| CFTC CoT incl. AUD (leveraged funds / asset managers) | none (release rule known, FACT) | cftc.gov legacy + TFF | 2019→ | weekly Tue positions, Fri 15:30 ET release | not revised; release≠position date | free | not fetched | fetch when positioning hypotheses enter measurement |
| Open interest per contract (OI-based roll, capacity) | none in raw | vendor/CME | 2019→ | daily OI per contract | T+1 publication | vendor terms | not in entitlement snapshot | add to vendor data spec |

Priority = top-3 causal drivers (rate differential, China/ToT, full-session intraday) +
the one time-critical $0 fix (serial re-fetch before the expired-resolve wall ages them
out). This dossier does NOT condition on the full wishlist.

## 7. Framework coverage

Master framework §1 (10 questions):

1. Underlying economic exposure → AUD 100,000 vs USD, USD-per-AUD quote, physically
   delivered; China/commodity/rates-differential/risk-appetite exposure per framework
   core. [OBSERVED S1; exposure framing POSTULATED]
2. Natural hedgers/speculators/MMs/arbitrageurs → commodity exporters/importers/banks;
   macro funds/CTAs/carry; MMs & CIP-basis arbitrage vs spot. [POSTULATED]
3. Exchange & hours → CME Globex Sun 17:00→Fri 16:00 CT, daily 16–17:00 CT break;
   RTH 08:30–16:00 CT recorded; DST verified in bars (S9 method). [OBSERVED]
4. Size/tick/currency/margin/settlement → AUD 100k; 5e-05 = $5/tick (tick CONFLICT
   flagged, CME blocked); USD; margin ~$1.9k maint/$2.09k init (broker-class public);
   physical delivery 3rd Wednesday. [OBSERVED + FACT-secondary; adjudication NOT_RUN]
5. Listed months & normally liquid expiries → quarterlies H,M,U,Z backbone + listed
   serials (incl. current serial front); liquid = nearest quarterly. [OBSERVED]
6. When does liquidity migrate → NOT fully observable (old-side truncation); new
   quarterly reaches front scale 6–11 sessions after roll date; serials never liquid.
   [OBSERVED with boundary disclosure]
7. Dominant price behavior → POSTULATED: rates-differential/macro-expectations +
   China/ToT; NOT cash-arbitrage or storage driven; measured: mild 2026 backwardation
   (roll gaps −0.3…−0.75% ann.), near-flat overnight drift. [POSTULATED + OBSERVED
   curve]
8. Which session matters → measurable only for US RTH (09:00 CT hour = 23% of RTH
   volume); home session (Sydney) where RBA/AU/China events land: NOT_RUN (no
   overnight bars). [OBSERVED/NOT_RUN]
9. "Tradeable" contract per timestamp → declared calendar rule NOT literally executable
   (6 missing serials, 2025-11→2026-08); quarterly adaptation executable and is the
   liquidity chain; OI unavailable; volume rule measurable only via front-scale ramp
   (post-roll). [OBSERVED]
10. Vendor symbols ↔ expiries, reproducible reconstruction → 6A{month}{year} codes,
    conIds in S1/filenames, raw per-contract files stored, 4 roll boundaries measured,
    no back-adjustment (description only). [OBSERVED]

6A framework's own checklist (foundation/market-structure/§14):

- What the contract represents / fair value vs cash → AUD/USD CIP forward; measured
  2026 calendar slope ≈ −0.07%/quarter (Oct-2026 ladder) / roll gaps −0.3%…−0.75%
  annualized, direction consistent with AUD short rates below USD; spot-basis/EFP
  NOT_RUN. [OBSERVED slope; POSTULATED linkage]
- Who must trade / who speculates → §1 participants [POSTULATED].
- Liquid expiries & migration timing → quarterly chain; ramp completes ~2 weeks into
  the new front window [OBSERVED; Q5/Q6].
- Settlement/delivery distortions of the front → physical delivery + 09:16 CT
  cessation; front distortion at expiry NOT measured (no expiry-week microstructure)
  [FACT-secondary; NOT_RUN].
- Which session contains information/liquidity → RTH only measured; home session
  NOT_RUN [§3].
- Minimum data to reconstruct a PIT series → per-contract daily TRADES+BID/ASK on the
  quarterly chain (HAVE, 13 months real-volume) + missing serials list (§6) [OBSERVED].
- Volume by session/expiry, roll speed, spread widening, opening/settlement effects,
  selection-rule stability, back-adjustment impact on trend → volume-by-expiry OBSERVED
  (serial/quarterly split); roll speed partially OBSERVED (new-side ramp; old-side
  truncated); spread near expiry/releases NOT_RUN (no synchronized quotes; serial
  quote-rot OBSERVED); opening/settlement intraday effects NOT_RUN; rule comparison
  (calendar vs volume vs OI) NOT_RUN (OI missing, crossover unobservable);
  back-adjustment effect NOT_RUN (no adjusted series built — description-only mandate).
- §14 questions (China/commodity explanation beyond USD beta; best commodity proxy;
  when RBA dominates; equity-beta stability) → all POSTULATED/NOT_RUN (no external PIT
  series in corpus this cycle); the control designs (6E/6B vs 6A, HG proxy) are
  specified in H2/H4.

---

### Defects / caveats register (this lane)

1. [OBSERVED] Serial months 2026-01/02/04/05/07/08 (6AF6…6AQ6) absent from the raw set →
   literal declared roll rule NOT executable 2025-11-28→2026-08-31; all chain stats use
   the quarterly adaptation (disclosed). Pre-2025-12 quarterlies absent entirely
   (expired wall) → chain tracks deferred contracts pre-2025-09 (settlement-derived).
2. [OBSERVED] Old-contract raw bars truncate at the fetch boundary (day-1 of expiry
   month) although legal last trade is ~2 weeks later (6AU6 ends 2026-08-31, last trade
   2026-09-14) → post-roll old-side decay and the exact volume crossover are NOT
   observable; GC-style "migration 1–2 sessions early" cannot be checked for 6A — the
   observable fact here is the new-side ramp (6–11 sessions post-roll).
3. [OBSERVED] Deep daily bars are settlement-derived (61–100% flat per contract) —
   usable as reference/curve only, never fill prices.
4. [NOT_RUN] CME official numeric spec/fee/SPAN/delivery text not retrievable (direct
   HTTP 403 re-verified by the data lane 2026-10-02; web-reader fallback renders
   marketing-level content only) — specs rest on broker secdef (OBSERVED, uniform) +
   vendor mirrors (secondary); 6A tick-size CONFLICT (0.00005 vs 0.0001) remains
   unadjudicated.
5. [NOT_RUN] Intraday = RTH-only 30-D windows + 2-D 1-min; no Sydney/Tokyo/London data;
   every AU/China scheduled event falls outside recorded bars (§4 tz map).
6. [OBSERVED] Event timing FACTs rest on rba.gov.au / abs.gov.au / pmi.spglobal.com
   (fetched 2026-10-02, primary) + federalreserve.gov / bls.gov / cftc.gov (primary,
   fetched by sibling GC lane the same task-date); China NBS/GACC/PBOC schedules NOT
   fetched — marked NOT_RUN, not assumed.

---

### CoT revision-policy verification note (added 2026-10-02, round co-owner-review-fix-1, lane HANDOFF-RESEARCH)

The CoT "not revised" wording in §2 driver-map row 7, §4 CoT calendar row and §6 missing-data CoT row (this dossier) was re-verified against primary CFTC
documentation on 2026-10-02:

1. Release rule CONFIRMED (FACT stands): "The COT Report is generally
   published each Friday at 3:30 pm Eastern Time (US)"; the reports
   "provide a breakdown of each Tuesday's open interest"; "Generally, the
   data in the COT reports is from Tuesday and released Friday."
   https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
   (accessed 2026-10-02).
2. No-revision property CONFIRMED for the AS-PUBLISHED weekly reports —
   the FACT stands with scope = as-published weekly files. CFTC FAQ answer,
   verbatim: "No, historical data is not updated once published."
   (same URL, accessed 2026-10-02).
3. SCOPE QUALIFICATION for the TFF supplement: TFF HISTORICAL compressed
   files are NOT vintage-stable — "the CFTC does not maintain a history of
   large-trader classifications, so, recent classifications had to be used
   to classify the historical positions of each reportable trader" (Form 40
   refreshed "every 2 years or more often"; classification shifts restated
   into history). Traders in Financial Futures Explanatory Notes,
   https://www.cftc.gov/sites/default/files/idc/groups/public/@commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf
   (accessed 2026-10-02). Strict PIT use must pin release-dated weekly
   files, never the current compressed history.

Verdict: no class downgrade for the release rule or the as-published
no-revision claim; the blanket "not revised" is scope-qualified wherever
"cftc.gov legacy + TFF" is cited as a future source (§6 here). Shared note in
RESEARCH_MATRIX.md §CoT.
