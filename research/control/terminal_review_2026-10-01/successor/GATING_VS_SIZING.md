# GATING vs SIZING — decomposition of the POLICY−B1 divergence (PC12A successor prep)

> **Hypothesis-generating only.** Analysis of EXISTING committed scored-test
> journals; no engine runs, no new scored computation beyond arithmetic on
> journal rows. The 8 test folds are exposed. Nothing here licenses a re-fit
> or a counterfactual policy claim; it characterizes WHERE the measured
> divergence came from, layer by layer, to inform successor slate design.

**Analyst task:** separate the GATING effect (participation blocked/deferred/
netted away) from the SIZE/NETTING/CAPS effect (same trades, different units)
in the POLICY−B1_ALWAYS_ON divergence, week by week, fold by fold, symbol by
symbol.

**Sources (read-only):**
`research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS/{POLICY,B1_ALWAYS_ON}/{journal.jsonl,metrics.json}`
(SCORED-TEST folds 0–7, window 2022-01-07→2025-12-26, tier ×1.0, pricing base).

**Provenance tags:** [M] = read directly from committed journal/metrics rows;
[derived] = arithmetic on journal rows under the conventions stated below;
[NR] = not reconstructable from committed evidence.

**Sign convention (every $ below):** divergence ΔW = POLICY net − B1 net.
Negative = POLICY worse. Components sum to ΔW exactly (residual $0.0000,
§V4). "Harm" totals reconciled to packet §2.1/§2.2: USDJPY −87,201.39,
EURUSD +1,714.26, GBPUSD +223.70, pooled −85,263.43.

---

## 1. Method (as executed, every step)

1. **Reconstruction.** Parsed both journals fully: NET_ORDER fills
   (cash_delta_usd, delta_units, units_after, ts_fill_utc, contributing_legs,
   order_kind), SWAP rows (swap_usd, ts_utc), and gate rows BLOCK / DEFER /
   NETTED_TO_ZERO (ts_decision_utc, leg_id, fold_id, blocked_reason_detail,
   eligibility_rule_id). Cash identity discovered and used:
   `cash_end = 100,000 + Σ fills_cash_delta − Σ swap_usd` — SWAP rows are
   positive-cost debits, already excluded from fill cash [derived, validated
   to ≤$0.000001 per segment]. Fold membership of every fill/swap was fixed
   by an exact cumulative-cash prefix scan against each
   `per_symbol_fold_records[f].cash_end − cash_start` [M] — this correctly
   handles inter-fold weekend gaps (force-flats dated after the fold-end
   Friday, e.g. 2022-07-03T21:04Z) that naive date-cuts misassign.
2. **Weekly grid.** Per symbol, the mark chain = that symbol's
   `friday_equity` series [M] with the fold-end point replaced by realized
   `cash_end` (the fold-edge force-flat realization lands in the boundary
   week). 208 weekly marks per symbol per arm → 624 symbol-weeks. Weekly net
   per arm = chain first difference [derived]. Events are bucketed into
   weeks `(prev_mark_date, mark_date]`; fold-edge weeks ("EDGE") extend to
   the fold's last journal event (includes weekend force-flats and the first
   boundary re-entries booked in that fold's cash chain).
3. **Cross-arm fill matching.** Fills grouped by exact `ts_fill_utc` per
   symbol-week per arm: same ts in both arms = **shared** (same-size if
   Δunits equal, else **sized**); ts only in B1 = **B1-only** (trades POLICY
   skipped); ts only in POLICY = **POLICY-only**.
4. **Weekly $ decomposition (exact identity).** With week-end mark P_end and
   week-start mark P_start (implied from the chain: P = (equity − cash)/units
   when units ≠ 0; cross-checked: both arms imply the SAME price at every
   anchor to 5 decimals [derived]); fallback last-fill mid when both arms
   flat — see §5):
   - **GATE_$** = −Σ over B1-only fills of (cash + Δu·P_end) — i.e. minus the
     marked PnL of the trades POLICY skipped (skipping a winner ⇒ negative).
   - **SIZE_$** = Σ over shared-ts fills of (cash_P − cash_B + (Δu_P − Δu_B)·P_end)
     — the direct effect of trading the same hours at different units.
   - **PONLY_$** = Σ over POLICY-only fills of (cash + Δu·P_end) — extra
     POLICY trades (netting/exposure management on its own path, boundary
     re-entries).
   - **CARRY_$** = (u_P,start − u_B,start)·(P_end − P_start) − (swap_P − swap_B)
     — week MTM + holding costs of the position divergence inherited from
     prior weeks.
   Sum ≡ ΔW identically (max residual $0.0000 over 624 weeks) [derived].
