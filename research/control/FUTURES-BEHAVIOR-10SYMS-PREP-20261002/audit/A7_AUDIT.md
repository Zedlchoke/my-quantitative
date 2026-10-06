# A7_AUDIT — FUTURES-BEHAVIOR-10SYMS-PREP-20261002

- **Lane:** A7-AUDIT (fresh-context independent auditor). READ-ONLY except `audit/` + `dispatch/handoff_A7.json`.
- **Audit date:** 2026-10-02 (UTC). Auditor script: `audit/recompute_headline.py` → `audit/recompute_headline.json` (my own fresh code; no lane analysis code reused).
- **Reference truth used:** `research/control/FUTURES-DATA-10SYMS-V1/` (root checkout, untracked snapshot): FINAL_REPORT.md, S1_IDENTITY.json (fetched_utc 2026-10-02T01:31:19Z), S6_FRONT_SPREADS.json, S9_INDEPENDENT_VERIFY.md; raw at `~/.my-quantitative-data/futures-10syms-v1/raw/` (read-only).

## Verdict

**PASS-WITH-FINDINGS. No BLOCKER.** The prep is honest, taxonomy-disciplined, reproducible where
reproducible, and clean of scored/PnL artifacts. Independent recomputation of 7 headline
descriptive groups (≈40 numbers) matches the dossiers exactly or to stated precision, with ONE
material exception (CL §3 return statistics — MAJOR M1). 4 MAJOR findings require fixes before
any backtest arm runs; none invalidates the prep task itself.

**Counts: BLOCKER 0 · MAJOR 4 · MINOR 5 · NOTE 4.**

## 1. Independent recomputation (my own script, raw data only)

| # | Dossier claim | Recomputed | Verdict |
|---|---|---|---|
| R1 | ES 5 declared-roll gaps +55.75/+58.75/+52.5/+61.75/+67.75 pts | +55.75 (2025-08-29), +58.75 (2025-11-28), +52.5 (2026-02-27), +61.75 (2026-05-29), +67.75 (2026-08-31) | **EXACT 5/5** |
| R2a | CL M2−M1 negative 280/280 days, median −$0.58 (2025-08-21→2026-10-01) | 280/280 negative, median −0.58, both-real-volume variant also 280/280; 280 real-volume front days in window | **EXACT** |
| R2b | CL 14 roll gaps median −$0.51, worst −$8.22 @2026-03-31 CLK6→CLM6 | 14 completed rolls, all negative, median −0.51, min −8.22 @2026-03-31; new/old volume ratio at rolls 0.148–0.339 (claimed 0.15–0.34) | **EXACT** |
| R2c | CL daily sd 3.17%/day | within-contract sd 3.047% (n=265); **stitched sample-sd over 279 consecutive-day returns = 3.166%** — reproduces the claim only when roll-boundary returns are included → MAJOR M1 | **MISMATCH (explained)** |
| R3a | SI 6 cycle-chain roll gaps +0.525/+0.725/+0.605/+0.495/+0.445/+0.770 $/oz | identical six values at identical sessions (2025-08-29, 2025-11-28, 2026-02-27, 2026-04-30, 2026-06-30, 2026-08-31) | **EXACT 6/6** |
| R3b | SI crash day 2026-01-30: o=98.355 l=74.000 c=78.530 v=173,244 n=123,771, −31.37%; peak close 115.505 @2026-01-26 | bar identical (h=101.375); prev close 114.43 → −31.373%; peak real-vol close 115.505 @2026-01-26 | **EXACT** |
| R4 | NG m1−m2 median −0.112, 75.2% negative, p10 −0.375 / p90 +0.345 (front era) | median −0.1115, 75.17% negative, p10 −0.375, p90 +0.345 (n=294 days, 2025-08-01→2026-10-01) | **EXACT** |
| R5a | GC real-volume era σ=1.61%/day (n=424, 2025-01-15→) | σ=1.6088% log, n=423 | **MATCH** (n±1) |
| R5b | GC 6 real-era cycle gaps +32.4/+37.3/+31.2/+31.0/+32.5/+27.5 | identical six values at 2025-09-30…2026-07-31; worst day −12.066% @2026-01-30 (claimed −12.07%) | **EXACT** (but see MINOR m2: a 7th roll completed in-snapshot) |
| R6a | 6J intervention days 2026-04-30 +2.48% (v 107,535), 2026-07-30 +2.75% (v 490,134) | +2.476%/+2.750% simple, volumes 107,535 / 490,134 exact (6JM6 / 6JU6) | **EXACT** (see NOTE n4 on log-vs-simple) |
| R6b | 6J quarterly roll gaps +109/+100/+92 ticks ($681.25/$625/$575) @2025-11-28/2026-02-27/2026-05-29 | +109.0/+100.0/+92.0 ticks at exactly those sessions | **EXACT** |
| R7 | Spread medians: ESZ6 last-20 = 1.0 tick (S6), NQZ6 = 6.5 (S6), NGX26 = 2.0 (S6), 6A 6AV6 = 4 ticks/$20 (n=95) | 1.0 / 6.5 / 2.0 ticks; 6AV6 median 0.0002 = 4.0 ticks over n=95 days (2026-05-18→2026-10-01) | **EXACT** |
| R8 | Contract specs vs S1_IDENTITY.json | all 10 multipliers/minTicks in dossiers AND `code/futbt/instruments.py` match S1 (NQ 20/0.25, ES 50/0.25, CL 1000/0.01, NG 10000/0.001, GC 100/0.1, SI 5000/0.005, 6E 125000/5e-5, 6J 12500000/5e-7=$6.25 tick, 6B 62500/1e-4, 6A 100000/5e-5); 6J USD-per-JPY orientation and SI 5000oz class asserted in code guards | **EXACT 10/10** |

