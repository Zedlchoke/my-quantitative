# PLAN — SOCCER-INTL-WINPROB-PREP-V1 (men's international football win-prob PREP, $0)

- cycle_id: SOCCER-INTL-WINPROB-PREP-V1 · asset: shared · budget 0/0 (ZERO
  scored cells — none are possible in this cycle) · registered 2026-10-07.
- owner authority 2026-10-07 (this chat): explicit instruction to open the
  FIRST successor PREP cycle from the SPORTS-WINPROB-DISCOVERY-PREP-V1
  shortlist, per `PREP_PACKET_SOCCER-INTL.md` (DISCOVERY integration
  `research/control/SPORTS-WINPROB-DISCOVERY-PREP-V1/PREP_PACKET_SOCCER-INTL.md`,
  HEAD 23b81a26). This instruction is explicitly **NOT a typed GO**: no scored
  execution, no backtest-OOS run, no real-game forecast, no second cycle
  registration, no S1, no betting language, no push/merge, no credentials or
  purchases. Rights: internal research under CC0-1.0 only; unclear commercial
  rights are never inferred — they stay NOT_RUN_RIGHTS.
- The DISCOVERY cycle stays TERMINAL and untouched. All NBA / WNBA / NFL /
  FUTURES cycles stay untouched.

## Scope (what this PREP cycle prepares)