5. **Classification** (weeks with |ΔW| > $100 only): GATE = B1-only fills,
   no sized/ponly; SIZE = no B1-only fills but sized and/or POLICY-only
   fills; MIXED = both; CARRY_ONLY = no fill-structure difference at all.
   Gate rows were called "on trading legs" when the gated leg had a nonzero
   vote/contribution in a B1 fill that week [derived].
6. **Gate typing** from the rows themselves: E1_FLOOR (BLOCK,
   `eligibility_rule_id=E1`, detail "NOT_RUN_THIN FLAT"), L6_COST_GUARD
   (DEFER, "L6 cost guard: trailing 28d spend … ≥ cap 2836.97"), L4_TIE
   (NETTED_TO_ZERO, "L4 tie"). B1-only fills with no same-ts POLICY gate row
   were sub-typed by journal evidence: `pathdown_policy_sizing_netting`
   (POLICY emitted DECISION rows at that ts but no order — sizing/netting
   layer suppressed it), `pathdown_b1_netting_mgmt(vote0)` (B1 vote-0
   exposure-management fill), `pathdown_no_policy_decision` (no POLICY row).

### Validation (all gates passed before any decomposition was trusted)

- **V1 fold cash:** worst |Σ journal (fills − swaps) − (cash_end −
  cash_start)| over all 48 (arm × symbol × fold) segments = **$0.000001** [derived vs M].
- **V2 weekly nets:** Σ weekly nets per symbol/arm vs Σ metrics
  `net_pnl_usd`: worst diff **$0.000002** [derived vs M].
- **V3 known totals:** Σ ΔW = USDJPY −87,201.39, EURUSD +1,714.26, GBPUSD
  +223.70, pooled −85,263.43 — exact to the cent vs packet §2.1/§2.2 [derived vs M].
- **V4 component identity:** max weekly residual |ΔW − Σcomponents| =
  **$0.0000** [derived].
- **V5 mark consistency:** implied Friday marks identical across arms at
  every anchor where both hold units; equity−cash = $0.00 whenever flat [derived].
- Fold 0 reproduces the packet's finding: all 78 symbol-week components are
  exactly $0.00 — the arms are identical there [derived; packet §2.1 [M]].

---

## 2. Headline decomposition (pooled, all 624 symbol-weeks)

| component | definition | USDJPY | EURUSD | GBPUSD | POOLED |
|---|---|---:|---:|---:|---:|
| **GATE_$** | trades POLICY skipped (marked wk-end) | **−386,130.32** | +409.00 | +221.70 | **−385,499.62** |
| **SIZE_$** | same-ts trades, different units | **−7,580.27** | +273.72 | 0.00 | **−7,306.56** |
| **PONLY_$** | POLICY-only extra trades | +66,189.85 | −512.26 | 0.00 | +65,677.59 |
| **CARRY_$** | MTM+swap on inherited position divergence | +240,319.36 | +1,543.80 | +2.00 | +241,865.16 |
| **ΔW** | POLICY − B1 | **−87,201.39** | +1,714.26 | +223.70 | **−85,263.43** |

All rows [derived]; ΔW row reconciles to metrics/packet [M]. Percentages for
USDJPY (denominator = net harm −87,201.39, or gate harm −386,130.32 where
noted): GATE = 442.8% of net harm; CARRY offsets 62.3% of gate harm; PONLY
offsets 17.1%; SIZE = 2.0% of gate harm (8.7% of net harm).

**The direct same-trade sizing effect is measured-small. The direct gating
effect is 4.4× the net harm, and the net harm survives only because carried
position divergence and POLICY-only trades gave 79% of it back.**

## 3. GATE component split by gate TYPE (journal-typed, marked wk-end)

Pooled [derived]; row counts are journal censuses [M]:

| gate type (source rows) | USDJPY | EURUSD | GBPUSD | rows in P journal |
|---|---:|---:|---:|---:|
| **L6 cost guard** (DEFER ×331, all USDJPY) | **−352,959.21** | — | — | 331 |
| **E1 floor** (BLOCK ×343) | +16,773.81 | +286.23 | +221.70 | 343 |
| **L4 netting tie** (NETTED_TO_ZERO ×35) | **0.00** (no same-ts B1-only fills) | 0.00 | 0.00 | 35 |
| pathdown_policy_sizing_netting | −31,686.08 | 0.00 | 0.00 | n/a |
| pathdown_b1_netting_mgmt(vote0) | −18,258.83 | +88.42 | 0.00 | n/a |
| pathdown_no_policy_decision | 0.00 | +34.36 | 0.00 | n/a |
| **Σ GATE** | **−386,130.32** | +409.00 | +221.70 | |

