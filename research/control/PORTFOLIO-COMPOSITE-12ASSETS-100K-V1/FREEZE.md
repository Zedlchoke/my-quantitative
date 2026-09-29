# FREEZE — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 prelaunch freeze (2026-09-29)

Ceremony per plan §5 and campaign §8: verification battery green →
sanitized exact-arm dry-run (zero outcome leak) → this freeze document →
independent A7 prelaunch (fresh context) → owner GO #2 at the scored gate.
**The scored GO remains REGISTERED_NOT_CONSUMED.**

## CODE_FREEZE

- Worktree `.worktrees/portfolio-composite-12assets-100k-v1/integration`,
  branch `orca/portfolio-composite-12assets-100k-v1-integration`.
- Chain: `65381730` (evidence) → `1b6e19dc` (impl lane: engine + 12 legs +
  82 tests + smoke) → `bfa51c2f` (verification lane: truncation replay,
  PIT joins, arm distinctness, counter-tests; 3 lookahead/integrity bugs
  caught and minimally fixed, all disclosed in
  `handoffs/VERIFY_battery.json`) → **FREEZE commit = the commit that
  carries this document** (sha recorded in the registry row immediately
  after; the binding freeze sha is that commit's full 40-hex).
- Test suite at freeze: **150 pc12a tests green** (82 impl + 68
  verification); full worktree suite 2057 passed / 7 failed / 1 skipped —
  the 7 are the pre-existing `test_family_failures.py` registry-parsing
  failures at this base, untouched by this cycle (disclosed, not ours).
- Runtime pins: root checkout `.venv` (python 3.12.14), **tzdata 2026.3**
  (the open engine-freeze item from the impl lane — pinned here).

## DATA_FREEZE

- M1 panels (read-only, in prior cycles' worktrees; per-file sha256
  manifests in `poolB/data_audit/panel_hashes_*.jsonl`):
  aggregate digests EURUSD `964abbac52132489…` · GBPUSD `9ffb0e4ba747de0c…`
  · USDJPY `57b77f770b29690d…` (Lane D audit, 12,552 files, coverage
  2021-01-01→2026-09-23). H1 panels (USDCAD/AUDUSD ANC parquets) are not
  consumed by the frozen 12-leg slate v0 (disclosed; enter at Stage-A
  expansion with their own digests).
- Fold calendar: 286 Fridays 2021-01-08→2026-06-26 (52w warmup + 8×26w
  test folds + 1w train-side embargo); sealed tail EXCLUDED, S1
  SEALED_UNTOUCHED.

## COST_FREEZE

- cost_kernel.py at CODE_FREEZE: C1/C2-Friday/C3 per COST_AUTHORITY_TABLE
  (reproduced exactly by the Lane D audit, 286/286 × 3 pairs); C2 Mon–Thu
  per the audit's CORRECTED (21:00,22:00] cells (EURUSD 1.2/3.7 · GBPUSD
  2.8/7.8 · USDJPY 2.1/7.4 pips — the wrong-hour cells are erratumed,
  erratum I-4); DECLARED pessimistic U2 0.35 bps/side, U3 0.2/1.0 pip,
  U4/U5 1.0 pip/night against (Wed ×3); stress tiers ×1.0/×1.5/×2.0;
  spread-once law + worst-fill grading per FILL_ACCOUNTING_SPEC.
- Every pair remains PROVISIONAL_PENDING_COST_AUTHORITY; every future
  Stage-C survivor carries NET_DEFAULT_COST. Swap-receiving legs stay
  BLOCKED_COST (owner statement pending).

## SELECTION_FREEZE (slate v0 — the exact arms of the frozen dry-run)

- 12 legs: the 9 VOLPROF class candidates (VC1/VC2/VC3 × EURUSD/GBPUSD/
  USDJPY per CLASS_SPEC_VOLPROF_M1 r2) + 3 exemplar T1 legs (USDJPY-S001
  Donchian trend · GBPUSD-S027 weekday gate · EURUSD-S009 MACD-exit),
  configs at `research/pc12a/legs_config/` (pairwise-distinct
  arm_config_digests, labels + cluster_ids verified by
  test_pc12a_arm_distinctness). This is the IMPLEMENTATION slate v0 —
  NOT the discovery slate: Stage-A mechanization screening of the 150
  triage-runnable candidates happens under the discovery ledger after the
  scored GO opens the campaign, per plan §4.
- Policy skeleton L1–L7 with FEATURES_BLACKLIST (GROUPING_PROPOSAL §3.6);
  L5 cluster caps and L6 guard constants are Stage-B freeze items,
  explicitly NOT frozen here.

## Sanitized exact-arm dry-run (zero outcome leak — RGC-INC-1 law)

- Smoke (8w, post-fix): 863 journal rows, leak-scan clean, two runs
  byte-identical (determinism proven post-fix).
- **Full window (286 Fridays, 12 legs, tier ×1.0): 35,504 journal rows,
  3m29s, leak-scan clean** (engine scanner + A1 independent grep both
  clean); journal sha256 `a6bde2cedc9de620…`; report carries ONLY
  decision/fill/blocked counts, cost-bill totals, digests. Artifacts:
  `dry_run/full_window/` (committed with this freeze).
- Honest feasibility signals from the dry-run (counts, not outcomes):
  recorded per-leg in the report; VC1's zero-fire window extends
  whole-calendar — a Stage-A floors question, not a tuning invitation.

## Boundaries standing at freeze

S1 SEALED_UNTOUCHED · heavy lock FREE_PROVEN (dry-runs stayed under 10
min; no lock consumed) · 0 scored cells · budget 0/48 identities ·
no push/merge · owner dirty tree in the root checkout untouched ·
one Lead session (P-17). Next and ONLY remaining gates: independent A7
prelaunch (fresh context), then owner GO #2
`GO PORTFOLIO COMPOSITE 12ASSETS 100K V1 SCORED EXECUTION`.
