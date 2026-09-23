# PLAN STOCKS-AMIHUD-V1 — Amihud illiquidity on US common stocks, 2019 / 2020 / repetition

> Status: `PLANNED_NOT_STARTED` (2026-09-23). Authority: explicit owner
> instruction 2026-09-23 (Vietnamese, intent anchors): open a NEW
> independent stocks cycle testing whether **Amihud illiquidity** produces
> tradable profit on **US stocks**, with **2019 and 2020 checked as
> separate windows plus one further repetition window**; crypto ILLIQ
> results are explicitly **NOT evidence** for stocks; STOCKS-SEARCH-V1 is
> BLOCKED/superseded — never resumed, its GO never reused, its artifacts
> never modified. This plan is audited by a fresh-context A7 before any
> implementation. A P0/D2 close with zero scored cells is a valid result.
> Nothing in this plan is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          STOCKS-AMIHUD-V1
asset             stocks
plan              plans/PLAN_stocks_amihud_v1.md
branch            orca/stocks-amihud-v1-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/stocks-amihud-v1/integration
budget            3 scored cells max (anchor / neighbour / reversal control)
go_phrase         GO STOCKS AMIHUD V1 SCORED EXECUTION
S0                OPEN — screening only; S0 results are never called OOS
S1                SEALED_UNTOUCHED (this cycle never opens S1)
orders            NONE — no paper, testnet or live orders; no broker access
data spend        NONE — EODHD /eod under the EXISTING owner entitlement only;
                  no purchases, no new channels, key never echoed in logs/git
```

Boundaries inherited verbatim: no push, no merge to `main` from lanes, no
history rewrite, no S1, registry writes only via `researchctl`, one heavy
job machine-wide (never kill a foreign worker; `NOT_RUN_RESOURCE_CONFLICT`
if the lock is held), `research/control/SANDBOX-OVERFIT-3ASSETS/` never
read (standing D2-CURIOSITY-V1 prohibition), PROSPECTIVE-SHADOW-V1 remains
independent and unread. STOCKS-SEARCH-V1's worktree and artifacts are
read-only history: this cycle resumes nothing, borrows no GO, edits no
file of it, and stages its own data from scratch under its own namespace.

## 1. Question, in simple language

> On the death-inclusive US common-stock daily grid, does a LONG-ONLY
> portfolio of the most Amihud-illiquid eligible names — rebalanced on a
> frozen monthly calendar, net of frozen band costs and under a frozen
> liquidity-participation cap — earn positive net profit in calendar 2019,
> in calendar 2020 (the March 2020 crash inside 2020's own fold, never
> merged with any other period), and does the result repeat in 2021–2022?
> And does it beat SPY and a matched-characteristic similar-stock book on
> the same clock — or is any apparent profit just short-term reversal,
> size, volatility or beta exposure wearing an illiquidity label?

Mechanism (research basis, frozen): Amihud (2002), "Illiquidity and stock
returns: cross-section and time-series effects", Journal of Financial
Markets 5(1), doi 10.1016/S1386-4181(01)00024-6 — expected returns
compensate illiquidity measured as average |return| per dollar of trading
volume; the premium is a transaction-cost / limits-to-arbitrage
compensation story. Observable: ILLIQ from daily
OHLCV only. When the mechanism must fail: after band costs and
participation caps on the illiquid tail, if the premium is concentrated in
sub-floor microcaps (excluded by frozen bookability floors) the tradable
book must NOT retain it; and if a reversal control reproduces the anchor,
the mechanism is not illiquidity but reversal.

## 2. Ancestry audit (measured 2026-09-23; A7 must re-verify)

- Amihud/ILLIQ has NEVER been scored on stocks. Registry + HYPOTHESIS_LEDGER
  + FAMILY_FAILURES carry ILLIQ only as **crypto** (CRYPTO-V11 REJECT
  12/13 gates on fold concentration 0.7055; CRYPTO-V12 replication
  BLOCKED_DATA; CRYPTO-NG1 veto of a v17proxy_amihud descendant). Per owner
  instruction those results are NOT evidence here: cross-asset transfer of
  a verdict is prohibited; crypto decision series live on a different
  universe, clock and cost model, so D2 rho vs crypto shadows is not even
  computable — declared inapplicable-with-evidence, not silently skipped.
- Nearest STOCKS ancestors this family must be measured against (D2 §6):
  V2 `A4_XSEC_ETF_RELATIONAL` cross-sectional momentum class; V4
  participation-shift (Gervais/Lo-Wang dollar-volume shock) and the V4
  semivariance **vol-level shadow cluster**; V5 nominal-price placebo
  cluster; V11 momentum_63s shadow; NG5 RELMOM-13W; NG6 `dvol_shock`,
  `reversal_5d`, `vol_restricted_event_20d/60d` event-conditional shadows;
  V13 dividend-transition book. All are price/volume-derivable and are
  therefore constructible on this cycle's own panel.
- Standing stocks-frontier law (STOCKS-NG6 terminal): reopening needs "a
  materially new evidenced source or an owner plan naming a changed
  killer." This cycle is an explicit owner plan naming a NEW family
  (Amihud illiquidity long-only) never scored on this asset — the second
  reserved branch (owner plan), exercised by the owner's own instruction,
  never dressed up as new data. The 0.30 R0 relaxation was a
  STOCKS-SEARCH-V1-only owner grant and is DEAD with that cycle: **the
  standing rho bar 0.20 is binding here and immovable in-cycle.**

## 3. What is frozen BEFORE any PnL exists (no grid search anywhere)

```text
formula (anchor)   ILLIQ_i,t = mean over the D=21 most recent served
                  sessions d<t of |r_i,d| / DV_i,d
                  r_i,d = adjclose_i,d / adjclose_i,d-1 - 1   [guarded, F3b]
                  DV_i,d = P_i,d * V_i,d on ONE adjustment basis fixed by
                  the F3a split fixture (same-basis law; never raw-close
                  times adjusted-volume or any mixed pair)
