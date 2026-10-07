# VERIFY_20261007_NFL_CADENCE_V2 — independent verification report

Role: INDEPENDENT VERIFIER (did none of the verified work). Method: adversarial,
from bytes; every verdict = command + observed output; missing evidence = NOT_RUN.
Read-only everywhere except this report dir. Interpreter
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`; $0; no network; no heavy jobs.

Object: cycle `NFL-WINPROB-NG-SCORED-V1`, worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration`,
branch `orca/nfl-winprob-ng-scored-v1-integration`, audited wave SHA `5bc05278f77211d315001469987b2143199a06f1`.

Verify instant: 2026-10-07T00:41Z (before the claimed next fire 2026-10-07T17:00Z).

## 0. State re-measure — PASS

| Check | Command | Observed |
|---|---|---|
| HEAD == audited SHA | `git -C <wt> rev-parse HEAD` | `5bc05278f77211d315001469987b2143199a06f1` |
| Branch | `git -C <wt> branch --show-current` | `orca/nfl-winprob-ng-scored-v1-integration` |
| Tree clean pre-run | `git -C <wt> status --porcelain` | empty |
| Wave commit single, parent | `git log --format="%H %P" -1 5bc05278` | parent `8983fefc3377290bb97196b6d0bf7f6c3367aac2` (w7 evidence commit, Oct 6 17:04Z) |
| Registry row head == HEAD | read `plans/CYCLE_REGISTRY.json` cycles[] | `head: 5bc05278f77211d315001469987b2143199a06f1` == measured |

## A. Law artifacts — PASS

- `lanes/EXEC/CADENCE_ERRATUM_R1.md` exists at HEAD (66 lines, `git show --stat` in wave commit). Clause-by-clause vs owner law:
  - single LOWEST un-recorded REG week ≥5, season 2026 — §1 ✔
  - window `6h ≤ (earliest kickoff K − now) ≤ 72h`; `>72h → NOOP window-not-open` (logs window-open instant K−72h); `<6h → NOT_RUN capture-window-missed`, no partial batch, no backfill ever — §2 ✔
  - prev-week (W−1) fully ended = final score present OR kickoff+4h ≤ now; otherwise NOOP prev-week-incomplete listing un-ended games — §3 ✔
  - NOOP-with-evidence to `~/.my-quantitative-data/nfl-ng-scored-v1/cadence/fire_log.jsonl`; ELIGIBLE and NOT_RUN fire there too — §4 ✔
  - NEVER a farther week while a nearer week pending ("lowest capturable week, batch now" declared DEAD) — §1 ✔
  - lock HELD while ELIGIBLE → wait/retry in window, never kill foreign worker; window closes → NOT_RUN_RESOURCE_CONFLICT — §5 ✔
  - executor UNCHANGED, layering decision recorded (§6) ✔
  - weeks 5–7 IMMUTABLE, 129 rows, chain head `67e89b2e8e5c01ad…`, no re-forecast ever — Immutability § ✔
- `lanes/EXEC/CADENCE.md` is v2: gate-first Step 2 with `--fire-log`; NOOP → STOP (fire log line IS the evidence); Step 4 TWO-FIELD reconciled freeze root with `execute_post_go.py = 87553cdc…` and `record_owner_go.py = f196c765…`; MANUAL_CADENCE fallback names week-8 window `[2026-10-27T00:15Z, 2026-10-29T18:15Z]` from opener `2026_08_CAR_GB 2026-10-30T00:15Z` ✔
- Dead v1 rule gone from the runbook: `grep -rn "capturable\|batch now\|batch NOW"` over EXEC runbook tree hits only the two DEAD declarations (ERRATUM line 22, CADENCE.md line 4). Historical v1 wording confirmed only in commit `65ebf0be` (superseded). ✔
- MINOR (doc nit, non-blocking): erratum §3 uses `kickoff + 4h ≤ now`; CADENCE.md Step 2 paraphrases `kickoff+4h < now`. The gate code implements `<=` (erratum wins); boundary differs only at the measure-zero instant `K_prev + 4h == now`.

## B. Gate code — PASS

