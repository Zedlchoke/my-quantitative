# A7 PRELAUNCH — BASISLV replication stage (CRYPTO-HISTORICAL-REPLICATION-3F-V1)

- Schema: `chr3f_a7_prelaunch@1` · Cycle: `CRYPTO-HISTORICAL-REPLICATION-3F-V1/BASISLV`
- Audit UTC: 2026-09-25T02:20:26Z · Head: `9405ab3a509546e19c1356486a722005228cdad2` (branch `orca/crypto-historical-replication-3f-v1-integration`)
- Scope: 8 scored cells = {Y2021, Y2022, Y2023, Y2024P} × {BASISLV-PREMFADE-28D anchor, BASISLV-PREMFADE-28D-INV control}, labels `REPLICATION_NOT_PROSPECTIVE` / `EQUIVALENCE_BIT_EXACT_ORIGINAL_WINDOW` / `UNIVERSE_LISTED_AT_WINDOW_START` on every row. Budget: 12 distinct cells on disk (XSECT 8 + ILLIQ 4) + 8 = **20 ≤ 24**.

## VERDICT: **REFUSED** — exactly one blocking finding; everything else measured clean.

### Blocking finding B1 — BASISLV fold-4 selection conflicts with the plan's deterministic law; census evidence missing

Plan §6: fold-4 per family = **Y2020P if that family's P0 stamp census passes, else Y2024P** ("deterministic fallback, chosen now"), and the choice must be "**recorded with the census evidence**" before any of that family's scored cells run. The conditionality is family-generic (2×4×3 = 24 cells), not ILLIQ-specific.

- `replication_data.FOLDS` pins **Y2024P** for BASISLV. **No BASISLV Y2020P census exists anywhere in the control tree** (Y2020P records exist only for XSECT — census passed, scored Y2020P — and ILLIQ — census failed with 4 skipped stamps on file).
- A7 independently traversed the plan §3 BASISLV Y2020P window (2020-11-16..2021-01-01; 5 open stamps, sanitized, no PnL): **0 eligibility-refused stamps** — 3 OK books at n_eligible = 12 = MIN_ELIGIBLE (2020-11-23, 12-07, 12-21) and 2 fold-terminal FLAT transitions (the frozen fold law, not refusals). **The census would PASS → the deterministic rule selects Y2020P, not Y2024P.**

Left unadjudicated, the sweep runs Y2024P where the plan's own law (absent a recorded owner override) selects Y2020P — a trial-identity defect in the scored denominator, in tension with §3's "no window substitution, no post-hoc year selection".

**Remediation (owner, before GO; no code change needed in either branch):** record the fold-4 decision with the census evidence — (a) attach the Y2020P census measurement (values above) and amend to fold-4 = Y2020P (budget unchanged 20 ≤ 24; Y2020P partials report separately per §8), or (b) attach the same measurement + an explicit owner override note selecting Y2024P for BASISLV (authority order 1). Then a mechanical A7 round 2.

## Checks that PASSED (all recomputed from bytes)

