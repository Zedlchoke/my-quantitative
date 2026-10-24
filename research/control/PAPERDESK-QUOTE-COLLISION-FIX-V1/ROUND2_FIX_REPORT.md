# W1.4 round 2 — producer evidence

Owner directive 2026-10-24 supersedes the round1 all-incomplete-peers block. Round2 baseline `f7195a2f79b9d98af4047ec3f66e422e79c207b4`; code commit `300297d6584284205f9ef0106f81cc62cd42b0d1`. New independent A7 is required; no adoption before its zero-HIGH/zero-MEDIUM PASS gate.

F1: explicit token_id_yes/token_id/tokenId/tokenID and outcome_id/outcomeId/outcomeID identifiers drive event+leg matching. Labels are used only if explicit IDs absent; comparison and DECISION disclose LEG_IDENTITY_SEMANTIC_FALLBACK. The exact A7 F1/F2 reproducer is now a regression test; both F1 directions covered.

F2: validate candidate first and every peer before classifying. Relevant incomplete peers outrank collision diagnostics regardless of row order and always return QUOTE_IDENTITY_MISSING.

Owner two-tier legacy ruling: no historical row is edited or supplemented. Incomplete peer with any available matching strong payload, event or market ID blocks QUOTE_IDENTITY_MISSING. Other incomplete peers are excluded with INCOMPLETE_PEERS_SKIPPED count and per-row match/hash/missing fields in DECISION.quote_observations. Candidate incomplete never uses the exclusion rule. Notes persist across standard/WSL, AI outcomes and W1.5 dispositions, including blocked decisions.

## Full-ledger replay

Frozen all **46 MARKET_QUOTE** rows match current ledger exactly. Full comparison uses all ledger rows, not isolated pairs. Outputs and decision disclosures: ROUND2_FULL_LEDGER_REPLAY.json.

| Candidate | W1.4 | INCOMPLETE_PEERS_SKIPPED | Price twin peer |
|---|---|---:|---|
| Charlotte 401909853 | CLEAR | 10 | 401909845 |
| Boston 401909095 | CLEAR | 10 | 401909093 |
| Utah 401909849 | CLEAR | 10 | 401909850 |
| Golden State 401909850 | CLEAR | 10 | 401909849 |

CLEAR means only this guard passed; it does not infer EV, AI/VETO or placement. Sandbox integration tests replay both pair and full-ledger contexts through EV/AI stubs and persist disclosures. No historical DECISION was rerun into production or changed.

## Battery and scope

Two sequential full PaperDesk runs: **364 passed / 0 failed / 0 skipped**, first **62.21s**, second **56.32s**. Equal result counts, exit 0; verbatim ROUND2_BATTERY_1.txt and ROUND2_BATTERY_2.txt. Command: `PYTHONPATH=. /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest -q tests/papertrade_exec`. Heavy lock FREE_PROVEN before both sequential runs.

V3 `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890`; frozen 56 FORECAST digest `f12710e2d5f89b5d232d5b49358d791d7fa0b49d77152dc9c61baf8ac02cf0f4` and first48 `f6dd607c6ebb6e6173047a06208b9c6ea733e67599a43e99068cfa36dadc5240` unchanged. Protected AI/V3/laws/config/decision pipeline files byte-identical to round2 base. AST outside source-identity helper, collision predicate, note metadata helper and the two cmd_decide note call sites unchanged. W1.5/EV/AI/stake/selection logic unchanged. Source files execute.py and one blocked-note call in wsl_lane.py; test_fixall_w1.py and test_quote_collision_identity.py updated; other changes control evidence only.

Independent A7 R2 pending on committed HEAD. Scope strictly round2 diff from f7195a2f; independent new probes for both F1 directions, F2 and all four full-ledger cases required. Only PASS/PASS_WITH_FINDINGS with zero open HIGH/MEDIUM permits main merge, rebuild/restart production, adoption dossier commit and push under owner instruction. Otherwise BLOCKED/STOP.

## Fresh A7 result and owner stop

A7_ROUND2_REPORT.md verdict **BUG_REFUSE: 0 HIGH, 1 MEDIUM open**. Audited target 8490e6101dd47cd353d1c25b6043f6d01c51ff88, report/log commit 899f09954599cd51171d179d39f9f204c2b25b34, handoff commit 16d920a3a2532806f41ae875d3f3bec219c36a8c. Targeted 55/55 and independently authored F1/F2 and four full-ledger cases passed; original F1 HIGH and F2 MEDIUM fixed.

New MEDIUM R2-F1: WSL cmd_decide indexes candidate bookmaker/payload_sha256 before calling W1.4; missing either raises KeyError with zero DECISION rather than QUOTE_IDENTITY_MISSING. Independent actual-caller reproducer is in A7_ROUND2_TEST_LOG.txt. Though pre-existing ordering, it violates the explicit round2 candidate-missing acceptance law. No repair was made after A7.

Lead independently validated handoff required fields, dispatch/start binding, existing audit commit/path scope and output/test-log digests (ROUND2_HANDOFF_VALIDATION.json). Orchestrator store tool unavailable; no store-validation claim. Gate FAIL due open_MEDIUM=1; registry BLOCKED, STOP pending owner instruction. No merge, rebuild, production restart, adoption, or push. Production runner PID15385 and appPID44911 remain the pre-existing instances; main production code has no delta from approved fixall baseline. Both are alive at the post-audit process check.
