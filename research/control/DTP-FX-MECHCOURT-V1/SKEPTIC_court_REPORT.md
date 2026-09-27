# SKEPTIC COURT REPORT — DTP-FX-MECHCOURT-V1 — `SKEPTIC_court_REPORT.md`

- Cycle: `DTP-FX-MECHCOURT-V1` (parent DAYTRADE-PLAYBOOKS-PROGRAM-V1 / DTP-FX,
  under ECONOMIC-ROBUSTNESS-PROGRAM-V1; inherits ERP-FOREX-PROGRAM-V1 §2/§7,
  SRLV F-0/PIT law, PWS §2 identity / §5 frontier, unless child is stricter).
- Lane: `skeptic-court` (Lane S — economic-skeptic; VETO power pre-PnL).
- Outcome-blind by construction: this cycle computes no PnL anywhere; this
  artifact computes and reads NO price-drift, premium, return or PnL
  statistic. Adjudication is on TEXTS and failure memory only.
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/dtp-fx-mechcourt-v1/integration`,
  branch `orca/dtp-fx-mechcourt-v1-integration`.
- `actual_start_sha`: root `main` measured at lane start =
  `051aaae002615a68a0ee1af0d50e97325c69a930` (`git -C /Users/hoangminhlong/my-quantitative rev-parse HEAD`).
  Worktree HEAD identical at lane start (verified `git rev-parse HEAD` in
  worktree). `commit_sha`: null — Lead commits.
- One-shot law acknowledged: each of the three frozen mechanisms (plan §2
  verbatim) is adjudicated exactly once below; any re-adjudication requires
  an owner amendment with a recorded reason.
- Diet disclosure (what I read / did not read): see §6 Honesty.

---

## 0. Verdict summary (priority order of plan §4: (a) F0 → (b) DATA → (c) COST → (d) FRONTIER)

| Mechanism | Working hypothesis (plan §4) | Court verdict | Veto / blocker exercised |
|---|---|---|---|
| **A — `DTPFX-A1`** month-end London fix rebalancing | (a) `F0_KILLED` vs FIXCERT, (d) fallback | **`F0_KILLED <VETO_VARIANT_SAME_FAMILY>`** — CONFIRMED | skeleton ≡ dead `TRACKA2-P4A-FIXCERT-01` law (re-gate/re-clock/rename); class 5 VIABILITY DEAD; Q-7 clock-book law armed |
| **B — `DTPFX-B1`** news → observed rate repricing → FX lag | (b) `BLOCKED_DATA` | **`BLOCKED_DATA`** — CONFIRMED (F-0 skeleton NOT cleanly killed; recorded as heavy-adjacency, not a veto) | intraday rates leg = 0 bytes (OFR daily-only, RETRIEVAL_TIME_ONLY; CME `BLOCKED_TRANSPORT`); PIT ledger below evidence floor by its own labels |
| **C — `DTPFX-C1`** cross-venue synchronous quote discrepancy | (b) `BLOCKED_DATA` | **`BLOCKED_DATA`** — CONFIRMED (F-0 kill-risk recorded as secondary, not exercised as primary) | second venue = 0 bytes (IBKR 0 two-sided obs; Dukascopy `BLOCKED_TRANSPORT`; EDQ1 `BLOCKED_SOURCE_LICENSE`); two-leg cost authority = 0 components |

**Total-cycle consequence (for A1 verdict assembly, not mine to write):** all
three mechanisms blocked ⇒ the plan §4 terminal
`DTP_FX_V1_BLOCKED_DATA_OR_COST` is the lawful aggregate. GO phrase
`GO DTP FX MECHCOURT V1 SCORED EXECUTION` dies UNCONSUMED. No scored cell,
no holdout look, no rho computed (§5 defines, does not compute).

No disagreement with the plan's working hypotheses on outcome; two precision
refinements recorded in §4 (the events-ledger "minute-exact" count; the
C-adjacency annotation that the same-pair cross-venue law itself lacks a
measured death — which is exactly why (b) and not (a) is C's primary).

---

## 1. Mechanism A — `DTPFX-A1` month-end London fix rebalancing

### 1.1 (i) SKELETON TEST — strip the observable, compare to the dead law

**The dead comparison family, frozen:** `TRACKA2-P4A-FIXCERT-01`
(`FAMILY_FAILURES.jsonl` row 132): "London fixing-window certainty premium
(pre-fix z-gated drift into 16:00 fix)". Frozen decision law (SKEPTIC_F0
cohort-2 §2.6): ride the final pre-fix hour into the WM/Reuters 16:00 London
fix; gate |z| ≥ 1.0 on trailing-60-fix-day pressure; direction = pressure
sign; entry F−1h bar open; exit F bar open. Death: `DECLARED_BAND_BELOW_MEASURED_COST`
— frozen declared premium band arithmetically below the measured ×2.0-stressed
per-session book at the candidate's own fill hours on both pairs; "Fix-window
geometry is real but the harvestable band after taker costs is negative on
the Dukascopy paper book" (row 132 `measured_summary`). Reopening condition
verbatim: "owner amendment with a NEW economic basis (cheaper measured
execution or larger evidenced premium); parameter re-tunes are barred".

**The proposal's normalized skeleton (plan §2.1, frozen):** trigger =
calendar window before the 16:00 London fix on month-end (last trading) days;
direction = sign of a public quantity computed from price history
(month-to-date return / benchmark-weight rebalance estimate); exit = after
the fix. Declared payer: benchmark-tracking mandates transact at the fix and
pay spread + drift for deadline certainty.

**Strip test.** Remove A1's mechanism-specific observable (the month-to-date
public return / rebalance estimate) exactly as the cohort-2 court removed
FIXCERT's pressure z. What remains: **enter at F−1h on a pre-fix calendar
window, exit after the 16:00 London fix, direction = sign of a
price-history-derived quantity.** That is the FIXCERT decision law with the
direction variable renamed. Under the anti-variant law (DTP master §2.3;
owner laws 2026-09-26 "adding an observable is not a new mechanism" and
2026-09-27 "đổi pair/timeframe/session/filter không phải strategy mới"),
two proposals are ONE identity when they differ only by rename / gate /
clock while trigger-direction-exit shape and payer are the same. Applying
each axis explicitly:

- **Day subset = re-gate.** FIXCERT conditioned on ALL fix days (60-fix-day
  trailing window); A1 conditions on the month-end subset of fix days.
  Restricting a dead law's event set is the canonical re-gate — the same
  move the court killed as `VETO_VARIANT_SAME_FAMILY` in C1/C2/C3
  (`FAMILY_FAILURES` row 134; SKEPTIC_F0 §2.1–2.3: "gating a [dead law]
  … is a gating combination"; "the slot is CLOSED permanently to same-family
  replacement").
- **Month-to-date direction = rename of the pressure sign.** FIXCERT's
  direction variable was a trailing pressure z over fix days (a
  price-history sign); A1's is a month-to-date return (a price-history
  sign). Both are "sign of a public price-history quantity"; swapping which
  price-history statistic supplies the sign is a rename, not a new
  information layer. The F-0 information layer axis (plan §3.3: identity
  must differ ≥2/3 of payer / PIT information layer / risk shape) does not
  move: same layer (panel price history), same risk shape (one-session hold
  into the fix), same payer.
- **Payer claim — materially different?** No. Plan §2.1 itself declares the
  payer as benchmark mandates paying "spread + drift cho deadline certainty"
  — materially identical to FIXCERT's F-0-adjudicated payer ("fix-benchmarked
  mandates (passive funds, NAV-marked hedgers, corporates) paying spread +
  pre-fix adverse drift for deadline certainty", SKEPTIC_F0 §2.6). The word
  "rebalancing" adds a flow-story, not a payer set: the entities paying the
  spread/drift are the same fix-time benchmark executors in both texts. A
  wording difference is not a material payer difference.
- **Session/pair:** unchanged (16:00 London fix; any major). A pair or
  session change is explicitly a non-identity axis under §2.3.

**Also check the wider class law.** VIABILITY class 5 (fix-window / clock /
calendar geometry) is **DEAD** (`VIABILITY_cohort3_REPORT.md` row 5: FIXCERT
own frozen band below measured stressed book at own fill hours; FXFV1-A3-P2
late-NY; FXNG3/NG4 weekday-geometry collapses; Q-7). The weekday-geometry
collapses are measured, not asserted: `FXNG4-A4-P1` pooled |rho| 0.8883 vs
`generic_dow_tue`, `FXNG4-A4-P2` 0.8908, `FXNG4-A5-P1/P2` 0.8896 —
"calendar-publication conditioning = dead ancestry class" because books
conditioned on calendar days stack on weekday geometry (`FAMILY_FAILURES`
rows 92–95; FXNG3-A5-P2 0.8932 vs generic day-of-week, row 87). A month-end
day-set is calendar geometry of exactly this family; the court expects
`generic_dow`-class shadows to dominate it at F-1, and no measured
counter-evidence exists that month-end conditioning escapes weekday geometry
(the burden is on the proposal; Q-7). The Q-7 clock-book kill law
(RATESNG1-A5-P1-ARM-AGGRESSIVE row 100: clock-only shadow +94.16 out-earned
the gated book +72.42 — "the edge belonged to the auction-release calendar
geometry, not the declared mechanism"; COMMNG1 rows 107–109: bare
release-clock control out-earned every anchor) is armed against any
ungated-month-end-clock shadow on re-entry.

**Ruling (i): FAILS — remainder ≡ the dead FIXCERT decision law.** Month-end
day-subset + public month-to-date direction **is** a re-gate (day subset)
plus re-clock (month-end days only) of the FIXCERT skeleton, with the
direction variable renamed and the payer claim unchanged in substance.

**Note for the record (one honest nuance):** FIXCERT itself F-0-PASSED as a
mechanism class at cohort-2 (its skeleton was then novel) and died at the
F-5 band arithmetic. A1 is not rescued by that history — plan §3.1 class law
("Tái chạy skeleton/payer đã chết = F-0 kill ngay") and §3.4 ("dead class
trong FAMILY_FAILURES/VIABILITY census binds mọi proposal cùng skeleton")
bind every later proposal with the same skeleton to the death record. A1
arrives after the class closed; its F-0 verdict is therefore issued against
the dead FIXCERT family, not against FIXCERT's own F-0 adjudication.

### 1.2 (ii) PAYER TEST

Declared payer: benchmark-tracking mandates (passive funds, NAV-marked
hedgers, corporates) that MUST transact at the 16:00 fix and pay spread +
adverse drift for deadline certainty. This is the same payer the cohort-2
court accepted for FIXCERT — identifiable, structurally persistent, and not
self-arbitrageable in the naive sense (mandates cannot choose to trade
"earlier" because their benchmark IS the fix). The payer test therefore does
not fail on payer identity — it fails because **the payer was already
adjudicated into a dead family**: the same deadline-certainty premium, on
the same fix-window geometry, was frozen and killed
`DECLARED_BAND_BELOW_MEASURED_COST` on the measured Dukascopy taker book
(row 132). A same-payer re-gate inherits the dead family's kill. Month-end
fixes are the MOST contested fix windows (highest activity; Q-2: the spread
is priced off the volatility you want), so the harvestable band can only be
worse than the all-fix-day average that already died. Self-arbitrage note:
mandates cannot self-arbitrage, but dealers/execution algos that front-run
fix flow can — and they are the reason the band compresses toward the
measured book.

**Ruling (ii): payer distinct-in-name only; materially the FIXCERT payer,
already priced into a terminal kill.**

### 1.3 (iii) INFORMATION TEST (Q-7)

Q-7: what information is NOT already in clock/trend/spread? A1's information
claim reduces to **trend sign at a calendar clock**: month-to-date return
sign IS a continuation/momentum statistic (the dead class 2: "momentum /
continuation, any cadence" — FXFV1-A3-P1, FXFV7-A4-P1, TRACKA2-P3B-DINV-1D
ancestry 0.3032/0.3103; VIABILITY row 2), applied on a calendar gate (the
dead class 5 geometry, measured collapses rho 0.88–0.89). No component of
A1's direction signal is outside {trend, clock} — the two bins Q-7 says do
the work. The sham-calendar precedents close the escape hatch: FXFV5
(row 40) — the +7-day SHAM calendar OUT-earned the anchor; calendar
conditioning around events "carries NEGATIVE information vs generic
exposure"; FXFV7-A4-P1 (row 51) — +7d sham ≈ anchor, "the calendar
conditioning carries NO incremental information". A1 offers no measured
evidence that month-end calendar conditioning carries information above its
own sham-calendar shadow, and this cycle (outcome-blind, pre-PnL) produces
none. The information test FAILS: the observable decides only whether/when
to trade the old law's direction — the exact "adding a gate is not enough"
clause.

**Ruling (iii): FAILS — information ≡ trend sign × calendar clock, both
constituents measured-dead; sham-calendar burden unmet.**

### 1.4 VERDICT A

**`F0_KILLED <VETO_VARIANT_SAME_FAMILY>`** — CONFIRMS the plan §4 working
hypothesis (a). Margin-to-fail reasoning: three of the three F-0-identity
axes (payer / information layer / risk shape) fail to move versus the dead
FIXCERT family; the skeleton strip is byte-for-byte the same decision law;
the enclosing class (VIABILITY 5) is DEAD with measured geometry collapses;
and the FIXCERT kill record is terminal for the identity on this surface
("no re-tune legal", row 132 RC). Costs are NOT the binding reason (the
fix-window census G2 sharpens the owner packet but cannot rescue A — frozen
in plan §4); the kill is identity + class + frontier.

**What would change this verdict (owner action seeds — FIXCERT RC verbatim
path):** (1) owner amendment with a NEW economic basis: measured cheaper
execution at fix-window hours (R1 two-sided broker data with measured
all-in crossing materially below the class-5 death band at the F−1h→F fill
hours; note the IBKR tick floor alone already measured 0.5 pip ⇒ base
crossing ≥ 0.5 pip — `VERDICT_session2.md` V3), or a licensed second venue
(R2/EDQ1) with a measured cheaper book; OR (2) a larger EVIDENCED premium:
a PIT information layer with authority that is NOT panel price history
(e.g., licensed fix order-flow / benchmark-flow estimate) — which would
have to pass payer+information afresh at F-0; plus (3) an unexposed FX
surface for any premium measurement (USDCHF-class after data gate; sealed
2026-H1 AUDUSD/USDCAD is one-look lineage — must NOT be consumed by a
blocked mechanism). Parameter re-tunes (band, threshold, day-window width)
are barred by the FIXCERT RC and the no-rescue law.

---

## 2. Mechanism B — `DTPFX-B1` news → observed rate repricing → FX lag

### 2.1 (i) SKELETON TEST

Frozen skeleton (plan §2.2): event = economic release with real PIT
`available_at`; entry CONDITION = the rates-market reaction is ALREADY
OBSERVED (intraday rates series, same window as FX); direction = the rate
repricing sign; FX leg = M1 bid/ask. Explicit prohibition: substituting the
FX reaction for the rates leg is news-fade (dead class).

**Strip test.** Remove the observed-rates conditioning observable: the
remaining law is "enter FX around release events" with NO direction source
— a directionless release-clock book. That is precisely the shape the
cohort-2 court met at FIXCERT's F-0 (§2.6: strip z → "no direction remains
— the remainder is the directionless fix-window clock book, which is not
itself a dead DECISION law … but its geometry is the dead calendar/clock
class"), NOT the shape that produced an automatic same-family veto. No dead
family's decision law is "enter FX on an observed intraday rates reaction":
the 15 dead macro families conditioned on release direction / revision
sign / calendar position at daily cadence (FXFV5/6/7/9, FXNG1/3/4 —
VIABILITY row 7), and the two closest rate-conditioned kills collapsed into
**daily rate LEVEL** exposure (FXFV8-A5-P1: DGS10-level control out-earned
the anchor 4.01×, row 56; FXNG1-A4-P2: CTL-DGS10LEVEL +4.13 out-earned
anchor −6.63, "the DGS10-level shadow remains the most lethal control in
the forex program", row 83) — an exposure form, not an intraday-observed
reaction law. Therefore the skeleton test does NOT produce a clean
`F0_KILLED`: the first violation in the plan §4 priority order is not (a).
This is the honest reading and it is why B's primary verdict falls to (b),
as the Lead hypothesized. What IS recorded, binding on any re-entry: the
conditioning axis (rates-derived) is twice-measured to be dominated by rate
level and twice-measured to be dominated by release clock (RATESNG1-AGGRESSIVE
row 100; COMMNG1 rows 107–109), and the sham-calendar kills (FXFV5 row 40;
FXFV7-A4-P1 row 51) showed release-adjacent calendar conditioning carrying
no/ negative information. B enters any future F-0 carrying that adjacency
as named shadows.

### 2.2 (ii) PAYER TEST

Who pays? The implicit claim: FX market-makers/late repricers pay for a
moment after rates markets have repriced — i.e., the stale-FX side of a
cross-market lead. Two measured problems: (1) FXFV7-A6-P2 (row 52) measured
the cross-market lead content as carrying NEGATIVE information vs own-lag
continuation (own-lag control out-earned the anchor) in FX — the "lagging
side" has repeatedly been the wrong side; (2) RATESNG1/COMMNG1 measured the
profitable residue as release-clock geometry, not information — a payer
story that reduces to the clock is not a payer. No dead family had a
"rates-dealer pays FX-taker" payer that was adjudicated live; equally, no
NEW payer is identifiable in B's text beyond the generic stale-side story
that Q-4's delay law (three program deaths "information that evaporates one
bar later is market-maker compensation") prices as MM compensation.
Payer test: NOT cleanly failed at F-0 (the intraday cadence is genuinely
unmeasured in this program) — but carrying a measured kill-risk on every
precedent. Recorded, not exercised.

### 2.3 (iii) INFORMATION TEST (Q-7)

Does the observed-rate-reaction conditioning carry information beyond (a)
the DGS10-level exposure form that KILLED FXFV8-A5-P1 and FXNG1-A4-P2
(CONTROL_OUTEARNED_ANCHOR twice), and (b) the sham-calendar kills (FXFV5;
FXFV7-A4-P1)? Measured record: rate-derived conditioning has been
dominated by rate LEVEL twice (both deaths: the control out-earned, the
anchor's "mechanism" was the level in new words), and release-calendar
conditioning has been dominated by the sham calendar twice. B's claimed new
information — the intraday-observed reaction — has NEVER been measurable in
this program (no intraday rates bytes have ever existed here; §4.1 below),
so the information test is UNRESOLVED on measurement and HEAVY-ADJACENT on
memory. Under the missing-evidence law (L6: asserted ⇒ NOT_RUN; missing
evidence is NOT_RUN, never inferred PASS), the information test cannot
PASS. It also cannot honestly FAIL as an identity kill, because no dead
family consumed this layer. Q-7 verdict: unresolved-pending-data; the
burden sits with the proposal on any re-entry, with DGS10-level and
clock-only and sham-calendar shadows armed by law.

### 2.4 VERDICT B (primary): data/cost sufficiency per plan §4 — with citations to artifacts I READ

B requires, by its own frozen definition: (i) an intraday rates-market
series covering the release window; (ii) a PIT release ledger with real
`available_at`, consensus and revision vintages; (iii) the FX M1 bid/ask
leg (exists). Measured state of (i) and (ii) on the authorized plane:

**(i) Intraday rates series = 0 bytes.**
- The only rates acquisition in program history is
  `FREE-DATA-FRONTIER-V1R1` → `FREE_DATA_FRONTIER_V1R1_PASS_OFR_ACQUIRED`
  (`research/wayfinder/MAP.md` lines 487–505, read this session): 5
  preregistered reference-rate series, **daily rows** (SOFR 2,111 rows
  2018-04-02→2026-09-14; BGCR/TGCR same; EFFR/OBFR 2,648 rows from
  2016-03-01), and explicitly "**RETRIEVAL_TIME_ONLY/prospective (no
  per-row publication timestamps; 'current vintage'), NOT authorized for
  historical scored joins**". Daily bars cannot witness an intraday
  reaction before an intraday FX entry — and P-18 (same-day statistic law)
  independently bars conditioning an intraday decision on same-day
  aggregates.
- The natural intraday rates vehicle (CME ZQ/ZZT fed-funds/SOFR futures) is
  measured-unreachable: `FX-FUTURES-FRONTIER-V1` →
  `FX_FUTURES_FRONTIER_V1_BLOCKED_TRANSPORT` (MAP.md lines 1206–1230): the
  entire official CME estate SNI-keyed reset, "0 content bytes, zero
  circumvention"; reopening requires ONE owner action (a network path
  without the domain filters) from the FROZEN manifest.

**(ii) PIT release ledger is below the evidence floor — by its own labels
and by my measurement.** I read
`research/control/ERP1-TRACKA-COHORT-1/failres/failres_events_timeline.jsonl`
(exists; 132 lines = 1 header + 131 event rows — I parsed all 131) and
`failres/failres_events_PROVENANCE.json` (schema
`failres_events/provenance@1`). Honesty ceiling, measured by me this
session:
- Labels on header AND every row: `DIAGNOSTIC_OUTCOME_EXPOSED`,
  `FAILURE_ROOT_CAUSE_RESEARCH`,
  **`EVENTS_OVERLAY_ONLY_NOT_CAUSAL_EVIDENCE`** — the ledger itself
  declares it may not ground a causal (scored) mechanism. Purpose line:
  "OVERLAY ONLY. NOT_CAUSAL_EVIDENCE. No PnL, no price data touched."
- Timestamp authority: my parse of the 131 rows — `fetch_status`:
  **FETCHED = 10** (primary page retrieved and verified this cycle),
  NOT_FETCHED_CANONICAL = 84 (schedule-asserted canonical times),
  SEARCH_SURFACED_URL = 22, SEARCH_SURFACED_TOPIC = 12, wire/slug/
  corrected/timeout = 3. `time_precision` field: EXACT = 106,
  APPROX_MINUTES = 5, APPROX_HOURS = 20 — but "EXACT" there means
  "minute-level from source **or standing schedule**" (the PROVENANCE
  legend), i.e., schedule-asserted. The honest number for
  primary-page-verified timestamps is **10/131**. (Precision note: plan §4
  says "10/131 minute-exact"; measured, 106/131 carry
  `time_precision=EXACT` but only 10/131 are FETCHED-verified — the
  binding honesty ceiling is the FETCHED count under L6: asserted ⇒
  NOT_RUN.)
- Consensus / revisions: ABSENT by design — row
  `F1_US_CPI_20210113`: `"consensus null (not reconstructed)"`; no
  revision vintages anywhere in the 131 rows (I checked field set; the
  PROVENANCE per_event map carries url/timestamp_basis only).
- `available_time_utc` is present in all 131 rows but is
  schedule-derived (e.g., `F1_US_CPI_20210113.available_time_utc =
  2020-12-01T00:00:00Z` — the reference-month start, not a true
  availability stamp). Plan PIT law §3.6 requires "available_at THẬT từ
  nguồn có authority + xử lý revision; thiếu ⇒ BLOCKED_DATA, KHÔNG thay
  bằng proxy".

**Ruling:** the defining conditioning leg of B ("rate reaction ALREADY
OBSERVED") cannot be observed at entry time on the authorized plane — 0
intraday bytes — and the release ledger that would date the events is
barred from causal use by its own labels and fails the PIT floor (10/131
verified; no consensus; no revisions; schedule-derived availability). Any
substitute would be a proxy, which PIT law forbids.

**VERDICT B: `BLOCKED_DATA`** — CONFIRMS the plan §4 working hypothesis (b).
Margin-to-fail: this is not a near-miss — the required series has zero
bytes on every authorized path, and both unblock paths (CME network +
license; PIT feed with vintages) are named owner actions. Secondary
recorded: adjacency to 15 dead macro families, the twice-fatal DGS10-level
shadow, the sham-calendar kills, taxonomy row 8 ("DEAD + DATA-GATED") —
data would open MEASUREMENT, not edge (plan §7.5 honest-expectation law).

**What would change this verdict:** (1) owner network unblock of the CME
estate + data license, or a broker-grade intraday rates source, so the
rates reaction is observable pre-entry (R5-class information-layer
reopener with authority); (2) a PIT release feed with true `available_at` +
consensus + revision vintages (ALFRED keyless for US; official non-US
calendars; licensed consensus source); (3) an unexposed FX dev surface for
the class (2026-H1 sealed window NOT consumable). Even with all three, the
mechanism enters F-0 adjacent to the measured-dead shapes above and must
carry them as named shadows.

---

## 3. Mechanism C — `DTPFX-C1` cross-venue synchronous quote discrepancy

### 3.1 (i) SKELETON TEST

Frozen skeleton (plan §2.3): two bid/ask feeds, SYNCHRONIZED (same clock
discipline, tick or better), from two independent venues; signal =
stale-quote discrepancy; execution = two taker legs, each filled per its
own venue's book. Explicit prohibition: one source's candles dressed as
arbitrage.

**Strip test.** Remove the stale-quote discrepancy: nothing remains — no
direction, no trigger; the two-leg book IS the discrepancy observable. So
the skeleton cannot degenerate to a dead decision law by stripping (the
same structural situation as FIXCERT/B). The nearest dead DECISION laws:
- `FXFV7-A6-P2` EURUSD lead-lag diffusion (row 52): cross-PAIR lead
  content carried NEGATIVE information vs own-pair continuation; own-lag
  control out-earned the anchor. Different object (two instruments, one
  venue) — a fenced adjacency, not an identical law.
- `TRACKA1-M2-XCONF` (row 129): cross-pair GATING on ancestry observables
  = `V4_BLEND` fence. Again cross-pair, not cross-venue.
- `DTPCX1-I002-LEAD-LAG-DIFFUSION` (row 138): cross-ASSET lead-lag at 1m —
  dead, and decisively for C: the lagging side was measured FICTIONAL
  ("SOL reprices WITHIN the signal minute, median 17.8–62.8 bps, while the
  next-minute capturable window is median −0.245..0.000 bps").
The same-pair CROSS-VENUE stale-quote law has **no measured death in this
program** — it has never been constructible here (every surfacing was
data-blocked). Honest skeleton ruling: no clean identity kill; the class
neighbors are all measured-dead and Q-4-fenced, but C's exact law is
unmeasured, not dead.

### 3.2 (ii) PAYER TEST

Who pays? The stale venue's quoted side — i.e., the venue whose quote lags
pays (adversely selects) whoever lifts it. Can they self-arbitrage away?
Yes — and that is the measured heart of the matter: stale quotes are
self-arbitraged by their own quoting bank in sub-second time. On ANY
bar-granularity plane (M1, the only authorized FX plane), the earliest
legal fill (PIT law: quote tradable AFTER the signal is known) is at
bar-open opposite quote — one full bar after the discrepancy existed. Q-4
(delay law, LESSONS.md Q-4): "information that evaporates one bar later is
market-maker compensation (three independent edges died exactly this way)";
`DTPCX1-I002` measured the same signature at 1m with power in hand
(315,579 events): in-signal-bar repricing 17.8–62.8 bps vs next-bar
capturable median ≤ 0 bps — the payer has repriced before any legal fill.
Additionally the two-taker-leg execution needs broker-grade books on both
venues: measured `BLOCKED_BROKER_COST_AUTHORITY` with ten components
unmeasured (`VERDICT_session2.md` V3 table) — an UNFUNDABLE-ARM exposure
exactly as VIABILITY class 10 vetoes ("sub-M1/maker/queue … 'assumed
maker/mid/low-spread numbers are NOT evidence'"). Payer test: FAILS as a
measured-precedent kill-risk (Q-4 ×4 including the CX measurement), though
again not as a clean identity kill of a same-pair cross-venue law.

### 3.3 (iii) INFORMATION TEST (Q-7)

What would a stale-quote discrepancy carry beyond the cross-pair lead-lag
class (FXFV7-A6-P2 dead, own-lag control out-earned) and the Q-4 delay law?
Measured record: cross-venue/cross-market lead content in FX carried
NEGATIVE information vs own continuation (row 52); every sub-minute edge
this program ever measured evaporated at delay-1 (Q-4, three FX-program
deaths + `DTPCX1-I002`); VIABILITY class 6 (cross-pair lead-lag /
diffusion) = DEAD + FENCED, class 10 (microstructure tape) =
UNCONSTRUCTIBLE/VETOED on M1. A discrepancy visible at the authorized
plane's resolution is by construction one bar stale — exactly Q-4's
artifact signature. Information test: no surviving information claim is
identifiable on this plane; the only plane on which the claim could be
fresh (synchronous tick two-venue) does not exist here (0 bytes, §3.4).
Like B: unresolved-by-measurement, fenced-by-measured-precedent — recorded,
not exercised as the primary.

### 3.4 VERDICT C (primary): data/cost sufficiency per plan §4 — citations to artifacts I READ

C requires, by its own frozen definition: (i) TWO synchronized two-sided
feeds, tick-or-better, two independent venues; (ii) both venues' books for
two-leg taker simulation; (iii) two-leg cost authority. Measured state:

- **Feed 1 (only):** Dukascopy M1 bid/ask — the single authorized source
  (`SINGLE_SOURCE_PANEL`; LESSON_TO_GATE_MATRIX exposure map: independent
  sources "0 bytes for tới owner unblock"). And even its own surface is
  transport-blocked for re-download: `FOREX-INTRA-BIDASK-V1` →
  `FOREX_INTRA_BIDASK_V1_BLOCKED_TRANSPORT` (MAP.md lines 1172–1205): the
  official Dukascopy surface unreachable from this environment
  (resolver/SNI-keyed TLS resets; 36 connection failures; zero
  circumvention), B2 license gate UNAVAILABLE_FAIL_CLOSED downstream;
  reopening = owner network path, then lane A2 re-runs from the frozen
  manifest.
- **Feed 2 (venue two): 0 bytes on every recorded path.**
  - IBKR probe, session 2 measured (`broker_cost_probe_FX_majors_2026-09/VERDICT_session2.md`,
    read in full): V2 = **NOT_SUBSCRIBED (two-sided)** — "Full 360s × 5
    pairs streams (2 runs): **0 valid two-sided observations** (no
    forward-fill; honestly empty)"; BID/ASK = −1 (UNSET) on all five
    pairs; V3 = `BLOCKED_BROKER_COST_AUTHORITY` stands; minTick MEASURED
    0.5 pip all five pairs. Unblock = owner enables FX delayed/two-sided
    data or shares subscriptions, + Activity/Flex statements.
  - The licensed-source route is owner-gated:
    `EURUSD-DATA-QUALIFICATION-V1` → **`BLOCKED_SOURCE_LICENSE`**
    (`…/eurusd_data_qualification_v1/CYCLE_VERDICT.md`, read in full):
    every technical gate PASSED (578,916 two-sided ticks decoded) but "no
    terms document governs `datafeed.dukascopy.com`… an unresolved license
    cannot ground a research dataset"; Twelve Data clear for research but
    exposes NO bid/ask ("reconciliation-only", cannot be cost authority).
    Unblock = owner/legal decision (written Dukascopy consent / licensed
    vendor / OANDA v20 practice path), then the 7–14-day probe, then plan
    amendment + new GO.
- **Cost authority for two taker legs:** broker probe = 8/10 components
  NOT_RUN/NOT_SUBSCRIBED (`VERDICT_session2.md`); EDQ1 stage-2 cost
  authority (spread p50–p99 by session, stress tiers) = NOT_RUN, gated
  behind the license FAIL. VIABILITY class 10 result stands: two-leg
  book-level execution on vendor M1 is UNFUNDABLE-ARM VETOED.

**VERDICT C: `BLOCKED_DATA`** — CONFIRMS the plan §4 working hypothesis (b).
Margin-to-fail: not thin — the mechanism's defining input exists on exactly
zero of the recorded paths; all three unblock paths (R1 broker data, R2/EDQ1
licensed second venue, network unblock for Dukascopy re-download) are named
owner actions, and even the FIRST venue's renewal is transport-blocked.
Secondary recorded (binding on re-entry): class 6/10 fences + Q-4 +
`FXFV7-A6-P2` own-lag precedent + `DTPCX1-I002` fictional-lag measurement —
a future C must ship a genuinely new payer + information layer and a
delay-pair (delay-0/delay-1 + clairvoyant) battery as part of its DEFINITION
(Q-4: standard battery for sub-hour cadences, not optional robustness).

**What would change this verdict:** (1) one EDQ1 path cleared (TrueFX
free-reg + verbatim license capture, Dukascopy written consent, or OANDA
v20 practice + API terms) AND a second synchronized two-sided venue at tick
or better BOTH sides with clock discipline measured; (2) R1-class cost
authority for at least one executable venue (two legs must be costable);
(3) because Q-4/`DTPCX1-I002` measured the lag fictional at every executable
granularity so far, the re-entry design must pre-register the delay-pair
battery and expect an F-0 kill-risk against the fenced lead-lag class; data
opens measurement, not edge.

---

## 4. Data/cost sufficiency restatement (plan §4 duty) — precision notes and refinements

1. **B's evidence floor, exact numbers (measured by this lane, this
   session):** ledger exists at
   `research/control/ERP1-TRACKA-COHORT-1/failres/` —
   `failres_events_timeline.jsonl` = 1 header + 131 event rows;
   `failres_events_PROVENANCE.json` documents the method honestly
   (url_status legend; per-event basis map). Refinement of plan §4's
   "10/131 minute-exact": 10/131 are FETCHED/page-verified (the binding
   number); 106/131 carry schedule-asserted `EXACT` precision; 84/131 are
   NOT_FETCHED_CANONICAL. Consensus absent by design; revision vintages
   absent; `available_time_utc` schedule-derived; causal use barred by
   ledger's own labels. Rates: OFR daily-only,
   `RETRIEVAL_TIME_ONLY`/prospective, not authorized for historical scored
   joins (MAP.md 487–505); CME = `BLOCKED_TRANSPORT` with 0 content bytes
   (MAP.md 1206–1230). ⇒ `BLOCKED_DATA` is byte-determined, not a judgment
   call.
2. **C's evidence floor:** IBKR 0 two-sided observations + minTick 0.5 pip
   (`VERDICT_session2.md`); Dukascopy re-download `BLOCKED_TRANSPORT`
   (MAP.md 1172–1205); second-source license `BLOCKED_SOURCE_LICENSE`
   (EDQ1 CYCLE_VERDICT.md). ⇒ `BLOCKED_DATA`.
3. **A needs no data ruling:** its verdict is identity/class-level; the
   fix-window cost census (Lane D, G2) is a measurement for the owner
   packet only and is frozen by plan §4 as unable to rescue A. The
   applicable measured book for context (VIABILITY §A; SKEPTIC_F0 §2.6
   arithmetic): conditional crossing p50 0.9–1.2 pips; ×2.0-stressed RT
   3.6/4.4 pips AUDUSD/USDCAD; precedent-fragile line ≈ 2× stressed RT
   (~7–9 pips intraday); FIXCERT's declared gross band 1.0–3.0 bps
   AUDUSD was already below both the stressed and (upper) even the ×1.0
   book — and month-end fix hours are the expensive end of the
   distribution by Q-2.
4. **Frontier state (context, not the binding blocker for any of the
   three):** VIABILITY cohort-3 `NO_CANDIDATE` (0/12 classes); reopener
   R1/R2/R3/R5 = 0 new bytes since 2026-09-26; DTP GO-1 Q4 = FX DORMANT.
   Even if A's skeleton had NOT matched (the §4 fallback), (d)
   `BLOCKED_FRONTIER_NOT_REOPENED` would hold — moot, since it matched.

## 5. Ancestry representation (DEFINED, NOT COMPUTED — per P-12)

No rho was computed in this cycle (outcome-exposed surfaces would be
consumed and no verdict here needs it). If any mechanism ever re-opens, the
rho representation below is the pre-registered definition each re-entry
inherits (committed code + representation before execution; one-shot; gate:
pooled |rho| = worst named shadow ≤ 0.20 per pair, dev-masked
`ts ≤ 2025-12-31` on AUDUSD/USDCAD-class surfaces, EURUSD/GBPUSD/USDJPY
lineage ancestry/fixture/cost-authority only):

- **A:** target array ∈ {−1,0,+1} int8 over the full H1 (and M1-resampled
  fix-window variant) dev-masked grid; position = sign(month-to-date
  return) on last-trading-day-of-month, held F−1h bar open → F bar open.
  Named shadows: the FIXCERT pre-fix z-gated book rebuilt from its frozen
  def; `f_dow_simple` (FXNG4 collapse class); `f_h1tsmom` + `f_daymom`
  (MTD sign is momentum); `f_sessma`; FXFV1-A3-P1 session-continuation
  book. Expectation on record: `f_dow_simple`-class dominance (rho 0.88–0.89
  precedent) ⇒ dead at F-1 absent a genuinely new layer — which is the same
  as saying this representation exists to CONFIRM the F-0 kill, not to
  rescue it.
- **B:** target array on the FX M1 plane at event time (first tradable bar
  after rates-observation timestamp → horizon T). Named shadows:
  FXNG1-A5-P1 release-order book; FXFV6-A4-P1 k=5 release-direction book;
  FXFV7-A4-P1 spillover book; the +7d sham-calendar shadow; the DGS10-level
  exposure form rebuilt on the daily 16:00-NY grid per the FXFV8 AX2-C8
  control (P-12 lesson: frozen decision-grid representation, never a
  monthly grid); `f_dow_simple`.
- **C:** two-leg book indicator over the M1 grid (long venue-A / short
  venue-B where synchronized discrepancy > threshold at bar open) — plus,
  as part of the DEFINITION (Q-4 standard battery, not robustness): the
  delay-pair (delay-0 vs delay-1 next to a clairvoyant control through the
  same delay). Named shadows: FXFV7-A6-P2 lead-lag book;
  TRACKA1-M2-XCONF cross-pair gate; `DTPCX1-I002` decision grid.

## 6. Honesty disclosure

**READ (primary artifacts, this session):** plan
`PLAN_dtp_fx_mechcourt_v1.md` in full; `research/wayfinder/FAMILY_FAILURES.jsonl`
all 139 lines (131 pre-existing + 8 later rows; 38 forex rows counted across
the file, incl. TRACKA1/2, FXNG1/3/4, FIXCERT row 132, DTPCX1 rows 138–139);
`VIABILITY_cohort3_REPORT.md` in full; `SKEPTIC_F0_cohort2_REPORT.md` and
`SKEPTIC_F1_cohort2_REPORT.md` in full (P4-A FIXCERT frozen def, P3-A QCRD,
F-0 methodology, F-1 results); `LESSON_TO_GATE_MATRIX.md` in full;
`PLAYBOOK_TAXONOMY.md` in full; `LESSONS.md` Q-1..Q-16 and P-27/P-28/P-29
sections as cited; `MAP.md` sections: FREE-DATA-FRONTIER-V1R1 (lines
487–505), FOREX-INTRA-BIDASK-V1 (1172–1205), FX-FUTURES-FRONTIER-V1
(1206–1230), EURUSD-OPEN-SEARCH close note (370–391);
`broker_cost_probe_FX_majors_2026-09/VERDICT_session2.md` in full;
`…/eurusd_data_qualification_v1/CYCLE_VERDICT.md` in full (in the EDQ1
worktree, read-only);
`ERP1-TRACKA-COHORT-1/failres/failres_events_PROVENANCE.json` (full) and
`failres_events_timeline.jsonl` (header + programmatic parse of all 131
event rows; counts measured, not quoted from memory).

**NOT READ (and why):** any file under erp1-tracka-cohort-1 repro_twin
containing AUDUSD/USDCAD parquet rows — no parquet opened at all (sealed
2026-H1 and dev corpora untouched); any shadow journal, dashboard, broker
surface; any `trial_ledger.jsonl` or scored/terminal PnL artifact of any
cycle; cohort-1/2 `SCORED_REPORT.md`; `INTAKE.md` of this cycle (Lead's
artifact — all facts here are re-cited from primary sources I read
directly); Lane D's census (parallel lane; not mine and not needed for
these verdicts). No PnL, no price series, no rho, no premium, no drift was
computed or read anywhere in this lane.

**Known limitations of this adjudication:** (1) the skeleton tests are
textual identity rulings under the frozen anti-variant law; if the owner
amends a mechanism's text (new payer + new information layer), F-0 re-runs
fresh — nothing here forecloses an amended identity; (2) the events-ledger
counts are my parses of the committed bytes and are reproducible from the
same file; (3) C's "(b) not (a)" ruling rests on the honest observation
that the same-pair cross-venue law lacks a measured death — a future
re-entry with real two-venue data could convert the recorded kill-risk into
a measurement in either direction.

## 7. One-shot declaration

The three frozen mechanisms were adjudicated exactly once each, above, on
the measured base `051aaae002615a68a0ee1af0d50e97325c69a930`, before any
rho, before any PnL, with the sealed window untouched. Verdicts —
A `F0_KILLED <VETO_VARIANT_SAME_FAMILY>`, B `BLOCKED_DATA`, C
`BLOCKED_DATA` — are FINAL absent an owner amendment recording its reason.
This artifact plus `HANDOFF_S.json` satisfy the lane-S deliverables of
plan §5.

— Lane S (economic-skeptic court), `skeptic-court`, 2026-09-27.
