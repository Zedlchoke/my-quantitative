# Program-level lessons register

> Maintained by the Lead Engineer. Distilled from cycle-level registers
> (stocks L1–L9, crypto L-V11-*, L-V14-0, forex per-cycle) into lessons that
> generalize across assets. Each entry: source incident → lesson →
> consequence (where it is encoded). Append-only; never rewrite history.
> 2026-09-11: Q-series added — external doctrine imported at owner direction
> from the QuantPulse dossier (§ "External lineage" at the end of this file).

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

## P-9 — Terminal reports quote cross-asset totals as of THEIR intake; the ledger is the only cross-asset authority

Source: the 2026-09-05/06 quad close (V4, V8, V14, V9 inside one day). V9's
terminal printed program totals 185/188 — measured at its intake, before the
sibling cycles published — while the true post-close totals were 197/200.
Each A1 measures foreign cycles only at its own intake; nothing re-syncs the
sum inside a running cycle.

Lesson: per-asset denominators in a terminal are authoritative (that A1 owns
them); the program-wide sum in any terminal is an intake-time snapshot that
goes stale the moment a sibling cycle publishes.

Consequence: cross-asset program totals are read ONLY from
`HYPOTHESIS_LEDGER.md` (Lead-maintained at every close); terminal-report
program sums are labeled as-of-intake. Encoded in the V15/V10 plan
templates.

## P-10 — The root checkout is a shared stage: never leave the index dirty across long operations

Source: Forex V5 closeout (2026-09-06). While the Lead ran long
verifications with 11 renames staged in the root index, the V5 A1 committed
its ledger/MAP sync in the same checkout — its commit swept the staged
renames along (recorded as INC-V5-1; 0 content change; a follow-up commit
4 minutes later restored the load-bearing files, final tree verified by a
full 912-test pass). Harmless by luck and transparency, not by design.

Lesson: two authorities can commit in the root checkout within minutes of
each other. Staged-but-uncommitted changes are a trap for the next
committer; `git commit` without pathspec publishes the whole index.

Consequence: in the root checkout, stage and commit ATOMICALLY (single
purpose, immediately); prefer committing by explicit pathspec
(`git commit -- <files>`); any agent finding foreign entries in its commit
records an incident the same way INC-V5-1 did.

## P-11 — A terminal can only price what the driver persisted: per-period series are a launch requirement, not a terminal wish

Source: two independent incidents. Forex V3R (2026-09-05): DSR/PBO
NOT_RUN fail-closed at terminal — "no per-period series in the program
ledger"; the statistic that prices multiple testing was unreachable on the
exact family that needed it most. Crypto V15 (2026-09-07): the same NOT_RUN
for the same reason (no per-period series committed), plus G6–G9 NOT_RUN
for absent per-symbol diagnostics, plus a reproduction spot-check dying to
an external tick-metadata loss mid-audit (fail-closed TECHABORT).

Lesson: reproduction certifies self-consistency (P-4) but cannot summon
data the runner never wrote. Every diagnostic the terminal will need —
per-period returns for DSR/PBO, per-symbol legs, margins per gate — must
be an output-contract item proven BEFORE launch, and the twin must be
smoke-tested to re-emit it.

Consequence: the diagnostic persistability gate (validate every mandatory
terminal diagnostic's output contract + frozen applicability for
conditionals + twin smoke; missing ⇒ BLOCKED_PRELAUNCH) is IMPLEMENTED and
TESTED on branch `orca/governance-family-pipeline` (commits a01d4a2 /
cffaeb9 / f31598d; 38 governance tests) per the owner's 2026-09-07
amended directive; adoption boundary crypto V16+, forex V7+, stocks V12+.
Cite: `research/wayfinder/FAMILY_PIPELINE.md` §8.1 and §11.

## Related program-level records

- Falsification-by-control cluster (13 instances, V11→V7; latest: forex V7
  sham reproduces spillover anchor #12, stocks V11 shuffled-chain reproduces
  cadence-latency alpha 1.2042x #13): `HYPOTHESIS_LEDGER.md` §E.2.
- P-11 first delivery (forex V7, 2026-09-07): DSR computed at terminal from
  the driver-persisted per-period series (N=39) — the diagnostic
  persistability gate turned a NOT_RUN class into a computed statistic on
  its first adopted forex cycle.
- Economic observation "policy-carry present under honest availability,
  contract-invalidated" (PF 1.2825 / +20.72 per trade under corrected books;
  front-door re-entry open in a future preregistered plan): recorded in the
  V3R terminal artifacts and the hypothesis ledger at closeout.
