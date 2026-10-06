# FREEZE ERRATUM R3 — cycle NFL-WINPROB-NG-SCORED-V1

- Lane: `EXEC` · Written: 2026-10-05 · Status: DRAFT for controller integration (the
  controller moves/commits this file with the EXEC lane outputs; `lanes/F_FREEZE/
  FREEZE_PACKET.md` and `lanes/FREEZE_ERRATUM_R2/ERRATUM_R2.md` are NOT edited in place —
  this erratum is append-only superseding authority for exactly the five items in §1–§5).
- Authority chain: FREEZE_PACKET.md (sha256 `9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e`,
  pinned in `freeze_digests.json`) → CODE_FREEZE_ADDENDUM.md (`CODE_FREEZE_SHA =
  7ec4c539394e68538f74df327d85fa2a477c6eb7`) → ERRATUM_R2.md (sha256
  `98681cde8f638b6a3686b4bc7cdd4286babd576343b1b5dacf3653f6e9939356`, pinned in
  `freeze_digests_r2.json`; its controller addendum measured `RECORDER_FREEZE_SHA =
  3e52b7b1de64c8e2f04867cee37524886c6b3111`) → DISPATCH_EXEC.md (wave EXEC) → this erratum.
- Machine-readable twin: `freeze_digests_r3.json` (same directory).
- Language law: calibration/forecasting vocabulary only. No betting vocabulary anywhere.

## 1. AUTHORITY RULING — execution-surface addition (R2 precedent)

**Ruling.** The freeze law permits ADDITIONS to the execution surface via ERRATUM. Precedent:
ERRATUM_R2 §3 added the recorder modules (`research/control/NFL-WINPROB-NG-SCORED-V1/recorder/`)
to the frozen execution surface after the freeze packet, without touching any arm input. The
same law covers this erratum's addition of ONE executor module to that same execution surface:

- `research/control/NFL-WINPROB-NG-SCORED-V1/recorder/execute_post_go.py` — the
  POST-OWNER-GO executor (gates G1–G8, §4). It WRAPS the frozen recorder (imports
  `frozen_refs`/`pipeline`/`priors`/`schedule` and the ported ledger tool read-only);
  it extends the package and does not modify it.
- **Arm code is untouched.** `CODE_FREEZE_SHA 7ec4c539394e68538f74df327d85fa2a477c6eb7`
  stands; `lanes/T_SELECT/{arms.py,select.py,boot.py}` sha256s are unchanged (pinned in
  `freeze_digests.json` § `files.code_freeze_files` and re-verified by gate G2 at every run).
  Any post-freeze change to arm code/config remains a NEW registered trial.
- **No frozen input changed.** Window, arms, grids, gates (T1–T3/R1–R3), the capture rule,
  the 6 h margin, the ledger law and both freeze packets stand verbatim. This erratum only
  pins the NEW execution entrypoint and the canonical GO-recording convention.

## 2. EXECUTOR FREEZE (module pins + two-step addendum)

Frozen execution-surface module added by this erratum (sha256 over raw file bytes,
lowercase hex; also in `freeze_digests_r3.json`):

| file | sha256 |
|---|---|
| `research/control/NFL-WINPROB-NG-SCORED-V1/recorder/execute_post_go.py` | `8318a399207e86b2a8f4dee4e88b4e7452a6bb17bb43710e78c3a81979e242d4` |

The executor's G2 gate re-verifies, at every run: the 5 ERRATUM_R2 recorder module pins, the
2 frozen imports (`lanes/T_SELECT/arms.py`, `…/ledger/nfl_ng_ledger.py`), the 3 arm-code
pins, its OWN sha256 against the pin above (read from `freeze_digests_r3.json`), and the
GENESIS payload digest R2 recompute. Any mismatch = loud refusal, exit 12, nothing written.

**EXECUTOR_FREEZE_SHA = PENDING_CONTROLLER_ADDENDUM** — the integration HEAD containing this
erratum plus the executor, measured by the controller with the SAME two-step procedure as
CODE_FREEZE_SHA and RECORDER_FREEZE_SHA (commit the lane outputs, measure HEAD, backfill an
`EXECUTOR_CONTROLLER_ADDENDUM.md` next to this file). The controller's addendum ALSO re-pins
`head_lineage.expected_sha` in `freeze_digests_r3.json` to that same integration HEAD (and
updates the registry row head), because gate G2 refuses unless worktree HEAD == registry row
head == this pin — by design, so a tree whose head lineage is unpinned cannot execute.

**Head lineage pin at lane time:** `876845e01932393319fcca05924dca0e8243744a` (the registered
dispatch head; measured equal to the worktree HEAD by this lane at writing time).

## 3. CANONICAL GO-RECORDING CONVENTION (registry state line)

When the owner types the registered phrase `GO NFL WINPROB NG SCORED V1 PROSPECTIVE` at THIS
cycle's own gate, the CONTROLLER — never an agent, never the executor — records the
consumption in the registry row (`researchctl cycle update`) at that moment, as EXACTLY:

```
go_phrase_state = OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>
```

where `<utc-iso>` is the consumption instant (`YYYY-MM-DDTHH:MM:SSZ`, UTC) and `<40-hex>` is
the integration HEAD at consumption. The registered `go_phrase` field stays
`GO NFL WINPROB NG SCORED V1 PROSPECTIVE` verbatim.

