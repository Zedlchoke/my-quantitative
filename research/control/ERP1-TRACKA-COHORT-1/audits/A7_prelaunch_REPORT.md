# A7_prelaunch_REPORT — ERP1-TRACKA-COHORT-1 — independent fresh-context prelaunch audit

Auditor: A7 PRELAUNCH (fresh context; no prior A7 artifact of this cycle read
before this audit; the A7 plan-audit reports under the root tracka_cohort1
namespace were read for the first time as evidence during this audit).
Scope: GO-1 chain audit of cycle ERP1-TRACKA-COHORT-1. READ-ONLY except this
report and the paired handoff JSON. No backtest, no PnL computation, no
download, no worker/process touch (verify-alive only), no registry write,
nothing committed.

## Measured state (this audit's own measurements, 2026-09-25 19:00–19:40 UTC)

- Root `main` @ `460d2acdf9c4dc3970a6dddbbdc36b08178f02a3` (matches expected).
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/erp1-tracka-cohort-1/integration`,
  branch `orca/erp1-tracka-cohort-1-integration`, HEAD
  `215ce855328d29b911bd05edecbe30c2aa623fa7`, `git status --porcelain` EMPTY
  (tree clean at tip).
- Heavy lock: `researchctl.py locks inspect` → `FREE_PROVEN`
  (`flock_state: free`, `pid_alive: false`); last history row is this cycle's
  `build_bars.py USDCAD` (released).
- FX-RANGEFADE-2M-SHADOW-V1 daemon PID 79157 ALIVE (`shadow_daemon.py`),
  dashboard PID 8093 ALIVE. UNTOUCHED by this cycle (evidence §F).
- Tests: `pytest tests/ -q` → **33 passed** in 0.96 s (worktree cycle tests,
  root `.venv`).

## A. GO law — VERIFIED

- `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/GO1_gate/GO_RECORDED.json`
  (root): `go_phrase_received = "GO ERP1 TRACKA COHORT 1 REGISTER AND
  COUNCIL"`, `match: EXACT` — byte-identical to plan §0 line 38
  (`plans/PLAN_erp1_tracka_cohort_1.md`).
- Registry row `ERP1-TRACKA-COHORT-1` (root `plans/CYCLE_REGISTRY.json`,
  LIVE working-tree state): `ACTIVE_LIGHT`, budget `{used: 0, max: 24}`,
  `go_phrase = "GO ERP1 TRACKA COHORT 1 SCORED"` (the GO-2 phrase),
  `go_phrase_state = REGISTERED_NOT_CONSUMED`, `head =
  215ce855328d29b911bd05edecbe30c2aa623fa7` (= measured tip), `s1 =
  SEALED_UNTOUCHED`, phase `P4_A7_PRELAUNCH`.
- GO-2 NOT consumed: worktree-wide grep for the GO-2 phrase hits ONLY the
  plan's own definition (line 43); zero hits in any cycle artifact; ledger
  contains zero scored rows; budget 0/24.
