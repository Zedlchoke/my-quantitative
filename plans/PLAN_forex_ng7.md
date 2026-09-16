# PLAN FOREX-NG7 — swing-extreme absorption via divergent close-location pressure

> Status: `PLANNED_NOT_STARTED` (2026-09-16). Authority: explicit owner
> directive 2026-09-16 (three-cycle program; this cycle: ONE materially new
> FX mechanism; NY Fed/OFR at D2 as funding/liquidity controls ONLY; budget
> max 3 scored cells / 1 family; plan audited by fresh-context A7 before
> registration). Outcome-blind dossier evidence is committed under
> `research/control/ng6_ng7_ng4_dossiers_2026-09/` (A2 proposal
> `72284c8f…`, A3 NY Fed/OFR source contract `1e05d07e…`, A4 hostile
> critique `52f735e4…`; SHA256SUMS.txt pinned). This cycle is fully
> independent of XAUUSD/IBKR; FOREX-NG6R1 stays
> `PROBE_PAUSED_NOT_RUN_TWS_UNAVAILABLE` and is untouched. A P0/D2 close
> with zero scored cells is a valid result. Nothing here is evidence of
> profitability.

## 0. Cycle identity

```text
cycle_id          FOREX-NG7
asset             forex
plan              plans/PLAN_forex_ng7.md
branch            orca/forex-ng7-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/forex-ng7/integration
budget            3 scored cells max / 1 family max
go_phrase         GO FOREX NG7 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

Family name (frozen): `SWING-EXTREME ABSORPTION (DIVERGENT CLV)` — the
daily failed-breakout spring/upthrust class. `PROSPECTIVE-SHADOW-V1`
untouched. STOCKS-NG6 and CRYPTO-NG4 share no budget, no GO and no rescue
path with this cycle.

## 1. Question, in simple language

Stop-loss and stop-entry orders clustered beyond a recent swing extreme are
price-inelastic — when price prints a fresh 20-bar extreme those orders
must execute there, and patient participants can absorb them. The
fingerprint is a disagreement: a fresh extreme WITHOUT confirming
close-location pressure. We ask one narrow question:

> On the five TD majors at the 16:00-NY daily clock, does a fresh 20-bar
> close extreme with an opposite-direction 20-bar CLV accumulation slope
> predict next-bar drift toward the absorption side — beyond what
> momentum, short-horizon reversal, trend/volatility state, the weekday/
> release clock, carry and the USD state already explain?

Anchor (frozen): state fires on completed bar t; entry at bar t+1's first
bookable price under the frozen 16:00-NY convention; exit at fixed 3-bar
hold, OR first opposite absorption state, OR first confirmed-extreme-against-
position bar, whichever first (1–3 bar holds by construction — the
FOREX-NG5 E1 weekly-financing-ceiling class avoided).

## 2. Why this is a new cycle — and its honest ancestry risk

- Zero ledger ancestry on this observable: no session windows, no range
  breakout, no rate differential, no carry input, no vol gate, no calendar/
  release/reaction structure, no positioning census, no CPI/vintage, no XAU
  leg, no cross-pair leader input (dossier `distinct_by_design_vs_every_
  closed_ancestor` enumerates all twelve closed frontiers). Novelty is a
  proposal claim until the D2 rho battery passes.
- A4 rulings adopted verbatim: (1) the state is REVERSAL-BY-CONSTRUCTION —
  trading against fresh 20-bar extremes — so BINDING momentum AND reversal
  rho controls are frozen (§6), with the FOREX-NG5 V5 kills (0.230/0.353)
  as the named precedent; large NEGATIVE rho vs momentum is still the killed
  ancestry, not evidence of novelty. (2) This proposal sits on NG4's LETHAL
  daily grid (measured clock rho 0.888–0.891 there; P-24 has fired three
  times across planes) — the clock-only shadow is existential, not
  decorative. (3) The mechanism cites stop clusters at bar H/L while the
  observable anchors on CLOSE extremes — a fingerprint mismatch disclosed
  and measured at D2 (the close-extreme form is what is scored; no H/L
  retrofit in-cycle).
- Fingerprint honesty: spring/upthrust is a named TA class; no ledger row
  has measured this daily divergent-pressure state on this authority.

## 3. M0 — methodology contract gate (before D1)

The shared D2-methodology golden suite (G1–G10 + G4N = 11/11; NG5/NG6
lineage, re-inherited BYTE-EXACT and re-run in this cycle's worktree, under
`research/control/forex_ng7_run/m0/`) plus the dual-books ordering fixture:
the price-only book must NOT invert sign vs the financed book on any arm,
adjudicated per the NG6 M0 G1–G10 ordering before family merge. M0 PASS
required before D1 dispatch; else `BLOCKED_METHOD_CONTRACT`, budget 0/3.

## 4. Source authority and P0 gates

Scored source: TD 1day OHLC spot majors. The A3/A4 staging chain is
BINDING — the five majors survive ONLY inside the P-13 archives (single
vintage; `~/staging_backups/cleanup_2026-09-12/`, digests verified against
`SHA256SUMS.txt`; EURUSD `01cb862b…` 5,000 rows 2007-10-18..2026-09-12;
GBPUSD `e3e4c519…`, USDCAD `4b988c44…`, AUDUSD `097cfe59…`, NZDUSD
`7dff3299…`, 5,000 rows each, spans 2007/2008..2026-09-10; ng1 copies
byte-identical to v9 copies). XAUUSD is EXCLUDED (cost authority BLOCKED,
FOREX-NG6 P0-F4; the NG6R1 construction-B preregistration stays binding and
untouched).

```text
F1 STAGING CHAIN (A4 5-step, all fail-closed)  (i) archive + member
                           sha256 verification vs SHA256SUMS.txt; (ii)
                           structural census (rows, span, OHLC integrity,
                           16:00-NY stamp convention); (iii) a fresh TD
                           re-pull cross-check on a bounded sample —
                           byte-identity or honest divergence disclosure;
                           fail-closed re-pull contract frozen BEFORE the
                           pull (if the vendor no longer serves byte-
                           identical history, the archive vintage is
                           declared THE authority for this cycle and the
                           divergence is recorded, never silently merged);
                           (iv) manifest pin into research/control/
                           forex_ng7_run/; (v) intersecting 5-leg calendar
                           census (holidays, missing bars — no ffill).
