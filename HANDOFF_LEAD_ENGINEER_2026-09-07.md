# HANDOFF — Lead Engineer of my-quantitative (2026-09-07, ~12:00 VN)

> Written by the outgoing Lead (successor of the 2026-09-06 handoff) for
> the incoming Lead. The owner pastes a short prompt pointing here. You
> act for the owner: Vietnamese-speaking, explain simply when asked,
> honest negatives are valued outcomes. Re-measure EVERYTHING before
> trusting this snapshot (handbook §3); this file is evidence about this
> morning, not current truth.

## 1. Read first, in full, in this order (they outrank this file)

1. `CLAUDE.md` — operating contract
2. `RULES.md` — the law + agent roster + GO registry + **§9 mechanism
   status ladder** (new)
3. `HOW_TO_BE_A_LEAD_ENGINEER.md` — handbook §1–35 (incl. §3.1
   ACTIVE_CYCLES router, §10.3 machine-wide heavy lock)
4. `research/wayfinder/LESSONS.md` — P-1..P-11 (P-11 new: a terminal can
   only price what the driver persisted)
5. `research/wayfinder/HYPOTHESIS_LEDGER.md` — every family + forbidden
   ancestry + the ONLY cross-asset denominator authority (P-9)
6. `research/wayfinder/FAMILY_PIPELINE.md` + `FAMILY_FAILURES.jsonl` —
   the merged research lifecycle (owner-approved) + machine-readable
   failure memory (50 entries, validator + `--verify` green)
7. `research/wayfinder/MAP.md`, `SURVIVORS.md`

## 2. Standing duties (as practiced this window)

- Review every A1 handoff against artifacts — never prose. Audit
  POSITIVE results stricter (§20.2). One cycle = one A1 thread; heavy
  cap 1 **machine-wide** (now a mechanism, see §4); full pytest runs
  ALONE; `pwd` before every `git worktree add`; never one branch in two
  worktrees; **never `git add -A`; commit by pathspec in the root** (P-10).
