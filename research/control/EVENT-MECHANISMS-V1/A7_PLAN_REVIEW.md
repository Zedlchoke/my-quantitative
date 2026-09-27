# A7 PLAN REVIEW — EVENT-MECHANISMS-V1 (independent audit, 2026-09-27)

Auditor: A7, independent, no stake in the cycle passing. Scope: the 11
artifacts named in the audit brief, read in full, plus on-disk verification
of probe evidence, hashes, cited constants, registry row, git/worktree
state. This audit repairs nothing; it records verdicts and findings only.
Audit HEAD (root `main`): `dd5a58c0`; cycle worktree
`.worktrees/event-mechanisms-v1/integration` at `6ac5f36d` on
`orca/event-mechanisms-v1-integration` (matches registry head field).

## 1. Verdict table

| Check | Verdict | Evidence (measured this audit) |
|---|---|---|
| A7-1 Owner-directive coverage | **PASS** (with disclosed narrowings, see F-4, F-5) | Directive reqs → artifacts: (a) 8-direction × 8-field screening — `SCREENING_MATRIX.md` §D1–D8 (D1–D3 full 8 fields; D4–D8 abbreviated but terminal-verdict, F-5); (b) trial ledger + outcome-exposure map BEFORE PnL — `TRIAL_LEDGER.jsonl` rows 1–2 stamped 2026-09-27T08:40:00Z, ledger header law + `outcome_exposure_map_seed` with `unopened_classes` incl. S1 and the acceptance-datetime planes; no PnL exists anywhere (intake census; S1 SEALED_UNTOUCHED); (c) skeptic veto — `SKEPTIC_REPORT.md` exercises it (D3 event book VETO; D2 amendment arm fenced); court adopted both verbatim; (d) ≤3 identities — exactly 2 (`EMV1-A1-FILINGFLOW-ACC`, `EMV1-A2-INSIDERFLOW-ACC`); (e) stocks priority — both stocks, D1/D2/D3 = owner-verbatim priorities 1/2/3; (f) BLOCKED_DATA discipline — D6 `BLOCKED_DATA`, `www.sec.gov` estate `BLOCKED_NETWORK_403` + GA-1, "no substitution" stated in G2 R1 and plan §2; (g) FX never scored — D8 NOT SCORED, plan §2 hard boundary, G2 R6 "NO AUTHORITY PURSUED"; (h) stop-at-GO — registry `go_phrase_state: REGISTERED_NOT_CONSUMED`, G3 "Scored execution: BLOCKED at owner GO gate by construction", ledger `budget_note` names the phrase; (i) handover list — plan §8 carries all 7 directive deliverables (A7 report = this file). Lesson-to-gate matrix maps all six owner-named error classes (E1–E6) to gates G4a-c/G5/G1+G3+L1/G6/G2/G8+G9. |
| A7-2 Consistency (screening vs skeptic vs court vs freeze vs G2) | **PASS** (one process tension → F-1) | No contradiction found. Skeptic VETO on D3 event book → court "event book VETOED", G3 contains no D3 arm. Skeptic fence on D2 amendment arm → court "KEEP → G3 WITHOUT amendment arm", G3 A2 "original filings only (amendment arm DROPPED by G1 court)". Skeptic D1 conditions: rho battery incl. date-only + NG6 shadows + clock-only → G3 shared battery items 1/2/4; after-hours-LP payer leg dropped → G3 A1 mechanism text omits it; lawful price planes → G2 R3. No silent override of any skeptic ruling. Tension: skeptic precondition "staged probe measuring per-entity acceptance history depth … BEFORE the G3 freeze" was satisfied only on a 4-entity sample (AAPL/SIRI/BBBY/FRC), cohort-wide staging deferred to C5 lane work; canary not recorded (F-1). |
| A7-3 Freeze quality | **PASS** (findings F-2, F-7) | Constants a priori: strata S1–S4 fixed by market clock; hold 5/10 sessions; $100k buy threshold; PF bar 1.10; rho bar 0.20 immovable — all frozen pre-PnL in `G3_FREEZE.md`, no tuning surface at execution. Falsifiability: PF<1.10 at ×1.0, rho>0.20 kills, placebo-must-not-reproduce, fold floors (≥100 events/fold, ≥400/anchor, ≥2/3 folds net-positive, ≤20% single name, drop-one-name) — operational; two exceptions not numeric (date-only control "within noise"; strata-spread "≈ 0") → F-2. Ancestry fences named with family_ids (`EMV1-A1-FILINGFLOW-ACC` vs NG6 event-conditional forms incl. reversal_5d 0.201; `EMV1-A2-INSIDERFLOW-ACC` vs SFNG1 declared-plan cadence + amihud ILLIQ-28D/63D), measurable bar 0.20. Merge condition operational (representation-rho of the two event-date indicator streams > 0.20 → A2 collapses into A1). **EMV1-A1 anchor lookahead reasoning (explicit):** acceptance instant t → first-post-acceptance session D* → direction = sign(close−open of D*) → entry at open of D*+1. Branch S1 (pre-open 00:00–09:30 ET): D* = same calendar session; its close is strictly before the next open. Branch S3/S4 (after 16:00 ET) and weekend bucket: D* = next session; its close strictly precedes the following open. In every branch all decision inputs (acceptance stamp, stratum label, D* session-return sign) exist strictly before the entry instant; the EOD price bar for D* is complete before D*+1 open under the declared after-close EODHD posting. **No decision input is available only after the entry time — the rule design is lookahead-free.** Implementation-level lookahead is NOT yet excluded: G4a unfinished-window guard, G4b future-mutation, G4c truncation replay are NOT_RUN (disclosed), so this verdict covers design only. |
| A7-4 Evidence integrity | **PASS** (findings F-6, F-8, F-10) | `shasum -a 256 -c probe_sha256.txt`: 8/8 OK. Spot-checked numeric claims against files: (1) SIRI paged `depth_SIRI_paged001.json` — exactly 1,735 acceptanceDateTime entries, 0 missing, min `1996-05-15T00:00:00.000Z`, pagination index `filingCount 1735, filingFrom 1996-05-15` — matches G2 R1 verbatim; (2) BBBY dead issuer — `depth_BBBY.json` is `20230930-DK-Butterfly-1, Inc.` (CIK 0000886158, tickers empty = delisted), 1,000 recent filings served through last acceptance 2023-12-04 + paged index 490 back to 1995-02-03 — "dead issuer fully served" verified; (3) AAPL — `probe_submissions_aapl.json` 163,991 B on disk (matches claim), 1,000 recent spanning 2015-07-28..2026-09-24 (exact match), paged 1,250 back to 1994-01-26; (4) wrong-CIK control — `depth_FRC.json` is a clean 404 `NoSuchKey` for `submissions/CIK0000038182.json`, proving the N4 dated-join is load-bearing; (5) both `www.sec.gov` 403 bodies 4,819 B identical (files measured 4,819 B each). Cited constants re-anchored: `FAMILY_FAILURES.jsonl` = 139 rows measured; DTP "death ledger 38" backed by DTP `GO_RECORD.md:56`; Q-7 "91.7% of 8-K windows at the 09:30 bar; 1.05×/1.74× vs 2.53×" backed at `research/wayfinder/LESSONS.md:450-452`; Q-2 3.33× band present in wayfinder. Request-count bookkeeping inconsistent across artifacts (F-6). |
| A7-5 Ledger law | **PASS** (finding F-9) | `TRIAL_LEDGER.jsonl`: header row states APPEND-ONLY law incl. errata-row correction mechanism and "every scientifically computed scored outcome … enters observed_scored_denominator at computation time"; denominators `observed 0 / published 0 / budget_max 6` = registry `budget {used:0, max:6}`; `outcome_exposure_map_seed` row states the before-PnL law, lists OUTCOME_EXPOSED planes (all prior-cycle kills, confirmation weight 0) and UNOPENED classes (S1, ERP1 holdouts, the acceptance-datetime planes themselves). Ledger predates any scored computation. Append-only is procedural, not hash-chained (F-9). |
| A7-6 Boundary discipline | **PASS** | No artifact authorizes scoring, S1 opening, shadow changes, orders, purchases, or GO consumption. Plan §2 non-goals explicit; G3 closes scored execution behind G4–G7 + owner GO; ledger budget_note conditions consumption on "A7 prelaunch PASS + owner GO phrase typed at this cycle's own gate"; gap matrix: "Nothing here authorizes purchases/signups — every owner action is a decision or an export the owner performs personally"; registry `REGISTERED_NOT_CONSUMED`; G2 pass verdicts are gate-progressions, not execution authorizations. FX/crypto scoring planes explicitly NOT PURSUED. |
| A7-7 Registry/worktree hygiene | **PASS** (findings F-3, F-9) | Registry row vs plan: `cycle_id EVENT-MECHANISMS-V1` ✓; `branch orca/event-mechanisms-v1-integration` ✓ (worktree exists at that branch, head `6ac5f36d` matches the registry head field) ✓; `budget {used:0, max:6}` ✓; `go_phrase "GO EVENT MECHANISMS V1 SCORED EXECUTION"` ✓ = plan; `go_phrase_state REGISTERED_NOT_CONSUMED` ✓; `s1 SEALED_UNTOUCHED` ✓; workers 0. Registry `phase` field stale ("G1 screening court in progress" while G1 court/G2/G3 artifacts exist) — LOW, folded into F-9. Material hygiene issue: G2, G3, SKEPTIC_REPORT, the court section of SCREENING_MATRIX, DATA_GAP matrix, the E-P1 plan erratum, and the four depth-probe bodies are UNCOMMITTED in the root checkout (verified via `git status --porcelain`) — the freeze is not yet git-anchored (F-3). |

