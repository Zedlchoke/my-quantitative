# Z3/A5 Working Notes — Trend/Defensive Family Spec (outcome-blind)

Date: 2026-09-03. Lane: Z3/A5, worktree `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z3-trend`,
branch `orca/stocks-free-v2-z3-trend`.

## 1. Worktree identity verification

- `git rev-parse HEAD` -> `b345de411440b8db2f87a2ee61803f1d4aacc378` (exact match to BOOTSTRAP_SHA b345de4)
- `git branch --show-current` -> `orca/stocks-free-v2-z3-trend` (exact match)
- `git status --porcelain=v1` -> empty (clean) at start
All git commands used absolute `-C` paths. PASS.

## 2. Outcome-blind compliance

- No returns, PnL, PF, Sharpe, ranking or backtest of any proposed arm was computed. No scored artifact exists
  or was created. Python venv used only to (a) sha256 digests of frozen inputs/spec files and (b) JSON syntax
  validation.
- The A4 (z3-momentum) lane's work was not read; no branch switch occurred. The legacy V1 files under
  `research/proposals/stocks/` (blocked previous cycle, verdict STOCKS_FREE_V1_BLOCKED_FREE_DATA_AUTHORITY)
  were consulted only for file-format conventions; they are historical artifacts on this branch, not any
  current lane's work.
- All literature citations are internal-knowledge based, marked MODEL_INTERNAL_UNVERIFIED; no quotes or DOIs
  asserted.

## 3. Inputs read (read-only)

- PLAN_stocks_free.md §3 (research object/clock/portfolio), §10 (Z3/Z4 family spec requirements).
- research/control/stocks_free_v2_run/: run_contract.json, partition.json, cohort_census.json, split_factors.json.
- research/audits/stocks_free_v2/da2/da2_evidence.json.

## 4. Key design decisions and why

1. **Cohort = all 11 (SPY + 10 sectors), not SPY-only core.** A SPY-only book would put 100% of positive PnL
   into one ETF, structurally violating the required "no ETF > 35% of positive PnL" concentration condition.
   Literature: index-level TSMOM (Moskowitz/Ooi/Pedersen 2012) + sector-level trend timing (Faber 2007).
   Sector overlap with SPY declared as a limitation; equal weighting is breadth, not a diversification claim.
2. **Arm 1 anchor = 12-month TSMOM sign + 10% vol target to cash.** Canonical lookback (252 sessions), zero
   skip (the 12-1 skip is a cross-sectional-reversal device), threshold at 0. Vol overlay motivated by
   Barroso/Santa-Clara 2015, Daniel/Moskowitz 2016, Moreira/Muir 2017.
3. **Arm 2 neighbour = 200-session SMA filter, weekly clock.** Different lever: trend-estimator FORM
   (level-vs-SMA distance vs point-to-point return sign). Weekly sampling declared together with the SMA form
   as one neighbour configuration (Faber's rule is conventionally sampled on a calendar clock; weekly retains
   information at modest turnover cost). Everything else identical to the anchor for comparability.
4. **Arm 3 control = sign inversion of the anchor** (eligible iff 12m return < 0), all else identical. This
   destroys the family's PRIMARY mechanism (trend selection) while holding the vol lever constant; per PLAN
   §10 exactly one control is registered. The vol lever is therefore not separately controlled this cycle —
   stated openly as a scope boundary.
5. **Ramp-in rule.** Official warmup is 63 sessions but the features need 252/200 sessions of TR history from
   coverage start 2018-01-02. Backward extension/fabrication is forbidden, so decisions before full lookback
   availability are suppressed with the book 100% cash (unscored), inside S0 fold 1. Evidence minimums
   (>=18/fold, >=70 total monthly; >=95/fold, >=340 total weekly) are set below the approximate calendar
   capacity (~21/29/29 monthly after ramp-in; ~100/128/128 weekly) so the ramp-in cannot mechanically void
   arms.
