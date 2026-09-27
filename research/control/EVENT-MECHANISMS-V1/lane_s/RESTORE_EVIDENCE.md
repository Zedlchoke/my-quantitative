# LANE S RESTORE EVIDENCE — S1 form-4 layer / S2 price panel / S3 div+splits (2026-09-27)

All digests recomputed by this lane (fail-closed); stored sums never trusted.

## Archive layer

| Archive | Size (B) | sha256 (recomputed) | vs SHA256SUMS.txt.cleanup_2026-09-17 |
|---|---|---|---|
| stocks-free-v13_integration.tar.gz | 227,759,507 | `57a9d42c95c0af51f395c677cb898ff587b388928313c86e920296d71533fefc` | EXACT |
| stocks-ng6_integration.tar.gz | 81,404,954 | `808ca4f1ce92ad0e80a6c33476dd4781f21cdcc31feb1f91325027e01c23824a` | EXACT (dispatch pin matches) |

Tar members listed: v13 = 697,889 entries (692,263 form4_xml-related);
NG6 = 3,524 entries.

## S1 — form-4 layer (restored into `.staging_eventmech/`)

| Artifact | sha256 (recomputed) | Verdict |
|---|---|---|
| `integration/.staging_sec_v13/form4_stream.jsonl` (167,883,229 B) | `6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991df5f05ba6742b2` | **= G2 PIN EXACT → lane continues** (fail-closed gate passed) |
| `integration/research/control/stocks_free_v13_run/substrate_manifest.json` (46,536,542 B) | `5d351623675f71a9950d0e290b1fafff89901265f18bf6c687660e96285ea26b` | = G2 manifest pin `5d351623…` EXACT |
| `substrate_manifest_digest.json` | `941ba6c30ec439ce6ffcad68dfe9c68e6b19f0043f726f5b6c8dbeb22a8b9c9c` | self-consistent (pins the two above + counts) |
| `form4_xml/.defects.jsonl` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty-string sha) | zero defects recorded |
| `form4_xml/.done` | `9efd5d731f04184a7206aab06bcde2fa97815cce727ffebf0db681d2d8dc7663` | — |

- Stream rows: **546,039** (`wc -l`) = substrate digest count = G2 record. 
- Full form4_xml extraction performed (disk allowed; 32 GiB free at start):
  **345,150 XML files** extracted, count EXACT vs manifest `form4_xml_docs: 345150`.
- Random sample verification vs `substrate_manifest.json` (seed 99, n=25):
  **25/25 sha256 EXACT** — evidence `lane_s/form4_xml_sample25.csv`.
- Manifest self-declared erratum noted: stream pin moved 427,096→546,039 rows
  (pre-INC-V13-12/13) with XML pins unchanged — consistent with what we measured.

## S2 — price panel (NG6) → CHOSEN PRICE PLANE per R2-5

- Restored `integration/data_raw/stocks_ng6_eod/` → 2,169 `.json.gz` files,
  **3,209,972 total rows** (≈3.21M expected), per-file sha256 manifest committed
  as `ng6_panel_digest.txt` (2,169 lines, file sha256 `b0b5a2a997befc58ba955ab5eb8b00631b763b8595bbff3bf29df6b5fcfcc342`).
- **Schema carries RAW OHLCV**: fields measured (first row of every file):
  `date, open, high, low, close, volume` — RAW/unadjusted — plus vendor
  `adjusted_close` (PRESENT but **FORBIDDEN by R2-1**; not used anywhere downstream).
- 20-ticker random sample (seed 42): date ranges 2015-01-02 .. 2026-09-15
  (alive names ~2,942 rows full-history; dead names short histories, e.g.
  HRLLL 5 rows 2020-06-22..2020-06-26; CIIC 289 rows) — death-inclusive panel
  confirmed. 5 sample rows recorded in REPORT.md.
- **CHOICE: NG6 panel is the price plane** (raw OHLC present → no eod_cache
  fallback needed; the read-only eod_cache was NOT touched — N9 re-pin of the
  unused subset therefore not exercised; recorded as a carried note).
- Cohort member list `cohort_members.json` + `cohort_manifest.json` restored;
  lineage `cohort_v9.json` sha `6a95401f…aa62` verified EXACT (see N4_REPORT.md).

## S3 — EODHD div/splits (restored from the v13 tar)

- Location measured: NOT in the NG6 tar (`tar -tzf | grep -ciE 'div|split'`
  → 7 unrelated filename hits, 0 data files); present in the v13 tar as
  `integration/.staging_sec_v13/eodhd_div/` + `eodhd_splits/`.
- Restored to `.staging_eventmech/integration/.staging_sec_v13/eodhd_{div,splits}/`:
  **2,168 + 2,168 files** (exact vs manifest counts; +1 NG6 panel dir total is SPY benchmark price series, not div/splits).
- Verification vs `substrate_manifest.json` (seed 7, n=25 per dir):
  **div 25/25 EXACT, splits 25/25 EXACT** — evidence `divsplits_SHA256_sample.csv`.
- Schema (measured):
  - div: `{date (ex-date), declarationDate, recordDate, paymentDate, period,
    value, unadjustedValue, currency}` — e.g. ABT last row 2026-07-15 value 0.63 USD Quarterly.
  - splits: `{date (ex-date), split: "numerator/denominator" string}` — e.g.
    ABT 7 rows, latest "10000.000000/4798.000000" 2013-01-02.
  - 1,268 div / 1,119 splits files are `[]` (no actions) — normal for the
    cohort's short-lived names.
- These feed the R2-2 corporate-action window exclusion (exclusion uses
  `date` = ex-date on both tables).
