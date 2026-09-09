# HANDOFF — Lead Engineer of my-quantitative (2026-09-09, ~09:00 VN)

> Written by the outgoing Lead (the 2026-09-07 handoff's successor) for
> the incoming Lead. The owner pastes a short prompt pointing here. You
> act for the owner: Vietnamese-speaking, explain simply when asked,
> honest negatives are valued outcomes. Re-measure EVERYTHING before
> trusting this snapshot (handbook §3); this file is evidence about this
> morning, not current truth.

## 1. Read first, in full, in this order (they outrank this file)

1. `CLAUDE.md` — operating contract
2. `RULES.md` — the law + agent roster + GO registry + §9 mechanism
   status ladder
3. `HOW_TO_BE_A_LEAD_ENGINEER.md` — handbook §1–35 (§3.1 registry router,
   §10.3 machine-wide heavy lock, §11.7 archive verdicts)
4. `research/wayfinder/LESSONS.md` — P-1..P-11 (+ the P-11 first-delivery
   note: forex V7 computed DSR from persisted per-period series)
5. `research/wayfinder/HYPOTHESIS_LEDGER.md` — every family, forbidden
   ancestry, the ONLY cross-asset denominator authority (P-9)
6. `research/wayfinder/FAMILY_PIPELINE.md` + `FAMILY_FAILURES.jsonl`
   (55 entries, validator + `--verify` PASS — run it yourself)
7. `plans/PLAN_system_hardening_v1.md` + `docs/RESEARCHCTL.md` — the
   hardened control plane now ON MAIN: cycles bootstrap through
   `researchctl`/canonical registry writes; retry taxonomy binds
   (CODE_OR_SCHEMA_ERROR is never auto-retried); dashboard/doctor reads
   leave the tree clean
8. `research/wayfinder/MAP.md`, `SURVIVORS.md`

## 2. Standing duties (as practiced this window — deltas from 09-07 in bold)

- Review every A1 handoff against artifacts — never prose; positives
  stricter than negatives (§20.2). One cycle = one A1 thread; heavy cap 1
  machine-wide (now a mechanism); full pytest ALONE; `pwd` before every
  `git worktree add`; never `git add -A`; commit by pathspec in the root
  (P-10). **I hit the cwd-drift trap myself once (a merge command ran in
  the wrong worktree — harmless, disclosed): use absolute `git -C` for
  every root/cycle operation, always.**
- **Router edits are Lead-only.** Two concurrent A1s raced CONTINUE.md
  edits at dispatch; ruling since: an A1 that finds a router gap REPORTS
  it to the Lead and never edits the intro itself.
- **A1 registry appends sometimes land uncommitted in the root working
  tree** (V7's rows did). On close, verify their content against the
  terminal artifact, append what's missing (mind the required
  `unknown_fields: []`), run the validator, then commit by pathspec.
- Claims discipline: a test count/PASS in a commit may only come from
  the LAST run before that commit. Timestamp discipline: control-file
  `ts_utc` fields have run ahead of real clocks (V11 ~+30 min); git
  carries truth — record, never "fix" frozen artifacts.
- **Owner words are literal: a question is not an order.** This window
  the owner asked "đã merge chưa?" — I correctly did not merge until the
  imperative came ("làm ngay đi"). Same class as P-8 form discipline.
- Push/merge-main/S1/purchases/keyed-signups/GO = OWNER-ONLY. GO two-key
  per P-8 (A7 fresh-context verdict first, owner types the exact phrase
  after reading it; early GOs are extinguished intent).

## 3. Measured program state at handoff (2026-09-09 08:58 VN)

- **233 published / 236 observed, 0 survivors, S1 SEALED everywhere.**
  crypto 155/158 · stocks 39/39 · forex 39/39. Registry 55 entries PASS.
- Closed this window (all A7-confirmed from bytes, all on origin):
  crypto V16 `V16_REJECT_ALL` (terminal `46db31d`, close `9d62d5c`, A7T
  addendum `2762cd7` — aggTrades exhausted at the daily clock; first
  governance-native cycle); forex V7 `FOREX_FREE_V7_REJECT_ALL`
  (terminal `f59ea0c` — cross-economy sham REPRODUCES the anchor, cluster
  #12; with V6 this closes the whole reaction-direction class); stocks
  V11 `STOCKS_FREE_V11_REJECT_ALL` (terminal `9d3a061`; cadence-latency
  falsified by shuffled-chain control, cluster #13); stocks V12
  `STOCKS_FREE_V12_BLOCKED_DATA_OR_SELECTION` (terminal `cc85fc5`; 0
  cells, 0/6 — all six proposals D2-killed measured: chain-structure
  rho 0.5822/0.2085 vs the V11 shadow; death-event self-subsumption
  0.9923).
- Main @ `4e71261` = SHV1 merge, pushed to origin. Live plans:
  crypto v17 / stocks v13 / forex v8 (RULES §7 has the GO registry).

## 4. ACTIVE cycles (each has an owner-dispatched A1 thread; measure first)

- **CRYPTO-V17** — mid prelaunch-remediation. Code freeze `fefa183`;
  families SILRES + ATTN-PHASE (of 6 blind proposals; FUNDJUMP
  ancestry-vetoed 0.2439, OICASCADE razor 0.1899 not selected). A7
  prelaunch REFUSED (`d4baecc`, 1 HIGH: SILRES anchor measured duty
  0.90%/1.08% per symbol outside the frozen feasibility band) →
  remediation loop is the expected arc (V15/V16/V8 precedent).
- **FOREX-FREE-V8** — also in prelaunch remediation as of 08:55
  (`997c850`, finding F1, zero-PnL plumbing fix). Family: FXFV8-A5-P1
  "US inflation-compensation term-structure dispersion" (slope z252;
  nominal-DGS10 level-form control mandatory). Lane-1 real-rate
  differential died BLOCKED_DATA in P0 (measured US-only on the keyed
  FRED catalog — 5 independent channels; non-US market real yields do
  not exist there). Q (dry-run + twin) PASS; INC-V8-2 (pin drift)
  resolved by restoring pinned bytes `5ca0bcea`.
- **STOCKS-FREE-V13** — substrate phase. Form-4 crawl 2,444/345,152 at
  08:58 (~1 doc/s sustained; SEC etiquette: 10-min silence windows that
  RELEASE the lock; 30-min cron watchdog relaunches; ETA ~93h ≈ Sunday).
  P0 FUNDABLE (dead-name canary 4/4; macro re-pins byte-MATCH 3/3);
  D1 six blind proposals frozen; D2 machinery ready and MUST NOT run on
  partial substrate. Optional speed experiments (pacing 0.25s window /
  official bulk channel with byte cross-verify) were offered to the
  owner — pre-authorized shape, census contract untouchable.
- Expect the next owner touches to be: two A7 prelaunch verdicts (V8
  first, V17 after remediation) → fresh GO phrases at their own gates.

## 5. SYSTEM-HARDENING-V1 (complete, merged, binding)

`SYSTEM_HARDENING_V1_PASS` (A7 `8b2a5ca`, 4 LOW all dispositioned).
Control plane on main: `researchctl` (list/doctor/pause/resume/locks),
canonical `cycle_registry@1` with atomic CAS writes + event journal,
retry taxonomy, dashboard purity (refresh leaves git status unchanged).
Bootstrap every cycle THROUGH it; never hand-edit `ACTIVE_CYCLES.json`.
Known follow-ups (SHV2 list in `research/governance/shv1/CLOSEOUT_REPORT.md`):
6 pre-existing test errors (`test_v9_universe_audit.py`, env-class — raw
data gitignored absent in fresh trees), worktree/branch cleanup (~56
worktrees/324 branches at closeout; archive-then-delete per manifest,
owner-authorized), content-addressed data store, registry closed-cycle
wording.

## 6. Dashboard (BUILT this window — first "app" of the program)

Merged + pushed (`e71e24e` merge, `effbe42` logo): stdlib collector →
self-contained Vietnamese HTML → pywebview window; opens via
`LabDashboard.command` (double-click); auto-refresh 30s; the collector
regenerates `plans/ACTIVE_CYCLES.json` (generated projection — with
worktree-existence semantics; the stale-wording follow-up is SHV2).
Evidence-first law holds (KHÔNG CÓ DỮ LIỆU for gaps; no CDN; tests 13/13).

## 7. Data, infrastructure, owner items

- **FRED key PRESENT** (owner-placed 2026-09-07; probe HTTP 200;
  CONTINUE.md carries current state). Not data authority by itself.
- **EODHD** $19.99/mo keep while stocks runs (V13 is).
- F-A7-T-1 kernel debt (verdict-neutral) still carried.
- Machine: 8 GB / 8-core; heavy lock enforces cap 1; schedule heavy
  phases off-peak; V13's SEC silence windows yield the lock — keep that
  pattern. Backups `~/staging_backups/` (manifest in-repo).

## 8. How the owner works (deltas this window)

- Vietnamese; simple-then-technical; decides via short imperatives;
  dispatches A1 threads personally — `git worktree list` + `researchctl
  cycle list` before assuming idle. **Asks questions to probe state —
  answer them, but treat only imperatives as authority.** Approves via
  cards/phrases; "merge và push đi" scopes exactly what it says.

## 9. Your first hour

1. Re-measure: pwd, branch, HEAD, porcelain, `git worktree list`,
   `research/researchctl.py cycle list`, heavy-lock registry, registry
   `--verify`; confirm 233/236 in the ledger.
2. Read the three ACTIVE cycle states from their control dirs (V8/V17
   prelaunch arcs move hourly; V13 substrate crawls to ~Sunday).
3. Emit your first independent status (§4.5).
4. Then keep the gates. 236 cells have said no; each no was cheap,
   recorded, and correct. The machinery — controls, gates that refuse,
   the lock that fails closed, the registry that remembers — is the
   product. Good hunting.

*Filed by the outgoing Lead. The books balance, the hardened plane is
live on main, and three cycles are moving toward their gates.*
