# FREEZE ERRATUM R2 — cycle NFL-WINPROB-NG-SCORED-V1

- Lane: `PIPE` · Written: 2026-10-05 · Status: DRAFT for controller integration (the
  controller moves/commits this file; `lanes/F_FREEZE/FREEZE_PACKET.md` is NOT edited in
  place — this erratum is append-only superseding authority for exactly the four items in §1–§4).
- Authority chain: FREEZE_PACKET.md (sha256 `9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e`,
  pinned in `freeze_digests.json`) → CODE_FREEZE_ADDENDUM.md (`CODE_FREEZE_SHA =
  7ec4c539394e68538f74df327d85fa2a477c6eb7`) → DISPATCH_PIPE.md (wave B) → this erratum.
- Scope: (1) ATL@NO capture-window wording defect; (2) the missing state-carry law
  (selection caps 2018/2017 vs recorder warmup); (3) recorder code freeze; (4) an updated
  GENESIS payload digest. Nothing else in the freeze is amended; every other section of
  FREEZE_PACKET.md stands verbatim.
- Machine-readable twin: `freeze_digests_r2.json` (same directory).
- Language law: calibration/forecasting vocabulary only.

## 1. ATL@NO RESOLUTION (Option B enforced; registered window unchanged)

**Defect.** FREEZE_PACKET.md §4 states that `2026_04_ATL_NO` and any other pre-week-5 game
"becomes capturable ONLY if the capture rule below is satisfied for it before its own
kickoff". Read literally, this admits a week-4 capture (e.g. a hypothetical batch landing
before 2026-10-06T00:15:00Z) — contradicting the registered Option B decision
(OWNER_DECISION_PACKET: the week-5 slate from 2026-10-09 becomes the FIRST prospective
window) and the gate brief's forfeit-by-design disposition for pre-week-5 games.

**Erratum (binding resolution, per registered Option B):**

1. **Capturable weeks = week 5 onward ONLY.** The first capturable week opens with the
   week-5 slate whose first scheduled kickoff is `2026_05_TB_DAL` at
   **2026-10-09T00:15:00Z** (measured week-5 opener, 15 games). Every NFL week whose first
   scheduled kickoff is at or after that instant is capturable under the unchanged capture
   rule (§4 of the packet).
2. **`2026_04_ATL_NO` and ALL pre-week-5 2026 games are `NOT_RUN` prospective, forever**
   (forfeit-by-design under Option B), joining the 63 already-played games in that class.
   No batch may ever record rows for them, regardless of timing; they are never backfilled,
   never presented as pre-game forecasts, never pooled into prospective aggregates, and
   never inferred PASS from absence. The apparent week-4 capture path created by the
   defective sentence is closed: **a batch landing before 2026-10-09T00:15:00Z is
   unrecordable by law** (there is no capturable week before week 5).
3. **The ≥6h margin rule applies WITHIN the capturable window**: a week ≥5 is captured iff,
   after owner GO at this cycle's gate, a recorder batch lands ≥ 6h before that week's first
   scheduled kickoff UTC and appends its rows to the ledger. Weeks whose batch deadline
   passes without a batch are `NOT_RUN` (missing evidence is `NOT_RUN`, never inferred PASS).
4. **The registered window is NOT changed by this erratum** — Option B's window (week 5,
   2026-10-09T00:15Z onward) is restated and enforced; the defective sentence is superseded
   and must be read as replaced by this section.

First prospective target (unchanged): `2026_05_TB_DAL`, 2026-10-09T00:15:00Z; its batch
deadline is 2026-10-08T18:15:00Z or earlier (≥6h margin), and only after owner typed GO.

## 2. STATE-CARRY LAW (resolves the 2018/2017 selection caps)

**Defect.** FREEZE_PACKET.md §1/§3 freeze the selection caps (`SEASON_MAX_GAMES=2018`,
`SEASON_MAX_PBP=2017`, lanes/T_SELECT) but no section states how the RECORDER (the cycle's
single ledger writer, §5) may consume completed-game outcomes after 2018 for the state
warmup that every prospective batch requires. Without that law the recorder would be
unreadable as either leakage (forbidden) or unpowered (unable to rate teams at all).

**Erratum (binding law):**

1. **Selection caps are PERMANENT for selection.** `SEASON_MAX_GAMES=2018` and
   `SEASON_MAX_PBP=2017` are frozen selection-time load filters (grep-auditable constants in
   lanes/T_SELECT). Selection is CLOSED; the SPENT window 2019–2025 is never re-selected,
   never a hypothesis-testing/selection/re-grid surface, never a re-scoring target, never a
   pooling partner (§4 SPENT cite-only law unchanged).
