# A7 F4/F5 Novelty & Rubric Audit — Cycle FOREX-FREE-V1

- **Auditor:** A7 (independent; audit artifacts only — no repairs, no selection, no returns)
- **Measured at UTC:** 2026-09-03T08:53:54Z
- **Worktree:** `integration/.worktrees/forex-free-v1/f5-a7-audit`
- **Branch:** `orca/forex-free-v1-f5-a7-audit` — **HEAD:** `858f6802c6d03a455552dd7ba0355a612f55aaed` (matches bootstrap; tree clean at audit start)
- **Authoritative machine-readable artifact:** `a7_f4_audit.json` (same directory)

## 1. Scope and inputs

Six new H1 proposals audited against the frozen selection rubric (`research/control/forex_free_v1_run/worktree_manifest.json::selection_rubric_frozen_before_audit`, items R1–R9, applied verbatim, never modified), the amended data contract (H1-only, 6.5y floor, bid/ask and financing UNAVAILABLE_FAIL_CLOSED), and — read-only — the six frozen old-cycle proposals and the old F2 novelty audit for the rescue check. DST/session claims were verified against `research/assets/forex/sessions.py`, the `tests/assets/forex/test_sessions_dst.py` goldens, and A7's independent zoneinfo recomputation across all four annual US/UK DST configurations of 2026.

## 2. Verdict table

| Proposal | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | Verdict | Worst objection |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FXFV1-A3-P1 (London-open 3-bar momentum) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **ELIGIBLE** | LOW |
| FXFV1-A3-P2 (late-NY fade, z-gated) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **ELIGIBLE** | LOW |
| FXFV1-A4-P1 (Tokyo range → London breakout) | PASS | PASS | PASS | PASS* | PASS | PASS | PASS | PASS | PASS | **ELIGIBLE** | **MEDIUM** |
| FXFV1-A4-P2 (London→NY threshold-free momentum) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **ELIGIBLE** | LOW |
| FXFV1-A5-P1 (EUR-core lead-lag, 2-leg USD-neutral) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **ELIGIBLE** | LOW |
| FXFV1-A5-P2 (NY-morning USD momentum, single leg) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **ELIGIBLE** | LOW |

\* A4-P1's R4 is a PASS on control *validity* with a MEDIUM spec-gap objection on the control arm (below). No R1–R7 FAIL exists anywhere; no HIGH/CRITICAL objection; no hidden rescue. All six are eligible; each scores 9/9, so the frozen lexicographic tie-break will bind. A7 expresses no preference.

## 3. Rollover avoidance and DST verification (measured)

Repo ground truth: rollover 17:00 America/New_York = 22:00Z EST / 21:00Z EDT; Friday close 16:00 NY = 21:00Z / 20:00Z; Sunday open 21:00 NY = Mon 02:00Z / 01:00Z (matches test goldens and independent recomputation).

- **A3 lane** (P1, P2): flatten at the close of the last completed bar strictly before the rollover — uniformly the bar ending **16:00 NY wall clock** (21:00Z EST / 20:00Z EDT), exactly 1h before the rollover in both configurations. The rule is stated in named-zone arithmetic, so it survives both DST configs by construction. A3-P2's 13:00→16:00 NY hold is 3 bars year-round (both instants NY-keyed).
- **A4 lane** (P1, P2): flatten fill at the **open of the 15:00 NY bar** (bar completes 16:00 NY) — measured exactly **2.0h before the rollover in EST and EDT**; one-event-delayed exits collapse into this fill by frozen rule, so the delay can never breach the invariant. Friday's 15:00 NY stamp is the week's last canonical bar.
- **A5 lane** (P1, P2): exit at the close of the **bar closing 16:00 ET** — measured strictly before the rollover in both configs; the 16:00–17:00 ET fixing-adjacent bar is never held; Friday override exits at the 15:00 ET close (the bar closing exactly *at* the 16:00 weekly close is not "strictly before" it) — internally consistent in both proposals.

Structural Monday/weekend facts (all measured, all handled):

- **A4-P1**: every Monday is invalid — only 5 (EDT) / 4 (EST) canonical Tokyo range bars exist because Mon 09:00–10:00 JST precedes the Sunday 21:00 NY open. Documented by the proposal as a calendar fact; confirmed.
- **A4-P2**: anchor Mondays valid (London window always post-open); Tokyo control Mondays structurally invalid (stamps 08–09/10 JST pre-open). Documented; confirmed.
- **A3-P2**: Tokyo neighbour Monday p0 bar (ends 09:00 JST = 00:00Z) is **always** out-of-calendar — *not documented* by the proposal (OBJ-A3P2-1, LOW); the fail-closed missing-bar rule is the implicit handler and is safe iff F8 gates every referenced bar by the frozen calendar.

