# GATES — DASHBOARD-AND-SHADOW-RELIABILITY-V1

Owner instruction 2026-09-24 (verbatim in session). Two apps:
Quant Shadow Dashboard (crypto, PROSPECTIVE-SHADOW-V1, 4 sleeves) and
Phorec (forex, FX-RANGEFADE-2M-SHADOW-V1, RANGEFADE-2M on EURUSD+GBPUSD).
Paper/shadow only; zero broker/order surface; no push/merge.

Measured at start (UTC): 2026-09-24T07:0x–07:5x. All findings below were
measured, not inherited.

## G0 — Authority & safety: PASS

- Cycles (plans/CYCLE_REGISTRY.json + `researchctl.py cycle list`):
  - PROSPECTIVE-SHADOW-V1 ACTIVE_LIGHT — integration worktree
    `.worktrees/prospective-shadow-v1/integration`, branch
    `orca/prospective-shadow-v1-integration`. Registry head 99e0026 is
    STALE vs measured: worktree had advanced to a8062b1a (3 commits:
    BANDRIDGE mount, dashboard 400k fix, fill-timing finding recorded
    not fixed per owner order) + 1 uncommitted file. Drift recorded;
    all subsequent commits by this task listed below.
  - FX-RANGEFADE-2M-SHADOW-V1 ACTIVE_LIGHT — worktree
    `.worktrees/fx-rangefade-2m-shadow-v1`, branch
    `orca/fx-rangefade-2m-shadow-v1`. Registry head 4bdfd0e STALE vs
    measured 50c7a465 (4 implementation commits: daemon, dashboard v2,
    app builder, restart-idempotent accounting). Drift recorded.
