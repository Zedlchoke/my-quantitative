# VERIFY_PREGO3 — final fresh-context independent verification, AUDIT-REPAIR wave
Cycle **FUTURES-ES-PB1-V1** · sub-wave verifier (pre-GO round 3) · 2026-10-05

## 0. Measurement anchors (X0)

- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
  (branch `prep/futures-es-reg-20261004`): one bare `rev-parse HEAD` →
  **`758aab74a5feaaeecae2e7e605c69df10de59cff`** — MATCHES the required SHA.
- ROOT `/Users/hoangminhlong/my-quantitative` (main): one bare `rev-parse HEAD` →
  **`bb4199d707abfb042519e06a6a393409c8c8c4bb`** — MATCHES the required SHA.
- `git status` at start: worktree CLEAN (`## prep/futures-es-reg-20261004`, no
  entries); root CLEAN on tracked files (`## main...origin/main [ahead 31]`).
- Git commands used (all read-only): 1× rev-parse per repo; status ×2 per repo
  (start/end); `log`/`log --follow`; `show --stat`/`show --name-only`;
  `show <rev>:<path>` (2 byte-extracts: pre-F-1 freeze, missing-path probe);
  `diff --name-only d1e5a5a6..758aab74`. Audit only; repaired nothing; zero
  network; zero quarantined-numeric reads (all quarantine-file checks were
  hash/structure only).
- Write boundary honored: this directory (`verify/prego3/**`) only.
- No handoff JSON written — this is a sub-wave verification; this file + its
  `.json` mirror are the deliverables.

## X1 — FAIL-before-fix discipline (the owner's core demand): **PASS**

Commit chain (chronological, from `git log` + per-file `--follow` + `--stat`):

| UTC (2026-10-05) | commit | content |
|---|---|---|
| 08:26 | `436d8cf8` | gate-3 re-run v2 ONLY (`a7_v2/` 3 files). No FAIL record, no DRYRUN-V2 artifacts (path probe: `dryrun_v2/DRYRUN_V2_REPORT.md` "not in 436d8cf8"). |
| 08:44 | `148a7bf5` | **DRYRUN-V2 verdict FAIL criterion (d)** — CRITICAL D-V2-1; `DRYRUN_V2_REPORT.md` L67/L70 record FAIL; lane applied NO mid-flight fix. |
| 08:58 | `d7170583` | the FIX: `dryrun_v2_1/` first appears (v2.1 carryover law). FAIL **strictly before** fix; no fix co-mingled with the FAIL commit. |
| 09:23 | `d1e5a5a6` | prior verifier verdict ALL_PRE_GO_CONDITIONS_PASS (later withdrawn). |
| 09:57 | **`456dac6b`** | **FAIL record D-V2-2** — `repair/FAIL_DONOR_VIOLATION.md`, single file, 35 insertions, nothing else ("no fix applied in this commit" proven by `--stat`). |
| 11:29 | `897e7519` | the FIX: machinery v3 (freeze v3 + C2 flag-based donor law). FAIL **strictly before** fix. |

- `FAIL_DONOR_VIOLATION.md` quotes SPEC §4 verbatim — I re-read the SPEC
  myself: `SPEC_PB1_ES.md` (sha `445f7499…`) §4 L87-89 ERRATUM A7-SPEC-M5
  contains exactly "**loại session short/flagged**" inside the SL law; the
  FAIL record's quote is character-exact.
- Withdrawal: FAIL record L34-35: "The previous ALL_PRE_GO_CONDITIONS_PASS
  verdict is WITHDRAWN pending the corrected gates' verification." — present.
- **Program-statement correction (INFO):** the dispatch's SHA labels for the
  D-V2-1 pair are transposed — the FAIL (d) was recorded at `148a7bf5` (08:44)
  and the v2.1 fix at `d7170583` (08:58); `436d8cf8` (08:26) contains only
  A7-v2 files. The SUBSTANTIVE law (FAIL recorded before every fix, in separate
  commits, no repair co-mingled with any FAIL record) is PROVEN either way.

