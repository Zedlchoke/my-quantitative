# A7 TERMINAL AUDIT — DTP-FX-MECHCOURT-V1 (independent fresh-context, 2026-09-27)

## `CONFIRM_WITH_FINDINGS`

The close `DTP_FX_V1_BLOCKED_DATA_OR_COST` is CONFIRMED. All three per-mechanism
verdicts (A `F0_KILLED VETO_VARIANT_SAME_FAMILY`; B `BLOCKED_DATA`;
C `BLOCKED_DATA`) are lawful under plan §4's pre-registered priority order, all
load-bearing court citations verified against primary sources, the fix-window
census recomputed exactly from the input bytes with ZERO deltas, the sealed
plane untouched, and the trial ledger clean. Findings below are LOW/INFO only
and change no verdict, number, or law application. Per plan §8 the FAMILY_
FAILURES append row for A may now proceed.

Auditor: LANE A7, independent, no repairs performed, no other file touched.
Worktree HEAD measured at audit start: `895489ca3cdfc8dcad540bf2457ae4fe303456c1`
(branch `orca/dtp-fx-mechcourt-v1-integration`, status clean — verified, matches
the dispatch). This artifact computes only spread-cost quantities and counts.

---

## A7-F1 (LOW) — Row-134 veto-class label compressed in court §1.1

Evidence: SKEPTIC_court_REPORT.md §1.1 says the re-gate move is "the same move
the court killed as `VETO_VARIANT_SAME_FAMILY` in C1/C2/C3 (`FAMILY_FAILURES`
row 134)". Parsed row 134 (`TRACKA2-C1C2C3-REGATED-RANGEFADE`): `verdict_class`
= `SELECTION_REJECTION`, `primary_failure.code` = `VARIANT_SAME_FAMILY`. The
substance (re-gate of a dead family killed as a same-family variant) is
verified; the string `VETO_VARIANT_SAME_FAMILY` is the plan §4/DTP-master §2.3
vocabulary for the same kill shape, not row 134's literal `verdict_class`.
Advisory: cite the row's own code when quoting the precedent. No impact on A's
verdict, which rests on row 132 (verified verbatim) + DTP master §2.3.

## A7-F2 (LOW) — OWNER_PACKET drops the ±0.1 pip qualifier on "fix window = mid-month"

OWNER_PACKET: fix-window p50 "BẰNG giữa tháng". Measured (census + my
recompute): EURUSD equal (0.3 = 0.3 across 14–16L, all day-sets); GBPUSD p50
+0.1 vs MID at hours 14–15 (0.8 vs 0.7), equal at 16 (0.7); USDJPY +0.1 at
14–15 (0.5 vs 0.4) and at 16 (0.5 vs 0.4). VERDICT_assembly carries the honest
"bằng giữa tháng, ±0.1 pip"; the owner-facing packet compressed it to equality.
Materially the conclusion stands (fix window is NOT an expensive bucket:
rollover p50 1.0/2.3/1.6 pips is 2–4× the fix window; p90 flat). Advisory:
owner communications should retain the ±0.1 qualifier.

## A7-F3 (INFO) — Registry row `head` still at lane-start sha (expected mid-close state)

`plans/CYCLE_REGISTRY.json` row DTP-FX-MECHCOURT-V1: lifecycle ACTIVE_LIGHT,
budget 0/0, go_phrase REGISTERED_NOT_CONSUMED, worktree/branch match reality —
all verified. The row's `head` field = `051aaae0…` (lane start) while the
worktree HEAD = `895489ca…` (the cycle commit). This is the expected
pre-two-half-close state: plan §8 sequences the registry advance, FAMILY_
FAILURES append (correctly NOT yet present — 0 DTPFX rows in worktree or root)
and MAP/ledger stamps after this A7 confirm. Not an inconsistency; must be
advanced at close.

## A7-F4 (INFO) — Consensus-mention count nuance (no impact)

