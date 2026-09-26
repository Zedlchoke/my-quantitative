# LANE C — COST/EXECUTION AUDITOR — COSTAUDIT_cohort2_REPORT.md

- Cycle: ERP1-TRACKA-COHORT-2 (child of ECONOMIC-ROBUSTNESS-PROGRAM-V1, Track A)
- Lane: tracka-cohort2-costaudit (council lane C — cost/execution auditor, BLOCKED power)
- Measured base at start: root `main` @ `3de439ab988d82cd246731ae6c277a688f6e2c31` (`git -C /Users/hoangminhlong/my-quantitative rev-parse HEAD`)
- Scope boundary honored: cost ceilings ONLY. No PnL, no strategy code, no outcome files read (no SCORED_REPORT, no series/, no trial ledgers, no MAP). READ-ONLY except this file and `HANDOFF_costaudit_cohort2.json`.
- Q-8 posture: every number below is measured from sha-pinned artifacts or quoted from a proposal's declared field; nothing is filled by optimistic assumption. Missing source would be recorded BLOCKED; none was (see §BLOCKED).

## Inputs and shas (all measurements pinned to these bytes)

| Input | Path | sha256 |
|---|---|---|
| Census AUDUSD (cost authority) | `.worktrees/erp1-tracka-cohort-1/integration/research/control/ERP1-TRACKA-COHORT-1/data_local/derived/census_AUDUSD.json` | `d337ff2c4e499238f6552c525cebf2027bbd5f2b876babc4e3e086fd09233473` |
| Census USDCAD (cost authority) | `.worktrees/erp1-tracka-cohort-1/integration/research/control/ERP1-TRACKA-COHORT-1/data_local/derived/census_USDCAD.json` | `27958f5a6b67ae017dea8bf35cf006868249926b03ff518ceb7663725ff35758` |
| H1 bars AUDUSD (break-hour conditioning source) | same dir `bars1h_AUDUSD.parquet` | `2a346e028f3867b892d3cfd0e1df33677fd5a6e2948ea93249e1406899a90344` |
| H1 bars USDCAD | same dir `bars1h_USDCAD.parquet` | `c2d9fdb641afbe2a842113a03fca30ba2aca6ca8cffa739bd7af52d564e126de` |
| C1 text | `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/PROPOSER1_cohort1_REPORT.md` (field 2: §1.1) | blind-lane artifact, no outcomes |
| C2/C3 texts | `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/PROPOSER2_cohort1_REPORT.md` (fields 2: §1.1, §1.2) | blind-lane artifact, no outcomes |
| F-5 law | `plans/PLAN_erp1_tracka_cohort_2.md` §6 and §8 (F-5) | child plan |

Both censuses: `schema=tracka_census@2`, `verdict=BUILD_PASS`, all five gates `true`, window `2021-01-03T22:00Z .. 2026-06-30T23:59Z`, 2007 day files each, pip = 0.0001 for BOTH pairs (`pair_config.pip`). Census m1 manifests pinned inside each census (`data_manifest.m1_manifest_sha256`: AUDUSD `f869cfa3…4e5396`, USDCAD `0f9a7df7…5b01db`).

**Units (binding for this whole report).** The executor book (child §6, inherited cohort-1 §6 verbatim) charges, per crossing, the fill bar's OWN measured spread = `a_open − b_open` (H1: verified `s_open == a_o − b_o`, max abs err 0.0 on both files; construction per cohort-1 cost-lane authority `HANDOFF_tracka1_datacost.json`, engine law v2_lib.py:27-28). All figures are in **pips** (1 pip = 0.0001 on both pairs). A **round trip (RT) = entry crossing + exit crossing** = sum of two per-crossing spreads. A single-bucket "spread" number below is **per crossing (per side), pips**; RT numbers are labeled RT. Stress multiplier k ∈ {1.0, 1.5, 2.0} applies to the measured spread at the fill bar (child §6).

---

## C1. Re-derived measured cost book (per pair)

### C1.1 Per-session-bucket median spread — base book (census authority, whole window, per crossing, pips)

