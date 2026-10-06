# F-1 Correction: P0A declared sha256 for COMEX.php.txt (65-hex typo)

Task: FUTURES-P3-QUARANTINE-20261004 | Cycle: UNREGISTERED_PREP | Lane: Q2-FIX-VERIFY
Generated: 2026-10-04T01:06:04Z UTC
Correction class: append-only r2 (supersedes BY REFERENCE; zero committed files edited).
Corrects: SYNTH-VERIFY finding F-1 (LOW), lane P0A-FEESOURCE.

## Correct digest (recomputed by this lane, 2026-10-04)

File (untouched): `research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/COMEX.php.txt`
(3,793 bytes, 63 lines)

```
true sha256 (64 hex):
4317c15a187162aef9a80c76e63af372b7034a4157e0317b9b634237e798997a
```

## Defect detail

- P0A handoff (`dispatch/handoff_P0A-FEESOURCE.json` outputs[]) declared:
  `4317c15a187162aeef9a80c76e63af372b7034a4157e0317b9b634237e798997a`
  — **65 hex chars**, i.e. the true digest with one extra `e` inserted at 0-based
  index 16 (declared `…7162ae` + `ef9a80…` vs actual `…7162ae` + `f9a80…`).
  First divergent character: index 16 (`e` declared vs `f` actual); from index 17 the
  declared string is the actual string shifted right by one.
- Nature: transcription typo in the handoff only. File content unaffected; the other
  13 P0A output digests were hash-identical per SYNTH-VERIFY and were not re-derived here
  beyond the three dispute targets of F-1/F-3/F-6.
- Impact unchanged from findings.json: mechanical integrity of the handoff outputs[]
  only; no evidence or conclusion affected (P0-VERIFY independently re-extracted every
  load-bearing cell from the captures).

The committed handoff stays verbatim; the digest above is the authority for any consumer
recomputing this output's hash.

## F-2 (same doc, cited together): P0-VERIFY's "17/17 match" was overbroad

P0-VERIFY's test T1 verdict ("sha256 recomputed for all 17 P0A/P0B outputs: 17/17 match
handoffs") cannot be literally true as worded: F-1's declared COMEX.php.txt digest is 65
characters and therefore cannot have matched `shasum -a 256` output byte-for-byte. The
correct statement is **16/17 match as declared; the 17th matches only after correcting
the F-1 insertion typo** (the underlying file is intact — P0-VERIFY's own source
re-extraction and the validator rerun by this lane confirm the content is exactly what
P0-VERIFY adjudicated). This is a statement-precision defect in a verification claim;
the erratum verdict itself (UPHELD_IN_FULL) is unaffected and stands. Both F-1 and F-2
are hereby corrected by this single reference.

## Reproduction

```
shasum -a 256 research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/COMEX.php.txt
# -> 4317c15a187162aef9a80c76e63af372b7034a4157e0317b9b634237e798997a   (exit 0)
```