2. **The RECORDER is a separate consumer with its own load law (state-carry).** To produce
   genuinely pre-game predictions the recorder must warm its state from ALL completed games
   (final scores present, kickoff strictly before the batch timestamp) through the FROZEN
   arms — B1* (K=40, HCA=0, γ=2/3, μ=1500) updates and C3 (θ=50, config `C3_T050`) boundary
   priors. This consumption of completed-game outcomes through the batch timestamp is the
   as-of law's admissible information set — it is a rating/prior UPDATE input, **not
   evaluation**. The warmup therefore does not touch 2019+ outcomes "for evaluation"
   because no LL, no metric, no calibration statistic, and no per-game probability is
   computed on ANY warmup game (grep-auditable in the recorder modules; the warmup-check
   mode emits aggregate counts only).
3. **Arm parameters are immutable.** The warmup consumes the frozen arm constants and the
   frozen arm-config digests (§1.1 of the packet); the recorder re-derives those digests and
   asserts equality with `freeze_digests.json` at every run. Any drift is a STOP.
4. **pbp 2018–2020 are STATE-CARRY INPUTS** (prior-season REG EPA aggregates feeding C3
   boundary priors for target seasons 2019–2026), pinned in `freeze_digests_r2.json` §
   `pbp_2018_2020`. They are NOT selection inputs and never widen the selection window.
   pbp 2000–2017 remain pinned by the A_DATA manifest (TRAIN priors 2001–2018); pbp
   2021–2025 (predecessor archive, read-only) are likewise state-carry inputs, pinned in
   `freeze_digests_r2.json`. In-season/current-season pbp remains NOT_RUN_PIT (§10
   quarantine unchanged): the offseason-prior role is the only pbp use.
5. **No metric on the SPENT window.** The state-carry update of a SPENT-window game never
   produces, and is never joined to, any scoring-time row class, metric, or gate reading.
   Prospective scoring vocabulary (§5, O-2) is untouched.

## 3. RECORDER FREEZE

The REAL prediction-record pipeline is implemented at
`research/control/NFL-WINPROB-NG-SCORED-V1/recorder/` (dispatch wave B; tested on SYNTHETIC
fixtures only; the warmup-check mode validated stages (a)+(b) on the real frozen snapshot
emitting aggregate counts only — evidence `lanes/PIPE/{warmup_check_evidence.json,
e2e_synth_evidence.json}`, report `lanes/PIPE/PIPELINE_REPORT.md`).

**Module sha256s at handoff (frozen; any later change is a new registered trial — same
law as §9 of the packet):**

| file | sha256 |
|---|---|
| `frozen_refs.py` | `f8afa92154c594d8380a51d7c39b44ff95f56acc8f923d6ab3d058d4e3edd1de` |
| `pipeline.py` | `f84febefc60ade8ee4949879f24b501a09872ee4e08428f4452ed9861d4c386b` |
| `priors.py` | `9bd7d2d2b2f3c5b6ca67cab611d16dccab5bc9e57fa872e6e1ecc79b04474767` |
| `record_batch.py` | `bf55b95bb52d04cdeb2783bf9c4b33cb8e79b922916e39241ae8c494a5864e7b` |
| `schedule.py` | `be941492efe173ff4dee187063c3e5810d57849486160c6b8f1d3be1abfe50a0` |

**RECORDER_FREEZE_SHA** = the integration HEAD containing this erratum and the recorder —
measured by the controller with the SAME two-step procedure as CODE_FREEZE_SHA
(commit, measure HEAD, backfill addendum; precedent-authorized, FREEZE_PACKET.md §9). The
GENESIS R2 payload below carries the placeholder `PENDING_CONTROLLER_ADDENDUM` for exactly
this field until that addendum substitutes it. The recorder imports the FROZEN selection
machinery (`lanes/T_SELECT/arms.py`, sha `19dddd3f…`) and the ported ledger tool
(`nfl_ng_ledger.py`, sha `6fb0a1d4…`) read-only, asserting both sha256s at every load.

**Recorder provenance of pbp 2018–2020** (state-carry inputs; downloaded 2026-10-05T11:58Z
by lane PIPE, $0 anonymous public release-asset URLs, 0 GitHub API calls — asset metadata
read from the cached A_DATA provenance copy):