Auditor artifacts: `audit/recompute_headline.py`, `audit/recompute_headline.json`.
Caveat on my own output: rows with `session: 2026-10-01` in the R1/R2/R3/R5 gap lists are
fetch-boundary artifacts of MY chain helper (active contracts' files end at the 2026-10-02
fetch, so later roll sessions are unreachable from their own bars). The completed-roll rows
(sessions ≤ 2026-09-30) are the authoritative comparison set quoted above.

## 2. Findings

### BLOCKER — none.

### MAJOR

**M1 — CL §3 return statistics are computed on stitched chain returns that include
roll-boundary gaps; undisclosed and inconsistent with the other nine dossiers.**
Evidence: `analysis/CL_behavior_stats.py` `ret_stats()` computes returns over consecutive
chain closes with no same-contract filter (source-verified); its output
`analysis/CL_behavior_stats.json` `return_stats` shows `n_returns: 279, sd: 0.03166` — the
dossier (CL_DOSSIER.md §3, "Daily sd 3.17%") prints this as the headline vol. My
recomputation: within-contract sd = 3.047%; stitched sample-sd = 3.166%. The synthetic
roll-day returns are large: 2026-03-31 stitched −9.45% vs the new contract's own same-day
market move −2.98% (6.5pp of the "return" is the −8.22 calendar gap); 2026-04-30 stitched
−7.24% vs own −0.97%; 2026-07-31 stitched −2.51% vs own **+0.85%** (sign flip). Skew
(−0.365), excess kurtosis (2.17), fat-tail shares (|r|>3% 24.7%, >5% 10.4%), weekday |ret|
table and autocorrelations in §3 are contaminated the same way. Every other dossier
(NQ/ES/NG/GC/SI/6E/6J/6B/6A) explicitly uses within-contract returns with roll-day returns
excluded/skipped; the CL dossier does not disclose the stitched convention (it says only
"Simple returns only"). Note: the separate claim "max |daily move| 11.7%" is legitimate —
their JSON min_date is 2026-04-08, a real crash day (−11.70%), not a roll artifact.
**Fix:** recompute CL §3 on within-contract returns (or disclose the stitched convention
and restate which stats include gaps) before these numbers feed any hypothesis design.

