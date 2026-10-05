# DISPATCH — Lane F_FREEZE (NFL-WINPROB-NG-SCORED-V1, wave 3)

ROLE: protocol/freeze lane. Assemble the cycle freeze packet binding EVERY §7 open item of the
predecessor draft from the landed, committed evidence (lanes A_DATA + T_SELECT at HEAD).
No new computation beyond digest arithmetic; no metrics; no ledger writes.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · DISPATCH SHA: 69798a8389f9992d7f59adc170890013423610e8
ALLOWED PATHS (write): lanes/F_FREEZE/** + lanes/DISPATCH/handoff_F_FREEZE.json.
READ-ONLY: everything else.
SOURCES (read): predecessor freeze draft + decision packet + protocol + mechanisms
(.worktrees/nfl-winprob-ng-prep-v1/integration/{research/control/NFL-WINPROB-NG-PREP-V1/
FREEZE_PACKET_DRAFT.md + OWNER_DECISION_PACKET.md, lanes/C_PROTOCOL/{PROTOCOL_NFL_NG.md,
LEDGER_SCHEMA.md}, lanes/B_MECHANISMS/{MECHANISMS_NFL_NG.md,POWER_NOTES.md}, lanes/E_LEDGER/});
this cycle's lanes/A_DATA/* + lanes/T_SELECT/{SELECTION_REPORT.md,SELECTION_LEDGER.jsonl};
selection outputs at ~/.my-quantitative-data/nfl-ng-scored-v1/selection/.
FREEZE PACKET MUST BIND (from bytes, cite paths/sha256s):
1. Arm enumeration final: slot 1 B0 (constant p = 0.571399049390, TRAIN 2000–2018 REG non-tie
   home-win rate 2765/4839); slot 2 B1* (own-Elo K=40 HCA=0 γ=2/3, frozen, exempt); slot 3
   C1 RELEASED (G-ENTRY kill: slope 1.626 out of band; no train gain); slot 4 C2 RELEASED
   (G-ENTRY kill + MACHINERY_SUSPECT recorded — venue-permutation control won; evidence
   retained, does NOT un-kill); slot 5 C3 FIELD (θ=50; inner pooled LL 0.648348; ΔLL −0.004149
   [−0.009944, +0.001837] weak-positive; slope 1.079; shuffled control clean) + its
   time-shuffled twin as DIAGNOSTIC arm (never a budget arm, never counts as a win); slot 6
   C4 RELEASED (G-INT fail, wrong direction); slot 7 RESERVE RELEASED (owner named none before
   freeze — Option B instruction names no reserve); slots 8–9 RELEASED. Fielded = 3 arms.
2. Selection ledger frozen: file paths + sha256 + row count (38 rows: 28 configs + 6 controls
   + verbatim accounting) + tie-break rule applied.
3. Data freeze: inputs with sha256 (games.csv archive; pbp 2000–2017 manifest; fresh schedule
   snapshot 486d7227… or newer if re-pulled); TRAIN list 2000–2018; 1999 excluded; kickoff
   fallback X not activated; neutral-site = location column (51 rows 2000–2018; HCA=0 law);
   32-lineage map restated.
4. Windows: SPENT 2019–2025 cite-only; PROSPECTIVE 2026+ ledger-only; 63 played = NOT_RUN
   forever (count frozen); 209 future at registration; earliest future kickoff
   2026-10-06T00:15Z ATL@NO — under Option B the week-5 opener 2026-10-09T00:15Z TB@DAL is
   the first prospective TARGET; capture rule mechanical: a week is capturable iff the batch
   lands ≥ margin before its first kickoff AFTER owner GO; no backfill ever.
5. Ledger law: tool nfl_ng_ledger@1 (predecessor commit provenance; port in wave 4);
   recorder = THIS CYCLE'S CONTROLLER (single writer; recorded_by per row); cadence = weekly
   batch per NFL week (+ playoff rounds); margin = ≥ 6h before week's first kickoff UTC;
   O-2 row classes verbatim; postponement/flex/cancel laws verbatim (protocol §4).
6. GENESIS: canonical payload spec (freeze digest, arm set, code freeze SHA, timestamp law)
   + computed sha256 of the canonical GENESIS payload string — pinned here; the real GENESIS
   row is written ONLY after owner GO (never this round).
7. Metrics/gates verbatim from protocol §5 (log loss primary; Brier + reliability + slope band
   [0.85,1.15]; paired kickoff-date-cluster bootstrap 10,000 resamples seed 20261005; T1–T3;
   R1–R3; playoffs separate; ≥2-season rule; no outcome-based early stopping); candidate-
   ranking rule REGISTERED: C = lowest pooled prospective LL among fielded candidate slots
   (= C3, the only fielded candidate).
8. Power disclosure verbatim from predecessor draft §6 (MDD 0.026–0.056 @1 season; 0.019–
   0.039 @2; effects 0.002–0.010 starved; ≥2 completed prospective seasons for strong
   conclusions).
9. Code freeze: sha256 of lanes/T_SELECT/{arms.py,select.py,boot.py} at HEAD + note that the
   CODE_FREEZE_SHA (integration HEAD containing this packet) is measured and appended by the
   controller in the immediately-following control commit (two-step, precedent-authorized).
10. Boundaries restated: no GO typed by agents; GO phrase verbatim `GO NFL WINPROB NG SCORED
    V1 PROSPECTIVE` owner-only at this cycle's gate after A7 verdict; internal-research-only
    rights posture (fail-closed on publication/commercial).
DELIVERABLE: lanes/F_FREEZE/FREEZE_PACKET.md (+ freeze_digests.json with every sha256 cited).
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_F_FREEZE.json (task_id
nfl-winprob-ng-scored-v1-F-FREEZE, dispatch_sha=actual_start_sha=69798a83…, commit_sha=null).
STOP CONDITIONS: any source artifact missing/mismatched sha (stop, BLOCKED_TOOLING evidence).
