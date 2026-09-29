# A7_PREREVIEW — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (pre-GO, wave 4, fresh context, 2026-09-29)

Independent read-only audit of the post-remediation package as it stands on
disk. The auditor has never seen this package before; every judgment below is
made only from the artifacts on disk at audit time and cited inputs re-read by
the auditor. Write scope (ONLY): this file + `handoffs/A7_prereview.json`.
No git operations, no network, no S1, no strategy simulation, no PnL
computation. `.venv/bin/python` was used exclusively for verification
arithmetic (byte-compare of the regenerated eligibility table, TSV/JSON
statistics and joins, sha256, and an independent from-scratch re-derivation of
all six accounting fixtures). The deterministic builder was re-run with its
output redirected to `/tmp` — the on-disk artifacts were never touched.

## 0. What was independently re-measured (not taken on trust)

1. **Ladder determinism.** `eligibility/build_portfolio_eligibility.py` was
   re-run against `PORTFOLIO-ROUTER-12ASSETS-100K-V1/census/CENSUS_1200.tsv`
   with output redirected: the regenerated TSV is **byte-identical** to the
   on-disk `PORTFOLIO_ELIGIBILITY_1200.tsv`
   (sha256 `af5d30dea5daf51e7ab963aab9108c3c63be3fb5962ad1457504de3957214e1e`)
   and the counts JSON is byte-identical too.
2. **Table integrity.** 1,200 rows / 1,200 unique gids; every copied field
   (symbol, s_id, family, title_short, mech_key, horizon, census_verdict)
   matches the census verbatim — **0 provenance mismatches**; the label rule
   re-derived independently produces **0 deviations** on all 1,200 rows; the
   15 F0 verdicts match SLEEVE-FX5 `f0/F0_VERDICTS.md`'s table exactly
   (10 REJECT_VARIANT_SAME_FAMILY / 3 REJECT_DATA_OR_COST /
   2 REJECT_NOT_STANDALONE).
3. **Ladder v2.1 counts (re-measured).** EXPLORATORY_CANDIDATE **294**
   (EURUSD 56 · GBPUSD 80 · USDJPY 51 · USDCAD 52 · AUDUSD 55); families
   G 40 · A 37 · C 33 · F 32 · I 32 · B 30 · E 30 · J 29 · H 20 · D 11;
   labels FHN 223 · PRIOR 59 · F0 12; blocked 565/110/90/68/41/23/9 (sum
   1,200). 89 of the 294 carry census verdict PIT_UNPROVEN (same figure the
   skeptic measured — disclosed, see D4/F-4).
4. **F-4/F-5 repair rows (verified on disk).** USDJPY-S012 =
   EXPLORATORY_CANDIDATE, pit_class PRICE_PLUS_CALENDAR, label
   F0_INDIVIDUAL_REJECT; USDCAD-S048 admitted PRICE_PLUS_CALENDAR;
   EURUSD-S082 / USDJPY-S028 admitted (triaged T3); EURUSD-S035 blocked
   NEEDS_COT_PIT_UNEVIDENCED; GBPUSD-S006/S031/S040 blocked
   NEEDS_MACRO_PIT_UNEVIDENCED (SOFR no longer in the evidenced set).
5. **Triage.** `mechanization_triage_292.tsv`: **294 rows**, T1 75 / T2 75 /
   T3 144; gid set exactly equals the 294 EC rows; symbol/family/horizon/label
   reconcile **0 mismatches**; per-symbol and per-family tier tables match
   GROUPING_PROPOSAL §1.2 exactly; USDJPY-S012 = T2/F0_INDIVIDUAL_REJECT;
   USDJPY-S020's reason carries **MECHANIZATION_DEVIATION**; no SOFR/EFFR
   string occurs anywhere in the TSV.
6. **Fixtures.** An independent from-scratch engine (written against
   FILL_ACCOUNTING_SPEC text only) re-derived every number of **all six**
   fixtures — fills, spread-once/slip/commission lines, dated swap lines with
   Wed ×3, timeline cash/equity at every step, totals, gross-vs-mid (closed
   and open forms), net PnL, the §6 decomposition invariant, fx3 pro-rata
   virtual attribution, fx5 guard windows (8.4+0.780191=9.180191 ≥ 9.00 →
   DEFER; 0.780191 < 9.00 → EXECUTE), fx6 graded fill / gap-excess / never-at-
   stop: **0 mismatches at 1e-9**.
