# A7 Pre-Launch Audit — EURUSD-OPEN-SEARCH-V2

- **Auditor**: A7 (independent, fresh context — no prior session state, no access to
  the implementing agents' reasoning; every claim re-derived from bytes)
- **measured_utc**: 2026-09-23T15:13:49Z
- **Scope**: pre-launch gate before the ONE holdout look (2026-01-01..2026-06-30)
  of the two frozen candidates. AUDIT-ONLY: this artifact pair is the only thing
  written by this audit; nothing else was changed, no commits made.
- **VERDICT: AUTHORIZED** (0 blocking findings; 1 minor, 3 informational)

## Fresh-context declaration

This audit was executed from a cold start: no handoff notes, no access to RUN
session logs, no trust in the dispatch context. Every number below was either
recomputed from the raw corpus/JSONL/parquet bytes or re-executed by the
auditor's own scripts. Engine sha verified independently of the freeze file's
self-declaration, then cross-checked against it.

## Verdict justification

The freeze chain is intact and monotone (freeze before outcomes, remediation
without freeze delta, candidates frozen after outcomes by the preregistered
deterministic rule), the RUN-1 look-ahead bug is genuinely fixed and
systematically guarded (truncation-invariance fixtures 4/4 PASS, re-run by
auditor), the dev/holdout boundary is physically enforced in code and verified
in both directions, and both frozen candidates' claimed dev numbers reproduce
EXACTLY (all three cost tiers plus all six folds) when re-run by the auditor on
an independently sliced dev plane. The holdout window has never been touched by
any committed artifact: `holdout_check_v2.json` does not exist and never existed
in branch history. The ONE look is armed with preregistered success criteria
(net>0 @1.0 AND @1.5, failure final, no rescue).

## Checks

### 1. FREEZE CHAIN — PASS
- Commit sequence on `orca/eurusd-open-search-v2-integration`:
  `7d404138` (plan) → `8bbbd4ef` (code freeze) → `4652c2fb` (remediation) →
  `cb479046` (RUN-2 outcomes) = HEAD.
- Plan provenance: `6e9b315f` on `main`; branch copy `7d404138` has identical
  content (blob sha256 `48cf91e1…ff2c09` at main, 7d404138, and HEAD).
- `selection_freeze_v2.json` first appears at `8bbbd4ef` (git log over the file
  returns only 8bbbd4ef; cb479046 diff vs 8bbbd4ef = 0 lines → UNCHANGED through
  remediation, exactly as the incident artifact claims).
- `outcomes/candidates_frozen_v2.json` first appears at `cb479046` only.
- engine.py sha256 recomputed at `8bbbd4ef`, `4652c2fb`, `cb479046`, HEAD and
  working tree: all `cc868402e63db2f6b487fc544fe0799889db4c5e0e0df3f3689693f0871cb491`,
  equal to `selection_freeze_v2.json.engine_sha256` and byte-identical to V1's
  engine at `bd61d200` (v1 semantics reused unchanged — claim verified).

### 2. RUN-1 VOID HANDLING — PASS
- `outcomes/INCIDENT_RUN1_VOID.json` (committed at 4652c2fb) discloses: crash at
  f_rangeexp (first day), f_daymom look-ahead (+26,297 pips / PF 4.21 fabricated),
  whole-run invalidation policy, freeze unchanged.
- Fix verified in `scripts/v2_lib.py::f_daymom`: signal window
  `ret = closes[days[j]] - closes[days[j-N]]` ends at `days[j]`; traded day is
  `days[j+1]`; the traded day's own close can never enter its own signal.
- `f_rangeexp` first-day guard present (`if d not in ranges: continue`).
- Truncation-invariance fixtures extended to 8 families including `daymom`,
  `rangeexp`, `dow`. Auditor ran the suite from repo root:
  `pytest scripts/test_v2_fixtures.py -q` → **4 passed** (0.86s).
- Sanity reasoning for the +26k fabrication: with the bug, the target for day
  d was derived from day d's own close; the engine then fills at day d's next
  bar open. The signal therefore contained the very move being traded —
  mechanically correlated with its own fill price — so the printed P&L was an
  artifact of self-fulfilling targets, not of any market edge. Magnitude
  (+26k pips vs RUN-2's family median of −786) is consistent with such a
  construction. Whole-run VOID was the correct policy (printed numbers cannot
  be partially trusted after an in-run signal-code bug).

### 3. LEAK GUARDS — PASS
- `v2_campaign.main` physically slices every plane array to
  `ts < 2026-01-01T00:00Z` before any outcome computation and hard-fails
  (`FAIL_CLOSED`) if any holdout bar survives the slice.
- `v2_holdout.main` loads only `ts >= 2026-01-01T00:00Z`, hard-fails otherwise,
  enforces bar-count stability and logs run_count.
- Auditor's own dev slice: 27,748 H1 bars, max ts 2025-12-31 20:00 UTC.
- `outcomes/` contains NO holdout metrics: `holdout_check_v2.json` does not
  exist; grep of all outcome files shows no 2026 metrics (only timestamps and
  the preregistered success string). Whole-branch-history search for
  `holdout_check_v2.json` matches only the runner script itself, never an artifact.

### 4. ENGINE SEMANTICS — PASS
- engine.py byte-identical to V1 (sha above) — no semantics drift.
- `H1Plane` masks verified in source: `skip = hour >= 20` (hours 20-23 exist in
  data, never traded); `fill_ok = tradable & (hour <= 18)` (no fills at the
  day-close bar or later); `is_day_close` marks each day's LAST tradable bar
  (19:00 normally → close at 20:00, one hour before the 21:00 rollover).
- `run_strategy` force-flat law: at `is_day_close` bars every open position
  closes at that bar's CLOSE price with k-adjusted opposite-side spread; the
  fixture `test_force_flat_before_rollover_h1` (PASS) proves one round-trip per
  day, same-day exits, exit hour <= 19. No overnight holds ⇒ swap never touched.

### 5. TRIAL ACCOUNTING — PASS
- `outcomes/campaign_dev_v2.jsonl`: 48 records, 48 distinct arm_ids, every
  record carries `d2 = OWNER_WAIVED_EXPLORATORY`, `code_freeze_sha = 4652c2fb…`
  (the remediated code RUN-2 actually ran on) and uniform
  `data_manifest_sha256 = ef154574…121c6`, which equals the auditor-recomputed
  sha256 of `data_local/duka/m1_manifest.json`.
- 12 config digests (≥6 required) hand-recomputed with raw
  `sha256(json.dumps({family, config}, sort_keys=True))[:16]` — NOT via
  `E.config_digest` — across 10 families: all match JSONL and
  `selection_freeze_v2.json`, including both frozen candidates
  (`020e645dbfec2cdc`, `548bb8606af4beae`).
- Full independent re-run of `FX2-RANGEEXP-C3` and `FX2-RANGEEXP-C4`: auditor
  loaded the H1 plane via `v2_campaign.load_h1_plane()`, sliced to dev, ran
  `E.run_strategy` at k ∈ {1.0, 1.5, 2.0}, computed `E.metrics` and folds.
  **EXACT match** (net_pips, trades, pf, hit, maxdd_pips and all six folds):
  - C3: 7147.1 / 6822.1 / 6497.1; PF 1.7287; 1000 trades; folds
    872.8/518.7/868.9/439.1/339.0/440.7 (6/6 positive — verified).
  - C4: 6561.1 / 6235.35 / 5909.6; PF 1.6497; 1003 trades; folds
    669.6/495.4/644.9/283.1/359.8/604.9 (6/6 positive — verified).
- Budget: 48 observed ≤ cap 96. RUN-1 is voided by policy and excluded from the
  denominator per the incident artifact; even counted, 48+48 = 96 = cap.

### 6. CLAIM CONSISTENCY — PASS
- `dev_distribution_v2.json` recomputed from JSONL: trials 48, positive@1.0 = 14,
  positive@1.5 = 10, eligible = 3; min/median/max @1.0 (−4569.7/−786.3/7147.1)
  and @1.5 (−5011.25/−1243.425/6822.1); total_trades_k1 = 93,820. All exact.
- All 48 records' gates G1-G5 recomputed from stored tiers/folds: zero
  inconsistencies; eligibility flag equals recomputed all-gates for every arm.
- Selection rule applied correctly: eligible ranked by net@1.5 →
  C3 (6822.1) > C4 (6235.35) > FX2-GAP-C4 (670.35); rule freezes ≤2 → C3, C4.
- FX2-GAP-C4 disclosed as `third_eligible_not_frozen` in
  candidates_frozen_v2.json with honest decay disclosure — verified from JSONL
  folds: F5 = −73.0, F6 = −202.1 (indeed decaying).
- `candidates_frozen_v2.json` dev_stats match the JSONL for both candidates
  (exact for C3/C4; GAP-C4's 670.4 is a 0.05-pip rounding of 670.35 — see F2).
- Sibling-mechanism note present: both candidates are wide-prior-day-range fade
  configs → holdout is treated as ONE mechanism test (conservative, correct).
- Preregistration content verified in the committed plan: owner option (a);
  `D2 = OWNER_WAIVED_EXPLORATORY`; G2 = PF ≥ 1.20 with V1 false-positive
  rationale (dev 1.14 → holdout 0.98); V1 holdout demoted to dev with the
  single-look contamination DISCLOSED; FRESH holdout 2026-01-01..2026-06-30
  never touched; success = net>0 @1.0 AND @1.5, ONE look, failure final;
  force-flat 19:00 bar (close 20:00); 12×4 = 48 planned / 96 cap.
- Data claims verified: manifest = 4014 files (3652 pre-2026 + 362 dated 2026),
  `complete: true`, 0 missing; 7/7 auditor-sampled files byte-exact vs manifest
  sha256 (mix of BID/ASK, 2021-2026); census `BUILD_PASS`: bars15_valid =
  130,911 (re-read from parquet: 130,911), H1 bars 30,550 (re-read: 30,550),
  `nonpos_spread_minutes = 0`.

### 7. BOUNDARIES — PASS
- Plan declares `orders: NONE`; no order/paper/live/broker code exists in the
  committed cycle tree (the single regex hit, `order_violations`, is a benign
  OHLC-ordering data-quality counter in the decode probe).
- No holdout metrics anywhere in outcomes/ or anywhere in branch history.
- No secrets in any committed cycle file (git grep for key/secret/password/
  token/bearer patterns: clean).
- Working tree clean except one untracked housekeeping file (`.gitignore`,
  content `data_local/`) — outside the freeze chain; data is properly untracked.

## Findings

| id | severity | finding |
|----|----------|---------|
| F1 | MINOR | `v2_lib.f_rangeexp` lines 296-297: a first assignment to `expand` is dead code (immediately overwritten by the next line). Effective semantics are the correct second assignment and match the frozen configs; the exact reproduction of outcomes makes any behavioral doubt moot. Cleanup-only. |
| F2 | INFO | `candidates_frozen_v2.json` discloses GAP-C4 net@1.5 as 670.4 vs JSONL 670.35 (0.05-pip rounding at 1dp). Zero materiality; C3/C4 values are exact. |
| F3 | INFO | `datetime.utcfromtimestamp` deprecation warning in `v2_lib.f_dow_simple` (60 warnings in fixture run). Cosmetic; no effect on Python 3.x current runtime. |
| F4 | INFO | Untracked `.gitignore` (`data_local/`) in the cycle dir — uncommitted housekeeping, not part of the freeze chain, consistent with the data-never-committed policy. |

## Blocking findings

None.

## What A7 authorizes

Proceed to the ONE holdout check (2026-01-01..2026-06-30) of exactly
`FX2-RANGEEXP-C3` and `FX2-RANGEEXP-C4` (treated as ONE mechanism test) via
`scripts/v2_holdout.py`, judging against the preregistered criteria in
`outcomes/candidates_frozen_v2.json`: net_pips > 0 @k=1.0 AND net_pips > 0
@k=1.5 on the holdout window. One look; failure is final; no rescue. Baselines
(LONG_ALWAYS / SHORT_ALWAYS / CASH / RANDOM_MATCHED) must be reported alongside.
