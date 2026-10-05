# VERIFICATION — Lane D · VERIFY (nflng-d-verify), cycle NFL-WINPROB-NG-PREP-V1

- verifier: Lane D quant-auditor (independent; verify-only, never repairs)
- date: 2026-10-05 · worktree `lane-d-verify` · branch `orca/nfl-ngprep-d-verify`
- start HEAD = dispatch/base SHA `71c04cf58f357b7aa50e854471aaa2223296cabd` (verified: pwd,
  branch, HEAD, porcelain-clean at intake; worktree was byte-clean before any lane D write)
- Method: every check re-measured from bytes with explicit commands; read-only outside
  `lanes/D_VERIFY/**`. No metric on any outcome was computed (all recounts are
  schema/coverage/chronology counts).

## Verdict table

| # | check | verdict |
|---|---|---|
| D-1 | download manifest ↔ bytes (re-hash ≥3 incl. largest) | **PASS** |
| D-2 | rights verbatim + provenance spot-check | **PASS** (1 minor non-blocking defect, see DEFECTS) |
| D-3 | 2026 played/future recount | **PASS** |
| D-4 | injury PIT verdict consistency | **PASS** |
| D-5 | no-metrics scan | **PASS** |
| D-6 | mechanisms structure | **PASS** |
| D-7 | protocol structure | **PASS** |
| D-8 | handoffs A/B/C validity | **PASS** |
| D-9 | registry/control coherence | **PASS** |
| D-10 | trial accounting = 0 scored | **PASS** |

**SUMMARY VERDICT: PASS — 0 blocking defects.** 1 minor non-blocking defect (D-2 quote
labeling) + 3 non-blocking observations. Details below.

---

## D-1 — Download manifest ↔ bytes: PASS

Command: `shasum -a 256` + `stat -f %z` on 4 files recorded in
`lanes/A_DATA/DOWNLOAD_MANIFEST.md`, including the largest recorded file (section B:
`raw/play_by_play_2024.parquet`, 20,597,560 B) and the fresh `games.csv` that D-3 depends on.

| file | manifest sha256 | recomputed | manifest bytes | measured | match |
|---|---|---|---|---|---|
| `nfl-nflverse-v1/raw/play_by_play_2024.parquet` (largest) | `3fd2896b…b73b28187b118ef8af6a3b` | `3fd2896bc0b911b615142d2f1fabae54a4bbba5ab7b73b28187b118ef8af6a3b` | 20,597,560 | 20,597,560 | YES |
| `nfl-ng-prep-v1/raw_schedules_20261005/games.csv` (row 4) | `338d7fe0…71d5b594f` | `338d7fe01d803916b2d5ed31fb4e5405914a8030ae2296ed449e27471d5b594f` | 2,182,476 | 2,182,476 | YES |
| `nfl-ng-prep-v1/rights/nflverse-data_LICENSE.md` (row 1) | `2a82ac9b…cfb9111` | `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111` | 18,651 | 18,651 | YES |
| `nfl-ng-prep-v1/raw_injuries_20261005/injuries_2026.csv` (row 7) | `5af78248…3453466b` | `5af782489dd0f9a7009663248ffa9be814a670eb194580ed5e7c10a63453466b` | 120,160 | 120,160 | YES |

4/4 hash+size matches. The pre-existing terminal-cycle archive was only re-hashed by
Lane A (no writes) — verified by byte-identity of the largest archive file.

## D-2 — Rights verbatim: PASS (with 1 minor non-blocking defect)

Held license: `~/.my-quantitative-data/nfl-ng-prep-v1/rights/nflverse-data_LICENSE.md`
(no downloads performed by Lane D; verification against the sha-pinned held bytes recorded
in the manifest and re-hashed above).

- sha256 `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111` — matches
  DATA_AUDIT §1 and DOWNLOAD_MANIFEST row 1 exactly.
- Title: contains "Creative Commons Attribution 4.0 International" (normalized-whitespace
  search: `Creative Commons Attribution 4.0 International Public License` FOUND).