## 4. Cost honesty

All six declare numeric frozen matrices before any return, include **x1.5 and x2** stress and a **one-event delay**, and disclaim live spreads explicitly. Verified arithmetic: A5-P1 costs **both legs on entry and exit** for the two-leg books ((1.6364+2.0)/2 = 1.8182 bp EUR→GBP; (1.6364+4.0)/2 = 2.8182 bp EUR→AUD) with leg bp derived correctly from frozen pip specs and round reference rates; A5-P2 is single-leg and discloses that its "x2 exceeds any both-legs charge" claim is an argument, not a computation (OBJ-A5P2-2, LOW). A3/A4 single-pair books cost both sides (entry+exit round trip).

## 5. Causal-control validity

All six controls genuinely destroy their mechanism if it is real: sign-flip mirrors (A3-P1, A3-P2), session-translated controls holding rule/execution/exit constant (A4-P1 quiet-window breakout, A4-P2 Tokyo-midday momentum), reversed leader/follower direction (A5-P1), and a causally valid prior-day placebo (A5-P2). One spec gap: **A4-P1's control arm** entries at 19:00–21:00 NY bar opens violate the *letter* of its own "no fill at/after 15:00 NY" invariant, and the same-day 15:00 NY flatten is unreachable; the unique consistent reading (exit at the *next* day's 15:00 NY flatten) crosses no rollover instant and no weekend (Friday control entries are out-of-calendar) and preserves the causal logic — but it must be frozen explicitly before any return exists (OBJ-A4P1-1, **MEDIUM**).

## 6. Novelty / hidden-rescue check — R8: PASS, no rescue found

Compared against the six old mechanisms (rollover-window premium; relative-spread scarcity; DST-desync overlap premium; pre-release withdrawal premium; PIT rate-differential carry; fixing-and-rollover window exposure):

1. **Old rollover-window premium** (holds *across* 17:00) — every new proposal is flat strictly *before* every rollover; exposure at the boundary is identically zero. A3-P2's rollover-adjacent *narrative* does not change its traded object (fade of same-day NY extensions; signal and exposure window both differ). Not a rescue.
2. **Old spread-scarcity** (quote-spread panel) — no new proposal touches spread/quote data; price-only throughout.
3. **Old DST-desync premium** (conditions on desync weeks) — no new proposal conditions anything on DST phase; A4-P2 mentions desync only as a labeling fact and tests robustness across it.
4. **Old pre-release premium** (holds pre-release windows) — no macro-calendar gating anywhere; A4-P2 keeps 08:30 NY releases *inside* its holding window; A5-P1 explicitly refuses calendar filtering.
5. **Old PIT carry** (financing is the mechanism) — structurally incompatible: zero financing, flat at rollover, financing fail-closed.
6. **Old fixing/rollover window premium** (holds through fixings and the financing hour) — no fixing instant referenced anywhere; A5 explicitly avoids the fixing-adjacent bar; 16:00 London inside A3-P1/A4-P2 holding windows is incidental to session-momentum direction. (The old FX2-A5-P2 was already INELIGIBLE in the frozen F2 audit; nothing of it reappears.)

## 7. Orthogonality (6x6)

Graded on mechanism / signal / clock / universe. **1 HIGH, 9 MEDIUM, 5 LOW.**

| | A3-P1 | A3-P2 | A4-P1 | A4-P2 | A5-P1 | A5-P2 |
|---|---|---|---|---|---|---|
| **A3-P1** | — | LOW | MED | **HIGH** | MED | MED |
| **A3-P2** | LOW | — | LOW | LOW | MED | MED |
| **A4-P1** | MED | LOW | — | MED | LOW | LOW |
| **A4-P2** | **HIGH** | LOW | MED | — | MED | MED |
| **A5-P1** | MED | MED | LOW | MED | — | MED |
| **A5-P2** | MED | MED | LOW | MED | MED | — |

