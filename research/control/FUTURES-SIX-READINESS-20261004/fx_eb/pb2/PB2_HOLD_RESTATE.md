# PB2 HOLD RESTATE — FX-EB-CALENDAR lane (FUTURES-SIX-READINESS-20261004)

Status: **PB2 remains HOLD by Co-Owner ruling. This lane does NOT reopen it and
adds NO new verdict text.** This file is a pointer restate only, written because
this lane closed calendar cells (expiry + holiday) that the PB2 court draft
lists as its dependency #1 — the closure changes the dependency's STATUS, not
the court's verdict.

## Pointers (no content reproduced beyond status)

1. **The court draft (authority for what PB2 is):**
   `research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/6e_6b/PB2_ANCESTRY_COURT_DRAFT.md`
   (sha256 `e358e2ce8d85ab7d3917725ad779ec289f51946c9f74fad42d3cbea1c32de57f`).
   §d "renders NO reopening verdict"; dependency table row 1 = "FX official
   holiday calendar 6E/6B (calendar-uncertainty => EXCLUDE must become
   evidence-based)" — owner: lane A2-CMECAL-FX, status at draft time NOT_RUN.
2. **P3-quarantine round matrix rows:** sibling round
   `FUTURES-P3-QUARANTINE-20261004` (read-only evidence at
   `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/...`),
   Q5-CAL-PERMITTED target 2 (FX expiries 2023-2025: 6E 12/12, 6B 0/12) and its
   `verify/findings_final.json` VF-12 (endpoint-provenance disclosure, owner
   decision D1 context). Values from P3-LANE quarantine/ captures remain
   FORBIDDEN evidence until the D1 owner ruling.
3. **Standing rulings unchanged:** PLAYBOOKS_DRAFT r5 §2 Co-Owner HOLD ("ho
   London-session tren FX spot da chet; ban futures nay chua chung minh khac ho");
   NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER; FX-F1 census is contingency only
   (`hypo/6e_6b/fx_hypotheses.json`, pb2_status field).

## What this lane changed (dependency-status only, not verdict)

- Dependency #1 (FX official holiday calendar 6E/6B): 6E side now has
  34/42 archived windows with deviation grids + 8 aged-out inconclusive
  (`../holiday/holiday_deviation_6e_6b.json`); **6B side remains 0 — NOT_OBTAINED
  with documented absence** (product id 42 in no archived by-product capture).
  Expiry close 2023-2026: 6E 14/16, 6B 10/16 (`../calendar/fx_eb_expiry_2023_2026.json`).
- Dependency #2 (exchange fee table) unchanged: MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN /
  UNDER REVIEW until owner-authorized A7; A7 packet READY-not-run.
- All other court dependencies (trigger census, per-pair dead-family books,
  placebo budget ruling, BBO) unchanged NOT_RUN.

**PB2 verdict state: HOLD — unchanged. Reopening remains the Co-Owner's alone.**
