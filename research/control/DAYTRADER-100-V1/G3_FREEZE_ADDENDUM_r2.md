# DAYTRADER-100-V1 — G3 ADDENDUM r2: A7 prelaunch remediation (pre-PnL)

- recorded_utc: 2026-09-28, after A7 prelaunch verdict AUTHORIZED_WITH_FINDINGS
  (1 HIGH), before any scored PnL and before key-2. Correction window open per
  addendum r1 §2 precedent.

## A7 verdict (recorded)

`AUTHORIZED_WITH_FINDINGS` — conditions: fix HIGH-1, record sha256 pins (M-2),
staged-bytes manifest (M-3). Full findings list preserved verbatim in
`A7_PRELAUNCH.md`.

## Remediation (all landed in this commit)

1. **HIGH-1 FIXED**: BASISTERM funding sign now −1.0 (same as CARRY): on the
   synthetic spread, dir=+1 ⇒ short the perp leg ⇒ funding is income for BOTH
   families. `run_dt100.py` fsign condition updated with the A7 derivation in
   a comment. Post-fix re-verification: fixtures 7/7 PASS; BASISTERM dry-run
   3/3 arms clean, counts identical to the pre-fix artifact (funding touches
   only fund_bps, never pos/counts) — the canonical COMPLETE artifact's 87 rows
   stand, with this note as the chain record.
2. **M-2 FIXED**: core-file sha256 pins recorded (post-remediation values):
   arms.py 1093682d827ee4e6fc15a961e57b0d9651f97cc111bcefd2d0c7c117f805f551 ·
   config.py 2519abf861d9552fc5bdb4e402c9f7c9424ebd19229c0a072c21da79d1be8812 ·
   engine.py bf536db84973f9316209b1ff71dba43079c2cac8d3cce160c51df93433286362 ·
   signals.py e8dfe15003a5892becee0b4e7fec9702889b1f9a65b318450ac4867f9998a2ac ·
   data.py 5071bdcc0384f05499f19f416219d342e81faaba003723c5768f40c6ae70ce69
3. **M-3 FIXED**: `STAGED_BYTES_MANIFEST.json` written — per-source file counts,
   byte totals, and sha256 head/tail samples for every staged and cross-worktree
   substrate (premium/funding/spot/quarterly/BTC-1m/ETH-1h/FX bi5).
4. **L-5 FIXED**: `BLOCKED_UNDER_ORDER` stale entries removed (CARRY/BASISTERM
   moved to ARMS by r1).
5. **L-4 / L-6 wording corrections** (no artifact rewrite): dry mode computes
   stats in memory but never persists or consumes them (row schema count-only;
   verified by A7 grep); merge provenance families = FUNDCONTRA, CARRY, PAIRMR,
   LEADLAG, ETHBTC, BASISTERM, FORECASTFUND (A7's independent diff confirms the
   other 22 families digest-identical).

## Two-key status after remediation

key-1 = A7 AUTHORIZED_WITH_FINDINGS, conditions discharged in this commit.
key-2 = owner phrase `GO DAYTRADER 100 V1 SCORED EXECUTION` — still required,
typed verbatim at the gate. Not typed yet.
