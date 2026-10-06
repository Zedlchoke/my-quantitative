# FEES_CORRECTED — IBKR futures fee erratum (P0A-FEESOURCE)

Task FUTURES-OVERNIGHT-PREP-20261003 | lane P0A-FEESOURCE | 2026-10-03 15:09-15:30Z UTC
Supersedes: research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/fees/fees_table_all.json (A4-FEES)
All numbers MODELED_COST, SOURCE=PUBLIC_REFERENCE, VERIFIED_VS_ACCOUNT=NOT_RUN.

## 1. Adjudication verdict: GLUED-SUPERSCRIPT CONFIRMED (FACT, byte level)

A4's extra digits are HTML footnote markers. Raw archive HTML proves the markup:

- `E-mini Equity Futures (BQX, ER2, NQ, ...): <td class="text-price">1.38<sup>6</sup></td>`
- `E-Mini S&P Equity Futures (EMD, ES, ...): <td class="text-price">1.38<sup>6</sup></td>`
- Regulatory: `0.02<sup>1</sup><br/>(For IB-JP customers: 0.022 incl. tax)` [June epoch]
  -> live today reads `0.011 (For IB-JP customers: 0.011 incl. tax)` = `0.01<sup>1</sup>` glued
- Sibling proof in vivo: NYMEX options row `0.95<sup>4</sup>` renders as "0.954".
- Footnote 6 = "Non-Member spread orders will be charged $1.30 per contract."

IBKR's own worked examples (flat text, no superscripts, live + 2026-09-25 archive):
- Fixed: "1 ES = 0.85 + 1.38 + 0.00 + 0.01 = USD 2.24" (arithmetic EXACT)
- E7:    "1 E7 = 0.5 + 0.85 + 0.00 + 0.01 = USD 1.36" (EXACT)
- Tiered ES line prints reg "0.00" but sum "2.24" — IBKR page-internal stale cell
  (components sum 2.23); adjudicated against 3 independent 0.01 signals.

Tax-arithmetic anchor: IB-JP parentheticals = base x 1.1 (0.02->0.022 June;
0.01->0.011 live) — proves bases are 0.02/0.01, not 3-decimal values.

## 2. Corrected per-code table (USD/contract/side, non-member, as of 2026-10-03)

Commission (commissions-futures.php?re=amer, live; identical 2026-09-25 archive):
Tiered T1 <=1,000/mo 0.85 | T2 0.65 | T3 0.45 | T4 >20,000 0.25; Fixed 0.85.
Marginal monthly volume across ALL futures/FOPs regardless of exchange.

| code | exchange table / row | commission (T1/T2/T3/T4, Fixed) | exchange fee | reg fee | ALL-IN T1=Fixed | T2 | T3 | T4 |
|---|---|---|---|---|---|---|---|---|
| NQ | CME.php "E-mini Equity Futures" (NQ verbatim) | .85/.65/.45/.25, F .85 | **1.38** (was 1.386) | **0.01** (was 0.011) | **2.24** | 2.04 | 1.84 | 1.64 |
| ES | CME.php "E-Mini S&P Equity Futures" (ES verbatim) | same | **1.38** | **0.01** | **2.24** | 2.04 | 1.84 | 1.64 |
| 6E | CME.php "Forex Futures" group (alias EUR; 6E not verbatim — PARTIAL) | same | 1.60 | 0.01 | **2.46** | 2.26 | 2.06 | 1.86 |
| 6B | same row (alias GBP) | same | 1.60 | 0.01 | **2.46** | 2.26 | 2.06 | 1.86 |
| 6J | same row (alias JPY) | same | 1.60 | 0.01 | **2.46** | 2.26 | 2.06 | 1.86 |
| 6A | same row (alias AUD) | same | 1.60 | 0.01 | **2.46** | 2.26 | 2.06 | 1.86 |
| CL | NYMEX.php futures "CL, HO, RB" Tier 1 | same | 1.50 | **0.01** (parent 0.02 WRONG) | **2.36** | 2.16 | 1.96 | 1.76 |
| NG | NYMEX.php futures "NG" Tier 1 | same | 1.60 | **0.01** (parent 0.02 WRONG) | **2.46** | 2.26 | 2.06 | 1.86 |
| GC | COMEX.php futures "GC, HG, SI" Non-Member | same | 1.65 (parent right) | 0.01 | **2.51** | 2.31 | 2.11 | 1.91 |
| SI | same row | same | 1.65 | 0.01 | **2.51** | 2.31 | 2.11 | 1.91 |