- Heavy lock: HELD_PROVEN by pid 22173 CRYPTO-HISTORICAL-REPLICATION-3F-V1
  data-staging (started 07:08:42Z, token match, flock held). This task
  acquired NO heavy lock and ran NO heavy job (test suites are offline
  and seconds-scale; data probe = 13 paced public reads, same class as
  the e-worker's own fetch path).
- Forbidden surfaces: no broker/order path touched; no S1; no
  credentials (workers are keyless public reads; FX feed is TrueFX
  indicative, read-only); no registry writes (CYCLE_REGISTRY.json is
  A1-writable — untouched); no history rewrite; no push/merge; ledgers
  append-only (verified byte-level in G3/G5 evidence below).
- Uncommitted changes found at takeover — PRESERVED then committed
  separately with provenance: integration worktree had
  `M research/control/prospective_shadow_v1/e/valuation_worker.py`
  (adds FAMILY_BANDRIDGE to valuation FAMILY_ORDER; file mtime
  08:11:38 +0700, valuation worker pid 68885 restarted 08:11:40 +0700
  with exactly this content → the running production worker already
  included it; commit 302d5f52 reconciles repo with production) and
  untracked `research/control/prospective_shadow_v1/audit/`
  (A7 artifact from the prior session; committed as evidence 887deb71).
- Foreign processes NOT touched: xauusd worker (4755), live-gateway
  (58774), sandbox view server (22766, SANDBOX-OVERFIT-3ASSETS — owner
  sandbox), http.server 8790, FX dashboard server (8093).

## G1 — Identity: PASS (crypto), PASS (forex), with 1 gap FIXED + 1 packet OPEN

- Crypto: `tests/test_shv1_identity_recovery.py` 11/11 — every manifest
  file re-hashed from bytes (sha256 + byte_len + git blob); verdict
  labels pinned; the 4th family (BTC4H-BANDRIDGE) entry completed this
  task to the same byte-level standard (gap found: entry had NO hash
  fields and its composite verdict label was not byte-quoted — fixed in
  28d923b2 with disclosed composite rule, see G3/G6).
- Executor identity pinning: `tests/test_shv1_worker_config.py` — all
  FOUR production executors construct against the REAL manifest through
  adapter.validate_config (identity-pinning path), frozen schedules
  weekly×2 + daily×1 + H4×1, cost books CURRENT_CONSERVATIVE_COST
  primary.
- Crypto signal parity to frozen engines: adapter suites
  `tests/test_shv1_families_identity.py` + `tests/test_shv1_engine_smoke.py`
  (virtual e2e through real decide paths) — green (suite totals below).
- Forex signal parity: daemon boot parity self-test (frozen
  v2_lib.f_rangeexp(0.3,0.7) vs daemon signal path on identical bars)
  — journal seq 38/39: EURUSD PASS, GBPUSD PASS (both boots measured).
- App identity: bundles rebuilt from exact worktree HEADs (see G5);
  no strategy/fill/cost law changed by this task. The ONE law question
  (BANDRIDGE sizing under costs) is NOT silently changed — regression
  tests pin current behavior both directions; owner decision packet:
  OWNER_DECISION_PACKET_bandridge_sizing_and_fill_law.md.
- NO_SIGNAL-CHANGE check: diff scope of every commit by this task:
  FX dtype ingest edge + tests; crypto display note + test pins +
  identity evidence completion + additive caps key mapping. No signal,
  capital, fee, or fill-law change. (Identity-relevant? The caps
  mapping closes a pinning gap without behavior change — disclosed in
  commit 236bf2f7.)

## G2 — Data & schedule: PASS with BLOCKED noted (BASISLV source healed; event still prospective)

- Crypto decision clock: e-worker heartbeat
  `results/prospective_shadow_v1/runtime/heartbeat.json` (inode-vs-path
  match true, interval 300s) — last_completed: XSECT daily 09-24T00:00Z
  OK; ILLIQ weekly 09-21 OK; BASISLV weekly 09-21 DATA_BLOCKED
  (UNAVAILABLE_FAIL_CLOSED, event 77a4c78…); BANDRIDGE H4 04:00Z
  UNAVAILABLE_FAIL_CLOSED (see G3). next_decision: XSECT 09-25T00:00Z,
  ILLIQ/BASISLV 09-28T00:00Z, BANDRIDGE 08:00Z (today).
- Basislv root cause (measured from ledger bytes): blocked_reason
  "missing 286 completed bar(s) in (2026-08-22T23:00Z, 2026-09-20T23:30Z];
  first gap at 2026-09-18T00:15:00Z" — vendor-side hole at decision
  time; fail-closed correct; the weekly event_id was consumed (no
  backfill, forward-only law holds).
- Source continuity probe (this task, production fetch path, paced):
  all 13 PREMFADE candidates, 15m, 30 days back → 2879 bars each,
  ZERO internal gaps; region covering the old 09-18 gap is fully
  served now. The 09-28 decision needs 08-29T23:00Z→; window covered.
  This is evidence about the SOURCE NOW, not a result: the 09-28
  verdict stays prospective (G7 NOT_RUN until the event).
- Valuation marks: premiumIndex bulk @5min; heartbeat
  valuation_heartbeat.json loop 73, marks_written 250, inode match
  true; marks at 07:05Z for all 4 families; ILLIQ RUNNING
  99,267.71; XSECT RUNNING 99,536.20; BASISLV/BANDRIDGE FLAT_OK
  100,000.00.
- Forex data/schedule: TrueFX poll 15s; H1 bars PIT (bucketed by the
  QUOTE's own timestamp, never wall clock); stale >15min → decisions
  stop; heartbeat written every loop; daemon had been DEAD 06:00Z–
  07:25Z (crash G4-1) — restarted 07:25Z, alive (heartbeats fresh).
  Status semantics measured in the served /health.json (daemon_alive
  false when heartbeat age >90s) — exercised in G4.

## G3 — Decision → virtual fill → accounting: PASS (mechanics + honest fail-closed), 1 ROOT CAUSE CLOSED for owner decision

- BANDRIDGE root cause (to the exact exception): sizing computes
  `qty = w * equity / ref_price` (executor._rebalance_steps L989) while
  the opening-buy cash guard requires
  `qty*fill_price + fee <= cash` (accounting.apply_fill L417-423) with
  `fill_price = ref + slippage_tick` and fee 0.0005 — for w=1.0:
  needed ≈ 100,050.02 > 100,000 → InsufficientCashError → the whole
  rebalance fails closed BEFORE mutation → ledger event
  UNAVAILABLE_FAIL_CLOSED, target_weights {BTCUSDT: 1.0} recorded,
  virtual_fill_events [], cash untouched. NOT a sizing-qty bug: the
  identical target with zero-cost books fills exactly weight 1.0.
  Same defect family as the recorded gross-1.0 tail-short finding
  (handoff_shv1-e-worker; shorts side already remediated by
  SIZING_AND_CAP_BASIS; the buy side never had an equivalent). NOT
  fixed unilaterally (owner constraint: exposure semantics change
  needs authority): regression tests pin both directions
  (tests/test_shv1_executor.py::test_weight_1_0_*), owner packet
  written with options A/B/C.
- Fill-timing mismatch (docstring "next H4 open" vs first completed
  15m bar) — already recorded-not-fixed by owner order (a8062b1a);
  included in the owner packet as question 2; nothing materialized
  (BANDRIDGE has 0 fills).
- Fill/accounting reconcile on books WITH fills: ILLIQ + XSECT marks
  reconcile to RUNNING equities via valuation (heartbeat above);
  engine-level: test_shv1_accounting / test_shv1_executor /
  test_shv1_valuation / test_shv1_combined all green — target→risk→
  cash→fee→slippage→fill→position→PnL path asserted, including
  identity assert per fill (equity moves only by MTM + booked costs).
- Forex fill mechanics: journal-based fills at live opposite quote,
  force-flat 20:00 UTC, restart replay idempotent
  (test_core_restart_account: full duplication collapses to identical
  state) — suite green (26/26 incl. 3 new dtype regressions).

## G4 — Runtime & restart: PASS (fix + live hour roll + live restart); feed-loss semantics verified at server level

- ROOT CAUSE of the FX daemon death (reproduced, not inferred): the seed
  parquet stores ms-unit ts (datetime64[ms, UTC]); live/replayed appends
  are ns-unit Timestamps; pd.concat cannot unify ms/ns and silently
  degraded the whole ts column to object → frozen engine's .dt accessor
  AttributeError at the first H1 boundary. The daemon had NEVER survived
  an hour roll (daemon.log shows 4 crash-loop generations: int(Timestamp)
  → missing `import json` → dtype crash). Fix f8bb2b73: normalize the
  seed ONCE at the ingest edge to datetime64[ns, UTC] (lossless for
  hourly bars); 3 regression tests pin the dtype through on_closed_bar
  and restore(); 26/26 FX tests pass.
- Live soak: daemon restarted 07:25:20Z; first real H1 boundary 08:00:00Z
  crossed CLEAN — journal seq 41/42 bar_closed EURUSD+GBPUSD (bar 07:00Z,
  target 0 → FLAT, no signal, no order — correct "no order when the
  market gives no signal"). NOTE disclosed: the 07:00Z bar is PARTIAL
  (built from quotes observed 07:25–08:00 after the mid-hour boot); the
  08:00–09:00 bar is the first complete one.
- Live restart test (owner law: restart never erases PnL, duplicates
  fills or drops a position): SIGTERM 28291 → clean stop → relaunch pid
  35609 → boot_replay restored both pairs (pos 0, realized 0.0,
  bars_restored 1 — the closed 07:00Z bar survived via journal replay),
  parity PASS both pairs, seq monotone (42→47, zero duplicate events),
  heartbeat fresh.
- Feed/worker loss semantics: FX /health.json reports daemon_alive=false
  when heartbeat age > 90s (verified live during the dead window:
  06:00–07:25Z the dashboard server kept serving last state while
  health showed the dead daemon; the Phorec app shows the OFFLINE/
  "Daemon sống" banner from the same health endpoint — captured live).
  Crypto workers: heartbeats with inode-vs-path checks (both true),
  valuation missing-price → UNAVAILABLE_FAIL_CLOSED (fail-closed law
  pinned in valuation_config + tests).

## G5 — Dashboard & .app: PASS (tests + rebuild + independent arithmetic + visual QA of both windows)

- Test suites: crypto engine 236 passed (incl. 4-sleeve sync + identity
  11/11 + executor 25 + smoke 5); dashboard app 57 passed (the previous
  "21 pass / 4 fail" 3-sleeve fixtures were already fixed at HEAD by the
  prior session's 400k commits — this task verified the ARITHMETIC
  independently instead of trusting green).
- Independent arithmetic (owner demand: verify the sum and the time
  anchor, not just the asserts): recomputed strict sums from RAW
  valuation_marks bytes for all 2,031 served combined-history points —
  1,981 exact matches, 50 gaps fail-closed with equity null, 0
  mismatches; mount-day invariant pnl = end − start − 100,000
  (flow BANDRIDGE @ 2026-09-24T01:10:00Z from its CAPITAL_SEED record,
  baseline 300,000 = 3 founding sleeves) with residual exactly 0.0.
  VERDICT ARITHMETIC_OK.
- Visual/display honesty: BANDRIDGE card shows FLAT with "0 fill đã thực
  hiện" (never fake RUNNING); BASISLV shows DATA BLOCKED; fail-closed
  banners rendered for both; totals 4-sleeve ($399,347.12 = Σ4 marks at
  08:10Z). Captured live screenshots of BOTH app windows.
- Rebuilds per repo process: Quant Shadow Dashboard.app rebuilt from
  dashboard worktree HEAD 61d86b43 (documented pyinstaller command;
  old bundle preserved at dist_prev_20260924-0810Z; new binary sha256
  939387ec2bcad877…; old a67229d3894ef2e6…). Phorec.app rebuilt via
  build_phorec_app.sh from FX worktree HEAD f8bb2b73 (staged build
  answered --check before replace; old bundle preserved at
  ~/Applications/Phorec-prev-20260924-150714.app; new binary sha256
  e6af66fccc644ac2…). Both apps launched and verified live: Phorec
  shows LIVE(paper), daemon alive, one-account $100k, fresh marks
  (sub-second age), next-decision countdown; crypto app shows LIVE,
  4 sleeve labels, honest statuses.
- Interactive tab-click QA was interrupted by OWNER ACTIVITY on the
  machine (owner opened/closed app instances and a macOS screenshot UI
  was frontmost mid-QA — the apps were also re-opened by the owner
  themselves, which is itself live evidence the apps work by
  double-click). Tab CONTENT was verified through the same page's API
  (/api/snapshot.json) rather than left unverified; no visual claim is
  made beyond the captured screenshots.


## G6 — A7 independent audit: CONFIRM (fresh-context, artifact A7-RELIABILITY-AUDIT-2026-09-24.md)

- A7 (independent agent, read-only + temp-dir pytest) re-measured all 5
  claim groups from bytes and live state: FX fix diff scope + 26/26
  tests + journal monotonicity/restart replay; crypto 6-commit diff
  scope (engine bytes identical except the disclosed additive caps key)
  + 52 tests + identity manifest re-hash (3 files match) + owner-packet
  numbers verified; ledger integrity (0 duplicate event_ids, fills
  exact vs the frozen cost law, heartbeat byte counts == on-disk);
  dashboard arithmetic (2,033 points match, gaps equity-null,
  mount-day invariant diff exactly 0.0); status semantics (BANDRIDGE
  chip FLAT + fail-closed banner, never RUNNING; BASISLV DATA BLOCKED).
  **A7 VERDICT: CONFIRM**, findings 1–3 non-blocking.
- Remediation decisions on the 3 findings (implementer + owner-facing):
  1) legacy FX journal rows 1–15 (03:25–03:54Z, pre-schema, no
     seq/event_id): LEFT UNTOUCHED — rewriting append-only journal
     bytes is forbidden; disclosed here and in the A7 artifact.
  2) no shutdown event type in the FX journal (SIGTERM evidenced
     indirectly via boot_replay + process start time): NOT patched
     post-CONFIRM (churn would invalidate the audited state);
     improvement option queued for the owner.
  3) BANDRIDGE 75 marks vs nominal grid: the gap fail-closed banner
     discloses it; app gap set matched A7's independent recompute —
     honest behavior, nothing to fix.