7. **Cost authorities.** FILL_ACCOUNTING_SPEC §3's dual-source table matches
   its cited sources verbatim: C1 (0.3/0.5, 0.8/1.3, 0.5/0.9; n=286/286) and
   C2-Fri (0.5/1.1, 1.2/2.3, 0.8/1.8) and C3 (5.9/9.0, 13.4/23.8, 11.0/22.0)
   vs `SLEEVE-FX5-100K-V1/pitcost/COST_AUTHORITY_TABLE.md`; corrected Mon–Thu
   cells (EURUSD 1.2/3.7 n=65,109 · GBPUSD 2.8/7.8 n=65,274 · USDJPY 2.1/7.4
   n=64,892) vs `poolB/data_audit/audit_summary.json`
   (`c2_window_variants.mon_thu_2100_2200_utc`), including the hour-shift
   diagnosis rows (22–23Z ≈ the table's stale column).
8. **Handoff pins.** All 12 sha256 pins in the M/P/R handoffs match the
   current files on disk (CLASS_SPEC dedbc6c7…; PASS_BARS_V2 e61958b0…;
   FILL_ACCOUNTING_SPEC b5bd0b6a…; fx1–fx6 + fixtures README; GROUPING
   395f3618…; triage 2d258d41…). Zero mismatches.
9. **Corpus spot-checks.** USDJPY-S020, USDJPY-S012, EURUSD-S010 rule texts
   read at `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/*.md` — triage
   reasons and class-spec quotes are faithful (the corpus itself flags the
   MOF ex-post-disclosure lookahead trap the MECHANIZATION_DEVIATION labels).

## 1. Findings by severity

### CRITICAL — none

### HIGH (3; all three are skeptic findings that reached A7 without a documented disposition — rubric-mandated elevation per the A7 audit plan; underlying technical severities annotated)

- **H-1 (skeptic F-12, underlying MEDIUM): two parallel switch-cost books,
  still unreconciled.** `poolB/grouping/GROUPING_PROPOSAL.md:588` —
  `switch_cost_usd` remains priced at "the measured spread cell of the actual
  fill hour (C1 per-hour p50 cell…)" while the book charges the fill bar's
  quoted spread through the fill price (FILL_ACCOUNTING_SPEC §2). The r1 edit
  added "spread charged EXACTLY ONCE … no second crossing line" (addresses
  double-counting) but neither of the skeptic's two requested dispositions
  (pin to journal realized crossings, or declare the cell figure an estimate
  with a divergence tolerance) was adopted, and no owner-decision or
  accepted-as-info record exists anywhere in the package (R handoff
  remediation_log lists only F-5/F-10/F-20/F-23/F-4-context; SESSION_REPORT's
  remediated list omits F-12). Fix is a two-sentence amendment.
- **H-2 (skeptic F-18, underlying LOW): ladder v1 still not reconstructible —
  and the summary's justification is itself unevidenced.**
  `eligibility/PORTFOLIO_ELIGIBILITY_SUMMARY.md:8` claims v1 "is preserved in
  git history" while `LANE_CHARTER.md:20-22` and SESSION_REPORT:7-8 record the
  whole control dir as **uncommitted** pre-GO evidence (the v2 builder
  regenerated the same path in place). No v1 copy or regeneration diff exists
  in the control dir. Either stage a v1 snapshot/diff inside the package or
  strike the "git history" claim.
- **H-3 (skeptic F-22, underlying INFO): ARTIFACT_PINS.json still not
  generated.** `manifest/` contains only `build_pins.py`; plan §10
  (`PLAN_..._DRAFT.md:183`) makes the registration receipt freeze the
  manifest digest. Per-artifact sha256s in the handoffs are correct (all 12
  verified), but the single owner-consumable pin manifest the plan promises
  does not exist. Run the builder before the owner packet.

### MEDIUM (4)

- **M-1: eligibility SUMMARY carries 292-vintage sub-counts under a correct
  294 headline.** `eligibility/PORTFOLIO_ELIGIBILITY_SUMMARY.md`: per-symbol
  line 23-24 "EURUSD 56 · GBPUSD 82 · USDJPY 53 · USDCAD 56 · AUDUSD 55"
  sums to **302 ≠ 294** (actual 56/80/51/52/55); family line 25-27 sums to
  **292** (actual D 11 / A 37 / B 30 / C 33 / E 30 per the builder and the
  grouping table); label line 30 "222/59/11" vs actual **223/59/12**;
  blocked-rows table lines 36-44 "115 / 39 / 22" vs counts.json **110 / 41 /
  23**; reading-rule-0 line 52 "T2 72 · T3_PARK 145" under a "150/294"
  headline (actual 75/144); line 58 "D-CARRY 0/13, F-EVENT 2/30" vs actual
  0/11, 2/32. The headline and the TSV/counts.json are correct — but this is
  the owner-facing summary and its sub-numbers contradict the artifacts they
  summarize.
- **M-2: plan v2 §2 is internally stale and contradicts its own §4.**
  `plan/PLAN_..._DRAFT.md`: §0 line 27 "222 / 59 / 11" (actual 223/59/12);
  §2 lines 61-62 "115 PIT-unevidenced … 39 ceiling, 22 feature-blocked"
  (actual 110/41/23); §2 lines 65-67 "75 T1 + 72 T2 at the 292-row vintage,
  being refreshed … 145 are T3_PARK" — the refresh already landed on disk —
  while §4 line 102 correctly states "triage-runnable 150 (75 T1 + 75 T2,
  post-remediation) … 144 T3 parked"; §2 line 71 "F-EVENT 2/30" (actual
  2/32). One plan, two vintages.
