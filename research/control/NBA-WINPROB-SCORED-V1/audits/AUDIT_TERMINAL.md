# AUDIT_TERMINAL — NBA-WINPROB-SCORED-V1 (A7 TERMINAL)

- Auditor: independent A7 terminal auditor (fresh session; read-only git; no repairs)
- Date: 2026-10-05
- Measured HEAD at audit time (dispatch_sha): `a1708045420b632e3d92b849182076b51f80b3bf`
  (branch `orca/nba-winprob-scored-v1-integration`, tree clean, 0 dirty files)
- Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
- Verdict: **A7_TERMINAL_CONFIRM** (findings: 1 LOW, 3 INFO — none blocking)

## 1. GO validity — PASS

- `GO_RECORDED.json` phrase = `"GO NBA WINPROB SCORED V1 EVALUATION"` — verbatim equal to
  `FREEZE_MANIFEST.json.go_phrase` and to the phrase registered in
  `plans/PLAN_nba_winprob_scored_v1.md` (grep-verified).
- `typed_by` = `"owner"`; `typed_at` = `"2026-10-05T00:26:44Z"` (ISO 8601).
- Two-key order in git (all commits on this branch, linear, no merges):
  - `3c2731f1` 2026-10-04T20:58:43+07:00 FREEZE v3 (code_freeze_sha `685f10ef…`)
  - `ae5ba282` 2026-10-04T21:10:34+07:00 A7r3 AUTHORIZED (manifest-only a7_report_path pin, allowlisted control/**)
  - `772e0c85` 2026-10-05T07:26:59+07:00 = 2026-10-05T00:26:59Z **GO RECORDED** — commit contains exactly one file: `research/control/NBA-WINPROB-SCORED-V1/GO_RECORDED.json`; commit instant is 15s after `typed_at`.
  - `a1708045` 2026-10-05T00:32:19Z results (ledger + scored_summary.json).
- `go_phrase_state` = `REGISTERED_NOT_CONSUMED` in the frozen manifest (frozen pre-GO); the run happened only after the record existed: ledger `computed_at_utc = 2026-10-05T00:31:22+00:00` > GO commit `00:26:59Z`.
- Runtime claim 252.6s consistent: GO commit 00:26:59Z → computed_at 00:31:22Z.

## 2. Ledger / denominators — PASS

- `TRIAL_LEDGER.jsonl` = 18 rows: 9 `PREREGISTERED` (class PRIMARY, `observed:false`, per-arm spec, registered_at 2026-10-04T12:09:43Z) + 9 `COMPUTED` (class PRIMARY). **No REPRO rows.** No other statuses.
- Exactly 9 COMPUTED rows, each arm once: B0, B1-a, B1-b, B1-c, B1-d, B2-a, B2-b, B2-c, B2-d; all `cycle_id = NBA-WINPROB-SCORED-V1`; schema `nba_winprob_trial_ledger@1` on every row.
- Observed denominator 9/9 (registry phase text). Registry `budget {used:0, max:9}` with `denominators.note = "see HYPOTHESIS_LEDGER.md (P-9)"` — ledger-as-authority per P-9 precedent (P-9 note present in `research/wayfinder/HYPOTHESIS_LEDGER.md`).
- All 9 pooled LL/Brier values in ledger byte-equal (1e-15) to summary `pooled_rs` (recomputed).

## 3. Summary integrity — PASS (38/38 independent recompute)

- `scored_summary.json`: 9 arms with `spec`/`kind` exactly equal to manifest arms (incl. AMENDMENT_1 f1_stream B1-a); `test_seasons` = [2009..2015] == manifest; `fold_meta` keys == 7 test seasons.
- Comparisons: pooled keys (11) == per-fold keys (11) == manifest `registered_comparisons` (no extra, none missing); every per-fold comparison has exactly the 7 test seasons as keys.
- Internal consistency (all 9 arms): fold n's sum == pooled n (8369); reliability bins sum == pooled n (8369); `fold_meta` n_rs sums to 8369; fold keys == test seasons.
- Playoff segment separate: `pooled_playoffs_separate` on all 9 arms, n=587 == Σ fold `n_po` (85+82+81+84+85+89+81); B2-a playoff LL 0.6201289 matches commit-message "0.62013 n=587". RS and PO never mixed.
- Verdict predicates recomputed from summary CIs: B2-a_vs_B1* CI [-0.00326,+0.00128] includes 0 (T1 FAIL, 5/7 folds negative); B2-a_vs_B2-c includes 0; B2-a_vs_B2-b CI [-0.00235,-0.00000] excludes 0 → "all decision CIs include 0" is FALSE with T2 PASS → INCONCLUSIVE=false correct. PROGRAM_PASS=false, REJECT.ANY=false. Verdict-taxonomy gap (no terminal label fully fits: strong Elo gain vs B0, no significant B2-a gain over B1*) is documented in summary + commit message and reported as-is; no rescue attempted (predicate arithmetic above confirms no label was forced).

## 4. Twin evidence — CONFIRMED (independently re-run by this auditor)

- `cmp /tmp/nba_twin/research/control/NBA-WINPROB-SCORED-V1/results/scored_summary.json <worktree>/results/scored_summary.json` → exit 0, **IDENTICAL**.
- sha256 both sides: `8aa680ed5c5183f25caba2f326523354635a484e2c097434faf3af8e010de52b`.
- Twin clone HEAD = `a1708045` (same results commit as worktree). Twin artifacts present; NOT the TWIN_EVIDENCE_FROM_CONTROLLER_LOG fallback — evidence re-verified first-hand.

## 5. Verdict language law — PASS

- grep `(?i)(pnl|profit|bet|betting|\bedge\b|stake|wager|odds|kelly|bankroll|\broi\b|\barb\b|market|moneyline|spread\b|handicap|bookmaker|casino|\bev\b)`:
  - scored_summary.json: only the `language_law` declaration line itself ("calibration language only; no PnL/betting/edge vocabulary") — a negation, expected.
  - commit messages b5b50847..HEAD: single token hit `"stake"` = substring of "mistake" (freeze-generator commit message) — false positive, not vocabulary use.
- No post-outcome re-tuning: `git log 685f10ef..HEAD -- nba_winprob/` is empty (code byte-unchanged since code_freeze_sha); results commit is HEAD; nothing exists after results except this audit. Registry `go_phrase_state`/`budget` remain in their frozen-state values by design (P-9).

## 6. S1 / seal / boundaries — PASS

- Registry `s1 = SEALED_UNTOUCHED`. No S1 references in `nba_winprob/*.py` (only `res1` variable-name substring). Runners take explicit `--games/--features/--freeze-manifest/--go-record`; inputs verified against pins by hash below.
- No push/merge: branch has **no upstream**; zero merge commits in b5b50847..HEAD; remote `origin` exists but branch untracked. No accounts/purchases anywhere in the cycle range.
- Raw/derived data hashes recomputed from bytes, all equal manifest:
  - raw/nbaallelo.csv `d46ed354…616bc` ✓; derived/games.csv `e24d9a3b…f098` ✓; **derived/features.csv `c86f104d…c86b` ✓**; derived/lineages.csv `c8cdd58a…61c1` ✓; derived/participants.csv `fd7cb539…1bf` ✓; raw/ATTRIBUTION.md `e134e20c…490a` ✓.
- Protocol digest recomputed: `c058760d…51f7` == manifest `protocol_digest`. `predecessor_tip b5b50847` is an ancestor of HEAD (merge-base verified).

## Findings (non-blocking)

1. **LOW** — Registry `go_phrase_state` still `REGISTERED_NOT_CONSUMED` after consumption; the phase text documents "GO consumed at own gate 2026-10-05T00:26:44Z" and controller context pre-disclosed "registry sync pending". Cosmetic sync lag in a controller-owned file; no gate consumed the stale field post-run.
2. **INFO** — `results/scored_summary.json` mtime (07:37 local) postdates the results commit (07:32 local); git status clean ⇒ working-tree bytes == HEAD bytes; consistent with twin-verification rewrite of identical content.
3. **INFO** — Results commit message fragment "(summary force-added past results/ gitignore as cycle evidence)" is ambiguous wording; actual state measured: the file is tracked and not matched by any ignore rule.
4. **INFO** — H3 "borderline" rests on B2-a_vs_B2-b ci95_hi = -0.00000 (float at zero boundary); the cycle itself labels it borderline rather than clean — honest reporting, no action.

## Final

**A7_TERMINAL_CONFIRM** — GO law, denominators, summary integrity, twin byte-identity, language law, and S1/seal/boundaries all reconcile; verdict output (PROGRAM_PASS=false / no REJECT / INCONCLUSIVE=false with documented taxonomy gap) reproduces exactly from the preregistered predicates. Findings LOW/INFO only; none affect validity.
