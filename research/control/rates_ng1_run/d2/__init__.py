"""RATES-NG1 D2 novelty measurement package.

P-12 law for this package (dispatch packet rates-ng1-d2-novelty):

- commit-1 carries the measurement code, the shadow-reconstruction
  definitions, the representation mapping and the frozen default
  parameters.  NO rho number of any kind may appear in any commit-1
  file (checked by tests/test_rates_ng1_d2.py::test_commit1_files_
  contain_no_rho_values).
- commit-2 carries the results artifact ``d2_novelty_panel.json``
  (per-proposal x per-shadow Spearman/Pearson decision-STATE
  correlations, pooled max, margin to the frozen 0.20 ceiling and the
  ELIGIBLE/VETO verdict), written by ``d2_run.run_measurement`` AFTER
  commit-1 exists.

Scope law: decision-STATE series correlation only.  No scored outcome,
no PnL, no cost-adjusted edge is computed anywhere in this package.
"""

SCHEMA = "rates_ng1_run/d2_novelty@1"
