# A7 PRELAUNCH AUDIT — STOCKS-FREE-V9 (one-pager)

Artifact: `a7_prelaunch_v9.json` (schema `stocks_free_v9_run/a7_prelaunch@1`)
Auditor: A7, fresh context, independent of A1. Audit-to-refute; nothing repaired, nothing committed.
Audited HEAD: `17e70ac` (V9 Q: V9-R1 + DRY_RUN_PASS_NONVACUOUS), branch `orca/stocks-free-v9-integration`, tree clean.

## Verdict

**STOCKS_FREE_V9_S0_LAUNCH_AUTHORIZED** — 9/9 items PASS, 0 blockers, 6 LOW findings (none can change a verdict-relevant number).

## Item results

| # | Item | Verdict | Decisive evidence |
|---|------|---------|-------------------|
| 1 | Freeze chain & ancestry | PASS | 13/13 chain SHAs ancestor-ordered into `17e70ac`; tree clean; 6/6 proposal byte-hashes match `d1_proposal_hashes`; selection packet sha `3402961b…` == file bytes; lane-commit blobs byte-match pins despite cherry-pick integration |
| 2 | Selection integrity | PASS | 1 family (SFV9-A4-H2) x 3 arms, budget 3/6; all 5 blocks carry measured D2 numbers; line-by-line packet-vs-runner diff found **zero divergence** (formulas, 330–400 guard, 800d at each gate, warmup 4/0/0 fold-1, legs, terciles, band table, gate table, folds, dead-name semantics) |
| 3 | Data authority PIT | PASS | Panel re-hash `67591464…` exact; V8 panel re-hash `1cb115d3…` exact; V8 file is a **byte-exact prefix** of V9 (cmp, 0 diffs; row delta 6,255,911 == p0c); 2190-file price manifest, 25/25 spot rehash; delisted cache full-sha match `bd7d969c…`; scan 1550/219/0 consistent (universe 410+1550=1960); p0a/p0b raw manifest samples all match |
| 4 | Kernel & accounting | PASS | L-I3 hard-fail present; V9-R1 exit path = C-ceiling(25)x mult for UNTRADABLE/missing, own band otherwise; entries strictly disjoint; costs linear, once per fill; F-A7T-1 counters driver-emitted (3/0), no publish-edit path; **two-key sandbox: all 3 refusal combos exit 1 and write nothing**; control dir hash-snapshot unchanged; targeted tests 41/41 |
| 5 | Dry-run hygiene | PASS | Independent leak scan: zero outcome values (one benign negated "no PnL computed" in producer_role); my re-run is byte-identical to the committed artifact after patching only the 4 by-design `code_freeze_sha` provenance fields (committed embeds `573d71c`, run pre-commit of `17e70ac`); floor 0.762931 / 75 decisions / min-fold 22 / min-legs 199 all reproduce |
| 6 | S1 & boundaries | PASS | S1 only ever SEALED/locked/not-authorized; zero V9 raw bytes tracked (gitignore 34/36); branch has **no remote ref** (never pushed); live key value in **0** tracked files |
| 7 | Denominator seed | PASS | state.json v9 0/0, budget 0/6 seed; selection commits 3/6; carries stocks 27/27 and program 182/185 prior (LOW: phase labels stale, counters correct) |
| 8 | Input assumptions | PASS | Load-bearing inputs are all staged, hash-pinned bytes. EODHD subscription at scored time NOT load-bearing (driver is offline; staged bytes only). Symbol join / SIC map / form labels = DERIVED with declared rules + per-member ±120d price-death validation; residual mis-join risk recorded, non-blocking |
| 9 | V9-R1 delta | PASS | Minimal (+24/+12/+1 test), conservative-direction (unrateable exits: crash/cheap → C-ceiling; cannot create survivors), tested, byte-invariant on real data. **No separate re-freeze needed** — it is inside the audited HEAD, pre-scored, preregistered-direction, recorded in `q_dryrun_evidence_v9.json` |

## Findings for A1 to record (all LOW, non-blocking)

- **A7-L1** Cross-HEAD dry-run identity requires patching the 4 `code_freeze_sha` provenance fields; record the recipe.
- **A7-L2** `producer_role` contains negated token "PnL"; reword or record standing exception.
- **A7-L3** `state.json` (P0B) and `heartbeat.json` (I_IMPLEMENTATION) phase labels stale; refresh at E open.
- **A7-L4** Equal-|w| L→S reversal of a decayed-band held name crashes fail-closed (BandResolutionError) — sanctioned safe-stop, optional hardening.
- **A7-L5** `d1_proposal_hashes.lane_commits` point to non-ancestral lane heads; closed by byte-identity of pinned blobs.
- **A7-L6** Residual dead-leg name-join misidentification risk irreducible from staged bytes; mitigated by per-member price-death reconciliation.

## Launch mechanics

This verdict is the **A7 key only**. Scored execution still requires BOTH the fresh exact owner phrase `GO STOCKS V9 SCORED EXECUTION` AND `V9_LAUNCH_AUTHORIZED=1`. `owner_go_intent.json` remains standing conditional intent, UNCONSUMED — correctly not treated as a key.

Auditor artifacts left **untracked** by design. Scratch work in `/tmp/a7_sandbox*` only; repo untouched (30-file control-dir hash snapshot identical before/after).
