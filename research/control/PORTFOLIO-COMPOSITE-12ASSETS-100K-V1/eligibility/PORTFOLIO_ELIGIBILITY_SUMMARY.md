# PORTFOLIO_ELIGIBILITY_SUMMARY — 1,200 IDs, ladder v2 (2026-09-29, post-amendment)

Pre-GO artifact of PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (draft cycle, NOT
REGISTERED). **Ladder v2 implements the owner's 2026-09-29 (2nd)
directive**: novelty/ancestry no longer excludes; implementability decides;
failure history rides along as an outcome-exposed label. Amendment of
record: `../plan/AMENDMENT_OWNER_DIRECTIVE_2026-09-29.md`. Ladder v1
(novelty-gated, 0 admissible) is preserved in git history and session-1
reports as the state under the OLD law.

Inputs (append-only evidence, re-verified): PR12A CENSUS_1200.tsv (1,200
rows, frozen rubric) · SLEEVE-FX5 F-0 verdicts (kept as labels) ·
DATA_COST_MATRIX · COST_AUTHORITY_TABLE · pr12a100k PIT dossier
(EFFR/VIX/Brent−WTI evidenced). Table:
`PORTFOLIO_ELIGIBILITY_1200.tsv` (1,200 rows; builder v2 deterministic;
validated: 1,200 unique gids, census-verdict provenance exact, 12×100
symbols, GBPUSD cost-axis typo fixed).

## Headline (v2)

**EXPLORATORY_CANDIDATE: 294 / 1,200 rows on the 5 evidenced pairs**
(ladder v2.1 — post-skeptic F-4/F-5 classifier fixes: 'news calendar'
false-positive repaired, SOFR removed from the evidenced set). EURUSD 56 ·
GBPUSD 80 · USDJPY 51 · USDCAD 52 · AUDUSD 55. All 10
families represented: G-XASSET 40 · A-TREND 38 · F-EVENT 32 · C-BREAKOUT
31 · I-STATARB 31 · B-MEANREV 29 · E-SESSION 29 · J-REGIME_OPT 29 ·
H-POSITIONING 20 · D-CARRY_TERM 13.

Outcome-exposed labels among the candidates (history preserved, never renamed):
FAMILY_HISTORY_NEGATIVE 223 · PRIOR_NOT_SCORED 59 · F0_INDIVIDUAL_REJECT
12. These labels flow into every trial-ledger row and every published
table of the cycle.

## Blocked rows and their named unblocks (unchanged by the amendment)

| status | rows | unblock |
|---|---|---|
| BLOCKED_NO_PRICE_DATA | 565 | owner data decision per symbol (NZDUSD/USDCHF M1 source; metals; energy futures) — stays BLOCKED per directive |
| BLOCKED_PIT_UNEVIDENCED | 115 | per-source PIT dossiers (COT/EIA/OIS/TIPS/DXY/GDT/SNB/…) |
| BLOCKED_VENUE_UNEVIDENCED | 90 (XAUUSD) | executable-venue evidence + PIT lag measurement |
| BLOCKED_NOT_MECHANIZABLE | 68 | none foreseeable (no falsifiable rule) |
| BLOCKED_DATA_CEILING | 39 | ERP1 M1 re-fetch (AUDUSD/USDCAD intraday rows) |
| BLOCKED_DATA_FEATURE | 22 | feature panels at declared ceiling |
| BLOCKED_COST_SWAP | 9 | IBKR statement (swap-profit dependence) |

## Reading rules (binding for every consumer of the table)

0. **TRIAGE OVERLAY (Lane R, same session — the operative layer):** the
   ladder's EXPLORATORY_CANDIDATE badge certifies panel/data/cost gates
   only, NOT input availability. Reading each row's rule text at its
   corpus source: **150/294 runnable today** (T1_RULE_READY 75 ·
   T2_DEFAULTS_DECLARED 75 · T3_PARK 144, per-row reasons in
   `../poolB/grouping/mechanization_triage_292.tsv`). Disclosed classifier
   incidents: I-R1 rows with unevidenced cross-asset inputs reached the
   ladder as PRICE_ONLY (triage parks them); I-R2 SONIA rows carried
   MACRO_PIT_EVIDENCED_PARTIAL via the "sofr" keyword though only the US
   leg is evidenced (parked). Families that fell on inputs: D-CARRY_TERM
   0/13, F-EVENT 2/30, H-POSITIONING 2/20.
1. EXPLORATORY_CANDIDATE ≠ edge claim. It means: rules can be written
   mechanically, the panel exists, PIT is provable at the panel clock,
   costs are testable under measured spreads + DECLARED bands. Every
   candidate's individual expectancy is UNKNOWN until its TRAIN-fold
   diagnostic runs — except labeled rows, whose family-level or individual
   history is KNOWN-NEGATIVE and is disclosed, not hidden.
2. The 294 rows are the discovery INPUT; the cycle's Stage-A
   (mechanization screening) will price how many compile into exact rules
   and clear decision-count floors on the real calendar — attrition is
   expected and recorded per row with reasons.
3. Selection priority per owner: clear rules · testable data/costs ·
   enough trades · complementary loss/win behavior. Complementarity is
   measured on TRAIN folds only (co-loss episodes, PnL correlation,
   order overlap) — never on test folds.
4. 7/12 assets remain BLOCKED; the portfolio carries their columns as
   FLAT-by-authority. No activation without the named unblock + gates.

## Cost authority state (5 evidenced pairs — binding for every leg)

Spreads MEASURED at fill hours (liquid p50/p90: EURUSD 0.3/0.5 · GBPUSD
0.8/1.3 · USDJPY 0.5/0.9 · USDCAD 1.2/1.6 · AUDUSD 1.0/1.3 pips), roll
window and Sunday reopen measured; commission/slippage/swap
DECLARED_PESSIMISTIC (U2/U3/U4-U5) → every pair
PROVISIONAL_PENDING_COST_AUTHORITY; no survivor is cost-PASS until the
owner statement lands. Lane D's physical panel audit (this session,
`../poolB/data_audit/`) re-verifies coverage, the tick-volume field and
the per-hour spread cells on the 3 M1 pairs.