## X2 — Donor law final state: **PASS**

- **(a) Re-derivation (mine, independent code path over the three JSONs):**
  v1 carryover (v1 labels ∩ {FACT_EARLYCLOSE, UNCERTAIN, COVERAGE_LT60},
  in-panel) = **139**; v3 five-family flags = 144; union = **144 exactly**
  (carryover fully subsumed — union adds nothing beyond the v3 flags).
  **Delta vs 139 = exactly the 5 named sessions**: 2015-07-02
  (`HOLIDAY_PDF_EQUITY_2011_2015`, no v1 label) + 2016-07-01, 2020-07-02,
  2021-07-02, 2021-12-31 (each `HOLIDAY_2016_UNPROVEN_FAILCLOSED`).
  v2-labels baseline = **140** = the FAIL record's "139 + 2015-07-02".
  All three counts match `dryrun_v3_digest.json § donor_law_v3` exactly.
- **(b) Builder donor hunk matches the SPEC law.** `final/dryrun_builder_v3.py`
  L248-259: `prev_short_flagged` from v1 labels (assert 139, carryover);
  `donor_family_v3 = {HOLIDAY_FACT_EARLYCLOSE, HOLIDAY_PDF_EQUITY_2011_2015,
  HOLIDAY_2016_UNPROVEN_FAILCLOSED, HOLIDAY_UNCERTAIN, COVERAGE_LT60}`;
  `sf_flags = {d … if cs & donor_family_v3}` (v3 labels);
  `short_flagged = sf_flags | prev_short_flagged` — flag-based on the CURRENT
  freeze per SPEC §4, carryover prevents any re-admission; count machine-
  derived (never asserted); FOMC_STATEMENT_DAY/WARMUP donor-admitted. The
  comment block (L224-239) cites the FAIL record and the SPEC verbatim.
- **(c) ONE logic hunk vs v2.1 — concurred from my own diffs.** My
  function-level AST diff: only `load_inputs` (C2 + input-path/schema shims),
  the criterion-(d) checker family (`_donor_series` new + checker-only usage —
  grep-verified, plus `check_surface_delta`→`_v3`), and `main` (digest
  metadata) differ; simulation chain `build_sessions / derive_state /
  parse_identity / simulate / era_close_min / c1_sign / run_pass /
  check_cost_sample / check_warmup_regression` AST-identical. Byte-level
  apparent diffs in `simulate`/`_tier_of` were my extractor over-capturing
  module-level FINDINGS/constants (docs + baseline-path shims), not function
  bodies. The criterion-(d) rewrite is the declared S5' post-hoc shim
  (baseline moved v2.1→v3, EXPECTED-CHANGE-TOLERANT per mission M3d) — gate
  checking, not simulation logic.
