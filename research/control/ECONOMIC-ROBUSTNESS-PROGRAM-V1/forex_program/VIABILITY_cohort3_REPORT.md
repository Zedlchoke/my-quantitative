# VIABILITY COUNCIL — cohort-3 frontier adjudication (ERP-FOREX-PROGRAM-V1 §7)

**VERDICT: NO_CANDIDATE — cohort-3 has NO legitimate basis on the currently
authorized evidence space; the program must report NO_CANDIDATE (with the
specific reopening conditions in §C below), not open a cycle to keep the loop
turning.**

- Lane: FRONTIER VIABILITY COUNCIL (`viability-cohort3`), outcome-blind;
  read-only except this file and `plan_review/HANDOFF_viability_cohort3.json`.
- Measured base at start: root `main` @ `6b59b3c36fade77774b7528e8809a78f09699626`.
- Adjudicated: 2026-09-26. No PnL-bearing artifact read beyond what failure
  memory (`FAMILY_FAILURES.jsonl`, 134 entries, 38 forex) already discloses.
- Question: master plan `plans/PLAN_erp_forex_program_v1.md` §7 stop-conditions —
  two consecutive `REJECT_ALL` cohorts (COHORT-1: 12 scored cells, 0 survivors;
  COHORT-2: 7/7 mechanisms falsified pre-PnL, 0 cells) — does a third cohort
  clear the bar?

---

## A. Remaining mechanism space on the AUTHORIZED evidence space

**Authorized space (plan §2 + LESSON_TO_GATE_MATRIX exposure map, restated):**
Dukascopy M1 bid/ask only (`SINGLE_SOURCE_PANEL`); AUDUSD/USDCAD dev
2021-01..2025-12 for NEW observables; EURUSD/GBPUSD/USDJPY ancestry-only;
2026-H1 AUDUSD/USDCAD SEALED-UNREAD; USDCHF/unsearched pairs outcome-free but
gated (data gate + owner slate amendment); independent sources 0 bytes
(EDQ1 `BLOCKED_SOURCE_LICENSE`); execution = intraday-only taker book at
bar-open opposite-quote crossings (engine law `v2_lib.py:27-28`); no financing
band citable (FOREX-NG6/NG7 F4 → multi-day holds blocked); no broker costs
(DATA-EDGE-UNLOCK lane F `BLOCKED_BROKER_COST_AUTHORITY`, ten components
UNMEASURED, stress ×2.0 frozen); broker/exchange domains network-filtered
(L-FXFF-1); no new downloads without owner.

**Measured cost floor (binding, `COSTAUDIT_F5_cohort2_REPORT.md` +
`COSTAUDIT_cohort2_REPORT.md`):** conditional crossing p50 AUDUSD 0.9 (last-6m)
/ 1.0 (whole dev) pips, USDCAD 1.1/1.2; ×2.0-stressed RT 3.6 (AUDUSD) / 4.4
(USDCAD) pips ≈ 5.5/3.8 bps; rollover p50 2.0/2.3 (p99 12.3/16.7); Sunday open
4.6/6.8; commission/slippage-beyond-spread `DECLARED_UNMEASURED` (erosion-only).
The precedent-fragile line observed at P3-B: a declared band must clear ~2×
stressed RT (~7–9 pips intraday) to be non-fragile. Across all 38 forex
failure entries and the 12-family census, NO honest measured gross intraday
premium ever reached that line — the only large-band results in program
history (R-ORIG +3,207/+5,030 pips; GBPUSD +8,525) are PROVEN LEAK (P-18:
R-ORIG passes all 8 gates, R-ANCHOR PIT-clean dies G2/G3/G4 at PF 1.03–1.05;
evidence class `DIAGNOSTIC_PENDING_PIT_REBASE`). Q-1/Q-3 structural: skill is
found where the cost gates are shut; gates open where measured skill is
negative.

**Enumeration — 12 candidate family classes, each against the four tests
(i) dead-class law in FAMILY_FAILURES; (ii) measured cost floor; (iii)
unfundable-arm veto; (iv) exposure-map legality:**