Executor binding (G1): `go_phrase_state` must start with the token `OWNER_GO_TYPED_LIVE` and
must fully match the regex `^OWNER_GO_TYPED_LIVE \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z at head
[0-9a-f]{40}$`; ANY other state — `REGISTERED_NOT_CONSUMED`, `CONSUMED`, `DEAD`, intent
records, or any deviant wording — REFUSES (exit 11). The executor reads ONLY the registry;
it never reads chat, tickets, or prose. The `<utc-iso>` in the state line is also the
GENESIS `created_at` substitution value (§4/§5), so the ledger anchor is bound to the
registry-recorded GO instant, not to any executor-observed wall clock (the executor contains
no wall-clock read at all).

## 4. GATE CHAIN SPECIFICATION — the auditable post-GO contract

The executor runs the gates IN ORDER. Every gate writes an audit line (gate, inputs,
verdict, detail) to the gate log BEFORE and AFTER evaluation; on any refusal the ONLY file
written is the gate log (no ledger, no genesis sidecar, no registration payload). Distinct
exit codes: G1=11 G2=12 G3=13 G4=14 G5=15 G6=16 G7=17 G8=18; usage=2; success=0.

| gate | law | refuses when |
|---|---|---|
| G1 registry authority | row `cycle_id=NFL-WINPROB-NG-SCORED-V1`; lifecycle ∈ {ACTIVE_LIGHT, ACTIVE_HEAVY}; `go_phrase_state` = canonical §3 form; registered `go_phrase` equality | no row; lifecycle not ACTIVE_*; state not the canonical typed-GO form; phrase mismatch |
| G2 freeze coherence | worktree HEAD == registry row head == `freeze_digests_r3.json head_lineage.expected_sha`; arm files + recorder modules + frozen imports + executor sha256 == pins; freeze-packet bytes sha == pin; GENESIS payload R2 recomputes | any head incoherence; any pin drift; GENESIS recompute mismatch |
| G3 heavy lock | `researchctl locks inspect` from the root cwd verdict == `FREE_PROVEN`; 3 attempts × 60 s | lock held or inspect fails after retries |
| G4 snapshot | sha256(snapshot) == provided pin AND pin present in the cycle data manifest; load re-checks pin, quarantine, kickoff parse; future-with-score rows abort; missing/unparseable kickoff aborts | pin mismatch; pin not in manifest; unparseable kickoff; any future game carrying a score |
| G5 week (Option B) | every batch game: season == target, game_type ∈ {REG, POST}, week ≥ 5; canary `2026_04_ATL_NO` and every `2026_0[1-4]_*` id refused by name | week < 5 requested; any pre-week-5 game in the batch; empty batch |
| G6 capture margin | batch_time + 6 h ≤ min(kickoff_utc of batch games) | margin < 6 h |
| G7 arms | exactly the 3 frozen arms B0 / B1_STAR / C3 loaded BY IMPORT from the sha-pinned frozen code; arm-config digests == freeze values; declared freeze arm set == the frozen triple (no 4th arm); diagnostic twin never fielded | arm-set cardinality/identity mismatch; config digest drift |
| G8 ledger | append via the ported `nfl_ng_ledger@1` tool at `--ledger-target`; GENESIS substitution law asserted BEFORE writing (placeholder-form payload re-digests to `bd94eb77…`; substitution touches EXACTLY `created_at` ← registry GO instant and `recorder_freeze_sha` ← controller-measured HEAD); chain validates after append; one row per (game, arm) with `recorded_at_utc < kickoff_utc` | filename law; real-path guard; broken pre-existing chain; placeholder digest mismatch; over-wide substitution; post-append chain break; timestamp violation |

Only after G1–G8: state warmup (state-carry law, ERRATUM_R2 §2 — completed games through the
batch timestamp via the frozen arms; no metric on any warmup game) → batch predict for the 3
fielded arms → append → chain validation → report. The pass path computes probabilities ONLY
for the batch games at the ledger target. Proven on SYNTHETIC fixtures only
(`lanes/EXEC/test_executor_gates.py`, 15 cases a–o); the REAL registry (currently
`REGISTERED_NOT_CONSUMED`) refuses at G1 before any data read — proven with an audit hook
(case a).

## 5. GENESIS R2 UNCHANGED; WINDOW/ARMS/GRIDS UNCHANGED

- **GENESIS R2 unchanged and binding.** The canonical payload V2 and its pinned digest
  `GENESIS_PAYLOAD_DIGEST_R2 = bd94eb77d35077ac7bc1761a2c61031a1cdf2f53c6d8be181de5ddfcefd51483`
  (`freeze_digests_r2.json` § `genesis_r2`) are NOT amended by this erratum. The substitution
  law stands: exactly two placeholders (`created_at` ← the GO instant recorded per §3;
  `recorder_freeze_sha` ← `3e52b7b1de64c8e2f04867cee37524886c6b3111`, the controller-measured
  integration HEAD per the ERRATUM_R2 CONTROLLER_ADDENDUM). Any other byte-level difference
  is a registration failure and stops the program (PROTOCOL §6.3). The ledger anchor remains
  `"GENESIS:" + sha256(freeze packet file bytes)` per LEDGER_SCHEMA §1.
- **Window/arms/grids unchanged.** Prospective window = 2026+ ledger-only, first capturable
  week = week 5 (opener `2026_05_TB_DAL` 2026-10-09T00:15:00Z; week-5 batch deadline
  2026-10-08T18:15:00Z or earlier, ≥ 6 h margin, after owner GO only). Fielded arms = B0,
  B1\*, C3 (+ diagnostic C3_TWIN, never fielded). All selection grids stay frozen and closed.
- Suites re-run at the EXEC tree (nothing weakened, all green): ledger 42/42; successor
  synthetic 16/16; PIPE recorder selftest + e2e-synth (3 scenarios); EXEC gate-fixture
  matrix 15/15 (see `lanes/EXEC/EXECUTOR_REPORT.md`).
