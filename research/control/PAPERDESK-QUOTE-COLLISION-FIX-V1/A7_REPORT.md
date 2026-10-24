# Independent A7: BUG_REFUSE

Audited 2026-10-24, target `dbdf4c6794af50c25762b2251b6130b066bd91f8`, approved baseline `d62d22d3b732aa82b8e4763d775150bc2f9931a5`. Exact worktree `/Users/hoangminhlong/my-quantitative/.worktrees/paperdesk-quote-collision-fix-v1/integration`; branch `orca/paperdesk-quote-collision-fix-v1-integration`. Initial tree clean; root canonical registry independently confirms target, lane and BATTERY_GREEN_A7_PENDING. Owner-approved baseline adjudication applied; branch-local old registry was not treated as authority. Global heavy lock independently FREE_PROVEN. Audit only; no code repair, scoring, adoption, restart, merge or push.

## Findings

**F1 HIGH — Explicit token/outcome identity is ignored, allowing a real source collision.** `research/papertrade_exec/execute.py:2000-2012` constructs legs from dictionary keys only; it never reads `token_id_yes`, token IDs or outcome identifiers. The frozen plan requires explicit token/outcome identity when available, allowing recorded semantic names as fallback. Independently authored probe: two fixtures, different valid payload hashes and different market IDs, same `event_id="event-actual"` and same `token_id_yes="actual-token-123"`; first quote uses semantic key HOME and second YES. Actual result is `{"status":"CLEAR","price_twin_match_ids":[]}`. Expected `NOT_RUN_QUOTE_COLLISION`, identifying `event-actual` and `actual-token-123`. This is an unsafe false negative at the W1.4 boundary; existing downstream gates may still refuse independently, but W1.4 has not enforced its law. Conversely same event + HOME label but different explicit tokens returns a collision, a false positive. Existing tests cover semantic names and market reuse, so their green result does not cover this defect. Both standard and WSL callers share this helper.

**F2 MEDIUM — Missing identity on a compared quote can be mislabeled as a collision.** `execute.py:2051-2063` checks and returns duplicates before handling `absent`. Independent probe: remove bookmaker from historical peer 401909853, give that peer candidate 401909845's payload hash. Actual status `NOT_RUN_QUOTE_COLLISION`; expected owner's literal `QUOTE_IDENTITY_MISSING` because the compared row lacks required bookmaker identity. The same applies to missing peer event/market/leg fields with another shared identity. This still fails closed financially, but it violates the required missing-identity diagnostic and masks incomplete evidence. Candidate missing identity and isolated peer missing identity correctly return `QUOTE_IDENTITY_MISSING`.

## Independent reproduction

Executed in target worktree with `PYTHONPATH=. /Users/hoangminhlong/my-quantitative/.venv/bin/python -` (inline script, exit 0). Core reproducer, authored by A7 without producer fixture helpers:

```python
from types import SimpleNamespace
from research.papertrade_exec import execute as E

a = {"type":"MARKET_QUOTE", "match_id":"peer", "bookmaker":"polymarket",
     "payload_sha256":"a"*64, "event_id":"event-actual", "odds":{"HOME":2.0},
     "pm_outcomes":{"HOME":{"market_id":"market-a", "token_id_yes":"actual-token-123"}}}
b = {"type":"MARKET_QUOTE", "match_id":"candidate", "bookmaker":"polymarket",
     "payload_sha256":"b"*64, "event_id":"event-actual", "odds":{"YES":2.0},
     "pm_outcomes":{"YES":{"market_id":"market-b", "token_id_yes":"actual-token-123"}}}
print(E.quote_collision(SimpleNamespace(rows=[a]), "candidate", b))
# Actual CLEAR; expected collision on event-actual + actual-token-123.
a.pop("bookmaker")
a["payload_sha256"] = b["payload_sha256"]
print(E.quote_collision(SimpleNamespace(rows=[a]), "candidate", b))
# Actual NOT_RUN_QUOTE_COLLISION; expected QUOTE_IDENTITY_MISSING.
```

