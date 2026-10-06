# A7_PRELAUNCH_V3 — prelaunch audit v3 (final, fresh-context) — cycle FUTURES-ES-PB1-V1

- Auditor lane: A7-PRELAUNCH-V3 (audit ONLY; never types or endorses GO).
  2026-10-05. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`.
- **ONE** `git rev-parse HEAD` at start →
  `897e7519e10b8995e77312edf18c4cccc57e4ef8` (equals the dispatch SHA).
  `git status --porcelain` start: **EMPTY**. End: only this lane's outputs
  (`a7_v3/**` + `dispatch/handoff_A7-PRELAUNCH-V3.json`). No other git
  command except read-only `git show`/`git log`/`merge-base --is-ancestor`.
  Never commit/stage/push.
- Locks: `researchctl.py locks inspect` before the panel/chain access →
  **FREE_PROVEN** (recorded; no lock taken; single-shot read-only reads).
- Zero network; zero quarantined-numeric reads (quarantine surfaces touched
  only by hash-pair comparison and header grep — no numeric content read);
  root repo read-only; Python = ROOT `.venv`.
- Write boundary: `research/control/FUTURES-ES-PB1-V1/a7_v3/**` +
  `dispatch/handoff_A7-PRELAUNCH-V3.json` only.
- Program: fresh re-audit of the CORRECTED final state (freeze v3 + SPEC
  §4 flag-based donor machinery + gate-4 third adjudication) owed after
  FAIL D-V2-2 + freeze v3 + machinery correction. Nothing inherited.

## Verdict

**AUTHORIZED_WITH_FINDINGS — 0 CRITICAL / 0 HIGH / 0 MEDIUM / 1 LOW / 2 NOTE.**

This verdict is the fresh A7 (key 1 of 2) for the changed operative surface:
`final/selection_freeze_v3.json` (a992baac…) + `final/exclude_list_v3.json`
(b101f5c7…) + `final/dryrun_builder_v3.py` (5a08c9fd…) + the y2016 evidence
block. It authorizes nothing by itself; the typed owner GO
(`GO FUTURES-ES-PB1-V1 SCORED EXECUTION`, registry state
REGISTERED_NOT_CONSUMED) remains the only key 2.

### R2 non-inheritance statement

No pass is inherited from A7 v1 (`a7/A7_PRELAUNCH.md`) or A7 v2
(`a7_v2/A7_PRELAUNCH_V2.md`). Those verdicts were measured against the v1/v2
surfaces and are **HISTORY** — the operative surface changed after them
(freeze v2→v3, builder v2.1→v3, 11 y2016 fail-closed additions, donor-law
correction D-V2-2), so under the scored_runner_spec R2 law the scored run
must consume **this** A7-PRELAUNCH-V3 verdict for the changed surface. Every
check below was recomputed fresh at HEAD `897e7519…` in this session.

## Program results (all recomputed fresh)

### 1. Freeze integrity v3 — PASS

- Carried 34-pin manifest
  `research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/freeze_pins_v2.json`
  re-hashed: **33/33 single-sha pins MATCH**, plus D3_RECORDED whose manifest
  entry carries the documented dual pin (`sha256` lane-time 99661246… /
  `sha256_v2` authoritative f54610eb…); measured = `sha256_v2` exactly, per
  the PIN_SUPERSESSION record. **34/34 effective MATCH.** Manifest self-sha
  `f7e1b580…` == `selection_freeze_v3.pins_manifest.base_manifest.sha256_at_head`.
- v2 delta pins MATCH: exclude_list_v2 `67060c8c…`, PREGO_REPAIR_RECORDED
  `db0360fa…`, pdf_equity_evidence_2011_2015 `f3a8b4d4…`.
- v3 pins MATCH at this HEAD: exclude_list_v3 `b101f5c7…`,
  selection_freeze_v3 `a992baac…`, dryrun_builder_v3 `5a08c9fd…`,
  build_freeze_v3 `b8adbd67…`, make_builder_v3 `cf0fd897…`,
  DRYRUN_V3_REPORT `096e8d0a…`, dryrun_v3_digest `b01b6b0b…` (all equal the
  FREEZE-V3-MACHINERY handoff output pins), FAIL_DONOR_VIOLATION `2f06de66…`
  (== freeze donor_law.correction_record.sha256), DONOR_LAW_CARRYOVER
  `314ae947…` (== supersedes sha), selection_freeze_v2 `cf150e24…` (==
  supersedes sha).
- y2016 artifacts MATCH the freeze y2016_evidence block: eval_v3
  `fad3c35a…`, exclude_2016_failclosed `1b846b17…`, sweep_candidates_v3
  `2953c5ca…`, EVAL_V3.md `6342b65f…`.
- pins2 authority artifacts MATCH scored_runner_spec §2 pins:
  DA45_DECISION_PACKET `3acc6e9d…`, da45_decisions `76fd46c0…`.
- SPEC of record `445f7499…` unchanged.
- Exclude-list counts block reconciles exactly: 1,322 array rows
  (1,283 in-panel + 39 no-panel-session) + 8 out-of-chain-span law dates in
  the dedicated `law_dates_out_of_chain_span` array = 1,330
  total_exclusion_entries; law_notes 5/5; per-class in-panel counts all
  match.

### 2. Identity enumeration — PASS

Independent re-transcription of SPEC §6 (pinned bytes 445f7499…) expanded the
two P-family patterns + FOMC pattern + C1-C4 rows myself:
**24/24 byte-exact, order AND set**, vs
`final/selection_freeze_v3.json` `identity_table.embedded.identities`.
Composition P-A 8 / P-B 8 / FOMC 4 / C1-C4 4 = 24; **zero unregistered
cells**; the forbidden D30×{S1,S3} cells absent; zero provisional markers.

### 3. Cost arithmetic (Variant A) — PASS

Recomputed from components: fees/side 0.85+1.38+0.02 = **2.25**;
all-in/side **21.00 / 33.50 / 46.00**; RT **42.00 / 67.00 / 92.00**; NFA
window 2014-10-01→2017-12-31 (0.01): fees 2.24 → **20.99 / 33.49 / 45.99**.
All three sources equal: (1) owner D3_RECORDED (f54610eb…, verbatim
"tôi chọn 2.25$") as superseded by COST_FREEZE_ERRATUM
(FUTURES-SIX-SCORED-GATE-PREP-20261004/synth/COST_FREEZE_ERRATUM.md; SPEC §5
stale prints marked NOT-consumed in the builder header);
(2) `selection_freeze_v3.cost_contract.embedded` (EXACT);
(3) `final/dryrun_builder_v3.py` — cost contract read from the freeze (never
hardcoded), full arithmetic asserted at load (L181-200).
**Forbidden-value scan: 0 use-as-value** — 1.386/21.006/33.506/46.006 appear
only inside ban-law strings and the builder's runtime ban tuples; 0
occurrences in exclude_list_v3. Labels binding intact: MODELED COST;
VERIFIED_VS_ACCOUNT = NOT_RUN (never inferred).

### 4. Donor-law compliance (THE corrected point, D-V2-2) — PASS

- **Code diff (mine):** `final/dryrun_builder_v3.py` vs
  `dryrun_v2_1/dryrun_builder_v2_1.py` — AST-level: **27→31 defs/vars; 21
  identical; differing = {paths (DRYRUN/V21 index), REMOVED_DATES, FINDINGS
  + new FINDINGS_NOTE, check_surface_delta→check_surface_delta_v3 + new
  `_donor_series` helper (the S5' post-hoc checker), load_inputs, main}**.
  The simulation chain `build_sessions / derive_state / simulate /
  run_pass / check_warmup_regression` is **byte-identical**. The only logic
  change is C2 inside `load_inputs`: donor-excluded := {in-panel sessions
  bearing ANY of the five short/flag-family classes in exclude_list_v3
  (HOLIDAY_FACT_EARLYCLOSE, HOLIDAY_PDF_EQUITY_2011_2015,
  HOLIDAY_2016_UNPROVEN_FAILCLOSED, HOLIDAY_UNCERTAIN, COVERAGE_LT60)} ∪
  {v2.1 carryover 139 (v1 labels)}; count machine-DERIVED, never asserted;
  FOMC_STATEMENT_DAY and WARMUP remain donor-admitted. This implements SPEC
  §4 [ERRATUM A7-SPEC-M5] "loại session short/flagged" as a FLAG-BASED law
  on the CURRENT freeze — exactly repair/FAIL_DONOR_VIOLATION.md's
  correction law; DONOR_LAW_CARRYOVER is recorded as withdrawn (freeze
  donor_law.supersedes).
- **Donor count re-derived (mine):** carryover = **139** (v1 labels,
  re-proven from freezegen/exclude_list.json); v2-label 4-family baseline =
  **140** == the FAIL-record expectation "139 + 2015-07-02 = 140";
  current-freeze five-family flags alone = **144**, and the carryover 139 is
  **fully subsumed** by the v3 flags (union adds nothing) — the flag-based
  law alone yields the donor set. **Donor set = 144** exactly; **delta vs
  139 = exactly the 5 sessions** {2015-07-02 (HOLIDAY_PDF_EQUITY_2011_2015,
  no v1 label), 2016-07-01, 2020-07-02, 2021-07-02, 2021-12-31
  (HOLIDAY_2016_UNPROVEN_FAILCLOSED)}; delta vs 140 = exactly the 4 new
  members. The digest `donor_law_v3` records the same 139/140/144 with the
  same per-session deltas — matches my independent derivation.

### 5. 2016 fail-closed compliance — PASS

- The 11 y2016 additions are in exclude_list_v3 with class
  `HOLIDAY_2016_UNPROVEN_FAILCLOSED`, all in-panel, **set-equal** to
  y2016/exclude_2016_failclosed.json; class absent in v2 (0). Spot-checks by
  date+class (5+): 2016-07-01, 2020-07-02, 2021-07-02, 2021-12-31,
  2016-11-25 (relabel from COVERAGE_LT60), plus full-11 listing — all OK.
- **Eval surface re-derived from the chain (single-shot read, 4,204
  sessions) + exclude_list_v3: 375 / 948 / 708 / 890 = 2,921 EXACT**, with
  eval bounds (F1 2011-06-10..2012-12-31, F2 2014-01-17..2017-12-29, F3
  2019-01-18..2021-12-30, F4 2023-01-18..2026-09-30) and warmup carve-outs
  (252 positional, per-fold ranges) all matching the freeze fields. F3's
  eval-last 2021-12-31→2021-12-30 emerges from the exclusion itself, as
  recorded.
- **No pattern-candidacy converted to proven-regular:** zero 2016 rows carry
  any PROVEN_REGULAR-type proof in y2016 outputs (grep: PROVEN_* labels key
  only to committed day-level artifacts for 2010 / 2011-15 / 2026-FACT);
  EVAL_V3 §5 states it verbatim; 2016 verdict = EXCLUDED_FAILCLOSED.
- **2016 enumeration stays NOT_RUN** (freeze not_run_register.v3_status +
  EVAL_V3 §6): the fail-closed class closes exposure, not the enumeration;
  never silently narrowed.

### 6. D-A4/D-A5 authority (pins2) — PASS

- SPEC-text citations verified **verbatim** against my own read of the pinned
  SPEC (445f7499…): §3 L73-74 ("điều kiện |m| ≥ q80(|m|, trailing-252d,
  strict-past) … không tune"), §4 L87-89 ("[ERRATUM A7-SPEC-M5] SL = 1.0 ×
  median của 20 range RTH session liền trước (strict past; close marks
  era-correct; loại session short/flagged) — frozen a priori, R=2"), §6 fold
  law L135-136 ("fold nhân evaluation không nhân identity").
- Classification confirmed in da45_decisions.json (76fd46c0…): D-A4 and
  D-A5 both **AUTHORITY_EXISTS / SPEC-text dispositive** (dispositive:
  true), zero OWNER_DECISION_REQUIRED; packet §2.5/§3.3 owner one-liners
  present.
- Implementation matches the adjudicated readings (code read by me):
  **D-A4** — derive_state computes m/q80/SL-donor windows over the CHAIN
  date list, trailing-252 computable |m| and trailing-20 usable RTH ranges,
  both strict-past, no fold scoping; trading fold-fenced via the frozen
  eval windows + positional warmup carve-outs. **D-A5** — cost_for() books
  fees + spread + slippage as per-side USD lines (rt = 2×side; net =
  gross − rt) at pinned table values, fill prices unadjusted; simulate()
  anchors `tp = entry ± 2.0·sld`, `sl = entry ∓ sld` at the FILL price
  (next-1m-bar open), same-bar SL priority before TP — R=2 semantics.

### 7. PIT/exclude coverage — PASS (13-date spot across all classes)

FOMC 2011-09-21 / 2016-12-14 / 2023-03-22 / 2025-09-17 → FOMC_STATEMENT_DAY,
each present in ES_fomc_stats.json evidence; PDF 2011-07-04 and 2015-07-02 →
HOLIDAY_PDF_EQUITY_2011_2015 (2015-07-02 the FAIL-record named session);
2026 FACT early-closes 2026-07-03 / 2026-04-03 → HOLIDAY_FACT_EARLYCLOSE,
present in cal_close/calendar_close_delta.json; 2016 fail-closed 2016-07-01 /
2021-12-31; relabel 2016-11-25; tail stub 2026-10-01 → COVERAGE_LT60,
fold=null (tail_note); warmup head 2013-01-02 → WARMUP. Warmup ranges and
eval bounds re-derived exactly (item 5). All 13 MATCH.

### 8. Budget accounting — PASS

Registry row (ROOT, read-only): budget {max: 24, used: 0}; identities 24 ==
registry cap 24; go_phrase exact and REGISTERED_NOT_CONSUMED; S1
SEALED_UNTOUCHED; workers 0. Gate-4 rehearsal consumed zero denominator
(quarantine-only; no ledger/counter/registry write anywhere — confirmed by
start-status EMPTY + append-only law).

### 9. Language scan + quarantine structure — PASS

No expectancy / positive-PnL / "measured cost" / GO-typed claims in
DRYRUN_V3_REPORT.md, dryrun_v3_digest.json, FAIL_DONOR_VIOLATION.md,
EVAL_V3.md, selection_freeze_v3.json (only "Measured start HEAD" — a git
measurement, not a cost claim). Quarantine: 26 + 26 files, all
quarantine/quarantine_rerun pairs **byte-identical** (hash pairs only — no
numeric content read); trades_index sha `6118b061…` and summary sha
`351135ca…` == the handoff pins; QUARANTINED header present on all 52 files.
Structurally untouched.

## Findings

| id | severity | finding |
|---|---|---|
| F-1 | **LOW** | `final/selection_freeze_v3.json` `fold_structure[].n_base_excluded` / `n_surviving` carry the v2-era counts (38/75/72/85; 627/1201/963/1142) and are internally inconsistent with the v3 `eval_sessions.n` by exactly the 4 new exclusions (1201−252=949≠948; 963−252=711≠708). The load-bearing fields (eval_sessions n/first/last, warmup carve-outs, total 2,921) re-derive EXACTLY from exclude_list_v3 + chain; the delta is correctly recorded in `freeze_diff_v3` (eval_surface old/new, per_fold old/new, n_added_exclusions_in_panel=4). Display-only staleness; the builder derives eval sets from exclude_list_v3, not these counts. Non-blocking; recommend a one-line correction in the next freeze touch. |
| N-1 | NOTE | Registry head-lag: row head `d7170583…` vs worktree HEAD `897e7519…` (researchctl doctor HEAD_MISMATCH, LOW); `d7170583…` IS an ancestor of the audit HEAD (merge-base verified); all other row fields reconcile (go_phrase exact REGISTERED_NOT_CONSUMED, ACTIVE_LIGHT, budget 0/24, S1 SEALED_UNTOUCHED). Controller reconcile; same character as prior audits' NOTE. |
| N-2 | NOTE | `head_sha` fields inside freeze v3 (`a855dab8…`) and dryrun_v3_digest record the authoring-time HEAD, i.e. pre-commit of the final state; audit HEAD `897e7519…` is the commit carrying those outputs, and every artifact re-hashes to its pin at the audit HEAD — pin chain intact. Informational. |

Carried honesty items (unchanged, verified): VERIFIED_VS_ACCOUNT = NOT_RUN on
every fee value; BBO/depth NOT_RUN; 2016 per-day enumeration NOT_RUN;
ES-specific 2011-2015 Globex transcription NOT_RUN; D-A1/D-A2/D-A3 ratified
(owner verbatim), D-A4/D-A5 adjudicated AUTHORITY_EXISTS with owner
one-liners pending formal acknowledgment per packet §2.5/§3.3.

## Verdict rationale

The D-V2-2 correction is implemented exactly as the law requires: the donor
exclusion is flag-based on the current freeze, machine-derived (144), with
the carryover union fully subsumed by current-freeze flags — no previously
donor-excluded session can be re-admitted, and no choice was justified by
preserving any prior PnL path (the correction's real cost — removed trades,
SL/exit changes on donor-window-affected dates — is reported in the
quarantined digest, not hidden). Freeze v3 is a deterministic +4/-0 merge
with 7 evidence relabels; eval 2,921 re-derives exactly; identities 24/24
byte-exact; costs exact with 0 forbidden-value use; quarantined rehearsal
outputs are structurally untouched; language clean; budget 0/24 consumed;
NO GO exists or is implied. Findings: 1 LOW (display-only bookkeeping
staleness) + 2 NOTE. 0 HIGH/CRITICAL ⇒ **AUTHORIZED_WITH_FINDINGS**.

— End A7_PRELAUNCH_V3.
