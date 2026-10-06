# FINDINGS STATUS — F-1..F-8 corrections round (r2)

Task: FUTURES-P3-QUARANTINE-20261004 | Cycle: UNREGISTERED_PREP | Lane: Q2-FIX-VERIFY
Generated: 2026-10-04T01:06:04Z UTC (session)
Findings source: `research/control/FUTURES-OVERNIGHT-PREP-20261003/verify2/findings.json` (SYNTH-VERIFY)
Law: append-only — **zero committed files edited**; every correction below supersedes its
stale statement BY REFERENCE. Originals remain verbatim as historical evidence.

## Status table

| ID | Sev | Lane | Defect (one line) | Correction artifact (this round) | Status |
|---|---|---|---|---|---|
| F-1 | LOW | P0A-FEESOURCE | outputs[] COMEX.php.txt digest declared 65 hex (extra 'e' at index 16) | `fixes/F1_SHA_CORRECTION.md` + `fixes/f1_sha_correction.json` — true digest `4317c15a187162aef9a80c76e63af372b7034a4157e0317b9b634237e798997a` | **CORRECTED_BY_R2** |
| F-2 | LOW | P0-VERIFY | "17/17 match" overbroad vs F-1 | Paragraph in `fixes/F1_SHA_CORRECTION.md` (cites both) — correct statement: 16/17 as declared, 17th matches after the F-1 typo fix; verdict UPHELD_IN_FULL unaffected | **CORRECTED_BY_R2** |
| F-3 | LOW | P2C-BLS-VINTAGE | outputs[] live_bls_ics digest single-char substitution (declared `…336c4bf030…`, actual `…334c4bf030…`) | Correct digest recorded in this doc, section F-3 below — recomputed from the artifact file this round | **CORRECTED_BY_R2** |
| F-4 | LOW | P2A-CALGAP-EQ | authority_claims non-empty (5 entries; evidence-provenance content, no authority grab — verifier classification) | `fixes/handoff_P2A-CALGAP-EQ-r2.json` — full schema copy, entries moved verbatim to known_limitations, authority_claims = [] | **CORRECTED_BY_R2** |
| F-5 | LOW | P2B-CALGAP-FXCOMM | authority_claims non-empty (6 entries; same nature as F-4) | `fixes/handoff_P2B-CALGAP-FXCOMM-r2.json` — same treatment | **CORRECTED_BY_R2** |
| F-6 | LOW | P2B-CALGAP-FXCOMM | outputs[] SHA256SUMS.txt declared placeholder, not a digest | Actual digest recorded in this doc, section F-6 below, and as an r2 note inside the P2B r2 handoff known_limitations | **CORRECTED_BY_R2** |
| F-7 | MEDIUM | P2B-CALGAP-FXCOMM | Gap-4 headline "43/45" not reproducible from the lane's own artifact (true grid 52/55 in-universe) | `fixes/F7_CORRECTION.md` + `fixes/f7_correction.json` — definitive recount, mechanism, supersession list | **CORRECTED_BY_R2** |
| F-8 | LOW | P1-ESNQ | outputs[] includes the handoff's own path with a declared "self-hash of the pre-final-save body" — inherently not recomputable after final save | Recorded as noted; **no action possible**: a pre-final-save self-hash can never be recomputed from any post-save artifact. Disclosed in-band by the original lane; 3 content outputs hash-match exactly | **KEPT_PARTIAL** (unfixable by nature; disclosure stands as the record) |

## F-3 — corrected digest

File (untouched): `research/control/FUTURES-OVERNIGHT-PREP-20261003/bls_vintage/captures/live_bls_ics_20261003_subset.txt` (16,555 bytes, 789 lines)

```
true sha256:
6612c5d492d99c8367ca9a42625cb87c3c96e723d2e3673334c4bf030ae1dcf6
```

P2C handoff declared `6612c5d492d99c8367ca9a42625cb87c3c96e723d2e3673336c4bf030ae1dcf6`
— single substitution at 0-based index 49: declared `6` where the file hashes to `4`
(declared fragment `…73336c4bf030…` vs actual `…73334c4bf030…`). Recomputed by this lane
2026-10-04 (`shasum -a 256`, exit 0); matches findings.json F-3 exactly. Handoff
transcription typo only; file and the other P2C outputs unaffected; all 6 dated-claim
spot checks of SYNTH-VERIFY stand.

## F-6 — actual digest recorded

File (untouched): `research/control/FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/fx_comm/captures/SHA256SUMS.txt` (13,393 bytes, 135 lines = 135 artifact hashes)

```
actual sha256:
17208199c6cc042057b1c94df1ffb6506c8ea9f0703c8ebf2002c17a1ebccc52
```

