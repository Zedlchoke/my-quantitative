# A7_PRELAUNCH_REPORT — SRLV-CX-C1

- Lane: `a7-prelaunch`, role `a7-independent`. Date: 2026-09-26.
- Worktree verified: `.worktrees/srlv-cx-c1/integration`, branch
  `orca/srlv-cx-c1-integration`, HEAD `2104a5b96b7cca1e44f662a36b0ce1354bb674ca`
  (measured at lane start, identical at lane end).
- Read-only on all artifacts audited; touched only this file +
  `HANDOFF_a7_prelaunch.json`. No commit. No PnL computed or read (none exists —
  verified §4).
- Authority chain audited: owner GO-1/GO-2 record (registry) → C0/C1/C2 verdicts
  → council reports + handoffs (sha-pinned in the freeze chain) → amended
  TRIAL_FREEZE_GO1.md.

## VERDICT: **PASS**

Scored execution may proceed under GO-2 (`GO SRLV CX C1 SCORED EXECUTION`,
REGISTERED_NOT_CONSUMED) after the frozen fixture battery (F1–F7 + per-mech)
passes on the exact frozen code digest. No blocking findings. Non-blocking
observations recorded in §6; none weakens a kill law, gate, or the budget.

---

## 1. Freeze chain audit (TRIAL_FREEZE_GO1.md + GO1_freeze_sha256.txt)

### 1(a) Pre-outcome amendment disclosed, both shas recorded — VERIFIED

- `GO1_freeze_sha256.txt` records both freeze shas: line 1
  `41ef0624b30dc23f090bec53312b1bf3441cc123b7a13edb134f9a1ea35453ff` (original)
  and line 7 `64aba7c3ffd038e96c129a8f4d7c648b6205c7bb3c96e15576e1728e0739cde2`
  (amendment). Independently reproduced both:
  - Original = `git show 2104a5b9:research/control/SRLV-CX-C1/freeze/TRIAL_FREEZE_GO1.md`
    → sha256 `41ef0624…35453ff` (exact match).
  - Amended = working-tree file → sha256 `64aba7c3…739cde2` (exact match).
- All five council-report shas in the pin file match the files on disk
  byte-for-byte (PROPOSAL_P1 `5069d9ea…`, PROPOSAL_P2 `63dfd511…`,
  SKEPTIC `b6a53622…`, COSTAUDIT `9b9eab94…`, PITAUDIT `2184a01f…`).
- The amendment is marked pre-outcome inside the freeze itself: Exit row
  "(sửa lỗi tóm tắt freeze bản đầu — pre-outcome amendment, disclosed)"; Arms
  row "(bản đầu freeze ghi N=4 là lỗi chép, sửa pre-outcome)"; impl-pins header
  "(pre-outcome, trước A7 prelaunch)". Diff of original (git) vs amended file
  confirms the changes are exactly: Entry law (was "close-through t / reclaim
  t+1 / fill t+2", now the cross-bar sweep/reclaim sequence with decision close
  c, fill open c+1), Exit law (was bare "time-stop 4 bars", now the three
  pre-registered exits), A2 N=4→N=3, plus impl-pins 1–9. Budget and verdict
  rows are byte-identical between versions. Amendment direction is strictly
  toward the sha-pinned proposal — nothing was relaxed.

### 1(b) Amended freeze consistent with PROPOSAL_P1.md (P1-A fields 5/6/9/10) — VERIFIED

- **Level (field 5):** N=6 strict pivot, `t_known` = close of j+6, earliest
  trigger j+7 — matches proposal §5 and the skeptic's off-by-one proof
  (§1.2, pin P1-8/9; fixture F-P1-OFFBYONE). Neighbours N ∈ {3,10} match both
  the proposal ("neighbors frozen at N ∈ {3,10}") and skeptic pin 14
  ("N ∈ {3,6,10} frozen at 6"). The freeze's `low[j] < low[j+6]` shorthand
  relies on the sha-pinned proposal for the full strict both-sides neighbour
  definition — see observation O3.
