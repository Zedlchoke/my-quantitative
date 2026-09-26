# PIPELINE_CONTRACT_DRAFT.md — 5-layer data pipeline contract (draft for A1 freeze)

Cycle: DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 · Lane: L-PIT · 2026-09-26.
Basis: plan §7 ("Pipeline design contract — deliverable, not implementation"),
plan §5 schema, COMMON.md, OWNER_DIRECTIVE.md (binding, entire file).
A1 freezes; this draft is the implementable contract text.

Per-layer status marks: **[EXISTS]** = machinery already committed and
exercised (pointer given); **[PARTIAL]** = some pieces exist, named gaps
listed; **[DESIGN-ONLY]** = contract text only, nothing committed.

---

## L1 — raw immutable layer

**Contract.** Every acquired byte lands once, machine-local, outside Git
(`~/.my-quantitative-data/<cycle>/raw/...` or cycle data roots), write-once.
Each corpus gets a committed sha256 manifest (one entry per file: path,
bytes, sha256, retrieval timestamp, source URL redacted of credentials,
authority_status, parser_version). The manifest — never the bytes — is the
Git artifact. Re-pull must be deterministic from recorded URLs + frozen
contracts. No raw bytes in Git, ever (P-13/V13 convention).

**Inventory.**
- [EXISTS] CADS content-addressed store — `research/platform_v3/cads.py`
  (`register/pin/resolve/verify`; re-hash mismatch raises
  `CADSIntegrityError`; used by RATES/VOL/COMMODITIES-NG1 and CRYPTO-NG4
  "panels+OI re-pinned to CADS digests").
- [EXISTS] committed per-file manifests + redacted-URL convention — FDF-V1
  manifests (`research/control/free_data_frontier_v1_run/manifests/*.json`
  on `orca/free-data-frontier-v1-integration`; entries carry raw_sha256,
  content_length, source_url_redacted, retrieved_time_utc, parser_version
  `free_data_frontier@1`).
- [EXISTS] chained manifest for streams — DEU-V1 Lane C collection contract
  (`content-addressed shard layout + chained manifest`, freeze field
  adopted from `cng4-a3`).