The original P2B outputs[] entry declared the placeholder "see file (135 artifact
hashes)". Digest recomputed by this lane 2026-10-04 (`shasum -a 256`, exit 0); identical
to SYNTH-VERIFY's recompute. The file is intact; its 135 listed artifact hashes remain
the lane's evidence. Also recorded as an r2 note inside `fixes/handoff_P2B-CALGAP-FXCOMM-r2.json` (outputs[] there kept verbatim per the r2 copy rule).

## F-8 — noted, no action

P1-ESNQ's outputs[] lists its own handoff path with a declared self-hash of the
pre-final-save body. Such a value is self-referential and cannot be recomputed from any
artifact that exists after the final save — there is nothing to correct it TO. The lane
disclosed the limitation in-band; its 3 content outputs hash-match exactly (SYNTH-VERIFY
clean_checks). Status KEPT_PARTIAL by nature, with this paragraph as the standing record.

## Updated lane verdicts (post-r2, honest accounting)

Mechanical defects in committed handoffs cannot be retroactively repaired — the
append-only law forbids editing them. Therefore each affected lane keeps its
SYNTH-VERIFY verdict **as committed (PARTIAL)**, and the r2 artifacts above supersede by
reference. "Effective" = what a downstream consumer should treat as current.

| Lane | Verdict as committed (SYNTH-VERIFY) | Findings | Effective post-r2 status |
|---|---|---|---|
| P0A-FEESOURCE | PARTIAL | F-1 | PARTIAL-as-committed; F-1 superseded by `fixes/F1_SHA_CORRECTION.md` (content itself VERIFIED) |
| P0B-FEEIMPACT | VERIFIED | — | VERIFIED (unchanged) |
| P0-VERIFY | VERIFIED | F-2 (wording only) | VERIFIED (unchanged); "17/17" statement corrected by reference in `fixes/F1_SHA_CORRECTION.md`; erratum verdict UPHELD_IN_FULL stands |
| P2A-CALGAP-EQ | PARTIAL | F-4 | PARTIAL-as-committed; `fixes/handoff_P2A-CALGAP-EQ-r2.json` is the compliant handoff of record (content VERIFIED) |
| P2B-CALGAP-FXCOMM | PARTIAL | F-5, F-6, F-7 | PARTIAL-as-committed; `fixes/handoff_P2B-CALGAP-FXCOMM-r2.json` + `fixes/F7_CORRECTION.md` supersede (content largely VERIFIED; gap-4 count now 52/55) |
| P2C-BLS-VINTAGE | PARTIAL | F-3 | PARTIAL-as-committed; F-3 digest corrected by reference in this doc (content VERIFIED) |
| P1-ESNQ | PARTIAL | F-8 | PARTIAL-as-committed and **remains PARTIAL** — F-8 unfixable by nature, disclosure stands (content VERIFIED) |
| P1-6E6B / P1-6J6A / P1-COMM / P1-CROSS | VERIFIED | — | VERIFIED (unchanged) |

No verdict anywhere is worsened by this round; F-7's correction moves measured gap-4
coverage UP (52/55 vs the stale 43/45 claim), conservative direction, no decision impact
(findings.json F-7 impact statement).

## Verifier reruns performed by this lane (all read-only; details in handoff tests[])

1. `fees_erratum/impact/validate_fee_sources.py --self-test` → **exit 0**, SELF-TEST
   PASS 6/6 (glue-detector behavior reproduced).
2. REAL mode: `validate_fee_sources.py <8 captures> --expected verify/p0_verify_expected.json`
   (no `--report` writer) → **exit 1 = EXPECTED-FAIL-BY-DESIGN**, 37/37 check verdict
   lines and final VERDICT byte-identical to the committed
   `verify/p0_verify_validator_stdout.log` (single-line delta: one capture-quality hint
   that names the report file in the original run vs the expected file here — affects no
   check). P0-VERIFY's recorded result reproduces.
3. `cme_cal_gap/fx_comm/build_coverage.py` sandbox rerun (temp dir, `captures/`
   symlinked read-only) → **exit 0**; regenerated `fxcomm_gapfill_coverage.json`
   **byte-identical** to the committed artifact (sha256 `91c0f0d9…f2d89e9`); stdout
   computed gap-4 counts 11/11/11/9/10 = 52 — proving the "43/45" headline is a
   hardcoded literal never derived from the cells (core F-7 evidence).
4. sha256 recomputes for the F-1/F-3/F-6 dispute targets (`shasum -a 256`, exit 0 each)
   — all three match findings.json exactly.
5. Gap-4 cell recount from the committed coverage JSON (read-only script) → exit 0;
   52 OBTAINED / 55 in-universe / 60 raw, matching SYNTH-VERIFY.

`verify2/` contains no runnable scripts (findings.json only); no other verifier scripts
in the round are safely rerunnable read-only (fetchers need network; extractors write
into committed paths).
