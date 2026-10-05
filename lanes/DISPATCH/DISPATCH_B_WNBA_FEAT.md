# DISPATCH — Lane B_WNBA_FEAT (WINPROB-PLAYERFEAT-PREP-V1)

ROLE: data/feature lane. OBJECTIVE: WNBA frozen player-feature table from the read-only
2002–2026 corpus, strictly pre-game-known information; no outcome metric, ever.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration
BRANCH: orca/winprob-playerfeat-prep-v1-integration · BASE/DISPATCH SHA: 00323ba64ebbbc107d05fcf926c7cadf8dfa7acd
ALLOWED PATHS (write): lanes/B_WNBA_FEAT/** and ~/.my-quantitative-data/playerfeat-prep-v1/wnba/**
(OUTPUT only — feature parquet + manifests; corpus itself never written). READ-ONLY: corpus
~/.my-quantitative-data/wnba-prep-v1/roster_audit/ (50 CSVs; spot re-hash ≥6 files incl. one
player_box + one game_rosters vs download_manifest_r2.json before use); team lineage
~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv.
FORBIDDEN: git commands; writes to corpus; scored metrics; S1; purchases; keys; betting vocabulary.
REQUIRED INPUTS: plan; predecessor lanes/B_WNBA/{FEATURE_PROPOSALS.md, PIT_AUDIT.md,
COVERAGE_SCHEMA.md} (.worktrees/winprob-playerdata-prep-v1/integration/lanes/B_WNBA/);
W-H2 continuity reference .worktrees/wnba-winprob-prep-v1/integration/lanes/B_MECHANISMS/
MECHANISMS_WNBA.md (reference only, never re-derive).
SCOPE LAWS: franchise 20-key lineage joins (never raw abbreviations); coverage floors
disclosed per season (≥90% seasons 2004+, minutes-quality floor 2013+ for minutes-weighted
variants, 2002 minutes 100% null → exclude); opening-roster v1 NOT_RUN_PIT; v2 = game-1
membership usable only from that team's game 2 onward; `active`/`reason` fields unusable;
era 1997–2001 out of corpus scope; DNP flag 2012+ only (pre-2012 absence = null-minutes proxy).
DELIVERABLES (lanes/B_WNBA_FEAT/): build_features.py (deterministic), FEATURE_SPEC.md,
COVERAGE_AUDIT.md, FEATURE_TABLE_MANIFEST.md (+json), PIT_AUDIT.md, VERDICT_TABLE.md;
feature parquet under ~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/.
GROUPS (from predecessor proposals, frozen spec written by this lane): A roster continuity
(v2 as-of law), B minutes-mass/load (k∈{3,5} both computed, selection deferred to successor),
C top-player form + absence proxy.
TEST COMMANDS: selftest asserts in build_features.py (leak guards, lineage coverage).
STOP CONDITIONS: corpus hash mismatch (stop, BLOCKED_DATA); >30 min compute; leakage suspicion.
COMMIT-PUSH: none. HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_B_WNBA_FEAT.json
(task_id winprob-playerfeat-prep-v1-B-WNBA-FEAT, dispatch_sha=00323ba…, commit_sha=null).
