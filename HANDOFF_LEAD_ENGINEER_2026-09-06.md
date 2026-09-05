# HANDOFF — Lead Engineer of my-quantitative (2026-09-06, ~06:50 VN)

> Written by the outgoing Lead (successor of Adam Hoàng) for the incoming
> Lead. The owner pastes a short prompt pointing here. You act for the
> owner: Vietnamese-speaking, explain simply when asked, honest negatives
> are valued outcomes. Re-measure EVERYTHING before trusting this snapshot
> (handbook §3); this file is evidence about yesterday, not current truth.

## 1. Read first, in full, in this order (they outrank this file)

1. `CLAUDE.md` — operating contract (plan pointers now live in `plans/`)
2. `RULES.md` — NEW reinforcement layer: universal law, the anti-overfitting
   doctrine (8 clauses), per-asset rules, the full agent roster (A1–A9 +
   Lead + Owner), and the GO-phrase registry. Every dispatch prompt now
   tells agents to read RULES.md first.
3. `HOW_TO_BE_A_LEAD_ENGINEER.md` — §1–35 handbook
4. `research/wayfinder/LESSONS.md` — P-1..P-10. P-7..P-10 are from the last
   two days; each entry cites its incident.
5. `research/wayfinder/HYPOTHESIS_LEDGER.md` — every family ever tried,
   forbidden ancestry, and the ONLY cross-asset denominator authority (P-9).
6. `research/wayfinder/SURVIVORS.md` — S-1 closed INVALIDATED; no survivor
   has ever existed. `research/wayfinder/MAP.md` — synced through V5.

## 2. Standing duties (unchanged from Adam's practice, plus P-10)

- Review every A1 handoff against artifacts (verdict files, ledgers, SHAs)
  — never prose. Audit POSITIVE results stricter (§20.2).
- One cycle = one A1 thread; heavy cap 1 machine-wide; full pytest runs
  ALONE; `pwd` before every `git worktree add`; never one branch in two
  worktrees.
- Root checkout: NEVER `git add -A`; stage by name; **commit by pathspec**
  (`git commit -m ... -- <files>`) — the root index is a shared stage and
  another agent committed within 4 minutes of you once (P-10/INC-V5-1).
- Push/merge-to-main/S1-opening/purchases/keyed-signups are OWNER-ONLY.
  GO phrases are owner-only and two-key (P-8): fresh-context A7
  authorization reaches the owner FIRST, then the owner types the exact
  phrase. A GO typed early is recorded intent, extinguished unconsumed.
  The frozen phrase gate refuses wrong/shorthand phrases — it did once;
  that refusal is the system working.
- Availability evidence is absolute (P-1). Margin-to-fail per gate (P-2).
- Update ledger + lessons at every close. NOTE: cycle A1s have begun
  appending their own ledger rows and MAP sync at close (V5 did, correctly)
  — VERIFY their rows and denominators instead of duplicating; you own the
  ground-rules line.
- Incidents get recorded even when harmless (§24). Three instructive ones:
  V8's single-thread self-audit deviation (→ A7 fresh-context is now
  MANDATED in plans), V8's vacuous dry-run (F-A7-1, non-vacuity gates now
  standard), V5's index swallow (P-10).

## 3. Measured program state at handoff (2026-09-06 ~06:50 VN)

- **200 published / 203 observed, 0 survivors, S1 SEALED in all assets.**
  crypto 143/146 · stocks 30/30 · forex 27/27.
- Closed this window (all REJECT/BLOCKED, all A7-confirmed, all pushed):
  Stocks V8 (falsified-by-control ×2), Forex V4 (carry door closed by
  measured rho), Crypto V14 (PREMFADE near-miss killed by fold
  concentration 0.5110; OICYC confirmatory closed; first program DSR ≈ 0),
  Stocks V9 (death-inclusive universe BUILT — durable asset; depletion
  runway dead), Forex V5 (window-avoidance dead pre-cost; sham-calendar
  placebo out-earned it — sham control now mandatory for calendar
  mechanisms).
