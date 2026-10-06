# P0_ERRATUM_VERDICT — independent verification of the P0 fee erratum

- Round: FUTURES-OVERNIGHT-PREP-20261003, lane **P0-VERIFY** (independent verifier)
- Verifies: P0A-FEESOURCE + P0B-FEEIMPACT work committed at batch-1 checkpoint
  `72c9bc5b1d94b812044a9bd21768c53b4d378436` (lanes themselves ran at `a8cd06f2`).
- Worktree: `prep/futures-behavior-10syms-20261002`. Read-only lane; wrote only
  `fees_erratum/verify/**` + dispatch handoff. **Zero network fetches performed**
  (all verification against committed captures; no re-fetch attempted).
- Taxonomy: every claim below is FACT (byte-verified in capture), INFERENCE
  (labeled), or NOT_RUN. Arithmetic was never used as a source-value pass.

## 0. Artifact integrity (sha256 recompute vs handoffs) — FACT

All 17 P0A/P0B outputs recomputed with `shasum -a 256`; **17/17 match** the
digests in `dispatch/handoff_P0A-FEESOURCE.json` (14 files) and
`dispatch/handoff_P0B-FEEIMPACT.json` (3 files). Byte digests in
`p0_verdict.json.outputs_recomputed`.

## 1. Per-code corrected-value adjudication (tier-1 = Fixed / Tiered ≤1k) — FACT per cited bytes

All-in formula verified by me: commission + exchange + clearing 0.00 + regulatory.
Commission ladder (live `commissions-futures-amer.php.txt` L23–26 + RAW
`archive_commissions-futures.php.html` 2026-09-25, identical): **0.85 / 0.65 /
0.45 / 0.25 Tiered; 0.85 Fixed** — LITERAL in both. Clearing 0.00 per IBKR's own
worked examples (RAW L4047–4057; live L46–47, 59–60).

| Code | Exchange fee | Regulatory | All-in T1 | T2/T3/T4 | Capture citation (all independently located by P0-VERIFY) | Cell verdict |
|---|---|---|---|---|---|---|
| ES | 1.38 | 0.01 | **2.24** | 2.04/1.84/1.64 | `archive_CME.php.html` row `EMD, ES, SMC,…` value `1.38<sup>6</sup>` (L1703–1707); live render L54 glued `1.386`; reg live L97–98 `0.011 (For IB-JP: 0.011 incl. tax)`; IBKR Fixed example `0.85+1.38+0.00+0.01=2.24` (RAW `archive_commissions-futures.php.html` L4047–4057, exact) | **CONFIRMED** |
| NQ | 1.38 | 0.01 | **2.24** | 2.04/1.84/1.64 | `archive_CME.php.html` row `BQX, ER2, NQ,…` value `1.38<sup>6</sup>` (L1691–1695); live L52 glued `1.386`; same reg evidence | **CONFIRMED** |
| 6E | 1.60 | 0.01 | **2.46** | 2.26/2.06/1.86 | `archive_CME.php.html` `Forex Futures 9 AUD,…,EUR,…,GBP,…,JPY,…,6H` value `1.60` clean, sup 9 on LABEL (L1666–1673); live L47 | **CONFIRMED** (value); mapping PARTIAL — alias EUR + 6H, no verbatim `6E` (carried caveat) |
| 6B | 1.60 | 0.01 | **2.46** | 2.26/2.06/1.86 | same Forex Futures row, alias GBP | **CONFIRMED** (value); mapping PARTIAL |
| 6J | 1.60 | 0.01 | **2.46** | 2.26/2.06/1.86 | same row, alias JPY | **CONFIRMED** (value); mapping PARTIAL |
| 6A | 1.60 | 0.01 | **2.46** | 2.26/2.06/1.86 | same row, alias AUD | **CONFIRMED** (value); mapping PARTIAL |
| CL | 1.50 | 0.01 | **2.36** | 2.16/1.96/1.76 | `archive_NYMEX.php.html` (2026-09-25) row `CL, HO, RB` `USD 1.50 / 1.50 / 0.75` (L2540s); reg table L2699 heading + L2712–2715 `All → 0.01/0.01/0.00`, NO markers; live L23 + L53 | **CONFIRMED** |
| NG | 1.60 | 0.01 | **2.46** | 2.26/2.06/1.86 | `archive_NYMEX.php.html` row `NG` `USD 1.60 / 0.90 / 0.80` (L2547+); same reg row; live L24 + L53 | **CONFIRMED** |
| GC | 1.65 | 0.01 | **2.51** | 2.31/2.11/1.91 | live `COMEX.php.txt` L21 `GC, HG, SI | USD 1.65 | USD 0.75`, reg L45 `All | USD 0.01`; March-10 `archive_COMEX.php.html` `GC, HG, SI … 1.60` (L1130s), reg L1226 `0.02`, MGC 0.60, QO/QI/QC 1.00 — both epochs byte-captured | **CONFIRMED** + genuine temporal change (see §3) |
| SI | 1.65 | 0.01 | **2.51** | 2.31/2.11/1.91 | same GC/HG/SI row (live L21/L31); March archive same row 1.60 | **CONFIRMED** + temporal change |

