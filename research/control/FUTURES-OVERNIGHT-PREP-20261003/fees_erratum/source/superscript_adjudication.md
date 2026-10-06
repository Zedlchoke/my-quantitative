# Superscript Adjudication — IBKR futures fee pages
Lane P0A-FEESOURCE | adjudicated 2026-10-03T15:10..15:30Z | worktree prep/futures-behavior-10syms-20261002 @ a8cd06f

Question: are trailing digits in fee numbers (e.g. "1.386", "0.011") real decimals, or
HTML `<sup>` footnote markers glued into the number by tag-stripping renderers?

## Mechanism (FACT, byte level)

IBKR fee tables attach footnote markers as `<sup>N</sup>` immediately after cell values.
Renderers that strip tags concatenate the marker digit onto the number.

Demonstrated in vivo — NYMEX.php Futures Options row (raw HTML, archive_NYMEX.php.html,
snapshot 2026-09-25):
  `<td ...>USD <span class="text-price">0.95<sup>4</sup></span></td>`
tag-stripped render (NYMEX.php.txt, live 2026-10-03, same row):
  `CL | USD 1.50 | USD 0.954 | USD 0.70`   <- "0.95" + footnote 4 reads as "0.954"

Markers on TEXT labels survive visibly instead:
  CME.php raw: `Forex Futures</strong><sup>9</sup>` -> render: "*Forex Futures* 9"

## Contested cell 1: CME E-mini exchange fee — VERDICT: 1.38, marker 6 (glue CONFIRMED)

Three independent checks:

(a) Cross-render comparison — FACT
  - archive_CME.php.html (2026-06-08 snapshot, RAW HTML bytes):
      E-mini Equity Futures (BQX, ER2, NQ, QCN, RS1, RSG, RSV, RTY, SPSOX, XAZ):
        `<td ... class="text-price">1.38<sup>6</sup></td>`
      E-Mini S&P Equity Futures (EMD, ES, SMC, ...):
        `<td ... class="text-price">1.38<sup>6</sup></td>`
      Housing Index: `1.38<sup>2</sup>`; Micro E-Mini: `0.35<sup>3</sup>`;
      Micro Nikkei: `0.43<sup>3</sup>`; NKD/NIY: `2.15<sup>5</sup>`.
  - CME.php.txt (LIVE 2026-10-03, tag-stripped): same cells read "1.386", "1.386",
      "1.382", "0.353", "0.433", "2.155" — exactly base+marker glued.
  - Live page state == parent A4's 13:05Z fetch state (both show glued "1.386"):
      the page did not change; only the reading differs.

(b) Footnote table — FACT
  CME.php notes (live + June archive), footnote 6 verbatim:
      "6. Non-Member spread orders will be charged $1.30 per contract."
  A footnote 6 EXISTS and is a per-row spread-rate caveat of the kind attached to
  tradeable product rows. Sibling footnotes 2/3/4/5/9 are spread-order rates ($1.30/
  $0.35/$0.14/$1.90/$0.12) — a coherent footnote family for fee cells, not decimals.

(c) IBKR's own worked example (commissions page, flat text, NO superscripts) — FACT
  archive_commissions-futures.php.html (2026-09-25) + live commissions render:
      Tiered: "1 ES Futures Contract = IBKR Execution Fee USD 0.85 + Exchange Fee USD
               1.38 + Clearing Fee USD 0.00 + Regulatory Fee USD 0.00 = USD 2.24"
      Fixed:  "1 ES Futures Contract = IBKR Execution Fee USD 0.85 + Exchange Fee USD
               1.38 + Clearing Fee USD 0.00 + Regulatory Fee USD 0.01 = USD 2.24"
  IBKR itself writes ES Exchange Fee = USD 1.38 (two-decimal) — never 1.386.
  [Tiered-example defect noted: 0.85+1.38+0.00+0.00 sums to 2.23, not the printed
   2.24 — page-internal stale cell; the Fixed line sums exactly and matches all
   regulatory evidence below.]

Sibling-cell corroboration (arithmetic): NIY cell 2.15⁵ with inline paren
"(For IB-JP customers: 2.58 incl. tax)": 2.15 x 1.2 = 2.58 EXACT; the glued reading
2.155 x 1.2 = 2.586 would print 2.59. NIY Mini (clean 1.28): 1.28 x 1.2 = 1.536 EXACT
matches its paren. The paren arithmetic proves the bases are the un-glued values.

## Contested cell 2: CME regulatory fee — VERDICT: 0.01, marker 1 (glue CONFIRMED)

(a) Cross-render — FACT
  - archive_CME.php.html (2026-06-08, RAW): `<td ...>0.02<sup>1</sup><br/>
    (For IB-JP customers: 0.022 incl. tax)</td>` — June value was 0.02 with marker 1.
  - CME.php.txt (LIVE 2026-10-03): "0.011 (For IB-JP customers: 0.011 incl. tax)".
  - Owner live read (owner cross-check, this tasking): "0.01 with superscript 1".
(b) Footnote/inline text — FACT
  Numbered footnote 1 (live): "In addition to any standard regulatory fee, US residents
  will also be charged the NFA assessment fee for executions on foreign exchanges. The
  fee rate is currently set at USD 0.01 ..." (June archive same note: USD 0.02).
  The inline IB-JP paren is cell text, not a numbered footnote: live "0.011 incl. tax"
  = 0.01 x 1.1 (10% Japan consumption tax) EXACT; June "0.022" = 0.02 x 1.1 EXACT.
  If the live base were truly 0.011, the tax-inclusive paren would read 0.0121->0.012.
  Owner's "footnote 1 = IB-JP incl. tax" is a mild conflation (the IB-JP text is the
  inline paren in the cell; numbered note 1 is the NFA-foreign note) — immaterial to
  the value: both readings agree the marker is "1" and the base is 0.01.