- Genuine grant language present in held bytes: "worldwide, royalty-free, non-sublicensable,
  non-exclusive, irrevocable license" FOUND; "reproduce and Share the Licensed Material, in
  whole or in part" FOUND; "produce, reproduce, and Share Adapted Material" FOUND;
  attribution condition "retain the following if it is supplied by the Licensor" FOUND
  (with "identification of the creator(s)" and "a copyright notice"); §4 Sui Generis
  Database Rights sentence FOUND **byte-verbatim**: "for the avoidance of doubt, Section
  2(a)(1) grants You the right to extract, reuse, reproduce, and Share all or a substantial
  portion of the contents of the database".
- The rights CONCLUSION (CC BY 4.0, reproduction/adaptation/attribution/database-extract
  grants) is therefore confirmed from held bytes. **Defect D2-a (MINOR, non-blocking):**
  DATA_AUDIT §1 labels two quotes "verbatim from the held copy" that are NOT byte-verbatim:
  (i) the §2(a)(1) grant quote "...license to Reproduce the Licensed Material, in whole or
  in part, and to perform, Display, and communicate the Licensed Material..." — the held
  text reads "...license to exercise the Licensed Rights in the Licensed Material to:
  a. reproduce and Share the Licensed Material, in whole or in part; and b. produce,
  reproduce, and Share Adapted Material." (the phrase "perform, Display, and communicate"
  appears nowhere in the file); (ii) "to produce, Reproduce, and Share Adapted Material"
  (capitalization differs from held "produce, reproduce, and Share..."); additionally the
  §3(a)(1)(A) attribution quote elides with "..." and drops "(s)" from "creator(s)".
  Severity MINOR: the mislabeled quotes do not change the scope or existence of the grants;
  the load-bearing §4 quote is verbatim and the license identity is sha-pinned.
- Provenance spot-check (second claimed-fetched artifact): `nfldata_DATASETS.md` sha256
  recomputed `8835ca9c15784a2cdc04c2c599c54b373629f8fbe91117acd5b7d0c615e03bf4` =
  manifest row 2 (claimed URL `https://raw.githubusercontent.com/nflverse/nfldata/master/DATASETS.md`,
  documentation-only, no LICENSE at nfldata root per held API bytes). Also re-hashed
  `raw_schedules_20261005/timestamp.json` = `fa921041…7a4bd119` = manifest row 5; content
  byte-check: `{"last_updated":"2026-10-04 23:16:28 EDT"}` exactly as claimed (injuries
  timestamp.json likewise reads `{"last_updated":"2026-10-04 09:08:56 EDT"}` as claimed).
  The three DATASETS.md sentences quoted by DATA_AUDIT §4/§6/§7 (gametime ET semantics,
  Home/Neutral location semantics, "Data begins with the 2006 NFL season" doc-drift) are
  all verbatim-found in the held DATASETS.md.

## D-3 — 2026 played/future recount: PASS

Command: read-only `/Users/hoangminhlong/my-quantitative/.venv/bin/python` recount from
`~/.my-quantitative-data/nfl-ng-prep-v1/raw_schedules_20261005/games.csv` (sha
`338d7fe0…`), kickoff UTC derived as `gameday`+`gametime` in `America/New_York` → UTC,
epoch `2026-10-05T03:13:51Z` (state.json / dispatch).

