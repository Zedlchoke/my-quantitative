# PLAN CRYPTO-NG4 — BETDIS cross-symbol beta-break dislocation convergence

> Status: `PLANNED_NOT_STARTED` (2026-09-16). Authority: explicit owner
> directive 2026-09-16 (three-cycle program; this cycle: ONE new crypto
> family on the HISTORICAL price/funding channel with authority; Coinbase/
> Kraken/Deribit data PROSPECTIVE-ONLY as D2 non-scored controls; budget
> max 3 scored cells / 1 family; plan audited by fresh-context A7 before
> registration). Outcome-blind dossier evidence is committed under
> `research/control/ng6_ng7_ng4_dossiers_2026-09/` (A2 proposal
> `7a3b6643…`, A3 prospective collection contract `d0423884…`, A4 hostile
> critique `346e7d87…`; SHA256SUMS.txt pinned). WebSocket data is
> prospective-only: it never backfills history and never adjusts the
> historical family. Nothing here is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          CRYPTO-NG4
asset             crypto
plan              plans/PLAN_crypto_ng4.md
branch            orca/crypto-ng4-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/crypto-ng4/integration
budget            3 scored cells max / 1 family max
go_phrase         GO CRYPTO NG4 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

Family name (frozen): `BETDIS — CROSS-SYMBOL BETA-BREAK MARKET-NEUTRAL
DISLOCATION CONVERGENCE`. `PROSPECTIVE-SHADOW-V1` untouched (this cycle
never reads its PnL/trades/marks/verdicts). STOCKS-NG6 and FOREX-NG7 share
no budget, no GO and no rescue path with this cycle.

## 1. Question, in simple language

On Binance USD-M perpetuals, portfolio-margin and cross-symbol basis books
run market-neutral pairs hedged at a trailing beta RATIO. When realized
co-movement between two co-listed perps breaks its own trailing beta by a
frozen z-band, every such book's hedge ratio is mechanically wrong and
margin stress forces ratio-restoring flow in the dislocated leg — buying
the under-mover, selling the over-mover, regardless of directional view.
We ask one narrow question:

> On the frozen BTC/ETH/SOL H1 panels, does a beta-break dislocation state
> predict convergence of the dislocated pair — beyond what volatility
> shock, tape-state proxies, short-horizon momentum/reversal, and the
> weekend clock already explain?

Anchor book return over its own entry/exit windows: `r_legA − β·r_legB` —
common momentum/vol/tape/carry states cancel BY CONSTRUCTION; the 29-shape
dead crypto inventory contains zero cross-symbol co-movement shapes.

## 2. Why this is a new cycle — and its honest ancestry risk

- A2 declares the primary kill risks honestly: dvol_shock ancestry via the
  z-normalization (NG1 0.4409; NG3 X1 0.402/0.426) and the X3 tape proxy
  (NG3: tape alone explained 0.547/0.262) — both are BINDING D2 controls
  (§6), not optional. `buy under-mover / sell over-mover` is short-horizon
  reversal BY CONSTRUCTION — BINDING momentum AND reversal controls.
- The pooled |rho| <= 0.20 bar killed all 10 crypto ng proposals so far;
  the dossier treats pre-score veto as a likely outcome and preregisters
  it as a valid close.
- A4 verdicts adopted: NO family KO; ONE KO on the COVERAGE FLOOR (the
  A3 floor covers ONLY the prospective control cells — the anchor's own
  z-band event population is NOT_MEASURED) => the cycle carries a
  preregistered `WAITING_PROSPECTIVE_COVERAGE` state (§9/§11); SOL pairs'
  venue controls are NOT_RUN by construction (SOL absent from the
  prospective venue set) => fail-closed at D2 unless a preregistered
  extension happens (none in-cycle).
- No historical order book/tape exists before collection; the family uses
  NONE — no scored dependence on any pre-collection book/tape observable.

## 3. M0 — methodology contract gate (before D1)

