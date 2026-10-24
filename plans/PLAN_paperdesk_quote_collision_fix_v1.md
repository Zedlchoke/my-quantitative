# PAPERDESK-QUOTE-COLLISION-FIX-V1

Owner directive 2026-10-24: repair only W1.4 source-identity collision predicate, decision notes, and tests. Base branch `orca/spt-exec-v1-integration`. Worktree `.worktrees/paperdesk-quote-collision-fix-v1/integration`; branch `orca/paperdesk-quote-collision-fix-v1-integration`.

Two distinct fixtures collide on equal nonempty payload_sha256, equal (bookmaker, market_id), or overlapping (pm_event_id, leg identity). Price equality alone is nonblocking PRICE_TWIN_OBSERVED with peer match IDs. Missing required source identity on either compared quote fails closed with QUOTE_IDENTITY_MISSING. No inference from odds. PM leg identity uses explicit token/outcome identifiers when available; semantic HOME/AWAY/DRAW leg names in existing pm_walk are recorded identities, never odds-derived. Scope covers standard and WSL W1.4 callers.

Freeze historical quote/decision evidence and current FORECAST prefix before edits. Replay four historical refusals descriptively without modifying ledger. Mandatory negatives: reused payload, market, event+leg and missing identity. Price twins reach EV and AI through existing stubs. Full PaperDesk battery alone with heavy lock free; independent A7 reruns historical and synthetic cases on committed HEAD. V3 registered digest must remain c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890; FORECAST bytes unchanged. No W1.5, EV, AI/VETO, stake, selection, or other production change.

Stop after green battery, independent A7, and owner report (commits, changed files, four-case classification, tests, invariants). No merge, adoption, production restart, or historical ledger write. Budget 0/0; no scored experiment; S1 sealed.

## Owner base adjudication

Owner selected fixall d62d22d3b732aa82b8e4763d775150bc2f9931a5 after requested spt base proved to lack W1.4/W1.5/V3. Original bootstrap chain preserved on orca/paperdesk-quote-collision-fix-v1-bootstrap-evidence; exact requested branch recreated from approved fixall and evidence cherry-picked. No merge or existing commit rewrite. All code scope checks use approved fixall as baseline.

## Owner round 2 directive (2026-10-24)

Resume same branch from f7195a2f. Explicit token/outcome IDs are principal leg identity; semantic label fallback only when explicit IDs absent and logged. Validate both sides before collision classification. Candidate incomplete always QUOTE_IDENTITY_MISSING. Incomplete historical peer with any shared available strong payload/event/market ID => QUOTE_IDENTITY_MISSING; otherwise skip with public INCOMPLETE_PEERS_SKIPPED count and detail in candidate decision. Never modify history. Freeze/replay all 46 MARKET_QUOTE rows for four historical candidates. Full battery twice sequentially with equal pass/fail counts, invariants unchanged. Fresh independent A7 on round2 diff, reproduce both F1 directions, F2, full-ledger four-case replay. Only PASS/PASS_WITH_FINDINGS with zero open HIGH/MEDIUM permits merge main without force, production rebuild/restart, adoption evidence commit and push. Otherwise BLOCKED/STOP.

## Owner round3 micro-fix (2026-10-24)

Only resolve A7 R2-F1: run existing W1.4 before constructing WSL downstream quote or stake/recheck, persist zero-stake QUOTE_IDENTITY_MISSING for candidate missing any required helper identity. Exact two WSL caller probes become regressions. Scan standard caller for equivalent ordering; change only if needed. F1/F2/two-tier helper code byte-unchanged. Full battery twice equal results, V3/FORECAST and all other laws unchanged. Fresh independent A7 only round3 diff, independently rerun WSL probes, all F1/F2/two-tier and original full-ledger four candidates. Zero open HIGH/MEDIUM PASS gate retains owner authority for merge main (no force), rebuild/restart, adoption dossier rounds1–3, commit+push; otherwise BLOCKED/STOP.
