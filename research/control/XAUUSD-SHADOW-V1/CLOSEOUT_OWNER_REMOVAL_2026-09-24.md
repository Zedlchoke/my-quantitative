# CLOSEOUT — XAUUSD-SHADOW-V1 OWNER REMOVAL (2026-09-24)

- Owner instruction (verbatim, session 2026-09-24): "bỏ XAUUSD swing ra
  khỏi hệ thống" — remove the XAUUSD swing sleeve from the shadow system.
- Executor of removal: A1, root checkout main (pre-commit HEAD 2a1ca136).
- Nothing here is a profitability claim; the sleeve's own standing label
  is quoted below.

## 1. Measured state BEFORE stop (2026-09-24 ~12:35Z)

- Worker: pid 4755 (PGID 4740), argv
  `research/control/xauusd_shadow_v1/xauusd_shadow.py --runtime-root
  results/xauusd_shadow_v1 --shadow-start 2026-09-21`, cwd
  `.worktrees/xauusd-shadow-v1/integration`, up since 2026-09-21 19:54:47
  local. No launchd/cron restart mechanism exists (measured:
  `launchctl list | grep xauus` and `crontab -l` both empty).
- Overlay: pid 68154 `python -m http.server 8790 --bind 127.0.0.1`,
  cwd = the sleeve runtime dir — confirmed to be this sleeve's read-only
  display surface (127.0.0.1:8790).
- Worktree: `.worktrees/xauusd-shadow-v1/integration`, branch
  `orca/xauusd-shadow-v1-integration`, HEAD `d0e983bd` — byte-matches the
  registry head. One pre-existing untracked file
  `research/control/xauusd_shadow_v1/a7_impl_r1.json` (prior-session A7
  artifact) — left in place, not part of this closeout.
- Runtime (`results/xauusd_shadow_v1/` in the worktree):
  `ledger.jsonl` 76 rows, `raw_bars.jsonl` 76 rows, sha-chained,
  append-only. `status.json` (pre-stop, written by the worker at
  2026-09-24T12:13:05Z): position FLAT, equity_usd 100,000.00,
  data_gaps [], n_bars 12540, last_bar 2026-09-23, label
  "XAUUSD-SHADOW-V1 / SHADOW_OBSERVATION_ONLY / NOT A PROFITABILITY
  CLAIM / COST MODEL UNMEASURED-CONSERVATIVE".
- 0 entries, 0 fills, 0 orders ever (prospective window 09-21..09-24;
  entry rarity is structural — SHADOW-PAPER-REVIEW-V1 measured ~1 entry
  intent / 5.1 years from the 12,337-bar replay).

## 2. Stop (measured)

- `kill -TERM 4755 68154` at 2026-09-24T12:3xZ; after 3s both pids gone
  (`ps -p` empty), `pgrep -fl xauusd` empty, port 8790 free (lsof empty).
- Ledger re-measured post-stop: still 76 + 76 rows — worker stopped
  between hourly marks; no partial write, no truncation. Evidence
  preserved byte-for-byte.

## 3. Consequences

- Cycle XAUUSD-SHADOW-V1 → TERMINAL (registry updated same commit).
  GO phrase "GO XAUUSD SHADOW V1 START" extinguished UNCONSUMED per P-8.
- Shadow program is now 6 sleeves: 4 crypto (PROSPECTIVE-SHADOW-V1),
  EURUSD+GBPUSD RANGEFADE-2M (FX-RANGEFADE-2M-SHADOW-V1). Program paper
  capital $600k (FX pair shares one account).
- SHADOW-PAPER-REVIEW-V1 owner-decision item O3 (XAUUSD sample-size
  time-law) is RESOLVED-SUPERSEDED by this removal — no time-law needed.
- Worktree + runtime retained as terminal evidence; no files deleted.
  Reopening XAUUSD would be a NEW owner-registered cycle (fresh identity
  per standing law; ancestry includes this terminal).
