# FX-FUTURES-FRONTIER-V1 — CME Micro FX futures as an independent FX vehicle (foundation/data/mechanism cycle)

> Status: `PLANNED_NOT_STARTED` at authoring. Registers ONLY after a
> fresh-context A7 plan audit returns AUTHORIZED with 0 unresolved
> HIGH/CRITICAL (remediation loop otherwise, fresh re-audit on any
> HIGH/CRITICAL; P-8 doctrine).
>
> Owner directive 2026-09-17 (verbatim authority, compacted): open a
> completely new foundation research cycle evaluating CME Micro FX Futures
> as an FX trading vehicle replacing spot-FX/CFD. The predecessor cycle
> FOREX-INTRA-BIDASK-V1 is TERMINAL `FOREX_INTRA_BIDASK_V1_BLOCKED_TRANSPORT`
> and must NOT be reopened, edited, deleted or re-verdicted. No Dukascopy,
> MT5 or OANDA in this cycle. The name FOREX-NG8 stays burned by
> predecessor law. This prompt is NOT a scored GO.

## 0. Cycle identity and ancestry

- `cycle_id`: **FX-FUTURES-FRONTIER-V1** (owner-proposed). Registry
  convention check (recorded for A7): the ID is unique in
  `plans/CYCLE_REGISTRY.json` (no cycle, live or terminal, uses it); it
  claims no predecessor identity; FOREX-NG8 remains unused; asset class is
  `forex` (the evaluated vehicle is an FX trading instrument). Evidence
  namespace `research/control/fx_futures_frontier_v1/`; governed raw root
  `/Users/hoangminhlong/.my-quantitative-data/fx-futures-frontier-v1/raw/`
  (outside git, never committed).
- Scientific change vs the blocked spot paths: the vehicle changes from
  spot-FX/CFD (broker quotes, financing/swap stack, OANDA/MT5/Dukascopy
  transport) to **exchange-traded CME Micro FX futures** — an independent
  instrument with its own contract identity, central-limit-book economics,
  official fee schedule, and where financing/carry is expressed in the
  futures **basis and roll structure** instead of a CFD swap line. This is
  a vehicle change, not a rename of any dead family; A5/A6/A7 adjudicate.
- Standing ancestry carried into every mechanism design: the full forex
  battery (FXFV1–FXFV7 session/clock/lead-lag/carry classes, FXNG1
  DGS10-level falsifications #14/#15, FXNG3 revision forms, FXNG4
  day-of-week geometry, NG5 veto battery), RATES-NG1 (clock-shadow
  falsification #16 — the AGGRESSIVE arm died because the release-calendar
  geometry out-earned the mechanism), COMMODITIES-NG1 (release-clock
  control out-earned every positioning anchor), plus the crypto/ng
  momentum/reversal/vol-shock shadow classes for cross-asset renames.
  HYPOTHESIS_LEDGER (P-9): program 257/260, 0 survivors; nothing here can
  move those denominators.

## 1. Hard boundaries (whole cycle)

- Budget `0/0` scored cells. NO GO phrase registered in this cycle.
  S1 `SEALED_UNTOUCHED`. Orders `NONE` (paper/testnet/live forbidden).
  PnL, profit, PF, Sharpe, drawdown, break-even FORBIDDEN at every depth —
  including "diagnostic" computations (P-15 posture: smoke numbers may
  kill + disclose only, and here none are produced at all; D2 measures
  observables, coverage, costs, correlations — never returns).
- No data purchases; no new accounts; no new API keys; no license/ToS
  acceptance on the owner's behalf; NO bypassing of DNS, network filters,
  paywalls or access controls (lesson L-FIBV1-1: a measured environment
  filter is an owner decision, never circumvented).
- Raw licensed bytes stay OUTSIDE git (governed root above). Only
  manifests, hashes, transcripts, dossiers and tests are committed.
- Missing evidence = `NOT_RUN` / `BLOCKED`; never an inferred PASS.
  Measured beats stated (Q-8) everywhere: contract specs, fees, hours,
  settlement rules are taken from fetched official pages/bytes (hashed
  into evidence), never from memory or unattached internet pages.