F2 ENTITLEMENT + TERMS     owner TD entitlement (V8/V9/NG5 precedent);
                           key environment-only, never echoed.
F3 CLOCK + EXECUTION       one frozen 16:00-NY daily decision clock;
                           next-bar fill at the first bookable price; the
                           open-vs-close fill choice is frozen BEFORE
                           scoring (V6/V8 execution-freeze law); no
                           same-bar signal-fill.
F4 COSTS                   A4 contract adopted: conservative 1.5 bps/fill
                           FLOOR band pending the P0-measured band (measured
                           beats stated, Q-8; the exact band is pinned at
                           P0 from the authorized evidence space — TD is a
                           vendor, so where a broker-grade band is
                           unmeasurable the 1.5 bps floor + STRESS TIER 2.0
                           PRIMARY carries the gate, with the break-even
                           bps per round trip reported per arm; V6 razor
                           class 3.0 bps hurdle named); financing:
                           1–3 bar holds only; NZD-USD worst-differential
                           exposure bounded by hold length and adjudicated
                           per arm x leg x fold BEFORE merge (A4: ~5.1 bps
                           over 3 nights can flip a sign vs a 3.0 bps
                           hurdle).
F5 FOLDS (Q-6)             three chronological folds frozen BEFORE any D2
                           diagnostic; RECENT-window trigger-rate floor
                           measured at A9/P2 (A4 form: trigger rate
                           [0.02, 0.10] bars/leg/day -> 25–125 round trips/
                           yr across 5 legs; the recent-window measured
                           value replaces the form before selection);
                           fail-closed if unpopulated.
F6 REPRODUCIBILITY         census, manifests, digests, clock contract,
                           folds committed under research/control/
                           forex_ng7_run/; detached rerun reproduces.
F7 CONTROL SOURCE AUTHORITY NY Fed rates (SOFR/EFFR/BGCR/TGCR/OBFR) and
                           OFR series are D2 funding/liquidity CONTROLS
                           ONLY — NEVER an FX signal (A3 identity ruling).
                           Classes bind: NY Fed = RETRIEVAL_TIME_ONLY (no
                           per-row publication timestamps; single-day T+1
                           bracket measured); OFR = RETROSPECTIVE_ONLY
                           ([date, value] wire). No forward-fill across
                           holiday/release gaps anywhere. NY Fed /get/
                           time-range channel measured HTTP 400 (P-7:
                           /last/ channel only) — historical depth in hand
                           is 10 rows/rate; deeper history only via a
                           future evidenced acquisition.