**M2 — Roll-rule basis fork: the engine/draft define the baseline on the LAST-TRADE month;
the NG dossier (and INTEGRATION_SUMMARY) treat the declared rule as infeasible on a
DELIVERY-month reading and implement a different chain.**
Evidence: `code/futbt/roll.py` (ExpiryMonthBasis.LAST_TRADE_DATE default; DELIVERY_MONTH
raises NOT_RUN) and `BACKTEST_LAUNCH_DRAFT.md` §0 ("expiry month = month of the contract's
last-trade date") — under this basis NG is feasible (e.g. NGX26 rolls at the last session
before 2026-10-01, i.e. 2026-09-30). NG_DOSSIER.md §1 instead declares the data-lane rule
"infeasible as written" (delivery-month reading; the front's last trade precedes the last
session of the prior month) and rolls its chain at each outgoing contract's FINAL session
(chain holds NGX26 through 2026-10-28 — ~1 month more exposure per contract than the engine
baseline). INTEGRATION_SUMMARY.md §1.1 endorses "NG: declared rule infeasible outright".
The data lane's authoritative S9 C3 is about field naming, not the rule basis; the engine's
chain and the NG dossier's chain are materially different objects and the divergence is
nowhere reconciled. **Fix:** pick one authoritative basis (or an explicit per-symbol
override table) and align draft §0, roll.py docs, NG dossier, and INTEGRATION_SUMMARY
before any Arm A/B construction.

