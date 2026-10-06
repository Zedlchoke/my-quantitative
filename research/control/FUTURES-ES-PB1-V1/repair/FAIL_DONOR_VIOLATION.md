# FAIL RECORD D-V2-2 — builder v2.1 donor law VIOLATES frozen SPEC §4 (correction of record, append-only)

- **Verdict of the current state (before any fix): FAIL.**
- Frozen law (SPEC_PB1_ES.md L87-89, ERRATUM A7-SPEC-M5): "SL = 1.0 ×
  median của 20 range RTH session liền trước (strict past; close marks
  era-correct; **loại session short/flagged**)" — donor exclusion is by
  FLAGGED STATUS, not by a fixed historical label list or a historical
  session set.
- Violations found (owner-side follow-up audit 2026-10-04, confirmed
  from bytes):
  1. **Builder v2.1** (DONOR_LAW_CARRYOVER.md, donor-set ≡ v1's 139)
     keeps **2015-07-02 donor-admitted** although freeze v2 flags it
     HOLIDAY_PDF_EQUITY_2011_2015 — a flagged session ⇒ must be
     donor-excluded. The "carryover v1 set" correction enforced
     conservatism vs v2's label bug but violated the SPEC's
     flag-based law for the NEW class.
  2. **Builder v2 (label-based 3-class list)** donor-admitted the 35
     relabeled flagged sessions (139→104) — same violation class.
- Root cause: two different law sources were conflated — the v1 CODE's
  hardcoded class list (implementation) vs the SPEC's flag-based law
  (authority). The authority text wins; both prior states FAIL it.
- Correction law (per frozen SPEC, NOT chosen to preserve any prior
  output): donor-excluded = every session flagged short OR bearing ANY
  exclusion/flag class in the CURRENT freeze (v2→v3), evaluated on the
  current freeze's flags. Expected set at freeze v2: 139 + 2015-07-02 =
  140 (to be machine-derived, not asserted).
- Impact discipline: SL distances and trade paths WILL change on
  affected dates; quarantined rehearsal outputs of ALL prior states
  stand as history; NO choice may be justified by keeping/restoring any
  prior PnL path. The corrected dry-run is the machinery of record.
- Consequence: gates 3-4 must re-run after the correction + the 2016
  fail-closed repair (separate finding, same wave) land.

— End FAIL record. The previous ALL_PRE_GO_CONDITIONS_PASS verdict is
WITHDRAWN pending the corrected gates' verification.