Read `lanes/EXEC/cadence_gate.py` (174 lines) in full. Law-relevant behavior confirmed by reading: REG 2026 weeks 5..18 only; weeks iterated in ascending order, first un-recorded week decides and the function returns → a farther week is never taken; `hours < 6` → NOT_RUN capture-window-missed; `hours > 72` → NOOP window-not-open (inclusive 6/72 boundaries eligible, matching the erratum); prev-week ended = score OR `kickoff+4h <= now` (zoneinfo `America/New_York`, DST-correct); `now >= K` → permanent capture-missed notice, evaluate next week; `HELD_PROVEN` while otherwise-eligible → NOOP lock-held; `--fire-log` appends exactly one JSON decision line (mkdir -p); no writes other than the fire log; exit 0/0/1 for ELIGIBLE/NOOP/NOT_RUN.

Snapshot pin: `shasum -a 256` on `~/.my-quantitative-data/nfl-ng-scored-v1/raw_schedules_w7_20261006/games.csv` = `1896f36a70ab2157ee5f2de9e2c8c6a39cd378083ceb032d8c3a4332325ab2c7` == required sha ✔

Independent hand re-derivation (my own minimal reimplementation written from the law text only, `/tmp/verify_cadence_v2/indy.py`, does NOT import the gate), on the REAL snapshot + REAL ledger (recorded weeks = {5,6,7}):

| Scenario | Independent result | Real gate CLI result | Expected |
|---|---|---|---|
| now 2026-10-13T17:00Z | NOOP window-not-open, wk 8, hours 391.25 | identical (hours_to_kickoff 391.25, window opens 2026-10-27T00:15Z) | NOOP ≈391h ✔ |
| now 2026-10-27T17:00Z | ELIGIBLE wk 8, hours 55.25, 14 games | identical (games list = week-8 set) | ELIGIBLE ≈55.25h ✔ |
| prev-week-7 completeness | last w7 kickoff 2026-10-27T00:15Z + 4h = 04:15Z ≤ 17:00Z | gate returns no `un_ended_games` | complete via kickoff+4h law ✔ |
| now 2026-10-29T19:30Z | NOT_RUN capture-window-missed, 4.75h | identical (exit 1) | NOT_RUN <6h ✔ |
| Oct-27 + HELD_PROVEN | NOOP lock-held | identical | NOOP lock ✔ |
| DST across Nov-1 | `2026_08_BAL_BUF` (Sun 2026-11-01 13:00 ET) → `2026-11-01T18:00Z` (EST −5; DST ends 02:00 local Nov 1) | gate parser identical | 18:00Z EST ✔ |

Week-8 opener from real bytes: snapshot line `2026_08_CAR_GB,2026,REG,8,2026-10-29,Thursday,20:15` → America/New_York EDT (−4) = `2026-10-30T00:15:00Z` ✔ (gate parser and independent code agree).

## C. Test suite — PASS

- Committed evidence `lanes/EXEC/cadence_tests/cadence_tests_evidence.json` (sha `edf3d881ed6397c6eeb015bbdd9d7d5420971c560139690d488630ae4db4c45e`): `checks_total: 27, checks_failed: 0`; required scenarios present: Oct13 NOOP (S1, S2R), Oct27 eligible real-bytes (S2R), duplicate (S3), no-farther-week (S4), capture-missed advance (S5b), postponement both sides (S6a target flex + S6b prev-week postponed), lock (S7), DST (S8a/b), immutability (S9). ✔
- I re-ran `lanes/EXEC/cadence_tests/test_cadence_gate.py` myself: `TOTAL: 27/27 checks`, exit 0. Regenerated evidence **byte-identical** to committed (sha `edf3d881…` equal; `diff` empty). `git status --porcelain` after the run: **empty** — no file modified at all, so nothing needed restoring (redirect-then-restore precedent not triggered). Re-run output == committed evidence. ✔
- Observation (non-blocking): S9 compares the real-ledger sha to itself — tautological as written; real immutability is independently established in battery D below. Sandbox writes confirmed confined to `cadence_tests/sandbox/` + the evidence file; real ledger/snapshot read-only.

## D. Immutability — PASS