DATAPIT says 92/131 events mention consensus retrospectively in free text; my
grep counts 102/131 rows containing the token "consensus" anywhere — the delta
is rows whose `expected_vs_actual` reads "consensus null (not reconstructed)"
(negative mentions). The binding fact is unchanged and verified: no structured
consensus field exists in any row key (row keys enumerated: event_id, window,
event_type, event_time_utc, publication_time_utc, available_time_utc,
time_precision, expected_vs_actual, primary_source_url, source_class,
timestamp_basis, fetch_status, labels, one_line); zero rows mention revision.
Structured consensus/revision vintages ABSENT — B's blocker stands.

## A7-F5 (INFO) — DFV1 commit bb010bc9 is not the direct trace source for owner packet §0

Commit `bb010bc9` = DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 FINAL_REPORT (owner
simple-language, gate table G0–G7). The R1/R2/R3 steps in OWNER_PACKET §0 trace
instead to: broker probe `VERDICT_session2.md` (Manage Data Subscriptions /
funded-account share / Activity-Flex statement / TWS restart / socket 7497
Read-Only / minTick 0.5 pip — all verified verbatim in that file), EDQ1
`owner_packet_source_survey_2026-09-22.md` (TrueFX free-reg + verbatim TCU
capture; Dukascopy written-consent email; OANDA v20 practice; Polygon/Massive
runner-up; "successor probe 7–14 days FIRST (P1-bis)" — line 53), VIABILITY
class 8 (FOREX-NG6/NG7 F4 financing — R3), and plan §7 (R5). Every §0 claim
traces to a measured artifact; none found untraceable. Recorded so the trace
chain is documented precisely.

---

## CHECK 1 — Verdict-vs-law (plan §4 priority order) — PASS

Command: read plan §4/§8 + VERDICT_assembly.md + SKEPTIC_court_REPORT.md §0 +
trial_ledger.jsonl; compared each verdict class and justification to the
pre-registered space.

- A: recorded `F0_KILLED VETO_VARIANT_SAME_FAMILY` vs `TRACKA2-P4A-FIXCERT-01`
  + fallback note `(d) BLOCKED_FRONTIER_NOT_REOPENED`. Plan §4 freezes exactly
  this: expectation (a) vs FIXCERT, parkings route a skeleton-mismatch to (d).
  Priority order respected: (a) fires first; the census is frozen as unable to
  rescue A ("KHÔNG cứu A trong mọi kết cục") — the assembly honors this
  verbatim ("số đo KHÔNG cứu A").
- B: recorded `BLOCKED_DATA` primary with class-7 adjacency recorded as fence,
  not verdict — plan §4 expectation (b) and its "Secondary (ghi kèm, không
  phải verdict chính)" instruction, followed exactly. The court explicitly
  declined an F0 kill for B (no dead family's decision law is "enter FX on an
  observed intraday rates reaction") — the honest application of the priority
  order, not an inversion.
- C: recorded `BLOCKED_DATA` primary with kill-risk recorded secondary — plan
  §4 expectation (b), followed exactly; court's refusal to exercise (a) is
  reasoned (same-pair cross-venue law has no measured death).
- Total: `DTP_FX_V1_BLOCKED_DATA_OR_COST` — plan §4's pre-registered terminal
  for the all-blocked outcome. GO phrase dies UNCONSUMED — consistent with the
  registry (`REGISTERED_NOT_CONSUMED`).
- Ledger class strings for B/C (`BLOCKED_DATA_RATES_INTRADAY_ZERO_BYTES_…`,
  `BLOCKED_DATA_SECOND_VENUE_ZERO_BYTES`) are descriptive qualifiers of (b)
  whose reasons are exactly the plan §4 expected reasons — in-space.
- No verdict anywhere is justified by a reason outside the pre-registered
  space. The precision refinement "10/131 minute-exact" → "10/131
  FETCHED-verified (106/131 schedule-asserted EXACT; 84/131
  NOT_FETCHED_CANONICAL)" is disclosed in court §0/§4.1 and STRENGTHENS the
  blocker; it does not change the verdict class.

## CHECK 2 — Court citations vs primary sources (11 checked, all verified) — PASS

1. FAMILY_FAILURES row 132 (TRACKA2-P4A-FIXCERT-01): family_title "London
   fixing-window certainty premium (pre-fix z-gated drift into 16:00 fix)"
   verbatim; kill class `DECLARED_BAND_BELOW_MEASURED_COST` verbatim;
   `measured_summary` "Fix-window geometry is real but the harvestable band
   after taker costs is negative on the Dukascopy paper book" verbatim; RC
   "owner amendment with a NEW economic basis (cheaper measured execution or
   larger evidenced premium); parameter re-tunes are barred" verbatim. MATCH.
