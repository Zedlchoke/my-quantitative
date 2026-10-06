# VERIFY_PREGO2 — final fresh-context independent verifier, FUTURES-ES-PB1-V1 pre-GO repair wave

- Role: final independent verifier (fresh context), audit-only. No repairs, no
  handoff JSON (this is a sub-wave check), zero network, NO quarantined-numeric
  reads (structural listings/hashes only; the one permitted data read was the
  mandated single-shot panel recompute below).
- Measured SHAs (one rev-parse per repo at audit start, both matched):
  - ROOT `/Users/hoangminhlong/my-quantitative` main = `409177361834dc91f8be7660fca1b4a1d2a83305` — MATCH
  - Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
    branch `prep/futures-es-reg-20261004` = `d7170583933452e15ea3df8d779fa9d4cea73da7` — MATCH
- Git commands used (all read-only, recorded): 1x rev-parse per repo, status
  both repos at start and at end, `git show`/`git diff`/`git log`/`git
  merge-base --is-ancestor` as listed per check.
- Heavy lock: `researchctl.py locks inspect` = `FREE_PROVEN` before the
  single-shot panel read (no NBA/NFL worker active).
- Write boundary honored: this directory only
  (`research/control/FUTURES-ES-PB1-V1/verify/prego2/**`, worktree).

## W1 — Authority records: PASS

`auth/PREGO_REPAIR_RECORDED.json` (sha256 `db0360faa1d2a70f9ace9e439082ebf94a058c05e0da53f7e5e10c0ba85d82bf` — recomputed, matches the pin embedded in `repair/selection_freeze_v2.json`):

- Both owner quotes verbatim present: `"okay lên lệnh cho agent trong zcode đi"`
  (HOLIDAY-REPAIR-AUTH, context "sau đề xuất sửa holiday theo hướng thận
  trọng") and `"Đồng ý cả ba cách trên"` (PINS-D-A1-A2-A3, context names q80
  linear interpolation, C2 always Long, C1 SHA-256 seed 20261002).
- The 3 pin effects match the owner-stated choices EXACTLY: D-A1
  `numpy.percentile(..., 80)` LINEAR on strict-past trailing-252d; D-A2 C2
  unconditional LONG, D0, hold to era-correct close, no TP/SL; D-A3
  `sha256('FBES1-PLA-D0-S2|seed=20261002|'+session_date)` first-byte sign,
  seed FROZEN. Cross-checked against `pins/pin_decisions.json` (all three
  `OWNER_RATIFICATION_REQUIRED`, dry-run recorded defaults == ratified options,
  adjudicated outcome-blind, 24-identity enumeration invariant M4).