| quantity | GAMES_2026_CLASSIFICATION.md claim | Lane D recount | match |
|---|---|---|---|
| total rows in file | 7,548 | 7,548 | YES |
| 2026 rows scheduled | 272 (all REG, weeks 1–18) | 272, `game_type={REG}`, weeks 1–18 | YES |
| 2026 rows with final scores | 62 | 62 | YES |
| kickoff_utc ≤ epoch | 63 (62 finished + 1 in flight) | 63 | YES |
| kickoff_utc > epoch | 209 (0 scored) | 209, 0 with any score | YES |
| internal consistency | 63 + 209 = 272 | 272 | YES |
| earliest future kickoff | 2026-10-06T00:15:00Z = `2026_04_ATL_NO` | `2026_04_ATL_NO` 2026-10-05 20:15 ET → 2026-10-06T00:15:00Z, unscored | YES |
| next futures | `2026_05_TB_DAL` 2026-10-09T00:15Z; `2026_05_PHI_JAX` 2026-10-11T13:30Z | identical | YES |
| boundary row | `2026_04_DET_CAR` kickoff 2026-10-05T00:20:00Z < epoch, no score | kickoff 2026-10-05T00:20:00+00:00, home/away score empty, pre-epoch=True | YES |
| anomaly scan | exactly 1 past-dated unscored 2026 row | exactly `2026_04_DET_CAR` | YES |
| directional law | all 62 scored games pre-epoch; no future game scored | `played ⊆ pre-epoch` True; post-epoch scored count 0 | YES |

All 63 played-before-epoch games are classified NOT_RUN prospective in the Lane A artifact
(per the prospective law: epoch is a lower bound; per-row `recorded_at_utc < kickoff_utc`
is the real authority — consistent with state.json `prospective_law` and LEDGER_SCHEMA R2).
No win-prob metric computed; schema/coverage counts only.

## D-4 — Injury PIT verdict consistency: PASS

- INJURY_PIT_VERDICT.md clears NO source as PIT: every candidate (nflverse-data `injuries`
  downloaded; `depth_charts`, `weekly_rosters` unverified; media-scraped archives; NFL.com)
  is **NOT_RUN_PIT**.
- Claimed schema vs held bytes: the verdict's 16-column schema
  `season,season_type,game_type,team,week,gsis_id,position,full_name,first_name,last_name,
  report_primary_injury,report_secondary_injury,report_status,practice_primary_injury,
  practice_secondary_injury,practice_status` matches the actual header of BOTH held files
  (`injuries_2026.csv`, `injuries_2025.csv`) character-for-character. Header
  date/time/modif/publish column-name search: zero matches in both files — "no timestamp
  column of any kind" is byte-true.
- Quarantine-law consistency: PROTOCOL §9 lists "Injuries / availability → NOT_RUN_PIT
  unless Lane A clears PIT" (Lane A did not clear — quarantine stands), "Odds columns →
  QUARANTINED" (DATA_AUDIT §7 measures odds-column presence for schema completeness only
  and declares them QUARANTINED — consistent), "pbp-derived CURRENT-GAME features →
  NOT_RUN_PIT" (DATA_AUDIT §7 records the embedded wp/epa columns as present-but-never-used
  — consistent). The verdict's reason (per-record publish timestamps unprovable from
  released bytes; predecessor's `date_modified` column since REMOVED) matches the held
  schema exactly.

## D-5 — No-metrics scan: PASS

Command: `grep -rniE "log.?loss|brier"` over `lanes/A_DATA lanes/B_MECHANISMS
lanes/C_PROTOCOL` and `~/.my-quantitative-data/nfl-ng-prep-v1/`.

- Downloads dir: **0 hits**.
- Lane artifacts: 7 hits, ALL in `lanes/C_PROTOCOL/PROTOCOL_NFL_NG.md` (5) +
  `lanes/C_PROTOCOL/handoff_C.json` (2). Every hit is DESIGN SPECIFICATION language —
  metric definitions/gates for the successor cycle ("PRIMARY: mean log loss LL = −mean[...]",
  "Secondary: Brier score mean[(p−y)²]", "T3 ... Brier(C) > Brier(B0)", "Single-season
  outputs are labelled descriptive (per-season LL/Brier/...)"). Zero hits in Lane A or
  Lane B artifacts.
- HISTORICAL citations (explicitly permitted): Lane B cites pooled LL 0.6407 (B1*) vs
  0.6935 (B0), ΔLL −0.0528, CI half-widths 0.0148/0.0080/0.0070/0.0012 — all traced to the
  TERMINAL cycle's bytes: `nfl-winprob-scored-v1/.../results/scored_summary.json` contains
  `log_loss: 0.6935481570681993` (B0) and `log_loss: 0.6407092590929282` (B1-c) — verified
  present in the cited file. POWER_NOTES.md's MDD arithmetic is analytic derivation from
  those measured half-widths, not a new outcome evaluation.
- **No newly computed value on 2026 outcomes exists anywhere.** The only 2026 numbers in
  artifacts are the schema/coverage/chronology counts of D-3 (verified legitimate).

## D-6 — Mechanisms: PASS

Evidence from `lanes/B_MECHANISMS/MECHANISMS_NFL_NG.md` (+ POWER_NOTES.md):

- **Exactly 3 candidates + 1 conditional**: §2 "Candidates (3 proposed + 1 conditional
  interaction)" — C1 SOS-adjusted Elo, C2 home/away split rating, C3 offseason EPA prior;
  C4 short-week×away explicitly CONDITIONAL, design-level, "no outcome runs in PREP",
  gated, "default expected disposition: slot released" (starved BY DESIGN, MDD ≈ 0.08 on
  ~340 train slice cells). Matches the plan's "AT MOST 2–3 genuinely new mechanisms" +
  conditional interaction.