neighbour          same formula, D=63 sessions (the ONE neighbouring
                  lookback; no other lookback is ever computed)
rebalance          ONE calendar: every 21 trading sessions from the first
                  eligible decision date; decision at session t close;
                  fills at t+1 open; book force-flat at each fold boundary
book               long-only, equal weight w_i = min(1/N_eligible, cap law
                  §5); membership = top quintile (>= 80th pct) of ILLIQ
                  among eligible names at t, ties broken by name
eligibility        common stock on the PIT cohort; >= 252 served sessions
                  before first eligible decision (first decision no
                  earlier than the 253rd served session); adjclose_t >=
                  $1.00; trailing 60-session median DV >= $2,000,000;
                  served bar at t and t+1 (else name skipped, counted)
reversal control   same machinery, same calendar, same eligibility,
                  ranking axis = 5-session past return ASC (long the
                  biggest 5-session losers) — the ONE reversal control
direction          LONG the most illiquid quintile (Amihud 2002 sign);
                  frozen; never flipped after seeing PnL
folds (S0)         F1 = CY2019; F2 = CY2020 (2020-03 lives in F2 alone);
                  F3 = CY2021–CY2022 (repetition window). Pull window
                  starts 2017-07-01 (warmup margin). Fold boundaries frozen
                  at P0-F8 BEFORE any PnL, never moved afterwards.
annual split       results reported per fold AND per calendar year even
                  where a fold spans two years (F3 reported 2021 and 2022
                  separately as well)
```

If any post-PnL change to formula, direction, lookback, calendar, book,
eligibility, folds or costs is proposed: that is a NEW plan and a NEW
cycle. There is no rescue path inside this one.

## 4. Data gate (P0) — fail-closed; missing evidence is BLOCKED_DATA

Primary and only scored source: EODHD `/eod` daily OHLCV incl. delisted,
existing owner entitlement (`EODHD_API_KEY` from gitignored `.env`, never
echoed; V8/V13/NG6/SEARCH-V1 precedent). Universe seed:
`/exchange-symbol-list` with delisted flag, filtered to common-stock type
codes (frozen filter list committed at P0). No fundamentals, earnings,
short-interest, FINRA or any other channel exists in this cycle (NG3/NG4
stay dead). Gates:

```text
F1 ENTITLEMENT + TERMS      P-25 three-layer gate (reachable/permitted/
                            served) on /eod FIRST.
