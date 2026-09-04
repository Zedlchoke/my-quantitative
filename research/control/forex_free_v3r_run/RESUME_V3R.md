# RESUME_V3R — exact runbook for the next fresh A1 session

Written 2026-09-05 by the A1 controller session whose shell died
(`spawn /bin/zsh ENOENT`, environment-level).  Everything below is STAGED,
NOT COMMITTED, and the two Python scripts are DRAFT—UNRUN.  Intake pins were
all re-verified earlier this day and reported in
`first_report_v3r_r1.json` (same directory) — do not redo them.

## Staged files in research/control/forex_free_v3r_run/

| file | state |
|---|---|
| `first_report_v3r_r1.json` | final intake artifact (Section 7 report) |
| `announcement_ledger_builder.py` | R1 builder, DRAFT—UNRUN; 5/8 area source patterns pre-verified via independent reader probes 2026-09-05 (US Fed PR + openmarket.htm, CA Valet V39079, AU cash-rate page incl. its own "2.30 pm" schedule text, GB summary pages, JP year index); ECB/CH/NZ degrade to conservative bounds by design |
| `build_evidenced_vintages.py` | R2 prep, DRAFT—UNRUN; fail-closed only-availability-differs invariant |
| `recompute_v3r.py` | R2 driver, DRAFT—UNRUN; G1–G5 guards incl. twin determinism vs the V3 ledger before any corrected number is accepted |
| `RESUME_V3R.md` | this file |

ALSO STAGED: a leftover duplicate of the first report at
`research/control/first_report_v3r_r1.json` (placed by the Lead Engineer
during environment restore).  Delete it before committing so the run dir is
the only home.

## Known draft defects to check on first run (authored blind)

- `announcement_ledger_builder.py`: verify `verify_candidate`'s date-token
  logic per area (BoE pages may state effective dates, not derived decision
  dates — degradation is the designed path, but review what verifies);
  confirm `parse_rate_tokens` behaves on Fed range text ("2 to 2-1/4
  percent" must yield both 2.0 and 2.25); confirm BoJ listing link joining.
- `recompute_v3r.py`: `--data-paths-template` must point at the ACTUAL
  data_paths JSON of the V3 scored run (find it in the V3 integration
  worktree — check `research/control/forex_free_v3_run/worktree_manifest.json`
  and the event log / handoffs for the exec invocation).
- All three scripts: run `python -m py_compile` on each first.

## Data prerequisites (per-tree copies are gitignored)

Before any run, verify in THIS worktree:
1. `data_raw/forex_free_v3_macro/*.json` exist and hash-match the
   `file_sha256` pins in the V3 `w3_freeze.json`
   (`sha256sum data_raw/forex_free_v3_macro/*.json`); copy byte-identical
   from `.worktrees/forex-free-v3/integration/data_raw/forex_free_v3_macro/`
   if absent.
2. The authorized price snapshot (`data_raw/forex_free_v1/…`, 156 files)
   exists under the directory the V3 data_paths template names; copy
   byte-identical from the V3 integration worktree if absent (it is the
   v1 authorized snapshot per w3_freeze `data_freeze.price_snapshot`).

## Run order

```bash
cd /Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3r/integration

# 0. commit intake (delete the duplicate staging copy first)
rm research/control/first_report_v3r_r1.json
git add research/control/forex_free_v3r_run/
git commit -m "FOREX-FREE-V3R intake + Section 7 first report; R1/R2 scripts staged (drafts unrun)"

# 1. compile + offline selftest of the builder (no network, all-unevidenced)
.venv/bin/python -m py_compile research/control/forex_free_v3r_run/*.py
.venv/bin/python research/control/forex_free_v3r_run/announcement_ledger_builder.py --offline-selftest
#   -> must print 151 change events + 8 baseline rows and the per-area counts
#      matching the first report (US 22, EMU 19, GB 22, JP 5, CH 11, CA 22,
#      AU 25, NZ 25).  Any drift = STOP and investigate.

# 2. R1 real run (network, keyless official sources, ~minutes; light)
.venv/bin/python research/control/forex_free_v3r_run/announcement_ledger_builder.py
#   review the status counts: evidenced vs DAY vs AVAILABILITY_UNEVIDENCED.
#   THEN, and only after review:
.venv/bin/python research/control/forex_free_v3r_run/announcement_ledger_builder.py --pin

# 3. R2 prep: evidenced vintages (fails closed on any non-availability diff)
.venv/bin/python research/control/forex_free_v3r_run/build_evidenced_vintages.py

# 4. R2 recompute (G1..G5; twin determinism FIRST, no publication anywhere)
.venv/bin/python research/control/forex_free_v3r_run/recompute_v3r.py \
    --v3-worktree /Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/integration \
    --data-paths-template <V3 scored run's data_paths.json> \
    --program-ledger <program published ledger jsonl, if located>
```

- Full pytest runs ALONE (shared machine): `pytest -q` in this worktree
  after the scripts stabilize and before R3.
- R3: spawn the independent A7 auditor on the produced artifacts
  (announcement-ledger completeness vs the union of rate-change dates the
  scored books ACTUALLY read, evidence quality, recompute determinism from
  the twin, reconciliation, gates re-evaluated UNCHANGED).  A7 never repairs.
- R4: STOP.  Present both-books-per-cell results and A7's findings to the
  owner BEFORE recording either verdict
  (`survivor RESTORED` / `FOREX_FREE_V3_DATA_AUTHORITY_INVALIDATED`).
  No middle path; rescue vetoed; V3 artifacts byte-immutable; S1
  SEALED_UNTOUCHED; no push/merge/main writes.

## Reconciliation contract already established (for the R2 report)

Finding 3 is structurally explained by the frozen runner contract
(`scored_runner.compute_cell`): expectancy (`base`, `base_price_only`) is
defined on the SCORED post-purge population (anchor: 105 trades), while the
booked columns sum ALL kept trades (anchor: 113; 8 purged within 14 days of
an internal fold boundary).  Bridge per book:
`booked = base.total_pnl + purged_contribution`; cost bridge
`gross − price_only == n_trades × $3.00` (1.5 bps/side × tier 1.0 round
trip); dual-book identity holds exactly on the V3 numbers
(−692.2937 + 2047.1507 = 1354.8570).  `recompute_v3r.py recon` emits all of
this per arm; the corrected run reports the same bridges under evidenced
availability.
