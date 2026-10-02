# SKEPTIC_REVIEW_V2 — fresh-context audit of the REVISED packet (2026-10-02)

Independent fresh-context skeptic (read-only; script re-run in /tmp; packet
files untouched) audited the post-ERRATUM_V2 packet in two layers: (1)
every ERRATUM_V2 fix-claim recomputed against the revised files; (2) an
adversarial pass over the full protocol/design for NEW defects. Verdict
relay below; all findings dispositioned before commit.

## Layer 1 — all five fix-claims VERIFIED

1. **BUDGET** — §6 both options recomputed from scratch: Option A committed
   33 identities / 192 scored rows / 204 total, max 36/210/222; Option B
   27/156/168 with HN-5 (25/144/156 without), max 30/174/186 (28/162/174
   without); caps ≥ maxima (40≥36, 240≥222; 32≥30, 204≥186); B0 = 1 id/0
   rows; crossed 2 ids/12 rows; HN-5 2/12; J3 grid 3 LEARN rows (grid 12);
   contingency 3/18; C2-outside alternative reproduces at 186/150. The
   lane-correction note verified consistent (27/156 is the table-consistent
   number). v1's committed §6 pulled from git `b707e0c0` and confirmed to
   match the erratum's characterization (29 ids / ≤140-row cap).
2. **CALENDAR** — script re-run in /tmp; committed `calendar_variants.json`
   byte-identical to the fresh run; protocol §1.3 matches exactly (A fold-1
   2026-10-02 → end 2029-09-27/28; A_emb → 2029-10-03/04; B LEARN
   2026-10-02→2027-04-01, fold-1 2027-04-08 → end 2030-04-03/04). A′
   withdrawal language only; standing owner directive quoted verbatim and
   A/A_emb conditional in D-1; stage law has A7 (stage 6) and GO (stage 7)
   after registration; nothing recommends consuming the sealed tail.
3. **SELECTION** — protocol §3.2 diagnostics-never-selectors; §3.3 deleted
   mid-cycle-edit sentence; §3.4 LEARN-undecidability arithmetic reproduced
   (S014 3.0–5.6, S017 3.5–7.5 on 26–40w vs floors ≥20/≥50; Poisson
   P(n<3)≈0.30/fold); register A-H4/HN-3/B-H-G1/B-H-E3 all
   frozen-at-registration + diagnostic-only.
4. **CLAIMS** — design law scoped to the measured set in English files;
   HN-1 carries POST_OUTCOME + DST-derived session marks + placebo;
   hard risk caps present as an independent frozen risk law (§4).
5. **COSTS** — component-wise law consistent across design §0-4, protocol
   D-2, Vietnamese §4-2; no absolute-blocker phrasing; "after-cost PASS"/"
   measured edge" appear only inside negations.

## Layer 2 — defects found → ALL FIXED before commit

| # | defect | fix |
|---|---|---|
| D1 | `SKEPTIC_REVIEW_V2.md` referenced but did not exist at audit time (premature past-tense verification claim) | this file now exists and records the audit; the sequence is disclosed here rather than papered over |
| D2 | Vietnamese report line 34 re-asserted the unscoped class claim | scoped: "giới hạn trong tập cơ chế ĐÃ ĐO trên lịch này" |
| D3 | Vietnamese report line 83 retained selector language for S014 ("để arm leave-one-leg quyết"); line 81 dropped the owner-election framing | rewritten: membership by owner decision at registration; LOL arm is diagnostic for the NEXT cycle |
| D4 | Cyrillic corruption "портfolio" in the Vietnamese report | replaced with "portfolio" |
| D5 | Register cross-refs pointed to "HN-4" (reserved placeholder) instead of the HN-1 family | both occurrences re-pointed to HN-1 (instance HN-1-EUR) |
| D6 | Register Part 3 said "LORO×LORO" — dropped the mandatory LOL pairing for A-H1 | corrected to "crossed LORO×LOL arms live" |
| D7 | Register Part 3 row re-asserted class-level refutation | corrected to "(measured set, this calendar)" |
| D8 | B-H-E3 re-entry vehicle named "amendment" (v1 vocabulary) | corrected to "registration of a NEW cycle (amendments clarify execution law only)" |

Non-defect observations recorded: JSON key `A_embargoed_1w` vs protocol's
`A_emb` (identical values, mapping stated); `HANDOFF.json` added to the
header file table after the audit flagged its absence.

## Bottom line (reviewer's, relayed)

"Yes — the packet is reviewable and internally consistent in everything
load-bearing. All five ERRATUM_V2 fix claims verify … budget, calendar,
selection-law, claim-scoping and cost-law arithmetic all reproduce exactly
(committed calendar JSON byte-identical to a fresh script run; §6 tables
recomputed to the row). The remaining defects are textual and localized" —
all eight were fixed pre-commit (table above). No number, date, or law
changed by these fixes.

— end record v2 —
