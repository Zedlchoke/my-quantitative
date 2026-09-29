# PLAN_portfolio_composite_12assets_100k_v1 — DRAFT v2 FOR OWNER (2026-09-29)

**Cycle ID (proposed):** PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 · **Status:
DRAFT v2, NOT REGISTERED.** Nothing in this plan is a GO. No scored cell, no
S1, no worker, no registry write has occurred for this cycle. Registration
requires the owner's typed phrase at §9 (P-8 two-key law: A7 first).
**v2 change of law:** per owner directive 2026-09-29 (2nd), recorded
verbatim in `plan/AMENDMENT_OWNER_DIRECTIVE_2026-09-29.md` — sub-strategy
novelty is NO LONGER an admission gate; old-family and previously-rejected
ideas enter as DIAGNOSTIC candidates with outcome-exposed labels; the
acceptance bar (untouched-fold after-cost PnL AND drawdown vs baselines)
is unchanged and non-negotiable.

## 0. Question and honest prior

**Question (owner, 2026-09-29, as amended):** does ONE portfolio-level
policy — deciding at each time which sub-strategies are ON/OFF, direction
and size, conflict resolution, per-asset/cluster exposure limits, and when
to stand outside — raise net PnL after all costs AND cut drawdown versus
legitimate baselines, on up to 12 assets, using 0..N sub-strategies per
asset drawn from the 1,200-idea corpus, where sub-strategies are admitted
by IMPLEMENTABILITY (rules, data, PIT, costs, decision count, complement
potential) and may carry known-negative individual history as diagnostic
candidates?

**Honest prior: NEGATIVE.** 294 corpus ideas are exploratory-implementable
today on the 5 evidenced pairs (223 carry family-level negative history,
59 were never scored, 12 carry individual F-0 rejects); 7/12 assets stay
BLOCKED on data authority. The direct ancestors of this question shape
died (RGC-V1 exposed reading; BTC-COMBO6 terminal); the owner has
explicitly authorized the diagnostic reopening with outcome-exposed
labels, missed-profit accounting and full switching-cost accounting — the
changed axis is authorization + accounting discipline, not new
information. Acceptance remains reserved to folds not used to select the
policy (PASS_BARS_V2). A negative close remains first-class and cheap.

## 1. Deliverable map (all pre-GO, this session)

| owner step | artifact | status |
|---|---|---|
| 1. authority re-measure | registry/lock/worktree verified; owner dirty tree preserved | DONE |
| 2. 1,200-ID eligibility table | `../eligibility/PORTFOLIO_ELIGIBILITY_1200.tsv` + SUMMARY | DONE — **0 admissible today**; pools P_A..P_E quantified |
| 3. controlled campaign | `../campaign/BACKTEST_CAMPAIGN_DESIGN.md` | DONE (draft) |
| 4. portfolio policy + baselines | `../policy/PORTFOLIO_POLICY_ARCHITECTURE.md` (B0–B9, P1–P8) | DONE (draft) |
| 5. journal + loss analysis | `../journal/JOURNAL_SCHEMA.md` | DONE (draft) |
| 6. this plan | freeze/budget/gates/owner decisions below | DONE (draft) |

## 2. Universe and eligibility law (binding, v2)

- 12 columns always present: EURUSD GBPUSD USDJPY USDCAD AUDUSD NZDUSD
  USDCHF XAUUSD XAGUSD BRENT WTI NATGAS. **7/12 are BLOCKED by data
  authority today** (DATA_COST_MATRIX); blocked columns activate ONLY via
  their named owner unblock + PIT/cost gates, as plan amendments.
- **Admission law v2 (amendment §2):** a corpus idea is an EXPLORATORY
  candidate iff implementable — mechanical rule compilable, panel exists,
  PIT chain provable, costs testable, no swap-profit dependence, decision
  count above floors, intraday features only on M1 pairs. 294 rows
  qualify (ladder v2.1, `eligibility/`, post-skeptic F-4/F-5 classifier fixes). Ancestry/individual failure
  history is carried as `outcome_exposed_label` into every ledger row —
  never an exclusion, never renamed as a new edge. The 68 not-mechanizable
  rows stay out; the 110 PIT-unevidenced, 90 venue, 565 no-price, 41
  ceiling, 23 feature-blocked and 9 swap-cost rows stay BLOCKED with named
  unblocks (ladder v2.1 counts).
