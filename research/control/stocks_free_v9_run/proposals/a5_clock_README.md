# V9 D1 — lane A5 (clock lane): two outcome-blind proposal packets

Cycle: STOCKS-FREE-V9 · Phase: D1 · Wave SHA: `86fecae8044d344e5d5ea9a49bbcfdb2f03c0b5a`
Branch: `orca/stocks-free-v9-d1-a5-clock` · Base/worktree HEAD at proposal time: `86fecae8044d344e5d5ea9a49bbcfdb2f03c0b5a`
Schema: `stocks_free_v9_run/d1_proposal@1` · Lane discipline: outcome-blind (no returns, no PnL exists in this cycle; none computed)

## Files

| File | Content |
|---|---|
| `a5_clock_H1.json` | SFV9-A5-H1 — filed-value **equity-stub thinness** (StockholdersEquity / EntityPublicFloat) |
| `a5_clock_H2.json` | SFV9-A5-H2 — **trade-credit chain position** (AccountsPayableCurrent / AccountsReceivableNetCurrent) |
| `a5_clock_README.md` | this file (design rationale + self-check record) |

## Design summary

Both packets are untested fundamentals mechanisms on the multi-vintage PIT panel
(`.staging_sec_v9/multivintage_panel.jsonl`, sha256 `67591464...`, 10,073,069
rows incl. 6,255,911 dead-filer rows), measured on the death-inclusive bookable
pool **ALIVE_EVIDENCED (410) + DEAD_PRICE_CONFIRMED (1550)** from
`cohort_v9.json`; GAP_COVERAGE (513) and the alive-name-guard/excluded legs are
never bookable.

**SFV9-A5-H1 equity-stub thinness** — anchor = filed book equity over filed
public float, long book-rich-over-float / short market-rich-over-book within
frozen SIC→SPDR sector; neighbour = book-cushion depth (Liabilities/SE,
required same-sign support); placebo control = par-stub
(CommonStockValue/EntityPublicFloat — same denominator, no going-concern
content, must NOT reproduce at ≥ 0.5x |alpha|). Mechanism reading: a
claim-shape channel whose terminal branch is censored by survivor panels and
only realized in this cohort. Distinct from the A4 distress axis: a single
filed-ratio shape conditioning, no hazard composite.

