# A7 TERMINAL AUDIT — ETHUSDT-OPEN-SEARCH-V1 (fresh context, refute-first)

Auditor: A7 (independent terminal auditor, fresh context). Posture: the positive
claim is held to the higher bar; every number below was recomputed from bytes,
not taken from any ledger or told to me. Writes confined to `audits_a7/`.

Audited at: 2026-09-25T02:02:03Z
Integration: worktree `.worktrees/ethusdt-open-search-v1/integration`, branch
`orca/ethusdt-open-search-v1-integration`, HEAD `12ff16de72ca53a90e3ef53c94603485a107b915`.
Repro twin: detached at `0b92ee65e8f2aaf0f9cff1b2ba45de9cb826637c` (verified).
Plan authority: `plans/PLAN_ethusdt_open_search_v1.md` (read in full; §2-§11, §12).

## C1. Scored run under consumed GO — CONFIRMED

- `audits_a7/go_authorization.json` was added by commit `37629434` (git show:
  exactly 1 file, +8 lines, 2026-09-25 08:28:23 +0700 = 01:28:23Z), phrase =
  registered `GO ETHUSDT OPEN SEARCH V1 SCORED EXECUTION`; unchanged since
  (tracked-clean). `run_scored.py scored()` hard-refuses without this file and
  exact phrase (code inspected).
- Two TECHABORTs recorded in `events.jsonl` (lines 10, 12), both PRE-publication:
  attempt 1 crashed in tier_table ID parse (control book IDs contain `|`),
  attempt 2 crashed on `NameError: v` in `gates()` — both before any output
  write; both diffs (`54f2b4f5`, `0b92ee65`) inspected by me: plumbing-only
  (3-line parse fix; the `tr` dict repointed to `refs["BASE_TREND_LF"]` exactly
  as the plan's G10 defines — a crash-fix toward plan semantics, never a gate
  change). No output existed under the buggy code.
- `scored/scored_summary.json`: verdict
  `ETHUSDT_OPEN_SEARCH_V1_NO_INCREMENTAL_VALUE`, `all_pass_cells: []`,
  denominator computations 24 = 8 cells x 3 tiers. Timeline: last code edit
  01:40:17Z (0b92ee65) < scored output built 01:48:45Z — the run postdates all
  edits.

## C2. Reproduction (G8) — CONFIRMED (recomputed, not trusted)

- Twin detached at exactly 0b92ee65 (verified; empty branch name = detached).
- I diffed the two `scored_summary.json` files myself: byte-identical modulo
  `built_utc` (integration 2026-09-25T01:48:45Z vs twin 01:49:07Z); every other
  byte equal.
- `eos1_engine.py`, `run_scored.py`, `stage_all.py`, `test_fixtures.py` hashes
  identical across twin and integration AND equal to the v4 freeze's
  `code_freeze` records (recomputed with shasum).

## C3. Gate arithmetic — CONFIRMED (recomputed for ALL 8 cells, min was 3)

I re-executed the committed engine in-memory (read-only, no file writes) for
every book x tier and recomputed G1, G2, G3 (+margins), G4, G5, G6, G7, G10
(+deltas +flips), G11 from the results: ZERO mismatches against
`scored_summary.json` (all booleans, all numeric fields to the recorded
precision). Independent hand checks agree (e.g. fold concentrations 0.4878 /
0.6149 / 0.5289 / 0.7868; G10 delta arithmetic; G3 margin arithmetic).

Claimed specifics, verified:
- G3 failed for all 8 because BASE_ALWAYS_ON_LONG 1,653,470.33 @1.0x exceeds
  every cell (largest cell net 625,621.14 = E1-A3); the ALWAYS_ON margin is the
  most negative margin in every cell. CONFIRMED.
- E1-A1 and E1-A4 failed ONLY G3 (all other gates pass). CONFIRMED.
- E2-B1: G6 FAIL — block-shuffled control net 68,166.68 > cell 67,991.14.
  E2-B2: G6 FAIL — shuffled 71,563.85 > cell 48,351.23. A block-shuffled
  control out-earned them; recorded as fail. CONFIRMED. (E2-B3 also G6-fail:
  114,166.55 > 79,472.94.)

## C4. Denominators — CONFIRMED with one publication nuance (F-A)

- Observed 24 arm-tier computations (8 x 3); the runner's full book census is
  84 = 24 arm-tier + 12 ref-tier + 48 control-tier, matching the dry-run's
  expected_computations=84 (cross-checked).
- Controls/references are zero-denominator reference computations per plan §8.
- Budget: all 8 cells computed (8/8). NOTE: registry still reads 0/8 and
  `state.json budget.used=0` — P6-close bookkeeping pending (see F-B).
- `scored/scored_summary.json` is NOT yet in git (untracked; never committed —
  verified `git log --all -- scored/` empty). The 24 computations are observed
  via byte-identical working-tree artifacts in two independent worktrees. The
  dispatch wording "published via the committed summary" overstates status at
  audit time (F-A).

## C5. Verdict lawfulness — CONFIRMED

- Zero all-pass cells ⇒ per plan §6 no cell earns the ceiling; §11 enum:
  `NO_INCREMENTAL_VALUE` is the lawful member (proposals computed, none beat
  the wall). `NO_ELIGIBLE_PROPOSAL` n/a (both lanes passed pre-PnL ancestry —
  A7 prelaunch/delta r1), no `BLOCKED_DATA` (census BUILD_PASS reconfirmed),
  not TECHABORT (the run completed).
