# HYPOTHESES_ESNQ_R3 — round-3 outcome-blind hypothesis search, ES + NQ (lane ESNQ)

- Task: **FUTURES-TEN-HYPO-PREP-20261004**, lane **ESNQ** (parallel,
  outcome-blind hypothesis search, no PnL). Generated 2026-10-04 UTC.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-ten-hypo/prep`
  @ HEAD **`a4a882658e09092b5b282b666b30a3cfc5ac3418`** (== dispatch base_sha,
  measured via the one permitted `git -C … rev-parse HEAD`; no other git run
  except `status --porcelain` at start/end), branch
  `prep/futures-ten-hypo-20261004`.
- Class: PREP hypothesis dossier. **Zero-PnL law (binding): 0 return / PnL /
  scored computations anywhere in this lane; no conditional-on-signal
  measurement of any proposed family (that measurement IS the family's
  scored trial and waits for scored authorization); 0 sweeps, 0 selection by
  any return statistic.** Every parameter **[PROVISIONAL]**. Missing evidence
  is **NOT_RUN / NOT_OBTAINED / BLOCKED_TRANSPORT**, never PASS.
- **No cycle registration, no trial creation, no registry/ledger writes.**
  `NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER` stand. Standing rulings
  restated (never reopened): **ES cap 24 FROZEN headroom 0 → any new ES
  family is born BLOCKED_TRIAL_BUDGET (D4 open)**; schedulability flag for
  the ES leg below = **BLOCKED_TRIAL_BUDGET**; **NQ only cache_v3 usable
  (canonical CANDIDATE pending D9; pre-v3 caches deprecated)**; fees
  MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN / **UNDER REVIEW until A7 re-audit
  (A7 NOT_RUN, D2 open)**; BBO NOT_RUN everywhere (conservative fill law);
  **D1-D12 all open — this lane self-ratifies nothing**.
- **Field format**: 11 numbered fields per family, exactly the baseline
  convention (ESNQ_HYPOTHESES.md / HYPOTHESES_R2.md): 1 Mechanism +
  microstructure · 2 Expected direction, falsifiable · 3 PIT feature
  availability · 4 Contract/unit/session/timezone/roll/expiry bindings · 5
  Entry/stand-aside/exit · 6 Baselines/placebo/negative controls · 7
  Refutation conditions · 8 Cost/spread/slippage sensitivity · 9 Regime/era
  breaks · 10 Coverage/hole proof · 11 Sources.
- Labels: **FACT** (primary source + capture, in-repo sha-provenanced) /
  **OBSERVED** (committed artifact + field) / **MECHANISM_HYPOTHESIS** /
  **INFERENCE** / **DERIVED** / **LITERATURE_ANCHOR** (named published
  literature, NOT fetched, INFERENCE-grade) / **NOT_RUN** /
  **NOT_OBTAINED** / **BLOCKED_TRANSPORT**. Words "measured cost",
  "complete cost" forbidden; "edge" claims forbidden.

---

## 0. Evidence base consumed before writing (all read-only)

1. Baseline hypo base (FUTURES-OVERNIGHT-PREP-20261003):
   `hypo/es_nq/ESNQ_HYPOTHESES.md` (8 families, §0.1-§0.5 standing context)
   + `hypo/es_nq/RANKING_INPUT.md` + `hypo/es_nq/esnq_hypotheses.json`;
   `hypo/cross/RANKING_FRAMEWORK.md` (D1-D5 0-3 anchors, aggregation +
   tie-break law, D5 floor definition); `synth/CENSUS_FINAL.md` (identity
   census conventions; controls-counted-in-minimal convention for
   ESNQ-class lanes; ES 36>24 headline).
2. R2 method exemplar + status updates: `FUTURES-SIX-ADOPT-PREP-20261004/
   hypo/HYPOTHESES_R2.md` (walls W1-W3; RMM/AF4 format; §4 carried-status
   items 2-3 for NQ-F3/NQ-F4) + `packet/CYCLE_LAUNCH_DRAFT.md` (§1 chains/
   costs/D3 basis variants, §2 PIT laws, §4 budget, §8 D1-D12).
3. Ancestry authorities: `research/wayfinder/FAMILY_FAILURES.jsonl` —
   **all 173 rows re-scanned this lane** (index of
   family_id / verdict_class / primary_failure code per row extracted and
   reviewed); `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/es_nq/
   NQ_DEEPFOUR_V3_ADDENDUM.md` §10 (dead-family transplant warning; FX
   cost-domination lesson; no prior scored equity-index-futures ancestor)
   + §11 (K1-K5 + NEW-1..NEW-4); `PB2_ANCESTRY_COURT_DRAFT.md` (court §b
   distinguishability method, cited via R2/RANKING_FRAMEWORK — read as
   summarized in those artifacts).
4. Calendar provenance (load-bearing for the NEW family below, all
   in-repo): `cme_cal/nq_es/nq_cal_coverage.json` (`expiration_rule.
   verbatim_er` era texts 2015/2018/2020; expirations 68/68 = 36
   product-specific + 32 family-level, cross-checks zero divergence;
   limits: 2026-era rule text NOT_OBTAINED, NQ early closes 2011/2021-25
   NOT_TRANSCRIBED); `cme_cal/nq_es/ES_EXPIRATIONS_GAPFILL.md` (official
   CME rolldates page verbatim: "Equity products roll date is the Monday
   prior to the third Friday of the expiration month"; BTIC termination
   Thursday); `FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/equity/
   EQ_GAPFILL_EVIDENCE.md` Gap 1 (ES 68/68 closure; dual independent
   captures G1a 20100528164817 / G1b 20100418154051; verbatim rows
   ESU10 09/17/2010 … ESU11 09/16/2011; rule-consistency cross-check
   "all five dates are the 3rd Friday of the contract month" recorded as
   OBSERVED consistency, never used as authority).
5. Anatomy artifacts (adjacent, cited precisely):
   `FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_session_stats.json`
   (`years[].sd_rth_pct` per year 2010-2026, median 0.6841% = 68.41 bp;
   `hour_profiles` per era; `eras`; `rth_buckets`);
   `analysis/NQ_a1_regimes.json` (`yearly[].vol_ann_pct` 17 years, median
   17.83% ⇒ session σ ≈ 112.3 bp DERIVED; known pre-recovery-series defect
   disclosed); `analysis/ES_fomc_stats.json` / `ES_cot_stats.json` /
   `ES_regime_stats.json` (occupied-family anatomy, unchanged).
6. Root read-only (`main d8cf8eca`): `research/control/FUTURES-DATA-10SYMS-V1/
   FINAL_REPORT.md` + `S6_FRONT_SPREADS.json` (ES spread 1.0 tick =
   $12.50, NQ 6.5 ticks = $32.50 close-proxy; IBKR fee law 2.24/side
   tier-1; ~14-month true-volume IBKR-era caveat for that chain — the
   R3 families below bind to the main chains of record per CYCLE_LAUNCH
   §1, not the 10SYMS chain; margins table for sizing-sensitive views).
7. `SPEC_PB1_ES.md` §5-§6 (frozen ES cost law Variant A 21.006/33.506/
   46.006 binding by default until D3; A-r4 24-identity enumeration law).

**Network use (disclosed)**: 5 fetch attempts / 30 budget, all
transport-blocked or 404, **0 bytes retrieved, 0 captures saved** — full
trail in `es_nq/fetch_log.jsonl`; `SHA256SUMS_lane.txt` is an empty
placeholder (zero captured content). Consequence: the index-OPTION-side
expiration calendar remains **NOT_OBTAINED** and the options-expiry
mechanism claim below stays MECHANISM_HYPOTHESIS + LITERATURE_ANCHOR
INFERENCE; the FUTURES-side calendar is fully FACT-grade **in-repo** (§0-4
above), which is what the family conditions on. Everything else in this
dossier is in-repo evidence.

---

## 1. Search result and closure

**1 NEW family is proposed — `ESNQ-F5 EXPWITCH` (quarterly
expiration-Friday forced-hedging conditioning; legs ES + NQ)** — **1
construction-only adjudication** is recorded (ES session-close era changes,
§3), and **17 candidates are vetoed** (§4), every one against a named wall.
The gap between 1 and the ≤3 cap is deliberate and evidenced: the
dispatch's suggested spaces (close-era natural experiments, rebalance
windows, COT-timestamp refinement, beyond-8:30 macro clocks) each died
against the occupied-family inventory, the dead-family inventory, or the
zero-PnL/PIT data laws — documented per candidate in §4. An honest count of
1 beats a padded three.

The four walls that did the killing (restated from R2 with R3-specific
citations):

- **W1 Ancestry (dead-family rename).** Calendar-flow and positioning-clock
  candidates hit dead rows directly (turn-of-month → `SFV3-A6-TOM-SETTLE`
  PF_BELOW_THRESHOLD + FX month-end fix `DTPFX1-A1-MEFIX`
  VARIANT_SAME_FAMILY; CoT release-clock → `COMMNG1-A4-P2` arms
  CONTROL_OUT_EARNS_RELEASE_CLOCK; volume-shock-conditioned arms →
  `XSECT-VOLSHK-S15`).
- **W2 Occupied-class / anti-multi-trial (baseline §0.5 + PB1 territory).**
  Fed-information second constructions (minutes, pre-FOMC drift),
  scheduled-print clock extensions (10:00 ET block, 08:30 non-CPI/NFP
  prints, claims Thursdays), and OVN-window restarts (Sunday reopen) are
  re-parameterizations of ES-F1/ES-F2/PB1's registered m's.
- **W3 Standing law / construction (DC §1.3 class).** Session-clock,
  chain, and settlement-mechanism facts (close-era changes, SOQ/chain
  audits) are construction rules and era-break fields, never alpha
  hypotheses.
- **W4/W5 Data absence / transport.** MOC imbalance feed, earnings
  calendars, fair-value/dividend/borrow corpus, monthly-opex calendar,
  options-side expiry rule text: NOT_IN_CORPUS, NOT_OBTAINED, or
  BLOCKED_TRANSPORT — none may be designed around by assumption.

## 2. ESNQ-F5 `EXPWITCH` — quarterly expiration-Friday forced-hedging conditioning (legs: ES + NQ)

1. **Mechanism + microstructure.**
   - **M-HEDGE-PERSIST [MECHANISM_HYPOTHESIS]**: on the third Friday of
     Mar/Jun/Sep/Dec the equity-index derivatives stack expires
     simultaneously: the quarterly futures terminate at 9:30 a.m. ET on the
     3rd Friday of the contract month [FACT, verbatim era rule texts,
     `nq_cal_coverage.json:expiration_rule.verbatim_er` — 2018/2020 texts
     "Termination Of Trading: Trading (terminates) at 9:30 a.m. Eastern
     Time (ET) on the 3rd Friday of the contract month"; 2015 text "up to
     8:30 a.m." with page times listed as Central Time; ES spec captures
     20150319105531 / 20200317052532 per EQ_GAPFILL], index options expire
     on the same third-Friday calendar with AM-settled series pinned to the
     opening SOQ [CONVENTION-ANCHOR: options-side primary page
     BLOCKED_TRANSPORT → NOT_OBTAINED, fetch_log; LITERATURE_ANCHOR:
     Stoll & Whaley's expiration-day studies document the
     expiration-driven hedging/volume mechanism on the S&P complex], and
     the expiring futures complex settles via the SOQ at the cash open.
     Dealers carrying short-gamma into expiry must unwind those hedges as
     the options die; index arbitrage must hold futures-cash convergence
     through the opening auction; passive/benchmark money is forced to
     trade the close. **Who is forced**: option dealers (hedge unwind on a
     date known years ahead), index arbitrageurs (convergence), close-
     benchmarked flow (execution benchmark). **Who is slow**: discretionary
     RTH liquidity re-pricing the decaying pressure through the afternoon.
     **Why an effect can exist**: the flow is calendar-forced and largely
     price-insensitive, concentrated on ~4 dates/yr — if the unwind
     pressure persists into the late-afternoon close, the close-window move
     extends (continuation arm).
   - **M-HEDGE-FADE [MECHANISM_HYPOTHESIS]**: the same forced afternoon
     flow is mechanical over-extension that exhausts at the close; once
     hedge demand dies with the options, the returning ordinary book fades
     the move — measured as same-session reversion after a late trigger
     (reversal arm), in direct competition with M-HEDGE-PERSIST (both
     arms registered together, falsification-by-competitor, PB §4.6
     convention).
   - Constraining anatomy: the witching-vs-ordinary-Friday interaction is
     **NOT_RUN** (never measured on the committed panels — the hour-level
     era profiles exist but contain no expiry-day separation). Adjacent
     committed anatomy this family stands on: era hour profiles and
     RTH-bucket structure [OBSERVED, `ES_session_stats.json:
     hour_profiles` per era E1-E7 + `rth_buckets`]; the 68/68 quarterly
     expiry calendars for both symbols with per-year captures [OBSERVED,
     nq_cal_coverage / EQ_GAPFILL Gap 1]; roll-vs-expiry calendar
     separation ("Equity products roll date is the Monday prior to the
     third Friday of the expiration month" [FACT verbatim,
     ES_EXPIRATIONS_GAPFILL.md §1]; ES roll T-5 66/66, NQ k=5
     crossover-DTE median 7 [OBSERVED, baseline §0.4]). **The anatomy
     pre-gate (field 7, F5-K6) is therefore the family's first required
     measurement — same structure as ES-F2's F2-K6.**
2. **Expected direction, falsifiable** [PROVISIONAL, no PnL claim].
   - M-HEDGE-PERSIST: on quarterly expiry Fridays, sign(W1) — where
     **W1 = log(close_of_14:00CT-bar / px_at_13:30CT)**, price-measured
     strict-past — agrees with the sign of (era-correct close − 14:00 CT
     entry) **more often than the weekday-matched ordinary-Friday clock
     placebo**, stable across the tri-eras, surviving S2 modeled cost.
   - M-HEDGE-FADE: the opposite sign statement, same machinery, same
     placebo contrast. If BOTH arms fail the K2-class floor at S1, the
     family is dead — re-parameterization FORBIDDEN.
   - Both statements are sign statements on committed panels; the
     conditional measurement itself is NOT performed in PREP (zero-PnL
     law).
3. **PIT feature availability.**
   - Conditioner = the quarterly expiry calendar: **ES 68/68 quarters**
     (42 product-specific + 26 official family rolldates; the five
     2010-11 gap quarters closed with dual independent archived product
     captures G1a/G1b, exact agreement, and NQ-product cross-checks
     zero-divergence) [OBSERVED, EQ_GAPFILL_EVIDENCE Gap 1 +
     ES_EXPIRATIONS_GAPFILL]; **NQ 68/68** (36 product-specific + 32
     family-level; every available product-specific cross-check agrees
     exactly) [OBSERVED, nq_cal_coverage]. 2026 dates authority-backed
     (3/20, 6/18 Juneteenth-shifted, 9/18, 12/18). Calendar is known years
     ahead ⇒ decide-at-close-t / effective-t+1 is trivially satisfied;
     no rule-derived date anywhere (derivation forbidden per calendar law;
     the 3rd-Friday consistency appears only as a recorded cross-check).
   - **NOT_OBTAINED (disclosed, scope-limiting)**: (i) the index-OPTION
     side of the expiry calendar (monthly-opex dose stratum and the
     options-expiry rule text) — BLOCKED_TRANSPORT this lane (5 attempts,
     fetch_log) ⇒ monthly-opex layer is **NOT_RUN descriptive-only** and
     the options-side mechanism stays MECHANISM_HYPOTHESIS; (ii) 2026-era
     futures rule text (JS shells) — conditioning unaffected (dates are
     obtained; the operative 9:30 a.m. ET termination is era-anchored
     2018/2020 verbatim); (iii) MOC/imbalance feeds — NOT_IN_CORPUS, never
     assumed; (iv) surprise/content conditioning — not needed (calendar
     conditioner), none invented.
4. **Contract / unit / session / timezone / roll / expiry bindings.**
   - ES: mult 50, tick 0.25 ($12.50/tick), quotes in index pts;
     NQ: mult 20, tick 0.25 ($5.00/tick). America/Chicago; all windows in
     CT trade-time. Era-correct closes per baseline §0.4 (16:30/16:15/
     16:00 CT eras; pre-2016 break-tails separated); NQ closes incl.
     Friday-15:15 era-A rule.
   - **Chain**: ES T-5 (66/66); NQ k=5 + cease-guard, **cache_v3 chain
     only** (D9 pending; pre-v3 caches deprecated). **Roll-vs-expiry
     separation is structural**: the switch date precedes expiry Friday
     (ES T-5; NQ crossover DTE median 7) ⇒ on expiry Friday the held
     chain holds the NEXT quarterly, which is not itself terminating; the
     9:30 a.m. ET termination binds the EXPIRING contract only [INFERENCE
     from the verbatim rule + chain rule]. K6 audits held-chain session
     integrity on expiry Fridays (no phantom gap around the expiring
     contract's termination); any session whose held-contract calendar is
     uncertain ⇒ EXCLUDE fail-closed.
   - Warmup 252 sessions (ES precedent). Universe = the 68 expiry
     Fridays per symbol 2010-2026 minus the exclude laws below.
5. **Entry / stand-aside / exit [PROVISIONAL]** (PB1 discipline).
   - Signal day = quarterly expiry Friday (calendar). W1 measured
     13:30 CT → the 14:00 CT 1m-bar close (strict past). Entry = **open of
     the NEXT 1m bar** after the trigger (conservative fill law; no
     limit/queue claims). Direction: CONT arm takes sign(W1); FADE arm
     takes −sign(W1) (both tails registered). **Delay pair {+1 bar (14:00
     CT), +30m (14:30 CT)} = two scored identities** per arm×tier. Exit:
     mandatory time exit at the era-correct close (never holds the
     break/overnight; the next-session continuation view is a **0-identity
     descriptive evaluation view only**, disclosed as PB1-adjacent since
     its holding window contains the OVN). TP 2.0×SL; SL = 1.0× median
     prior-20 same-session ranges (strict past, era-correct marks, short/
     flagged sessions excluded); same-bar touch of both ⇒ **SL priority**.
   - Stand-aside / excludes: (i) expiry Fridays stacking a scheduled 08:30
     CT macro print (event-stacking — occurs; excluded, count disclosed at
     census); (ii) FOMC statement days (essentially nil overlap — FOMC is
     Tue/Wed — but the standing law is applied anyway); (iii) calendar-
     uncertain days (2026 Globex-uncertain; NQ early-close
     NOT_TRANSCRIBED days) ⇒ EXCLUDE fail-closed; (iv) RTH-core coverage
     <60% ⇒ EXCLUDE; (v) 2020-03-20 is armed but pre-declared as a
     K3-guarded stratum (inside the COVID window).
   - **Overlap disclosure**: expiry Fridays can also be PB1-armed days
     (q80 OVN tails). Different m (calendar-forced afternoon window vs
     OVN overnight tail), different clock (14:00 CT vs 08:30 CT entry) —
     distinct constructions; overlap count disclosed at census.
6. **Baselines / placebo / negative controls.**
   - C1 seeded clock placebo: identical machinery on **weekday-matched
     ordinary Fridays** (months-position matched 2nd/4th/5th Fridays),
     new disclosed seed, single-seed single-delay limitation inherited.
     C2 always-in on expiry Fridays at the 14:00 CT clock (does W1's sign
     carry anything beyond event-day exposure?). C3 flat anchor (ledger).
     C4 dose-response in |W1| terciles.
   - **Family-specific negative control NC-1**: the matched ordinary-
     Friday set itself — if ordinary Fridays reproduce the W1→close
     pattern, the mechanism is "Friday clock," not expiration (kill,
     F5-K5).
   - **NC-2 (declared NOT_RUN)**: monthly-opex (non-quarterly third
     Fridays) as the graded dose member between quarterly witching and
     ordinary Fridays — its calendar is NOT_OBTAINED (options-side;
     arithmetic derivation forbidden) ⇒ the dose layer stays descriptive-
     NOT_RUN until a permitted-route capture lands (D12-class residual).
7. **Refutation conditions** (mechanism kills first).
   - **F5-K1 era instability**: surviving arm's sign flips across tri-eras
     (2010-16 / 2017-21 / 2022-26) ⇒ participation/era artifact, kill.
     Pre-registered interpretation: published expiration effects are
     old-regime phenomena (LITERATURE_ANCHOR); modern-era decay is a live
     outcome and manifests as the K6 anatomy death, not as a scored loss.
   - **F5-K2 both arms below Stage-A floor at S1 (1-tick) ⇒ dead;
     re-parameterization FORBIDDEN.** *Expected-failure honesty
     [DERIVED]*: armed n ≈ 66-68 events/symbol minus excludes (~60-66);
     court-method MDE (two-sided α=0.05, power 80%, z=2.80; dispersion
     proxy = committed session σ, an upper bound): **ES** median RTH
     session sd **68.41 bp** [OBSERVED, ES_session_stats years[]
     .sd_rth_pct median 0.6841%] ⇒ **MDE ≈ 23.6 bp at n=66** vs modeled
     RT(S2) ≈ 1.34 index pts = **12.2 bp at the 2010-era price ~1,100**
     (conservative era-low; **2.0 bp at ~6,800**); **NQ** median ann vol
     **17.83%** ⇒ session σ ≈ **112.3 bp** [OBSERVED, NQ_a1_regimes
     yearly[].vol_ann_pct median; pre-recovery-series defect disclosed]
     ⇒ **MDE ≈ 38.7 bp** vs RT(S2) 2.849 pts = **15.8 bp conservative /
     1.1 bp modern**. **MDE ≥ cost scale at realistic n in both legs ⇒
     this family is power-marginal by construction; a null at n≈66 is the
     pre-registered K2 death, NOT evidence of absence.**
   - **F5-K3 concentration**: ≥80% of contribution from 2020-03..04
     (2020-03-20 expiry sits inside the window — pre-declared).
   - **F5-K4 delay flip**: sign flips between +1bar and +30m ⇒ close-
     auction microstructure artifact, downgrade to descriptive.
   - **F5-K5 placebo reproduction**: NC-1 matched ordinary Fridays show
     the same pattern ⇒ "Friday clock" artifact, kill.
   - **F5-K6 anatomy pre-gate (construction gate, 0 identities,
     PREP-legal)**: before any scoring is ever proposed, (i) the
     witching-Friday session anatomy must be measured on the era-correct
     mapping and show elevated close-window volume/activity vs matched
     ordinary Fridays **in the modern eras**; (ii) held-chain session
     integrity on expiry Fridays must pass (no phantom gaps; switch-day
     audit law NEW-4 inherited for the NQ leg). Failure ⇒ the family
     never enters scoring.
   - Cost survival statement: whatever survives must survive **S2** with
     S1/S3 flanks reported, ×1.0/×1.5/×2.0 ladder; fee values UNDER
     REVIEW (D2/A7 NOT_RUN).
8. **Cost / spread / slippage sensitivity.** MODELED COST only.
   - ES: S1 20.99 / S2 33.49 / S3 45.99 per side (corrected 2.24/side
     tier-1 fee composition, spread half-turn proxy 6.25, slippage 1/2/3
     ticks × $12.50 = assumption D1). **Default-binding variant**: SPEC
    _PB1_ES §5 frozen law S1 21.006 / S2 33.506 / S3 46.006 (NFA 0.02
     single-source) binds until D3 rules the basis; delta $0.01/side.
   - NQ: S1 23.49 / S2 28.49 / S3 33.49 per side (2.24 + spread proxy
     16.25 from the 6.5-tick close proxy, high-biased; slippage ×$5.00).
   - Expiry-Friday late-session fills plausibly face worse-than-median
     books — **no slippage claim beyond the {1,2,3}-tick tier triple is
     legal** (double-stress forbidden); BBO NOT_RUN; stress ladder
     ×1.0/×1.5/×2.0 mandatory at any future scoring. Words "measured/
     complete cost" FORBIDDEN.
9. **Regime / era breaks.** Tri-era 2010-16 / 2017-21 / 2022-26 mandatory
   per leg; session-close-era views (16:30/16:15/16:00 CT) as
   evaluation views; carry-era roll-spread-sign covariate (§0.5-2)
   annotation; 2020-03-20 pre-declared K3 stratum; index-option volume
   growth regime annotated (mechanism-size prior, never a conditioner).
10. **Coverage / hole proof.** Panels: ES 4,204 sessions / NQ 4,219 held
    sessions 2010-06→2026-10, 0 integrity violations [OBSERVED, baseline
    §0/F10]; event n = 68 quarterly expiries per symbol 2010-2026, minus
    the exclude laws (expected ~60-66; exact census disclosed when a
    packet is ever drafted). Holes declared: options-side / monthly-opex
    calendar NOT_OBTAINED (BLOCKED_TRANSPORT trail saved);
    2026-era futures rule text NOT_OBTAINED (dates obtained); NQ early
    closes 2011/2021-25 NOT_TRANSCRIBED (excluded fail-closed); BBO and
    account-fee verification NOT_RUN. No other input is required; nothing
    unavailable is assumed.
11. **Sources.** `nq_cal_coverage.json` (expiration_rule verbatim_er;
    expirations 68/68; limits) + `ES_EXPIRATIONS_GAPFILL.md` +
    `EQ_GAPFILL_EVIDENCE.md` Gap 1 (dual captures G1a/G1b + sha-pinned
    captures dir) + `NQ_CALENDAR_EVIDENCE.md` (all under
    FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/ and
    FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/equity/); ES_session_stats
    .json years[].sd_rth_pct + hour_profiles; NQ_a1_regimes.json
    yearly[].vol_ann_pct (defect disclosed); NQ_DEEPFOUR_V3_ADDENDUM §4/
    §10/§11 (NEW-4 law); ES_DEEPFOUR_V3_ADDENDUM §3 (era closes);
    FEES_CORRECTED.md; SPEC_PB1_ES §5-§6; CENSUS_FINAL §1 conventions;
    RANKING_FRAMEWORK D5 floor definition; Stoll & Whaley expiration-day
    studies [LITERATURE_ANCHOR — named, NOT fetched, INFERENCE-grade];
    lane fetch_log.jsonl (5 attempts, 0 captures — BLOCKED_TRANSPORT).

### 2b. Trial-identity census (CENSUS_FINAL conventions; controls counted in minimal)

| leg | grid (arms × delays × tiers) | full-grid IDs | minimal-core | + scored controls | minimal total |
|---|---|---|---|---|---|
| ES | 2 × 2 × 3 | 12 | 4 (S2, +1bar, both arms) | 3 (C1, C2, NC-1) | **7** |
| NQ | 2 × 2 × 3 | 12 | 4 | 3 | **7** |
| both | — | 24 | 8 | 6 | **14** |

0-cost legs (never scored): F5-K6 anatomy pre-gate; monthly-opex dose
stratum (NOT_RUN); next-session continuation view (PB1-adjacency
disclosed); era/delay evaluation views on existing paths.

### 2c. Provisional D1-D5 (RANKING_FRAMEWORK anchors, applied mechanically; outcome-blind)

| dim | score | one-line mechanical basis |
|---|---|---|
| D1 | **2** | 68/68 expiry calendars + era hour profiles committed on-target multi-era, but the family-specific witching×session interaction is NOT_RUN (anchor 2c — RMM precedent) |
| D2 | **2** | actors + exact timing + symbol/era reason + family-specific NC present, **conservatively capped at 2**: nearest-name dead-class relative exists (CNG1-A5-P2 options-expiry class — blocked pre-scoring, different asset, never falsified) and the options-side primary capture is BLOCKED_TRANSPORT ⇒ the D2=3 anchor is not claimed |
| D3 | **2** | kills complete (K1-K6 incl. anatomy pre-gate + delay pair + cost-tier statement) and court-method MDE computed at realistic n — but MDE (23.6/38.7 bp) is at/above cost scale at n≈66 (anchor 2a; power-marginal by construction) |
| D4 | **3** | the sole conditioner is the quarterly expiry calendar: PIT, per-year + dual independent captures, 68/68 both symbols, zero rule-derivation, no external conditioner, look-ahead structurally excluded |
| D5 | **2** | floor computed AND MDE computed from committed dispersion proxies; r = RT/MDE ≈ 0.52 (ES, era-conservative price) / 0.41 (NQ, era-conservative) ≤ 1; the r ≤ 1/3 band is reached only at modern price levels (disclosed, not claimed) |
| **Total** | **11** | ties the baseline's ES-F1/NQ-F1 package score (11) — disclosed for the synthesis lane |

Status: **ES leg BLOCKED_TRIAL_BUDGET at birth** (cap 24 FROZEN, headroom
0; D4 open) — carried as dossier-worthy under the strong-mechanism clause
(FACT-grade calendar, forced-actor mechanism, complete kill set). **NQ leg
CTG** (no NQ cap; gates: fee A7 D2, calendar-2026 excludes, D9 cache_v3
ratification, F5-K6 anatomy pre-gate).

## 3. Construction-only adjudication — ES session-close era changes (16:30/16:15/16:00 CT)

Adjudicated per the dispatch's own hint, honestly: **CONSTRUCTION-ONLY —
not a family.** The close-time changes are session-clock facts of the
chain construction [OBSERVED, ES_DEEPFOUR_V3_ADDENDUM §3; baseline §0.4].
DC §1.3 law: roll timing, chain, session clock = construction rules, never
alpha hypotheses. Any "liquidity-redistribution around the close change"
candidate is (i) a clock-only construction whose conditioning variable is
the venue's own rule, (ii) already carried as the era-break/evaluation-
view surface of every existing family (hour_profiles/rth_buckets per era),
and (iii) un-scoreable without inventing an actor story the artifacts do
not support. The correct disposition — already in force — is that all
families carry the era splits as K1-style views. Recorded here so the
synthesis lane sees the space was probed and closed, not skipped.

## 4. Veto ledger — every rejected candidate and the wall that killed it

| # | candidate (design space probed) | verdict | wall (specific) |
|---|---|---|---|
| V1 | Quarterly index-rebalance windows (S&P quarterly share changes; NDX annual re-rank) vs roll-week | **DUPLICATE-VETO / adjacency** | (a) no index-level forced DIRECTIONAL actor — a rebalance basket is internally long/short, net ≈ 0 for the index instrument (the forced flow is intra-index = cross-sectional territory); (b) effective dates are the third Fridays — temporally confounded with both the roll-week (NQ-F4 class) and EXPWITCH's own dates ⇒ indistinguishable constructions; (c) the volume-conditioning arm of the idea is adjacent to dead `XSECT-VOLSHK-S15` (dollar-volume shock continuation, SELECTION_REJECTION); (d) rebalance announcement calendar NOT_OBTAINED in-repo (W4) |
| V2 | CFTC COT publication-timestamp refinement over ES-F3 (Friday 15:30 ET release-minute/afternoon conditioning) | **DUPLICATE-VETO** | ES-F3 owns the positioning class (its stage-1 session-granularity vol leg is the registered 0-ID carrier); a release-clock layer is a re-parameterization of the same weekly signal; dead adjacency: `COMMNG1-A4-P2` CoT arms CONTROL_OUT_EARNS_RELEASE_CLOCK — the release clock itself out-earned the conditioned arms in the program's only CoT-release corpus; NQ TFF NOT_RUN (100% null) stands (W1+W2) |
| V3 | FOMC minutes release days (14:00 ET, ~8/yr) as a family | **DUPLICATE-VETO** | ES-F1 owns the Fed-scheduled-information mechanism class; minutes are a second construction on the same event series (multi-trial inflation, baseline §0.5); minutes anatomy NOT_RUN (ES_fomc_stats covers statements only); crypto precedent `CNG1-A4-P1` FOMC-instant family blocked ANCESTRY_RHO_BLOCK — program precedent against additional FOMC-instant constructions (W1+W2) |
| V4 | Pre-FOMC drift (Lucca-Moench-class calendar long) | **DUPLICATE-VETO** | the documented drift accrues predominantly in the pre-release/OVN window — PB1 parent-pair territory (24 FROZEN) with FOMC-day exclusion as its standing law; a FOMC-conditional OVN-side position is a calendar-filtered re-parameterization of the parent's m (§0.5-1); NQ addendum NEW-2 already frames FOMC-conditional splits as evaluation views (W2) |
| V5 | 10:00 ET macro block (ISM, consumer sentiment, home sales) + 9:45 ET flash PMI | **DUPLICATE-VETO** | occupied scheduled-print class (ES-F2); the thin-book actor that makes 07:30 CT special (3.0% volume hour, |1m| 1.61 bp) does not exist at 10:00 ET — prints land into the liquid RTH book; day-of-week confounds (Friday sentiment, 1st-business-day ISM); surprise conditioning NOT_RUN (W2) |
| V6 | 08:30 CT scheduled-print extensions: PPI, retail sales, GDP, jobless-claims Thursdays | **DUPLICATE-VETO** | ES-F2's 08:30 clock class; extension to other series = same-family multi-trial; ES-F2's anatomy pre-gate (F2-K6) already governs the clock (W2) |
| V7 | Treasury auction / quarterly refunding announcement clocks (12:00 CT results window) | **DUPLICATE-VETO + DATA-BLOCKED** | rates-transmission mechanism, second-order for equity indices; auction-surprise conditioning (stop-through/yield vs WI) NOT_IN_CORPUS; calendar-only conditioning = weaker clone of the occupied print class with no thin-book actor (W2+W4) |
| V8 | API crude-inventory Tuesday 16:30 ET | **OUT-OF-LANE VETO** | energy print — CL/NG mechanism (COMM lanes' territory); equity-index transmission via energy equities is second-order with no named forced actor on ES/NQ |
| V9 | MOC / closing-auction imbalance window (daily 15:50/15:58 ET) | **DATA-BLOCKED** | the conditioning variable (MOC imbalance feed) is NOT_IN_CORPUS; the calendar-only variant is a clock family that fails its own negative control by construction (placebo wall); no capture route without a data entitlement (W4) |
| V10 | Pre-holiday full-session conditioning | **VETO** | no forced actor (liquidity/disposition story is generic); confounded with the always-on C2 baseline (calendar long = clock family); no committed event-separable anatomy; adjacent DT100 calendar-clock deaths (`DT100-34-WEEKEND` NEGATIVE_EXPECTANCY class) (W1+W2) |
| V11 | Circuit-breaker / limit-move days as event class | **DATA-BLOCKED VETO** | armed n is a handful of days in 16.4y (below any ≥5-per-fold floor); halt-session bars are calendar-uncertain under the coverage law ⇒ EXCLUDE fail-closed — the class cannot even be armed honestly (W4) |
| V12 | Turn-of-month / month-end settlement flows | **ANCESTRY VETO** | dead `SFV3-A6-TOM-SETTLE` (stocks, PF_BELOW_THRESHOLD) is the same signal class; FX month-end London-WMR fix family `DTPFX1-A1-MEFIX` VARIANT_SAME_FAMILY; `FXFV5-A6-P1` pre-release-avoidance CONTROL_OUTEARNED_ANCHOR adjacent (W1) |
| V13 | NDX mega-cap earnings-cluster windows (aggregate earnings-season conditioning) | **DATA-BLOCKED VETO** | member-level earnings calendars NOT_IN_CORPUS; index-level aggregate effect is a participation/volume class adjacent to the dead volume-shock family; cross-sectional territory (W1+W4) |
| V14 | ES/NQ relative-value, lead-lag, or spread conditioning | **OUT-OF-LANE** | cross-symbol designs belong to the CROSS lane (baseline lane discipline; X-2 RELMIN-SIG already exists there); nothing single-symbol is proposed |
| V15 | Sunday reopen / Globex 17:00 CT conditioning | **DUPLICATE-VETO** | the 17:00 reopen is the OVN window's start — PB1's registered territory (M-A/M-B); a reopen-minute family is an inside-the-window re-parameterization (W2) |
| V16 | Index-vs-futures basis / fair-value / dividend-calendar / FF-futures-implied conditioning | **OUT-OF-LAW + DATA-BLOCKED** | DC §1.3 structural-input law (carry/basis = overlays on structural inputs, never standalone alpha); the PIT dividend/borrow/fair-value corpus is absent — any design would be built on NOT_RUN inputs (W3+W4) |
| V17 | NQ crash-roll / chain-artifact days as event class | **CONSTRUCTION-ONLY** | chain-integrity events are construction facts (NQ-F4 Role A law + NEW-4 standing audit); "conditioning" on them selects data defects, not market behavior; already owned by the Role-A audit as a kill condition, never a signal (W3) |

## 5. Ancestry-check table (every candidate vs the dead inventory)

Scan basis: all **173** `FAMILY_FAILURES.jsonl` rows re-scanned this lane;
court §b method as summarized in R2/RANKING_FRAMEWORK; NQ addendum §10
("no prior scored ancestor for equity-index futures exists in this
program" [OBSERVED]).

| candidate | nearest dead entries (asset, family_id, class/code) | distinguishability statement | verdict |
|---|---|---|---|
| **ESNQ-F5 EXPWITCH** | CNG1-A5-P2 (crypto; SELECTION_REJECTION / ANCESTRY_RHO_BLOCK — "monthly post-options-expiry unwind, settlement-hours hedge pressure": **blocked pre-scoring on ancestry rho, never falsified on evidence**); TRACKA2-P4A-FIXCERT-01 + DTPFX1-A1-MEFIX (forex calendar-flow/fix classes; DECLARED_BAND_BELOW_MEASURED_COST / VARIANT_SAME_FAMILY); DT100-34-WEEKEND (crypto calendar-clock, NEGATIVE_EXPECTANCY); XSECT-VOLSHK-S15 (volume-shock class, if a volume-conditioned variant were proposed — it is not: the conditioner is the calendar, volume appears only inside the K6 anatomy gate) | (i) mechanism class = derivative-expiration forced hedging + settlement anchoring — requires an options/futures expiration machinery; the only in-corpus relative (CNG1-A5-P2) is a different asset and was blocked, not falsified; (ii) the signal m is the third-Friday calendar itself [FACT-grade 68/68 in-repo], not a price tail, volume shock, or generic session window; (iii) windows are disjoint from the occupied classes: roll switch precedes expiry Friday by construction (T-5 / crossover-DTE-7), FOMC/macro clocks are excluded by law; (iv) no scored equity-index-futures ancestor exists anywhere in the program; (v) MOC/imbalance and options-side inputs are declared NOT_OBTAINED, never assumed | **NO_VETO** — pass, with the CNG1-A5-P2 row disclosed as nearest-name, F5-K5/F5-K6 gates pre-registered, and the options-side FACT upgrade marked BLOCKED_TRANSPORT |
| V1 rebalance windows | NQ-F4 ROLLWK (registered class, not dead); XSECT-VOLSHK-S15 (volume-conditioning arm) | no index-level forced directional actor; temporally confounded with expiry/roll dates | **VETO-cited** (occupied/confounded) |
| V2 COT-clock | COMMNG1-A4-P2 (commodities; CONTROL_OUT_EARNS_RELEASE_CLOCK); ES-F3 occupied | same positioning class + release-clock out-earned precedent | **VETO-cited** |
| V3 minutes / V4 pre-FOMC | CNG1-A4-P1 (crypto FOMC-instant, ANCESTRY_RHO_BLOCK); ES-F1 / PB1 occupied | second constructions on Fed-information class / parent OVN territory | **VETO-cited** |
| V12 turn-of-month | SFV3-A6-TOM-SETTLE (stocks, PF_BELOW_THRESHOLD); DTPFX1-A1-MEFIX (VARIANT_SAME_FAMILY) | same calendar-flow signal class | **VETO-cited (ancestry)** |
| all others (V5-V11, V13-V17) | see §4 table rows for per-candidate citations | — | **VETO-cited** |

## 6. Budget surfaces (marked per dispatch; NO caps invented)

- **ES**: ESNQ-F5 ES leg = born **BLOCKED_TRIAL_BUDGET** (cap 24 FROZEN,
  headroom 0; D4 open). If an owner amendment ever legalized it: +12
  full-grid / **+7 minimal** (incl. 3 controls) additive ⇒ ES minimal
  surface would move 36 → 43 vs the frozen 24. Until ruled: 0 identities,
  only the F5-K6 anatomy pre-gate is executable (PREP-legal, 0-cost).
- **NQ**: no numeric cap exists in standing rulings (CENSUS_FINAL §4);
  ESNQ-F5 NQ leg is **CTG contingency-only**: +12 full / +7 minimal
  census lines, consumable only after fee A7 (D2), calendar-2026 excludes,
  D9 cache_v3 ratification, F5-K6 gate — and an explicit owner NQ ceiling
  before any packet.
- Controls counted inside minimal totals (ESNQ-lane convention,
  CENSUS_FINAL §1); C1 single-seed limitation inherited; placebo-budget
  ruling slot remains EMPTY (CENSUS_FINAL §5) — nothing here presumes it.
- Diagnostics: none proposed this lane (the F5-K6 anatomy gate is
  specified inside the family as its own construction gate, matching the
  ES-F2 F2-K6 pattern; it is not a separate X-class item).

## 7. NOT_RUN / NOT_OBTAINED / BLOCKED_TRANSPORT register (this lane)

1. Options-side expiry calendar + monthly-opex dose calendar + options
   rule text: **NOT_OBTAINED** — BLOCKED_TRANSPORT, 5 attempts logged, 0
   bytes, 0 captures (fetch_log.jsonl; SHA256SUMS_lane.txt intentionally
   empty). EXPWITCH's options-expiry mechanism statement remains
   MECHANISM_HYPOTHESIS + LITERATURE_ANCHOR; the futures-side conditioning
   calendar is FACT-grade in-repo.
2. Witching×session interaction anatomy (both legs): **NOT_RUN** — the
   F5-K6 pre-gate; never measured on the committed panels.
3. Next-session continuation view of EXPWITCH: **NOT_RUN descriptive**
   (PB1-adjacent; 0 identities forever).
4. NQ dispersion used in the D5/MDE arithmetic is from the **pre-recovery
   series** (NQ_a1_regimes yearly vol_ann_pct) — defect disclosed; full-era
   rebuild precondition inherited by every NQ leg.
5. 2026-era futures expiry rule text: NOT_OBTAINED (JS shells); operative
   termination rule era-anchored 2018/2020 verbatim; 2026 dates
   authority-backed.
6. Standing (unchanged, inherited): surprise/consensus NOT_RUN; publish
   latency NOT_RUN; BBO NOT_RUN; A7 NOT_RUN (fees UNDER REVIEW, D2);
   MOC/imbalance feeds NOT_IN_CORPUS; earnings calendars NOT_IN_CORPUS;
   NQ early closes 2011/2021-25 NOT_TRANSCRIBED; D1-D12 all open.
7. Owner rulings this lane DECLARES but does not self-ratify: (a) any
   future ES identity budget amendment for the ESNQ-F5 ES leg (D4); (b)
   NQ ceiling before any NQ packet; (c) D9 cache_v3 canonicalization; (d)
   D2 fee A7 authorization. None is presumed.

— End HYPOTHESES_ESNQ_R3.md. Zero PnL/returns entered any cell; 5 network
attempts logged with zero content retrieved; 1 NEW family + 1
construction-only adjudication + 17 vetoes + 9 carried statuses; every
ancestry check cited; missing evidence is NOT_RUN, never PASS. No
registration, no trial creation — proposals on paper only.
