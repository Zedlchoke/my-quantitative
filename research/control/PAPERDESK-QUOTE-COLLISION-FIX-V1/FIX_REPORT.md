# PAPERDESK-QUOTE-COLLISION-FIX-V1

Code commit: `8d790592724d51a882ad9e9a583094637b3d5af2`. Approved base: `d62d22d3b732aa82b8e4763d775150bc2f9931a5`. No merge, adoption, push, production restart, or historical ledger write.

## W1.4 behavior

Source reuse across distinct fixtures (including across leagues) blocks on equal real payload SHA256, intersecting (normalized bookmaker, market ID), or intersecting (PM event ID, explicit leg identity). DECISION reason names the actual shared identifier; status remains NOT_RUN_QUOTE_COLLISION. Two-way PM rows expose market/event IDs and HOME/AWAY leg names in pm_walk; WSL uses explicit per-leg pm_outcomes market IDs. PM bookmaker aliases normalize to one family. Missing required identity on either quote fails closed with status/reason QUOTE_IDENTITY_MISSING. Same-fixture snapshots are exempt. No source ID is inferred from price.

Equal full odds or full VWAP vectors with complete distinct identities produce nonblocking DECISION.quote_observations: PRICE_TWIN_OBSERVED plus peer match_ids. Notes survive normal decisions, W1.5 disposition rows and terminal AI outcomes. Economic and AI predicates are unchanged.

## Four historical refusals

| Refused fixture | Price peer | New classification |
|---|---|---|
| Charlotte–Miami 401909853 | Orlando–Minnesota 401909845 | false price collision |
| Boston–Knicks 401909095 | 401909093 | false price collision |
| Utah–New Orleans 401909849 | Golden State–Memphis 401909850 | false price collision |
| Golden State–Memphis 401909850 | Utah–New Orleans 401909849 | false price collision |

Exact identities and hashes: HISTORICAL_CASES.json and HISTORICAL_CLASSIFICATION.md. Each isolated historical pair passed W1.4, reached EV and AI stubs, and retained the price-twin note on a VETO DECISION. These regressions do not imply an economic pass or revise historical refusals.

## Battery and invariants

Final full PaperDesk battery: **347 passed, 0 failed, 0 skipped in 65.47s**. Command: `PYTHONPATH=. /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest -q tests/papertrade_exec`; output BATTERY_FINAL.txt. Initial full run: 335 passed / 6 failed in 66.10s from incomplete/obsolete synthetic identity fixtures and the old price-collision assumption. Updated test fixtures; gates were not bypassed. Affected subset then passed 102 tests; six additional W1.4 cases were added before the final full run. Reused payload/market/event+leg blocks, missing candidate/peer fields, cross-league reuse, WSL per-leg market overlap, price/VWAP twins, aliases and downstream EV/AI calls are covered.

V3 registered SHA256 `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890`. Frozen 56-row FORECAST prefix unchanged; first 48 SHA256 `f6dd607c6ebb6e6173047a06208b9c6ea733e67599a43e99068cfa36dadc5240`. INVARIANTS_AFTER.json confirms protected files byte-identical and AST diff outside allowed W1.4 helpers plus note plumbing in the two cmd_decide functions empty. W1.5 disposition/crosscheck and AI gate function bodies remain byte-identical; EV/stake/selection source is unchanged.

Production files changed: execute.py, wsl_lane.py. Test files changed: test_fixall_w1.py, test_exec_battery.py, test_b1r_fail_closed.py; added quote_identity_fixtures.py and test_quote_collision_identity.py. The synthetic battery supplies explicit source identities in sandbox fixtures; production quote emitters are unchanged.

## Material limitation before adoption

Current ledger identity audit: **10 of 46 quotes lack required source identity**; see SOURCE_IDENTITY_COMPLETENESS.json. Under the owner's fail-closed rule a full-ledger candidate comparison remains blocked by those legacy rows. The four cited pairs themselves have complete distinct identities, but pair regressions do not claim a full-ledger production pass. No historical identity was guessed, completed, or discarded. Owner must see this limitation before any separate adoption decision.

## Independent A7 and owner stop

A7 audited target `dbdf4c6794af50c25762b2251b6130b066bd91f8`; audit artifacts committed at `dc0f49c8e28f327f3d19036e173c89d96c0a5695`. Verdict **BUG_REFUSE: 1 HIGH, 1 MEDIUM**. A7 independently reran 38 targeted tests (all passed, 1.15s), the four historical pairs, and its own probes; full battery green does not cover the defects below.

- HIGH F1: explicit token/outcome IDs are ignored. Same event and same token under different semantic labels HOME versus YES incorrectly returns CLEAR; different tokens under the same label can incorrectly collide. W1.4 therefore does not yet enforce the real source identity law.
- MEDIUM F2: a peer with missing identity plus another shared identifier returns collision before the missing-identity diagnostic. It remains financially fail closed, but the reason/status must be QUOTE_IDENTITY_MISSING.

A7 independently confirmed all four pair classifications and the full-ledger 10/46 missing-identity block. V3, FORECAST and scope invariants passed independently. Exact probes and findings are in A7_REPORT.md; structured handoff in A7_HANDOFF.json. No producer repair was made after the independent audit. Cycle BLOCKED; STOP at owner report, with no merge, adoption, production restart or push. Further repair and fresh A7 require the owner's next instruction.