- **Mechanization triage overlay (Lane R, this session):** reading every
  candidate's rule text at its corpus source, **150 of 294 are runnable today
  (75 T1 + 75 T2, post-remediation); 144 are T3_PARK** with
  per-row reasons (`poolB/grouping/mechanization_triage_292.tsv`). The
  ladder badge does not certify input availability — the triage is the
  layer that does (incidents I-R1 keyword mis-buckets, I-R2 SONIA parked).
  Whole families fell on inputs: D-CARRY_TERM 0/13, F-EVENT 2/30,
  H-POSITIONING 2/20. 4 candidate slates proposed (12+12+12+10 legs; 36
  unique corpus legs + 9 VOLPROF class candidates) — prior reasoning only;
  complementarity measured on TRAIN folds post-registration.
- Cost authority: all 5 evidenced pairs PROVISIONAL_PENDING_COST_AUTHORITY
  (spreads measured; commission/swap/slippage declared pessimistic). Every
  Stage-C survivor carries `NET_DEFAULT_COST`; swap-receiving legs stay
  BLOCKED_COST until the owner statement.

## 3. Protocol (frozen at registration; references carry the detail)

- Folds: 286-Friday calendar, 52w warmup, 8×26w test folds, 1w embargo,
  26w sealed tail SEALED (campaign §3). Sample floors 20/3/100 typed.
- Stages A/B/C with discovery-vs-scored separation; DSR + PBO over the
  FULL ledger; P-20 arm-distinctness rho ≤0.20 vs dead ancestors AND
  co-admitted legs (campaign §2, §5).
- Policy: 7 layers, risk-only eligibility, netting, cluster caps, typed
  standing-out rules (POLICY-ARCH). Baselines B0–B9; PASS bars P1–P8.
- Journal: append-only hash-chained rows incl. blocked signals; per-bar
  reconciliation; loss taxonomy with the fold-lock law on condition
  promotion (JOURNAL §3).

## 4. Trial budget (DRAFT v2 — owner amends at registration)

Wide discovery, narrow scoring — the exploratory ledger is large BY DESIGN
(owner-authorized), the scored surface stays small BY LAW:

| class | cap |
|---|---|
| discovery-ledger rows (mechanization screening + TRAIN-fold diagnostics incl. controls, all outcome-labeled) | **1,500** |
| Stage-C scored arm-executions (policy + B0–B9 + robustness on TEST folds) | **48** |
| exploratory candidates entering mechanization screening | ≤294 ladder v2.1; **triage-runnable 150 (75 T1 + 75 T2, post-remediation) — the operative first-pass scope**; 144 T3 parked at 0 runs |
| B4 random battery (ONE identity, seeded sub-runs; skeptic F-3 counting unit) | ≤128 seed sub-runs, own disclosed budget line |
| legs surviving into the assembled portfolio | ≤12 |
| Stage-B policy variants (frozen grid) | 8 |
| ledger overflow at any point | STOP → owner decision |

Compute estimate (Lane R sequencing): breadth-first — 75 T1 + 9 VOLPROF
exact-arm dry-runs first (no PnL, RGC law), then the T2
defaults-registration pass, then TRAIN diagnostics ordered G2→G1→G4→G3;
worst case ≈ 500 engine runs inside the 900–1,200 bound, order 1–3 h under
the single heavy lock (deterministic replay class proven at this scale by
DAYTRADER-100 and BTC-COMBO6). DSR/PBO price the FULL discovery ledger at
Stage-C (P5). Scored cells if a policy survives to Stage-C: ≤48.

## 5. Freezes before any scored computation

- CODE_FREEZE (engine + policy + journal writer), DATA_FREEZE (panel
  digests + PIT manifest), SELECTION_FREEZE (admitted leg ids +
  arm_config_digests + policy variant grid + PASS bars + budget),
  COST_FREEZE (component table digest). Freeze ceremony: exact-arm dry-run
  WITHOUT PnL (identities, decision counts, cost bills only — RGC-INC-1
  law), then independent A7 prelaunch (fresh context) — requested at its
  gate only after registration, not now.

## 6. Verification gates (all must PASS before Stage-C)

no-lookahead truncation replay (prefix-exact) · PIT join proofs with
staleness fail-closed · accounting reconciliation to 1e-9 with UNAVAILABLE≠0
· determinism (byte-identical twin) · exact-arm distinctness (pairwise) ·
dry-run PnL-leak scan. Any failure ⇒ typed `NOT_RUN_INTEGRITY` + remediation
loop; never silent continue.

