# A7_tracka1_delta_review_REPORT — round-2 delta audit of ERP1-TRACKA-COHORT-1 (DRAFT, post session-2)

- Auditor: A7, independent fresh context (quant-auditor). Round 2. Read-only
  except this report, the ROUND 2 section appended to
  `A7_tracka1_plan_audit_REPORT.md`, and the updated
  `HANDOFF_tracka1_a7_plan_audit.json`. No repair, no gate suggestions beyond
  recorded dispositions, no commits, no registry writes, no downloads, no
  backtests, no PnL computation, no touch of any running worker.
- Audited object: `plans/DRAFT_ERP1_TRACKA_COHORT_1.md` as changed by session
  2, plus the session-2 artifacts in
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/`.
- Measured base: root `main` @ `69ddc60447d223249319f82b71b21e26ab941203`
  (`git rev-parse HEAD`, re-measured this session) — **unchanged from round
  1; no lane committed anything** (last commit remains the pre-existing
  registry landing of 2026-09-25T05:36Z). Working tree: untracked control
  artifacts only.
- Live re-measure: registry grep `TRACKA` = 0 (child still unregistered; 68
  cycles); heavy lock `FREE_PROVEN`; FX-RANGEFADE-2M-SHADOW-V1 daemon PID
  79157 alive with continuous etime, untouched; registry `updated_at_utc`
  unchanged (2026-09-25T05:36:15Z).

## VERDICT (round 2): PASS

Zero CRITICAL, zero HIGH. All four round-1 conditions (C1–C4) are verifiably
integrated into the current plan text, correctly worded, with no gate
weakened. Every session-2 addition is correct, correctly evidence-scoped and
leak-tight. Remaining findings: one MEDIUM freeze-completeness bundle (D1)
whose content belongs in the GO-1 freeze artifact that GO-1 itself
authorizes, and five LOW recorded dispositions (D2–D6).

## 1. Round-1 conditions — verification against current file bytes

| Cond. | Plan location (current text) | Verification |
|---|---|---|
| C1 / F1 council composition | §7.1 ("Composition completed per owner decision D-E … two additional BLIND PROPOSER lanes (P1, P2) … NO additional mechanism slots and M2 stays dead"); §11 (D-E LOCKED, "composition literal-compliant"); A.3 session-2 block (proposals = FUTURE-COHORT candidates; "No mechanism slot was opened and M2 was not rescued (owner instruction, binding)") | **RESOLVED.** P1/P2 reports carry signed outcome-blindness disclosures; contain zero outcome numbers (every figure is a declared hypothesis band, clock arithmetic, a plan-internal citation, or a failure-class label); make no slot claim ("the current cohort is FROZEN (no slots open)"; "none requested"); lanes mutually independent (each read no other lane's output). Handoffs schema `zcode_orch_v3_handoff@1`, `commit_sha: null`, `workers: 0`. The RECLAIM-ABSORB / retest-class cross-lane tension (explorer's FXFV2-A4-P2 self-veto vs P2-A) is flagged on the record in A.3 for a future cohort's D2. |
| C2 / F2 representation law | §8 F-1: "pooled \|rho\| ≤ 0.20 vs dead families is computed on the EXACT scored target-array representation with the frozen variant set, BY THE SKEPTIC LANE, not the proposer — a rho computed on a friendlier representation is void" | **RESOLVED** — verbatim in strength; closes the friendly-representation path into the scored cohort. |
| C3 / F3 holdout scope | §9.1: "each pair's holdout is consumed by EXACTLY ONE preregistered evaluation PASS, whose membership is frozen before the pass: the promotable ANCHOR arms that passed ALL dev gates … plus — computed in the same single pass, as companions, never as independent consumers — their preregistered causal control, inverted control and baseline books … **Never-selectable arms (R-ORIG, R-NEIGH) and dev-killed mechanisms (including KILL_PIT_SEAM and control kills) take NO holdout look**" | **RESOLVED and extended** per proposer P2's finding: the inverted control joins the single pass (closing the inversion-evaluable-on-dev-only hole), at zero additional look cost. Strictly strengthens; no rescue path created (inverted companion feeds the existing §9.3/§9.4 inversion laws). |
| C4 / F4 F-5 arithmetic | §8 F-5: "the ceiling is DECLARED-BAND ARITHMETIC … NO backtest, no measured gross return — the premium side stays the proposal's declared hypothesis until the scored phase. Negative ceiling = veto BEFORE scoring" | **RESOLVED** — the ordering-law circularity is closed; the ceiling side remains measured (census, ×2.0, conditional break-hour bucket, F-6 recent window) while the premium side stays declared. |

## 2. Session-2 additions — audit results

**(a) `INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md` — CORRECT.** The evidence
invalidation is scoped exactly right: ancestor scored results (V2 selection +
holdout, RANGEEXP-SCORED, FX-MAJORS transfer) "remain valid AS historical
facts about R-ORIG on those consumed windows (append-only evidence,
unchanged)" and "MUST NOT be cited as evidence about the law the daemon is
running … nor about the PIT-clean R-ANCHOR"; the "parity PASS" citation ban
is restated; the journal is unaffected as raw data with its interpretive
class routed to the separate classification proposal. Nothing executed,
repaired, restarted or re-scored; daemon verified alive/untouched. The plan
(§6) binds the incident's citation law onto every artifact of the program.
Cited line ranges re-checked against the round-1 fresh code read: accurate.
Handbook §26 (Incident transparency, `HOW_TO_BE_A_LEAD_ENGINEER.md:842`)
exists — the format reference is real.

**(b) `PROPOSAL_SHADOW_CLASSIFICATION_FX-RANGEFADE-2M_2026-09-25.md` —
CORRECT, proposal-only.** No execution, no promotion, no $100k-account
action, no parameter change, no restart, no re-registration; fail-closed
default ("no decision ⇒ no change"); both exit conditions are owner-gated
amendments (PIT rebase = new identity/successor per umbrella §5.6 with new
strategy ID and append-only journal preservation; beta/cost observability =
amendment A1-controls completion). Consistent with the untouched daemon
(PID 79157, continuous etime) and the registry's amendment-A1
activation-in-progress token. Registered in the plan (§11 D-F) and the owner
packet as OPEN/proposal-only. No covert promotion path: the rebase branch
requires a fresh owner GO and never bypasses the child's
`CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` ceiling.

**(c) Proposer lanes P1/P2 — CLEAN.** Signed blindness disclosures (P1 §4;
P2 §5) with explicit read-set enumerations and mutual independence; zero
outcome numbers anywhere (P2's "29 of 126 `ANCESTRY_RHO_BLOCK`" is a failure-
class frequency from the mandated failure registry, not a scored outcome);
no slot claims (future-cohort candidates only, stated in both reports and
both handoffs); P1: 1 offered / 8 self-vetoed with firing veto recorded /
2 dead on data authority; P2: 2 offered / 4 self-vetoed; both declare their
strongest veto adjacencies honestly (P1's V-4 adjacency; P2's sign-sensitive
V-1/V-6 kill risk). The four integrated design findings are all in the plan
text and strictly strengthen it: F-3 mode-sham (P1) — explicitly
"signal-level, no scored arm, no new slot"; §9.1 inverted holdout companion
(P2); M3/all-controls gross+net decomposition (P1+P2) with kill bands
explicitly unchanged (NET) in A.2 and the §10 ledger schema; F-4
beta-composition disclosure (P2) with the no-post-PnL-retrofit law.

**(d) Owner-locked decisions reflected.** D-B: §11 ("pair slate = AUDUSD +
USDCAD … never re-scored here (A7 F10 ratified)"); D-C: §5.3 head
("Owner decision D-C (2026-09-25, LOCKED): no independent-source unblock
this cycle … `SINGLE_SOURCE_PANEL` … paper tier"); D-E: §7.1/§11/A.3; D-F
proposal-only in §11. Ledger contract §10 frozen: append-only JSONL row
schema (`cycle_id … labels[], sha_chain{code_freeze, data_manifest,
selection_digest}`) with mandatory `SINGLE_SOURCE_PANEL`,
`FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`, `PAPER_TIER` labels and
control-row `gross_pnl`/`net_pnl` decomposition.

**(e) `OWNER_PACKET_tracka_cohort1.md` rev 2 — CONSISTENT.** Decision table
matches the plan and the artifacts (D-B/D-C/D-E LOCKED; D-A OPEN = the GO-1
gate with the exact phrase; D-F OPEN, proposal-only); the GO-1 authorization
list matches plan §0 and stops before any scored cell; §6 "did NOT do"
list verified true by this audit (no registration, no commits, no worker
touch).

**(f) External state.** Registry grep `TRACKA` = 0; daemon PID 79157 alive
and untouched; lock `FREE_PROVEN`; zero commits by any lane (HEAD identical
to round 1); handbook citations real (§26 :842; §34.4 :1072 — P2's handoff
citation is correct).

## 3. Fresh-eye pass over the final plan — new-inconsistency hunt

- **Arm-count drift: none.** M1 = 6 arms/pair × 2 pairs = 12; M3 = 6 arms;
  mode-sham explicitly adds no arm and no slot; holdout companions are
  dev-scored arms re-evaluated inside the single pass, not new cells.
  §0 / §10 / A.4 all still say 24 cap / 18 effective — consistent.
- **GO-phrase drift: none.** §0 and owner-packet §2 carry the byte-identical
  phrases; GO-2 remains fresh-typed, post-A7-prelaunch, not pre-consumed.
- **§9.1 vs §9.3:** the single-pass law and the PROMOTE holdout conditions
  are now mutually consistent (causal + inverted + baseline all evaluable on
  holdout inside the one look; ×1.0/×1.5 books are re-costings of the same
  pass, not extra looks).
- **§11's round-1 A7 record is accurate** (verdict, 0C/0H, F1–F11
  dispositions all locatable in the text: F1 §7.1, F2 F-1, F3 §9.1, F4 F-5,
  F5 §3.2, F6/F7 A.3 errata, F8 §9.4, F9 recorded fail-safe, F10 D-B, F11
  recorded).
- New issues found: D1–D6 below. Nothing else.

## 4. Round-2 findings register

| ID | Severity | Finding | Evidence (file:line, current bytes) | Required disposition |
|---|---|---|---|---|
| D1 | MEDIUM | Freeze-completeness bundle — (i) numeric value + storage location unpinned for the PROMOTE bootstrap seed and the mode-sham shuffle seed ("frozen seed" named, no number/artifact); (ii) §9.1's "membership frozen before the pass" names no preregistration artifact or sha; (iii) mode-sham firing consequence/verdict label unnamed (sham in the R-ORIG role of §9.4 — firing must be a kill; the mechanical reading exists but is not pinned); (iv) two-pair close semantics unpinned (partial-replication label vs REJECT_ALL composition at cycle close); (v) seam limb (iii) minimum evaluability floor (`N_diff`/matched-pair count) absent — recommended by BOTH proposers, not integrated | plan :462-469 (mode-sham "frozen seed"), :550-553 ("frozen seed"), :515-529 (§9.1 membership), :586-592 (limb iii), PROPOSER1 §2.1 items 3/6/7, PROPOSER2 §4.1 items 1/5, §4.3 | All five belong IN the GO-1 freeze artifact (registration packet) and are verified by A7 prelaunch (§11) before GO-2; none may be added post-PnL. **Non-blocking for typing GO-1**: they are content of the freeze that GO-1 authorizes, and the existing prelaunch gate re-audits them |
| D2 | LOW | F-5 cross-reference typo: "the proposal's preregistered premium band (from its §5.3 field 2)" — the 10-field format is §7.3 | plan :486 | Correct to "§7.3 field 2" at registration |
| D3 | LOW | §5.3 residual "If the owner completes an unblock path before GO-2…" upgrade bullet is dead text under the LOCKED D-C | plan :278-280 vs :263-266 | Annotate superseded-by-D-C at registration (fail-safe as is: activation still requires owner amendment + new GO) |
| D4 | LOW | §5.2/A.1 not annotated with the D-B lock — slate reads "Council proposes … frozen at GO-1"; USDCHF spare remains owner-amendment-only (consistent, but the lock state is understated where the slate is defined) | plan :235, :684-687 vs :641-643 | Reference D-B in §5.2 at registration |
| D5 | LOW | §9.4(iii) pairing multiplicity unpinned (whether one R-ANCHOR-only trip may anchor multiple R-ORIG-only pairings); same-day nearest-pair rule otherwise well-defined and fail-safe (unmatched trips excluded and counted) | plan :588-591 | Pin the multiplicity rule in the freeze alongside `c_rt` |
| D6 | LOW | P2's mode-day-restricted beta decomposition table (computable from already-scored baseline cells, no new cell) not mandated — F-4 carries the disclosure and the no-retrofit law, but the specific table was P2's recommendation | plan :478-482; PROPOSER2 §4.1 item 2 | Add as a freeze reporting item (report-only) at GO-1 |

## 5. Gate state

- Blocking conditions remaining: **none.**
- D1 binds the freeze artifact produced under GO-1 and is re-audited by the
  existing A7 prelaunch gate before GO-2; D2–D6 are recorded dispositions.
- Nothing is registered, executed, downloaded, scored or touched; the daemon
  is untouched; no lane committed; the child is absent from the registry.

**GO-1 READY: YES**

— A7 quant-auditor, tracka-cohort1-a7, round 2, 2026-09-25, at root main
`69ddc60447d223249319f82b71b21e26ab941203`.