(c) Worked example: Fixed ES example regulatory = USD 0.01 (exact-sum line); E7
  example regulatory = USD 0.01 (0.5+0.85+0.00+0.01=1.36 exact).

Temporal note (FACT): CME reg changed 0.02 (2026-06-08 archive) -> 0.01 (live today),
accompanied by the NFA-foreign note changing USD 0.02 -> USD 0.01. Both snapshots carry
marker 1; glue affects every epoch equally.

## Contested cell 3: NYMEX regulatory fee — VERDICT: 0.01, NO marker (parent 0.02 contradicted)

(a) archive_NYMEX.php.html (2026-09-25, RAW): `<td>USD <span class="text-price">0.01
  </span></td>` Tier I; Tier 2 0.01; Tier 3 0.00 — NO sup anywhere in the row.
(b) NYMEX.php.txt (LIVE 2026-10-03): "All | USD 0.01 | USD 0.01 | USD 0.00".
(c) Worked examples: reg 0.01 (Fixed ES, E7).
Footnote 2 on NYMEX = "Regulatory fees are assessed by the NFA."
Parent A4's 0.02 (fetched 13:06Z) matches NEITHER the live page NOR the 8-day-old
archive. INFERENCE (most likely): parent extraction error (possibly anchored on the
2018-01-01 $0.02 NFA history in its own A5 source). Cannot fully exclude a page edit
inside 13:06Z-15:22Z, but that would require 0.01->0.02->0.01 inside 2.5h against a
stable 2026-09-25 archive state — implausible. TAXONOMY: INFERENCE for the parent-error
claim; FACT for live+archive values.

## Contested cell 4: COMEX GC/SI futures fee — VERDICT: 1.65 live (parent CORRECT; page changed mid-2026)

- archive_COMEX.php.html (2026-03-10, RAW): futures row `GC, HG, SI | USD 1.60 |
  USD 0.75`; options row `GC, SI, HG | 1.65 | 0.80`; reg All 0.02.
- COMEX.php.txt (LIVE 2026-10-03): futures `GC, HG, SI | USD 1.65 | USD 0.75`; MGC
  0.70|0.20 (archive 0.60|0.20); QO/QI/QC 1.50|0.70 (archive 1.00|0.50); reg All 0.01.
FACT: COMEX metals fees were revised upward between 2026-03-10 and 2026-10-03 (multiple
rows moved coherently — not a reading artifact, the raw HTML of both epochs is byte
evidence). Live 1.65/0.01 = parent A4's values = owner's read. No glue on these cells
in either epoch.

## Contested cell 5: CME Forex Futures (6E/6B/6J/6A group) — VERDICT: 1.60, marker ON LABEL not value

archive_CME.php.html RAW: `Forex Futures</strong><sup>9</sup><br/> AUD, BRE, ...,
EUR, GBP, ..., JPY, ..., 6H | USD | <td class="text-price">1.60` — value cell CLEAN
1.60; marker 9 sits on the product label (June footnote 9: "Exchange Fee is waived-off
for 6H Futures"; live footnote 9: spread $0.12). Parent's 1.60 was correct.
E-mini Forex (E7, J7): 0.85 clean. Mapping caveat unchanged: the row prints CME aliases
(EUR, GBP, JPY, AUD, ..., 6H) — 6E/6B/6J/6A not verbatim (parent fx_mapping_note
stands; corroboration remains PARTIAL).

## Verdict table

| cell | glued reading | true value | marker | checks passed | verdict |
|---|---|---|---|---|---|
| CME E-mini Equity (NQ) | 1.386 | 1.38 | 6 (spread $1.30) | a+b+c | GLUE CONFIRMED |
| CME E-Mini S&P (ES) | 1.386 | 1.38 | 6 | a+b+c | GLUE CONFIRMED |
| CME regulatory | 0.011 | 0.01 | 1 (NFA/IB-JP) | a+b+c | GLUE CONFIRMED |
| NYMEX regulatory | (0.02 claimed) | 0.01 | none | a+b+c | PARENT VALUE CONTRADICTED (no glue involved) |
| COMEX GC/SI futures | 1.65 | 1.65 | none | a+b | PARENT CORRECT (temporal change 1.60->1.65 pre-Oct) |
| COMEX regulatory | 0.01 | 0.01 | sup 1 on heading only | a+b | PARENT CORRECT (0.02 in Mar epoch) |
| CME Forex Futures (6E/6B/6J/6A) | 1.60 | 1.60 | 9 on LABEL | a+b | PARENT CORRECT |
| NYMEX CL / NG futures | 1.50 / 1.60 | 1.50 / 1.60 | none | a+b | PARENT CORRECT |

Parent-round root cause (INFERENCE, high confidence): A4-FEES read tag-stripped
web_reader renders and absorbed <sup> digits into the numbers ("1.386", "0.011"),
and separately misstated NYMEX reg as 0.02; it saved no raw captures, so nothing
could catch either error. Page values did not change for CME between 13:05Z and this
lane's fetch (identical glued renders both times).
