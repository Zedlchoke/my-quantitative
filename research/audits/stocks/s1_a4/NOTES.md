# S1 A4 — Session calendar US_EQUITY_REGULAR_V1 + corporate actions

Lane: A4 Stocks-S1 · Worktree: `.worktrees/stocks/s1-calendar` · Branch:
`orca/stocks-s1-calendar` · Base SHA: `a04b8d1b90a3cc079ddf6a726eea9cff86a0a9df`
· Frozen: 2026-09-02 · Synthetic goldens only, zero repo writes during tests.

## Deliverables

- `research/assets/stocks/calendar.py` — `US_EQUITY_REGULAR_V1`, implements the
  shared `research.assets.common.calendar.SessionCalendar` interface
  (calendar_id / is_session_day / holidays / session_bounds /
  early_close_cutoff_utc).  09:30–16:00 America/New_York via stdlib
  `zoneinfo` (DST-correct), embedded frozen holiday + half-day table
  2010-01-01..2030-12-31 (195 holidays, 45 half days at 13:00 ET, 4
  documented unscheduled closures).  Extras: `is_session`,
  `sessions_in_range`, `next_session`, `require_session`, `closure_reason`,
  `monthly_manifest_digest` / `annual_manifest_digest`,
  `calendar_manifest_digest` (sha256 of canonical frozen-table JSON),
  explicit pre/post-market phase flags (DISABLED in baseline scoring,
  fail closed unless enabled at construction), `classify_gap` /
  `assert_no_unexplained_gap` with `HaltInterval` (gap_ok_with_reason vs
  GAP_UNEXPLAINED; `synthetic_fill_allowed` is permanently False — halts
  explain, never fill).  Queries outside the table horizon raise
  `ValueError` (never guesses).  `NEEDS_PROVIDER_VERIFICATION` is exported.
- `research/assets/stocks/corporate_actions.py` — immutable
  `CorporateAction` records (ex/effective dates, validated), engine applies
  splits and cash dividends at the ex/effective timestamp (default:
  ex-date session open; explicit `effective_at_utc` must land on the
  ex-date ET), split factor (prices /ratio, shares ×ratio, value
  preserved), dividend cash = post-split shares × amount, EXPLICIT
  `price_adjustment_policy` (`RAW` fill path / `TOTAL_RETURN` research
  path; required kwarg, never implicit; missing previous close for a
  dividend adjustment fails closed), `reconcile_raw_vs_total_return`
  (per-event identity `(1+raw)·(cumC/cumP)−1` within tolerance; missing
  boundaries produce explicit fail-closed records, never silent passes),
  `classify_earnings_timestamp` → BTO/AMC with fail-closed `UNKNOWN`
  (inside regular session or non-session ET date, always with reason),
  `corporate_action_manifest_digest` (canonical sha256 over sorted
  records; order-independent, field-sensitive).
- Tests: `tests/assets/stocks/test_calendar.py` (54 tests),
  `tests/assets/stocks/test_corporate_actions.py` (30 tests) — 84 passed.

Acceptance (run from lane cwd with the shared venv):

```
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
  tests/assets/stocks/test_calendar.py tests/assets/stocks/test_corporate_actions.py -q
# 84 passed in ~1s; git status unchanged by the run (no __init__.py was
# created in either stocks package — those belong to another lane)
```

## Pinned golden digests

| artifact | sha256 |
|---|---|
| calendar manifest (frozen table, canonical JSON) | `028a7b21c9e306c7399467309d18e3ed696181682ca01f1e3170c21bdceb69ab` |
| corporate action manifest (TEST split+div records) | `2a1bc75c4df92716457edc14369debd83163e9546da54f724f0efd11008b4d10` |

Any change to the frozen table or the record schema changes these digests
and requires a new `CALENDAR_TABLE_VERSION` / new manifest (never in-place).

## Frozen-table derivation evidence

`generate_frozen_table.py` renders NYSE Rule 7.2 for 2010–2030 and
cross-checks documented annual session counts (all reproduced exactly:
2010=252, 2012=250 incl. 2 Sandy days, 2018=251 incl. Bush mourning,
2019=252, 2020=253, 2021=252, 2022=251, 2023=250, 2024=252, 2025=250 incl.
Carter mourning).  Full literal output: `frozen_table_evidence.txt`.
Key documented behaviors verified by goldens:

- 2024-07-03 early close 13:00 ET (17:00Z); 2024-07-04 / 2025-07-04 /
  2025-06-19 closures; 2022-06-20 first Juneteenth observance.
- DST goldens: 2024-03-08 EST 14:30–21:00Z vs 2024-03-11 EDT 13:30–20:00Z;
  2024-11-01 EDT vs 2024-11-04 EST.
- Saturday-New-Year's-Day is NOT observed (regular Friday Dec 31 sessions:
  2010-12-31, 2021-12-31, 2027-12-31), while Saturday Independence/Christmas
  ARE observed the preceding Friday (2015/2020/2026-07-03, 2010/2021-12-24)
  and Sunday holidays roll to Monday (2012-01-02, 2010/2021-07-05,
  2011/2016/2022-12-26, 2023-01-02).
- Unscheduled closures: 2012-10-29/30 (Sandy), 2018-12-05 (G.H.W. Bush
  national mourning), 2025-01-09 (J. Carter national mourning).

## NEEDS_PROVIDER_VERIFICATION (rule-derived, not yet on a published nyse.com calendar)

1. `2027-06-18` — first Juneteenth Saturday-observance (Jun 19 2027 is a
   Saturday); Friday observance assumed per Independence-Day Saturday
   precedents (2015-07-03, 2020-07-03).
2. `2027-07-05` — Independence Day Sunday-observance (precedents
   2010-07-05, 2021-07-05).
3. `2027-12-24` — Christmas Saturday-observance (precedents 2010-12-24,
   2021-12-24).
4. `2028-01-17 .. 2030-12-31` — all remaining 2028–2030 entries are
   rule-derived pending publication (early closes 07-03 / 11-24..29 /
   12-24 pattern, 2029 New Year entries, etc.).

Verify each against `https://www.nyse.com/trade/hours-calendars` when the
year is published; any drift = re-freeze a new table version + new calendar
manifest.  The pinned reference is per PLAN_stocks.md §2; `pandas_market_calendars`
and `exchange_calendars` were NOT imported (not installed; stdlib only).

## Assumptions / notes for integrators

- Half-day close is 13:00 ET as specified by the lane brief (nyse.com lists
  13:00 for the random-close-length program since 2021; earlier years also
  used 13:00 since the 1:00 p.m. convention predates the table window).
- Dividend total-return factor uses the CRSP-style proportional
  adjustment `1 − amount / previous_close`; raw fill path stays raw.
- Earnings exactly at the open classifies UNKNOWN (ambiguous boundary);
  exactly at/after the close is AMC.
- Reconciliation tolerance default 1e-9 (relative identity residual).
