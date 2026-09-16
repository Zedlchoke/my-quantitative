# PLAN FOREX-NG6R1 — IBKR London Gold real-yield / USD dislocation (successor)

> Status: `PLANNED_NOT_STARTED` (draft 2026-09-16, owner directive /lead-start
> same day: "Mở và điều phối song song hai hướng nghiên cứu độc lập ... B.
> XAUUSD — IBKR London Gold, successor của FOREX-NG6 đã terminal"). This is
> a SUCCESSOR cycle, not a reopening of FOREX-NG6: the TERMINAL
> `FOREX_NG6_BLOCKED_SOURCE_OR_COST` row (branch orca/forex-ng6-integration,
> terminal 3b13d1da) is append-only history and is never rewritten. The
> FOREX-NG6 recorded reopening condition — "an owner broker-specific XAUUSD
> cost authority" — is the authority path this successor executes: the owner
> has provided a TWS simulated-trading endpoint (localhost, Read-Only API)
> trading IBKR London Gold XAUUSD, and ordered a broker-cost probe before
> any cycle registration. Registration happens ONLY after
> XAUUSD-BROKER-COST-PROBE-V1 PASS and an A7-XAU fresh-context
> AUTHORIZED verdict on this plan + the probe contract. Nothing in this
> plan is evidence of profitability.

## 0. Cycle identity (to be registered exactly like this)

```text
cycle_id          FOREX-NG6R1
asset             forex
subtype           metal_fx_quote
plan              plans/PLAN_forex_ng6r1.md
branch            orca/forex-ng6r1-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/forex-ng6r1/integration
budget            3 scored cells max / 1 family max
go_phrase         GO FOREX NG6R1 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders; Read-Only API only
```

Family name (frozen): `XAUUSD REAL-YIELD / USD DISLOCATION` (unchanged —
the hypothesis carries; the instrument and cost authority change).

Classification disclosure (carries from FOREX-NG6, updated): broker
convention = IBKR London Gold CMDTY quote on SMART; economic underlying =
gold, a commodity. D2 ancestry pools FOREX + COMMODITIES + RATES +
gold-price families. The asset label exists for data-plane routing only
and must never be used to dodge ancestry.

`PROSPECTIVE-SHADOW-V1` remains independent and `ACTIVE_LIGHT`; its
outcomes are never read. No budget, GO or rescue is shared with
STOCKS-NG5 or with the dead FOREX-NG6.

## 1. Instrument identity (frozen; the cycle's spine)

```text
provider         Interactive Brokers TWS API (localhost:7497, Read-Only API,
                 simulated trading endpoint), ibapi 10.45.1
provenance       twsapi_macunix.1045.01.zip, sha256
                 56ea048911052e86d6621ab712957c790fce6d547bc2a55900136ae4f6835941
                 (provenance string ONLY — the ZIP is never committed)
contract         conId 69067924; symbol/localSymbol/tradingClass XAUUSD;
                 secType CMDTY; exchange SMART; currency USD; minTick 0.01
                 (MEASURED from the live contract; the stated $0.001 on a
                 2022 Campus page is a flagged DISCREPANCY — measured beats
                 stated, Q-8); longName "London Gold"; timezone US/Eastern
law              the cycle trades THIS contract or does not run. It is NOT
                 the Twelve Data composite XAU/USD and must never be
                 presented as such. No XAUUSDT, no generic gold index, no
                 GLD/GC/MGC/other-broker substitution anywhere, in any
                 direction (instrument, cost, or fallback).
credentials      none in prompts, logs, artifacts or git; no account numbers
                 recorded; Read-Only API is never disabled or bypassed
```

The FOREX-NG6 TD XAU/USD archive (12,268 daily rows, sha-pinned) is
ARCHIVE/REFERENCE only. Using it as signal history for this instrument
requires the mapping/basis test + representation contract drafted by the
frontier lane (`research/control/xauusd_ibkr_probe_2026-09/
td_archive_join_contract.json`) and P0 acceptance; absent that acceptance
the join is forbidden.

## 2. Why a successor cycle — honest ancestry

- FOREX-NG6 closed on DATA/COST AUTHORITY (F4 fail-closed), NOT on a
  measured scientific kill: the real-yield/USD dislocation hypothesis
  remains UNTESTED. The owner-supplied broker endpoint is exactly the
  recorded reopening condition. The four named dodge-configurations
  (A4 critic) are each forbidden by construction: IBKR-as-cost-badge with
  TD-as-price substrate (only via the accepted basis test), direction
  re-derivation (the mean-reversion preregistration carries verbatim),
  CMDTY-label rerouting (ancestry pooling is frozen in §0), stated-cost
  laundering (stated vs simulated vs measured are separate labels).
- The hostile prior carries IN FULL (FOREX-NG6 plan §2, ledger row):
  DFII10/DFII5 are already granted control series; gold price history is
  consumed ancestry (COMMNG1-A4-P2 088691/IAU, release-clock kill #17);
  the DGS10-LEVEL shadow is the program's most lethal control (#14: 4.01x
  out-earn; #15); FXFV9-A5-P1 real-rate-deviation veto 0.3034; V4 carry
  closure rho 0.997-1.000; clock kills #16/#17. The FOREX-NG5 E1
  financing ceiling 18.07 bps is an FX-pair precedent, explicitly NOT
  citable as an XAUUSD band (A4); the successor measures its OWN costs.
- NEW economics vs FOREX-NG6: IBKR London Gold is a spot commodity quote
  with first-order storage/financing costs (stated 0.10%/yr long storage;
  borrow at benchmark+tiers — all stated, never treated as measured until
  P0 evidence). Cost decomposition is mandatory from day one (§7 C14):
  the dislocation signal must survive the raw-vs-cost-adjusted book split
  and the financing-cost-state + unconditional-long-gold controls (A4
  additions); a family whose economics reduce to carry dies at the V4
  closure (0.997-1.000).
- The outcome-blind preregistration CARRIES and binds D1 exactly as
  frozen in the FOREX-NG6 frontier dossier
  (`research/control/ng5_ng6_frontier_2026-09/handoffs/
  xauusd_ng6_researcher.json`): construction B = MEAN-REVERSION of the
  macro-implied residual (unconditional; falsifier: sign-inverted
  continuation control out-earns, or anchor <= 0 with continuation >= 0.5x
  positive — secondary clause arithmetic pinned at threshold freeze per
  A7-NG6-F1); construction A = macro-state response; A and B are ONE
  family (variants as arms).

## 3. M0 — methodology contract gate (before D1)

Shared law with STOCKS-NG5: G1–G10 + the round-2 owner hardening — G4's
AST purity proof (`verify_verdict_purity`) and the **G4N** negative
control; the golden suite must report **11/11 PASS** with the frozen
contract sha before D1 opens. Implementation copies the proven machinery
under `research/control/forex_ng6r1_run/m0/` with this cycle's identity.
M0 FAIL => `FOREX_NG6R1_BLOCKED_METHOD_CONTRACT`, D1 never opens, 0/3.

## 4. The probe phase — XAUUSD-BROKER-COST-PROBE-V1 (pre-cycle)

The probe is a preregistered pre-cycle collection under
`research/control/xauusd_ibkr_probe_2026-09/`, governed by the probe
contract frozen from the A3 lane's draft (`probe_contract_draft.json`)
BEFORE any long collection, and audited by A7-XAU together with this
plan. Contract minimum content (the frozen contract is authority):

```text
B1 SAMPLING          event-driven streaming subscription on conId 69067924
                     (one market-data line, within IBKR pacing); 1s grid
                     snapshots in IBKR SERVER time only (reqCurrentTime +
                     tick timestamps), never local clock; no forward-fill
B2 WINDOW            >= 10 trading days spanning a mid-month AND a month-end
                     plus at least one scheduled high-volatility macro event
                     day (FOMC/CPI/NFP-class, 60 min pre / 120 min post);
                     frozen Asia/London/New York session boundaries in
                     US/Eastern; a mandatory low-liquidity rollover bucket
                     (16:55-17:15 ET); high-volatility hours mandatory
B3 RESILIENCE        reconnect/disconnect handling (gaps recorded, no
                     resume-mid-second fabrication); pacing-limit handling;
                     durable resumable state (xauusd_probe_state@1 schema:
                     coverage_by_session, gap records, monotonic sample_seq,
                     fsync-then-offset-commit, Q-13 heartbeats with
                     bytes-written + payload shape); missing interval =
                     MISSING, never backfilled
B4 METRICS           spread in USD/oz AND bps-of-mid; per-session and
                     per-hour-bucket median/p90/p95/p99/max; regime buckets
                     session x {quiet/normal/high-vol} with the threshold
                     rule frozen BEFORE analysis (T = P95 of 1-min mid
                     log-returns from days 1-2); stress multiplier 2.0
                     frozen BEFORE any outcome exists
B5 COST AUTHORITY    each component separate, labelled STATED vs MEASURED:
                     live Bid/Ask spread (measured, probe); commission
                     schedule + minimum per order (stated official bytes:
                     London Gold tiered 1.5/1.0/0.7 bps, min USD 2.00/order,
                     exchange+regulatory fees included); long storage
                     (stated 0.10%/yr); short borrow/financing (stated
                     benchmark+tiers); margin (currently UNMEASURED —
                     official pages JS-rendered; must come from the
                     published margin table bytes at P0; never invented);
                     minimum order size and size increment; price increment
                     (measured minTick 0.01 vs stated 0.001 DISCREPANCY
                     recorded); paper-fill limitations (simulated fills
                     carry ZERO evidential weight for execution cost)
B6 AVAILABILITY      TWS unavailable / logged out / API unresponsive =>
                     NOT_RUN_TWS_UNAVAILABLE recorded (as measured
                     2026-09-16); no gate lowering; no silent backfill;
                     resumable; coverage reported exactly as it exists
```

Probe verdicts:

```text
PROBE_PASS           all B1-B5 evidenced; the cost authority feeds the
                     P0/D2 cost ceiling (P-21 law: ceiling pre-scored,
                     never re-derived after numbers exist)
PROBE_BLOCKED_COST   any component UNMEASURABLE in the authorized space
                     => the successor does NOT register (or, if already
                     registered, terminates FOREX_NG6R1_BLOCKED_SOURCE_OR_
                     COST 0/3); probe evidence is banked
NOT_RUN_TWS_UNAVAILABLE  endpoint unavailable; resumable; no verdict
```

Raw market stream bytes are staged (sha-pinned, untracked) per the
licensing law; committed evidence = code, manifests, hashes, aggregates
and the contract artifacts.

## 5. P0 gates (after registration; only after PROBE_PASS + A7-XAU)

```text
F1 INSTRUMENT PROOF      live contractDetails re-verification (conId 69067924
                         fields identical); contract bytes pinned
F2 CLOCK/SESSIONS        daily-close convention frozen (US/Eastern, weekend
                         handling of the CMDTY quote measured, not assumed);
                         T-1 availability rule frozen
F3 HISTORY               the probe window IS the history start; depth census;
                         revision behavior measured (double-pull identity)
F4 COST CEILING (P-21)   conservative spread + commission + storage/financing
                         vs the gross diagnostic band, at stress tier 2.0;
                         ceiling exceeded => family dies at D2, no scored cell;
                         components UNMEASURABLE => BLOCKED_SOURCE_OR_COST
F5 MACRO AUTHORITY       carries from FOREX-NG6 §F5: DFII10/DFII5 granted
                         (AX2 as-of), nominal/breakeven granted-set controls,
                         USD leg adjudicated (DTWEXBGS candidate-not-authorized
                         or the PIT-clean 5-leg basket with its own authority
                         row)
F6 FOLD FREEZE (Q-6)     three chronological folds over the probe-window
                         reality, frozen before any D2 diagnostic
F7 REPRODUCIBILITY       manifests + digests committed; detached rerun rule
F8 BASIS TEST            TD-archive join only after the three-gate join
                         contract passes (PIT-lag test; basis distribution
                         over >= 20 aligned IBKR trading days with thresholds
                         frozen at P0; representation contract — TD never
                         relabelled IBKR)
```

## 6. D1 outcome-blind proposal contract

Exactly ONE family, two constructions carrying from the FOREX-NG6 frontier
dossier verbatim (A macro-state response; B residual dislocation with the
preregistered MEAN-REVERSION direction), variants as arms, <= 3 scored
cells, allocation frozen at S, mandatory controls consume no scored slots.
Proposal hashes freeze before any sanitized dry-run.

## 7. Mandatory controls and D2 ancestry battery

Controls carry from FOREX-NG6 §6 (C1-C13) plus the A4 additions:

```text
C14 COST DECOMPOSITION   raw vs commission-adjusted vs storage/financing-
                         adjusted books — the dislocation signal must be
                         identified NET of the carry-like cost structure
C15 FINANCING-STATE CONTROL   a financing-cost STATE shadow (the new
                         first-order exposure must not BE the signal)
C16 UNCONDITIONAL-LONG-GOLD CONTROL   the structural long-gold drift of
                         the sample must not explain the anchor
```

D2 ancestry battery carries FOREX-NG6 §7 A1-A14 in full (XAUUSD/gold
momentum-reversal, USD-only, real-yield-only, nominal-yield LEVEL +
mandatory level-vs-shape decomposition, inflation/breakeven incl. FXFV9
0.3034, SPY risk-off, volatility, day-of-week/session, macro release
clock, GLD momentum diagnostic, COMMNG1 CoT release-clock template,
RATES-NG1 curve/release families, rate-differential/carry 0.997-1.000,
cost ceiling), extended by the A4 G1-G16 template enumeration committed in
`research/control/ng5r1_ng6r1_frontier_2026-09/handoffs/
a4_ancestry_critic.json`. The shadow inventory is enumerated and frozen
BEFORE any rho (A7-F2 law); the 0.20 pooled |rho| bar is immovable;
UNDER-ENUMERATION IS AN INVALID PASS. M0 G4N-class adjudication governs.

## 8. Trading, costs and risk contract

```text
decision        frozen daily/weekly grid on the IBKR quote where ALL macro
                inputs are available (AX2 as-of macro, T-1 price)
entry/exit      frozen executable convention; force-flat at fold boundary
universe        IBKR London Gold XAUUSD only; gross cap 1.0; no leverage;
                no short unless the cost authority evidences short financing
accounting      price PnL + commission + storage/financing accrual per
                holding day (C9 reconciliation); raw AND financing-adjusted
                books both reported; simulated fills never labelled live
costs           from PROBE_PASS evidence only; stress tier 2.0; break-even
                margin reported; ceiling never re-derived (P-21/P-15)
claims          no gross-only claims; D2 eligible != profitable
```

## 9. Execution phases

```text
PC  XAUUSD-BROKER-COST-PROBE-V1 (pre-cycle, frozen contract, resumable)
PA  A7-XAU fresh-context audit of this plan + the probe contract
RG  researchctl registration ONLY after PROBE_PASS + PA AUTHORIZED
    (+ remediation of every valid HIGH/CRITICAL; REFUSED => fix => NEW
    fresh-context A7, never the same auditor re-approving)
M0  golden gate 11/11 before D1
P0  F1-F8 instrument/cost/macro/basis authority
D1  A + B freeze (outcome-blind), <= 3 cells / 1 family
D2  non-scored ancestry/feasibility/cost-ceiling measurement
S   selection + hash freeze; I isolated lanes; Z sanitized dry-run
A7  independent prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types `GO FOREX NG6R1 SCORED EXECUTION` at this cycle's own
    gate; early/paraphrased GO dies unconsumed (P-8)
E   <= 3 scored cells under the machine-wide heavy lock
R   detached reproduction; T terminal audit + two-half close
```

All lanes write `zcode_orch_v3_handoff@1` to their exact dispatch paths;
lanes never merge, rebase, push, edit registries/ledgers or read other
lanes' outcomes.

## 10. Trial accounting

Observed and published denominators counted separately; every computed
cell consumes an observed slot; unused slots never reassigned. Forex
denominators currently 48/48; program 257/260 (P-9). Starts at 0/3.

## 11. Prewritten terminal outcomes

```text
FOREX_NG6R1_BLOCKED_METHOD_CONTRACT
FOREX_NG6R1_BLOCKED_SOURCE_OR_COST
FOREX_NG6R1_BLOCKED_SOURCE_OR_SCHEMA
FOREX_NG6R1_BLOCKED_DATA_OR_SELECTION
FOREX_NG6R1_BLOCKED_PRELAUNCH
FOREX_NG6R1_REJECT_ALL
FOREX_NG6R1_INCOMPLETE_NOT_PROMOTABLE
FOREX_NG6R1_TECHABORT_PRESERVED
```

A correct early close is governance success. No predeclared survivor.

## 12. Boundaries

- Read-Only API only; no order placement, preview or transmit; Read-Only
  API never disabled; no account creation/funding; no credentials in
  prompts/logs/artifacts/git; the TWS API ZIP is never committed.
- No S1, no shadow reads, no scored execution without A7 prelaunch + the
  fresh exact owner GO; no push; no merge to main; no `.zcode/` writes.
- Registry only via researchctl; one heavy job machine-wide.
- No GLD/GC/MGC/XAUUSDT/TD-composite substitution in any direction.
- No budget/GO/rescue sharing with STOCKS-NG5 or the dead FOREX-NG6.

## 13. Immediate actions

```text
1. Freeze the probe contract (A3 lane draft -> controller freeze) under
   research/control/xauusd_ibkr_probe_2026-09/.
2. A7-XAU fresh-context audit of this plan + the probe contract.
3. Remediate every valid HIGH/CRITICAL; REFUSED => new fresh A7.
4. Run the probe when the TWS endpoint is available (resumable; honest
   coverage reporting; NOT_RUN_TWS_UNAVAILABLE recorded 2026-09-16).
5. Register FOREX-NG6R1 via researchctl ONLY after PROBE_PASS + AUTHORIZED.
6. Stop at the scored prelaunch gate; wait for the exact owner GO.
```
