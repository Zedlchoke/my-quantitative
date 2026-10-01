# SKEPTIC_PREREG_FINAL — fresh-context final pre-registration review (2026-10-01)

Reviewer: fresh-context skeptic, no authorship of any reviewed object.
Read-only everywhere except this one file. `.venv/bin/python` used for
read-only recomputation. Objects reviewed: everything under
`…/successor/daily_successor/` at main HEAD 541fc223 (plus the untracked
`G6_ADJUDICATION.md`, flagged below), worktree
`.worktrees/pc12a-daily-exploratory-prep` @ 2f7bc832 (engine + tests +
`research/control/DAILY-EXPLORATORY-V1/FREEZE.md`), and context
(`DECISION_PACKET.md` §13, `PASS_BARS_V2.md`,
`SUCCESSOR_PLAN_DRAFT.md`, `OI_DECISIONS_APPLIED.md`).

Owner election of record (dispatch, verbatim): **"ĐI TIẾP KHÔNG CÓ SAO
KÊ"** — exploratory-only amendment for a NEW DAILY exploratory cycle;
OI-2 NOT_RUN; DECLARED costs only; no MEASURED/after-cost PASS;
exploratory PnL under ×1.0/1.5/2.0 stress; no edge claim from exposed
folds.

Everything below was re-measured by this reviewer unless marked
"reported-only". Verdict at the end.

---

## 1. Exploratory-only law — is it airtight?

**Core scoping: AIRTIGHT where it matters.** Four independent layers,
each independently read and none contradicted by any output I could
produce or find:

1. `PLAN_DAILY_SUCCESSOR_DRAFT.md` §4 opens with the binding scope law:
   "every bar in this section reads ONLY on the prospective surface
   (≥6×26w of post-registration accumulated daily bars; earliest honest
   evaluation ≈ 2029-09 …) The §2 2020–2026 battery (folds 1–8) is
   EXPLORATORY reporting at most — no PASS, no GO, no after-cost claim
   is readable from it; 'pooled over folds 1–8' below means exploratory
   reporting only." §0b ¶4 carries the same law at admission level;
   §2 states "All folds in this section are EXPLORATORY per §0b ¶4".
2. `DRAFT_AMENDMENT_EXPLORATORY_ONLY.md`: "No scored GO is requested or
   implied … No after-cost PASS, **ever**, under this amendment … every
   net number carries PROVISIONAL/DECLARED labels; survival claims are
   impossible by construction." Budget consumed "as EXPLORATORY ledger
   rows only".
3. Worktree `FREEZE.md` (scope header): owner election verbatim quoted;
   "no after-cost PASS ever; PnL published only as exploratory under
   frozen ×1.0/1.5/2.0 stress; **no edge claim from the 2020–2026
   exposed folds**; validation surface = post-registration prospective
   accumulation only".
4. **Mechanical layer (strongest):** the G9 journal writer enforces the
   RGC-INC-1 leak law at write time on every row — forbidden
   key vocabulary (`pnl`, `profit`, `sharpe`, `drawdown`, `equitydelta`,
   `return`, `cagr`, `calmar`, `sortino`, `winrate`, …; tokens `pf`,
   `pnl`, `ret`, `rets`, `dd`, `pl`) anywhere, nested included, fails
   the write (`journal.py` `scan_keys_for_leaks` +
   `_validate_row`). Poison counter-tests pass (top-level and nested).
   The cost kernel and quote-CCY book expose identity components, cost
   bills and bookkeeping levels only — no performance field exists in
   any output dataclass (read line-by-line). So even the exploratory
   battery cannot emit a journal row that LOOKS like a score.

Greps for edge/survivor/outperform/alpha language across all package
files: nothing beyond bar definitions and boundary-compliance lines.
No file claims validation, edge, or survival from the 2020–2026 folds.

**Findings:**