- Cycle-level registers: stocks L1–L9, crypto L-V11-1..7 and L-V14-0
  (cost-kernel per-fill fix), forex per-cycle — remain the authoritative
  detail records.

## P-12 — A measured PASS binds to the representation it was computed on

Source: Forex V9 prelaunch (2026-09-10). A7 fresh-context CRITICAL: the D2
novelty PASSes (0.1062/0.0580) had been measured on undisclosed monthly-grid
1917..2026 state maps — not the frozen daily 16:00-NY decision-grid books the
contract binds. Recomputed on the frozen representation: pooled |rho|
0.3034/0.3119 vs the forbidden V8 ancestor (bar 0.20) — all four proposals
dead, selection freeze invalid, cycle closed BLOCKED at 0 cells. The A1's own
measurement used the wrong representation and was irreproducible from
committed state.

Lesson: representation identity (grid, books, decision clock) is part of
measurement identity. A gate number computed on a different representation
than the one the frozen contract names is not a PASS — it is an unverified
number wearing a PASS label.

Consequence: D2/feasibility measurements must commit the code AND the
representation they ran on; A7 prelaunch recomputes every measured gate on the
frozen representation by default. Generalizes P-3 (control semantics) to
measurement semantics.

## P-13 — An inherited pin is a cross-cycle dependency; archive-then-delete is what made it survivable

Source: Stocks V13 (2026-09-10). V13's D2 builders consumed V9's panel/prices
and V10's observables through inherited hash pins. The owner-ordered worktree
cleanup deleted the sibling worktrees — correctly, archive-first: tarballs +
SHA256SUMS in ~/staging_backups. The A1 still hit 0B paths, blocked
fail-closed (constraint 2) and requested an owner decision; Option A
(restore-from-backup) recovered byte-exact bytes, pins held, P3 needed no
amendment, D2 proceeded to a 3-cell REJECT_ALL.

Lesson: a pin into another cycle's staging survives that cycle's TERMINAL —
cleanup of any pinned artifact must either migrate it into the inheriting
cycle or record the archive location where sibling cycles can resolve it.
Fail-closed blocking was correct; the missing piece was discovery (the A1
could not know the bytes were archived).

Consequence: hash-pin manifests now record the backup/archive location
(SHA256SUMS pattern) so the next inherited-pin consumer resolves drift without
owner adjudication.

## P-14 — Transport speed is an operator variable; data identity is not

Source: Stocks V13 SEC crawl (2026-09-09/10). The owner-ordered speed
experiment (adaptive pacing ladder + parallel workers within the 10 req/s SEC
policy) moved the Form-4 crawl from 0.44 to ~6.5-7 doc/s — ETA from ~9 days to
under one day — with the census contract untouched, byte cross-verification
against cached docs, and a zero-unexplained reconciliation at the finish
(345,150/345,152 with two named-reason docs).

Lesson: pacing, transport, and scheduling are operator-tunable at any time
WITHOUT preregistration because they do not touch score-affecting identity —
provided byte-identity is re-verified and the manifest re-pins identical
content. Identity changes (bytes, universe, window) are science decisions and
follow plan law.

Consequence: transport/pacing changes are pre-authorized operator class;
any change that alters pinned bytes is a new-science decision requiring a
preregistered amendment.

## P-15 — Smoke-namespace numbers may kill but never select — and only with disclosure

Source: Crypto V17 terminal (2026-09-10). The cycle closed at the prelaunch
gate with ZERO scored cells: all six families died pre-authorization by
frozen rules or measured gates (coverage, ancestry rho 0.5628/0.475/0.2439,
expectancy-nonpositive, control-out-earns-anchor). Two of those kills used
T2.0 books measured in the smoke (dry-run) namespace — disclosed as SMOKE
EXPOSURE, used strictly as selection-phase kill evidence, never counted in
any denominator, budget 0/6 intentionally unconsumed.

Lesson: an unscored evidence namespace (dry-run/smoke) may legitimately SEE
outcome-shaped numbers before authorization, but its evidentiary use is
one-directional: it can kill a family, never rescue or select one, and every
use must be disclosed at terminal. The cheapest correct close in program
history (a full six-family cycle at zero scored cost) came from exactly this
discipline.