## 2. Known-limitation disclosure check (all four verified DISCLOSED, none hidden)

1. G4–G7 NOT_RUN — disclosed in `G3_FREEZE.md` §"Gate status after this
   freeze" ("implementation lanes not yet dispatched"); no artifact claims
   them PASS.
2. Cost ceilings PROXY-PRIOR — labeled in G2 R5 ("all G6 ceilings are
   PROXY-PRIOR"), G3 shared battery item 5, skeptic blocker B8, gap-matrix
   GA-2 ("a survivor would carry that label into any promotion decision").
3. Cohort-wide acceptance staging probe-scale only — disclosed in G2 R1
   ("PASS (probe-scale)") and gap-matrix C5; the residual tension with the
   skeptic's precondition timing is finding F-1.
4. EODHD eod_cache N9 unpinned defect carried — disclosed in G2 R3
   ("defect carried", re-pin as lane job) and gap-matrix C3.

## 3. Findings

Severity scale: HIGH = invalidates a verdict or violates a binding law;
MEDIUM = must be closed before the next gate dispatch; LOW = documentation/
bookkeeping, close opportunistically. No HIGH findings.

- **F-1 (MEDIUM) — Skeptic precondition only partially satisfied before the G3 freeze.**
  What: The skeptic's attached condition on D1 required "a staged probe
  measuring per-entity acceptance history depth (recent + paged), with
  per-file sha manifest and a canary, BEFORE the G3 freeze" over the
  death-inclusive cohort (410 alive + 1,769 dead). What was done before
  freeze: 4 entities (AAPL/SIRI/BBBY/FRC) with sha manifest; cohort-wide
  staging deferred to lane item C5; no canary recorded.
  Where: `SKEPTIC_REPORT.md` §1 D1 condition 1 + §5 B1;
  `G2_DATA_GATE.md` R1; `G3_FREEZE.md` (freeze proceeded on the sample).
  Why it matters: the fold floors (≥100 events/fold, ≥400/anchor) that
  make the freeze operable depend on cohort-wide depth that is estimated
  (DFV1 N2 class), not measured; the cycle deviated from its own
  independent-checkpoint contract.
  Disposition (audit only): complete C5 cohort-wide staging and record the
  canary BEFORE G4 lane dispatch, or have the court record an explicit
  condition-relaxation errata noting the 4-entity sample and the floor
  backstop — either path is lawful; silence is not.
- **F-2 (MEDIUM) — Two core kill criteria are not numerically operationalized.**
  What: The date-only control kill ("reproduces the anchor's net expectancy
  within noise") and the unmonitored-vs-monitored strata falsifier
  ("|drift| spread ≈ 0 after costs") have no preregistered numeric band,
  while every other falsifier does (PF<1.10, rho>0.20, fold floors).
  Where: `G3_FREEZE.md` shared battery item 1 and EMV1-A1 falsifiers.
  Why it matters: the date-only control is THE test of the cycle's claimed
  new information layer (acceptance clock vs filing date); an undefined
  "within noise" is the exact surface where post-hoc discretion (E3
  multiple-testing / tuning-by-verdict) re-enters after outcomes are seen.
  Disposition: freeze addendum preregistering the bands (e.g., bootstrap CI
  or fixed delta on net-expectancy difference) with an explicit
  no-PnL-exists attestation, landed before G4 dispatch. Adding missing
  bands completes the freeze; it does not revise a hypothesis.
- **F-3 (MEDIUM) — Gate evidence and the freeze are uncommitted in the root checkout.**
  What: `git status --porcelain` shows `G2_DATA_GATE.md`, `G3_FREEZE.md`,
  `SKEPTIC_REPORT.md`, `DATA_GAP_OWNER_ACTION_MATRIX.md`, the four
  `depth_*.json` bodies, modifications to `SCREENING_MATRIX.md` (court
  section) and `plans/PLAN_event_mechanisms_v1.md` (E-P1 erratum) as
  untracked/modified; only the bootstrap artifacts (directive, intake,
  lesson matrix, ledger seed, initial screening + probes) are committed.
  Where: root checkout `main` at `dd5a58c0`.
  Why it matters: the G3 freeze defines `arm_config_digest`/`code_freeze_sha`
  against a file that git does not yet anchor — freeze drift would be
  invisible to the audit trail; the committed plan still carries the
  uncorrected "owner-reviewed" provenance labels.
  Disposition: one pathspec-staged control-plane commit (per P-10, no
  `git add -A`) landing all of the above before any lane dispatch.
- **F-4 (MEDIUM) — One owner-verbatim stocks priority (D3 event book) removed by skeptic veto; must be an explicit owner decision point.**
  What: The owner directive names three stocks priorities (acceptance
  timestamp, Form 4, corporate-action PIT). The court, applying the
  skeptic's VETO, removed the D3 ex-date event book as a scored identity
  (payer mechanics false: index weights are split-invariant; skeleton
  collapses onto D1; dead-reversal collision), keeping only the N3/N4
  data-plane repair as G2 work.
  Where: `SCREENING_MATRIX.md` court ruling #1; `SKEPTIC_REPORT.md` §1 D3.
  Why it matters: the veto is lawful — the directive grants the skeptic an
  unqualified veto and the directive's own conflict rule defers to that
  grant — but an owner could reasonably read "ưu tiên kiểm corporate-action
  PIT" as requiring the event direction to be tested. The measured grounds
  (Q-6-published anomaly, no forced flow) make the veto scientifically
  sound; the governance point is that owner-verbatim scope was narrowed by
  a delegated instrument.
  Disposition: the stop packet must present the D3 veto as a
  ratify-or-override decision for the owner (with the three measured
  grounds), not as a settled internal matter.
- **F-5 (LOW) — Owner's 8-field screening format written in full only for D1–D3.**
  What: D4–D8 entries are condensed paragraphs labeled "(abbreviated, court
  record)" rather than eight labeled fields.
  Why it matters: the directive's instruction is per-direction and
  unconditional; the narrowing is substantive-neutral (all four are
  terminal verdicts — veto/blocked/not-scored — where cost-ceiling and
  falsifier fields are vacuous) but is presented as abbreviation, not as a
  labeled deviation.
  Disposition: one sentence per terminal direction naming which of the 8
  fields are vacuous and why, in the owner packet; no rework of the matrix
  required.
- **F-6 (LOW) — Probe request-count bookkeeping inconsistent across artifacts.**
  What: `PROBE_LOG.md` etiquette line says "6 HTTP requests total" while
  its table lists 5; `G2_DATA_GATE.md` R1 says "7 HTTP requests total";
  gap-matrix C1 says "7 probes". Preserved request artifacts = 9 (5 initial
  incl. one HEAD + 4 depth), so none of the three claimed totals matches
  the on-disk evidence.
  Why it matters: etiquette/fair-access compliance is a stated control;
  an unreconciled count weakens it.
  Disposition: errata row with the reconciled count (9 request artifacts;
  enumerate them), no re-probing needed.
- **F-7 (LOW) — Freeze asserts "every constant fixed a priori with a stated
  reason" but several constants carry no inline reason.**
  What: $100,000 open-market-buy threshold, hold 5/10-session horizons, and
  the PF 1.10 bar have no stated rationale in `G3_FREEZE.md`; the text also
  says "dispatch packets below" while none follow the section.
  Why it matters: no tuning surface exists (constants are frozen before any
  PnL), so this is documentation, not validity — but an unstated-reason
  claim that the text does not honor is an integrity blemish an owner will
  notice.
  Disposition: add the reasons (and the dispatch-packet pointer or remove
  the reference) in the same freeze addendum as F-2.
- **F-8 (LOW) — Skeptic's same-session re-measurements are asserted without preserved evidence.**
  What: The skeptic states it re-listed the v13/NG6 archives and re-measured
  the eod_cache (111,323 files) "today", but no listing/hash output is
  preserved in the control directory; those numbers otherwise rest on DFV1
  citations.
  Why it matters: P-19/P-30 (measured stamps) wants evidence, not
  attestation; a later dispute would have nothing to check.
  Disposition: preserve the tar-listing/file-count outputs as data_gate
  artifacts next time they are asserted (G6/G7 will re-assert them anyway).
- **F-9 (LOW) — Ledger append-only is procedural; registry phase stale.**
  What: `TRIAL_LEDGER.jsonl` has no row-hash chaining (append-only is a
  stated law + git history, not a structural property); the registry row's
  `phase` field still reads "G1 screening court in progress" although G1
  court, G2 and G3 artifacts exist; `updated_at_utc` 08:35:21Z predates the
  later artifacts.
  Why it matters: minor — the binding fields (budget, go_phrase_state,
  branch, s1, head) are all consistent and correct; only the narrative
  phase lags.
  Disposition: land the ledger with the F-3 commit and refresh the registry
  phase via researchctl at the next transactional write.
- **F-10 (LOW) — The `www.sec.gov` 403 is classified "environment-level estate block" without excluding a UA-policy cause.**
  What: The preserved 403 body is SEC's "Your Request Origins from an
  Undeclared Automated Tool" page; the declared UA used ("MyQuantitative
  Research") carries no contact email, which SEC's fair-access guidance
  asks declared UAs to include. UA-independence was measured (declared vs
  browser UA, identical 4,819-B body), but both could fail a
  declaration-completeness check; the L-FIBV1-1/L-FXFF-1 precedent class is
  consistent with either cause.
  Why it matters: GA-1 asks the owner for a network unblock; if the real
  cause is UA policy, the owner action is misdirected and the estate is
  openable by this cycle itself with a conformant UA string.
  Disposition: one extra probe with a conformant declared UA (name +
  contact email) before the owner is asked to spend GA-1; if it still 403s,
  the environment-block classification stands as written.

## 4. Positive findings worth recording

- Probe evidence is unusually verifiable: all 8 sha256s check out and every
  spot-checked number in G2 R1 (SIRI 1,735/1996-05-15; BBBY dead-issuer
  served incl. 2023-12-04 last acceptance; AAPL 1000-recent exact span;
  FRC 404) reproduced exactly from the preserved bodies.
- The skeptic veto chain is clean: both vetoes and all three corrections
  were adopted by the court and are visibly enforced in the G3 freeze (no
  D3 arm, no amendment arm, LP payer leg dropped).
- The EMV1-A1 anchor design is lookahead-free by construction (reasoned in
  A7-3); the residual risk is correctly assigned to the NOT_RUN G4
  implementation gates, which are disclosed as such.
- Boundary discipline is intact everywhere: nothing in any artifact
  consumes the GO phrase, opens S1, or authorizes execution.

## 5. Final verdict

AUTHORIZED_WITH_FINDINGS — the plan, screening court, data gate and freeze
are internally consistent, evidence-anchored and boundary-clean, and the four
known limitations are disclosed rather than hidden; the 4 MEDIUM findings
(F-1 cohort-depth precondition, F-2 unoperationalized kill bands, F-3
uncommitted freeze evidence, F-4 owner ratification of the D3 veto) must be
closed before G4 lane dispatch, and none requires re-running G1–G3.