Every corrected value matches `source/fees_corrected.json` and the 10/10 owner
provisional tier-1 numbers. My independent arithmetic re-check of all T1–T4
cells (commission ladder deltas −0.20/−0.40/−0.60) reproduces the table exactly.
Give-up 0.05 published but excluded from all-in (waiver sentence captured) — concur.

**CME reg 0.01 (live epoch) evidentiary note**: no post-June raw CME.php capture
exists (live raw transport BLOCKED_TRANSPORT on this machine). 0.01 rests on 3
independent signals: (a) live render glued `0.011` + inline paren tax arithmetic
`0.011 = 0.01 × 1.1` (mirrors June-raw `0.022 = 0.02 × 1.1`, L1890); (b) IBKR
worked example `Regulatory Fee USD 0.01` in marker-preserving 2026-09-25 RAW
HTML; (c) Sep-25 NYMEX RAW + live COMEX already at 0.01. Adjudicated CONFIRMED
with this residual documented.

## 2. Glue adjudication — CONFIRMED at byte level (FACT)

- `archive_CME.php.html`: `1.38<sup>6</sup>` exactly twice — NQ row (L1691–1695)
  and ES row (L1703–1707); a third `1.38<sup>2</sup>` belongs to the Housing
  Index row (correctly not attributed to ES/NQ). Footnote 6 text = "Non-Member
  spread orders will be charged $1.30 per contract."
- Regulatory marker: June-08 RAW `0.02<sup>1</sup>` (L1890) vs live render glued
  `0.011` — same cell class, marker 1 = NFA note.
- In-vivo glue demo: `archive_NYMEX.php.html` options row raw bytes
  `USD <span class="text-price">0.95</span><sup>4</sup>`; the live render prints
  glued `0.954` (NYMEX.php.txt L41) — the renderer demonstrably glues markers
  onto digits on these exact pages.
- Tax paren arithmetic exact: live `0.011 = 0.01×1.1`; June RAW `0.022 = 0.02×1.1`
  (also `2.58`, `1.536` parens on other rows — same pattern family).
