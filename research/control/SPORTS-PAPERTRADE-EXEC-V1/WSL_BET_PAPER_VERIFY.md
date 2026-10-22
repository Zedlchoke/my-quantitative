# WSL_BET_PAPER_VERIFY.md — independent fresh-context A7 verification

**VERDICT: VERIFY_PASS_WITH_FINDINGS**

Independent verifier, fresh context, 2026-10-14. Audits only; repairs nothing,
commits nothing, pushes nothing; consumed NO GO phrase; this file is the ONLY
file created (scratch scripts lived in /tmp and were deleted from scope; the
/tmp/wsl_verify_clone used for the pre-round failure-set baseline is a throwaway
clone, the shared repo was only read). Shared ledger, service, registry and all
other cycles' worktrees untouched (verified by sha before/after and read-only
git status).

Audited head at start: `a82b7f7d83cd6b93b5b0c839d4354380fb2fc55c`; mid-audit the
round's own audit commit `e294e1e792c7d7da09652b7f4b09a622a3e2a51e` landed
(JSON-only, zero code delta — `git diff a82b7f7d..e294e1e7 --stat` = audit JSON,
92 insertions). Within "a82b7f7d or later" scope; all code findings apply to
both heads byte-identically.

---

## A. Git state

- HEAD at audit start `a82b7f7d83cd6b93b5b0c839d4354380fb2fc55c`, branch
  `orca/spt-exec-v1-integration`; at audit end HEAD `e294e1e7` (moved by the
  round's own audit commit during my window — see F-5). Working tree now fully
  clean; the only pre-existing untracked file was the round's own
  `WSL_FIRST_ROWS_AUDIT.json` (committed as e294e1e7 mid-audit; my report is
  the sole new untracked file after this write).
- `git show a82b7f7d --stat` read in full: touches ONLY
  `research/papertrade_exec/execute.py` (+44−x), `research/papertrade_exec/
  wsl_lane.py` (+59−x), `tests/papertrade_exec/test_wsl_lane.py` (+40).
  `git diff bf1a265c..HEAD --stat` (whole round): execute.py, wsl_lane.py,
  test_wsl_lane.py, WSL_FIRST_ROWS_AUDIT.json. **No config.json change, no
  registry change, no core change, no data-plane code change.**
- Round commits read in full: a1e73cd3 (wiring + day-batch forecast rewrite),
  a82b7f7d (WSL-TAG scan 105959 + ERRATUM_WSL_LANE_1), e294e1e7 (audit JSON).

## B. RAW-BYTES math (re-implemented walk, independent of lane code)

Raw snapshot integrity — all four journal GETs' `sha256` recomputed from the
files under `~/.my-quantitative-data/sports-polymarket-cutover-prep-v1/live/`,
all match the journal `journal_wsl_lane_2026-10-14T022344Z.jsonl` byte-for-byte:
- `gamma_events/wsl_tag_p00_2026-10-14T022344Z.json` =
  `4d8e88b984e656b2…24d9a` (2,807,771 bytes, 35 events, http 200, LIVE_HTTP)
- `clob_books/wsl_1167584_{HOME,DRAW,AWAY}_2026-10-14T022346Z.json` =
  `11490d69…` / `e05ab3b4…` / `ea094980…`

Independent walk (my own code, raw bytes; asks sorted ascending; fee
`0.05·p·(1−p)` per share; stake 1022c = 10.22 USDC; full-stake depth check at
budget=10.22 then fixed point `B + F(B) == 10.22`, lane's iteration to 1e-12):

| leg | best_ask | vwap_ask | filled_shares | spend | fee_total | outlay | levels | budget_short | d_eff = filled/outlay |
|---|---|---|---|---|---|---|---|---|---|
| HOME | 0.9 | 0.9055488059 | 11.2329407775 | 10.1719761075 | 0.0480238925 | 10.22 (exact) | 2 | 0.0 | 1.0991135790117417 |
| DRAW | 0.07 | 0.0795926841 | 122.7548398663 | 9.7703871893 | 0.4496128107 | 10.22 − 1.78e-15 | 2 | 0.0 | 12.011236777524463 |
| AWAY | 0.058 | 0.058342482 | 167.2957922949 | 9.7604517454 | 0.4595482546 | 10.22 − 1.78e-15 | 2 | 0.0 | 16.369451300870843 |

- Every field equals the stored MARKET_QUOTE row `a9795d8fb665492638d9c881a6901
  6c8e14410bf6aea3c341f768848ddbedde1` `pm_outcomes[leg]` **exactly** (all
  rounded 10-dp values bit-equal; `budget_short == 0.0` all legs; stake never
  shrunk).
- Stored `odds[leg]` == my lane-form d_eff `filled/(spend+fee)` to **full float
  precision** on all three legs. The plan §3.4 form `filled/stake` differs by
  1–2 ULP on DRAW/AWAY only because the fixed point converges at 1e-12
  (outlay = 10.22 − 1.78e-15) — see F-2; economically null, and the plan's
  DATED NOTE endorses the inclusive-walk identity.
- `payload_sha256` recomputed from MY OWN walk's fills =
  `cef8d1c3906e8a76b7f654b70b6ea5cfcb47b8f178b895b53133c3c7cdf774bc` == stored.
- EV recomputed from the shared-ledger FORECAST row `b18b7bdd…` p values
  (`EV = p·d_eff − 1 − 0.02`):
  - HOME: 0.7947807579055409 × 1.0991135790117417 − 1.02 = **−0.14644567664877625**
  - DRAW: 0.13235551666863574 × 12.011236777524463 − 1.02 = **+0.5697534495185697**
  - AWAY: 0.07286372542582328 × 16.369451300870843 − 1.02 = **+0.17273920495803877**
  - EV_DRAW ≥ 0.05 ✓ and DRAW is the **argmax** ✓; all three equal the stored
    DECISION `ev_net_by_leg` bit-exactly.

## C. JOIN LAW from the raw Gamma page snapshot

- Event 1167584 present in `wsl_tag_p00_…json` (tag page carries
  `sport.sport = "wsl"`, `primaryTagId 105959`); title
  `"Arsenal WFC vs. Birmingham City WFC"`; `teams = ['Arsenal WFC',
  'Birmingham City WFC']` — resolves through the pinned crosswalk
  (`WSL_PM_NAME_TO_FD_NAME`: Arsenal WFC→Arsenal, Birmingham City WFC→
  Birmingham City; `WSL_FD_NAME_TO_TEAM_ID`: Arsenal→T-001-T, Birmingham
  City→T-003-T).
- Pinned source sha recomputed by me:
  `polymarket_source.py` = `4b27ab17b1dcc169bc15a6c1eca4d61ed67ea46e3ad05ba5ed
  96d3ae8f7a270f` ✓ (== lane pin).
- Three YES markets `5528995/5528996/5528997` all `closed=false active=true
  acceptingOrders=true`; each description carries verbatim **"first 90 minutes
  of regular play plus stoppage time"** ✓.
- Event `startTime = 2026-10-17T11:45:00Z`; fixture kickoff identical; delta
  **0 s ≤ 3600 s** ✓; anchor 2026-10-17T05:45:00Z (kickoff − 6h); all GETs
  (02:23:44–46Z) strictly before anchor by ~3 days ✓.
- **NO(Home)-as-AWAY excluded**: each leg's stored `token_id_yes` is its OWN
  market's `clobTokenIds[index("Yes")]` (HOME 1014579277…26208, DRAW
  3422730870…75008, AWAY 2819712861…305539); HOME's NO token
  (7499691098…84142) is never used anywhere; journal GET per leg fetched
  exactly the ledger-stored token of that leg's own market ✓.

## D. FORECAST recomputation (bit-exact, three ways)

- Pinned engine sha recomputed:
  `wsl_engine.py` = `109c3ec168809008b723ca3f8700d03927c6983cfc5d0678391f4a201
  831cc66` ✓ (== lane pin).
- My own run: corpus `~/.my-quantitative-data/sports-papertrade-exec-v1/data/
  wsl_substrate_corpus.jsonl` (2704 rows; fixture FD-2026-M37 NOT in corpus —
  unplayed, consistent with the day-batch design), rows sorted (date, match_id),
  `DayBatchReplay(rows, universe_seasons=sorted(set), predict_seasons=[])`.
  `run(K=24.0, nu=0.55, HCA=40.0)`; end ratings Arsenal (T-001-T)
  `1929.280649147988`, Birmingham (T-003-T) `1554.1862604787934`;
  `davidson3(rh, ra, 40.0, 0.55)` →
  **p = 0.7947807579055409 / 0.13235551666863574 / 0.07286372542582328**.
- Bit-exact `==` against (i) the shared-ledger FORECAST row `b18b7bdd7c3921d7
  92ad7500f099a595ba2df2ea94ff9548c66a59f9c3513be6` (all three legs) and
  (ii) the provenance ledger FORECAST row (all three legs).
- Provenance ledger `~/.my-quantitative-data/wsl-winprob-paper-prep-v1/ledger/
  paper_ledger.jsonl`: file sha `dd8a501fdf675064…a179c` (== plan §4.1 pin
  dd8a501f…), exactly 3 rows, `verify_chain()` OK via the pinned core. Rows:
  GENESIS; FORECAST FD-2026-M37 (recorded 2026-10-10T09:58:33Z, no stake/pnl);
  DECISION **NO_QUOTE stake_cents 0** (2026-10-10T09:58:54Z). File mtime
  2026-10-10T09:58:54Z — **never written by this round**. The bet lives ONLY in
  the shared ledger; no double-count (provenance carries no stake, no pnl, and
  its equity feed is a different wallet).

## E. Ledger

- Shared ledger `~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/
  paper_ledger.jsonl`: **24 rows**, `verify_chain()` OK (pinned core
  `spt_core.ledger`), equity `102215c`, open exposure `1022c`.
  `stake_for_decision(102215) = (102215+50)//100 = 1022` ✓.
- Row inventory walked (24 rows: GENESIS, WNBA×2 fc+q+d + settlements,
  SOCCER fc+NO_QUOTE d, WNBA 299/300 fc+q+d+settlements, SOCCER fc,
  then WSL rows 20–23).
- Last 4 rows, append-only linkage intact (each `prev_row_sha256` chains; chain
  verify passes):
  1. FORECAST `b18b7bdd…` recorded 2026-10-14T02:18:15Z, engine
     `WSL_B1_K24_NU0.55_HCA40@engine109c3ec16880`.
  2. DECISION artifact `992aba48b6499dd140eb745c5e090c720de5d2d597eb1f8fed3c0f
     9cda2eaa2b` NOT_RUN_UNMAPPED_TEAM, reason `event team name 'Bitcoin' does
     not resolve to a WSL fixture side (fail-closed; never guessed)`, stake 0,
     02:18:58Z.
  3. MARKET_QUOTE `a9795d8f…` fetch 2026-10-14T02:23:45Z, mode REAL, 3 legs.
  4. DECISION BET_PAPER `2b31f6c666523cac797382dfc3855d2d10440d77300220b475949
     102fc077827` 02:24:45Z: stake_cents **1022**, stake_law **"v3-1pct"**,
     chosen DRAW, equity_at_decision 102215, forecast_row_sha256 = b18b7bdd…,
     quote_row_sha256 = a9795d8f…, odds_frozen/p_frozen == my recomputation.
- Exactly **one** BET_PAPER row for FD-2026-M37 in the entire ledger ✓.
- Artifact row byte-frozen: chain verify passes; ERRATUM_WSL_LANE_1
  `CONTROLLER_ERROR_NON_TERMINAL_ROWS` pins exactly this row sha (verified
  equality).
- Erratum scope probes (in memory, against `non_terminal_matches`):
  - artifact-only match → non-terminal `{match}` ✓
  - artifact + any real DECISION row on same match → stays decided (`set()`) ✓
  - real-only match → decided ✓
  - the function is keyed by exact row sha (match-agnostic in code), but a row
    sha covers the full canonical row incl. match_id, so cross-match reuse is
    not constructible short of a sha collision — scope is effectively
    exact-row ✓
  - real ledger: `decided_match_ids()` includes FD-2026-M37 both raw and via
    `_NonTerminalView` now that the real BET_PAPER row exists ✓ (post-decision
    state correct; a pre-decision re-run would have seen it retryable).

## F. Gates (negative review) + battery

Code read: `cmd_quote`, `cmd_decide`, `quote_event`, `walk_budget_for_stake`,
`make_in_lock_recheck` (lane) plus pinned-core `PaperLedger.append_decision`
(recheck REQUIRED for BET_PAPER, executed inside flock against the reloaded
tail; capital_law=3 re-validates stake == stake_for_decision(equity) in-lock)
and `risk.in_lock_recheck` (go/duplicate/drawdown/stake≤0/cap+availability
bounds in-lock). Confirmed reachable and journaled precisely:
missing leg (join MARKET_INCOMPLETE→NOT_RUN_MARKET_MISMATCH; empty asks→
NO_QUOTE), wrong fixture (cross-match refusal), closed market (NOT_RUN_MARKET_
CLOSED), non-90min rules (stage law + rules whitelist → NOT_RUN_RULES), empty
book (NO_QUOTE), stale snapshot (strict `<` anchor; == anchor stale →
NOT_RUN_SNAPSHOT_STALE), depth-short (budget_short>1e-9 → NO_QUOTE_DEPTH, stake
never shrunk), no-forecast (NOT_RUN_NO_FORECAST), duplicate (one-decision law,
in-lock BLOCKED_DUPLICATE_SELECTION), shared cap/availability (BLOCKED_OPEN_
EXPOSURE in-lock), two-key phrase gate (BLOCKED_NO_GO in-lock on fresh registry
bytes), stake-drift (BLOCKED_STAKE_DRIFT), no plumbing (BLOCKED_NO_QUOTE_
PLUMBING), settle refuses (BLOCKED_NO_RESULTS_SOURCE; WSL bets stay OPEN).

Battery run by me, from the worktree, with the workspace venv:
- `pytest tests/papertrade_exec/test_wsl_lane.py -q` → **17 passed** ✓
- `pytest tests/papertrade_exec/ -q` → **16 failed, 86 passed**; failure set
  compared name-for-name against a pre-round baseline measured at `bf1a265c`
  in a throwaway clone: **byte-identical 16 names** (no new failures, none
  fixed) ✓. Composition: 15 in `test_exec_battery.py` + **1 in
  `test_b1r_fail_closed.py`** (`test_run_day_sandbox_soccer_journals_no_b1r`)
  — see F-1.
- Real ledger byte-unchanged by the battery (sha re-measured after the run,
  item H) ✓.

## G. NO REAL MONEY / NO GO / boundaries

- Ledger contains paper-accounting fields only (`wallet_cents` is the paper
  wallet balance field carried by GENESIS/DECISION rows; no order/signature/
  api-key/tx fields anywhere; `mode: "REAL"` on the MARKET_QUOTE row denotes
  real *market data* capture, not real-money trading).
- Registry (`plans/CYCLE_REGISTRY.json`, mirror): SPORTS-PAPERTRADE-CAPITAL-V3
  `OWNER_GO_TYPED_LIVE 2026-10-10T12:43:51Z`; WSL-WINPROB-PROSPECTIVE-PAPER-
  PREP-V1 `OWNER_GO_TYPED_LIVE 2026-10-10T13:05:50Z` (ordering recorded:
  typed after GO-A). Both consumed 2026-10-10, **before** this round; nothing
  in `bf1a265c..HEAD` touches the registry — nothing re-typed.
- `config.json`: `capital_law {version: 3, effective_utc: 2026-10-10T12:43:51Z,
  open_cap_cents: 50000, …}` unchanged by the round (pre-GO commit cabbba29);
  `sport_keys.WSL` present. No config change in the diff ✓.
- Pinned files in other cycles' worktrees byte-identical to their pins
  (shas recomputed in C/D); `git status` in both pinned worktrees shows only
  pre-existing untracked `DISPATCH/` dirs (mtime Oct 9/10, before this round).
  Data-plane writes this round went to the cutover-prep **data plane**
  (`~/.my-quantitative-data/sports-polymarket-cutover-prep-v1/{journal,live}`),
  which plan §4.3 explicitly designates for WSL append-only snapshots ✓.

## H. Ledger sha before/after all my runs

- Before: `01ef99ca07c0d91146ca33341ade4885ddb04fd9f68cdfb3fcf54b77e6de9901`
  (24 rows). After the full battery + all recomputation scripts:
  **identical** — `01ef99ca…9901`, still 24 rows. No service-native append
  occurred during the audit window (launchd `com.myquant.sptexec.ops` is
  running, pid 5795; no new journal files after 02:23:44Z run either).

## Findings

- **F-1 (MINOR, descriptive only):** the round's commit message and the
  dispatch describe the 16 pre-existing failures as "sibling-entry-drift tests
  in test_exec_battery.py". Measured: 15 of 16 are in `test_exec_battery.py`;
  one is `test_b1r_fail_closed.py::test_run_day_sandbox_soccer_journals_no_b1r`
  (same sibling-engine-entry root cause: `BLOCKED_SOCCER_ENTRY: Lane C replay
  entry absent`). The substantive invariant — failure set byte-identical
  pre-round (bf1a265c) vs HEAD, name-for-name, nothing new — **holds exactly**.
  No repair requested; evidence prose should cite both files.
- **F-2 (INFO):** stored `odds` is the lane form `filled/(spend+fee)`. The plan
  §3.4 form `filled/stake` differs by 1–2 ULP on DRAW/AWAY (outlay residual
  −1.78e-15 from the 1e-12 fixed-point tolerance). Economically null; the plan
  DATED NOTE explicitly adopts the inclusive-walk identity, of which
  `filled/(spend+fee)` is the exact algebraic form. No action.
- **F-3 (INFO):** the BET_PAPER row's `wsl_phrase_gate` field is a pointer
  ("checked in-lock (see reason)") and the `reason` field carries EV/stake
  evidence but not the registry states. The gate IS enforced in-lock (verified
  in pinned `append_decision` → recheck → `wsl_phrase_state` on fresh bytes),
  but the row itself embeds no registry-evidence snapshot. Suggestion for a
  future round (recorded rows are never edited): include the two
  `go_phrase_state` strings in the row evidence.
- **F-4 (INFO):** `cmd_quote`'s no-forecast path journals only to the command
  result (not the ledger); the ledger terminal row for that condition arrives
  from the decide pass. Precise either way; noting the asymmetry.
- **F-5 (OBSERVATION, no defect):** HEAD moved `a82b7f7d → e294e1e7` during the
  audit window (the round's own audit commit, JSON-only, zero code delta;
  ledger sha stable across it). Recorded per H-law honesty; within dispatch
  scope ("a82b7f7d or later").

## What I did NOT check

- Full content of the 021823Z broad-scan snapshots (URL pattern verified only)
  and the purpose of the single-GET 022052Z intermediate run.
- The pinned core (`sports-papertrade-v1` ledger/risk) beyond the functions
  named in F; I did not run that repo's own battery.
- The live dashboard rendering (§4.5) and `plan --league WSL` output end-to-end.
- Live re-fetch of Gamma/CLOB (verification is from the pinned raw snapshots,
  per the raw-bytes law); current market state may have moved since 02:23Z.
- WSL settlement path behavior beyond the code read (no settlement has
  occurred; `cmd_settle` refuses by law).
- Full economic history of ledger rows 0–19 (chain-verified; equity cross-
  checked via the core's own `equity_cents()`).
- Quota journal and non-WSL data-plane side effects of the round.

## Bottom line

Every claimed number in WSL_FIRST_ROWS_AUDIT.json reproduces from raw bytes
under my own independent implementations: the three-leg walk (fills, vwap,
fees, d_eff, budget_short=0, payload hash), the EV gate (DRAW argmax
0.5697534495185697 ≥ 0.05), the forecast (bit-exact three ways), the join law
(1:1, three open YES markets, verbatim 90-min rules, own-market YES tokens,
kickoff delta 0s), the ledger (24 rows chained, equity 102215c, exposure
1022c, single v3 stake-1022 BET_PAPER at 02:24:45Z, artifact byte-frozen and
exactly-scoped), the gates (17/17 lane battery; suite failure set identical to
pre-round), and the boundaries (paper only, no re-typed GO, no foreign
worktree writes, ledger sha stable). No real money; no GO consumed.
