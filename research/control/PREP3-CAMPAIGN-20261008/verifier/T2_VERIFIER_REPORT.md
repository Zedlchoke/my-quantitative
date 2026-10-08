# T2_VERIFIER_REPORT — PREP campaign turn 2 (2026-10-08)

Fresh-context, A7-class independent verifier. Saw nothing of the lanes' work; verified
from bytes, re-runs and own live probes only. Repaired nothing. PREP only: no
registration/GO/scored/S1/orders/purchases/push/merge performed. Write scope:
`research/control/PREP3-CAMPAIGN-20261008/verifier/T2_*` + `verifier/handoffs/handoff_VERIFIER_T2.json`.

## OVERALL VERDICT: **PASS_WITH_FINDINGS**

0 HIGH · 0 MEDIUM · 6 LOW/INFO findings (F-1..F-6 below). Every load-bearing claim of both
lanes verified against committed bytes, independently re-run, or independently re-measured
live against TWS. No fabricated number found; no weakened threshold found; no real-forecast
row exists anywhere; the Q1 block is intact and enforced.

Environment at verification start (C1): heavy lock `FREE_PROVEN`
(`research/researchctl.py locks inspect`; registry + flock both free); TWS paper port
127.0.0.1:7497 OPEN (7496/4001/4002 closed). Root main HEAD at start:
`d65880b615b31211d6b55dce9458cc59aef49946`.

---