| # | Class | (i) dead-class check | (ii) clears 3.6/4.4 pips stressed RT? | (iii) unfundable arm? | (iv) exposure-legal? | Result |
|---|---|---|---|---|---|---|
| 1 | Range-edge / prev-day-band fade + ANY gate (provenance, reclaim, probe-count, vol, session) | DEAD — `TRACKA1-M1-RANGEFADE-PIT` (KILL_PIT_SEAM class law), `TRACKA2-C1C2C3-REGATED-RANGEFADE` (`VARIANT_SAME_FAMILY`; owner law 2026-09-26: adding an observable is not a new mechanism) | No — declared bands 1.0–6 pips gross vs 3.6 stressed RT; C1 ceiling −2.1/−0.6 pips | taker arm is fundable but band underwater | dev surface legal but class vetoed | DEAD (class-closed vs gated variants; only a NEW payer + new information layer could carry a range-adjacent trigger — none exists on this space) |
| 2 | Momentum / continuation, any cadence (H1, day, session), any gate | DEAD — FXFV1-A3-P1, FXFV7-A4-P1, FXNG1-A5-P1, `TRACKA2-P3B-DINV-1D` (`ANCESTRY_RHO_BLOCK` 0.3032/0.3103; Q-3 re-clock = ancestry violation) | Only a >~7-pip-band variant could clear cost; every honest momentum measurement in program history is PF ≤1.35 gross and dies at ×1.5–2× | n/a | n/a | DEAD |
| 3 | Quote-state / spread-state GATES on any trigger | DEAD — `TRACKA1-M3-QSTATE` (F-5 cost ceiling), `TRACKA2-P3A-QCRD-H1` (F-0 pass, F-1 pass 0.079/0.088, F-5 `CEILING_NEGATIVE_VETO`: gate selects tight minute-median but executor charges hour-unconditional bar-open spread; Q-2) | No — needs ≤0.41-pip crossing, measured 0.9–1.0 | n/a | n/a | DEAD at current bands; re-entry only via P3-A's frozen reopening condition (§D) |
| 4 | Quote-layer observables as SIGNAL (bid/ask skew, spread level/migration) | DEAD — `TRACKA2-P4B-QSKEW-01` (band below even ×1.0 base book at own fill hours; vol-content control mandatory on any re-entry) | No — below base book, a fortiori below stressed | n/a | n/a | DEAD |
| 5 | Fix-window / clock / calendar geometry (fix certainty, session clocks, weekday, rollover-adjacent) | DEAD — `TRACKA2-P4A-FIXCERT-01` (own frozen band below measured stressed book at own fill hours); FXFV1-A3-P2 late-NY; FXNG3/NG4 weekday-geometry collapses; Q-7 clock-book kill law (RATESNG1/COMMNG1) | No — and the expensive buckets are exactly the clock events (rollover p99 12–17 pips, Sunday 6.8) | n/a | n/a | DEAD |
| 6 | Cross-pair lead-lag / diffusion / attribution gating | DEAD + FENCED — FXFV7-A6-P2 lead-lag; `TRACKA1-M2-XCONF` (`V4_BLEND`: cross-pair gating on ancestry observables) | n/a | n/a | ancestry fence explicit | DEAD |
| 7 | Event / macro observables (CPI, revisions, release order, spillover, PPP/real-rate, term-structure dispersion, policy-rate) | DEAD — FXFV5 (control out-earned), FXFV6 ×2 (PF below / expectancy), FXFV7 ×2, FXFV8 (control out-earned), FXFV9 ×4 (ancestry rho), FXNG1 ×2, FXNG3 ×4, FXNG4 ×4 — 15 entries; new macro feeds = new downloads (owner gate) adjacent to 15 dead families | Bands never covered stress in any measured instance | n/a | EURUSD-lineage exposure on most macro pairs | DEAD |
| 8 | Carry / financing-bearing multi-day holds | BLOCKED at gate — FOREX-NG6 `BLOCKED_SOURCE_OR_COST`, FOREX-NG7 F4: "a citable FINANCING band was hunted across the entire authorized evidence space and NONE exists"; prior carry family FXFV3-A5-P1 died STRESS_TIER_FAIL | Moot — holds >1 day cannot even be costed | financing leg unfundable on vendor data | blocked | BLOCKED (not constructible) |
| 9 | Volatility-state conditioning as direction source (vol regimes, dispersion, vol-of-vol) | DEAD — Q-7 (variance predictable, direction 0/96 twice), FXFV8 `CONTROL_OUTEARNED_ANCHOR`, FXFV3/FXFV4 STRESS_TIER_FAIL | No | options/IV arm unconstructible (no options data authorized) | n/a | DEAD |
| 10 | Microstructure quantity/tape (order flow, depth, trade signs, maker/queue, sub-M1) | UNCONSTRUCTIBLE — Dukascopy M1 bid/ask carries no volume/depth/tape; Q-4 delay-pair law: every sub-minute "edge" in this program's history evaporated at delay-1 (MM compensation) | No measurable band possible | UNFUNDABLE-ARM VETO (sub-M1/maker/queue; "assumed maker/mid/low-spread numbers are NOT evidence") | n/a | VETOED (not constructible + unfundable) |
| 11 | Mean-reversion oscillators (Bollinger/Stoch/hour-reversal) | DEAD/EXPOSED — FXOS-04 (`HOLDOUT_FAILURE_NO_RESCUE`, net negative after measured costs), STOCH/HOURREV are ancestry-exposed census families (F-1 shadows, rho 0.29) | No — Bollinger fade died precisely on the cost book | n/a | n/a | DEAD |
| 12 | New-pair transfer as a cohort basis (USDCHF / unsearched pairs) | Not a mechanism class — a surface. Transfer windows are consumption assets: an identity must first pass dev gates on a home pair (plan §4 R5(ii)); no identity exists | Moot | n/a | Legal ONLY with owner slate amendment + cohort-1 §5.2 data gate | NOT A BASIS (empty slate by construction — §7(a)'s literal definition) |

**Tally: 12 classes enumerated, 0 survive all four tests.** Every class that
could declare a band above the ~7-pip non-fragility line is dead on ancestry
or expectancy; every class declaring an honest small band is measured
underwater at the conditional taker book. The cost floor does not merely
trim candidates — it partitions the space exactly along the dead/surviving
boundary, with zero remainder.

---

## B. Surviving notions — F-0 three-tests pass TODAY?

**None.** Three borderline notions were stress-tested and honestly rejected:

1. **Per-fill `s_open` tightness residual** (the F-5 round-2 disclosed
   limitation: within-hour fill-minute spread state is UNMEASURABLE from
   counts-only histograms). This is a real unmeasured quantity — but it is
   not a mechanism: it is P3-A itself, closed with a frozen reopening
   condition requiring measured ALL-IN execution below 0.41 pips/crossing
   ("broker/venue cost authority or maker-fill evidence"). A vendor-data
   per-fill artifact could at most bound the spread component; it cannot
   produce ALL-IN evidence (commission = zero bytes), and the executor's
   bar-open charging law is frozen — rewriting it post-freeze would be an
   execution claim, not a strategy claim (Q-5/Q-8). **Not authorizable; not a
   cohort-3 candidate.**
2. **USDCHF replication-transfer surface.** Outcome-free and legal — and
   empty: R5(ii) requires an identity frozen on a home pair first; zero
   mechanism classes survive F-0, so a cohort opened for USDCHF would have a
   structurally empty slate (the literal §7(a) stop state) after consuming a
   data gate. New pairs change the surface, not the frontier. **Not a basis.**
3. **New macro/event observables** (e.g., central-bank path, positioning
   flows). Requires new downloads (owner gate) and would open adjacent to 15
   dead macro families with the same taker cost book; no named observable
   carries a NEW payer that the dead families lacked. **No constructible
   F-0 pass; any such proposal today would be dressing a dead class.**

## C. Verdict and §7 reconciliation

**NO_CANDIDATE** — the authorized space is measured-exhausted for viable
mechanisms. §7 reconciliation:

- (a) **MET**: no remaining hypothesis class passes D2 (Section A: 0/12)
  after two consecutive empty-slate cohorts. This is the literal stop text.
- (b) **PARTIAL**: Dukascopy M1 (five majors + AUDUSD/USDCAD dev) remains
  authorized — so the space is not authority-empty — but it is
  measured-exhausted; every NEW authority (independent source, broker cost,
  financing band, new pairs) is owner-blocked.
- (c) **NOT met**: the sealed map is not empty (2026-H1 AUDUSD/USDCAD still
  UNREAD). Therefore this NO_CANDIDATE is a *frontier* report, not a program
  terminal: the sealed window stays sealed (an arm that never existed never
  looks at holdout), and it becomes consumable exactly when a reopening below
  produces an identity that passes dev gates.
- (d)/(e) **Moot** — no candidates ⇒ no power/budget computation.

**Reopening conditions (owner actions that change the frontier; each is a
gate, not a wish):**

1. **Broker cost authority** (unlocks the P3-A class and converts every
   `DECLARED_UNMEASURED` into measurement): owner starts TWS/IB Gateway
   logged in (Read-Only API) ONCE; the preregistered FX-majors cost probe
   (templates verbatim from the paused xauusd probe) then measures
   contractDetails + one full Wed–Sun Activity/Flex statement for the five
   TD majors. DATA-EDGE-UNLOCK-V1 lane F deliverable; terminal label
   `BLOCKED_BROKER_COST_AUTHORITY__WAITING_COVERAGE`. Local gateway API
   sidesteps L-FXFF-1 (network filter on remote broker domains); still run
   the G0 reachability probe first (L11).
2. **EDQ1 source decision** (unblocks R5(iii) independent-source limb and a
   second cost book): pick one of the three recorded unblock paths —
   (i) TrueFX/Integral free registration + verbatim license capture;
   (ii) Dukascopy written consent for automated bi5 retrieval;
   (iii) OANDA v20 practice + API-terms read + M1 depth probe
   (runner-up: Polygon/Massive BBO). Any cleared path requires the successor
   7–14-day probe FIRST, then plan amendment + new GO.
3. **Citable financing band** (reopens multi-day/carry-horizon mechanisms,
   currently blocked by FOREX-NG6/NG7 F4 "no citable financing band exists
   on vendor data"): broker statement or venue-native financing source under
   owner authority. Without it, every hold >1 day is uncostable and
   fail-closed.
4. **USDCHF / new-pair slate amendment**: legal transfer surface, but only
   consumable AFTER an identity exists on a home pair — it amplifies a
   reopened frontier, it does not create one.
5. **Genuinely new evidenced information layer** (e.g., a PnL-free per-fill
   `s_open` artifact from an implementer round): sharpens the within-hour
   spread state but still cannot satisfy P3-A's ALL-IN condition without
   item 1 — record it as a prerequisite sub-deliverable of a reopened
   cohort, never as its own cycle.

## D. P3-A reopening condition — satisfiable by currently-authorizable evidence?

**CONFIRMED: NO — it cannot be satisfied without owner action.** Three
independent grounds:

1. **Arithmetic floor**: ALL-IN ≥ taker crossing ≥ fill-bar quoted spread.
   The measured conditional crossing at the gated book is 0.9–1.0 pips
   (even the conditional p25 is 0.8) against the frozen ≤0.41-pip threshold;
   the quoted spread is the floor of any taker execution on this data.
2. **Zero bytes**: the ALL-IN quantity includes commission and
   slippage-beyond-spread — ten cost components UNMEASURED (lane F census,
   zero account-bound bytes in the authorized space). Vendor bid/ask cannot
   produce them by construction; "assumed maker/mid/low-spread numbers are
   NOT evidence" (FAMILY_FAILURES `TRACKA2-P3A-QCRD-H1` reopening text).
3. **Frozen law**: the engine charges bar-open opposite-quote spread
   (`v2_lib.py:27-28`, frozen); re-deriving the 0.41 threshold or switching
   to intra-bar fill assumptions post-freeze is barred (no re-tune, Q-8) and
   would still lack the commission component.

The ONLY path is owner action: the lane-F IBKR Read-Only gateway probe
(reopening item 1), producing measured all-in execution against the frozen
0.41-pip number.

---

*Outcome-blind discipline held: no PnL-bearing artifact opened; no parameter
re-tune proposed for any dead candidate; no rescue attempted. Failure memory,
measured cost book and authority state are the only inputs. Không tạo cycle
chỉ để tiếp tục vòng lặp — cohort-3 does not clear the §7 bar today.*