**M3 — "Close-only bars can never fill" is enforced only for ENTRY fills; exit and roll-leg
fills can execute on settlement-derived bars.**
Evidence: `code/futbt/engine.py` guards only the pending-entry path (`if not
bar.is_close_only:` → ORDER_LAPSED_CLOSE_ONLY_BAR, engine.py ~line 235). TP/SL intrabar
exits, TIME exits, MANUAL exits and both roll legs call `exec_cost()` and emit
`journal.FillRecord` without any close-only check; `journal.FillRecord` carries no
`is_close_only` field (the guarded `accounting.Fill` dataclass exists but the engine never
uses it). On a close-only bar h=l=c=settlement, so a TP/SL level beyond the settlement close
cannot be "hit" — but a level at/beyond it WILL book an intrabar fill at a settlement price,
and roll legs routinely execute at the new contract's settlement-derived close in the deep
era. BACKTEST_LAUNCH_DRAFT.md §3 states the law unconditionally ("Close-only bars can never
fill (orders lapse with reason recorded)"); no test covers exits on close-only bars
(test_engine.py:205 covers entry only; test_accounting.py:62 covers the unused Fill class).
Practical exposure in the 2025+ real-volume window is limited (held contracts mostly have
real bars), but deep-era replays and thin post-roll windows can hit it. **Fix:** propagate
`is_close_only` into every fill path (or document and test a settlement-auction exception)
before Arm B.

**M4 — NYMEX delivery-month convention stated incorrectly in two documents (contradicting
S9 C3, the raw data, and their own usage).**
Evidence: S9_INDEPENDENT_VERIFY.md C3 (authoritative): raw `expiry_month` holds
lastTradeDate, "which for CL/NG is one month before the delivery month implied by the
localSymbol code" — i.e. **delivery month = letter-code month**. Raw confirms: CLX6 (X=Nov)
LTD 2026-10-20 = 3 business days before Oct 25 (month prior to Nov delivery); CLV6 (V=Oct)
LTD 2026-09-22 (3 bus. days before Sep 25); NGX26 LTD 2026-10-28 = 3rd-last business day of
Oct (all computed from headers, `audit/recompute_headline.json` R8). But CL_DOSSIER.md
§Conventions states "delivery month = month after the localSymbol month code (X = Nov)"
(which would make CLX6 a December delivery) — contradicting its own "29 contiguous delivery
months 2025-10…2028-02" (letter months) — and DATA_ACQUISITION_SPEC.md §4 repeats "for CL/NG
the delivery month is the month after the letter-code month" in the section that instructs
the paid Databento pilot to "keep delivery-month logic on our side". NG_DOSSIER.md gets it
right ("localSymbol letter = delivery month; raw expiry_month holds lastTradeDate, one month
earlier"), as does 6A. **Fix:** one-sentence corrections in CL_DOSSIER.md and
DATA_ACQUISITION_SPEC.md §4 before the pilot spec is acted on.

### MINOR

**m1 — NG curve-shape label error.** NG_DOSSIER.md §3: "m1−m2 … 75.2% of days negative
(backwardated)" — negative m1−m2 (near below far) is contango-shaped (deferred premium);
the dossier's own seasonality bullet calls the same negative medians "autumn/spring
contango", and mid-winter positive medians "backwardation". Echoed in
INTEGRATION_SUMMARY.md §1.3 ("NG seasonal flip (m1−m2 75% backwardated)"). Numbers
verified correct (R4); the word is wrong in both places.

**m2 — GC real-era roll count understated by one.** GC_DOSSIER.md §3 reports "six real-era
cycle rolls" (+32.4…+27.5). A seventh completed inside the snapshot: GCV6→GCZ6 at
2026-09-30, gap +31.1 USD/oz, old leg 245 lots (real volume) — consistent with the
contango conclusion and with the dossier's own event-calendar note that GCV6's roll
occurred 2026-09-30. Recomputed in `audit/recompute_headline.json` R5.

**m3 — Chain-length framing mixes definitions.** INTEGRATION_SUMMARY.md §1.4: "True-volume
front chains are 13.5–16 months only (2025-05/08/09→now)" — this is the coverage-manifest
calendar-run definition; GC_DOSSIER.md claims real-volume from 2025-01-15 (≈21 months,
424 returns, cycle-skip chain) and 6J from 2025-05-20 (quarterly chain). The summary's
range silently uses the narrower definition; a reader comparing artifacts will see
inconsistent starts. Add a definitional footnote.

**m4 — Vendor-claim citation precision.** DATA_ACQUISITION_SPEC.md §8.3 attributes "bulk
NDFD from 2020-04-16 to present" to https://registry.opendata.aws/noaa-ndfd — the live
registry page does not state that date (it lives in NODD documentation elsewhere); the
spec's "search-verified" label is honest but the citation should point at the page carrying
the date. Separately, I could not independently re-render the Databento catalog page
(JS-only render; only the word "Databento" served to my fetcher), so "Available from
2010-06-06 UTC", the schema list and the tier prices could not be re-verified in this
audit session — no evidence of fabrication (internally consistent, plausible, and the spec
pins access dates), but Phase 0 must re-confirm them against the API before any spend.

**m5 — 6J intervention-day return convention slip.** 6J_DOSSIER.md §3 declares
within-contract **log** returns but quotes +2.48% / +2.75% for 2026-04-30 / 2026-07-30,
which are the **simple** returns (log: 2.44% / 2.71%). Volumes and roll gaps exact (R6).

### NOTE

**n1 —** `code/futbt/engine.py` ~line 270: typo "NOT fabricatad" (comment only).

**n2 —** Taxonomy discipline is good across all 10 dossiers: POSTULATED/NOT_RUN used
consistently; no inferred PASS found; corpus-1200 reuse explicitly NOT_RUN/disclaimed in
every §5; no invented costs anywhere (slippage NOT_RUN_NO_DECLARED_VALUE; exchange fees
NOT_RUN 9/10 with cost_incomplete stamping in `code/futbt/costs.py`).

**n3 —** No scored/PnL artifacts: greps for sharpe/sortino/win-rate/profit-factor/CAGR/
total-PnL across `analysis/`, `dossiers/`, `data/`, and the three control docs return only
"no PnL" disclaimers; `journal.summary()` returns counts only ("no performance metrics in
prep"); PnL fields exist solely as engine machinery fields (gross/net per trade) exercised
on synthetic fixtures in tests.

**n4 —** Prep-code laws verified in source and tests (beyond M3): PIT enforcement
(PITDataView.FutureAccessError; feature as-of validation in journal.py; truncation +
future-mutation hooks, engine.py `_mutate_future` + walkforward asserts); roll decisions
use only past info (CalendarRollRule schedule-only; VolumeRollRule cutoff_lag ≥ 1,
same-day final volume refused by PolicyError); negative-CL handling (log_return raises on
non-positive; arithmetic pnl; ratio adjustment refuses non-positive); 6J orientation
(SIXJ_PRICE_BAND guard + InstrumentSpec tick-value guard $6.25); tick rounding via Decimal;
AMBIGUOUS_ORDER (engine books worst-case bound, journal refuses point PnL,
scenario_bounds stored); no fold suppression (ALLOWED_DROP_REASONS =
{INSUFFICIENT_COVERAGE}); additive attribution forbidden (guard raises; leave-one-leg/rule
via full-path re-runs); cost components provenance-tagged. Test suite:
**140 tests, OK, ~1.7s** (`python -m unittest discover -s tests -t .`, recorded 2026-10-02).

## 3. Scope checklist results

1. **All 10 dossiers** read in full. Framework coverage (§7 in each dossier vs
   00_MASTER_FRAMEWORK §1's 10 questions + per-symbol checklists) is present and honestly
   classed in all 10; FACT claims carry primary-source URL + access date (2026-10-02) with
   secondary-vendor sources explicitly demoted (FACT[secondary-vendor]); OBSERVED claims
   cite script + window. Contract specs correct vs S1 in all 10 (R8). Roll/curve/cost
   statements internally consistent EXCEPT M1 (CL stats), M2 (NG rule basis), M4 (CL/NG
   delivery-month sentence), m1 (NG label).
2. **Recomputation:** 7 groups / ~40 numbers (section 1) — 1 material mismatch (M1),
   everything else exact or to stated precision.
3. **Prep code + tests:** 140/140 OK; law-by-law source audit in n4; one law partially
   unenforced (M3).
4. **DATA_ACQUISITION_SPEC + COVERAGE_MANIFEST:** no fabricated prices/dates found;
   the 2010-06-06 caveat is present and explicit ("CRITICAL CAVEAT … does NOT prove any
   specific schema × symbol covers from that date"); Phase-0 free verification gates every
   spend; no credentials/purchases. Coverage manifest is OBSERVED-based and internally
   consistent with `analysis/engine_adapter_smoke.json` (spot-checked 6A/6B/6E/6J/CL/ES
   close-only fractions and contract counts). Citation nits: m4.
5. **BACKTEST_LAUNCH_DRAFT:** explicitly "DRAFT — NOT A GO"; admission bars (§6) and pass
   bars (§7, all 15 framework tests) stated; multiple-testing structure sane and explicit
   (cell-count formula 180·R·K + baselines + full-path ablations; never-additive;
   IN_SAMPLE_MASQUERADE guard). No self-granted GO anywhere.
6. **INTEGRATION_SUMMARY cross-check:** roll-defect claims per symbol verified against
   dossiers (9/10 union correct — CL is the non-counted symbol; FX+SI serial trap, NG
   infeasibility per M2's fork, ES/NQ/GC/6A timing group with 6A double-listed but union
   correct); serial-hole lists match dossiers exactly (GC 6 / 6J 8 / 6B all expired
   serials / 6A 6); S6 SI correction verified against S6_FRONT_SPREADS.json (SI front =
   dead serial SIV6, 4.5 ticks/$112.5) — SI liquid-era proxy $100 consistent with SI
   dossier; time-critical re-fetch dates match 6A dossier (6AF6/6AG6 age out ~Jan–Mar
   2027); spot-verified cross-claims 6JX6=26 lots and SIV6 max=944 vs raw — exact;
   "140 offline tests green" matches. Residual: m1 echo, m3 framing.
7. **Ownership:** `git -C worktree status` → only
   `?? research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/`; branch
   `prep/futures-behavior-10syms-20261002` at base_head `1f61b489…` (matches
   DISPATCH_MANIFEST). No other lanes touched; no ledger/registry writes; all 12 lane
   handoffs present, schema `zcode_orch_v3_handoff@1`, status COMPLETE, required fields
   valid. Raw data untouched (read-only reads only).

## 4. Artifacts

- `audit/recompute_headline.py` — auditor recomputation script (fresh, ~350 lines).
- `audit/recompute_headline.json` — raw output incl. all variant computations.
- `audit/A7_AUDIT.md` — this report.
- `dispatch/handoff_A7.json` — handoff (zcode_orch_v3_handoff@1).

---

# DELTA AUDIT — 2026-10-02 (fix verification, lane FIX-A7-FINDINGS)

Inputs: `audit/FIX_LOG.md` (implementer disclosure) + direct inspection/recomputation of every
touched file. Test suite re-run by auditor: **`Ran 147 tests … OK` (~1.7 s)** — matches the
claimed 140 original + 7 new close-only regressions. Git state unchanged (only this task
namespace untracked, correct branch at base_head `1f61b489…`).

## Delta verdict: ALL FIXES VERIFIED — M1-M4, m1-m5, n1 all VERIFIED; 0 new findings

| Finding | Status | Evidence |
|---|---|---|
| **M1** CL stitched-returns stats | **VERIFIED** | (a) `analysis/CL_behavior_stats.py` now has `within_contract_returns()` (returns whose consecutive closes switch contract are excluded and recorded); `ret_stats`, rolling-20d vol, dependence and weekday tables all use it; convention string in JSON. (b) `analysis/CL_behavior_stats.json` regenerated: `n_returns: 265, n_roll_boundary_returns_excluded: 14` (each excluded row lists session/from/to/stitched_ret), **sd 0.030528 sample — matches this auditor's independent within-contract recomputation exactly** (my population-sd 3.047%, n=265; 3.047×√(265/264)=3.0528); corrected skew −0.223, exkurt 2.296, tails 24.15%/9.06%, rolling-vol median 38.2%/max 93.6% @2026-04-09/last 42.4% @2026-09-30, dependence 0.194/0.019/0.000/−0.056; superseded stitched values preserved in `erratum_2026_10_02_M1`. (c) `dossiers/CL_DOSSIER.md` §3: ERRATUM blockquote quantifying every superseded→corrected value, corrected Volatility/Trend/Weekday bullets matching the JSON, honest disclosure that the original Trend text (+0.007/−0.003) matched neither the old nor new JSON, and the correct note that max \|daily move\| 11.7% (2026-04-08) was a genuine crash day. Largest excluded stitched returns disclosed (2026-04-01 −10.36%, 2026-05-01 −8.12%, 2026-08-03 −8.00%) — consistent with this auditor's roll-session-indexed variants (−9.45%/−7.24%/−2.51% incl. the 2026-07-31 sign flip), both indexing conventions reconciled in the erratum. |
| **M2** roll-rule basis fork | **VERIFIED** | Canonical basis (expiry month = LAST-TRADE month, raw `expiry_month` header; delivery-month reading retired) adopted in all four carriers: `code/futbt/roll.py` module docstring (CANONICAL BASIS paragraph, no behavior change — enum/default already implemented it), `BACKTEST_LAUNCH_DRAFT.md` §0 (canonical pin + NG consequence + pointer), `dossiers/NG_DOSSIER.md` §1 (rewritten CANONICAL BASIS paragraph + ERRATUM retiring "INFEASIBLE as written"; §4 next-roll row and §5 universe line updated), `INTEGRATION_SUMMARY.md` §1.1 (NG bullet replaced — feasible on canonical basis, re-classed as rule-vs-market divergence). The fix lane's NEW measured claim — "every expired NG/CL file is cut exactly AT the canonical roll session (12/12 each), except the most-recently-expired (NGV26 through 2026-09-29, CLV6 through 2026-09-23)" — was **independently recomputed by this auditor from raw**: exact match (NGV25…NGU26 and CLV5…CLU6 all cut at canonical sessions; NGV26 last bar 2026-09-29; CLV6 last bar 2026-09-23). Residual divergences are DISCLOSED, not silently merged: NGV26's last matured roll ~4 weeks later than canonical; live front NGX26 held to ~2026-10-28 by the lane's descriptive chain vs engine canonical roll 2026-09-30 — engine (canonical) is declared authoritative for any Arm A/B. |
| **M3** close-only fill law on exits | **VERIFIED** | `code/futbt/engine.py`: module docstring CLOSE-ONLY FILL LAW; `exec_cost(bar_is_close_only=…)` raises PolicyError (single choke point); TP/SL "NEVER on a close-only bar" (guarded before hit tests); TIME exit defers to next tradeable session (deferral counted); MANUAL exit defers to a pending exit filled at next tradeable open (`fill_timing="next_open"`, note recorded); roll legs execute only when BOTH old and new bars are tradeable (deferral note; RollEvent carries execution session + execution-session gap); FORCED_ROLL defers without a tradeable old bar; end-of-data censoring discloses never-executed roll/manual/time exits and computes unrealized on the HELD contract's bar (per-conid bar maps added). `code/futbt/journal.py`: `FillRecord.is_close_only_bar` refused structurally (`__post_init__` raises — a close-only fill cannot be constructed, so it can never enter a journal). Tests: `TestCloseOnlyNeverFills` — 7 new tests (test_engine.py:439-574: SL-never-on-close-only; TIME deferred; MANUAL deferred to next tradeable open; roll legs deferred; censoring when no tradeable bar returns; zero fills when the whole universe is close-only; FillRecord refusal). Auditor re-ran suite: 147 OK; `code/README.md`, draft §0/§8, INTEGRATION §4 counts updated to 147 with audit-M3 provenance. Typo fixed ("fabricated", engine.py:309 — also closes n1). |
| **M4** NYMEX delivery-month convention | **VERIFIED** | `dossiers/CL_DOSSIER.md` conventions line corrected + ERRATUM ("delivery month = the localSymbol month code's own month (X = Nov — CLX6 is the Nov-2026 delivery…)", now consistent with §7 Q10). `DATA_ACQUISITION_SPEC.md` §4: paragraph corrected with do-not-act-on-old-text warning — and BOTH errors fixed (delivery = letter-code month AND the roll-rule basis, cross-referenced to M2). `data/scripts/measure_coverage.py` `_caveats[0]` + regenerated `data/coverage_measured.json` string corrected (JSON re-validated by auditor — loads cleanly). `code/futbt/rawdata.py` `month_code` diagnostic comment corrected. `dossiers/NG_DOSSIER.md` was already correct (cross-referenced). All corrected statements match S9 C3 and this auditor's raw-LTD verification (R8). |
| **m1** NG curve label | **VERIFIED** | `dossiers/NG_DOSSIER.md` §3 curve bullet: negative m1−m2 now labeled contango-shaped (near at a discount to the deferred winter leg) with fix note; `INTEGRATION_SUMMARY.md` §1.3 echo corrected identically. Numbers unchanged (auditor R4 exact). |
| **m2** GC roll count | **VERIFIED** | `dossiers/GC_DOSSIER.md` §1 and §3: seventh real-era cycle roll added — GCV6→GCZ6 @2026-09-30, gap +31.1 USD/oz, old leg 245 lots — exactly this auditor's R5 recomputed values; fix note added. |
| **m3** chain-length definitional mix | **VERIFIED** | `INTEGRATION_SUMMARY.md` §1.4 definitional footnote: 13.5–16 months = coverage-manifest calendar-run definition; GC 2025-01-15 (~21 months, cycle-skip chain) and 6J 2025-05-20 (quarterly chain) are per-dossier eras on different constructions — "starts differ by definition, not by disagreement". |
| **m4** citation precision | **VERIFIED** | `DATA_ACQUISITION_SPEC.md` §8.3: 2020-04-16 no longer attributed to the registry page (not stated there; found via NODD/AWS docs) with re-verify-at-collection instruction; §2: JS-render re-verification note added (Databento facts rest on access-date-stamped lane fetches; Phase-0 steps 1–3 re-confirm). |
| **m5** 6J simple-vs-log | **VERIFIED** | `dossiers/6J_DOSSIER.md` §3: both intervention-day returns labeled SIMPLE (+2.48%/+2.75%) with log equivalents (+2.44%/+2.71%) — exactly the auditor's R6 values; 2026-07-31 echo tagged "simple". |
| **n1** typo | **VERIFIED** | engine.py:309 "NOT fabricated". |
| n2/n3/n4 | no action required | Positive audit findings; n4's single partially-unenforced law closed by M3. |

## Delta residuals (advisories, no action required from implementer)

1. `REPORT_VI.md` test-count residual (FIX_LOG residual #1): **already cleared** — the file
   now reads "147 test PASS (140 gốc + 7 regression close-only sau audit)" (updated outside
   the fix lane, evidently by the lead).
2. The disclosed-not-merged NG divergences (M2 residuals) remain by design: the NG
   dossier's descriptive chain holds the live front NGX26 to ~2026-10-28 while the engine
   canonical baseline rolled 2026-09-30. Correctly documented in NG §1; engine basis
   authoritative for backtests.
3. CL rolling-vol "last" is now as-of 2026-09-30 (the 2026-10-01 return is an excluded
   roll-boundary return) — disclosed in the dossier erratum.
4. This auditor's own `recompute_headline.json` caveat stands (fetch-boundary rows at
   2026-10-01 are artifacts of the auditor's chain helper, not data claims).

## New findings introduced by the fixes: NONE

Checked specifically: corrected CL numbers vs JSON and vs my recomputation (exact);
corrected CL weekday ordering vs JSON (Mon 2.52 > Wed 2.25 ≈ Tue 2.24 > Thu 2.21 > Fri
1.92 — matches); canonical-basis file-cut claim recomputed from raw (exact); new engine
deferral paths (no close-only fill constructible; zero-fills universe test);
coverage_measured.json still valid JSON; no writes outside the task namespace.

**Final cumulative counts after delta: BLOCKER 0 · MAJOR 0 (4 fixed/verified) ·
MINOR 0 (5 fixed/verified) · NOTE 4 (n1 fixed; n2–n4 positive findings / advisories).**