## SUBJECT A — LANE H Q1-TIMING-FIX

Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-q1q2q3-prep/prep`,
branch `prep/futures-q1q2q3-prep-20261007`, HEAD `b8d52076231ad6d9f078739eaa66d6976074c910`
(== claimed lane commit; single parent `b143e917d4632776fbb5fdba92a2d7a1c589dc39` ==
dispatch; porcelain clean before and after all verifier activity).

### A1. Git + handoff sha256 — PASS
- Single clean commit; 76 changed files, ALL under `research/control/PREP-FUTURES-Q1Q2Q3-20261007/`
  (zero matches outside). All inside dispatch 32 allowed paths: `prospective/**`, `33_*`,
  `34_*`, `35_*.md`(+`.json`), `handoffs/handoff_Q1_TIMING_FIX_H.json`.
- Handoff `outputs{}`: 19/19 path sha256 recomputed from committed blobs via
  `git show b8d52076:<path> | shasum -a 256` — ALL MATCH (incl. q1_collector.py
  `ca5d0b96ae08f850…`, test_q1_collector.py `f7985681ff6e60b3…`, 35 md `85023a1c…`,
  35 json `736b17bc…`, manifest.jsonl `946eb6fe…`).
- Handoff schema `zcode_orch_v3_handoff@1` present; commit_sha null (self-referential;
  disclosed; lane G precedent).

### A2. Reproduction of Q1-TIMING-F1 — PASS
Verifier re-ran the harness itself (copied to /tmp so the committed log could not be
overwritten; the harness extracts blob 752adac3 via `git show` — working file untouched):
- `prospective/ops/repro_q1_timing_f1.py` run exit **0**; blob sha256 re-derived
  `18011a05b2c3eb66bed0f684d6c327f71672d63ef2fc9d2d234d9bc6899c7411` (matches handoff).
- F1(a) PROVEN: invocation 09:59:30 ET issues 2 FORECAST_ISSUED rows from a partial 09:59
  bar (rv30 computed from partial values; cutoff checks bar-START only).
- F1(b) PROVEN: 09:59:57 entry + 2×4 s fetch latency ⇒ forecast_made_at lands
  14:00:01Z/14:00:05Z — after the 10:00 ET boundary, no recheck.
- F1(c) PROVEN: NQ fetch failure after ES append strands `['ES']`; healthy restart ⇒
  `DUPLICATE_REFUSED`, NQ unrecoverable.
- `SYNTHETIC_LOGIC_ONLY` labels present in harness docstring + log. Verifier-regenerated
  log is byte-equivalent to committed `ops/repro_Q1-TIMING-F1.log` modulo real-wall-clock
  timestamps.

### A3. Fix code inspection — PASS (line numbers against commit b8d52076)
`prospective/q1_collector.py`:
- L112 `FORECAST_WINDOW_ET = ((10, 0, 0), (10, 5, 0))`; L819–824 `in_forecast_window`
  inclusive-start/exclusive-end on America/New_York (L59 `NY = ZoneInfo("America/New_York")`).
- L113 `BAR_COMPLETED_ET = (10, 0, 0)`; L827–838 `bar_completed_at` + `require_bar_completed`
  (`NOT_RUN_BAR_INCOMPLETE`) enforced at entry L888.
- L210 `CUTOFF_ET = tod_ns(10, 0)` unchanged; L921 fetch `end_et = et_wallclock(session_date,
  (10, 0, 0))` — no bar starting ≥10:00 can enter; L925 `cut_input_window` still refuses any
  ≥10:00:00 ET bar (L698–713, exit 6).
- L924 `data_arrival_at[sym]` at fetch return; L956 `bar_completed_at` row field;
  L958 `issue_deadline_et`; L985 single `forecast_made_at = now_utc_iso()` AFTER all fetches.
- Write-gate: L984 `require_before_deadline` BEFORE the forecast_made_at write;
  L995 `require_before_deadline` immediately before EVERY `append_ledger` (L841–852).
- Both-before-append: L902–915 + L916–980 build BOTH payloads in PHASE A (no append inside
  the loop); L988–993 duplicate pre-validation of BOTH rows; L994–996 append loop.
- Block: L114 `BLOCK_FILE = CTL / "COLLECTOR_BLOCKED.json"`; L855–864 `check_block_file`
  raises `NOT_RUN_BLOCKED_BY_FINDING` (exit 14, L117 `EXIT_BLOCKED = 14`); called at L872
  after prechecks, before any market access.
- observe_close: window constants (L107–108 area: OBSERVE_OPEN_ET 16:15 / OBSERVE_LATEST
  06:00 next day), MISSED bookkeeping logic unchanged. F-2 note below on its fetch format.
- Laws intact: full 176-line diff 752adac3→b8d52076 reviewed line-by-line; no change to
  verify_pins, precheck_lock, append_ledger (fsync+sha-chain), duplicate refusal (retained
  at entry L890–894 and strengthened at L988–993), redact, PACING_S, byte cap, BLS guard.

### A4. Test suite — PASS
Verifier re-ran the suite from `/Users/hoangminhlong/my-quantitative` venv against the
worktree files: **exit 0, "Ran 37 tests … OK"** (17.5 s; second confirmation run exit 0).
Worktree porcelain empty after both runs. Test diff 752adac3→b8d52076: only ADDITIONS —
new `T10WindowLaw` (5 tests: window constants, boundaries 09:59:59F/10:00:00T/10:04:59T/
10:05:00F, bar-completed precondition, deadline recheck, fire_utc = window start) and
`T11FixedForecastPath` (6 tests: block-file refusal, window-boundary invocations, deadline
expiry after both fetches appends ZERO rows with 2 fetch calls made, NQ-failure strands
nothing, restart duplicate idempotent, row timestamp fields). No tests removed. T7 body
made environment-agnostic (disclosed in handoff incident #3): re-read in full — all
fail-closed assertions (zero ledger rows, zero raw writes, terminal in ops+state,
next_fire_et, pins, script sha) hold in BOTH TWS-up and TWS-down branches.

### A5. Amendment draft 34 — PASS
`34_AMENDMENT_DRAFT_ISSUE_WINDOW.md` exists, titled and statused
**AMENDMENT_DRAFT_NOT_APPROVED** ("DRAFT — NOT APPROVED. NOT IN FORCE."), contains the
window-change table, the PIT section ("PIT law unchanged — the information set moves zero"),
the trial-accounting section ("Trial accounting impact: none… one-shot scoring condition
unchanged"), and the two-condition activation + Lead-only block deletion.

### A6. Parity 35 — PASS (with F-1, F-3, F-4 notes)
- §1 pin precedes results: §1.2 comparison-set rule verbatim, §1.4 metrics, §1.5 thresholds
  M1–M6 (each "per symbol"/"any …" as dispatched) all appear before §2 Results and §3
  verdict in `35_IBKR_DATABENTO_PARITY.md`.
- Verdict **BLOCK_PROSPECTIVE_PENDING_OWNER** present, fired by M4 only, with 3 owner
  options and the standing-block independence stated.
- Verifier INDEPENDENT recompute from the committed capture blobs (own RV30 implementation,
  later-anchored consecutive-pair log returns; not importing the lane module):
  - ES: 420/420 matched closes, median AND max rel diff = **0.0** (bit-exact claim TRUE);
    RV30 rel = 0.0 all sessions.
  - NQ: median close rel 0.0, max 3.2354e-05 (matches claimed 3.235e-05); max RV30 rel
    0.0143405 @ 2026-09-22 (matches claimed 1.434e-02 @ 2026-09-22); median RV30 rel — see F-1.
  - M4 fires under either median convention (both ≫ 1e-6) ⇒ verdict unaffected.
- Guards: results JSON scanned — 84 guard comparisons (28 session-symbols × G3/G1/G2),
  **0 flips**; G3 independently verified from captures (30/30 bars both sides, all 28);
  G1/G2 full-day re-fetch not re-executed by verifier (F-4).
- Capture integrity: manifest.jsonl 56 lines; **56/56 capture files re-hashed from
  committed blobs — all sha256 match**.
- Forbidden metrics: grep over 35 md/json + parity_results json — ΔR²/delta_R2, PnL,
  rest30-model appear ONLY as the declared prohibition lists ("FORBIDDEN and NOT computed",
  `"forbidden_and_not_computed": ["delta_R2","rest30_target_model_evaluation","pnl"]`).
  Zero computed values of any forbidden metric. Analytic bound through PINNED betas
  recomputed by verifier: ES 0.0 exact; NQ 0.008277996111545663 vs claimed
  0.008277996111545918 (log-Δ form; 15-significant-digit match); betas equal the committed
  `17_null_calibration_raw_v2.json` full_beta[3]/[4] exactly.
- NOT_RUN limitation recorded: §1.2 + §1.6 — 2021-03/2024-06 eras NOT_RUN (IBKR refuses
  expired chain contracts), Databento corpus ends 2026-09-30, single-Z6-era degradation
  recorded, not silently widened. Verifier re-verified the error-200 claim LIVE (own
  clientId 9416): months 202103/202406 ⇒ `Error 200: No security definition has been found
  for the request`, 0 candidates — matches.

### A7. endDateTime format defect (error 10314) — PASS
- Probe evidence committed: `ops/parity_probe_2026-10-08_useastern_format_rejected.json`
  (09:21:08Z, US/Eastern form, all probes 0 bars incl. current-contract walkback+retry) vs
  `ops/parity_probe_2026-10-08.json` (09:26:35Z, 60-bar mornings served) — see F-3.
- Verifier INDEPENDENT LIVE re-verification (own clientId 9415, readonly, same instant
  2026-10-07 10:00:00 ET = 14:00:00Z, ESZ6):
  - `"20261007 10:00:00 US/Eastern"` ⇒ **error 10314 verbatim** ("End Date/Time: The date,
    time, or time-zone entered is invalid…"), **0 bars**.
  - `"20261007-14:00:00"` (UTC dash) ⇒ **60 bars** (09:00–09:59 ET), zero errors.
- Fix is format-only: `ib_end_str(end_et) = end_et.astimezone(UTC).strftime("%Y%m%d-%H:%M:%S")`
  (L660–671); input `end_et` unchanged (`et_wallclock(session_date, (10,0,0))`, L921); same
  instant, DST-correct via zoneinfo. No timestamps-law change. Applied at 3 call sites
  (fetch helper L671, forecast raw-record L935, observe-close raw-record L1055) — see F-2.

### A8. Invariants — PASS
- `prospective/ledger_q1_prospective.jsonl` ABSENT (find over whole control dir: no file).
- `prospective/COLLECTOR_BLOCKED.json` sha256
  `2302f8d69d882c03975262e85b4e53a5b2c71e9045cce5392a2d9cabb27f6ed0` — byte-identical to
  the block commit `50456e0f` blob (recomputed both sides).
- `26_Q1_TRIAL_LOG.json` = `2ab92ae14caa3572c936483504da4d785226f69d4a916d173cdfa2e5894b8052`,
  `27_Q1_OOS_VAL_RESULTS.json` = `ad718b18caddbab9c3788c44be8692238c17cc509dc4b49d93d4b7972a3cf595`
  — both byte-identical to their `e2e651ac` blobs.
- No forecast row anywhere for today (or ever): ops_log.jsonl contains ZERO `FORECAST_ISSUED`
  events (6 events total: 3 rehearsal fail-closed/terminal, LANE_COMMIT, real-CLI
  `TERMINAL_FAIL_CLOSED NOT_RUN_BLOCKED_BY_FINDING` at 09:16:09Z, later rehearsal OK);
  COLLECTOR_STATE `mode=waiting, ledger_rows=0, next_fire_et=2026-10-09T14:00:00Z`;
  `grep -rl FORECAST_ISSUED` outside code/logs hits only docs (31/33/handoff) — no row.

### A9. Automation interlock — PASS (code side) / NOT_RUN-verifiable-by-config (prompt side)
- Block file exists at the path the collector and block file name:
  `<lane worktree>/research/control/PREP-FUTURES-Q1Q2Q3-20261007/prospective/COLLECTOR_BLOCKED.json`,
  sha `2302f8d6…` verified against block commit (above). Collector refuses (L855–864, exit
  14) — verified by code inspection, T11 test, and the recorded real-CLI refusal
  (ops_log TERMINAL_FAIL_CLOSED 09:16:09Z).
- The automation PROMPT-side check ("prompt also checks this file first and records the
  skip", per block file `unblock_effects`) cannot be verified from the repository — the
  automation config is Lead-side and outside verifier reach. Marked
  **NOT_RUN-verifiable-by-config**. The fail-closed path does not depend on the prompt:
  even if the automation fires, forecast_step refuses and records the skip.

---

## SUBJECT B — LANE I IBKR-CFD

Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-cfd-feasibility-prep/prep`,
branch `prep/futures-cfd-feasibility-20261008`, HEAD `8ba835e4e8a4e0bc54d18cc1c0a66035c6e08280`
(== claimed; single parent `211124d64c6ac78e9a634929b8df0fe4b177e5ab` == dispatch;
porcelain clean).

### B1. Git + handoff — PASS
Single clean commit; 19 changed files ALL under `research/control/PREP-FUTURES-CFD-FEASIBILITY-20261008/`.
Handoff outputs{}: 18/18 sha256 recomputed from committed blobs — ALL MATCH. Schema valid;
commit_sha deferred post-commit (disclosed; precedent-consistent) — resolves to 8ba835e4.

### B2. Raw captures manifest — PASS
`10_IBKR_RAW_MANIFEST.jsonl`: 8 entries; 8/8 sha256 recomputed from committed raw blobs
MATCH; 8/8 byte sizes MATCH (raw_bytes_total 123,919 ≤ 5,000,000 cap).

### B3. Read-only discipline — PASS
`ibkr_cfd_probe_I.py` full scan: NO placeOrder, whatIf, reqAccountUpdates, reqPositions,
reqAllOpenOrders, reqExecutions, reqIds, or any order/account/positions/execution endpoint
(the only grep hits are the docstring DECLARING them forbidden). Actual API surface:
connect(clientId, readonly=True), reqCurrentTime, reqContractDetails, reqMarketRule,
reqMarketDataType, reqMktData+cancelMktData, reqTickers, reqHistoricalData, disconnect.
Redaction: verifier pattern scan (`\bU\d{6,}\b`, `DU\d+`, `account*`, `[A-Z]{1,3}\d{4,}`
minus legitimate conIds/error-codes/years) over raw captures + artifacts — CLEAN;
manifest `redaction_applied=false` on all lines is accurate (nothing to redact).

### B4. Spot re-probe — PASS (live, by verifier)
TWS 7497 still OPEN at verification time. Verifier's own readonly connection (unique
clientIds 9413/9414, ≥3.5 s pacing, clean disconnect):
- IBUST100 CFD: **conId 111767885**, exchange SMART, multiplier **EMPTY (`''`)**, minTick
  **0.01**, minSize **1.0**, sizeIncrement 1.0, marketRuleIds "25".
- IBUS500 CFD: **conId 111767871**, same field shape.
All match the committed captures (`raw/contract_details_*.json`) and the handoff exactly.

### B5. Feasibility 09 — PASS
- Arithmetic recomputed: IBUST100 1 × 31,033.75 = $31,033.75 (310.3% of $10k); IBUS500
  1 × 7,782.00 = $7,782.00 (77.8%); IBUST100 margin-fit threshold ≤ 32.22%
  (10,000/31,033.75 = 32.224%) — all exact.
- Reference levels verified against raw bars: IBUST100 bar `2026-10-08T10:01:00+01:00`
  close = 31033.75 (exact); IBUS500 same bar close = 7782.0 (numeric equal to claimed
  7782.00; float formatting). Both bars are the LAST bar of each capture — consistent with
  "own 1-min BID bar close".
- Labels verbatim: `NOT_TRADEABILITY_CONCLUDED` (verdict), "Futures PnL does NOT convert to
  CFD PnL" (mandatory statement 1), `CONVENTION_ASSUMPTION_1TO1`, `REFERENCE_LEVEL_UNVERIFIED`
  all present; margin/commission/overnight financing = NOT_KNOWN with the by-measurement
  explanation; units affordable = NOT_COMPUTABLE.

### B6. Errors preserved verbatim — PASS
Quote-checked against artifacts AND the raw session log: error **10168** ×4 verbatim
("Requested market data is not subscribed. Delayed market data is not enabled."); **162** ×4
verbatim ("Historical Market Data Service error message:No historical market data for
IBUS500/CFD@UKBBO Last 60" + IBUST100 same shape); **10299** ×2 verbatim ("Expected what to
show is TRADES, please use that instead of AGGTRADES."); **200** ×4 ("No security definition
has been found for the request"). The 354-vs-10168 same-day variance (prior cancelled run
recorded 354) is disclosed in 08 §1 and the handoff — honest, not fabricated.

---

## SUBJECT C — CROSS

### C1. Lock + ports — MEASURED
Heavy lock FREE_PROVEN at start (verdict + evidence above). TWS ports: 7497 OPEN,
7496/4001/4002 closed. (Lane I's own 09:04:31Z measurement agrees.)

### C2. Heads, handoffs, no push — PASS
- Lane H HEAD `b8d52076231…` on `prep/futures-q1q2q3-prep-20261007`; Lane I HEAD
  `8ba835e4e8…` on `prep/futures-cfd-feasibility-20261008`; both porcelain-clean;
  re-measured unchanged at verification close.
- Both handoffs present, schema `zcode_orch_v3_handoff@1`, all required fields present.
- No push: lane branches exist ONLY as local `refs/heads/*` — zero `refs/remotes/*`
  entries match either branch name in either worktree or the shared root repo; remote refs
  predate these lanes (20261006 publication set). Root main untouched by lanes.

### C3. Language discipline — PASS
Scan over both lanes' committed artifacts for profitab/edge/alpha/tradeability claims:
only negations and constraint statements (e.g. 02_q2_power_repair.md's "cannot distinguish
edge from cost"; Lane I `minimum_tradable_size_units` = size granularity field). No lane
artifact calls Q1 profitable or a valid strategy, calls the amendment draft an edge, or
asserts CFD tradeability (`NOT_TRADEABILITY_CONCLUDED` present; "no tradeability or edge
conclusion" stated verbatim).

---

## FINDINGS

| id | severity | finding |
|---|---|---|
| F-1 | LOW | NQ "median" RV30 rel is the **upper-middle element** (index `len//2` of 14 sorted values) per `parity_q1_two_vendor.py` L223-225, not the interpolated median: claimed 2.099e-05; verifier's interpolated median **1.0494e-05** (7 of 14 sessions are exactly 0.0). The convention is not stated in 35 md. Both values exceed the pinned 1e-6 threshold by an order of magnitude ⇒ M4 fires and the verdict is identical under either convention. No effect on any gate. |
| F-2 | LOW | "observe_close unchanged" is true for its window/bookkeeping logic, but the endDateTime **format** fix necessarily touches observe_close's fetch call (3rd `ib_end_str` site, L1055) — else its fetches would fail-closed forever on TWS 176. Verified format-only/same-instant; no timestamps-law change. Precision note only. |
| F-3 | LOW | The committed serving probe JSON (`parity_probe_2026-10-08.json`, 09:26:35Z) records `endDateTime` in the OLD "US/Eastern" label format while showing 60 bars served; the committed probe script records `ib_end_str` (dash) strings — i.e. the serving JSON predates the final script text (uncommitted intermediate). Defect conclusion unaffected: verifier independently re-verified BOTH formats LIVE (error 10314 + 0 bars vs 60 bars, same instant). |
| F-4 | LOW | M5 "0 guard flips / 84" verified by scanning the results JSON (28×3, all agree) and G3 independently from captures (30/30 bars both sides, all 28); G1/G2 were NOT independently recomputed from raw full-day bars (full-day captures are not persisted; IBKR re-fetch not re-run by verifier). Non-load-bearing: M4 alone forces BLOCK_PROSPECTIVE_PENDING_OWNER. |
| F-5 | LOW | The rejected-format probe JSON records `n_bars: 0` without the 10314 error string (errorEvent not captured by that probe); the error-200 text for expired months is likewise asserted in §1.2 prose but absent from the committed probe JSON. Both claims independently re-verified LIVE by the verifier (10314 and 200 verbatim). Evidence-file completeness note only. |
| F-6 | INFO | Lane I handoff `commit_sha` deferred post-commit (field carries a pointer note); resolves to 8ba835e4e8a4e0bc54d18cc1c0a66035c6e08280. Precedent-consistent (lane G / turn-1 verifier). Also Lane I honestly discarded its cancelled prior attempt's evidence and re-executed everything (clientId 9211 → 9317; 354→10168 error-code shift disclosed). |

No fabricated numbers found anywhere: every numeric claim sampled recomputed exactly
(ES bit-exact, NQ maxima, analytic bound to 15 digits, $10k table, manifest sha chains,
block/trial-log/OOS blob equality). No weakened threshold (M1–M6 as dispatched; suite
assertions strengthened, none removed). No real-forecast row exists.

---

## Preconditions to lift the Q1 block (exact, per COLLECTOR_BLOCKED.json + 34 §activation)

1. **Owner approval of `34_AMENDMENT_DRAFT_ISSUE_WINDOW.md`** — explicit, owner-initiated
   turn (the draft is NOT_APPROVED and NOT IN FORCE; it changes owner-approved protocol
   28 §3 issuance mechanics).
2. **Independent fresh-context verifier confirmation** of the fix, tests and evidence —
   this T2 report is such a confirmation record for the current commit; any lift turn
   should re-verify HEAD at that time.
3. **The Lead (never a lane) deletes `research/control/PREP-FUTURES-Q1Q2Q3-20261007/prospective/COLLECTOR_BLOCKED.json`
   in a dedicated commit** (sha `2302f8d6…` today; re-hash before deleting).
4. First possible live issuance is then the next NY-session fire at the window start
   10:00:00 ET (`next_fire_et = 2026-10-09T14:00:00Z` at verification time); the first
   live in-progress-09:59-bar case remains `NOT_RUN_UNTIL_LIVE_FIRE_AFTER_OWNER_APPROVAL`.

Separately and additionally: the parity verdict
`BLOCK_PROSPECTIVE_PENDING_OWNER` (35 §3, fired by M4 NQ RV30 divergence) is an
INDEPENDENT owner decision on the vendor-reconciliation question (options 1–3 in 35 §3);
lifting the timing block does not by itself resolve the parity block.

— T2 fresh-context verifier, 2026-10-08
