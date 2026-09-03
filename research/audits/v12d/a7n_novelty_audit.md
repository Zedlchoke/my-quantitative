# V12 D2 — A7-N novelty / anti-rescue audit of the six blind proposals

Auditor: A7-N (independent). Branch `orca/v12d-a7n-novelty`, base `9c176797ec23352b96047d5c41108da7ff13fe8b`.
Audit only — no proposal or production file was edited.

**Worktree identity note.** The designated worktree `d2-a7n-novelty` / branch `orca/v12d-a7n-novelty`
did not exist at start; the shell opened in the integration worktree whose HEAD *equaled* the
bootstrap SHA with an empty porcelain. The auditor created the designated worktree and branch at
that exact SHA (content-identical), re-verified identity, and proceeded. No history rewritten.

Integrity: all 15 lane files re-hashed — every sha256 matches `pool_manifest.json`. S1 was not read.

---

## 1. Verdict table

| ID | Novelty | Rescue | Verdict | One-line reason |
|---|---|---|---|---|
| V12-A5-P1-BAB-LOWBETA | GENUINE | not a rescue | **ELIGIBLE** | Systematic-beta pricing absent from inventory; ranks decorrelated from every rejected/reserved ancestor (|rho| ≤ 0.20); frozen 90d warmup, cap by construction. |
| V12-A5-P2-MIX-ORDERSIZE | GENUINE | not a rescue | **ELIGIBLE** | Order-size composition has no price term (|rho| 0.22 vs reserved Amihud feature), no returns, no signed flow; windows derive from the frozen warmup; trades column verified present. |
| H-A6-OSCOMP | VARIANT_OF_FORBIDDEN | reserved-family collision | **INELIGIBLE** | Anchor rank is the sign-INVERTED reserved ILLIQ-AMIHUD rank: \|rho\| = 0.81 in-window / 0.87 prewindow (threshold 0.50 = HIGH), i.e. the reserved family's inverted control arm relabelled. |
| H-A6-RVX | GENUINE | not a rescue | **ELIGIBLE** | Two-name cointegration residual ≠ single-name reversal; the scored random-pair control would kill any renamed reversal; pairs pre-registered in an outcome-blind lane. |
| A8-P1-BAB-PERP | GENUINE (but duplicate) | not a rescue | **INELIGIBLE** | Caveat-source DOI 10.1111/jofi.13121 verified WRONG (resolves to a JF prizes announcement) = HIGH; and rank-identical to A5-P1 (|rho|=1.0 at all 85 stamps) = duplicate mechanism. |
| A8-P2-TICKET-MIX-CONTRARIAN | GENUINE | not a rescue | **ELIGIBLE** | Normalised weekly ticket decorrelates from Amihud (|rho| 0.27/0.30); sound sign-flip + placebo controls; see merge note vs A5-P2. |

Per plan: any unresolved HIGH ⇒ ineligible. A8-P1's HIGH is **curable** (fix/drop the caveat-source
DOI — mechanism untouched); OSCOMP's HIGH is **not curable by parameter change** (the observable is
the problem).

## 2. Measurement (features only — no PnL/returns/backtests)

PIT feature cross-sectional ranks at Monday 00:00Z stamps from read-only staged bars + consolidated OI.
Raw per-stamp values: `a7n_scratch/a7n_rank_similarity_raw.json`, `a7n_scratch/a7n_oilev_collision_raw.json`,
`a7n_scratch/a7n_beta_vs_illiq_diag.json`.

Key numbers (mean |rho| unless noted; in-window = 52 S0 stamps, prewindow = 33 Mondays before 2025-08-22):

| Pair | in-window | prewindow | Reading |
|---|---|---|---|
| A5-P1 vs A8-P1 (beta90) | **1.000** (52/52 stamps) | **1.000** (33/33) | same mechanism, definitively merged |
| A5-P2 vs A8-P2 (ticket) | 0.63 (38% ≥ 0.70; max 0.89) | **0.74** (73% ≥ 0.70) | same participant-mix mechanism → merge for selection |
| A6-P1 vs A5-P2 / A8-P2 | 0.23 / 0.23 | 0.36 / 0.33 | raw ticket LEVEL is rank-distinct from the normalised pair |
| **A6-P1 vs Amihud28 (reserved)** | **0.81, sign −0.81** (94% ≥ 0.70) | **0.87, sign −0.87** (100% ≥ 0.70) | the HIGH reserved-collision finding |
| A5-P2 / A8-P2 vs Amihud28 | 0.22 / 0.27 | 0.30 / 0.30 | normalisation removes the liquidity-scale entanglement |
| beta90 vs Amihud28 / ticket | 0.15 / 0.15 | — | BAB anchors clean — the OSCOMP collision is specific |
| any feature vs momentum (V4 proxy) | ≤ 0.20 mean (single-stamp max 0.78, not persistent) | ≤ 0.21 | no V4 collapse; BAB momentum-confound probe unlikely to trigger |
| any feature vs OI-flow / OI-stock (reserved OILEV) | 0.18–0.30; zero stamps ≥ 0.70 | — | no OILEV-V2 collision for anyone |

