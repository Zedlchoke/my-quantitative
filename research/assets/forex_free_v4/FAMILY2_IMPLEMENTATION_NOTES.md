# FXFV4-A6-P2 — FAMILY2 IMPLEMENTATION NOTES (lane I-FAMILY-2)

Cycle FOREX-FREE-V4, branch `orca/forex-free-v4-i-family-2`, base `b123980016f5a036b624527ad7e29e8c34526cc8`.
Mechanical implementation of the frozen packet
`research/proposals/forex_free_v4/d1-a6-proposals/PROPOSAL_FXFV4-A6-P2.json`
under the BINDING directives in
`research/control/forex_free_v4_run/selection_freeze.json`
(`implementation_directives_from_audits`) and the A9-F findings
(`research/audits/forex_free_v4/a9_f_feasibility_v4.json`, FXFV4-A6-P2).
No V3 frozen file was modified; nothing scored ran on real data.

## Files (all new, this lane only)

| file | content |
|---|---|
| `research/assets/forex_free_v4/__init__.py` | V4 family-package namespace |
| `research/assets/forex_free_v4/family2.py` | the family module (V4 namespace, mirrors the V3 family-module discovery pattern / `run_arm` contract) |
| `tests/assets/forex_free_v4/__init__.py` | test package |
| `tests/assets/forex_free_v4/test_family2.py` | 37 tests, synthetic fixtures only |
| `research/assets/forex_free_v4/AMBIGUITIES.md` | recorded ambiguities for A1 |
| `research/assets/forex_free_v4/FAMILY2_IMPLEMENTATION_NOTES.md` | this file |

## Packet field -> code map (`research/assets/forex_free_v4/family2.py`)

