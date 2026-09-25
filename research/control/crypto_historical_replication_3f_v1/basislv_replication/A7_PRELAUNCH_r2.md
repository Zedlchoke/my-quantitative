# A7 prelaunch round 2 (delta) — BASISLV replication — AUTHORIZED

Cycle `CRYPTO-HISTORICAL-REPLICATION-3F-V1` / stage `BASISLV`
Artifact: `basislv_replication/A7_PRELAUNCH.json` (schema `chr3f_a7_prelaunch@1`, round 2)
Audit UTC: 2026-09-25T02:33:37Z · Head: `5dfb17761e1fdfa7e8601c86b0557e0fdc77724e`
Branch: `orca/crypto-historical-replication-3f-v1-integration`
Prior: r1 REFUSED (`9405ab3a`), one blocking finding **B1**.

## Verdict: AUTHORIZED

B1 remediation is in bytes, the dry-run reproduces it, and there are no
regressions. The scored sweep is authorized for exactly the 8 cells
`CHR3F-BASISLV-{Y2021,Y2022,Y2023,Y2020P}x{ANCHOR,INV}` as scoped in the JSON
artifact. Blocking findings: none.

## B1 remediation — verified

1. **Fold-4 swap in bytes (R1, PASS).** The remediation commit's
   `replication_data.py` diff is exactly the swap: the `Y2024P
   2024-01-01..2024-08-19` pin replaced by the census-evidence comment +
   `("Y2020P", "2020-11-16T00:00:00Z", "2021-01-01T00:00:00Z")` — verbatim
   plan §3's BASISLV Y2020P row and the outcome of plan §6's deterministic law
   (census PASSES → Y2020P). Census evidence is recorded in four places: the
   FOLDS comment, `dryrun_report.json` folds.Y2020P, commit message `5dfb1776`,
   and the A7 r1 H1 / r2 R3 measurements. No owner override needed.
2. **Dry-run delta surgical (R2, PASS).** r1 vs r2 report diff: `Y2024P`
   section removed, `Y2020P` added; Y2021 49/0/2 @12, Y2022 49/0/2 @12,
   Y2023 46/4/2 @0..15 and **all** data-loading sections are byte-identical to
   r1. Y2020P: 6 scheduled Mondays (11-16 start edge excluded), 5 open stamps,
   3 OK / 0 INSUFFICIENT / 2 FORCE_FLAT, eligible 12..12, non-vacuous, 0 errors.
3. **Independent reproduction (R3, PASS).** Fresh sanitized traversal through
   the real plugin surface reproduced the report and my r1 census
   stamp-for-stamp: OK @ n_eligible=12 (11-23, 12-07, 12-21, 8 weights,
   7 refused = exactly the 7 not-yet-listed names), FORCE_FLAT at 11-30/12-14.
4. **Single-sourced fold set (R4, PASS).** `replication_scored.py:115` imports
   `ARMS, FOLDS` from `replication_data`; the cell runner takes fold/window via
   CLI only. No duplicated fold pin in executable code.

## No regressions

- **R5:** every executable lane file except `replication_data.py` is
  byte-identical to the r1-audited head — r1's A1/A2/B2/B3/C1/E3 conclusions
  carry over. Remap expression re-diffed vs the proven equivalence runner:
  identical (`snap(ts)+15m`, duplicate-boundary refusal, i128 decode).
- **R6:** banned-token scan of the regenerated report: 0 banned fields (only
  the literal `no_pnl` key and a numeric substring coincidence).
- **R7:** 3 labels per row (code unchanged); `scored_out/` and
  `scored_status.json` do not exist — the sweep has never run; the launcher
  gate is armed on this artifact.
- **R8:** budget 12 distinct rc=0 cells on disk (8 XSECT + 4 ILLIQ) + 8
  planned = 20 ≤ 24.
- **R9:** 0 S1/credential/network refs; `CHR3F-BASISLV` exists in no cell row
  anywhere; heavy lock FREE_PROVEN before/after; this audit wrote only
  `A7_PRELAUNCH.json` + `A7_PRELAUNCH_r2.md`.
- **R10:** Y2020P feasibility from raw bytes: all 12 eligible names' basis
  origins precede the 28d warmup need (tightest: AAVE 2020-10-16 vs need
  2020-10-26); AAVE basis first open 2020-10-16T07:00Z, ADA 2020-06-01T00:00Z;
  AAVE/ADA bars cover the fold on the complete 15m grid (4842 slots, no
  interior holes).

## Non-blocking findings (must be fixed at the next commit; none gate the launch)

- **N1r2 (false remediation claim).** Dispatch item 4 and commit `5dfb1776`'s
  message claim the 03:45Z→03:45Z mislabel was fixed. It was **not**: every
  ISO-text occurrence still says `2023-11-10T03:45Z` for bucket `1699587900000`
  (actual `2023-11-10T03:45:00Z`) — `replication_data.py:15`,
  `basis_convert.py:34/:203` (+ `basis_convert_report.json` grid_gap_policy),
  `replication_scored.py:39/:41`, `IMPLEMENT_HANDOFF.json:38/:65`. Machine
  values were always correct and nothing consumes the ISO string, so this
  stays non-blocking (it was r1 N1), but the commit-message claim itself is
  now inaccurate and must not propagate into terminal reporting.
- **N6 (stale docstrings).** `replication_scored.py:5` and `dryrun.py:7` still
  enumerate `{Y2021,Y2022,Y2023,Y2024P}` in non-executable text; execution is
  single-sourced on `replication_data.FOLDS` (now Y2020P).
- **N2 (carried).** Registry numeric budget fields still stale vs the
  artifact-derived 12; owner reconciliation before terminal close.
- **N3r2 (updated).** Y2020P fold thirds carry 2 decision stamps each
  (F1/F2/F3 = 2/2/2, purge 0) — far below the frozen
  MIN_DECISIONS_PER_FOLD=15 constant, which the scored runner does not enforce;
  disclose in the Y2020P cell report. (Supersedes r1 N3's Y2024P note.)
- **N4/N5 (carried).** Y2023's 4 INSUFFICIENT stamps admissible (disclosure
  required at reporting); D2/D3 admissible — unchanged bytes.

## Authorization scope (binding)

8 cells `CHR3F-BASISLV-{fold}-{arm}`, folds/windows verbatim
`replication_data.FOLDS`, arms `BASISLV-PREMFADE-28D` / `...-INV`, heavy lock
(role scored-cells), cycle-local `scored_out/` + `scored_status.json`, three
labels per row. Any deviation voids this authorization and requires A7 round 3.

## Method note

Round 2 is a delta re-audit; every claim recomputed from bytes (git diff
`9405ab3a..5dfb1776`, structural report diff, raw parquet reads, one fresh
sanitized Y2020P traversal — lock-free, no scored compute). The scored
launcher was not executed this round.