- Registry writes only via `research/researchctl.py`; lanes never merge/
  rebase/push/touch registries or other lanes; structured handoffs
  mandatory (`zcode_orch_v3_handoff@1`); one heavy job machine-wide
  (this cycle's lanes are LIGHT; max 3 concurrent light lanes).
- PROSPECTIVE-SHADOW-V1 (ACTIVE_LIGHT) and FOREX-NG6R1 (PAUSED) are never
  read or disturbed. FOREX-INTRA-BIDASK-V1 terminal artifacts are
  immutable evidence; its governed root is not written by this cycle.
  The MT5 cost probe stays `NOT_RUN_CONNECTIVITY`, untouched, not retried.
- IBKR/TWS: NOT retried in this cycle. An existing read-only channel may
  be used ONLY if a NEW preregistered diagnosis measures it working AND A7
  accepts the diagnosis; absent that, IBKR is out of scope.

## 2. Frozen subject and eligibility law

- Candidate universe (exactly these five): **M6E** Micro EUR/USD,
  **M6B** Micro GBP/USD, **M6A** Micro AUD/USD, **MCD** Micro CAD/USD,
  **MJY** Micro JPY/USD. All five start as CANDIDATES; none is guaranteed
  to live. Per-instrument eligibility is decided ONLY by the
  data/identity/liquidity/cost gates (§5–§6), never by profit (none can
  be computed). Instruments failing gates are recorded DEAD with the
  failing gate named; instruments passing carry a per-instrument
  eligibility row into the successor.
- Identity law: futures are NEVER called spot forex; never claimed
  equivalent to OANDA/Dukascopy/IBKR spot or CFDs; no CFD swap line
  exists — carry/financing content lives in the basis and roll structure
  and is analyzed as such. Every cost component starts UNKNOWN and is
  never set to 0 without measured/document-class authority.

## 3. Allowed sources (measured, canary-first)

- **CME Group** (official): contract specifications; contract calendar;
  expiry and settlement rules; daily settlement files; volume/open
  interest; exchange and clearing fee documentation.
- **CFTC**: Commitments of Traders (report calendar + correction policy;
  the COMMODITIES-NG1 release-clock lesson binds any CoT mechanism).
- **NY Fed / OFR / FRED**: rate/liquidity/macro context, each with an
  explicit availability clock (FDF-V1/V1R1 precedents: NY Fed reference
  rates, OFR SOFR official endpoints, FRED pinned series already proven
  reachable from this environment).
- **Twelve Data** (existing entitlement, no new key): spot prices ONLY as
  a diagnostic basis comparison against futures settlements — NEVER as a
  futures execution price, NEVER to back-fill futures history.
- Forbidden: undocumented endpoints; third-party mirrors without
  provenance; continuous futures series that cannot be reproduced from
  actual dated contracts; using the current front contract to rewrite
  history; back-adjustment computed with future information; scraping in
  violation of terms.
- Transport law (L-FIBV1-1 applied): canaries before any bulk; per-fetch
  transcript (url/method/status/content-type/bytes/sha256/fetched_at);
  deterministic re-fetch re-hash ALL_MATCH; HEAD-census with frozen
  etiquette (sequential, ≥1 s spacing, ≤2 retries exponential backoff,
  census volume cap 5 × (5 instruments × sampled-years × 8) probes);
  hard byte cap 300 MB total; on a connection-level block, run the
  SNI/destination-IP discrimination experiment and record it — a measured
  filter is a `BLOCKED_TRANSPORT` owner-action input, never bypassed.

## 4. Preregistered measurement contract (frozen before any outcome)

1. Per-instrument official identity pack (A2): exchange official name;
   actual contract codes and their naming scheme (month//year convention
   as served); contract multiplier/unit; tick size and tick value;
   trading hours as published; expiry cycle and last trade day;
   settlement/delivery mechanics (cash or physical); historical contract
   availability span; daily settlement availability; volume/OI
   availability; license/terms class (hashed pages, verbatim clauses);
   downloadable formats; PIT availability timestamp rule; transport
   canaries with full transcripts; raw manifest with byte sizes and
   SHA256.
2. Roll contract (A3, frozen before any data is seen): front contract
   selected ONLY by information available at decision time (calendar/
   days-to-expiry rules; volume/OI usage restricted to PIT-declared
   windows — never future volume); roll date rule and guard rails
   (expiry/delivery guard: no position concept may extend into the last
   K trading days before expiry — K frozen at selection time and never
   loosened); actual dated contracts only; no synthetic fills; no
   back-adjustment with future data; missing contract = `NOT_RUN`;
   timezone/DST normalized from measured evidence; duplicate/gap/outlier
   censuses with frozen definitions; settlement vs BBO/trade identity
   kept distinct and labeled; deterministic reconstruction + detached
   reproduction mandatory. **If only non-reproducible continuous series
   are obtainable, the cycle is `BLOCKED_ACTUAL_CONTRACT_HISTORY`.**
3. Cost stack (A4): per instrument — historical/current bid-ask authority
   (measured or classified with its evidence class); spread; exchange
   fee; clearing/regulatory fee; broker commission (UNKNOWN posture,
   never 0); minimum contract quantity; roll cost (measured from
   settlement-vs-settlement spreads across the frozen roll rule);
   slippage (stress coverage); margin (report-only, never a profit
   input); contract notional. Stress ladder frozen NOW: observed/base,
   1.5x, 2.0x. Capital feasibility per instrument for $1,000 / $10,000 /
   $300,000 with a frozen definition: tier C feasible iff official
   initial margin ≤ C/2 AND estimated all-in round-trip cost at the
   observed tier ≤ 0.5% of C (margin and costs as measured; the
   feasibility table is a standing output; the gate fails only if NO
   tier is feasible). **Without a measured or document-classified spread
   authority and commission authority, no scored successor may be
   opened** (§8) and the terminal mapping fires `BLOCKED_COST_AUTHORITY`.
4. Mechanism classes (A5, outcome-blind, ≤ 3): (i) front/next-contract
   basis or roll-curve dislocation; (ii) volume/open-interest absorption
   around scheduled macro events; (iii) cross-currency futures
   relative-value pressure conditioned on rate/liquidity information
   from CFTC/NY Fed/OFR/FRED. Each candidate carries: economic mechanism
   (who is forced and why it exists); exact availability clock for every
   input; falsifier; negative controls (including a clock-only shadow —
   the RATES-NG1/COMMODITIES-NG1 law); state variables; direction
   freeze; full forex/rates/commodities ancestry mapping; explicit tests
   that it is not momentum/reversal/carry/session-pattern renamed. No
   returns or PnL anywhere in any dossier.
5. D2 battery (§6) runs before any successor and computes no PnL.

## 5. Lanes (independent, outcome-blind)

- **A2 — instrument/source/license researcher** (`fxf-a2`): the §4.1
  identity pack for all five instruments; canaries per §3; transcripts +
  SHA256 manifests; license/terms classification. Verdict per instrument:
  `SOURCE_ELIGIBLE` | `SOURCE_DEAD_<gate>`; lane verdict
  `PASS_SOURCES_MEASURED` | `BLOCKED_LICENSE_OR_ENTITLEMENT` |
  `BLOCKED_TRANSPORT`.
- **A3 — actual-contract and roll auditor** (`fxf-a3`; after A2): the
  §4.2 roll contract executed against actual dated contracts; PIT
  front-selection; roll reconstruction; coverage per contract/year;
  deterministic reconstruction + detached reproduction; continuous-
  synthetic-only detection. Verdict: `PASS_ACTUAL_CONTRACT_ROLL` |
  `BLOCKED_ACTUAL_CONTRACT_HISTORY` | `BLOCKED_PIT_ROLL_CONSTRUCTION` |
  `BLOCKED_SCHEMA_OR_IDENTITY`.
- **A4 — cost and tradability auditor** (`fxf-a4`; after A3): the §4.3
  cost stack + capital feasibility table; stress ladder frozen. Verdict:
  `PASS_COST_STACK_MEASURED` | `BLOCKED_COST_AUTHORITY` |
  `BLOCKED_CAPITAL_FEASIBILITY` | `BLOCKED_LIQUIDITY_OR_BBO`.
- **A5 — mechanism and ancestry researcher** (`fxf-a5`; after A2–A4):
  ≤ 3 candidate classes per §4.4 with declared representations; the
  shadow-ancestry inventory and kill-control list; the
  structural-vehicle-change adjudication dossier (futures vs spot is a
  vehicle change with its own cost/roll/basis structure — not a rename;
  A4 authors evidence, A6 attacks, A7 judges). Per candidate:
  `CANDIDATE_LISTED` | `ANCESTRY_DEAD` | `NOT_RUN`.
- **A6 — hostile critic** (`fxf-a6`; reads A2–A5): attacks — micro
  contracts too thin; spread/BBO missing; settlements not executable;
  continuous-series lookahead; roll-rule shopping; basis is old carry
  renamed; CFTC information too slow; macro timing leaks; commission/
  roll cost kill the edge; $1,000 insufficient capital; broker/account
  cannot trade futures; physical-delivery risk; unstable instrument
  identity; plus any invented attack. Every attack dispositioned with
  evidence or CONCEDED; an unresolved BINDING attack maps to
  `BLOCKED_*` (data/cost layers) or `PASS_DATA_CONTROL_ONLY` /
  `ANCESTRY_DEAD` (mechanism layer) per §7.
- **A7 — independent auditor** (`quant-auditor`, fresh-context): r1
  audits this plan BEFORE registration (authority chain; new identity;
  old cycles immutable; no ancestry dodge; actual-contract/PIT roll
  contract; source and license law; complete cost stack; capital
  feasibility; verdict mapping; S1/order/PnL boundaries; successor and
  owner-GO law). A7 never edits the plan; HIGH/CRITICAL → remediation
  lane + fresh re-audit. r2 = terminal audit, independently reproducing
  the material conclusions from committed bytes.

## 6. D2 — non-scored battery (before any successor; NO PnL)

1. Official instrument identity (all five, from official bytes/pages).
2. Actual-contract history (dated contracts, not synthetic).
3. PIT front-contract selection (decision-time information only).
4. Roll reconstruction (deterministic, frozen rule).
5. Coverage per contract/year.
6. Volume/open-interest coverage.
7. Liquidity and BBO/spread census (frozen floors; settlement vs BBO
   identity distinct).
8. Complete cost-stack authority (every component measured or
   document-classified; none zeroed).
9. Capital feasibility ($1k/$10k/$300k per frozen definition).
10. Expiry/delivery guard (frozen K, enforced in the reconstruction).
11. Ancestry and novelty tests (renames detected, not asserted).
12. Pooled |rho| ≤ 0.20 against declared dead-family shadows (§0 panel).
13. Fold-population census (Q-6 recent-window feasibility).
14. Detached reproduction (byte-level, evidence chain).
15. A7 independent recomputation.

## 7. Preregistered terminal verdicts (exact, negative-first, deterministic)

Required proofs R1–R15 = D2 items 1–15, each recorded PASS/FAIL/NOT_RUN/
BLOCKED with evidence, plus (R16) per-instrument eligibility rows and
(R17) A6 disposition table. Mapping, first matching rule wins:

1. License/entitlement of an allowed source measured insufficient →
   **`BLOCKED_LICENSE_OR_ENTITLEMENT`**
2. Transport fails under the frozen etiquette (with the L-FIBV1-1
   discrimination evidence attached) → **`BLOCKED_TRANSPORT`**
3. Actual dated-contract history unobtainable / only non-reproducible
   continuous series → **`BLOCKED_ACTUAL_CONTRACT_HISTORY`**
4. Instrument identity unstable (codes/multiplier/tick mismatch vs
   official records; settlement/BBO identity conflated) →
   **`BLOCKED_SCHEMA_OR_IDENTITY`**
5. PIT front-selection or roll reconstruction fails (lookahead, future
   back-adjustment, non-determinism, guard violation) →
   **`BLOCKED_PIT_ROLL_CONSTRUCTION`**
6. Liquidity/BBO/spread census below the frozen floors →
   **`BLOCKED_LIQUIDITY_OR_BBO`**
7. Spread or commission authority unmeasurable/absent from the authorized
   evidence space → **`BLOCKED_COST_AUTHORITY`**
8. No capital tier ($1k/$10k/$300k) feasible per the frozen definition →
   **`BLOCKED_CAPITAL_FEASIBILITY`**
9. Every A5 candidate measured dead (rename test fires or pooled |rho| >
   0.20 vs dead shadows) → **`ANCESTRY_DEAD`**
10. Any of R1–R17 `NOT_RUN`/unresolved with no rule above fired →
    **`INCOMPLETE_NOT_PROMOTABLE`**
11. R1–R15 PASS + ≥ 1 candidate `CANDIDATE_LISTED` passing D2-11/12/13 +
    A6 binding attacks all dispositioned + A7 terminal independent
    re-verification → **`PASS_FX_FUTURES_RESEARCH_AUTHORITY`** — a
    RESEARCH authority only; PASS never means profitable; limitations
    stand verbatim in every artifact.
12. Data gates (rules 1–8 clean) but the mechanism layer fails
    non-fatally (fold population, timing-too-slow, or a binding A6 attack
    on the mechanism layer) → **`PASS_DATA_CONTROL_ONLY`** (data plane
    usable as control only; NO scored successor).

## 8. Successor law

If and ONLY if terminal = `PASS_FX_FUTURES_RESEARCH_AUTHORITY` with A7
independent reproduction: the Lead may AUTHOR a successor plan (working
name `FX-FUTURES-FRONTIER-V2`; GO phrase `GO FX FUTURES FRONTIER V2
SCORED EXECUTION`, registered at the successor's registration and typed
ONLY by the owner at the successor's own prelaunch gate). Successor
structure, immutable: exactly one family; ≤ 3 scored cells; actual
contracts only (no synthetic execution); the frozen roll rule immutable;
complete cost stack (spread + commission authority present); full
ancestry battery; D2 non-scored; fresh-context A7 prelaunch; then scoring
→ reproduction → terminal audit → two-half close. The Lead STOPS before
any scored execution and reports the exact GO phrase. This directive is
NOT a scored GO.

`PASS_DATA_CONTROL_ONLY`, `ANCESTRY_DEAD`, any BLOCKED, or INCOMPLETE:
NO successor. The cycle closes honestly; no source change, family change
or parameter rescue after results are seen.

## 9. Process

```text
G0  intake (2026-09-17, this session): main@d9e11a42 measured; registry/
    doctor/locks/store clean; PREDECESSOR terminal rows confirmed immutable
    (FOREX-INTRA-BIDASK-V1 558b366c, DEU-V1 0f6cee90, NG1..NG7 all TERMINAL)
G1  plan committed to main -> fresh-context A7 plan audit ->
    AUTHORIZED with 0 unresolved HIGH/CRITICAL (remediation loop on
    anything else; fresh re-audit on HIGH/CRITICAL)
G2  registration AFTER audit: researchctl cycle register (budget 0/0,
    NO GO phrase); worktrees .worktrees/fx-futures-frontier-v1/
    {integration,lane-a2..lane-a6} from the plan tip; orchestrator tasks
    with dependency chain (store-level cycle_id mislabel disclosed)
G3  waves (sequential, ≤3 concurrent light lanes):
    a2 sources/license -> a3 contracts/roll -> a4 costs/capital ->
    a5 mechanisms/ancestry -> a6 hostile critic
G4  D2 battery (15 items) from frozen definitions
G5  integration: sequential cherry-picks, targeted tests per pick
G6  terminal A7 (fresh-context, independent recomputation); HIGH/CRITICAL
    -> remediation + fresh re-audit
G7  two-half close: terminal verdict per §7 on the integration branch;
    registry TERMINAL + MAP + lessons (if any); denominators unchanged
    257/260; FAMILY_FAILURES rows only for measured D2 kills of A5
    candidates; no hypothesis-ledger family rows (nothing scored);
    ELI5 Vietnamese owner report (the ten questions of the directive)
```

## 10. Incident transparency

Hook refusals, dirty-tree anomalies, transport failures, cap breaches,
schema drift and authority ambiguities are recorded same-session
(what/scope/exposure/repair/prevention; handbook §26). Fetch failures
fail LOUD (Q-13). Standing incidents at intake: the disclosed residual
store rows of the previous close (INC-FIBV1-1/2 and the three MOOT
fibv1-a3/a4/a5 rows of the TERMINAL predecessor) are inherited as-is —
this cycle neither claims nor retires them.