- [EXISTS] raw-out-of-Git with pinned manifest — commodities_ng1_run
  `.gitignore` ("Raw source bytes are pinned by p0_raw_manifest.json, not
  committed … re-pull is deterministic from the recorded official URLs").
- [PARTIAL] uniformity: three manifest shapes coexist (FDF entry objects,
  p0 census+sha-pin objects, CADS journal). A single manifest schema is
  DESIGN-ONLY (recommend `dfv1_manifest@1` = FDF entry shape + CADS address
  field optional).

**Invariants.** write-once (no in-place edit of staged raw; corrections are
new vintages); every byte hashable from its manifest entry; manifest
committed BEFORE the cycle that owns the corpus can close; MISMATCH from a
possibly mid-write file is never written (plan §14 F5).

## L2 — normalized + provenance layer

**Contract.** Raw → typed canonical records carrying row-level lineage:
`source_id`, `normalizer_version` (parser contract version), `source_url /
retrieval identity`, `bar_id`/event identity, and the frozen rule IDs that
governed the transform (e.g. adjustment rules). Integers/fixed-point
strings only in persisted models (no floats in bar payloads); canonical
request ids recorded per retrieval.

**Inventory.**
- [EXISTS] typed no-float bar model with golden identity —
  `research/market_data_plane/models.py` +
  `tests/test_mdp_bars.py::test_float_input_rejected_no_floats_anywhere_in_the_bar_model`,
  `test_decimal_inputs_persist_as_canonical_fixed_point_strings`,
  `test_bar_id_golden_recomputed_by_hand_from_frozen_identity_tuple`,
  `test_exact_frozen_field_set_order_and_missing_extra_rejected`.
- [EXISTS] frozen adapter rule IDs as lineage — stocks adapter
  `ADJUSTMENT_AVAILABILITY_RULE = "FACTOR_AVAILABLE_AT_EX_DATE_SESSION_OPEN"`
  (divergent rules fail closed;
  `.worktrees/stocks-amihud-retest-v1/integration/research/market_data_plane/adapters/stocks/context.py`).
- [EXISTS] per-record provenance fields — FDF manifests carry
  `canonical_request_id`, `parser_version`; NY Fed records carry
  revisionIndicator + effectiveDate.
- [EXISTS] canonical module — `research/platform_v3/canonical.py` and
  `research/market_data_plane/_canonical.py`.
- [PARTIAL] a single cross-asset `normalizer_version` vocabulary: versions
  exist per program (`free_data_frontier@1`, mdp bar model, data_fusion) but
  a registry mapping source → normalizer contract version is DESIGN-ONLY.

**Invariants.** normalization is pure (same raw bytes + same
normalizer_version ⇒ same canonical bytes); unknown fields rejected, never
silently dropped; identity (symbol/ISIN/venue instrument) resolved via the
identity store — current aliases are never projected backward.

## L3 — PIT/quality gate layer (fail-closed)

**Contract.** Every normalized record/batch passes a gate set before it can
be consumed by any research or scoring surface. Gate failures are
fail-closed: the datum is quarantined with a reason code; a missing gate
verdict is NOT_RUN, never PASS. The fixture battery (see
FIXTURE_BATTERY_CONTRACT.md) defines the gate semantics; P-18 (ERP1) is the
truncation-proof standard for any PIT claim.

**Inventory.**
- [EXISTS] event quality gate with frozen reason codes —
  `research/market_data_plane/quality.py`:
  `IMPOSSIBLE_TIME_ORDER`, `UNKNOWN_INSTRUMENT`, `NEGATIVE_PRICE`,
  `NEGATIVE_SIZE`, `CROSSED_QUOTE`, `STALE_QUOTE`, `OUT_OF_ORDER_DELIVERY`,
  `DUPLICATE_EVENT`, `SEQUENCE_GAP`, `MANIFEST_MISMATCH`,
  `STATISTICAL_ANOMALY`; `status_from_codes` verdict vocabulary.
- [EXISTS] PIT as-of/vintage semantics — `tests/data_fusion/test_pit.py`
  (later revision does not leak backward; effective-date enforced; vintage
  series append-only; a later pull with different content is refused —
  `test_df_issue2_append_refuses_later_pull_with_different_content`).
- [EXISTS] executed PIT battery (the ERP1 F-PIT-1 standard) — designs
  M-1..M-5 in `SKEPTIC_cohort1_REPORT.md` (`.../ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/`),
  executed in TrackA cohort 1 (M-2 PASS 22.99%/20.38%; M-3
  DISCLOSED_SEAM 43.0%/63.4% day-flip; ledger row ERP1-TRACKA-COHORT-1) and
  cohort 2 ("generic PIT battery harness (pit_battery2, leak-catch proven)",
  F-2 PASS_PIT 4/4; TrackB: "PIT battery M-1..M-5 ALL PASS (318/318
  truncation replay byte-identical, P-18)").
- [EXISTS] calendar/session gate, fail-closed on official discrepancy —
  `research/platform_v3/calendar_engine.py` +
  `tests/platform_v3/test_calendar_engine.py` (12 gates incl.
  `test_official_discrepancy_fails_closed`,
  `test_us_federal_vs_exchange_holiday_difference`).
- [EXISTS] engine-level truncation invariance —
  EURUSD-OPEN-SEARCH-V1 `scripts/test_engine_fixtures.py::test_pit_truncation_invariance`
  (branch `orca/eurusd-open-search-v1-integration`); EOSV2 RUN-1 was voided
  pre-selection when extended truncation fixtures caught a look-ahead bug.
- [PARTIAL] one gate registry binding reasons → dispositions (drop /
  quarantine / fail cycle) across all planes: reason codes exist in mdp and
  data_fusion separately; a single failure-disposition table is DESIGN-ONLY.

**Fail-closed semantics (normative).** (i) unknown/missing gate verdict ⇒
NOT_RUN and consumption blocked; (ii) quarantined data is never silently
patched from a cross-source (data_fusion law: "cross-check never patches
primary gap"); (iii) missing bars stay missing and are COUNTED — no
interpolation, no forward-fill, no venue-cross substitution, no synthetic
reconstruction — ever (cng4 freeze field 13, adopted by DEU Lane C); (iv)
any PIT claim in prose must cite an executed truncation fixture (P-18).

## L4 — cost book layer

**Contract.** Per-asset cost books carry MEASURED (not stated) spreads,
commissions, financing/swap and fees, each with a source class
(`measured_account_bound` / `measured_census` / `declared_seed`) and stress
tiers (sweep ×1.0/×1.5/×2.0 minimum). Vendor-derived numbers are not broker
cost authority (F4 class fail-closed): a cost component with no measured
authority blocks the family, never defaults to a silent zero. Books are
digest-pinned before first cost-bearing use; a seed book carries a prominent
seed disclosure and a parallel stressed view — never merged into the base
book.

**Inventory.**
- [EXISTS] measured spread censuses — EURUSD-OPEN-SEARCH-V1 (119,038 valid
  15m bars, 0 non-positive-spread minutes, spread p50 0.3 pips from 3,652
  Dukascopy day files); FX-MAJORS-SEARCH-V1 per-pair censuses; PWS-CX-SOLUSDT-C1
  6-month bookTicker spread census (p50 0.469 bps, sha-pinned).
- [EXISTS] stress-tier sweep convention — BTC-H4-EDGE-SEARCH-V1 / BAND-RISK
  / ETHUSDT-OPEN-SEARCH-V1 (fees 5bps + 1 tick, tiers 1.0/1.5/2.0 folded
  into cell denominators); EOSV1 engine fixture
  `test_stress_k2_widens_cost_monotonic`.
- [EXISTS] digest-pinned seed book with separation law — ERP1 TrackB
  A7 condition M-1: cost book pinned "via a NEW dated file + new digest",
  "parallel view never merged (separate realized_net_stress field + basis
  strings); SEED disclosure prominent".
- [EXISTS] fail-closed cost authority rulings — FOREX-NG6 P0_F4 and
  FOREX-NG7 F4 (vendor quote ≠ broker product; financing band absent ⇒
  family BLOCKED, "never scored on a silent zero").
- [EXISTS] path-ladder cost model for multi-leg vol books — Q-16 contract
  exercised in VOL-NG1 (cost-ceiling family kill fired at the binding site).
- [PARTIAL] one cross-asset cost-book schema: the pieces above are
  per-cycle; a unified `dfv1_cost_book@1` (instrument × component × source
  class × tier × digest) is DESIGN-ONLY.

**Invariants.** no cost component enters a scored cell without a source
class; stress sweep is mandatory (a book that dies at ×2.0 is dead, not
"robust enough"); cost is charged once per round trip (V13 LIQEPIS anomaly
is the recorded violation class; cost-once kernel remediated in V14).

## L5 — query/replay read-only layer

**Contract.** All research/scoring reads go through a read-only query
surface over frozen manifests: no SQL escape, deterministic order, frozen
query identity, byte-identical replay. A scored run must be reproducible
from committed artifacts by a detached twin (ALL_MATCH) — this is the
program's standing reproduction standard.

**Inventory.**
- [EXISTS] QueryPlane — `research/platform_v3/query_plane.py`
  (`ForbiddenSQL`, `DuplicateManifestID`, `PathEscape`, `FrozenQuery`,
  `ManifestEntry`, `_enforce_frozen_order`); `consume_via_plane` adoption in
  ng1 cycles (CRYPTO-NG1 "S4 5/5 digests via consume_via_plane").
- [EXISTS] deterministic replay + reproduction tooling —
  `research/platform_v3/reproduce_core.py`; program-wide detached-twin
  ALL_MATCH precedent (FOREX-V6/V7/V8, BTC/ETH cycles, ILLIQ-REG-V1 "8/8
  artifact+shard files byte-identical").
- [EXISTS] authority binding at read time —
  `research/platform_v3/authority.py` / `pa4_pa5_authority.py`
  (AuthorityRegistry; V3-GA4 authority table granting S4 series).
- [PARTIAL] uniform cross-asset query API (mdp bridge exists:
  `research/market_data_plane/nautilus_bridge.py` +
  `tests/test_mdp_adapter_{crypto,forex,stocks}.py`); macro/vintage series
  still read outside the plane in places — DESIGN-ONLY to unify.

**Invariants.** reads never mutate L1–L4; replay of the same frozen query on
the same manifests is byte-identical; any consumption path that bypasses the
plane is a violation recorded as an incident.

---

## C-CX-1 — the crypto no-candle-inference clause (owner law, verbatim)

OWNER_DIRECTIVE.md (binding, line 36) rules for crypto, verbatim:

> "Không suy ra order book hay forced flow từ nến."

(= no order book and no forced flow may be inferred from candles.)

**Clause C-CX-1 (normative).** For any crypto dataset, feature, or state
variable: constructs that *represent or stand in for* order-book state
(depth, imbalance, L2/L3 topology, book pressure) or forced flow
(liquidations, stop cascades, taker/aggressor identity) MUST be derived
only from sources that actually record those phenomena (trades/quotes,
bookTicker, L2 snapshots, OI/liquidation feeds with their own PIT history
and license ruling). OHLCV candles (klines), mark/index price klines, and
any derived price/volume statistic are NOT admissible inputs for such
constructs. A consumer that cannot evidence a non-candle source manifest
for a book/flow construct must fail closed (refuse to compute), not
approximate. Consistent standing evidence: Binance um liquidationSnapshot is
404-everywhere and bookTicker export discontinued after 2024-04 (bear-recon
PIT_DISCLOSURES) — the missing tape may not be synthesized from klines.

**Named fixture requirement F-CX-NOBOOK-1.** A registered crypto
feature/consumer that claims book/flow semantics, when fed a candle-only
panel (klines with no trades/quotes/bookTicker/OI manifest), MUST reject the
input with reason code `NO_ORDERBOOK_FROM_CANDLES` (fail-closed), and the
battery must include a positive control (same construct fed a manifest-backed
tape fixture computes normally). **Status: DESIGN-ONLY** — the law exists
(OWNER_DIRECTIVE + plan §13) and adjacent fail-closed machinery exists (mdp
`UNKNOWN_INSTRUMENT`/manifest-context rejection path; TrackB
"bookTicker ABSENT → spreads DECLARED+stress" staging decision), but no
committed fixture carries this name or reason code. This is the battery's
one mandatory new fixture for crypto lanes.

---

## Layer-by-layer gap summary (feeds DATA_GAP_MATRIX)

1. L1: unify manifest shapes (`dfv1_manifest@1`) — DESIGN-ONLY.
2. L2: normalizer-version registry — DESIGN-ONLY.
3. L3: single failure-disposition registry; F-CX-NOBOOK-1 fixture; DST
   intraday fixture — DESIGN-ONLY.
4. L4: unified cost-book schema; FX broker-grade measured book still
   BLOCKED_ACCOUNT/BLOCKED_COST (owner action — see §3 rows 5/12).
5. L5: route macro/vintage series through the plane — DESIGN-ONLY.

Freeze note to A1: this draft intentionally contains no implementation code;
adoption requires per-layer adoption commits per the ng1 precedent.
