# A7 FOREX-FREE-V1 Terminal Audit (FXFV1-A7-TERMINAL-V1)

- **Auditor:** A7
- **Measured at (UTC):** 2026-09-03T15:40:26Z
- **Audited tip:** `d354e9cd1f892402d3e044eb8d94bb7786244c36` (`orca/forex-free-v1-f7-a7-prelaunch`, reset to the integration tip per cycle precedent — see O4)
- **W1 sha:** `f33a32a2f245d08447a67bb6a0b1f7276c7c5a85`
- **Runner sha256:** `c71176e31cd63f28ea166f8469d36b54ca305f684eec1e47528a5987bf3ca1be`
- **Staged freeze sha256:** `78db42051d54be9dbd769d46a612de4d22dbc5e96e69484a3baae3156d9c0e42`
- **Published ledger sha256:** `066db4337e31139d7c9dc08703b1afb4f5b54a9a394c8273864fdc92677eecd7`
- **Reproduction verdict:** `REPRODUCTION_ALL_MATCH` (independently recomputed and confirmed)
- **Authorization:** `research/control/forex_free_v1_run/w1_launch_verdict.json` + `research/audits/forex_free_v1/prelaunch/a7_w1_delta_audit_v4.json` (VERDICT `FOREX_FREE_V1_W1_LAUNCH_AUTHORIZED`, blockers: none)

## Recommended sprint verdict: `FOREX_FREE_V1_REJECT_ALL`

All six frozen cells FAIL Stage-A (`EXPECTANCY_NONPOSITIVE` x6); no family survives; the negative
result is complete, exactly reproduced, and preserved as evidence. No stronger label (any
PASS/survivor label) is available because zero cells pass Stage-A; the outcome is a completed
negative result rather than BLOCKED or INCOMPLETE_NOT_PROMOTABLE because both denominators are
full (observed = published = 6), reproduction is exact 6/6, and evidence is committed.

## Check results

### C1 — W1 pin: PASS
- `exec-2` and `repro-2` are detached exactly at `f33a32a2f245d08447a67bb6a0b1f7276c7c5a85` (git rev-parse).
- Staged `w1_freeze.json` in both trees hashes to `78db4205...` and is byte-identical (cmp) to the committed integration freeze; freeze `FOREX_FREE_V1_W1 = f33a32a`.
- `sha256(scored_runner.py @ f33a32a) = c71176e3...` equals the authorized runner hash; the runner is byte-identical across exec-2 / repro-2 / the f33a32a blob; freeze `code_hashes` 6/6 re-verified against f33a32a blobs.
- Authoritative `staged_data_manifest.json` replay re-run by A7: 312/312 ok, 0 mismatch, 0 missing across both trees; manifest W1 = freeze W1.

### C2 — Scored ledger: PASS
- `research/control/forex_free_v1_run/scored_ledger_published.jsonl`: exactly **6 entries**, one per frozen cell (family1/family2 x anchor/neighbour/control — key set matches `w1_freeze.six_arm_config_digests`).
- Digests are content-addressed (sha256 over canonical JSON of family, arm, tier, pairs, **full trade list**, module authorization fields); 6 unique digests / 6 unique labels, **published exactly once each** (once-per-digest idempotency in `publish_cell`; ledger multiplicity check clean).
- Committed ledger sha256 `066db433...` == `ledger_sha256` in **both** execution summaries == sha256 of exec-2's and repro-2's local ledgers (all byte-identical). Committed `execution_summary.json` is byte-identical to both exec-2 and repro-2 copies.
- Every entry records `w1_sha = f33a32a` and the module `scoring_authorized` field verbatim.

### C3 — Reproduction: PASS — `REPRODUCTION_ALL_MATCH` confirmed
- A7 independently recomputed the comparison: exec-2 vs repro-2 cell digests 6/6 equal (trades, total_pnl < 1e-9, gates equal per cell); published ledger digest-by-digest == both summaries == both local ledgers.
- `reproduction_report.json` claims (all_digests_match, ledger_digest_match, verdict `REPRODUCTION_ALL_MATCH`) are **confirmed by independent recomputation**.
- **O1 (MEDIUM):** the report file itself is **untracked** in the integration worktree — never committed. Claim verified; artifact must be committed at closeout.

### C4 — Cell sanity: PASS
- All six gates in **both** trees = `[false, "EXPECTANCY_NONPOSITIVE"]`.
- Direction coherence confirmed: family1 control −3.6473 worse than anchor −2.3527; family2 control −3.1043 worse than anchor −2.8957; family1 neighbour −3.1597 weaker than anchor as predicted. Family2 neighbour −2.7196 slightly **better** than anchor — recorded as an observation only (O3); it changes no gate.
- No re-run / re-score / substitution: exactly one `SIX_CELLS_SCORED` event, zero events after it; `publish_cell` refuses a second publication per digest and hard-gates on `LAUNCH_AUTHORIZATION_MISSING` / `LAUNCH_NOT_AUTHORIZED` / `W1_SHA_MISMATCH` (scored_runner.py:166-171); state.json `scored_cells` digests == published digests; repro-2's independent rerun reproduced all six digests from a separate tree.
- observed = 6 = published = 6; budget 6/6 consumed exactly (`planned=6, computed=6`); denominators `{published: 6, observed: 6}`.