- **(d) Impact REPORTED, no preservation rationale.** `DRYRUN_V3_REPORT.md`
  §7 "The correction's real cost — reported honestly, NOT a defect":
  13,185 → **13,165** (20 removed on the 4 newly-excluded dates), **124**
  trades SL-changed on exactly the 59 derived SL-change dates, **21** exit
  knock-ons; digest cross-check: `n_trades_sl_changed_total=124`,
  `n_exit_changed_total=21`, 0 unexpected diffs, 0 attribution breaks,
  `gate4_verdict=PASS`, summary-table total = 13,165. Preservation sweep
  (grep for preserve/keep/restore-PnL rationales): only PROHIBITION language
  found ("NOT chosen to preserve any prior output", "NO choice was justified
  by keeping/restoring any prior PnL path" — in the FAIL record, the report,
  and the digest's `impact_discipline_law`). The report frames the impact as
  the correction's cost throughout.

## X3 — 2016 fail-closed: **PASS**

- **(a) Evidence-of-absence, no fetch:** `y2016/sweep_candidates_v3.json`
  (schema `y2016_audit_sweep@1`, 202 candidate rows 2010-2026) — `input_paths`
  are exclusively committed repo artifacts (universe sha `e56c4a53…`
  re-verified; 2011-15 PDF evidence; 2010 PDF; readiness/cal corpora). Zero
  2016 artifacts fetched; zero network; EVAL_V3 §4: the M1 sweep of every
  round dir found **zero 2016 schedule artifacts**; "the 2016 day-level
  enumeration itself remains NOT_RUN" is stated as an honest NOT_RUN_OBTAIN.
- **(b) The 11 additions:** all 11 present in `exclude_list_v3.json` with
  class `HOLIDAY_2016_UNPROVEN_FAILCLOSED`, in_panel=True, correct folds
  (8×F2, 3×F3) — I enumerated ALL 11 (exceeds the spot-6 requirement):
  4 new members + 7 relabels (each recorded with the replaced COVERAGE_LT60
  candidate evidence); addition file sha `1b846b17…` re-hashed MATCH.
- **(c) Eval surface:** independently re-derived from the session universe
  (4,204 sessions, sha verified) + `exclude_list_v3`: **375 / 948 / 708 / 890
  = 2,921 EXACT**, bounds match (F3 eval-last moved to 2021-12-30), and the
  warmup law holds (first 252 post-base sessions of every fold all
  WARMUP-excluded).
- **(d) Zero "proven regular" conversions:** v2→v3 set-diff = **+4 / −0**
  (no session ever left the exclusion set). The only KEEP_PROVEN_REGULAR rows
  (2010-07-02, 2010-12-31, 2011-07-01, 2026-07-02) rest on committed
  day-level artifacts naming those exact dates; the two 2010 keeps sit in F1
  WARMUP (excluded anyway); 2011-07-01's PDF adjudication binds 2011 only and
  was NOT used for 2016-07-01. `EVAL_V3` states "No pattern-candidacy was
  converted into 'proven regular' anywhere" — verified true.
- **(e) 2016-07-01 survivor story:** sweep row — in_panel, **390 bars**,
  coverage 1.0, v2_classes=[] (eval-eligible under v2), proof UNPROVEN →
  `V3_EXCLUDE_2016_UNPROVEN`. EVAL_V3 §0 records the rejected inference
  ("full 390 bars is not evidence of no-early-close; 2015-07-02 falsified
  it") and §3a names 2016-07-01 "The audit-predicted 2015-07-02-shaped
  exposure" — i.e. exactly the case the rejected inference would have missed.
  Corpus-wide, the ONLY other in-panel 390-bar unproven candidates are
  2020-07-02 / 2021-07-02 / 2021-12-31 (all now excluded) and 2022-07-01
  (warmup-closed). Story consistent end-to-end.

## X4 — A7-v3 + F-1 fix integrity: **PASS (with 1 LOW finding, below)**

- A7-v3 verdict: **AUTHORIZED_WITH_FINDINGS — 0 CRITICAL / 0 HIGH / 0 MEDIUM /
  1 LOW (F-1) / 2 NOTE** (report L26, digest `verdict` field). R2
  non-inheritance recorded (v1/v2 verdicts are HISTORY).
- F-1 fix landed at HEAD in `selection_freeze_v3`: my leaf-level diff of the
  freeze between `897e7519` and `758aab74` = **exactly 5 fields** — the four
  `n_surviving` values (627/1201/963/1142 → **375/948/708/890**, now equal to
  the load-bearing `eval_sessions.n`) + the embedded `_f1_correction_note`.
  NO load-bearing field changed ⇒ the A7-v3 adjudication remains valid for
  the post-fix freeze.
- Re-hash at THIS SHA: `exclude_list_v3.json` = **`b101f5c7…` MATCH** pin;
  `dryrun_builder_v3.py` = **`5a08c9fd…` MATCH** pin;
  `selection_freeze_v3.json` = **`de627f14…`** — intentionally differs from
  the pre-fix `a992baac…` (see LOW-2).
- Identities: 24/24 unique in the freeze; A7-v3 independently re-transcribed
  from SPEC §6 with composition P-A 8 / P-B 8 / FOMC 4 / C1-C4 4, zero
  unregistered cells, no D30×{S1,S3}.
- **Variant-A cells recomputed (4 checks, all exact):** fees/side
  0.85+1.38+0.02 = **2.25**; NFA-window fees = **2.24**; all-in/side =
  **21.00 / 33.50 / 46.00**; RT = **42.00 / 67.00 / 92.00**; window all-in =
  **20.99 / 33.49 / 45.99**. Forbidden values 1.386/21.006/33.506/46.006:
  my scan found them ONLY in ban-law strings/tuples (builder L71 comment +
  L197 ban tuple + L663 findings string; freeze `forbidden_values_law`;
  prose) and **0 numeric use-as-value in any machine artifact** (JSON scan
  of 9 artifacts).

## X5 — D-A4/D-A5 + gate-6 infra: **PASS**

- pins2 packet (`DA45_DECISION_PACKET.md` + `da45_decisions.json` sha
  `76fd46c0…` re-verified): D-A4 and D-A5 both **AUTHORITY_EXISTS /
  SPEC-text dispositive** (`dispositive: true`), 0 OWNER_DECISION_REQUIRED,
  0 CRITICAL flags. I grepped every quoted SPEC line myself (SPEC sha
  `445f7499…`): §3 L73-74 ("trailing-252d, strict-past … không tune"),
  §4 L85-90 (fill law; ERRATUM A7-SPEC-M5; R=2; same-bar SL priority),
  §5 L95 ("Chi phí MODELED COST (per side, USD)"), §6 L135-136 ("fold nhân
  evaluation không nhân identity"), §7 L139-143 (4 folds). All verbatim.
- **My concurrence (asked by the program):** I CONCUR the SPEC text is
  dispositive. §3/§4 window definitions are complete on their face and carry
  no fold qualifier; §6 makes folds evaluation-only; the warmup carve-outs
  (frozen, positional 252/fold-head) supply the trading-side fold-head
  protection, making fold-fenced windows a redundant unmentioned design; no
  law artifact anywhere mentions fold-fencing of donor windows (packet §2.3
  negative sweep — consistent with my own reading of the corpus layout).
  D-A5 cost half is denomination-dispositive (per-side USD + RT×2 + ladder;
  no price-space cost representation exists in the law) and the anchor half
  follows from R=2 semantics + the fill law. **Position on the one-line owner
  acknowledgment: NOT required as a substantive gate.** No owner choice
  exists to ratify; the adjudicated reading is the only one the frozen text
  admits, and the scored runner is already bound to it (runner spec + R2
  non-inheritance). The packet's "formal acknowledgment" is a record-
  hygiene formality that can ride with the GO message ("Confirmed: …" — the
  packet's own one-liners); its absence must not block GO, but I recommend
  including it at gate 5 so the scored-run law chain has zero dangling
  formalities.
- Gate-6 smoke (synthetic): digest `smoke_checks {pass: 28, fail: 0}` ✓.
  **My independent recomputation from the raw JSONL:**
  1. **observed=16 denominator arithmetic** — per-identity final statuses
     11 PASS / 5 FAIL / 8 REFUSED over 24 slots; 11+5 = **16** =
     `observed_denominator`; `counts_observed=true` on exactly the 16
     PASS/FAIL rows and false on every REFUSED/NOT_RUN row (denominator law
     implemented in the data itself); refusal ledger 9 rows, all REFUSED,
     zero counts_observed.
  2. **Append-only hash chain** — `prev_row_sha` = sha256(previous raw
     line): 30/30 links verified intact.
  3. **Reproduction twins** — twin_run_A vs B: 24/24 files byte-identical
     (sha256 per file); A vs C: exactly 1 differing file
     (perturb-fail design) ✓.
  Refusal classes present: paraphrased-GO / delegated-GO / registry-mismatch
  / no-A7-auth / unresolved-HIGH / lock-held / lock-drift / freeze-drift /
  owner-ordered-variant-pins. `SYNTHETIC_BANNER.txt` + per-artifact banners
  present ("fabricated data, zero real-outcome PnL, gates nothing").
- Scored runner + real-input gates: **NOT_RUN by law** (GATE6_READINESS
  component table rows 4/5/6/7; no typed GO exists).

## X6 — Registry + hygiene: **PASS**

- Registry row (ROOT `plans/CYCLE_REGISTRY.json`): `head =
  758aab74a5feaaeecae2e7e605c69df10de59cff` (= worktree HEAD);
  `go_phrase = "GO FUTURES-ES-PB1-V1 SCORED EXECUTION"` exact with
  `go_phrase_state = REGISTERED_NOT_CONSUMED`; lifecycle **ACTIVE_LIGHT**;
  budget **0/24**; s1 SEALED_UNTOUCHED; workers 0; active_heavy false.
- Reconcile commit **`bb4199d7` surgical**: touches exactly 3 control-plane
  files (`plans/CYCLE_REGISTRY.json`, `plans/ACTIVE_CYCLES.json`,
  `plans/CYCLE_REGISTRY.events.jsonl`); the registry diff contains ONLY
  envelope fields (updated_at_utc/writer/write_token) + the ES row's
  `head` (d7170583→758aab74) + its `updated_at_utc` — **zero foreign cycle
  rows changed**; events.jsonl gained exactly 2 append-only lines.
- `cycle doctor --json` (read-only): **0 findings for FUTURES-ES-PB1-V1**
  (71 total findings, all foreign cycles' stale worktrees).
- Wave diff `d1e5a5a6..758aab74`: 154 files, **all under
  `research/control/FUTURES-ES-PB1-V1/`** — NONE outside the cycle dir.
- Stale-value sweep: 0 use-as-value (X4; string-context occurrences are the
  ban law itself).
- GO string sweep: every occurrence of
  `GO FUTURES-ES-PB1-V1 SCORED EXECUTION` is in a LAW context — registry row
  field, plan §5 citation, runner-spec R1 refusal law, `CANONICAL_GO_PHRASE`
  gate constant, synthetic smoke fixtures, "NO GO / not_a_go_law" record
  strings, and verifier prose stating it remains owner-only. No consumed GO
  record exists anywhere.

## X7 — Pre-GO verdict

| # | Condition | Verdict |
|---|---|---|
| 1 | Registration (row exists, phase REGISTERED, head synced, phrase exact REGISTERED_NOT_CONSUMED, ACTIVE_LIGHT, 0/24) | **PASS** |
| 2 | Cost freeze D3=A (owner verbatim "tôi chọn 2.25$" pinned; Variant-A table recomputed exact; forbidden values 0 use-as-value; VERIFIED_VS_ACCOUNT stays NOT_RUN) | **PASS** |
| 3 | Pins D-A1/D-A2/D-A3 owner-ratified ("Đồng ý cả ba cách trên" as law in freeze) + implementation-verified (A7-v2 3/3 EXACT; A7-v3 re-check) | **PASS** |
| 4 | Pins D-A4/D-A5 AUTHORITY_EXISTS, SPEC-text dispositive | **PASS — and I CONCUR the SPEC text is dispositive; the one-line owner acknowledgment is a formality, NOT a blocking decision** (recommend it ride with the GO message) |
| 5 | Donor law corrected per SPEC §4 (FAIL-before-fix proven; 144 re-derived; ONE logic hunk; impact reported, no preservation rationale) | **PASS** |
| 6 | Holiday 2011-15 PASS (exposure_proof_v2 verdict PASS, unchanged) / 2016 fail-closed (all candidates excluded, zero exposure; enumeration honestly NOT_RUN) | **PASS** |
| 7 | A7-v3 AUTHORIZED_WITH_FINDINGS 0 C/H/M | **PASS** |
| 8 | Dry-run v3 gate-4 PASS (a-e; 24/24; 20/20; determinism; 0 unexpected diffs; warmup zero) | **PASS** |
| 9 | Gate-6 infra synthetic-tested 28/28 (denominator/chain/twins/refusals recomputed by me); scored runner NOT_RUN by law awaiting typed owner GO | **PASS (real run NOT_RUN by law)** |
| 10 | Registry synced (758aab74; surgical bb4199d7; doctor 0 ES findings) | **PASS** |
| 11 | Hygiene (wave confined; stale-value 0; GO string law-only; trees clean) | **PASS** |

NOT_RUN by law / honesty (none is a pre-GO blocker): 2016 day-level
enumeration (NOT_RUN_OBTAIN — exposure closed fail-closed); gate-5 typed GO
+ gate-6 real scored run + real twin + terminal A7 (owner only, post-GO);
VERIFIED_VS_ACCOUNT fees; BBO/depth; ES 2011-15 Globex transcription.

### Verdict: **GO_READY**

Zero CRITICAL/HIGH/MEDIUM findings. Remaining items before scored execution
(the exact list):
1. **Owner types the GO** at this cycle's own gate: `GO FUTURES-ES-PB1-V1
   SCORED EXECUTION` (gate 5; registry phrase consumed only then).
2. **Recommended (formality, may accompany the GO):** the one-line D-A4/D-A5
   acknowledgments from packet §2.5/§3.3 — closes the ratification chain
   with zero dangling formalities; not a substantive decision.
3. **Scored-run law pin:** the scored run consumes THIS verdict (R2
   non-inheritance) and should pin the operative freeze sha
   `selection_freeze_v3.json = de627f14…` (post-F-1 bytes) in its law
   record, since the freeze carries no self-hash and the A7-v3-measured
   pre-fix sha was `a992baac…`.

## Findings (this verification)

- **LOW-1** — F-1 fix is partial and its note overstates: `n_surviving` was
  refreshed (display now eval-consistent) but `n_base_excluded` remains
  v2-stale (F2 75 vs true 76; F3 72 vs true 75 — I recomputed both from
  `exclude_list_v3`), so the fold block still fails window−base−252 =
  surviving for F2/F3 (949≠948; 711≠708); `_f1_correction_note` claims BOTH
  fields were "refreshed". Display-only (nothing consumes `n_base_excluded`;
  builder derives eval sets from `exclude_list_v3`); non-blocking. Fix in
  the next freeze touch together with item 3 above.
- **LOW-2** — Operative-freeze sha drift vs adjudication: A7-v3 adjudicated
  `a992baac…`; the same-commit F-1 fix changed the bytes to `de627f14…`.
  Mitigations verified: leaf-diff proves display-only delta (5 fields);
  commit message discloses; R2 non-inheritance binds the scored run to this
  verdict. Resolved operationally by pre-GO item 3.
- **INFO-1** — The dispatch program statement's SHA labels for the D-V2-1
  FAIL-before-fix pair are transposed (FAIL at `148a7bf5`, fix at
  `d7170583`; `436d8cf8` holds only A7-v2). The FAIL-before-fix law holds
  regardless (X1).
- **INFO-2** — `repair/exposure_proof_v2.json` (HISTORY) retains the
  superseded "2016 basis PROVEN" claim; superseded append-only by
  `y2016/EVAL_V3`, which records the rejection explicitly. No action.

— End VERIFY_PREGO3. Both trees re-checked clean at end (only `verify/prego3/**`
added in the worktree). No GO exists or is implied by this verification; the
typed owner GO remains the sole authorization for scored execution.
