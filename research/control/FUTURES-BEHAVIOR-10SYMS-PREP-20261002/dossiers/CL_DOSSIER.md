# CL_DOSSIER — WTI Light Sweet Crude Oil Futures (NYMEX)

- **Symbol:** CL (tradingClass CL, NYMEX, CME Group)
- **Exchange:** NYMEX (CME Group); Globex electronic
- **Generated_utc:** 2026-10-02
- **Author lane:** SYMBOL-DOSSIER-CL (task FUTURES-BEHAVIOR-10SYMS-PREP-20261002, prep only — no scored runs, no PnL, no event studies, no parameter selection)
- **Inputs:**
  - `owner_framework/CL_RESEARCH_FRAMEWORK.md` sha256 `f3c32c9effd70914cd4c30705c4b422ce83547bacaa0a280322d5653426a2cce` (owner research document; its claims are HYPOTHESES, not facts)
  - `owner_framework/00_MASTER_FRAMEWORK.md` sha256 `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`
  - `research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md` (+ S1_IDENTITY.json, S6_FRONT_SPREADS.json, S9_INDEPENDENT_VERIFY.md, costs/) — untracked read-only data-lane snapshot, 2026-10-02
  - Raw data: `~/.my-quantitative-data/futures-10syms-v1/raw/CL_*` (read-only; 29 per-contract daily 6Y TRADES files + BID/ASK 1Y + H1 30D RTH + M1 2D RTH; fetched 2026-10-02 via TWSAPI)
  - This lane's computation: `analysis/CL_behavior_stats.py` → `analysis/CL_behavior_stats.json` (all OBSERVED numbers below trace there)
- **Conventions (data lane S1/S9, verified):** raw field `expiry_month` holds lastTradeDate (e.g. CLX6 → 20261020); **delivery month = the localSymbol month code's own month (X = Nov — CLX6 is the Nov-2026 delivery; its last trade 2026-10-20 sits ~3 business days before Oct-25, in the month prior to delivery)** [ERRATUM 2026-10-02, audit M4: an earlier revision of this line said "delivery month = month after the localSymbol month code", which would make CLX6 a December delivery — contradicting S9 C3 ("delivery month … implied by the localSymbol code", lastTradeDate one month earlier), the raw LTDs, and this dossier's own "29 contiguous delivery months 2025-10…2028-02" letter-month count. Corrected here and in DATA_ACQUISITION_SPEC.md §4.]. Intraday files are useRTH=True (09:30–17:00 ET bars only). Deep per-contract daily history is close-only v=0 settlement-derived — reference/signal price only, NEVER a fill price. Real volume exists only in each contract's final months.

---

## 1. Mechanics

