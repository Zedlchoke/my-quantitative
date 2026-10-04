# AUDIT_PRELAUNCH_R4 — NFL-WINPROB-SCORED-V1 (A7, round 4, post-AMENDMENT_1 delta)

- auditor: A7 prelaunch, fresh context; the round-1 A7 (AUTHORIZED, 4 LOW) is
  SUPERSEDED by the AMENDMENT_1 remediation and carries no authority here —
  this report evaluates the CURRENT freeze-v2 package only. Every item
  re-measured from bytes on 2026-10-04.
- worktree HEAD measured: `18412f4876804c07a25b9ddeb3fefdb1062cc992`
  (branch `orca/nfl-winprob-scored-v1-integration`, clean tree)
- code freeze v2: `91dcff14bf66d5ba5a0fb2322be10ee1b08d26ad`
- supersedes v1: `8cd0e1bcf9c9d45f5e10ae1b73b93eee7560a7b7`
  (`FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json` + `SUPERSEDED_NOTE.md`, §24
  evidence kept; rename verified byte-identical, 0 content delta)
- AMENDMENT_1 (`AMENDMENT_1.md`, commit `649557b7`): L1' ledger schema fix,
  L2' drift-prefix fix — both re-verified by verifier-lane independent
  execution AND by this audit (see D3, D4; companion evidence
  `lanes/E2_data_freeze/VERIFICATION_REPORT_R4.md`, VERIFICATION_PASS 7/7).

# VERDICT: A7_PRELAUNCH_AUTHORIZED_CONDITIONAL_ON_PIN

A7_PRELAUNCH_AUTHORIZED — 0 HIGH, 0 CRITICAL — subject to exactly ONE
pre-GO action: a **manifest-only** commit repointing `a7_report_path` from
`audits/AUDIT_PRELAUNCH.md` (round 1) to `audits/AUDIT_PRELAUNCH_R4.md`
(this document). The action is allowlisted
(`research/control/NFL-WINPROB-SCORED-V1/**`), requires no code change, and
follows the completed NBA precedent (NBA manifest pin moved to
`AUDIT_PRELAUNCH_ROUND3.md`). After the pin move, launch remains two-key
gated: this artifact + the owner's structured GO record typed at this
cycle's own gate.

## Why the pin must move (coherence analysis of the old pinned file)

The manifest still pins `audits/AUDIT_PRELAUNCH.md`. That file DOES carry
the literal token `A7_PRELAUNCH_AUTHORIZED`, so the launch-gate grep would
mechanically pass today. But the token is not coherent with the current
code:

1. It certifies HEAD `2ddef086` / freeze `8cd0e1bc` — both SUPERSEDED; the
   audited code (`run_evaluation.py` blob
   `1fe355b7d4c6463bd19f2d34358dfb8c3a6b830a`) and generator (blob
   `8e5ebb9e14b877f245594aed9fe14e8875a4b6b0`) postdate it.
2. Its LOW-1/LOW-2 findings (NBA-schema ledger append, dead `nba_winprob/`
   drift prefix) describe defects that AMENDMENT_1 has since FIXED — a
   pinned artifact asserting open defects that are actually fixed is itself
   an accounting inconsistency at GO time.
3. `go_phrase_state` in the pinned artifact's certification chain references
   the v1 freeze; the operative freeze is v2 with the `supersedes` block.

Therefore the pin must move to this R4 report (which re-certifies the
current package). Until the pin move lands, the verdict is
AUTHORIZED_CONDITIONAL_ON_PIN; once landed, it reads
AUTHORIZED for launch.

## §19.3 delta item-by-item

### D1 Hashes chain incl. supersedes evidence — PASS
All five manifest-pinned hashes recomputed from bytes and match: raw
`games.csv` `f1e8fe78…`, derived `games_nfl.csv` `f7909fa5…`,
`lineages_nfl.csv` `977a43e2…`, `features_nfl.csv` `4ee2175e…` (UNCHANGED —
the remediation touched neither raw nor derived features),
`ATTRIBUTION.md` `b1852975…`; `protocol_digest` `5b035a1c…` matches
`lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md` (byte-identical to the PREP-twin
copy). Supersedes evidence chain verified:
`8cd0e1bc` (v1) → renamed `FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json` (0-delta
rename, commit `27dbc1d8`) + `SUPERSEDED_NOTE.md` ("0 outcomes ever
computed; kept append-only as evidence") → v2 manifest `18412f48` carrying
the `supersedes` block with old manifest pointer. The v1→v2 manifest delta
is exactly `code_freeze_sha` + `created_utc` + the added `supersedes` block;
every identity field (arms, data hashes, constants, registered comparisons,
pins, allowlist, GO phrase, `go_phrase_state`) is byte-SAME.

### D2 9-arm identity unchanged — PASS (four-way)
Identical across (i) manifest `arms`, (ii) `nfl_winprob/protocol.py` `ARMS`
(with `assert len(ARMS) == 9`), (iii) `PROTOCOL_EVAL_NFL.md` (all 9 ids
present), (iv) `TRIAL_LEDGER.jsonl` rows (same order): B0; B1-a K=20/HCA=0;
B1-b K=20/HCA=65; B1-c K=40/HCA=0; B1-d K=40/HCA=65 (γ=2/3); B2-a
f1–f6; B2-b f1,f5,f6; B2-c f1,f2,f3,f4; B2-d f1. Constants identical
everywhere: L2=1.0, seed=20261005, elo_init=1500.0, gamma=2/3,
TEST 2019–2025, TRAIN 2000–2018 inclusive. 11 registered comparisons
manifest == runner `REGISTERED_COMPARISONS` (comparisons are not arms; the
9-arm trial budget is unchanged). GO phrase identical in manifest /
protocol.py / runner. AMENDMENT_1 changed no arm, no fold, no threshold.

### D3 Accounting consistency NOW HOLDS (was the L1' violation) — PASS
Single schema end-to-end, re-measured by this auditor's own execution (not
only by the shipped test): `append_trial_rows` writes
`nfl_winprob_trial_ledger@1` on both PRIMARY and REPRO passes into a temp
ledger; `nba_winprob_trial_ledger` occurs 0 times in the runner source;
on-disk ledger = exactly 9 rows, all `PREREGISTERED`, `observed=false`,
0 COMPUTED, all NFL schema, registered 2026-10-04T13:36:33Z. Registry
budget: used 0 / max 9. `results/` empty. The round-1 LOW-1 is closed.