| packet field | code |
|---|---|
| events = RATE_CHANGE rows, delta != 0, of the DEDUPED ledger | `load_ledger_rows` -> `dedupe_ledger_rows` (last-row-wins by `(area, effective_date)`, file order) -> `extract_events` (delta != 0; missing availability stamp -> `unavailable`, reason `MISSING_AVAILABLE_TIME_EVIDENCE`, never read) |
| availability instant `a = operative_available_time_utc`, EVIDENCED stamps + conservative LATER bounds "exactly as the ledger carries them" | `Event.available_dt` read from `announcement.operative_available_time_utc` (no adjustment) |
| decision instant T = first completed 16:00 America/New_York flat bar with completion >= a (DST-aware; 20:00Z EDT / 21:00Z EST via zoneinfo) | `ny_decision_stamp` + `existing_decision_bars` + `first_bar_at_or_after`; decision bar must EXIST in the pair's snapshot |
| warmup: first decision before 2020-02-11 => NO_EVAL fail-closed, never backfilled | `NO_EVAL_CUTOFF_UTC`, counted in `meta.eligibility.no_eval_before_cutoff` |
| direction map: non-US area -> own pair, base/quote sign convention; US drives all 7 (long-USD on hike, flipped on cut) | `AREA_OWN_PAIR`, `PAIR_AREAS`, `US_HIKE_SIDE`, `mapped_directions` |
| entry: OPEN of the next session's 16:00-NY bar strictly after T (one-event lag); gap > 4 days => fail-closed NO_TRADE; missing bar => void | `_schedule_pair` (`MISSING_NEXT_FILL_BAR`, `FILL_LAG_EXCEEDS_4_DAYS`); a missing session between decision and fill shifts the fill to the next EXISTING bar (inherited V3 "next existing 16:00-NY bar" convention, inside the frozen 4-day allowance) |
| hold: anchor H = 10 NY-days; neighbour H = 10 hike / 3 cut (delta sign); control/bench H = 10 | `ANCHOR_HOLD_NY_DAYS`, `NEIGHBOUR_CUT_HOLD_NY_DAYS`, `hold_ny_days` |
| exit at the open of the 16:00-NY bar after the H-th completed NY-day following entry | the H-th EXISTING 16:00-NY bar after the entry bar, at its open (each snapshot bar completes one NY trading day; a holiday day is not a completed NY trading day and does not count) |
| missing/beyond-snapshot exit => earliest-scheduled exit, never fill-forward | exit at the latest existing bar before the scheduled instant (`earliest_scheduled_exit_data_end`); no such bar => `END_OF_DATA_NO_EXIT` (trade voided) |
| force-flat at internal fold boundaries; entry whose fill lands on the force-flat bar suppressed; no position crosses a boundary | `_force_flat_indices` (boundaries 2022-05-01, 2024-07-01; a boundary beyond the snapshot's last bar produces no force-flat bar), interception in `_schedule_pair` (`FOLD_BOUNDARY_NO_ENTRY`) |
| governor: max 1 position/pair, max 1 entry/pair/NY-day, blocked = NO_TRADE never deferred; tie-break earlier availability wins | position state in `_schedule_pair` (`no_refresh_ignored`); candidates sorted by `(decision_idx, available_dt, effective_date, area)` |
| control: frozen sham derangement mapping table | `SHAM_AREA` (packet `arms.control.sham_derangement_frozen.mapping` VERBATIM; see AMBIGUITIES for the `+3` rule-text discrepancy), direction re-expressed in the sham area's base/quote role; sham == US => full long-USD map |
| benchmark: anchor law, every availability instant +180 calendar days | `BENCHMARK_LAG_DAYS` in `run_arm(arm="benchmark_treatment")`; `bench_schedule_id = FXFV4-A6-P2-bench`; late events whose stale twin falls past the snapshot drop out (NO_DECISION_BAR_AVAILABLE), the A9-L2-accepted asymmetry |
| costs: F1-fixed tiers through the inherited P1 accounting kernel; tier 2.0 primary; delay stress separate, never blended | booking in `assemble_cell_record` / `stress_book` via `research.assets.forex_free_v3.accounting.book_dual / book_stress` (READ-ONLY import); `meta.delay_stress.carried_unblended` |
| dual book + financing formula (frozen verbatim), day-start as-of differential from the evidenced vintages | `_financing_adjustment` + `LedgerVintageReader`: vintages reconstructed from the SAME deduped ledger (BASELINE_LEVEL floor + every RATE_CHANGE step — BIS WS_CBPOL policy rates are piecewise constant), eligibility `available <= t AND effective <= t` at each UTC day-start in `[entry_date, exit_date)`; percent-per-annum -> decimals (/100) once at the boundary; missing read => `DataBlocked` |
| fold grid 2020-03-01 / 2022-05-01 / 2024-07-01 / end 2026-09-02; fold gates on POPULATED folds; purge 14 calendar days | `FOLD_BOUNDARIES`, `INTERNAL_BOUNDARIES`, `PURGE_DAYS`; `fold_of` mirrors kernel `fold_of` (entry-side purge + warmup region); exit-side purge per the packet's "entry OR exit inside a purge window" rule in `assemble_cell_record` (`purge_excluded_exit_side`) |
| margin-to-fail fields per Stage-A gate | `margin_to_fail` (distances: expectancy vs 0, PF vs 1.10, price-only no-inversion, positive populated folds vs 2-of-3, fold positive share vs 0.50, MDD vs 2500, pair concentration vs 0.40, USD-drift vs 0.30, dropout vs 6-of-8, incremental alpha vs 0, decisions vs 40), attached to every record from `assemble_cell_record` (which mirrors the runner's record structure and reuses the kernel's `stage_a_gates` READ-ONLY) |
| control preregistered non-reproduction rule | `family_control_gate` (expectancy > 0 AND pf >= 1.10, OR expectancy >= 0.5 x anchor) |

## data_paths contract (for the V4 runner / A1)

`data_paths = {"h1_dir": <authorized H1 snapshot dir>, "announcement_ledger": <path to the pinned v2 announcement_ledger.jsonl>}`.
`run_arm(arm, data_paths, macro_reader=None, freeze_token=None)` follows the inherited V3 family API (`macro_reader`/`freeze_token` accepted, unused: macro reads go through the pinned ledger; the runner owns scored/dry-run semantics). Schedule-only counting: `schedule_counts(data_paths)` (no PnL).

## Verification (this lane)

- `pytest tests/assets/forex_free_v4/test_family2.py -q` -> 37 passed (synthetic fixtures only).
- `pytest tests/assets/forex_free_v3/ -q` -> 95 passed, 2 skipped (data-dependent), 0 failures (V3 kernel untouched).
- `compileall` on both new trees: OK. No scored/PnL run on real data anywhere.
- A cross-check test pins this module's frozen constants to the V3 kernel's (read-only import) so the two can never drift.

## Limitations

- No scored runner exists yet in the V4 namespace: `assemble_cell_record` mirrors the runner record structure locally (booking through the inherited P1 kernel) but the V4 runner wiring, publication and scored/dry-run sanitization belong to the execution lane.
- The financing vintage series is reconstructed from the deduped ledger rather than read from `data_raw/forex_free_v3r_macro_evidenced/` (gitignored, absent here). For piecewise-constant policy rates the two are value-identical on every row the ledger pins; the ledger is the pinned, in-repo authority.
- The stress-tier / margin-to-fail tests book SYNTHETIC trade sets only (kernel-level); no real-data PnL exists or was computed.