- **Window (field 5):** W_k = [S_k−1h, S_k+3h] on the 00/08/16 UTC grid ⇒
  5 close-times/settlement; close-time semantics carried by the sha-pinned
  proposal §5 (freeze entry row cites "theo PROPOSAL_P1 §5"; pin P0 fixes
  open-time labeling so close-time = open+1h). The 62.5%-of-hours coverage
  DEFECT is disclosed verbatim in the freeze Window row with the adjudicator
  being the ungated-clock kill law — no post-hoc narrowing (COSTAUDIT §2.3
  last row honored).
- **Entry sequence (field 5):** sweep bar s inside W_k (wick-through, no
  intrabar ordering), reclaim = first bar c, s < c ≤ s+3, `close[c] > L`;
  breakdown expiry at close < L − 0.25×ATR24 routed to the P1-B population
  (recorded only); decision at close c, fill open c+1 — verbatim proposal §5.
- **Exits (field 6):** (i) opposite-side reclaim close → next open;
  (ii) disaster stop close beyond sweep extreme > 1.0×ATR24 → next open;
  (iii) hard flat-by-settlement, exit open precompute = open of the last bar
  whose close ≤ S_{k+1} − 2h, with pin P1-1 skip rule (skip entry if exit open
  ≤ entry open); worst-case hold ≤ 4 bars; base funding ≡ 0. Matches proposal
  §6, PITAUDIT finding F-1's unique fail-closed resolution, and COSTAUDIT
  component 8's required flat-boundary convention.
- **Falsifiers (field 9):** ±4h placebo windows (04/12/20 UTC) ≥0.5× ⇒
  K-CTRL + VETOED_FICTIONAL_COUNTERPARTY; placebo levels; inverted control;
  delay-1 (Q-4); G8 per-direction folds; block-shuffle; per-boundary-hour
  payer-label check; power ≥100 RT/dir/pair with NOT_RUN_THIN fail-closed —
  all present (kill-laws row + impl-pins 1,2,4,6,8 + Power row).
- **Controls (field 10):** A4 causal placebo ±4h; A5 inverted sign-flip on
  same fills; A6 cash 0 / long-hold on measured funding path / trend SMA-720h;
  block-shuffle twin (pin 4), GMT-hour dummies + weekend split (pin 5).
  ATR24 ruled unit-of-account scale (skeptic §2.1-4) — freeze uses it only
  for buffer/stop sizing.
- **Ancestry shadows:** bar 0.20 with CNG2-A5-P1 (0.4178), CNG2-A5-P2
  (0.4872), PSV1-Donchian, Donchian-168 (P2-M2 shadow), PDHLOC/band-fade,
  displaced-fade + pin-3 frozen representations (band-fade-reclaim,
  Donchian-168 two-way, settlement-clock drift CNG2-style, rev24) — covers the
  skeptic §6.3 F-1 minimum named set (see O4).
- **Flat-by-settlement:** pinned as exit (iii) with precompute + skip, funding
  assertion (pin 9) and fixture F-P1A-FLAT — structural funding ≡ 0 holds only
  under this pin, exactly as PITAUDIT/COSTAUDIT require.

### 1(c) Impl-pins 1–9 do not weaken any kill law or gate — VERIFIED

- Pin 1 placebo-level kill fires at ≥0.8× anchor — STRICTER than skeptic §6.3
  item 5 ("≥ same ⇒ kill").
- Pin 2 ungated-clock kill fires at net>0 @1.0 with ≥100 RT/dir — STRICTER
  than skeptic item 4 ("out-earning ⇒ kill"); implements the skeptic-armed
  clock kill law (Q-7/RATESNG1/COMMNG1) the proposal itself did not
  pre-register.
- Pin 3 shadows: CNG2-style settlement-clock drift covers the mandatory
  event-clock form envelope; band-fade-reclaim, Donchian-168 two-way, rev24
  cover the fence-4/Donchian set. See O4 for the representation-coverage note.