Consequence: smoke-namespace kills are admissible selection-phase evidence
when disclosed; a smoke number may never appear on the selecting side of any
rubric; denominators never move without scored execution.

## P-16 — TERMINAL on the branch is not closed until the registry and root ledger say so

Source: The 2026-09-09/10 triple close (V8, V9, V13, V17). Cycles closed
cleanly on their branches with A7 confirmations, but the canonical registry
rows stayed ACTIVE_LIGHT and the root ledger stayed two closes behind until
the Lead sync — and one close (V8) briefly produced a duplicate ledger row
because the A1 and the Lead both synced in parallel (deduped same day).

Lesson: closeout has TWO halves — the branch-side terminal chain (A1) and the
control-plane landing (registry flip + root ledger/MAP/failure-registry, one
writer: the Lead). Until both land, the router misleads the next dispatch and
cross-asset denominators undercount.

Consequence: the Lead close-sync is a required checklist item of every
TERMINAL close (registry lifecycle + head + budget, ledger totals + row,
failure registry, MAP); A1s append on their own branches only. The sync
itself is verified (validator --verify + cycle doctor) before the commit.

## Related program-level records (2026-09-09..11 window)

- Falsification-by-control cluster: forex V8 DGS10-level control out-earns
  its anchor 4.0116x (cluster #14) — the owner-mandated control killed a
  whisper-positive anchor (PF 1.0531) exactly as designed; crypto V17's
  OICASCADE control-out-earns kill is the same doctrine on the selection
  side.
- P-8 reinforced twice: the owner typed the exact V9 GO phrase at P0; the A1
  refused the wrong-form phrase, recorded the exact one as standing intent,
  and the intent died unconsumed with the cycle's BLOCKED close.
- P-6 reinforced: V17's six families died by their OWN frozen rules (rule-4
  coverage, ancestry vetoes, falsification) — no threshold was argued,
  because none could be.
- P-11 delivered end-to-end: V8's DSR computed at terminal from persisted
  per-period series (N=42); V13/V17 DSR/PBO NOT_RUN fail-closed with zero
  scored trials — both correct under the contract.
- Secrets hygiene: a pre-factory .env (Binance key pair) was found committed
  in early git history and already published on origin; owner informed and
  accepted (repo private). Standing rule stands: keys are environment-only.

## P-17 — Two live Lead sessions will eventually race; mid-flight is not abandoned

Source: ZCODE-ORCHESTRATION-V3 close (2026-09-11). Dual-controller occurrence
#2: while a fresh session executed /lead-close (batteries mid-run, store
TERMINAL transitions at 03:03Z not yet committed), the original Lead session
measured "no new commits", read the close-out items as abandoned, and landed
its own registry/artifact writes at 03:04Z. Occurrence #1 (same day) was the
mirror: a fresh /lead-start session detected the original's writes and halted
cleanly. Damage across both: zero — CAS/single-writer semantics absorbed every
collision, both closes independently reached the identical verdict on all
eleven gates.

Lesson: the recurring root cause is TWO live sessions holding the same
authority, and the trigger is interpreting a measurement gap as abandonment —
a session mid-turn shows exactly the "incomplete and silent" signature of a
parked one. Machinery (CAS, single-writer transitions, convergent gates)
absorbs the writes; it cannot absorb two reasoners diverging on judgment.

Consequence: one live Lead session per cycle is the real guard (close the
other window); before writing to a surface another authority may own, a Lead
must first rule out "in flight" (activity check or one waiting cycle), and a
completed close supersedes nothing silently — both closes here are retained
as convergent evidence.

## External lineage — QuantPulse dossier (imported 2026-09-11)

Imported at owner direction from the QuantPulse retrospective (12-day solo
programme, ten research programmes, every cell closed by a pre-registered
verdict, zero tradable edges) —
https://www.informationism.org/artifacts/quantpulse-dossier.html, rev 4 Sep
2026. Source preserved in-repo:
`research/wayfinder/external/quantpulse_dossier.html`
(sha256 `014a9aec42aa79570fffb5006a234896cd7c2a84d39b10177ff00261760c50f4`)
plus an extracted-text copy. Q-entries are external doctrine, numbered apart
from program-internal P-entries; where a Q-lesson already binds in our
machinery the cross-reference is given. Both series are binding.