- **[BLOCKING — F1] §7 (the operative registration-gate text) still
  gates registration on OI-2 landing, with no exploratory-only
  carve-out in §7 itself.** §7 item 1: "OI-2 LANDS … Until then the
  NOT_RUN_STATEMENT blocker stands — no scored run, no after-cost PASS,
  nothing in this plan scores", under "GATE — registration of the
  scored DAILY successor executes ONLY when ALL hold". The elected
  path (register the EXPLORATORY-ONLY amendment with G1/G2 NOT_RUN) is
  authorized elsewhere — §0b ¶2 G1 row ("An EXPLORATORY-ONLY amendment
  … may be registered instead if the owner elects it"),
  `OI_DECISIONS_APPLIED.md` OI-2 option (c), the DRAFT_AMENDMENT, and
  the owner election — but §7 is the sentence a registering agent
  executes, and it directly contradicts the worktree FREEZE.md's
  "Registration authorized by owner election." This is the SAME defect
  class the prior adjudicator graded BLOCKING ("the operative sentence
  at registration" contradicting §0b — SKEPTIC_OWNER_REVIEW_ADJUDICATION
  Q4/B2). Minimal fix below.
- **[MINOR — F2]** §7's registration input-naming list ("this plan +
  OWNER_PACKET v2 + GATE_UPDATE v2 + GATE_TABLE_V2 + frozen manifests +
  DAILY_ADMISSION_MATRIX + OI_DECISIONS_APPLIED") predates the
  G3–G10 artifacts and does not name `G3_G4_VIX_SIGMA.md`,
  `G5_G6_SPREADS_INPUTEND.md`, `G6_ADJUDICATION.md`, `g6_pull/
  {MANIFEST,VERIFICATION}.json`, `DRAFT_AMENDMENT_EXPLORATORY_ONLY.md`,
  or the worktree FREEZE.md + engine commit. Fold into the F1 edit.
- **[MINOR — F3]** §4 inheritance line "≥6-fold calendar floor — met
  with 8" is residual old-law phrasing (under the scope law the floor
  can only be met by prospective folds; the 8 are exploratory).
  Defused by the scope-law paragraph immediately above it, but a reader
  quoting lines in isolation could misuse it. One-clause conform.
- **[MINOR — F4]** `ACTION_PACKET_GATES.md` and the
  `G7_G8_G10_FREEZE_DRAFTS.md` "Gate status" table are pre-pull,
  pre-adjudication, pre-election state ("G6 NOT_RUN — 2 lawful options
  ready"; "when G1–G12 ALL PASS → register"; "amendment … NOT
  dispatched"). They are dated session artifacts (evidence of the
  past), but the registration packet must NOT cite them as current
  gate state — the plan §0b, G6_ADJUDICATION and FREEZE.md supersede.