The shared D2-methodology golden suite (G1–G10 + G4N = 11/11; NG5 lineage,
re-inherited BYTE-EXACT and re-run in this cycle's worktree under
`research/control/crypto_ng4_run/m0/`) PLUS crypto-specific golden
fixtures: (a) time-based fold assignment fixture (event-triggered entries
must fall in their wall-clock fold; a fold-population < 4 decisions kill
reproduces the NG3 2<4 failure in-test); (b) two-leg funding accounting
fixture (sign conventions, 1:−β notional weighting, 4h-cadence stress
handling, boundary rule — charged exactly once per settlement); (c) the
prospective contract floor verifier (recomputes the §7 arithmetic from the
frozen contract file; any mismatch = fail). M0 PASS required before D1
dispatch; else `BLOCKED_METHOD_CONTRACT`, budget 0/3.

## 4. Source authority and P0 gates

Scored source: frozen S4 Binance H1 panels via the platform plane
(`consume_via_plane`): panel_BTCUSDT_h1.csv `111c1a2d…`, panel_ETHUSDT_h1
.csv `ebd487a6…`, panel_SOLUSDT_h1.csv `c4…` (SOL perp-perp presence
byte-verified by A4: 8,760 rows — the "366-day panel" wording in the A2
dossier is corrected: panels measure 365x24 rows), plus frozen OI series
`oi_series_reduced.json` `f26a61e4…` (2,904 H4 snapshots from 2025-04-25)
as a NON-SCORED D2 diagnostic only — OI enters no feature.

```text
F1 PANEL RE-PIN           S4 digests re-verified in the cycle worktree;
                          the A4 G1 ruling binds: the canonical X1 shadow
                          battery bytes (NG1 29-shape inventory blob
                          6411e685…, NG3 d2_verdict) are RE-PINNED into
                          research/control/crypto_ng4_run/ BEFORE D1;
                          if unresolvable, X1 is NOT_RUN fail-closed and
                          D2 cannot PASS.
F2 FUNDING AUTHORITY      keyless fapi funding settlements re-proved per
                          series at P0 (V17-measured class; CNG2 grid
                          1094x3); the COMPLETE two-leg accounting is
                          re-proven fail-closed per A4: sign convention
                          per leg, 1:−β notional weighting, cadence read
                          MEASURED per symbol per window (8h nominal;
                          4h stress and any 1h adjustment are data, read
                          from the re-proved series, never hardcoded),
                          and the settlement-boundary rule is INCLUSIVE —
                          a settlement timestamped exactly at entry or
                          exit is charged; unproven -> NOT_RUN_BLOCKED,
                          never assumed.
F3 SYMBOL/PAIR CENSUS     BTC/ETH/SOL USDT perp panels; 3 pairs; SOL
                          venue-control gap recorded (§7); funding for
                          SOL re-proved like the others.
F4 CLOCK + FOLDS          UTC H1 on the panels; decisions evaluated at
                          bar close on last_price; state-triggered at
                          ARBITRARY hours (no calendar/session/settlement
                          conditioning in the signal); EXACT UTC FOLD
                          BOUNDARIES FROZEN IN THIS PLAN, BEFORE D1
                          (A7-F1): the panel window is 2025-08-22T00:00Z
                          .. 2026-08-21T23:00Z (365x24 H1 bars; first
                          decidable panel day index 61 = 2025-10-22T00:00Z);
                          the four folds are contiguous and equal:
                          FOLD-1 2025-10-22T00:00Z..2026-01-05T23:00Z,
                          FOLD-2 2026-01-06T00:00Z..2026-03-22T23:00Z,
                          FOLD-3 2026-03-23T00:00Z..2026-06-06T23:00Z,
                          FOLD-4 2026-06-07T00:00Z..2026-08-21T23:00Z.
                          P0 verifies the panel span census-EXACT against
                          these timestamps; ANY mismatch ->
                          CRYPTO_NG4_BLOCKED_SOURCE_OR_SCHEMA — the
                          boundaries are never recomputed or shifted
                          in-cycle. The A2 "margin day 2026-08-22" is a
                          PHANTOM (outside the window — A4) and is never
                          a decision or holding day; every full holding
                          window inside a single fold; force-flat
                          truncations COUNTED, never dropped. The M0 fold
                          fixture assigns against THESE frozen
                          timestamps.
F5 COSTS                  L-V14-0 cost-once-per-fill kernel; stress
                          multipliers applied to booked PnL; costs broken
                          out fills vs holding; funding as a cost line
                          only (complete per F2).
F6 REPRODUCIBILITY        census, manifests, digests, fold contract
                          committed under research/control/crypto_ng4_run/;
                          detached rerun reproduces.
F7 PROSPECTIVE SOURCES    Coinbase/Kraken/Deribit are D2 non-scored
                          controls ONLY under the frozen collection
                          contract (§7); wire formats from the FDF-V1
                          measured census; nothing prospective ever joins
                          history.
```