- **No re-grid of rejected mains as arms**: update laws frozen at B1* values (C1 "Update
  law unchanged: standard K=40 binary update ... γ=2/3"; C2 common stream "exactly the
  B1\* stream"; C3 "In-season: UNCHANGED B1\*"); §3 REJECT item 2: "Any re-grid of K,
  league-constant HCA, rest/short-week/form MAIN effects ... rejected ... mains stay
  dead"; C4 "HCA/rest MAIN effects are never re-tested anywhere (ancestry veto)" and is a
  one-cell restricted constant (δ=0 null), not a main re-test.
- **Falsifier + negative control + power per candidate**: C1 — REJECT iff pooled ΔLL CI
  includes 0 or > 0 / fold rule; negative control time-shuffled-SOS twin; power MDD
  0.026/0.019/0.006 (1 season / 2 seasons / train-internal). C2 — same CI+fold falsifier;
  controls = venue-label permutation + time-shuffled twin; capacity/degeneracy check;
  power per POWER_NOTES. C3 — CI+fold falsifier; time-shuffled EPA prior control; power
  (coverage-conditional). C4 — shuffled-label control; slice power arithmetic (starved).
  All four carry designed nulls (β=λ=θ=δ=0 reproduce B1\* bit-for-bit). POWER_NOTES.md
  calibrates on measured terminal half-widths and empirically validates √n scaling.
- **Reject section present**: §3 with 8 entries — MOV/blowout-weighted Elo OUT per
  ancestry; K/HCA/rest main re-grids; additive logistic-over-elo_diff (dead in both
  terminal cycles); γ re-tune; in-season pbp features NOT_RUN_PIT; injury features
  NOT_RUN_PIT; 538/odds banned; travel/timezone unselected.

## D-7 — Protocol: PASS

Evidence from `lanes/C_PROTOCOL/PROTOCOL_NFL_NG.md` + `LEDGER_SCHEMA.md`:

- **Retrospective rows forbidden**: LEDGER_SCHEMA §2 field 9 + R2 "Timestamp law":
  `recorded_at_utc < kickoff_utc` strictly, enforced at append time AND re-validated at
  scoring against the ACTUAL kickoff; violation ⇒ INVALID_PROSPECTIVE (excluded, count
  disclosed, never deleted). PROTOCOL §4 identical; §1.3 played-before-record law:
  already-played 2026+ games permanently NOT_RUN prospective, never backfilled.
- **No outcome columns**: LEDGER_SCHEMA "No outcome fields" (no scores/results/winners)
  + R8 no-outcome check with outcome-vocabulary list (`score`, `home_score`, `away_score`,
  `result`, `winner`, `outcome`, `total`, `spread`) failing the file.
- **≤9-arm enumeration incl. B0 + B1\* K=40 HCA=0**: PROTOCOL §3 table — slots 1–9;
  slot 1 B0 (constant, TRAIN-only refit); slot 2 B1\* "own-Elo K=40, HCA=0, γ=2/3 ... not
  selectable"; slots 3–5 the ≤3 Lane-B candidates; slot 6 conditional interaction (G-INT
  gate); slot 7 one named RESERVE; slots 8–9 RELEASED. Negative controls are diagnostic
  arms outside the budget, never candidate wins.