- Pin 4/6 (block-shuffle 200 perms, block 20d, seed pinned; delay-1 fill c+2):
  kill thresholds (twin ≥0.5×; residual ≈0 / <50% survival) live in the
  sha-pinned SKEPTIC report — the freeze binds the battery "skeptic 14-item"
  by reference to that pinned artifact. No threshold contradicted. (O5.)
- Pin 7 cost book = COSTAUDIT measured numbers verbatim (tick BTC 0.1 / ETH
  0.01; RT 10.06/15.08/20.11 BTC and 10.24/15.35/20.47 ETH; funding +11.80%/yr
  worst −30.0 bp BTC, +13.95%/yr worst −35.63 bp ETH; worst-settlement-inclusive
  50.19/56.46 reported, not base gate). Ceiling convention PINNED =
  measured-distribution — exactly the pre-scoring pin COSTAUDIT §3 demanded
  (avoiding the CEILING_NEGATIVE_VETO flip).
- Pin 8 gates G1–G8 all per-pair; G6 = placebo <0.5× AND inverted < anchor AND
  ungated must die; G8 top-fold ≤0.50 per direction + pooled. Fail-closed
  throughout; nothing dropped from the skeptic battery.
- Pin 9 funding assertion + F-P1A-FLAT = skeptic item 13 / PITAUDIT §1.7.
- SOL/BNB arms blocked: skeptic item 13 called base arms "scoreable", but the
  COST lane holds BLOCKED power and ruled
  CEILING_UNDECIDABLE_MISSING_SPREAD for every SOL/BNB arm, with fail-closed
  default "SOL/BNB arms are excluded from the allowed scored panel". The
  freeze follows the stricter lane ruling — correct precedence, panel = BTC/ETH
  ("full allowed panel" per skeptic item 2, as narrowed by K-COST).

### 1(d) Per-pair adjudication vs skeptic pooling ruling — CONSISTENT (stricter direction)

Skeptic item 12 pre-registered: below the 100-RT/direction/pair floor, the
pooled panel row is the adjudicator. The freeze pre-registers instead:
below floor ⇒ NOT_RUN_THIN per pair; adjudication per-pair primary, identity
passes only if BOTH BTC and ETH pass gates; pooled = diagnostic only. In every
contingency the freeze is equal-or-stricter (a thin or failing pair kills the
identity; pooled evidence can never rescue it). The skeptic's anti-selection
intent — pooling fixed before any outcome, never post hoc — is honored by the
freeze's own pre-registration. No gate weakened; the divergence from the
skeptic's exact thin-pair adjudicator is recorded here as a disclosed,
fail-closed strengthening made pre-outcome.

### 1(e) Budget — UNCHANGED

6 scored cells (A1 anchor N=6, A2 N=3, A3 N=10, A4 placebo windows, A5
inverted, A6 baselines) + slots 2–3 EMPTY closed to same-family replacement =
skeptic ranked slate "1 mechanism + 2 empty slots" verbatim. Registry shows
0/18 consumed. The amendment did not touch the budget (verified by diffing the
original and amended freeze from git).

### 1(f) Labels — PRESENT

All six required labels pinned: PAPER_TIER, SINGLE_VENUE_PANEL,
ANCESTRY_EXPOSED_DEV, PROXY_NOT_ORDERBOOK, FILL_QUALITY_CLASS_DECLARED,
FUNDING_PATH_STRESSED (stress arm) — matching skeptic pin 14 exactly.

## 2. Council handoffs — EXIST, valid JSON, schema-declared; strict-shape deviations recorded

All five files parse as JSON and declare `zcode_orch_v3_handoff@1` with
cycle_id `SRLV-CX-C1`, correct role/lane, changed_paths confined to
`c3_council/`, and lane start sha `d3f063a0…` anchored (P1/P2/cost/pit in
`actual_start_sha`; skeptic in `tree_status`):