## Q-1 — Skill is found; the market keeps it

Source: dossier §0/§3 Law 1. Four real, null-beating signals, each dying a
different measured death: timing skill costing 2–4× its own value to
collect; an hourly signal whose value lived in the un-executable first bar; a
lead-lag edge with the largest per-bar margin ever measured there, killed by
one bar of delay; an in-window survivor that failed to generalize on the
spent holdout. The failure mode was never "no signal" — it was the bill, the
clock, or the calendar.

Binds here: a near-miss positive is decomposed into bill / clock / calendar
BEFORE any successor plan is written (which of the three killed it names the
next question); feasibility arithmetic before selection (handbook §14.4) is
the same doctrine bought earlier.

## Q-2 — The spread is priced off the volatility you want

Source: Law 2. At the open, per-minute movement ran 3.33× midday and the
measured spread 3.35× midday — they cancel to two decimals; a maker quoting
volatile minutes charges for the variance the strategy wants to harvest.
Extended: any per-share commission is a tax on low prices, and any
volatility-seeking signal drifts into exactly the cheap, volatile names
where per-unit costs bite.

Binds here: cost models are conditional (time-of-day, price level, name
liquidity), never flat constants; a cost tier that does not condition on the
signal's own trading distribution is an accounting gap, not a conservative
choice.

## Q-3 — Skill and feasibility anti-correlate across horizons

Source: Law 3. Significant skill at 1m/5m where cost gates are shut; gates
open at 15m+ where measured skill is negative. Categorical, and it survived
every correction of the cost model.

Binds here: cadence is part of family identity (frozen clock contract); a
cost-gate failure at one cadence is NOT evidence about another, and a
cross-horizon rescue of a dead family is an ancestry veto (§12.3 equivalent
here).

## Q-4 — The delay signature is the artifact detector

Source: Law 4. Every minute-scale "edge" must be quoted at delay-0 AND
delay-1 next to a clairvoyant control run through the same delay; information
that evaporates one bar later is market-maker compensation (three independent
edges died exactly this way).

Binds here: our PIT mutation tests (§11.7) are the same instrument at event
granularity; for any sub-hour cadence family, the delay pair + clairvoyant
control is standard battery, not optional robustness.

## Q-5 — With no edge, the optimizer stops trading; grade on WORST

Source: Law 6. Seven of eight evolution champions pinned position size to
the floor — smallest-allowed is optimal when expected value is negative. The
one that sized up had its entire "edge" living inside the fill assumption
(+$20k optimistic, −$118k worst across 117 fresh windows).

Binds here: size-collapse under search is INFORMATION (report it, do not
"fix" it); optimistic-fill profit is an execution claim, never a strategy
claim; grading always on the worst fill is our stress-tier doctrine stated
independently.

## Q-6 — The ceiling is small, and it decays twice

Source: Law 7. Perfect-foresight ceilings decay as 1/√H in horizon AND in
calendar time as the tape matures (crypto compressed ~5× since 2018).

Binds here: feasibility gates measure the RECENT window's ceiling, never the
full-archive average; judging an idea against a stale ceiling understates
the bar by exactly the amount the tape has matured.

## Q-7 — Variance is predictable, direction is not — and the clock did the work

Source: Law 8 + its correction. Event-conditioned variance ladders were
real; direction at the same moments scored 0/96 twice. And after
decomposition, most "event" variance was the CLOCK: 91.7% of 8-K windows
open at the 09:30 bar; clock-adjusted, a plain 8-K adds only 1.05× (earnings
8-K 1.74×) against the 2.53× originally credited.

Binds here: every event-conditioning proposal carries a clock-only shadow
control; the event gets credit only for what remains above the clock (the
exposure-form shadow discipline, same shape).

## Q-8 — Measured beats stated, every single time

Source: Law 9. Every constant the programme ever measured was wrong as
stated: FX spread 0.3→1.05 bp (with a rounding bug zeroing 7 of 12 pairs),
perp spread 23× too wide, impact cap 40× too high, a 21,000× fee error.
"The most dangerous number in a backtest is the one nobody ever measured."