Source: census `spread_pips.by_session_open.p50` (open-of-minute sampling; census `reconcile` block states the persisted method: "per-bar s_open/pip medians recomputed from persisted bars15 parquet, bucketed per session, vs census p50", max_abs_diff_pips 0.0, pass true).

| Session bucket (UTC) | AUDUSD p50 | AUDUSD p99 | USDCAD p50 | USDCAD p99 |
|---|---|---|---|---|
| asia_00_07 | 1.0 | 1.709 | 1.3 | 2.3 |
| london_07_12 | 1.0 | 1.6 | 1.2 | 2.1 |
| ny_overlap_12_16 | 1.0 | 2.4 | 1.2 | 3.4 |
| ny_late_16_21 | 1.0 | 1.8 | 1.2 | 2.3 |
| rollover_21_22 | 2.0 | 12.304 | 2.3 | 16.7 |
| late_22_24 | 1.3 | 6.5 | 1.7 | 10.8 |
| friday_20_23 | 1.1 | 8.744 | 1.3 | 5.736 |
| sunday_open_21_22 | 4.6 | 14.789 | 6.8 | 21.38 |

Family session (07:00–18:00 UTC = london + ny_overlap + first 2h of ny_late) mixture median ≈ **1.0 pip/crossing (AUDUSD)**, **1.2 pips/crossing (USDCAD)**. All session-bucket values are per side; RT base = 2 × crossing.

### C1.2 Break-hour bucket (conditional spread at break-style fill bars)

The census has NO break-conditioned bucket (verified: no break-keyed section exists; buckets are session-clock only). The F-5 law (child §8: "conditional spread tại break-style bars … 6 tháng gần nhất") therefore requires conditioning on the census-persisted H1 bars (same derived directory, shas above). Definition used — the family's own declared geometry, byte-consistent across all three candidate texts:

- Event bars: H1 bars starting 07:00–17:00 UTC (session 07:00–18:00), PDH/PDL = previous TRADED day's bid high/low over that day's traded bars (family `_prev_day_stats` convention; P2-A field 4 states it verbatim).
- **Live-break class (C1/C3 trigger)**: `b_c > PDH` or `b_c < PDL` (close beyond edge). **Reclaim class (C2 trigger)**: traded beyond (`b_h > PDH` or `b_l < PDL`) AND closed back inside. Union class = traded beyond regardless of close.
- Fill bar = NEXT H1 open (family fill law; fill-bar start hour ≤ 18, "no fills on/after the 19:00 bar").
- **Last-6-months window (Q-6 nearest)**: fill bar ts in `2026-01-01 .. 2026-06-30` (census `last_ts = 2026-06-30`; 154 traded days in window).

Measured fill-bar `s_open` distribution, per crossing, pips (conservative primary = p50 of the class-matched fill-bar spread; both RT crossings charged at this same conditional figure — stated assumption, because the exit bar hour is event-conditioned and unknowable pre-PnL; charging the exit at the conditional figure is the conservative side since force-flat lands ≤ 20:00 UTC, inside/near session medians):

| Class (fill-bar spread s_open) | AUDUSD p50 | AUDUSD p75/p90 | n fills 6m | USDCAD p50 | USDCAD p75/p90 | n fills 6m |
|---|---|---|---|---|---|---|
| Live-break (close-beyond) — C1/C3 class | **0.9** | 1.0 / 1.1 | 592 | **1.1** | 1.2 / 1.3 | 639 |
| Reclaim — C2 class | 0.9 | 1.0 / 1.1 | 142 | 1.0 | 1.15 / 1.2 | 175 |
| Union break-style | 0.9 | 1.0 / 1.1 | 734 | 1.1 | 1.2 / 1.3 | 814 |
| Session-all (unconditioned, same window) | 0.9 | 1.0 / 1.1 | 1393 | 1.1 | 1.2 / 1.3 | 1386 |
| Same classes, FULL window (reference) | 1.0 | — | 8843 | 1.2 | — | 8818 |