F2 LIVENESS + RETRIEVAL     dead canaries TWTR / SIVB / TWX / FRC (real
                            history ending at exact death sessions) +
                            never-existed control absent; double-pull
                            byte-identity 3/3; raw sha256 pinned.
F3a SPLIT-CONSISTENCY       OWNER-MANDATED FIXTURE. Split canaries INSIDE
     (dollar-volume basis)   the scored window: AAPL 4:1 (2020-08-31),
                            TSLA 5:1 (2020-08-31); out-of-window
                            confirmations: CMG 50:1 (2024-06-26), TJX 2:1
                            (2018-11-07). For each: measure whether /eod
                            volume jumps x-k at the ex-date (raw volume)
                            or not (split-adjusted volume). The fixture
                            VERDICT fixes the DV formula pair (raw x raw
                            or adjusted x adjusted) in
                            dollar_volume_contract.json BEFORE any signal
                            computation. Blindly multiplying raw close by
                            split-adjusted volume (or any mixed pair) is
                            a hard fail and an A7 HIGH.
F3b ZERO/NON-FINITE GUARD   OWNER-MANDATED LAW (STOCKS-SEARCH-V1 died
     (every division)        here — TECHABORT_3 ZeroDivisionError at
                            adj_close[prev]==0 in a CONTROL-side division).
                            Before EVERY division whose denominator is a
                            price or adjusted price — anchor, neighbour,
                            reversal control, matched book, benchmarks,
                            census code, no exceptions: denominator must
                            be > 0 and finite; violation => name-day is
                            excluded from that computation, counted in a
                            fail-closed guard_counter, and disclosed in
                            the final report. An unguarded division site
                            found in review or audit = HIGH; a raised
                            ZeroDivisionError/inf/nan reaching a scored
                            number = TECHABORT, never a silent fill.
F4 COHORT + COVERAGE        death-inclusive PIT cohort: symbol-list seed
                            (incl. delisted) x per-name first/last served
                            bar => alive-interval per name; per-name
                            served-session census; gap census (stretches
                            of missing sessions inside alive interval);
                            in-horizon death census per fold (BC-7a,
                            counted BEFORE any scored computation);
                            warmup attrition census; bookability-floor
                            survival census. Data-availability evidence:
                            per-name first/last bar dates ARE the
                            availability/stop-trading dates under this
                            channel (V8 probe precedent), stated as such.
F5 CLOCK + EXECUTION        decision at t close; fills t+1 open; bar-
                            readable close+1 availability (V7 law); NY
                            calendar via exchange_calendars with DST
                            fixtures; no lookahead anywhere.
F6 COSTS + PARTICIPATION    band schedule BAND_BPS = {A:10, B:15, C:25}
                            bps/fill on ADV bands {50M, 10M, 2M} (RULES
                            §9 lineage); cost exactly once per fill;
                            STRESS TIER 2.0 PRIMARY; worst-case ceiling
                            25bps x 2 fills x 2.0 = 100 bps round trip;
                            band-C fraction measured on the FIRED
                            population — majority band-C => the 100 bps
                            ceiling is the operative stress number.
                            LIQUIDITY PARTICIPATION CAP (frozen): per-name
                            trade notional <= 15% of the name's trailing
                            60-session median DV at the rebalance date;
                            weight w_i = min(1/N, cap_i); capacity number
                            reported = the book AUM at which the binding
                            name first hits the cap. All frozen before PnL.
F7 BENCHMARKS               SPY total-return buy-and-hold exposure-matched;
                            C-RANDOM-TIMING clock twin; MATCHED-
                            CHARACTERISTIC similar-stock book (EW book of
                            names matched at each rebalance on size-proxy
                            tercile = trailing median DV, volatility
                            tercile = 60-session realized vol, price tier)
                            — the owner-required peer comparison. Declared
                            UNMEASURABLE under this entitlement (fail-closed,
                            no vendor-stated constants, Q-8): true market
                            cap (fundamentals channel 403, NG3) and sector
                            classification (not derivable from /eod).
                            Size control therefore runs on the DV proxy;
                            vol and market beta (vs SPY, from the panel)
                            are measured and reported per book.