- ACTIVE at handoff: **crypto V15** (P3 frozen, D1 dispatched 06:46 from
  wave 56e4d7c — 3 lanes on OI-level/crowding axes from data.binance.vision
  archives) and **stocks V10** (bootstrapped at V9 terminal 3a61638, early
  — filing-timing/revision observables). Each has its own A1 thread the
  owner dispatched. Forex **V6 is planned but NOT dispatched**
  (plans/PLAN_forex_v6.md; dispatch prompt pattern: read plan + RULES.md →
  first report → autonomous to prelaunch → HARD STOP two-key).
- Owner's pending moments: V15/V10 checkpoints; GO phrases
  `GO CRYPTO V15 SCORED EXECUTION` / `GO STOCKS V10 SCORED EXECUTION` /
  `GO FOREX V6 SCORED EXECUTION` (each only when its A7 authorizes);
  optional free FRED key for forex V6's market axis (owner signup → .env
  FRED_API_KEY, like EODHD).

## 4. Data and infrastructure

- **EODHD** owner subscription $19.99/mo (All World; key in gitignored
  `.env` EODHD_API_KEY). Probe 6/6 PASS incl. delisted canaries. Keep
  active while a stocks cycle runs; cancel when stocks idle; re-subscribe
  at any future S1 stage. FIRST-CYCLE-USE NOTES: the current-registry
  panel has NO in-window deaths (M-I1 — never claim a delisted leg the
  cohort doesn't contain); V9's death-inclusive cohort + census +
  dead-filer panel live in `.worktrees/stocks-free-v9/integration`
  staging (KEEP that worktree — V10+ re-hash it).
- **Backups**: every deleted closed-cycle forest is archived whole in
  `~/staging_backups/` (12 tarballs + SHA256SUMS; manifest committed at
  `research/control/staging_backups_manifest.md`). Restore = tar xzf.
  The v12 lesson (no deletion without backup) is now encoded practice.
- **Worktrees at handoff: 15.** Cleanup candidate: the forex-free-v5
  forest (closed at 3dacf1a) — archive-then-delete per the same protocol
  once you verify its ledger/evidence are pushed. KEEP: root,
  crypto/v15/*, stocks-free-v10/integration, stocks-free-v9/integration.
- **Root layout**: `plans/` (21 plans; live = highest version per asset),
  `RULES.md`, `bs/` (legacy archive: sprint docs + 3 analysis scripts).
  The `strategy*.py`/`regime*.py`/`main.py` files at root are LOAD-BEARING
  (strategy_factory imports them statically; the root pytest suite is
  ~912 tests — that is the bootstrap suite; per-cycle 2000+ counts live on
  cycle branches; do not "clean" them again — it was tried and reverted).
- **Coordination**: GLM quota peak weekdays 13:00–17:00 VN (1.2x vs 0.4x
  off-peak; night event to 2026-09-20). Prefer heavy agent phases
  off-peak. A1s respect each other via NOT_RUN_RESOURCE_CONFLICT.

## 5. How the owner works

- Vietnamese; wants simple-layer-then-technical; decides via cards; says
  "đã xong"/"cho GO" early sometimes — apply P-8 kindly and literally.
  Twice now an early GO arrived; both times the record-keeping held
  (extinguished → fresh GO at the true gate). Keep that pattern.
- The owner moves FAST (five cycles closed in ~24h once) and will dispatch
  A1 threads themselves — measure for new worktrees/branches before
  assuming idle.

## 6. Your first hour

1. Re-measure: pwd, branch, HEAD, porcelain, `git worktree list`, ps for
   workers; confirm S1 sealed, denominators 200/203 in the ledger.
2. Read V15 and V10 control states (state.json, event_log, latest commits).
3. Emit your first independent status to the owner (handbook §4.5):
   measured time, tree, workers, cycle phases, budget, S1, blockers,
   GO/NO_GO for next steps.
4. Then just keep the gates. The machinery is proven; your job is to keep
   it honest, not to make it produce survivors. 200 cells have said no so
   far — each no was cheap, recorded, and correct.

*Filed by the outgoing Lead. The lab is clean, the books balance, and
every door is either measured-closed or preregistered. Good hunting.*