P0 is source engineering and census only. No candidate PnL/PF/Sharpe/
drawdown/survivors/S1 evidence.

## 5. D1 outcome-blind proposal contract

The committed A2 dossier (sha `7a3b6643…`) is BINDING, frozen before any
return exists. At most THREE constructions enter D2:

```text
1 anchor        CNG4-A2-P1-BETDIS-ANCHOR: per pair (BTC-ETH, BTC-SOL,
                ETH-SOL): r_s(t) = log(last_price_s(t)/last_price_s(t-1));
                beta_AB = rolling OLS slope of r_legA on r_legB over
                trailing 720 bars, PIT-strict (bars <= t-1 only); residual
                e_AB(t) = r_legA(t) - beta_AB(t-1)*r_legB(t);
                z_AB(t) = e_AB(t) / rolling 720-bar MAD-to-sigma; entry
                when |z_AB| breaks its frozen z-band; exit per the frozen
                convergence/re-show rule (exact constants = the A2
                dossier, binding); warmup 30 panel days beta + 30 panel
                days residual history (first decidable panel day index
                61); OI/funding/weekend/session in NO feature.
1 neighbour    NEIGHBOUR SELECTION RULE (A7-F7): the A2 dossier declares
                TWO alternatives; the scored neighbour is A2's
                z>=2.0-frequency construction; the OI-share-gated variant
                is X2-exposed by A3/A4's own declaration and is NOT scored
                (it dies with X2 by its own definition); both declarations
                are frozen outcome-blind here. Anchor exit (A2 verbatim,
                binding): H = 24 bars OR |z_AB| crossing 0 at a bar close,
                whichever first. Same self-subsumption |rho| <= 0.98 vs
                anchor (P-20).
1 mandatory stale-beta causal control book (non-scored) — §6.
```

Arms consume declared trial identities; controls consume none. CELL
GRANULARITY (A7-F4, explicit): EACH SCORED PAIR-BOOK IS ONE SCORED CELL
(a pair-book run at E consumes exactly one observed+published slot); the
neighbour scores only within the remaining budget; total scored cells
<= 3, never force-filled.

## 6. Mandatory controls and killers (A4 BINDING set)

```text
VOL-SHOCK     generic_dvol_shock same-bet per leg AND on the pair
              residual; dvol_level_log; RV24 STRESS/VOLATILITY_EVENT
              states — HISTORICAL-leg labels are computed PANEL-NATIVELY
              from S4 last_price H1 returns (the prospective cross-venue
              median mid of §7 does not exist historically — A7-F2):
              BTC/ETH use the §7 frozen constants; SOL constants are
              frozen from the SOL panel's first 180 days by the same
              percentile construction (LOW < P33.3 <= MID < P66.7 <=
              HIGH; STRESS > P90), pinned at P0 BEFORE D1, outcome-
              independent; the S4->cross-venue estimand transfer for the
              prospective RV24 is DECLARED APPROXIMATION (A4 axis-8) and
              never silently treated as identical — bar 0.20
TAPE-PROXY    X3-native proxy per leg PLUS panel-native taker-imbalance
              (panels carry buy/sell qty — strictly better proxy),
              correlation-decay (24/72 bar), fill-clock clustering,
              lead-lag ±1/±2 bars
MOM/REV       rev24 (-sum 24h log rets), mom168, tsmom28, pair
              spread-trend lagged >= 1 bar — all same-bet, bar 0.20
WEEKEND       wkndliq shadow + weekend/weekday sub-books with per-fold
              populations + Q-7 clock decomposition + session geometry
              (X4 killed NG3 at 0.326/0.626)
SHAM          randomized-event-time sham matched to the trigger rate —
              out-earns -> family dead (no hedged population exists)
STALE-BETA    causal control trading the break with a deliberately stale
              beta estimate — must NOT out-earn
FOLD POP      any fold with < 4 decisions on an arm -> that arm dies
              pre-score (NG3-A5 precedent)
```

