# DRAFT AMENDMENTS — INDEPENDENT REVIEW, ROUND 2 (fresh-context A7-class audit)

- Reviewer: independent fresh-context reviewer (audit only, no repair). No prior
  review treated as authority; every finding below is derived from the three
  drafts, the production bytes, and the owner's round-2 fix requirements R1–R5.
- Measured tree: branch `main` @ `376311a5aac02fb14cef65d2b1e4faaa93285213`
  (identical to dispatch sha). Read-only except this report and the handoff JSON.
- Objects audited:
  1. `plans/DRAFT_amendment_FX-RANGEFADE-2M-SHADOW-V1_A1_controls.md` (A1, owner D2)
  2. `plans/DRAFT_amendment_PSCTV1_A2_bandridge_pins.md` (A2, owner D3)
  3. `plans/DRAFT_amendment_PSCTV1_A3_xsect_retire.md` (A3, owner D4)

## 0. Verdicts

| Draft | Verdict | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| A1 (FX controls) | **PASS** | 0 | 0 | 1 |
| A2 (BANDRIDGE pins) | **PASS** | 0 | 0 | 2 |
| A3 (XSECT retire) | **FAIL** | 0 | 1 | 1 |

Totals: HIGH 0, MEDIUM 1, LOW 4. A3's FAIL is a single named one-line defect
(residual sentence contradicting its own binding phase model); every other
requirement on A3 is closed — after that one reword, R2 is met on the text as
written and no other section needs reopening.

## 1. Production-bytes verification (method)

All load-bearing claims were re-measured, not accepted from prose:

- `…/prospective_shadow_v1/e/shadow_worker.py` (PSV1 worktree, 36,098 bytes,
  mtime 2026-09-24):
  - L180 `FEE_RATE_CURRENT = 0.0005` — module-global. L181
    `SLIPPAGE_TICKS_CURRENT = 1.0`. L184
    `FEE_RATE_ILLIQ_LINEAGE = FEE_RATE_CURRENT * 1.5` (ILLIQ lineage book is
    DERIVED from the same global).
  - L505–527 `cost_books_for(family_id)`: the `CURRENT_CONSERVATIVE_COST`
    book (L508–509) is built from the globals for EVERY family; the non-ILLIQ
    `LINEAGE_COST` book mirrors them (L524–525); ILLIQ's lineage book uses the
    ×1.5 derivation (L514–515).
  - L145 `FAMILY_ORDER = (FAMILY_ILLIQ, FAMILY_PREMFADE, FAMILY_CARRY,
    FAMILY_BANDRIDGE)` — exactly four families, as A2 states.
  - Exhaustive grep: L180/184/508/509/514/515/524/525 are the ONLY
    consumption sites of the cost constants; a package-wide grep for
    `0.0005`/`0.0006` over `research/shadow_v1/**.py` finds no second
    fee-rate source.
- `…/research/shadow_v1/executor.py`: L427
  `self.cost_regime_digest = canonical_digest(self.cost_books_cfg)` — the
  digest is computed PER FAMILY over that family's cost-book config. Therefore
  a family-keyed override changes only BANDRIDGE's digest;
  ILLIQ/XSECT/BASISLV digests are stable as long as their `cost_books_cfg`
  bytes are unchanged.
- Live ledgers (`…/integration/results/prospective_shadow_v1/ledgers/`):
  - XSECT-FUND-CARRY-7D: 11 decisions, 52 fills, fee 286.43, slip 68.02,
    funding +4.60, net −349.85 — matches A3 §0 and umbrella §4.5 exactly
    (cost:carry 354.45/4.60 ≈ 77:1).
  - BTC4H-BANDRIDGE: 61 decision rows, 0 fills — matches A2's "before the
    first fill"; 56 rows `UNAVAILABLE_FAIL_CLOSED` + 5 `OK` — matches A2 §3's
    "56 fail-closed rows" exactly.
  - All families' rows carry the shared digest `130d2e7e…` (61 BANDRIDGE, 11
    XSECT, 1 BASISLV rows) — confirming A2 P-3's narrative that a global flip
    would move the live cost law of the other families mid-run.
