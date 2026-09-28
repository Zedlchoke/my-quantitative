# A7_PREREVIEW — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (Lane L5 independent skeptic, 2026-09-28)

Independent pre-GO prereview of the integrated artifacts. I audited; I did not
repair. Scope and authority per `LANE_CHARTER.md` (read-only session; only
these two outputs written: `skeptic/A7_PREREVIEW.md`, `handoffs/L5_skeptic.json`).
No git writes, no backtests, no S1, no registry/ledger/MAP/LESSONS access.

Method: every mandatory check was executed with independent re-measurement
(recounted TSVs, re-grepped source files, re-shasummed pins, re-ran git
read-only commands, re-verified ancestry ids against
`research/wayfinder/FAMILY_FAILURES.jsonl`). Evidence below cites file + what
was measured. 54 census rows were spot-checked in full across all 12 symbols
and all 6 verdict classes (requirement was ≥36 rows / ≥8 symbols).

---

## Findings

Severity order. CRITICAL/HIGH counts drive the verdict line at the end.

### F-1 (MEDIUM) — V2/V3 PIT "cheap evidence path" (ALFRED) contradicted by L1's own measured finding

- `router/ROUTER_POLICY_DESIGN_DRAFT.md:197-199` (V2): "the cheap evidence
  path is ALFRED vintage stamps (first-available timestamps), recorded in
  `datacost/PIT_SOURCE_TABLE.md`". `plan/PLAN_portfolio_router_12assets_100k_v1_DRAFT.md:75-77`
  repeats: "PIT gate via ALFRED vintages REQUIRED".
- `datacost/PIT_SOURCE_TABLE.md` row 9 (TIPS/FRED, measured evidence): "**ALFRED
  (true vintages) is BLOCKED_DATA_AUTHORITY on this host** (FOREX-FREE-V5: CSV
  hang 12/13, keyless API 400, license page unreachable)".
- Measured contradiction: the router/plan lean on a channel this program's own
  L1 artifact documents as transport-blocked. Consequence is fail-closed
  (`NOT_RUN_PIT_GATE_FAILED`, disclosed in plan §3), NOT lookahead — but as
  written the state engine's V2/V3 gates have no evidenced unblock path except
  the direct-history routes (row 11: CBOE publishes VIX daily closes freely;
  EIA/FRED DCOILBRENTEU/DCOILWTW) whose publication clocks still need machine
  evidence. Required fix before registration: name the actual V2/V3 evidence
  path per PIT_SOURCE_TABLE (CBOE direct + publication-clock gate, or an owner
  ALFRED-unblock action), and delete/reword "cheap evidence path is ALFRED".

### F-2 (MEDIUM) — donchian_breakout dead-family adjudication is not uniform across lanes; 2 of the 15 headline DISTINCT_TESTABLE rows are exposed to demotion