The retrospective 3-way (home/draw/away) win-probability protocol for men's
international football on the martj42/international_results corpus
(49,547 games, 1872→2026-08, CC0-1.0). Deliverables: refreshed corpus +
full QC, a PROVEN as-of law (or honest NOT_RUN_PIT), frozen split/metric/
budget protocol, and frozen baseline designs. **The central hard problem
(owner's words): the corpus is date-only — this cycle must PROVE an as-of
law and a same-day ordering rule, or mark NOT_RUN_PIT. Fabricating kickoff
times is forbidden.** Prospective ledger tooling is OUT unless a $0/no-auth
future-fixture source is evidenced (else NOT_RUN_SOURCE — a results-only
corpus has no future schedule). A scored successor (its own plan, gates and
typed GO) would consume this freeze; nothing here runs it.

## Lanes (worktree per agent; integration is controller-only)

1. L-DATA `lane-data` — CORPUS REFRESH + FULL QC: re-download
   martj42/international_results results.csv (+shootouts.csv if present),
   byte-diff vs the DISCOVERY snapshot (23b81a26 manifest), refresh sha256
   manifests + CC0 license bytes + ATTRIBUTION.md. QC battery: schema check;
   duplicate match keys (date+home+away+competition); team-name identity
   crosswalk (variants→canonical; historical renames preserved as history);
   competition/friendly classification from the tournament column (Friendly
   vs competitive splits measured); home/away/neutral flag consistency;
   3-way result derivation (H/D/A from scores) with zero unclassifiable
   rows; date-only timezone law (UTC-date assumed, stated as limitation);
   coverage estimates per competition and era; revision-integrity light
   probe (upstream commit history metadata only — no heavy clone).
2. L-PIT `lane-pit` — RIGHTS + PIT LAW (the hard lane): (a) re-verify CC0
   from bytes; (b) byte-proof the corpus carries NO time-of-day fields
   (schema scan); (c) derive and PROVE the as-of law: features for a match
   on date D may use only results with date STRICTLY < D; all same-date
   matches are excluded from the feature pool (provable without kickoff
   times — never fabricated); (d) QUANTIFY the cost of the same-day
   exclusion (share of potential feature updates lost; per-era); (e)
   publication-lag and revision honesty: a static CSV cannot evidence
   historical available_time — state it, and check upstream commit metadata
   for revision behavior; (f) verdict: PIT_LAW_PROVEN_SAMEDAY_EXCLUSION or
   NOT_RUN_PIT with the exact reason. The law, once proven, is binding on
   L-BASE designs and any successor.
3. L-BASE `lane-baseline` — BASELINE + PROTOCOL FREEZE (design + synthetic
   tests only; NO real-data evaluation): B0 = train-window H/D/A shares
   (descriptive constant MAY be computed and frozen from TRAIN ONLY, labeled
   descriptive — never an OOS evaluation); B1 = Elo/Davidson 3-way design
   (rating update law, K and home-advantage estimation procedure from TRAIN,
   neutral-venue law per the corpus neutral flag, warmup 1872–1950, fit
   procedure frozen NOT fitted); splits warmup 1872–1950 / train 1951–2000 /
   chronological OOS 2001–2022 / held-out 2023→; metrics multi-class log
   loss + RPS + Brier(one-vs-rest) + calibration deciles; trial budget
   B0+B1+1 preregistered; null test (outcome-shuffled calibration sanity);
   leakage gates bind L-PIT's same-day exclusion law; synthetic tests
   (fixtures) prove the split/as-of/same-day rules in code with zero
   real-data evaluation; operational cadence + prospective blocker
   (fixture feed NOT_RUN_SOURCE).
4. L-VERIFY `lane-verify` — INDEPENDENT VERIFIER (fresh context, quant-
   auditor; dispatched LAST on integration HEAD; writes audit namespace
   only, never repairs): re-measure QC counts from bytes, re-hash manifests,
   re-derive the same-day exclusion math, attack the as-of law (try to find
   a leak or an unprovable step), verify no fabrication of kickoff times,
   no OOS evaluation, no model fits beyond the declared descriptive B0,
   boundary compliance ($0, no GO, registry coherent, DISCOVERY + other
   cycles untouched). Verdict PASS / PASS_WITH_FINDINGS / FAIL.

## Hard boundaries (all lanes)

$0; no accounts/API keys/tiers; no scored computation on any window; no
real-game probability; no GO (none exists for this cycle); no S1; no
push/merge/rebase; no writes to other cycles' artifacts/ledgers/registries
(DISCOVERY TERMINAL stays frozen at 23b81a26); missing evidence = NOT_RUN
(NOT_RUN_PIT / NOT_RUN_SOURCE / NOT_RUN_RIGHTS / NOT_RUN_RESOURCE) with
concrete estimates, never inferred PASS; WNBA constants appear nowhere.
Data bytes OUTSIDE git under
`~/.my-quantitative-data/soccer-intl-winprob-prep-v1/` with sha256
manifests; worktrees carry manifests/code/reports only. Root-level
`.my-quantitative-data/` is FOREIGN — never read. Light network only
(politeness caps; heavy lock for anything >10MB/>2min via
`governance.heavy_lock.acquire`; refusal = NOT_RUN_RESOURCE_CONFLICT).
Read-only QC for CRICKET-INTL is permitted ONLY outside this cycle's git
tree (notes under the data plane), as preparation for a later packet — it
registers nothing.

## Gate sequence

plan commit + `researchctl cycle register` (CAS) → worktrees (integration +
4 lanes) → task registration + dispatch packets → lanes L-DATA / L-PIT /
L-BASE (parallel; L-BASE consumes L-PIT's law, so it freezes subject to the
PIT verdict) → handoff validation (zcode_orch_v3_handoff@1; store + git +
test re-run) → sequential cherry-pick → controller assembly (FREEZE_PACKET.md
+ PREP verdict, PIT verdict stated verbatim) → independent verifier L-VERIFY
on integration HEAD → owner report → TERMINAL close (two-half). Registry
writes only via researchctl (CAS); on conflict re-measure + retry.

## Artifacts

`research/control/SOCCER-INTL-WINPROB-PREP-V1/` in each worktree: `DISPATCH/`
(packets + store driver), `handoffs/`, `lanes/{L_DATA,L_PIT,L_BASE,L_VERIFY}/`;
at integration: `FREEZE_PACKET.md`, `PREP_VERDICT.md`,
`A7_PREP_AUDIT.md` (verifier). Data + manifests-of-record under
`~/.my-quantitative-data/soccer-intl-winprob-prep-v1/`.

## Terminal outcomes (negative-first)

PREP_COMPLETE_PENDING_OWNER_SCORED_DECISION (protocol frozen; scored
successor unregistered) | PREP_PARTIAL_<gap> | NOT_RUN_PIT_ASOF_UNPROVEN
(protocol frozen WITH the PIT hole stated — never silently) |
NOT_RUN_RESOURCE_CONFLICT | BLOCKED_DATA_RIGHTS | TECHABORT_*. This cycle
has NO GO phrase; the scored successor's GO can only be typed by the owner
at that successor's own gate.
