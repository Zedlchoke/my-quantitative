# VERIFY_AT_77a763ac — independent audit-followup verification (fresh context)

- Round: `FUTURES-ES-PB1-REGPREP-20261004`, wave: audit-followup
- Measured at: **`77a763ac4c5389fb674eac287e7876ef83aba04e`** (branch `prep/futures-es-reg-20261004`)
- Verifier role: independent, audit-only; repair nothing; zero network; zero PnL
- Measurement mode: **working tree** (X1 proved clean tree == committed SHA; no git-show fallback needed)
- Machine mirror: `verify/audit_followup/verify_at_77a763ac.json`

## X1 — Working state is the committed SHA — **PASS**

| evidence | value |
|---|---|
| `git rev-parse HEAD` | `77a763ac4c5389fb674eac287e7876ef83aba04e` (exact match) |
| `git status --porcelain` | EMPTY (clean) |
| mode used | working tree (permitted, since clean at exact SHA) |

## X2 — v2 manifest completeness (load-bearing) — **PASS**

`freeze/freeze_pins_v2.json` (sha256 `f7e1b580071c0952…`) re-hashed pin-by-pin by this verifier
(sha256 of raw file bytes, independent of the manifest):

- `pin_count` field = 34; actual `pins[]` length = 34 ✓
- **34/34 pins MATCH disk at 77a763ac against `sha256_v2` (authoritative field)** — zero mismatches
- `delta_count` = 1; single delta = `research/control/FUTURES-ES-PB1-REGPREP-20261004/auth/D3_RECORDED.json`;
  delta `v1_pin` = `99661246…715d8` == v1's D3 pin; delta `v2_pin` = `f54610eb…1e355` == actual disk hash ✓
- Legacy `sha256` field: 33/34 (D3's legacy field intentionally retains the lane-time `99661246…`;
  the delta block discloses this — authoritative field is `sha256_v2`)
- Cross-check vs `freeze/freeze_pins.json` (v1): same 34 paths; **33/34 pin values identical**;
  sole difference = D3 (as declared). v1 **UNMODIFIED**: sha256 `da72dfca613c4a75…` identical at
  1bcf07cc (via `git show`) and at 77a763ac (working tree); v1 D3 pin = `99661246…` (lane-time) intact;
  v1 `head_sha_at_pinning` = `ffed828f…`, summary `pin_count_total: 34` intact

Full 34-row re-hash (all MATCH vs `sha256_v2`):