**SFV9-A5-H2 trade-credit asymmetry** — anchor = AP/AR, long supplier-financed
/ short customer-financed within sector; neighbour = AP share of
LiabilitiesCurrent (same-sign support); placebo control = Cash/AP run in the
declared weak-liquidity direction (kills the "generic settlement-liquidity
stress" alternative, must NOT reproduce at ≥ 0.5x |alpha|). No inventory leg
and no asset scaling anywhere in the family; the V8 F1 allowance-coverage
neighbour is explicitly NOT re-proposed (rejected-family arm form).

**Clocks.** Every cited clock tuple is quoted verbatim from
`p2_v9_coverage_first.json → dead_leg_funded_clocks.clocks` (56 entries; the
only citable set). All eight arm fields use the funded unbounded bound
(`latest filed vintage as of t (unbounded)`), chosen because it is the only
bound at 30/30 dates ≥ 0.6 coverage on the dead leg for these fields. H1:
StockholdersEquity 0.8823/1730, EntityPublicFloat 0.8622/1727,
CommonStockValue 0.9009/1479, Liabilities 0.8666/1604. H2: AP 0.8787/1196,
AR 0.8998/1016, Cash 0.8858/1682, LiabilitiesCurrent 0.8681/1491. H1's
drop-one diagnostic additionally cites CommonStockSharesOutstanding
0.9051/1398 (funded). H2's ancestry diagnostics use Assets/INV/AR/AP vintages
inside diagnostics only, never in any arm.

**The critical V8-a5 lesson, honored structurally.** Control identifiability
is designed to be measurable BEFORE selection: each packet declares gates
R1–R4 — (R1) Spearman midrank rho between anchor and control conditioning
ranks ≤ 0.70 per date on ≥ 90% of the frozen grid dates and pooled ≤ 0.70;
(R2) non-degeneracy (largest midrank tie-group ≤ 25% of the measured universe,
V8 a5_h1's 80.8%-tie vacuous placebo precedent); (R3) control populated on ≥
60% of the anchor universe; (R4) anchor non-degeneracy. The pre-check universe
is the 63-bar-floor pool; inputs are the PIT panel (avail < gate(t)) plus
price-bar availability only — no band computation, no returns, never PnL.
Failure blocks the proposal pre-selection (fail-closed). Additionally, H2
declares binding pre-selection ancestry diagnostics A1/A2: pooled |rho| ≤ 0.20
vs the V8 WC stock-LEVEL shadow rank and vs the V8 F1 accrual-FLOW rank,
computed from the panel alone before selection; and both packets declare the
plan §1 standard |rho| ≤ 0.20 vs every forbidden ancestor, measured at D2
before any selection freeze.

**Inherited execution semantics** (declared per packet, unchanged): 63-bar
floor + ADV63 ≥ $2M (band C or better; D excluded) + RAW ≥ $1.00; session-index
grid 63+21k per frozen fold; warmup_decisions = 0 (level ratios, no delta
legs); sector terciles with one-decile retention hysteresis, sectors < 6
ranked names abstain; fills next session close, no same-session fill;
preregistered dead-name book semantics verbatim (fill-check, exit-at-last-close,
no survivorship re-substitution); band cost model 10/15/25 bps base, 2x stress,
charged once per fill, L-I3 fail-closed band resolution; folds S0_FOLD_1/2/3;
inherited Stage-A gate table with ex-ante margin-to-fail expectations per P-2.

## Self-check record

Executed on the worktree at HEAD `86fecae8044d344e5d5ea9a49bbcfdb2f03c0b5a`
(before the single documentation commit). The checker verifies: both JSONs
parse; all 24 required top-level fields; mechanism's four claim components;
cohort legs + 63-bar floor + band floor + sector conditioning; warmup and
21-session grid; the three dead-name book semantics strings; band cost model;
exactly three arms; the ≤ 0.70 pre-selection rho gate with no-band/no-returns/
no-PnL scoping; every cited clock tuple (field, max_age_days, coverage,
mapped) is a verbatim member of the 56-clock funded set; novelty declared per
confusable ancestor; explicit outcome-blind attestation.

```text
PASS funded clock set loads and has 56 entries (got 56)
== a5_clock_H1.json
PASS schema == stocks_free_v9_run/d1_proposal@1
PASS hypothesis_id == SFV9-A5-H1
PASS wave_sha pinned to 86fecae
PASS all 24 required top-level fields present
PASS mechanism covers who-forced / why-exists / observable / when-must-fail
PASS universe names cohort legs
PASS 63-bar floor declared
PASS band floor declared
PASS sector conditioning choice declared
PASS warmup_decisions declared
PASS inherited 21-session decision grid declared
PASS fill-check semantics present
PASS exit-at-last-close semantics present
PASS no-survivorship-re-substitution semantics present
PASS inherited band cost model declared
PASS exactly three arms defined (anchor/neighbour/control)
PASS pre-selection control rho gate <= 0.70 declared
PASS pre-check uses no band computation
PASS pre-check uses no returns
PASS pre-check never from PnL
PASS all 4 cited clock tuples verbatim members of the 56-clock funded set
PASS novelty declared vs SFV8-F1-WC-ACCRUAL-FLOW
PASS novelty declared vs SFV8-F2-DEP-RESERVE-COVERAGE
PASS novelty declared vs SFV4-A4-H1-SEMIVARIANCE-SHAPE_and_vol_level_shadow
PASS novelty declared vs SFV4-A5-H1-PARTICIPATION-SHIFT
PASS novelty declared vs A4_XSEC_ETF_RELATIVE_MOMENTUM
PASS novelty declared vs A5-S2-F1-LENDING-CONSTRAINT-PREMIUM
PASS ancestry |rho| <= 0.20 standard declared
PASS outcome-blind attestation present and explicit
== a5_clock_H2.json
PASS schema == stocks_free_v9_run/d1_proposal@1
PASS hypothesis_id == SFV9-A5-H2
PASS wave_sha pinned to 86fecae
PASS all 24 required top-level fields present
PASS mechanism covers who-forced / why-exists / observable / when-must-fail
PASS universe names cohort legs
PASS 63-bar floor declared
PASS band floor declared
PASS sector conditioning choice declared
PASS warmup_decisions declared
PASS inherited 21-session decision grid declared
PASS fill-check semantics present
PASS exit-at-last-close semantics present
PASS no-survivorship-re-substitution semantics present
PASS inherited band cost model declared
PASS exactly three arms defined (anchor/neighbour/control)
PASS pre-selection control rho gate <= 0.70 declared
PASS pre-check uses no band computation
PASS pre-check uses no returns
PASS pre-check never from PnL
PASS all 4 cited clock tuples verbatim members of the 56-clock funded set
PASS novelty declared vs SFV8-F1-WC-ACCRUAL-FLOW
PASS novelty declared vs SFV8-F2-DEP-RESERVE-COVERAGE
PASS novelty declared vs SFV4-A4-H1-SEMIVARIANCE-SHAPE_and_vol_level_shadow
PASS novelty declared vs SFV4-A5-H1-PARTICIPATION-SHIFT
PASS novelty declared vs A4_XSEC_ETF_RELATIVE_MOMENTUM
PASS novelty declared vs A5-S2-F1-LENDING-CONSTRAINT-PREMIUM
PASS ancestry |rho| <= 0.20 standard declared
PASS outcome-blind attestation present and explicit

RESULT: PASS
self-check exit code: 0
```

First iteration of the checker recorded 9 FAILs: 1 real gap (the literal
`exit_at_last_close` label was missing from the semantics string in both
packets — fixed) and 8 checker-strictness mismatches (substring checks against
combined novelty keys, rule-vs-inputs scoping, attestation phrasing) — fixed
in the checker and in the two rule strings ("never from PnL" now inside the
rule body). Final run above is the recorded result.

## Known limitations (declared, not hidden)

- H1's par-stub placebo has a declared ex-ante rho expectation of 0.2–0.6 with
  a hard 0.70 gate: if measurement lands above 0.70 the proposal blocks
  pre-selection by design (fail-closed, not a scored surprise).
- H2's anchor universe is leg-intersection-bound (AR mapped 1016 vs AP 1196 on
  the dead leg); the ≥ 30 scored-decision floor could be coverage-stressed —
  declared as a SAMPLE_FLOOR failure mode, never a silent book.
- Unbounded clocks mean a name's last filed vintage can be arbitrarily stale
  near death; staleness is structural and handled by declared as-of semantics,
  per-decision vintage-age reporting, and placebo controls sharing the exact
  mixing structure — not argued away.
- The V9 band populations (dead leg skews to lower ADV) are expected to lift
  the blended cost toward the band-C ceiling; declared as the dominant
  margin-to-fail risk on expectancy for both anchors.
- If both A5 proposals are selected at D2, they consume exactly the 6-cell V9
  scored budget (3 arms × 2); unused slots are never reassigned.
- Nothing is scored anywhere in this cycle yet; the HARD STOP before the first
  scored cell until the owner types `GO STOCKS V9 SCORED EXECUTION` stands
  (P-8).

## Provenance

Read before writing (in order): root `PLAN_stocks_v9.md`; wayfinder
`HYPOTHESIS_LEDGER.md` + `LESSONS.md` (root copies — the ledger files are not
present in this worktree at the wave SHA); V9 `run_contract.json`,
`cohort_v9.json`, `p2_v9_coverage_first.json`, `p3_invariants_freeze.json`; V8
`family_verdicts.json`, `forbidden_family_inventory.json`,
`selection_freeze.json`, `d1_proposal_packet.json` + the six V8 proposals
(incl. the ineligible a5_h1/a5_h2 whose measured control failures motivated
the R1–R4 design); `research/assets/stocks/v8_family_runner.py` for execution
semantics/feasibility realism only. Wave verification: all three D1 lane
worktrees (`d1-a4-distress`, `d1-a5-clock`, `d1-a6-deathevent`) are at
`86fecae8044d344e5d5ea9a49bbcfdb2f03c0b5a`.