```

P0 is source engineering and census only. No candidate PnL/PF/Sharpe/
drawdown/survivors/S1 evidence.

## 5. D1 outcome-blind proposal contract

The committed A2 dossier (sha `72284c8f…`) is BINDING, frozen before any
return exists. At most THREE constructions enter D2:

```text
1 anchor        FNG7-A2-P1-ABSORB: per leg, CLV_t = ((C-L)-(H-C))/(H-L);
                pressure P_t = sum CLV over trailing 20 completed bars;
                BULLISH absorption = fresh 20-bar close LOW with pressure
                slope (P_t vs P_{t-5}) NOT confirming the downside
                (divergent) -> LONG; mirror for HIGH -> SHORT; warmup 60
                bars; per-leg state, no cross-pair input.
1 neighbour     FNG7-A2-P1-NEIGH-K10: identical with pressure-slope window
                k=10 (slower confirmation); declared outcome-blind;
                self-subsumption |rho| <= 0.98 vs anchor (P-20).
1 complement control book (non-scored) — CONFIRMED extremes, §6.
```

Both directions are economically arguable ex ante; sign carried by R1.

## 6. Mandatory controls and killers

```text
CTL-EXTREMEONLY   CONFIRMED extremes (fresh 20-bar extreme + CONFIRMING
                  5-bar slope) traded with the extreme — the causal/
                  placebo complement; null-validity adjudication rule
                  (Q-11) frozen: valid null requires identical
                  representation/cost/stress semantics with floors frozen
                  at P0; KILL iff complement >= anchor (tie kills); a
                  self-failing complement still kills (V15 precedent); a
                  degenerate complement (sub-floor population) is R3
                  NOT_RUN in both directions, never an inferred PASS
CTL-TRENDONLY     pressure-slope-only book (no extreme condition)
CLOCK-ONLY        rotation on the same daily clock, no signal input,
                  plus a fresh-extreme FIRING CENSUS (DOW/month/release-
                  day overlay) — existential on this grid (NG4 0.888–0.891)
VOL-REGIME        vol-tercile shadow + fold split (V4/V8 lineage)
MOM20 / MOM63     momentum shadows on the same grid (V5 precedent kills
                  0.230/0.353)
REV1 / REV5       short-horizon reversal shadows (the state IS reversal-
                  selected; large negative rho vs momentum is the killed
                  ancestry, never novelty evidence)
USD-DRIFT GATE    |corr(anchor daily PnL, equal-weighted USD basket return
                  built from the same five legs)| <= 0.20 (V6/V7 precedent)
DGS10-LEVEL       the program's most lethal control lineage (#14/#15)
REAL-YIELD        DFII10/DFII5 granted set, control-only
CURVE-SHAPE       DGS2/DGS10 slope, control-only
CARRY             policy-differential shadow on the position series
SPY-RISK-OFF      SPY-drawdown state shadow
```

Scoping rule (A4, binding): a control state not knowable at decision time
is RETROSPECTIVE_ONLY — it may KILL (a family whose earnings it explains
is dead regardless of knowability) but may NEVER RESCUE (it cannot be cited
to make the anchor look better, and RETROSPECTIVE-controlled conditioning
never enters a scored feature).

Ordered kill rules (first binding kills; all NET, financed book, stress
2.0 PRIMARY):

```text
R0  pre-score ancestry veto   pooled |rho| > 0.20 vs the frozen shadow
                              inventory on the P-12 representation
                              (fng7_a2_p1_daily16NY_v1: pooled daily
                              position series x log returns per leg)
                              -> dies pre-score
R1  expectancy                fin-adj net expectancy <= 0 at stress 2.0
R2  robustness                PF < 1.10 OR fold positivity fails OR fold-
                              population sub-gate fails