- **Playoffs separate**: §5.1 "Playoffs separate ... NEVER pooled into regular-season
  headline aggregates" (terminal precedent pooled_rs n=1865 vs playoff n=89); R7 allows
  REG/POST only, PRE forbidden.
- **≥2-season rule present**: §7 "Strong conclusions require ≥2 completed prospective
  seasons (≈ ≥540 regular-season games)" + pooling pre-registration + single-season
  outputs labelled descriptive.
- **Seed stated**: §5.2 "Seed decision: INHERIT 20261005" (also §2.1 solver seed 20261005).
- **SYNTHETIC labeling**: LEDGER_SCHEMA header "All examples in this document are
  SYNTHETIC" + §5 "All rows below are SYNTHETIC" — fabricated teams/ids/digests only; no
  real-game predictions in examples.

## D-8 — Handoffs A/B/C: PASS

Command: `json.load` + field assertions on all three handoffs.

| handoff | schema | task_id | lane | dispatch_sha | actual_start_sha | commit_sha | at dispatch path |
|---|---|---|---|---|---|---|---|
| lanes/A_DATA/handoff_A.json | zcode_orch_v3_handoff@1 | nflng-a-data | A_DATA | fce0b14f…c5e3 | fce0b14f…c5e3 | f2e800c8…ffde359 | YES (DISPATCH_A_DATA.md "EXACT path lanes/A_DATA/handoff_A.json"; state.json lanes.A_DATA.handoff_path) |
| lanes/B_MECHANISMS/handoff_B.json | zcode_orch_v3_handoff@1 | nflng-b-mech | B_MECHANISMS | fce0b14f…c5e3 | fce0b14f…c5e3 | 3810e2c4…e71036 | YES (DISPATCH_B_MECHANISMS.md; state.json) |
| lanes/C_PROTOCOL/handoff_C.json | zcode_orch_v3_handoff@1 | nflng-c-proto | C_PROTOCOL | fce0b14f…c5e3 | fce0b14f…c5e3 | 02fc0434…6dc5ca | YES (DISPATCH_C_PROTOCOL.md; state.json) |

All parse as valid JSON; cycle_id `NFL-WINPROB-NG-PREP-V1` on all three; each carries
authority_claims / known_limitations / incidents / tree_status / outputs. All three
commit_shas resolve: each is the tip commit of its lane branch with subject
`NFL-NG-PREP lane A|B|C: …` (git log verified).

## D-9 — Registry/control coherence: PASS

Commands run from root `/Users/hoangminhlong/my-quantitative`:

- `.venv/bin/python research/researchctl.py cycle list` → row
  `NFL-WINPROB-NG-PREP-V1  ACTIVE_LIGHT  0/0  71c04cf  orca/nfl-winprob-ng-prep-v1-integration`
  — matches state.json (lifecycle ACTIVE_LIGHT, budget 0/0, integration branch) and the
  dispatch base SHA (71c04cf58f357b7aa50e854471aaa2223296cabd).
- `.venv/bin/python research/researchctl.py locks inspect` → `verdict: FREE_PROVEN`,
  `flock_state: free`, no pid — heavy lock FREE.
- `git -C .worktrees/nfl-winprob-ng-prep-v1/integration status --porcelain` → empty
  (CLEAN); integration HEAD = `71c04cf58f357b7aa50e854471aaa2223296cabd` (the post-landing
  HEAD all lane branches were cut from).
- Lane-branch ancestry: `git merge-base fce0b14febcaec6e924cb1bf6629ccdeeb47c5e3 <branch>`
  = `fce0b14f…c5e3` for all of `orca/nfl-ngprep-a-data`, `orca/nfl-ngprep-b-mech`,
  `orca/nfl-ngprep-c-proto` (and `orca/nfl-ngprep-d-verify`) — every lane branch is based
  on the recorded dispatch SHA.