- **L6 = 91.4% of USDJPY's direct gate harm** (−352,959.21 = 4.05× the net
  harm). Fold concentration: f1 −169,657, f2 −181,874 [derived]. Worst L6
  weeks: 2024-11-29 (−107,726), 2022-08-05 (−94,889), 2024-10-04 (−69,774).
- **E1 floor is net-positive overall** (+17,281.73 pooled): it blocked legs
  whose B1 fills lost at the margin in f5 (+108,761 in f5 alone, e.g. week
  2024-10-04 +107,710), but was harmful in f1/f2/f3/f4/f7 [derived].
- **L4 tie: measured $0** — a tie nets to zero in both arms, so it never
  creates a B1-only fill [derived]. Not a harm mechanism in this window.
- **E-degradation and W-rules: zero rows exist** in either journal (no such
  `eligibility_rule_id` or reason detail) — absence documented [M]; any
  contribution is [NR], evidence says none was booked.
- **SUPERMAJORITY_BLOCK exists only in the metrics histogram** (POLICY 659 vs
  B1 1,021 blocked_reason_histogram [M]) — no journal rows, so direct $
  attribution is [NR]. It is part of BOTH arms' sizing stack (more blocks in
  B1 because more legs survive eligibility). Closest measurable proxy:
  `pathdown_policy_sizing_netting` −31,686.08 [derived].

## 4. Per-fold decomposition (all symbols pooled)

| fold | ΔW | GATE_$ | SIZE_$ | PONLY_$ | CARRY_$ |
|---|---:|---:|---:|---:|---:|
| 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 1 | −83,402.98 | −130,016.47 | +71,381.23 | −67,047.27 | +42,279.53 |
| 2 | −208,827.50 | −158,791.86 | +75,748.79 | −105,578.96 | −20,205.47 |
| 3 | −3,099.98 | −13,955.20 | +283.33 | −62,188.96 | +72,760.85 |
| 4 | +111,528.13 | −27,161.04 | +4,911.83 | +29,056.17 | +104,721.17 |
| 5 | +174,192.41 | +21,905.92 | −98,708.83 | +313,053.89 | −62,058.57 |
| 6 | −79,259.31 | +12,120.48 | +23,809.47 | −48,186.17 | −67,003.08 |
| 7 | +3,605.80 | −89,601.45 | −84,732.37 | +6,568.89 | +171,370.72 |
| **Σ** | **−85,263.43** | **−385,499.62** | **−7,306.56** | **+65,677.59** | **+241,865.16** |

Per-symbol × fold tables: USDJPY carries essentially everything (e.g. f2
USDJPY ΔW −209,367.77 = gate −159,464.65 + size +75,902.68 + ponly
−105,418.13 + carry −20,387.67); EURUSD/GBPUSD rows are 3-digit [derived].
The harm folds (1, 2, 6) are all gate-dominated at the direct level; the
helper folds (4, 5) are ponly/carry-dominated.

## 5. Weekly classification census (624 symbol-weeks; 208 marks × 3 symbols)

| class (|ΔW|>$100 weeks) | n | ΣΔW | Σ\|ΔW\| | median anatomy |
|---|---:|---:|---:|---|
| GATE (only missing trades) | 20 | +11,652 | 98,508 | pure skip weeks net ≈ 0 |
| SIZE (no missing; sized/ponly only) | 88 | **+371,526** | 1,456,857 | sizing-path weeks net POSITIVE |
| MIXED (both) | 74 | **−460,224** | 1,707,693 | all the harm lives here |
| CARRY_ONLY (no fill-structure diff) | 24 | −8,817 | 75,536 | inherited divergence MTM |
| SMALL/MATCH (|ΔW|≤$100) | 418 | +600 | 4,514 | 354 fully identical |
| **total** | **624** | **−85,263** | **3,343,108** | |

206 of 624 symbol-weeks (33.0%) diverge beyond ±$100 [derived]. Inside MIXED
weeks the pooled components are gate −350,462 / ponly −37,091 / size +13,565
/ carry −86,236 [derived]. **Weeks whose only structural difference is
trade-sizing (SIZE class) netted +371,526 in POLICY's favor; weeks where
gate-skips interleaved with the size path (MIXED) carry the entire net
harm.**

