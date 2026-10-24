# Independent A7 ROUND2 — BUG_REFUSE

Audited 2026-10-24 on clean target `8490e6101dd47cd353d1c25b6043f6d01c51ff88`, branch `orca/paperdesk-quote-collision-fix-v1-integration`, exact worktree `/Users/hoangminhlong/my-quantitative/.worktrees/paperdesk-quote-collision-fix-v1/integration`. Reviewed only ROUND2 diff from `f7195a2f79b9d98af4047ec3f66e422e79c207b4`, including its caller behavior against the explicit ROUND2 acceptance laws. This is a fresh audit; ROUND1 verdict was not reused. Canonical root registry independently names this target, lane, and ROUND2_TWIN_BATTERY_GREEN_FRESH_A7_PENDING. Registered plan is available in canonical root, absent in lane checkout; canonical plan and ROUND2_OWNER_PLAN.md agree and were read. Global heavy lock measured FREE_PROVEN; no audit workers remain.

## Open finding

**R2-F1 MEDIUM — WSL candidate missing bookmaker or payload bypasses the required identity diagnostic and crashes before W1.4.** In `research/papertrade_exec/wsl_lane.py:897-904`, `cmd_decide` builds its downstream quote using `qrow["bookmaker"]` and `qrow["payload_sha256"]` before calling `quote_collision` at line 909. Independently authored in-memory caller probes remove each field individually from an otherwise populated WSL candidate. Both raise `KeyError` and persist **zero DECISION rows**. The owner requires “Candidate incomplete always QUOTE_IDENTITY_MISSING”; expected is the terminal zero-stake missing-identity decision, with public disclosures where applicable. The helper alone handles these inputs correctly, but the WSL caller never reaches it. The existing ordering predates ROUND2: this is an unmet explicit ROUND2 acceptance requirement, not a claim that ROUND2 introduced the ordering. It remains financially fail-closed, hence MEDIUM rather than HIGH. The caller probe uses actual `wsl_lane.cmd_decide` and actual W1.4 helper, mocks external core/fixture/ledger seams only, and performs no file or production ledger writes. Complete executable source and observed exceptions are in the audit log.

This finding blocks the owner's zero-HIGH/zero-MEDIUM gate. Stop; no repair, adoption, merge, rebuild/restart or push was performed.

## Independently verified repaired behavior

- Original F1 exact rows: same event `event-actual` and token `actual-token-123`, HOME versus YES labels => NOT_RUN_QUOTE_COLLISION naming both IDs.
- Inverse F1: same event and HOME label, distinct explicit tokens => CLEAR, no semantic fallback. All seven supported token/outcome aliases independently exercised.
- F2 exact original sequence: remove peer bookmaker, copy candidate payload => QUOTE_IDENTITY_MISSING. Relevant incomplete peers take precedence over a complete collision in either ledger order.
- Candidate missing identity at helper => QUOTE_IDENTITY_MISSING. Each available shared payload, market or event ID independently blocks an incomplete peer. An unrelated incomplete peer is skipped with INCOMPLETE_PEERS_SKIPPED count and per-row missing fields; no history is edited.
- Explicit IDs take precedence per recorded leg. Semantic label use when IDs are absent produces LEG_IDENTITY_SEMANTIC_FALLBACK. Source inspection confirms standard and WSL reached-W1.4 terminal paths, EV outcomes, W1.5 dispositions and AI terminal outcomes preserve notes. The open finding concerns the WSL path before W1.4.

## Original full-ledger replay

The original production ledger was opened read only; all **46 MARKET_QUOTE rows** independently match `ROUND2_FULL_QUOTE_LEDGER.json` exactly. The actual entire 46-row context was used, with no exclusions from the input. Ledger raw bytes were hashed before/after the probe and matched. Public candidate DECISION dictionaries were created only in memory, checking the complete skip details, row hashes and missing fields.

| Candidate | W1.4 | Skipped incomplete peers | Price twin peer |
|---|---|---:|---|
| Charlotte 401909853 | CLEAR | 10 | 401909845 |
| Boston 401909095 | CLEAR | 10 | 401909093 |
| Utah 401909849 | CLEAR | 10 | 401909850 |
| Golden State 401909850 | CLEAR | 10 | 401909849 |

CLEAR establishes only W1.4 behavior. It does not establish EV, AI approval, placement or profitability. Existing sandbox integration tests independently rerun both isolated and full-ledger contexts through EV and AI stubs; historical decisions were not appended to production.

## Tests, scope and invariant evidence

Independent targeted command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest -q -p no:cacheprovider tests/papertrade_exec/test_quote_collision_identity.py tests/papertrade_exec/test_fixall_w1.py` — **55 passed in 0.96s, exit 0**.

Independent inline identity/full-ledger/invariant probes: **PASS, execution exit 0**. Independent WSL caller candidate-missing probe: execution exit 0, **requirement FAIL** (both missing fields reproduce KeyError and zero decisions). The full producer battery was not rerun by A7; committed producer logs were inspected and record 364 passed in 62.21s and 364 passed in 56.32s, with equal result counts. No live/provider/runtime acceptance claim is made.

Independently measured registered V3 digest: `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890`. Original ledger: 56 FORECAST raw lines, frozen56 `f12710e2d5f89b5d232d5b49358d791d7fa0b49d77152dc9c61baf8ac02cf0f4`, first48 `f6dd607c6ebb6e6173047a06208b9c6ea733e67599a43e99068cfa36dadc5240` — all PASS.

Round2 Git source diff was reviewed in full. Protected ai_producer.py, ai_gate_v2.py, laws.py, config.json and decision_pipeline.py are byte-identical to ROUND2 base. V3 registered digest is unchanged. Independent AST normalization removes only the three intended identity/collision/note helpers and the added note call in the two W1.4 blocked branches; all remaining AST is identical. W1.5/EV/AI/stake/selection logic is unchanged. Non-control source changes are confined to execute.py and one WSL note call; remaining non-control changes are the two targeted test files.

Audit log: `research/control/PAPERDESK-QUOTE-COLLISION-FIX-V1/A7_ROUND2_TEST_LOG.txt`; SHA256 `a7e14f772163ef82009aa7e3055f3adef7c3f433e854a38a73ac59fe1871cded`. It contains targeted stdout, independent probe source and outputs, four complete replay/disclosure results, protected-file and AST checks, and the WSL defect reproducer.

## Handoff and verdict

Verdict **BUG_REFUSE**. `severity_counts = {"CRITICAL":0,"HIGH":0,"MEDIUM":1,"LOW":0}`; `open_HIGH = 0`; `open_MEDIUM = 1`. No authority claim. Audit writes are limited to A7_ROUND2_REPORT.md, A7_ROUND2_TEST_LOG.txt and A7_ROUND2_HANDOFF.json. Report/log are committed first; handoff references that existing audit artifact commit and is committed separately. The structured-handoff skill was read. Orchestrator MCP is unavailable in this environment, so no store validation or integration mark is claimed; Lead must verify schema, Git scope and digests independently. Next action: STOP/BLOCKED, repair the WSL candidate validation ordering under owner/Lead control, then run fresh independent A7 before the acceptance gate.