**Underlying exposure.** One CL contract = 1,000 barrels of WTI light sweet crude, physically delivered at Cushing, OK (pipelines/storage), quoted in USD and cents per barrel, tick $0.01/bbl = $10/contract. [FACT — CME product page https://www.cmegroup.com/trading/energy/crude-oil/light-sweet-crude.contractSpecs.html (direct fetch transport-blocked this session; spec essentials confirmed via search render of the official page: "Contract Unit 1,000 barrels", "Price Quotation U.S. dollars and cents per barrel", min fluctuation $0.01/bbl; cross-checked with three independent public spec mirrors fetched 2026-10-02: https://www.ninjatrader.com/futures/futures-contracts/energy/crude-oil/ , https://www.ampfutures.com/trading-info/contract-specifications/ , https://en.wikipedia.org/wiki/West_Texas_Intermediate ; and with data-lane S1_IDENTITY.json: multiplier 1000, minTick 0.01 on all resolved CL contracts. Access date 2026-10-02 for all.] Multiplier/minTick verified against S1 as required (raw bars do not carry them — S9 caveat C4). [OBSERVED for the S1 cross-check]

**Participants.** Natural hedgers: producers (sell forward), refiners (buy crude / sell products), physical merchants, airlines/transport consumers. Speculators: CTAs, commodity index/funds, macro funds. Market makers and spread traders arbitrage the curve (calendar spreads, WTI–Brent, crack spreads). [POSTULATED — participant taxonomy from owner framework §13 and standard market structure; no position-level data measured in this prep. The existence of the commercial vs non-commercial split is FACT via the CFTC CoT report structure itself (see §4), but no positioning behavior was measured: NOT_RUN.]

**Sessions + DST.** CME Globex Sun 18:00 → Fri 17:00 ET with a 60-minute daily maintenance break 17:00–18:00 ET. [FACT — CME spec page (render/snippet as above; access 2026-10-02); corroborated OBSERVED by S1_IDENTITY.json tradingHours string for CLX6/CLZ6: `20260930:1800-20261001:1700;...;20261003:CLOSED;20261004:1800-...` in US/Eastern.] Bar timestamps are DST-correct at each bar's own date (S9 independent check #5: 30 CL 1-min files, 100% ISO-offset match to US/Eastern, EST/EDT switches correct). [OBSERVED — S9]

**Holidays.** Weekends CLOSED per tradingHours string [OBSERVED — S1]; full NYMEX holiday calendar (e.g. shortened Christmas sessions) NOT verified: CME holiday page transport-blocked. [NOT_RUN]

**Delivery / first-notice / expiry / price limits.**
- Physical delivery via transferable receipts; there is no equity-style "first notice day" for CL, delivery follows the delivery month; contact with the delivery cycle is avoided by rolling before the last-trade month begins. [POSTULATED for mechanics detail; the delivery month convention is FACT/OBSERVED below]
- Termination rule: "trading ceases three business days before the 25th calendar day of the month prior to the contract month" [FACT — NinjaTrader/Wikipedia/TradingCharts mirrors of the NYMEX rule, URLs above, access 2026-10-02; CME rulebook text itself transport-blocked]. Cross-check: all 29 contracts' raw lastTradeDate fields are consistent with this rule once weekend/holiday reference shifts are accounted for (naive weekday arithmetic matches 16/29 exactly; the 13 others sit 1–3 calendar days earlier, the pattern expected when the 25th falls on a weekend/holiday — e.g. Nov-2025 delivery LTD Tue 2025-10-21 with the 25th on a Saturday). Exact holiday adjudication NOT_RUN. [OBSERVED — analysis/CL_behavior_stats.json `contracts`]
- Price limits: dynamic (initial limit cited as 15% above/below prior settlement for CL by Barchart profile, https://www.barchart.com/futures/quotes/CL*0/profile , access 2026-10-02 — secondary source; CME rulebook primary = transport-blocked). No limit-hit day occurred in the true-volume window (max |daily move| 11.7% < 15%). [FACT(secondary) for the mechanism; OBSERVED for no-hit]

**Listed months & liquid maturities.** All 12 months listed, current year + ~10 calendar years + 2 additional months. [FACT — NinjaTrader/Wikipedia mirrors, access 2026-10-02] OBSERVED in snapshot: 29 contiguous delivery months 2025-10 … 2028-02 present. Liquidity concentrates in M1–M3: volume on 2026-10-01 was M1 CLX6 121,980 / M2 CLZ6 42,203 / M3 CLF7 14,136 / M4 CLG7 4,199 / M5 CLH7 5,004 / M6 CLJ7 1,619 (curve closes 92.87 → 83.16, steep backwardation). [OBSERVED — CL_behavior_stats.json]

**Liquidity migration front→next.** At the data-lane declared roll date (last session before day-1 of the last-trade month, median 21 calendar days before last trade across 14 realized rolls) the OLD contract still carried 3–7× the next contract's volume (new/old volume ratio 0.15–0.34 at every realized roll). A genuine volume-leadership switch was directly observable only where data extends past the roll boundary (gap-filled CLV6): leadership passed to CLX6 on 2026-09-18, **4 calendar days** before CLV6's last trade (2026-09-22). Measurement limitation: per-contract 6Y files were fetched with windows ending at the declared roll boundary, so within-final-month volume is observable for one contract only (n=1). [OBSERVED — CL_behavior_stats.json `roll_table`]

**PIT contract selection + roll rule (baseline = data-lane declared rule).** Hold until the last session BEFORE day 1 of the last-trade month, roll to the next listed contract at that close; the listed-months calendar is published years ahead, so the decision uses only information available at the time. [Declared rule — data lane FINAL_REPORT 2026-10-02; the rule's decision dates are PIT-legal. Alternative rules: (a) volume-switch roll (roll when next-contract volume exceeds old for k consecutive sessions — more aggressive, holds the liquid contract longer; needs volume past the boundary which the snapshot lacks for 13/14 rolls); (b) OI-based roll: NOT_RUN — raw data carries no open interest. Back-adjustment: NOT_RUN — no adjusted series was constructed in prep; roll close-gaps are reported raw (see §3).]

---

## 2. Causal driver map

Sources → mechanism → sign/horizon → regime dependency → confounders → falsification → PIT data. Primary-source URLs + access date 2026-10-02. "Effect" entries are unmeasured in prep (event studies prohibited) unless marked OBSERVED.

| # | Driver | Source → mechanism | Predicted sign / horizon | Regime dependency | Confounders | Falsification test | PIT data source (primary) | Class |
|---|---|---|---|---|---|---|---|---|
| 1 | EIA weekly crude + Cushing inventory surprise | EIA WPSR Wed 10:30 ET → supply-availability update → repricing of scarcity | Draw (bullish surprise) → up; build → down; minutes–days | Strongest in low-inventory/backwardated regimes | Consensus already prices survey expectations; product/Cushing detail vs headline conflict; simultaneous macro releases | Conditioned event returns ≈ 0 after costs; sign reversal when Cushing vs total conflict | https://www.eia.gov/petroleum/supply/weekly/schedule.php (release calendar; vintage + errata pages) | schedule FACT; effect POSTULATED |
| 2 | API weekly estimates (Tuesday) | Pre-WPSR information leak of inventory direction | Same sign as #1, smaller; overnight-to-next-day | Same as #1 | API vs EIA methodology gap; selective reporting | API-implied surprise does not predict EIA surprise or price | api.org (not fetched this session) | FACT(Tuesday release; CME overview page snippet) timing detail NOT_RUN |
| 3 | OPEC+ production policy (quotas, meetings, MOMR) | Quota changes → expected supply path → level + curve slope shifts | Output cut → up; hike → down; days–weeks | Dominant when spare capacity low; weak when quota compliance poor | Demand news released same window; quota compliance uncertainty; unpublished meeting outcomes | Policy-change dummies have no conditional drift after costs | opec.org MOMR schedule (page 403 this session; dates corroborated via official-page render and Dec-2025 MOMR PDF) https://www.opec.org/monthly-oil-market-report.html | schedule FACT(snippet); effects POSTULATED |
| 4 | USD / macro rates | Dollar-denominated crude; rate path affects demand + storage carry | Stronger USD → down (demand-channel), horizon days | Sign/size varies with US-vs-global growth differential and tightness | Oil-specific supply shocks move both; endogeneity USD↔oil | Conditional beta ≈ 0 or unstable sign across regimes | FX PIT series (not in this dataset) | mechanism POSTULATED; measurement NOT_RUN |
| 5 | Term structure / convenience yield (front calendar spread) | Inventory scarcity raises convenience yield → backwardation deepens → spot-anchored drift up; reverse when loose | Δ(M2−M1) more negative → front drift up; weeks | Only in physically-tight regimes; flat in oversupply (curve data OBSERVED 100% backwardation days — see §3) | Financial flows (roll of index funds), storage/pipe constraints at Cushing | Spread-change sorts show no forward drift after roll/execution costs; sign flips in contango | Per-contract closes (in hand, this snapshot) + EIA Cushing stocks | structure OBSERVED; predictive content POSTULATED |
| 6 | Positioning (CFTC CoT) | Crowded net length → convexity/vulnerability to negative shocks; MML positioning | Extreme length → asymmetric downside; days–weeks | Matters when speculative share high | CoT aggregates reportables only, Tuesday as-of vs Friday release; no intra-week | Extremes do not condition return distribution | https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm (as-of Tuesday, released Fri 15:30 ET, no revisions) | schedule FACT; effect POSTULATED |
| 7 | Geopolitical supply disruptions | Flow-loss risk repricing; risk premium in front of curve | Disruption → up, front-led, steepening backwardation; hours–weeks | Reverses when flows restored / SPR released | Headline vs realized-loss gap; SPR policy offset | Event drift absent when disruption does not reduce measured flows | Official announcements (not systematically owned) | mechanism POSTULATED; consistency OBSERVED (spring-2026 vol/backwardation spike, §3 — attribution unproven) |
| 8 | Refinery utilization / product cracks (RB, HO) | Refinery demand for crude + product scarcity set crack-driven crude pull | High runs/cracks → supportive; weekly horizon | Seasonal maintenance windows | Product-specific shocks; export arbitrage | Crack-conditioned crude drift ≈ 0 | NYMEX RB/HO (NOT in this snapshot) | NOT_RUN (data absent) |
| 9 | Cushing infrastructure constraints | Pipeline tarps/line fills change effective storage at the delivery hub → front-spread dislocations independent of total US stocks | Constraint → front cheapens vs deferred; days | Only when Cushing near operational limits | EIA Cushing stocks proxy the state imperfectly | Cushing-spread moves unexplained by stocks are transient | EIA Cushing weekly stocks (in WPSR) | mechanism POSTULATED |
| 10 | Roll-window microstructure | Index/CTA roll demand compresses/expands the front spread around roll dates | Spread pressure around 4–6 business days pre-LTD; hours–days | Direction depends on aggregate length positioning | Overlaps drivers 5/6 | Roll-window spread seasonality vanishes net of costs | Volume/depth data past roll boundary (absent for 13/14 realized rolls) | n=1 OBSERVED (leadership switch date); effect NOT_RUN |

---

## 3. Behavior (measured where legal)

All computations: `analysis/CL_behavior_stats.py` → `analysis/CL_behavior_stats.json`; raw daily per-contract TRADES (legal snapshot, 2026-10-02). Rule-front "true market-front" window = **2025-08-21 → 2026-10-01, 280 real-volume days** (start clamped: CLU5, the prior front, is not in the dataset). Simple returns only (no log-return assumption; dataset itself has no negative prices — min close/low 40.72 on CLV5 2020-03-20, 0 negative bars of 43k+ — but CL printed negative nearby prices in Apr-2020 outside this snapshot, so the convention is mandatory). **Return convention (audit M1 fix, 2026-10-02): all §3 return statistics are WITHIN-CONTRACT — the return on the first session after each roll (consecutive closes from different contracts) is a synthetic stitching jump and is EXCLUDED (14 excluded; n=265 returns), the same convention as the other nine dossiers; the excluded rows are listed in the JSON.** [OBSERVED]

> **ERRATUM 2026-10-02 (audit M1).** The original revision computed §3 return statistics on stitched chain returns that INCLUDED the 14 synthetic roll-boundary returns; the convention was undisclosed and inconsistent with the other nine dossiers. The roll-day stitching is material: the first session after each roll mixes the overnight move with the calendar gap — e.g. 2026-04-01 (CLK6→CLM6, gap −$8.22) stitched **−10.36%**; 2026-05-01 (CLM6→CLN6, gap −$5.93) **−8.12%**; 2026-08-03 (CLU6→CLV6, gap −$3.18) **−8.00%**; the auditor's variant (return indexed on the roll session itself, gap-adjusted comparison against the new contract's own same-day move) shows the same contamination including a sign flip on the 2026-07-31 roll (stitched −2.5% vs own +0.85%). Superseded (contaminated) values → corrected values:
> - daily sd 3.17% → **3.05%** (sample sd; auditor's population-sd variant 3.047%)
> - rolling 20d ann vol: median 39.8% → **38.2%**; p90 84.5% → **78.0%**; max 99.7% (2026-04-06) → **93.6% (2026-04-09)**; last 41.4% (2026-10-01) → **42.4% (2026-09-30; the 2026-10-01 return is a roll-boundary return, excluded)**
> - |ret| autocorr lag-1 0.229 → **0.194**; lag-5 0.071 → **0.019**
> - skew −0.37 → **−0.22**; excess kurtosis 2.17 → **2.30**
> - |ret|>3% share 24.7% → **24.2%**; >5% 10.4% → **9.1%**
> - weekday |ret|: Mon 2.64/ Tue 2.23 / Wed 2.36 / Thu 2.18 / Fri 2.01% → **Mon 2.52 / Tue 2.24 / Wed 2.25 / Thu 2.21 / Fri 1.92%** (n 47–56)
> Unaffected: "max |daily move| 11.7%" (2026-04-08, −11.70%) is a genuine crash day, not a roll artifact (auditor-verified); curve/roll-gap bullets compare same-day closes across contracts and involve no stitched returns. Superseded values are preserved in `CL_behavior_stats.json` → `erratum_2026_10_02_M1`. [DISCLOSED CORRECTION]

- **Volatility.** Daily sd 3.05% (sample sd, n=265 within-contract returns; ≈48% annualized over the window; auditor's population-sd variant 3.047%); rolling 20d annualized vol: median 38.2%, p90 78.0%, min 20.2% (2025-08..09), max 93.6% (2026-04-09), last 42.4% (2026-09-30 — the 2026-10-01 return is a roll-boundary return, excluded). Vol clustering: lag-1 autocorr of |ret| 0.194, lag-5 0.019. Fat tails: skew −0.22, excess kurtosis 2.30; |ret|>3% on 24.2% of days, >5% on 9.1%. (Superseded stitched values: see erratum above.) [OBSERVED — script + window above]
- **Trend.** Lag-1 autocorr of returns 0.000 and of sign −0.056 → no measurable daily momentum; the mild negative sign persistence is descriptive only (short window; not a claim about other regimes). (Superseded: the original text quoted +0.007/−0.003, which matched neither the old stitched JSON values −0.001/−0.013 nor the corrected within-contract values.) [OBSERVED, scope-limited]
- **Curve.** M2−M1 (front calendar spread, both real-volume closes) negative on **280/280 days** (100% backwardation share), median −$0.58/bbl, deepest −$8.65 (spring 2026); M3−M2 median −$0.49. Realized roll close-gaps (old→new at declared roll dates, 14/14 backwardated): median −$0.51, largest −$8.22 (2026-03-31 CLK6→CLM6), then −$5.93 (2026-04-30). Long-history (pre-2025-08) curve stats NOT_RUN — the dataset lacks the market front months before 2025-08 (deferred-contract quotes only). [OBSERVED]
- **Roll timing.** Declared calendar rolls execute median 21 calendar days before last trade with the old contract still 3–7× more liquid than the next (§1); observed leadership switch (1 case) 4 calendar days before last trade. [OBSERVED]
- **Intraday session (RTH only).** H1 pooled across contracts' final ~30-day files, 2025-07-21→2026-10-01 (291 days; roll/expiry weeks overrepresented): volume share by ET hour — 09:xx 10.0%, 10:xx 18.3%, 11:xx 18.5%, 12:xx 13.9%, 13:xx 12.4%, 14:xx 17.4%, 15:xx 6.2%, 16:xx 3.4%; mean bar range peaks 10:00–12:00 (0.88%/0.82% per H1 bar). Overnight/Asia/Europe session behavior NOT_RUN — intraday files are useRTH=True (no 18:00–09:30 bars); M1 depth ~2 days, H1 ~14 months via tiling. [OBSERVED + NOT_RUN]
- **Weekday |return| (description only — NOT an event study):** Mon 2.52% (n=47) > Wed 2.25% (EIA day) ≈ Tue 2.24% > Thu 2.21% > Fri 1.92% (n=53–56). [OBSERVED, descriptive; corrected within-contract values — see erratum]
- **Seasonality.** NOT_RUN — true-front window covers ~14 months; each calendar month appears at most twice; deferred pre-2025-08 quotes are not the market front and were excluded.
- **Event behavior (EIA/API/OPEC/CoT reactions).** NOT_RUN — return-based event studies prohibited in this prep task.
- **Costs (descriptive, from legal data).** Front spread (close-bid vs close-ask, non-synchronous, CLX6 1Y, 251 days, 0 crossed): median 3.0 ticks / p90 4.0 ticks over the last 2 months (matches data-lane S6 front 20d median 3.0 ticks = $30); full-1Y median 5.0 / p90 18.0 / max 1455 ticks — inflated by CLX6's deferred (stale-quote) months. Commission: IBKR $0.85/side + exchange + regulatory (exchange fee for CL: NOT_FETCHED — JS table did not render; CME fee page blocked). Margins (public brokers, 2026-10-02/2026-08-31 fetches): maintenance $8,021–$9,448, initial $8,823+ (day-margin $1,000 NinjaTrader). Slippage: NOT_RUN_NO_DECLARED_VALUE. Roll close-gap (basis level, not an execution cost): see curve bullet. [OBSERVED/FACT(doc) per item]
- **Continuous adjustment.** NOT_RUN — no back-adjusted series built in prep (construction-only note: back-adjustment would subtract the 14 observed gaps, median −$0.51, max −$8.22; any signal test must verify no stitching alpha).

---

## 4. Event calendar

Exchange tz: US/Eastern (NYMEX/CME Globex energy sessions expressed in ET; DST handled — S1/S9). All schedules accessed 2026-10-02.

| Event | Schedule (actual) | Effective vs available vs retrieved | Vintage/revision/consensus PIT notes | Class |
|---|---|---|---|---|
| EIA Weekly Petroleum Status Report (crude, Cushing, gasoline, distillate, refinery runs) | Wed after 10:30 ET (main tables; other files after 13:00 ET); data for week ending prior Friday; holiday weeks shift (typically Thu 12:00 ET; NY week Thu 11:00 ET; Christmas week Mon 17:00 ET) | Effective: as-of Friday close; available: Wed 10:30 ET; retrievable: at release | Weekly data are preliminary; some tables marked preliminary (crude-imports table); errata page exists; consensus NOT official — vendor surveys must carry own timestamps | FACT — https://www.eia.gov/petroleum/supply/weekly/schedule.php + /petroleum/supply/weekly/ |
| API Weekly Statistical Bulletin | Tuesday (afternoon; ~16:30 ET widely cited) | Available Tue pm; precedes EIA by ~24h | api.org not fetched this session (time NOT_RUN); CME overview page confirms "Released on Tuesdays" | FACT(day)/NOT_RUN(time) — https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.html (partial render) |
| CFTC Commitments of Traders (CoT, incl. crude oil) | Friday 15:30 ET; positions as of close of the preceding Tuesday; holidays shift release | Release ≠ position date (3-day processing); no historical revisions ("historical data is not updated once published") | Only 13 months of reports kept on site; historical archives separate; no consensus concept | FACT — https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm |
| OPEC Monthly Oil Market Report (MOMR) | Monthly, ~10th–16th; 2026 dates published by Secretariat (e.g. 2026-01-14, 02-11, 03-11, 04-13, 05-13) | Report contains OPEC-only production (secondary-source estimates) + demand outlook | Monthly vintages; production figures restated across months | FACT(snippet; opec.org direct HTTP 403) — https://www.opec.org/monthly-oil-market-report.html |
| OPEC+ ministerial/production-policy meetings | Irregular, announced ad hoc | Decisions published as press releases after meetings | Compliance visible only in later MOMR vintages | NOT_RUN (page 403; no schedule compiled) |
| CL roll / last trade | Monthly cycle; LTD = 3 business days before the 25th of the month prior to delivery; declared roll last session before LTD-month day-1 | Exchange calendar published years ahead (PIT-safe) | — | FACT(rule)/OBSERVED(29/29 lastTradeDate fields consistent, §1) |
| US federal holidays / exchange holiday calendar | Not compiled this session (CME page transport-blocked) | — | — | NOT_RUN |

Weather does not drive CL directly (NG-concept) — hurricane Gulf-of-Mexico supply disruptions would enter via realized outage risk; forecast-vintage handling would be required if ever used. [POSTULATED; no measurement]

---

## 5. Hypotheses (ranked by testability × causal plausibility — NOT by PnL)

No hypothesis has been run (prep task). Each follows the master template; common execution frame below. corpus-1200 reuse: NOT_RUN — corpus not consulted in this lane; any FX→futures transfer of prior ideas must be re-registered with basis/roll/cost differences, never treated as already-valid.

**Shared frame.** Universe/roll: CL chain, data-lane declared roll (§1) with volume-switch roll as the required alternative-roll test; sizing: PARAM-GAP (any vol-target parameter is parameter selection — not done in prep); cost model: IBKR $0.85/side + exchange fee (NOT_FETCHED — stress at 1.5×/2× per framework §9 once set) + half-spread 1.5 ticks ($15) per side from the 3-tick front median (non-synchronous caveat) + roll execution as a calendar-spread cost (NOT_RUN, no synchronous spread book); invalidation master-list = framework §10/§16 (edge gone at 2× costs, one-regime dependence, roll-method dependence, same-bar execution requirement, revised-data dependence).

**H1 — Term-structure tightening momentum (rank 1; most testable with data already in hand).**
When the 20-day change in the front calendar spread Δ(M2−M1) is below its own past rolling median (strictly trailing window), the front contract drifts up over the next 1–4 weeks, because deepening backwardation = rising convenience yield = tightening physical balance that spot-following capital chases. Strongest in low-Cushing-inventory regimes; weakest/reversed in contango. Entry: spread-change state computed at close; exit: horizon 5–20 sessions or state flip; direction: long/short front outright; universe M1 with declared roll. Falsification: conditioned forward returns ≤ costs; sign flips with curve regime; roll-rule alternative changes the conclusion (construction alpha). Data needed: per-contract closes (HAVE, incl. settlement-derived deep history — must be flagged); EIA Cushing stocks for regime split (public). Weakness: 100%-backwardation window (2025-08→2026-10) means no observed contango regime in true-volume data → regime breadth NOT_RUN until deeper volume history acquired. [POSTULATED; enabling OBSERVED structure §3]

**H2 — EIA crude/Cushing inventory surprise reaction (rank 2).**
When the WPSR crude/Cushing build-draw deviates from consensus at Wed 10:30 ET, the front moves in the surprise direction within minutes and partially reverts by next session, because inventories update physical-availability expectations. Strongest when Cushing (the deliverable hub) contradicts the national headline. Entry at first bar after 10:30 ET; exit same session; direction: sign of surprise. Falsification: reaction absorbed by spread before outright; entering 5 minutes later destroys it. Data gap: consensus history + release-time intraday (PARAM-GAP — surprise cannot be defined without consensus; intraday exists only ~10 months RTH, which does cover 10:30 ET). PIT: EIA release timestamps; survey vintages must be timestamped. [POSTULATED; schedule FACT §4]

**H3 — Post-EIA reversal on headline-vs-detail conflict (rank 3).**
When headline crude draw conflicts with products/Cushing/refinery detail, the first move reverts, because algos trade the headline and fundamentals reprice the detail. Needs RB/HO + Cushing detail — none in this snapshot (data gap; PARAM-GAP for the conflict definition without product data). [POSTULATED]

**H4 — USD-shock sensitivity conditional on physical tightness (rank 4).**
CL reaction to USD moves scales with curve backwardation (tight physical balance couples oil to dollar-demand; loose balance decouples). Needs PIT USD series (not owned). Falsification: conditional beta stable across regimes. [POSTULATED; measurement NOT_RUN]

**H5 — Roll-window liquidity timing (rank 5; microstructure, cheapest to falsify once volume depth is acquired).**
Because liquidity stays with the old contract until ~4–6 days before last trade while the declared calendar roll exits ~21 days early, a roll-rule switch changes execution quality (§1 OBSERVED, n=1). Predicted effect: volume-switch rolls reduce effective spread paid vs calendar rolls in stress weeks. Falsification: execution-cost difference between rules ≤ noise once measured with synchronous quotes. Data gap: per-contract volume past the roll boundary + synchronous BBO. [OBSERVED motivation; predictive claim NOT_RUN]

---

## 6. Missing data table

Top-3 causal drivers prioritized (term structure H1 — largely in hand; inventory surprise H2; positioning H6-driver).

| Need | Have | Source | Period | Schema | PIT properties | License / cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Deep per-contract daily volume + OHLCV (true volume, 2019→2025) + open interest | 2025-08→2026-10 true volume only (280 front days); OI none | Databento / CME DataMine (CME-licensed vendors) | 2015→2026 | daily OHLCV+OI per conId | exchange calendar public; no revision issue | paid (owner decision) | purchase gate (owner) | quote vendor scope incl. OI; prerequisite for H1 regime breadth + roll studies |
| EIA WPSR history + consensus/survey vintages | Release schedule only | EIA (public) + consensus vendor | 2015→2026 | weekly stocks (crude, Cushing, products, runs) + release timestamps | official vintages + errata; surveys need own timestamps | EIA free; consensus paid | consensus vendor + purchase gate | register EIA fields needed; decide consensus source |
| CFTC CoT history (crude) | Schedule only | CFTC public (archives) | 2006→2026 | Fri report, Tue as-of positions | as-of Tue ≠ release Fri; no revisions; 13-month site window | free | none (retrieval task) | pull historical archive + build as-of→release lag table |
| Intraday M1 multi-year (event studies) | ~10 months RTH H1/M1 only (useRTH) | same vendors as row 1 | 2015→2026 | M1 trades per conId | none (exchange data) | paid | purchase gate | include in row-1 quote |
| RB/HO product futures (H3, cross-asset) | none in snapshot | NYMEX via same vendor | 2015→2026 | daily/M1 | none | paid | purchase gate | bundle with row 1 |
| PIT USD / DXY with vintages | none | FRED ALFRED / vendor | 2015→2026 | daily index + release times | vintage-aware required | free/metered | retrieval task | add to next data cycle |
| OPEC+ decision record | MOMR dates only | opec.org (403 this session) + press archive | 2015→2026 | decision date, quota table | post-hoc compliance restated in later MOMRs | free | transport-blocked | manual compile with access-date stamps |
| Synchronous BBO / depth (spread + roll cost measurement) | daily non-synchronous BID/ASK 1Y (median 3 ticks last-2m) | vendor (bbo-1m) | recent years | bid/ask per minute | none | paid | purchase gate | scope for execution-quality module |
| CL exchange fee + slippage declared values | IBKR $0.85/side only; exchange fee NOT_FETCHED | broker fee schedule / exchange | current | fee table | n/a | free | CME pages transport-blocked; IBKR table JS-rendered | retry via rendered page or record owner broker's actual schedule |

---

## 7. Framework coverage

Master framework §1 (10 questions):

| Q | Answer | Class |
|---|---|---|
| 1 Underlying exposure | 1,000 bbl WTI, physical delivery Cushing; USD/bbl | FACT (§1) |
| 2 Natural hedgers/speculators/MMs/arbitrageurs | producers, refiners, merchants, consumers; CTAs/funds; MMs; cash-curve-crack arbitrage | POSTULATED (taxonomy; CoT split exists: FACT §4) |
| 3 Exchange + hours | NYMEX/Globex Sun 18:00–Fri 17:00 ET, 60-min break | FACT (§1) |
| 4 Size/tick/currency/margin/settlement | 1,000 bbl; $0.01=$10; USD; maintenance $8.0–9.4k (2 public brokers); physical delivery | FACT/FACT/FACT/OBSERVED(doc)/FACT (§1, §3) |
| 5 Listed months + liquid expiries | all 12, ~10y+2m listed; liquidity M1–M3 (121,980/42,203/14,136 lots on 2026-10-01) | FACT / OBSERVED (§1) |
| 6 Liquidity migration | old 3–7× next at declared roll (14/14); observed switch 4 cal days before LTD (n=1) | OBSERVED (§1) |
| 7 Dominant price behavior | carry/convenience-yield + inventory expectations + geopolitics; this window: 100% backwardation, high vol | OBSERVED structure + POSTULATED attribution (§3) |
| 8 Which session matters | RTH: volume/range peak 10:00–12:00 ET, elevated 14:00 ET hour (settlement window); overnight NOT_RUN (no data) | OBSERVED / NOT_RUN (§3) |
| 9 Tradeable contract per timestamp | M1 by volume everywhere observed; declared rule holds M1 to ~21 days pre-LTD; PIT volume-based rule preferred but data-limited | OBSERVED (§1) |
| 10 Vendor symbols → expiries; reproducible continuous build | localSymbol = CL{monthcode}{yeardigit} → delivery month (code month); lastTradeDate raw field; roll table + close-gap computed in this lane; back-adjustment NOT_RUN | OBSERVED (§1, §3) |

CL framework checklist (its own questions): foundation Q1–Q5 answered §1; Q6 (min data for PIT series) = per-contract OHLCV + OI + exchange calendar (gap table §6); market-structure Qs (volume by session/expiry, roll shift speed, spread behavior, opening/settlement effects, contract-selection rule stability, back-adjustment sensitivity) = §3 partially (session RTH only; spread non-synchronous; roll n=1 past boundary; selection-rule comparison + back-adjustment NOT_RUN); driver table = §2; regime map = NOT_RUN (single regime observed — persistent backwardation + high vol 2025-08→2026-10; no regime tagging beyond vol level performed); event-study framework = NOT_RUN (prohibited in prep); term-structure/roll research = partially done §3 (front + M3 spread, roll gaps; farther expiries + roll-rule comparison NOT_RUN); cross-asset = NOT_RUN (no RB/HO/BRN/6C/DXY data in snapshot); candidate signals = §5 hypotheses (owner's §15 list mapped: inventory surprise → H2; front-spread tightening → H1; post-EIA reversal → H3; term-structure momentum → H1; USD regime dependence → H4); data checklist (Databento ohlcv-1m/definition/statistics) = §6; failure modes (§16: negative-price/expiry mechanics — convention handled, no negatives in data [OBSERVED]; headline jumps; delivery stress excluded by roll rule; roll artifacts flagged; inventory-expectation leakage) = carried into H1–H5 invalidation rules.

**Bottom line.** CL in this snapshot is a physically-settled, M1/M2-concentrated, steeply backwardated, high-volatility market (front real-volume depth only 13.7 months). Mechanically well-understood and cheap to describe; every causal claim beyond schedule/mechanics remains POSTULATED; all event/return-conditioned measurement is NOT_RUN pending data depth and the end of the prep prohibition.

---

### CoT revision-policy verification note (added 2026-10-02, round co-owner-review-fix-1, lane HANDOFF-RESEARCH)

The CoT "not revised" wording in §2 driver-map row 6 and §6 missing-data CoT row (this dossier) was re-verified against primary CFTC
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