Binds here: this is our data-authority doctrine (§11) and P-7 channel
canaries stated from the cost side; every cost/coverage/spread constant
carries a measured source or dies conservative — a vendor-stated number is
a hypothesis, not a constant.

## Q-9 — Seal the criteria, not just the data: half a seal protects nothing

Source: §4 seal ceremony. SHA-256 over every holdout file AND over the
criteria file; reseals append to a superseded-seals ledger; a spent holdout
is published as-is, failure included; deviations are disclosed as the
exception that makes the rule checkable (their FX window read three times,
the third explicitly labeled "not a reopening").

Binds here: S1 + our freeze chain (BASE→WAVE→SELECTION→CODE_FREEZE→DATA→
AUDIT→TERMINAL) is the same ceremony; gates frozen before proposals exist
(P-6) is "seal the criteria"; our deviation class is the incident register.

## Q-10 — A closed door states its reopening condition once

Source: §2 closed-doors registry. "Re-litigating one by accident is the
failure mode this table exists to prevent" — every closure names the
instrument that closed it and the only condition that reopens it.

Binds here: FAMILY_FAILURES + forbidden ancestry ARE our closed-doors
registry; adopting their practice — state the reopening condition at close,
so the next blind-proposal packet forbids by condition, not just by name.

## Q-11 — A permutation is only a null if it moves the signal

Source: §4 dependence-preserving-nulls gap. A block or index permutation
applied to a slow signal barely moves it, so the null KEEPS the effect and
scores above the real result (their week-block nulls: 0.0504 / 0.1207
against real 0.0328 / 0.0319 — the null out-scored the signal twice).

Binds here: extends P-3 — a control's validity is itself measured before it
can kill: check autocorrelation at whatever the control permutes/conditions;
a control that reproduces the anchor is not always a mechanism kill, it may
be an INVALID NULL (distinguish explicitly in the verdict).

## Q-12 — A conservative bar can read real structure as zero

Source: §4 gaps note. An overnight sweep's "0 survivors" was partly a
bar-calibration outcome: the bar demanded r ≥ 0.31 per-year where the real
structure lives at 0.05–0.27 (with 0 on the null).

Binds here: thresholds are set against measured effect-scale evidence
(neighbour families, shadows, literature) and the bar's exclusion zone is
logged in the plan; "nothing passed" must always be quotable with the bar's
height attached (the margin-to-fail discipline, P-2, applied to the gate
itself).

## Q-13 — Long-running collectors need an inode check and a loud payload failure

Source: §6 standing-state note. A 7-day poller kept "running" while writing
into an orphaned inode (its log file had been replaced under it; ~1,400
observations lost), and its fetch loop silently discarded every non-list
JSON payload — a lapsed plan or error payload looked exactly like "no news
today".

Binds here: every daemon/crawler (V13-class substrate crawls, pollers)
checks its append handle against the path's inode and fails LOUD on
unexpected payload shape; "quiet" is never accepted as "healthy" — heartbeat
must carry bytes-written and payload-shape counters.

## Q-14 — Gross and net must pair on the same vehicle; equivalence baselines go stale silently

Source: §2 slow-programme record + §6 entry 6. One apparent survivor died
when its overnight-only gross was found paired with costs netted across
rebalances — on the registered vehicle every consistent accounting nets
negative. Separately: a bit-identical evaluator snapshot had silently
diverged after a spread-semantics change, caught only by re-verification and
re-baselined with the reason recorded.

Binds here: dual-book/accounting identity is per-vehicle and per-rebalance-
boundary (our trial identity, §15); every equivalence/baseline fixture is
re-run when the semantics it encodes changes — a passing stale baseline is
a false PASS.

## Q-15 — Proxy arithmetic first; pay only to confirm

Source: §6 IF0/IF1. The free proxy predicted the paid tape to 2–4% — the
first time that programme paid for data and had the free answer hold.

Binds here: probe/canary before purchase is already law (P-7); add the
confirmation half — when paid data DOES arrive, cross-verify the proxy
against the paid bytes and record the agreement factor, so the next proxy's
credibility is measured, not assumed.

## Q-16 — The instrument is the asset

Source: §7. "A research instrument whose negative results are trustworthy —
which is the property that makes future positive results worth anything";
the methodology itself (seal ceremonies, capture-bar gates, peel
decompositions) was judged ahead of published practice and worth shipping
even with zero trading edges.