F8 FOLD FREEZE (Q-6)        folds frozen BEFORE any D2 diagnostic or PnL;
                            >= 30 bookable decisions per fold measured at
                            census (fail-closed kill); 2019, 2020 and
                            2020-03 never share a fold with any other
                            period.
F9 REPRODUCIBILITY          census code, raw-request manifest, digest
                            manifest, calendar/clock contract, DV-basis
                            contract, cost bands, participation cap, folds
                            and the D1 freeze set committed under
                            research/control/stocks_amihud_v1/; detached
                            rerun reproduces.
```

P0 is source engineering and census ONLY. It may NOT compute candidate
PnL, PF, Sharpe, drawdown, survivors or S1 evidence. Any missing-evidence
hole (dead canary unserved, split fixture undecidable, coverage floor
unmet) => `BLOCKED_DATA` close with the hole named — never self-filled.

## 5. Trial identity and cells (every scored arm counted)

```text
cell 1  SAMV1-ANCHOR-ILLIQ21     anchor, D=21 formation
cell 2  SAMV1-NEIGH-ILLIQ63      neighbour, D=63 formation
cell 3  SAMV1-C-REVERSAL5        reversal control (5-session losers)
budget 3/3; slots never reassigned; every scientifically computed outcome
counts in the observed denominator even if publication fails; observed and
published denominators kept separate (P-9). Benchmarks (SPY twin, matched
book, random-timing twin) are evaluation context, not scored cells.
```

Trial identity per cell: cycle_id, family_id, arm_id, arm_config_digest,
data_snapshot_digest, code_freeze_sha, cost_tier, fold contract. Exact-arm
dry-run must show record IDs pairwise distinct.

## 6. D1 freeze and D2 novelty gate (before implementation)

D1 commits, hashed, BEFORE any outcome: `family_contract.json` (§3
verbatim), `fold_contract.json`, `cost_contract.json` (§4 F6),
`evaluation_contract.json` (§8), `dollar_volume_contract.json` (F3a
verdict), `shadow_inventory.json` (the §2 ancestor list, constructible
definitions pinned).

D2 measures, on THIS cycle's staged panel and frozen decision grid, the
pooled |rho| of the anchor's decision representation vs every enumerated
stock shadow (vol-level, dvol-shock, reversal-5d, momentum-63, price-level
placebo, DV-level, RELMOM-13W class, dividend-transition where
constructible). Standing law: **any |rho| > 0.20 => R0 VETO, the family is
not scored, cycle closes `BLOCKED_DATA_OR_SELECTION` with 0 cells**;
UNMEASURABLE shadows are recorded fail-closed per-shadow (they never
silently pass); self-subsumption (control rho vs own anchor) reported.
Neighbour and control are measured on the same grid and vetoed
independently. Crypto ILLIQ ancestry: inapplicable-with-evidence (§2).

## 7. Phases

```text
P0  data gate F1–F9 + censuses (census code may run light; the full-universe
    /eod crawl is a HEAVY job under the machine-wide lock — queued while
    REGIME-STRATEGY-MAPPING-V1 or any foreign worker holds it; never
    contended)
D1  freeze set committed (no outcome exists anywhere)
D2  novelty/shadow measurement, fail-closed 0.20 bar
I   implementation lanes + golden tests (below), no outcome computed
Z   sanitized exact-arm dry-run: scored=false, real_pnl=false; no
    PnL/PF/stress/break-even at ANY record depth; record IDs pairwise
    distinct; non-vacuous (empty book / zero-decision = FAIL)
A7  fresh-context prelaunch audit: hashes chain, exact-arm identity, data/
    PIT authority, cost+cap accounting, dry-run hygiene, S1 seal, no
    post-freeze drift, zero unresolved HIGH/CRITICAL
GATE  STOP. Report to owner: plan path, worktree, branch, full HEAD,
    freeze digests, test results, A7 verdict path, heavy-lock state, and
    the exact GO phrase. Owner GO must be typed AFTER this gate exists,
    fresh, exact-phrase; this plan and the registering instruction are NOT
    a GO (P-8).
E   one bounded scored job under the heavy lock: run the 3 frozen cells;
    never peek cell 1 to alter cells 2–3; count every computed outcome;
    release lock in finally
R   independent reproduction (detached tree, exact freeze SHAs, byte-level
    ledger comparison) + A7 terminal fresh-context audit
