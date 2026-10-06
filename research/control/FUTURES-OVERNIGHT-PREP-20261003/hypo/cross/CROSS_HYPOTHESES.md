# CROSS_HYPOTHESES — Cross-symbol falsification designs (P1-CROSS)

- Task: **FUTURES-OVERNIGHT-PREP-20261003**, lane **P1-CROSS**. Generated UTC
  2026-10-04. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` @
  `72c9bc5b1d94b812044a9bd21768c53b4d378436` (re-measured via `git -C` before
  writing; no tracked drift), branch `prep/futures-behavior-10syms-20261002`.
- Class: PREP cross-symbol falsification designs. **0 PnL, 0 scored runs, 0
  sweeps, 0 selection by return statistics; every parameter [PROVISIONAL];
  outcome-blind.** These are DIAGNOSTICS whose pre-declared "result" is a
  sign-consistency or co-movement statistic, **never a PnL**. No cross design
  registers a scored identity (see CENSUS_PROPOSAL.md, family-type T6 = 0
  identities).
- Evidence base read at 72c9bc5b before writing: six v2 dossiers
  (`FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/{ES,NQ,6E,6B,6J,6A}_DEEP_v2.md`),
  four v3 addenda + PB2 court draft
  (`FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/**`),
  `FUTURES-DATACONTRACT-QUAL-V1/{DATACONTRACT_QUALIFICATION.md,PLAYBOOKS_DRAFT.md}`,
  batch-1 facts (`fees_erratum/source/FEES_CORRECTED.md`,
  `bls_vintage/BLS_VINTAGE_INVESTIGATION.md`, `cme_cal_gap/**`), and the two
  RETURNED sibling outputs `hypo/es_nq/{ESNQ_HYPOTHESES.md,RANKING_INPUT.md}`
  and `hypo/6e_6b/{FX_HYPOTHESES.md,RANKING_INPUT.md}`. P1-6J6A / P1-COMM
  outputs NOT read (concurrent lanes; synthesis handles them).
- Labels on every substantive claim: **OBSERVED** (artifact + field) /
  **MECHANISM_HYPOTHESIS** (unmeasured causal story) / **INFERENCE** (argument
  from evidence, flagged) / **NOT_RUN** (missing evidence is never PASS).
  **No new web numerics fetched this lane** — every number below is a repo
  artifact cited with path (+sha256 prefix in §sources; full table in
  `cross_hypotheses.json`).
- Design IDs: **X-1 … X-5**. They are cross-symbol by construction: each
  requires ≥2 symbols and tests a mechanism claim that **only exists across
  symbols** (venue-independence, common-factor structure, era-driver
  synchronization, pooled null machinery). Nothing here duplicates a
  single-symbol family.

---

## 0. Standing context all cross designs inherit (cite-once block)

### 0.1 Panels and era clocks (per symbol) [OBSERVED]

| symbol | panel | era clock available for cross designs |
|---|---|---|
| ES | 16.4y, 4,204 sessions 2010-06→2026-10-01 (ES addendum §6) | tri-era 2010-16 / 2017-21 / 2022-26 (K1 OVN convention) + FOMC data-eras 2016-19 / 2020-22 / 2023-26 + 7 data-quality eras E1-E7 |
| NQ | 4,219 held sessions 2010-06-07→2026-10-01 (NQ addendum §6) | same tri-era convention; OVN-share level shift ~2018-19; full-era rebuild on alias-recovered series outstanding (hard precondition) |
| 6E/6B | 6.8y, 1,746 sessions each 2020-01→2026-09 (court §c1) | policy eras 2020-22 (COVID/ZIRP/2022 USD shock) vs 2023-26 (carry); 6B adds the 2022 LDI crisis vol regime + zero-diff window 2025-26 |
| 6J | 6.8y, 1,745 sessions 2020-01→2026-09 (`6J_qa_ledger.json`) | yen-weak super-cycle 2021-26 (one −46.7% rolled drawdown); BoJ regime-change MPMs 2024-26 |
| 6A | 6.8y, 1,746 sessions 2020-01-02→2026-09-30 (6A §0) | same policy eras as 6E/6B; own CIP clock = RBA−Fed differential (2024 contango → 2026 backwardation) |

**Binding consequence**: any cross design containing an FX leg is confined to
the 2020-01→2026-09 overlap window (the ES/NQ 2010-19 history has no FX
counterpart — this is a coverage fact, not a choice). ES/NQ-only designs
(X-1) may use the full 16y.

### 0.2 Quote-orientation law (binding on X-2/X-3) [OBSERVED]

6E = USD per EUR (tick 5e-05 = $6.25); 6B = USD per GBP (tick 0.0001 = $6.25,
adjudicated GLBX 19,183 rows); 6A = USD per AUD; **6J = USD per JPY
(0.0061-0.0099, NOT USDJPY; 6J UP = yen appreciation; implied USDJPY =
1/(6J price), band 100.80-163.68)** [OBSERVED, 6J_DEEP_v2 §0 quote-orientation
trap, restated load-bearing]. Therefore in **USD-appreciation terms**
u_t(s) = −1m-return of the futures price, applied UNIFORMLY to all four FX
legs: dollar-up ⇒ 6E/6B/6A/6J prices ALL fall. **The 6J inversion binds at
the corpus boundary, not inside the futures quartet**: every sign imported
from the USDJPY-convention world (the dead spot corpus, FX commentary) must
be flipped for 6J (USDJPY-long = 6J SHORT; 6J_DEEP_v2 §7). Any pooled
statistic that skips this normalization is void by construction law, not by
outcome [INFERENCE from the two cited orientation laws].

### 0.3 Corrected cost law (batch-1) [OBSERVED, MODELED]

Tier-1/fixed all-in per side: ES/NQ **2.24**, FX (6E/6B/6J/6A) **2.46**,
CL 2.36, NG 2.46, GC/SI 2.51 USD [FEES_CORRECTED §2, sha256 006d6372…]. All
MODELED COST, VERIFIED_VS_ACCOUNT=NOT_RUN, **UNDER REVIEW until a new A7
re-audit**. Cross designs are diagnostics: they carry **no per-identity cost
and no double-counted costs** (hosts already charge their own tiers); cost
appears in X-designs only as an execution-realism annotation (§8 per design).

### 0.4 Event-calendar authority [OBSERVED]

FOMC: 132 archived statements 2011-01→2026-09, **92 with in-document release
times (85 @14:00 ET + 7 irregular), 2011-15 day-level only** [ES addendum §2].
In-panel FX counts: 6E 58/58 time-proofed, 6B 58+1 (M4-disclosed), 6A 59.
RBA: 67 meetings 2020-01→2026-09 (23 changes/44 holds), anchor 14:30 Sydney
effective_date−1-AU-BD, as-published gate HTML [6A §4.1]. BoE MPC: 56
in-panel, minute-720 London anchor, DST-stable [6B dossier]. BoJ MPM: 156
statements stored; regime-change MPMs 4 measured + 2 v1-FACT [6J §7-H4].
BLS CPI/EMPSIT: PASS_EVIDENCED 204+204 @08:30 ET with **vintage law**
(BLS_VINTAGE §5; 2025: 11 CPI/10 EMPSIT actual prints; canceled-but-expected
days enumerated). **No PIT surprise/consensus archive exists anywhere in the
program (H3) — every cross design conditions on schedules + realized prices
only.**

---

## X-1 `OVN-COMOVE` — ES/NQ overnight-share co-movement: falsifier for the whole OVN family

**(1) Mechanism + constraining anatomy.**
- **M-X1 [MECHANISM_HYPOTHESIS]**: the OVN pair's premise (parent H-A/H-B,
  PB1 M-A/M-B, NQ M-A′/M-B′) is that OVN moves carry *venue-independent
  information* accumulated while liquidity is thin, which RTH then either
  continues (M-A) or fades (M-B). If the information is venue-independent,
  the *participation regime that carries it* must co-move across correlated
  venues: ES and NQ OVN shares should rise/fall in the same eras. A
  single-symbol artifact (index-membership migration, one venue's
  institutional flow) would NOT co-move.
- OBSERVED anatomy, ES [ES_DEEP_v2 §3 era table; ES addendum §11-K1]:
  Var(ON) share by era **E1 38.5 / E2 38.6 / E3 43.6 / E4 28.4 / E5 50.7 /
  E6 32.8 / E7 34.2 %** (crisis 50-54%, quiet 21% in 2018); K1 convention
  2010-16 ≈ 30-46%, 2017-21 spans 20.9→53.8%, 2022-26 ≈ 29-45%. ES OVN
  *volume* share: stable ~15-17% across 16 years [ES_DEEP_v2 §3].
- OBSERVED anatomy, NQ [NQ_DEEP_v2 §2; NQ addendum §8]: OVN *volume* share
  **10.2% (2010) → 15.8% (2016) → 22.5% (2019) → 19-24% (2023-26, 2026:
  23.8%)**, level shift ~2018-19. **NQ OVN variance share by era: NOT_RUN**
  (never measured; the committed NQ series is the volume kind).
- **Kind mismatch disclosed [INFERENCE]**: the two committed series are
  different statistics — ES variance-share vs NQ volume-share. Notably, on
  the VOLUME kind the raw facts already diverge in shape (ES flat 15-17% vs
  NQ doubling 10→24%) while on the VARIANCE kind only ES is measured. The
  design therefore begins with a same-kind recompute (field 5) and forbids
  any conclusion drawn across kinds.

**(2) Expected direction IF true (falsifiable, no PnL).**
If the OVN-information premise holds at family level, then per-era
(2010-16/2017-21/2022-26, plus year-by-year) deviations of ES and NQ
OVN shares from their own trailing medians should be **positively rank-correlated
beyond a symbol-shuffled placebo band** (pre-declared statistic: Spearman ρ
of same-kind annual share deviations; placebo = year-label permutation within
symbol, ≥1,000 draws, seeds disclosed). **This is a FALSIFIER, not an alpha**:
co-movement provides no new family (anti-multi-trial ruling, ESNQ §0.5-1);
divergence beyond the placebo band on BOTH same-kind recomputes (volume-kind
and variance-kind) ⇒ the "OVN information regime" story is symbol-specific ⇒
the K1/NEW-1 participation-artifact verdict escalates from per-symbol to the
whole OVN family (ES pair + NQ pair share the mechanism claim).

**(3) PIT availability.** Fully in-repo: both share series derive from
session-segment statistics on held chains (strict-past by construction); no
external conditioner. NQ leg inherits the **full-era rebuild precondition**
(alias-recovered series; only 2020 aggregates re-measured) — the recompute
must run on the recovered series or be labeled NOT_RUN [OBSERVED, NQ §9
precondition (iv)].

**(4) Bindings.** Era-correct session closes per symbol (ES 16:30/16:15/16:00
CT; NQ Mon-Thu 16:15→16:00 CT 2015-09-21+, Friday 15:15 CT era-A excluded);
ON segment = 17:00→08:29 CT era-correct; DST-correct America/Chicago both
symbols; tri-era clock 2010-16/2017-21/2022-26 + FOMC data-eras as
sensitivity views. No 6J/FX leg exists for this design (their panels start
2020 — no era span).

**(5) Diagnostic run specification [PROVISIONAL, 0 scored identities].**
Step 1 (prep-legal descriptive, prerequisite): compute the missing cells of
the 2×2 (symbol × statistic-kind) — NQ var(ON)-share by year/era on the
recovered series; ES OVN volume-share by year (exists: ~15-17% stable) — same
window conventions as ES_DEEP_v2 §3. Step 2: era-level and year-level
deviation series per symbol-kind; Spearman ρ(ES, NQ) per kind + placebo band
(year-permutation within symbol). Step 3: report the two ρ's with bands.
**No entries, no exits, no stand-aside beyond each symbol's standard
exclude-list (calendar-uncertain EXCLUDE/NOT_RUN); the pre-declared result is
the two consistency statistics, never a PnL.**

**(6) Baselines/placebo/negative controls.** (i) Year-permutation placebo
(above); (ii) **negative control NC-X1**: same statistic computed on RTH
*volume* shares (expected stable in both symbols — a structural quantity with
no information claim; if OVN shares "co-move" as strongly as this null
quantity, the co-movement carries no mechanism content); (iii) crisis-window
annotation: E5 2020-21 must be reported with/without (its 50.7-53.8% ES
variance share is the NEW-1 crisis-participation suspect — a co-movement
driven only by E5 is itself the participation artifact).

**(7) Refutation conditions.** X1-K1: either same-kind ρ fails to exceed its
placebo band ⇒ **family-level OVN premise downgraded to symbol-specific**
(recorded as an evaluation constraint on both parents' K1/NEW-1 views, not a
new kill of registered identities). X1-K2: co-movement exists ONLY through
E5/E7 crisis windows ⇒ participation artifact (consistent with NEW-1). X1-K3:
NQ recompute cannot complete (rebuild blocked) ⇒ NQ leg NOT_RUN, ES-only
conclusion FORBIDDEN (no cross-symbol claim from one symbol).

**(8) Cost sensitivity.** None — descriptive on existing session statistics;
no scored legs; no cost charged or double-counted (hosts PB1-ES / future NQ
packet carry their own tiers).

**(9) Regime/era breaks.** Tri-era mandatory; FOMC data-eras as sensitivity;
2020 alias window (NQ) must be recovered-series only; 2018-19 NQ level shift
is itself part of the measured input (not smoothed away).

**(10) Coverage/hole proof.** ES 4,204 sessions / NQ 4,219 held sessions,
0 integrity violations both [ES/NQ addenda §6]. Holes: NQ var-share NOT_RUN
until Step 1; NQ full-era rebuild precondition; ES yearly var_on_pct exists
in `ES_session_stats.json` (K1's constraining anatomy). Nothing else
unavailable.

**(11) Sources.** ES_DEEP_v2.md §3 (sha256 05f0874f…); ES addendum §11-K1
(d18d5422…); NQ_DEEP_v2.md §2 (d3cf621c…); NQ addendum §8 (e78548a6…);
PLAYBOOKS_DRAFT §0 H-A/H-B rows (7610ed3c…); ESNQ_HYPOTHESES §0.5
anti-multi-trial rulings (9f9176e5…).

---

## X-2 `RELMIN-SIG` — scheduled-release-minute cross-venue signature (FOMC anchor class)

**(1) Mechanism + constraining anatomy.**
- **M-X2 [MECHANISM_HYPOTHESIS]**: a scheduled information release resolves
  uncertainty at a *known minute*; if the release genuinely carries common
  information (rather than each venue's book responding to local
  microstructure), then across venues the release minute should show (a) a
  volume/|ret| elevation of consistent ORDERING by event class (policy
  decisions > hard data > no-event) and (b) a consistent SIGN structure: the
  USD-appreciation-normalized first-minute response on FOMC minutes should
  agree in sign across 6E/6B/6A (and the index venues respond oppositely to
  a dollar-up move only through their own cash-flow channel — the index leg
  is reported as a stratum, not pooled with FX). If the sign structure is
  inconsistent across venues, the "scheduled-information resolution"
  mechanism story shared by ES-F1/NQ-F1/FX-F2/FX-F3 dies at the
  mechanism level.
- OBSERVED anatomy (parent F-8 correction embodied: **the largest scheduled
  1m-volume event on 6E is FOMC (×17.24), NOT ECB (×1.73)**):
  - ES: release 15-min bucket **2.906× volume / 3.188× |1m ret|**; +30m
    2.653× (presser wave); reaction peak median +1 min [ES_fomc_stats.json,
    via ESNQ ES-F1; sha 228fe2d4…].
  - NQ: release minute itself **×3.5 volume**; 0-30m 2.256×, 30-60m 2.637×;
    era table lull 0.80→0.59, spike 2.99→1.46, |ret| stable 2.2-2.4×
    [NQ_a4_events.json, sha 5a09aff9…].
  - 6E: FOMC statement minute 13:00 CT **×17.24** median volume vs control
    Wednesdays; +5m ×9.96; +10m ×5.61; re-amplifies ×8.81 at 13:40 CT;
    ECB decision minute ×1.73 [6E_a4_events.json `fomc`/`ecb`, via
    FX_HYPOTHESES §2].
  - 6B: MPC first-5m **18.7×** (minute exactly 720 London, DST-stable);
    FOMC on 6B 9.5× first-5m [6B_a4_events.json].
  - 6A: RBA ±5min **9.0× volume / 4.8× |1m ret|**; FOMC on 6A ±5min
    **8.2× volume / 6.2× |ret|**, "larger and longer than RBA's — US rates
    are the bigger common factor for AUD/USD" [6A_DEEP_v2 §4.1-§4.2].
  - 6J: BoJ MPM |ret| 1.9× baseline, regime-change MPMs 1.9-2.7× volume;
    **FOMC-on-6J: NOT_RUN** [6J_DEEP_v2 §7-H4].
- **Window heterogeneity disclosed [OBSERVED]**: the committed ratios above
  use FOUR different windows (15-min bucket; release minute; ±5min;
  first-5m) and two baseline conventions. No cross-venue consistency
  statistic is legal on them as-is — the common-window re-measure (field 5)
  is a hard prerequisite.

**(2) Expected direction IF true (pre-declared consistency statistic, never
PnL).**
On the common window (release-minute ±5 min, weekday-matched non-event
same-minute baseline, per venue): (i) every venue's FOMC volume ratio > its
no-event baseline ratio trivially, and the class ordering
FOMC > RBA/MPC-on-home-venue… is tested per venue as: **home-policy-decision
ratio vs FOMC ratio ordering must match the "US-rates dominance" pattern on
6A/6E/6B (FOMC ≥ home except 6B-MPC) or the mechanism story needs
revision**; (ii) **sign consistency**: per common-timed FOMC event e (n ≈ 53
in the 2020-01→2026-09 FX∩index window), the USD-appreciation first-minute
signs across {6E, 6B, 6A} agree (all-dollar-up or all-dollar-down) at a rate
exceeding the weekday-matched non-event placebo band computed the same way;
(iii) the index venues (ES/NQ) show a first-minute sign whose relation to
the dollar sign is reported as a stratum with NO pooling assumption.

**(3) PIT availability.** FOMC minute-proof PASS_EVIDENCED (92 timed
statements, as-issued HTML; §0.4). FX panels 2020+ ⇒ common event set =
in-panel timed statements 2020-01→2026-09 (6E 58/58, 6B 58+1, 6A 59; ES/NQ
minute anchors 2016+). RBA/MPC/ECB/MPM anchors PASS_EVIDENCED per §0.4.
Surprise content NOT_RUN everywhere ⇒ the design conditions on the EVENT and
realized first-minute sign only (stated limitation, same as all macro
families).

**(4) Bindings.** Quote-orientation law §0.2 (u = −futures-return for all FX
legs; 6J would enter inverted vs USDJPY convention — and is in any case
NOT_RUN for FOMC until measured). Era clocks: ES/NQ FOMC data-eras
2016-19/2020-22/2023-26; FX 2020-22 vs 2023-26 policy eras; common-window
convention fixed BEFORE any computation [PROVISIONAL: ±5 min volume, ±1 min
sign].

**(5) Diagnostic run specification [PROVISIONAL, 0 scored identities].**
Step 1: common-window re-measure of release-minute ±5min volume ratio and
first-minute |ret| per venue per event class (FOMC on all venues; RBA/MPC/
ECB/MPM on home venues; BLS 07:30 CT class on ES/NQ/6E/6B). Step 2:
cross-venue sign-consistency rate on the common FOMC event set + placebo
band (weekday-matched non-event minutes, same normalization, ≥1,000
permutations of event dates, seeds disclosed). Step 3: class-ordering table.
**No entries/exits; the pre-declared result = the consistency rate vs its
band + the ordering table. NEVER a PnL, never a cross-venue "trade".**

**(6) Baselines/placebo/negative controls.** (i) Weekday-matched non-event
same-minute placebo per venue (the pooled version is X-4); (ii) **NC-X2
same-minute ECB stratum**: ECB decision minutes (×1.73 class) must show a
WEAKER signature than FOMC on 6E — if equal, the statistic is measuring
"any scheduled central-bank timestamp", not information intensity;
(iii) **NC-X2b off-hour FOMC-timed control**: the 7 irregular-time statements
(2020-03-15 17:00 Sun etc.) enter as a separate stratum, never pooled
(liquidity state differs by construction).

**(7) Refutation conditions.** X2-K1: cross-venue sign agreement on common
FOMC events fails to exceed the placebo band ⇒ the shared
"scheduled-information resolution" mechanism of ES-F1/NQ-F1/FX-F2/FX-F3 is
not a common-information phenomenon ⇒ each family's mechanism section must
be re-scoped to venue-local stories before any registration (downgrade
recorded family-wide; NOT a rescue). X2-K2: class ordering inverted on ≥2
venues (e.g., home-bank spike < no-event-class spike) ⇒ intensity story
dead on those venues. X2-K3: consistency exists only in one policy era ⇒
era-specific artifact, annotation not mechanism.

**(8) Cost sensitivity.** Diagnostic only; no scored legs; no cost charged.
Execution-realism annotation: FX-F2's T+60s law (6B_v2 §8-H2') already
documents that same-minute fills inside 9.96-17.2× spikes are optimistic —
X-2 makes no fill claim and none may be inferred from it.

**(9) Regime/era breaks.** FOMC data-eras (ES/NQ) and 2020-22/2023-26 (FX)
reported as strata; 2020 emergency-timing statements excluded from the
common set (rare-timed law, all families); 2025 BLS vintage break irrelevant
here (FOMC anchor only) but the BLS-class stratum inherits the vintage law
if extended.

**(10) Coverage/hole proof.** Common event set enumerated from committed
calendars (§0.4); zero missing event-day bars on 6E (session coverage median
1,356 bars); 6J FOMC leg NOT_RUN (declared); ES/NQ 2011-15 day-level only ⇒
excluded from minute statistics. NQ aggregates on the alias window must use
recovered-series re-measures (same precondition as X-1).

**(11) Sources.** ES_fomc_stats.json (228fe2d4…); NQ_a4_events.json
(5a09aff9…); 6E/6B addenda §5 (12e2aa56…/5cc26206…); 6A_DEEP_v2 §4.1-4.2
(76d32f1c…); 6J_DEEP_v2 §7 (ef95ad8d…); FX_HYPOTHESES §2 (f8403a0f…);
ESNQ_HYPOTHESES ES-F1/NQ-F1 (9f9176e5…).

---

## X-3 `FX-BASKET` — common-dollar-factor vs idiosyncratic central-bank conditioning (6E/6B/6J/6A)

**(1) Mechanism + constraining anatomy.**
- **M-X3a common factor [MECHANISM_HYPOTHESIS]**: the four USD-per-foreign
  futures respond to a common USD factor; on US-information minutes the
  basket's u = −return series should co-move (X-2 is the event-minute
  instance; X-3 is the basket-level conditioning question). **M-X3b
  idiosyncrasy [MECHANISM_HYPOTHESIS]**: home central-bank conditioning
  (ECB/MPC/RBA/BoJ days and policy regimes) BREAKS or modulates the common
  factor — the FX-F2 family's per-symbol stories and FX-F5's regime
  conditioning presuppose this separation. X-3 makes the separation itself
  the measured object: if home-bank conditioning does NOT modulate basket
  co-movement, the per-symbol "policy-decision resolution" stories collapse
  into one dollar story; if US minutes do NOT produce common co-movement,
  the FX-F3 "US-data spillover" story dies as a basket mechanism.
- OBSERVED anatomy: 6A FOMC 8.2× vs RBA 9.0× (FOMC "larger and longer" on
  6A — §X-2); 6E FOMC 17.2× vs ECB 1.73×; 6B MPC 18.7× vs FOMC 9.5×; 6J
  MPM 1.9× (weakest class, thin US-overnight book: BoJ window median 1m
  volume 34 vs 53 full-day) [6J_DEEP_v2 §0-2]; 6E 07:30 CT block ×1.95
  present every weekday, and the 06:30-08:00 CT block carries **15.58% of
  session RV on 12.5% of volume** (highest information-per-contract
  segment); 6B 07:00-12:00 London share drift 28.7%→23.7% with the 08:00
  London hour falling hardest (7.7→5.7%) — the US-macro dominance drift
  [FX_HYPOTHESES §3]; 6B idiosyncratic risk pricing exists: rolling-63d
  corr(6B ret, Δgilt10) min −0.57 at 2022-10-17, LDI crisis = THE 6B vol
  regime 2022-12-20 [6B_DEEP_v2 §5-6].
- **Dollar-measure availability, stated honestly [OBSERVED]**: NO PIT-strict
  daily dollar or policy-rate series exists on disk — FRED DFF/SOFR/
  DFEDTARU latest-vintage; ALFRED year-end vintages only (no 2025 SOFR
  vintage); ECB €STR latest; BoE Bank Rate revision-free; **DXY: NOT on
  disk; NO purchases allowed** (owner law). The basket factor is therefore
  constructed IN-VENUE (strict-past cross-sectional aggregation of the four
  u series); any external dollar series can appear only as a
  descriptive, latest-vintage covariate labeled NOT PIT.

**(2) Expected direction IF true (falsifiable, no PnL).**
Pre-declared statistics: (i) **common-factor share**: average pairwise
Spearman of 5-minute u-blocks across the four legs on all minutes vs on
FOMC/08:30-ET minutes vs on home-bank minutes — under M-X3a+b, co-movement
on US-information minutes exceeds both the all-minute base and the
home-bank-minute level by more than the weekday-matched placebo band;
(ii) **idiosyncrasy modulation**: on home-bank event days the HOME leg's
idiosyncratic share (1 − |corr with basket factor|) rises vs its own
non-event days; (iii) **era stability**: the (i)-(ii) contrasts hold in
both 2020-22 and 2023-26 eras. All three are correlation/consistency
statistics — never PnL.

**(3) PIT availability.** Event calendars §0.4 (all PASS_EVIDENCED); in-venue
price data strict-past by construction; the external-dollar covariate is
NOT PIT (latest-vintage) and may not gate anything. FX expiries 2023-2026
NOT_OBTAINED (FXCAL §1) — irrelevant here (no expiry-window contact;
declared per law).

**(4) Bindings.** §0.2 orientation law: u = −futures-return uniformly;
**6J inverted vs USDJPY corpus conventions** (the single most likely
fatal transcription error in this design — pre-declared as a binding, with
a one-line arithmetic self-check: sign of 6J u must EQUAL the others' u on
FOMC minutes under dollar-dominance). Era clocks: 2020-22 vs 2023-26;
6J's yen-cycle legs as declared strata (never pooled); 6B LDI window
2022-09→2022-12 as a high-vol stratum.

**(5) Diagnostic run specification [PROVISIONAL, 0 scored identities].**
Step 1: build u series per leg (1m → 5-min blocks, era-correct session
template 17:00→16:00 CT, 23h continuous — 6J median 1,357/1,380 bars);
Step 2: basket factor = cross-sectional median of standardized u (strict-past
standardization); Step 3: the three pre-declared statistics with placebo
bands (weekday-matched non-event minutes; ≥1,000 permutations, seeds
disclosed). **No entries, no exits, no stand-aside beyond each symbol's
standard excludes; result = the contrast table of consistency statistics.**

**(6) Baselines/placebo/negative controls.** (i) Weekday-matched non-event
minute placebo (all three statistics re-computed on it); (ii) **NC-X3
rotated-orientation control**: recompute statistic (i) with the 6J sign
deliberately NOT normalized — the design's own trap detector: if the "wrong"
version shows similar co-movement, the statistic is insensitive and void;
(iii) **NC-X3b thin-book stratum**: 6J's BoJ-window (median 34 contracts/min)
reported separately — if 6J's co-movement is indistinguishable from its
thin-book noise floor, drop 6J from the basket statistic and report 6E/6B/6A
only (pre-degraded, not a failure).

**(7) Refutation conditions.** X3-K1: US-minute co-movement does not exceed
the all-minute base beyond the band ⇒ FX-F3's basket-level "US-data
spillover" story dead (per-symbol F3 legs may survive as venue-local
families — recorded as re-scoping). X3-K2: home-bank days show NO idiosyncrasy
modulation ⇒ the per-symbol FX-F2 policy stories collapse toward one dollar
factor (FX-F2's strata design loses its distinguishing content). X3-K3:
everything is era-unstable ⇒ no basket claim at all. X3-K4: NC-X3 passes
(rotated orientation indistinguishable) ⇒ statistic void, redesign required.

**(8) Cost sensitivity.** Diagnostic; no scored legs; no cost charged.
(Informational note only: 6J execution in its thin windows pays ~2× thinner
books — 6J-H6 law; this is why 6J is a stratum here and never silently
pooled.)

**(9) Regime/era breaks.** 2020-22 vs 2023-26 mandatory; 6B LDI stratum;
6J yen-cycle legs; 2022 USD shock year reported as its own annotation
(6A §0 regime map: 2022 vol 13.4% vs 8.4-12.1% neighbors).

**(10) Coverage/hole proof.** 4 legs × 1,745/1,746 sessions, 0 integrity
violations (6J 1 stray halt bar; 6B 1 maintenance-break bar in 6.8y — both
declared in dossiers); FOMC-on-6J NOT_RUN; external-dollar PIT NOT_RUN
(declared, §1); no other holes.

**(11) Sources.** 6E/6B/6J/6A dossiers (bf2a952d…/bc8a1dc3…/ef95ad8d…/
76d32f1c…); FX_HYPOTHESES §2-§5 (f8403a0f…); 6B addendum §3 (5cc26206…);
DATACONTRACT §1.3 roll rows (df175a2d…); FEES_CORRECTED §2 (006d6372…).

---

## X-4 `PLACEBO-POOL` — pooled cross-symbol placebo band (one program-level power statement)

**(1) Mechanism + constraining anatomy.**
- **M-X4 [INFERENCE → diagnostic instrument, not an alpha claim]**: every
  family in the program carries a weekday-matched non-event clock control
  (NC-1 ES 13:00 clock; NC-2/NC-6 07:30 clocks; NC-5 NQ 13:00; C3-FX
  weekday-matched non-event; C1 multi-seed bands). These controls sample the
  SAME null — "the clock without information" — on different symbols. If the
  null machinery is sound, the symbol-standardized control statistics should
  be exchangeable; pooling them yields ONE placebo band (tighter than any
  single family's) and therefore ONE pooled power statement for the whole
  program: the dispersion of the program's null.
- OBSERVED basis: control specifications are committed in both sibling
  outputs (ESNQ §(6) per family; FX_HYPOTHESES §1-§6 controls + court §c4
  multi-seed law "single-seed is explicitly insufficient (PB1 precedent)");
  the PB2 court §c3 supplies the MDE method (two-sided α=0.05, power 80%,
  z=2.80, daily-σ upper-bound proxy). **The pooled statistic itself:
  NOT_RUN** (no family has run; nothing to pool yet).

**(2) Expected direction IF true (falsifiable, no PnL).**
Pre-declared: (i) pooled standardized null band from all symbols' control
legs (statistic = symbol-standardized sign-agreement deviation, z-scored by
each symbol's own control dispersion); (ii) **between-symbol heterogeneity
test** on the control legs (pre-declared: χ²-type dispersion test across
symbols' z-distributions); (iii) the single pooled power statement: "at the
achieved pooled control-n, the program null dispersion is estimated at σ̂
[CI], so a family-level standardized effect is distinguishable at 80% power
when its own n satisfies |effect| ≥ 2.80·σ̂/√n_family" (court §c3 method
applied with the pooled σ̂). No family ranking input beyond power framing;
NO PnL anywhere.

**(3) PIT availability.** Controls use only in-venue prices + committed
calendars (weekday matching); nothing external; no PIT hole. Multi-seed
extension requires the placebo-budget ruling (CENSUS_PROPOSAL §3) — if
seeds are ruled budgeted identities, the pooled band is built from the
already-mandatory single-seed legs per family and the limitation is
published, not hidden.

**(4) Bindings.** Same-symbol standardization mandatory (raw bp never pooled
across symbols — tick grids and notionals differ by factors of ~4-10);
era-stratified pooling as sensitivity (a null that drifts across eras must
not be forced stationary); FX legs enter only from 2020+.

**(5) Diagnostic run specification [PROVISIONAL, 0 scored identities].**
Runs when the FIRST registered families run their mandatory control legs:
harvest each family's control-leg statistic (already mandatory — no new
runs), standardize per symbol, pool, report (i)-(iii). **No entries/exits;
the "result" is the band + heterogeneity verdict + one power sentence.**

**(6) Baselines/placebo/negative controls.** The design IS the placebo
layer; its own negative control = **leave-one-symbol-out stability** of the
pooled band (if dropping any one symbol moves the band materially, the
exchangeability assumption fails — report, never rescue).

**(7) Refutation conditions.** X4-K1: between-symbol heterogeneity
significant ⇒ pooling VOID — each family keeps its own band and the
"program-level power statement" is downgraded to per-family statements
(honest branch, pre-declared). X4-K2: pooled band cannot be built (no
families run) ⇒ stays NOT_RUN — never an inferred pass of anything.

**(8) Cost sensitivity.** None: control legs are already budgeted inside
each family's census; X-4 adds ZERO identities and ZERO cost (its entire
value is arithmetic on already-mandatory outputs — the cheapest design in
the program).

**(9) Regime/era breaks.** Era-stratified pooling sensitivity mandatory
(2020-22 vs 2023-26 on FX legs; tri-era on ES/NQ legs where they exist).

**(10) Coverage/hole proof.** Depends on future registered runs; today
NOT_RUN with the harvest specification frozen here. No data hole beyond
those inherited per symbol (§0.1).

**(11) Sources.** PB2_ANCESTRY_COURT_DRAFT §c2-§c4 (e358e2ce…); PLAYBOOKS
§1 C1-C5 classification + A-r4 single-seed limitation (7610ed3c…);
ESNQ_HYPOTHESES control sections (9f9176e5…); FX_HYPOTHESES §1-§6 +
RANKING_INPUT (f8403a0f…/b7f62080…).

---

## X-5 `ERA-SYNC` — carry-era roll-spread sign synchronization across NQ/ES/6B/6A/6J(+6E)

**(1) Mechanism + constraining anatomy.**
- **M-X5 [MECHANISM_HYPOTHESIS]**: the program's families use a common era
  clock whose economic content is "the USD short-rate regime changed in
  2022" (ZIRP → positive rates). The measurable consequence on term
  structure: per-symbol calendar-spread/roll-gap signs should flip into the
  carry era SYNCHRONIZEDLY (each with own-differential amplitude), because
  the common driver is the USD leg of every differential. If the flips are
  NOT synchronized, the "common era driver" story is per-symbol noise and
  the tri-era clocks used by K1-type kills inherit symbol-specific
  instability. **H-G law binding [OBSERVED, PLAYBOOKS §0]**: roll-gap CIP
  carry is a structural input, NEVER alpha — X-5 is a diagnostic of era
  fields, not a family, and registers nothing.
- OBSERVED per-dossier sign facts (all committed):
  - **NQ** [NQ_DEEP_v2 §3]: ann. adjacent-quarter premium by year
    −0.40…−0.83% (2010-15) / +0.53, +1.50, +1.23% (2017-19) / −0.46, −0.26,
    +1.13% (2020-22) / **+5.00, +4.99, +4.09, +3.81% (2023-26)** — sign
    stabilizes positive exactly 2022+.
  - **ES** [ES addendum §0.5-2 / ES_roll_stats]: roll gaps 39 neg / 27 pos;
    61/66 sign match vs DFF−1.8pp proxy (**proxy NOT PIT**).
  - **6B** [6B_DEEP_v2 §3]: corr(gap ticks, Fed-target-upper − Bank Rate)
    Pearson +0.84 / Spearman +0.7445; calendar-spread medians walk with the
    differential +19.5 ticks (2022) → −1.0 (2026); zero-diff 2025-26 rolls
    show mixed small gaps (−5..+13 ticks).
  - **6A** [6A_DEEP_v2 §3.1-3.2]: sign agreement **16/16 rolls with
    material |Δ|≥25bp** (74% overall, misses = 2021 ZIRP noise); median gap
    +0.41% ann; 2024-01-02 +0.65% contango (Fed 4.25-4.50 vs RBA 3.10) →
    **2026 rolls −15/−27/−22 ticks (−0.42/−0.75/−1.87% ann)** — flipped
    backwardation as RBA 4.35% > DFF 3.63%.
  - **6J** [6J_DEEP_v2 §0/§7-H3]: near<far on **100.0%** of overlapping
    sessions (14 pairs); 25/27 roll gaps positive (2 tiny negatives in
    zero-rate 2021); annualized medians 0.52/0.13% (2020/21) → 2.33% (2022)
    → **5.50/5.46% (2023/24)** → 2.87/2.42% (2025/26).
  - **6E** [6E_DEEP_v2 §4 / ERRATUM MAJOR-2]: 27/27 roll gaps positive; sign
    agreement with SOFR−€STR 27/27 latest-vintage / 26/27 PIT-as-of;
    correlation **vintage-fragile (r=+0.9097 latest vs −0.107 PIT-as-of)**.

**(2) Expected direction IF true (falsifiable, no PnL).**
Pre-declared statistics on the common 2020-01→2026-09 window (all six
symbols): (i) **flip clustering**: the year in which each symbol's annual
median spread/roll-gap sign turns (or, for FX, tracks its differential)
should cluster in 2022-23 under the common-driver story; measured as the
cross-sectional dispersion of first-sustained-positive years (NQ 2022; 6J
2022; 6B 2022; 6A 2024 — driven by its own differential, not 2022; 6E
positive throughout) with a pre-declared clustering tolerance [PROVISIONAL:
±2 quarters at quarterly granularity where roll dates permit]; (ii) **annual
co-movement**: mean pairwise Spearman of the six symbols' annual median
spread series 2020-26 vs a year-shuffled placebo band (≥1,000 draws);
(iii) **differential-timing residual**: per symbol, flip timing vs its own
rate-differential flip (latest-vintage, labeled NOT PIT, descriptive only).
If (i) fails to cluster AND (ii) fails its band, the common-era-driver
story is dead at program level.

**(3) PIT availability.** Spread/roll-gap series: fully in-repo strict-past
(roll rules per DATACONTRACT §1.3: ES T-5, NQ k=5+cease-guard, 6E Friday
rule, 6B/6J k=5, 6A declared-extrapolation — **6A k=5 not yet measured,
ERRATUM A7-DC-F3 — the 6A roll dates used must be the declared-rule dates
with that caveat attached**). Rate differentials: latest-vintage/ALFRED
year-end only ⇒ NOT PIT-strict — statistic (iii) is descriptive-only by law
and may not gate anything.

**(4) Bindings.** Era clocks: tri-era on ES/NQ (whose 2010-21 legs exist);
2020-22/2023-26 on FX; per-symbol own-differential timing as the
idiosyncratic reference. Sign conventions per symbol stated once: equity
premium = new-over-old annualized; FX gap = new−old close at last
both-traded session (economically the carry cost); **6J's positive gap =
long-JPY pays carry (near<far) — orientation restated so no reader flips
it** [6J §7].

**(5) Diagnostic run specification [PROVISIONAL, 0 scored identities].**
Pure arithmetic on committed series: assemble the six annual-median series
(2020-26; ES/NQ also 2010-19 as extended strata where measured), compute
(i)-(iii) with the placebo bands. **No entries/exits; result = the
synchronization verdict. NEVER a PnL; NEVER a signal (H-G law).**

**(6) Baselines/placebo/negative controls.** (i) Year-shuffled placebo
(within symbol) for statistic (ii); (ii) **NC-X5 own-differential-only
control**: a synthetic "synchronized" series built from each symbol's OWN
differential sign — if the real co-movement is no stronger than this
control, there is no COMMON residual beyond idiosyncratic CIP (which is
already law, H-G) — the design then concludes "era clocks are per-symbol
differential clocks", which is itself the useful verdict; (iii) ES-proxy
sensitivity: recompute the ES leg with and without the DFF−1.8pp proxy
(proxy NOT PIT — both versions reported).

**(7) Refutation conditions.** X5-K1: mean pairwise Spearman within placebo
band ⇒ no common era driver; tri-era clocks must be re-labeled
"per-symbol policy clocks" and every K1-type era-kill inherits the
instability annotation (families do NOT die from X-5 — their era VIEWS get
honest labels). X5-K2: flips cluster but residuals contradict own
differentials on ≥2 symbols ⇒ measurement/roll-rule suspicion (audit
escalation, not mechanism verdict). X5-K3: 6A leg invalid until k=5
measured ⇒ 5-symbol version reported, 6A excluded (never inferred).

**(8) Cost sensitivity.** None — no trading content at all; carry is a
structural input (H-G). Corrected fees cited for completeness only (§0.3).

**(9) Regime/era breaks.** The design IS the era-break test; 2022 USD
shock, 2025-26 differential collapse (6B/6A backwardation windows), and the
2025 BLS vintage break (irrelevant here) all annotated as strata.

**(10) Coverage/hole proof.** ES/NQ 66 rolls each 2010-2026; FX 27 rolls
each 2020-2026; 6A roll-rule caveat (§3); differentials NOT PIT (declared);
6E vintage fragility carried as the standing example of why statistic (iii)
is descriptive-only. No other holes.

**(11) Sources.** NQ_DEEP_v2 §3 (d3cf621c…); ES addendum §0.5/§11
(d18d5422…); 6B_DEEP_v2 §3 (bc8a1dc3…); 6A_DEEP_v2 §3.1-3.2 (76d32f1c…);
6J_DEEP_v2 §0/§3/§7 (ef95ad8d…); 6E_DEEP_v2 §4 (bf2a952d…); PLAYBOOKS §0
H-G row (7610ed3c…); DATACONTRACT §1.3 (df175a2d…).

---

## Cross-cutting NOT_RUN register (cross designs)

1. NQ full-era rebuild on the alias-recovered series — hard precondition for
   X-1 (NQ leg) and X-2 (NQ aggregates); inherited from the NQ addendum §9.
2. NQ OVN variance share by era; ES OVN volume share by year (recompute) —
   X-1 same-kind prerequisite cells.
3. FOMC-on-6J minute anatomy — NOT_RUN; X-2/X-3 run without the 6J FOMC leg.
4. Common-window release-minute re-measure (±5min convention) — NOT_RUN
   until the Step-1 descriptive pass; X-2 forbids conclusions from the
   heterogeneous committed ratios.
5. PIT-strict daily dollar/policy-rate series — NOT_RUN (latest-vintage /
   ALFRED year-end only; DXY absent; NO purchases). X-3 in-venue factor
   only; X-5 statistic (iii) descriptive-only.
6. 6A k=5 roll rule measurement (ERRATUM A7-DC-F3) — X-5 6A leg runs on
   declared-rule dates with the extrapolation tag, or is excluded.
7. Pooled placebo band — NOT_RUN until registered families run their
   mandatory control legs (X-4 harvest).
8. Surprise/consensus conditioning — NOT_RUN program-wide (H3); all cross
   designs condition on schedules + realized prices only.
9. Cross-symbol outcome data of any kind — none exists and none was used;
   no PASS is claimed for any consistency statement.

## Law compliance

- Outcome-blind: no return statistic of any conditioned/traded construction
  entered any design decision; the only numbers used are committed
  descriptive anatomy (volume/|ret| ratios, shares, spreads, correlations)
  cited to artifacts.
- [PROVISIONAL] on every threshold, window, tolerance and seed policy.
- No registration proposed, no GO recommended, no family killed by fiat —
  X-designs record CONSISTENCY verdicts that re-scope mechanism claims or
  label era views; registered identities remain governed by their own
  cycles, caps and owners.
- Writes confined to `hypo/cross/**` (this file, `cross_hypotheses.json`)
  and the dispatch handoff; no committed file touched; sibling outputs read
  only.

— End of CROSS_HYPOTHESES.md.
