# REALPATH_PROOF — WNBA-WINPROB-2026-REMAINDER-V1 · Lane WNBA-REALPATH

Measured 2026-10-07 (worktree
`.worktrees/wnba-2026-remainder-v1/integration`, branch
`orca/wnba-2026-remainder-v1-integration`, head at lane start
`2c9db5e05402ac598ddd2dce55cf5a858e6c3042`).

## 0. What this closes

Gap: "WNBA 2026 has a ledger but no proven real path from pre-game data →
B1-WNBA → probability → ledger." This lane proves the REAL data path:

```
pinned snapshot (0ed97faf…) completed rows
  → result-present filter (stream-state law)
  → B1-WNBA verbatim rating stream (K=32 / HCA=50 / γ=0.65, tip-batch
    snapshot law, ordered by (tip, game_id))
  → state at each remaining-slate batch anchor (tip < anchor STRICT)
  → wnba26_predict() entries {match_id, tip_utc, p_home, p_away,
     state_digest, model_id, constants}
```

Entry point: `research/papertrade_wnba26/predict.py` — `wnba26_predict(
completed_rows, upcoming)`, a PURE function: no I/O, no network, no wall
clock, no randomness, no prints. Deterministic; byte-stable across runs
(test-enforced, both synthetic and real rows).

## 1. Pins re-measured at run start (all == pins)

| artifact | sha256 (first 8) | pin status |
|---|---|---|
| `wnba_schedule_2026.csv` (pinned snapshot) | `0ed97faf` | == pin |
| frozen engine `arms.py` (read-only source `wnba-playerfeat-scored-v1/integration/lanes/T_SELECT/`) | `82263eab` | == pin |
| frozen engine `harness.py` (same source) | `b9446f76` | == pin |

## 2. Census — pinned snapshot `refresh_20261007/wnba_schedule_2026.csv`

| measure | value |
|---|---|
| total rows | 360 (all `season == 2026`) |
| `status_type_state == "post"` (completed = HISTORY) | **345** |
| … of which `STATUS_FINAL` (result present → stream material) | **344** |
| … of which `STATUS_POSTPONED` (no result) | **1** — game `401857072` (DAL vs NY, tip 2026-07-17T01:00Z, "Travel Issues - Makeup date July 20", scores 0-0) |
| `status_type_state == "pre"` (remaining slate) | **15** |

