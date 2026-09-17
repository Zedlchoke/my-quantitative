# FOREX-INTRA-BIDASK-V1 — intraday bid/ask research foundation (rollover-flat by design)

> Status: `PLANNED_NOT_STARTED` at authoring. Registers ONLY after a
> fresh-context A7 plan audit returns AUTHORIZED with 0 unresolved
> HIGH/CRITICAL (P-8 doctrine; DEU-V1 precedent).
>
> Owner directive 2026-09-17 (verbatim authority, translated compactly):
> open a new Forex direction that can work WITHOUT OANDA/MT5 and without
> assuming swap = 0. Mandatory direction: FOREX INTRADAY on historical
> BID/ASK data; every position must close BEFORE rollover. Priority source
> to test: Dukascopy Historical Data. First cycle must be a
> foundation/data-authority cycle: budget `0 scored cells`, S1
> `SEALED_UNTOUCHED`, orders `NONE`, PnL/profit/PF/Sharpe/drawdown
> `FORBIDDEN`, no API key or broker account, no paper/testnet/live order,
> no bulk download before license + transport + schema gates PASS.
>
> This is a data-authority cycle. Denominators stay 257/260 (P-9) — nothing
> here can move them.

## 0. Why this cycle exists (ancestry, and what changed)

**The killer it addresses.** FOREX-NG7 closed
`FOREX_NG7_BLOCKED_SOURCE_OR_SCHEMA` at P0-F4: "NO citable financing band
in the authorized evidence space (TD=vendor OHLC-only; FOREX-NG6 P0-F4
precedent class)" — the trigger census was feasible (721/802/674 per fold);
"the family died on cost authority, not data". Reopening condition verbatim:
"owner broker-grade cost authority for TD majors". DATA-EDGE-UNLOCK-V1 Lane
F then measured a THIRD independent census: zero account-bound bytes
anywhere in existing entitlements → `BLOCKED_BROKER_COST_AUTHORITY`; owner
deliverables A/B/C recorded; "**no FOREX-NG8**" (the name FOREX-NG8 is
BURNED by that law and is NOT used by this cycle). The MT5 cost probe
(`research/control/forex_mt5_cost_probe_2026-09/`) is standing evidence at
`NOT_RUN_CONNECTIVITY`: A7 pre-deploy r2 AUTHORIZED_WITH_FINDINGS, but the
owner has not executed the F7-compile + 30-min smoke; this cycle does NOT
retry MT5/OANDA and does NOT touch that probe.

**The scientific change (owner-specified).** Old killer: a strategy may hold
through rollover, so swap long/short, triple swap and the rollover clock are
unmeasurable cost components, and without account-bound bytes the financed
book is NOT_MEASURABLE. New design: research is INTRADAY ONLY; every
position is force-closed before rollover by a preregistered buffer; NO
position is ever open across the financing timestamp. Because no overnight
exposure can exist, financing/swap is **not a component of the trade design
at all** — this is structural exclusion by construction, NOT a substitution
of swap by 0 (the DEU-V1 Lane-F prohibition targets silent zero-fill of an
exposure that exists; here the exposure is made impossible by the holding
contract, and the impossibility itself is a tested property — D2-2). A4/A5/A7
must adjudicate this as a valid structural change vs an ancestry dodge; if
dodge, the cycle fails closed (verdict mapping §7).

