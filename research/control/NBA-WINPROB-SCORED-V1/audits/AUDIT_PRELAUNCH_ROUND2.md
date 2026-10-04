# AUDIT_PRELAUNCH_ROUND2 — NBA-WINPROB-SCORED-V1 (Lane A7 round 2, independent, fresh-context)

## VERDICT: A7_PRELAUNCH_BLOCKED — REFUSED (1 CRITICAL, 3 MEDIUM, 7 LOW)

Round-1 A7 approval is superseded (owner-independent rejection; freeze 39b11156
marked SUPERSEDED_BLOCKED). This is a fresh, adversarial re-measurement of the
REMEDIATED package (freeze v2). No round-1 result was inherited. I attempted to
refuse on every axis; the remediation itself is largely real and verifiable —
but the freeze commit violates the frozen drift law it declares, so the package
**cannot pass its own launch gate as committed**, and per §19.3 (authorize only
at 0 HIGH/CRITICAL) authorization is withheld. The verdict token above is
deliberately NOT the authorization token; see finding L6 before string-matching
this file.

- Audit date: 2026-10-04. Auditor: A7 round-2 (independent). Read-only git; the
  only writes are this file and `handoff_A7r2.json` (both inside the pinned
  write scope).
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-scored-v1/integration`
- Branch: `orca/nba-winprob-scored-v1-integration`
- HEAD at audit start and at verdict: `227e3faa81c1cb3d8a458c6d5d47a32a104a7f4d`
  (= manifest freeze commit). `227e3faa^ == 2c64b6f3` verified.
- code_freeze_sha (manifest): `2c64b6f34b0b2cf46db7243418f5b929a6a5b4c8`
- Venv: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
- Tree state: **clean at audit start** (porcelain empty). During the audit, two
  UNCOMMITTED allowlisted-path artifacts from the concurrent E2 round-2 lane
  appeared (`lanes/E2_data_freeze/E2_REPORT_ROUND2.md`, `handoff_E2r2.json`;
  mtimes inside the audit window). This audit's two files are likewise
  uncommitted by design. Clean-tree at launch is a gate precondition (A3) and
  holds once the controller commits these allowlisted artifacts.

## §19.3 audit table (verdict + evidence each)

| # | Item | Verdict | Evidence (measured this audit) |
|---|------|---------|-------------------------------|
| 1 | Hashes chain | **FAIL (C1, L7)** | Manifest schema `nba_winprob_scored_freeze@2`; `supersedes` block present; `FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json` (@1, code 39b11156) + `SUPERSEDED_NOTE.md` present append-only. All 6 pinned sha256 recompute byte-exact via `shasum -a 256`: features `c86f104d…50fc86b`, games `e24d9a3b…636f098`, raw `d46ed354…8d616bc`, lineages `c8cdd58a…5610061c1`→`…061c1`, participants `fd7cb539…285c1bf`, attribution `e134e20c…24fb490a`. `protocol_digest` c058760d… and `amendment_digest` e7531c7e… recompute exactly. **BUT** `git diff 2c64b6f3..227e3faa --name-status` = `M nba_winprob/make_freeze_manifest.py` (outside allowlist, inside the immutable tree — finding C1) and the worktree is not currently clean (E2r2 lane artifacts, L7). |
| 2 | Exact-arm identity | **PASS** | 9 arms pairwise distinct (2×2 B1 grid + 4 distinct B2 feature tuples + B0). Programmatic set-compare: manifest arms == `protocol.py ARMS` (ids/kind/K/HCA/features all equal), ledger specs == manifest specs per arm, and all three match PROTOCOL_EVAL.md §5 table verbatim. `constants.f1_stream = "B1-a (K=16, HCA=0) — AMENDMENT_1 A1"` in the manifest; `export_features.py:81-82` writes plain `elo_diff` from the `B1-a` engine (`er_a = elo_by_arm["B1-a"][...]`). Spot check on 3 random rows of the real features.csv (seed 20261004: 197101170DNR, 195602270FTW, 200501120GSW): `elo_diff == elo_diff_B1-a` in 3/3. |
| 3 | Data / PIT | **PASS** | `pytest nba_winprob/tests` → **33 passed** (47.5s). Named: D1-regression `test_real_csv_path.py::test_real_features_header_has_plain_elo_diff`, `::test_real_csv_load_rows_end_to_end` (would KeyError pre-D1), `::test_real_row_counts_per_split` (63157 rows; 8369 test RS / 587 test PO); no-lookahead `test_features_asof.py::test_no_lookahead_mutation_property`; same-day `test_elo.py::test_sameday_disjoint_games_do_not_inform_each_other`, `::test_sameday_doubleheader_excludes_leg1_from_leg2`, `test_features_asof.py::test_sameday_games_never_inform_each_other_features`; leakage-grep `test_identity.py::test_static_leakage_grep`. Real features.csv header contains NO outcome/538 columns (banned-set intersection empty; `home_win`/`pts` asserted absent by test). |
| 4 | Accounting | **PASS** | `TRIAL_LEDGER.jsonl`: 9 lines, all `PREREGISTERED`, all `observed:false`, 0 `COMPUTED` (grep over control dir finds no COMPUTED rows and no scored outputs). Registry `plans/CYCLE_REGISTRY.json` cycles[87] `NBA-WINPROB-SCORED-V1`: `budget {"used":0,"max":9}`. Stale-head caveat M3 below. |
| 5 | Dry-run hygiene | **PASS** | `results/` EMPTY; no `scored_summary.json` anywhere; selftest is synthetic-only. Refusal paths, all measured: (a) `nba_winprob.evaluate` → exit **3** `REFUSED: freeze manifest missing ['freeze_sha','go_record_ref']`; (b) `run_evaluation` with nonexistent GO record → exit **3** with `no GO record` reason; (c) `run_evaluation` with wrong-phrase GO JSON (`/tmp/a7r2_go_wrong.json`) → exit **3** `GO record phrase mismatch`; (d) additionally `--games /tmp/a7r2_fake_games.csv` → refused `--games … != pinned …`. No files written to `/tmp` by the runner; results/ untouched. Note: v2 runner has no `--out` flag at all (results dir is manifest-fixed) — the round-1-era `--out` instruction does not map to the v2 CLI; fixed results dir verified structurally. |
| 6 | S1 untouched | **PASS** | Zero S1/SEALED references in `nba_winprob/*.py` + tests (grep). Registry: `s1: "SEALED_UNTOUCHED"` on both cycles[85] (PREP) and cycles[87] (SCORED). |
| 7 | No post-freeze drift | **FAIL (C1)** | See item 1 / finding C1: the freeze commit itself modified `nba_winprob/make_freeze_manifest.py`. |
| 8 | Twin | **NOT_RUN by design** | No scored run exists (item 5); nothing can be twin-verified pre-scoring. Consistent. |
| 9 | Owner authority | **PASS** | No GO record exists anywhere for this cycle; registry `go_phrase_state: "REGISTERED_NOT_CONSUMED"`; go_phrase matches protocol §9 verbatim. `check_launch_gates` consumes ONLY a structured JSON file at a path: `phrase` == exact registered phrase, `cycle_id`, `typed_by == "owner"`, non-empty `typed_at` (run_evaluation.py:332-348). Chat "intention to score" cannot satisfy the gate — only the file can, and per mission law the owner types it at this cycle's own gate. The gate is currently refusing on its own (measured, GATE_OK False) even before any GO question arises. |
| 10 | Remediation completeness (D1–D4) | **D1 FIXED, D2 FIXED (M1/M2 caveats), D3 IMPLEMENTED (L1–L3 gaps), D4 FIXED** | Detail in the delta section below. |

## Remediation delta — owner-cited defects re-checked

**D1 — plain `elo_diff` + real-CSV tests: FIXED (verified).**
`export_features.py` writes unsuffixed `elo_diff` from the B1-a engine
(line 81-82, comment "AMENDMENT_1 A1"); rebuilt features.csv sha `c86f104d…`
pinned in manifest v2 and recomputed byte-exact; header carries the column;
`load_rows` end-to-end on the real CSV passes (33/33); 3-row equality spot
check passes. The original KeyError path no longer exists.

**D2 — fold-level reliability/slope/CI + verdicts: FIXED (two semantic caveats M1/M2).**
`run_evaluation.run_evaluation` emits per-fold AND pooled reliability bins +
calibration slope for every arm (`_metrics` on each fold and pooled); all 11
registered comparisons get pooled AND per-fold date-cluster bootstrap CIs;
§6 verdicts T1/T2/T3 (+PROGRAM_PASS), R1/R2/R3 (+ANY), INCONCLUSIVE, and
hypotheses H1/H2/H3 with per-comparison CI evidence are all emitted. Selftest
runs end-to-end (`--synthetic-selftest` with required args): `SELFTEST PASS v2`,
deterministic repeat, verdicts emitted, no real data touched.
`test_output_completeness_v2` pins structure. Caveats: H1's REJECT predicate
adds an extra OR term beyond the §1 falsification rule (M1); INCONCLUSIVE uses
a broader predicate than §6's "all decision CIs include 0" (M2).

**D3 — hardened gates: IMPLEMENTED and demonstrably firing (partial gaps L1–L3).**
Measured live in `check_launch_gates` (run_evaluation.py:277-349): pinned
absolute games/features paths (refusal shown for a wrong `--games`); required
ledger + fixed results dir from the manifest (no `--out` on the CLI at all);
structured GO record (phrase/cycle/typed_by/typed_at — wrong-phrase refusal
shown, exit 3); dirty-tree check (fired during this audit on the E2r2
artifacts); A7-artifact existence + token check; heavy-lock FREE_PROVEN check
(`researchctl locks inspect` → `FREE_PROVEN` at audit time). The hardened
gates work — in fact they are what catches C1 below.

**D4 — f1 stream frozen: FIXED.**
AMENDMENT_1 A1 names the stream (B1-a, K=16, HCA=0) with rationale and
no-outcome-contact statement; manifest `constants.f1_stream` pins it; export
source implements it; the CSV equality check (item 2) confirms it.

## Findings

### C1 — CRITICAL: the freeze commit itself violates the frozen drift law; the package cannot pass its own launch gate
`git diff 2c64b6f3..227e3faa` = `nba_winprob/make_freeze_manifest.py` (M) +
`research/control/NBA-WINPROB-SCORED-V1/FREEZE_MANIFEST.json` (M). The first
path is inside `nba_winprob/`, which the manifest's own drift law declares
immutable from code_freeze_sha, and outside `post_freeze_allowlist`. The
shipped gate (`run_evaluation.py:307-312`) executes exactly this diff at
launch and refuses on both counts. **Measured live** with the shipped code:

```
GATE_OK: False
  - CODE DRIFT (nba_winprob/ immutable): ['nba_winprob/make_freeze_manifest.py']
  - post-freeze drift outside allowlist: ['nba_winprob/make_freeze_manifest.py']
```

These two reasons are permanent for the package as committed — no owner GO
record, lock state, or A7 report can clear them. The freeze commit (227e3faa,
parent = 2c64b6f3 verified) bundled the schema-@2 generator upgrade with the
manifest it generates; the generator change had to land inside the
code-freeze snapshot (or a freeze v3 with corrected sequencing is required).
Mitigations measured: the drifted file is the manifest-generator utility, not
the scientific path — `run_evaluation.py`, `protocol.py`, `elo.py`,
`features.py`, `export_features.py`, `evaluate.py` are all byte-identical to
the frozen snapshot (diff shows only the generator + the manifest); and the
hardened gate caught the drift, so no silent launch is possible. Resolution
requires an owner-visible re-freeze (freeze v3 with the generator inside the
snapshot, or a gate-consistent reconciliation) and a fresh A7 delta. I did not
repair anything (audit lane is read-only by charter).

### M1 — MEDIUM: H1 REJECT predicate deviates from the preregistered falsification rule
`run_evaluation.py:228-230`: `"REJECT": all(not arm_favors(f"{a}_vs_B0") for a
in B1_ARMS if a == b1star) or all(not arm_favors(...) for a in B1_ARMS)`.
Protocol §1: "H1 REJECT iff ALL FOUR 95% CIs … include 0 or lie entirely > 0."
The second term is the registered rule; the first OR term additionally rejects
H1 when only the B1\* arm fails to beat B0 — a state the registered "iff"
forbids rejecting in. The emitted `rule` string itself states only the
registered rule, so the implementation contradicts its own documentation, and
AMENDMENT_1 A2's "No thresholds change — they are §6 verbatim." Tests type-check
the verdicts but do not pin H1 semantics, so a wrong terminal hypothesis
verdict could ship silently in the edge case. Blast radius limited: all four
per-arm CIs + `favors_arm` flags are emitted as evidence, so the registered
rule is recomputable from outputs.

### M2 — MEDIUM: INCONCLUSIVE predicate broader than §6
`run_evaluation.py:224-225` labels INCONCLUSIVE whenever `not PROGRAM_PASS and
not REJECT.ANY and T2 holds`. §6 defines INCONCLUSIVE as "all decision CIs
include 0 while T2 holds". E.g., "T1 pooled CI < 0 but < 4/7 folds negative"
(a decisive CI with a failed fold rule) gets labeled INCONCLUSIVE where §6 is
silent. Terminal-state labeling should be verbatim; it is not.

### M3 — MEDIUM: registry row stale vs freeze v2
cycles[87] still carries `head 07f8e1b6` (round-1 audit commit), phase text
"[round-1 authorization token] 9/9 … freeze 39b11156 … findings F1-F4 LOW"
(literal omitted per L6), updated 12:27:05Z — i.e., the superseded round-1
state, ~1h before freeze v2 (13:30:17Z). Budget 0/9, s1 SEALED_UNTOUCHED, go_phrase_state
REGISTERED_NOT_CONSUMED are correct. Risk: an authority surface advertises a
PASS that this audit supersedes. Only the controller may reconcile the
registry (lane boundary); must be updated together with the round-2 verdict.

### L1 — LOW: `--ledger` CLI override survives (partial A3)
`run_evaluation.py:415,430`: ledger defaults to the manifest's required path
but an operator can pass `--ledger /tmp/x.jsonl`, forking trial accounting.
The canonical `scored_summary.json` still lands in the fixed results dir, so a
fork is detectable post hoc; A3's "required ledger path" is thus only
default-pinned, not enforced.

### L2 — LOW: gate skips data-hash verification for absent files
`run_evaluation.py:298-300`: `if os.path.exists(...) and sha != pinned` — only
pinned games/features get explicit existence checks (295-297); raw/lineages/
participants deleted from disk would not fail the gate. None of the three is
read by the runner, so no outcome risk; chain-of-custody weakening only.

### L3 — LOW: `typed_at` not validated as ISO
A3 promises "typed_at ISO"; the gate (line 345-346) only checks truthiness.

### L4 — LOW: selftest banner says "7 comparisons"; actual count is 11
`run_evaluation.py:422` — cosmetic, but it contradicts the assertion two lines
down and the manifest's 11 registered comparisons.

### L5 — LOW: selftest requires dummy `--freeze-manifest/--go-record` args
The `--synthetic-selftest` branch sits after argparse `required=True` for those
flags (line 416-421); bare invocation exits 2 (argparse) before reaching the
branch. Round-1's F1 nuance persists in v2 form.

### L6 — MEDIUM-adjacent note: the A7-artifact gate is a naive substring match
`run_evaluation.py:322-324` passes the A7 gate iff the report file CONTAINS the
authorization token. A refusal report that quotes the token (as round-1's
quoting style would) would satisfy the check. This report deliberately does
NOT contain the token string; if a future re-audit lands AUTHORIZED, the token
will be present legitimately. Defense-in-depth only — the owner GO record
remains the operative second key — but the check cannot distinguish an
authorization from a refusal that mentions the token.

### L7 — LOW: tree not clean at audit end (expected lane flow)
Clean at audit start; during the audit the concurrent E2 round-2 lane landed
two uncommitted allowlisted-path artifacts; plus this audit's own two files.
All inside `research/control/NBA-WINPROB-SCORED-V1/**`. The clean-tree launch
gate is satisfied once the controller commits them.

## What would clear this audit

1. Owner-authorized freeze v3 (or gate-consistent reconciliation) that puts
   `make_freeze_manifest.py` v2 inside the measured code snapshot, so
   `git diff code_freeze_sha..HEAD` touches allowlisted control/results paths
   only; regenerate manifest; E2+A7 delta re-audit (fast: all other items pass
   today and the scientific files are already frozen).
2. Fix M1 (drop the extra OR term so H1 REJECT is exactly the §1 rule) and M2
   (verbatim INCONCLUSIVE predicate) inside that new snapshot, with a
   semantics-pinning test each.
3. Controller commits E2r2 + A7r2 artifacts and reconciles the registry row
   (M3) to the new freeze.
4. Optionally L1 (drop `--ledger` or gate-refuse non-canonical values), L2
   (fail on missing pinned files), L3 (ISO-parse `typed_at`), L4 (banner), L5
   (argparse order).

Until then: **scoring must not be attempted.** The gate will refuse (measured),
the ledger remains 9 PREREGISTERED / 0 COMPUTED, and no outcome has been
observed — the cycle remains safely pre-outcome.

— A7 round-2 auditor, 2026-10-04