### D4 No post-freeze drift — PASS
`git diff --name-status 91dcff14..HEAD` = `FREEZE_MANIFEST.json` only
(allowlisted); `nfl_winprob/` byte-unchanged since the code-freeze commit;
worktree clean. The explicit drift check is now the pure
`_code_drift_reasons` with prefix `nfl_winprob/` (round-1 LOW-2's dead
`nba_winprob/` prefix closed): positive case flags a package change with
`CODE DRIFT (nfl_winprob/ immutable)`, negative case leaves the allowlisted
control file unflagged, and the allowlist fallback still catches anything
else. Heavy lock measured `FREE_PROVEN`. Chain hygiene: `649557b7` code+tests+
AMENDMENT_1.md only; `27dbc1d8` rename+note only; `91dcff14` generator-only
before manifest; `18412f48` manifest-only; `TRIAL_LEDGER.jsonl` untouched by
the entire chain.

### D5 S1 untouched — PASS
No S1 paths or accessors in the package (grep clean, 0 hits). Registry
records `s1: SEALED_UNTOUCHED` for this cycle (and the PREP cycle). The
remediation chain touches only `nfl_winprob/` and the cycle control dir; no
credentials, no push/merge, no betting surface.

### D6 Twin NOT_RUN-by-design — PASS
This cycle: scored evaluation NOT_RUN by design pre-GO — 0 COMPUTED ledger
rows, empty `results/`, refusal paths re-executed (`evaluate` stub exit 3;
scored runner without GO record exit 3 with named reasons; synthetic
selftest exit 0, no real data). NBA twin program: untouched by this cycle's
commits; the round-1 NBA-schema label remnant that concerned LOW-1 is now
removed from the source entirely (0 occurrences), so nothing NBA is even
labeled, let alone executed.

### D7 Owner authority — PASS
No GO record exists for NFL-WINPROB-SCORED-V1 anywhere (searched; only other
cycles' GO records exist). `go_phrase_state = REGISTERED_NOT_CONSUMED` in
both the v2 manifest and the registry; plan §0: owner intent is INTENT ONLY,
not a typed GO. The structured-JSON gate is enforced
(`phrase == "GO NFL WINPROB SCORED V1 EVALUATION"`, `cycle_id`,
`typed_by == "owner"`, non-empty `typed_at`; any miss refuses exit 3 —
re-verified this round).

## Findings

- **CONDITION-1 (the pin)** Repoint manifest `a7_report_path` →
  `audits/AUDIT_PRELAUNCH_R4.md`. Manifest-only, allowlisted, no code
  change, no freeze invalidation (the manifest is inside its own
  allowlist). NBA precedent completed identically. Until landed: verdict is
  conditional.
- **LOW-A** Registry `head` stale at `2986de8c…` vs measured `18412f48…`
  (registry writes outside auditor/verifier lanes; controller normalizes at
  landing — same disposition as round-1 LOW-3).
- **LOW-B (latent)** `make_freeze_manifest.py` line 54 still hardcodes
  `a7_report_path` → `audits/AUDIT_PRELAUNCH.md`; a post-pin-move regen
  would resurrect the stale pin. Latent only — the gate consumes the
  manifest file, not the generator; the NBA twin carries the identical
  divergence (generator ROUND2 vs manifest ROUND3). Owner's call whether to
  fold the generator line into the pin-move commit; NOT required for
  authorization.
- **L4 (informational, carried)** The selftest's trailing verdict JSON
  (`PROGRAM_PASS:false / REJECT:true`) is computed on random synthetic data
  — mechanics-only, exit 0; noted to prevent misreading at GO time.

## Launch posture

Preconditions for G5 (owner GO), none in auditor scope beyond CONDITION-1:
(1) land the manifest-only pin move; (2) owner types the structured GO
record at this cycle's own gate; (3) heavy lock FREE at launch (currently
FREE_PROVEN); (4) clean tree at launch (currently clean). On GO the runner
writes only into the pinned `results_dir` and appends COMPUTED ledger rows
now guaranteed NFL-schema. Without GO: refusals exit 3, verified.

A7_PRELAUNCH_AUTHORIZED_CONDITIONAL_ON_PIN — 0 HIGH / 0 CRITICAL /
1 CONDITION / 2 LOW / 1 informational.
