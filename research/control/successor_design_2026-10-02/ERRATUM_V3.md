# ERRATUM_V3 — round-3 corrections to successor_design_2026-10-02 (co-owner F1–F5)

v2 committed as `cfb7ae57`. Round-3 co-owner review (F1 sample/power +
floor causality; F2 freeze timing; F3 exposure/sealed audit; F4 residual
contradictions; F5 canonical budget) was executed by two parallel review
lanes (sample-power/floor-causality; freeze-timing/exposure-lineage — both
read-only, no sealed bytes, no PnL computation) plus the controller. Every
change is itemized below; v2 text survives in git at `cfb7ae57`. Frozen
DAILY artifacts were NOT edited — the lineage defect found is disclosed,
not repaired in place.

## F1 — Sample/power + floor causality

New file `SAMPLE_FEASIBILITY_MATRIX.md`: per-hypothesis/per-arm feasibility
rows (denominator & surface, measured rate, clustering, expected counts on
LEARN 26w/39.86w and 6×26w validation, applicable floor, Poisson P(unmet)
with stated assumptions, verdict + typed consequence). Headlines: HN-1-EUR
VAL window floor at 24–32% risk; both HN-1 LEARN grids expected
NOT_RUN_GRID_THIN (70–100% unmet — the de-bias re-learn is expected
inoperative); S017 refutation STRUCTURALLY UNDERPOWERED (P(meet ≥50) ≈
0.03%; expecting 50 needs ≈10.3 folds ≈ 5.1y — expectation math); HN-3
pooled floor a 33–65% coin-flip (evaluation UNIT frozen at FREEZE-1:
decision-unit ≈108 pooled vs ≥20 comfortable, entry-unit coin-flip);
S014's 3.6 entries/fold ⇒ expecting the 100-aggregate needs ≈27.8 folds ≈
13.9y; S023/VC2-JPY LOL pre-typed thin; J3 m∈{1.5,2.0} node feasibility
NOT ESTIMABLE pre-run (spend-band histogram action added). Aggregate-floor
reading ambiguity (per-leg: 8–9 of 12 legs fail; pooled: trivially passes)
flagged as a FREEZE-1 election. **No floor loosened anywhere.**

**Floor-causality defect (v2 design §1) — REPEALED and replaced.** v2's "a
leg whose per-fold decision floor fails is FLAT for THAT fold (DAILY
precedent)" is fold-total lookahead. The lane PROVED the DAILY precedent
implemented exactly that: the 24 BLOCKED_FLOOR rows exist only in the two
sub-3-fire folds, at mid-fold timestamps, with reason text naming the
per-fold floor, and the DAILY journal schema has NO trailing-count field (a
lawful trailing rule would have blocked early decisions in ≥3-fire folds
too). Bounded impact: 3 would-be fires suppressed across arm-replays; a
trailing-26w ECO floor would have admitted them; DAILY's exploratory-
negative conclusions unaffected. Replacement: the two-layer INF/ECO law
(INF = fold-close typing only, never touches trades; ECO = trailing-only
PIT suppression with a FREEZE-1-frozen seeding/cold-start law), with
pseudo-code and the T1–T4 truncation-replay test spec the successor engine
must implement and A7 prelaunch must pass (design §1; matrix §floor-
causality). No retroactive fold-zeroing, ever.

## F2 — Freeze timing

v2 §3.1 froze LEARN-learned VALUES at registration while stage 4 learns
them — contradiction. Replacement (protocol v3 §2): **FREEZE-1 at
registration** freezes the search space (grid node lists), selection
objective, deterministic LEARN-only algorithm, NOT_RUN_GRID_THIN collapse
law, membership elections, calendar variant, budget, floors law (INF/ECO),
risk caps, warmup pins; **FREEZE-2 after LEARN** freezes the learned
values + engine code SHA + data manifests + selection audit trail. **GO
gate:** fold-1's first session starts strictly after max(FREEZE-2, A7,
GO); v2's variant-A "fold 1 = 2026-10-02" (δ=0) is UNLAWFUL under v2's own
stage law. Dates are now ILLUSTRATIVE pending actual anchors:
`end_A(δ) = R+δ+1092d` (δ=1w → 2029-10-05; δ=4w → 2029-10-26);
`end_B(δ) = max(L+δ+1, L+7)+1091d` (δ=1w → 2030-04-04; δ=4w →
2030-04-25); the calendar script now emits `anchor_status_v3` with the
gate law and marks everything PENDING_ILLUSTRATIVE. Purge/embargo now has
a per-family basis table (HN-1 0d + force-flat; E2/HN-2 26w feature-warm;
J3 28d state election; multimonth legs via LEARN-end force-flat). Warmup:
v2's "trim B's warmup to 26w" is REPEALED as an unlawful trim — the corpus
code/configs give per-leg warmups (S002 230td≈46w, S003 290td≈58w, S014
230td, S009 277td code-derived, S023 142td code vs 140 config, …), and
under variant B four legs (S002-JPY, S003, S014, S009) reach into the
owner-typed tail at fold-1 start → option triple frozen per leg at
FREEZE-1: (i) tail-as-warmup for FEATURE inputs only, (ii) fold-2
admission typed NOT_RUN_WARMUP, (iii) not admissible. Three corpus warmup
constants are unpinned (S009 config omits the field; S023 140<142; VC2
profile window) — pinned at FREEZE-1.

## F3 — Exposure / sealed lineage