- No gate relaxed after PnL — verified: plan file last touched 2026-09-24
  15:25Z (micro-amendment 8a5a06b4, cross-reference clarification only, §12
  pre-outcome); `eos1_engine.py` untouched after commit 4d053745 (pre-GO);
  `run_scored.py` post-GO edits are the two pre-publication TECHABORT fixes
  only; ZERO code edits after the scored output (01:48:45Z); working tree
  clean vs HEAD except untracked `scored/`.
- Interpretation notes (both frozen PRE-PnL, neither can flip any cell to
  all-pass since the G3 wall binds everywhere): G7 = execution-cost semantics
  (2 ticks/rt in bps) per delta-r1 adjudication of plan gate text; G5 =
  max-positive-fold share of positive folds (the stricter reading).

## C6. Incident record + freeze chain — CONFIRMED

- Both TECHABORTs in `events.jsonl` with zero exposure (scored/ empty), plus a
  transparent date-label correction event.
- Freeze chain: v1/v2/v3 `*_SUPERSEDED_BLOCKED.json` present, git-tracked,
  working tree byte-clean vs HEAD; v4 `eos1_freeze.json` records 8 hashes
  (4 code + 4 evidence) — ALL match the working files in BOTH worktrees
  (recomputed).

## C7. References table + hand recomputation — CONFIRMED (decisive check)

From-scratch ALWAYS_ON F1, my own loader and arithmetic, zero engine code,
straight from the 80 staged Vision zips (all 80 sha256-match the committed
`staged_manifest.json`; twin's 2020-01/2021-04 zips byte-identical to
integration's):

- entry 2020-01-01T00:00Z open 129.12; exit last F1 H4 bar (2021-04-30T20:00)
  close 2,773.15 (1h 23:00 close); qty = 100000/129.12 = 774.473358
- gross = 2,047,715.30; fees = 1,123.87 (2 legs x 5 bps x raw notionals)
- measured funding while held = −419,187.52 (1,458 settlements in
  [entry, 2021-05-01T00:00), floor-hour-OPEN pricing, 0 fallbacks in F1)
- NET = 1,627,403.92 vs recorded 1,627,403.92 — diff 0.0044 (rel 2.7e-9,
  float accumulation order). Sign and magnitude exact.
- Cross-algebra: ALWAYS_ON F1 + SHORT F1 = −2,278.71 matches the closed form
  −(4·q·tick + 2·q·(open+close)·fee) — the two reference books are mutually
  consistent.
- Table sanity: BASE_TREND_LF +472,864.82, REF_SHORT_ALWAYS −1,656,451.03,
  fold sums re-add to net@1.0 within rounding — all match my recompute.
- Data: 58,440 ETH 1h bars; funding 7,305 rows with floor exactly
  2020-01-01T00:00Z (census claim exact); ETH H4 dropped windows = 0.

## C8. S1 / orders / credentials / foreign surfaces — CONFIRMED

- Whole branch `f3daf990..HEAD` touches ZERO files outside
  `research/control/ethusdt_open_search_v1/`.
- No credential-like strings committed; stager URLs are keyless
  data.binance.vision (manifest inspected).
- `state.json`: s1 SEALED_UNTOUCHED, orders NONE. My own writes: this
  directory only.

## Corroboration

Fixture suite executed in the twin: ALL FIXTURES PASS, exit 0 (11 groups
incl. PIT settlement-pricing law and the post-TECHABORT synthetic `gates()`
exercise).

## Findings (none material to the verdict)

- F-A LOW (documentation-lag): the terminal report `scored/scored_summary.json`
  is untracked/never committed at audit time; "published via the committed
  summary" is not yet literally true. Evidence is byte-verified in two
  independent worktrees; commit lands at P6 close.
- F-B LOW (documentation-lag): no `events.jsonl` entry for the successful
  scored run (01:48:45Z) or the twin rerun (01:49:07Z); `state.json` phase
  still P4-rerun with budget.used 0; registry 0/8 head 51378f5 — all P6-close
  bookkeeping, designed to land after this audit.
- F-C INFO (cosmetic): v4 freeze `tree.dirty_paths[0]` reads `esearch/...`
  (dropped leading `r`); one events.jsonl line has non-uniform JSON spacing.
- F-D INFO: G7/G5 interpretation notes as in C5 — locked pre-PnL in the freeze
  chain, disclosed, and immaterial: under any stricter reading the cells gain
  failures, none can reach all-pass.

## Verdict

CONFIRM_WITH_FINDINGS — the terminal verdict
`ETHUSDT_OPEN_SEARCH_V1_NO_INCREMENTAL_VALUE` stands as recorded with evidence
intact: 24 observed computations, zero all-pass cells, G3 wall
(BASE_ALWAYS_ON_LONG 1,653,470.33) above every cell, block-shuffled controls
out-earn E2-B1/B2/B3, reproduction byte-identical modulo built_utc, and the
headline reference number reproduces from raw staged bytes to 2.7e-9 relative.
Findings F-A/F-B are LOW documentation-lag items to be discharged at P6 close.