- **Claims discipline (my window's own lesson, twice paid)**: a test
  count or PASS claim in a commit message/report may only come from the
  LAST test run executed before the commit — not the run before the
  cleanup edit. I shipped two commits with stale claims and had to
  amend; disclose yours if it happens (§24).
- **Timestamp discipline**: control files' `ts_utc` fields written by
  A1s have twice run ahead of real clocks (V10: +40..90 min). Git
  commits carry truth; flag the drift, don't silently trust or "fix"
  frozen artifacts.
- Push/merge-main/S1/purchases/keyed-signups/GO phrases are OWNER-ONLY.
  GO two-key per P-8 (A7 fresh-context first, owner types the exact
  phrase after reading the verdict; early GOs are extinguished intent).
- Ledger + MAP + LESSONS at every close: cycle A1s (V15, V6) have begun
  syncing their own rows — VERIFY their rows and denominators instead
  of duplicating; you own the ground-rules line. Watch the P-9 trap:
  terminal program totals are intake-stamped (V10's said 203/206 when
  truth was 206/209).
- Disclosure gaps get recorded, not papered over (I recorded V6's
  A7-terminal NOT_RUN in its ledger row; the gap was later closed by
  addendum — that is the system working).

## 3. Measured program state at handoff (2026-09-07 ~12:00 VN)

- **218 published / 221 observed, 0 survivors, S1 SEALED in all assets.**
  crypto 149/152 · stocks 36/36 · forex 33/33.
- Closed this window (all A7-confirmed, all on origin): crypto V15
  `V15_REJECT_ALL` (falsification cluster #11: control CTL-ELITELEVEL
  out-earned the anchor then failed concentration itself; DSR/PBO NOT_RUN
  for missing per-period series → P-11); stocks V10 `REJECT_ALL` (timing
  axis carries real directional content drowned by the sector book);
  forex V6 `REJECT_ALL` + post-close A7T CONFIRM `0dead47` (the forex
  near-miss: A4-P1 +0.963/trade dying on 4 robustness gates with the
  SHAM control NEGATIVE — genuine calendar information).
- ACTIVE (each has its own owner-dispatched A1 thread; measure before
  assuming):
  - **stocks V11** — D1 integrated (6 blind proposals, wave ea66879);
    next D2.
  - **crypto V16** — P2 funded (26/26 symbol-months aggTrades, ~654
    symbol-days), P3 frozen; **diagnostic gate LIVE on its branch: it
    refused a wrong-shaped scaffold (BLOCKED_PRELAUNCH verbatim) then
    passed the canon-correct one**; next D1.
  - **forex V7** — D2 + selection done: A6-P1 ANCESTRY_VETO (0.2689 vs
    V6 USD-PC1 — the named risk measured real), A4-P2 coverage-starved;
    SELECTED FXFV7-A4-P1 (k4/k9/+7d-sham) + FXFV7-A6-P2 (q80/q70/own-
    lag); selection freeze carries the validated
    diagnostic_output_contract; next I/Q.
- Pending owner items: FRED key (free signup → `.env` FRED_API_KEY —
  unlocks V7-class market axis in a future cycle; currently ABSENT,
  measured); kernel debt F-A7-T-1 (gate-equality quirk, verdict-neutral,
  carried from V6 closeout); **dashboard build** (see §5).

## 4. Governance program (NEW this window — merged on main @77e31ff)

Three mechanisms, owner-amended through two remediation rounds, live in
`research/governance/` with 54 tests + registry `--verify`:
- **FAMILY_FAILURES registry + validator** — the failure memory; append
  at every close (five-class taxonomy; TECHABORT carries no quality
  evidence; TERMINAL_PENDING until A7 terminal + canonical ledger).
- **Diagnostic persistability gate** — canon `CATEGORY_REQUIRED_FIELDS`,
  registered schema ids, fresh-emission sandbox smoke; runs BEFORE A7
  launch authorization; first real ADOPTION evidence: V16's P3 (see §3).
- **Machine-wide heavy lock** — `~/.my-quantitative-governance/
  heavy_runtime` (home, outside every repo); PID + process-start-token;
  malformed registry / live-pid-missing-token ⇒ CONTROL_STATE_DRIFT
  fail-closed; reclaim only on PROVEN pid-dead or token mismatch; FAILED
  releases must carry the stderr tail (two V16 P0 failures were
  unrecoverable because they didn't).
Adoption boundary: crypto V16+ / forex V7+ / stocks V12+ (all three
current cycles are past it). Status ladder lives in RULES.md §9 —
ADOPTED only when a cycle actually uses a mechanism.

## 5. Dashboard (approved, NOT built)

`plans/PLAN_dashboard.md` (owner-approved 2026-09-07): a macOS
standalone app (pywebview window + double-click launcher) showing
program overview + live cycle status, Vietnamese UI, evidence-first
display law; the collector also generates `plans/ACTIVE_CYCLES.json`
(handbook §3.1 registry — still missing). Worktree ALREADY created:
`.worktrees/governance/lab-dashboard` @ branch `orca/lab-dashboard`
(base 752a3ff). Commits A (stdlib layers + tests) and B (app layer) per
plan. The owner dispatches a build agent with the prompt they hold;
merge/push stays owner-only.

## 6. Data and infrastructure

- **EODHD** $19.99/mo (key in gitignored `.env`) — keep active while a
  stocks cycle runs (V11 is); cancel when stocks idle.
- **Backups**: `~/staging_backups/` (12 archives + `cleanup_2026-09-07/`
  with sha256 manifests; restore = `tar xzf`). Committed manifest at
  `research/control/staging_backups_manifest.md`.
- **Repo**: git is TINY (~27 MB pack); the heavy stuff is gitignored
  worktree data (~12G; v9 worktree 4.8G is the canonical panel holder —
  next big cleanup only after stocks cycles stop re-hashing it).
- **Machine**: 8 GB / 8-core; heavy cap 1 (lock enforces); GLM quota
  walls have killed lanes mid-task twice (I-F1, V6) — schedule heavy
  phases off-peak.
- **Worktrees**: 38 at handoff (cleanup candidates appear as cycles
  close; archive-then-delete per manifest protocol, owner-authorized).

## 7. How the owner works

- Vietnamese; simple-layer-then-technical; decides via cards; moves
  VERY fast (three cycles dispatched in one morning); dispatches A1
  threads personally — always `git worktree list` before assuming idle.
- GO phrases (exact, fresh, at their own gate — P-8):
  `GO STOCKS V11 SCORED EXECUTION` / `GO CRYPTO V16 SCORED EXECUTION` /
  `GO FOREX V7 SCORED EXECUTION`. Dead phrases never carry forward.
- Approves via short imperatives ("merge và push đi") — execute exactly
  the granted scope, no more.

## 8. Your first hour

1. Re-measure: pwd, branch, HEAD, porcelain, `git worktree list`, ps;
   confirm S1 sealed and 218/221 in the ledger.
2. Read the three ACTIVE cycle states (V11/V16/V7) from their control
   dirs — phases move hourly; do not trust this letter's snapshot.
3. Emit your first independent status to the owner (§4.5): measured
   time, tree, workers, cycle phases, budget, S1, blockers, GO/NO_GO.
4. Then keep the gates. 221 cells have said no; each no was cheap,
   recorded, and correct. The machinery — including the controls, the
   gate that refuses, and the lock that fails closed — is the product.

*Filed by the outgoing Lead. The books balance, the mechanisms are live,
and every door is either measured-closed or preregistered. Good hunting.*
