# INCIDENT — phase-1 launcher failures before any cell computed (no exposure)

- cycle: ILLIQ-REG-V1 · what happened: two launch attempts failed before any
  `run_strategy` call, plus one lock-hygiene miss:
  1. Attempt 1 (in-process design): `ModuleNotFoundError:
     research.governance` — importing the v11 side (via gated_plugin →
     chr3f_illiq_plugin → research.v11...) bound the `research` package to
     `v11_root/research` in `sys.modules`; the later root-repo import
     `research.governance.heavy_lock` then resolved against v11_root only.
     Fix: the chr3f `illiq_scored.py` process-isolation pattern — launcher
     keeps root paths only; each cell is a SUBPROCESS owning the v11 imports
     (`illiq_reg_cell.py`).
  2. Attempt 2: `KeyError: date(2024-08-26)` — the gate map is keyed by ISO
     date STRINGS; the cell indexed it with a `date` object. Fixed with
     `.isoformat()`. The same attempt also called `heavy_lock.release` as a
     MODULE function; the real API is `HeavyLockHandle.release(status,
     note)` — the AttributeError in the `finally` killed the launcher and
     left a RUNNING registry row behind a free flock.
  3. Recovery: `heavy_lock.cleanup_stale()` archived the stale row
     (`action: archived_stale, reason: pid_dead` — the sanctioned path), and
     `locks inspect` returned `FREE_PROVEN` before the successful relaunch.
- outcome-data exposure: NONE. Both failures occurred before any engine run;
  no PnL was computed or printed; budget remained 0/4; the successful sweep
  (4/4 cells) followed with the lock correctly held and released (FINISHED).
- evidence: background-task logs of both failed attempts (session exec logs),
  this file, and the fixed `phase1_sweep.py` / `illiq_reg_cell.py` committed
  at the freeze SHA.
- prevention: process-isolation rule recorded in `phase1_sweep.py`
  docstring; release API fixed; per-cell heartbeat added.
