# A7 Independent Audit Log — MARKET-DATA-PLANE-V1

Auditor: A7 (fresh context, independent). Commit audited: `42981b1b1f66ed03e0a933db0a5ef7041220d80e`.
Worktree: `.worktrees/market-data-plane-v1/a7-audit` @ `orca/market-data-plane-v1-a7-audit` (HEAD = 42981b1).
Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`. Date: 2026-09-09.

Method: every gate claim re-derived from bytes. Gate JSONs were read as claims, not evidence.
All probes written outside the repo (`/tmp/a7_audit_tmp`) or into this audit directory only.
The machine-wide heavy lock was only ever inspected read-only; the foreign STOCKS-FREE-V13
worker (pid 6418) was never killed, contended, or disturbed. The full repo pytest was NOT run.

---

## Item 1 — SHV1 M0 operational closure — PASS

- `python -m pytest tests/test_cycle_registry.py tests/test_heavy_lock.py tests/test_scheduler.py
  tests/test_protocol_registry.py tests/test_atomic_io.py tests/test_legacy_adapters.py
  tests/test_diagnostic_persistability.py tests/test_registry_reconcile.py
  tests/test_lock_job_reconciliation.py -q` → `112 passed in 2.97s`, exit 0.
- `researchctl locks inspect` → `HELD_PROVEN`, evidence: pid 6418 alive
  (`os.kill(pid,0)`), process-start token `ps:Wed Sep  9 17:55:05 2026` matches the registry
  row exactly (`token_match: true`), flock state `held`. Verdict vocabulary is exactly the
  frozen tri-state.
- `researchctl cycle doctor --json` → 9 findings: 1 LOW (stale heartbeat of paused CRYPTO-V17,
  labeled expected) + 8 HIGH. All 8 HIGH map 1:1 to the two explanation classes recorded in
  `gates/M0_SHV1_POST_ADOPTION.json`: 6 `EXPECTED_EPHEMERAL_STAGING`
  (V12_CLOSEOUT_VERIFICATION.json x4, PAUSE_CRYPTO_V17.json x2) + 2
  `POST_PAUSE_EVOLUTION_OUT_OF_SCOPE` (PAUSE_CRYPTO_V17 pins p0_freeze_v17.json /
  reconcile_v17_daily.py). Independently verified:
  `git log f3903f8..42981b1 -- '*PAUSE_CRYPTO_V17*' '*V12_CLOSEOUT*'` → 0 commits (MDP never
  touched those packets); `git check-ignore` proves the `.worktrees/**` staging paths are
  gitignored by the root `/.worktrees/` rule (raw staging data must not be restored per contract).
- `researchctl job list` → `job_view@1`, reconciled view; the live V13 row carries
  `"source": "heavy_lock"`, full liveness object with `token_match: true`, and an explicit
  `control_state_drift: null` field. Sources are labeled as required.
- Projection equality recomputed independently:
  `governance.cycle_registry.load('plans/CYCLE_REGISTRY.json')` →
  `projection_bytes()` sha256 `6a3a6e11b76ffae6683d8842fff0d98681ebd3d2935322e03bfd2960e3b2eefc`
  == `plans/ACTIVE_CYCLES.json` sha256 (same). `BYTE EQUAL: True`. Projection contains
  STOCKS-FREE-V13 ACTIVE_LIGHT, FOREX-FREE-V9 PLANNED_NOT_STARTED (placeholder 000… head),
  MARKET-DATA-PLANE-V1 ACTIVE_LIGHT — registry includes the current cycle set.

## Item 2 — Provenance / license — PASS

- Fresh read-only clone of https://github.com/Aryan-20-04/mdrap into `/tmp/a7_audit_tmp/mdrap_audit`,
  checkout `7bc831ccde5b3d97dd784aeeb51e2d17982771c3` (HEAD verified). Nothing executed from it.
- All 59 entries of `upstream_manifest.json.file_sha256` recomputed from the clone: 59/59 match,
  0 mismatches, 0 missing. The one tracked upstream file not listed, `src/fastpath.dll`, is a
  forbidden binary that is explicitly named in `forbidden_from_import` (never inspected/used;
  hashing not required).
- LICENSE: text is MIT (`MIT License` / `Copyright (c) 2026 MDRAP Platform Contributors`,
  matching the manifest `copyright_line`); its sha256 `33f80e45…eb406` matched (part of the 59).
- Dependency lock vs environment: `pip list` shows dvc 3.67.1, hypothesis 6.168.0,
  pandera 0.33.1 — equal to `dependency_freeze.json` pins; `install_verification.versions_match_pins`
  claim confirmed independently. Lock contains 93 resolved artifacts, none deferred.
- Licenses read from installed dist-info bytes (not from the notice):
  dvc `licenses/LICENSE` = Apache License 2.0; hypothesis METADATA `License-Expression: MPL-2.0`
  and LICENSE.txt contains "Mozilla Public License Version 2.0"; pandera `licenses/LICENSE.txt`
  = MIT License. `docs/THIRD_PARTY_NOTICES.md` states all three correctly (including the
  MPL-2.0 "measured" correction) plus the exact MDRAP pin, license, and LICENSE hash.

## Item 3 — No competing strategy/execution stack — PASS

- Scanned `research/market_data_plane/*.py` (13 modules):
  - strategy/risk/portfolio/broker/order/execution terms: single hit is the docstring
    disclaimer in nautilus_bridge.py line 41 ("No strategy, risk, portfolio, broker or
    execution code is introduced here").
  - forbidden MDRAP components (shm/sbe/fastpath/multicast/excel_bridge/exporter/security/
    strategy_sdk/broker/live/mdrap): no code hits.
  - network clients (requests/urllib/socket/websocket/ccxt/httpx/aiohttp): none in the plane,
    none in tests/test_mdp_*.py or tests/mdp_hypothesis/.
  - deferred-project imports (rd_agent/skfolio/dagster/qlib/openlineage/mlflow/
    great_expectations/arcticdb): none.

## Item 4 — Exact arithmetic and clock semantics — PASS

- `python -m pytest tests/test_mdp_models.py -q` → `29 passed in 0.46s` (matches P5 claim).
- Golden 1 hand-verified from first principles: `Decimal('0.1')` is exact `0.1`
  (binary-float `0.1+0.2` = `0.30000000000000004` shows what is being avoided).
- Golden 2 hand-verified: `(Decimal('0.00001')+Decimal('0.00002'))/2 == Decimal('0.000015')`
  exactly (binary float gives `1.5000000000000002e-05`).
- event_id determinism: built one event via the plane API and recomputed the id independently
  from the frozen rule (`sha256` of 0x1F-joined
  `schema_version|source_id|venue|instrument_id|event_type|exchange|receive|available|sequence|raw_sha256`):
  both `a8f00ec67b0779674e3a3062ce84a97429d1d1590e840bca8047fd130262500f`. MATCH.
- Clock semantics: float timestamp → `MALFORMED_SHAPE` ("float timestamp rejected; timestamps
  are int UTC ns"); string timestamp → rejected; negative receive time and available<exchange →
  `IMPOSSIBLE_TIME_ORDER`.

## Item 5 — Archive immutability + corruption visibility — PASS

- `python -m pytest tests/test_mdp_archive.py -q` → `29 passed in 0.33s`.
- Live probes in `/tmp/a7_audit_tmp` against a real 5-record chunk written through
  `archive.write_chunk` (temp+fsync+replace+read-back-verify):
  - Append probe: appended `{"evil":true}` to the published chunk. `verify_chunk`'s report
    records `content sha256 d9ce7cf5… != path name b4920154…` (verify_chunk is documented to
    return a diagnostic report rather than raise, so callers can route corruption); a re-put of
    the pristine payload then raises `HashDisagreement` (fail closed, never overwrite). Not silent.
  - Corruption probe: flipped one mid-file byte. `verify_chunk` report errors again non-empty;
    `scan_orphans` lists the file under `sha_mismatch_chunks`. Corruption is visible through
    two independent paths.
- Note: I first ran `verify_chunk` without reading its returned report and it "returned no
  error" — that was my probe's bug, not the plane's; the report object is the contract
  (docstring: "Never raises for findings … so callers … can route corruption visibly").

## Item 6 — Deterministic replay from a DETACHED tree — PASS

- Cloned the root repo to `/tmp/a7_audit_tmp/replay_clone`, checked out the frozen SHA
  `42981b1b1f66ed03e0a933db0a5ef7041220d80e` (detached). My worktree is also exactly at
  the frozen SHA.
- Built a 100-event archive (4 chunks x 25 TRADE/QUOTE events, manifests via
  `put_chunk_records` with entitlement evidence) in `/tmp/a7_audit_tmp/replay_data`.
- Replay in fresh subprocesses, explicit manifest list + predicate:
  - Tree A = integration-frozen worktree, cwd=worktree, PYTHONHASHSEED=1
  - Tree B = detached clone, cwd=/tmp, PYTHONHASHSEED=999
  - Both: `{"event_count": 100, "stream_digest": "4f2939a0e45dfba7b027df41fd669ddda99f48050ae7c7ad5d29110ec2b075c6"}`.
    Byte-identical.
- Newer-file nondiscovery: added a 5th chunk + manifest (event at ns 9e9, not in the list);
  replay from the clone with PYTHONHASHSEED=7 returns the identical digest and event_count=100.
  No silent discovery.
- Note: the `orca/market-data-plane-v1-integration` branch tip has since advanced to `b344f45`
  ("MDP-V1 run control: … G11 A7 in flight from frozen 42981b1");
  `git diff 42981b1..b344f45` touches only run-control files (event_log.jsonl, heartbeat.json,
  state.json) — no audited code. Recorded as LOW objection OBJ-1 for traceability.

## Item 7 — Quality/quarantine non-silence — PASS

- `python -m pytest tests/test_mdp_quality.py tests/test_mdp_quarantine.py -q` → `36 passed`.
- `except … pass` census in `research/market_data_plane/*.py`: three sites, all read:
  - `archive.py:103 except OSError: pass` — unlink of the temp file during exception
    unwinding; the original exception is immediately re-raised. Not swallowing.
  - `_pandera_spike.py:707/723` — validation calls inside *timing benchmark* loops where
    rejection is the expected outcome being measured; the module is the isolated dev-only
    spike (not imported by any production module), not a data path.
- No `except Exception: pass` anywhere in quality/replay/quarantine paths.

## Item 8 — BBO/depth/TCA correctness — PASS

- `python -m pytest tests/test_mdp_bbo.py tests/test_mdp_depth.py tests/test_mdp_tca.py -q`
  → `68 passed`.
- Independent TCA recompute (exact Decimal, from the frozen formulas and the fixtures' own
  comment arithmetic — test_mdp_tca.py:153-165):
  - realized spread H=1e9: `2*(+1)*(100.02-100.03)/100.02*1e4` = `-1.99960007998400319936…`
    → equals the fixture literal `-1.9996000799840032` under float().
  - effective spread: `2*(-1)*(99.98-100.03)/99.98*1e4` = `10.0020004000800160032…` → equals
    fixture literal `10.002000400080016`.
  - impact proxy: `(100.03-100.02)/100.02*1e4` = `0.99980003999200159968…` → equals fixture
    literal `0.9998000399920016`.
  (A naive left-to-right float evaluation differs in the 12th digit — confirming the plane's
  Decimal core is what produced the literals.)
- `bbo.py`: `staleness_threshold_ns` is a REQUIRED parameter of evaluation calls
  (`is_quote_stale` validates it as int ns; no hidden default). Consolidated BBO records
  `reference_currency` per A1 ruling A4_Q2 (bbo.py docstring line 249).

## Item 9 — Nautilus compatibility — PASS

- `python -m pytest tests/test_mdp_nautilus_bridge.py -q` → `25 passed in 2.27s`.
- `nautilus_trader==1.230.0` installed (pip list).
- Spot round-trip (my own one-off, reusing the suite's AAPL.XNAS Cfd instrument, precisions 2/1):
  QUOTE event bid `100.04` ask `100.06` sizes `5`/`7` → `QuoteTick` prints
  `100.04 / 100.06 / 5.0 / 7.0`; `ts_event == 1_000_000_001` (exchange) and
  `ts_init == 1_000_000_003` (available) exactly; bid/ask round-trip exact at declared
  precision (sizes print `5.0` because the instrument declares size precision 1 — value-equal).
  Also observed: `build_event` without explicit quality status defaults to QUARANTINED and the
  bridge refuses it (`BridgeQualityError … pass diagnostic_only=True`) — the fail-closed default
  from A1 rulings works end-to-end.
- `to_bar(...)` raises `NotImplementedError(BAR_NOT_MAPPED_IN_V1)` ("mdp.market_event@1 has no
  BAR type; OHLCV can never become q[uotes/depth]").

## Item 10 — No credentials / raw licensed payloads in git — PASS

- Secret-pattern grep over the full `git diff f3903f8..42981b1` (128 files, +21,887/-252):
  every hit is (a) the manifest secret-denylist machinery (`_SECRET_KEY_PATTERN` regex, doc
  sections), (b) parameter names (`api_key` as a function argument in adapter-checklist docs —
  no values), or (c) evidence JSON describing the scans. No literal secret values
  (`"api_key"/"token"/"password"/"secret": "<8+ chars>"` grep: zero).
- `write_token` fields in registry journal events are operator labels
  (`resume:FOREX-FREE-V8`, `register:STOCKS-FREE-V13:…`), confirming the deferred-scan claim.
- Non-text/odd additions in the diff: `.dvc/config` (0 bytes — see item 11) and
  `tests/data_fusion/adapters/fixtures/truefx_ticks_usdjpy.csv` — 3 rows of obviously synthetic
  boundary timestamps (20240101 22:00:00.123 / .456 / 23:59:59.999), adopted verbatim from the
  audited Data Fusion pin commit (be6f680), not raw provider payload.

## Item 11 — DVC transport proof + zero scientific mutation — PASS

- `researchctl program counters` → `236 published / 239 observed logical, 0 survivors`
  (forex 42/42, crypto 155/158, stocks 39/39); s1 `SEALED_UNTOUCHED`. Matches
  `dvc_poc_result.json.zero_scientific_mutation` exactly.
- Registry sha256 NOW: `d41ed3af68e6b74e44b9a98c04888b77f3bffdf1343923103433d2e4fe856d68` —
  equals the (truncated) value recorded pre/post POC, proving the registry is unchanged since.
- Disposable remote `/Users/hoangminhlong/.my-quantitative-governance/mdp_dvc_remote` exists
  (contains `files/`), retained as audit evidence per the bounded cleanup list.
- No experiment/ranking artifacts in the integration worktree: no `dvc.yaml`, no `.dvc/plots`,
  `.dvc/tmp` holds only dvc's normal state (btime/lock/rwlock), no `exp` artifacts.
- Tracked `.dvc/config` is 0 bytes (carries nothing — no credentials, no host path);
  the host-private remote path lives in `.dvc/config.local`, confirmed gitignored
  (`git check-ignore` matches).
- NEG evidence read: NEG1 absent object dvc exit 1; NEG2 recorded DVC-LIMITATION-1 (3.67.1
  local-remote transfer does not re-hash on pull) with detection delegated to the mandatory
  plane manifest-verification layer — an honest, disclosed limitation rather than a hidden one;
  NEG3 wrong pointer exit 1.

## Item 12 — Hypothesis profile reproducibility — PASS

- Ran the CI profile myself: `python -m pytest tests/test_mdp_hyp_models_quality.py -q`
  (default profile) → `11 passed in 15.29s`.
- `tests/mdp_hypothesis/profiles.py` registers `mdp_ci`
  (derandomize=True, max_examples=50, deadline=None, suppress_health_check=[], print_blob=True)
  and `mdp_deep` (derandomize=False, max_examples=500, rest same) — character-for-character the
  frozen `architecture_freeze.json.hypothesis_profiles`; unknown HYPOTHESIS_PROFILE values raise.
- Honesty of `oss/hypothesis_result.json` ("no real counterexamples discovered"): grep for
  "counterexample" across tests/ returns nothing — no golden test claims Hypothesis origin, so
  nothing contradicts the absence claim; the invariant set is additionally covered by
  deterministic goldens (database_rule honored).
- Tightened contract: `strategies.py` draws `manifest_sha256` via `hex64()` at both call sites
  ("A1 ruling A2_Q1: required 64-hex in @1") — the strategy can no longer generate None, and
  `models` rejects null (verified in item 4 build attempts: missing manifest_sha256 →
  `MALFORMED_SHAPE`).

## Item 13 — Pandera decision vs frozen criteria — PASS

- `oss/pandera_spike_result.json`: decision `PANDERA_EVALUATED_NOT_ADOPTED`; criteria table:
  5 PASS, 2 FAIL — (1) identical row-set/reason attribution FAIL (one type-poisoned raw row
  makes the strict dtype contract reject the whole batch where native rejects just that row;
  macro attribution differs), (2) runtime regression FAIL (8.3x–267x median). The frozen rule
  is adopt-requires-ALL, so NOT_ADOPTED follows deductively from the recorded evidence; the
  native validator retained; pandera stays installed as dev-only evidence dependency.
- `python -m pytest tests/test_mdp_pandera_spike.py -q` → `6 passed`.
- Import isolation independently verified: importing each of the 11 production modules
  (models, quality, replay, archive, bbo, reason_codes, depth, tca, quarantine, manifest,
  _canonical) in a fresh subprocess leaves no pandas/pandera/dvc/nautilus_trader in
  `sys.modules`. No production module imports `_pandera_spike` (grep).

## Item 14 — Zero runtime import/install of deferred projects — PASS

- `git diff f3903f8..42981b1 | grep -iE "rd_agent|rdagent|skfolio|dagster|qlib|openlineage|
  mlflow|great_expectations|arcticdb"`: only documentation and adoption-matrix entries
  (design-only references are authorized by plan §4.4/§4.8); zero imports.
- `pip list` shows none of the deferred projects installed.
- `requirements.txt` (repo) not modified in the range (name-only diff: no requirements hits).

## Item 15 — Full-suite result and resource precondition — PASS

- `locks inspect` run FIRST (read-only): `HELD_PROVEN` by STOCKS-FREE-V13 pid 6418
  (token match, flock held) — the foreign worker owns the machine-wide slot.
- `gates/P5_battery.json` records the full repo pytest as `NOT_RUN_RESOURCE_CONFLICT`
  with the correct justification; every other component is a targeted suite.
- No evidence of a full-suite attempt: event_log.jsonl (9 events) contains no full-suite
  event; all battery evidence cites targeted commands. I did NOT run the full suite and did
  not contend.

## Item 16 — Tree/worktree/worker state — PASS

- Integration worktree `git status --porcelain`: empty (clean).
- `git worktree list`: 6 MDP worktrees (a2, a3, a4, a7, a8, integration) all directly under
  `.worktrees/market-data-plane-v1/`, none nested inside another; the `m0-governance` worktree
  is absent (removed as claimed; M0 commit 6643359 was cherry-picked into integration).
- V13 worker: `ps -p 6418` alive, etime 02:35:18, still running
  `p0d_bulk_ingest_v13.py` — untouched throughout the audit.

---

## Verdict rationale

All 16 audit items independently PASS. No HIGH or CRITICAL objections. One LOW objection
(OBJ-1) is recorded for traceability: the integration branch tip advanced past the frozen
audit SHA with run-control-only bookkeeping while A7 was in flight (no audited code changed).
Per plan §11, `MARKET_DATA_PLANE_V1_PASS` requires zero HIGH/CRITICAL from A7 — satisfied
against the audited SHA 42981b1.