- IBKR's own worked example (2026-09-25 RAW): **Fixed ES `0.85 + 1.38 + 0.00 +
  0.01 = 2.24` — arithmetic exact**; the Tiered ES example prints reg `0.00` yet
  sum `2.24` (components sum 2.23) — IBKR-side stale cell, exactly as P0A
  documented; 0.01 is carried by the Fixed example + paren + reg row.

## 3. Temporal-provenance verdict

- **CME cells (1.386 / 0.011): EXTRACTION DEFECT, not page change — FACT.**
  Parent A4 fetch log (13:05:20Z, `fees/fetch_log.jsonl` L5) itself embeds
  "NQ 1.386; ES 1.386 … Regulatory … 0.011" — the identical glued render P0A got
  at 15:20Z; the June-08 archive proves the sup markers existed for months.
  Parent saved no raw capture; glue is the only mechanism difference.
- **NYMEX reg parent 0.02: PARENT_VALUE_CONTRADICTED** — 0.01 in live render AND
  2026-09-25 RAW (L2712–2715); parent 0.02 NOT_LOCATED in both. "Extraction
  error" classification is **INFERENCE** (a 0.01→0.02→0.01 flip inside
  2026-09-25..10-03 is not physically excludable from this machine; implausible).
  Note: 0.02→0.01 is NOT producible by append-glue — distinct defect mode, as
  P0B flagged and P0A adjudicated cell-by-cell.
- **Two GENUINE mid-2026 page changes — FACT, both epochs byte-captured**:
  (1) COMEX GC/SI group 1.60 → 1.65 (2026-03-10 RAW vs 2026-10-03 live;
  corroborated MGC 0.60→0.70, QO/QI/QC 1.00→1.50); (2) regulatory 0.02 → 0.01
  (CME June-08 `0.02<sup>1</sup>` vs Sep-25/Oct-03 0.01; COMEX March 0.02 vs
  live 0.01). Historical-year use needs the current-schedule-as-approximation
  rule (carried from parent).

## 4. Impact-map completeness — CONFIRMED

- Propagation grep re-run at worktree root (exit 0): **26 files**, identical to
  P0B's list. False positive verified: `coverage_remeasure.json` L1784
  `"ts_event_min_utc": "2025-04-01T00:00:00.011588+00:00"` (sub-second
  timestamp). **25 genuine = 22 FROZEN-HISTORICAL + 3 LIVING-DOC** — per-file
  classification in FEE_ERRATUM_DRAFT §3 verified (spot-checked living sites:
  DATACONTRACT_QUALIFICATION.md L206–207 r6 sentence; SUMMARY_QUAL_ACTIONS L15;
  OWNER_DECISION_PACKET L17; PLAYBOOKS_DRAFT L75/185/210 supplementary
  rounded-value site, converges under correction).
- In-repo corroboration verified: `d2_feesrc/fees_table_es.json` E2 row carries
  the verbatim `…0.85 + 1.38 + 0.00 + 0.01 = 2.24` example (pre-existing).
- Batch-1 commit hygiene: `72c9bc5b` = **359 files, 100% status A (pure
  additions), all inside the round dir — zero tracked files modified**.
- DISPATCH_MANIFEST "27 files" vs measured 26 — off-by-one stands as reported
  (Lead-owned manifest; erratum records measured truth).

## 5. Validator results (P0B `validate_fee_sources.py`)

- Self-test: **6/6 PASS, exit 0** (reproduced by me).
- **REAL mode** (P0-VERIFY's own 37-check grid, `verify/p0_verify_expected.json`,
  not copied from P0B): exit 1 — correct semantics, because the grid deliberately
  includes adverse parent-value checks. Outcome per class:
  - corrected values: **all LITERAL** in marker-preserving RAW HTML / clean live
    renders (1.38 with marker-adjacent flag on both CME rows; 1.60/1.50/1.65/
    0.01/0.05/0.95; ladder 0.85/0.65/0.45/0.25; worked-example 1.38/0.01/2.24
    in RAW);
  - parent values: `1.386` → **FOOTNOTE_GLUED** on both CME rows (base 1.38 +
    marker 6); `0.011` NOT_LOCATED in June RAW; NYMEX `0.02` NOT_LOCATED;
    `0.954` NOT_LOCATED — every parent reading fails exactly as the erratum
    claims. No arithmetic-pass path exists in the tool (verified by code read).
  - `0.01` on live CME.php.txt → NOT_LOCATED (renderer destroyed the token into
    `0.011` artifact, which IS located) — the documented MARKERS_ABSENT
    limitation; authority for that one cell = §1 note (3 signals).
- Validator warts found by this lane (do not affect verdicts; raw HTML is
  authority): (a) argv parsing treats `--expected`/`--report` VALUES as capture
  paths — report file must pre-exist (IO-error exit 1 otherwise); (b) glue
  classifier requires marker immediately after the digit — span-wrapped cells
  (`0.95</span><sup>4</sup>`) yield NOT_LOCATED instead of FOOTNOTE_GLUED;
  (c) P0A's annotation header inside `CME.php.txt` makes its MARKERS_PRESENT
  flag spurious (annotation text itself contains `<sup>`).

## 6. NOT_RUN / not independently reproduced

- VERIFIED_VS_ACCOUNT = NOT_RUN on **every** value (all MODELED_COST
  public-reference schedule values). Owner account verification NOT_RUN.
- Overnight Position Fee tables: NOT_RUN (JS-driven, never render).
- FX outright symbols 6E/6B/6J/6A verbatim in row: NOT_LOCATED by design (alias
  mapping EUR/GBP/JPY/AUD + 6H only) — mapping corroboration stays PARTIAL.
- Parent-quoted sentence "These commission rates are charged by all IBKR
  entities": 0 archive hits (P0A finding, not re-verifiable live from this
  machine — live transport blocked). Do not cite.
- No live re-fetch of any IBKR page by P0-VERIFY (0 web attempts; sinkhole
  environment documented by P0A — re-fetch would add nothing beyond the four
  RAW archive snapshots already adjudicated).

## 7. FINAL ERRATUM VERDICT

**UPHELD in full.** Glued-superscript extraction defect CONFIRMED at byte level;
corrected tier-1 all-ins **ES/NQ 2.24, 6E/6B/6J/6A 2.46, CL 2.36, NG 2.46,
GC/SI 2.51 USD/side** all CONFIRMED from captures (tiered T2–T4 likewise);
provenance = extraction defect (FACT for CME cells; INFERENCE for NYMEX reg
contradiction) with exactly two genuine temporal changes documented (GC/SI
1.60→1.65; regs 0.02→0.01); impact map complete at 25 genuine sites (22 frozen
+ 3 living); batch-1 commit touched nothing tracked. Parent rounds' published
1.386/0.011-derived values (2.247/2.461/2.37/2.47 family) are RETIRED as source
values; downstream consumption should use `fees_erratum/source/fees_corrected.json`.
Gates: unchanged by this lane (SPEC freeze-ready / cost-gate statuses remain
UNDER REVIEW per erratum law §4 until a new A7 re-audit).
