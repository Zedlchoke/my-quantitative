# D2 novelty + feasibility audit — STOCKS-FREE-V9 (one page)

Producer: D2 independent auditor, fresh context, audit base HEAD `93d47c3`, wave `86fecae`.
HEAD advanced once mid-audit (`77a992c`: owner GO intent per P-8, event-log only);
every audited input verified byte-unchanged between base and close.
Audit-only: no repairs, no gate loosening, **no returns/PnL computed** — conditioning
variables, populations, availability and rank correlations only. Full artifact:
`d2_novelty_feasibility_v9.json` (schema `stocks_free_v9_run/d2_audit@1`).

## Method

For each of the six proposals, the ANCHOR conditioning variable was computed exactly
as its packet defines it (fields, clock bound, `avail < gate(t)` as-of, fiscal-match
rules) on the **frozen 30 quarterly decision dates** (V6 `p0a_coverage_census`) over
its declared universe (A4/A5: 410 ALIVE + 1,550 DEAD_PRICE_CONFIRMED with packet
eligibility; A6: dead leg only). Pooled Spearman (midranks) vs the **reimplemented
forbidden ancestors** per `v8_family_runner.py` specs: SFV8-F1 accrual FLOW, WC
stock-LEVEL shadow, SFV8-F2 AccumDep/PP&E coverage, Goodwill/Assets shadow, V4-style
21d/252d dollar-volume participation, 63-session prior return. Gate: plan §1
|rho| <= 0.20 vs F1/F2 forms+shadows (+ participation where the packet claims it);
63-session return gated only for A4-H1's declared <0.80 bar. Panel sha256 re-verified
(`67591464…`); all six packet SHA256s match `d1_proposal_hashes.json`.

## Item 1 — NOVELTY_DECORRELATION: **FAIL** (4 of 6 fail)

| proposal | worst measured pooled rho vs V8 ancestors | verdict |
|---|---|---|
| A4-H1 `L/(L+ME)` | **GW/Assets −0.2212**; F1-flow **−0.20010** (knife-edge, 15/30 dates) | **NOVELTY_FAIL** |
| A4-H2 `(ΔRE−Cash)/Assets` | worst −0.1628 (WC stock); all four ≤0.20 | **NOVELTY_PASS** |
| A5-H1 `SE/PubFloat` | **GW/Assets −0.2028** (18/30 dates) | **NOVELTY_FAIL** |
| A5-H2 `AP/AR` | **WC stock −0.4133 (30/30 dates)**; F1-flow −0.2087 — its own A1/A2 diagnostics | **NOVELTY_FAIL** |
| A6-H1 `N63` regime | date-level: F1-flow **0.339**, GW/Assets **0.504** | **NOVELTY_FAIL** |
| A6-H2 `P63` regime | date-level: all four V8 forms **0.335/0.721/0.621/0.485** | **NOVELTY_FAIL** |

A4-H1's momentum-shadow screen passes easily (rho −0.0996 ≪ 0.80); it fails vs the
V8 forbidden forms. A6 conditioners are date-level (zero within-date variance), so the
pooled standard resolves to the between-date correlation vs ancestor cross-sectional
means (n=30) — recorded as an adjudication note for A1, not loosened.

## Item 2 — CONTROL_IDENTIFIABILITY_PRESELECTION: PASS, one packet-level FAIL

- A4-H1: momentum bar −0.0996 < 0.80 PASS; anchor-vs-book-leverage-control rho 0.626 < 0.95 PASS.
- A4-H2: anchor-vs-cash-level-control rho −0.594 < 0.95 PASS.
- A5-H1: R1–R4 all PASS (mean rho 0.246, max date 0.366 ≤0.70 on 80/80; control tie-group max 4.5%; coverage min 83%; anchor tie max 0.4%). Declared float-size diagnostic measured −0.02 vs declared 0.1–0.4 expectation (benign).
- A5-H2: R1–R4 PASS but its **declared pre-selection ancestry diagnostics A1/A2 FIRE** (0.413/0.209 > 0.20) → packet rule: INELIGIBLE at D2, no rescue.
- A6-H1/H2: no pre-selection control-identifiability gate declared (controls are scored arms); nothing violated.

## Item 3 — FEASIBILITY: **PASS** (no PnL)

Grid 27/26/27 = 80 decisions (A4/A5 packets understate fold 1 as "≈22" — recorded).
Every arm fills: A4-H1 anchor 309–504 names/decision; A4-H2 sampling floor 0.832 median
vs 0.25 gate (packet expected 0.25–0.45); A5-H1 552–1,031; A5-H2 342–604 (AR-bound, as
declared); A6 eligible 315–447 / 173–365 / 0–145 (med 363/281/73, one zero decision
abstains), scored regimes 54 (H1) / 60 (H2), all folds ≥5. Dead-leg band blend
18.5 bps/side reproduces the A6 packets' 16.5–19.4 claim; A4/A5 blend ≈14 bps.
**Flag (as instructed): A6-H2 fold 3 is ALL-LONG** (L27/M0/H0) — arms still fill, but
the preregistered "channel-unvalidated" branch is live. Runtime realistic: 1.5 GB
panel streams in 27 s; full measurement pass 18 s; scored cells ≪ 45-min safe stop.
The v8 runner's missing-price-leg skip is confirmed to need the packets' declared
exit-at-last-close kernel change.

## Items 4–5

PACKET_COMPLIANCE **PASS** (all 6): every cited (field, bound) clock is in the funded
56-set with matching coverage/mapped to the digit; exactly 3 arms; dead-name book
semantics verbatim; outcome-blind attestations present. ANCESTRY_SWEEP: no mechanism
collapses to a listed forbidden family under renaming/universe-change — the closest
approach is **A5-H2** (AP/AR is a within-WC reparameterization of the forbidden WC
stock exposure on a new universe; its declared decorrelation rationale is refuted by
measurement). Blocked-by-measurement, not by mechanism identity: A4-H1, A5-H1, A6-H1/H2.

## Bottom line

**Only SFV9-A4-H2 is measured-eligible on all five items.** Five of six proposals are
blocked from selection by the measured novelty gate. Artifacts left uncommitted for A1;
nothing else touched.