### C5 — Boundary: PASS
- **S1:** `SEALED_UNTOUCHED` declared in `run_contract.json`, `state.json`, `selection_freeze.json`; "inspecting S1" is a forbidden action; the cycle diff touches no S1 or `forex_run` control paths.
- **No paper/live/orders/credentials:** cycle diff (39650c5..d354e9c, 14 files) contains none; the only credential-adjacent content is a negative test asserting `api_key` is absent from the runner source.
- **No push, no main-merge:** zero merge commits in the cycle range; `main` does not contain the cycle base; no `origin/*forex-free-v1*` remote branches (never pushed).
- **Workers zero:** heartbeat `owned_workers=0`, `owned_worker_pids=[]`; no cycle processes running at audit time; execution was serial (anchor -> neighbour -> control per family).
- **Raw data never committed:** `data_raw/` gitignored (.gitignore:17), 0 tracked files; catalog/ and results/ matches are pre-existing old-cycle files outside the cycle diff.
- **No old-cycle rescue/re-grade:** `selection_freeze.json` rescue_check PASS ("no hidden rescue of the six frozen old proposals"); event log records 0 rescues.

### C6 — Verdict: `FOREX_FREE_V1_REJECT_ALL`
- Stage-A requires after-cost expectancy > 0 (PLAN_forex.md §13); every cell is negative (−2.35 to −3.65 per trade, 10k USD unit) — the failure is mechanism-level, and direction coherence (controls weaken both mechanisms) supports the negative reading rather than a gate artifact.
- Process clean and complete (C1–C5 PASS): the correct closeout label is the strongest allowed, `FOREX_FREE_V1_REJECT_ALL`; negative results preserved as evidence (content-addressed ledger, byte-identical summaries, state, event log, this audit).

## Per-cell table

| Cell | Digest (sha256, first 16) | Gate | Trades | Expectancy | PF | Total PnL | exec=repro | Published |
|---|---|---|---|---|---|---|---|---|
| family1:anchor | `ad04f64a351e40a7` | FAIL EXPECTANCY_NONPOSITIVE | 11459 | −2.3527 | 0.8489 | −26,959.22 | yes | yes |
| family1:neighbour | `5fccd108c55706bc` | FAIL EXPECTANCY_NONPOSITIVE | 11512 | −3.1597 | 0.6286 | −36,374.00 | yes | yes |
| family1:control | `d679f851c32da2b1` | FAIL EXPECTANCY_NONPOSITIVE | 11459 | −3.6473 | 0.7756 | −41,794.78 | yes | yes |
| family2:anchor | `2ed1f8cff277f824` | FAIL EXPECTANCY_NONPOSITIVE | 1020 | −2.8957 | 0.6376 | −2,953.57 | yes | yes |
| family2:neighbour | `4c4ddea9c689db28` | FAIL EXPECTANCY_NONPOSITIVE | 142 | −2.7196 | 0.8874 | −386.18 | yes | yes |
| family2:control | `3cd4b4993784e09a` | FAIL EXPECTANCY_NONPOSITIVE | 1020 | −3.1043 | 0.6180 | −3,166.43 | yes | yes |

Full digests are in `a7_terminal_audit.json` (per_cell_table). Budget: 6/6 consumed exactly.

## Objections

| ID | Severity | Finding | Blocking |
|---|---|---|---|
| O1 | MEDIUM | `reproduction_report.json` is untracked in the integration worktree (absent from d354e9c). The `REPRODUCTION_ALL_MATCH` claim is independently confirmed by A7, but the artifact is not preserved in git. A1 must commit it (with a refreshed state.json) at closeout. | no |
| O2 | LOW | state.json bookkeeping stale: `measured_at_utc` 01:15:00Z predates the 15:20:00Z scoring event; phase `F8_SCORED_6_6_REPRODUCTION_PENDING` and `verdict: null` are accurate pre-terminal but not refreshed after reproduction. Scored content itself is correct and matches the ledger. | no |
| O3 | LOW | family2 neighbour (−2.7196) slightly better than family2 anchor (−2.8957), opposite of the predicted ordering (family1 neighbour is weaker as predicted). Observation only — rescues nothing, since every cell fails `EXPECTANCY_NONPOSITIVE`. | no |
| O4 | LOW | `git merge --ff-only` to the integration tip was impossible (lane v4 commit 3834dc1 and integration copy 1ffd62d both descend from 4e763fb); lane reset to the integration tip d354e9c per cycle precedent. Superseded lane-only v2/v3 blobs remain reachable at 3834dc1 but are not in the integration tip tree (v4 blobs are, byte-identical). | no |

## Blockers

None.

*Audit-only lane: no repair applied to scored artifacts; the lane received only the two audit deliverables.*