Binds here: this is our mission invariant discovered independently by a
stranger's programme — 242 recorded noes are not 242 failures; they are the
calibration that prices the first yes. Both programmes reached the same
conclusion from opposite coasts: the trustworthy negative is the product.

## P-18 — An authority ruling lives only where the machine reads it (FOREX-NG1, 2026-09-11)

**Source:** FOREX-NG1 A7 prelaunch arc (two REFUSED rounds before AUTHORIZED).

**Lesson:** A1 ruled the FX spot channel AUTHORIZED_INTERNAL_RESEARCH in the event
log — but the fail-closed gate `require_scored_authority` reads a committed JSON
block (`authority_status.scored_consumption`) and compares an exact string. A
ruling recorded anywhere else (event log, prose, top-level key, paraphrased value)
does not open the gate; worse, GO typed against an unopened gate auto-fails every
cell and burns the one-shot run. The same arc caught a second variant: flipping
the right concept at the WRONG KEY with the WRONG VALUE is indistinguishable from
not fixing it — only an execution probe from committed bytes proves the gate open.

**Consequence:** Authority decisions that must bind machine behavior are enforced
by editing the exact bytes the enforcing reader reads (exact key, exact enum),
committed BEFORE the dependent key (GO), and proven by executing the gate from a
detached tree. Prose rulings are disclosure, never enforcement. (Also: quote your
heredocs — an unquoted `EOF` let shell backtick-substitution corrupt three
control-plane files in one close; caught by assert + inspection, repaired in the
same commit window, disclosed here.)

## P-19 — Owner throughput directive: one more cycle when a generation yields <= 6 scored cells (2026-09-11)

**Source:** owner instruction verbatim: "nếu mà tổng scored cell không quá 6 cells(2
family) thì ghi chú lại lesson, ledger,... và làm lại thêm 1 cycle lại từ đầu nữa
nhé. Quyền GO vẫn thuộc về bạn."

**Lesson:** Standing directive — when a cycle generation ends with no more than 6
scored cells (<= 2 families), the factory records the lessons/ledger (done as part
of the two-half close) and immediately opens ONE more full cycle from scratch
(new plan, new registry row, preregistered negative outcomes, fresh D1/D2/E),
with the GO key standing-delegated to the Lead under the same two-key structure
(A7 first). ng1 measured exactly 6 cells / 2 families → FOREX-NG2 opens under
this directive.

**Consequence:** Cycle throughput is an owner-set dial, not a Lead inference;
the scientific gates do not loosen (D2 ancestry bar, R1-R6, no-rescue all stand).

## P-20 — A control that shares its state source with the arm is tautological, not a test (VOL-NG1, 2026-09-14)

**Source:** VOL-NG1 H1 arc — the index-only shadow proposed for the index-state
volatility family read the same index state as the arm, so control == arm by
construction; the degeneracy was refuted at terminal A7, not by the shadow
itself.

**Lesson:** A control drawn from the identical state variable as its arm can
never diverge from it — it is a mirror, not a measurement, and scoring it would
have manufactured a fake "distinct" verdict. The fix that survived audit: score
the control on a different instrument expression of the same state (a
hypothetical index-point book), and MEASURE books_distinct instead of assuming
it — `None` fail-closed when both books are empty, never an inferred PASS (the
NEIGH-PERSIST dry-run cell where the arm never leaves FLAT produced
distinct == None and carried fail-closed NOT_RUN into E, disclosed).

**Consequence:** Distinctness of control from arm is a structural check that is
knowable outcome-blind at S: it must be measurable from book geometry alone,
with an explicit fail-closed value when unmeasurable. A control whose state
source equals the arm's is rejected at D1 battery review — not discovered dead
at A7.

## P-21 — Preregistered cost ceilings kill novel families honestly (VOL-NG1, 2026-09-14)

**Source:** VOL-NG1 A4-P2 — novel at D2 (rho 0.091), dead at E: every arm <= 0
after the measured Q-16 path ladder + expense (expectancies -55.83 / -49.13 /
-54.64 USD/RT, PF 0.292-0.312); the preregistered family kill fired exactly as
frozen at D1.

