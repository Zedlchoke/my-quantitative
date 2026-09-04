# V13 D2 — A7-N Novelty / Anti-Rescue Audit (six blind proposals)

- Auditor: A7-N (independent; audit artifacts only — nothing under audit was modified)
- Cycle: CRYPTO-V13, Phase D2
- Generated: see `a7n_novelty_v13.json` (`generated_utc`)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v13/d2-a7n-novelty` (branch `orca/v13-d2-a7n-novelty`)
- Inputs of authority: `research/proposals/v13/blind_input_packet.md`; `research/control/v13_run/forbidden_family_inventory.json` (13 forbidden classes + DATA-GATED boundary); `research/control/v13_run/run_contract.json` `shadow_region_rule` (binding)
- Companion data: `a7n_novelty_v13.json` (full per-class map, rho distributions, per-fold means, data-access log)

## 0. Headline

| Proposal | Inventory map (13 classes) | rho vs frozen OILEV-V2 anchor | rho vs inverted control | 0.20 gate | Attestation | NOVELTY verdict |
|---|---|---|---|---|---|---|
| A13-V13-A5-EXITCAP | CLEAN | **+0.0963** | -0.0963 | PASS | PRESENT | **ELIGIBLE** (dup flag: NEAR-DUPLICATE of OITD) |
| A13-V13-A5-LIQEPIS | CLEAN | **+0.1445** | -0.1445 | PASS | PRESENT | **ELIGIBLE** (dup flag: EXACT signal duplicate of LIQPRO, opposite book) |
| A13-V13-A6-CAPVEL | CLEAN | **+0.1086** | -0.1086 | PASS | PRESENT | **ELIGIBLE** (dup flag: INVERSE-BOOK duplicate of EXITCAP/OITD) |
| A13-V13-A6-LIQPRO | CLEAN | **+0.1445** | -0.1445 | PASS | PRESENT | **ELIGIBLE** (dup flag: EXACT signal duplicate of LIQEPIS, opposite book) |
| A13-V13-A8-OITD | CLEAN | **+0.0528** | -0.0528 | PASS | PRESENT | **ELIGIBLE** (dup flag: NEAR-DUPLICATE of EXITCAP) |
| A13-V13-A8-TCH | CLEAN | **+0.1467** | -0.1467 | PASS | PRESENT | **ELIGIBLE** (dup flag: SAME-FAMILY variant of LIQEPIS/LIQPRO) |

All six pass the binding shadow-region novelty gate (`|rho| <= 0.20` vs BOTH the frozen OILEV-V2 anchor AND its inverted control, on the common window). **But the six proposals are NOT six mechanisms: they collapse into exactly TWO distinct signal variables** (section 3). The eligibility verdicts are per the binding rule; the duplicate findings constrain SELECTION.

## 1. Method (signal-only; no returns, no PnL, anywhere)

- Common window: 52 Monday stamps 2025-08-25..2026-08-17 (frozen calendar, imported from the frozen V12 module). Universe: 19 tradable symbols (20 REQUIRED_SYMBOLS minus BTCUSDT — the frozen anchor refuses BTCUSDT by construction and every proposal excludes it as benchmark; 19 is the maximal COMMON window).
- Frozen reference: `research/v12/families/oilev_v2/strategy.py::signal_scores_at`, anchor arm `OILEV-V2-28D-FLOW-W` (oi_flow = 28d log OI growth; strict-before PIT, 48h staleness, positive), imported read-only and called, not re-implemented. Inverted control = arm `OILEV-V2-28D-FLOW-W-INV`. Sanity: rho(anchor, inverted) = -1.000000 exactly on all 988 (stamp, symbol) pairs.
- Each proposal's ANCHOR signal was re-implemented faithfully, signal-only, from its JSON definition (see `faithful_signal_only_implementation` per proposal in the JSON). Data: authorized on-disk bars / funding / OI, read-only, decode per frozen conventions (raw i128/1e16; close-boundary snap; last-write-wins dedupe).
- Statistic: per-stamp cross-sectional Spearman rho on common eligible symbols (>= 9 breadth), averaged over the common window (primary); pooled within-stamp rank rho reported as robustness (values agree to ~0.002). Common-window overlap: **52/52 stamps** for every pair; 18–19 common symbols per stamp (18 where ETHUSDT is fail-closed-refused, see caveats).

## 2. Anti-rescue map (from mechanisms, verified independently)

Each proposal was checked against all 13 forbidden classes (`V12-OILEV-V2`, `V11-OILEVER-DELEV`, `V6/V1-CARRY-FUNDING`, `V11-ILLIQ-AMIHUD`, `V12-ILLIQ-REPLICATION`, `V11-LOTTERY-MAX-SKEW`, `V10-M01-AGGRESSOR-ABSORPTION`, `V4-XSECT-MOM`, `V8R-XSECT-REVERSAL`, `V9-TS-TREND`, `WEEKLY-REVERSAL/MR-RESCUE`, `V1-VOLCOMP` incl. V9 dollar-volume shock, `V12-BAB-LOWBETA`) — **all CLEAN for all six**; per-class reasons are in the JSON. Key independent verifications (not taken from the proposals' self-assessments):

- No anchor signal of any proposal contains an OI difference/flow term, a past-return term, or a funding term. This audit re-implemented every anchor from its JSON and confirmed the input set directly.
- The three OI-using proposals (EXITCAP, CAPVEL, OITD) condition on the OI **stock** relative to turnover **flow** — a different construct from the frozen 28d log-OI-growth anchor; the measured rho (0.05–0.15) confirms no hidden parametric rescue. No sign flip, horizon tweak, cap raise, carve-out or renaming of a listed family exists.
- The turnover-shape proposals (LIQEPIS, LIQPRO, TCH) are scale-invariant within-window dispersion statistics with no threshold/shock trigger and no continuation premise — the nearest neighbouring forbidden class is V9 dollar-volume shock; the boundary holds (boundary note recorded in the JSON).
- Vol-level and volume-level quantities appear only in a6/a8 **causal control arms** (`VOLREG-28D`, `CTL-VOLLEVEL`, `VOLLEVEL-28D`), each carrying a preregistered must-not-reproduce rule and never promotable — the opposite of a rescue.
- Shadow-region self-claims: all six declare NOT in the shadow region; all six nevertheless carry the binding A7-N gate (a5 pre-stages the full front door; a6/a8 adopt it as a voluntary falsifier). Since all pass, none needs confirmatory classification on this evidence.

## 3. Duplicate / near-duplicate findings (selector-critical)

Mean per-stamp Spearman rho between anchor signals (values); book direction resolved from each JSON's long/short mapping. Full 15-pair matrix in the JSON.

| Pair | rho (values) | Judgment |
|---|---|---|
| EXITCAP–OITD | **+0.9746** | **NEAR-DUPLICATE** — same construct (OI-notional / 28d $-turnover), same long-low book; differences are smoothing only (single OI snapshot x snapshot-paired mark vs 7-stamp OI mean x latest mark; 10%-missing tolerance vs strict all-28-days) |
| LIQEPIS–LIQPRO | **+1.0000** (all 52 stamps) | **EXACT signal duplicate** — `HHI_norm = 2688 x H` is an exact monotone transform; identical slot-level dollar-volume Herfindahl over trailing 2688 slots; books exactly OPPOSITE (LIQEPIS longs smooth, LIQPRO longs bursty) |
| CAPVEL–EXITCAP | **-0.9145** | **INVERSE-BOOK duplicate** — volume/OI is the approximate reciprocal of OI$/turnover$; CAPVEL's long-low-churn book is the opposite book of EXITCAP's |
| CAPVEL–OITD | **-0.9371** | **INVERSE-BOOK duplicate** — same cluster |
| LIQEPIS–TCH | **+0.6490** | **SAME-FAMILY variant**, same book direction (both long LOW turnover concentration); differs in granularity (15m slots vs UTC days) |
| LIQPRO–TCH | +0.6490 (values) | SAME-FAMILY variant, opposite book (LIQPRO longs high-H, TCH longs low-H) |
| CAPVEL–TCH | +0.2337 | DISTINCT (weak overlap: both long low-activity names) |
| remaining 8 pairs | \|rho\| 0.09–0.23 | DISTINCT |

**Mechanism clusters:**
- **Cluster A — OI stock vs turnover flow (positioning capacity/churn):** EXITCAP and OITD (same book, rho +0.97); CAPVEL (same variable, opposite book).
- **Cluster B — turnover temporal concentration shape:** LIQEPIS and LIQPRO (identical variable, opposite books); TCH (same family, coarser granularity, LIQEPIS-direction book).
- Cross-cluster |rho| is only 0.09–0.23 — the two clusters are genuinely distinct from each other.

**Selector conclusion:** with the 6-cell / <= 2-family sprint ceiling, at most ONE proposal per cluster should advance. Lanes a5 and a8 each contributed one proposal to EACH cluster; the six submissions do not constitute six independent mechanisms, and proposals within a cluster share their scored-evidence fate.

## 4. Attestation check

All six MDs carry the signed `OUTCOME-BLIND ATTESTATION` block in the packet's exact format (lane, proposal, statement, utc, agent): a5 @2026-09-04T11:19:42Z (line 250 both), a6 @2026-09-04T11:17:21Z (CAPVEL line 263, LIQPRO line 267), a8 @2026-09-04T11:16:00Z (OITD line 312, TCH line 317). All six JSONs carry the matching item-13 attestation object. Verdict: PRESENT for 6/6.

## 5. Caveats (honest reporting)

1. ETHUSDT is fail-closed-refused at the first 4 stamps by the complete-formation-window signals (bar-ingest gap ~14h on 2025-08-21 between ingest windows); the frozen anchor itself had 19/19 eligible at every stamp.
2. Per-fold means disclosed: LIQEPIS/LIQPRO F2 fold mean rho = +0.2041 marginally exceeds 0.20 within that single fold; the binding statistic is the common-window correlation (all 52 stamps), and individual Mondays reach |rho| up to 0.72 — the gate verdicts use the window-level measure per packet/contract.
3. Mark price for EXITCAP/OITD notional conversion proxied by markPrice at funding-settlement stamps (`funding_data/scan_2026`), available at settlement stamp; rank-level insensitive.
4. CAPVEL OI denominator interpreted as snapshots in (T-28d, T] with >= 26 required, per its JSON item5.
5. Boundaries kept: read-only data access; no S1; no returns/PnL/portfolio computation of any kind; no proposal or family code modified. Data-access log (paths read) in the JSON.

## 6. Verdict

Six ELIGIBLE proposals on the inventory map and the binding 0.20 rho gate; two genuinely distinct mechanism clusters only. Selection should take at most one proposal per cluster and must not read the six as six independent novelties.