Protocol v3 §1 replaces the v2 ledger with per-axis verdicts:
battery-execution authorization PROVEN (two-key GO); tail-reads-as-S1-
unseal **NOT_RUN_UNPROVEN** (no artifact names the tail in any election;
the GO record asserts the opposite); statistical exposure **PROVEN
EXPOSED** (manifests contain all tail dates; DAILY journals contain
tail-dated FILLED rows 2026-01-28…06-10; G5 bands derived on the full
window); tail-as-untouched-validation **REFUTED**; same-bytes **PROVEN at
hash level** (DAILY sha-verifies the identical .bi5 files PC12A froze);
separate-S1-store existence NOT_RUN_UNPROVEN. **Recorded lineage defect
(disclosed):** DAILY's committed chain asserts "S1 SEALED_UNTOUCHED /
throughout" in three places (GO record, plan §0b, TERMINAL_DECISION) while
its own journals disprove it; frozen artifacts stay append-only — owner
action D-1a (retroactive ratification or DAILY-side erratum) resolves the
axis. Standing-directive timeline added: the "stays SEALED" directive
predates DAILY's tail-opening fills by ~4h the same morning; nothing
connected them. Sealed-tail LENGTH discrepancy (CAM "26-week" vs owner
176d=25.1w) flagged for registration pinning. The v2 grep over-claim is
replaced with scope-honest wording (three trees searched; repo-wide
unreadability NOT_RUN_UNPROVEN; the collector streamed live post-09-23
ticks by design — metadata-only logging, schema gap disclosed).

## F4 — Residual contradictions (all fixed)

1. design §1 tier C no longer lists "cost statement" as admission-mandatory
   (component-wise law; statement = optional upgrade).
2. design §4 capacity re-anchored to owner-declared limits / measured
   execution history — a statement measures commission/swap attribution,
   NOT capacity.
3. design §5 C2 row now labels the 128/128 figure a DP §2.3 DIAGNOSTIC
   (PC12A's B4 never executed); seeds declared in the
   multiple-testing/compute denominator though on their own ledger line.
4. register HN-1: "the SAME structural window" → POSTULATED (POST_OUTCOME)
   shared mechanism; placebo/clock-shadow are the promote/kill controls.
5. design §0-2: MAE/MFE + attribution journaling scoped to FORENSICS;
   marginal contribution only via FULL-PATH replay arms (LOL/LORO re-run
   the whole netting/caps/cost path; per-leg PnL arithmetic banned as a
   marginal-contribution estimate); trig/pfold/solo named DIAGNOSTICS.

## F5 — Canonical budget/slate

New machine-readable authority: `analysis/arm_manifest.json` (every arm:
id/class/composition/tier/folds/rows/option membership; canonical
resolutions: LOL over ADMITTED legs only — no LOL/S017, its contrast rides
LORO(G1); LORO(J3) realized as guard-IN; C2 rows inside; ×2.0
identity-classified) + `analysis/verify_arm_manifest.py` (recomputes all
totals; structural checks). **Canonical numbers: Option A 30 core / 32
with-HN-5 identities, 174/186 scored rows, max 35/204, total 216, caps
≤39/≤228; Option B 24/26 identities, 138/150 scored rows, max 29/168,
total 180, caps ≤32/≤198** — v2's 33/192 A and 27/156 B superseded (their
LOL sets included retired/benched legs; the controller also caught and
corrected one lane-prose arithmetic slip in v2's Option B). Reserve = 3
identities, TECHNICAL re-runs only, never new hypotheses after FREEZE-2,
never PnL search; headroom spendable only by pre-FREEZE-2 amendment.
Selection deterministic TRAIN-only. Alternatives (LOL-over-12, C2-outside,
×2.0-rows-only) live ONLY in this erratum's appendix note, not in the
design.

**Two-track practical framing added (protocol v3 §5):** Track 1 HISTORICAL
EXPLORATORY (TB-LABELS, journal forensics incl. the J3 spend-band
histogram, full-path LOL/LORO replay design/execution on EXPOSED folds as
its own registered exploratory identity, cost/mechanism checks under
DECLARED+stress — start immediately, never independent validation, every
new scored computation needs its own cycle/gates/GO) vs Track 2
PROSPECTIVE (the 6×26w battery after FREEZE-2+A7+GO; pre-declared sample
milestones; interim typed diagnostics allowed; acceptance bars unchanged).
Recommended priority: TB-LABELS + forensics first (they feed registration
inputs), then the exploratory replay (membership-election evidence), with
Track-2 registration whenever the owner is ready — 2029/2030 are
full-battery dates, not research start dates.

## Verification

Both lanes' arithmetic re-verified by the controller; the manifest totals
are machine-verified (`verify_arm_manifest.py` ALL MATCH); a fresh-context
skeptic audited the revised packet against these five items and the
protocol invariants (verdict + dispositions in `SKEPTIC_REVIEW_V3.md`).
Boundaries: 0 scored runs, 0 S1/sealed bytes read, 0 registrations, 0
closed-budget reuse; owner dirty tree and futures lane untouched.


## Appendix — superseded v2 alternatives (record only; NOT current budget)

Kept here because design §6 and this erratum reference them; the authority
is `analysis/arm_manifest.json` alone. The v2 tables (git `cfb7ae57`,
ERRATUM_V2 §1) differed from canonical v3 as follows: LOL was declared over
12 legs INCLUDING retired S017 and benched VC2 pairs (A: 33 committed ids /
192 scored rows; B with 6 LOL incl. S017: 27/156 with HN-5); the C2-outside
convention (DAILY style) read 186/150 committed rows (A/B); the
×2.0-rows-only convention read −2 identities. Also recorded: the budget
lane's own prose slip (Option B "29/168 with-HN-5" vs table-consistent
27/156) caught by controller verification. Canonical v3 superseded all of
these by declaring LOL over admitted legs only (A 11 / B 5 live), C2-inside,
×2.0 identity-classified — one number per option.

— end erratum v3 —