- Lifecycle/phase/head consistent with this audit's measurements. GO_RECORDED
  records GO received at root main `69ddc604…`; measured: `69ddc604` IS an
  ancestor of `460d2acd`, and `460d2acd` is exactly the registration commit
  ("register ERP1-TRACKA-COHORT-1 under owner GO-1 … researchctl write,
  only-own-row verified"). Consistent.
- FINDING F1 (see Findings): the same 19:23:14Z registry update that moved
  phase/head also set `workers: 0 → 1`, contradicting both lane handoffs
  (`workers: 0`) and measured truth (no TRACKA worker process exists;
  heavy lock FREE). Registry bookkeeping inconsistency — CONDITION C1.

## B. Hash chain — VERIFIED

Ancestry measured with parent linkage (`git log --format='%h %p'`):

```
460d2acd (base = current root main)
  └─ 43a84688  data-gate work commit (port, probes, download, census, tests)
      └─ 2682422a  data-gate structured handoff (bookkeeping)
          └─ 3931aed8  falsifier work commit (battery, freeze, ledger seed)
              └─ 5b89e1ee  falsifier handoff (bookkeeping)
                  └─ 43cb8b1f  clock-placebo REBUILD per ADJUDICATION #2
                      └─ 215ce855  falsifier handoff update (bookkeeping) ← tip
```

Linear, single-parent at every node, no merge commits, no force events; root
`main` still exactly `460d2acd`. Tree clean at tip.

## C. Data gate — VERIFIED (recomputed from bytes)

- `DATAGATE_REPORT.md` verdict lines: `PROBE_PASS` + `BUILD_PASS` ×2
  (AUDUSD, USDCAD).
- Committed census bytes == working bytes:
  - `census_AUDUSD.json` sha256 `d337ff2c4e499238f6552c525cebf2027bbd5f2b876babc4e3e086fd09233473`
  - `census_USDCAD.json` sha256 `27958f5a6b67ae017dea8bf35cf006868249926b03ff518ceb7663725ff35758`
  (both also match the sha_chain pins in ledger row 2).
- Gate fields recomputed from census JSON (schema `tracka_census@2`):
  - AUDUSD: midweek_tradable_share 0.98611 (margin +0.08611),
    nonpos_spread_minutes **0**, bars15_valid **130,160** (>100k), dup gate
    True, reconcile max_abs_diff_pips 0.0 ≤ 5e-4; price_range_violations 0.
  - USDCAD: 0.98607 (+0.08607), **0**, **130,102**, True, 0.0; 0 violations.
  - All five gates `True` in both files.
- Session buckets: all 8 fixed-UTC buckets n ≥ 312 (AUDUSD min = sunday_open
  312; USDCAD min = sunday_open 321); `low_sample` lists EMPTY in both
  censuses (LOW_SAMPLE_BUCKET absent). OPEN + CLOSE quantiles (p50–p99) present
  per bucket and overall, both pairs.
- m1 manifests: committed `m1_manifest_AUDUSD.json` sha256
  `f869cfa32210194c3c743fca99a1bb9c660e3bed15c492843d8e7e2d974e5396`,
  `m1_manifest_USDCAD.json` `0f9a7df78bcaf481229db1a1a45f6d94da9c61073a95f2c8641b80ec675b01db`
  (matches report's "head" prefixes). Each manifest has **4,014 entries**,
  `days_missing: []`, window 2021-01-01..2026-06-30; raw files on disk:
  4,014/pair (count match).
- **Spot-check 5 files/pair recomputed from raw bytes** (sha256 + byte count,
  deterministic spread across the window incl. a 2026 file): **10/10 OK**.

## D. Falsifier battery — VERIFIED (with two bookkeeping findings)

- `trial_ledger.jsonl`: **27 rows** (2 datagate BUILD_PASS, 1 F-5 M3 kill,
  2 F-5 M1 report-only, 2 F-PIT-1 PASS_PIT, 2 F-1 disclosure, 2 mode-sham,
  14 F-6 populations, 2 F-3-control-rebuild CONSTRUCTIBLE). Every row carries
  all three mandatory labels (`SINGLE_SOURCE_PANEL`,
  `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`, `PAPER_TIER`); `net_pnl` /
  `gross_pnl` are null in every row (programmatic check: 0 violations).
- (1) M3 kill row (row idx 2): `falsifier_id F-5`, `mechanism_id M3`,
  `verdict NOT_SCORED_FALSIFIED`, kill_line 2.0, measured_stress_rt 4.8,
  margin 2.8, base RT 2.4; arithmetic **2 × 2.0 × 1.2 = 4.8 ≥ 2.0** reproduced
  from `census_USDCAD.json` bytes: buckets london_07_12 / ny_overlap_12_16 /
  ny_late_16_21 OPEN p50 = 1.2, 1.2, 1.2 (n = 28,390 / 22,787 / 27,811;
  n-weighted mean exactly 1.2). Moot conditions (V-1, T-1, T-2, T-3)
  explicitly recorded as not-run.
- (2) F-PIT-1 verdicts and all five M-tests recorded with margins; report
  numbers match `falsifier_results.json` bytes: M-1 arrays equal (PASS),
  M-2 share 0.229903 / 0.203757 (3,349/14,567; 2,983/14,640, gate ≥ 2%),
  M-3 bar disagreement 0.16654 / 0.19617 + day-flip 43.0%/63.4% disclosed,
  M-4 fixture committed and passing, M-5 R-ORIG T0 share 0.72111 / 0.74961
  (LEAK_PROVEN) with R-ANCHOR 0 differing days. F-1 pooled |rho| 0.135166 /
  0.121374 (gate ≤ 0.20). Limb (iii) matched pairs 337 / 306 ≥ floor 20.
- (3) Five mandatory freeze pins present in
  `freeze/GO1_freeze_artifact.json` (`pins.(i)_seeds` bootstrap 20260925 +
  mode-sham 20260925 + storage path; pins file written 19:00:17Z before
  consuming computations; `(ii)_holdout_pass_membership` — sha256 RECOMPUTED
  from the pinned membership blob = `45ff897d3075d806…` **MATCH**;
  `(iii)` mode-sham outcome vocabulary verbatim per plan §10; `(iv)`
  two-pair identical UTC close semantics; `(v)` seam limb (iii) minimum-N
  floor 20 fail-closed). Skeptic-amended clock-placebo predicates recorded;
  per-pair r = 0.908093 / 0.887120 recomputed as
  (occ_anchor + 0.10)/occ_natural — match to 1e-6; before/after occupancy
  (0.6583→0.4534 AUDUSD; 0.6566→0.4393 USDCAD) recorded; new
  arm_config_digests (6f754a82303e8160 / c53a04331318728a) in registry +
  membership pin; signed zero-PnL statement sha `f91c317cc1adcc6b…`
  recomputed **MATCH**.
- (4) Skeptic `ADJUDICATION #2` (root `SKEPTIC_cohort1_REPORT.md`) read; the
  rebuild matches its text on every binding clause: one-shot r calibration
  (measured r within the adjudication's stated expectation ≈0.909/≈0.886),
  uniform-random in-session entry hours from the pinned seed deliberately NOT
  the anchor's hour distribution, seed 20260925 unchanged, ONE occurrence
  consumed (`occurrence: ONE … any second rebuild is unavailable`),
  BLOCKED_F3_CONTROL fail-closed recorded, A2.2 freeze obligations met
  (subject to FINDING F2 on the `arm_config_digest_old` field).
- (5) No-PnL sweep (adversarial): `expectancy|profit_factor|win_rate|sharpe`
  hits only negation/law statements; `net_*` tokens are the null `net_pnl`
  ledger fields plus `net_pips` which exists ONLY inside the ported ancestor
  `engine.py` `run_strategy`/`metrics` — and **no script, test or artifact
  imports or calls engine's scoring path** (grep: only docstring mirror
  reference in `tracka_lib.py`). `falsifier_results.json` and
  `falsifier_rebuild_results.json` contain zero non-null net fields. **No
  arm-level net number exists anywhere in the cycle namespace.**
  `rebuild_results_sha256` 15e41d5c… matches the file.

## E. Holdout virginity — VERIFIED

- Only two parquet read paths exist in the falsifier machinery
  (`falsifier_run.py:231`, `placebo_rebuild.py:74`); BOTH immediately filter
  `df["ts"] < 2026-01-01T00:00:00Z` before any SignalPlane/statistic
  construction. `HOLDOUT_START` constants occur only as window strings.
- Falsifier outputs (`falsifier_results.json`,
  `falsifier_rebuild_results.json`, freeze artifact, ledger): zero references
  to bars ≥ 2026-01-01; every "2026" token is the seed `20260925`, a
  substring of the r value, or the declared holdout window STRING
  (`holdout_untouched_here: "2026-01-01..2026-06-30"`).
- Planes/parquets on disk are FULL-window by plan design (data gate §5.2/§6
  mandates the full 2021-01..2026-06 census; the 15m/1h planes — port and
  ANC-convention — are mechanical OHLC aggregations + a convention-diff QA
  report, not arm statistics). Verified no falsifier output consumed the
  holdout segment (read paths above). The holdout-membership pin
  (`(ii)`, sha `45ff897d3075d806…`) freezes who may read it later.
- Finding F4 (INFO): the full-window census/plane files are the residual
  holdout-adjacent surface; documented here so the scored phase reads them
  only through holdout-aware paths.

## F. Boundaries — VERIFIED

- S1: no S1 access, request or surface anywhere in the cycle namespace
  (registry `s1: SEALED_UNTOUCHED`; grep clean — apparent hits were
  `bars15`/`bars1h` substrings).
- Daemon FX-RANGEFADE-2M-SHADOW-V1: PID 79157 + dashboard 8093 alive
  (verify-alive only). Its namespace's 4 files with post-GO mtimes
  (`shadow_state.json`, `daemon_heartbeat.json`, `equity_curve.json`,
  `shadow_journal.jsonl`) are the daemon's OWN live runtime writes — its own
  lanes, permitted. No tracka script writes that worktree (references in
  `duka_lib.py`/`build_bars.py`/`engine.py` are read-only docstring lineage
  citations; the falsifier report attests the daemon source was never read).
- Heavy lock FREE_PROVEN at audit time (see Measured state).
- workers: both lane handoffs claim `workers: 0` and process scan confirms
  ZERO TRACKA workers — but the registry row says `workers: 1` (FINDING F1 /
  CONDITION C1).

## G. Tests — VERIFIED

- Full cycle suite run by this auditor from the WORKTREE with the root venv:
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/ -q`
  → **33 passed, 0 failed** (data gate 20 + falsifier 12 + rebuild fixture 1).
- Spot-run: `test_m5_truncation_pit_synthetic` **PASSED**;
  `test_m4_self_test_blindness_fixture` **PASSED**.

## H. Denominator / orientation — VERIFIED

- Observed counter = ledger rows = **27** (pre-PnL battery rows only).
- Published = 27 (FALSIFIER_REPORT §9: 25 seed + §12: 2 rebuild rows).
- Zero scored cells: no scored verdict class in any ledger row; no
  `fold_or_holdout_tag` other than `PRE_PNL_BATTERY`/dev-fold populations.
- Budget: registry `used 0 / max 24` — untouched.

## Findings

- **F1 — MEDIUM (registry consistency).** Registry row `workers: 1` (set by
  the 2026-09-25T19:23:14Z update, writer "A1 … Clock-placebo rebuilt per
  skeptic ADJUDICATION #2") contradicts both lane handoffs (`workers: 0`),
  the checklist expectation, and measured truth (no TRACKA worker process;
  heavy lock FREE). Evidence: `git diff plans/CYCLE_REGISTRY.json` (root,
  uncommitted), cycle-list row, `ps` scan. Disposition: **CONDITION C1** —
  normalize to the measured value 0 (or record the intended meaning) before
  GO-2 is typed.
- **F2 — LOW (freeze-artifact field defect).** In
  `freeze/GO1_freeze_artifact.json`, `clock_placebo_rebuild.per_pair.*.
  arm_config_digest_old` duplicates the NEW digest (6f754a82303e8160 /
  c53a04331318728a) instead of the superseded natural-recipe digests, which
  were `1309837df94cff94` (AUDUSD) and `b43204afc449f295` (USDCAD) per
  commit `3931aed8`'s freeze artifact. FALSIFIER_REPORT §12's claim "old
  digests retained in the rebuild section" is therefore factually wrong;
  A2.2 traceability currently requires git archaeology. Disposition:
  **CONDITION C2** — before GO-2, correct the field or append a signed
  erratum to the freeze artifact recording the true superseded digests.
- **F3 — LOW (wording precision, recorded not blocking).** The freeze's
  `amended_predicate_text_verbatim` is an ASCII-normalized rendering
  (≤ → <=, × → x) with a parenthetical denominator clarification quoted from
  A2.1, not byte-verbatim against the skeptic's "Exact predicate text as
  frozen" sentence. Clause-by-clause semantics are identical (a–f verified).
  Disposition: recorded; no condition.
- **F4 — INFO.** Full-window census JSONs and bar parquets (port + ANC) exist
  machine-local by plan design; holdout protection rests on the verified
  read-path filters + membership pin. Documented for the scored phase.
- **F5 — INFO.** Root checkout working tree is dirty (registry, skeptic
  report/handoff edits uncommitted; untracked control dirs). Root owner
  space is outside this lane's authority; the LIVE registry state (working
  tree) is what this audit measured and it matches the branch tip. Flagged
  so the owner commits root bookkeeping in its own discipline.
- **F6 — INFO (pre-existing, other cycle).** Doctor carries accepted-
  historical HIGH frozen-artifact-drift findings (CRYPTO-V17 / FOREX-V8 /
  V12 class) and a LOW `HEAD_MISMATCH` + stale heartbeat on the
  FX-RANGEFADE-2M-SHADOW-V1 row (daemon itself alive). None belongs to this
  chain; no TRACKA doctor finding exists.

## VERDICT

**PRELAUNCH_PASS_WITH_CONDITIONS**

The GO-1 chain is clean on substance: GO law exact, hash chain linear and
measured, data gate recomputes from bytes, the M3 kill arithmetic is
reproducible from the committed census, all five freeze pins verify (membership
sha recomputed-match), the ADJUDICATION #2 rebuild conforms, no net-return
number exists anywhere, the holdout was never read by any output, S1/daemon/
lock boundaries hold, 33/33 tests pass, denominator 27 = 27 with budget 0/24.
The two conditions below are bookkeeping-grade and BINDING before GO-2:

1. **C1:** Registry row `workers` normalized to the measured truth `0`
   (currently `1`) — or an explicit owner-side record of the intended
   meaning — before GO-2 is typed.
2. **C2:** Freeze artifact `arm_config_digest_old` fields corrected (true
   superseded digests `1309837df94cff94` AUDUSD / `b43204afc449f295` USDCAD
   from commit `3931aed8`) or a signed erratum appended, before the scored
   phase reads the freeze artifact.

— A7 PRELAUNCH (quant-auditor), 2026-09-25T19:40Z, fresh context, nothing
committed by this audit.
