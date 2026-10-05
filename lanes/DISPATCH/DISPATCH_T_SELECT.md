# DISPATCH — Lane T_SELECT (WNBA-PLAYERFEAT-SCORED-V1) — IMPLEMENTATION + TRAIN-INTERNAL SELECTION

ROLE: implementation/selection lane. TRAIN-INTERNAL ONLY (real data hard-capped: B1-WNBA
grid folds ≤2018; feature folds ≤2018 with era floors 2013+/2014+). OOS [2020..2026] NEVER
touched (evaluate-oos mode refuses real data without GO token).
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1/integration
BRANCH: orca/wnba-playerfeat-scored-v1-integration · DISPATCH SHA: 8130de5af6c05dcf8e67efdfd2f5bc6f575ca92d
ALLOWED PATHS (write): lanes/T_SELECT/** + lanes/DISPATCH/handoff_T_SELECT.json + outputs
~/.my-quantitative-data/wnba-playerfeat-scored-v1/selection/. READ-ONLY: everything else.
FORBIDDEN: git; OOS computation; betting vocabulary; modifying corpus/frozen table.

## Inputs (read-only)
- Feature table: ~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/ (11,976 rows;
  spec/manifest in .worktrees/winprob-playerfeat-prep-v1/integration/lanes/B_WNBA_FEAT/).
- Universe + corpus: ESPN-side universe 5,988 games 2002–2026 (universe law in
  lanes/B_WNBA_FEAT/COVERAGE_AUDIT.md); stats-side 1997–2001 warm-up rows if present on
  disk under ~/.my-quantitative-data/wnba-prep-v1/ (locate; else warm-up 2002–2004 disclosed);
  franchise 20-key lineage ~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv.
- Laws: plans/PLAN_wnba_playerfeat_scored_v1.md; predecessor packet .worktrees/
  wnba-winprob-prep-v1/integration/research/control/WNBA-WINPROB-PREP-V1/
  SUCCESSOR_PACKET_SCORED.md (§1 windows, §2 baseline grid, §4 W-H2 PIT law, §5 data freeze);
  W-H2 machinery reference lanes/B_MECHANISMS/MECHANISMS_WNBA.md (reference only).

## Arms (designed-null ≡ parent bit-for-bit)
- B0 constant (TRAIN-window home-win rate frozen);
- B1-WNBA fresh own-Elo: grid K∈{8,16,32}×HCA∈{0,50,100}×γ∈{0.65,0.75,0.85} (27 fits,
  counted), warm-up 1997–2001 (or 2002–2004 fallback, disclosed), 4 expanding-origin
  2-season validation blocks over TRAIN tail (per packet); degenerate K→0 kill; selected
  config frozen;
- WF-A continuity carryover: R_start = 1500 + γ_sel·c_i·(R_end−1500) with c from feature
  table (2014+ rows; expansion/missing → c=1 i.e. parent; null c≡1 ≡ B1-WNBA);
- WF-B load/concentration: argument += φ_B·(x_H−x_A) standardized (2013+ era floor);
- WF-C form/absence: argument += φ_C·(x_H−x_A) standardized (DNP 2012+);
- GRIDS (pre-registered): φ_B, φ_C ∈ {−50,−25,0,25,50}; WF-A has NO free scalar (c from
  table; γ frozen from B1-WNBA selection);
- Diagnostics (outside budget): time-shuffled twins per arm (seed 20261005);
  warm-up-vs-cold-start rerun (diagnostic only);
- Feature-fold structure: 5 expanding-origin single-season folds 2014..2018 (era-floor
  adaptation, disclosed in plan); criterion pooled inner LL; G-ENTRY as NBA plan (vs frozen
  B1-WNBA; slope band; twin clean);
- Uncertainty: paired ΔLL, tip-date-cluster bootstrap 10,000 resamples seed 20261005;
  neutral-site rows HCA=0 default with separate report.

## Deliverables
lanes/T_SELECT/{harness.py,arms.py,--selftest fixtures (Elo update, HCA argument, γ
reversion, 20-key lineage canary — raw-abbreviation join must fail, continuity arithmetic,
designed-null ≡ parent byte-identity on ≥3 synthetic streams, era-floor/neutral rules,
doctored 2019-row ABORT), SELECTION_LEDGER.jsonl, SELECTION_REPORT.md (B1-WNBA frozen
config + φ or releases; moments pinned; fit counts incl. the 27 grid fits), VERDICT_TABLE.md}.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_T_SELECT.json (task_id
wnba-playerfeat-scored-v1-T-SELECT, dispatch_sha=actual_start_sha=8130de5a…, commit_sha=null).
STOP CONDITIONS: designed-null mismatch; corpus/table sha mismatch; lock not FREE_PROVEN
(inspect from root; retry; else NOT_RUN_RESOURCE_CONFLICT).