2. Rows 92–95 (FXNG4): pooled |rho| 0.8883 / 0.8908 / 0.8896 / 0.8896 vs
   `generic_dow_tue` — MATCH (court's four numbers exact); row 87 (FXNG3-A5-P2)
   0.8932 vs generic day-of-week — MATCH.
3. Row 100 (RATESNG1-A5-P1-ARM-AGGRESSIVE): clock-only shadow +94.16 vs +72.42
   — MATCH; "the edge belonged to the auction-release calendar geometry"
   verbatim in measured_summary. Rows 107–109 (COMMNG1): "bare release-clock
   control out-earned every anchor" verbatim — MATCH.
4. Rows 40/51 (sham-calendar kills): row 40 "+7-day SHAM-CALENDAR neighbour
   OUT-earned the anchor (+2.744 vs -2.608)" — MATCH; row 51 "+7d sham
   -4.067/trade ~= anchor -4.026 … the calendar conditioning carries NO
   incremental information" verbatim — MATCH.
5. Rows 56/83 (DGS10-level control deaths): row 56 "= 4.01x anchor (+4.93)"
   — MATCH; row 83 "CTL-DGS10LEVEL +4.134114/trade out-earns anchor -6.632352"
   + "the DGS10-level shadow remains the most lethal control in the forex
   program" — MATCH.
6. Row 138 (DTPCX1-I002): "median 17.8-62.8 bps … next-minute capturable
   window is median -0.245..0.000 bps" verbatim; 315,579 events @theta10 in
   secondary failure COST_DOMINATED — MATCH. Row 129 (XCONF): `V4_BLEND`,
   NOVELTY_VETO_PRE_PNL — MATCH (see A7-F1 for row 134 wording).
7. VIABILITY_cohort3_REPORT.md: class 5 fix-window/clock/calendar DEAD
   (FIXCERT + FXFV1-A3-P2 late-NY + FXNG3/NG4 + Q-7 RATESNG1/COMMNG1) —
   MATCH; class 7 DEAD 15 entries — MATCH; class 2 momentum DEAD
   (TRACKA2-P3B-DINV-1D 0.3032/0.3103) — MATCH; class 6 DEAD+FENCED; class 10
   UNCONSTRUCTIBLE/UNFUNDABLE-ARM VETO — MATCH; NO_CANDIDATE 0/12 — MATCH.
8. failres ledger (parsed independently by this lane, all 131 rows):
   FETCHED=10, NOT_FETCHED_CANONICAL=84, SEARCH_SURFACED_URL=22,
   SEARCH_SURFACED_TOPIC=12, other=3; time_precision EXACT=106/APPROX_MIN=5/
   APPROX_HOURS=20; source_class 110/12/9; labels `DIAGNOSTIC_OUTCOME_EXPOSED`
   + `FAILURE_ROOT_CAUSE_RESEARCH` + `EVENTS_OVERLAY_ONLY_NOT_CAUSAL_EVIDENCE`
   on header AND all 131 rows; the 10-event FETCHED list matches DATAPIT's list
   exactly; example `F1_US_CPI_20210113.available_time_utc =
   2020-12-01T00:00:00Z` verbatim. 10/131 honesty ceiling CONFIRMED.
9. Broker probe `VERDICT_session2.md`: "0 valid two-sided observations"
   verbatim; BID=-1/ASK=-1 UNSET ×5 pairs; "minTick = 0.00005 = 0.5 pip, all 5
   pairs"; `BLOCKED_BROKER_COST_AUTHORITY`; 8/10 components
   NOT_RUN/NOT_SUBSCRIBED (components 1,2,3,4,5,6,7,9) — ALL MATCH. I further
   parsed `sanitized_result_20260926T055513Z.json` myself: minTick 5e-05 ×5,
   n_valid=0, n_invalid=357, cells_with_obs=0 — CONFIRMED.
10. EDQ1 `CYCLE_VERDICT.md`: `BLOCKED_SOURCE_LICENSE` verbatim; 578,916 ticks;
    "no terms document governs `datafeed.dukascopy.com`"; Twelve Data no
    bid/ask — ALL MATCH.
11. MAP.md frontier rows (FREE-DATA-FRONTIER-V1R1 daily-only
    RETRIEVAL_TIME_ONLY; FOREX-INTRA-BIDASK-V1 BLOCKED_TRANSPORT;
    FX-FUTURES-FRONTIER-V1 BLOCKED_TRANSPORT) cited with correct line ranges —
    spot-verified present.

## CHECK 3 — Independent census recompute — PASS, ZERO DELTAS

Command: my own script `/tmp/a7_census_recompute.py` (separate implementation:
pyarrow column read + `datetime.astimezone(ZoneInfo("Europe/London"))`
bucketing + hand-written linear-interpolation percentile + numpy `percentile`
as a second engine), reading the same three parquets; compared every field of
`fixwindow_spread_census.json`.

Inputs (sha256, all MATCH the JSON `inputs` section):
- EURUSD `9fe9e4b1…c9f2bd`, 136,485 rows, 2021-01-03 22:15Z → 2026-09-23 23:45Z — MATCH
- GBPUSD `fe90677e…c11a978`, 137,135 rows, 2021-01-03 22:00Z → 2026-09-23 23:45Z — MATCH
- USDJPY `99e276df…da9de7c`, 137,376 rows, 2021-01-03 22:00Z → 2026-09-23 23:45Z — MATCH

Recompute table (p50/p90 pips, my recompute vs published JSON — delta = 0
everywhere; p25/p75/p99 also all exact, 59 published stat-nodes total):

| Pair | Bucket (London hour × set) | n (mine=JSON) | p50 | p90 | Δ |
|---|---|---|---|---|---|
| EURUSD | 13×ME1 / 14×ME1 / 15×ME1 / 16×ME1 / 17×ME1 | 232/232/232/232/231 | 0.3 (all) | 0.99/0.5/0.5/0.5/0.5 | 0 |
| EURUSD | 13×MID / 14×MID / 16×MID | 788/788/786 | 0.3 (all) | 0.8/0.5/0.5 | 0 |
| EURUSD | rollover 21–22UTC | 4159 | 1.0 | 4.1 | 0 |
| EURUSD | fixcert entry 14–15L ME1|ME2 / exit 16L | 942 / 470 | 0.3 / 0.3 | 0.5 / 0.5 | 0 |
| GBPUSD | 13×ME1 / 14×ME2 / 15×MID / 16×ME1 / 17×MID | 232/469/787/232/786 | 0.8/0.8/0.7/0.7/0.8 | 1.6/1.1/1.1/1.1/1.1 | 0 |
| GBPUSD | rollover 21–22UTC | 4249 | 2.3 | 8.1 | 0 |
| GBPUSD | fixcert entry / exit | 940 / 470 | 0.8 / 0.7 | 1.2 / 1.1 | 0 |
| USDJPY | 13×ME1 / 14×MID / 15×ME1 / 16×MID / 17×MID | 232/788/231/786/776 | 0.5/0.5/0.5/0.4/0.5 | 1.4/0.8/0.9/0.7/0.8 | 0 |
| USDJPY | rollover 21–22UTC | 3985 | 1.6 | 7.3 | 0 |
| USDJPY | fixcert entry / exit | 940 / 471 | 0.5 / 0.5 | 0.9 / 0.8 | 0 |

(Full per-bucket comparison executed for all 5 hours × 3 day-sets × 3 pairs +
3 rollover + 6 fixcert nodes; not all rows shown above — every field matched.)

Consistency checks:
- Day-set coverage: 69 months, ME1=69, ME2=138, MID=236 days per pair — MATCH.
- Published observations, non-overlapping scope (15 hour buckets + rollover
  per pair): 11,609 + 11,695 + 11,411 = **34,715** — matches DATAPIT/assembly/
  owner packet exactly. (JSON also contains the overlapping fixcert composites:
  38,948 counting those — arithmetic of both scopes verified.)
- `n_nonpos = 0` in every published bucket — zero non-positive spread claim
  CONFIRMED by my recompute (0 across all 38,948 observations).
- DST: zoneinfo conversions verified at 5 boundary instants
  (2026-03-29T01:00Z→02L BST; 2026-10-25T01:00Z→01L GMT; 2021-03-28→02L;
  2021-10-31→01L; 2023-06-15T14:00Z→15L) — MATCH; and my astimezone path
  reproducing the cycle's pandas tz_convert path bucket-for-bucket is itself a
  cross-engine DST agreement across 69 months of data.
- Census artifact hashes: fixwindow_spread_census.json =
  `15efee6ac2f58375fb47a22ca30389b3d85f155dec9d03ae7de19d7db5cf38e0`,
  fixwindow_census.py = `3c3b7b29cdc10b31b8dd5475cc8e616dec919d9e50d69c8d66d59
  0b573de9d6e` — both MATCH DATAPIT's pinned values.
- Scope guard: the script computes s_open percentiles and counts only. My
  recompute likewise computed no price/return/PnL statistic.

## CHECK 4 — Anti-variant check on A (independent judgment) — AGREES WITH COURT

Frozen FIXCERT definition (row 132 + SKEPTIC_F0_cohort2 §2.6, read directly):
trigger = final pre-fix hour into 16:00 London; gate |z|≥1.0 trailing-60-fix-
day pressure; direction = pressure sign; entry F−1h bar open; exit F bar open.
Variant (plan §2.1): trigger = pre-fix calendar window on month-end last
trading days; direction = sign of public price-history quantity (MTD return /
benchmark-weight rebalance estimate); exit = after fix.

DTP master §2.3 (read directly): two identities must differ in ≥2 of
(a) payer + payment-forcing mechanism, (b) information layer PIT (source +
observable), (c) risk shape (holding horizon, direction logic, risk
transferred); otherwise they are ONE identity.

My judgment, axis by axis:
- (a) payer: plan §2.1 itself declares benchmark mandates paying "spread +
  drift cho deadline certainty" — identical to FIXCERT's adjudicated payer
  (fix-benchmarked mandates, spread + pre-fix adverse drift, deadline
  certainty). NOT moved.
- (b) information layer PIT: FIXCERT direction = trailing pressure z from
  panel price history; variant direction = MTD return sign from panel price
  history (or a benchmark-weight rebalance estimate — public weights, same
  public/price-history layer, sign-supplying statistic swapped). NOT moved;
  even the most charitable reading moves this axis alone.
- (c) risk shape: both one-session hold, entry pre-fix, exit post-fix,
  sign-direction exposure, no horizon or risk-transferred change. NOT moved.

0/3 axes moved (< 2 required) ⇒ SAME identity ⇒ the month-end + MTD-direction
variant FAILS the anti-variant test and `F0_KILLED VETO_VARIANT_SAME_FAMILY`
is the lawful verdict. My independent conclusion AGREES with the court.

## CHECK 5 — Sealed/OOS safety — PASS

- grep of all cycle artifacts for `drift|pnl|return|premium`: every hit is a
  negative-scope declaration ("no price-drift, return, premium or PnL
  statistic…"), a verbatim dead-family definition quote ("pre-fix z-gated
  drift into 16:00 fix"), payer mechanism text ("pay spread + drift…"), the
  phrase "month-to-date return" as a mechanism definition (no computed value),
  or python `return` statements. NO computed price-drift/premium/return/PnL
  statistic anywhere in the cycle. Measured precedent numbers quoted by the
  court (+94.16, 4.01×, 17.8–62.8 bps, …) are citations of other cycles'
  committed failure records (failure memory), not new computations.
- trial_ledger.jsonl: exactly 3 rows (A1/B1/C1), all `ADJUDICATION_NOT_SCORED`,
  all `scored:false, pnl_computed:false, holdout_looks:0` — VERIFIED.
- AUDUSD/USDCAD: all mentions in the cycle dir are file listings, footer
  metadata, pinned cost-census citations (census/probe/plane_diff/manifest
  JSONs — cost quantities, not parquet rows), and sealed-window warnings. I
  independently confirmed the DATAPIT footer claims by parquet
  FOOTER-METADATA-ONLY reads (no row access): AUDUSD rows=30,420, footer span
  2021-01-03 23:00Z → 2026-06-30 20:00Z; USDCAD rows=30,386, footer max
  2026-06-30 23:00Z — MATCH. census_AUDUSD.json / census_USDCAD.json sha256
  match DATAPIT's pins (`d337ff2c…33473`, `27958f5a…35758`). Sealed 2026-H1
  rows present but unread — one-look lineage preserved. This auditor likewise
  opened no sealed row content.

## CHECK 6 — Registry consistency — PASS (see A7-F3 for the expected head lag)

- Root `plans/CYCLE_REGISTRY.json` row: lifecycle `ACTIVE_LIGHT`, budget
  used 0 / max 0, go_phrase `GO DTP FX MECHCOURT V1 SCORED EXECUTION` state
  `REGISTERED_NOT_CONSUMED`, s1 `SEALED_UNTOUCHED`, workers 0 — ALL MATCH the
  plan and reality.
- `git -C <worktree> rev-parse HEAD` = `895489ca3cdfc8dcad540bf2457ae4fe303456c1`
  = the dispatch sha; branch `orca/dtp-fx-mechcourt-v1-integration`; `git
  status --porcelain` clean before my two deliverables; log shows 895489ca
  (cycle G1–G3) on top of 051aaae0 (plan registration) — matches INTAKE.

## CHECK 7 — Owner packet accuracy — PASS (see A7-F2, A7-F5)

Section 0/1/2/3 claims traced: minTick 0.5 pip (VERDICT_session2.md V3 + my
parse of the sanitized JSON); R1 two steps + statement + 7497 read-only
(VERDICT_session2.md "Exact owner documents…" section, verbatim); R2 three
paths + 7–14-day probe (EDQ1 owner_packet_source_survey_2026-09-22.md, incl.
line 53; runner-up Polygon/Massive); R3 NG6/NG7 F4 (VIABILITY class 8);
census numbers p50 0.3/0.7–0.8/0.5 (recompute-verified, with the ±0.1 nuance
of A7-F2); 34,715 obs; rollover p99 7.8–16 pips; FIXCERT declared band
1.0–3.0 bps vs 6.2 bps stressed book (SKEPTIC_F0_cohort2 §2.6, verbatim:
"×2.0-stressed 4.0 pips ≈ 6.2 bps AUDUSD"); 245/245 forex trials 0 survivors
(MAP.md lines 308/737); 10/131 FETCHED (my parse); 0/357 valid obs/pair (my
parse). No untraceable number found.

## CHECK 8 — Refusal paths (steelman) — recorded verdicts stand in every case

- A alternative: `(d) BLOCKED_FRONTIER_NOT_REOPENED` — supportable if the
  benchmark-weight rebalance estimate were ruled a genuinely new information
  layer (skeleton mismatch). Why (a) remains correct: under DTP master §2.3 the
  identity moves at most 1/3 axes, short of the ≥2 required, so the strip test
  still collapses to the dead law; and the plan §4 parkings route any mismatch
  to (d) — either way A does not score and the terminal aggregate is
  unchanged. The alternative cannot rescue A.
- A alternative 2: `(b) BLOCKED_DATA` (PIT fix-flow layer absent per DATAPIT
  §8A) — would invert the pre-registered priority: (a) is checked first and
  fires; the plan explicitly froze A at (a) with the census unable to rescue.
  Refused.
- B alternative: `(a) F0_KILLED` via the DGS10-level/clock dominance precedents
  — supportable in spirit (twice-measured control-out-earned shape) but wrong
  under §4: no dead family's decision law is an intraday-observed-rates-
  reaction law (the 15 macro kills are daily-cadence release-direction/
  calendar/level families), and the plan froze B's expectation at (b) with the
  adjacency as secondary. (b) is byte-determined (0 intraday rates bytes;
  PIT ledger below floor by its own labels) and is the first violation in the
  priority order. The recorded (b) is strictly more honest than an (a) kill.
- C alternative: `(a) F0_KILLED` via Q-4 + DTPCX1-I002 fictional-lag — the
  payer story is arguably already measured-dead, but §4(a) requires an
  identity kill against a dead family row + class law; the same-pair
  cross-venue law has no measured death (the precedents are cross-pair/
  cross-asset objects — fences, not kills), and the plan froze C at (b).
  (b) stands, byte-determined (venue-2 = 0 bytes on every path; my parse of
  the sanitized probe JSON confirms 0/357).
- Aggregate: with all three blocked, plan §4 admits exactly one terminal —
  `DTP_FX_V1_BLOCKED_DATA_OR_COST`. `BLOCKED_FRONTIER_NOT_REOPENED` as the
  aggregate would be wrong (it is reserved for the case where mechanisms pass
  (a)–(c) but no reopener exists).

No ground for REFUSED exists: no post-hoc rationalization, no census-rescue of
A, no sealed-plane consumption, no priority-order inversion, no unverifiable
number load-bearing anywhere.

---

## Verdict authority claims (for HANDOFF_A7.json)

1. Close `DTP_FX_V1_BLOCKED_DATA_OR_COST` CONFIRMED; per-mechanism verdicts
   A/B/C confirmed as recorded; GO phrase dies UNCONSUMED.
2. Census reproduced exactly from bytes (0 deltas, 59/59 stat-nodes, 3/3
   input hashes, 34,715 non-overlapping published obs, 0 non-positive).
3. FAMILY_FAILURES append row for A (plan §8) is now authorized to proceed.

## Known limitations

- Citation audit covers 11 load-bearing citations + all row-level numbers I
  could enumerate; MAP.md line-range citations spot-checked, not re-read in
  full (their substance is independently confirmed by DATAPIT's byte checks).
- The recompute runs on the same input files at the same sha256; it validates
  the census as published, not the upstream Dukascopy derivation of bars15
  (out of scope for this cycle; the corpus is ancestry/cost-authority only).
- Footer-only parquet reads of the sealed ANC files were performed once by
  this lane (metadata statistics only; no row content, consistent with the
  dispatch allowance "metadata/footer only if needed").

— LANE A7 (independent-auditor), `a7-terminal`, 2026-09-27.
