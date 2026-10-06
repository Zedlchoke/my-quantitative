# VERIFY_AT_19f42a8d — verifier-2 (fresh context), audit follow-up 2

- Round: `FUTURES-ES-PB1-REGPREP-20261004`
- Measured at (committed SHA): `19f42a8d15354bc214d623453357b98716cdaad9`
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
  (branch `prep/futures-es-reg-20261004`)
- Mode: audit only; repair nothing; zero network. Write boundary honored:
  this directory only (`verify/audit_followup2/**`). No handoff JSON written.
- Date: 2026-10-04

## Gates

| gate | command | result |
|---|---|---|
| HEAD | `git -C <wt> rev-parse HEAD` | `19f42a8d15354bc214d623453357b98716cdaad9` — MATCH |
| tree clean | `git -C <wt> status --porcelain` | EMPTY (exit 0, no output) → disk == committed tree; all content additionally measured via `git show 19f42a8d:<path>` |

## Y1 — F-AF1 closure (REGISTRATION_READINESS correction) — **PASS**

`freeze/REGISTRATION_READINESS.md` at 19f42a8d (143 lines):

| sub-check | evidence | verdict |
|---|---|---|
| ends with dated CORRECTION section | L129: `## CORRECTION 2026-10-04 (post-77a763ac audit, F-AF1 — append-only)`; file ends at L143 with the correction's final line | PASS |
| (a) supersedes the L80 blanket sentence with precise scoping | L131-136: explicitly supersedes §(b) sentence "The three remaining open rulings are FX/NYMEX-scoped…" at L80; scoping restated as **e.1 FX-scoped; e.2 geography-scoped (account-geography basis; not consumed under Variant A — the 0.011 offset is unused); e.3 NYMEX-scoped**, per D3_RECORDED sufficiency_conclusion (as completed) + A7_EXECUTION_PACKET §4 | PASS |
| (b) redirects pin basis to freeze/freeze_pins_v2.json AUTHORITATIVE | L137-141: "the AUTHORITATIVE pin manifest is **`freeze/freeze_pins_v2.json`** (34 pins re-hashed at the corrected final state; supersession record: `freeze/PIN_SUPERSESSION.md`). v1 stands as the lane-time historical measurement." | PASS |
| append-only (original text still present above) | `git show --numstat 19f42a8d` = `16 0` (insertions-only); original L80 sentence intact at L80; L128-143 are pure additions | PASS |

### Round-wide grep for blanket label `FX/NYMEX` (committed tree, `git grep -n 'FX/NYMEX' 19f42a8d -- <round dir>`)

**LIVE uses = 0.** 13 hit-lines, all classified ALLOWED:

| file:line | context | class |
|---|---|---|
| freeze/REGISTRATION_READINESS.md:80 | original §(b) sentence "The three remaining open rulings are FX/NYMEX-scoped…" | ALLOWED — superseded-original (now explicitly superseded by the appended correction in the same file) |
| freeze/REGISTRATION_READINESS.md:132 | correction section quoting the superseded sentence | ALLOWED — correction text |
| auth/D3_RECORDED.json:63 | `_fv1_correction` (labeled correction, quotes old label) | ALLOWED — correction field |
| auth/D3_RECORDED.json:72 | `_superseded_sufficiency_conclusion_1bcf07cc` | ALLOWED — superseded field |
| freeze/PIN_SUPERSESSION.md:32 | supersession narrative, label in quotes | ALLOWED — supersession record |
| REPORT_VI.md:66 | corrections-log text criticizing the label's imprecision for e.2 | ALLOWED — correction-history |
| dispatch/handoff_VERIFY.json:70 | F-V1 finding record, label in quotes | ALLOWED — historical finding |
| dispatch/handoff_FREEZE-AUDIT.json:83 | lane-time `readiness_conclusion` prose | ALLOWED-HISTORICAL — append-only lane artifact, byte-frozen (Y3: sha `297b839f…` unchanged); staleness disclosed via PIN_SUPERSESSION + the readiness correction chain (same classification as verifier-1 X6) |
| verify/VERIFY_REPORT.md:19,53,78 | verifier-0 findings quoting the label | ALLOWED — verifier quotation |
| verify/verify_findings.json:114 | finding record | ALLOWED — verifier record |
| verify/audit_followup/VERIFY_AT_77a763ac.md:132,142,200 | verifier-1's own classification table + F-AF1 finding | ALLOWED — verifier history |
| verify/audit_followup/verify_at_77a763ac.json:104,116,175 | same, machine mirror | ALLOWED — verifier history |

F-AF1 is CLOSED: the single residual live use verifier-1 flagged (REGISTRATION_READINESS §(b) L80) is now superseded in place by an append-only, dated correction with the precise e.1/e.2/e.3 scoping.

## Y2 — Pin stability at 19f42a8d — **PASS (34/34)**

Re-hashed all pins of `freeze/freeze_pins_v2.json` (sha256 of `git show 19f42a8d:<path>`) against `sha256_v2` (authoritative final-state field):

| metric | expected | measured |
|---|---|---|
| pin_count field / entries / unique paths | 34 / 34 / 34 | 34 / 34 / 34 |
| `sha256_v2` matches | 34/34 MATCH | **34/34 MATCH** |
| v1 `sha256` field matches | 33 + 1 disclosed delta | 33/34; exactly 1 delta = `auth/D3_RECORDED.json` (v1 `99661246…` → v2 `f54610eb…`, disclosed in manifest `deltas[]` + PIN_SUPERSESSION) |
| REGISTRATION_READINESS.md in v2 pin list | ABSENT | **ABSENT** — the F-AF1 append touched a file outside the pin set, so v2 pin stability is structurally unaffected |
| manifest self-pinned | no (no-self-reference law) | not self-pinned |