| season | bytes | sha256 | API asset digest match |
|---|---|---|---|
| 2018 | 19,072,097 | `2e6f2dce7c7ebd46e985cabe0c17eb72b39a77f98cb4478409294f50b5820150` | (no API digest published; API size matches exactly) |
| 2019 | 19,119,729 | `60c3067017db2d28a78f66a79b657268be8578d9a5288e6a827efdcd7fe42540` | YES — byte-exact |
| 2020 | 19,286,459 | `8889f5d8782b5c5dce3c3644acdc0322b228a7e9cb13fa36cbac250e260e9f60` | YES — byte-exact |

License gate: CC BY 4.0 re-fetched once 2026-10-05T11:57Z, sha256
`2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111` = pin (no
BLOCKED_DATA_RIGHTS). Full provenance: `~/.my-quantitative-data/nfl-ng-scored-v1/
raw_pbp_2018_2020/DOWNLOAD_MANIFEST.{md,json}`. pbp 2021–2025 (predecessor archive,
read-only) sha256s measured and pinned in `freeze_digests_r2.json` § `pbp_2021_2025`.

## 4. GENESIS PAYLOAD DIGEST R2 (supersedes `ae99a803…`)

**Reason for supersession.** The pinned GENESIS digest
`ae99a803dfcc280e85d46bdc192a5b1a042320af127f688d66481ba3f1aaa3e7`
(freeze_digests.json `genesis.payload_sha256_pinned`) hashes the §6 canonical payload with
`code_freeze_sha = PENDING_CONTROLLER_ADDENDUM`. The controller addendum has since measured
the real value (`7ec4c539394e68538f74df327d85fa2a477c6eb7`), and §3 of this erratum adds a
`recorder_freeze_sha` field that must be bound into the ledger anchor before the first
prospective row. Both changes are byte-level payload changes ⇒ the R1 pin is invalid for
consumption and is superseded; the freeze packet's own bytes and `freeze_digest` input are
UNCHANGED (`9978a950…`).

**Canonical payload V2** (schema string unchanged `nfl_ng_scored_v1_genesis@1`; field set =
§6 fields + `recorder_freeze_sha`; serialization: sorted keys, separators `,`/`:`, no
whitespace, `ensure_ascii=false`, UTF-8; placeholders carry the SAME literals and the SAME
substitution law as §6):

```json
{"arm_set_ids":["B0","B1_STAR","C3"],"code_freeze_sha":"7ec4c539394e68538f74df327d85fa2a477c6eb7","created_at":"POST_GO_TIMESTAMP","cycle_id":"NFL-WINPROB-NG-SCORED-V1","diagnostic_arm_ids":["C3_TWIN"],"freeze_digest":"9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e","recorder_freeze_sha":"PENDING_CONTROLLER_ADDENDUM","schema":"nfl_ng_scored_v1_genesis@1"}
```

**GENESIS_PAYLOAD_DIGEST_R2 (pinned): `bd94eb77d35077ac7bc1761a2c61031a1cdf2f53c6d8be181de5ddfcefd51483`**

Substitution law at GO (two placeholders, nothing else): `created_at` ← real UTC timestamp
after owner typed GO (never before, never by an agent); `recorder_freeze_sha` ← the
controller-measured integration HEAD per §3. Any other byte-level difference between this
pinned payload and the written GENESIS payload is a registration failure and stops the
program (PROTOCOL §6.3 ledger-integrity stop). `ae99a803…` is superseded, retained above for
audit only, and must never anchor a ledger.

## 5. Verification pass of this erratum

- R1 digest recomputed from the §6 canonical payload = `ae99a803…` exactly (matches the
  pinned value — canonicalization verified before computing R2).
- Suites re-run on the current tree after the recorder additions (nothing weakened, all
  green): predecessor ledger suite **42/42 PASS**; successor synthetic suite **16/16 PASS**.
- Recorder modes: `--selftest` PASS (10 checks incl. hand-computed Elo/margin/DST/prior
  arithmetic); `--mode e2e-synth` PASS (nominal week 24 rows sandbox → chain intact;
  margin-violation refusal with nothing written; future-score abort with nothing written;
  double-run byte-identical); `--mode warmup-check` PASS on the real frozen snapshot
  (7,080 completed games 2000–2026 absorbed; 63 games in 2026 — matches the registration
  audit exactly; 209 future; 32 lineages; 830 C3 z-entries each applied exactly once at its
  (season, lineage) boundary; 0 future-with-score violations; **0 probability values
  emitted**).