Observations (honest, both directions): (i) the last-6-months conditional break-hour p50 is marginally TIGHTER than the whole-window session medians (0.9 vs 1.0 AUDUSD; 1.1 vs 1.2 USDCAD) — break-style fills cluster in liquid hours, so no adverse bucket penalty is visible at p50; the p90 tail (1.1/1.3) is where conditioning shows. (ii) My full-window recomputation reconciles with the sha-pinned census (1.0 and 1.2 = census session p50), same construction the census itself used for its `reconcile` block.

### C1.3 Round-trip book and ×2.0 stress (pips per RT)

RT = entry crossing + exit crossing, both at the stated figure; stress = k × measured spread at fill bar, k = 2.0 per F-5 (k = 1.5 also reported).

| Book (LAST 6 MONTHS, Q-6 window) | base RT | ×1.5 RT | **×2.0 RT** |
|---|---|---|---|
| AUDUSD conditional break-hour (live-break class, 0.9 + 0.9) | 1.8 | 2.7 | **3.6** |
| AUDUSD session-mix (0.9 + 0.9) | 1.8 | 2.7 | **3.6** |
| USDCAD conditional break-hour (live-break class, 1.1 + 1.1) | 2.2 | 3.3 | **4.4** |
| USDCAD session-mix (1.1 + 1.1) | 2.2 | 3.3 | **4.4** |
| Census whole-window reference (AUDUSD 2×1.0; USDCAD 2×1.2) | 2.0 / 2.4 | 3.0 / 3.6 | 4.0 / 4.8 |

F-5 ruling input = the LAST-6-MONTHS conditional figures: **AUDUSD ×2.0-stressed conditional RT = 3.6 pips; USDCAD = 4.4 pips.** The whole-window census numbers (4.0/4.8) are shown only as the authority reconciliation; the Q-6 nearest window is what the law names, and it is also the TIGHTER book (using it is not optimistic — it lowers the stress cost and therefore favors the candidate).

---

## C2. F-5 declared-band ceiling arithmetic (three range-family candidates)

Law (child plan §8 F-5, verbatim intent): declared premium band (proposal field 2) vs ×2.0-stressed per-session book measured from the census on the last 6 months, conditional spread at break-style bars; **negative ceiling ⇒ veto pre-PnL (VOL-NG1 precedent; M3 cohort-1 died by this exact law)**. Verdict rule applied per dispatch packet: veto iff the declared band (its upper bound) is below the stressed conditional RT cost ("band < stress cost"). All inputs cited file + key.

### C2.1 — C1 PROV-ABSORB (P1; home pair AUDUSD — P1 field 9)