FX row honesty note: the 1.60 row is a generic CME "Forex Futures" product-group row
listing CME aliases (EUR, GBP, JPY, AUD, ... 6H). The page does NOT print 6E/6B/6J/6A
next to 1.60 — the mapping is the standard CME outright-symbol convention (PARTIAL
corroboration, unchanged from parent). The sup-9 marker sits on the row LABEL, not the
value; the value cell is clean 1.60.

Owner provisional tier-1 all-ins (ES/NQ 2.24, FX 2.46, CL 2.36, NG 2.46, GC/SI 2.51):
ALL TEN CONFIRMED by capture (see fees_corrected.json owner_hypothesis_check).

## 3. Provenance verdict (parent A4 fetched 13:05-13:25Z; this lane 15:10-15:30Z)

- CME cells: page state IDENTICAL between epochs (live render glued "1.386"/"0.011"
  both times) -> **EXTRACTION_DEFECT_CONFIRMED** (glued sups), not a page change.
- NYMEX reg: parent 0.02 contradicted by live capture AND 2026-09-25 archive (0.01,
  no markers) -> parent extraction error (INFERENCE; 2.5h page-flip not fully
  excludable but implausible).
- COMEX GC/SI 1.65 + reg 0.01: parent CORRECT. Genuine temporal changes exist and are
  byte-documented: reg 0.02->0.01 across CME/COMEX/NYMEX between 2026-06/03 and
  2026-09/10; COMEX metals futures 1.60->1.65 (with MGC 0.60->0.70, QO/QI/QC
  1.00->1.50) between 2026-03-10 and 2026-10-03.
- Root cause (INFERENCE, high confidence): A4 read tag-stripped renders and saved no
  raw captures, so glued digits and the NYMEX misread survived unchecked.

## 4. Geography / account context

- commissions URL carries ?re=amer: capture shows region selector pinned to
  "Americas"; US section used; publisher Interactive Brokers LLC (SEC/CFTC-regulated).
- Footnote-1 / IB-JP: the marker-1 on the 0.01 reg cell points to the NFA note; the
  IB-JP text is an inline paren IN the cell ("For IB-JP customers: 0.011 incl. tax"
  = 0.01 x 1.1 Japan consumption tax). It is a Japan-ENTITY pricing note, NOT a
  condition on the US number — for US accounts the regulatory fee is 0.01. (Owner's
  "footnote 1 = IB-JP incl. tax" is a mild conflation of the inline paren with the
  numbered note; immaterial to values.)
- Give-up 0.05 published on all pages, waived when IBKR is prime+executing — excluded
  from all-in (self-directed assumption), disclosed.
- Parent-quoted "These commission rates are charged by all IBKR entities": NOT found
  in this lane's captures (archive grep 0 hits) — unverified this round, do not cite.

## 5. Evidence inventory (this directory; sha256 in MANIFEST.md)

- archive_CME.php.html (RAW 2026-06-08), archive_NYMEX.php.html (RAW 2026-09-25),
  archive_COMEX.php.html (RAW 2026-03-10), archive_commissions-futures.php.html
  (RAW 2026-09-25) [+ .gz_raw originals] — byte authority incl. <sup> markup.
- CME.php.txt / NYMEX.php.txt / COMEX.php.txt / commissions-futures-amer.php.txt —
  LIVE renders 2026-10-03 (glue behavior documented).
- superscript_adjudication.md — three-check adjudication with verbatim quotes.
- fees_corrected.json — machine table with per-cell capture refs.
- fetch_log.jsonl — every attempt incl. BLOCKED_TRANSPORT (live curl/WebFetch blocked:
  www.interactivebrokers.com sinkholed to 127.0.0.1 machine-level; archive.org used).
- CME.php.md — QUARANTINED transcription incident (harness truncation; not evidence).

## 6. Residual NOT_RUN / limits

VERIFIED_VS_ACCOUNT=NOT_RUN everywhere; Overnight Position Fee NOT_RUN (JS tables);
effective dates unpublished; FX symbol mapping PARTIAL; live raw-HTML transport
blocked (renders + archives are the live evidence pair).
