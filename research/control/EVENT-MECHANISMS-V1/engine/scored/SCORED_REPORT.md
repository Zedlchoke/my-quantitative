# LANE E — SCORED EXECUTION REPORT — EVENT-MECHANISMS-V1 (2026-09-28)

Authority: owner GO **"GO EVENT MECHANISMS V1 SCORED EXECUTION"** typed
verbatim 2026-09-28, recorded `ROOT research/control/EVENT-MECHANISMS-V1/auth/
GO_RECORDED.json` (`match: EXACT_VERBATIM`, key_1 = A7 prelaunch AUTHORIZED,
key_2 = owner phrase at the cycle's own gate). Lane E consumed that GO and
computed **exactly the 3 GO-authorized cells** + the registered
control/baseline re-evaluations. No other arm, no parameter variation, no new
windows. Budget consumption: **3 of 6** (A2 cells NOT_RUN_THIN per
`G3_FREEZE_ADDENDUM_r3.md` F-ADJ-1 — never presented).

- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/event-mechanisms-v1/integration`,
  branch `orca/event-mechanisms-v1-integration`, HEAD `1978607785f306e7de050f934482a5adc042a77f`
  (asserted by the runner, fail-closed).
- Frozen artifacts untouched (G3_FREEZE + addenda r1/r2/r3, engine books):
  read-only consumption; every consumed book verified sha256 against the
  committed `.gz` bytes (byte-identical) before any arithmetic.
- Code: `engine/scoring/` (score.py, gates.py, run_scored.py) — clearly
  separated from the frozen book builder; tests in
  `engine/tests/test_scoring_fixtures.py`.
- Python: root `.venv` 3.12.

---

## 1. E0 — Machine-wide heavy lock (evidence: `scored/lock_evidence.json`)

Acquired via `research.governance.heavy_lock` (ROOT module) with
`cycle_id="EVENT-MECHANISMS-V1", role="scored-e"`; released in `finally`.

| step | evidence |
|---|---|
| before | `FREE_PROVEN` — "no registry row and the lock file is not flocked" |
| acquired | registry row: cycle EVENT-MECHANISMS-V1 / role scored-e / pid 95341 / status RUNNING / started 2026-09-28T00:57:38Z / command digest recorded / expected_artifacts = the three scored outputs |
| released | `FINISHED` — "scored 3 GO-authorized cells + controls; outputs written" |
| after | `FREE_PROVEN`; history tail row status FINISHED (append-only) |

Two earlier starts aborted **before computing any outcome** (fail-closed
guards — see §8 incidents E-I1); both released the lock FAILED per protocol.

## 2. Books consumed (read-only, fail-closed digests)

| book | sha256 (raw `.jsonl` = committed `.gz`, verified) | rows |
|---|---|---|
| a1_decisions.jsonl | `7e6b6a1dc603093a1ad1061295d8e27da8c7949ce91066b456e8adcf866532f3` | 41,444 (14,096 + 12,783 + 14,565) |
| control_a1_dateonly.jsonl | `96f63ae0bc835e539b5e9334d9127d26d931d2f624ce8e4235ed3a69de6ca443` | 55,023 |
| control_a1_permuted.jsonl | `a2a4332473469e67a8d24d5726e8e4e955448985b16004c671b955d9827c07fe` | 42,288 (3 × 14,096) |
| control_a1_clock_shadow.jsonl | `ade5e0ddf6a2c489b82aa121182080f459eebb066772679cf137160bc6e07971` | 10,389 |

Book invariants re-checked at load: directions ∈ {LONG, SHORT}; positive
finite prices; non-negative cost bands; record identity unique under
(control_variant, draw, event_id). Arm↔hold mapping asserted (anchor 5 /
N1 10 / N2 5); N2 records all S2-monitored; anchor/N1 records all
unmonitored buckets (S1/S3/S4; WKND measured 0, per the r3 AMB-1 census).

## 3. Scoring contract (dispatch E1; frozen cost law)

Per event, in return space on RAW prices already in the records:
`gross = direction × (exit/entry − 1)` (LONG: ratio−1; SHORT: 1−ratio);
`cost = (cost_entry_bps_x1 + cost_exit_bps_x1) × power / 10⁴` with power ∈
{1.0, 1.5, 2.0} read from `emv1.config.COST_STRESS_POWERS` — **two fills,
each costed exactly once** (entry at the Q-2 open band ×3.35, exit at the
midday/close basis ×1.0; bands by DV tier at entry: A/B/C = 10/15/25 bps).
`net = gross − cost`. Aggregates per arm, per fold (F1..F4), and pooled:
net expectancy per event (bps), PF = Σgains/Σ|losses| on net, counts.
Measured round-trip band at ×1.0 (anchor mix): **57.00 bps mean**
(band-C bound 108.75); at ×2.0: **114.00 bps measured** (bound 217.50).
Anchor DV mix: A 8,825 / B 3,532 / C 1,739.

## 4. THE THREE CELLS (all numbers bps per event; P-2 margins in §5)

| | **A1-ANCHOR** (H=5) | **A1-N1** (H=10) | **A1-N2** (S2, H=5) |
|---|---|---|---|
| events | 14,096 | 12,783 | 14,565 |
| folds F1/F2/F3/F4 | 3,679/4,013/2,553/3,851 | 3,392/3,665/2,319/3,407 | 4,873/4,778/2,633/2,281 |
| **net ×1.0** | **−66.0481** | **−61.9162** | **−91.2516** |
| PF ×1.0 | 0.7128 | 0.7956 | 0.6846 |
| net ×1.5 | −94.5479 | −90.6882 | −125.3259 |
| PF ×1.5 | 0.6167 | 0.7158 | 0.5954 |
| net ×2.0 | −123.0477 | −119.4602 | −159.4001 |
| PF ×2.0 | 0.5342 | 0.6445 | 0.5187 |
| gross ×1.0 | −9.0485 | (detail json) | −23.1031 |
| fold nets ×1.0 | −51.29/−72.46/−81.94/−62.93 | −41.98/−53.76/−107.06/−59.81 | −127.45/−76.26/−79.32/−59.09 |
| folds net-positive | **0 of 4** | **0 of 4** | **0 of 4** |
| delisting_exit records (scored, flagged) | 5 | 10 | 25 |
| **overall** | **KILLED_BY_PF_BAR_1X** | **KILLED_BY_PF_BAR_1X** | **KILLED_BY_PF_BAR_1X** |

Gross expectancy is already negative (anchor −9.05 bps): the directional
signal has no gross edge before costs; the open-band cost drag (~57 bps RT
mean) takes net to −66. N2's own preregistered prediction (S2 net ≈ 0 or
negative after costs) is **confirmed** (−91.25 bps) — consistent with the
clock mechanism's monitored-window claim, but the anchor itself fails, so
this does not rescue the identity.

## 5. Every bar with margin-to-fail (P-2; negative margin = bar FIRED)

Bar heights (Q-12 exclusion-zone statement, all preregistered): PF ≥ 1.10
at ×1.0 pooled; ≥3 of 4 folds net-positive at ×1.0; max single-name share of
|book net| ≤ 0.20; drop-one verdict-class survival; stress survival = net
expectancy > 0 at ×2.0; Band 1 ratio bar 0.50 (positive anchors only); Band 2
threshold = measured RT band at ×2.0 = 114.00 bps (band-C bound 217.50);
placebo reproduction bar 0.50 of anchor (r1 ILLIQ convention).

| bar | ANCHOR | N1 | N2 |
|---|---|---|---|
| PF_BAR_1X | **FIRED** (0.7128 vs 1.10, margin −0.3872) | **FIRED** (0.7956, −0.3044) | **FIRED** (0.6846, −0.4154) |
| FOLD_BAR | **FIRED** (0 pos, need ≥3, margin −3) | **FIRED** (0, −3) | **FIRED** (0, −3) |
| CONCENTRATION_BAR | pass (max 0.005576, margin +0.194424) | pass (0.003489, +0.196511) | pass (0.040228, +0.159772) |
| DROP_ONE_BAR | pass (class unchanged) | pass (class unchanged) | pass (class unchanged) |
| STRESS_BAR (net>0 @×2.0) | **FIRED** (−123.05 bps) | **FIRED** (−119.46) | **FIRED** (−159.40) |
| BAND1_DATEONLY | not adjudicable (anchor net ≤ 0; see §6) | — | — |
| BAND2_STRATA_SPREAD | **FIRED** (identity dies; see §6) | inherits | inherits |
| PERMUTED_PLACEBO | structurally non-informative — does NOT adjudicate (see §6) | — | — |

Concentration top-3 names (share of Σ|event net|): ANCHOR UPL 0.558% /
EPZM 0.275% / ASTS 0.272%; N1 CNR_OLD2 0.349% / EPZM 0.253% / TWST 0.239%;
N2 UPL 4.023% / WLL 0.217% / IMGN 0.215%. Drop-one (largest-|net| name
removed): ANCHOR (UPL) PF 0.7128→0.7033, net −66.05→−68.25; N1 (CNR_OLD2)
0.7956→0.8005, −61.92→−60.14; N2 (UPL) 0.6846→0.7343, −91.25→−71.68 — all
verdict classes unchanged. No bar outcome sits in a thin exclusion zone:
every fired bar misses by a wide margin (PF margins ≥ 0.30 PF-units; fold
deficit 3 folds; stress deficits ≥ 119 bps), and no passing bar is thin
except concentration (all ≤ 4.1% vs the 20% bar — comfortable).

## 6. Controls / baselines (re-evaluations)

- **Band 1 — date-only kill**: date-only anchor net **−69.7739** bps
  (n 28,739, PF 0.7241) vs anchor −66.0481 → descriptive ratio 1.0564 vs bar
  0.50. **NOT adjudicated**: r1 restricts Band 1 to positive anchors and the
  anchor is already dead by the PF/fold bars. (Date-only N1: −67.4134, PF
  0.7957, n 26,284.) The numbers, for the record: the date-only clock
  reproduces the anchor's (negative) result almost exactly — there is no
  acceptance-clock edge for Band 1 to find.
- **Band 2 — strata-spread (r1 canonical, GROSS basis)**: E[gross,
  unmonitored S1∪S3∪S4∪WKND] − E[gross, monitored S2] = −9.0485 −
  (−23.1031) = **+14.0546 bps ≤ 114.00 bps measured RT at ×2.0 → identity
  DIES** (margin −99.9447; also ≤ the 217.50 band-C bound). The unmonitored
  strata are *less bad* than the monitored strata by 14 bps gross — the
  direction the clock story predicts — but the spread does not clear even
  the doubled round-trip band: it is zero for decision purposes. (Net-basis
  spread reported alongside: +25.2035 bps.)
- **Permuted-acceptance placebo ×3 (seed 20260927)**: **STRUCTURALLY
  NON-INFORMATIVE — SCORING-TIME FINDING (E-P1, §8).** Each draw reproduces
  the anchor's net expectancy to machine precision (−66.0481, ratio 1.0000):
  the frozen shuffle permutes stamps *within issuer×form×year*, folds are
  year-aligned, and every scored field is a deterministic function of
  (ticker, stamp, hold) — so the (ticker, stamp) multiset is preserved
  (verified) and the booked-record multiset of every draw is EXACTLY the
  anchor's (verified: equality of multisets over ticker/entry_session/
  entry_price/exit_price/direction/fold). Every aggregate is therefore
  invariant BY CONSTRUCTION; Q-11 ("a null must move the signal") can never
  be asked. The placebo is recorded as **not adjudicable** — it is NOT
  evidence that the clock is noise, and NOT a kill. Re-specification
  (owner/A1; e.g., a shuffle that moves stamps across the scored-function
  groups) is required before any placebo-based clock adjudication.
- **Clock-only shadow** (n 10,389): net **−76.5758** bps at ×1.0 (−145.2718
  at ×2.0); **gross −7.8798** (mean RT 68.696). Diagnostic reading: pure
  stratum-clock conditioning carries gross ≈ −7.9 bps, indistinguishable
  from the anchor's −9.05 bps gross — the event payload adds ≈ 1.2 bps gross
  over the clock alone, and both are far below any cost hurdle.
- **Baseline — buy-and-hold equal-weight cohort** (context only): pooled
  **−34.4401** bps; per fold F1 −25.0322 / F2 −74.1725 / F3 −25.7962 /
  F4 −7.7546. The cohort itself is cost-negative; the event-direction rule
  (−66.05) is *worse* than naive buy-and-hold.

## 7. Verdict

**The EMV1-A1-FILINGFLOW-ACC identity is DEAD on the merits.** All 3 cells
fail the PF bar (preregistered first-fired bar), the fold bar, and the ×2.0
stress bar with wide margins; gross expectancy is negative before costs;
Band 2 kills the identity independently (strata spread does not clear the
doubled RT band); the date-only clock reproduces the (negative) anchor;
the clock-only shadow carries the same gross as the payload rule. No
post-hoc adjustment was made to any book, band, bar, or record; the
placebo degeneracy is reported, not repaired.

**S0-is-seen-data caveat (honest):** every number above is computed on the
dev window 2015-01-05..2026-06-30 — the same data the screens and folds were
designed on. This is S0 screening on SEEN data, NOT untouched OOS; S1
remains SEALED and untouched. Per the GO outcome law, all 3 rows are marked
`observed: true` and enter the observed scored denominator including this
failure.

**DSR context row: NOT_RUN** — deflated view not computed: single family,
3 arms; DSR requires trial-history covariance across the family/cycle
history. Raw results only are reported.

## 8. Incidents

| id | severity | detail |
|---|---|---|
| E-I1 | LOW (protocol worked) | Two runner starts aborted fail-closed BEFORE any computation: (a) CODE_FREEZE_MISMATCH — a runner path-resolution bug pointed `git -C` at the main checkout (HEAD aa954939 ≠ 19786077); fixed in the runner, worktree HEAD verified 19786077 thereafter; (b) BOOK_INVARIANT duplicate-id guard keyed on bare event_id — the permuted book legitimately reuses anchor event ids under a distinct control_variant/draw; guard re-keyed to (control_variant, draw, event_id). Both released the heavy lock FAILED with notes, per protocol. |
| E-P1 | MEDIUM (spec defect in a frozen control, found at scoring time) | Permuted-acceptance placebo structurally non-informative (§6): within-issuer×form×year stamp shuffling preserves the scored-record multiset, making all draws aggregate-identical to the anchor by construction. Books were built exactly to the frozen spec — nothing adjusted. Owner/A1 item: re-specify the placebo in a new freeze before any clock-adjudication use. |
| E-I2 | INFO | Determinism double-run: run B written outside the repo (`/tmp/emv1_scored_runB`); `scored_detail.json` byte-identical (sha256 `92b20bed…be202e33` both runs); rows byte-identical after stripping only `computed_utc` (`scored/determinism_scored.json`). |

## 9. Tests + determinism

- pytest (root .venv): **49 passed / 0 failed** (35 pre-existing engine tests
  + 14 new scoring tests: 12 hand-computed fixtures incl. short side,
  cost-exactly-once/two-fills, delisting-exit-scored, fold/pooled/PF hand
  arithmetic, concentration shares, Band-1 fire mechanics, buy-hold
  baseline; + 2 placebo-invariance regression tests).
- Full scoring re-run ×2 → byte-identical outputs (§8 E-I2).

## 10. Outputs

- `engine/scored/scored_rows.jsonl` — 3 rows, schema
  `event_mechanisms_v1_scored_row@1` (arm_config_digest
  `a448211b…c1bea4` = sha256 of the G3_FREEZE A1 section;
  data_snapshot_digest `18dfc1db…e72bbba` = sha256 of
  `.staging_eventmech/SHA256SUMS.staged.txt`; code_freeze_sha `19786077…`).
- `engine/scored/scored_detail.json` — every aggregate, every bar with
  margins, controls, frozen-constants echo.
- `engine/scored/lock_evidence.json`, `engine/scored/determinism_scored.json`.
- `engine/scoring/` (score.py, gates.py, run_scored.py),
  `engine/tests/test_scoring_fixtures.py`.
- Root `TRIAL_LEDGER.jsonl` NOT touched (A1-owned); these rows are
  worktree-local for A1 to consume.
