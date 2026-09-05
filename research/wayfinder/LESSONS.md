# Program-level lessons register

> Maintained by the Lead Engineer. Distilled from cycle-level registers
> (stocks L1–L9, crypto L-V11-*, L-V14-0, forex per-cycle) into lessons that
> generalize across assets. Each entry: source incident → lesson →
> consequence (where it is encoded). Append-only; never rewrite history.

## P-1 — A plausible-sounding assumption passes every review

Source: Forex V3 survivor downgrade (2026-09-05). The BIS availability rule
("every CBPOL change is announced on or before its effective date") lived in
a code docstring, sounded economically correct, and passed A7 prelaunch, A7
terminal, and Lead review — until the owner's independent audit asked where
the evidence was.

Lesson: an assumption that matches reviewer intuition is never checked by
reviewer intuition. Only per-event evidence is evidence; asserted upper
bounds are `AGENT_ASSUMPTION_UNAUTHORIZED` until evidenced.

Consequence: availability-evidence tables with an EVIDENCED/ASSERTED/
UNEVIDENCED taxonomy are a named gate class (PLAN_crypto_v14 §2,
PLAN_stocks_v7 §6.P0b-2 gate 5); asserted bounds are never authorized.

## P-2 — Thin margins make micro-optimism fatal; report margin-to-fail

Source: the same remediation. Correcting availability on a handful of events
moved the survivor from PF 1.331 (17/17 gates) to PF 1.282 (16/17 — stress
tier 2.0 broke). A few hours of early readability on a few rate changes was
worth one full gate.

Lesson: at PF 1.2–1.3 there is no room for ANY optimism anywhere in the
chain (data timing, costs, fills, financing). A gate pass says nothing about
how close the pass was.

Consequence (new, from this incident): every future survivor must report
**margin-to-fail** — for each gate, the distance to its failure threshold —
so the program knows whether it is looking at a robust pass or a knife-edge
pass BEFORE any remediation shock hits it. To be encoded in the next
cycle plan that produces a survivor.

## P-3 — A control's verdict is conditional on its data authority

Source: V3R corrected recompute. The placebo control (−7.22, "fails as
designed") was computed under inferred availability; under evidenced
availability the control cell ABORTED (one USD/JPY decision → 4-day-late
fill, refused by the frozen validator). The mechanism-specificity evidence
could not be reproduced honestly.

Lesson: "control fired correctly" means "fired correctly *under the data
semantics it was computed with*". Any data-authority change must recompute
controls, not just anchors — a control verdict does not survive a semantics
change for free.

Consequence: V3R recomputed all three arms (this is what invalidated the
family, correctly); remediation plans now recompute controls as standard
scope.

## P-4 — Exact reproduction reproduces the bug, too

Source: V3's A7 terminal recomputed 39/39 fields and matched — computed from
bytes that themselves encoded the inferred availability. The audit was
perfect and the claim was still wrong.

Lesson (already handbook §28.2 — this incident is its proof case):
`REPRODUCTION_ALL_MATCH` certifies self-consistency, never scientific truth.
Reproduction re-runs the same assumptions under the same roof.

Consequence: ALL_MATCH is read as "consistent with itself" in every Lead
review; positive results additionally require the four-layer test
(mechanical / data / statistical / economic — handbook §21).

## P-5 — The remediation pipeline conserved S1, the program's only bullet

Source: the survivor was provisional, not promoted. Opening S1 for it would
have spent the program's single untouched out-of-sample window on a result
containing micro look-ahead.

Lesson: HARD STOP + provisional status + remediation-before-S1 is what stands
between the program and its most expensive possible mistake. The sealed
window is worth more than any single survivor.

Consequence: no survivor reaches an S1 plan without the four-layer test AND
a clean remediation verdict; S1 plans remain owner-only (unchanged, now with
a proof case for why).

## P-6 — Freeze the rules while calm; they are the only thing that holds when it hurts

Source: PLAN_forex_v3r §5 was written before any corrected number existed.
When the corrected books showed PF 1.2825 and exactly one failed gate, the
OTHERWISE branch fired without a single exception being argued — because
there was no room left to argue.

Lesson: the value of a gate is decided on the day it is written, not the day
it binds. Negative terminal branches in plans are not pessimism; they are
the pre-made decision for the moment the result is beautiful and wrong.

Consequence: every cycle plan carries terminal-negative outcomes as
first-class closes (standard since V4; this is the strongest proof case).

## P-7 — Bundle ≠ endpoint: a coverage verdict binds to the exact channel measured

Source: Stocks V8 probe-terminal (2026-09-05). The owner hand-downloaded
Stooq's bulk US bundle (`d_us_txt.zip`, sha256 `0a75aee8...`); the canary set
killed it in minutes — 0/14 dead names, absent with identical semantics to
never-existed controls, i.e. a currently-listed snapshot wearing a "full
history" label. Stooq's per-symbol CSV endpoint, meanwhile, has never been
measured for delisted coverage (V6 touched it only on living names before the
agent channel was closed).

Lesson: one provider serves several artifacts — bulk bundle, per-symbol
endpoint, API — and their universes can differ. A coverage PASS/FAIL names a
channel, not a vendor. Any channel switch re-runs the canary set (dead names
+ never-existed controls) before any universe freeze.

Consequence: the canary probe is mandatory per channel (second confirmed kill
after Twelve Data Basic in V7); encoded in `research/control/
stocks_free_v8_probe/probe_verdict.json` and carried into any future price
authority probe.

## P-8 — A GO phrase typed before its gate exists is intent, never a key

Source: Forex V4 (2026-09-05 10:41). The owner typed the exact launch phrase
`GO FOREX V4 SCORED EXECUTION` into the A1 thread while the cycle was still
in P0a — weeks before any prelaunch exists to stop at (and plausibly as a
"continue" nudge, since the phrase had been quoted to them as the future
gate). The A1 recorded it as a standing release but correctly preserved the
A7 `S0_LAUNCH_AUTHORIZED` condition and skipped nothing.

Lesson: the launch GO is the final human decision made WITH the A7 report in
hand — a two-key design (A7 key, then owner key, turned in that order). A GO
typed before the stop exists cannot carry that decision: it is recorded as
owner intent and is extinguished-unconsumed at the moment it would otherwise
be spent (the V6 ruling, now restated within-cycle).

Consequence: at the true prelaunch, the A1 presents the A7 verdict to the
owner through the Lead and requests a FRESH, exact-phrase GO; early-typed
GOs never authorize the first scored cell on their own. Any cycle closing
before prelaunch kills its standing GO unconsumed.

## Related program-level records

- Falsification-by-control cluster (7 instances, V11→V5):
  `HYPOTHESIS_LEDGER.md` §E.2.
- Economic observation "policy-carry present under honest availability,
  contract-invalidated" (PF 1.2825 / +20.72 per trade under corrected books;
  front-door re-entry open in a future preregistered plan): recorded in the
  V3R terminal artifacts and the hypothesis ledger at closeout.
- Cycle-level registers: stocks L1–L9, crypto L-V11-1..7 and L-V14-0
  (cost-kernel per-fill fix), forex per-cycle — remain the authoritative
  detail records.