| # | path (repo-relative) | sha256_v2 (first 16) | re-hash | verdict |
|---|---|---|---|---|
| 1 | FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md | 445f749906481f33 | 445f749906481f33 | MATCH |
| 2 | FUTURES-ES-V1-PACKET/PLAN_futures_es_v1.md | 06140882f13d96fd | 06140882f13d96fd | MATCH |
| 3 | FUTURES-SIX-READINESS-20261004/es/DATA_READINESS_ES.md | 1407b1d4828c4d71 | 1407b1d4828c4d71 | MATCH |
| 4 | …/es/es_readiness.json | 84cefa3a5c1453f1 | 84cefa3a5c1453f1 | MATCH |
| 5 | …/es/es_o1m_roll_recheck.json | e7ab27ea2bfaab16 | e7ab27ea2bfaab16 | MATCH |
| 6 | …/es/es_expiry_recheck.json | 2b065d5b94540e27 | 2b065d5b94540e27 | MATCH |
| 7 | …/es/es_session_holiday.json | 8885d5de4e7f4c5f | 8885d5de4e7f4c5f | MATCH |
| 8 | …/synth/OWNER_DECISIONS.md | d14e436f9110dd1a | d14e436f9110dd1a | MATCH |
| 9 | …/synth/SIX_SYMBOL_CENSUS.md | 7c006db6aa0aecb5 | 7c006db6aa0aecb5 | MATCH |
| 10 | FUTURES-SIX-SCORED-GATE-PREP-20261004/fee_a7/A7_FEE_REAUDIT.md | 2c1095d63af35dda | 2c1095d63af35dda | MATCH |
| 11 | …/fee_a7/a7_fee_digest.json | fa697c691d2914fd | fa697c691d2914fd | MATCH |
| 12 | …/synth/COST_FREEZE_ERRATUM.md | cf83bc2d41bd6a30 | cf83bc2d41bd6a30 | MATCH |
| 13 | …/budget/IDENTITY_TABLES.md | 750858ab60b8930a | 750858ab60b8930a | MATCH |
| 14 | FUTURES-K6GATE-PREP-20261004/synth/SYNTHESIS_K6.md | 03a8e77e2120f60c | 03a8e77e2120f60c | MATCH |
| 15 | …/synth/SHORTLIST_STALE_COST_ERRATUM.md | 7fe438c2771a89e4 | 7fe438c2771a89e4 | MATCH |
| 16 | **FUTURES-ES-PB1-REGPREP-20261004/auth/D3_RECORDED.json** | **f54610eb15e6cb41** (delta) | f54610eb15e6cb41 | MATCH |
| 17 | FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json | 228fe2d4efbde959 | 228fe2d4efbde959 | MATCH |
| 18 | …/audit/a7_es/r3_fomc.json | ba57bc3325559b7f | ba57bc3325559b7f | MATCH |
| 19 | FUTURES-OVERNIGHT-PREP-20261003/bls_vintage/BLS_VINTAGE_INVESTIGATION.md | 2b18f6ce27158c21 | 2b18f6ce27158c21 | MATCH |
| 20 | …/bls_vintage/bls_vintage_evidence.json | cf246d7306a6d12b | cf246d7306a6d12b | MATCH |
| 21 | FUTURES-SIX-SCORED-GATE-PREP-20261004/cal_close/calendar_close_delta.json | 626deccc5debad9e | 626deccc5debad9e | MATCH |
| 22 | …/cal_close/CAL_CLOSE_REPORT.md | 338cf4e8ffc086ae | 338cf4e8ffc086ae | MATCH |
| 23 | FUTURES-SIX-ADOPT-PREP-20261004/fee_es/A7_EXECUTION_PACKET.md | a000c478636c3f5f | a000c478636c3f5f | MATCH |
| 24 | FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet | 7ae6de2d5896d9e1 | 7ae6de2d5896d9e1 | MATCH |
| 25 | …/ES_cache/es_1m_seg.parquet | 787c4912622e844b | 787c4912622e844b | MATCH |
| 26 | …/ES_cache/es_chain_DECL.parquet | fe21a78ef180b428 | fe21a78ef180b428 | MATCH |
| 27 | …/ES_cache/es_chain_OI.parquet | 11426c4ff8dc9a8b | 11426c4ff8dc9a8b | MATCH |
| 28 | …/ES_cache/es_chain_T5.parquet | 7b6179d27a2c9da7 | 7b6179d27a2c9da7 | MATCH |
| 29 | …/ES_cache/es_chain_VOL.parquet | 9f5311de33958d02 | 9f5311de33958d02 | MATCH |
| 30 | …/ES_cache/es_contract_daily.parquet | 763b9cd46ee837b4 | 763b9cd46ee837b4 | MATCH |
| 31 | …/ES_cache/es_contracts.json | 9939fb866b5db1f1 | 9939fb866b5db1f1 | MATCH |
| 32 | …/ES_cache/es_roll_table.json | 7a8da4857d1a9b0d | 7a8da4857d1a9b0d | MATCH |
| 33 | …/ES_cache/es_statistics_daily.parquet | 4710d0e815a5ffba | 4710d0e815a5ffba | MATCH |
| 34 | …/ES_cache/es_vol_regime.parquet | 551a1185359067c9 | 551a1185359067c9 | MATCH |

## X3 — Supersession documentation fidelity — **PASS**

`freeze/PIN_SUPERSESSION.md`:

- Quotes both stale-pin pairs exactly (prefix-exact):
  - pair 1: v1 pins `auth/D3_RECORDED.json` at `99661246…` while committed file was `97bf1ad3…` ✓
  - pair 2: handoff outputs[] pins `freeze/cost_freeze_check.json` at `d6b9be83…` while committed file was `53e7e016…` ✓
- Old hashes verified to actually exist in the primary artifacts:
  - `99661246…715d8` = v1 `freeze_pins.json` D3 pin (read from file) ✓
  - `d6b9be83…4cfaa0` = `handoff_FREEZE-AUDIT.json` `outputs[2].sha256` (cost_freeze_check.json) ✓
