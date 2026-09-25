# INDEPENDENT FRESH-CONTEXT REVIEW — THREE DRAFT AMENDMENT PLANS (A1-FX / A2-BANDRIDGE / A3-XSECT)

- Role: quant-auditor (A7-class, fresh context). Audit only — no repair, no
  scored computation, no commit, no worker action.
- Measured: 2026-09-25, root checkout `main` @
  `376311a5aac02fb14cef65d2b1e4faaa93285213` (= dispatch sha; verified
  `git rev-parse HEAD`). Read-only except this report + the handoff JSON.
- Objects: `plans/DRAFT_amendment_FX-RANGEFADE-2M-SHADOW-V1_A1_controls.md`,
  `plans/DRAFT_amendment_PSCTV1_A2_bandridge_pins.md`,
  `plans/DRAFT_amendment_PSCTV1_A3_xsect_retire.md` — all status
  DRAFT_FOR_OWNER_GO, none registered, none executed (confirmed in bytes).
- Authorities read in full/relevant-part: umbrella
  `plans/PLAN_economic_robustness_program_v1.md` §1.3, §2, §3, §4.1, §4.3,
  §4.5, §4.7, §5.4, §5.6, §5.7, §5.15, §8, §9, §10;
  `plans/PLAN_fx_rangefade_2m_shadow_v1.md` (full);
  `plans/PLAN_prospective_shadow_v1.md` §2, §3.2, §3.3, §4, §6, §7, §8, §9.6,
  §13, §14, G3, Amendment A1; `OWNER_DECISIONS.md` D1–D10;
  `EXPLORER_state_remeasure_REPORT.md` (measured-state authority);
  `DATACOST_critic_REPORT.md` §1.2/§1.4; registry `plans/CYCLE_REGISTRY.json`
  (re-read: FX-RANGEFADE-2M-SHADOW-V1 = ACTIVE_LIGHT/REGISTERED;
  PROSPECTIVE-SHADOW-V1 = ACTIVE_LIGHT; ECONOMIC-ROBUSTNESS-PROGRAM-V1 absent
  = not registered — all three drafts' hedged citations are correct).
- Code-level verification performed (read-only greps):
  `.worktrees/prospective-shadow-v1/integration/research/control/
  prospective_shadow_v1/e/shadow_worker.py` L180 `FEE_RATE_CURRENT = 0.0005`
  (module-global), consumed at L508/L524 (`cost_books_for()`) — see A2-H1.

---

## VERDICTS

| Draft | Verdict | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| A1 FX-RANGEFADE controls (D2) | **PASS_WITH_FINDINGS** | 0 | 2 | 3 |
| A2 PSCTV1 BANDRIDGE pins (D3) | **REMEDIATION_REQUIRED** | 1 | 1 | 3 |
| A3 PSCTV1 XSECT retire (D4) | **PASS_WITH_FINDINGS** | 0 | 1 | 3 |
| **Set overall** | **PASS_WITH_FINDINGS** | **1** | **4** | **9** |

One HIGH finding (A2-H1) must be remediated **in the draft text before the
owner types the A2 GO phrase**; it is a one-sentence scoping fix plus one
regression fixture. No draft contains any authorized-implementation leakage;
all three correctly stop at their own GO gates.

---

## DRAFT 1 — A1 CONTROLS (FX-RANGEFADE-2M-SHADOW-V1, owner D2)

### A. Fidelity to D2

D2 (verbatim intent): planning-level approval — short-beta control +
aggregate USD exposure + event-time stress-spread + fee/slippage field;
parameters & trading behavior unchanged; independent review then STOP at its
own GO gate.

- All four elements present and only those four: §1.1 control arm (C-FX-1),
  §1.2 USD exposure (C-FX-2), §1.3 stress book (C-FX-3), §1.4 ledger cost
  fields (C-FX-4). Status banner correctly states nothing is live law before
  the owner GO; §4 stops at `GO FX RANGEFADE AMENDMENT A1 CONTROLS MOUNT`.
- Freeze language is strong and testable ("any diff that changes a
  live-sleeve decision, fill, size or force-flat behavior ... rejects the
  amendment"; §3(e) no-diff proof over frozen paths).
- Registry claim verified: FX-RANGEFADE-2M-SHADOW-V1 is ACTIVE_LIGHT in
  `plans/CYCLE_REGISTRY.json`; the draft's "if registered; cited as draft law
  otherwise" hedge for the umbrella is accurate (umbrella is not registered).

### B. Parent-law safety

Zero change to live parameters/behavior/sizing/clock — control arms are
declared VIRTUAL with no orders; stress book is "reported alongside, never
merged into primary PnL"; worker restart deferred to the implementation
cycle's own gate. No sentence authorizes more than D2 except the two flagged
below (A1-M1 lineage claim, A1-L1 draft-added inverted control).

### C. Technical correctness

- **CTRL-SHORT-ALWAYS is well-defined on weekends and holiday-thin days.**
  "Each weekday" + "first fillable H1 open" inherits the parent fail-closed
  data law (DATA_STALE → no decisions, FX plan §2); weekend flat is the
  parent's own law; force-flat at the sleeve's own 20:00 UTC boundary is a
  no-op if no entry occurred. No undefined state found.
- **Session-bucket sourcing is sound in kind**: the sha-pinned Dukascopy
  census is a real, authority-cited artifact (umbrella §5.4 "spreads
  0.3/0.8/0.5 pips p50" — the draft's "global 0.3-pip median" reference
  checks out; critic §1.2 condition 3 and lane-F dossier
  `f_cost_authority_dossier.json` both exist on disk). USDJPY is correctly
  absent — it is a Track-A cohort replication target (umbrella §5.4), not a
  sleeve pair, and the draft adds no pair. Residual: the draft names source
  families but not exact sha-pinned curve files per pair — the implementation
  gate must pin EURUSD **and** GBPUSD curve hashes explicitly.
- ×2.0 multiplier = umbrella §8 frozen FX stress tier ✓; "quarterly
  re-census, dated hash boundary, never in-place rewrite" is consistent with
  §8 ✓ (cadence itself is draft-proposed — A1-L3).
- §1.4 field set supports exactly the C-FX-4 purpose (round-trip win-rate
  via `round_trip_id`/`realized_net`); NOT_RUN_COST_FIELDS for old rows
  matches umbrella §4.7 and NOT_RUN semantics ✓.

### D. GO-gate hygiene — PASS. Own gate, fresh phrase, "typed early = intent
only, dies unconsumed per P-8" stated twice; implementation cycle opens only
after GO, with its own A7 prelaunch arc (umbrella §5.6 law correctly cited).

### E. Append-only — PASS. §1.4 explicit: existing rows never backfilled.

### F. Cross-draft consistency — PASS. §2 pins control-arm cost book =
sleeve cost book (same H1 open, same opposite-quote rule) — the exact
consistency the umbrella demands. One advisory carried in the body below
(stress-view symmetry on control fills).

### Findings

- **A1-M1 (MEDIUM)** — CTRL-SHORT-ALWAYS is defined as a weekday day-session
  short (00:00→20:00Z, re-entered daily) but is presented as "the
  ancestor-mandated short-beta reference" with the ancestor's +314.0-pips
  figure. The ancestor SHORT_ALWAYS (EURUSD-RANGEEXP-SCORED-V1 §2:
  "baselines recomputed identically per cell window") is a window-long short
  including overnight; the prospective control will NOT be numerically
  comparable to +314.0. Advisory: add one line disclosing the definitional
  difference (or match the ancestor definition), so the mandated comparison
  is not silently redefined.
- **A1-M2 (MEDIUM)** — §2 primary book "declared fee schedule + measured
  spread-at-fill (as today's design intends)" is not true as measured: the
  journal today books gross price movement only and has zero cost fields
  (explorer §2.2), and no declared FX fee schedule exists in the parent plan.
  Advisory: pin the declared components (commission buffer level etc., per
  the critic's five conditions) or state explicitly that the primary book
  stays gross with costs as reporting fields until the owner pins a schedule.
- **A1-L1 (LOW)** — CTRL-SHADOW-MATCHED (inverted control) is a draft
  addition beyond D2's four named elements; defensible under umbrella §5.7
  but tag it "draft-added" for explicit owner affirmation at GO.
- **A1-L2 (LOW)** — "Display-only per owner D10" vs C-FX-2's "display +
  record" duty: the record duty IS stated in §1.2; reword to "display +
  record, no caps, no behavior change" to remove the misreading risk.
- **A1-L3 (LOW)** — Quarterly re-census cadence is draft-proposed, not in
  D2/§8; mark it as proposed for preregistration at the implementation gate.
- Body note (no number): state whether the stress view also prices
  control-arm fills — symmetric stress reporting is what makes
  sleeve-minus-control a clean comparison at stress tier too.

---

## DRAFT 2 — A2 BANDRIDGE PINS (PROSPECTIVE-SHADOW-V1 sleeve 4, owner D3)

### A. Fidelity to D3

D3: do the law-pinning NOW, before the first fill — sizing B + fill law A +
KEEP 6 bps/side in identity; executor hash-verified before any fill has
evaluability; two cost laws may not coexist.

- All three pins present (P-1/P-2/P-3) plus the hash-match enforcement
  (P-4) that operationalizes D3's "hash-verified" clause; the
  `UNPINNED_COST_LAW — NOT PROMOTABLE` fail-closed label with "can never be
  promoted, only disclosed" matches C-BR-3 and umbrella §8 exactly.
- Pins land before the first fillable decision produces a fill — matches the
  measured window: 61 rows, 0 fills ever, gate continuously ON (explorer
  §1.4), so the pins are still in time.
- C-BR-4 disclosure carried forward verbatim-in-substance (§2) ✓.

### B. Parent-law safety — ONE HIGH FINDING (A2-H1).

The draft's pin set itself is exactly D3's three pins. But two sentences are
not scoped to sleeve 4 and, read literally against the verified production
code, authorize more than the owner approved:

- **A2-H1 (HIGH)** — §3 "executor cost constant → 6 bps/side" and P-3 "the
  current shared digest `130d2e7e…` stops applying to new records" are not
  scoped to BANDRIDGE. Verified in production bytes: `e/shadow_worker.py`
  L180 `FEE_RATE_CURRENT = 0.0005` is a module-level global consumed by
  `cost_books_for()` (L508/L524) **for every family**; `130d2e7e…` is the
  shared cost-regime digest of CARRY (52 booked fills) + BASISLV +
  BANDRIDGE (explorer §1.1/§1.3/§1.4). A literal global flip would move the
  live cost law of two running sleeves mid-run — beyond D3 (which is
  BANDRIDGE-only), a violation of PSV1 §6 ("Cost assumptions cannot move
  during the run") and §4 (no lowering/raising of costs outside a new
  identity), and it would contaminate every future CARRY/BASISLV adjudication.
  **Remediation before GO (one sentence + one fixture):** scope the re-pin
  and the new dated cost-regime digest to BANDRIDGE records only; state
  explicitly that `130d2e7e…` remains the cost-regime digest of
  XSECT/BASISLV/ILLIQ; add a regression fixture proving the other three
  sleeves' cost books and digests byte-unchanged.

### C. Technical correctness

- **6 bps re-pin mechanics are otherwise consistent with the identity-manifest
  language**: PSV1 amendment A1 pins `fee_bps_per_side: 6.0` in the identity
  manifest (families[3], explorer §4b); PSV1 §6 and umbrella §8 both mandate
  "dated cost-regime boundary + new frozen hash, never in-place rewrite" —
  the draft's dated boundary row + digest override + hash-match assertion is
  the correct mechanism, and P-3/P-4 landing together with the boundary at
  GO consumption is coherent. The only defect is scoping (A2-H1).
- **Sizing-B realized ≈ 0.99946 is arithmetically plausible** — see A2-L1:
  the measured 0.99946 (SHADOW-PAPER-REVIEW packet, cash guard
  `qty·fill_price + fee ≤ cash`, fill = ref + 1 tick) sits where the
  formula predicts (≈ 1/(1+fee) ≈ 0.99950 at 5 bps; the small residual is
  tick/ref). But at the pinned 6 bps identity the expected realized fraction
  becomes ≈ 0.9994 — the draft pins a constant measured under the cost law
  it is replacing.
- Fill law A matches C-BR-2 verbatim and the BASISLV sleeve-2 precedent
  (PSV1 §3.2: "first completed 15-minute bar strictly after the decision")
  ✓; the doc-vs-executor finding it closes is the one recorded at a8062b1a.

### D. GO-gate hygiene — PASS. Distinct phrase
`GO PSCTV1 AMENDMENT A2 BANDRIDGE PINS`, own gate, P-8 cited, no
implementation before GO.

### E. Append-only — PASS. "backfill is forbidden", pre-boundary rows parse
unchanged, no backfill of the 56 fail-closed rows, restart-idempotence
required.

### F. Cross-draft consistency — PASS with A2-H1. "Measured funding per
settlement unchanged" preserves the amendment-A1 identity; CONDITIONAL_KEEP
concentration disclosure carried (§2); no conflict with A1/A3.

### Findings

- **A2-H1 (HIGH)** — as above; remediation is a scoping sentence + regression
  fixture, in the draft, before the owner GO. Advisory: after the fix this
  draft is GO-ready.
- **A2-M1 (MEDIUM)** — the implementation home names the bandridge
  computation home + "PSV1 ledger adapter", but the three pins physically
  live in the PSV1 production executor
  (`integration/research/control/prospective_shadow_v1/e/shadow_worker.py`,
  `accounting.py` fee/fill lines per explorer §4a/§4b). Advisory: name the
  exact executor files in §3 so the bounded change-set is addressable and
  cannot drift into the wrong worktree.
- **A2-L1 (LOW)** — pin the sizing-B formula, not the stale "≈ 0.99946"
  constant (measured at 5 bps; ≈ 0.9994 at the pinned 6 bps).
- **A2-L2 (LOW)** — P-1 "packet owner-field closed with digest": the packet
  lives in `research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/` (owner
  path, P0-4 no-write for lanes). Advisory: closure must be owner-performed
  or via an appended record + digest reference, never an in-place lane edit.
- **A2-L3 (LOW)** — test battery lacks a sizing-B hand-computed cash-guard
  fixture (fill-law, hash-mismatch, boundary and no-diff fixtures are
  listed; the sizing pin is not fixture-covered).

---

## DRAFT 3 — A3 XSECT RETIRE (PROSPECTIVE-SHADOW-V1 sleeve 3, owner D4)

### A. Fidelity to D4

D4: planning-level approval of identity retirement; keep all history; pin
the stop-open timestamp via a separate amendment; the worker is NOT stopped
by the decision.

- §0 header restates this accurately; R-1's `T_ret` is set only at the
  amendment's own GO gate (the "separate timestamp freeze"); §2 explicitly
  does not stop/restart the worker — the scheduler keeps emitting decision
  rows after `T_ret`; §2/§5 forbid touching other sleeves and any ledger
  byte. All four D4 clauses are present; nothing added beyond D4 except the
  successor-law restatement, which is the umbrella's own C-XS-2 carried
  into the amendment as §4.5 requires ("the binding conditions columns are
  what a child cycle/amendment must implement").
- §0 measured basis verified against the explorer authority: 11 decisions /
  52 fills / −349.85 booked / fee 286.43 + slip 68.02 vs funding +4.60 →
  354.45/4.60 = 77.0 ≈ 77:1 ✓; turnover ~0.62×/day ✓; ~11%/yr vs ~1.7%/yr ✓;
  `CANDIDATE_FAIL` top-fold 51.66% matches PSV1 §3.3 ✓.

### B. Parent-law safety

The only live-behavior change (stop-open + final flat + terminal row) is
exactly the owner-approved C-XS-3 mechanics. The worker-continuity clause
preserves D4's "worker not stopped" precisely. No over-authorizing sentence
found.

### C. Technical correctness

- **Stop-open vs 24h rebalance law is coherent.** The frozen mechanism
  (PSV1 §3.3) rebalances daily at 00:00Z, so every holding at `T_ret` is by
  construction < 24h old; "run to natural frozen-law expiry → book to flat
  at the next daily boundary" is the correct terminal reading of C-XS-3's
  "book remaining holdings to natural expiry per frozen law", and residual
  exposure is bounded by < 24h. The draft explicitly authorizes the single
  final flat event, so "rebalances nothing" cannot strand positions.
- **One internal defect** — A3-M1: test fixture (a) as written
  ("post-`T_ret` decision row emits NO_NEW_POSITIONS with zero fills")
  contradicts R-1's final book-to-flat at the first post-`T_ret` daily
  boundary, which necessarily carries closing fills. Implemented literally,
  the fixture and R-1 are mutually unsatisfiable (implementer either never
  flattens or fails the fixture). Carve out the single final flatten event.
- **Terminal-row decomposition** (price/fee/slip/funding/equity + decision
  count + blocked count + pinned label) satisfies §4.7's separate-named-
  fields law and C-XS-3; the equity field must name its basis (A3-L2).
- **Successor law matches C-XS-2**: new strategy ID, no prospective-history
  inheritance, "rebalance only when expected carry over the intended holding
  period ≥ full round-trip stress cost" — verbatim, with the "umbrella §4.5
  C-XS-2 applies verbatim" clause restoring the full anchor text (incl. the
  "+ funding uncertainty" qualifier the abbreviated restatement drops).
  Arithmetic checks: 20–25 bps ÷ 1.11 bps/day = 18.0–22.5 days ✓ "18–23";
  ×1.5 → 27.0–33.8 ✓ "27–34"; ≥3–5 week holds ✓; maker-only measured-not-
  assumed ✓.

### D. GO-gate hygiene — PASS. Distinct phrase
`GO PSCTV1 AMENDMENT A3 XSECT RETIRE`; `T_ret` defined as the GO-consumption
moment recorded in the amendment artifact — i.e., the timestamp is pinned at
the gate, exactly as D4 requires; P-8 cited.

### E. Append-only — PASS. R-3 append-only/byte-untouched; no relabeling;
`CANDIDATE_FAIL` stays the label of record; restart-idempotence test (c).

### F. Cross-draft consistency — PASS. Does not touch A2's sleeve (BANDRIDGE)
or A1's cycle; retired-history dashboard move is display-only, matching
D10's posture.

### Findings

- **A3-M1 (MEDIUM)** — fixture (a) conflicts with R-1's final flatten;
  carve out the single book-to-flat event (one line).
- **A3-L1 (LOW)** — "force-flat at fold boundary law" cites a PSV1
  exit-policy class (§9.6/G3) that is not the XSECT sleeve's frozen exit
  policy (its frozen law is the 24h rebalance, §3.3); drop the clause or
  mark it evaluation-layer only — the operative rule is the next-daily-
  boundary flat.
- **A3-L2 (LOW)** — the terminal row's "equity" must state its basis:
  booked decision-row equity and valuation-mark equity are two different
  bases (umbrella §4.7; explorer §2.1 — 99,948 ledger vs 99,094 mark);
  §0 already reports both — require both in the terminal row.
- **A3-L3 (LOW)** — cosmetic: `NO_NEW_POSITIONS_RETired` mixed-case typo in
  the emitted row type.

---

## SET-LEVEL ASSESSMENT

1. All three drafts are faithful to their owner decisions, stop at their own
   GO gates with distinct fresh phrases, keep P-8 semantics, respect
   append-only/no-backfill everywhere, and correctly treat the umbrella as
   draft law (it is not yet registered — verified in the registry).
2. The single remediating defect is A2-H1: the executor re-pin text is not
   scoped to sleeve 4, and the verified production code structure (global
   `FEE_RATE_CURRENT`) makes the literal reading dangerous to two running
   sleeves with booked fills. This is a draft-text fix, cheap and
   well-defined; A2 should return to the owner only after the fix lands.
3. A1 and A3 are GO-ready as drafts; their MEDIUM findings (ancestor-control
   definitional disclosure; unpinned primary-book cost declaration;
   fixture/flatten consistency) are strengthen-before-GO advisories that do
   not change what the owner is being asked to approve.
4. Standing limitation of this review: census curve sha paths for EURUSD/
   GBPUSD were verified at the authority-reference level (umbrella §5.4 +
   critic §1.2 + lane-F dossier present on disk), not re-pinned file-by-file;
   the A1 implementation gate must pin both pairs' curve hashes explicitly.
   Worktree HEADs were quoted from the explorer/lane artifacts, not
   re-verified (same NOT_RUN class as the explorer's §6).

— quant-auditor lane `amendment-drafts-review`, ECONOMIC-ROBUSTNESS-PROGRAM-V1,
2026-09-25. Handoff: `HANDOFF_drafts_review.json` (same directory).
