# PORTFOLIO_MIGRATION_COMPAT — compatibility table for the shared $100k shadow portfolio

Owner requirement (2026-09-25, session 4): a **shared shadow portfolio of
$100,000, new epoch PnL, updated dashboard**. Ruling: this is a **separate
migration/identity** (a future owner-registered cycle, working name
PORTFOLIO-CONSOLIDATION-V1). The three amendment GO phrases
(P-G1/P-G2/P-G3) grant **NO** authority to change capital, reset ledgers,
or cut over dashboards. D1's umbrella registration grants none either.

## 1. Identity & epoch law (binding for any consolidation cycle)

- Consolidation = a **NEW portfolio identity** with its own ledger and its
  own `EPOCH_START` baseline of exactly $100,000. "Reset" means an epoch
  marker in the NEW book — **never** deletion, rewrite or re-basing of any
  existing sleeve ledger. All old ledgers stay append-only citable
  evidence (umbrella §4.7 bases keep applying per-identity).
- Sleeve admission into the portfolio is a **per-sleeve mount decision**
  (like PSV1 amendment A1 mounted sleeve 4): each admitted sleeve needs
  identity manifest, capital fraction, and cost-law pins valid under the
  portfolio book.
- Dashboard: a NEW portfolio view (combined epoch PnL, per-sleeve
  contribution) is ADDITIVE; the existing per-sleeve dashboard keeps
  running until its own owner decision. No automatic cutover.

## 2. Compatibility table

| Item | Still needed for the OLD shadow (proceed regardless) | Transfer / redesign for the NEW $100k portfolio |
|---|---|---|
| **A1 FX controls (D2)** | YES — short-beta control, USD-exposure report, stress-spread book, cost fields are laws of the EXISTING FX-RANGEFADE sleeves; unchanged | REUSE as components (control-arm calculator, session-spread stress, cost fields). REDESIGN: portfolio-level FX sleeve is a new mount — control and USD aggregation must re-scope from "per pair on one FX account" to "FX contribution inside the portfolio book"; epoch PnL starts at the portfolio's `EPOCH_START` |
| **A2 BANDRIDGE pins (D3)** | YES — and TIME-CRITICAL: identity cost law 6 bps/side + sizing B + fill law A must be pinned (`T_act`) before ANY fill can carry evaluability, whether or not consolidation ever happens; a fill before `T_act` = `UNPINNED_COST_LAW — NOT PROMOTABLE` | REDESIGN REQUIRED: sizing B is defined as a fraction of the sleeve's OWN $100,000. Inside a shared $100k portfolio the capital base changes → the pin must be re-expressed (fraction-of-portfolio-capital, or the sleeve keeps an isolated capital sleeve inside the portfolio). This is a NEW design decision for the consolidation cycle — A2 as drafted does not authorize it |
| **A3 XSECT retire (D4)** | YES — retirement is orthogonal to consolidation: cost-dominated (≈77:1) under the sleeve's own frozen identity; history preserved append-only; `T_ret` semantics per the revised draft | Binding constraint ON the portfolio: the successor law (rebalance only when expected carry ≥ full round-trip stress cost; new strategy ID) applies verbatim to any carry-style sleeve admitted to the portfolio. The retired identity is NOT carried into the new book |
| **BTC4H / ILLIQ / BASISLV sleeves** | keep running under PSV1 with umbrella §4 dispositions (BANDRIDGE conditional-keep; ILLIQ diagnostic-only D13; BASISLV observation-only price-only) | each requires its own mount decision + capital fraction; ILLIQ is DIAGNOSTIC_ONLY — not eligible for the portfolio book by construction (D5 law) |
| **Aggregate risk reporting (umbrella §5.15)** | display-only per D10 | becomes the natural reporting core of the new portfolio view (crypto-beta, USD-beta, correlation, drawdown overlap, capacity, venue/data-source concentration); caps remain owner-only |

## 3. Non-inferences (explicit)

- The three GO phrases (P-G1..P-G3) = authority to write code for THEIR
  amendments only — not capital changes, not ledger resets, not dashboard
  cutover, not portfolio creation.
- Any portfolio cycle needs: its own plan + A7 arc + owner GO at its own
  gate (umbrella §5.6 child-cycle law), and it may not retroactively
  rewrite sleeve history to manufacture a clean epoch.
- The dashboard "update" the owner wants belongs to the consolidation
  cycle's scope, sequenced AFTER the measurement amendments (D7 order).
