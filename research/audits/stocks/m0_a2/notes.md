# M0-A2 — asset-neutral common core: build notes and evidence

Lane: orca/stocks-m0-common, bootstrap 3f985e12791b34c9da790c1c6c3537c8ee1cb220.
Owner: A2 (shared multi-asset contracts and compatibility), PLAN_stocks.md sections 3, 6, 15 (M0_PASS).

## Acceptance evidence (lane-local)

- Command (from lane cwd):
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/assets/common tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q`
- Result: `78 passed` (57 in tests/assets/common, 21 historical protocol tests untouched).
- `git status --porcelain=v1` before and after the suite: identical (only the
  allowed untracked lanes `research/assets/`, `tests/assets/` and this audit
  dir; `.pytest_cache` self-ignores via its own `.gitignore`; `__pycache__/`
  and `results/` are repo-gitignored).
- No tracked historical crypto artifact read for mutation, no scored PnL, no
  network, no writes outside allowed globs.

## Deliverable map (PLAN section 6 -> files)

- asset-neutral contracts with explicit `asset_class`/`venue`/`calendar_id`/
  `cost_model_id` (+ provider provenance): `research/assets/common/contracts.py`.
  All identity fields are keyword-only and validated; there is no default
  asset class, venue, calendar or cost model anywhere (tests assert no
  `DEFAULT*` symbol exists in contracts/calendar/ledger_policy modules).
- session-calendar interface, holidays, early closes, no 24/7 default:
  `research/assets/common/calendar.py`. The only 24/7 calendar is
  `TEST_ONLY_DummySolar24x7` with the contractual `TEST_ONLY_` id prefix;
  `require_production_calendar_id` fails closed against it.
- carry interface + neutral `CashflowLine`: `research/assets/common/carrying_cost.py`
  (funding / borrow+dividend / rollover as abstract per-asset-class models).
- normalized instrument metadata: `research/assets/common/instrument.py`.
- execution-cost interface with immutable `CostModelId`:
  `research/assets/common/execution_cost.py`.
- exact arm identity + counters: `research/assets/common/trial_identity.py`.
  Identity digest = sha256 over canonical JSON whose `namespace` and
  `asset_class` keys both carry the asset class, so cross-asset-class
  identities are structurally unable to collide
  (`assert_cross_asset_class_separation`, `assert_no_collision`; tests force a
  broken payload and prove the asserts fire). Counters are pure functions +
  `TrialCounterBook` (no ledger IO): compute-once/publish-fail increments
  observed only; idempotent replay increments neither; publish at most once
  per observed identity.
- crypto migration adapter: `research/assets/common/crypto_compat.py`. It
  imports `research.protocol.manifest.build_manifest` (read-only reference,
  never patched) and accepts a `ManifestSpec` or its persisted dict/YAML
  payload. Historical validation is reused, so old manifests that would fail
  `build_manifest` fail identically here. Every historical value is preserved
  verbatim (`legacy_payload` == exactly the key set `write_manifest` dumps);
  `venue`/`calendar_id` are required keyword args (no historical source, no
  invention); `cost_model_id` is deterministically composed FROM the
  historical fee/slippage/funding strings
  (`CRYPTO_COMPAT::<fee_model>::<slippage_model>::<funding_mode>`); family/
  arm/config-digest map from hypothesis_id / strategy_type@candidate_version /
  config_sha256.
- ledger placement: `research/assets/common/ledger_policy.py`. Roots:
  `CRYPTO_PERP -> results/registry` (historical, untouched),
  `US_CASH_EQUITY -> results/registry/stocks`, `FX_SPOT -> results/registry/forex`
  (reserved). Unknown classes fail closed. ONE global trial index path
  (`results/registry/global_trial_index.jsonl`) exposed through the
  `GlobalTrialIndex` ABC that has only `snapshot/digest/count` — no write
  method exists in the interface. Path policy only; no runtime IO.
- profit-factor separation: `AssetExperimentContract` and
  `ScoredResultContract` carry distinct `position_pnl_profit_factor` and
  `return_series_profit_factor` fields (kw_only, so positional swap is
  impossible), mirroring `research/protocol/metrics.py` (position_pf from the
  net position series vs series stats from stats_returns). Metric absences
  use `MetricReading(value=None, reason=<non-empty>)`; silent 0.0 is
  structurally impossible.

## Assumptions / notes for integration

- `ARM_IDENTITY` schema version pinned at 1 (`IDENTITY_SCHEMA_VERSION`).
- `canonical_json` is stdlib-local (sorted keys, tight separators) with the
  same byte format as `contracts.protocol.canonical_json`; the common layer
  deliberately does not import the crypto protocol package (only
  `crypto_compat` does, for migration).
- Historical manifests never carry venue/calendar, so the adapter REQUIRES
  them per call; a future backfill can pin per-experiment values.
- The forced-collision test monkeypatches
  `research.assets.common.trial_identity.canonical_identity_payload` inside
  the test and restores it in a finally block; it never touches
  `research/protocol/**`.
- Suite-side no-mutation is additionally enforced by
  `tests/assets/common/test_no_runtime_writes.py` (fresh-interpreter import of
  all modules leaves `git status --porcelain=v1` unchanged).

## Commit

Exactly one commit on orca/stocks-m0-common:
"M0: asset-neutral common core + compatibility tests (A2)".
Staged paths: research/assets/**, tests/assets/**, research/audits/stocks/m0_a2/**.
