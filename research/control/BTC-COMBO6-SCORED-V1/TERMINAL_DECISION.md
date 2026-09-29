# TERMINAL_DECISION — BTC-COMBO6-SCORED-V1 — 2026-09-29

## Verdict
**TERMINAL: COMBO6_NO_INCREMENTAL_VALUE** (predecided plan §7; A7 terminal
CONFIRM_WITH_CONDITIONS 0C/0H/1M/2L/4I, sha256 1ccca70ec39fb55763b2e76a3b464c2168eb056a3634cca8af5b75d90315c0a4).

Scored (stress ×1.0, folds F1..F10 = 2021-01-04..2025-12-29, net after 6bps/side +
measured funding): LEG-1 −46,534.21 · LEG-2 +4,707.81 · LEG-3 +1,662.25 ·
LEG-4 −6,618.22 · LEG-5 −9,515.51 · LEG-6 −7,319.99 · COMBO −63,617.86 (PF 0.9158,
4/10 folds, maxDD 97,271 on 60,000). Stress ×1.5 −100,107.48; ×2.0 −136,597.10.
B1 always-long +10,689.21 dominates every cell and the combo; B3 best-leg-prior
−12,645.24. Verdict bars: P1/P2/P3/P4/P5/P7 FAIL, P6 PASS (vacuous). 7/12 cells
(observed 7 = published 7, TRIAL_LEDGER.jsonl).

## A7 terminal conditions — discharged here
- **C1 (T-1 MEDIUM)**: DSR: **NOT_COMPUTED**. The plan §8 precondition (≥100
  observations) was met (6,080 combo trades) but no DSR field exists in any scored
  artifact. The sentence "DSR computed in artifact" in scored/SCORED_REPORT.md is a
  MISSTATEMENT — erratum recorded here; the frozen artifact is left untouched (no
  silent fixes, §39.5). This omission could not change the label: every governing
  bar P1-P7 fails on arithmetic independent of any DSR value.
- **C2 (T-2/T-3 LOW)**: freeze binding of record: CODE_FREEZE_SHA
  c0f97a9db2e460707188877348af01d1c5d395d6 (chain 2481f307 → 2db0e19b → c0f97a9d →
  ce1dd0ef → 7f3cce39 → this terminal commit). TRIAL_LEDGER header constant
  freeze_commit="PENDING_FREEZE" is DISCLOSED and intentionally left unedited
  (A7 recommendation: preserve twin-equality evidence; the binding lives here,
  in FREEZE.md, and in the registry row). Root registry closed at this commit:
  lifecycle TERMINAL, head = this commit, budget 7/12, GO phrase consumed-then-
  extinguished per P-8 (standing owner directive 2026-09-29, auth/GO_RECORDED.json).
- **C3 (T-4/I-1)**: the CORRECT stress ×2.0 content digest is
  e1a43807dd659175fbda60b3239d1238757505ef52ebe70d0bc438cd24a2776d (the
  …fbda6033… in the R-REPRO dispatch constant was a one-char transcription typo;
  every artifact, ledger row and both worktrees carry the correct value).

## Boundaries
S1 SEALED_UNTOUCHED. Sealed tail [2025-12-29, 2026-09-22) loaded-not-evaluated,
untouched (A7-verified). No orders/live/paper. No parameter rescue, no leg
promotion post-PnL. LEG-2/LEG-3 positives are recorded P1 PASSes inside a failed
portfolio — NOT survivors (no SURVIVORS.md entry; four-layer law §23 unsatisfied).

## Reopen door
A follow-up (e.g. slow-leg-only sleeve, any MA/RSI/momentum re-parameterization,
symbol swap, cost-tier relaxation) requires a NEW plan with fresh identity and
passes the ancestry fence against FAMILY_FAILURES line
BC6-OWNER-PINNED-TA-COMBO-6LEG + this ledger row. Changed mechanism axis only (Q-10).

## Reproduction
Detached twin @ c0f97a9d ALL_MATCH: 3/3 artifacts canonical-equal, 7/7 ledger rows
equal, truncation replay 18/18 prefix-exact (A7 terminal independently re-counted
all 18). P-4 applies: ALL_MATCH proves self-consistency, not truth.

## Durable assets
btcombo6 engine (PIT next-bar fill law, pessimistic TP/SL, measured funding,
fold walls, leak-proof dry mode, 27 tests), 102-zip sha-pinned 5m corpus with
perfect-grid census, dry/scored/lock wrapper kit, fold-erratum precedent
(independent data lane caught the arithmetic slip pre-freeze).