NOT_COMPUTED: H-A6-RVX pairwise similarity — a state-dependent pairs book emits no single-name
cross-sectional rank vector; mechanism-level assessment used instead (allowed by the D2 contract).

## 3. Source validation

Verified resolvable this audit (CrossRef/arXiv/RePEc): `10.3390/math12091351`, `10.1016/j.frl.2026.109851`,
`10.1016/j.frl.2023.104909`, arXiv `2607.09426` (Kim & Hansen, authors match), arXiv `2109.10662`
(Tadi & Kortchmeski, authors match), `10.1111/jofi.13183`, `10.1016/0304-405X(93)90029-B`, and the
Ozdamar JIFMIM RePEc page (whose abstract — retail attention negative, institutional positive —
supports A6-P1's sign transfer). Canonical and consistent with auditor knowledge: FP2014, BAC-2020,
Hvidkjaer `hhn049`, Kelley-Tetlock `jofi.12028`, Engle-Granger `1913236`, Gatev `hhj020`,
Avellaneda-Lee, Ang-Chen-Xing `hhj035`, Cong et al. `mnsc.2021.02709`.

**Fabricated DOI (HIGH):** `10.1111/jofi.13121`, cited in a8_prop1 as Liu-Tsyvinski-Wu (2022),
actually resolves to "Brattle Group and Dimensional Fund Advisors Prizes for 2021" (JF 77(2), 2022).
The proposal had flagged it "inferred" — the disclosure was honest, the DOI is nonetheless wrong.
Affects A8-P1 only; caveat-only source; curable.

Claim-to-test mapping and spot-to-perpetual caveats: present and specific in all six (checked line by line).

## 4. Causal control quality

- **Strong:** H-A6-RVX random-pair permutation (mechanism-destroying, *scored* — a renamed single-name
  reversal cannot survive it); A5-P2 trade-count permutation (preserves marginals, destroys the temporal
  mix alignment the anchor statistic actually uses).
- **Adequate:** sign-flips (A5-P1, A8-P1, A8-P2, A6-P1) are genuinely sign-destroying for signed-pricing
  claims. Residual limits noted: sign-flip cannot separate beta-pricing from generic low-vol preference
  (A5-P1/A8-P1, inherent, LOW), and cannot separate attention-decay from inverted-illiquidity when the
  anchor rank *is* the inverted illiquidity rank (A6-P1 — subsumed by the HIGH).
- No placebo that would pass either way was found anywhere in the pool.

## 5. Hidden-rescue scan

Clean on all four vectors: (i) no neighbour is a disguised parameter menu — every neighbour is a
theory-mandated sibling estimator (BAC / downside-beta / bucket-share / ticket-trend / OU half-life) and
none reproduces a reserved identity's windows (no 28d/56d Amihud or OI flow/stock variants anywhere);
(ii) no window overlaps a rejected family's signal — all ranks vs momentum/Amihud/OI features measured,
not asserted; (iii) no cap bypass — all books ≤ 0.30 by construction with pre-emission whole-book shrink
(explicitly not the forbidden post-score renormalisation); (iv) no unavailable/purchased data — staged
schema fields verified on disk (bars from 2024-08-21/23, `quote_volume` + `count` present for all 20
symbols ⇒ no fail-closed precondition triggered). RVX's pair list is self-attested pre-registration, but
the lane was outcome-blind with no scored artifacts in existence, so there was nothing to mine.

## 6. Dedup / merge map

- **BAB-leverage-constraint:** {V12-A5-P1-BAB-LOWBETA, A8-P1-BAB-PERP} — one mechanism (|rho|=1.0);
  eligible representative as-submitted: A5-P1.
- **Participant-mix/order-size:** {V12-A5-P2-MIX-ORDERSIZE, A8-P2-TICKET-MIX-CONTRARIAN} — one mechanism
  (0.63/0.74 straddling the 0.70 line, same source, same sign); both members individually eligible; select one.
- **Raw ticket level:** {H-A6-OSCOMP} — INELIGIBLE (reserved-ILLIQ inversion).
- **RV-cointegration:** {H-A6-RVX} — eligible, unique class.
- Pool = 4 mechanisms; **3 eligible mechanisms as submitted**.

## 7. Ranking-neutral notes for A1

1. Verdicts above are novelty/rescue only — no profitability ranking is expressed or implied.
2. Select at most one per merged group; A5-P1 and (post-repair) A8-P1 are interchangeable inside the BAB slot.
3. OSCOMP re-submission needs a genuinely different observable, not a re-parameterisation (the two
   normalised ticket statistics already in the pool demonstrate the achievable decorrelation: 0.22–0.30 vs 0.81).
4. If the owner repairs A8-P1's DOI before lock, the repair must be limited to that citation; any other
   edit reopens D2 review.
