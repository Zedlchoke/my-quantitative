# DONOR_LAW_CARRYOVER — correction of record (append-only)

- Trigger: D-V2-1 (DRYRUN-V2 CRITICAL, caught by gate 4 exactly as
  designed): the v1 machinery computed SL-donor exclusions from class
  LABELS; the repair's 35 COVERAGE_LT60→HOLIDAY_PDF_EQUITY relabels
  (exclude set unchanged) silently re-admitted them as donors (139→104),
  changing SL distances on 244 eval dates / 177 exits.
- **Correction law (effective for this cycle's machinery)**: the
  SL-donor exclusion SESSION SET is the v1 set (139 sessions), evaluated
  on the v1 class labels; exclusion-list relabeling is evidentiary
  metadata for EVAL membership only and can never alter donor
  statistics. 2015-07-02 was not donor-excluded in v1 and stays
  donor-admitted (the repair changes eval membership only).
- Basis: conservative intent of the owner's repair authorization
  (verbatim "okay lên lệnh cho agent trong zcode đi" after the
  conservative-holiday proposal; recorded auth/PREGO_REPAIR_RECORDED).
  This restores frozen v1 behavior under relabeling — NOT a new design
  choice; any future owner preference for PDF-admitted donors is a new
  amendment with its own gate re-runs.
- Verification: DRYRUN-V2-1 PASS (a)-(e); donor-excluded == 139
  asserted; delta vs v1 quarantine = exactly the 3 trades dated
  2015-07-02; 13,185 common trades byte-identical, 0 SL-distance diffs;
  determinism sha eaae8b6b…; zero warmup violations.
- Machinery of record for gate 6: dryrun_v2_1/dryrun_builder_v2_1.py
  (v1 logic + 2 v2 shims + this one donor-set correction; all diffs
  documented in DRYRUN_V2_1_REPORT.md).

— End DONOR_LAW_CARRYOVER.