- XSECT ledger last equity 99,948.38 (A3 §3's "99,948 ledger"); mark-basis
  99,094.92 is the umbrella §4.5 measured value (A3's "99,094 mark") — the
  equity-basis example is production-grounded on both legs.
- Parent-law citations exist: umbrella §4.1/§4.3/§4.5/§4.7/§5.4/§5.6/§5.7;
  PSV1 §3.3, §6 ("Two cost ledgers, frozen before activation"), §14; P-13
  cross-worktree mount convention at PSV1 plan L690; `btc-h4-band-risk-v1`
  worktree contains the `shadow_bandridge` namespace
  (`update_shadow_bandridge.py`, `SPEC.md`); the `fx-rangefade-2m-shadow-v1`
  worktree exists.
- Umbrella C-FX-1..4 and C-XS-1..3 were read and compared against A1/A3
  content (see §3, §5).

## 2. R1 — A2 per-family cost-override fix (owner requirement: prove in production bytes that no global change path remains)

**CLOSED — genuinely met.**

- The defect class is real in production bytes: `FEE_RATE_CURRENT` (L180) is
  module-global, feeds `cost_books_for()` for all four families, and ILLIQ's
  lineage book is derived from it (L184). A literal flip would change
  `cost_books_cfg` for ILLIQ/XSECT/BASISLV → per L427 their `cost_regime_digest`
  would change on new rows mid-run — beyond D3 and against PSV1 §6.
- The draft now mandates the only architecture-sound fix: a per-family cost
  override keyed to the BANDRIDGE family id inside the cost-book construction,
  explicitly "NOT by changing any module-global constant" (P-3), scoped in the
  change-set (§3), with the override row and digest boundary limited to
  BANDRIDGE records.
- No residual global path: all fee consumption flows through
  `cost_books_for()`; fixtures (c) (XSECT/BASISLV/ILLIQ cost constants
  untouched, books reproduce identically — this also catches the ×1.5 ILLIQ
  lineage derivation moving) and (e) (override keyed to BANDRIDGE family id
  only) close the two plausible regression routes. P-4 makes hash mismatch
  fail-closed (`UNPINNED_COST_LAW`).
- A2-LOW-1: P-4 records "the BANDRIDGE executor cost-code sha256 (the
  per-family override path)". Since `research/shadow_v1/executor.py` is shared
  by all four families, the file-level code freeze sha WILL change for everyone
  when the file is edited; the cost LAW of the other families stays pinned by
  their unchanged per-family `cost_regime_digest`. Advisory: the activation
  artifact should record BOTH (override-path digest + explicit note that
  non-BANDRIDGE `cost_regime_digest` values are unchanged), so the hash change
  cannot be misread as a cost-law change for the other sleeves.

## 3. R2 — GO-vs-tests-vs-activation sequencing (all three)

Phase model exists in all three drafts and is binding:

- **A1 §3/§4**: G (GO authorizes code-writing only) → I (code, daemon
  untouched) → V (fixtures (a)–(e) + A7; "the GO cannot waive them") → A
  (activation; `T_ctrl` recorded to the second in an activation artifact;
  "A typed GO is never evidence the daemon changed"). §3: "The GO phrase alone
  restarts nothing." No residual sentence found.
- **A2 §1b/§3/§4**: explicit G/I/V/A block ("A typed GO is NEVER evidence that
  any worker changed"; "Tests gate ACTIVATION, not the GO"); P-3 pins the
  boundary to `T_act`, "NOT the GO typing moment"; §4 restates that the GO
  authorizes code-writing ONLY. No residual sentence found.
- **A3 §1/§4**: binding lifecycle with `T_ret` at Phase A ("The GO typing time
  is NOT `T_ret`"); §4: GO authorizes code-writing ONLY. **But the §0 status
  blockquote still contains the residual sentence**: "…the worker is NOT
  stopped by the decision itself — **a separate timestamp freeze at this
  amendment's GO gate governs**." Under the binding §1/§4 model nothing about
  the stop is fixed at the GO gate (only code authorization happens there;
  `T_ret` is recorded at Phase A activation). Read alone, the header sentence
  defaults the stop-timestamp act to the GO gate — the exact residual class
  R2 forbids, and a direct internal contradiction with §1's own heading
  ("takes effect at ACTIVATION, not at the GO typing").

**R2 status: A1 MET, A2 MET, A3 NOT fully met (A3-MED-1).**

## 4. R3 — boundary = activation moment + transition-window handling (A2/A3)

**MET in both.**

- A2: `T_act` = the moment the per-family override is actually live on the
  worker, recorded to the second in an activation artifact (timestamp +
  cost-override digest + executor hash-match proof); transition window G→A:
  every decision/fill under the OLD law, recorded `TRANSITION_OLD_LAW`;
  pre-`T_act` BANDRIDGE fills permanently
  `TRANSITION_OLD_LAW → UNPINNED_COST_LAW — NOT PROMOTABLE`; "Backfill is
  forbidden"; digest `130d2e7e…` stops applying to NEW BANDRIDGE records only
  at the boundary.
- A3: `T_ret` = the moment the stop-open flag is actually live on the worker,
  recorded to the second (Phase A artifact); R-1b: GO→`T_ret` decisions/fills
  recorded `TRANSITION_OLD_LAW`, "honestly counted, never backfilled, never
  re-labelled; the retirement does not retroactively start at the GO".
- A1 (not strictly required by R3, checked anyway): same pattern with `T_ctrl`,
  `TRANSITION_OLD_LAW`, no backfill of cost fields onto old rows
  (`NOT_RUN_COST_FIELDS` for old rows).
- Consistency note: umbrella C-XS-3 says "stop opening … at a preregistered
  timestamp"; A3 refines this to recorded-at-activation `T_ret`, which is the
  honest reading and exactly what R3 demands (A3-LOW-2: add one cross-reference
  sentence noting the refinement of C-XS-3's wording, so no future reader
  tries to pre-set a clock time).

## 5. R4 — A3 separate open/close tests + state-based terminal row

**MET.**

- (a1) no-new-opens fixture (post-`T_ret` rows emit `NO_NEW_POSITIONS_RETired`,
  ZERO opening fills) and (a2) closing-permitted fixture (pre-`T_ret` holdings
  still produce R-1 book-to-flat closing fills; "closings are asserted PRESENT,
  not absent") — the two laws are tested separately, and R-1 makes closing
  lawful and REQUIRED.
- R-2 terminal row emitted ONLY when the sleeve is measured ACTUALLY FLAT —
  "a state condition, never a timestamp assumption", checked at a decision
  boundary; fixture (b) asserts emission fires only on the measured-flat
  condition with hand-computed decomposition.

## 6. R5 — prior MEDIUMs remain closed

- A1 day-session comparability note: CLOSED — §1.1 "Comparability note
  (binding)": the control is a DAY-SESSION short book; the ancestor's
  +314.0-pip SHORT_ALWAYS (commit `bf4f07f1`) was a window-long construct,
  "NOT numerically comparable", cited only as the reason the control is
  mandatory. (Matches umbrella C-FX-1's citation of the same commit/number.)
- A1 primary cost book pin: CLOSED — §2 primary book pinned at the
  implementation gate "before any new row is written", values + provenance
  frozen in the implementation freeze and recorded in `cost_book_digest`;
  stress book reported alongside, never merged into primary PnL.
- A3 closing-vs-opening fixture + equity basis naming: CLOSED — separate
  (a1)/(a2) fixtures (see §5); §3 "Terminal-row equity MUST name its basis
  (decision-row ledger basis vs valuation-mark basis — e.g. 99,948 ledger vs
  99,094 mark class gap; umbrella §4.7 vocabulary)". Both example numbers are
  production-grounded (ledger 99,948.38; umbrella §4.5 mark basis 99,094.92).
- A2 production executor files in scope: CLOSED — §3 names `e/shadow_worker.py`,
  `cost_books_for()` and the per-family cost-book construction, plus the PSV1
  ledger adapter under the documented P-13 cross-worktree mount (verified at
  PSV1 plan L690).

## 7. Cross-draft consistency

- GO phrases distinct: `GO FX RANGEFADE AMENDMENT A1 CONTROLS MOUNT` /
  `GO PSCTV1 AMENDMENT A2 BANDRIDGE PINS` / `GO PSCTV1 AMENDMENT A3 XSECT
  RETIRE`. No collisions.
- Append-only laws consistent: A1 §1.4/§4 (schema append-only, no backfill,
  `NOT_RUN_COST_FIELDS` for old rows), A2 P-3/§1b/§3 (backfill forbidden,
  forward-only, 56 fail-closed rows untouched — count verified), A3 R-1b/R-3/§5
  (append-only, byte-untouched, never rewritten).
- Scope bounded by owner decisions: A1 = D2 exactly (the four C-FX additions;
  strategy law frozen with no-diff fixture (e); no parameter/sizing change).
  A2 = D3 exactly (sizing B, fill law A, cost identity 6 bps — with the
  per-family scoping keeping it inside D3's BANDRIDGE-only mandate). A3 = D4
  exactly (planning of retirement; "Does not stop/restart the worker process
  (owner D4 explicit)"; other three sleeves untouched; R-4 successor law
  mirrors umbrella C-XS-2 verbatim in substance — no new law invented).
- No draft claims any worker has already changed: all three carry
  `DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED`; A2's production-byte
  citations are measurements of the UNCHANGED state (FEE_RATE_CURRENT still
  0.0005; shared digest still applying), which is evidence of NO change; A3 §0
  describes already-booked history only (byte-verified, §1 above).

## 8. Findings register

- A3-MED-1 (verdict-driving): residual §0 sentence "a separate timestamp
  freeze at this amendment's GO gate governs" contradicts binding §1/§4
  (`T_ret` recorded at Phase A activation; GO authorizes code only). Advisory:
  reword to "…a separately recorded activation timestamp (`T_ret`, Phase A
  artifact) governs". One line; nothing else reopens.
- A1-LOW-1: §2 "pinned at implementation gate" — name the phase (Phase I
  freeze, effective before Phase A `T_ctrl`) so the pin moment is unambiguous
  inside the G/I/V/A model.
- A2-LOW-1: activation artifact should record the override-path digest AND an
  explicit statement that non-BANDRIDGE `cost_regime_digest` values are
  unchanged (the shared file's code-freeze sha will change for all families;
  cost law does not).
- A2-LOW-2: §1 heading "Pins (freeze before the first fillable decision
  produces a fill)" is a scheduling objective, not an authority statement;
  anchor it to §1b (mount completes at Phase A; any pre-`T_act` fill is
  `UNPINNED_COST_LAW` by law).
- A3-LOW-2: add a cross-reference noting `T_ret` (recorded at activation)
  refines umbrella C-XS-3's "preregistered timestamp" wording.

## 9. Limitations

- Draft-level audit only: no implementation or tests exist yet; all fixtures
  were audited as specified requirements, not executed.
- A2 P-1's "realized fraction ≈ 0.99946" is a planning-level number carried
  from the D3 packet; provenance not re-derived (does not gate any verdict).
- The D4 decision text itself is not on file in this review's sources; the
  A3-MED-1 finding stands under either reading of the header sentence (faithful
  quote of a stale D4 phrasing, or a drafting leftover) because the draft must
  be internally consistent regardless.
- The current XSECT `valuation_marks` file's newest row differs from the
  99,094.92 umbrella-measured mark (marks update over time); A3's example was
  checked against the umbrella §4.5 measured basis and the live ledger, both of
  which match.

## 10. ROUND 2B — A3 remediation delta check (append-only)

- **Delta claimed:** only the §0 header sentence reworded; no other change to
  A3. **Verified:** full re-read of
  `plans/DRAFT_amendment_PSCTV1_A3_xsect_retire.md` against the round-2 read.
  The ONLY diff is in the §0 status blockquote (lines 3–9), where
  "a separate timestamp freeze at this amendment's GO gate governs" is replaced
  by "the stop-open law takes effect only at the recorded ACTIVATION moment
  `T_ret` (Phase A, §1 lifecycle), not at the GO." All other content — §0
  measured basis, §1 lifecycle (binding), R-1/R-1b/R-2/R-3/R-4, §2, §3
  (fixtures (a1)/(a2)/(b)/(c)/(d), equity-basis naming), §4 GO gate, §5 — is
  byte-identical to the round-2 read (file 101 → 102 lines, consistent with the
  re-worded sentence's extra wrap line).
- **Closure assessment:** the replacement sentence is consistent with binding
  §1 ("The GO typing time is NOT `T_ret`") and §4 (GO authorizes code-writing
  ONLY); it no longer defaults any stop-open/activation/timestamp event to the
  GO gate. Internal contradiction resolved. **A3-MED-1 CLOSED.**
  A3-LOW-2 (C-XS-3 "preregistered timestamp" cross-reference) remains open,
  non-blocking.
- **Re-issued verdict: A3 = PASS** (0 HIGH, 0 MEDIUM, 1 LOW).
- Set-wide after round 2b: A1 PASS, A2 PASS, A3 PASS — HIGH 0, MEDIUM 0,
  LOW 4 (A1-LOW-1, A2-LOW-1, A2-LOW-2, A3-LOW-2; all advisory, none blocking).
  All three drafts are adequate to proceed to their own GO gates.
