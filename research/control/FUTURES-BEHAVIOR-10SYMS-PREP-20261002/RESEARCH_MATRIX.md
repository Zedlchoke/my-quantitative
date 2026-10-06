# RESEARCH_MATRIX — FUTURES-BEHAVIOR-10SYMS-PREP-20261002

- Written: 2026-10-02, round **co-owner-review-fix-1**, lane **HANDOFF-RESEARCH**.
- Purpose: map EVERY output/test/question demanded by the owner framework —
  `owner_framework/00_MASTER_FRAMEWORK.md` (sha256
  `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`) §1–§10,
  including §6's 15 required tests — and each per-symbol framework file →
  where it is answered (dossier § / artifact) + evidence class, or NOT_RUN.
- Evidence classes (workspace taxonomy): **FACT** (primary source + URL +
  access date) / **OBSERVED** (computed from legal raw; script + window) /
  **POSTULATED** (mechanism reasoning, unmeasured) / **NOT_RUN** (default;
  never inferred PASS).
- Scope guard: everything below is PREP. No scored runs, no PnL/event
  studies/rule sweeps, no registrations/purchases. The framework is an owner
  research document; its claims are HYPOTHESES, never facts or PASS.

## 0. Answer-key (dossier section map)

Every dossier has the same 7 sections: §1 Mechanics, §2 Causal driver map,
§3 Behavior (measured), §4 Event calendar, §5 Hypotheses (ranked,
template-complete), §6 Missing-data table, §7 Framework coverage (its own
§-by-§ answer to the master framework + its symbol checklist). Engine/data
artifacts: `code/futbt/*` (12 modules, 147 offline tests at eae8c3d2),
`BACKTEST_LAUNCH_DRAFT.md`, `data/COVERAGE_MANIFEST.json`,
`DATA_ACQUISITION_SPEC.md`, `audit/A7_AUDIT.md` + `audit/FIX_LOG.md`.

## 1. Master framework §1 — Foundation: the 10 questions