## 7. Terminal outcomes (first-class, preregistered)

`NO_ELIGIBLE_PROPOSAL` (0 legs — the T0 default) · `POLICY_NO_INCREMENTAL_
VALUE` · `POLICY_COST_DOMINATED` · `POLICY_ONE_LEG_CARRIER` ·
`NOT_RUN_THIN | NOT_RUN_INSUFFICIENT_CALENDAR | NOT_RUN_PIT_GATE_FAILED |
NOT_RUN_INTEGRITY` · PASS (all P1–P8) → prospective-shadow pipeline (separate
authorization). Negative closes are cheap by design.

## 8. Blockers and owner decisions (each ONE action; NOTHING runs without them)

1. **Register or return this draft** (GO phrase §9). Default if silent:
   nothing runs (fail-closed).
2. **P_A — cost authority:** export IBKR Activity/Flex statement (FX trades
   + Interest Accruals) to `~/.my-quantitative-data/ibkr_statement/`.
   Recommended regardless (cheapest; upgrades every future FX cohort).
   **Owner reminder 2026-09-29: the IBKR read-only API (TWS port 7497) is
   available** — the already-scheduled bounded read-only sessions
   (SIXSOURCE cadence, sanitized windows accumulating in the owner's tree)
   continue closing the C1–C3 panel→IBKR venue-transfer caveat toward the
   ≥200-obs/pair-hour-bucket threshold WITHOUT new owner action. The API
   channel does NOT substitute for the statement: commission/swap/
   slippage measurement (U2/U3/U4-U5) requires the Activity/Flex export —
   read-only quotes cannot price fees. Until then every pair stays
   PROVISIONAL_PENDING_COST_AUTHORITY and every survivor carries
   NET_DEFAULT_COST.
3. **P_B — volume-profile class cycle:** authorize the fresh preregistered
   volume-profile program on EURUSD/GBPUSD/USDJPY M1 (the only unclaimed
   observable class per the F-0 court; must clear DT100-13-VWAPMR ancestry
   and declare its tick-volume proxy). Without P_B (or P_C/P_D) this cycle
   has NO lawful legs and closes empty at 0 cells.
4. **P_C — ERP1 M1 re-fetch for AUDUSD/USDCAD:** name an allowed
   source/channel for the 2×~4,014 raw .bi5 files.
5. **P_D / P_E — symbol data and macro-PIT unblocks** (each its own
   acquisition cycle; listed for sequencing only).
6. **Pending from other cycles (visible here for one-screen clarity, no
   action taken):** SLEEVE-FX5 D1/D2 packet; REGIME-GATED-COMBO a/b.

## 9. GO phrases (typed, one per gate — NOT consumable from this document)

1. Registration: `GO PORTFOLIO COMPOSITE 12ASSETS 100K V1 REGISTER PLAN plan/PLAN_portfolio_composite_12assets_100k_v1_DRAFT.md`
2. Scored execution (only after A7 prelaunch AUTHORIZED, fresh at its gate):
   `GO PORTFOLIO COMPOSITE 12ASSETS 100K V1 SCORED EXECUTION`

Typed early = intent, dies unconsumed (P-8). The owner's 2026-09-29 request
that produced this session is intent, never a key.

## 10. Artifact pins

All pins live in the A1-maintained external manifest
`../manifest/ARTIFACT_PINS.json` (schema `artifact_pins@1`) — refreshed by
A1 at every integration, never self-pinned inside a pinned document (a
document cannot contain its own hash). The registration receipt freezes
the manifest digest.

## 11. Honest limits of this draft

- Architecture and protocol are UNTESTED designs until the verification
  battery runs; prior drafts in this workspace have died at their first
  measured gate and this one is priced to die the same way if the evidence
  says so.
- The 0-admissible-today state: census verdicted all 1,200 rows; the F-0
  court + skeptic deep-adjudicated the 15 DISTINCT_TESTABLE survivors; the
  3 volume-profile rows are candidates pending the fresh class-spec
  adjudication (this control dir, `poolB/`). It is the state under the
  gates in force — not a conclusion that no edge can exist.
- No A7 has reviewed this draft; the formal independent A7 prelaunch runs
  post-registration, pre-GO (fresh context), per repo process.