Ordered kill rules (first binding kills; NET of full costs incl. funding):

```text
R0  pre-score ancestry veto   per-pair-AND-pooled |rho| > 0.20 vs the
                              re-pinned X1 inventory (dead-form envelope:
                              the 32 crypto-adjacent FAMILY_FAILURES
                              entries under the cycle_id predicate
                              ^(CRYPTO|CNG|SCNG) — A7-F6) + the §6
                              state set on the frozen P-12 representation
                              -> dies pre-score
R1  expectancy                anchor net expectancy <= 0 after full costs
R2  robustness                PF gate + fold positivity + fold population
R3  mechanism specificity     SHAM or STALE-BETA out-earns the anchor
R4  vol/tape reduction        dvol/tape-proxy shadow reproduces >= 0.5x
                              same-sign -> REJECT
R5  momentum/reversal         rev24/mom168/tsmom28 reproduces >= 0.5x
                              same-sign -> REJECT
R6  weekend/clock             weekend sub-book divergence or X4-class
                              clock reproduction -> REJECT
venue controls                per pair: venue divergence, basis, spread
                              proxy, liquidation/volatility, weekend
                              liquidity, funding-state controls from the
                              PROSPECTIVE store — NOT_RUN (coverage
                              insufficient) -> that pair FAILS CLOSED
```

Plus frozen crypto Stage-A gates on any survivor (fold-positive-share,
concentration, MDD, stress margin, drop-one, per-period series persisted
(P-11) for DSR over ~260 observed trials, PBO fail-closed < 8).

## 7. Prospective collection contract (frozen BEFORE any collection)

The committed A3 contract (sha `d0423884…`) is BINDING and freezes, before
any collector starts: venue + instrument identity; channel/schema per
venue; exchange AND local receive timestamps; sequence semantics; reconnect
+ gap policy (fail-loud, gap-marked, never silent); heartbeat policy;
raw-byte hashing + content-addressed append-only manifests; duplicate/
out-of-order policy; minimum coverage = 60 CONSECUTIVE UTC days all 3
venues; >= 1,296 valid triads (90% of 1,440 H1 bars); 4 x 15-day folds
aligned to the family's fold count with >= 324 valid triads/fold and >= 4
valid bars per control cell per fold (min population share 1.2346%);
weekend coverage: collect every UTC day; the BINDING weekend guarantee is
the CALENDAR guarantee — every 15-day fold contains >= 4 weekend days =
96 raw weekend H1 bars, and the floor verifier asserts >= 4 VALID weekend
cells per control per fold plus >= 16 weekend days per 60-day window; the
"86 valid bars" figure from the A3 dossier is NOT the guarantee (it would
presume 90% validity WITHIN weekend bars, which fold-global 90% does not
imply — A4/A7-F3) and is not used; a missing weekend day = floor unmet;
ONE preregistered regime: RV24(t) = sqrt of the trailing-24 hourly squared
log returns of the cross-venue median mid, labels frozen from the S4
panels (BTC LOW<0.0171<=MID<0.0299<=HIGH, STRESS>0.0542; ETH
0.0331/0.0571/0.1042) — outcome-independent; missing = missing, NO
synthetic backfill; stopping date calendar-based, outcome-independent.
Sparse event constants frozen from FDF census bytes (divergence 2xP90 per
pair, spread 5xP50 per venue, basis 1e-3, funding 1.377e-5) —
underpopulation is a fail-loud terminal, NEVER retuned.

A7 FLOOR AUDIT BEFORE COLLECTION: a fresh-context A7 verifies the floor
arithmetic and its decision-frequency meaning BEFORE any collector starts.

A4 KO adopted into law: the floor covers ONLY the prospective control
cells; the ANCHOR's own z-band decision/fold/pair population is
NOT_MEASURED — the cycle is WAITING_PROSPECTIVE_COVERAGE on anchor
decisions/fold/pair population, the funding P0 proof, and the anchor
identity bytes until measured. ANCHOR IDENTITY (A7-F8, named): NO
prospective anchor z-band identity exists this cycle — the Coinbase legs
are SPOT (BTC-USD/ETH-USD), no Binance venue is collected, and therefore
no prospective perp z-band series may be claimed or silently substituted
for the historical anchor identity; the item stays WAITING. An incomplete
window is NEVER PASS and is never scored.