- **[INFO — F5]** DRAFT_AMENDMENT item 1's "validation = post-
  registration prospective surface only" could be misread as
  prospective data eventually validating THIS cycle. Item 2 ("No
  after-cost PASS, ever, under this amendment") blocks that in
  substance (all PB2 bars are net-of-all-costs bars). One clarifying
  sentence at dispatch — prospective accumulation feeds the LATER
  measured-cost re-registration — would close the ambiguity.

## 2. G6 adjudication legality (ruling (b), owner's no-relabel law)

**The FAIL stays recorded — verified in the artifact of record.**
`g6_pull/VERIFICATION.json` `sanity_verdicts.pre_registered_band` =
`{"AUDUSD": "FAIL", "USDCAD": "FAIL"}` with the band note verbatim;
`G6_PULL_REPORT.md` §6 reports "FAIL on both pairs"; the adjudication
(§2.3) explicitly does NOT endorse the lane's "PASS-with-disclosure /
overall PASS" verdicts as they stand — a PASS over a failed
pre-registered screen is lawful only after the owner freezes the
corrected law, and the same measurements then pass **by measurement
under the new law, not by relabeling**. No relabel anywhere I looked.

**The corrected law is justified by the observable's nature —
re-measured independently, every number reproduces:**

- **The failing leg is unsatisfiable by the accepted corpus.** I
  recomputed the frozen 7-asset corpus close-side stats (all-weekday
  quantile 'lower', crossed-book filter): NZDUSD Q3-2026 p90 = 8.0
  (fails strict `< 8`), USDCHF 12.5; full-window NZD 11.5 / CHF 14.0 —
  exactly the adjudication's §1.1 proof 1. A band the frozen accepted
  panels cannot pass cannot discriminate data quality.
- **The Friday exclusion is mechanism, not convenience.** Same frozen
  corpus, same quarter: NZD Friday median 8.0 vs midweek 0.5 (16×);
  CHF 13.5 vs 3.0 (4.5×); full-window Friday medians 10.5 / 9.5 — all
  reproduce the adjudication §1.3. G6 pull (my re-derivation from the
  raw files): midweek medians 1.5 / 2.0 vs Friday 8.5 / 16.0; 10 of
  the top 13 spreads are Fridays on both pairs — the all-weekday p90
  measures day-set composition (weekend-stale session-last prints),
  not data quality. Because the same regime exists in data frozen and
  accepted 2026-09-30 (before this pull existed), excluding Friday
  from magnitude gating cannot be data-driven convenience; the
  adjudication also keeps Friday DISCLOSED (median/p90/max + top-tail
  weekday composition) and never trimmed (owner G5 no-trim law).
- **The anchors pre-date the pull.** Envelope-law midweek bracket
  [0.5, 3.0] pips = the frozen corpus's own midweek p50s (NZD 0.5, CHF
  3.0 — verified); midweek p90 cap 11.0 = corpus full-window midweek
  p90 max (CHF 11.0 — verified). G6 passes by measurement with margin
  (midweek p50 1.5 / 2.0; midweek p90 4.0 / 3.5 — both re-derived by
  me), not a boundary fit.
- **The excluded quantity prices nothing.** The daily kernel fills at
  the bar's own OPEN side quotes (`costkernel.price_fill` reads
  `ask_open`/`bid_open`; the close-side statistic the failed band
  measured is not a cost-consumed quantity) and the owner's G5 decision
  already classifies the async two-sided daily difference as a
  BAR-SIDE DIFFERENCE, not an executable spread.
- **Rejection typing correctly refused.** `NOT_RUN_INPUT_END` has
  fixed semantics = consumed bar does not exist. The bars exist (I
  re-hashed 16/16 raw files against `MANIFEST.json`; coverage 66/66
  weekdays, sides date-aligned); typing absence over existing
  sha-verified data would write a false trial-accounting record.
- **Stricter-where-it-counts check:** the corrected law ADDS fail-closed
  structural legs (crossed books, side alignment, minTick multiplicity,
  mid-domain, coverage) and a same-source midweek bracket the old band
  lacked; it loosens only the one quantity proven miscalibrated (the
  absolute all-weekday p90 cap) and narrows the C1-multiple leg to the
  commensurable midweek subset. The no-loosening claim survives.

**Findings:**

- **[MINOR — F6]** `G6_ADJUDICATION.md` is **untracked** in the main
  repo (present in the working tree, not at HEAD). The plan, FREEZE.md
  and the envelope law all reference it. It must be committed with/at
  the registration commit or the frozen law points at an untracked
  file.
- **[MINOR — F7]** The adjudication reserves the envelope-law freeze to
  the OWNER ("takes effect only at owner freeze"); the lane-authored
  worktree FREEZE.md declares "Corrected envelope law
  HMDS-D1-CLOSE-ENVELOPE@1 frozen per G6_ADJUDICATION.md". The
  registration act must EXPLICITLY ratify HMDS-D1-CLOSE-ENVELOPE@1 and
  the G6 data acceptance — the recorded election phrase covers the
  exploratory-only amendment, not expressly the envelope law. One
  sentence in the registration packet closes it.

## 3. Engine integrity (worktree @ 2f7bc832)

