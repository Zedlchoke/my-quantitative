# POST-ACTIVATION AUDIT — A1/A2/A3 (read-only, 2026-09-25T06:53Z)

Session scope (owner instruction): re-measure + cross-check only. No
restart, no score, no S1, no orders, no dashboard change, no portfolio.
Every claim below carries path + timestamp. This file is UNTRACKED (no
commit grant this session).

## 0. Machine state (re-measured 2026-09-25T06:53:28Z)

| Item | Value | Evidence |
|---|---|---|
| root | main @ `69ddc604…`, tracked files clean | `git rev-parse/status` |
| PSV1 worktree | `3cca6833…` clean | same |
| FX worktree | `68156025…` clean | same |
| band-risk worktree | `d396ae9a…` clean | same |
| heavy lock | FREE_PROVEN | `researchctl locks inspect` 06:53Z |
| workers | e-worker 65078 (hb 06:52:45Z), valuation 35871 (hb 06:49:59Z), FX daemon 72270 (hb 06:53:21Z) — all alive, `last_error: null` | heartbeat files |
| registry | FX/PSV1 rows updated 2026-09-25 (A1/A3 activations) | `plans/CYCLE_REGISTRY.json` |

## 1. A1 FX — anomaly triage: **METADATA BUG (state layer); activation REAL**

Journal bytes prove the new law is live (all under
`.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/shadow_journal.jsonl`):

| seq | ts (UTC) | event | content |
|---|---|---|---|
| 95/96 | 05:35:03/04Z | boot_replay | 94 events read, **0 dup, 0 bad**; sleeve state restored (EURUSD +120 / GBPUSD −33 realized, pos 0) |
| 97 | 05:35:04Z | cost_book | digest `sha256:de02abf1…`, status `PINNED_CENSUS_OWNER_OPTION_1_2026-09-25` |
| 101/102 | 06:00:06Z | bar_closed | normal H1 cadence |
| 103 | 06:00:06Z | **ctrl_open EURUSD** | fee_bps 0.2, slip_pips 0.1, **spread_at_fill 0.4 (measured)**, session Asia, **stress_slip 9.0 = 0.3×2×$15** ✓ pinned census |
| 105 | 06:00:06Z | **ctrl_open GBPUSD** | spread_at_fill 0.5, **stress_slip 27.0 = 0.9×2×$15** ✓ — the PINNED census GBPUSD Asia 0.9 (old seed was 0.8) is the value in force |
| — | — | sleeve fills since activation | **0** (both sleeves flat; per_pair_direction 0/0) |

Defect (owner-reported, confirmed): `shadow_state.json.a1_controls`:
- `phase: "PHASE_I_code_only_NOT_ACTIVATED"` — WRONG
- `T_ctrl: null` — WRONG
- `short_beta_label: "SHORT_BETA_SEPARATED (control arms emitting…)"` —
  lawful per the amendment's letter (control records exist since
  06:00:06Z) but overstated wording, and internally contradictory next to
  the phase field.

**Root cause**: the Phase I change-set wrote these as STATIC placeholders;
the daemon rewrites state from in-memory constants every poll and has NO
mechanism to learn T_ctrl (does not read the activation artifact, does not
derive from journal). They can never self-correct → design gap in the
state writer = metadata bug. NOT an activation failure (journal is
authoritative: activation + pinned cost book + live control arms).

**Correct values**: phase = `ACTIVATED`; T_ctrl = `2026-09-25T05:35:03Z`
(A1_ACTIVATION.json + journal seq 95; the 05:34:40Z first attempt died
before opening the file — disclosed in the activation artifact);
label should read "separation ACCRUAL since 06:00:06Z — interpretation
gated on preregistered decision-count; no FX-vs-control conclusion".

