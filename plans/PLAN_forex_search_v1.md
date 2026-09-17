# PLAN FOREX-SEARCH-V1 — bounded session-bounded strategy search on the TD majors (owner-relaxed acceptance)

> Status: `PLANNED_NOT_STARTED` (2026-09-17). Authority: explicit owner
> instruction 2026-09-17, verbatim: "mở cycle tìm kiếm strategy overfit tí
> xíu cũng được Cho stocks và forex". Frozen English reading (authoritative
> for gates): open a strategy-search cycle for forex; a MILD, BOUNDED amount
> of overfit is acceptable in the acceptance statistics. The relaxation is
> frozen in §3 and nowhere else. This plan is audited by fresh-context A7
> before registration. A P0/D2 close with zero scored cells is a valid
> result. Nothing in this plan is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          FOREX-SEARCH-V1
asset             forex
plan              plans/PLAN_forex_search_v1.md
branch            orca/forex-search-v1-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration
budget            3 scored cells max
go_phrase         GO FOREX SEARCH V1 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

`PROSPECTIVE-SHADOW-V1` remains independent and ACTIVE_LIGHT; this cycle
never reads its PnL, trades, marks or verdicts. STOCKS-SEARCH-V1 is a
sibling cycle under the same owner instruction; the two share NO budget, no
GO and no rescue path. The name FOREX-NG8 is deliberately NOT used and
remains burned (FOREX-INTRA-BIDASK-V1 / FX-FUTURES-FRONTIER-V1 closures:
their successor door is tied to an owner network path this cycle does not
provide and does not claim).

## 1. Question, in simple language

> On the five TD majors at the 16:00-NY daily clock, does ANY construction
> in a frozen, pre-enumerated grid of session-conditioned classes —
> divergent close-location pressure, fresh-extreme fade/confirm, opening-gap
> geometry, vol-regime-conditional drift, calendar-conditional drift —
> predict next-session open-to-close drift net of a conservative cost +
> financing ladder, under an acceptance battery whose overfit-sensitive
> statistics have been relaxed by a bounded owner grant?

Every family in this cycle holds EXACTLY ONE session (entry at bar t+1
open, exit at bar t+1 close). This is a construction LAW, not a preference:
it is the only way the FOREX-NG6-F4 / FOREX-NG7-F4 financing-authority
fail-closed class is answered honestly (see §4 F4).

## 2. Why this cycle is legal — reopening ancestry (audit item #2)

The forex frontier's standing closures, quoted and adjudicated:

- FOREX-NG6/NG7 (P0-F4 class): no citable financing band exists in the
  authorized evidence space; TD daily payloads are OHLC-only. NG7's family
  died on cost authority, NOT on price data. This cycle does NOT claim a
  new financing authority: it removes multi-session holds from the
  construction space entirely and charges a frozen conservative worst-night
  band on the single session (§4 F4) — the measured-beats-stated law (Q-8)
  is satisfied on its stated-conservative branch, and the dual-books gate
  runs degenerate-but-disclosed. A7 must rule this sufficient (audit
  item #1).
- FOREX-NG5 ("reopening needs a new evidenced information source per
  standing law") and the FOREX-NG1 note ("forex re-entry needs materially
  new information sources"): NO new information source is claimed here —
  the same single-vintage TD archive NG7 pinned is re-pinned. Where a
  predecessor's reopening clause demands a new source, the owner
  instruction of 2026-09-17 is exercised as the SUPERIOR authority
  (AGENTS.md authority order 1) to reopen with a named changed killer
  (§3). This override is DISCLOSED, not silently absorbed; A7 must
  adjudicate its faithfulness (audit item #2).
- Cross-plane analogy (STOCKS-NG6/CRYPTO-NG4 "owner plan naming a changed
  killer" branches): analogy-only context, NOT an operative reopening
  authority for the forex plane; the sole operative authority is the
  disclosed owner-instruction override above.
- FOREX-INTRA-BIDASK-V1 / FX-FUTURES-FRONTIER-V1 (transport-blocked):
  untouched; this cycle performs ZERO network acquisition of Dukascopy/CME
  data and adjudicates nothing about those estates.
- DATA-EDGE-UNLOCK-V1 Lane F: zero broker-grade cost bytes exist (third
  census). This cycle therefore runs stated-conservative costs (§4 F4),
  never measured-broker claims.

Ancestry facts that must not travel silently: FOREX-NG5's kills included
momentum rho 0.230/0.353 (V5) — the relaxed floor re-admits the 0.230
class and NOT the 0.353 class; NG4's clock rho 0.888–0.891 makes the
clock-only control existential on this grid, not decorative.

## 3. Owner-grant relaxation ledger (frozen BEFORE any measurement)

The owner grant relaxes EXACTLY these axes, for THIS program only:

```text
axis                        standing value              this program
-------------------------------------------------------------------------
R0 ancestry veto floor      per-leg AND pooled          <= 0.30 (owner)
                            |rho| <= 0.20
DSR deflation set N         program-cumulative ~260     frozen grid size
                            (P-9)                       (<= 80, §5)
DSR alpha                   0.05                        0.10
search breadth              1 family + 1 neighbour      <= 80 enumerated
                                                        configurations
```

Boundedness argument, frozen: 0.30 is a 50% relative relaxation of the
standing floor, chosen before any this-cycle rho exists; it re-admits the
FOREX-NG5 0.230 class and the STOCKS-NG6 0.201–0.260 class (public
committed history) and does NOT re-admit the NG5 0.353 momentum-kill
class. alpha 0.10 is one notch. Every result artifact prints BOTH the
standing and relaxed values.

NOT relaxed (mission invariant, non-negotiable): data identity and the P-13
staging chain, cost and financing bands with stress-2.0 primary, R1 net
expectancy > 0, R3/R4/R5/R6 control rules, USD-drift gate at 0.20,
per-leg-AND-pooled rho measurement law, fold structure, population floors,
fired-census weekday floor, serial-clustering census, dual-books sign
invariance, reproduction, trial accounting, S1 seal, GO-at-gate. Being
vetoed at 0.30 is not grounds to move the bar again in-cycle; a further
relaxation is a NEW owner instruction and a NEW cycle.

### 3b. Owner amendment 2026-09-17 #2 — D2 SKIPPED (verbatim intent:
"chay tu dau toi GO cua toi, nhung khong chay buoc D2" — run from the
start to the owner GO, but do not run the D2 step)

Owner authority (AGENTS.md order 1) instructs the chain to run from the
start to the owner GO gate with D2 skipped. Frozen effect: the D2 phase is
NOT dispatched in this cycle; the R0 ancestry battery is therefore NOT
MEASURED (NOT_RUN — never an inferred PASS); the §9 chain's D2 row reads
SKIPPED. §5 selection tier (i) is replaced by the P0 fired-population
census and tier (ii) loses its W_c term (both non-performance,
outcome-blind properties retained); the fired census and feasibility
floors are measured at P0 as a pure data census (fired counts only — no
candidate returns, no PnL, no PF); P-20 books-distinct at S is UNCHANGED.
Terminal survivor outcome names and §10 language carry `R0_NOT_RUN`
alongside the standing 0.20/0.30 disclosure. This amendment is an
owner-authority act recorded in the registry; it widens nothing by Lead
initiative and everything skipped is printed on every result.



## 4. Source authority and P0 gates

Scored source: TD 1day OHLC spot majors, single vintage, EXCLUSIVELY the
P-13 staging archives (`~/staging_backups/cleanup_2026-09-12/`, digests vs
`SHA256SUMS.txt`; EURUSD `01cb862b…` 5,000 rows 2007-10-18..2026-09-12;
GBPUSD `e3e4c519…`, USDCAD `4b988c44…`, AUDUSD `097cfe59…`, NZDUSD
`7dff3299…`, 5,000 rows each, spans 2007/2008..2026-09-10; ng1 copies
byte-identical to v9 copies). XAUUSD EXCLUDED (cost authority BLOCKED,
FOREX-NG6 P0-F4). No Dukascopy, no CME, and no network acquisition of FX
data beyond the F1(iii) bounded TD re-pull cross-check under its
fail-closed contract.

```text
F1 STAGING CHAIN (NG7 A4 5-step, all fail-closed)  (i) archive sha256
                           verification; (ii) structural census (rows,
                           span, OHLC integrity, 16:00-NY stamp
                           convention); (iii) fresh TD re-pull cross-check
                           on a bounded sample — byte-identity or honest
                           divergence disclosure, fail-closed re-pull
                           contract frozen BEFORE the pull (if the vendor
                           no longer serves byte-identical history, the
                           archive vintage is THE authority and divergence
                           is recorded, never silently merged); (iv)
                           manifest pin into research/control/
                           forex_search_v1_run/; (v) intersecting 5-leg
                           calendar census (holidays, missing bars — no
                           ffill).
F2 ENTITLEMENT + TERMS     owner TD entitlement (V8/V9/NG5/NG7 precedent);
                           key environment-only, never echoed.
F3 CLOCK + EXECUTION       one frozen 16:00-NY daily decision clock; state
                           on completed bar t; entry at bar t+1 open, exit
                           at bar t+1 close — SINGLE-BAR HOLD LAW (§1).
                           OPEN-GAP EXCEPTION (frozen HERE, before
                           scoring): the OPEN-GAP state is formed from
                           close(t) and open(t+1) — knowable exactly at
                           bar t+1's open — and its forced fill AT that
                           same open(t+1) is the ONE declared exception to
                           the no-same-bar-signal-fill rule (no look-ahead:
                           the fill price IS the first bookable price);
                           exit mapping frozen before scoring: any exit
                           condition knowable at a bar close executes at
                           the next bar's open under the same convention
                           (V7 F-A7-PL-1 lookahead class pre-empted); no
                           same-bar signal-fill; the open-vs-close fill
                           choice frozen BEFORE scoring (V6/V8 law).
F4 COSTS + FINANCING       costs: conservative 1.5 bps/fill floor band
                           (TD is a vendor; where a broker-grade band is
                           unmeasurable the floor + STRESS TIER 2.0
                           PRIMARY carries the gate; V6 razor class 3.0 bps
                           hurdle named; break-even bps per round trip
                           reported per arm). FINANCING (this cycle's
                           resolution of the NG6/NG7 F4 class, audit item
                           #1): every trade holds exactly one session and
                           is charged exactly one conservative worst-night
                           band of 1.7 bps (derivation: NG7-A4's committed
                           illustration "~5.1 bps over 3 nights" for
                           NZD-USD; 5.1/3 = 1.7 — caveats DISCLOSED: a
                           3-night cumulative average does NOT bound the
                           single worst night, and NZD-USD-worst is
                           generalized to all five legs without a per-leg
                           differential census, none being derivable from
                           OHLC-only TD; the D1 manifest prints source
                           bytes, arithmetic and these caveats verbatim),
                           marked STATED-CONSERVATIVE — charged uniformly
                           across legs regardless of sign, so no leg can
                           benefit from an assumed favourable differential;
                           stress 2.0 applies to costs AND financing;
                           operative stress worst case per round trip =
                           2 x 1.5 x 2.0 + 1.7 x 2.0 = 9.4 bps. The
                           dual-books gate runs with the financed book =
                           price book + this uniform charge: sign
                           inversion between them fails the arm,
                           fail-closed. NO multi-session hold exists in
                           the grid, so no silent-zero financing book can
                           arise.
F5 FOLDS (Q-6)             three chronological folds frozen BEFORE any D2
                           diagnostic; RECENT-window fired-rate floor
                           measured at P2 (form: fired rate [0.02, 0.10]
                           bars/leg/day -> 25–125 round trips/yr across 5
                           legs; the recent-window measured value replaces
                           the form before selection); fail-closed if
                           unpopulated; >= 30 fired decisions/fold pooled.
F6 REPRODUCIBILITY         census, manifests, digests, clock contract,
                           folds, frozen search-space manifest committed
                           under research/control/forex_search_v1_run/;
                           detached rerun reproduces.
F7 CONTROL SOURCE AUTHORITY NY Fed rates (SOFR/EFFR/BGCR/TGCR/OBFR) and
                           OFR series are D2 funding/liquidity CONTROLS
                           ONLY — never an FX signal (A3 identity ruling
                           re-inherited); NY Fed = RETRIEVAL_TIME_ONLY; OFR
                           = RETROSPECTIVE_ONLY; no forward-fill across
                           holiday/release gaps; no retrieval-time-only
                           evidence claims historical PIT.
```

P0 is source engineering and census only. No candidate PnL/PF/Sharpe/
drawdown/survivors/S1 evidence.

## 5. D1 — the frozen search-space contract (this cycle's core artifact)

Before any D2 diagnostic, this cycle commits a hashed
`search_space_manifest.json` enumerating EVERY configuration:

```text
grid cap          <= 80 configurations total
config ID         FSS-<FAMILY>-<PARAMKEY>, stable, lexicographic
families (5)      with FROZEN parameter sub-grids, all parameters declared
                  from construction logic (Q-12), never tuned:
 1 CLV-DIVERGENCE fresh K-bar close extreme + divergent 20-bar CLV
                  pressure slope, K in {10, 20, 60} x slope window
                  k in {5, 10} (NG7 anchor class, grid-extended)
 2 EXTREME-FADE   fresh K-bar extreme faded, K in {10, 20, 60} — the
                  causal complement direction
 3 OPEN-GAP       opening-gap fade and confirm vs prior close, gap size
                  threshold at {25th, 50th, 75th} percentile of the
                  trailing 252-bar SIGNED-gap distribution (gap_t =
                  open_t − close_{t−1}, SIGNED; the absolute-value
                  reading is forbidden)
 4 VOL-DRIFT      realized-vol tercile-conditional 1-session momentum and
                  reversal, lookback {21, 63}; tercile formation CAUSAL,
                  pinned: estimator = close-to-close log-return SAMPLE
                  std (ddof=1) over the trailing lookback L; boundaries
                  = 1/3 and 2/3 quantiles (linear interpolation) of the
                  TRAILING 252-bar window ending at and including bar t,
                  refreshed daily, same-bar assignment — NEVER
                  full-sample (look-ahead class)
 5 CLOCK-COND     day-of-week / month-position conditional drift,
                  ENUMERATED: 5 weekday states + 2 month-position states
                  (first-half / second-half of month), each in both
                  directions = 14 configurations (grid total 19 + 14 =
                  33 <= 80; exact count declared so the frozen DSR N is
                  unambiguous at freeze time); declared EXPECTED-TO-DIE
                  at R5; included so the search is honest about what the
                  clock explains
direction         the D1 manifest FREEZES each configuration's sign from
                  the mechanism statement (NG7 F3b pattern); R1
                  adjudicates the frozen sign and never selects it;
                  where the mechanism admits both directions they are
                  enumerated as distinct configurations inside the cap
holds             ALL configurations single-session (§1 law)
```

Selection inside the grid (frozen BEFORE D2, outcome-blind; every
statistic consumed below is a D2 ancestry/census measurement, never a
performance statistic). Definitions, pinned: for each configuration c,
W_c = max over ALL frozen R0 shadows s of max( max over the five legs L
of |rho_L(c, s)|, |rho_pooled(c, s)| ) on the P-12 daily
position-series x log-return representation (the R0 law's per-leg AND
pooled requirement; per-fold rhos computed and REPORTED as disclosure
only, never gating). Family tier value T_F = min over the family's
D2-surviving configurations of W_c (the family's best-case distance from
lethal ancestry). Ranking, applied mechanically: (i) families DESCENDING by P0 fired-population census (family-level sum of fired decisions over the most recent fold; AMENDED per §3b — D2 skipped, T_F/W_c not computed); ties break by lexicographic family name; (ii) within a family, configurations DESCENDING by P0 fired-population census (config-level), tie-break lexicographic config ID (AMENDED per §3b); (iii) selection is FAMILY-STRATIFIED
round-robin over the tier-ordered families — one configuration per
family per round, at most 2 scored cells per family, until 3 cells are
filled. P-20 books-distinct at S: a candidate whose pooled |rho| vs any
higher-ranked already-selected candidate exceeds 0.98 is SELF-SUBSUMED,
skipped, and the next candidate by the frozen order is taken; an
unmeasurable pairwise rho makes the slot NOT_ADJUDICABLE, fail-closed —
never an inferred PASS. The corrected order carries VERBATIM into the D1
manifest freeze. NO return, expectancy, PF, Sharpe or any performance
statistic may be computed for ANY configuration before the S freeze (the
§7 D2 ancestry rho, feasibility floors and fired censuses are NON-SCORED
diagnostics explicitly carved out of this ban); a performance-based
narrowing at any point consumes scored cells for everything narrowed-on
and is a BLOCKED_METHOD_CONTRACT incident.

The hashed manifest is REQUIRED to contain, fail-closed (a missing field
is a D1 freeze failure): per-configuration full construction definitions
incl. sign as frozen from the mechanism statement (§5 direction rule);
the VOL-DRIFT tercile formation rule (§5); the OPEN-GAP state timing
exception (§4 F3); each family's CTL-COMPLEMENT and trend-only (R4) book
definitions; the per-state per-fold population floor value (§6 R2); the
warmup rule (§8); the CLOCK-COND enumeration with exact count (the
frozen DSR N must be unambiguous at freeze time); and the §4 F4
financing derivation printed verbatim with its caveats.

## 6. Mandatory controls and killers

```text
CTL-COMPLEMENT        each family's confirmed/non-divergent complement
                      (declared ex ante per family in the manifest)
CLOCK-ONLY            rotation on the same daily clock, no signal input,
                      plus a FIRED CENSUS (DOW/month/release-day overlay)
                      — existential on this grid (NG4 0.888–0.891)
VOL-REGIME            vol-tercile shadow + fold split (V4/V8 lineage)
MOM20 / MOM63         momentum shadows (V5 precedent kills 0.230/0.353)
REV1 / REV5           short-horizon reversal shadows (reversal-selected
                      states: large negative rho vs momentum is killed
                      ancestry, never novelty evidence)
USD-DRIFT GATE        |corr(candidate daily PnL, equal-weighted USD basket
                      from the same five legs)| <= 0.20, measured per-leg
                      AND pooled (V6/V7 precedent); pooled-only is NOT_RUN,
                      never PASS
DGS10-LEVEL           the program's most lethal control lineage (#14/#15)
REAL-YIELD / CURVE    DFII10/DFII5, DGS2/DGS10 slope, control-only
CARRY                 policy-differential shadow on the position series
SPY-RISK-OFF          SPY-drawdown state shadow
C-PIT-MUTATION        one-bar-earlier recomputation changes/refuses the
                      book on every fired decision
C-NULL-VALIDITY       autocorrelation + population of every null reported
                      before any control may kill (Q-11)
```

Scoping rule (A4, binding): a control state not knowable at decision time
is RETROSPECTIVE_ONLY — it may KILL but may NEVER RESCUE.

Ordered kill rules (first binding kills; all NET on the conservatively-
financed book, stress 2.0 PRIMARY):

```text
R0  pre-score ancestry veto   per-leg AND pooled |rho| > 0.30
                              (owner-relaxed, §3) vs the frozen shadow
                              inventory on the P-12 representation
                              (daily position series x log returns); BOTH
                              per-leg and pooled measurements required —
                              pooled-only DILUTES and is NOT accepted as
                              PASS evidence; a pooled-only run is NOT_RUN
                              -> configuration dies pre-score; the 0.20
                              standing value printed alongside
R1  expectancy                fin-adj net expectancy <= 0 at stress 2.0
                              -> REJECT_ALL
R2  robustness                PF < 1.10 OR fold positivity fails OR the
                              per-state per-fold population floor fails —
                              floor VALUE frozen HERE: >= 10 fired
                              decisions per state per fold, pinned in the
                              D1 hashed manifest BEFORE any D2 measurement
                              (S2 class)
R3  mechanism specificity     CTL-COMPLEMENT out-earns or matches the
                              candidate (tie kills; self-failing complement
                              still kills — V15 precedent; degenerate
                              sub-floor complement is R3 NOT_RUN both ways,
                              never an inferred PASS)
R4  trend/vol reduction       VOL-REGIME or the family's trend-only book
                              (declared per family in the D1 manifest:
                              the conditioning-variable-only book — state
                              variable traded WITHOUT the trigger/
                              direction component) reproduces >= 0.5x
                              same-sign >= 2/3 folds -> REJECT; where a
                              family admits no such analog, R4 is
                              NOT_ADJUDICABLE for that family, disclosed,
                              never an inferred PASS
R5  clock geometry            CLOCK-ONLY out-earns, OR the FIRED CENSUS
                              breaches the pre-pinned max weekday share
                              floor of 0.35 (frozen HERE before any census
                              is read; breach => the state IS a calendar
                              condition, NG4 dead-ancestry class)
                              -> REJECT
R6  usd/macro reduction       USD-drift gate fail (per-leg AND pooled, both
                              vs the 0.20 bar), or DGS10/real-yield/curve/
                              carry/SPY shadow reproduces the candidate
                              (>= 0.5x same-sign) -> REJECT
serial-clustering             consecutive fired bars overlap states:
                              trade-independence DECLARED NOT ASSUMED at
                              the P0 manifest freeze; PF/trade-count
                              reporting carries the clustering census
dual-books                    price-only book inverts sign vs the
                              conservatively-financed book on any arm ->
                              that arm fails, fail-closed (financed book =
                              price book + §4 F4 uniform charge)
```

Plus the frozen forex Stage-A gates on any survivor (UNCHANGED, §3):
fold-positive-share, concentration, MDD, stress margin, drop-one,
per-period series persisted (P-11) for DSR with N = frozen grid size at
alpha 0.10 (owner-relaxed) AND program-cumulative ~260 at alpha 0.05
(reported, not gating). P-20 books-distinct at S: a scored candidate
whose position-series |rho| vs any higher-ranked already-selected
candidate exceeds 0.98 is SELF-SUBSUMED, skipped, next-in-order taken;
unmeasurable = NOT_ADJUDICABLE, fail-closed. PBO disposition, prewritten
for the <=3-cell regime (the frozen V17/FOREX-NG1 alternative, commit
d0992d17df8e2dfde57c9a0806a5798f14021a4f — Lead Bash-verifies the commit
at registration; CRYPTO-V14/FOREX-FREE-V8 lineage): CSCV PBO requires >= 8
performance-evaluated configurations — §5's freeze plus this cycle's
3-cell budget make that unreachable BY CONSTRUCTION, so PBO is NOT_RUN,
declared fail-closed and printed on every result; a survivor with PBO
NOT_RUN is bookable ONLY with the NOT_RUN label carried into the
terminal outcome name and the §10 result language; no performance may be
computed for PBO outside the <=3 scored cells (a §5 tripwire).

## 7. D2 ancestry and feasibility gate (non-scored)

D2 measures, on the frozen P-12 representation, for EVERY grid
configuration: the R0 inventory (relaxed 0.30 floor, per-leg AND pooled,
against the hashed shadow list committed BEFORE any rho — P-12/A7-F2 law),
feasibility floors (F4/F5 forms), the fired census, and the funding/
liquidity CONTROL set under their RETRIEVAL_TIME_ONLY / RETROSPECTIVE_ONLY
classes. NO scored outcome is computed at D2. If fewer than one
configuration survives: selection empty -> close at 0/3.

## 8. Trading, costs and risk contract

```text
decision        frozen 16:00-NY daily clock; warmup = max(60, the
                family's LARGEST state-formation window INCLUDING
                auxiliary trailing distributions): VOL-DRIFT = max(L,
                252) = 252 and OPEN-GAP = 252 — tercile boundaries and
                gap percentiles each consume a trailing 252-bar window —
                so first decision bar 253 for both; CLV-DIVERGENCE,
                EXTREME-FADE, CLOCK-COND = 60 (first decision bar 61);
                a state that cannot be formed from COMPLETE windows is
                NOT FIRED — fail-closed; no expanding-window or
                partial-window convention exists anywhere in this cycle;
                pinned per family in the D1 manifest
entry/exit      bar t+1 open -> bar t+1 close (single session, §1 law);
                force-flat at fold boundary by construction
universe        five TD majors (EURUSD, GBPUSD, USDCAD, AUDUSD, NZDUSD);
                per-leg long/short by state; no XAU; no cross-pair input
books           conservatively-financed + price-only dual books; sign must
                not invert (§6 dual-books)
costs           1.5 bps/fill floor + 1.7 bps/night financing, both stress
                2.0 PRIMARY, charged once per fill / once per session;
                break-even bps per round trip per arm
claims          D2 eligible = allowed to be tested, never profitable
```

## 9. Execution phases and ownership

```text
M0  methodology golden suite (G1–G10 + G4N = 11/11, NG5/NG6/NG7 lineage)
    re-inherited BYTE-EXACT + the dual-books degenerate fixture (the
    uniform-charge financed book must not invert sign vs price-only on any
    fixture arm) — re-run under research/control/forex_search_v1_run/m0/;
    PASS required before D1
P0  F1–F7 staging chain + authority + census gates
D1  search-space manifest freeze (outcome-blind; hashed; the manifest IS
    this cycle's A2-equivalent dossier)
D2  R0-relaxed ancestry + feasibility + fired census + funding-control
    measurement for EVERY configuration (non-scored)
S   selection by frozen construction-based order + exact arm/data/fold/
    config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context independent prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types `GO FOREX SEARCH V1 SCORED EXECUTION` at this cycle's own
    gate; early/paraphrased GO dies unconsumed (P-8)
E   at most 3 scored cells under the machine-wide heavy lock
R   detached reproduction from committed artifacts
T   terminal audit and close
```

All delegated lanes write `zcode_orch_v3_handoff@1` JSON to their exact
dispatch path. Lanes never merge, rebase, push, edit registries/ledgers or
read other lanes' outcomes.

## 10. Trial accounting and result language

Observed and published denominators counted separately; every computed
cell consumes an observed slot even if publication fails; unused slots are
never reassigned and never force-filled. The frozen grid size is itself
published as the search's multiple-testing universe. Forex denominators
currently 48/48; program 257/260 (P-9) — this cycle starts at budget 0/3.
Any result language must carry the §3 relaxation disclosure verbatim:
"accepted under owner-relaxed acceptance battery (R0 0.30 / DSR alpha 0.10
at N = grid) | PBO NOT_RUN fail-closed (<=3 cells, d0992d17 class) | R0 NOT_RUN (D2 skipped by owner amendment §3b)" AND
the §4 F4 financing disclosure: "financing =
stated-conservative nightly-average extrapolation (1.7 bps; worst single
night may exceed it; no per-leg differential census exists — OHLC-only
source)".

## 11. Prewritten terminal outcomes

```text
FOREX_SEARCH_V1_BLOCKED_METHOD_CONTRACT
FOREX_SEARCH_V1_BLOCKED_SOURCE_OR_SCHEMA
FOREX_SEARCH_V1_BLOCKED_DATA_OR_SELECTION
FOREX_SEARCH_V1_BLOCKED_PRELAUNCH
FOREX_SEARCH_V1_REJECT_ALL
FOREX_SEARCH_V1_SURVIVORS_UNDER_RELAXED_BATTERY_R0_NOT_RUN_PBO_NOT_RUN (only if
    Stage-A passes; carries the §3 + §4 F4 disclosures AND the PBO
    NOT_RUN fail-closed label; never a profitability claim)
FOREX_SEARCH_V1_INCOMPLETE_NOT_PROMOTABLE
FOREX_SEARCH_V1_TECHABORT_PRESERVED
```

A correct early close is success of governance. No predeclared survivor.

## 12. Boundaries

- Keyless-or-entitled sources only; no signup, no purchase; keys never
  echoed. No TWS, no IBKR, no XAU substitution (GLD/GC/MGC/composite
  forbidden). No Dukascopy or CME network acquisition; those estates stay
  adjudicated-closed pending the owner network path.
- SOFR/EFFR/BGCR/TGCR/OBFR/OFR are USD funding/reference rates — never an
  FX signal; D2 controls only, under their measured PIT classes.
- No S1 access; no paper/testnet/live orders; no deployment.
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`; `CYCLE_REGISTRY.json` changes only
  through `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- No budget/GO/rescue sharing with STOCKS-SEARCH-V1 or PROSPECTIVE-SHADOW-V1.
- The §3 relaxation may not be widened in-cycle.

## 13. Immediate actions

```text
1. Commit this plan by exact pathspec.
2. Independent fresh-context adversarial plan audit (A7) — audit items,
   numbered: (1) the §4 F4 stated-conservative financing resolution of
   the NG6/NG7 fail-closed class; (2) the §2 reopening override; (3)
   the §3 boundedness of "tí xíu"; (4) the §5 grid and outcome-blind
   selection; (5) the §6 battery integrity under R0 0.30.
3. Remediate every valid HIGH/CRITICAL; re-audit with a NEW fresh-context
   A7 if the verdict was REFUSED.
4. Register FOREX-SEARCH-V1 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree; run M0; PASS required before D1.
6. Stop at the scored prelaunch gate and wait for the exact owner GO.
```