Collector hygiene: collectors are LIGHT long-running daemons (never the
machine-wide heavy lock), with Q-13 discipline — heartbeats carrying
bytes-written + payload-shape counts, inode-check on append handles,
payload-shape mismatch fails LOUD.

## 8. Trading, costs and risk contract

```text
decision        UTC H1 bar close on last_price; arbitrary-hour triggers
entry/exit      frozen z-band entry; frozen convergence/re-show exit;
                every full holding window inside one fold
universe        BTC-ETH / BTC-SOL / ETH-SOL pairs on USDT perp panels;
                1 : −β notional; no leverage beyond the pair structure
accounting      L-V14-0 cost-once-per-fill; two-leg funding as cost line;
                stress multipliers on booked PnL
claims          D2 eligible = allowed to be tested, never profitable;
                WAITING_PROSPECTIVE_COVERAGE is never PASS
```

## 9. Execution phases and ownership

```text
M0  methodology golden tests + crypto fixtures + floor verifier (§3)
P0  F1–F7 re-pin + authority + census gates (incl. funding accounting proof)
D1  anchor + neighbour + stale-beta freeze (outcome-blind; A2 dossier binding)
D2  ancestry/feasibility on HISTORICAL panels (R0–R6 historical set) +
    prospective venue controls WHERE COVERAGE PERMITS (fail-closed else)
S   selection + exact arm/data/fold/config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context independent prelaunch audit; zero unresolved HIGH/CRITICAL
    (includes the PRE-COLLECTION floor audit of §7)
GO  owner types `GO CRYPTO NG4 SCORED EXECUTION` at this cycle's own gate;
    early/paraphrased GO dies unconsumed (P-8)
E   at most 3 scored cells under the machine-wide heavy lock — ONLY when
    coverage floors are MET; otherwise the cycle parks at
    WAITING_PROSPECTIVE_COVERAGE with collectors running light
R   detached reproduction from committed artifacts
T   terminal audit and two-half close
```

WebSocket collectors MAY run prospective while the sibling cycles work
(owner directive); collectors start only AFTER the A7 floor audit, under
the frozen contract, in the cycle worktree.

## 10. Trial accounting and result language

Observed and published counted separately; every computed cell consumes an
observed slot even if publication fails. Crypto denominators currently
155/158; program 257/260 (P-9) — this cycle starts at budget 0/3.

## 11. Prewritten terminal outcomes

```text
CRYPTO_NG4_BLOCKED_METHOD_CONTRACT
CRYPTO_NG4_BLOCKED_SOURCE_OR_SCHEMA
CRYPTO_NG4_BLOCKED_DATA_OR_SELECTION
CRYPTO_NG4_WAITING_PROSPECTIVE_COVERAGE   (honest park; not PASS; not a scored close)
CRYPTO_NG4_BLOCKED_PRELAUNCH
CRYPTO_NG4_REJECT_ALL
CRYPTO_NG4_INCOMPLETE_NOT_PROMOTABLE
CRYPTO_NG4_TECHABORT_PRESERVED
```

A correct early close is success of governance. No predeclared survivor.

## 12. Boundaries

- Keyless public endpoints + frozen S4 panels only for scored work; no
  signup, no purchase; keys never echoed.
- Coinbase/Kraken/Deribit data: prospective-only, D2 non-scored controls;
  no historical order book/tape is claimed to exist before collection.
- No prospective result ever edits the historical family; no parameter
  change after any scored outcome.
- No S1 access; no paper/testnet/live orders; no deployment.
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`; `CYCLE_REGISTRY.json` changes only
  through `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- No budget/GO/rescue sharing with STOCKS-NG6 or FOREX-NG7.

## 13. Immediate actions

```text
1. Commit this plan + the dossier evidence by exact pathspec.
2. Independent fresh-context adversarial plan audit (A7).
3. Remediate every valid HIGH/CRITICAL; re-audit with a NEW fresh-context
   A7 if REFUSED.
4. Register CRYPTO-NG4 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree; run M0; PASS required before D1.
6. Freeze the collection contract, A7-audit the floor, then start light
   collectors; stop at the scored prelaunch gate for the exact owner GO.
```
