# A7 Independent Prelaunch — ILLIQ-AMIHUD-28D-W scored cells (CHR3F)

**Verdict: AUTHORIZED** — no blocking findings. 20/20 checks PASS.
Audit UTC 2026-09-24T01:29:40Z. Lane head `ab76aba2`; root HEAD `eb6e162b` (unchanged
during audit). Artifact: `a7_prelaunch_illiq.json` (schema `chr3f_a7_prelaunch@1`).
This artifact lands BEFORE the first ILLIQ scored cell; the launcher
`illiq_scored.py` self-gates on exactly this file (rc=5 REFUSED unless
`verdict == "AUTHORIZED"`).

Subject: 8 cells = {Y2021, Y2022, Y2023, Y2024P} x {anchor ILLIQ-AMIHUD-28D-W,
INV ILLIQ-AMIHUD-28D-W-INV} under A2 (launch authority) + A3
(EQUIVALENCE_DATA_RESTAGE_UNPROVEN admission).

## What was independently recomputed (not trusted)

1. **A3 + equivalence FAIL characterization.** A3 exists at ROOT bootstrap,
   committed `fb1ac98c`. Every quoted number verified from
   `illiq_equivalence_out/equivalence_payload.json` vs the baseline anchor
   (`recovered/v11_root/baseline_wave2.json` W2-1): net 0.713248156397 vs
   0.581969254868 (rel 0.2255), PF 1.462307048803 vs 1.3548410108404612,
   MDD 0.086796257225 vs 0.091821657373, positions 328 vs 336, funding
   +0.11085867408, hit-rate 24/52 exact. F1 fold PF 1.0645 vs 1.0831 = 1.72%
   ("matches to 2%" accurate). The tick-hypothesis run IS the committed
   constant-1e-07 equivalence run; its payload still misses the baseline, so
   "ticks are NOT the driver" is genuinely rejected by bytes. The FAIL is
   disclosed as FAILED, not minimised. (Caveat N1: the run's own verdict JSON
   shows `got:null` — harness surface key-name mismatch, numbers were read
   from the payload; substance unaffected.)
2. **Engine frozen.** All 4 files under `research/v11/families/illiq_amihud/`
   byte-identical (cmp) to commit `c97283e0`. M0 rerun fresh: **16/16 PASS**
   (23.91s).
3. **Subclass derivation.** `chr3f_illiq_plugin.py` overrides only the
   fold-partitioning surface; `targets_at` is semantically identical to the
   frozen body except the fold lookup; force-flat (incl. final-instant
   carve-out) preserved; `compute_stamp_features`/`build_quintile_book` are
   the frozen module's code called verbatim; everything else inherited.
4. **Census.** A7 reran Y2024P (committed script, unchanged) and Y2021
   (independent /tmp variant): both reproduce the verdicts EXACTLY
   (33/30/3 skips; 52/38/14 skips, identical skip dates and weight heads).
   Y2022/Y2023/Y2020P verified on structure (force-flat signatures, quintile
   widths consistent with era listings).
5. **Fold law.** Y2020P census 5/9 fails the plan §3 "EVERY scheduled stamp"
   condition under EITHER reading of engine skips → fold-4 = Y2024P is
   interpretation-invariant and faithful to plan §6's deterministic fallback.
   Not a stretch.
6. **Data authority.** 2 kline zips: local sha256 == local `.CHECKSUM` ==
   LIVE binance.vision HEAD (fetched during this audit). Funding B bundles
   (BTC/SOL/ZEC): row content byte-equal to staging (4534/4385/4534), with
   the r2 `requested_start_ms/end_ms` metadata; coverage spans all 4 windows.
   b20 catalog ADAUSDT rows_written 160,768 == A7 recount of zip data lines
   (header-semantics exact; 24 of 56 months are headerless).
7. **Invocation.** Self-gate on this artifact; windows verbatim plan §3 (no
   overlap with the forbidden band); both arms in the frozen ARMS registry;
   `EQUIVALENCE_DATA_RESTAGE_UNPROVEN` + `REPLICATION_NOT_PROSPECTIVE` on
   every row; outputs strictly cycle-local; heavy lock held for the sweep
   (FREE at audit); budget 8 (XSECT rc=0) + 8 (ILLIQ) = 16 ≤ 24 cap.
8. **Boundaries/denominators.** Root registry touched only by disclosed
   commits; all lane commits scoped to the cycle control dir; sandbox/shadow/
   gateway surfaces untouched by CHR3F; no credentials; `illiq_scored_status.json`
   and `illiq_scored_out/` ABSENT → 0 ILLIQ cells run.

## Non-blocking findings (7)

- **N1** equivalence verdict JSON `got:null` (harness key mismatch; numbers
  verified from payload — fix the surface keys next run).
- **N2** committed census script covers only Y2024P; 4-window generating
  invocation not preserved as a version (mitigated by A7 reruns of 2 windows).
- **N3** scored tick table = constant 1e-07 (disclosed A3 hypothesis, not the
  lost original table) — must travel with every ILLIQ report line.
- **N4** registry budget field stale at 0/24; post-sweep update must book 16/24.
- **N5** B funding bundle ends exactly at the 2024-08-20T00:00Z boundary row;
  not exercised by any Y2024P holding, but mention in the provenance note.
- **N6** payload identities carry the frozen historical window strings by
  design; ILLIQ reports must state fold windows explicitly per line.
- **N7** ILLIQ's A2 gate-2 is satisfied via census traversal + equivalence
  traversal per A3's owner enumeration (no XSECT-DR2-style synthetic run) —
  recorded as the amended gate definition, disclosed in A3.

## Consequence

The 8 ILLIQ scored cells may launch now under A2+A3, heavy lock, cycle-local
outputs, and the registered labels. Every ILLIQ result must be read as "the
frozen mechanism on best-effort restaged data", NOT as the historical family's
exact-identity numbers; the label-upgrade path (archive restoration) re-opens
the equivalence gate per A3.
