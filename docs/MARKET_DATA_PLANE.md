# Market Data Plane (MDP-V1)

Engineering plane for research-grade market data: bad data becomes
**observable, replayable, and fail-closed**. It sits below the strategy
factory and above raw provider payloads. MDP-V1 authorizes no dataset for
scoring, opens no S1, and validates no edge.

```text
provider payloads
  -> immutable raw chunks + manifests        (research/market_data_plane/archive.py, manifest.py)
  -> canonical market events + quality       (models.py, quality.py, reason_codes.py)
  -> quarantine or accepted stream           (quarantine.py)
  -> deterministic replay                    (replay.py)
  -> BBO / depth / TCA research views        (bbo.py, depth.py, tca.py)
  -> strict NautilusTrader bridge            (nautilus_bridge.py)
  -> existing asset research factories
```

## Contracts

- Event schema `mdp.market_event@1`: 27 frozen fields; integer UTC-ns
  timestamps (three distinct clocks: exchange / receive / available);
  exact decimal strings + declared precisions (never binary float in
  persisted evidence); deterministic `event_id` = sha256 of the 0x1F
  identity string; `manifest_sha256` REQUIRED (upstream retrieval
  manifest — A1 rulings A2_Q1/A3_Q4).
- Manifest schema `mdp.raw_chunk_manifest@1`: content-addressed
  (`payload_sha256`), entitlement evidence mandatory, secrets-removed
  request identity, completeness + gap reasons, sequence semantics.
- Quality: `VALID / SUSPECT / INVALID / QUARANTINED` with the versioned
  `reason_codes@1` registry. Sequence gaps only where the source
  guarantees contiguity; crossed quotes only inside one venue;
  statistical anomalies are diagnostic, never silent deletion. Every
  rejection carries a raw reference and reason.
- Archive: content-addressed chunks written via sibling temp file →
  fsync → atomic replace → re-read verify → manifest publication.
  Existing content hashes are read-only; appends are forbidden; orphans
  are diagnosed, never guessed complete.
- Replay: total order over
  `(exchange, receive, available, source, venue, instrument, type,
  sequence, event_id)`; explicit manifest list + predicate inputs
  (recorded verbatim; never discovers newer files); byte-identical
  streams across processes, cwds, and detached worktrees.
- Views: venue-local then consolidated BBO with contributor IDs and a
  REQUIRED staleness threshold (no hidden defaults); depth is
  `NOT_EVALUABLE` without proven snapshot/delta semantics and is never
  synthesized from bars; TCA metrics (arrival mid, decision-to-fill
  slippage, effective/realized spread at frozen horizons, fill ratio,
  fees, funding, impact proxy) with missing evidence → `NOT_EVALUABLE`,
  never zero.
- Bridge: `nautilus_trader==1.230.0`, QUOTE→QuoteTick, TRADE→TradeTick,
  instrument metadata mandatory, lossless-or-raise precision gate
  (nautilus silently rounds — we pre-verify and raise), exact ns
  timestamp mapping, quality-gated streaming with explicit diagnostics
  sidecar, `to_bar` refuses (no canonical BAR type in @1). See
  `docs/MDP_BRIDGE_NOTES.md`.

## Example

```python
import sys; sys.path.insert(0, "research")
from market_data_plane import models, quality, archive, replay

event = models.build_event({... 27 canonical fields ...})      # validates
status, codes = quality.evaluate(event, None, QualityParams(...))
chunk = archive.write_chunk(root, b"...\n")                    # immutable
res = replay.replay(root, [manifest_id], predicate={...})      # byte-stable
res["stream_digest"]                                           # reproduction key
```

End-to-end demo: `research/control/market_data_plane_v1_run/demo_e2e.py`
(committed synthetic fixtures only; no network, credentials, orders, or
scored logic).

## Semantics

Data Fusion (`research/data_fusion/`, adopted from audited pin `c6a0576`)
remains the evidence layer for availability, validity, license, source
and transformation lineage. MDP adds event-stream and microstructure
semantics; it never creates a competing `NormalizedRecord`. Two MDP
versioned corrections to the pin are documented in
`research/control/market_data_plane_v1_run/gates/G3_data_fusion_fixes.json`
(next-day-exclusive date-only boundaries; retrieval-time removed from the
vintage conflict identity — the later pull no longer silently wins).

## Limits (honest)

- No provider is made authoritative; no source is authorized for scored
  research by this plane. Every future asset cycle must separately
  authorize data and freeze semantics (see `docs/MDP_ASSET_ADOPTION.md`).
- Performance: ~11.6k events/s median for the full
  build→validate→classify→serialize→archive→replay path on the reference
  host — an engineering figure, not an HFT claim.
- DVC (`docs/MDP_DVC_OPERATOR.md`) is transport-only and **never**
  establishes data authority; its local-remote transfer does not re-hash
  (DVC-LIMITATION-1) — always verify manifests after `dvc pull`.