- Extracted all 21 rows with `mech_key=donchian_breakout` from
  `census/CENSUS_1200.tsv`. Twelve are VARIANT_OR_DUPLICATE citing the dead
  PSV1 donchian/breakout families (GBPUSD-S001, USDJPY-S001/S009,
  XAUUSD-S001/S004/S028, NZDUSD-S027, BRENT-S006, WTI-S027, EURUSD-S007,
  USDCAD-S003/S006/S029, XAGUSD-S001). Two are DISTINCT_TESTABLE **with the
  same dead-family ids in `ancestry_hits`**: AUDUSD-S002 ("ungated two-sided
  Turtle; dead PSV1 Donchians were regime-gated single-direction variants")
  and USDCAD-S002 ("no in-file or dead-class exact match").
- Frozen rule (`census/CENSUS_PROTOCOL.md` §3 rule 2): dup-of-dead-family is a
  mechanism-CLASS judgment ("payer + information source + skeleton"),
  symbol-agnostic — either the class matches (→ all VARIANT) or it does not
  (→ none). The lanes adjudicated the same class both ways.
- Impact: strict re-adjudication could move DISTINCT_TESTABLE 15 → 13 and
  change the plan's test slate. Mitigations that keep this MEDIUM not HIGH:
  the hits are recorded (not hidden) in `ancestry_hits`; `CENSUS_SUMMARY.md`
  caveat 1 discloses granularity/adjacency judgment; admission gate 1 + the
  F-0 mechanism-class court re-adjudicate before any slot is granted
  (`router/ROUTER_POLICY_DESIGN_DRAFT.md` §2.2). Required fix: A1/owner should
  re-adjudicate the donchian class once, class-wide, before registration and
  re-publish the headline count.

### F-3 (MEDIUM) — merged `priority_score` is not the frozen §5 rubric's output (four mapping deviations in `merge_census.py`)

Measured by reading `census/merge_census.py:49-63,87-89` against
`census/CENSUS_PROTOCOL.md` §5-§6 and recomputing caps:

1. M: frozen rubric has "named but thin = 2"; code emits only 0/1/3.
2. F: no intermediate 2 (code: NOT_FALSIFIABLE→0, no-timestamp→1, else 3).
3. C: code assigns 3 ("measured vehicle stack") to ANY `FX-spot` vehicle, while
   the program's own cost authority says FX commission/swap/rollover are
   UNMEASURED (`cost/CENSUS_PROTOCOL.md` §4; `cost/COST_ACCOUNTING_SPEC.md`
   §1.1; sixsource FINAL_REPORT: one 02Z bucket measured). FX-spot rows get
   full cost-determinability marks they have not earned.
4. A: "VARIANT rows inherit 0" is implemented only for VARIANT rows WITH an
   ancestry hit; 46 no-hit (in-file-dup) VARIANT rows score with A=3. Measured
   consequence: 46 VARIANT rows exceed the literal-rubric cap, and USDJPY-S087
   (VARIANT_OR_DUPLICATE, `anc=none-found`) carries the file-maximum 9.23 —
   above every DISTINCT_TESTABLE row except two.
   Also §6's frozen exemplar tiebreak "highest data_status then lowest gid" is
   implemented as (verdict tier, data_status, priority desc, gid).

Impact bounded: shortlist membership is verdict-class-driven, and the plan's
test slate is not priority-ordered — this affects ordering/appearance, not
gates. But the protocol advertises "frozen … A1 computes uniformly, no agent
judgment", and the uniform computation differs from the frozen text. Required
fix: either amend CENSUS_PROTOCOL §5 to match the implemented mapping (and
note FX-spot C=3 is conditional) or recompute scores per the frozen text;
publish which is authoritative.

### F-4 (LOW) — two verdict-order deviations (BLOCKED_COST where data rules should fire first)

`census/CENSUS_1200.tsv`: XAGUSD-S003 and XAGUSD-S067 are BLOCKED_COST with
`data_status=MISSING` (XAG price leg absent from repo). Frozen order
(CENSUS_PROTOCOL §3) puts BLOCKED_DATA (3) / PIT_UNPROVEN (4) before
BLOCKED_COST (5); with a missing price leg the earlier rule should fire (the
same symbol's XAGUSD-S019, MISSING, correctly got BLOCKED_DATA). Class
mislabel only — both classes are equally not-runnable-now; but the follow-up
routing differs (PIT gate vs cost measurement). Recommend A1 note or
re-verdict at next touch.

### F-5 (LOW) — one ancestry id cited in 4 rows exists nowhere in the digest

Token `SPRINT-CRYPTO:H-VOLSHK-BRKOUT-v1` (rows NZDUSD-S022/S023,
USDCHF-S022/S023) — verified absent from `research/wayfinder/FAMILY_FAILURES.jsonl`
(python pair-check over all 169 entries; SPRINT-CRYPTO's families are
H-XSECT-MOM-v1, H-FUNDCROWD-MR-v2, H-VOLCOMP-BRKOUT-v1, …). Almost certainly a
mis-citation of `H-VOLCOMP-BRKOUT-v1`. No verdict flips: in 3 of 4 rows the
dup verdict independently rests on the real `DT100-04-SQUEEZE` hit, and
USDCHF-S022 is PIT_UNPROVEN where ancestry only affects priority. Citation
hygiene fix only.

### F-6 (LOW) — floor relaxation F1≥10/F2≥2 echoes the documented RSM mirage values; owner should sign it knowingly

`router/ROUTER_POLICY_DESIGN_DRAFT.md` §3.5 adapts the ancestral 20/3/100
floors (BTC-H4-TWO-REGIME §1.5, verified at MAP.md:292-327) to 10/2/26. The
first two values coincide with the RSM owner-relaxed 10/2/50 comparison that
MAP.md:1326-1328 records as a thin-sample mirage (+2,529 at 1.0x, dead at
1.5x). The clock-scale arithmetic justification is sound (a weekly clock has
~5.25× fewer decision points; ≥100 state-true weeks/state/fold would require
>64% per-state occupancy and is structurally impossible), and the compensation
is binding, not advisory (×1.5 cost survival + leave-one-out for any state
<20 merged episodes; margin-to-floor-to-20 published; EVALUATION §7.1). L4's
own handoff names this "the single most attackable preregistration choice".
No repair demanded — but the owner-facing plan should surface it as a decision,
not a footnote.

### F-7 (LOW) — plan §8 handoff count is wrong (says 17, disk has 15)

`plan/PLAN_portfolio_router_12assets_100k_v1_DRAFT.md:147-148`: "17 present:
12 census + L1 + L3 + L4". Measured: `handoffs/` contains 15 files (12 census
+ L1_data_pit + L3_cost_accounting + L4_router_design); with L5 on dispatch it
becomes 16. Cosmetic factual error in an owner-facing governance section.

### F-8 (LOW) — KS1 fallback threshold `ΔVIX(5d) ≥ +6 points` is the one non-self-normalizing constant

`router/ROUTER_POLICY_DESIGN_DRAFT.md` KS1 row. Everything else in the state
engine is rolling-percentile or bp-delta; +6 raw VIX points is level-dependent
(12→18 ≠ 40→46 in % terms), implicitly calibrating to a particular VIX-level
era. It is preregistered, chosen by data availability only, and purely
risk-reducing (exits D-family), so it cannot manufacture edge — but a
percentile-of-ΔVIX form would remove the scale dependence. Flag for the freeze.

### F-9 (LOW) — budget classes sum correctly but the "arm-execution" unit needs one crisp definition

`plan/TRIAL_BUDGET_FREEZE_DRAFT.md`: ledger 220 = 54+40+90+6+30 (verified) and
scored 64 = 10+27+27 (verified); census math in item 3 is real (548 variants;
554 = 433 PIT_UNPROVEN + 121 BLOCKED_DATA); no double-count or hidden class
found. Ambiguity: baselines are budgeted as up to 90 LEDGER rows ("9 arms ×
≤10 folds") but only ≤27 SCORED arm-executions, and B4's 100 internal seeds
live inside a single arm-execution. Pin the definition at registration so
per-fold and seed-replicate accounting cannot drift across the two caps.

### F-10 (INFO) — EFFR publication clock stated two ways

`datacost/PIT_SOURCE_TABLE.md` row 7: "next business day ~08:00 ET";
`router/ROUTER_POLICY_DESIGN_DRAFT.md` §3.4: "Monday ~09:00 ET". (NY Fed
publishes the SOFR family ~08:00 ET and EFFR/OBFR later; neither in-file
number is exact for EFFR.) Immaterial: the T−1 Thursday lock at a Friday
17:00 ET decision is safe under any morning publication. Pin one number
(DECLARED-ASSUMED) at the PIT gate.

### F-11 (INFO) — V2 availability wording errs conservative, not lookahead

§3.4: "Friday's VIX print lands after CBOE close 16:15 ET, inside the decision
hour". Friday's VIX close (16:15 ET) actually lands ~45 min BEFORE the 17:00 ET
decision and would be technically usable; using Thursday's close is stricter
than necessary (and satisfies row 11's close+1 rule with margin). No lookahead
anywhere in the state engine — this is the only imprecision and it is in the
safe direction.

### F-12 (INFO) — cross-cluster risk-budget split not written

`router/ROUTER_POLICY_DESIGN_DRAFT.md` §5 gives equal risk per enabled sleeve
WITHIN a cluster plus cluster caps, but not how the total budget divides
ACROSS clusters. Allocation constants are preregistered trials so it will be
pinned — name the cross-cluster rule explicitly before freeze.

### F-13 (INFO) — s_id padding inconsistent in merged TSV

BRENT rows carry zero-padded `S007` (artifact of the disclosed mechanical
repair); all other symbols use `S7`-style. Protocol specifies gid padding only;
cosmetic; keep the disclosed repair as-is.

### F-14 (INFO) — cost spec covers 7 FX pairs including two L1-FLAT symbols

`cost/COST_ACCOUNTING_SPEC.md` §1.1 gives defaults for NZDUSD/USDCHF which the
final matrix verdicts FLAT_BLOCKED_DATA. The spec discloses it was written
vehicle-class-parametric before L1 finalized; harmless, but a reader could
mistake spec coverage for eligibility.

---

## Checked and clean (absence of findings is itself reported)

1. **Census counts (independent recount).** All six verdict classes
   (VARIANT 548 / PIT_UNPROVEN 433 / BLOCKED_DATA 121 / NOT_FALSIFIABLE 68 /
   DISTINCT 15 / BLOCKED_COST 15 = 1,200), all six data-status classes (753/
   207/156/50/33/1 = 1,200), the per-symbol verdict table (12×100), 917
   family×mech_key groups, 87 cross-symbol groups, shortlist 385 = 371+14 with
   per-family counts (65/56/45/45/36/34/30/30/27/17) — recomputed from
   `CENSUS_1200.tsv` directly; all match `counts.json` and `CENSUS_SUMMARY.md`
   exactly. 1,200 rows × 21 fields, gid-unique, 0 unresolved exemplar refs
   (recomputed). Parts vs merged spot-diff (USDCHF, XAUUSD, WTI): identical.
   BRENT mechanical repair consistent (gid↔s_id).
2. **Stratified row audit (54 rows, 12 symbols, 6 verdicts).** Every sampled
   `source_ref` line range was printed from
   `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/*.md` and lands on the correct
   S-id idea text — 54/54 real, none fabricated. Verdicts follow the frozen
   decision tree in 52/54 (exceptions = F-4). Spot-verified in-file dup claims
   against their named exemplars (EURUSD-S007→S2, BRENT-S067→S63,
   NATGAS-S031→S5, USDCHF-S074→S58, XAGUSD-S036→S31, WTI-S003→S41). NOT_FALSIFIABLE
   rows are genuinely book-incapable (meta-filters/wrappers/policy overlays) —
   checked against idea text.
3. **Ancestry honesty.** 218 distinct ancestry tokens extracted from all 1,200
   rows; every one resolves to a real `FAMILY_FAILURES.jsonl` (cycle_id,
   family_id) pair, a prefix-legitimate shorthand of one, or a disclosed
   charter citation (JEV-REGIME-ROUTER-V2 / REGIME-STRATEGY-MAPPING-V1 /
   REGIME-GATED-COMBO-V1 / PHASE-STRATEGY-V1 — CENSUS_SUMMARY caveat 3) —
   except the single F-5 token. `ancestry/FAMILY_FAILURES_DIGEST.tsv` is a
   faithful 169/169 projection of the wayfinder authority (0 divergent pairs).
4. **No-outcome contamination.** Full-text scan of every artifact for
   PnL/PF/Sharpe/win-rate/winner/Top-10/outperform/validated language: every
   hit is (a) design language ("nothing here is a PnL claim", "pre-PnL
   battery"), (b) measured MARKET facts with cited paths (spreads, p50/p90
   pips, rates), or (c) the brainstorm's own idea text quoted inside census
   mechanism fields. "Top-10" appears only with explicit NOT-winners framing.
   The source corpus's Sep-2026 gilt-yield episode number does not propagate
   into any census row. All 1,200 remain HYPOTHESIS/NOT_RUN everywhere;
   DATA_COST_MATRIX (0 NOT_RUN mentions) instead carries fail-closed framing.
5. **State-engine PIT audit.** V1 EFFR Δ63bd: Thursday's fixing at a Friday
   17:00 ET decision is published (next-business-day morning) before the
   decision — available, no lookahead; 5bd staleness coherent with 1bd
   publication lag. V2: Thursday close conservative (F-11). V3: EIA spot
   next-day publication respected via the same T−1 lock; 2bd staleness
   coherent. Friday-17:00 decision → Monday 08:00-17:00 UTC execution windows
   is consistent (≤1 trading week, per-cluster session filters). No
   late-confirmed-event inputs in the state (COT/MOF/GDT/SNB excluded by
   design); state is a pure function of T−1 series values (no label step).
   Fail-closed: PIT-gate failure ⇒ NOT_RUN, no substitution.
6. **Loss-segment-rescue audit.** All router thresholds are functions of the
   three macro series only (rolling percentiles, bp-deltas, dwell/merge in
   weeks); caps (2%/1%/6%/30%, 0.25-0.5% per trade) are general portfolio
   rules. No ON/OFF cell, threshold, or kill constant encodes Sep-2026 or
   2022-specific numbers: the corpus's $3-6/$11-14 war-spread ranges are NOT
   used as levels (p85 trailing percentile instead); the WAR_ENERGY precious
   OFF cell is a preregistered falsifiable prior with corpus citation, not a
   fitted constant. Structural no-rescue guarantees present (policy §2.2.6;
   evaluation §6 no attribution feedback). Residuals: F-8 (one scale-sensitive
   constant), F-6 (mirage-adjacent floor values).
7. **Baseline completeness.** B0 FLAT; B1 ALWAYS_ON which IS the
   equal-risk-budget simple baseline (policy §5: equal risk per enabled
   sleeve, no performance-weighted sizing; evaluation §5: baselines share the
   allocation plumbing and differ only in the enable rule); B2 BEST_LEG
   train-only; B3 ABSTAIN-ONLY; B4 RANDOM_GATE 100 frozen seeds matched to
   duty cycle AND turnover; B5 CLOCK_GATE; B6 INVERTED; B7 LAGGED (4/8w);
   B8 ORACLE non-governing. Null validity (Q-11) checked before nulls score.
   Everything on the owner's required list is present.
8. **Budget arithmetic.** Sums verified, no double-counting, no hidden class
   (unit note = F-9). Overflow law and zero-cell closes are typed.
9. **Data matrix honesty.** All 12 eligibility verdicts re-verified against
   physical evidence: EURUSD M1 2,092 day-files/side 2021-01-01→2026-09-23
   (rangefade worktree); GBPUSD/USDJPY 2,092 (fx-majors worktree);
   USDCAD/AUDUSD bars1h parquets + census JSONs (erp1 repro_twin);
   XAUUSD_1day_full.json sha256 49c2684e… re-hashed and matches; OFR
   FNYR-EFFR-A series staged; `~/.my-quantitative-data/ibkr_statement/`
   confirmed absent (consistent with UNMEASURED commission/swap). Prospective
   vs historical respected everywhere (02Z one-bucket band never treated as
   history; TD archive ARCHIVE/REFERENCE only). No ELIGIBLE that should be
   FLAT or vice versa (USDCAD/AUDUSD H1 ceiling disclosed; XAU daily-only
   research allowance is gated, not assumed).
10. **Plan-level.** GO phrases typed, one per gate, explicitly NOT consumable
    from the document (P-8 law stated); §2's four arguments against scoring
    1,200 are sound and factually check (α=0.05 × 1,200 ≈ 60 false edges;
    548/433/121 census counts real; 5/12 symbols with repo history real).
    Negative outcomes first-class with typed close codes and a one-shot
    reopening condition (changed mechanism axis only). S1 boundary explicit.
    **All 11 artifact sha256@16 pins re-computed — all match** (CENSUS_1200,
    CENSUS_SUMMARY, shortlist, DATA_COST_MATRIX + DRAFT, PIT_SOURCE_TABLE,
    COST_ACCOUNTING_SPEC, both router drafts, LANE_CHARTER, CENSUS_PROTOCOL).
11. **STATE_REMEASURE vs git.** `git rev-parse HEAD` =
    abe7f70bf22639184541be6b3564cd0760580f45 on `main` (matches); porcelain =
    owner's untracked SANDBOX-OVERFIT-3ASSETS `{data,out}/` + this program's
    untracked control dir, exactly as stated. CYCLE_REGISTRY REGIME-GATED-COMBO-V1
    row matches the charter's characterization (ACTIVE_LIGHT, 0/3, prelaunch
    REFUSED, awaiting owner a/b; untouched).
12. **Authority citations.** MAP.md 1278-1342 (JEV loses to ALWAYS_ON and
    RANDOM; switching attrition monotonic ×1.0/1.5/2.0; RSM floors 20/3/100 and
    the +2,529-at-1.0x mirage), 1429-1460 (ERP track-a REJECT_ALL; whole-day
    lookahead; PF 1.03-1.05), 292-327 (two-regime 5/6/5 episodes vs 20/3/100)
    — all verified verbatim. All cited LESSONS ids (P-4/8/9/15/20/21/24/27/28/
    29/30, Q-5/7/8/9/10/11/16) exist with content matching the use made of
    them.

---

## Verdict

0 CRITICAL · 0 HIGH · 3 MEDIUM (F-1, F-2, F-3) · 6 LOW · 5 INFO.

PREREVIEW_VERDICT: AUTHORIZED_FOR_OWNER_REVIEW

Advisory (non-blocking) fixes before or at registration, in priority order:
1. F-1: reconcile the V2/V3 PIT evidence path with L1's ALFRED-blocked finding;
   name the real unblock route (CBOE/EIA direct + publication-clock evidence,
   or an owner network action).
2. F-2: re-adjudicate the donchian_breakout dead-class question once,
   class-wide; re-publish the DISTINCT_TESTABLE headline accordingly.
3. F-3: declare which priority mapping is authoritative (frozen §5 text vs
   `merge_census.py`) and regenerate or amend; document FX-spot C=3 as
   conditional on the owner cost statement.
4. F-7: correct the handoff count in plan §8 (15 present, 16 with L5).

— Lane L5 independent skeptic, read-only session, no git writes.
