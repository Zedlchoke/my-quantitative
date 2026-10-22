# ERRATUM — EXEC-NBA-REWIRE (Lane E, cycle SPORTS-PAPERTRADE-EXEC-V1)

Written 2026-10-07. Scope: the NBA engine path of the EXEC runner
(`research/papertrade_exec/`), its pins, its battery, and the rehearsal
record. No real paper rows exist; the GO
(`GO SPORTS PAPERTRADE EXEC V1 RUN ALL`) remains REGISTERED_NOT_CONSUMED —
typed by the owner alone. $0 held; no network was used by any rehearsal or
test.

## 1. What changed

The NBA engine path is REWIRED from the blocked scored-corpus path to the
LAWFUL PROSPECTIVE PIT path landed by NBA-WINPROB-PROSPECTIVE-PREP-V1
(Lane D, content commit `65ebefc4`, lane final HEAD `82542aa8`, both trees
read-only for this lane):

* `adapters.py`: new `nba_engine_available` / `nba_engine_entry_drift` /
  `nba_engine_modules` / `nba_engine_predict` — lazy import of
  `research/papertrade_nba/loader.py` + `predict.py` at the pinned worktree
  path, pin-checked before any execution; plus the post-GO incremental
  payload-refresh plumbing (`nba_refresh_game_days` (pure),
  `espn_fetch_scoreboard` (network, post-GO only, same $0 no-auth endpoint
  lineage as the frozen 208 payloads), `nba_incremental_refresh`,
  `nba_payload_verdict`) and the multi-day window loader
  `load_nba_fixtures_window` (fixtures whose UTC TIP date lies in
  `[--date, --to-date]`).
* `execute.py`: NBA `probe_engine` now reports
  `WIRED_ENGINE_READY / BLOCKED_NBA_ENTRY / BLOCKED_PIN_DRIFT_ENTRY` against
  the `nba26` pins; REAL-mode NBA forecast = entry/pin checks FIRST, then the
  post-GO payload refresh for the batch's game-days, then
  `nba_engine_predict` at the batch anchor (mode=ENGINE rows post-GO; the
  sandbox rehearsal keeps storing labeled SYNTHETIC rows);
  `--to-date` extends `plan/forecast/quote/decide` with the multi-day NBA
  batch window (single-day behavior unchanged); `nba26_root` added to the
  pinned roots.
* `__init__.py` `verify_pins`: the NBA data-pin branch now uses the
  manifest-aware `nba_payload_verdict` (composite == frozen pin OR the
  lawfully chained `REFRESH_MANIFEST.jsonl` extension; everything else
  fail-closed). `nba_payload_composite` retained.
* `pins.json` / `PINS.md`: new `nba26` package (loader.py
  `2679be80f1fb7f7d9862f76b65e546708aac3df6654fa7e8d866aedecd6461c8`,
  predict.py
  `57f0c810f8cd1a12d78bcb68881ca49b6d8bdb16a4a0f61a11dfcc7987c6d81c`,
  dispatch_head "65ebefc4 (content) / 82542aa8 (final)"); `nba_harness`
  package annotated RETAINED-FOR-BATTERY-ONLY; the NBA data pin documents
  the refresh-manifest contract.
* Battery: 8 new NBA tests (28 → **36/36 PASS**); sibling suites re-run
  read-only with clean trees: WNBA **79/79**, SOCCER **94/94**, NBA-prep
  **81/81**.
* REHEARSAL_REPORT.md: NBA wiring row + new §7 (NBA success-path rehearsal,
  census, disclosures); §2 row 13 wording fixed per A7 F1 (see §4 below).

## 2. Why the old path is DEAD (disclosed, never worked around)

The pre-rewire path routed real NBA ratings through the SCORED cycle's
harness corpus (`harness.real_loader.load_oos_corpus(mask_outcomes=False)`).
That read is outcome-bind-token-gated by the SCORED cycle's own law: the
token (namespace REAL) is mintable only by ITS postgo gate after ITS own
owner-GO check, for ITS (retired-unconsumed) phrase. This cycle's GO is a
different phrase and **cannot mint that token** — the refusal
(`BLOCKED_NBA_CORPUS_BIND`, exit via `OutcomeBindRefused`) was therefore
permanent for this cycle, disclosed in the rehearsal report and the A7
packet, and never improvised around.

Disposition of the old code — marked DEAD, not deleted (removal is the
riskier change):

* `adapters.nba_real_corpus_read`: kept, docstring-marked
  `DEAD / UNREACHABLE since EXEC-NBA-REWIRE`; no caller reaches it.
* `adapters.nba_engine_replay_synthetic` (scored-harness pure functions on
  SYNTHETIC inputs): kept because the battery's history test exercises it;
  explicitly NOT the forecasting engine.