| File | role | schema | cycle_id |
|---|---|---|---|
| HANDOFF_P1.json | blind-proposer | zcode_orch_v3_handoff@1 | SRLV-CX-C1 |
| HANDOFF_P2.json | blind-proposer | zcode_orch_v3_handoff@1 | SRLV-CX-C1 |
| HANDOFF_skeptic.json | economic-skeptic | zcode_orch_v3_handoff@1 | SRLV-CX-C1 |
| HANDOFF_cost.json | cost-execution-auditor | zcode_orch_v3_handoff@1 | SRLV-CX-C1 |
| HANDOFF_pit.json | pit-data-auditor | zcode_orch_v3_handoff@1 | SRLV-CX-C1 |

Non-blocking shape deviations vs the strict v3 field list (O2): `dispatch_sha`
null in all five; `commit_sha` null (consistent with the no-commit dispatch);
`tests[]` entries carry {command, result} rather than
{command, exit_code, verdict, log_digest} (skeptic: string list); `outputs[]`
present only in skeptic, as paths without sha256;
tree_status/workers/incidents/recommended_next_action absent in 4 of 5. These
were accepted at GO-1 integration (Lead validation step; GO-1 commit 2104a5b9);
the authority content of each lane lives in the reports, which are sha-pinned
and byte-verified in the freeze chain. Fixture-phase handoffs (F6/A7 era) must
use the full strict shape.

## 3. Registry and locks — VERIFIED

- `cycle list` (repo root): `SRLV-CX-C1 ACTIVE_LIGHT 0/18 2104a5b
  orca/srlv-cx-c1-integration`. Registry entry phase:
  "GO-1 COMPLETE: C0/C1/C2 PASS + council done; 1 mechanism frozen M1
  SETTLE-RESOLVE (6/18 cells, 2 slots empty closed, sha-pinned
  freeze/TRIAL_FREEZE_GO1.md + GO1_freeze_sha256.txt); … next: A7 prelaunch
  then STOP for owner GO-2 'GO SRLV CX C1 SCORED EXECUTION' (registered NOT
  consumed)". `go_phrase_state: REGISTERED_NOT_CONSUMED`; s1
  SEALED_UNTOUCHED; head = measured worktree HEAD.
- `locks inspect`: **FREE_PROVEN** — "no registry row and the lock file is not
  flocked"; no live heavy worker.

## 4. No scored outcome exists — VERIFIED

Full inventory of `research/control/SRLV-CX-C1/`: 18 control artifacts
(c0 ×1, c1 ×2, c2 ×1, c3_council ×10, freeze ×2), trial_ledger.jsonl, and
data_local (funding parquet + sha manifest + 391 staged kline/funding zips:
BTC 80, ETH 80, SOL 72, BNB 79 kline months + 80 ETH funding months — counts
match CENSUS_1h_funding.json exactly). Keyword sweep (scored_outcome / pnl /
net_bps / expectancy / sharpe) hits only narrative reports asserting the
negation ("No PnL exists", "ZERO PnL") and pre-PnL census counts — no outcome
artifact exists anywhere under the cycle directory. Trial ledger has exactly
**5 rows** (4 council adjudications + 1 freeze row), every row
`scored_cells: 0`, `outcome_viewed: false`; verdicts match the council reports
and freeze. Budget consumed 0/18 corroborates.

## 5. C0/C1/C2 artifacts and facts — VERIFIED

- `C0_CONTROLPANE_VERDICT.md`: PASS (lock FREE_PROVEN, doctor findings 0 touch
  SRLV, collisions cleared, owner paths untouched).
- `C1_DATAGATE_VERDICT.md` + `CENSUS_1h_funding.json`: BTC/ETH klines PASS
  (58,440 bars each, 0 gaps), SOL PASS_WITH_DISCLOSURE (52,145 bars, floor
  2020-09-14, 2 disclosed gaps), BNB PASS (57,472 bars, floor 2020-02-10);
  funding BTC fapi **7,643** / ETH Vision **7,305**; SOL/BNB funding
  NOT_RUN_BLOCKED_PENDING_STAGING; spread census NOT_RUN. All figures match
  what the freeze and COSTAUDIT pins cite (tick method reproduces the same bar
  counts; funding anchors 7,643/7,305 in COSTAUDIT §2.1).