- Audit numbers **reproduce from git objects**:
  - `git show 1bcf07cc:…/auth/D3_RECORDED.json` → sha256 `97bf1ad32ea8145271f143b73d9e0f6f95bbc03ce9a86b5bf12cff21b4e526ee` ✓
  - `git show 1bcf07cc:…/freeze/cost_freeze_check.json` → sha256 `53e7e016a529c028839cb32c65b2eba2ba54d993448e3a8b852f243b3b11496d` ✓
- States the no-self-reference law (its own §, plus `freeze_pins_v2.json.self_reference_law`) ✓
- v2 `handoff_output_pin_supersession` final-state pins **match disk**:
  - cost_freeze_check final `53e7e016…` == working-tree hash of `freeze/cost_freeze_check.json` ✓
    (note: the wave did NOT touch this file — its 1bcf07cc state IS the final state)
  - D3 final `f54610eb…` == working-tree hash of `auth/D3_RECORDED.json` ✓

## X4 — No self-referential hash loop — **PASS**

- `freeze_pins_v2.json` does NOT contain its own sha256 (`f7e1b580071c0952…` absent from the file) ✓
- v2 pins NO verification-scope docs: no pin path is REGISTRATION_PACKET / PRELAUNCH_A7_SPEC /
  DRYRUN_SPEC / REPORT_VI / verify/** / dispatch/** / freeze_pins* / PIN_SUPERSESSION ✓
- `synth/REGISTRATION_PACKET.md` (L30) references `freeze_pins_v2` as AUTHORITATIVE — one-directional ✓;
  PRELAUNCH_A7_SPEC (L6) and REPORT_VI (L76) also point to v2
- Nothing pins the packet: sha256 of REGISTRATION_PACKET (`2d0d30141407bf79…`), PRELAUNCH_A7_SPEC
  (`c61c9fc4e0590e1a…`), DRYRUN_SPEC (`7c7da6225b0ba185…`), REPORT_VI (`2c89f961b451f067…`),
  PIN_SUPERSESSION (`98653e4bd73d91b1…`), v2 itself — none appear in any round .md/.json ✓
- Reverse-walk: nothing pins `handoff_VERIFY.json` (`531a6c68…`) or `handoff_FREEZE-AUDIT.json`
  (`297b839f…`) bytes → no cycle ✓
- Chain spot-walk: v2 → 34 artifacts (verified); packet/spec/report → v2 (reference);
  PIN_SUPERSESSION → v1 + handoff **by QUOTE only** (historical hash strings, not byte pins) ✓
- Output-ledger recordings (one-directional, no cycle): handoff_FREEZE-AUDIT records v1's hash;
  handoff_VERIFY records VERIFY_REPORT/verify_findings hashes; none of those files hash the handoffs back ✓

## X5 — D3 record integrity after the wording fix — **PASS**

`auth/D3_RECORDED.json` (sha256 `f54610eb15e6cb41…`):

- `decision_quote_verbatim` == `"tôi chọn 2.25$"` EXACTLY ✓
- Effective cost table recomputes from components:
  - fees/side: 0.85 + 1.38 + 0.02 = **2.25** ✓
  - all-in/side: 2.25 + 6.25 (spread half-turn) + {12.5, 25.0, 37.5} = **21.00 / 33.50 / 46.00** ✓
  - RT ×2 = **42 / 67 / 92** ✓
  - window (reg 0.01): 0.85 + 1.38 + 0.01 = 2.24 → all-in **20.99 / 33.49 / 45.99** ✓
- `sufficiency_conclusion` scopes precisely: e.1 FX-scoped; e.2 **geography-scoped, not symbol-scoped**
  (IBKR offset 0.011 unused under A); e.3 NYMEX/CL/NG-scoped ✓
- `_superseded_sufficiency_conclusion_1bcf07cc` preserves the old blanket string byte-for-intent ✓
- `_corrections_log` records the full chain:
  `99661246…` (v1 pin) → `97bf1ad3…` (post F-V1 partial, at 1bcf07cc) → final-state recorded in
  `freeze_pins_v2.json` (by reference, no self-hash — by design) ✓
- NO `VERIFIED_VS_ACCOUNT` claim: labels say `VERIFIED_VS_ACCOUNT = NOT_RUN … NOT inferred`;
  `does_NOT_do` includes "does not make fees VERIFIED_VS_ACCOUNT" ✓
- NO registration/GO/lifts: `does_NOT_do` = not a typed GO, not cycle registration, no S1/order/
  purchase/push, does not lift D9/PB2/PB3/D8/caps; sufficiency text explicitly says registration
  at ROOT is NOT included in current authority ✓

## X6 — Blanket-label eradication round-wide — **FAIL** (1 residual live use)

Grep of ALL round `.md`/`.json` for `FX/NYMEX-scoped` / `FX/NYMEX scoped` — 7 occurrences, classified:

| file | occurrence | class |
|---|---|---|
| auth/D3_RECORDED.json | `_superseded_sufficiency_conclusion_1bcf07cc` | ALLOWED (superseded field) |
| auth/D3_RECORDED.json | `_fv1_correction` note | ALLOWED (quotes old label, labeled correction) |
| freeze/PIN_SUPERSESSION.md | correction narrative, label in quotes | ALLOWED |
| REPORT_VI.md | corrections-log text ("đã sửa" = fixed) | ALLOWED |
| dispatch/handoff_VERIFY.json | F-V1 finding record, label in quotes | ALLOWED (historical finding) |
| dispatch/handoff_FREEZE-AUDIT.json | lane-time `readiness_conclusion` prose | ALLOWED-HISTORICAL (append-only, byte-frozen per X7; staleness explicitly disclosed in v2 + PIN_SUPERSESSION) |
| **freeze/REGISTRATION_READINESS.md (§(b), L80)** | **"The three remaining open rulings are FX/NYMEX-scoped and **non-blocking for ES**"** | **LIVE — NOT allowed** (present-tense status doc; not a quote of the superseded field; not labeled historical/superseded anywhere in the supersession chain) |

The residual: the wave's `git show --stat` (6 files) did NOT touch `freeze/REGISTRATION_READINESS.md`,
although the original F-V1 finding named REGISTRATION_READINESS as an echo location. `PIN_SUPERSESSION.md`
claims the packet header + REPORT_VI carry the precise scoping but is silent on REGISTRATION_READINESS —
a disclosure gap, not a false statement. Operative conclusion (non-blocking for ES) is unaffected and the
verbatim §4 quote immediately below the stale sentence itself states e.2's geography basis. No numeric,
pin, authority, or gate impact.

Stale-value scan `1.386|21.006|33.506|46.006`: **use-as-value = 0**. All hits are law/program/classification text:
D3 `forbidden_values_law` (names the retired values); PRELAUNCH_A7_SPEC L16 (the scan's own pattern line);
cost_freeze_check classification rows (incl. the disclosed false-positive trade price `19801.386`,
which only substring-matches); VERIFY_REPORT/verify_findings classification detail.
Out-of-round: SPEC_PB1_ES §5 L100/L104 still prints the glued values as committed history — superseded
by COST_FREEZE_ERRATUM by reference, caveated (REGISTRATION_READINESS C-2) and declared in the v2 pin role text.

## X7 — Handoff outputs ledger — **PASS**

- `dispatch/handoff_FREEZE-AUDIT.json` sha256 = `297b839fc296440f…` at **both** 1bcf07cc (git show)
  and 77a763ac (working tree) → **UNMODIFIED, append-only respected** ✓
- Its stale output pin (`outputs[2].sha256 = d6b9be83…` for cost_freeze_check.json) is documented,
  not hidden: v2 `handoff_output_pin_supersession` block + PIN_SUPERSESSION pair 2 ✓

## X8 — Cost cells + identities final re-verification — **PASS**

- 4 cost cells recomputed from components (see X5): 2.25; 21.00/33.50/46.00 — agree with
  D3 `effective_cost_table_es` and `freeze/cost_freeze_check.json` (RT 42/67/92 and window
  20.99/33.49/45.99 also recomputed) ✓
- `freeze/identity_table_24.json`: **24 identities**, composition P-A 8 + P-B 8 + FOMC 4 + C1-C4 4 ✓
- Spot-check vs SPEC_PB1_ES §6: `FBES1-FLAT` = "C3 anchor" (SPEC L129) and `FBES1-DOSE-D0-S2` =
  "C4 dose-response" (SPEC L130) — exact; `FBES1-PB1-CONT-UP-D0-S2` instantiates the SPEC §6
  P-A pattern `FBES1-PB1-{CONT,REV}-{UP,DN}-{D0,D30}-S2` (8) ✓

## X9 — Non-action proof — **PASS**

- `git show --stat 77a763ac`: exactly 6 files changed vs 1bcf07cc, ALL under
  `research/control/FUTURES-ES-PB1-REGPREP-20261004/`: REPORT_VI.md, auth/D3_RECORDED.json,
  freeze/PIN_SUPERSESSION.md (+40), freeze/freeze_pins_v2.json (+306), synth/PRELAUNCH_A7_SPEC.md,
  synth/REGISTRATION_PACKET.md. No registry/ledger/plan/other-round changes ✓
- Root registry `/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json`:
  `grep -c "FUTURES-ES-PB1"` = **0** — NO FUTURES-ES-PB1 entry ✓

## Git commands run (all read-only, recorded)

1. `git rev-parse HEAD`
2. `git status --porcelain`
3. `git show 1bcf07cc:research/control/FUTURES-ES-PB1-REGPREP-20261004/auth/D3_RECORDED.json | shasum -a 256`
4. `git show 1bcf07cc:research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/cost_freeze_check.json | shasum -a 256`
5. `git show 1bcf07cc:research/control/FUTURES-ES-PB1-REGPREP-20261004/dispatch/handoff_FREEZE-AUDIT.json | shasum -a 256`
6. `git show 1bcf07cc:research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/freeze_pins.json | shasum -a 256`
7. `git show --stat 77a763ac4c5389fb674eac287e7876ef83aba04e`
8. `git status --porcelain` (second call, AFTER writing outputs — proves the write boundary was
   respected: the only untracked path is `verify/audit_followup/` itself; no other file touched)

## Findings

| id | severity | finding |
|---|---|---|
| F-AF1 | MINOR | Residual LIVE blanket label in `freeze/REGISTRATION_READINESS.md` §(b) L80 ("The three remaining open rulings are FX/NYMEX-scoped…") — over-scopes e.2 (geography-scoped). The fix wave did not touch this file; no supersession text labels it stale. X6 therefore FAILS as specified. Operative conclusion (non-blocking for ES) unchanged; adjacent verbatim A7 §4 quote already states e.2's geography basis; no numeric/pin/authority impact. Same file L10 still cites v1 (`freeze_pins.json`) as its pin basis, now superseded by v2. Remedy is a one-line append-only correction + fresh verifier pass at the new committed SHA (per the wave's own protocol). |
| F-AF2 | NOTE | `handoff_FREEZE-AUDIT.json` retains lane-time blanket phrase and stale output pin — append-only history, byte-frozen (X7), staleness explicitly disclosed in v2 + PIN_SUPERSESSION. Allowed. |
| F-AF3 | NOTE | D3 `_corrections_log` entry 2 records the final sha by reference ("recorded in freeze_pins_v2.json") rather than literally — intentional anti-self-reference design; the literal final value `f54610eb…` lives in v2 and matches disk. |
| F-AF4 | NOTE | v2's legacy `sha256` field for D3 intentionally retains the lane-time `99661246…`; authoritative field is `sha256_v2` (34/34 verified). The delta block discloses this. |
| F-AF5 | NOTE | Out-of-round SPEC_PB1_ES §5 committed stale prints (1.386 / 21.006 / 33.506 / 46.006) remain as history — superseded by COST_FREEZE_ERRATUM by reference, caveated (C-2), declared in v2 pin role text. Not in round-dir X6 scope; classified, no action. |

## Verdict

**FAIL** — 8 of 9 checks PASS; X6 FAILs on exactly one residual live blanket label
(F-AF1). Pin stability itself is fully verified: 34/34 pins match at the committed SHA,
the supersession chain is faithful, no hash loop exists, and the round remained non-action.
