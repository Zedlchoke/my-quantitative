# PLAN — WNBA-WINPROB-PROSPECTIVE-PREP-V1 (WNBA prospective win-prob PREP cycle, $0)

- cycle_id: WNBA-WINPROB-PROSPECTIVE-PREP-V1 · asset: shared · PLANNED_NOT_STARTED,
  budget 0/0 at registration, GO phrase registered but NOT typed:
  `GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS`
- owner authority 2026-10-06 (this chat): REGISTRATION authorization for a PREP cycle
  ONLY — the successor-packet round that follows the TERMINAL close of
  WNBA-PLAYERFEAT-SCORED-V1 (A7_R8 PASS at head 6d860236e27a59b883d14a88ee852d2b3a94e70d;
  B1-WNBA K=32/HCA=50/γ=0.65 beats B0 on OOS 2020–2026, ΔLL −0.085856,
  CI [−0.103702, −0.067931], falsifier NOT_REJECTED, budget 2/9). This instruction is
  explicitly **NOT a typed GO**; **no real forecast of any real game is authorized**;
  no real-game probability is computed anywhere in this cycle before its own typed GO.
  Proposal of record: `.worktrees/wnba-playerfeat-scored-v1/integration/research/control/
  WNBA-PLAYERFEAT-SCORED-V1/SUCCESSOR_PACKET_PROSPECTIVE.md` (PROPOSAL status,
  committed at 73c0315a on orca/wnba-playerfeat-scored-v1-integration).
- Hard boundaries: $0; no network/data purchases; no S1; no paper/live/betting language;
  no push/merge/rebase/history-rewrite; no edits to any other cycle's frozen
  artifacts/ledgers; no self-typed GO; missing evidence = TBD_PREP / NOT_RUN, never
  inferred PASS. Language law: calibration/forecasting vocabulary only.

## Scope (what this PREP cycle prepares)

The prospective scored-execution successor **WNBA-WINPROB-PROSPECTIVE-V1** (per the
packet): PROSPECTIVE ONLY season 2027+; B1-WNBA verbatim (K=32/HCA=50/γ=0.65) as the
mandatory arm + B0 constant 0.603755 floor; slots 3–9 RELEASED pre-look;
`wnba_prospective_ledger@1` append-only sha-chain ledger with `recorded_at_utc <
tip_utc` STRICTLY; daily batch ≥6h before that day's first tip (Eastern day key);
no backfill ever, played-before-record = NOT_RUN forever; remaining 2026 playoffs =
NOT capturable. This PREP cycle computes ZERO scored cells (budget 0/0): it refreshes
data, ports and tests the ledger tooling, and freezes the protocol — nothing else.

## Gate sequence (canonical; FUTURES/NBA precedent)

registration (this commit + `researchctl cycle register`, CAS) → prep lanes → freeze →
A7 prelaunch (fresh-context, 0 unresolved HIGH/CRITICAL required) → **owner typed GO:
`GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS`** → prospective ledger execution under the
machine-wide heavy lock → reproduction twin → terminal A7 → two-half close. Two-key
law (P-8): the GO is typed ONLY by the owner at THIS cycle's own gate, verbatim, fresh;
nothing survives from any earlier cycle (WNBA-PLAYERFEAT-SCORED-V1's GO was consumed
and extinguished at its close); an early/paraphrased GO dies unconsumed.

## Tasks (prep lanes; stop before GO)

1. Lane A — SUCCESSOR DATA REFRESH: one frozen-snapshot refresh of the
   sportsdataverse/wehoop release store lineage (espn_wnba_schedules +
   espn_wnba_team_boxscores; $0, no auth, provenance URL+tag+timestamp+bytes+sha256
   per file) to (a) absorb the remaining 2026 playoff finals as HISTORY only (rating
   stream 2002–2026; never scored rows — remaining 2026 playoffs are NOT capturable),
   (b) ingest the published 2027 schedule when it exists (TBD_PREP if not yet
   published at lane time), (c) re-verify rights bytes (ATTRIBUTION.md 1068e5c7…,
   license-badge text) and re-hash the feature table (ceaf10ba…) + crosswalk
   (e4115f04…); re-clear fail-closed at freeze per packet §5. Tip-UTC law verbatim
   (SPEC §3): tip_utc := parse(espn.date, ISO8601, UTC); local_date := ET date.
   Measured anchors carried from the packet: 2026 universe 341 (331 RS + 10
   postseason; 117 ET game-dates, max slate 6), first tips 2024-05-14T23:00Z /
   2025-05-16T23:30Z / 2026-05-08T23:30Z → launch clock planned against ≈early May
   2027 (actual 2027 first tip TBD_PREP).