- **Tests: 13/13 PASS, run twice by me** (0.27 s / 0.34 s), worktree
  clean after both runs. Coverage matches the dispatch order: quote-CCY
  §6 identity on hand numbers (EURUSD + USDJPY + blocked-zero-event +
  Wed×3), ×1.5/×2.0 stress, bar-side-difference law, hardcoded band
  table, tamper detection (edit/delete/reorder/restore), leak-law
  poison counter-tests (top-level + nested), byte-identical
  determinism, OI-1 next-business-day enforcement (incl. lookahead,
  Saturday, Sunday, too-late rejections).
- **Independent quote-CCY verification on MY OWN synthetic case**
  (constructed by me, not from their fixtures): USDJPY BUY 50,000 Mon
  2026-06-01 @ ASK_open 144.200 (+0.2 pip slip → 144.202), hold through
  Mon×1 + Tue×1 + Wed×3 swap events (Thu 22:00 after the exit
  correctly NOT charged — verified against
  `iter_swap_events`), SELL Thu @ BID_open 149.800 − slip → 149.798;
  non-exact-decimal same-bar rates. Hand-computed ledger: commission
  252.3535 / 262.1465 JPY, spread_once 5,000 + 5,000 JPY, slip 100 +
  100, swap 2,500 JPY. **Engine matches on every line; §6 identity
  residual = 0 exactly; final cash 3,877,846.170814… JPY equals the
  hand ledger to the last digit; level change = hand LHS 276,785.50
  JPY; conversion rows one-per-event (1 open + 2 fills + 3 swaps) at
  the correct same-bar rates; par replay within the disclosed bound.**
  (My single initial 100-JPY mismatch was my own hand-arithmetic slip —
  50,000 × 149.798 = 7,489,900, not 7,498,000-class; the engine was
  right, the corrected hand ledger agrees to full precision.)
- **Forbidden keys:** recursive grep over all package outputs
  (`g6_pull/**.json`, engine outputs) for performance-named keys:
  clean. The writer's built-in scan is the load-bearing guard and is
  counter-tested.
- **Determinism:** no wall-clock in rows; explicit byte-identical
  re-run test; my two full suite runs identical.
- **[INFO — F8]** `next_business_day` models weekend-skip only; the
  holiday calendar is a named registration-freeze item (disclosed in
  the code). The registration must name it or accept the typed
  fallback — it affects `available_time_utc` validity on
  holiday-adjacent sessions for the REAL panel runs (not the fixtures).

## 4. FREEZE.md completeness (worktree `research/control/DAILY-EXPLORATORY-V1/FREEZE.md`)

**Present and correct:** OI-1 labels + σ tripwire values (64.64 /
49.62 / 112.18, never loosened); G5 no-trim decision + band-cell role
law; G6 pull state + FAIL-stands + adjudicated envelope law; G9 engine
commit 09fb1b74 + 13/13 leak-clean + synthetic-only; slate DS-03+DS-05
with 5 parked; budget ≤10 identities / ≤83 rows; calendar folds +
prospective law + S1 SEALED; PASS-bar scoping (no edge claim, no
after-cost PASS ever); DECLARED-cost labels; owner election verbatim;
forming-bar exclusion.

**[MINOR — F9] Missing/under-specified for a self-contained freeze:**

