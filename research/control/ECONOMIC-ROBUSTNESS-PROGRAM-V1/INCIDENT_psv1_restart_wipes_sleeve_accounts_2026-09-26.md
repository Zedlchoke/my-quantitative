# INCIDENT — PSV1 restart wipes virtual sleeve accounts (2026-09-26T00:25Z)

Severity: **HIGH** (evidence-integrity class; no orders, no S1, no scored
cells involved). Discovered during the owner-requested A3 post-decision
check. No mutation performed after discovery; no restart; ledger untouched.

## What happened

The XSECT retirement decision row (2026-09-26T00:00:00Z, observed
00:19:49Z, row 12) shows the sleeve ALREADY flat with **zero fills**,
equity/cash reset to exactly **100,000.00** (yesterday's true book:
equity/cash **99,948.38**, 4 open positions gross **0.8004** — row 11).
The four positions did not close by trading; they **vanished** because the
worker's in-memory sleeve account was a FRESH account.

## Root cause (code-verified)

`research/shadow_v1/executor.py` L462–465: every executor constructs
`SleeveAccount(starting_cash=100_000.0)` at build time. The production
e-worker has **NO boot-time recovery of cash/positions from the ledger**
(only event_id idempotence — "decisions already in the ledger are
skipped"). grep over worker/executor: no restore/replay path exists in
production (the only replay code is the separate rehearsal lane).
Therefore EVERY e-worker restart resets all four virtual sleeve accounts.
The FX daemon, by contrast, HAS boot_replay (its state survived its
restarts — verified earlier).

## Trigger timeline (today's restarts)

| Time (UTC) | Event | Effect |
|---|---|---|
| 09-24 08:21 | original worker 35779 starts; accounts hold real state | — |
| 09-25 03:57 | A2 activation restart → 57505 | **wipe #1** (XSECT 4 positions + ILLIQ 8 positions lost from live account; BANDRIDGE/BASISLV flat → invisible) |
| 09-25 04:37 | A3 activation restart → 65078 | wipe #2 (fresh account again) |
| 09-26 00:19 | first post-restart decision WITH pre-restart holdings (XSECT daily) | defect exposed: vacuous flat → terminal row on empty book |

The latent defect predates the amendments (ANY restart would trigger it);
the A2/A3 activation restarts are what fired it. The A7 prelaunch audits
did not catch it because no test boots a worker over a ledger with open
positions (the same "main() never booted by tests" blind spot flagged as
A7 F2 LOW-residual).

## Damage census (ledger bytes are all intact — append-only preserved)

| Sleeve | Live-account damage | Ledger evidence |
|---|---|---|
| XSECT | 4 positions (ADA −0.2, BNB +0.2, DOGE −0.2, XRP +0.2) + true book (99,948.38) lost; row 12 terminal decomposition is **vacuous** (equity 100k, closed_count 0, fees 0 — NOT a faithful final accounting) | rows 1–11 faithful |
| ILLIQ | 8 positions (gross 1.0006, equity 99,936.79 at 09-21) lost from live account; Monday 09-28 00:00Z decision would run on a wiped book (DIAGNOSTIC_ONLY — no promotion risk, but continuity broken) | row 1 faithful |
| BANDRIDGE | none (never filled; equity always 100k) | intact, pinned digest continues |
| BASISLV | none (flat, DATA_BLOCKED) | intact |
| FX (A1) | NONE — daemon has boot_replay; verified across 3 restarts | intact |

Note: the valuation worker (pid 35871, never restarted) may still mark the
4 ghost XSECT positions — dashboard MTM vs ledger may diverge until
reconciled.

## A3 verdict vs the owner's four checks (row 12 evidence)

| Check | Verdict | Detail |
|---|---|---|
| Bốn vị thế đã đóng | **FAIL** | 0 closing fills; positions vanished via account reset, not by law |
| Không mở vị thế mới | PASS (trivial) | target_weights {} — retire law active; also nothing could open on an empty book |
| Terminal row đúng một lần | **FAIL (content)** | fires exactly once (row 12 only) but on a VACUOUS book — not a faithful final accounting |
| Ledger đối soát | **FAIL** | equity 99,948.38 → 100,000.00 with zero fills — unexplainable by any lawful trade |

The stop-open law itself IS working (no new positions can ever open);
what failed is the book's continuity across restart.

## Remediation options (owner decides; nothing executed)

1. **Engine fix (root)**: add boot-time sleeve-state recovery to the
   e-worker — replay each family's ledger fills into SleeveAccount at
   construction (the FX daemon's boot_replay pattern; the rehearsal lane
   already proves replay determinism). Gate: patch + restore-fixtures
   (build over a ledger with open positions; restart-idempotence) + A7
   delta + owner GO for restart. **Urgency: before Mon 09-28 00:00Z**
   (ILLIQ weekly decision) and before any BANDRIDGE fill (a fill whose
   position is later wiped would corrupt that sleeve's book too).
2. **XSECT terminal-row honesty**: append (never rewrite) a supplemental
   correction record after the engine fix — e.g.
   `RETIRE_TERMINAL_CORRECTION` carrying the faithful final book computed
   from the full ledger replay; row 12 stays as-is with the incident
   reference.
3. **Valuation reconciliation**: after the engine fix, reconcile the
   valuation worker's ghost XSECT marks (restart of the valuation worker
   under its own cycle law, owner-gated).
4. Do-nothing baseline is NOT recommended: every future restart repeats
   the wipe.