Result-present law (FREEZE_PACKET §3: "tip_utc < batch anchor AND result
present"): the postponed row carries NO result and is EXCLUDED from the
rating stream — never inferred as an outcome (fail-closed would also reject
a FINAL row with equal scores; none exist). The rating stream therefore
consumes **344 result-present rows** of the 345-row HISTORY census; tips span
2026-05-08T23:30:00Z … 2026-10-04T20:00:00Z — **every completed tip is
strictly before the earliest remaining-slate anchor** 2026-10-07T17:20:00Z
(test-enforced on the real rows).

The 344 rows cover 17 franchise keys (ESPN team ids; one rating per
franchise); 55 completed tips are shared by multiple games (tip-batch law
exercised by the real stream); 1 completed row is neutral-site (HCA_eff=0).

## 3. State at SF1's anchor

- SF1 = game `401918297` (NY @ ATL, tip 2026-10-07T23:30:00Z, ET local_date
  2026-10-07). Its ET day-batch anchor = day_first_tip 2026-10-07T23:30:00Z −
  6h10m = **2026-10-07T17:20:00Z** (exclusive deadline).
- State fed to the stream: the 344 result-present completed rows with
  tip < anchor (all of them — verified independently by rebuilding the
  filtered stream and recomputing the digest: MATCH).
- **state_digest @ SF1 anchor**
  `8bdf1515159cc2227be338c92314b75edac65969210edc803e0ac2e70a1587ae`
  (sha256 of the sorted rating table, 17 lines `fk=repr(rating)`, UTF-8;
  a rating-table hash — no probability material enters it).
- All 15 upcoming entries share this one digest: every slate anchor
  postdates every completed tip, so each day-batch state contains the full
  344-row replay (the filter is structural, not incidental — see the
  mutation tests).

## 4. Per-game anchors (15 games, 11 ET game-dates)

`anchor = anchor_for_game(tip, day_first_tip) = day_first_tip − 6h10m`
(strict/exclusive); `per_game = tip − 6h10m` (per-row deadline variant).
Both reproduce FREEZE_PACKET §5 exactly (test-enforced, all 15 + all 11
gates). "X @ Y" = X at Y (Y is home side).

| game_id | tip_utc | ET local_date | matchup | day anchor | per-game anchor |
|---|---|---|---|---|---|
| 401918297 | 2026-10-07T23:30:00Z | 2026-10-07 | NY @ ATL | 2026-10-07T17:20:00Z | 2026-10-07T17:20:00Z |
| 401918298 | 2026-10-08T01:30:00Z | 2026-10-07 | LV @ GS | 2026-10-07T17:20:00Z | 2026-10-07T19:20:00Z |
| 401918299 | 2026-10-09T23:30:00Z | 2026-10-09 | ATL @ NY | 2026-10-09T17:20:00Z | 2026-10-09T17:20:00Z |
| 401918300 | 2026-10-10T01:30:00Z | 2026-10-09 | GS @ LV | 2026-10-09T17:20:00Z | 2026-10-09T19:20:00Z |
| 401918302 | 2026-10-11T04:00:00Z | 2026-10-11 | LV @ GS | 2026-10-10T21:50:00Z | 2026-10-10T21:50:00Z |
| 401918301 | 2026-10-11T18:00:00Z | 2026-10-11 | ATL @ NY | 2026-10-10T21:50:00Z | 2026-10-11T11:50:00Z |
| 401918303 | 2026-10-14T04:00:00Z | 2026-10-14 | NY @ ATL | 2026-10-13T21:50:00Z | 2026-10-13T21:50:00Z |
| 401918304 | 2026-10-14T04:00:00Z | 2026-10-14 | LV @ GS | 2026-10-13T21:50:00Z | 2026-10-13T21:50:00Z |
| 401918305 | 2026-10-17T19:30:00Z | 2026-10-17 | TBD @ TBD | 2026-10-17T13:20:00Z | 2026-10-17T13:20:00Z |
| 401918306 | 2026-10-20T00:00:00Z | 2026-10-19 | TBD @ TBD | 2026-10-19T17:50:00Z | 2026-10-19T17:50:00Z |
| 401918307 | 2026-10-23T00:00:00Z | 2026-10-22 | TBD @ TBD | 2026-10-22T17:50:00Z | 2026-10-22T17:50:00Z |
| 401918308 | 2026-10-24T19:30:00Z | 2026-10-24 | TBD @ TBD | 2026-10-24T13:20:00Z | 2026-10-24T13:20:00Z |
| 401918309 | 2026-10-27T00:00:00Z | 2026-10-26 | TBD @ TBD | 2026-10-26T17:50:00Z | 2026-10-26T17:50:00Z |
| 401918310 | 2026-10-30T00:00:00Z | 2026-10-29 | TBD @ TBD | 2026-10-29T17:50:00Z | 2026-10-29T17:50:00Z |
| 401918311 | 2026-11-01T00:00:00Z | 2026-10-31 | TBD @ TBD | 2026-10-31T17:50:00Z | 2026-10-31T17:50:00Z |

ET-day batch gates (full-slate, exclusive): ET 10-07 → 2026-10-07T17:20:00Z ·
ET 10-09 → 2026-10-09T17:20:00Z · ET 10-11 → 2026-10-10T21:50:00Z ·
ET 10-14 → 2026-10-13T21:50:00Z · ET 10-17 → 2026-10-17T13:20:00Z ·
ET 10-19 → 2026-10-19T17:50:00Z · ET 10-22 → 2026-10-22T17:50:00Z ·
ET 10-24 → 2026-10-24T13:20:00Z · ET 10-26 → 2026-10-26T17:50:00Z ·
ET 10-29 → 2026-10-29T17:50:00Z · ET 10-31 → 2026-10-31T17:50:00Z (all UTC).

TBD sides (Finals games) resolve to fresh-entry rating 1500 by the frozen
"new franchise entry" law — the entry point predicts whatever fixture it is
given, deterministically; ledger-side classification of those rows remains
the recorder's concern, not this lane's.

## 5. The path is proven; the probabilities are NOT here

**Real probabilities are computed only post-GO by execute.py calling this
entry (`wnba26_predict`); nothing is persisted pre-GO.** No ledger file
exists today; no real-game probability is stored or committed anywhere in
this lane's deliverables.

Disclosure (test family c): the self-test
`tests/papertrade_wnba26/test_realpath_predict.py::
test_c_real_path_fixture_ids_and_digest_stability` runs the entry on the
REAL completed rows + REAL upcoming fixture ids. The REAL engine p values
are computed IN MEMORY ONLY: no assertion inspects probability values,
nothing is printed, logged, or persisted, and the values are OVERWRITTEN
with synthetic placeholders (0.5) before any further use. Only counts,
fixture ids, tips and state digests are asserted. The engine's verbatim
equivalence to the pinned `arms.py` bytes is proven bit-for-bit on a
synthetic corpus (`test_a_verbatim_equivalence_to_pinned_engine`, sha-pinned
read-only import, re-hashed in-suite).

## 6. Test evidence

```
.venv/bin/python -m pytest tests/papertrade_wnba26 -q
79 passed  (67 pre-existing, untouched, + 12 new REALPATH tests)
```

New tests (`tests/papertrade_wnba26/test_realpath_predict.py`):
(a) synthetic replay determinism byte-stable ×2 + input-order invariance +
verbatim equivalence to pinned engine; (b) future-dated completed-row
mutation leaves state_digest unchanged (STRICT anchor boundary; pre-anchor
row changes it; POSTPONED row never enters state); (c) REAL rows + REAL
fixture ids (sha-verified snapshot), 15/15 ids, digest stability, one shared
state, placeholder overwrite; (d) anchor law exactness (dispatch pins
401918297 → 17:20:00Z, 401918298 → 19:20:00Z partial-batch form), fail-closed
validation, all 15 per-game anchors + 11 ET-day gates == FREEZE_PACKET §5.

## 7. Boundaries honored

$0 spent; no network; no `~/.config`; no GO typed or assumed; other
worktrees read-only (engine imported read-only, sha-pinned, never
modified); writes confined to `research/papertrade_wnba26/predict.py`,
`tests/papertrade_wnba26/test_realpath_predict.py`, this file, and the
lane handoff JSON; pathspec-only `git add`; no push.
