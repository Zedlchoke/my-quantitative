# LAUNCH_CONTRACT_V2 — FUTURES-ES-PB1-V1 gate-6 scored runner (operative; supersedes gate6/scored_runner_spec.md v1)

- Lane RUNNER (pre-GO) · 2026-10-05 · worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`,
  branch `prep/futures-es-reg-20261004`, written at committed HEAD
  `8c8c5020174c8a1a5dd00e5d53ba168235407ec9`.
- **This contract authorizes nothing.** It is the operative launch contract
  the scored runner (`gate6/runner/scored_runner.py`) enforces. Every refusal
  is fail-closed: the runner REFUSES (zero denominator consumption) rather
  than approximating. The v1 spec (`gate6/scored_runner_spec.md`) is HISTORY —
  it pointed at the superseded surface (freeze v2 `cf150e24…`, builder v2.1
  `00141bf0…`, and `repair/DONOR_LAW_CARRYOVER.md` as an operative input,
  since withdrawn by D-V2-2). That file is not edited; this contract replaces
  it. The machine mirror is `LAUNCH_CONTRACT_V2.json` (the runner's pin
  source — the two are written and committed together).

## 1. Operative authority (all hashes measured at HEAD 8c8c5020…)

| item | path (worktree-relative) | sha256 | status |
|---|---|---|---|
| Operative freeze v3 | `research/control/FUTURES-ES-PB1-V1/final/selection_freeze_v3.json` | `0b0d269abbcafd065fa84ba3ba1047ac27df7fcc86675ccfef6f47666d951ff9` | OPERATIVE — exact sha per `final/OPERATIVE_FREEZE_PIN.md` (`5b3ea93c…`) |
| Freeze pin law record | `…/final/OPERATIVE_FREEZE_PIN.md` | `5b3ea93c9f389c2fae6467d55b54248f4864138a7d49aff77cba0fc0bee3da4c` | OPERATIVE |
| Exclusion set v3 | `…/final/exclude_list_v3.json` | `b101f5c7490f9a182ef6be6d188322ce368fe79476c3f3f46f37bca7cdc5b4aa` | OPERATIVE (round-trips inside freeze `exclude_list.sha256`) |
| Machinery of record | `…/final/dryrun_builder_v3.py` | `5a08c9fd8a94948cc61762933f77e5fe7db660ade43e1f2d140d2c628e164906` | OPERATIVE |
| Freeze/builder generators | `…/final/build_freeze_v3.py` / `…/final/make_builder_v3.py` | `b8adbd67…` / `cf0fd897…` | OPERATIVE lineage |
| A7 prelaunch v3 | `…/a7_v3/A7_PRELAUNCH_V3.md` + `a7_prelaunch_v3_digest.json` | `f8842e3d…` / `d42f27d9…` | OPERATIVE R2 authority — AUTHORIZED_WITH_FINDINGS, 0 CRITICAL / 0 HIGH / 0 MEDIUM (1 LOW F-1, 2 NOTE N-1/N-2). A7 v1/v2 verdicts are HISTORY, never inherited (R2 non-inheritance) |
| SPEC of record | `research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` | `445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073` | OPERATIVE (§4 ERRATUM A7-SPEC-M5 donor law; §5 stale cost prints NOT consumed) |
| Pinned panel | `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet` | `7ae6de2d5896d9e150f70209f2709ca70b625f0b06bbdbfed348b1b0e0227b95` | OPERATIVE (7,825,657 bars; preflight = existence+sha ONLY) |
| Held chain | `…/ES_cache/es_chain_T5.parquet` | `7b6179d27a2c9da7dd5972f03d40209ded0119aabfc14a5abc08167894e8f06f` | OPERATIVE (4,204 sessions; same access law) |
| Identity table source | `research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/identity_table_24.json` | `6e3919808ecea86d147ba67d8e5df4f4e83bed2414973f87de051054da6e471f` | OPERATIVE (== freeze `identity_table.source_sha256`) |
| Repair authority | `…/auth/PREGO_REPAIR_RECORDED.json` | `db0360fa…` | OPERATIVE |
| Holiday evidence | `…/holiday/pdf_equity_evidence_2011_2015.json` | `f3a8b4d4…` | OPERATIVE |
| D-A4/D-A5 adjudication | `…/pins2/DA45_DECISION_PACKET.md` + `da45_decisions.json` | `3acc6e9d…` / `76fd46c0…` | OPERATIVE (both AUTHORITY_EXISTS, SPEC-text dispositive) |
| D-V2-2 correction record | `…/repair/FAIL_DONOR_VIOLATION.md` | `2f06de66…` | OPERATIVE (== freeze `donor_law.correction_record.sha256`) |
| Donor carryover law | `…/repair/DONOR_LAW_CARRYOVER.md` | `314ae9478da23b012babb46a4d4989da52a985d3415410bc41c4b703d0767d7d` | **HISTORY — REJECTED as donor-law source.** The freeze itself declares it withdrawn (`freeze.donor_law.supersedes`); the runner verifies that declaration and NEVER consumes it as law |
| Trial ledger (fixed) | `…/gate6/trial_ledger.py` | `bf89be550705d0474e0214c51417ca1c57f7cf168b822f38a46b7b77affd5a2c` | OPERATIVE — the reopen/append cursor fix (commit `8c8c502`); the runner imports THIS file and re-hashes it at startup |
| A7-adjudicated freeze bytes | `selection_freeze_v3.json` @ `a992baac…` | `a992baac3c6dc8c37f05d74edce9bba4d604ec20db8ce9b7e55a525490f616bb` | HISTORY — superseded by `0b0d269a…` via the two disclosed display-only corrections (F-1 + VP3-L1), load-bearing fields byte-identical per the verifier |

## 2. Embedded laws (re-verified against the LIVE freeze bytes at every run)

- **Identities**: exactly 24 (P-A 8 / P-B 8 / FOMC 4 / C1–C4 4), byte-exact
  order+set vs the contract's embedded id list; the runner re-derives ids from
  the live freeze — mismatch ⇒ `REFUSED_DRIFT`.
- **Folds**: F1–F4, eval 2,921 sessions (375 / 948 / 708 / 890); fold
  multiplies evaluation, never identity (SPEC §6 L135-136).
- **Costs — Variant A only** (owner D3 "tôi chọn 2.25$"; COST_FREEZE_ERRATUM
  supersedes stale SPEC §5 prints): fees 2.25/side (0.85+1.38+0.02); all-in
  21.00 / 33.50 / 46.00 per side (S1/S2/S3); RT ×2 (42/67/92); retired values
  `1.386 / 21.006 / 33.506 / 46.006` banned as values; labels MODELED COST /
  VERIFIED_VS_ACCOUNT=NOT_RUN, never upgraded.
- **Donor law**: SPEC §4 [ERRATUM A7-SPEC-M5] — flag-based on the CURRENT
  freeze ("loại session short/flagged"); donor set machine-derived 144;
  carryover 139 fully subsumed; `DONOR_LAW_CARRYOVER.md` WITHDRAWN history.
- **Budget**: max 24 identities (registry row budget.max), used 0 at contract
  time; S1 SEALED_UNTOUCHED.

## 3. Refusal gates v2 (fail-closed, evaluated in order; ANY failure ⇒ refuse, nothing computed)

| # | gate | pass condition | refusal verdict |
|---|---|---|---|
| R0 | REGISTRY | the runner itself loads the ROOT registry row (`plans/CYCLE_REGISTRY.json`) — no caller booleans: row exists; `row.branch` == actual branch; `row.go_phrase` byte-exact == `GO FUTURES-ES-PB1-V1 SCORED EXECUTION`; `row.head` == actual `git -C <worktree> rev-parse HEAD`. Head policy: MATCH required; LAG_ANCESTOR (row head a proper git ancestor — the disclosed N-1 character, doctor LOW) FAILS the execution gate (controller reconciles the registry via its own tooling first); DIVERGED (not an ancestor) is proven control-plane corruption | `REFUSED_CONTROL_STATE_DRIFT` |
| R1 | NO_GO | GO artifact (default `auth/GO_RECORDED.json`) present, parses, `cycle_id` matches, `key_2_owner_go.verbatim` BYTE-EQUAL to the canonical phrase (no trim/case-fold — paraphrase dies), `typed_by_owner` true + `typed_by == "OWNER"` (delegation language anywhere ⇒ refuse), `key_1_a7_prelaunch.sha256` == the operative A7-v3 digest sha (a GO bound to a7 v1/v2 is EARLY/SUPERSEDED ⇒ refuse), registry `go_phrase` consistent. GO in a prompt/chat is intent only and dies unconsumed. ABSENT ⇒ refuse (this is the state TODAY) | `REFUSED_NO_GO` |
| R2 | NO_AUTH | A7-PRELAUNCH-V3 md + digest present at pinned shas; verdict `AUTHORIZED_WITH_FINDINGS`; severity CRITICAL=0, HIGH=0, MEDIUM=0 | `REFUSED_NO_AUTH` |
| R3 | LOCK | canonical machine-wide heavy-lock inspect ⇒ `FREE_PROVEN`. The check is the `governance.heavy_lock.inspect()` decision tree (flock on `~/.my-quantitative-governance/heavy_runtime/heavy_worker.lock` + `heavy_worker.registry.json` + pid liveness + process-start token), reimplemented READ-ONLY with an injectable runtime dir and DELEGATED to the governance module's own primitives — never a weaker check. `HELD_PROVEN` ⇒ conflict; `CONTROL_STATE_DRIFT` ⇒ drift refuse. (The ACQUIRE is the post-GO lane's act, immediately before panel access.) | `NOT_RUN_RESOURCE_CONFLICT` / `REFUSED_CONTROL_STATE_DRIFT` |
| R4 | DRIFT | every §1 pin re-hashed and matched from the real paths; freeze round-trips: `freeze.exclude_list.sha256` == sha256(`exclude_list_v3.json`); live-freeze identity ids == contract list (byte-exact); cost table + forbidden-value ban strings present; eval total 2,921; `freeze.donor_law.supersedes` names DONOR_LAW_CARRYOVER at `314ae947…`; `A7-SPEC-M5` present in the freeze donor law; trial_ledger.py re-hash == pin | `REFUSED_DRIFT` |
| R5 | ADJUDICATION | D-A4/D-A5 stand as adjudicated `AUTHORITY_EXISTS` per the pinned `da45_decisions.json`; the scored run consumes the adjudicated readings verbatim; any different choice is a freeze amendment, never a runner option | `REFUSED_PINS_UNRESOLVED` |

## 4. Execution law (pre-GO stub)

When — and only when — R0–R5 all pass, the runner enters the execution path.
**In this lane that path is a STUB**: it logs `WOULD EXECUTE` plus the planned
invocation sketch and computes nothing. The real scored wiring — two
independent passes over the machinery of record (`final/dryrun_builder_v3.py`
adapted, mechanics unchanged), per-identity outputs + trades index, G8
byte-match twin, per-identity terminal ledger rows, digest + manifest, lock
acquire/release in `finally`, terminal A7 hook — is the POST-GO lane's job and
must be built against THIS contract. The scored run is the FIRST PnL
computation; no quarantined numeric is ever consumed.

## 5. Ledger + preflight law

- Ledger: `gate6/trial_ledger.py` (the FIXED module — imported, never
  reimplemented) opens the 24-slot ledger. Execution-mode default path
  `gate6/ledger/trial_ledger.jsonl`; every run-level refusal is recorded via
  `TrialLedger.record_refusal(reason, note)` (`identity_id=None`); REFUSED
  never increments the observed denominator (registered plan §6).
- `--preflight-only`: READ-ONLY proof the wiring touches REAL authority —
  existence + sha of every pin from the real paths, real registry row, real
  lock inspect, real GO-absence detection; NO outcome computation, NO parquet
  parse, NO writes (except the optional deterministic `--manifest-out`, which
  carries no wall-clock fields). Preflight exit 0 = all pins green + lock
  FREE_PROVEN (GO absence is the EXPECTED pre-GO state; a disclosed
  LAG_ANCESTOR registry head is recorded as a finding with
  `must_reconcile_before_go: true`); exit 2 = any drift / auth failure / lock
  conflict-or-drift / DIVERGED head. Preflight exit 0 is NOT an authorization.
- Reproduction: two preflight runs produce byte-identical twin manifests (the
  PREFLIGHT twin; the real reproduction twin of scored OUTPUTS is post-GO).

## 6. Invariants

No push/merge/history-rewrite; no S1; no network; root read-only; registry
written only by its own tooling; budget counters touched only by the
controller through the registry's own tooling; Python = ROOT `.venv`; one
heavy job machine-wide; the runner never commits.

— End LAUNCH_CONTRACT_V2.

---

# v2.1 ADDENDUM (2026-10-05, lane EXEC-BUILD) — the real execution path

Append-only correction of record per gate6/runner/GO_READY_WITHDRAWAL.md:
the §4 pre-GO "WOULD EXECUTE" stub is **REMOVED**. The machine pin source
(`LAUNCH_CONTRACT_V2.json`) carries the same addendum under
`v2_1_addendum` (append-only; no prior key rewritten; all `§embedded_laws`
and `§pins` above are UNCHANGED and remain the operative authority).

## 4.1 Execution path (replaces the §4 stub paragraph)

When — and only when — R0–R5 all pass, the runner invokes the REAL execution
path `gate6/runner/scored_executor.py`:

1. **Lock lifecycle** — acquire via the CANONICAL
   `governance.heavy_lock.acquire` (never reimplemented; in `--sandbox-root`
   mode the canonical runtime is redirected under the sandbox for the run
   and restored in `finally`). AFTER acquire, the runner re-verifies the GO
   artifact, the registry head (must be MATCH) and the input pins
   (freeze/exclude/panel/chain/identity table/builder/trial ledger) — any
   drift ⇒ `REFUSED_CONTROL_STATE_DRIFT`, lock released. Release happens in
   `finally` ALWAYS (`FINISHED` / `FAILED` / `TECHABORT`), exceptions
   included. Lock held at acquire ⇒ `NOT_RUN_RESOURCE_CONFLICT` (ledger
   REFUSED row, exit 75).
2. **Computation** — the machinery of record `final/dryrun_builder_v3.py`
   is IMPORTED (never forked): `load_inputs / build_sessions /
   derive_state / parse_identity / simulate / c1_sign / check_cost_sample /
   check_warmup_regression` run verbatim (production = pinned module +
   real pinned inputs, sha-asserted; sandbox = the SAME source executed
   with only its location constants redirected to the synthetic fixtures).
3. **Ledger** — the FIXED `gate6/trial_ledger.py` opens the 24-slot
   ledger. Every scientifically computed result is recorded to the observed
   denominator (PASS / FAIL; `published=false` on a publication failure)
   even if subsequent publication fails. Per-identity terminal rows exactly
   once; an interrupted run's retry SKIPS already-terminal slots (never
   recompute, never double-count, never mint identities), copying the prior
   run's published bytes after verifying the recorded `result_sha`.
4. **Publication + reconciliation** — per-identity outputs + trades index +
   summary under a run dir; a reconciliation summary against the frozen
   identity table; any mismatch ⇒ fail-closed.
5. **Reproduction twin** — a second independent pass (fresh machinery
   instance, fresh input load, separate output dir) must be byte-identical;
   a twin mismatch ⇒ terminal state `TWIN_MISMATCH`, NEVER success.
6. **Terminal handoff** — `terminal_handoff.json` per run (paths + shas of
   outputs, twin manifests, ledger summary, lock record, verdict) for the
   post-GO terminal A7.
7. **Fail-closed law** — any computation/ledger/publication/twin failure ⇒
   non-zero exit + terminal state recorded; success is NEVER returned for
   incomplete execution.
8. **Sandbox isolation law** — synthetic fixtures and fault injection live
   ONLY under `--sandbox-root`: (a) authority inputs (GO artifact, registry
   row copy, contract, freeze/panel paths, ledger, lock runtime) resolve
   under the sandbox; (b) every output is stamped `SYNTHETIC-SANDBOX`;
   (c) `--sandbox-root` combined with any real-root authority path REFUSES;
   (d) the production default (no flag) uses ONLY the real paths + real
   authority — ANY authority-path override reaching the execution branch
   refuses (anti-bypass guard); (e) a sandbox run cannot write the real
   ledger, the real registry, or the machine-wide lock runtime.

## 4.2 Pins added by v2.1 (see `v2_1_addendum.new_pins` in the JSON)

`scored_executor` f5ad7d48… · `scored_runner_v2_1` 18258cf1… ·
`test_execution_path` d9d011c1… · `test_runner_refusals_v2_1` 3678446b… ·
`make_sandbox_fixtures` 588775db…

## 4.3 Pre-GO state — UNCHANGED

With no typed owner GO at this cycle's gate the runner still REFUSES
(proven on the real state in its own smoke test). NO real scored outcome
has been computed. The fake GO exists ONLY inside the sandbox fixtures.