**Lesson:** The worst-case round-trip cost ceiling measured at P2 (~2,200bps at
the worst legs: spread + expense + Q-16 path components, pinned pre-score in
the D1 feasibility citation) did its job before any money was risked — the
family died at the only gate that mattered, on frozen text. Realized all-in
costs (~345bps/RT) were irrelevant to the verdict because the Q-16 path ladder
dominated the book; the ceiling was conservative in the right direction.

**Consequence:** Novel families get a measured, preregistered cost ceiling at
P2 (not a guess at D1), and the E-stage kill law is written so the ceiling (or
its expectancy equivalence) fires mechanically. A cheap-to-trade appearance at
realized costs never rescues a family whose preregistered ceiling already
killed it — and no ceiling is ever re-derived after numbers exist (P-15).

## P-22 — Subagent pool exhaustion is an operational hazard with a designed recovery (new-assets generation, 2026-09-14)

**Source:** generation-closeout operations — 3 lanes died mid-generation on
[1310] (model pool exhaustion); the owner pinned a different model; a probe
lane verified the pin via runtime metadata BEFORE any re-dispatch.

**Lesson:** Lane death is an operational hazard with a designed recovery path,
not an ad-hoc scramble: (1) owner authority pins the replacement model;
(2) a probe lane verifies the pin from runtime metadata before real dispatches
trust it; (3) retries review the attempt-1 partials — kept, never erased — and
fix the latent defects they reveal (7 defects fixed in the vol retry alone).

**Consequence:** Every retry must (a) verify its runtime assumptions with a
cheap probe before spending lanes, (b) preserve and mine the dead attempt's
partials for defects, and (c) disclose the attempt history in the cycle
artifacts. Pool exhaustion costs throughput; skipping the probe or erasing
partials costs evidence.

## P-23 — Fail-closed Z rehearsals catch crash classes before scored money (COMMODITIES-NG1, 2026-09-14)

**Source:** commodities empty-booked-population TypeError — the bare release
clock booked one lifetime trade spanning a split-boundary; the split-boundary
law excluded it; the exclusion left an empty booked population and the kernel
reconcile crashed (Z FAIL).

**Lesson:** The Z rehearsal caught a whole crash CLASS, not a one-off bug: a
control can correctly book zero surviving trades, and "empty book" must be a
first-class verdict, not an exception. Z-R1 remediated by short-circuiting an
empty booked population to DECLARED NOT_EXECUTABLE rows with explicit
disclosures (6 rows: WEAT/IAU x 3 arms — no kernel book, no root
reconciliation, no outcome number defined or inferred); Z-R2 re-passed with
coordinate_match true and pass_row_parity, proving the remediation changed
only the empty-population path.

**Consequence:** Every degenerate-population class (empty book, zero pairs,
undefined share) gets an explicit fail-closed verdict row with a disclosure
string at Z time — before any scored cell exists. A crash in rehearsal is the
system succeeding; the same crash at E would have burned scored budget.

## P-24 — Falsification-by-control keeps compounding (new-assets generation, 2026-09-14)

**Source:** #16 RATES-NG1 AGGRESSIVE — the clock-shadow control out-earned the
arm +94.16 vs +72.42 (margin +21.74 over 386 aligned pairs): the edge belonged
to release-calendar geometry, not curve-shape. #17 COMMODITIES-NG1 — the
crowd-carry release-clock control out-earned every arm: positioning
information added nothing over the CoT release calendar.

**Lesson:** Controls are not a one-cycle tax; each kill localizes where the
money actually is, and the localization transfers. 3/4 commodities D1
proposals had already died by their own price-only shadows at D2 — the same
instrument, declared outcome-blind at D1, executed its falsification before
any kernel ran. The compounding is cumulative across families: a
release-calendar-geometry falsification in rates reappeared as the executioner
in commodities.

**Consequence:** Every D1 battery declares its killers before measurement, and
the verdicts feed the cross-family failure registry (FAMILY_FAILURES +
forbidden ancestry), so the next generation's proposals are forbidden by
condition, not surprised by control. A generation with 0 survivors and sharp,
pre-declared kills is a profitable generation of knowledge (Q-16).

New-assets generation tally (closed 2026-09-14): 3/3 REJECT_ALL
(RATES_NG1_REJECT_ALL / VOL_NG1_REJECT_ALL / COMMODITIES_NG1_REJECT_ALL),
12 cells scored, 0 survivors, program 257/260; every surviving-candidate path
was falsified by its own pre-declared controls, which is the system working.
