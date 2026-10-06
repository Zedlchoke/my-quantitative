# FREEZE_DIFF — FUTURES-ES-PB1-V1 / lane BUILDER-REPAIR (M3)

- Cycle: FUTURES-ES-PB1-V1. Lane: BUILDER-REPAIR. Generated 2026-10-05.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, HEAD
  **`fc9c83621687bffafc8cc71039dee9e4c4c46dae`** (single bare `rev-parse` at
  lane start; no commit/stage/push; heavy lock FREE_PROVEN).
- Owner authority: `auth/PREGO_REPAIR_RECORDED.json` decision
  **HOLIDAY-REPAIR-AUTH** — *"okay lên lệnh cho agent trong zcode đi"*
  (following the conservative holiday repair proposal);
  **PINS-D-A1-A2-A3** — *"Đồng ý cả ba cách trên"*. Not a typed GO
  (`not_a_go_law` honored; GO phrase remains owner-only).
- Old → New (append-only supersession; v1 gate-2 artifacts are HISTORY and
  unmodified):
  - `freezegen/exclude_list.json`
    `bc8a41b673eccb998017e704a9865d139e67438fe984906f7f522782f93b438a`
    → `repair/exclude_list_v2.json`
    `67060c8ce5bf2402672c847b20e22842c3f2c14a5951b703ff19061b88ffcbcd`
  - `freezegen/selection_freeze.json`
    `e2b9934af01127ee698adda2fa0579d519f54881958e07463157728a8b96c1b7`
    → `repair/selection_freeze_v2.json`
    `cf150e248dc8d01acea2e456daa5db550ed396645afd19638f535c7b5cf135b1`
- Machine deliverable: `repair/freeze_diff.json`
  (`28eb5dfb80b87c7bf1dca8bf05c78a7615b79ad39b106deefe614097a82a7a3f`) —
  this document is its human projection; the JSON is authority.

---

## 1. The one change: rule class `HOLIDAY_PDF_EQUITY_2011_2015`

`repair/build_exclude_v2.py` starts from the exact frozen v1 logic
(`freezegen/build_exclude_and_freeze.py`, every rule preserved) and adds
exactly one class, consuming the committed 53-PDF extraction
`holiday/pdf_equity_evidence_2011_2015.json`
(`f3a8b4d43be720966ee8f2978de571e27c4e4ff5d2694dab4d1f4cd116c6bc53`):

> exclude every in-panel session whose date is a committed PDF primary-tier
> candidate (CLOSED / HALT / EARLY_CLOSE) **not** PDF-adjudicated regular.

- Fail-closed law preserved: PDF-absent dates keep their current classes.
- 2015-09-04 stays **INCLUDED** (PDF `2015-labor-day-holiday-schedule.pdf`
  equity section: *"Friday, Sep 4 — 1615 CT – Regular close"*; panel agrees,
  390 bars, last bar 16:14 CT).
- 2016: the class deliberately covers **no** 2016 date (no per-day PDF set
  exists; evidence of absence in `holiday/HOLIDAY_CLOSURE.md` M2) — 2016 is
  NOT silently treated as resolved; its fail-closed basis is re-proven by
  `repair/exposure_proof_v2.json` (section 5 below).
- Priority: `FOMC_STATEMENT_DAY > HOLIDAY_FACT_EARLYCLOSE >
  HOLIDAY_PDF_EQUITY_2011_2015 > HOLIDAY_UNCERTAIN > COVERAGE_LT60 >
  WARMUP`. The exclude SET is the union either way; only labels move.

## 2. Added exclusions (session-level): exactly ONE

| session | fold | v1 status | v2 class | panel | PDF evidence |
|---|---|---|---|---|---|
| **2015-07-02** | F2 | eval-eligible survivor (the v1 `NOT_RUN_BLOCKER`) | `HOLIDAY_PDF_EQUITY_2011_2015` | ESU5, 390 bars, coverage 1.0 (E2/CB_1615/T1) | `2015-4th-of-july-holiday-schedule.pdf` sha256 `2c8831c207c60a421d3d1ae283632b77959198de83a07d16db4b4bc713abbaeb`, EARLY_CLOSE 1215 CT — verbatim *"1215 CT / 1315 ET / 1715 UTC –Early close 1700 CT / 1800 ET / 2200 UTC –Regular open for trade date Monday, July 6\*"* |

This is the evidence-vs-data conflict that `holiday/exposure_proof_2011_2016.json`
named as the sole blocker; the owner-authorized repair resolves it in the
conservative direction (session EXCLUDED, never upgraded on a conflict).