6. **Split handling.** The 5 sector 2:1 splits (eff 2025-12-05) sit inside SEALED S1; S0 unaffected. Signals
   run on the amended TR chain (raw closes x issuer-confirmed split factors + SSGA distribution records);
   targets are notional-based so raw price halving only changes share counts. The control/inverted arm shares
   the same semantics so the mutation remains a pure sign flip.
7. **Vol estimator simplification.** sigma_arena = sqrt(mean of eligible per-ETF variances) — deterministic,
   no covariance estimation. Declared a priori; sector correlations are high so the bias is small and, more
   importantly, it is frozen before any outcome is seen.
8. **Monthly vs weekly clocks frozen per arm** (anchor/control monthly, neighbour weekly) — the plan requires
   freezing the clock before scoring; both clocks are literature-natural for their estimator.

## 5. Digests computed

Input digests (sha256, venv python hashlib over exact bytes):
- PLAN_stocks_free.md d3458d858f0c39371361819541189e8e6b2ef4e310bde94edf40bf92919f7318
- cohort_census.json 4f9cab6af48126955a92e4d5d9ef12954a59a59a8250175a4c2d31cdc65a3a0f
- partition.json 9b4ad7993f943edb1f4a995184eb85083879168f9f86eb1720b2a66623ef17c7
- run_contract.json 65410307ca4e8b25fa31d74f1ebad0562097f32d251f5316bd007c0f435735d8
- split_factors.json f666565124155bd26ecec8de9b88864b58f85831f404ccac48bcbb8cc135fc9b
- da2_evidence.json 014e73682fa45d60332dcdac6f07b2807d51556cfff192baa6cd35bea172a1da

Output spec digests (recorded in a5_family_manifest.json):
- a5_arm1_tsm12_ivol.json 6c301db551c8e5faa68bb923411137c28581d5aa9816984d076e3cbf603cfc57
- a5_arm2_sma200_weekly.json 8c65c0d7ea7582b70df0c216c42b202f5ca23788a06945ec2e9676837e69c4c1
- a5_arm3_tsm12_inverted_control.json 5f3d93ba85241d22bde44978efa0bc98d3c5fbdb9cbee6f2d8881d313db39527
- a5_family_manifest.json d69fb046b9b148f36747ce8968b332b071420f7836fc74a830b242dec3b4a3c8

All output JSONs parsed with json.loads (syntax valid).

## 6. Assumptions / declared judgment calls (for A7 attention)

- 10 bps/side spread+slippage is a conservative declaration, not a measured value (TD Basic gives no quotes).
- Turnover/evidence-count numbers are expectations from rule structure + calendar arithmetic; nothing was
  simulated.
- The fold scored windows in this spec (2020-09-01 / 2023-02-09 / 2025-07-24 scored ends, purge 5) are taken
  verbatim from partition.json's serialized fold records.
- The Z8 primary statistic is named prospectively ("excess vs flat benchmark, realized-vol-normalized, per
  fold") for falsifiability; the Z3/A5 lane does not compute it.
- The empty-eligible-set edge case is frequent by construction for the CONTROL (all-ETF uptrend months) and is
  counted as a valid 100%-cash decision event so the control keeps evidence parity with the anchor.
- If A7/A6 later needs an exact first-decision date, it must be derived from the frozen session calendar
  (count of completed TR sessions from 2018-01-02), not from this spec's ~2019-01 / ~2018-10 approximations.

## 7. Writes

- research/proposals/stocks_free_v2/a5_arm1_tsm12_ivol.json
- research/proposals/stocks_free_v2/a5_arm2_sma200_weekly.json
- research/proposals/stocks_free_v2/a5_arm3_tsm12_inverted_control.json
- research/proposals/stocks_free_v2/a5_family_manifest.json
- research/proposals/stocks_free_v2/a5_family_spec.md
- research/audits/stocks_free_v2/z3_a5/notes.md (this file)
Single commit on orca/stocks-free-v2-z3-trend. No merge/rebase/push; no child agents.