- `not_a_go_law` present verbatim ("NOT a typed GO, NOT scoring
  authorization, NOT S1/order/purchase/push/merge. GO phrase remains
  REGISTERED_NOT_CONSUMED: ... owner-only at the cycle's own gate").
- No GO consumed anywhere: registry `go_phrase_state=REGISTERED_NOT_CONSUMED`,
  `budget used=0/max=24`, `s1=SEALED_UNTOUCHED`, `workers=0` (see W5).

## W2 — Repair chain integrity: PASS

(a) Superset re-derivation (my own set algebra on the two committed lists):
- In-panel ADDED (v2 − v1) = exactly `{2015-07-02}`; in-panel REMOVED = `[]`
  (0 removals); in-panel 1278 → 1279.
- Full exclusion-entry set: +21 entries, 0 removed — the other 20 are
  law dates with no panel session (law_dates_with_no_panel_session 19 → 39),
  consistent with counts.
- 35 in-panel sessions were RELABELLED `COVERAGE_LT60` →
  `HOLIDAY_PDF_EQUITY_2011_2015` (still excluded; union set unchanged), +1 new
  (2015-07-02) = 36 in the new class. The 2015-07-02 entry cites the owner law
  and the committed PDF `2015-4th-of-july-holiday-schedule.pdf` sha
  `2c8831c2…` (file hash re-verified in
  `research/control/FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/fx_comm/captures/`).

(b) `repair/selection_freeze_v2.json`:
- Embeds exclude_list_v2 sha `67060c8c…` — recomputed file hash EXACT match;
  supersedes v1 sha `bc8a41b6…` — recomputed EXACT match.
- Pins-as-law: all three pins embedded verbatim (question + owner effect +
  ratified option) under `owner_ratified_pins_law`.
- PDF-evidence law row (REPAIR-1): spot-verified 2 shas —
  `holiday/pdf_equity_evidence_2011_2015.json` = `f3a8b4d4…` (recomputed
  EXACT) and `auth/PREGO_REPAIR_RECORDED.json` = `db0360fa…` (recomputed EXACT).

(c) `repair/exposure_proof_v2.json` verdicts:
- `epoch_2011_2015.verdict = PASS`, `blocker_dates=[]`, `n_blocker_rows=0`
  (2015-07-02 blocker row GONE; the mission-literal exposure row remains only
  as an `EXCLUDED_ADJUDICATED` documentation row).
- `epoch_2016.verdict = FAIL_CLOSED_BASIS_PROVEN`, `ambiguous_rows=[]`,
  `n_ambiguous_rows=0`, enumeration honestly `NOT_RUN (unchanged)`.
- 2016-11-25 spot-recompute performed BY ME: locks `FREE_PROVEN` first, then a
  single-shot `pq.read_table` (columns raw_symbol+ts_event) of the pinned panel
  (`es_1m_outright.parquet`, sha `7ae6de2d…` — matches the proof's
  data_version_binding), CT bar-starts in [08:30, 15:00) for held `ESZ6`:
  **225/390 bars, coverage 0.5769** — matches the proof row exactly.

(d) v1 artifacts untouched:
- `git diff --name-only 476f0a2..d7170583`: 140 files, ALL inside
  `research/control/FUTURES-ES-PB1-V1/` (dirs: auth, repair, a7_v2, dryrun_v2,
  dryrun_v2_1, dispatch, holiday, pins, verify, REPORT_VI*.md); nothing
  outside the cycle.
- freezegen/, dryrun/, a7/ (v1) dirs: ZERO-diff across the range.
- v1 `holiday/exposure_proof_2011_2016.json` was ADDED once (d44de21b) and
  never modified after; its hash `8ffc0fa2…` equals the `supersedes.sha256`
  recorded by the v2 proof (append-only supersession).

## W3 — Gate verdicts as recorded: PASS

- A7-v2 (`a7_v2/a7_prelaunch_v2_digest.json`, measured head 47d60303):
  `AUTHORIZED_WITH_FINDINGS`, severity tally CRITICAL 0 / HIGH 0 / MEDIUM 0 /
  LOW 0 / NOTE 5 (N-1..N-5). Pin-implementation check PASS 3/3 with quote
  lines: D-A1 `q80[d] = float(np.percentile(m_hist[-252:], 80))` (L300, numpy
  default = LINEAR, strict past); D-A2 `direction = 1  # PIN D-A2` (L463,
  unconditional LONG, no TP/SL, hold to era close); D-A3
  `sha256("FBES1-PLA-D0-S2|seed=20261002|"+date)[0] < 0x80` (L105-110).
  I re-grepped the builder — the quoted code is present verbatim.
- DRYRUN-V2: verdict honestly **FAIL** on criterion (d) only ((a)(b)(c)(e)
  PASS), CRITICAL D-V2-1 fully documented (35 relabels silently re-admitted
  sessions into the v1 label-set SL-donor filter: donor-excluded 139→104,
  sl_distance changed on 244 eval dates, 177 exit-level changes in 18 TP/SL
  identities; q80/entry paths clean; C2 control clean; lane applied NO fix).
  **Commit order verified**: `436d8cf8` is an ancestor of `148a7bf5`
  (merge-base --is-ancestor) and `148a7bf5` is an ancestor of `d7170583` —
  the FAIL was committed BEFORE the fix, exactly as the gate caught it.
- DRYRUN-V2-1: `gate4_verdict = PASS`, all five criteria (a)-(e) PASS;
  `donor_correction`: donor exclusion SESSION SET == v1's exact 139 sessions
  evaluated on v1 labels, `donor_excluded_count_v1_labels=139`,
  `session_2015_07_02_donor_admitted=true`; delta-vs-v1 = **exactly 3 trades**
  removed (ALW/PLA/DOSE, `n_trades_removed_total=3`); determinism
  trades-index sha `eaae8b6b13453db7ef0666bb1ac15a5111898ea01019ebbd0c974a505e6df4a8`
  identical across both passes — I independently recomputed it as the sha256
  of the canonical `index` payload and got the same value (EXACT match).
- DONOR_LAW_CARRYOVER.md matches the implemented correction: the builder
  (`dryrun_v2_1/dryrun_builder_v2_1.py` L212-240) loads v1
  `freezegen/exclude_list.json` (read-only), filters in-panel sessions by the
  v1 donor classes {HOLIDAY_FACT_EARLYCLOSE, HOLIDAY_UNCERTAIN,
  COVERAGE_LT60}, and HARD-ASSERTS `len == 139`, `2015-07-02 not in` the donor
  set, and 35 recovered relabels. Doc == code.

## W4 — Determinism + quarantine: PASS

- `dryrun_v2_1/quarantine` vs `dryrun_v2_1/quarantine_rerun`: `diff -rq` clean
  — all 26 files byte-identical. Spot-hashed 4 files (ALW, REV-DN-D30-S2,
  PLA, trades_index.json): hashes MATCH pairwise.
- Quarantine headers present: `trades_index.json` and `summary.json` carry
  `QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED — ZERO DENOMINATOR CONSUMPTION —
  pre-GO rehearsal per registered plan §4 gate 4`.
- Zero denominator/ledger/registry writes in the wave diff: grep of
  476f0a2..d7170583 file list for ledger/registry/denominator/CYCLE/.runtime/
  governance = 0 hits.
- Note (reconciled, no defect): the trades-index FILE-bytes hash
  (`dbf0d10f…`) differs from the digest-quoted `eaae8b6b…` because the digest
  hashes the canonical index payload (excluding the quarantine header and
  generated_utc) — verified by independent recompute, per builder L710-712.

## W5 — Registry + doctor: PASS (with a concurrency observation)

- ROOT registry row FUTURES-ES-PB1-V1 at 40917736 AND in the current file:
  `head = d7170583933452e15ea3df8d779fa9d4cea73da7`, `go_phrase = "GO
  FUTURES-ES-PB1-V1 SCORED EXECUTION"`, `go_phrase_state =
  REGISTERED_NOT_CONSUMED`, `lifecycle = ACTIVE_LIGHT`, `phase = REGISTERED`,
  `budget {used: 0, max: 24}`, `s1 = SEALED_UNTOUCHED`. ACTIVE_CYCLES.json
  entry agrees.
- Reconcile commit 40917736: touches ONLY the 3 control-plane files
  (ACTIVE_CYCLES.json, CYCLE_REGISTRY.events.jsonl, CYCLE_REGISTRY.json);
  within the registry only the header write_token/updated_at + the ES row's
  head/updated_at. Row-level compare parent→40917736: changed rows =
  [FUTURES-ES-PB1-V1] ONLY. NBA/NFL rows byte-identical
  (NBA-WINPROB-PREP-V1, NBA-WINPROB-SCORED-V1, NFL-WINPROB-PREP-V1,
  NFL-WINPROB-SCORED-V1 — all unchanged).
- `cycle doctor --json` (read-only): **0 findings for FUTURES-ES-PB1-V1**
  (69 findings exist for other/stale cycles — WORKTREE_MISSING /
  STATE_MISSING / FROZEN_ARTIFACT_DRIFT / STALE_HEARTBEAT / HEAD_MISMATCH —
  none reference this cycle).
- CONCURRENCY OBSERVATION (out-of-wave, recorded for the owner): during the
  audit window main advanced by two foreign commits (034c4c1c 09:11:29+0700,
  5dae709b 09:15:10+0700) from the concurrent WINPROB-NG-PREP-V1 controller,
  touching only the same 3 control-plane files and only the WINPROB-NG-PREP-V1
  row. The FUTURES-ES-PB1-V1 row is byte-identical before/after them (verified
  by row-level compare), root is clean at end, and the audited ES artifacts are
  unaffected. This is live control-plane activity by another lane, not a
  defect of this wave; it is why my start-SHA premise (40917736) and end-HEAD
  differ — all ES findings above were re-confirmed against the final registry
  content.

## W6 — Sweeps: PASS

- Stale values 1.386 / 21.006 / 33.506 / 46.006: use-as-value = 0. Occurrences
  are (i) the retirement law text and (ii) a RUNTIME BAN-GUARD in every
  builder (`for banned in (...): assert banned not in cc_json`,
  dryrun_v2_1 builder L184). Legal table 21.00/33.50/46.00 (+NFA-window
  20.99/33.49/45.99) applied via pinned Variant-A values (A7-v2 check 3 PASS;
  DRYRUN-V2-1 criterion b 20/20 incl. NFA-window rows).
- GO string `GO FUTURES-ES-PB1-V1`: 26 occurrences in the cycle dir — all in
  law/record contexts (registry-row field quotes, not_a_go_law verbatim
  quotes, verifier reports of the phrase's REGISTERED_NOT_CONSUMED state).
  Zero consumption.
- Forbidden language: wave-diff added lines contain no order/submit/network/
  push/merge/S1-access action language — every S1/order/purchase/push/merge
  hit is a NEGATION inside not_a_go / write-boundary statements. "scored"
  appears only as NOT-SCORED / zero-scored / pre-GATE-6-blocker contexts;
  scored truth = 0.
- End status: worktree clean except this verifier's outputs
  (verify/prego2/**); root clean.

## W7 — Pre-GO readiness assessment

| # | Condition | State |
|---|---|---|
| 1 | Registration | PASS — registry row REGISTERED/ACTIVE_LIGHT, plan PLAN_futures_es_pb1_v1.md, branch+worktree pinned |
| 2 | Cost freeze (D3=A + errata) | PASS — D3 quote `tôi chọn 2.25$` embedded with COST_FREEZE_ERRATUM cross-ref + forbidden-values law; A7-v2 check 3 PASS; runtime ban-guard on retired values |
| 3 | Pins D-A1/D-A2/D-A3 ratified + implemented | PASS — owner ratification verbatim recorded; A7-v2 pin-implementation 3/3 EXACT vs builder code (independently re-grepped) |
| 4 | Holiday blocker closed | PASS — 2015-07-02 excluded by HOLIDAY_PDF_EQUITY_2011_2015 (superset law, 0 removals); exposure_proof_v2 epoch 2011-2015 PASS, blocker rows 0; eval 2,926→2,925 (F2 950→949 only) |
| 5 | 2016 fail-closed basis | PASS (enumeration NOT_RUN, non-load-bearing — reasoning below) |
| 6 | D-A4/D-A5 LOW pins (recorded, non-ratified) | NON-BLOCKING per A7-v2's own verdict — carried as NOTE N-4; MUST be adjudicated before gate 6 scored execution |
| 7 | A7-v2 | PASS — AUTHORIZED_WITH_FINDINGS, 0 C/H/M, 5 NOTE |
| 8 | DRYRUN-V2-1 | PASS — all criteria (a)-(e), donor==139, delta == exactly 3 trades, determinism eaae8b6b two-pass |
| 9 | Registry synced | PASS — head d7170583, REGISTERED_NOT_CONSUMED, budget 0/24; reconcile 40917736 surgical |
| 10 | Doctor clean | PASS — 0 findings for FUTURES-ES-PB1-V1 |

### Is the 2016 enumeration NOT_RUN load-bearing? — No. Reasoning:

The owner's HOLIDAY-REPAIR-AUTH law explicitly required 2016 to be "re-proven
fail-closed sufficient or stay NOT_RUN". The proof does the former: the
fail-closed SPEC §2-E1 law (unproven ⇒ exclude) is operationalized through the
coverage floor — a scheduled early-close day that actually traded short would
produce a PARTIAL session (<234 bars ⇒ COVERAGE_LT60-excluded), and the machine
census shows the 2011-2016 panel has ZERO sessions in the partial-eligible band
[0.60, 1.0) (bands: cov==1.0: 1491, 0<cov<0.60: 40, cov==0: 4, partial-eligible:
0). Every candidate-named 2016 session is truncated (2016-11-25 = 225/390,
independently recomputed by me) or absent from the panel (2016-03-25,
2016-12-26); every COMPLETE 2016 session sits on a date named by no committed
2016 artifact, and its 390-bar real-volume data is itself the evidence no early
close occurred that day. Zero ambiguous rows. The remaining NOT_RUN
(per-day 2016 PDF enumeration, like the Globex transcription) is therefore an
honestly-registered evidence limitation with a machine-proven fail-closed
closure — it does not gate pre-GO; the register keeps it visible per A7-v2 N-2.

### Remaining items (none load-bearing for pre-GO)

1. D-A4/D-A5 (LOW, implementation pins, recorded verbatim in the builder and
   A7-v2 N-4): non-blocking per A7-v2's AUTHORIZED_WITH_FINDINGS verdict, but
   they must be owner-adjudicated before gate 6 scored execution.
2. Concurrency observation (W5): another lane's controller advanced ROOT main
   by 2 commits during the audit (WINPROB-NG-PREP-V1 row only; ES row
   byte-identical before/after). Out-of-wave, no action needed for this cycle;
   noted because shared control-plane files are the workspace's known
   contention point.

## Verdict

**ALL_PRE_GO_CONDITIONS_PASS**

No load-bearing item remains open for the pre-GO state of FUTURES-ES-PB1-V1 at
worktree `d7170583933452e15ea3df8d779fa9d4cea73da7`. The typed GO remains the
owner's alone: `GO FUTURES-ES-PB1-V1 SCORED EXECUTION`, state
REGISTERED_NOT_CONSUMED, budget 0/24, S1 SEALED_UNTOUCHED. This verifier
consumed nothing and authorizes nothing; audit-only.

— End VERIFY_PREGO2.