Ledger `~/.my-quantitative-data/nfl-ng-scored-v1/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl` (file sha256 `7d9af2867b480f08c7b195398e15f927fd45172e25899130125a7e8f1a922c90`):

- Exactly **129 rows**: week namespaces 45×`2026_05_` + 42×`2026_06_` + 42×`2026_07_`, positionally contiguous ✔
- **Zero (game_id, arm_id) duplicates**: 129 pairs, 129 unique ✔
- Hash algorithm verified from `research/control/NFL-WINPROB-NG-SCORED-V1/ledger/nfl_ng_ledger.py` source (`row_hash = sha256(canonical_json(row minus row_hash))`, FIELD_ORDER insertion order, `,`/`:` separators). Independent full 129-row walk (my own code): row0 prev == `GENESIS:` + recomputed sha256(FREEZE_PACKET.md bytes) = `9978a950…`; linkage + per-row re-hash **intact, zero breaks** ✔
- Segment heads: row 45 = `d2de7f48f8a0…` (matches committed w5 audit); row 87 = `42b00271fd41…` (matches `audit_w6_20261006/recompute_output.txt` lines 37/111); row 88 prev == row 87 hash (w7 batch joined exactly onto the w6 head) ✔
- Final chain head: `67e89b2e8e5c01ad3b6df915f461713f417d71b8a239f8e1d2c4c78105650750` — prefix `67e89b2e8e5c01ad` ✔; equals `REAL_W7_NOTE.md` and `real_w7_20261006_gate_log.jsonl` (`chain_head=67e89b2e8e5c…`) ✔
- Time law: `recorded_at_utc < kickoff_utc` strict on 129/129; w7 batch uniform `2026-10-06T17:03:36Z` ✔
- Untouched by the wave: ledger mtime `2026-10-06T17:03:39Z` **precedes** wave commit `2026-10-07T00:30:53Z`; `git show --stat 5bc05278` touches ONLY `lanes/EXEC/CADENCE.md`, `CADENCE_ERRATUM_R1.md`, `cadence_gate.py`, `cadence_tests/*` (11 files, +652/−50) — no F_FREEZE, no research/, no ledger-adjacent path ✔

## E. Registry + executor unchanged — PASS

- Registry row `NFL-WINPROB-NG-SCORED-V1`: `head` == `5bc05278…` == measured HEAD; `budget {used: 0, max: 9}`; `go_phrase_state: "OWNER_GO_TYPED_LIVE 2026-10-06T10:45:02Z at head 8288a25e…"`; `updated_at 2026-10-07T00:31:04Z` (post-wave head sync). ✔
- `execute_post_go.py` sha256 = `87553cdcb3b940cbac3c82035637a124cd51ba28e549a523decd04f5d2be1685` — ERRATUM_R6 pin held; executor bytes unchanged (layering decision held). ✔
- `record_owner_go.py` sha256 = `f196c76540f180ffd9f6c6442a393d0082f6088e56aaf5fc987517614b5ecd8e`. ✔
- Freeze digests r4/r5 untouched: wave commit touches no freeze paths; `lanes/F_FREEZE/freeze_digests.json` last commit `3bf01582` (w7 pin, pre-wave); `controller_freeze_roots/` (r5 `reconciled_r5_20261006`, r6, w7 roots) mtimes all pre-wave. ✔

## F. Automation config — attestation-consistency PASS; scheduler direct inspection NOT_RUN (by design)

