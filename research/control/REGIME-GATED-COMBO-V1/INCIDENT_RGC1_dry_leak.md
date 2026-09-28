# RGC-INC-1 — dry-mode PnL leak (disclosed, purged from tree, kept in history)

- what: run_combo() wrote the FULL scored payload (combos total_bps, per-fold,
  verdict) to rgc100_dry.json in dry mode; only rgc100_dry_summary.json was clean.
  Committed at 32f77333 — the leak is permanently in git history as evidence.
- caught by: A7 prelaunch (REFUSED, H1) before any GO. Verbatim finding stands.
- exposure: anchor verdict visible pre-gate — GATED 383.5 bps < ALWAYS_ON 1115.0
  < BEST_LEG 3760.3; PASS_ALL_BASELINES false; folds_beating_always_on 1/4.
  Because scored mode replays identical code/seed/data, a scored run would be a
  foregone bit-identical replay — burning cells for it is theater, refused.
- disposition: file purged from working tree (this commit); no scored cells run;
  GO phrase stays registered-not-consumed and CANNOT be typed over the refusal;
  terminal reading per plan §5 preregistration: REGIME_COMBO_NO_INCREMENTAL_VALUE
  — overdetermined (fails baselines outright; the plan's additional floors are
  moot given outright baseline loss; A7 H2 verdict-law incompleteness noted for
  the record and fixed only if the owner elects a purge-and-rescore path).
- A7 findings M3/L4/L5/L6/L7 acknowledged: partial leading week bucket, G3/G4
  not actually logged (3-variable gate), BEST_LEG pre-pick, FX fold-tail
  deviation, wrong week count in commit message (true 283).
