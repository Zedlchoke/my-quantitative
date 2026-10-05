# A7_PRELAUNCH_VERDICT — NFL-WINPROB-NG-SCORED-V1

- Lane: `A7_PRELAUNCH` (independent prelaunch auditor) · Written: 2026-10-05 (UTC)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration`
  · Branch `orca/nfl-winprob-ng-scored-v1-integration` · HEAD audited `8cf29fe60809dd62c7d573292853d62b01cae0d4`
  (== dispatch SHA). Interpreter used throughout: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
- Method: every checklist item recomputed from bytes/raw data; probes ran read-only, outputs only
  under `lanes/A7_PRELAUNCH/tmp/`. No audited artifact was modified. Command/exit-code detail:
  `AUDIT_EVIDENCE.md` (same directory).

## VERDICT: A7_PRELAUNCH_PASS

Zero blocking findings. Three disclosed non-blocking notes (N1–N3 below). The prelaunch gate is
ready for the owner typed-GO decision (P-8 two-key: this verdict first, then the owner types
`GO NFL WINPROB NG SCORED V1 PROSPECTIVE` verbatim at this cycle's own gate — never an agent).

## Per-check table

| # | check | verdict | decisive evidence |
|---|---|---|---|
| A7-1 | SHA chain across named commits; linear parentage; clean tree | **PASS** | All 7 named commits exist (`git cat-file -t`=commit), single-parent, 0 merges in `f55dab66..HEAD`; chain f55dab66→832f695→f6ff4945→059005aa→69798a83→7ec4c539→e08e4c42→36288f1b→8cf29fe6; messages match recorded lane events; HEAD==dispatch sha; no upstream configured (never pushed); `git status` clean except untracked A7 dispatch packet (by design) |
| A7-2 | Designed-null re-run on OWN synthetic stream, arms.py unmodified | **PASS** | arms.py sha256 == freeze pin `19dddd3f…` asserted at import; my own stream (38 rows, lineages AAA–FFF, 2001–2004, same-kickoff batch, tie, neutral, odds columns present): C1_B000 / C2_NULL / C3_T000 / C4_D000 all **max \|Δp\| == 0.0 exactly** and `.tobytes()` equal vs B1*; power check: β=25 moves p (8.97e-4) — null is not vacuous |
| A7-3 | No-spent-window: code + runtime 2019 probe + odds scan | **PASS** | `SEASON_MAX_GAMES=2018` hard filter + assert; `SEASON_MAX_PBP=2017` loop bound + assert (arms.py lines 26–27,137,140–141,377–382). Doctored 2019 row: **dropped at load** (`n_dropped_over_ceiling=1`, 0 rows > 2018 survive); backstop assert demonstrated loud on an unfiltered frame ("season > SEASON_MAX_GAMES leaked"). pbp canary: files 2000–2019 on disk, only 2000–2017 ever read. Odds: 9 named columns + patterns quarantined at load; loaded frame carries zero odds columns. N2 below on the probe's expected failure mode |
| A7-4 | Real-ledger absence; SYNTH-only sandbox; GENESIS placement | **PASS** | Zero `prediction_ledger*.jsonl`/`predictions_*.jsonl` worktree-wide and in `~/.my-quantitative-data/nfl-ng-scored-v1/` (only sandbox + selection ledgers exist; control `ledger/` holds only .py/README). Sandbox ledger: 45 rows / 15 games, all `SYNTH_2030_W1_G01–15`, arms exactly B0/B1_STAR/C3, kickoffs 2030; sha256 `77029ae6…` == DRYRUN_REPORT determinism claim. Freeze GENESIS `ae99a803…`: **0 occurrences in any ledger byte or genesis sidecar**; appears only in documentation/assertion contexts (incl. `dryrun_evidence.json` solely as field `freeze_genesis_digest_never_used`) — see N1 |
| A7-5 | Rights: license pin trail present; optional live re-fetch | **PASS (trail) / live probe NOT_CONCLUSIVE** | On-disk `rights/nflverse-data_LICENSE.md` sha256 == pin `2a82ac9b…` (18,651 B == freeze_digests bytes field). Trail: DOWNLOAD_MANIFEST.md, FREEZE_PACKET §3/§11, freeze_digests, ATTRIBUTION.md (records lane A live re-fetch 2026-10-05T09:01:18Z from `…/HEAD/LICENSE.md` == pin; full URL/HTTP/timestamp/sha provenance). Auditor's single allowed live fetch hit a wrong path (`master/LICENSE` → 404); budget spent, not retried — see N3 |
| A7-6 | Selection ledger completeness + own replay recompute ≥3 configs | **PASS** | 38 rows (28 config + 6 control + 4 arm_verdict); every pre-registered grid point present (B0, B1STAR, C1×5, C2×12+null, C3×5, C4×3). Own independent replay from raw (`nfl-nflverse-v1/raw/games.csv` + 18 pbp parquets; my own Elo/SOS/EPA-z implementation, no lane code imported): B1STAR 0.6524968479911611, C3_T050 0.6483475228409372, C1_B025 0.6526382289724465, B0 0.6830369855947883 — **all Δ=0.0 vs ledger** (tolerance 1e-9). Also reproduced: 5,057 rows / 2,491 dropped, fold counts {255,256,254,256,254}=1,275, 574 z-entries (2001–2018), B0 p0=0.5713990493903699=2765/4839; p∈[0.13,0.89] so the 1e-15 clamp never binds |
| A7-7 | Freeze §7 (10 items) completeness; arm configs; CODE_FREEZE_SHA; GENESIS discipline | **PASS** | DISPATCH_F_FREEZE items 1–10 each bound in FREEZE_PACKET §1–§10 (mapping in AUDIT_EVIDENCE). Arm configs == SELECTION_REPORT (C3_T050 θ=50 fielded; B0 const; B1* exempt; C1/C2/C4 released; C3_TWIN diagnostic). `CODE_FREEZE_ADDENDUM.md` CODE_FREEZE_SHA `7ec4c539…` == `git cat-file -t` commit; that commit's tree contains FREEZE_PACKET.md whose blob sha256 == pinned `9978a950…`. GENESIS pinned payload digest **recomputed == `ae99a803…`**; all 4 arm_config_digests recomputed == pins; real GENESIS unwritten (no ledger exists) |
| A7-8 | Boundary compliance | **PASS** | Budget 0/9 (registry row + control state.json); `s1: SEALED_UNTOUCHED`; `go_phrase_state: REGISTERED_NOT_CONSUMED`. Zero real-game probability rows (sandbox all-SYNTH; real ids in lane docs appear only as schedule/kickoff facts — no p_home association found). GO phrase occurrences confined to registered/boundary contexts (registry, plan, control state "registered, NOT typed", freeze §10, freeze_digests, handoff items). No upstream → no push. Suites independently re-run: 42/42 + 16/16 pass (bytecode writes disabled) |
| A7-9 | Power language + ≥2-season rule + no-outcome-early-stop verbatim | **PASS** | Wrap-tolerant verbatim greps all FOUND in FREEZE_PACKET: "Strong conclusions require ≥2 completed prospective seasons"; "metric readings do NOT stop arms"; "mid-window stopping on the primary metric is optional stopping and is prohibited"; "decision reads happen once per completed prospective season"; MDD 0.026–0.056 @1 season / 0.019–0.039 @2; "STARVED at 1 season"; "train-internal adjudication FIRST"; T1–T3; R1–R3; band [0.85, 1.15]; Playoffs separate; Seed INHERIT 20261005; candidate-ranking rule |
| A7-10 | Incidents/caveats coherence | **PASS** | C2 MACHINERY_SUSPECT recorded in 3 places (ledger arm_verdict `machinery_suspect=true`; SELECTION_REPORT §6/§7; freeze §1 slot 4 — evidence retained, never fielded). B1* TRAIN slope 1.605 underconfidence note present (SELECTION_REPORT §5 note; freeze §1 slot 2 "slope 1.6051"). Margin-config absence documented with caller-side ≥6h law (exact 6h accepted, 5h59m/post-kickoff rejected; freeze §4/§5 pins margin ≥6h) — see N1 for the token nuance |

## Blockers

None.

## Disclosed notes (non-blocking)

- **N1 (vocabulary, minor).** The margin-config NOT_RUN is recorded as `NOT_RUN_MARGIN_CONFIG` in
  lanes/S_SYNTH artifacts + handoff_S_SYNTH, while the S_SYNTH commit message (36288f1b) says
  `NOT_RUN_TOOLING`. Same underlying fact, different label; substance fully documented
  (tool exposes no margin config; caller-side ≥6h law enforced and test-covered). No behavioral impact.
  Similarly, the freeze GENESIS digest string occurs beyond "freeze docs" strictly so — in lane-S
  documentation, test assertions, handoffs, and as the `freeze_genesis_digest_never_used` value in
  `dryrun_evidence.json` — but **never inside any ledger file or sandbox ledger byte** (grep count 0),
  which is the binding requirement.
- **N2 (probe semantics).** The dispatch expected the doctored-2019 probe to fail via "loud
  assertion failure". Actual defense-in-depth: the 2019 row is **dropped by the hard load filter**
  (counted, never silently included), and the assertion is a backstop that demonstrably fires if the
  filter ever failed (verified on an unfiltered frame). Both layers verified loud; no weakness found.
- **N3 (registry lag, informational).** Root registry row for this cycle records `head 8b196ef5`
  (wave-2 update) while integration HEAD is `8cf29fe6` (waves 3–4 committed later). Registry writes
  go through the controller's CAS cadence; the freeze chain of record is the integration commit
  chain verified in A7-1/A7-7. No action required before GO; the controller should reconcile the
  registry head at its next CAS write.

## What this verdict does NOT do

It does not type, paraphrase, or consume the GO phrase; it does not open the prospective window
(the window opens only via the §4 capture rule AFTER owner GO); it does not validate any outcome
claim (none exists — 0 arms scored, 0/9 budget). Terminal outcome on this evidence:
**PRELAUNCH_READY_PENDING_OWNER_GO**.