- The id `automation-990d5fb2` appears in-tree **only** as the claim in CADENCE.md §"Automation of record"; no scheduler config artifact exists in the workspace and I did not (cannot) call the scheduler → direct config inspection is NOT_RUN per dispatch design. Everything the claimed prompt references was instead verified against artifacts:
  - (i) 2026-10-06 'batch now' rule DEAD — CADENCE.md line 4 + ERRATUM §1 ✔
  - (ii) gate-first `lanes/EXEC/cadence_gate.py` with `--fire-log` — file at HEAD ✔; argparse `--fire-log` present ✔
  - (iii) NOOP → STOP with fire-log evidence — CADENCE.md Step 2 ✔
  - (iv) ELIGIBLE-only executor per runbook v2 two-field root — CADENCE.md Steps 4–5; both reconciliation shas measured equal on disk ✔
  - (v) weeks 5–7 immutable — ERRATUM Immutability § + CADENCE.md header ✔
  - (vi) next fire 2026-10-07T17:00Z — wave enacted 2026-10-07T00:30:53Z; daily 17:00Z schedule ⇒ next fire same day 17:00Z ✔ (and 00:41Z verify instant precedes it; the fire-log dir `~/.my-quantitative-data/nfl-ng-scored-v1/cadence/` does not exist yet — consistent; the gate `mkdir -p`s it on first append, so the referenced path resolves)
  - ledger path `~/.my-quantitative-data/nfl-ng-scored-v1/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl` exists (100,834 B, 129 rows) ✔; snapshot-dir convention matches existing `raw_schedules_w6_20261006` / `raw_schedules_w7_20261006` ✔
- **No unresolved reference.** Every path and SHA the claimed prompt uses resolves in the tree/data dir.

## G. Next-window math — PASS

K = 2026-10-30T00:15Z (`2026_08_CAR_GB`, earliest week-8 kickoff in the real snapshot).

- Eligible window `[K−72h, K−6h]` = **[2026-10-27T00:15Z, 2026-10-29T18:15Z]** — matches CADENCE.md fallback ✔
- Daily 17:00Z fires (assuming schedule holds, week 7 ended — last w7 kickoff 2026-10-27T00:15Z + 4h = 04:15Z — and lock FREE_PROVEN):

| Fire | K−now | Verdict |
|---|---|---|
| Mon 2026-10-13T17:00Z | 391.25h | NOOP window-not-open ✔ (dispatch-expected) |
| Tue 2026-10-20T17:00Z | 223.25h | NOOP window-not-open ✔ (dispatch-expected) |
| Mon 2026-10-26T17:00Z | 79.25h | NOOP window-not-open |
| **Tue 2026-10-27T17:00Z** | 55.25h | **first ELIGIBLE** ✔ |
| Wed 2026-10-28T17:00Z | 31.25h | ELIGIBLE |
| Thu 2026-10-29T17:00Z | 7.25h | ELIGIBLE (deadline 18:15Z) |
| Fri 2026-10-30T17:00Z | −16.75h | NOT_RUN (window blown / games started) |

## Verdict table

| Battery | Verdict |
|---|---|
| 0 State re-measure | PASS |
| A Law artifacts | PASS (1 MINOR doc nit) |
| B Gate code + independent re-derivation | PASS |
| C Test suite re-run | PASS (byte-identical 27/27; 1 observation S9) |
| D Ledger immutability | PASS |
| E Registry + executor pins | PASS |
| F Automation attestation | PASS on attestation; scheduler direct = NOT_RUN (by design) |
| G Next-window math | PASS |

**OVERALL: PASS** — the wave commit `5bc05278` enacts exactly the owner law; the gate reproduces my independent re-derivation on real bytes for every required scenario; the committed 27/27 evidence regenerates byte-identical; weeks 5–7 (129 rows, chain `67e89b2e…`, w7 joined onto w6 head `42b00271…`) are intact and untouched; executor pins and freeze digests unchanged; every automation-prompt path/SHA resolves.

## Anomalies / observations (none blocking)

1. MINOR: CADENCE.md Step 2 paraphrases prev-week completeness as `kickoff+4h < now` vs the erratum's `≤ now` (gate implements `≤`). Measure-zero boundary; recommend aligning the runbook wording at the next law edit.
2. Observation: test S9 (real-ledger immutability) is self-comparing (sha vs same sha) — tautological; independent verification supplied by this report's battery D.
3. Informational: `~/.my-quantitative-data/nfl-ng-scored-v1/cadence/` does not exist yet — expected before the first post-enactment fire (2026-10-07T17:00Z); the gate creates it on first append.
4. NOT_RUN by design: the ZCode scheduler config for `automation-990d5fb2` is outside the repo and was not called; its attestation consistency was verified via the referenced artifacts (battery F).
5. Ledger file sha256 recorded for continuity: `7d9af2867b480f08c7b195398e15f927fd45172e25899130125a7e8f1a922c90`.