T   terminal close per handbook §32 (two-half close)
```

Scoring-gate preconditions (ALL): zero unresolved CRITICAL/HIGH · data
gate PASS · cost+cap contracts PASS · golden tests PASS · freeze digests
committed · clean worktree · heavy lock FREE_PROVEN · A7 prelaunch
authorizing · fresh owner GO.

## 8. Golden tests (must PASS before scoring; no outcome during I)

no-lookahead (information set <= t at every decision) · next-available-bar
execution · fold force-flat + annual split correctness · cost exactly once
per fill · participation cap arithmetic · **negative zero-division test:
inject adj_close==0 / inf / NaN fixtures into anchor, neighbour, CONTROL
and benchmark paths — must be excluded + counted + disclosed, never raise,
never propagate** · split-basis fixture replay (DV formula pair locked) ·
deterministic double-run · missing-data fail-closed · S1 access denial ·
exactly-three-cell enforcement · dry-run leak scan (recursive, no outcome
fields at any depth).

## 9. Evaluation contract (frozen report shape; PASS/FAIL/NOT_RUN per item)

Per cell, per fold (F1=2019, F2=2020, F3=2021–22 AND 2021, 2022
separately): gross PnL, costs, net PnL, return %, PF, expectancy/decision,
number of trades/decisions, max drawdown, exposure, turnover; portfolio
metrics on the book (not per-name cash). Concentration: largest-fold PnL
share (<= 50% bar), largest-calendar-year share, largest single-ticker PnL
share, top-decile ticker share. Comparisons: SPY exposure-matched on the
same clock; matched-characteristic book same clock; random-timing twin.
Reversal adjudication: control earning >= 0.5x anchor same-sign in >= 2/3
folds => falsification-by-control REJECT. Vol/beta attribution: measured
market beta vs SPY and vol-tercile composition per book, reported. Stage-A
gates (standing, unrelaxed): net expectancy > 0 after band costs; PF >=
1.10; >= 2/3 folds positive net; MDD <= 15%; concentration <= 50%; SPY-
excess positive >= 2/3 folds at matched exposure; stress-2.0 net positive;
drop-one-ticker and drop-one-year survival; neighbour support reported;
reversal control not reproducing the anchor (Q-11 adjudication, kill vs
null distinguished); long-short claims: NONE — long-only only, and any
discussion of short legs is explicitly forbidden as unevidenced (no
borrow-fee or locates evidence exists under this entitlement).

Plain-language honesty clause: if the data gate fails or the picture is
only pretty before costs, the report says exactly that. No threshold, fold,
cost or eligibility change to save the strategy. `REJECT`, `BLOCKED_DATA`
and `NOT_RUN` are valid terminal outcomes.

## 10. Terminal vocabulary (fixed)

```text
STOCKS_AMIHUD_V1_REJECT_ALL                 every scored cell fails §9
STOCKS_AMIHUD_V1_STAGE_A_CANDIDATE          all frozen gates pass (opens
                                            S1 planning ONLY — not
                                            deployment, not paper)
STOCKS_AMIHUD_V1_BLOCKED_DATA_OR_SELECTION  data gate or D2 veto, 0 cells
STOCKS_AMIHUD_V1_BLOCKED_PRELAUNCH          A7/dry-run/gate failure
TECHABORT                                   computation invalid/technical
```

## 11. Owner decision points

1. GO phrase at the §7 GATE (this cycle's own gate, after A7 prelaunch):
   `GO STOCKS AMIHUD V1 SCORED EXECUTION` — typed fresh and exact; early
   or malformed GO is intent only and dies unconsumed (P-8).
2. Any spend beyond the existing entitlement, any S1 opening, any
   paper/live step: separate explicit owner instruction. Default
   fail-closed.

## 12. Standing prohibitions (non-exhaustive)

No resume of STOCKS-SEARCH-V1; no use of its GO; no edits to its
artifacts; no cross-asset import of crypto ILLIQ verdicts; no grid search
or parameter rescue; no vendor-stated constants treated as measured (Q-8);
no S1; no orders; no push from lanes; no writes to ZCode internal
databases; no credentials in prompts/logs/git; heavy lock never contended,
foreign workers never killed.