**The HIGH pair — FXFV1-A3-P1 vs FXFV1-A4-P2 — is the headline finding.** Both are post-London-open intraday momentum (both cite Gao-Han-Li-Zhou 2018); the signal windows differ by exactly **one bar** (3 vs 4 London-morning bars, both anchored at the 07:00-London-stamp close); both fill at the **same instant and same price** (12:00 London); exits differ by one hour (bar closing 16:00 NY vs 15:00-NY-bar-open); identical 7-pair universe. These are near-duplicate trades on almost every day. Flagged for the selector: the frozen selection rule has no orthogonality cap, but if both rank at the top they should be treated as one candidate cluster, not two independent families.

The A3-P2 ↔ A5-P1 MEDIUM cell is also substantive: identical trigger variable on EUR/USD (08:00–12:00 ET z-gated move) and identical execution clock (13:00→16:00 ET), with *opposite* EUR-leg signs — near mirror tests of the same events, not redundant but not independent.

## 8. Outcome blindness and trial counts

Grep sweep + full read: **zero computed returns anywhere**; every performance-vocabulary hit is a no-backtest declaration. Quantitative forward statements are limited to trade-count design bounds (A4 lane), a calendar warm-up date (A3-P2), and frozen costs. Trial counts: A3/A4 lanes declare 21 = 3 arms × 7 pairs each (expected and fine); A5 lanes declare 3 fixed pair-set configurations each (cost/delay tiers correctly excluded as accounting stresses). All coherent.

## 9. Objection register

| ID | Proposal | Severity | Objection |
|---|---|---|---|
| OBJ-A4P1-1 | FXFV1-A4-P1 | **MEDIUM** | Control-arm entry window [18:00,21:00) NY contradicts the letter of its own flat invariant; exit rule under the control must be frozen explicitly (next-day 15:00 NY flatten crosses no rollover; no Friday entries possible) |
| OBJ-A3P1-1 | FXFV1-A3-P1 | LOW | "Uniformly 9 bars" holding window is 8 bars during the ~2–3 UK/US desync weeks (measured); operative named-zone rule unaffected; F1d diagnostic already guards clock artifacts |
| OBJ-A3P2-1 | FXFV1-A3-P2 | LOW | Tokyo neighbour Monday p0 bar always out-of-calendar (measured); undocumented; fail-closed missing-bar rule must gate by the frozen calendar in F8 |
| OBJ-A4P1-2 | FXFV1-A4-P1 | LOW | "Deep Asian quiet window" imprecise in EST weeks (18:00 NY = 08:00 JST, Tokyo open); control design still valid |
| OBJ-A4P1-3 | FXFV1-A4-P1 | LOW | Data-gap exit can in principle reach the next weekly open; already logged-as-breach + reconciled, never silent |
| OBJ-A4P1-4 / OBJ-A4P2-1 | A4 lane | LOW | "Decision instant strictly before fill instant" is imprecise — they are equal (fill at next bar open at publication instant); standard, non-look-ahead convention |
| OBJ-A5P1-1 | FXFV1-A5-P1 | LOW | F2 kill compares anchor NET vs control GROSS — deliberate, disclosed conservatism; implement as frozen, do not "fix" |
| OBJ-A5P2-1 | FXFV1-A5-P2 | LOW | Friday × one-event-delay cell is degenerate (zero-hold, cost-only); delayed-Friday-entry skip rule unstated; freeze before returns |
| OBJ-A5P2-2 | FXFV1-A5-P2 | LOW | "x2 exceeds any plausible both-legs charge" is an assertion, not a computed bound |

No blocker. Worst severity overall is MEDIUM (OBJ-A4P1-1), which under the frozen selection rule is not disqualifying (that requires a rubric FAIL on R1–R7, HIGH/CRITICAL, or a hidden rescue — none met).

## 10. Assumptions

1. JSON authoritative over MD (spot-checked consistent).
2. Canonical series exclude out-of-calendar bars (amended data contract), so pre-open bar references are "missing" under fail-closed rules.
3. Bar timestamps are bar-open instants, per the proposals' shared convention and the contract's completed-bar PIT guarantees.
4. DST claims verified against the repo sessions module, test goldens, and independent zoneinfo recomputation — not against raw provider data.
5. R9 feasibility judged on bar availability/warm-up only; no strategy statistic exists or was computed.

**Bottom line: 6/6 ELIGIBLE, no rubric fails, no hidden rescue, one HIGH orthogonality pair flagged (A3-P1 / A4-P2), one MEDIUM spec-gap objection (A4-P1 control arm). Selection is the controller's call under the frozen rule; A7 expresses no preference.**