1. warmup 52w / LEARN 51w (2021-10-01→2022-09-22) / embargo 1w
   boundaries, the fold-date table and the rounding-down-to-whole-weeks
   law are not restated or referenced by section (only "8×26w
   2020-10-02→2026-09-24").
2. LEARN grid G1 nodes (B 3% default / C 5%, A null-control-only) and
   the LEARN selection objective + tie-break chain.
3. G3's tail re-extension duty: 2026-09-28/29/30 post-date the frozen
   VIX fetch (G3_G4 §1.4 requires the registration re-run to
   re-extend); the freeze's "G3 PASS" should carry that duty.
4. G5 honesty nit: "Band cells D1BAND-* frozen per G5_G6 file" — but
   the G5 file's table covers only NZD/CHF/XAU/XAG; the VEHICLE
   instruments' cells (EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD) are
   `NOT_COMPUTED` by the plan's own §5 law (a registration-freeze
   MEASURED-DERIVED computation from the frozen M1/H1 panels). "All
   prereg gates resolved" slightly overstates G5 on the vehicle side.
   Fails safe (the kernel types NOT_COMPUTED and never guesses; fills
   price from the bar's own side quotes; bands are validation-only),
   but the registration ceremony must run that derivation.
5. Declared cost constants (U2 0.35 bps/side; U3 0.2/1.0 pip; U4/U5
   1 pip/night Wed×3 calendar) are pinned only via engine commit
   09fb1b74 + PLAN §5 — one restating line would make the freeze
   self-contained.
6. OI-3 XAU pinned-archive sha `49c2684e…`, OI-5 EIA labels, AUD/CAD
   conIds (14433401 / 15016062, in `MANIFEST.json` but not the freeze).

## 5. Boundary sweep — CLEAN

- **No S1/paper/live/orders/GO:** g6_pull scripts connect
  `readonly=True` (clientIds 66/69), `orders_placed=0`,
  `market_data_subscriptions=0`, no whatIf/account-data/subscription
  requests; VERIFICATION.json confirms; greps over all objects clean;
  every reviewed doc repeats no-S1/no-orders/no-GO.
- **TERMINAL cycles untouched:** main-repo commits 3acf085d, 7d14f72e,
  9db7f7f1, 541fc223 touch ONLY `terminal_review_2026-10-01/**`;
  worktree commits 09fb1b74/2f7bc832 touch ONLY
  `research/daily_exploratory/**`, `tests/test_daily_exploratory.py`,
  `research/control/DAILY-EXPLORATORY-V1/FREEZE.md`.
- **No closed-budget reuse:** fresh 10-identity/≤83-row rescope for a
  NEW cycle; `researchctl cycle list` shows DAILY-EXPLORATORY-V1 NOT in
  the registry (no premature registration act; the FREEZE is labeled
  preparation).
- **Owner dirty tree preserved** exactly as found (data-lane
  SIXSOURCE files + untracked SLEEVE/SANDBOX dirs + G6_ADJUDICATION.md
  — untouched by this review); data-lane worktree read only.
- **No account IDs/keys anywhere:** `account_ids:
  "REDACTED-NOT-RECORDED"`, `paper_du_prefix_only: true`, described
  log redaction; raw files are pure OHLC rows; DU-prefix / accountId /
  api-key / secret greps clean.

## 6. Registration readiness (G1/G2 NOT_RUN by election)

| gate | genuinely resolved? |
|---|---|
| G1/G2 | NOT_RUN **by owner election** — lawful per §0b gate table + OI-2 option (c) + DRAFT_AMENDMENT + election on record. NOT a gap, but §7 text must say so (F1). |
| G3 | computed + verified (50/50 sha; dual-channel 9,278/0 diffs; t→t+1-close law). Registration re-run + tail re-extension duty stands. |
| G4 | computed; NZD 64.6388 / CHF 49.6150 reproduce lane Δ0.0000; XAU 112.1838 freeze-basis. Registration-day re-run duty stands. |
| G5 | computed + probe-exact for the 4 IBKR instruments; VEHICLE-side D1 band cells remain a named registration-freeze computation (F9.4). |
| G6 | pulled (16/16 sha re-hashed by me), adjudicated; owner ratification + commit of G6_ADJUDICATION.md outstanding (F6/F7). |
| G7 | complete (DS-03/DS-05 param sets; parked legs frozen-as-parked with named un-park conditions). |
| G8 | FREEZE.md is the manifest; the freeze ACT is registration itself. |
| G9 | built + tested leak-clean; real-panel runs correctly wait for the cycle. |
| G10 | complete draft law (per-input collection; earliest honest eval ≈2029-09). |
| G11/G12 | correctly phased at/post registration. |

Prior skeptics' blocking findings (B1 PASS-scoping, B2 budget rescale,
B3 G1 node A; F-1/F-2/F-3/F-5/F-6 citations) — all verified as
discharged in the current text.