* `execute.compute_forecasts` no longer raises
  `BLOCKED_NBA_CORPUS_BIND`; the `nba_harness` pins stay (battery-only) with
  a RETAINED-FOR-BATTERY-ONLY note.

## 3. The new data contract

* **Source**: ONLY the frozen ESPN per-date scoreboard payloads
  `~/.my-quantitative-data/nba-winprob-prospective-prep-v1/espn_schedule_2026_27/`
  (208 files, composite pin `3d527b3c1b3a215dc1bf480a79776602f3b8c4ee1f68463102c05d8ae2bc25e6`,
  recipe = sha256 of the newline-joined per-file sha256 list, lexicographic
  by filename). The scored cycle's bind corpus is never read, never needed,
  and no bind token is ever minted on this path.
* **Completed-only law**: `load_completed` returns FINAL rows with tip
  STRICTLY `< asof_anchor_utc` (tip == anchor excluded; leak-impossible by
  construction, defensively re-filtered inside `replay_completed`). Battery
  proves an injected FINAL row with tip `>` anchor AND tip `==` anchor moves
  neither `p` nor `state_digest`.
* **Upcoming law**: `load_upcoming` returns SCHEDULED rows with tip `>=`
  the window start; `nba26_predict` refuses any forecast target whose tip is
  already past the anchor.
* **Warm-up**: ratings init at R0 = 1500, the 2016-17 season-start value
  carried from the successor packet pre-registration
  (`SUCCESSOR_PACKET_SCORED.md`: "WARM-UP (streams run, never scored): NBA
  seasons 2016, 2017") — a CARRIED pre-registration, not a new fit.
* **Frozen model law** (quote-only, never re-fit): B1_STAR constants
  K=32 / HCA=100 (prediction-only) / gamma=0.75 quoted from the scored
  cycle's `SELECTION/selection_real.json` (sha-pinned in Lane D's
  FREEZE_ADDENDUM_PIT_LOADER.md); `p_home = 1/(1+10^(-(R_H+100-R_A)/400))`,
  `R <- R + 32*(S-E)`, season boundary `R <- 1500 + 0.75*(R-1500)`.
* **Corpus extension (post-GO only)**: the incremental refresh fetches
  per-date payloads for the batch's game-days (same $0 no-auth endpoint
  lineage as the frozen 208), writes bytes + a `.meta` record (frozen
  format) and appends a self-hashed `REFRESH_MANIFEST.jsonl` record chain
  anchored at the frozen composite (each record: prev_composite →
  new_composite + valid record self-sha). Verification accepts composite ==
  frozen pin OR the fully-chained manifest extension; bytes-vs-meta mismatch,
  missing meta, unrecorded bytes, or a chain break all fail closed
  (`BLOCKED_NBA_PAYLOAD_TAMPER` / `BLOCKED_PIN_DRIFT`). PRE-GO the refresh
  refuses (`BLOCKED_NO_GO` defense-in-depth) and is never executed — the
  frozen snapshot is the only lawful PRE-GO state.

## 4. Carried disclosure (VERBATIM, byte-faithful to the scored cycle)

Carried unchanged from the scored cycle via Lane D's
FREEZE_ADDENDUM_PIT_LOADER.md §7 — **slope 0.8107, NO recalibration**:

> pooled OOS F1–F5 2022–2026 LL 0.639953, Brier 0.223545, n=6,605;
> calibration slope 0.8107 BELOW [0.85,1.15] — overconfidence sign;
> NO recalibration on viewed OOS

This cycle runs the same frozen law UNCHANGED — no refit, no recalibration,
no coefficient edits, on the viewed OOS or anywhere else.

## 5. Report wording fix (A7 F1, LOW)

REHEARSAL_REPORT.md §2 row 13 said run-day reports go "to `sandbox/`, never
`runs/`". Precise wording now: SANDBOX run reports are written under
`<data-root>/sandbox/`; the one file that exists under `<data-root>/runs/`
is the REAL-mode pre-GO refusal artifact (a `BLOCKED_NO_GO` refusal JSON
only, zero rows) produced by the refusal rehearsal — itself evidence of the
gate working. No data violation; wording precision only.

## 6. Evidence

* Rehearsal: `rehearsal/exec_nba_rewire_rehearsal.json` — 8-row opening
  window (2026-10-20/21), anchor 2026-10-20T12:50:00Z, completed=0 ⇒ all
  ratings R0=1500, p_home = 0.640065 (= 1/(1+10^(−100/400))), digest
  `f2d59f35…`, chain forecast→quote→decide→(dup no-op)→settle→dashboard all
  exit 0, census GENESIS 1 / FORECAST 8 / MARKET_QUOTE 8 / DECISION 8 /
  SETTLEMENT 2, SANDBOX banner + chain_ok. Persisted rows SYNTHETIC; engine
  probabilities in-memory only.
* Battery: `tests/papertrade_exec/test_exec_battery.py` 36/36.