**What this cycle is NOT.** Not a rescue of FOREX-NG7; not a rename of the
dead session families (FXFV1 London-open continuation / late-NY fade, FXFV2
range compression/breakout) or the dead clock/lead-lag classes (FXFV5/FXFV7,
FXNG1 release-order) or the nominal-exposure class (FXFV8/FXNG1 DGS10-level
shadow, falsification-by-control #14/#15); not an executable-strategy
authority claim; not market-wide data (Dukascopy quotes are broker quotes);
never an equivalence claim to OANDA or IBKR execution.

## 1. Hard boundaries (whole cycle)

- Budget `0/0` scored cells. S1 `SEALED_UNTOUCHED`. Orders `NONE` (paper/
  testnet/live all forbidden). PnL/PF/Sharpe/MDD/break-even are FORBIDDEN at
  every depth — including "diagnostic" and smoke-namespace scoring (P-15:
  smoke numbers may only kill + disclose, and here they may not exist at
  all; D2 measures observables and correlations, never PnL).
- No API keys, no accounts, no purchases, no license acceptance, no
  credentials in prompts/logs/git.
- NO bulk download before license, transport AND schema gates PASS (§3
  canary cap; availability census uses HEAD/manifest probes on a frozen
  stratified sample, never wholesale fetch). No synthetic backfill. Missing
  evidence is `NOT_RUN`, never inferred PASS.
- Raw downloaded bytes NEVER enter git — governed data root only:
  `/Users/hoangminhlong/.my-quantitative-data/forex-intra-bidask-v1/raw/`.
  Only manifests, hashes, transcripts, dossiers, tests are committed.
- Registry writes only via `research/researchctl.py`. Lanes never merge,
  rebase, push, touch ledgers/registries/other lanes. Structured handoffs
  mandatory (`zcode_orch_v3_handoff@1` at the exact `handoff_path`).
  One heavy job machine-wide; all lanes here are LIGHT. Max 3 light lanes
  concurrent (8GB host).
- PROSPECTIVE-SHADOW-V1 (ACTIVE_LIGHT) and FOREX-NG6R1 (PAUSED,
  XAUUSD/TWS) are never read or disturbed. The MT5 probe directory is
  read-only context, never executed by this cycle.
- Measured beats stated (Q-8) everywhere: every Dukascopy property (quote
  sidedness, timezone, coverage) must come from fetched bytes or official
  pages hashed into evidence — never from an unattached internet page or
  memory.

## 2. Cycle identity

- `cycle_id`: **FOREX-INTRA-BIDASK-V1** (fresh identity; the FOREX-NG8 slot
  is burned by DEU-V1 Lane-F law and remains burned regardless of this
  cycle's outcome).
- asset: forex. Plan: `plans/PLAN_forex_intra_bidask_v1.md`.
- Integration: `.worktrees/forex-intra-bidask-v1/integration` on
  `orca/fibv1-integration`. Lanes: `.worktrees/forex-intra-bidask-v1/{lane-a2,
  lane-a3, lane-a4, lane-a5}` on `orca/fibv1-a2|a3|a4|a5`. Evidence
  namespace (committed): `research/control/forex_intra_bidask_v1/`.
- Budget 0/0. NO GO phrase in this cycle (nothing scored exists to
  authorize). The successor's own GO phrase is named in §8.

## 3. Frozen subject and acquisition law (freeze BEFORE any fetch)

- **Exactly 5 pairs**: EURUSD, GBPUSD, AUDUSD, USDCAD, NZDUSD (the TD-majors
  lineage). No other symbol, no XAUUSD.
- **Source**: Dukascopy Historical Data via Dukascopy's own documented
  public surfaces only (official historical datafeed URLs / JForex or
  web CSV-tick export as measured reachable). Third-party mirrors,
  scrapes of aggregators, and unauthenticated undocumented endpoints are
  forbidden. A2 hashes every license/terms page relied upon.
- **Canary cap (bulk protection)**: total raw bytes ≤ 300 MB for the whole
  cycle; per fetch batch the manifest is frozen BEFORE fetching. Canary
  set (frozen): per pair — (i) one recent full UTC trading day of
  bid/ask ticks, (ii) one historical day ≥ 3 years old, (iii) hourly
  files spanning one March DST transition; plus per pair × per year
  availability HEAD-census on ≥ 8 stratified sampled hours (including a
  DST boundary, a Friday-close hour, a Sunday-open hour). If the measured
  transport cannot express this census, that is a `BLOCKED_TRANSPORT`
  input, not a reason to bulk-fetch.
- **Census request etiquette (frozen, A7 r1 F-6)**: HEAD probes only;
  sequential with ≥ 1 s spacing; ≤ 2 retries with exponential backoff per
  probe; no concurrent hammering; single HTTP session; census volume cap
  = 5 × (pairs × sampled-years × 8) probes. Any 4XX/5XX pattern is
  EVIDENCE (a `BLOCKED_TRANSPORT` input), never a reason to escalate
  request volume.
- **Transport evidence per fetch**: url, method, HTTP status, content-type,
  byte size, fetched_at_utc, sha256 — committed as transcript; deterministic
  re-fetch (or documented archive-immutability behavior) required; re-hash
  ALL_MATCH for every canary.
- **No attribution of Dukascopy quotes as market-wide, executable, or
  OANDA/IBKR-equivalent** — anywhere, by any lane, ever.

## 4. Preregistered research contract (frozen now; binds the successor)

1. Pairs: exactly the five in §3.
2. Source and quote identity: real two-sided BID and ASK tick series
   required; midpoint-only or OHLC-only = `BLOCKED_SCHEMA_OR_IDENTITY`.
3. Time: all decision logic in UTC; source-native timezone measured from
   bytes (never assumed); DST normalization frozen from the measured
   transition canaries; timestamps strictly monotonic per pair.
4. Rollover clock: 17:00 America/New_York (22:00 UTC in EST, 21:00 UTC in
   EDT) — the financing instant positions must never reach.
5. Safety buffer: every position force-flat at `rollover_instant − 300 s`
   (buffer 300 s frozen; a successor may tighten it, never loosen without a
   new plan).
6. Maximum holding duration: 8 h; any entry whose forced exit would land
   inside the buffer window is forbidden by construction.
7. Sessions (A7 r1 F-4 closing the literal hole): entries are forbidden
   inside the window `[rollover_instant − 2100 s, rollover_instant]` —
   this INCLUDES the buffer window itself — and across weekend gaps. No
   position may be opened at ANY time whose forced exit would land inside
   `[rollover_instant − 300 s, rollover_instant + 3600 s]`; forced exit =
   the contract-mandated action that makes the book flat at the buffer
   (rollover_instant − 300 s). Finer session bounds are frozen at
   successor selection under a rubric frozen NOW (A7 r1 F-3): successor
   bounds may only NARROW these outer bounds, must be derived from
   measured session-structure evidence produced by this cycle, and must
   be frozen in the successor's selection-freeze BEFORE any scored
   computation exists.
8. Fills: long entry = ASK, long exit = BID; short entry = BID, short exit
   = ASK; midpoint fills FORBIDDEN.
9. Spread is read at the exact decision timestamp from the same quote
   series (never a daily average, never a later snapshot).
10. Missing quote at any required instant = `NOT_RUN` for that decision —
    no forward-fill, no interpolation, no synthetic backfill.
11. Commission: `UNKNOWN` posture — never 0, never inferred. If no valid
    commission authority is constructible in the successor, the successor
    may still hold DATA/CONTROL authority but is barred forever from
    executable/profitable authority claims by this plan's law.
12. Cost stresses frozen: spread-derived cost ladder 1.0x / 1.5x / 2.0x
    (successor scoring must survive the full ladder to pass).
13. Target-broker mismatch (Dukascopy historical quote vs any target
    broker's executable spread) is a STANDING LIMITATION recorded in every
    successor artifact; it is never argued away.
14. Folds: 3 contiguous time folds; embargo ≥ 5 trading days at every
    train/eval boundary; trial accounting per P-9 (observed vs published
    kept separate); ancestry bar pooled |rho| ≤ 0.20 (program law) on the
    declared representation.
15. Data-quality and coverage floors (byte-level, on the fetched canary
    set; A3 audits, A7 re-verifies): bid>0 and ask>0 always; crossed
    quotes (ask<bid) = 0 — locked (ask==bid) allowed but counted and
    disclosed per pair; exact-duplicate tick rate ≤ 1% (definition frozen:
    identical timestamp+bid+ask rows); monotonic-timestamp violations = 0
    else fail-closed; DST boundary hours populated; staleness (no quote
    change ≥ 300 s during official market hours) and outlier/bad-tick
    (jump ≥ 50× recent spread reverting within 5 s) censused with frozen
    definitions; pair identity/orientation (quote currency is the second
    symbol; one pip = 1e-4 except JPY-quote pairs, none in this set)
    verified. Depth floor: per pair, availability census (HEAD probes) must
    evidence history ≥ 3 years back to within the sampled-year structure of
    §3; the ≥95%-of-trading-days-per-year byte-level floor is a SUCCESSOR
    acquisition floor, restated here so it cannot be invented later.
16. Stopping rule (outcome-independent): each lane runs its frozen
    checklist to completion and records every item PASS/FAIL/NOT_RUN/
    BLOCKED; the cycle is terminal when all dossiers + the D2 battery +
    A7 audits are recorded. No interim re-scoping, no floor renegotiation
    after bytes are seen.

## 5. Lanes (outcome-blind; there is no outcome to see)

- **A2 — source/license/transport researcher** (`fibv1-a2`): license and
  terms-of-use from official pages (hashed into evidence); whether the
  documented CSV/JForex-tick export actually works; whether tick data is
  real BID+ASK (two-sided) vs midpoint/OHLC-only; timestamp/timezone as
  served; available history per pair (census per §3); execute the frozen
  canary manifest; write transcripts + SHA256 manifests; raw bytes to the
  governed root. Verdicts: `PASS_SOURCE_AUTHORIZED` |
  `BLOCKED_LICENSE_OR_TERMS` | `BLOCKED_TRANSPORT`.
- **A3 — PIT/schema/quality auditor** (`fibv1-a3`, independent of A2's
  conclusions): bid ≤ ask; crossed/locked census; duplicates; missing
  intervals vs the FX weekly calendar and market closures; timestamp
  monotonicity; DST/UTC normalization; stale quotes; outliers/bad ticks;
  pair identity and quote orientation; per pair × year × session coverage;
  deterministic manifest + detached reproduction of the evidence chain;
  label Dukascopy quotes as BROKER QUOTES (never market-wide); verify no
  lane claims OANDA/IBKR equivalence. Verdict: per-check PASS/FAIL/NOT_RUN
  + `PASS_QUALITY` | `BLOCKED_SCHEMA_OR_IDENTITY` |
  `BLOCKED_COVERAGE_OR_QUALITY`.
- **A4 — mechanism and ancestry researcher** (`fibv1-a4`; dispatched only
  after A2+A3 dossiers land, still before any outcome — none exists):
  designs candidate INTRADAY mechanism classes whose information set is
  genuinely new vs TD daily OHLC — candidates from: session-transition
  microstructure, spread/liquidity dislocation, bid/ask recovery dynamics,
  cross-pair timing structure. Must NOT rename momentum/reversal/breakout
  or session-continuation dead families; must produce the full shadow
  ancestry inventory + kill-control list the successor must carry.
  Verdict per candidate: `CANDIDATE_LISTED` | `ANCESTRY_DEAD` | `NOT_RUN`.
- **A5 — hostile critic** (`fibv1-a5`; reads A2–A4): attacks — no usage
  rights; quotes not executable; historical spread unrepresentative of any
  target broker; rollover avoidance is an ancestry dodge; spread/session
  state is a price proxy in disguise; commission/slippage absent; timestamp
  leaks; coverage bias; cost stress evaporates the edge. Every attack
  dispositioned with evidence or CONCEDED (a conceded attack that hits a
  binding floor feeds the verdict mapping §7).
- **A7 — fresh-context independent auditor** (`quant-auditor`): r1 audits
  THIS plan before registration; r2 audits the terminal evidence (§6–7)
  independently, recomputing what is recomputable. HIGH/CRITICAL →
  remediation lane + fresh re-audit before terminal. A7 never repairs and
  never audits its own prior work.

## 6. D2 — non-scored verification battery (BEFORE any successor scoring)

- **D2-1 identity**: consolidated two-sided-quote proof (A2+A3), pair
  identity/orientation, UTC/DST normalization — from bytes.
- **D2-2 rollover-flat property**: deterministic property test (pure
  function, fixture-tested, NO PnL) proving the §4 contract cannot hold a
  position across the buffer — including the 8 h max-hold interaction and
  the Friday/weekend boundary.
- **D2-3 novelty**: the declared representation of each A4 candidate
  measured against the dead-family shadow panel — FXFV1 session
  continuation, FXFV2 range compression/breakout, FXFV3 policy-rate-diff
  carry (PIT-invalidated), FXFV4 commodity-bloc exposure, FXFV5
  sham-calendar/CPI avoidance, FXFV6 CPI reaction-direction near-miss
  class, FXFV7 lead-lag/spillover, FXNG1 release-order + DGS10-level
  class (falsifications #14/#15), FXNG3 revision-form class, FXNG4
  day-of-week geometry class, and the NG5 D2 veto battery classes (A7 r1
  F-5) — and against TD-daily-OHLC-derivable proxies; pooled |rho| ≤ 0.20
  bar. Measurement of observables/correlations only — no PnL, no
  scoring, no cells consumed.
- **D2-4 feasibility census**: recent-window decision counts (Q-6), fold
  population, coverage floors on the canary+census evidence.
- **D2-5 structural adjudication**: is rollover-flat intraday a valid
  structural change vs an ancestry dodge? Criteria frozen NOW (A7 r1
  F-2). **VALID iff ALL of**: (a) D2-2 proves the holding contract makes
  financing exposure structurally impossible — no position can exist at
  the financing instant (property test + hand-computed fixtures);
  (b) design-level proof that every `CANDIDATE_LISTED` mechanism requires
  no financing/swap number of any value (a structural argument, not a
  substituted number); (c) ≥ 1 candidate passes D2-3 novelty.
  **DODGE** otherwise. Adjudication ownership: A4 authors the
  adjudication dossier with evidence; A5 attacks it; A7 audits it; the
  Lead RECORDS the joint outcome and may never adjudicate unilaterally;
  any unresolved disagreement resolves fail-closed to
  `INCOMPLETE_NOT_PROMOTABLE`.

## 7. Preregistered terminal verdicts (exact, negative-first)

Deterministic mapping (first matching rule wins; every gate verdict is
PASS/FAIL/NOT_RUN/BLOCKED with evidence):

0. Required proofs enumerated (A7 r1 F-1): (R1) A2 lane verdict
   `PASS_SOURCE_AUTHORIZED`; (R2) A3 per-check PASS set on §4.15 floors;
   (R3) canary re-hash ALL_MATCH per §3; (R4) D2-1 identity PASS;
   (R5) D2-2 rollover-flat property PASS; (R6) D2-3 novelty PASS on ≥ 1
   candidate; (R7) D2-4 feasibility PASS; (R8) D2-5 adjudication VALID;
   (R9) every A5 binding-floor attack dispositioned (evidence-backed or
   conceded); (R10) A7 terminal AUTHORIZED. A terminal rule-6 PASS
   requires R1–R10 all in their PASS/VALID state; any other state of any
   required proof resolves through rules 1–8 below, never to a PASS.
1. A2 license/terms fails → **`BLOCKED_LICENSE_OR_TERMS`**
2. A2 transport/canary cap fails or re-hash not ALL_MATCH →
   **`BLOCKED_TRANSPORT`**
3. Two-sided bid/ask unproven, or pair identity/orientation fails →
   **`BLOCKED_SCHEMA_OR_IDENTITY`**
4. Any §4 byte-level floor fails → **`BLOCKED_COVERAGE_OR_QUALITY`**
5. Data gates 1–4 all PASS, and (D2-5 adjudicates DODGE, OR D2-3 novelty
   fails for every candidate, OR D2-2 rollover-flat property or D2-4
   feasibility fails while data gates stand) →
   **`PASS_DATA_CONTROL_ONLY`** (data is sound as a control plane; NO
   scored successor may be opened from it)
6. Data gates 1–4 PASS + R5/R6/R7/R8/R9 all PASS/VALID + A7 terminal
   AUTHORIZED → **`PASS_INTRADAY_BIDASK_RESEARCH_AUTHORITY`** — a
   RESEARCH authority only. It NEVER asserts executable or profitable
   authority; commission stays UNKNOWN-posture and the §4.11/4.13
   limitations stand verbatim.
7. Any required proof R1–R10 ends `NOT_RUN` (or unresolved) at terminal,
   and no rule 1–5 condition fired → **`INCOMPLETE_NOT_PROMOTABLE`**
8. A5/A7 evidence that the data gates PASS but the cost/execution
   identity class itself is unsound in a way 5–6 do not cover →
   **`BLOCKED_COST_OR_EXECUTION_IDENTITY`**

A conceded A5 binding attack maps to the rule of the gate it attacks
(data floor → 4; quote identity → 3; transport/license → 1–2; cost/execution
class → 8; structural validity → 5).

`PASS_INTRADAY_BIDASK_RESEARCH_AUTHORITY` requires A7 independent
re-verification (fresh-context) of the D2 battery and the evidence chain.
Missing evidence is never a PASS.

## 8. Successor law (post-terminal; owner-visible)

If and ONLY if terminal = `PASS_INTRADAY_BIDASK_RESEARCH_AUTHORITY` with
A7 re-verification: the Lead may AUTHOR a successor plan (working name
`FOREX-INTRA-BIDASK-V2`; its GO phrase `GO FOREX INTRA BIDASK V2 SCORED
EXECUTION` is registered at the successor's own registration and typed ONLY
by the owner at the successor's own prelaunch gate). Successor structure,
immutable from this plan: exactly 1 family, ≤ 3 scored cells; family/
mechanism/direction frozen BEFORE scoring; max-hold and rollover-flat rule
IMMUTABLE (§4.4–4.7); full forex ancestry battery (§6 D2-3 panel + the A4
shadow inventory); D2 non-scored first; fresh-context A7 prelaunch; then
scoring → reproduction → terminal audit → two-half close; S1 stays sealed
until a valid gate. The Lead STOPS before any scored execution and reports
the exact GO phrase to the owner. This directive is NOT a scored GO.

`PASS_DATA_CONTROL_ONLY`, any BLOCKED, or INCOMPLETE: NO successor. The
cycle closes honestly; FOREX-NG8 remains burned regardless.

## 9. Process gates

```text
G0  intake (DONE 2026-09-17): main@683ea65c measured; registry/locks/store/
    denominators read; DEU-V1 + FOREX-NG7 TERMINAL confirmed; MT5 probe
    NOT_RUN_CONNECTIVITY recorded; stale store row deu-a7-cycle-audit
    disclosed (INC-FIBV1-1, transition-lawful retirement refused by the
    state machine; no work exists for it)
G1  this plan committed to main; fresh-context A7 plan audit ->
    AUTHORIZED with 0 unresolved HIGH/CRITICAL (remediation loop otherwise)
G2  registration AFTER audit: researchctl cycle register (budget 0/0,
    NO GO phrase); worktrees + orchestrator tasks registered (store-level
    cycle_id mislabel disclosed per single-cycle-store limitation, NG1
    precedent)
G3  wave 1: fibv1-a2 (source/license/transport, canaries per §3)
    wave 2: fibv1-a3 (independent quality audit of the exact fetched bytes)
    wave 3: fibv1-a4 (mechanism/ancestry design; reads A2+A3 dossiers)
    wave 4: fibv1-a5 (hostile critic; reads A2–A4)
G4  D2 battery (Lead-side or small lane) from frozen definitions
G5  integration: sequential cherry-picks into the integration worktree,
    targeted tests after each pick, one event per pick
G6  terminal A7 (fresh-context): audits the WHOLE cycle, recomputes D2;
    HIGH/CRITICAL -> remediation + fresh re-audit
G7  terminal: verdict per §7 mapping; two-half close (registry TERMINAL +
    MAP + lessons if any; denominators unchanged 257/260; FAMILY_FAILURES
    rows appended only for measured D2 kills of A4 candidates, NG3/NG4
    precedent; no hypothesis-ledger family rows — nothing scored);
    successor eligibility report to owner per §8; the owner handoff is
    written in ELI5 Vietnamese whose conclusion words are ONLY
    PASS / FAIL / BLOCKED / NOT_RUN (A7 r1 F-7)
```

## 10. Incident transparency

Any hook refusal, dirty-tree anomaly, transport failure, cap breach,
schema drift or authority ambiguity is recorded the same session with
what/scope/exposure/repair/prevention (handbook §26). Fetch failures fail
LOUD (Q-13). The disclosed standing incidents at intake: INC-FIBV1-1
(stale ready task `deu-a7-cycle-audit`, superseded by deu-a7-t2,
state machine correctly refuses backward retirement); MT5 probe
`NOT_RUN_CONNECTIVITY` (owner actions pending; untouched here).
