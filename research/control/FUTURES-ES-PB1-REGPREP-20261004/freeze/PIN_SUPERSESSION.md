# PIN_SUPERSESSION — correction of record for the freeze pin chain (append-only)

- Trigger: owner-side audit at final HEAD `1bcf07cc` found the
  FREEZE-AUDIT-era pins stale for exactly the two files the controller
  corrected AFTER the freeze-audit lane measured: (1)
  `freeze/freeze_pins.json` pins `auth/D3_RECORDED.json` at
  `99661246…` while the committed file was `97bf1ad3…` (F-V1 wave); (2)
  `dispatch/handoff_FREEZE-AUDIT.json` outputs[] pins
  `freeze/cost_freeze_check.json` at `d6b9be83…` while the committed
  file was `53e7e016…` (F-V2 wave). The "34/34 pins" claim was true at
  lane time, NOT at final HEAD — the owner's finding stands.
- Remedy (append-only, no history rewritten):
  1. `freeze/freeze_pins_v2.json` is now the **AUTHORITATIVE pin
     manifest** for the registration freeze: all **34 artifacts re-hashed
     at the corrected final state; 33/34 identical to v1; exactly 1
     delta** (`auth/D3_RECORDED.json`, decision content byte-verified
     unchanged — only the sufficiency wording + corrections log moved).
  2. `freeze/freeze_pins.json` (v1) and `handoff_FREEZE-AUDIT.json`
     stand as the lane's **historical lane-time measurement**; their
     stale pins are documented in v2's `handoff_output_pin_supersession`
     block, not edited.
  3. `auth/D3_RECORDED.json` `_corrections_log` records the full sha
     chain `99661246 → 97bf1ad3 → final-state (pinned by v2)`.
- **No self-referential hash loop (by construction)**: v2 hashes only
  the 34 freeze artifacts; it does not hash itself, the registration
  packet, or verifier outputs. The packet references v2
  (one-directional). No file in the chain hashes a file that hashes it.
- F-V1 completion: `D3_RECORDED.sufficiency_conclusion` now scopes
  e.1 FX / e.2 geography / e.3 NYMEX precisely (original string
  preserved in `_superseded_sufficiency_conclusion_1bcf07cc`); the
  registration packet header and REPORT_VI carry the same precise
  scoping (their blanket "FX/NYMEX-scoped" labels are corrected in this
  same wave).
- Protocol fix going forward (the root cause): **no bytes may change
  after a verifier measures without a fresh verifier pass at the new
  committed SHA**; the final verification of this wave runs at the
  committed SHA, and the commit of verifier outputs is followed by a
  read-only pin-stability rerun documented in the round report.

— End PIN_SUPERSESSION.
