# PAPERDESK-QUOTE-COLLISION-FIX-V1

Owner directive 2026-10-24: repair only W1.4 source-identity collision predicate, decision notes, and tests. Base branch `orca/spt-exec-v1-integration`. Worktree `.worktrees/paperdesk-quote-collision-fix-v1/integration`; branch `orca/paperdesk-quote-collision-fix-v1-integration`.

Two distinct fixtures collide on equal nonempty payload_sha256, equal (bookmaker, market_id), or overlapping (pm_event_id, leg identity). Price equality alone is nonblocking PRICE_TWIN_OBSERVED with peer match IDs. Missing required source identity on either compared quote fails closed with QUOTE_IDENTITY_MISSING. No inference from odds. PM leg identity uses explicit token/outcome identifiers when available; semantic HOME/AWAY/DRAW leg names in existing pm_walk are recorded identities, never odds-derived. Scope covers standard and WSL W1.4 callers.

Freeze historical quote/decision evidence and current FORECAST prefix before edits. Replay four historical refusals descriptively without modifying ledger. Mandatory negatives: reused payload, market, event+leg and missing identity. Price twins reach EV and AI through existing stubs. Full PaperDesk battery alone with heavy lock free; independent A7 reruns historical and synthetic cases on committed HEAD. V3 registered digest must remain c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890; FORECAST bytes unchanged. No W1.5, EV, AI/VETO, stake, selection, or other production change.

Stop after green battery, independent A7, and owner report (commits, changed files, four-case classification, tests, invariants). No merge, adoption, production restart, or historical ledger write. Budget 0/0; no scored experiment; S1 sealed.
