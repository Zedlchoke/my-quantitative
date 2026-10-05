# AUDIT_TERMINAL — NFL-WINPROB-SCORED-V1 (A7 TERMINAL)

- Auditor: independent A7 terminal auditor (fresh session; read-only git; no repairs)
- Date: 2026-10-05
- Measured HEAD at audit time (dispatch_sha): `2c6a22d6ea3cf456f9ac1d999f8c058da3080638`
  (branch `orca/nfl-winprob-scored-v1-integration`, tree clean, 0 dirty files)
- Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
- Verdict: **A7_TERMINAL_CONFIRM** (findings: 1 LOW, 1 INFO — none blocking)

## 1. GO validity — PASS

- `GO_RECORDED.json` phrase = `"GO NFL WINPROB SCORED V1 EVALUATION"` — verbatim equal to
  `FREEZE_MANIFEST.json.go_phrase` and to the phrase registered in
  `plans/PLAN_nfl_winprob_scored_v1.md` (grep-verified).
- `typed_by` = `"owner"`; `typed_at` = `"2026-10-05T00:26:44Z"` (ISO 8601).
- Two-key order in git (linear history, no merges):
  - `18412f48` 2026-10-04T21:15:28+07:00 FREEZE v2 (code_freeze_sha `91dcff14…`)
  - `c56451d3` 2026-10-04T21:26:30+07:00 A7 R4 AUTHORIZED_CONDITIONAL_ON_PIN resolved by the manifest-only pin move (allowlisted control/**)
  - `86166ab7` 2026-10-05T07:26:59+07:00 = 2026-10-05T00:26:59Z **GO RECORDED** — commit contains exactly one file: `research/control/NFL-WINPROB-SCORED-V1/GO_RECORDED.json`; 15s after `typed_at`.
  - `2c6a22d6` 2026-10-05T00:33:55Z results (ledger + scored_summary.json).
- `go_phrase_state` = `REGISTERED_NOT_CONSUMED` in the frozen manifest (frozen pre-GO); the run happened only after the record existed: ledger `computed_at_utc = 2026-10-05T00:33:27+00:00` > GO commit `00:26:59Z`.
- Runtime claim 60.6s consistent with a sequential run after NBA's (NBA computed 00:31:22Z, NFL start ≈ 00:32:26Z → computed 00:33:27Z).

## 2. Ledger / denominators — PASS

- `TRIAL_LEDGER.jsonl` = 18 rows: 9 `PREREGISTERED` (class PRIMARY, `observed:false`, per-arm spec, registered_at 2026-10-04T13:36:33+00:00) + 9 `COMPUTED` (class PRIMARY). **No REPRO rows.** No other statuses.
- Exactly 9 COMPUTED rows, each arm once: B0, B1-a, B1-b, B1-c, B1-d, B2-a, B2-b, B2-c, B2-d; all `cycle_id = NFL-WINPROB-SCORED-V1`; schema `nfl_winprob_trial_ledger@1` on every row (the earlier round-1 "NBA-schema label remnant" LOW is confirmed closed — zero NBA strings).
- Observed denominator 9/9 (registry phase text). Registry `budget {used:0, max:9}` with `denominators.note = "see HYPOTHESIS_LEDGER.md (P-9)"` — ledger-as-authority per P-9 precedent.
- All 9 pooled LL/Brier values in ledger byte-equal (1e-15) to summary `pooled_rs` (recomputed).

## 3. Summary integrity — PASS (38/38 independent recompute)

- `scored_summary.json`: 9 arms with `spec`/`kind` exactly equal to manifest arms (K{20,40}×HCA{0,65}; B2 feature sets); `test_seasons` = [2019..2025] == manifest; `fold_meta` keys == 7 test seasons.
- Comparisons: pooled keys (11) == per-fold keys (11) == manifest `registered_comparisons` (no extra, none missing); every per-fold comparison has exactly the 7 test seasons as keys.
- Internal consistency (all 9 arms): fold n's sum == pooled n (1865); reliability bins sum == pooled n (1865); `fold_meta` n_rs sums to 1865; fold keys == test seasons.
- Playoff segment separate: `pooled_playoffs_separate` on all 9 arms, n=89 == Σ fold `n_po` (11+13×6); B2-a playoff LL 0.6299155 matches commit-message "0.62992 n=89". RS and PO never mixed.
- Ties disclosed per fold: n_ties_excluded_disclosed = {2019:1, 2020:1, 2021:1, 2022:2, 2023:0, 2024:0, 2025:1}, total 6 == commit message "6 total".
- Verdict predicates recomputed from summary CIs: all three decision comparisons include 0 (B2-a_vs_B1* [-0.00526,+0.00877]; B2-a_vs_B2-b [-0.00105,+0.00123]; B2-a_vs_B2-c [-0.00555,+0.00146]) AND T2 PASS (slope 0.97714 in [0.85,1.15]) → preregistered sec6 predicate "all decision CIs include 0 while T2 holds" → **INCONCLUSIVE=true correct** (fired per predicate, not post-hoc). H1 ALIVE (B1*_vs_B0 CI [-0.06757,-0.03797] excludes 0), H2 REJECTED, H3 REJECTED, R1-R3 not fired, PROGRAM_PASS=false. Continuation-gating language ("NEW registered cycle with NEW mechanism claim") is the protocol's own sec6 sentence, verbatim.

## 4. Twin evidence — CONFIRMED (independently re-run by this auditor)

- `cmp /tmp/nfl_twin/research/control/NFL-WINPROB-SCORED-V1/results/scored_summary.json <worktree>/results/scored_summary.json` → exit 0, **IDENTICAL**.
- sha256 both sides: `48b2378a2f7eff9c919de1eb3b3e5a0c1551a6e95ee1e72dd143bafc1bc47b8b`.
- Twin clone HEAD = `2c6a22d6` (same results commit as worktree). NOT the TWIN_EVIDENCE_FROM_CONTROLLER_LOG fallback — evidence re-verified first-hand.

## 5. Verdict language law — PASS

- grep `(?i)(pnl|profit|bet|betting|\bedge\b|stake|wager|odds|kelly|bankroll|\broi\b|\barb\b|market|moneyline|spread\b|handicap|bookmaker|casino|\bev\b)`:
  - scored_summary.json: only the `language_law` declaration line itself — a negation, expected.
  - commit messages 9639706f..HEAD: single token hit `"odds"` inside "odds-token sweep clean" (E2 verification narrative reporting that the sweep found nothing) — negation/verification context, not vocabulary use.
- No post-outcome re-tuning: `git log 91dcff14..HEAD -- nfl_winprob/` is empty (code byte-unchanged since code_freeze_sha); results commit is HEAD; nothing exists after results except this audit. INCONCLUSIVE predicate shown above to be arithmetic consequence of frozen CIs, not tuning.

## 6. S1 / seal / boundaries — PASS

- Registry `s1 = SEALED_UNTOUCHED`. No S1 references in `nfl_winprob/*.py`. Runners take explicit `--games/--features/--freeze-manifest/--go-record`; inputs verified against pins by hash below.
- No push/merge: branch has **no upstream**; zero merge commits in 9639706f..HEAD; no accounts/purchases in the cycle range.
- Raw/derived data hashes recomputed from bytes, all equal manifest:
  - raw/games.csv `f1e8fe78…5248e` ✓; derived/games_nfl.csv `f7909fa5…21565` ✓; **derived/features_nfl.csv `4ee2175e…f982` ✓**; derived/lineages_nfl.csv `977a43e2…7aff0` ✓; raw/ATTRIBUTION.md `b1852975…3aedc` ✓.
- Protocol digest recomputed: `5b035a1c…7c31` == manifest `protocol_digest`. `predecessor_tip 9639706f` is an ancestor of HEAD (merge-base verified); the registry PREP head (65087562) is stale-by-design, superseded by the erratum remediation at 9639706f — disclosed in the registry phase text.

## Findings (non-blocking)

1. **LOW** — Registry `go_phrase_state` still `REGISTERED_NOT_CONSUMED` after consumption (phase text documents "GO consumed at own gate 2026-10-05T00:26:44Z"); same cosmetic sync lag as NBA; controller-owned file, no gate consumed the stale field post-run.
2. **INFO** — Results commit message cites runtime 60.6s while ledger `computed_at` is ~6.5 min after the GO commit; consistent with sequential execution after the NBA cycle (NBA computed 00:31:22Z, NFL computed 00:33:27Z, registry updated between). No impact.

## Final

**A7_TERMINAL_CONFIRM** — GO law, denominators, summary integrity, twin byte-identity, language law, and S1/seal/boundaries all reconcile; the INCONCLUSIVE terminal state is the exact arithmetic consequence of the preregistered sec6 predicate (all decision CIs include 0 while T2 holds), with continuation correctly gated to a new registered cycle. Findings LOW/INFO only; none affect validity.