**Added law dates with no panel session: 20** (CLOSED / full-RTH-halt days —
nothing to exclude, recorded `in_panel=false` exactly as v1 recorded
non-session `HOLIDAY_*` law dates): 2011-04-22, 2011-12-26, 2012-01-02,
2012-11-22, 2012-12-25, 2013-01-01, 2013-01-21, 2013-02-18, 2013-03-29,
2013-05-27, 2013-07-04, 2013-09-02, 2013-11-28, 2013-12-25, 2014-01-01,
2014-02-17, 2014-04-18, 2014-12-25, 2015-01-01, 2015-12-25. Each carries its
PDF file + sha + classification inside `exclude_list_v2.json` evidence blocks.

## 3. Removed exclusions: NONE

`removed_exclusions: []` — `critical_finding: false`. The v2 exclude set is a
strict SUPERSET of v1 (in-span entries AND out-of-span law dates compared).
Conservative direction verified by machine test.

## 4. Class relabels (same exclude set): 35 × `COVERAGE_LT60 → HOLIDAY_PDF_EQUITY_2011_2015`

These 35 in-panel candidate sessions were ALREADY excluded in v1 (truncated
RTH-core, coverage < 0.60); the new class (priority rank 2) now carries the
label, each with its PDF sha + verbatim quote embedded. The SET is unchanged
for them:

2011-01-17, 2011-02-21, 2011-05-30, 2011-07-04, 2011-09-05, 2011-11-24,
2011-11-25, 2012-01-16, 2012-02-20, 2012-04-06, 2012-05-28, 2012-07-03,
2012-07-04, 2012-09-03, 2012-11-23, 2012-12-24, 2013-07-03, 2013-11-29,
2013-12-24, 2014-05-26, 2014-07-03, 2014-07-04, 2014-09-01, 2014-11-27,
2014-11-28, 2014-12-24, 2015-01-19, 2015-02-16, 2015-04-03, 2015-05-25,
2015-07-03, 2015-09-07, 2015-11-26, 2015-11-27, 2015-12-24.

WARMUP sets are bit-identical v1 → v2 (4 × 252; the single added exclusion
sits after every fold-head warmup window end).

## 5. M2 exposure proof re-run (`repair/exposure_proof_v2.json`, sha `296c21a5ac13874370ac635059e74cb2c0e370dfc2e5d2247b4cf3a3fb76d4d0`) — verdict from machine rows

| sub-epoch | verdict | basis (machine rows) |
|---|---|---|
| **2011-2015** | **PASS** | zero sessions with unadjudicated holiday status inside the eval surface; the 2015-07-02 blocker row is GONE (now `HOLIDAY_PDF_EQUITY_2011_2015`); 2015-09-04 RESOLVED_REGULAR and stays included; no other conflict rows |
| **2016** | **FAIL_CLOSED_BASIS_PROVEN** | 258 in-panel sessions enumerated: candidate-named 2016-03-25 and 2016-12-26 are ABSENT from the panel (closures); 2016-11-25 is truncated (225 bars, 0.5769) and COVERAGE_LT60-excluded; ZERO ambiguous rows. Enumeration remains NOT_RUN (no per-day 2016 list is claimed); had an ambiguity existed, the class stays NOT_RUN with that named blocker. Evidence sources: cmecal year-2016 note days; readiness holiday json (windows 2017+, no 2016 window); cal_close FACT cells (2026-only). |

Overall verdict: **PASS** (zero blocker rows across both sub-epochs). Band
census unchanged: cov=0 → 4; 0<cov<0.60 → 40; [0.60,1.0) → **0** (band still
empty); cov=1.0 → 1491. Eval-eligible full sessions 2011-2016: 1084 → 1083
(−2015-07-02). 36/36 checks PASS.

## 6. Evaluation surface: 2,926 → 2,925

| fold | window | sessions | base excl old→new | surviving old→new | warmup | eval n old→new | eval first/last old→new |
|---|---|---|---|---|---|---|---|
| F1 | 2010-06-01..2012-12-31 | 665 | 38→38 | 627→627 | 2010-06-07..2011-06-09 (252) | **375→375** | 2011-06-10..2012-12-31 (unchanged) |
| F2 | 2013-01-01..2017-12-31 | 1276 | 74→**75** | 1202→**1201** | 2013-01-02..2014-01-16 (252) | **950→949** | 2014-01-17..2017-12-29 (unchanged bounds; 2015-07-02 removed from the middle) |
| F3 | 2018-01-01..2021-12-31 | 1035 | 72→72 | 963→963 | 2018-01-02..2019-01-17 (252) | **711→711** | 2019-01-18..2021-12-31 |
| F4 | 2022-01-01..2026-09-30 | 1227 | 85→85 | 1142→1142 | 2022-01-03..2023-01-17 (252) | **890→890** | 2023-01-18..2026-09-30 |
| **total** | | 4204 | | | 1008 | **2926→2925** | |