- **M-3: PASS_BARS_V2's closing matrix asserts P4a/P4b/P4c as GOVERNING with
  no body section defining them.** `policy/PASS_BARS_V2.md:545-547` lists
  P4a (B5 CLOCK-GATE), P4b (B6 INVERTED), P4c (B7 LAGGED) with strict
  conditions, but the document's body defines P1, P2, P3, P5, P6, P7, P8
  only — no P4 section (formulas, fail close-codes, edge cases; B7's
  first-fold handling). The semantics are inferable (P1-shape vs each
  baseline; B5-B7 realization laws exist in §1) but the bar authority is
  incomplete exactly where it declares governance.
- **M-4: skeptic F-11's two PBO/CSCV edge rules remain unpinned (the dedup /
  N_eff half of F-11 did land).** `policy/PASS_BARS_V2.md:341-371`: the
  exclusion rule covers trials with no returns in a CSCV block for
  *ranking*, but ω_c is still undefined when the TRAIN-best trial n*(c) has
  no returns in that combination's TEST blocks; and the "out-of-sample rank
  fraction" normalization (rank/N vs rank/(N+1)) is not pinned, which
  matters at the λ=±∞ extremes the spec does define.

### LOW (3)

- **L-1: stale sub-number in the session-2 owner report.**
  `SESSION_REPORT.md:23` "D-CARRY 0/13" (actual post-delta 0/11; the
  grouping documents the 0/13→0/11 transition).