## G7 addendum (final sweep 09:00:52Z)

- FX 08:00–09:00Z bar — the FIRST COMPLETE bar — closed clean at
  09:00Z for both pairs (bar_closed seq 48/49, target 0 → FLAT, no
  order), daemon heartbeat 09:00:28Z fresh. G4's "two H1 closures" is
  satisfied with real events (08:00Z partial + 09:00Z complete).
- Crypto final sweep: e-worker pid 35779 loop 8 last_loop 08:56:21Z
  error null — last_completed: XSECT OK/OK @09-24T00:00Z, ILLIQ
  OK/OK @09-21T00:00Z, BANDRIDGE OK/OK @08:00Z (first OK), BASISLV
  DATA_BLOCKED @09-21 (healed source, verdict at 09-28). Valuation
  pid 35871: marks fresh, ILLIQ RUNNING 99,477.90 / XSECT RUNNING
  99,614.74 / both FLAT sleeves 100,000.00.
- Both .app windows were closed BY THE OWNER at 15:5x local ("window
  closed by user; exit 0; shadow workers untouched") after having been
  opened and used live — the apps are launch-on-demand; workers keep
  running independently (that separation is by design and verified).

## G7 — Prospective soak: PARTIAL by design (per-cadence events above; the stale placeholder section below is retained only for its task-commit list)

Real events observed this session (all PROSPECTIVE, no backfill):
- FX H1 (EURUSD+GBPUSD): 08:00:00Z boundary crossed clean — bar_closed
  both pairs (bar 07:00Z, PARTIAL from mid-hour boot, disclosed), target
  0 → FLAT, no order (market gave no signal — correct). 09:00:00Z
  boundary = first COMPLETE bar — checked at the end of this session
  window. Next decisions hourly 00:00–18:00 UTC; force-flat 20:00 UTC.
- BANDRIDGE H4: decision 08:00:00Z executed 08:16:30Z (fill-bar law):
  band_gate_on=1.0, donch_state=0.0 → NO breakout → target {} → FLAT,
  accounting OK — the sleeve's FIRST accounting-OK decision since mount
  (a legitimate no-trade; the weight-1.0 fill path remains gated by the
  owner decision packet for whenever the breakout fires; next 12:00Z).
- XSECT-FUND-CARRY-7D daily: last OK at 09-24T00:00Z; next 09-25T00:00Z
  (beyond this session) → NOT_RUN-as-of-report-time, worker scheduled.
- ILLIQ-AMIHUD-28D-W / BASISLV-PREMFADE-28D weekly: next 09-28T00:00Z
  (beyond this session) → NOT_RUN-as-of-report-time. BASISLV source
  continuity for that decision probed OK (30d, 0 gaps, 13/13).
- Production worker restarts (G4/G1 alignment): e-worker 65251→35779
  and valuation 68885→35871 restarted cleanly on SIGTERM; ledger byte
  counts IDENTICAL across the e-worker restart (idempotent restaging);
  all marks re-verified flowing after restart.
- The overall program gate is therefore PARTIAL: PASS for everything
  fixable/measurable now; remaining prospective events (FX 09:00Z+ bars,
  BANDRIDGE 12:00Z, XSECT 09-25, ILLIQ/BASISLV 09-28) are genuinely
  pending the market/calendar, and are listed as such — NOT claimed.

### Task commits (pathspec, no push/merge)

FX worktree (orca/fx-rangefade-2m-shadow-v1):
- f8bb2b73 dtype ingest fix + 3 regression tests (26/26 pass)

Integration worktree (orca/prospective-shadow-v1-integration):
- 302d5f52 valuation lane FAMILY_ORDER + BANDRIDGE (reconcile with prod)
- 12540ebe executor regression: weight-1.0 fail-closed pinned both ways
- 887deb71 land prior-session A7 artifact (evidence)
- 3bf495b7 anchor_note fix + engine test sync 3→4 sleeves
- 28d923b2 identity manifest completion + verifier extension
- 236bf2f7 caps verbatim max_abs_weight mapping + worker-config 4-family
  pins + smoke scoping

Post-fix suite totals: crypto shadow 236 passed (231 + 5 smoke),
dashboard app 40 passed, forex 26 passed.
