"""futbt.dbn — offline Databento DBN v3 ingestion adapter (PREP).

SYNTHETIC-ONLY: every byte this package consumes in tests comes from
`fixtures.build_fixture_dir` (deterministic, fabricated, labeled). No API
keys, no network, no billable calls, no real data paths.

Layer map (see README.md in this directory for the full disclosure table):
  spec     DBN v3 wire layouts, enums, sentinels, pack/unpack (byte-exact
           port of the reference implementation, main@2026-10-02)
  wire     DBN file framing: metadata prelude/body encode+decode, record
           stream decode; fail-closed on unknown record types
  textio   CSV/JSONL export shapes (pretty rules + column order per the
           reference serializer); lenient-by-name readers
  fixtures deterministic synthetic GLBX.MDP3-shaped DBN/CSV/JSONL files
           with the adversarial behaviors the program must survive
  ingest   file -> typed frames; contract identity resolution from
           definition actions; continuous-series execution guard
  session  exchange-tz session calendar (DST-correct), holiday/short
           inference, absence-aware NO_DATA, full-session reconstruction
  ohlcv    trade classification, 1m->session aggregation with explicit
           boundaries, settlement separation, negative-price preservation
  bbo      book-time BBO/trade synchronization, crossed/locked detection,
           executable-quote enforcement, bar-side spread proxies
  pit      point-in-time as-of views, settlement vintages, feature-only
           roll adjustment factors
  qa       SHA256 manifests, gap/duplicate/monotonic checks, coverage
           reports, roll-window volume/OI migration summary
"""
__version__ = "0.1.0"
