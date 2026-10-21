# A7 ROUND-17 RE-AUDIT NOTES — SPORTS-PAPERTRADE-EXEC-V1

Re-auditor: independent A7 re-audit (round-17 remediation verification).
Date: 2026-10-21. Audit only — nothing repaired, nothing pushed, no
processes killed, live ledger touched read-only.

## Anchor

- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`
- Branch: `orca/spt-exec-v1-integration`
- HEAD: `c4422f8de18b945c8f9073e7bae09e90168bffb0` (`rev-parse c4422f8d` matches exactly)
- Lineage: `git log --oneline ef45e249..HEAD` → exactly one commit:
  `c4422f8d PaperDesk round-17d (A7_ROUND17 remediation) …`. No HEAD_DRIFT.
- Prior audit: `A7_VERDICT.json` in this directory — FAIL at `ef45e2495…`
  driven by F-1 HIGH (soccer seed pin with fabricated 52-char digest tail),
  plus F-2/F-3/F-4a LOW.

Interpreter note: the dispatch named `~/.venv/bin/python`; the actual venv
is `/Users/hoangminhlong/my-quantitative/.venv/bin/python` (workspace root,
per AGENTS.md). All commands ran from the worktree cwd with that interpreter.

## R1 — F-1 closure (soccer seed pin) — PASS

- `shasum -a 256` of
  `/Users/hoangminhlong/.worktrees/soccer-intl-winprob-prospective-prep-v1/integration/research/papertrade_soccer/PROVIDER_NAME_CROSSWALK_SEED.csv`
  = `f5b85fb9ea2baa083c4c8cdc34a2462d6f5fa4bc0c4fbe2f17c183b734d03441`.
- pins.json `packages.soccer.files["PROVIDER_NAME_CROSSWALK_SEED.csv"].sha256`
  = `f5b85fb9ea2baa083c4c8cdc34a2462d6f5fa4bc0c4fbe2f17c183b734d03441`.
- Equality method: full-string comparison of two 64-char hex strings
  (`pin == actual` → True). NOT a prefix match (the F-1 failure mode was a
  12-hex true prefix + fabricated 52-char tail; that value is gone).
- `verify-pins` exit 0, `drift: []`,
  `soccer/PROVIDER_NAME_CROSSWALK_SEED.csv: status OK`.
- Extension pin still verifies: data `soccer_crosswalk_extension_csv`
  `57354475…366a3` == actual bytes, status OK; raw-byte check
  `ext.startswith(seed) == True` (seed prefix intact, appended rows remain).
- Erratum present in the pin note (pins.json): "ERRATUM 2026-10-21
  (A7_ROUND17 F-1 HIGH): … the re-seal commit cef8412c recorded a seed
  digest whose 52-char tail was not a measurement … re-measured shasum -a
  256 and re-pinned the true full digest here — digest also matches the
  prep lane's CONTROLLER_CROSSWALK_20261009.md".

## R2 — F-2 closure (fee_total) — PASS

- `research/papertrade_exec/pm_quote_source.py` L65: `"fee_total":
  legs_result[leg].get("fee_cents")` (L66 also carries `fee_cents` itself).
- `pm_moneyline.walk_ask` (pm_moneyline.py L245-250) genuinely returns
  `fee_cents: round(fee*100)` computed from `0.05·p·(1−p)·take` (L237) —
  the sourced value is a real measurement, never None-by-construction.
- Audit harness measurement (mocked `probe_event_moneyline` with
  fee_cents 30/42): emitted `fee_total` = 30/42, `NO_NONE_FEE=True`.
- The battery's seam tests (test_pm_cutover_wiring.py, test_exec_battery.py)
  inject `fee_total` at the pm_probe seam level, so they don't regress this
  mapping either way; the adapter mapping is covered by the measurement
  above.

## R3 — F-3 closure (env seam real-mode block) — PASS (code law); test part NOT_RUN

- `execute.py` L1733-1739: `load_ai_opinion` raises
  `BlockError("BLOCKED_TEST_HOOK_IN_REAL_MODE", …)` when the attr seam
  **or** `PAPERTRADE_AI_OPINION_JSON` is present and
  `getattr(args, "sandbox", False)` is falsy — exactly the symmetry with
  `_pm_probe_seam` that F-3 asked for.
- Live measurement (audit harness):
  - env-only + real mode → raised `BLOCKED_TEST_HOOK_IN_REAL_MODE`;
  - attr seam + real mode → same raise;
  - env + sandbox=True → seam loads without raise (returns per mapping).
- Battery coverage: `test_pm_probe_seam_refused_in_real_mode`
  (test_pm_cutover_wiring.py L186-193) proves the block pattern for
  pm_probe's attr seam. **No** battery test drives `load_ai_opinion` with
  the env var in real mode (both `PAPERTRADE_AI_OPINION_JSON` uses in
  test_exec_battery are sandbox-mode). Recorded `NOT_RUN` for the test
  sub-part per the dispatch instruction; the code law itself is PASS by
  inspection + measurement. → finding R-N1 (LOW).

## R4 — F-4a closure (3-YES joiner detail) — PASS

- `_join_3yes_in_event` (pm_moneyline.py L172-208) now returns
  `(None, best partial reason)` shaped as
  `"3-YES join incomplete on event {id}: legs={sorted(legs)} (need HOME/DRAW/AWAY)"`
  — event id + legs found, per event, best across variants.
- `discover_and_join_3yes` (L164-169) threads `last_reason` through the
  search variants and returns it (generic fallback only when no variant
  produced a reason).
- `execute.py` L1277-1281 interpolates it into the fail-closed detail:
  `NOT_RUN_PM_QUOTE / "PM 3-YES join failed for {match_id}: {legs_m}"`.
- `test_discover_join_3yes_laws` asserts the missing-draw case fails closed
  with `"3-YES"` in the why-text.

## R5 — Regression battery — PASS

- Command: `/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
  tests/papertrade_exec/ -q` (cwd = worktree).
- Result: `147 passed in 47.76s`, exit code **0**. Matches expectation.

## R6 — Pin-note honesty sweep — PASS (zero CRITICAL)

Method: two independent layers.

1. Coverage check: every 64-hex string in pins.json
   (regex `[0-9a-f]{64}`) must be a pin value, and every pin value must
   appear. Result: 21 hex strings == 21 pin values, both difference sets
   empty. (Notes in pins.json carry only 8-12 char abbreviations — no
   hidden full digests.)
2. Byte verification: recompute sha256 with audit-owned hashlib code
   (not verify-pins) for all 20 direct-sha pins:

   | pin | result |
   |---|---|
   | paper_core `__init__.py` / ledger / risk / dashboard / odds_client / go_gate / sandbox (7) | OK |
   | wnba26 wnba_2026_remainder_ledger.py / predict.py (2) | OK |
   | nba_harness arms.py / game_universe.py / real_loader.py (3) | OK |
   | nba26 loader.py / predict.py (2) | OK |
   | soccer replay.py / PROVIDER_NAME_CROSSWALK_SEED.csv (2) | OK |
   | b1r_switch b1r_adapter.py (1) | OK |
   | data wnba_schedule_2026_csv / soccer_corpus_results_csv / soccer_crosswalk_extension_csv (3) | OK |

   → 20/20 direct-sha pins match actual bytes, 0 mismatches. The F-1 error
   class (unmeasured digest written as a pin) does not recur anywhere.
3. Composite: `nba_espn_schedule_2026_27` verified per its documented
   manifest-chain law (not recomputed standalone): `verify-pins` reports
   status OK. Measured composite `e0beb91a9c4e83c452b1917f9bd428a17972fa4
   f863295440220c7909f925e76` differs from the frozen anchor
   `3d527b3c…bc25e6`; the pins.json source note documents exactly this
   lawful state (post-GO refresh extension via the self-hashed
   REFRESH_MANIFEST.jsonl chain anchored at the frozen pin; last
   new_composite must equal the recomputed composite — the tool accepted
   it).

## R7 — Live ledger untouched — PASS

- Path: `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl`
- Rows: **82** (GENESIS 1 / FORECAST 27 / MARKET_QUOTE 17 / DECISION 27 /
  SETTLEMENT 10 — identical to the prior audit's census).
- Pinned-core `PaperLedger(path).load().verify_chain()` →
  `chain_ok=True, errors=[]` (ledger.py imported from the paper_core
  worktree, bytes pinned `5da11965…be5d5`).
- mtime before verification `Oct 20 23:51:50 2026`, after `Oct 20
  23:51:50 2026`, size 79619 both — unchanged, predates this session
  (2026-10-21). No write occurred.

## Findings

- **R-N1 (LOW)** — no dedicated battery test for the `load_ai_opinion`
  env-seam real-mode block (the F-3 remediation is correct and measured,
  but untested by the battery). Suggested: one small unit test
  (env + `spec=[]` args + `pytest.raises(BlockError)`). Test part recorded
  NOT_RUN in R3.
- **R-N2 (INFO)** — `pm_moneyline.walk_ask` docstring (L214) still names
  the old return keys `spend`/`fee` (actual: `spend_cents`/`fee_cents`).
  Cosmetic; no behavior impact.
- **R-N3 (INFO)** — sibling-lane measured heads differ from the free-text
  `dispatch_head` strings in pins.json (paper_core 4e7e6140, nba26
  82542aa8, soccer a8057a95, wnba26 f1c0e1b3). pins.json declares heads
  ADVISORY ONLY; the binding identity is file bytes and every byte pin
  verifies. No action.

## Verdict

**PASS_WITH_FINDINGS** — F-1 HIGH closed (true full digest pinned + erratum
+ verify-pins OK), F-2/F-3/F-4a LOW closed, battery 147/147 exit 0, live
ledger untouched, and the pin-honesty sweep found no digest mismatch
anywhere. Residual items are LOW/INFO only and do not block remediation
closure. Production gates remain OFF (unchanged scope of this audit).