- Declared band (PROPOSER1_cohort1_REPORT.md §1.1 field 2 "Premium bps/decision"): gross **1.0–3.0 pips per round trip** on majors; net hypothesis **0.5–1.5 pips/decision** at base book. P1 field 7 pre-registers the kill basis: "×2.0-stressed conditional break-hour round-trip cost ≥ 2.0 pips against the declared ≤1.5-pip net hypothesis band ⇒ ceiling negative ⇒ pre-PnL veto".
- Stressed conditional RT (AUDUSD, break-hour, last 6m): **3.6 pips**.
- Ceiling arithmetic:
  - Net-band basis (P1's own pre-registered basis): 1.5 − 3.6 = **−2.1 pips**
  - Gross-band basis: 3.0 − 3.6 = **−0.6 pips**
  - P1's own trigger: 3.6 ≥ 2.0 → fired.
  - Even the whole-window census book (4.0) and the ×1.5 stress (2.7) both exceed the 1.5 net band; the base ×1.0 RT (1.8) already exceeds the net band upper and the gross band lower (1.0 < 1.8).
- **Verdict C1: CEILING_NEGATIVE_VETO.** The band is under water at ×2.0 on EVERY declared reading (net and gross), and already marginal at ×1.0. Veto BEFORE any scoring — VOL-NG1 / M3 precedent class.

### C2.2 — C2 RECLAIM-ABSORB (P2-A; home pair AUDUSD — P2-A field 10)

- Declared band (PROPOSER2_cohort1_REPORT.md §1.1 field 2): **2–6 pips gross per round trip** (no separate net band declared).
- Stressed conditional RT (AUDUSD, reclaim-class fill bars, last 6m): 0.9 + 0.9 = 1.8 base → ×2.0 = **3.6 pips**.
- Ceiling arithmetic: at band upper: 6.0 − 3.6 = **+2.4 pips**; at band lower: 2.0 − 3.6 = **−1.6 pips**.
- **Verdict C2: CEILING_PASSED_DECLARED** (band upper 6.0 > stressed cost 3.6). Conditions recorded: the lower half of the declared band (2.0–3.6) is stressed-underwater; commission is `DECLARED_UNMEASURED` program-wide and can only erode the +2.4 margin (never netted in, per child §6); and the inherited stricter precedent reading (below) would fail this band. Necessary, not sufficient.

### C2.3 — C3 PROBE-DEPLETION GATE (P2-B; home pair USDCAD — P2-B field 10)

- Declared band (PROPOSER2_cohort1_REPORT.md §1.2 field 2): **2–6 pips gross per round trip** (same harvest geometry as P2-A).
- Stressed conditional RT (USDCAD, live-break class — P2-B field 7: "fills occur strictly on close-beyond bars (same bars as the family)", class-matched, last 6m): 1.1 + 1.1 = 2.2 base → ×2.0 = **4.4 pips**.
- Ceiling arithmetic: at band upper: 6.0 − 4.4 = **+1.6 pips**; at band lower: 2.0 − 4.4 = **−2.4 pips**.
- **Verdict C3: CEILING_PASSED_DECLARED** (band upper 6.0 > stressed cost 4.4), with the THINNEST margin of the three (+1.6 pips before the declared-unmeasured commission component; lower 2/3 of band stressed-underwater).

No BLOCKED in C2: both proposals declare field-2 bands; both censuses carry the session buckets; the break-hour bucket was derivable from census-persisted H1 bars (missing from the census aggregate itself — disclosed, not blocking, derivation documented above).

---

## C3. Context note (not a verdict) + generic common scale

**Skeptic F-0 precedence.** Per child §4 and §8, all three candidates (C1 PROV-ABSORB, C2 RECLAIM-ABSORB, C3 PROBE-DEPLETION GATE) still face F-0 mechanism-class adjudication by the skeptic BEFORE any rho fixture or PnL (ordering law F-0 → F-1 → F-2..F-7; F-0 is one-shot per candidate, owner law 2026-09-26). C2 additionally carries the binding cohort-1 cross-lane tension: the explorer self-vetoed the retest/second-probe and displaced-fade classes on ancestry FXFV2-A4-P2 — if the class dies at F-0, C2 dies at zero fixture cost. **The ceilings above are a NECESSARY, not SUFFICIENT, condition**; a passed ceiling confers no mechanism validity.

**Generic common scale** — hypothetical "one round trip per day-session on each pair" (no declared band exists for a generic; the scale IS the stressed book an open-call proposer's band must clear). Last-6-months session book (§C1.3), per RT, pips:

| Pair | base ×1.0 | ×1.5 | **×2.0 (F-5 stress)** | 2 × ×2.0 (stricter precedent line, see below) |
|---|---|---|---|---|
| AUDUSD | 1.8 | 2.7 | **3.6** | 7.2 |
| USDCAD | 2.2 | 3.3 | **4.4** | 8.8 |

Open-call comparability rule implied by the book: a proposer's declared gross band must at minimum exceed the ×2.0 figures (3.6 AUDUSD / 4.4 USDCAD) to produce a positive ceiling, and — under the inherited cohort-1 fill-quality precedent ("Arms whose gross premium per round trip does not clear ~2× the stressed round-trip spread of their session mix die at F-5 before scoring", `DATACOST_cohort1_REPORT.md` §7 item 4, inherited verbatim via child §6 conditions 1–5) — should clear ~2× that (≥ ~7.2 / ~8.8 pips) to survive the unmeasurable adverse-selection term at break-edge fills. **Flag for council adjudication:** under that stricter inherited precedent line, C2 (6.0) and C3 (6.0) would ALSO fail F-5; the child plan §8 operative one-liner ("band minus stressed cost negative ⇒ veto") is the dispatch's verdict rule and is what the verdicts above apply. The discrepancy is recorded, not resolved, by this lane — resolution belongs to council/owner (my lane reports ceilings and BLOCKED facts, not law amendments).

---

## C4. Standing unfundable-arm check (sub-M1 / maker / queue-geometry veto law)

**Law restated** (child §6 binding summary + inherited cohort-1 §6 conditions; child §4 C3 bullet): any arm whose execution or observable REQUIRES (i) sub-M1 sequencing/timing, (ii) maker/passive fills, or (iii) queue/depth geometry — information that does not exist in the M1 bid/ask bar corpus — is NOT costable in the paper-tier book and is VETOED pre-PnL (M3-era law). Companion wording bans: taker PAYS the spread; no "capture/earn the spread", no "fill at mid", no maker-capture or queue claims; `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` mandatory on every verdict.

**Candidate check (from observable definitions in the proposal texts only):**

| Candidate | Execution law (declared) | Observable source (declared) | Verdict |
|---|---|---|---|
| C1 PROV-ABSORB | H1 closed-bar decision, fill next H1 open at OPPOSITE quote, taker-only ("no maker/queue capacity is claimed", field 6); P1 self-veto #5 rejected quote-side attribution precisely because it would need data beyond closed M1 aggregates | Formation hour of prior-day H1 bars — closed prior-day bars only (field 4) | Law NOT triggered |
| C2 RECLAIM-ABSORB | Same family fill law, next H1 open opposite quote; "no depth claims (queue/depth evidence does not exist on M1)" (field 6) | H1 close-back-inside event on bid-series OHLC (field 4) | Law NOT triggered |
| C3 PROBE-DEPLETION GATE | Same family fill law (close-beyond trigger bars); gate = count of CLOSED M1-bar extreme touches strictly before the H1 close — "no sub-M1 event timing, no tick sequencing — M1 bars are the corpus" (field 4); child §4: "costable trên M1 bid/ask với H1 clock" | Closed M1 extremes + closed H1 closes (field 4) | Law NOT triggered (the probe counter consumes only closed M1 bars by decision time — M1-corpus costable) |

No candidate above requires the veto. This check is necessary-not-sufficient like everything else in this report.

---

## BLOCKED

None. All required inputs existed: field-2 bands declared in both proposer texts; both censuses `BUILD_PASS` with all gates true; the break-hour bucket derived from census-persisted H1 bars in the same sha-pinned directory.

## Known limitations (disclosed, per Q-8)

1. The census aggregate has no break-conditioned bucket; the conditional figures are this lane's recomputation on census-persisted `bars1h_*` parquet (shas above), using the family's own declared trigger geometry — documented and reproducible, but derived, not census-native.
2. Exit-side charging assumes both RT crossings at the conditional fill-bar figure (conservative; the true exit bar hour is event-conditioned and unknown pre-PnL).
3. The last-6-months window (2026-01..06) coincides with the sealed holdout; this lane measured ONLY persisted bid/ask spread columns and price geometry for conditioning — no outcome, PnL or scored surface was touched. This is the measurement the F-5 law itself mandates ("6 tháng gần nhất").
4. Commission/slippage-beyond-spread remain `DECLARED_UNMEASURED` program-wide; all ceilings are measured-spread-only and any unmeasured fee component only erodes them.
5. Single-vendor cost authority (Dukascopy) — inherited limitation; no independent bid/ask replication exists.
6. Event/fill counts (592/639 class-matched fill bars over 154 traded days) are distribution samples for the spread book, not population estimates; F-6 feasibility belongs to another lane.
7. The stricter "~2×" inherited precedent line vs the child §8 one-liner is flagged unresolved (§C3) — verdicts apply the dispatch's stated rule.