2. Lane L — LEDGER TOOLING: port the append-only ledger tool (source law
   `nfl_ng_ledger@1`, NFL-WINPROB-NG-PREP-V1 lane E precedent) into this cycle's tree
   as `wnba_prospective_ledger@1` with provenance note; WNBA adaptations: tip_utc
   field + daily-batch validator (all rows of a batch recorded ≥6h before that ET
   day's first tip; strictly `<` inequality at append AND scoring) + the frozen
   same-tip batch rating law from the closed runner. 42-test-class synthetic suite +
   adversarial probes re-run green; hash-chain tamper detection; real ledger file
   must NOT exist pre-GO.
3. Lane F — FREEZE PACKET: bind the packet's open items: B1-WNBA constants verbatim
   (frozen arm-code pins 82263eab…/b9446f76… re-hashed at freeze), B0 = 0.603755,
   window law (PROSPECTIVE 2027+ only; stream replay warm-up 1,022 + 5,988 universe
   rows to the freeze cutoff), bootstrap seed pinned once (TBD_PREP), MIN_VALID = 300
   for the full-season primary, planning count 341 (range [310, 360]) with the
   pre-registered interim power statement verbatim, budget raise 0 → ≤9 via registry
   CAS at this gate (slots 1–2 committed, 3–9 RELEASED), falsifier wording verbatim
   (packet §4), no-parameter-change-after-first-real-row law, O-2 row vocabulary,
   played-before-record census law, launch-clock schedule. FREEZE_PACKET.md + code
   freeze SHA binding.
4. Lane S — SYNTHETIC TESTS + DRY-RUN: designed-null/no-lookahead mutation probes
   (strictly-pre-tip append, ET/UTC midnight + DST boundary fixtures, force-flat day
   batch, tamper detection); full record-pipeline rehearsal into a SANDBOX ledger on
   synthetic 2027-style games (never the real path); exact-arm identity checks; zero
   real rows, zero scored cells. DRYRUN_REPORT.md.
5. Lane A7 — INDEPENDENT PRELAUNCH AUDIT (fresh context; never repairs): registry
   coherence, freeze hash re-verification, ledger-law tests, rights re-clear, boundary
   compliance (0 scored cells, no GO typed, no real-game probability computed), launch
   clock stated. A7_PRELAUNCH_VERDICT.md; 0 unresolved HIGH/CRITICAL for PASS.

## Boundaries

- No scored computation on any window (historical or prospective) in this cycle; the
  retrospective OOS 2020–2026 verdict is the closed cycle's inheritance — never re-run,
  never extended. No real-game probability for any 2027+ game before this cycle's own
  typed GO. Registry writes only via researchctl (CAS); on conflict: re-measure +
  retry, never overwrite. Root checkout = control plane only; lane work in the exact
  worktree/branch named below; data outside git under ~/.my-quantitative-data/ (the
  wnba-v1 corpus stays EXTEND-ONLY; foreign ROOT-level `.my-quantitative-data/` is
  FOREIGN content — never read, never bundled). Heavy runs take the global lock
  (NOT_RUN_RESOURCE_CONFLICT if held; never kill foreign workers).
- Branch/worktree: `orca/wnba-winprob-prospective-prep-v1-integration`; worktree path
  to be created at lane start (planned placeholder — no worktree/head pinned at this
  registration).

## Artifacts

`lanes/A_DATA/ · lanes/L_LEDGER/ · lanes/F_FREEZE/ · lanes/S_SYNTH/ · lanes/A7_PRELAUNCH/
· lanes/DISPATCH/` in the integration worktree; control state under
`research/control/WNBA-WINPROB-PROSPECTIVE-PREP-V1/`; each lane ends with handoff JSON
`zcode_orch_v3_handoff@1` at its handoff_path.

## Terminal outcomes (negative-first)

PRELAUNCH_READY_PENDING_OWNER_GO | GATE_FAIL_<GATE> (FAIL/NOT_RUN recorded; affected
scope released, never forced GO-ready) | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING |
BLOCKED_NO_2027_SCHEDULE (freeze reached before the 2027 schedule is published) |
NOT_RUN_RESOURCE_CONFLICT | TECHABORT_*. The GO phrase
`GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS` is typed ONLY by the owner at this
cycle's own gate after reading the A7 verdict; it is never typed, paraphrased or
consumed by any agent.
