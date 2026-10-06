#!/bin/zsh
# Check 3 evidence (verbatim command run 2026-10-03, exit 0).
# NOTE: dispatch anticipated the date column might differ; the loader exposes
# obs_date (derived from observation_period), so the probe prints obs_date min/max.
cd /Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003 && /Users/hoangminhlong/my-quantitative/.venv/bin/python -c "
import sys; sys.path.insert(0,'analysis')
import NQ_deep_lib as L
c = L.load_cot_nq_all_lines()
s = c[c.series_id=='COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE']
print('rows:', len(s))
print('columns:', list(s.columns))
print('window:', s.obs_date.min(), '..', s.obs_date.max())
print('series_ids present:', sorted(c.series_id.unique()))
"