- **L-2: residual "tick-volume" wording in two owner-facing spots.**
  `plan/PLAN_..._DRAFT.md:162` ("declare its tick-volume proxy" — should be
  size-weighted volume per erratum I-3 / spec r1) and
  `eligibility/PORTFOLIO_ELIGIBILITY_SUMMARY.md:84` ("the tick-volume
  field"). Load-bearing sections (class spec §3, triage reasons) are clean.
- **L-3: minor stale phrases.** `campaign/BACKTEST_CAMPAIGN_DESIGN.md:117`
  annotation still says "147 runnable at the 292-row vintage, being updated
  for the 294-row delta" (the update landed: 150);
  `journal/fixtures/README.md:30` "same in all five" (six fixtures since
  fx6); SUMMARY title says "ladder v2" while its headline says v2.1.

### INFO (4)

- **I-1:** git state (branch, uncommitted-ness) NOT verified by this audit —
  A7's own law forbids git operations. Governance claims about the tree come
  from the charter/session report and the file inventory.
- **I-2:** SESSION_REPORT session-1 section retains pre-amendment numbers
  (≤24 arm-executions, 300 ledger rows) — explicitly headed "superseded
  numbers inline"; acceptable as history.
- **I-3:** amendment §3 presents the 292-row ladder-v2 partition as executed
  state — true at its recording moment; plan v2/grouping document the v2.1
  regeneration (294). Historical record, not a defect.
- **I-4:** positive verifications worth recording: registry contains 0 rows
  for this cycle and `plans/` contains no file for it; GO phrases appear only
  in plan §9 explicitly marked NOT consumable (lines 171-179); the F-4
  disclosure layer exists (plan §2 overlay paragraph; SUMMARY reading rule 0)
  even though 89 PIT_UNPROVEN-verdict rows remain admitted under the keyword
  screen (disclosed, mitigated by the triage's binding T3 layer).

## 2. D1–D10 checklist

| # | check | verdict | evidence |
|---|---|---|---|
| D1 | Governance | **PASS** | Plan is DRAFT v2 / NOT REGISTERED (plan lines 3-6); 0 registry rows for PORTFOLIO-COMPOSITE (`plans/CYCLE_REGISTRY.json` grep = 0); no plan file in `plans/`; package file inventory contains no registry/ledger/MAP/LESSONS artifacts; GO phrases only in plan §9 marked "NOT consumable from this document", "dies unconsumed (P-8)"; amendment recorded verbatim (Vietnamese owner text quoted in full); charter stop-point law present; no scored cell / S1 / orders claimed anywhere (every lane artifact carries HYPOTHESIS/NOT_RUN; fixture PnL numbers are synthetic accounting gates, labeled as such). Limitation: git state not verified (I-1). |
| D2 | Eligibility chain | **PASS** | Builder re-run (output redirected): TSV + counts JSON byte-identical to disk; 1,200 rows / 1,200 unique gids; provenance vs census 0 mismatches; label rule 0 deviations; F0 15/15 exact; ladder v2.1 = 294 with per-symbol 56/80/51/52/55 (re-measured); 12-row spot-check incl. all F-4/F-5 repair rows verified (§0.2-0.4). |
| D3 | Triage | **PASS** | 294 rows; T1 75 / T2 75 / T3 144 (totals + per-symbol + per-family re-counted from the TSV); joins to EC set exactly, 0 field mismatches; USDJPY-S012 = T2, F0_INDIVIDUAL_REJECT; USDJPY-S020 carries MECHANIZATION_DEVIATION in its reason; grep of EFFR/SOFR over the TSV = 0 hits and no SOFR-evidenced claim anywhere in the package (only skeptic quotes of the old error and UNEVIDENCED statements). |
| D4 | PASS bars v2 | **FAIL (2 of 8 sub-checks)** | F-1 FIXED (P5a = "DSR > 0.95" governs at §5 line 311, equivalence 314-318, matrix line 548; the only "DSR > 0" strings are repeal-provenance notes, lines 23/301). F-2 FIXED (B2 = equal split of the policy's realized total heat target, §1 line 133; N=1 natural coincidence, §3 lines 214-217). F-3 FIXED (E-Law 8 identities-vs-seeded-sub-runs, lines 110-119; plan §4 B4 line "≤128 seed sub-runs, own disclosed budget line"). F-6 FIXED-BY-DISCLOSURE (PSR companion REPORTING + IS/OOS double-correction disclosure, lines 327-339). F-7 FIXED (fold-edge asymmetry disclosure + mandatory per-arm companion table, lines 72-82). F-17 FIXED (B3 obj_B3 frozen + 4-step tie-break, line 134). F-11 PARTIAL → M-4. Closing-matrix-vs-body consistency FAILS on P4a/b/c → M-3. |
| D5 | Accounting | **PASS** | Dual-source C2 table verified verbatim against BOTH cited authorities (COST_AUTHORITY_TABLE for C1/C2-Fri/C3; DATA_AUDIT_REPORT §D(iii) / audit_summary.json for corrected Mon–Thu 1.2/3.7, 2.8/7.8, 2.1/7.4 with exact n's; the table's stale Mon–Thu column 0.6/2.7, 1.4/5.8, 1.0/4.9 correctly identified as the 22–23Z hour). All six fixtures independently re-derived from their own bars and conventions: 0 mismatches at 1e-9 (fills, crossing lines, commissions, swap calendar with Wed ×3, timeline, totals, gross-vs-mid, net, invariant; fx3 virtual attribution; fx5 guard; fx6 grading). |
| D6 | VOLPROF spec r2 | **PASS** | CTRL-B is a two-arm family (§7b): B1 day-blocked permutation retained as decomposition diagnostic with survives-by-construction stated exactly; B2 full-window permutation governs the kill with the independence argument; movement diagnostic keyed to B2; B1 outcomes are labels (POC_CROSSDAY_DRIVEN / EDGE_CROSSDAY_COMPONENT_ONLY), not kills; §9.3 and the falsifier cells updated consistently. No residual tick-volume semantics in load-bearing sections (remaining occurrences are verbatim census quotes or descriptions of the refuted premise; L-2 covers the two cosmetic spots). Unit-invariance section §3.3 intact and clause-by-clause. Status line: CONDITIONAL_RESOLVED_AUDIT_CLEAN (header, line 8). |
| D7 | Skeptic dispositions | **FAIL (22/25 disposed)** | F×disposition table in §3: 16 fixed-in-artifact, 1 disclosed, 1 fixed-by-annotation, 1 partial, 3 affirmative-verified; **F-12, F-18, F-22 have no documented disposition** → H-1/H-2/H-3 per the A7 rubric (underlying severities MEDIUM/LOW/INFO). |
| D8 | Cross-doc coherence | **FAIL (2 stale clusters)** | Agreed everywhere current: 294 ladder (plan §4, grouping, session report), 150 triage-runnable (plan §4, session report, grouping), 1,500 discovery rows / 48 identities + ≤128 B4 seeds / ≤12 legs / DSR>0.95 (plan §4, campaign §5-6 annotation, PASS_BARS_V2, session report); V1/V2 supersession annotated (architecture §10 + PASS_BARS_V2 header); no 292-as-binding or 147-as-final claim (skeptic/handoff uses are records of the review moment). FAILS: SUMMARY sub-counts (M-1) and plan §2 sub-numbers (M-2) are 292-vintage and internally contradictory; minor L-1/L-3 residues. |
| D9 | Handoffs | **PASS** | 5/5 handoffs schema `zcode_orch_v3_handoff@1`, status DONE (D, M, P, R, S); remediation logs with old→new sha256 present where remediation occurred (M: spec 2ee2832f→dedbc6c7, verified on disk; P: FILL_ACCOUNTING e1957525→a1ed4928 (rev 1) → b5bd0b6a (final, on disk); R: GROUPING 7e8cc533→395f3618, triage 465b378c→2d258d41, both verified). **All 12 pinned sha256 values match the current on-disk files — zero mismatches.** D and S were not remediation lanes (D is the erratum source; S is the reviewer). |
| D10 | Verdict inputs | **PASS (assembled)** | See §4. Open items each correctly gated or owner-actionable; none requires new measurement. |

## 3. Skeptic F×disposition table (25 findings)

| F | severity (skeptic) | subject | disposition in revised package | A7 evidence |
|---|---|---|---|---|
| F-1 | CRITICAL | P5a "DSR > 0" vacuous | **FIXED-IN-ARTIFACT** | PASS_BARS_V2 §5 line 311 `P5a = PASS iff DSR > 0.95` + equivalence lines 314-318 + matrix line 548; only provenance mentions of the old text remain |
| F-2 | HIGH | B2 degenerate sizing | **FIXED-IN-ARTIFACT** | §1 line 133 (same-total-budget B2, F-2 provenance), §3 lines 214-217 (N=1 natural coincidence) |
| F-3 | HIGH | budget vs ≥100-seed battery | **FIXED-IN-ARTIFACT** | E-Law 8 lines 110-119; plan §4 B4 line "≤128 seed sub-runs, own disclosed budget line" |
| F-4 | HIGH | PIT screen mislabels | **FIXED-IN-ARTIFACT (classifier) + DISCLOSED (overlay)** | builder lines 44-59 (macro-first ordering, bare 'news' removed, evidenced set = vix/effr/brent−wti); USDJPY-S012/USDCAD-S048 admitted, GBPUSD-S006/S031/S040 blocked (verified on disk); plan §2 overlay paragraph + SUMMARY reading rule 0 disclose that the badge ≠ input availability; residual: the iff-sentence still says "PIT chain provable" (plan line 56) — disclosed but overstated; 89 PIT_UNPROVEN rows remain admitted by design, mitigated by the triage |
| F-5 | HIGH | SOFR falsely evidenced | **FIXED-IN-ARTIFACT** | builder maps 'sofr'→NEEDS_MACRO_PIT_UNEVIDENCED; grouping evidence table + FORBIDDEN item 5 now "only EFFR/VIX/Brent−WTI"; package-wide grep: 0 residual evidenced claims (0 SOFR/EFFR strings in triage TSV) |
| F-6 | MEDIUM | DSR under-pinned / double-correction | **DISCLOSED (accepted-as-conservative)** | §5 lines 327-339: IS/OOS double-correction disclosure + PSR (no-deflation) value mandatory alongside DSR; matrix row P5-disclosure |
| F-7 | MEDIUM | fold-edge force-flat asymmetry | **FIXED-IN-ARTIFACT (disclosure + companion)** | E-Law 2 lines 72-82: asymmetry stated, per-arm fold-edge cost companion table mandatory in every Stage-C report |
| F-8 | MEDIUM | campaign stale arithmetic | **FIXED-IN-ARTIFACT** | campaign §5 lines 98-104 (1,500 rows, ~75 false edges at α=0.05, ≤48 identities) + §6 annotation marking the tier table v1-era; residual phrase "147 … being updated" (L-3) |
| F-9 | MEDIUM | CTRL-B placebo weak | **FIXED-IN-ARTIFACT** | class spec §7b r2 two-arm family; B2 governs the kill; movement diagnostic keyed to B2; B1 outcomes = labels; sha dedbc6c7 verified on disk |
| F-10 | MEDIUM | USDJPY-S020 PIT trap | **FIXED-IN-ARTIFACT** | triage reason carries MECHANIZATION_DEVIATION (verified); grouping §1.1 convention + §5.2/§5.3 wiring; corpus text confirms the trap |
| F-11 | MEDIUM | PBO dedup / edge rules | **PARTIAL** | §5 lines 279-298: byte-identical-arm dedup + cluster-adjusted N_eff (E[max] at N_eff) + raw-N DSR reported alongside — the dedup half landed; the two edge rules did not → M-4 |
| F-12 | MEDIUM(-LOW) | two switch-cost books | **NO DOCUMENTED DISPOSITION** | GROUPING_PROPOSAL.md:588 still cell-p50-based; neither requested resolution adopted; not listed in any remediation log → H-1 |
| F-13 | LOW | fx2 step numbering | **FIXED-IN-ARTIFACT** | fx2 timeline steps 1..10 sequential (verified) |
| F-14 | LOW | swap weekday casing | **FIXED-IN-ARTIFACT** | fx2/fx5 swap_lines all lowercase (verified) |
| F-15 | LOW | swap identity over-claim | **FIXED-IN-ARTIFACT (softened)** | spec §2: "DECLARED U4/U5 realization, a frozen modeling calendar, NOT a venue-measured fact"; fixture wording updated |
| F-16 | LOW | no worst-fill fixture | **FIXED-IN-ARTIFACT** | spec §1.5 + fx6 fixture; independently re-derived clean (graded fill 1.08498 = min(bid_open,bid_close) − band, never at stop, gap excess $5.00 inside slip line) |
| F-17 | LOW | B3 definitional wobble | **FIXED-IN-ARTIFACT** | §1 line 134: obj_B3 = DSR_T(leg) at ×2.0 with ledger SR₀/N_eff + frozen 4-step tie-break recorded into the trial identity |
| F-18 | LOW | ladder v1 not reconstructible | **NO DOCUMENTED DISPOSITION** | no v1 copy/diff in the package; SUMMARY line 8's "preserved in git history" unevidenced for an uncommitted dir → H-2 |
| F-19 | LOW | campaign "3 corpus rows" stale | **FIXED-BY-ANNOTATION** | §6 annotation supersedes the v1 tier table (incl. its "3 corpus rows" line); plan §4 current |
| F-20 | INFO | F-EVENT 2/30 vs n=32 | **FIXED-IN-ARTIFACT** | grouping §1.2 table F-EVENT n=32 (2/0/30) + §1.3 item 2 "2/32" with the 28+2 breakdown |
| F-21 | INFO | VERIFIED CLEAN (accounting core) | **STANDS (affirmative)** | A7's own independent engine concurs: 6/6 fixtures clean at 1e-9; dual-source cells verbatim-faithful |
| F-22 | INFO | ARTIFACT_PINS.json missing | **NO DOCUMENTED DISPOSITION (open)** | manifest dir has builder only; plan §10 ties the manifest digest to the registration receipt → H-3 |
| F-23 | INFO | tick-volume terminology | **FIXED-IN-ARTIFACT** | triage reasons renamed (EURUSD-S010 verified); residuals only in plan §8 / SUMMARY wording (L-2) |
| F-24 | INFO | VERIFIED CLEAN (dead-ancestor tension disclosed) | **STANDS (affirmative)** | plan §0, architecture §0 table, amendment §4, class spec §8, grouping §6 all carry the honest framing |
| F-25 | INFO | VERIFIED CLEAN (containment) | **STANDS (affirmative)** | A7 re-derived the label rule over all 1,200 rows: 0 deviations; triage joins 294/294; no current-panel fold outcome exists anywhere |

Tally: fixed-in-artifact 16 · disclosed 1 · fixed-by-annotation 1 · partial 1 ·
affirmative-stand 3 · no-documented-disposition 3 = 25.

## 4. Owner-facing verdict (D10)

**Is the package READY FOR OWNER REGISTRATION DECISION?** Not quite. The
substance is in materially better shape than the skeptic's REVISE_BEFORE_OWNER
moment: every blocking text defect the skeptic identified (F-1..F-5) is
verifiably repaired on disk, the accounting core reproduces under a second
independent engine, the eligibility chain is deterministic and byte-faithful
to its inputs, the triage overlay is the binding input-availability layer it
claims to be, and every handoff pin matches. What remains is a bounded
text-and-generation pass, not new measurement — but it touches exactly the
documents the owner reads at the gate (the eligibility SUMMARY contradicts
its own headline; plan §2 contradicts plan §4; the bar authority's matrix
references an undefined P4; three skeptic findings went quiet without a
disposition; the promised pin manifest was never generated).

Open items and their gating (all cheap, none measurement-bearing):

1. H-1/F-12 — pin `switch_cost_usd` to journal realized crossings or add the
   divergence-tolerance sentence (grouping §4.2).
2. H-2/F-18 — stage a ladder-v1 snapshot/diff in the package or strike the
   "preserved in git history" claim (SUMMARY line 8).
3. H-3/F-22 — run `manifest/build_pins.py` before the owner packet (plan §10
   makes the registration receipt freeze this digest).
4. M-1/M-2 — refresh the SUMMARY and plan §2/§0 sub-counts to the on-disk
   v2.1 numbers (110/41/23 blocked; 223/59/12 labels; 75/75/144 triage;
   0/11 and 2/32 family falls; per-symbol 56/80/51/52/55; families per
   builder).
5. M-3 — add the P4 body section (or explicitly defer P4a-c definitions with
   an edge-case pointer).
6. M-4 — pin the two CSCV edge rules (ω_c undefined case; rank-fraction
   normalization).
7. L-1..L-3 — wording cleanups (D-CARRY 0/11; tick-volume proxy; "147…
   being updated"; "all five"; SUMMARY title v2 vs v2.1).

Correctly-gated external items (no action required pre-registration, each
already gated): tzdata version pin (engine freeze at Stage-A); release/holiday
calendar archive staging (class-iii prerequisite, ~20 T2 rows, slate survives
refusal via declared-off fallbacks); IBKR Activity/Flex statement (P_A — the
API channel explicitly does NOT substitute); program-wide C2 Mon–Thu
COST_AUTHORITY_TABLE correction (SLEEVE-FX5 owner; PC12A side already
dual-sourced); FAMILY_FAILURES asset-label erratum (post-registration writable
lane); registration itself remains the owner's typed §9 phrase with A7
prelaunch still to come fresh at its own gate.

## 5. Verdict

Findings: **0 CRITICAL · 3 HIGH · 4 MEDIUM · 3 LOW · 4 INFO** (the 3 HIGHs are
rubric-elevated undisposed skeptic findings with underlying severities
MEDIUM/LOW/INFO; none is an integrity hole). D-checklist: 7 PASS · 3 FAIL
(D4, D7, D8 — each on enumerated sub-checks) · 0 NOT_RUN.

A7_PREREVIEW_VERDICT: REVISE_BEFORE_OWNER
