# DFV1 dispatch — COMMON rules (every lane packet includes this by reference)

Cycle: DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1. Plan:
`plans/PLAN_data_foundation_fx_crypto_stocks_v1.md` (read §1-§6, §8, §14 in
full from your worktree). Owner directive (binding, entire file):
`research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/OWNER_DIRECTIVE.md`.

## Identity
- Base/dispatch SHA: `189c6d23ab2a6f50475819cf6df2e2e4def92820` (your branch
  HEAD at spawn; verify with `git -C <worktree> rev-parse HEAD`).
- Use `.venv/bin/python` from the ROOT checkout for any python need
  (`/Users/hoangminhlong/my-quantitative/.venv/bin/python`); never another
  interpreter silently.

## Hard boundaries (violating any = incident)
- OFFLINE lane: **zero network requests** (probes are A1-only, later).
- Read-only everywhere EXCEPT your allowed write paths inside YOUR worktree.
- NEVER read: `.env` or any credentials/secrets; S1/sealed/holdout file
  CONTENT (sealed inventory = committed-manifest metadata only — plan §14 F8);
  `research/wayfinder/` is readable but NOT writable; other cycles' control
  dirs readable, NOT writable; `plans/` read-only.
- NEVER: push, merge, rebase, history ops, `git add -A` (stage by pathspec
  only), touching another worktree, killing any process, `reset`/`clean`.
- No heavy jobs: run your first substantive chunk under `/usr/bin/time` and
  ABORT+report if projected >10 min CPU or >1 GB temp (plan §14 F10 —
  measured, not estimated). One lane = one light process; no parallel workers.
- Racing-read rule (§14 F5): datasets owned by an ACTIVE_LIGHT cycle with
  workers>0 or heartbeat <24h old → metadata-only census
  (`manifest_verify: INHERITED_NOT_REHASHED_LIVE_OWNER`, using that cycle's
  COMMITTED manifests); NEVER write MISMATCH from a possibly mid-write file.
- Hashing budget: full re-hash only when a committed SHA256SUMS/manifest
  exists AND corpus ≤500 MB; else sample ≤20 files + total byte/file count,
  and set `manifest_verify: SAMPLED` with the sample size stated. File
  existence alone NEVER yields AVAILABLE_VALIDATED (plan §5).
- Truth discipline: statuses only from the enum; missing evidence = NOT_RUN
  with reason; numbers in prose come from your own artifact fields (P-19).
  Shas measured (`git rev-parse` / `shasum -a 256`), never typed from memory.

## Authority-row output (plan §5 schema, one JSON object per line)
Write `inventory_rows.jsonl` in your lane dir. Every row needs
`status_evidence` naming the command/artifact that produced the status.
`AVAILABLE_VALIDATED` requires THIS-cycle re-measurement (manifest verify +
coverage census: instruments, first/last timestamp, row/file counts,
measured_from: bytes). Use `INHERITED_NOT_REHASHED_LIVE_OWNER`, `SAMPLED`,
`NO_MANIFEST`, `MISMATCH`, `NOT_RUN` as measured.

## Deliverables in your worktree (relative to worktree root)
1. `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/<lane>/inventory_rows.jsonl`
2. `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/<lane>/LANE_REPORT.md`
   — what exists, what is validated, what is missing (gap candidates with:
   why needed, hypothesis class opened, which recorded kill it fixes, which
   control would falsify its value, priority, cost/volume estimate)
3. `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/<lane>/HANDOFF_<lane>.json`
   — schema `zcode_orch_v3_handoff@1`: {schema, task_id: "dfv1-<lane>",
   cycle_id, role, lane, dispatch_sha, actual_start_sha, commit_sha,
   changed_paths, tests (list of {command, exit_code, result} for your
   validation commands), authority_claims (list), known_limitations,
   incidents, tree_status, workers: 0, outputs (absolute paths)}

## Commit discipline
- Verify `pwd` + `git -C <worktree> branch --show-current` + `rev-parse HEAD`
  before and after; stage by explicit pathspec; one clean commit on YOUR
  branch; tree clean at handoff; write the handoff JSON BEFORE the final
  `git status` check and include it in the commit.
- If you cannot complete an item: leave it NOT_RUN with reason in the report;
  never pad, never infer.

## Stop conditions for your lane
- Scope of your packet exhausted (every listed dataset has a row or explicit
  NOT_RUN reason), or 2 abort-threshold events, or any boundary hit → stop,
  commit what is honest, hand off with limitations.