Mark-source census: 210 weeks priced by B1-implied Friday mark, 123 by
POLICY-implied, 291 (46.6%) by last-fill-mid fallback (both arms flat at the
mark) [derived]. Component TOTALS are identity-exact regardless; the split
between (gate/size/ponly) and carry in fallback weeks moves with the
marking convention — bounded by |unmatched Δu| × |Friday-close − last fill|,
not computable exactly from the journals [NR].

## 6. Worked example — worst week (ties to packet §2.3(b))

USDJPY week ending 2024-11-08 (f5), ΔW = −114,124.85 [derived]:
- 14 B1 fills vs 9 POLICY fills; 9 shared ts (ALL sized differently), 5
  B1-only, 0 POLICY-only.
- GATE −54,204: 2 skips typed E1 (S002/S003 BLOCK rows at the exact fill
  ts), 3 skips path-downstream (B1 vote-0 exposure closes);
- SIZE −46,361 (same hours, different units — the packet's "positions
  differed in SIZE" is exactly this bucket);
- CARRY −13,559.
Cross-check vs packet §2.3: my gate component for week 2023-05-19 is
**+2,191 ≈ the packet's cited +2,190.70** B1 round trip that the L6 guard
deferred [derived vs M] — same event, same sign under the stated convention.

## 7. Fold-edge / force-flat effects

The 24 fold-EDGE weeks (force-flat realization + first boundary re-entries)
pool to **−105,525.42** (USDJPY −105,654.60; f6 EDGE −34,137.31 and f7 EDGE
−53,930.51 the worst) [derived]. n_force_flat 6 vs 11 and force-flat cost
$6,925.86 vs $7,114.83 (P vs B1) [M]. Fold-edge realization differences
alone are larger than the entire net harm — they are offset inside folds.

## 8. Limitations / honest [NR]

1. **Intra-week ordering:** GATE/SIZE/PONLY mark remnant units at the Friday
   mark; which intra-hour path produced the cash is not decomposable from
   journals. All SIZE weeks are therefore reported as one bucket
   (SIZE-unattributed inside the week) rather than guessing per-fill PnL
   ordering. [NR]
2. **CARRY origin:** CARRY_$ is downstream of whichever earlier event created
   the unit divergence; attributing it back to gate-vs-size origin requires
   lot-level (FIFO) counterfactual accounting not supported by the journals.
   [NR] — reported as its own line, never folded into GATE or SIZE.
3. **291 fallback-marked weeks** (§5): component split convention-sensitive,
   totals exact. [NR for the split]
4. **No counterfactual policies** were run; "B1's trades made $X" is
   realized-B1 evidence, not a claim that a different gate would have
   captured it. Packet §2.3's ban on counterfactual search stands.
5. B4_BATTERY's 128/128 duty-matched random eligibility patterns beating the
   frozen policy [M] is consistent with, but not quantified by, this
   decomposition.

## 9. Measured conclusions for the slate-designer

1. **The harm is a GATING phenomenon, not a caps phenomenon.** Direct
   same-trade unit-scaling (netting/caps on identical decision hours)
   measured **−$7.3k pooled (2% of USDJPY gate harm)**; direct skipped-trade
   harm measured **−$385.5k**. A successor slate should spend its design
   budget on the participation layer, not on re-scaling units of trades it
   already takes.
2. **The L6 cost guard is the single largest identified harm mechanism:**
   −$352,959 direct (91.4% of USDJPY gate harm; concentrated in folds 1–2:
   −$351.5k of it), consistent with the docket's independent +$274,572 on
   the 29 B1-filled guard defers [M: USDJPY_DOCKET §6]. The guard fires on
   realized trailing spend ($2,836.97 cap) and skips winners in trends.
3. **The E1 activity floor did not hurt on net** (+$17.3k pooled; strongly
   helpful in f5 +$108.8k): thin-leg participation blocks were roughly
   PnL-neutral-to-positive. E-degradation and W-rule gates never fired in
   the scored window [M: zero rows] — do not spend slate budget there.
4. **The L4 netting tie and the supermajority layer are not measurable
   harms:** L4 ties produced $0 divergence (ties net to zero in both arms);
   supermajority has no journal rows in either arm (histogram-only, P 659 vs
   B1 1,021 [M]) with a pathdown proxy of only −$31.7k [derived].
5. **Path persistence, not sizing, created the tail:** the carried position
   divergence returned +$240k and POLICY-only trades +$66k (together
   offsetting 79% of the gate harm), while fold-edge realization weeks alone
   diverged −$105.5k. Gate-skips matter mostly through the multi-week
   position paths they create — so the successor's gate layer should be
   evaluated on path outcomes (as here), not on per-decision skip counts.

— End of file. Scratch computations were run from committed journals only;
the only artifact written is this file.
