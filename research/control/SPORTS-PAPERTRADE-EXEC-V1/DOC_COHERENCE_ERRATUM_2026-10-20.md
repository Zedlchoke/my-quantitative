# DOCUMENTATION COHERENCE ERRATUM — 2026-10-20

## Precedence (highest → lowest)
1. Owner live instructions (most recent chat)
2. plans/CYCLE_REGISTRY.json phase (CAS)
3. AMENDMENT_MACOS_APP_UI_V1 + rounds 1-11 law files in this directory
4. plans/PLAN_sports_papertrade_exec_v1.md (original plan)
5. CAPITAL-V3 config commit

## Corrections
| Stale ref | Current law | Where |
|---|---|---|
| stake $5 (STAKE_CENTS=500) | 1% equity v3-1pct (capital_law=3) | config.json capital_law |
| cap $100 (OPEN_EXPOSURE_CAP=10000) | cap $500 (OPEN_EXPOSURE_CAP_V3=50000) + availability | config.json capital_law |
| B1 soccer | B1R_SOCCER (live model; B1-only → NOT_RUN) | pins.json soccer lane |
| GO 'RUN ALL' (consumed 2026-10-07) | consumed; current = cutover phrase REGISTERED_NOT_CONSUMED | registry |
| WSL settle: no source | WSL RESULTS SOURCE V1 (polymarket_uma) | WSL_RESULTS_SOURCE_V1.md |
| AI: advisory only | AI_GATE_MANDATORY_V1 built (advisory until authority GO) | AI_ACTIONS_PACKET |
| NBA: blocked | worktree nba26 restored at 82542aa8, pin-verified | round-9 commit |
