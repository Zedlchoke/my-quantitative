# CONTINUE.md — STOCKS-FREE-V6 TERMINAL (BLOCKED_DATA_AUTHORITY) ENTRY STATE

Read `PLAN_stocks_v6.md` completely. It is the fresh-context Stocks
authority for any next stocks cycle; `PLAN_stocks.md` (V2/V2R/V3),
`PLAN_stocks_v4.md` and `PLAN_stocks_v5.md` are closed historical
authorities and are not rewritten.

## Verdict lineage (must agree with `research/wayfinder/MAP.md`)

- V2 effective verdict: `STOCKS_FREE_V1_REJECT_ALL` (canonical W1
  `106378230abecbaefff4248eeb373794f1b73038`), V3:
  `STOCKS_FREE_V3_REJECT_ALL` (W1 `586f9fe`), V4:
  `STOCKS_FREE_V4_REJECT_ALL` (A7T CONFIRMED, W1 `dfa099a`).
- V5 terminal verdict: `STOCKS_FREE_V5_REJECT_ALL` (A7T
  `STOCKS_FREE_V5_REJECT_ALL_CONFIRMED`, audit head `bc5827e`;
  `STOCKS_FREE_V5_W1 = 0ecca232caf6cee21a84d78579681e336b616388`).
- V6 terminal verdict: `STOCKS_FREE_V6_BLOCKED_DATA_AUTHORITY`
  (integration `orca/stocks-free-v6-integration`; terminal report
  `research/control/stocks_free_v6_run/terminal_report.json`). No scored
  cells: budget 0/6. Statistical denominator unchanged: 21 observed /
  21 published (V2 6 + V3 6 + V4 6 + V5 3). S1 SEALED_UNTOUCHED. No
  paper/live/orders. V6-owned workers zero.

## Why V6 closed blocked

The F1 remediation leg (P0a) PASSED: the V5 single-vintage collapse was
reproduced from store bytes on every declared number, the mechanism was
isolated (bridge single-vintage semantics; median newest-vintage cohort
15/40 filers; sanitizer/filer-coverage/window-edges CLEARED), the
multi-vintage PIT panel was rebuilt (pooled coverage e.g. us-gaap:Assets
0.946/0.985/0.998 at S0 start/mid/end; availability lag p50 121d p90
419d), and A1 froze 154/228 evaluated conditioning clocks as the fundable
set (`p0a_clock_freeze.json`).

The single-name price leg (P0b) FAILED CLOSED with evidence: Stooq serves
a JavaScript proof-of-work challenge to every scripted endpoint and its
rendering channel demonstrably corrupts series (TJX fails OHLC
consistency; no SEC-corroborated split signature), so it is
UNAVAILABLE_FAIL_CLOSED for hash-pinned scripted research use; Massive
Basic requires signup + API key under non-commercial terms =
CANDIDATE_NOT_AUTHORIZED (no signup performed). D1 proposals cannot be
truthfully invited without a PIT observable with EVIDENCED availability,
so the cycle closed blocked instead of scoring a degraded panel
(plan §2/§15). The owner decision request (compliant Stooq path /
owner-provided source / accept blocked close) was issued and remained
unanswered; the fail-closed default was applied.

## What V6 established (evidence, not sunk cost)

- The inherited PIT store is intact and hash-verified
  (sha256 f53eb371…df955; 3,817,158 records / 410 filers / 4,677 fields /
  643,610 multi-stamp vintage groups).
- F1 is fully diagnosed and remediated in artifacts: `p0a_f1_census_repro.json`,
  `p0a_multivintage_panel_manifest.json` (derived panel gitignored,
  sha256-pinned), `p0a_coverage_census.json`, `p0a_fundable_clocks.json`,
  `p0a_clock_freeze.json`. Any next stocks cycle inherits a READY
  fundamentals panel and a frozen clock list — the V5 blocker is dead.
- Price-leg evidence packet: `p0b_price_authority.json`,
  `p0b_license_evidence.json`, `p0b_availability_evidence.json`,
  `p0b_sample_probe_report.json`, `p0b_bulk_download_plan.json` (L7
  corporate-action cross-check caught the channel-integrity failure in
  the light phase).
- Owner GO "GO STOCKS V6 SCORED EXECUTION" was received 2026-09-04T23:40Z
  and is recorded as a STANDING Phase-E release (event_log
  OWNER_GO_RECEIVED): it satisfies the owner gate for any authorized
  continuation that completes the factory chain and passes independent
  A7 prelaunch. It does not waive any gate.

## Entry conditions for the next thread

1. Read `PLAN_stocks_v6.md` (closed authority for V6) and the cumulative
   forbidden inventory `research/control/stocks_free_v6_run/forbidden_family_inventory.json`.
2. Re-opening the price question needs an owner data-authority decision:
   authorize a compliant scripted-access path for Stooq, provide an
   owner-entitled source, or name a new registered candidate. Any new
   source passes the same gates (license capture, availability evidence,
   L7 cross-check, coverage census) before authorization.
3. Any next cycle needs a fresh owner plan (V7 or a price-authority
   remediation plan). The V6 clock freeze binds: proposals may cite only
   clocks in `p0a_clock_freeze.json`.
4. Heavy cap 1 on the 8 GB host; full pytest runs alone; one cycle = one
   A1 thread (L8); publish through the convention-pinned publisher (L9).
