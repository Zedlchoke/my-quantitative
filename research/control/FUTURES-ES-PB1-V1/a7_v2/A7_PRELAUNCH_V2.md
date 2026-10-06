# A7 PRELAUNCH V2 — pre-GO re-run audit of the REPAIRED freeze (gate 3, key 1 of 2)

- Cycle: `FUTURES-ES-PB1-V1`
- Role: prelaunch A7 re-run auditor (v2). Fresh context. **Audit only; never types or endorses a GO.**
- Audit authority read first: `research/control/FUTURES-ES-PB1-V1/auth/PREGO_REPAIR_RECORDED.json`
  (owner decisions `PINS-D-A1-A2-A3` — "Đồng ý cả ba cách trên" — and `HOLIDAY-REPAIR-AUTH` —
  "okay lên lệnh cho agent trong zcode đi"; NOT a typed GO; GO phrase remains REGISTERED_NOT_CONSUMED).
- Measured at committed HEAD `47d603030f7928c2298e0354d06c4fc916832b00`
  (worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`). Nothing inherited from A7 v1 (`a7/A7_PRELAUNCH.md`,
  verdict a33978b7) or from any prior verifier.
- Discipline: ONE `git rev-parse HEAD` at start = `47d60303…` (RECORD: matched dispatch); start
  `git status --porcelain` EMPTY. Heavy lock inspected first: `researchctl.py locks inspect` →
  `FREE_PROVEN` (no worker, flock free). Python = root `.venv`; single-shot reads of
  `es_chain_T5.parquet` and `es_1m_outright.parquet` (date-filtered) only; zero PnL/quarantine-numeric
  reads; zero network; ROOT repo read-only; nothing staged/committed/pushed.

## VERDICT: AUTHORIZED_WITH_FINDINGS — 0 CRITICAL / 0 HIGH / 0 MEDIUM / 5 NOTE

All nine program checks PASS. The repaired freeze (gate-2 v2) is internally consistent, pinned,
superset-safe, and its ratified pins are implemented exactly by the dry-run machinery. The v2 audit
key authorizes nothing by itself: the typed owner GO
`GO FUTURES-ES-PB1-V1 SCORED EXECUTION` remains owner-only at the cycle's own gate.

---

## Findings ledger

| id | severity | finding |
|---|---|---|
| N-1 | NOTE | Registry head-lag (pre-authorized by dispatch): registry row `head = d44de21b6464d3f1b427ce69fc3298f823531d0f` while the branch has advanced to `47d60303…` (repair-wave commit). Verified `d44de21b` IS an ancestor of `47d60303` (`git merge-base --is-ancestor` → true). All OTHER row fields verified unchanged: `go_phrase` exactly `GO FUTURES-ES-PB1-V1 SCORED EXECUTION`, state `REGISTERED_NOT_CONSUMED`, lifecycle `ACTIVE_LIGHT`, phase `REGISTERED`, budget `{used: 0, max: 24}`, `s1 SEALED_UNTOUCHED`, plan path `plans/PLAN_futures_es_pb1_v1.md`, branch matches. Head reconcile pending on the controller's side; recorded as NOTE per dispatch instruction, not a finding. |
| N-2 | NOTE | Carried NOT_RUN register (unchanged by the repair, disclosed in the v2 freeze's own `not_run_register` and `exclude_list_v2.not_run_elements`): per-day holiday enumeration **2016** remains NOT_RUN (no committed 2016 day-level artifact set; class `HOLIDAY_PDF_EQUITY_2011_2015` deliberately does NOT cover 2016) and ES-specific per-day/per-time Globex transcription 2011-2015 remains NOT_RUN. Both are now backed by the fail-closed machine proof (`repair/exposure_proof_v2.json` = PASS, zero blocker rows): every candidate-named 2011-2016 session is excluded or absent; zero ambiguous rows; the conservative direction is machine-verified, never silently narrowed. Obligation language carried to scored-execution discipline. |
| N-3 | NOTE | The gate-4 dry-run artifacts (`dryrun/quarantine*/`, generated 2026-10-04 at HEAD `42885faf`) were produced against the **v1** gate-2 freeze; the v2 repair moved exactly one eval session (2015-07-02, `in_eval_surface_v1: true`) out of F2. The ratified pins D-A1/D-A2/D-A3 are machinery-level (identity mechanics) and are unaffected by the exclude delta — pin-implementation check 4 PASSES, so no dry-run re-run is REQUIRED for pin fidelity by this check. The scored engine at gate 6 must consume the v2 freeze (eval 2,925; F2 949). Dry-run outputs remain QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED; zero scored cells. |
| N-4 | NOTE | Declared (non-ratified) implementation pins D-A4 (chain-wide strict-past q80/SL-donor window fencing) and D-A5 (costs as USD lines at pinned table values) remain LOW recorded findings of the dry-run lane, visible verbatim in `dryrun_builder.py` (module docstring + code). They are not part of the owner's three-way ratification and were not adjudicated here. |
| N-5 | NOTE | Stale SPEC §5 prints (1.386/21.006/33.506/46.006) remain in the pinned SPEC text by construction; retired by COST_FREEZE_ERRATUM + forbidden-values law; 0 use-as-value in the v2 operative surface (scan below). No action. |

---

## Check 1 — Freeze integrity v2: PASS

Re-hashed at HEAD `47d60303…` (sha256, fresh measurement):

| set | items | result |
|---|---|---|
| Carried 34-pin manifest `FUTURES-ES-PB1-REGPREP-20261004/freeze/freeze_pins_v2.json` (`pin_count: 34`) | 34/34 | **34/34 MATCH, 0 mismatch.** For the single delta pin `auth/D3_RECORDED.json` the measured sha equals the manifest's `sha256_v2` `f54610eb15e6cb41d32dec28616cdaaed6225fce0cfee9fe4cc3522b2fa1e355` (supersedes v1 pin `99661246…`, disclosed in `_corrections_log`); all other 33 pins measured == `sha256` == `sha256_v2`. Manifest self-reference law holds (manifest hashes only the 34 artifacts, not itself). |
| Manifest self sha vs `selection_freeze_v2.pins_manifest.base_manifest.sha256_at_head` | 1/1 | measured `f7e1b580071c09526f13915523a287094ed56a530d2196adc4de0c85907b469a` == expected → **MATCH** |
| v2 delta pins (`selection_freeze_v2.pins_manifest.v2_delta_pins.added_pins`, exactly 3) | 3/3 | `repair/exclude_list_v2.json` = `67060c8c…` MATCH; `auth/PREGO_REPAIR_RECORDED.json` = `db0360fa…` MATCH; `holiday/pdf_equity_evidence_2011_2015.json` = `f3a8b4d4…` MATCH |
| Repair cross-reference hashes inside `selection_freeze_v2.json` | 9/9 | `freeze_diff` `28eb5dfb…`, `identity_table_24` `6e391980…`, `pit_exclude_set` `f504c731…`, `pin_decisions` `ef267c3a…`, supersedes `selection_freeze.json` `e2b9934a…`, supersedes `exclude_list.json` `bc8a41b6…` — all MATCH (v1 gate-2 history byte-intact, append-only supersession) |
| Registered plan (ROOT authority side) `plans/PLAN_futures_es_pb1_v1.md` vs `registered_plan.sha256` | 1/1 | ROOT copy `e29b3d2f89273cd97c91712f4340d4209034322dda356d9f8a272513729f9b93` MATCH; no worktree copy exists (consistent with "ROOT repo — read-only authority side") |

## Check 2 — Identity enumeration vs SPEC §6: PASS

Independent re-transcription (this lane, from the pinned SPEC bytes, not copied from any freeze):
patterns `FBES1-PB1-{CONT,REV}-{UP,DN}-{D0,D30}-S2` (8), `FBES1-PB1-{CONT,REV}-{UP,DN}-D0-{S1,S3}` (8),
`FBES1-PB1-{CONT,REV}-{UP,DN}-D0-S2-FOMCIN` (4), fixed `FBES1-PLA-D0-S2` / `FBES1-ALW-D0-S2` /
`FBES1-FLAT` / `FBES1-DOSE-D0-S2` (4).

| property | result |
|---|---|
| count | my transcription 24; embedded table 24 unique; **byte-exact set equality TRUE** (diff both directions empty) |
| composition | P-A 8 + P-B 8 + FOMC 4 + C1-C4 4 = 24; embedded `composition_transcribed {C1-C4:4, FOMC:4, P-A:8, P-B:8}` `composition_match: true`, `count_match: true` |
| unregistered cells | 0. Negative control D30×{S1,S3}: absent (SPEC §6 L133-135 law); 0 duplicates; `provisional_markers_found: []`; C1 seed note "seed 20261002" present in SPEC §6 text |
| source | embedded table imported (parsed, not retyped) from `identity_table_24.json` (sha `6e391980…` MATCH, check 1) |

## Check 3 — Cost arithmetic (Variant A) + forbidden-value scan: PASS

Recomputed from components by this lane (exact decimal):

| cell | recomputed | frozen (selection_freeze_v2 = D3_RECORDED = plan §2) | verdict |
|---|---|---|---|
| fees/side | 0.85 + 1.38 + 0.02 = **2.25** | 2.25 | MATCH |
| all-in/side | S1: 2.25+12.50+6.25 = **21.00**; S2: 2.25+25.00+6.25 = **33.50**; S3: 2.25+37.50+6.25 = **46.00** | 21.00 / 33.50 / 46.00 | MATCH |
| round trip | 2× = **42.00 / 67.00 / 92.00** | 42.0 / 67.0 / 92.0 | MATCH |
| window rows (2014-10-01..2017-12-31, NFA 0.01) | fees 2.24 → **20.99 / 33.49 / 45.99** | 20.99 / 33.49 / 45.99 | MATCH |

Labels binding carried identical: `MODELED COST`; documentation-A7 clean (AUTHORIZED_WITH_FINDINGS,
0 HIGH/CRITICAL); `VERIFIED_VS_ACCOUNT = NOT_RUN` (never inferred). Forbidden-value scan across the
entire v2 frozen surface (selection_freeze_v2, exclude_list_v2, freeze_diff, exposure_proof_v2,
FREEZE_DIFF.md): the strings `1.386` / `21.006` / `33.506` / `46.006` occur in exactly ONE place —
inside the `forbidden_values_law` retirement quotation itself; **0 use-as-value** in any numeric
field. The dry-run builder additionally asserts the retirement law at load time (lines 153-155).

## Check 4 — Pins now law: dry-run machinery implements EXACTLY the ratified definitions — PASS (no mismatch; no dry-run re-run owed by this check)

Machinery file: `research/control/FUTURES-ES-PB1-V1/dryrun/dryrun_builder.py`.
Measured sha256 `867946f3f1057049c7a1df7637494f15ac6dabaa4f801aa8abeea9f25878e3ee` — the file
present at HEAD `47d60303` is byte-identical to the file the ratification cites
(`dryrun_builder.py sha 867946f3` in all three `dryrun_recorded_default` strings of
`pins/pin_decisions.json`). Code read in full (750 lines). Exact matches:

**(a) D-A1 — `numpy.percentile(..., 80)` LINEAR on strict-past trailing-252d OVN tail.**
`dryrun_builder.py` lines 295-304:

```python
    # q80 threshold: trailing 252 computable |m| sessions, strict past
    # (IMPLEMENTATION PIN D-A4; percentile method D-A1).
    q80, m_hist = {}, []
    for d in dates:
        if len(m_hist) >= 252:
            q80[d] = float(np.percentile(m_hist[-252:], 80))
        else:
            q80[d] = None
        if d in m:
            m_hist.append(abs(m[d]))
```

- `np.percentile(m_hist[-252:], 80)` with no `method`/`interpolation` override → numpy default
  **linear** interpolation. MATCHES the ratified option "numpy.percentile(values, 80) linear
  interpolation".
- Window = trailing 252 **computable** |m| values (`m_hist`); **strict past**: for session `d` the
  threshold is computed BEFORE `|m[d]|` is appended (append is the last statement of the loop
  body). Consumed as `abs(mv) >= q` (line 448: skip iff `abs(mv) < q`). MATCHES the owner effect
  "applied to the strict-past trailing-252d OVN tail distribution".

**(b) D-A2 — C2 unconditional LONG, D0 entry, hold to era-correct close, no TP/SL.**

Line 368-369 (class map): `if iid == "FBES1-ALW-D0-S2": return {"klass": "C2", "delay": 0, "tier": "S2"}`
Line 462-463 (direction):

```python
        elif cfg["klass"] == "C2":
            direction = 1            # PIN D-A2 (unconditional long baseline)
```

Line 430 + 468-477 (D0 signal bar 08:30, fill = next 1m bar open):
`signal_min = D30_SIGNAL_MIN if cfg.get("delay") == 30 else RTH_OPEN_MIN` → C2 delay 0 ⇒ 08:30;
`i_fill = i_sig + 1; entry = float(s["o"][i_fill])` (with an exact `tns` adjacency guard).

Line 480 (no TP/SL) and 502-503 (hold to era-correct close):

```python
        use_tpsl = cfg["klass"] != "C2"
```
```python
        if reason is None:
            reason, exit_px, exit_bar = "TIME", float(s["c"][-1]), len(s["tod"]) - 1
```

Sessions are truncated at the era-correct close mark (line 242: `gg = g[g["tod"] < era_close_min(d)]`,
with `era_close_min` 16:30/16:15/16:00 CT per era, lines 86-91), so `s["c"][-1]` IS the era-correct
session close. C2's session set = the frozen per-fold eval sets (line 425-428), i.e. "every RTH
session" of the frozen surface. MATCHES the ratified option verbatim on all four elements
(unconditional LONG / D0 fill / hold-to-era-close / no TP/SL).

**(c) D-A3 — per-session `sha256('FBES1-PLA-D0-S2|seed=20261002|'+date)` first byte < 0x80 → ±1.**
`dryrun_builder.py` lines 105-110 (called at line 461 for C1):

```python
def c1_sign(session_date: str) -> int:
    # IMPLEMENTATION PIN D-A3 (see module docstring).
    d = hashlib.sha256(
        f"FBES1-PLA-D0-S2|seed=20261002|{session_date}".encode()
    ).digest()
    return 1 if d[0] < 0x80 else -1
```

Byte-exact string template `FBES1-PLA-D0-S2|seed=20261002|` + session date; sha256; **first byte**
`d[0] < 0x80` → `+1` else `-1`; pure function of the session date (deterministic per session);
seed 20261002 frozen. MATCHES the ratified option verbatim.

**Conclusion: 3/3 pin implementations EXACT. No CRITICAL; the dry-run does not need to be re-run
for pin fidelity.** (N-3 records the v1-freeze-surface note; N-4 records D-A4/D-A5 as declared,
non-ratified implementation pins.)

## Check 5 — PIT / exclude coverage on the v2 freeze: PASS

**(a) The PDF rule vs its sources** (`exclude_list_v2.json` ↔ `holiday/pdf_equity_evidence_2011_2015.json`, sha `f3a8b4d4…` MATCH):

| probe | result |
|---|---|
| 2015-07-02 excluded citing PDF sha `2c8831c2` | YES — row `HOLIDAY_PDF_EQUITY_2011_2015`, in_panel true, fold F2; evidence verbatim from `2015-4th-of-july-holiday-schedule.pdf` (sha `2c8831c207c60a421d3d1ae283632b77959198de83a07d16db4b4bc713abbaeb`): "1215 CT / 1315 ET / 1715 UTC –Early close"; `not_pdf_adjudicated_regular: true`. This is the v1 NOT_RUN blocker, resolved by exclusion (freeze_diff `v1_to_v2_blocker_resolution` → `EXCLUDED_ADJUDICATED`). |
| 2015-09-04 NOT excluded | YES — 0 rows in `exclude_list_v2`; evidence `regular_adjudicated_dates["2015-09-04"]` = REGULAR_CLOSE, `2015-labor-day-holiday-schedule.pdf` sha `56d4554c…` (matches the freeze's `pdf_files_sha256` list); verbatim "1615 CT / 1715 ET / 2115 UTC – Regular close"; freeze `new_rule_law.kept_included_by_adjudication` names it exactly. |
| 5 further spot-checks | 2012-04-06 (EARLY_CLOSE 0815, 2012-good-friday.pdf `85471dca…`), 2013-11-29 (EARLY_CLOSE 0515 CT, 2013-thanksgiving.pdf `cf84e247…`), 2013-12-24 (1215, 2013-christmas.pdf `b1c5403c…`), 2014-12-24 (1215, 2014-christmas-holiday-schedule.pdf `96b4b3fe…`), 2015-11-27 (1215, 2015-thanksgiving-holiday-schedule.pdf `f92e56dc…`) — all 5: exclude-row evidence == evidence-json entry (file+sha256+classification+time_ct), and each PDF sha matches the freeze's 53-file `pdf_files_sha256` list. |
| full-class sweep | all 36 in-panel `HOLIDAY_PDF_EQUITY_2011_2015` rows are backed by a CLOSED/HALT/EARLY_CLOSE candidate in the evidence json (56 candidates); 0 rows carry a regular adjudication; 0 evidence-sha incoherencies |

**(b) Superset law: v2 exclusion set ⊇ v1.** Re-derived by set arithmetic on in-panel dates:
v1 = 1,278 dates; v2 = 1,279 dates; **removals = NONE (v1 ⊆ v2 holds)**; additions = exactly
`{2015-07-02}`. Reason-class labels shifted for 35 sessions (COVERAGE_LT60 → HOLIDAY_PDF_EQUITY_2011_2015,
priority rank 2 beats rank 4; freeze_diff `class_relabels_same_set` n=35, `n_class_relabels: 35`)
— the SET is the union either way per `priority_rule`; exclusion count never decreased anywhere
(WARMUP 1008=1008, FOMC 131=131, HOLIDAY_FACT 10=10, HOLIDAY_UNCERTAIN 60=60, COVERAGE 69→34 with
the 35 re-labelled, +36 PDF class). Any removal would have been CRITICAL; **zero removals measured.**

**(c) Eval surface re-derived: 2,925 (F2 = 949).** Independently recomputed from the held T-5 chain
(single-shot read, 4,204 sessions 2010-06-07..2026-10-01) + the v2 exclusion set + fold windows +
positional warmup (d > warmup_carve_out.last):

| fold | re-derived n / first / last | frozen n / first / last | verdict |
|---|---|---|---|
| F1 | 375 / 2011-06-10 / 2012-12-31 | 375 / 2011-06-10 / 2012-12-31 | MATCH |
| F2 | **949** / 2014-01-17 / 2017-12-29 | **949** / 2014-01-17 / 2017-12-29 | MATCH |
| F3 | 711 / 2019-01-18 / 2021-12-31 | 711 / 2019-01-18 / 2021-12-31 | MATCH |
| F4 | 890 / 2023-01-18 / 2026-09-30 | 890 / 2023-01-18 / 2026-09-30 | MATCH |
| **total** | **2,925** | **2,925** (v1: 2,926; F2 950→949 only — freeze_diff `eval_surface`) | MATCH |

**(d) 2016 fail-closed basis.** `repair/exposure_proof_v2.json` epoch_2016: 258 sessions
(251 complete ≥234 bars + 7 partial <234), `n_ambiguous_rows = 0`, verdict
`FAIL_CLOSED_BASIS_PROVEN`; overall verdict PASS (zero blocker rows both sub-epochs). All 7
partial 2016 sessions (2016-01-18, 02-15, 05-30, 07-04, 09-05, 11-24, 11-25) are COVERAGE_LT60
and all 7 are excluded in-panel; ZERO 2016 rows carry the HOLIDAY_PDF class (deliberately does
not cover 2016); enumeration honestly NOT_RUN. **Independent re-derivation of the 2016-11-25
coverage fact by this lane** (single-shot panel read, held chain symbol ESZ6, dash-filtered):
RTH-core distinct minutes [08:30, 15:00) CT = **225/390 = 0.5769 < 0.60** → COVERAGE_LT60
exclusion independently JUSTIFIED; matches the proof row byte-for-value
(`bars_rth_core: 225, coverage_recomputed: 0.5769`). An earlier discrepant 391/390 reading during
this audit was traced to a unit bug in MY filter (ms vs ns), corrected, and re-measured to the
matching value — the artifact was right.

## Check 6 — Budget accounting: PASS

Registry row `FUTURES-ES-PB1-V1` (ROOT, read-only): `budget = {used: 0, max: 24}` — **used 0**.
Identity census (check 2) = 24 == registry max 24 == `IDENTITY_TABLES` ES cap 24 FROZEN; zero
unregistered cells. Repair invariants (`freeze_diff.invariants`): `trial_budget: 24, unchanged:
true`; `warmup_change: {identical: true, v1_n: 1008, v2_n: 1008}`. No ledger/counter/registry
write by this lane.

## Check 7 — Language scan + quarantine untouched: PASS

Token scan of the entire v2 frozen surface (selection_freeze_v2.json, exclude_list_v2.json,
freeze_diff.json, exposure_proof_v2.json, FREEZE_DIFF.md) for performance-claim language:
`expectanc*`, `profitab*`/`positive-PnL`/`PnL>0`/`measured PnL`, `measured cost`, typed-GO
phrase-as-consumed → **0 hits**. The typed GO string appears nowhere as consumed; the only
GO-adjacent text is the not_a_go_law itself. Quarantine directories (`dryrun/quarantine/`,
`dryrun/quarantine_rerun/`) verified by STRUCTURAL LISTING ONLY (26 files each = 24 identity JSONs
+ summary.json + trades_index.json; mtimes 2026-10-04, pre-audit); NO numeric read of any
quarantine file; start `git status` EMPTY proves no tracked file (incl. quarantine) was modified.

## Check 8 — Registry consistency (read-only): PASS with NOTE N-1

Row fields verified: `go_phrase` exactly `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` with
`go_phrase_state: REGISTERED_NOT_CONSUMED`; lifecycle `ACTIVE_LIGHT`; phase `REGISTERED`;
budget 0/24; `s1: SEALED_UNTOUCHED`; branch `prep/futures-es-reg-20261004` matches the worktree;
plan path exists at ROOT. `head = d44de21b…` verified to be an ANCESTOR of audit HEAD `47d60303…`;
the head-lag (branch advanced by the repair-wave commit; registry reconcile pending) is recorded
as **NOTE N-1** per dispatch instruction — not a finding.

## Verdict rationale

Zero CRITICAL, zero HIGH, zero MEDIUM findings. All nine checks PASS on fresh measurement.
The two owner decisions (PINS-D-A1-A2-A3, HOLIDAY-REPAIR-AUTH) are properly recorded,
outcome-blind, and faithfully implemented; the repair is superset-safe with exactly one
adjudicated addition; the 2016 fail-closed basis is machine-proven and independently re-measured.
Remaining obligations are NOTE-level and already carried in the freeze's own registers.

**AUTHORIZED_WITH_FINDINGS (0 HIGH/CRITICAL)** — this is audit key 1 of 2 only. It does NOT
authorize scoring, S1, orders, push/merge, or consume the GO phrase.

## R2 non-inheritance statement

No pass inherited from A7 v1 or any prior verifier. All 34 carried pins + 3 delta pins + 9 repair
cross-refs + manifest self-sha re-hashed fresh at `47d60303`; the 24-identity table re-transcribed
from SPEC bytes; the cost table recomputed from components; the pin implementations re-read from
the builder source (sha re-measured); the superset law, eval surface (chain read) and the
2016-11-25 coverage fact (panel read) re-derived; budget, language, quarantine and registry checks
re-executed. Prior verdicts (a33978b7 A7 v1, fc9c8362, d44de21b, and any verifier output) are
history, never evidence.
