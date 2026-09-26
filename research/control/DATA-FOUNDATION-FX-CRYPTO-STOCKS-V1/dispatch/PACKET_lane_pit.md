# PACKET — L-PIT (PIT/license cross-asset + pipeline & fixture contracts + outcome-exposure map)

ROLE: A3/A2-class cross-cutting lane. WORKTREE:
`/Users/hoangminhlong/my-quantitative/.worktrees/data-foundation-v1/lane-pit`
BRANCH: `orca/dfv1-lane-pit`. Allowed writes: `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/pit_license/` only. COMMON.md applies in full.

## Deliverables (beyond inventory_rows.jsonl + LANE_REPORT.md + handoff)

### 1. LICENSE_RULINGS_VERIFIED.md
Verify EVERY row of plan §3 against its source artifact (terminal verdict /
owner packet path under `research/control/**` or worktrees). For each: ruling,
artifact path, artifact sha (measured via `git -C <repo> rev-parse` for
committed files or `shasum -a 256` for plain files), one-line quote. Mark any
ruling you cannot evidence as UNVERIFIED (never infer PASS).

### 2. authority_row_schema.json
Machine-readable §5 schema (field names, enums, required fields) — the
contract every lane row must satisfy; include a validator snippet
(`.venv/bin/python` stdlib-only) `validate_rows.py` that checks a jsonl file
against it. Run it on your own outputs.

### 3. PIPELINE_CONTRACT_DRAFT.md
The 5-layer pipeline design (plan §7) as an implementable contract: per
layer, inputs/outputs, invariants (write-once raw, sha manifests,
provenance fields incl. normalizer_version, PIT gate fail-closed semantics,
cost-book schema with stress tiers, read-only replay determinism), and where
existing machinery already implements each piece (CADS in
`research/platform_v3/`, market_data_plane, EURUSD census fixtures, ERP1
F-PIT-1 battery, CHR3F fixtures) — inventory what EXISTS vs what is DESIGN-
ONLY. Encode the crypto law verbatim: "Không suy ra order book hay forced
flow từ nến" (no order book or forced flow inferred from candles) as a
contract clause + a named fixture requirement.

### 4. FIXTURE_BATTERY_CONTRACT.md
Named fixture designs (synthetic, hand-computable): future-leak truncation
replay; revision/restatement detection (value changes retroactively); DST
boundary; symbol/identity change; duplicate/missing bar; quote crossed/stale;
source disagreement; stamp-scale migration (L-TRACKB1-1 law: assert
first/last stamp within one bar of declared window end); spread non-positive
rejection; volume-0 unfillable bar (L-SAMV1-3); reverse-split adjustment
(L-SAMV1-1). For each: existing implementation pointer if any (search
tests/ and research/control fixture artifacts), else DESIGN-ONLY.

### 5. OUTCOME_EXPOSURE_MAP.md
From `research/wayfinder/HYPOTHESIS_LEDGER.md` + MAP.md sprint states ONLY
(read-only): tabulate (a) OUTCOME-EXPOSED research data — every dev/holdout
window actually read by a scored or exploratory cycle (e.g. EURUSD M1/H1
2021–2025 dev + 2026-H1 holdout; GBPUSD/USDJPY dev + 2026-H1 holdout; BTC
H1/H4 2020–2026 panels; ETH corpus 2020–2026; SOL/BNB klines+funding; stocks
EODHD panels + windows; CoT/curve/vol windows) — instrument × window × cycle
that consumed it; (b) UNOPENED confirmation data — S1 (sealed, everywhere),
ERP1 sealed 2026-H1 AUDUSD+USDCAD holdouts (manifest metadata only!), all
post-2026-09 prospective streams; (c) the separation RULE: unopened windows
readable only by a future owner-authorized confirmation plan; prospective
collectors must not be replayed into research.

## Census rows you own
Shared/cross-asset datasets: FRED (owner key exists — status
AVAILABLE_UNVALIDATED this cycle: key use forbidden; note channel), ALFRED,
BIS, ECB, Treasury par yields, CBOE VIX family, CFTC CoT, NY Fed, OFR,
exchange calendars (GB/CA/AU/NZ + exchange_calendars library), NWS/EIA/USDA
(FDF-V1). Locate each on disk (worktrees/staging/`~/.my-quantitative-data`),
manifest status, coverage measured where cheap.