R3  mechanism specificity     CTL-EXTREMEONLY out-earns or matches the
                              anchor (falsification-by-control, cluster
                              #17-class) — adjudicated under the Q-11 rule
R4  trend/vol reduction       CTL-TRENDONLY or VOL-REGIME reproduces
                              >= 0.5x same-sign >= 2/3 folds -> REJECT
R5  clock geometry            CLOCK-ONLY out-earns -> REJECT
R6  usd/macro reduction       USD-drift gate fail, or DGS10/real-yield/
                              curve/carry/SPY shadow reproduces the anchor
                              (>= 0.5x same-sign) -> REJECT
dual-books                    price-only book inverts sign vs financed book
                              on any arm -> that arm fails, fail-closed
```

Plus the frozen forex Stage-A gates on any survivor (fold-positive-share,
concentration, MDD, stress margin, drop-one, per-period series persisted
(P-11) for DSR over ~260 observed trials, PBO fail-closed < 8).

## 7. D2 ancestry and feasibility gate (non-scored)

D2 measures the R0 inventory on the frozen P-12 representation (committed
as a hashed list BEFORE any rho — P-12/A7-F2 law), the feasibility floors,
the firing census, and the funding/liquidity CONTROL set (NY Fed/OFR under
their RETRIEVAL_TIME_ONLY/RETROSPECTIVE_ONLY classes — used only where
their class permits; a use that would require knowability is forbidden).
Observation date vs publication time vs retrieval time are kept distinct
everywhere; no retrieval-time-only evidence claims historical PIT. If the
family is explained by any shadow, it dies here — 0/3 close.

## 8. Trading, costs and risk contract

```text
decision        frozen 16:00-NY daily clock; warmup 60 bars; first
                decision bar 61
entry/exit      next-bar fill; fixed 3-bar hold OR first opposite
                absorption state OR first confirmed-extreme-against-
                position, whichever first; force-flat at fold boundary
universe        five TD majors (EURUSD, GBPUSD, USDCAD, AUDUSD, NZDUSD);
                per-leg long/short by state; no XAU; no cross-pair input
books           financed + price-only dual books; sign must not invert
costs           measured-at-P0 band (1.5 bps floor) charged once per fill;
                stress tier 2.0 PRIMARY; break-even bps per round trip
                per arm; financing adjudicated per arm x leg x fold
claims          D2 eligible = allowed to be tested, never profitable
```

## 9. Execution phases and ownership

```text
M0  methodology golden tests + dual-books fixture (§3)
P0  F1–F7 staging chain + authority + census gates
D1  anchor + neighbour + complement freeze (outcome-blind; A2 dossier binding)
D2  ancestry/feasibility + firing census + funding-control measurement
S   selection + exact arm/data/fold/config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context independent prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types `GO FOREX NG7 SCORED EXECUTION` at this cycle's own gate;
    early/paraphrased GO dies unconsumed (P-8)
E   at most 3 scored cells under the machine-wide heavy lock (selection
    with fewer identities runs fewer — never force-filled)
R   detached reproduction from committed artifacts
T   terminal audit and two-half close
```

Structured handoffs mandatory on every lane; lanes never merge, rebase,
push, edit registries/ledgers or read other lanes' outcomes.

## 10. Trial accounting and result language

Observed and published counted separately; every computed cell consumes an
observed slot even if publication fails. Forex denominators currently
48/48; program 257/260 (P-9) — this cycle starts at budget 0/3.

## 11. Prewritten terminal outcomes

```text
FOREX_NG7_BLOCKED_METHOD_CONTRACT
FOREX_NG7_BLOCKED_SOURCE_OR_SCHEMA
FOREX_NG7_BLOCKED_DATA_OR_SELECTION
FOREX_NG7_BLOCKED_PRELAUNCH
FOREX_NG7_REJECT_ALL
FOREX_NG7_INCOMPLETE_NOT_PROMOTABLE
FOREX_NG7_TECHABORT_PRESERVED
```

A correct early close is success of governance. No predeclared survivor.

## 12. Boundaries

- Keyless-or-entitled sources only; no signup, no purchase; keys never
  echoed. No TWS, no IBKR, no XAU substitution (GLD/GC/MGC/composite
  forbidden).
- SOFR/EFFR/BGCR/TGCR/OBFR/OFR are USD funding/reference rates — never an
  FX signal; D2 funding/liquidity controls only, under their measured PIT
  classes; no forward-fill across holiday/release gaps.
- No S1 access; no paper/testnet/live orders; no deployment.
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`; `CYCLE_REGISTRY.json` changes only
  through `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- No budget/GO/rescue sharing with STOCKS-NG6 or CRYPTO-NG4.

## 13. Immediate actions

```text
1. Commit this plan + the dossier evidence by exact pathspec.
2. Independent fresh-context adversarial plan audit (A7).
3. Remediate every valid HIGH/CRITICAL; re-audit with a NEW fresh-context
   A7 if REFUSED.
4. Register FOREX-NG7 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree; run M0; PASS required before D1.
6. Stop at the scored prelaunch gate and wait for the exact owner GO.
```