Additional independent inline probes used deepcopy of original historical ledger rows, not test identity fixtures: shared payload hash, shared market ID, shared event plus recorded semantic leg all return `NOT_RUN_QUOTE_COLLISION`; reasons name the actual duplicate hash/market/event and peer fixture. Candidate missing payload and peer missing market ID return `QUOTE_IDENTITY_MISSING`. Actual IDs observed: payload `5a923cb1a86a93d89f0ca285bd5d9468422ff2d7e37caf7152e75f51bf462770`, market `5847746`, event `1208439`.

## Historical replay and operational limitation

All rows in HISTORICAL_CASES.json independently matched original ledger rows exactly as parsed, including historical decision/hash fields. Historical ledger was read only. Isolated comparisons independently rerun:

| Candidate | Peer | W1.4 result | Observation |
|---|---|---|---|
| Charlotte 401909853 | Orlando 401909845 | CLEAR | PRICE_TWIN_OBSERVED, peer 401909845 |
| Boston 401909095 | Philadelphia 401909093 | CLEAR | PRICE_TWIN_OBSERVED, peer 401909093 |
| Utah 401909849 | Golden State 401909850 | CLEAR | PRICE_TWIN_OBSERVED, peer 401909850 |
| Golden State 401909850 | Utah 401909849 | CLEAR | PRICE_TWIN_OBSERVED, peer 401909849 |

Independent full-ledger scan measured **46 MARKET_QUOTE rows, 10 incomplete**; the missing IDs are market_id, pm_event_id and leg_identity. All four candidates return **QUOTE_IDENTITY_MISSING against the full ledger**. This reproduces the producer's disclosed limitation; isolated pair success cannot establish operational readiness. Historical rows were neither completed nor omitted from the full-ledger comparison.

## Tests and invariants

A7 reran `PYTHONPATH=. /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest -q -p no:cacheprovider tests/papertrade_exec/test_quote_collision_identity.py tests/papertrade_exec/test_fixall_w1.py`: **38 passed in 1.15s, exit 0**. These include four historical sandbox cases reaching EV then AI and retaining the nonblocking observation on AI veto, synthetic payload/market/event and missing-identity refusals before EV, and W1.5 checks. Producer's full battery remains producer evidence: 347 passed/65.47s; A7 did not rerun the full suite. No live/provider/production evidence claimed. Raw targeted output observed through tool results; no additional log file was written because audit writes are restricted to this report and handoff.

Independently measured V3 registered digest via `ai_producer.registered_prompt_sha(...,"AI_PROMPT_V3")`: `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890` (PASS). Read-only ledger raw-line hashes: 56 FORECAST rows, frozen56 digest `f12710e2d5f89b5d232d5b49358d791d7fa0b49d77152dc9c61baf8ac02cf0f4`; first48 `f6dd607c6ebb6e6173047a06208b9c6ea733e67599a43e99068cfa36dadc5240` (PASS).

Independent Git byte comparison to approved baseline: AI_PROMPT_V3.md, ai_producer.py, ai_gate_v2.py, laws.py, config.json and decision_pipeline.py identical. AST comparison: execute.py changes confined to _quote_source_identity, _quote_vwap_vector, quote_collision, note_price_twins and cmd_decide; wsl_lane.py only cmd_decide. Full source diff reviewed: cmd_decide changes are W1.4 status handling and observation plumbing; W1.5/EV/AI/stake/selection logic unchanged. Production source changes only execute.py and wsl_lane.py; remaining changes tests/control.

## Stop

**BUG_REFUSE: 0 critical, 1 high, 1 medium.** Stop at owner report. F1 requires a separate repair and fresh independent audit before any acceptance; F2 must preserve the literal missing-identity status. The known full-ledger block also prevents any operational pass claim. This audit authorizes no adoption or runtime action. Structured-handoff plugin skill was not installed/discoverable; handoff follows the existing repository zcode_orch_v3_handoff@1 example and records that validation limitation.