- `EXPOSURE_VERIFICATION_C1.md`: history OOS = NONE for all four pairs at 1h;
  OOS = prospective post-freeze (D13/D26/D52); dev fold contract F1..F4 with
  force-flat boundaries and ANCESTRY_EXPOSED_DEV — identical to the freeze
  Folds row. ETH-V2/CHR3F collisions untouched.

## 6. Non-blocking observations (for the fixture phase; none weakens a gate)

- **O1** `GO1_freeze_sha256.txt` lists both freeze shas without labels
  (original vs amendment disambiguated only by order + git history). Both are
  reproducible; a one-line label would prevent misreads.
- **O2** Handoff strict-shape deviations detailed in §2.
- **O3** The freeze's compressed pins (`low[j] < low[j+6]`; `W_k =
  [S_k−1h, S_k+3h]` without restating "close-time") rely on the sha-pinned
  PROPOSAL_P1 §5 for the full strict both-sides neighbour set and close-time
  window semantics. The F6 independent implementation (from proposal text only)
  plus F-P1-OFFBYONE/F-GRID will fail closed if any reading diverges — but the
  impl spec handed to the runner should quote proposal §5 verbatim.
- **O4** Skeptic F-1 named PSV1-Donchian H1-uptrend/H4-uptrend/H1-breakdown
  representations and a separate dead-FOMC-form envelope shadow; the freeze's
  pin-3 set approximates the envelope with the CNG2-style settlement-clock
  drift shadow and Donchian-168 two-way. Coverage of the dead-family classes
  is present; the runner should emit the per-shadow rho table so A7 can confirm
  the worst-shadow ≤ 0.20 rule (one-shot, runner+spec committed before
  execution, A7 recomputes).
- **O5** Block-shuffle kill threshold (twin ≥ 0.5× anchor) and delay-1
  thresholds (residual ≈ 0; < 50% survival ⇒ margin-to-fail review) live in
  the sha-pinned SKEPTIC report rather than being restated in the freeze pins.
  Binding by reference; the fixture-phase runbook should restate them
  explicitly next to the arm definitions.
- **O6** The P1-B ride arm is REPORT-only (not a scored cell), per the
  skeptic's structural absorption (§3.1-4) and the freeze's own A5 row; its
  mirror inverse (fade-the-acceptance) is correspondingly not a gated kill.
  The identity that can pass GO is the fade-anchor book only — strictly
  narrower, so nothing is weakened — but the ride-arm report and its rho vs
  the Donchian-168 shadow (skeptic §6.3 item 3(e)) must still be emitted as
  disclosed diagnostics so the K-ANC information is on the record.
- **O7** COSTAUDIT component 3 (BTC funding fapi-vs-Vision cross-check) is a
  named GO gate only for arms holding across settlements; M1 scored arms are
  structurally flat-by-settlement so the condition does not fire. If any
  scored book's arithmetic ever consumes the measured funding path as
  outcome-relevant (long-hold baseline feeding G7, stress arm), name the
  cross-check in the runbook before those numbers are read.
- **O8** The freeze + sha-file amendment is currently uncommitted working-tree
  state (the only dirty paths in the worktree). Content shas are verified; the
  Lead should commit the amendment before or with the fixture-phase integration
  so the sha-pinned chain is fully in-history at scored-run time.

## 7. Gate state after this audit

1. A7 prelaunch: **PASS** (this artifact + HANDOFF_a7_prelaunch.json).
2. Next: fixtures F1–F7 + per-mech battery on the exact frozen code digest;
   exact-arm dry-run (no PnL headline). F6 independent-impl diff is the A7
   recomputation hook.
3. **STOP.** Scored run only after the owner types
   `GO SRLV CX C1 SCORED EXECUTION` — phrase REGISTERED_NOT_CONSUMED as of
   this audit; consumption is the owner's act alone.