---

# VERDICT: **FIX_THEN_REGISTER**

The package is substantively ready — the exploratory-only law is
enforced in prose AND mechanically, the G6 adjudication is lawful and
mechanism-justified (independently re-measured), the engine is exact,
and boundaries are clean. But a pre-registration package lives on
unambiguity, and one operative sentence still contradicts the elected
path. Exact minimal edits (all in editable draft/registration
documents; none touch frozen evidence):

1. **(F1, BLOCKING)** `PLAN_DAILY_SUCCESSOR_DRAFT.md` §7 item 1 —
   append one carve-out sentence, e.g.:
   > "**Exploratory-only carve-out (owner election 2026-10-01, 'ĐI TIẾP
   > KHÔNG CÓ SAO KÊ'):** this item is satisfied for the
   > EXPLORATORY-ONLY amendment of `DRAFT_AMENDMENT_EXPLORATORY_ONLY.md`
   > by the owner's recorded election with G1/G2 NOT_RUN — registration
   > then proceeds under DECLARED costs with no after-cost PASS ever
   > (§0b ¶2 G1 row); the measured-cost scored cycle remains gated on
   > OI-2 landing as written."
   In the same edit, extend the §7 "Then A1" input list to name
   `G3_G4_VIX_SIGMA.md`, `G5_G6_SPREADS_INPUTEND.md`,
   `G6_ADJUDICATION.md`, `g6_pull/{MANIFEST,VERIFICATION}.json`,
   `DRAFT_AMENDMENT_EXPLORATORY_ONLY.md`, and the worktree
   `DAILY-EXPLORATORY-V1/FREEZE.md` + engine commit 09fb1b74.
2. **(F6, required at the registration commit)** commit
   `G6_ADJUDICATION.md` (and this review) so the frozen envelope law
   references a tracked artifact.
3. **(F7, registration-ceremony content)** the registration packet
   must explicitly ratify **HMDS-D1-CLOSE-ENVELOPE@1** and the G6
   AUD/CAD D1 acceptance, and record the owner election verbatim
   (FREEZE.md already quotes it; the registry entry should carry it).
4. **(F9, same touch)** add to FREEZE.md: calendar detail reference
   (warmup/LEARN/embargo/fold table + rounding law, PLAN §2); G1 grid
   nodes + LEARN objective; G3 tail re-extension duty; the G5
   vehicle-side NOT_COMPUTED note (registration-freeze derivation,
   MEASURED-DERIVED, logged); declared-cost constants one-liner; XAU
   archive sha; conIds.
5. **(F3/F5, optional conforming)** §4 "met with 8" → "calendar floor
   reads only on prospective folds (8 exploratory folds exist for
   reporting)"; one sentence in the amendment clarifying prospective
   accumulation feeds the LATER measured-cost re-registration.
6. **(F4, usage note)** do not cite `ACTION_PACKET_GATES.md` /
   `G7_G8_G10` gate-status tables as current state in the registration
   packet (they are pre-adjudication session evidence); §0b +
   G6_ADJUDICATION + FREEZE.md govern.

Registration ceremony must additionally EXECUTE the named freeze-time
acts: G3 re-run + VIX tail re-extension, G4 re-run on registration-day
bytes, G5 vehicle-side band derivation (MEASURED-DERIVED, logged), and
name the holiday calendar for `next_business_day` (F8). No blocker
found in the engine, the data, the adjudication's legality, or the
boundaries.

Nothing in this review scores, registers, freezes or amends anything;
no PASS inferred from any cell; OI-2 stands.

— end SKEPTIC_PREREG_FINAL —