- **A (subclass partition)**: `BasislvWindowFoldPlugin` overrides exactly the fold-binding surface (schedule via the frozen `weekly_mondays` re-targeted — start edge excluded, end edge included; thirds F1/F2/F3 day-truncated; purge_days=0 disclosed; targets_at wraps the frozen `compute_targets_at` verbatim; fold-terminal flat re-scoped; context narrowing only). `universe()` NOT overridden — frozen 19 at every window. Signal, book geometry, fills, marks, funding, costs, stress = frozen module code called verbatim; identity = frozen `frozen_identity`.
- **B (conversions + the load-bearing remap)**: parquet schema equals the frozen `restage_basis.py` schema; independent ETHUSDT JSON→parquet conversion = **0/147935 value mismatches**, 0 dups, all opens on-grid, identity max dev 5.0e-05 ≤ 1e-4. The kline-OPEN→close-boundary remap is line-identical to the proven `equiv_runner.py` (`_snap_close_to_boundary_vectorized(ts) + 15m`, availability = close) and was re-verified from raw bytes: vision-zip kline open 2021-01-01T00:00Z close 731.64 → b20 catalog ts_event = that open, close 731.64 → loader boundary 2021-01-01T00:15Z. Equivalence gate verdict EQUIVALENT (all surfaces abs_diff 0.0, run hashes equal per arm) makes a remap mismatch structurally impossible.
- **C (D1)**: frozen `strategy.py` lines 41–43 and 683–685 say verbatim "the stamp refuses and the refusal is counted; fail closed" — D1's flat refusal-counted book **is** the frozen semantics; whole-cell abort is not supported by the frozen text (the fold-terminal flat-OK book is the in-file precedent).
- **D (dry-run honesty)**: report totals verified (186 open stamps = 51+51+52+32; per-fold OK/INSUFFICIENT/FORCE_FLAT as disclosed); 4 stamps independently re-derived and matched exactly, incl. 2023-11-13 (n_eligible=0, refused 15 MISSING_OR_NON_FINITE_SLOT + 4 INSUFFICIENT_HISTORY — exactly the Mondays whose 28d window straddles the single gap bucket; arithmetic exact). Recursive banned-token scan: 0 PnL fields at any depth.
- **E (scored conformance)**: windows verbatim plan §3 (no overlap with [2024-08-20, 2026-08-21]; end-edge Monday 2024-01-01 belongs to Y2023's schedule-final edge, excluded from Y2024P by the frozen start-edge rule); 3 labels + note on every row; outputs/registry cycle-local (`basislv_replication/scored_out/` + `scored_status.json`); whole sweep under the machine-wide heavy lock (inspected FREE). **Self-gate verified live**: `replication_scored.py` without this artifact printed REFUSED and exited **rc=5** before any lock acquisition.
- **F (boundaries)**: no S1 references, no network/credentials, writes namespace-local only; **no CHR3F-BASISLV scored cell exists anywhere** (grep clean across the control tree).
- **G (data spot-check)**: ETHUSDT staged basis 147935 rows, 2020-06-01T00:00Z..2024-08-19T23:45Z (inside [2020-06-01, 2024-08-19]), ~96 rows/day (95.94 with exactly the 1 gap), loader series = close-boundary indexing with exactly 1 NaN slot.

## Non-blocking findings

1. **N1 — disclosure mislabel**: the gap bucket `1699587900000` is **2023-11-10T03:45:00Z** (close 04:00Z), repeatedly labeled "03:45Z" in `basis_convert.py` (docstring + report text), `replication_scored.py` (D2), and the commit message. Machine values are correct everywhere; only the ISO label is wrong. Correct in the next commit.
2. **N2 — registry staleness**: `CYCLE_REGISTRY.json` numeric `budget.used = 0` vs the phase text "Budget 12/24" and 12 cells on disk. Reconcile before terminal close.
3. **N3 — Y2024P thirds = 11 stamps/fold < frozen `MIN_DECISIONS_PER_FOLD=15`**: not enforced by the scored runner (gate_runner constant); same geometry already ran in ILLIQ Y2024P. Disclose in cell reports.
4. **N4 — Y2023's 4 INSUFFICIENT stamps ADMISSIBLE**: plan §3 registers Y2023 unconditionally; the "every stamp eligible" conditionality belongs to the Y2020P fold-4 row and §6's census law, not within-fold stamp eligibility. §4's gap law ("NOT_RUN counts, never interpolations") is satisfied by the refusal-counted books. Required at reporting: the 4 stamps + cause visible in every cell row (`n_insufficient_eligible_refusals`) and the family report.
5. **N5 — D2/D3 admissible**: gap-tolerant basis load (REPORTED NaN, engine per-slot refusal decides) and the fold-terminal pre-check re-scope (never-held names only; covered symbols still fail closed verbatim) are disclosed and preserve fail-closed behavior.

## Audit conduct

All rederivations were lock-free sanitized local reads (no scored compute), the same class as the implementer dry-run; the heavy lock was inspected FREE before and after. The scored launcher was executed exactly once, WITHOUT the A7 artifact (rc=5, no lock, no cell). No file outside `A7_PRELAUNCH.json`/`A7_PRELAUNCH.md` was written by this audit.