**No conclusion FX-vs-control is drawn** (1 epoch of control data; the
amendment's decision-count gates govern).

### Minimal patch proposal (NOT applied — awaits gate)

1. `daemon/shadow_daemon.py` (+ small helper in `fx_shadow_core.py`): at
   boot, derive `T_ctrl` from the journal (ts of the first `cost_book`
   event row); `phase = ACTIVATED` iff that row exists; label wording →
   `SHORT_BETA_SEPARATION_ACCRUING (control records since <ts>;
   interpretation gated on preregistered decision-count law)`. State-layer
   ONLY — no decision/fill/cost path touched.
2. Fixture: boot state derives T_ctrl from a synthetic journal containing
   a cost_book row; no-row journal keeps the Phase I placeholder.
3. Gate required: patch commit + fixture + A7 delta review + **fresh
   owner GO for the restart** (the A1 GO's Phase-A restart was consumed;
   a new daemon restart needs new authority per P-8 discipline). No
   history rewrite; state self-corrects at next boot; journal untouched.

## 2. A2 BANDRIDGE — PASS

`…/ledgers/BTC4H-BANDRIDGE.jsonl` (62 rows, 06:53Z):
- digest census: **61× `130d2e7e…` (pre-T_act) + 1× `b84ae93e…`**
  (decision 2026-09-25T04:00:00Z, observed 04:17:20Z — first row after
  T_act 03:57:05Z) — clean boundary, zero stragglers.
- **fills total = 0** → no fill under the old law after activation
  (trivially and provably true).
- No new row since 04:00Z is expected before the 08:00Z H4 decision
  (~08:17Z observable).

## 3. A3 XSECT — pre-decision checks PASS; post-decision checks **PENDING (NOT_RUN)**

Now = 2026-09-25T06:53Z < decision 2026-09-26T00:00:00Z ⇒ per owner
instruction the close/terminal checks are **PENDING**, not COMPLETE.

- T_ret 05:45:00Z has PASSED; worker 65078 runs the A3 code (restarted
  04:37:07Z from `73e13860`; heartbeat fresh 06:52:45Z).
- Ledger unchanged: 11 rows; last = 2026-09-25T00:00:00Z holding
  {ADA −0.2, BNB +0.2, DOGE −0.2, XRP +0.2} gross 0.8004 — the four
  positions the 2026-09-26T00:00Z decision must close.
- Expected at 2026-09-26T00:00Z (~00:17Z observable): target_weights {}
  forced, exactly the four closing fills, zero opens, terminal row
  `IDENTITY_RETIRED_COST_DOMINATED` on that same row (A7 F2), first
  occurrence canonical (A7 F1 advisory).

## 4. Verdict table

| Check | Verdict | Evidence (path + ts) |
|---|---|---|
| Machine re-measure clean (HEADs/lock/workers/heartbeats) | PASS | §0 table, 06:53Z |
| A1 activation real (journal authority) | PASS | journal seq 95–105, 05:35:03→06:00:06Z |
| A1 pinned cost book in force (census values driving stress) | PASS | seq 97 (05:35:04Z) + seq 105 stress_slip 27.0 = 0.9×2×15 |
| A1 state metadata correct | **FAIL** (metadata bug; correct values + minimal patch proposed) | shadow_state.json a1_controls, updated 06:53:36Z |
| A1 restart-idempotence | PASS | seq 95/96: 94 events, 0 dup, 0 bad |
| A1 FX-vs-control conclusion | NOT_DRAWN (by law — 1 epoch of control data) | seq 103/105 only |
| A2 boundary digest clean | PASS | ledger census 61×old + 1×new; 04:17:20Z |
| A2 no old-law fill post-activation | PASS (0 fills total) | ledger, 06:53Z |
| A3 pre-decision state (law armed, holdings intact) | PASS | ledger row 11 (00:00Z), worker hb 06:52:45Z |
| A3 four-positions-closed / no-new-opens / terminal-row-once / ledger reconcile | **PENDING (NOT_RUN)** — decision 2026-09-26T00:00Z | re-audit after ~00:17Z 2026-09-26 |

Zero-claims this session: restarts 0 · scored cells 0 · S1 0 · orders 0 ·
dashboard/portfolio untouched.