Per-pin results (all 34 `v2=OK`): SPEC_PB1_ES.md, PLAN_futures_es_v1.md, DATA_READINESS_ES.md, es_readiness.json, es_o1m_roll_recheck.json, es_expiry_recheck.json, es_session_holiday.json, OWNER_DECISIONS.md, SIX_SYMBOL_CENSUS.md, A7_FEE_REAUDIT.md, a7_fee_digest.json, COST_FREEZE_ERRATUM.md, IDENTITY_TABLES.md, SYNTHESIS_K6.md, SHORTLIST_STALE_COST_ERRATUM.md, D3_RECORDED.json, ES_fomc_stats.json, r3_fomc.json, BLS_VINTAGE_INVESTIGATION.md, bls_vintage_evidence.json, calendar_close_delta.json, CAL_CLOSE_REPORT.md, A7_EXECUTION_PACKET.md, es_1m_outright.parquet, es_1m_seg.parquet, es_chain_DECL.parquet, es_chain_OI.parquet, es_chain_T5.parquet, es_chain_VOL.parquet, es_contract_daily.parquet, es_contracts.json, es_roll_table.json, es_statistics_daily.parquet, es_vol_regime.parquet.

## Y3 — v1 + handoff untouched — **PASS**

| file | sha256 @77a763ac (git show) | sha256 @19f42a8d (git show) | sha256 (disk) | identical |
|---|---|---|---|---|
| freeze/freeze_pins.json | `da72dfca613c4a75b857463f97b332e40a7399fc6bf34d1cdcf94e440b2532f6` | same | same | YES |
| dispatch/handoff_FREEZE-AUDIT.json | `297b839fc296440f1dd98ba62858465c92a7603d2172423c8f04f943923b93de` | same | same | YES |

Handoff sha also matches verifier-1's X7 record (`297b839fc296440f…`).

## Y4 — Commit hygiene — **PASS**

| sub-check | evidence | verdict |
|---|---|---|
| exactly 1 file, insertions-only, +16 | `git show --stat 19f42a8d`: `freeze/REGISTRATION_READINESS.md | 16 ++++++++…`; numstat `16 0` | PASS |
| parent is the verifier-outputs commit | parent `980d98e2c63f34574857f360e6aa9f4db6c06c88` = "FUTURES-ES-PB1-REGPREP-20261004: verifier-1 outputs at committed SHA 77a763ac (…)" | PASS |
| nothing outside the round dir | `git diff --name-status 77a763ac 19f42a8d`: 3 paths, all under `research/control/FUTURES-ES-PB1-REGPREP-20261004/` (REGISTRATION_READINESS.md M; verify/audit_followup/VERIFY_AT_77a763ac.md A; verify_at_77a763ac.json A) | PASS |
| no registry/ledger changes in 77a763ac..19f42a8d | range = 2 commits (980d98e2 verifier outputs, 19f42a8d F-AF1 fix); changed-path set above contains no `plans/CYCLE_REGISTRY.json`, no ledger files | PASS |

## Y5 — Stale-value final sweep — **PASS**

`git grep -nE '1\.386|21\.006|33\.506|46\.006' 19f42a8d -- <round dir>` — **use-as-value = 0.** 10 hit-lines, all meta/law/classification:

| file:line | context | class |
|---|---|---|
| auth/D3_RECORDED.json:44 | `forbidden_values_law` (names the retired values as never-consumable) | law text |
| freeze/cost_freeze_check.json:233 | classification detail (false-positive trade price `19801.386` substring; stale row explicitly marked stale) | meta |
| synth/PRELAUNCH_A7_SPEC.md:16 | the scan's own pattern/program line ("use-as-value scan = zero") | meta |
| verify/VERIFY_REPORT.md:29 | classification detail citation | meta |
| verify/verify_findings.json:33 | classification detail | meta |
| verify/audit_followup/VERIFY_AT_77a763ac.md:151,153,204 | verifier-1 scan program/classification + F-AF5 note | meta |
| verify/audit_followup/verify_at_77a763ac.json:120,122,180 | machine mirror of the above | meta |

## Verdict

**PINS_STABLE_VERIFIED** — Y1 PASS, Y2 PASS (34/34), Y3 PASS, Y4 PASS, Y5 PASS.

## Git commands used (all read-only; repo named explicitly via `git -C`)

1. `git rev-parse HEAD` (once)
2. `git status --porcelain` (once)
3. `git show --stat 19f42a8d`
4. `git show --numstat --format=… 19f42a8d`
5. `git show 19f42a8d^ --format='%H %s' -s`
6. `git log --format='%H %s' 77a763ac..19f42a8d`
7. `git diff --name-status 77a763ac 19f42a8d`
8. `git show 77a763ac --format='%H %s' -s`
9. `git show 19f42a8d:research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/REGISTRATION_READINESS.md` (line count + lines 60-143)
10. `git grep -n 'FX/NYMEX' 19f42a8d -- <round dir>`
11. `git grep -nE '1\.386|21\.006|33\.506|46\.006' 19f42a8d -- <round dir>`
12. `git show 19f42a8d:…/verify/audit_followup/VERIFY_AT_77a763ac.md` (classification section, lines 125-160)
13. `git show 19f42a8d:…/freeze/freeze_pins_v2.json`
14. python3 loop: 34 × `git show 19f42a8d:<pin path>` sha256-hashed (Y2) + `git show` @77a763ac / @19f42a8d / disk reads for the 2 Y3 files
