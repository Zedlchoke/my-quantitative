# WSL PROSPECTIVE PROVENANCE CAPTURE — REPAIR RECORD (round-7, 2026-10-20)

## Gap (owner report, confirmed)

- The WSL lane refuses `NOT_RUN_NO_PROVENANCE_FORECAST` unless the READ-ONLY
  provenance ledger (wsl-winprob-paper-prep-v1, 15 rows) has a FORECAST row
  for the fixture — recorded by the D-1 batch automation (cron
  automation-6d193fce, fired last on 2026-10-17 ICT for the Oct-18 matchday).
- That automation no longer fired after Oct 18 → zero provenance forecasts
  for the 140 future fixtures → the next cadence window (fixtures Oct 24-25)
  would have journaled NOT_RUN_NO_PROVENANCE_FORECAST for every WSL fixture.
- Separate, parallel gap: the corpus (both representations) is sealed at the
  R5 snapshot (last played round 2026-10-04). The qualified upstream
  (fixturedownload wsl-2026-UTC.csv) had STILL not posted the Oct 17-18
  finals as of 2026-10-20T01:15Z (refetch probe: R6 rows exist with Result
  EMPTY — same latency behavior batch-B documented for M37). Scores from a
  non-posted source cannot be invented; the R6 finals therefore remain OUT
  of the corpus pending upstream posting (probe again before the Oct-23
  D-1 batch). Ratings for the Oct 24-25 forecasts are therefore R5-sealed —
  exactly like batch-B's own forecasts (lawful; less-informed is honest).

## Repair (executed 2026-10-20T03:20-03:22Z, gates intact)

1. Fixtures for Oct 24-25 rebuilt from the exec substrate
   (`wsl_fixture_substrate.jsonl`, 7 fixtures: M44 Tottenham v Arsenal,
   M48 Brighton v West Ham — Oct 24; M47 Crystal Palace v Chelsea,
   M45 Liverpool v London City, M46 Everton v Aston Villa,
   M49 Birmingham v Charlton, M43 Man United v Man City — Oct 25) with
   team ids via the PINNED crosswalk (15 rows, all MAPPED).
2. Provenance batches run through the UNCHANGED pinned adapter
   (`wsl_forecast_adapter.py forecast`, gate require_gate = FIRST BATCH GO
   consumed 2026-10-10 — passed; anchor law: all recorded_at 2026-10-20,
   anchors Oct 24/25 — strictly pre-anchor; corpus: the batch-B
   D-1 snapshot corpus_merged_dminus1_20261018.csv sha 62fc9d5e…,
   2707 rows, seal law rows_future_excluded_seal=0):
   - 2026-10-24: written [M44, M48];
   - 2026-10-25: written [M47, M45, M46, M49, M43].
3. Provenance ledger now carries 7 FUTURE FORECAST rows (M43-M49), each
   with engine p + anchor_utc + recorded_at (PIT).
4. Sandbox next-fixture e2e: exec-side `engine_forecast` (from the exec
   corpus wsl_substrate_corpus.jsonl) reproduces each provenance p
   BIT-EQUAL for M44 and M48; `cross_check_forecast` PASSES — the exact
   refusal point NOT_RUN_NO_PROVENANCE_FORECAST is GONE for the window.

## Continuity law going forward (controller duty, unchanged)

The D-1 batch must run before every matchday: refetch CSV → merge corpus
(only if new FINALS posted — never forecast-unborn rows) → fixtures file →
`wsl_forecast_adapter forecast --date D`. The owner-side automation
(cron) that used to fire it is no longer present on this machine; until it
is re-established, the controller runs the batch manually each D-1. The
Polymarket markets for Oct 24-25 are ALREADY LISTED (probe: event 1212252
Tottenham v Arsenal 3-YES + derivatives, 1212928 Brighton v West Ham —
the quote leg of the cadence has live targets).

## Known open gaps (honest)

- R6 (Oct 17-18) finals: upstream not posted → corpus stays R5-sealed.
  Re-probe before each D-1; do NOT source scores from unqualified places.
- BBC page exposes only the NEXT matchweek (no R6 archive scores in the
  fetched page); api-football free plan lacks season 2026; The Odds API and
  ESPN have no WSL. Qualified-scores source remains OPEN.
- The exec-side cadence (live ops_service) runs the pre-round-6 module in
  memory; the refreshed substrate/provenance are FILES it already reads —
  no restart needed for the forecast cross-check to pass at the next
  anchor (file-based, derived each tick).