## 7. Counts old → new (every changed number explained)

Per reason class, in-panel sessions:

| class | old | new | why |
|---|---|---|---|
| FOMC_STATEMENT_DAY | 131 | 131 | unchanged |
| HOLIDAY_FACT_EARLYCLOSE | 10 | 10 | unchanged (2010+2026) |
| HOLIDAY_PDF_EQUITY_2011_2015 | 0 | **36** | 35 relabelled COVERAGE sessions + 2015-07-02 |
| HOLIDAY_UNCERTAIN | 60 | 60 | unchanged (2017-2025) |
| COVERAGE_LT60 | 69 | **34** | 35 candidate sessions relabelled (rank 2 beats rank 4) |
| WARMUP | 1008 | 1008 | identical sets |
| **in-panel total** | **1278** | **1279** | +2015-07-02 |

Chain-span entries / totals:

| metric | old | new | why |
|---|---|---|---|
| HOLIDAY_PDF_EQUITY_2011_2015 (chain span) | 0 | **56** | 36 in-panel + 20 non-session law dates |
| total_exclusion_entries | 1305 | **1326** | +1 session + 20 law dates |
| law_dates_with_no_panel_session | 19 | **39** | +20 non-session PDF candidate dates |
| law_dates_out_of_chain_span | 8 | 8 | unchanged |
| coverage margin | 0.5795 / 0.9641 | identical | data untouched (single-shot panel recompute 4204/4204 equal) |

## 8. Invariants (unchanged)

- **Identity table: 24** — `freeze/identity_table_24.json`
  `6e3919808ecea86d147ba67d8e5df4f4e83bed2414973f87de051054da6e471f`,
  embedded verbatim in `selection_freeze_v2.json`; P-A 8 + P-B 8 + FOMC 4 +
  C1-C4 4; the repair touches session membership only, never identities.
- **Budgets: 24** — trial budget frozen at 24 (ES cap 24 FROZEN); cost
  contract untouched (Variant A, owner D3 *"tôi chọn 2.25$"*,
  `D3_RECORDED` sha `f54610eb…` = freeze_pins_v2 pin).
- Session universe 4204 (2010-06-07..2026-10-01); pinned panel
  `7ae6de2d…` read-only single-shot; raw panel untouched; no quarantined
  PnL read or used; zero network.

## 9. What selection_freeze_v2 additionally carries (M4)

- `exclude_list` → v2 path + sha `67060c8c…` (supersedes v1, append-only).
- New law component **REPAIR-1 HOLIDAY_PDF_EQUITY_2011_2015** (the 7 v1
  PIT components embedded verbatim + this row): PDF evidence json sha +
  the 53 per-holiday PDF sha256 list + owner record sha.
- **PINS now LAW** (`owner_ratified_pins_law`): `auth/PREGO_REPAIR_RECORDED.json`
  sha `db0360fa…` + `pins/pin_decisions.json` sha `ef267c3a…`, the owner
  quotes verbatim, and the three pin definitions verbatim (D-A1 q80
  `numpy.percentile(..., 80)` LINEAR on the strict-past trailing-252d OVN
  tail; D-A2 C2 unconditional LONG; D-A3 C1 sign = +1 iff sha256 of the
  string `"FBES1-PLA-D0-S2|seed=20261002|"+session_date`, first byte
  `< 0x80`, else −1; seed 20261002 frozen).
- `pins_manifest`: base `freeze_pins_v2` (34 pins, sha
  `f7e1b580…`) **referenced, not re-pinned**; v2 delta pins add exactly:
  `exclude_list_v2.json`, `auth/PREGO_REPAIR_RECORDED.json`,
  `holiday/pdf_equity_evidence_2011_2015.json`. No self-hash.
- `not_run_register`: 8 carried items + 2016 enumeration NOT_RUN (explicitly
  unresolved) + ES-specific transcription NOT_RUN; RESOLVED by this repair:
  the 2011-2015 primary-tier candidate enumeration (exposure zero).

## 10. Boundary compliance

ONE bare `git rev-parse HEAD` at start + `git status --porcelain`
start/end; no other git; no commit/stage/push. Writes confined to
`research/control/FUTURES-ES-PB1-V1/repair/**` and
`dispatch/handoff_BUILDER-REPAIR.json`. Original gate-2 artifacts
(`freezegen/**`) never modified. Every consuming script performs a
single-shot panel read (builder + proof; the builder was re-run twice only
to verify bit-identical regeneration). Raw panel untouched; no quarantined
PnL read or used; root read-only; Python = root .venv; zero network; heavy
lock FREE_PROVEN recorded.

— End FREEZE_DIFF (FUTURES-ES-PB1-V1 / BUILDER-REPAIR).