| # | Question | Answered in | Evidence class | Key exceptions / NOT_RUN residues |
|---|----------|-------------|----------------|-----------------------------------|
| 1 | Underlying economic exposure | all dossiers §1 + §7.1 | OBSERVED (S1 identity) + POSTULATED framing | none (each contract's unit/quote verified: 6J USD-per-JPY, SI 5000oz class SI, etc.) |
| 2 | Natural hedgers/speculators/MMs/arbitrageurs | all §1 + §7.2 | POSTULATED | participant composition NOT_RUN everywhere (no CoT/OI pull) |
| 3 | Exchange, listing venue, trading hours | all §1 | FACT (S1 tradingHours) + OBSERVED | CME official text transport-blocked (HTTP 403) for 9/10 — broker-mirror secondary |
| 4 | Size/tick/tick-value/currency/margin/settlement | all §1 | OBSERVED (S1) + FACT-secondary | tick CONFLICT unadjudicated: 6A (0.00005 vs 0.0001), 6B (0.0001 vs 0.0002), 6E ($6.25 vs $12.50 — machine value governs); CME SPAN NOT_RUN |
| 5 | Listed months; which expiries are normally liquid | all §1 | OBSERVED | FX+SI serials are dead books (6EV6 214/day vs 6EZ6 71,234; 6JX6 26 vs 6JZ6 118,886); SI cycle = H/K/N/U/Z |
| 6 | When liquidity migrates front→next | all §1 (migration subsections) | OBSERVED with disclosed boundary | exact old-vs-new crossover NOT_RUN everywhere (expired files cut at fetch boundary); migration shapes differ: GC 1–2 sessions EARLY; ES/NQ/6E/6B/6A thin-book windows 4–11 sessions POST-roll; NG seasonal/heterogeneous; 6J no pre-roll crossover |
| 7 | What dominates price behavior (arb/carry/macro/seasonality/order-flow) | all §1/§2 + §7.7 | POSTULATED attribution; OBSERVED components (roll/carry gaps measured) | dominance attribution NOT_RUN (no causal identification data) |
| 8 | Which session matters most | all §1/§3 + §7.8 | OBSERVED (US-RTH profile) / NOT_RUN (Asia/London/overnight) | ALL raw bars useRTH=true → Globex/Asia/London NOT_RUN for every symbol; only RTH-open gap proxies exist (6E gap = 79% of RTH-day std; SI 86%; ES 63%) |
| 9 | "Tradeable" contract per timestamp (PIT) | all §1 (roll-rule + executability) | OBSERVED defects + design | declared rule defective 9/10 (INTEGRATION_SUMMARY §1.1); OI unavailable → OI-roll NOT_RUN; literal next-listed routes into dead serials (FX+SI) |
| 10 | Vendor symbols ↔ expiries; reproducible continuous | all §1 + §7.10 | OBSERVED | conId/localSymbol in S1+filenames; 4–7 roll boundaries measured per symbol; back-adjustment NOT_RUN (description-only mandate; engine implements causal-additive) |

## 2. Master §2 — Causal map (8 required fields per driver)

All 10 dossiers §2 present the full required field set (driver, why it
matters, expected sign, lag/horizon, regime dependency, PIT source,
confounders, falsification test) — structure **OBSERVED-complete**;
mechanisms are **POSTULATED**; every driver-level *measurement* is NOT_RUN
(no external PIT series were pulled: no rates, no CoT values, no consensus,
no OI, no DXY/VIX). Driver counts per symbol: NQ/ES/CL/NG/GC/SI/6E/6J/6B/6A
≈ 7–11 rows each, mapped onto §3's buckets.

## 3. Master §3 — Driver taxonomy (7 buckets)

| Bucket | Covered by | Status |
|--------|-----------|--------|
| Macro | all 10 §2 | calendars FACT; series NOT in repo → effects NOT_RUN |
| Fundamental/physical | CL/NG/GC/SI full; FX via terms-of-trade analogue (6A iron ore, 6E energy) | EIA schedules FACT; NOAA NOMADS archive FACT; physical data NOT_RUN |
| Cross-asset | all §2 + partial §3 measurements (SI-GC corr 0.828; 6B-6E 0.837; 6B-ES 0.308; GC/SI ratio) | few pairs OBSERVED descriptively; matrix NOT_RUN (lane scope) |
| Positioning | all §2 | release rule FACT (see §CoT below); CoT values NOT fetched → NOT_RUN |
| Term structure | all §1/§3 | OBSERVED (roll gaps, curve stats, CL 280/280 backwardation, NG seasonal flip, 6J −2.6%/yr) |
| Microstructure | all §1/§3 | OBSERVED (spread proxies reconcile S6; volume profiles; serial/quarterly cliffs) |
| Event-driven | all §4 | calendars FACT (CFTC/BLS/Fed/ECB/BoE/BoJ/RBA/ABS/EIA/NOAA/LBMA verified with URLs + 2026-10-02); responses NOT_RUN |

## 4. Master §4 — Regime framework (10 tags) — **STRUCTURAL DISCLOSURE**

**NOT RUN for every symbol and every tag.** Regime tagging requires
multi-regime real-volume history; the corpus provides single-regime windows
only (see §Disclosure below). No dossier claims a regime-split result; the
engine has the split machinery (futbt walkforward/composition) but no data to
feed it. Deep pre-wall bars are settlement-derived marks of deferred curve
points — usable as reference, NOT as tradable-market regime evidence.

## 5. Master §5 — Hypothesis template (9 fields)

All 50 hypotheses (5 per symbol, dossiers §5) are written to the template
(entry/exit/holding/direction/universe-roll/sizing/costs/invalidation +
regime strongest/weakest + counter-hypothesis + failure conditions). Every
one carries PARAM-GAPs where thresholds cannot be set without lookahead-free
protocol or missing data. Per-hypothesis status table:

| ID | Theme (short) | Mechanism | Data status | Denominators / floors | PARAM-GAPs | Controls | Verdict |
|----|---------------|-----------|-------------|----------------------|------------|----------|---------|
| NQ-H1 | real-yield shock → NQ underperforms ES | macro/real-rates | rates NOT in repo; FRED/ALFRED free | ≥2y history or declared 16m acceptance | real-yield vintage series | ES same-window | NOT_RUN |
| NQ-H2 | CoT extremes → conditional vol/asymmetry | positioning/crowding | CoT release rule FACT, values free unfetched | ≥2–3y for extremes; 16m in-window feasible | extreme percentile def | non-event weeks | NOT_RUN (cheapest unblocked) |
| NQ-H3 | surprise × rate response | macro event | consensus archive MISSING | ≥40 events/class | consensus source | surprise-alone | NOT_RUN (BLOCKED) |
| NQ-H4 | overnight→RTH continuation | session/liquidity | Globex ABSENT (useRTH=true) | ≥2y full-session | — | — | NOT_RUN (BLOCKED; useRTH=false re-pull is $0) |
| NQ-H5 | roll-window carry/microstructure | micro/carry | gaps OBSERVED (+217–296 pts ×5) | ≥2y real volume + sync quotes | tradable roll cost | declared vs T-5 A/B | NOT_RUN |
| ES-H1 | roll-calendar alignment (T-5) | micro/liquidity | migration OBSERVED 4/4 cycles | ≥4 cycles (met descriptively) | rule choice | declared-rule A/B | design OBSERVED; test NOT_RUN |
| ES-H2 | roll-gap carry sign = rates−div | carry/CIP-like | gaps OBSERVED 5/5 (+52.5..67.75 pts) | ≥8 quarters | SOFR/div-yield series | none | NOT_RUN |
| ES-H3 | post-release persistence | event diffusion | consensus MISSING | ≥40 events/class | consensus | date-based v1 fallback | NOT_RUN (BLOCKED) |
| ES-H4 | ES/NQ RV on FOMC/CPI | relative macro | dates FACT; 14m depth | ≥2y | surprise split | NQ-vs-ES beta | NOT_RUN |
| ES-H5 | overnight-gap × vol regime | session/tail | gap OBSERVED (std 0.48%) | multi-regime (absent) | regime tag threshold | trailing-vol split | NOT_RUN (single regime) |
| CL-H1 | term-structure tightening momentum | storage/scarcity | curve OBSERVED 280/280 backwardation | ≥2y true-volume (vendor) | tightening metric | season dummies | NOT_RUN |
| CL-H2 | EIA/Cushing surprise reaction | inventories | WPSR schedule FACT; consensus MISSING | ≥100 events | surprise def (Bcf) | storage percentile | NOT_RUN (consensus GAP) |
| CL-H3 | headline-vs-detail reversal | report micro | consensus + detail data MISSING | ≥60 events | detail parse | headline-only | NOT_RUN (BLOCKED) |
| CL-H4 | USD-shock × physical tightness | macro×physical | DXY NOT in corpus | ≥2y | DXY vintage | tight/loose split | NOT_RUN |
| CL-H5 | roll-window liquidity timing | micro | old-side truncated (n=1 gap-fill) | both-side volume (vendor) | — | NGV-style crossover | NOT_RUN |
| NG-H1 | storage surprise × percentile/season | storage state | WNGSR FACT; consensus vendor; M1=2d | ≥100 events | X Bcf, exits, TP/SL | weather-revision control | POSTULATED; NOT_RUN |
| NG-H2 | forecast-revision drift when tight | weather vintages | NOMADS archive FACT; latency unmeasured | event count by winter | k degree-days | ample-storage split | NOT_RUN |
| NG-H3 | curve slope → near-term returns | term structure | m1−m2 OBSERVED (75.2% contango-shaped) | in-corpus feasible | s threshold, direction two-sided | month dummies | inputs OBSERVED; test NOT_RUN |
| NG-H4 | weather-premium reversion on normalization | risk premium | vintages + ≥3y true volume | ≥3y | retrace fraction | freeze-off episodes | NOT_RUN |
| NG-H5 | execution-timing descriptivum (NOT alpha) | micro | OBSERVED Thu 10:00 bucket 25.3% | — | — | — | OBSERVED (execution constraint) |
| GC-H1 | roll-timing microstructure | micro | crossover OBSERVED 5 cycles (1–2 sessions early) | ≥5 cycles (met) | rule variant | declared-rule A/B | design OBSERVED; forward NOT_RUN |
| GC-H2 | post-CPI real-rate sign vs headline | macro/real-rates | consensus MISSING; TIPS/FRED free | ≥40 events | real-yield surprise | headline surprise | NOT_RUN (BLOCKED) |
| GC-H3 | contango-curve stress signal | carry | curve OBSERVED 99.8–100% contango | ≥2y | stress threshold | flat-curve split | NOT_RUN |
| GC-H4 | GC/SI ratio regime behavior | relative value | ratio OBSERVED 44.0→92.8→68.7 | multi-regime (absent: ONE squeeze) | percentile bands | rolling corr | NOT_RUN (single event) |
| GC-H5 | real-yield level driver | macro | FRED free pull pending | ≥5y | — | CPI-days | NOT_RUN |
| SI-H1 | cycle-chain construction (H/K/N/U/Z) | micro | OBSERVED serials dead (max 944/d) | met (construction) | roll-day choice | quarterly A/B | design OBSERVED; forward NOT_RUN |
| SI-H2 | GC/SI ratio extremes → RV reversion | relative value | OBSERVED ratio + elasticity ~1.9 | multi-regime | extreme def | GC-beta control | NOT_RUN |
| SI-H3 | contango gap sign = carry | carry | gaps OBSERVED 6/6 (+0.565 $/oz median) | ≥8 quarters (6 met partially) | lease rates (paid) | rates-only split | NOT_RUN |
| SI-H4 | convex beta to GC | cross-asset | elasticity OBSERVED 1.9 median | multi-regime | convexity spec | linear beta | NOT_RUN |
| SI-H5 | overnight-gap tail clustering | session/tail | gaps OBSERVED (86% of daily std) | multi-regime | cluster threshold | trailing-vol | NOT_RUN |
| 6E-H1 | quarterly-only selection + expiry-week roll | micro | OBSERVED 4/4 migration in IMM week | ≥4 cycles (met) | T-choice | declared-rule A/B | design OBSERVED; forward NOT_RUN |
| 6E-H2 | CIP gap = USD−EUR short rates | carry/CIP | gaps OBSERVED 4/4 (+82..106 ticks = $512.50–662.50) | ≥8 quarters (4 met) | FRED SOFR + ECB €STR (free) | sign flip check | NOT_RUN (1 free pull away) |
| 6E-H3 | FOMC post-release persistence | event | M1=2d; consensus MISSING | ≥40 events/class | entry ≥5min post | macro-efficiency null | NOT_RUN (BLOCKED) |
| 6E-H4 | US-vs-EA surprise differential | macro relative | consensus both regions MISSING | ≥2y + events | differential spec | US-only model | NOT_RUN (BLOCKED) |
| 6E-H5 | FX-spot session ideas transferred | session | London morning ABSENT (RTH-only) | full-session M1 ≥2019 | corpus re-registration | — | NOT_RUN (structurally blocked; POSTULATED transfer only) |
| 6J-H1 | HMUZ quarterly-chain roll rule | micro | OBSERVED 99.73% volume on quarterly | met | — | calendar-next | design OBSERVED; engine default candidate |
| 6J-H2 | post-intervention reversion/drift | intervention | MOF amounts FACT (mof.go.jp); n≈2–3 events | ≥8 interventions (NOT met) | reversion horizon | non-op days | NOT_RUN (floor unmet) |
| 6J-H3 | roll-drag hurdle −2.6%/yr | carry | OBSERVED 100% contango sessions | descriptive (met) | — | — | OBSERVED (hurdle constant, not alpha) |
| 6J-H4 | BoJ MPM-day conditional | event | BoJ calendar FACT; decisions in invisible overnight | ≥20 meetings | MPM-day def | non-MPM | NOT_RUN |
| 6J-H5 | intervention-threshold regime break | regime | needs threshold model + deep history | multi-year | threshold spec | — | NOT_RUN |
| 6B-H1 | roll-timing/selection microstructure | micro | OBSERVED quarterly chain + thin windows | ≥4 cycles (met) | rule variant | literal serial (unexecutable) | design OBSERVED; forward NOT_RUN |
| 6B-H2 | BoE-vs-Fed repricing | policy relative | calendars FACT; rates/consensus MISSING | ≥2y events | differential spec | US-only | NOT_RUN |
| 6B-H3 | UK fiscal-credibility → GBP< EUR | political/fiscal | mini-budget dates on settlement marks; context POSTULATED unsourced | ≥5 stress events | event def | 6E same-window | NOT_RUN |
| 6B-H4 | London-session breakout by regime | session | London ABSENT (RTH-only) | full-session data | corpus re-registration | — | NOT_RUN (BLOCKED; POSTULATED transfer) |
| 6B-H5 | US-macro hidden-gap reaction | event/gap | gap machinery HAVE (median −1 pip, std 0.30%) | ≥60 events | event alignment | non-event gaps | NOT_RUN |
| 6A-H1 | RBA hidden-session gap reaction | policy event | RBA calendar+time FACT; 8 mtgs/yr | ≥16 meetings | hawk/dove classification (5-min spot MISSING) | non-event days | NOT_RUN ($0 daily version specifiable) |
| 6A-H2 | commodity/China confirmation of AUD trend | terms-of-trade | HG in corpus; iron ore licensed | ≥8 rolling quarters | trend thresholds | 6E/6B USD-beta control | NOT_RUN |
| 6A-H3 | quarterly-roll vs thin-serial trap | micro/execution | 95% OBSERVED (17-lot vs 35k books) | met | — | literal rule | mostly OBSERVED; forward residual NOT_RUN |
| 6A-H4 | AUD equity-beta regime dependence | cross-asset | ES/NQ in corpus | multi-regime | regime tag threshold | 6E control | NOT_RUN |
| 6A-H5 | rate-diff sign vs roll-gap sign | carry/CIP | gaps OBSERVED (4 rolls, −0.31..−0.75% ann 2026) | ≥8 rolls (4 met) | RBA/Fed rate series (free) | sign flip | NOT_RUN |

## 6. Master §6 — The 15 required tests

Framework §6 says "At minimum" — these are the pass bars of a FUTURE
registered cycle (BACKTEST_LAUNCH_DRAFT §7). Status at end of prep:

| # | Required test | Prep status | Evidence class |
|---|---------------|-------------|----------------|
| 1 | Full-sample result | NOT_RUN — zero backtests executed (prep prohibition); engine replay kernel built + 147 offline tests | code OFFLINE-PASS; real-data NOT_RUN |
| 2 | Walk-forward / rolling OOS | Harness built: purge ≥ true-horizon enforced, embargo audit, nested selection stamped at train_end, fold-suppression-forbidden (tests green on synthetic fixtures) | code OFFLINE-PASS; real-data NOT_RUN |
| 3 | Regime split | NOT_RUN — no regime tags computable (single-regime windows; no macro series) | NOT_RUN |
| 4 | Year-by-year stability | NOT_RUN — true-volume windows 13–21 months, no full-year real-volume boundary (see §Disclosure) | NOT_RUN |
| 5 | Long vs short contribution | Journal schema supports per-side contributions; no runs | code READY; NOT_RUN |
| 6 | Event vs non-event periods | NOT_RUN — event studies prohibited in prep; calendars verified for future use | calendars FACT; tests NOT_RUN |
| 7 | Front-month vs deferred contracts | Descriptive half-done: front chains OBSERVED; deferred = settlement-derived marks (deferred behavior = mark-behavior, dossiers disclose); execution comparison NOT_RUN | partial OBSERVED; test NOT_RUN |
| 8 | Parameter perturbation | NOT_RUN — rule set R not frozen (registration-gated); V-variant plumbing exists | NOT_RUN |
| 9 | Entry-delay sensitivity (0/1/2 sessions) | Engine V4 variant defined (draft §1); no runs | code READY; NOT_RUN |
| 10 | Cost/slippage stress ×1/1.5/2 | Cost model implemented with PUBLISHED/MEASURED/DECLARED classes, completeness refusal, ×1/1.5/2 (tests green); slippage NOT_RUN_NO_DECLARED_VALUE; exchange fees NOT_FETCHED 9/10 | code OFFLINE-PASS; components NOT_RUN |
| 11 | Alternative roll rule | Two rules implemented (declared calendar + strictly-PIT volume rule); distinguishability PROVEN on synthetic fixtures; real-data A/B NOT_RUN (roll windows truncated by fetch boundary) | code OFFLINE-PASS; real-data NOT_RUN |
| 12 | Alternative data source / cross-check | Partial: front spreads independently recomputed and reconciled with data-lane S6 (per dossier; SI/6A corrections); IBKR↔Databento overlap pilot SPECIFIED (NQ+CL, thresholds), not run; Phase-0 free probes specified, not run | partial OBSERVED; cross-vendor NOT_RUN |
| 13 | Look-ahead audit | Engine: PIT-enforced view, truncation + future-mutation hooks, past-only roll decisions, prefix determinism — tests PASS offline; real-data audit NOT_RUN (no runs to audit) | code OFFLINE-PASS; real-data NOT_RUN |
| 14 | Survivorship / symbol-mapping audit | OBSERVED: S1 identity audit + adapter smoke 1160/1160 files, 202 (symbol,conId) contracts, filename-marker classes; identity traps documented (SI class, 6J orientation, 6A/6B tick conflicts). Survivorship across pre-wall delisted contracts NOT_RUN (corpus starts at the wall) | partial OBSERVED |
| 15 | Capacity and turnover review | NOT_RUN — daily non-synchronous BID/ASK only; capacity explicitly NOT provable from this data (draft §7 caveat) | NOT_RUN |

**Hard-rule engine laws already enforced** (from draft §7): ambiguous-bar
bounds-only reporting; censored trades never netted; no
performance-reason fold suppression; marginal contributions only via
full-path leave-one-out; DECLARED weights (fitted = IN_SAMPLE_MASQUERADE).

## 7. Master §7 — PIT data rules (6 fields per external series)

Dossier §4 tables record, per event family: release time + source tz + UTC +
exchange-tz collision, vintage/revision property, effective-vs-available
time, source URL + access date. **Retrieval status: NOT_RUN for every
series** — nothing has been pulled into a PIT store this cycle (dossiers
state "retrieved: NO"). Revision-sensitive series flagged: NFP prior-two-month
revisions (ALFRED needed), ABS CPI seasonal revision, CPI seasonal factors,
ONS first prints, PBOC credit revisions; CoT per §CoT below.

## 8. Master §8 — Futures-specific data rules

- Raw individual contracts stored: YES — 1160 files, 202 contracts
  (OBSERVED, adapter smoke). Vendor continuous chains: correctly REFUSED
  (draft §5.4; CONTFUT dead-bar pathology measured earlier).
- Minimum fields: timestamp ✓, raw_symbol ✓, instrument_id (conId) ✓, expiry
  ✓ (S1, not raw metadata — caveat S9 C4), OHLCV ✓, volume ✓, open interest
  ✗ (absent from all raw — NOT_RUN everywhere), settlement separable ✓ (S9
  method; close-only bars flagged), BID/ASK ✓ (non-synchronous daily — cost
  evidence, not executable), tick/multiplier ✓ via S1 only.
- Roll tables (old/new, decision ts, reason, old/new volume+OI, raw gap,
  adjustment factor): 4–14 measured roll boundaries per symbol in dossiers
  §1/§3; OI column NOT_RUN; full implementation in futbt/roll.py with
  additive+ratio factors (ratio refused on non-positive prices).

## 9. Master §9 — Research output standard (14 items)

Dossier structure maps: 1 thesis→§1; 2 participant map→§1 (POSTULATED);
3 driver map→§2; 4 regime map→§4-disclosure (NOT_RUN); 5 event calendar→§4
(FACT); 6 term-structure logic→§1/§3 (OBSERVED); 7 cross-asset→§2/§3
(partial OBSERVED); 8 candidate signals→§5 (50 hypotheses, POSTULATED);
9 required datasets→§6; 10 backtest plan→§5 + BACKTEST_LAUNCH_DRAFT (DRAFT,
no GO); 11 execution/cost model→§3 costs + futbt/costs.py (components
NOT_FETCHED 9/10); 12 failure modes→§5 failure conditions; 13 open
questions→§5 + handoffs; 14 ranked next experiments→§5 rankings. Items with
no prep artifact: rejection log (NOT_RUN — no runs to reject), backtest
report (NOT_RUN).

## 10. Master §10 — Stop conditions (8)

All eight are evaluation-time gates for a future registered cycle; **none is
evaluable now** (zero runs). The engine pre-builds the measurable ones:
#1 cost stress (×1/1.5/2 law), #5 roll-method sensitivity (rule A/B), #7
entry-timing realism (delay variants, close-only never fills,
AMBIGUOUS_ORDER bounds). #2 one-year/event dominance is pre-answerable as a
WARNING: current windows ARE single-regime/single-event (§Disclosure) — any
future result must carry that prior.

## 11. Per-symbol framework files → answers

| Framework file (sha256) | Answered in | Symbol-specific residues (top NOT_RUNs) |
|---|---|---|
| NQ (9545fb08…) | NQ_DOSSIER §7 | consensus archive; Globex session; ≥2y depth; serial N/A (quarterly chain complete) |
| ES (92e9d510…) | ES_DOSSIER §7 | June Juneteenth expiry special-case (OBSERVED); consensus; overnight |
| CL (f3c32c9e…) | CL_DOSSIER §7 | consensus for EIA surprise; vendor pre-2025 depth; exchange fee |
| NG (285d010f…) | NG_DOSSIER §7 | weather vintages (NOMADS); WNGSR cutoff/revision policy; consensus |
| GC (be444f23…) | GC_DOSSIER §7 | 6 missing serials (time-critical, SERIAL_REFETCH_MANIFEST.md); consensus; official specs |
| SI (d0349504…) | SI_DOSSIER §7 | regime breadth (single squeeze); lease rates; price-limit schedule; HG copper absent |
| 6E (db5fbaff…) | 6E_DOSSIER §7 | FRED/€STR free pull (H2); full-session M1; consensus both regions |
| 6J (bc3ad5a3…) | 6J_DOSSIER §7 | 8 missing serials (2 likely past resolve wall); full-session (BoJ overnight); Japan CPI schedule |
| 6B (510032d4…) | 6B_DOSSIER §7 | ONS calendar + BoE time (fetch failures); tick adjudication; London session |
| 6A (6f1e1413…) | 6A_DOSSIER §7 | 6 missing serials (age out Jan–Mar 2027); iron-ore price; consensus; home-session data |

## §Disclosure — invariants NOT derivable from this corpus (mandatory read)

The following framework properties are **structurally NOT derivable** from
13–21 months of single-regime, RTH-only, partially settlement-derived data.
They are disclosure items, not conclusions:

1. **Regime stability of any edge** (§4, §6 tests 3/4): every real-volume
   window is ONE regime — NQ/ES persistent rally (~+27% level, 12–18% ann
   vol); SI one squeeze-crash (+217% then −31.4% single day); 6J a record
   MOF-intervention year; NG a high-vol regime 2–4× its 2020–24 level; GC a
   vol shift 14→31% ann; FX single policy-drift windows (EUR 1.20→1.13; AUD
   mild backwardation). "Stable across regimes" cannot be tested; "comes from
   one exceptional period" cannot be excluded — for SI it is near-certain.
2. **Year-by-year stability** (§6 test 4): no real-volume sample spans two
   full years; the only year boundary (2025/2026) is inside one regime.
3. **Causal attribution**: no consensus/surprise data, no OI, no vintaged
   macro series pulled, and all non-RTH sessions absent → every §2 mechanism
   stays POSTULATED; event-response identification is NOT_RUN everywhere.
4. **Overnight/Asia/London session properties** (§1 Q8, several §5 H's):
   useRTH=true clipping removes ~79–86% of FX daily variance context and all
   BoJ/ECB/RBA/AU/China event windows; only open-gap proxies exist.
5. **Pre-2025 "behavior"** is settlement-derived deferred-marks behavior —
   reference/curve evidence, never tradable-market behavior (fill prices).
6. **Capacity** (§6 test 15): daily non-synchronous BID/ASK cannot bound
   market impact; capacity/turnover review NOT_RUN until depth data exists.
7. **Absolute liquidity levels**: vendor volume-recording artifacts (GC V-month
   1–2 orders thin) make absolute volume unusable; relative migration only.

## §CoT — shared CoT revision-policy verification note (2026-10-02)

Re-verified against primary CFTC documentation by lane HANDOFF-RESEARCH:

1. Release rule **FACT stands**: "The COT Report is generally published each
   Friday at 3:30 pm Eastern Time (US)"; positions are "each Tuesday's open
   interest"; "Generally, the data in the COT reports is from Tuesday and
   released Friday."
   (https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm,
   accessed 2026-10-02).
2. No-revision property **FACT stands with scope = as-published weekly
   files**: CFTC FAQ verbatim — "No, historical data is not updated once
   published." (same URL, accessed 2026-10-02).
3. **Scope qualification — TFF supplement**: TFF historical compressed files
   are NOT vintage-stable: "the CFTC does not maintain a history of
   large-trader classifications, so, recent classifications had to be used to
   classify the historical positions of each reportable trader" (Form 40
   refreshed "every 2 years or more often").
   (https://www.cftc.gov/sites/default/files/idc/groups/public/@commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf,
   accessed 2026-10-02). Strict PIT use must pin release-dated weekly files,
   never the current compressed history.

Verdict: no class downgrade for the release rule or the as-published
no-revision claim; blanket "not revised" is scope-qualified wherever
"legacy + TFF" is cited. Per-dossier pointer notes added to 6A/6J/CL/GC/NG
dossiers (the claiming dossiers). ES/6E carry schedule-FACT rows only; NQ/SI
make no revision claim; 6B's CoT schedule row is NOT_RUN (fetch failures) —
all consistent with this note.

## §Errata registry (this round, lane HANDOFF-RESEARCH)

1. 6A_DOSSIER §3 Seasonality: bp band was 10× off and the statistic
   mislabeled — corrected to 55–87 bp/day of daily-return **σ** by month
   (erratum block in situ; superseded wording preserved).
2. 6E_DOSSIER §3 spread bullet: "p90 4 ticks ($50)" inconsistent at
   $6.25/tick → p90 ≈ 8 ticks ($50); roll gaps +82..+106 restated explicitly
   as TICK COUNTS = +$512.50..+$662.50/contract (erratum block in situ).
3. INTEGRATION_SUMMARY + REPORT_VI: handoff count corrected 12/13 → **14**
   (12 lanes + A7 + FIX); validation claim scoped to script-only.