- `git diff --name-only fce0b14f <lane-branch>`: lane A adds exactly its 5
  `lanes/A_DATA/*` files; lane B exactly 3 `lanes/B_MECHANISMS/*`; lane C exactly 3
  `lanes/C_PROTOCOL/*`. Integration adds exactly the same 11 lane files — no writes
  outside lane dirs by any lane.

## D-10 — Trial accounting: PASS

- Budget: registry row `0/0`; state.json `"budget": {"used": 0, "max": 0}`.
- `find` over `lanes/**` and `research/control/NFL-WINPROB-NG-PREP-V1/` in the cycle tree:
  NO TRIAL_LEDGER (or any *trial*/*ledger* file) exists under any lane dir; the cycle
  control dir holds only `state.json` + `event_log.jsonl` (single G0_BOOTSTRAP event,
  "budget 0/0; no GO phrase" — no scored events).
- Branch-level confirmation: per D-9 diffs, this cycle's entire write surface (across lane
  branches AND integration) is the 11 lane artifact files. The TRIAL_LEDGER.jsonl files
  visible in full-tree listings are frozen artifacts of OTHER (historical, terminal)
  cycles — untouched (their hashes/baselines are inherited history; no cycle lane path
  contains them).
- No GO phrase registered or consumed: state.json `go_phrase: null`,
  `go_phrase_state: NOT_REGISTERED`; PROTOCOL and MECHANISMS affirm no GO consumed.

---

## DEFECTS

| id | severity | artifact | description | blocking? |
|---|---|---|---|---|
| D2-a | MINOR | lanes/A_DATA/DATA_AUDIT_NFL_NG.md §1 | Two quotes labeled "verbatim from the held copy" are paraphrases, not byte-verbatim: the §2(a)(1) grant sentence ("...to Reproduce the Licensed Material, in whole or in part, and to perform, Display, and communicate...") does not exist in the held license (actual: "...license to exercise the Licensed Rights in the Licensed Material to: a. reproduce and Share the Licensed Material, in whole or in part; and b. produce, reproduce, and Share Adapted Material."); "perform, Display, and communicate" appears nowhere in the file; "to produce, Reproduce, and Share Adapted Material" differs in capitalization; the §3 attribution quote elides and drops "(s)". The §4 Sui Generis quote IS verbatim, the sha256 pin matches, the license identity/grant substance is genuine CC BY 4.0. Rights verdict unaffected. | NO |

## NON-BLOCKING OBSERVATIONS

1. `handoff_B.json` records `"workers": 1` (A and C record 0) — appears to record its own
   worker session; no dispatch rule violated; registry `workers` budget respected.
2. Lanes B and C used the two-commit backfill procedure (artifacts commit + handoff
   commit_sha backfill commit) although their dispatch packets say "exactly ONE clean
   commit" — explicitly disclosed in handoff_B `commit_sha_note`, handoff_C
   known_limitations, and PROTOCOL §11.5 as task-authorized; recorded here for the audit
   trail. Lane D follows the same authorized procedure (see handoff_D.json).
3. Lane C's arm slots 3–5 were frozen as placeholders ("binds to Lane B's handoff",
   OQ-1) because Lane C closed before Lane B landed; the plan priorities used as
   placeholders (SOS-Elo, home/away split, offseason EPA prior) match Lane B's actual
   C1–C3 exactly — no inconsistency, but the successor freeze packet must do the final
   binding (already registered as OQ-1).

## Verifier declarations

- Read-only outside `lanes/D_VERIFY/**` (all commands above are reads/re-hashes/
  read-only python recounts; no bytes written anywhere else; no downloads; no credentials;
  no push/merge/rebase; no `git add -A`; no metric computed on any outcome).
- Defect D2-a was NOT repaired — reported only.
- Lane D ends with exactly the two authorized commits (artifacts + handoff_sha backfill)
  on `orca/nfl-ngprep-d-verify`, tree clean.
