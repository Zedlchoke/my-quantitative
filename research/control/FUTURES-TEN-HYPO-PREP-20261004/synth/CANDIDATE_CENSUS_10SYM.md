# CANDIDATE_CENSUS_10SYM — FUTURES-TEN-HYPO-PREP-20261004 synthesis (controller)

- Round: **FUTURES-TEN-HYPO-PREP-20261004**, thread "multi-symbol futures
  hypothesis search (PREP, outcome-blind)". Controller synthesis over 6
  returned lanes (ESNQ / FXEB / FXJA / COMM-EN / COMM-ME / CROSS) at wave-1
  commit `b7f274a4` on branch `prep/futures-ten-hypo-20261004`, base
  `a4a88265` (verified 7/7 by round-2 VERIFY-R2).
- **Outcome-blind: NO return statistic entered any cell. 0 PnL, 0 scored
  runs, 0 registrations, 0 trial identities created.** NO_GO_REGISTER /
  NO_GO_SCORE / NO_GO_ORDER stand; D1-D12 all open; nothing self-ratified.
- Classification vocabulary: **NEW** (this round proposes the family) /
  **CARRIED** (existing family re-statused, specs unchanged) /
  **DUPLICATE-VETO** (rejected: rename/variant of dead or existing class,
  cite row) / **DATA-BLOCKED** (viable mechanism, data absent; dossier +
  data requirements) / **CONSTRUCTION-ONLY** (T5-class rule, 0 alpha IDs).

## 1. Round result in one line

**5 NEW families proposed (1 on O1M symbols; 4 commodity DATA-BLOCKED
dossiers), 31 carried entries re-statused, 1 construction-only pair, and
~62 candidate adjudications of which ~35 died on cited walls** — the
search favored quality over quantity exactly as directed: both FX lanes
and FXJA returned honest zeros rather than force families past the dead
FX-spot session corpus.

## 2. The 10-symbol candidate census (master table)

Legend: D1-D5 = provisional package score 0-15 (RANKING_FRAMEWORK anchors;
outcome-blind). Sched = schedulability flag, SEPARATE from package score.
Census = trial identities this round ADDS to the hypothetical census
(full/minimal, census conventions per lane; nothing registered).

| Sym | Family (id) | Class | D1-D5 | Sched | Census add | One-line basis (artifact) |
|---|---|---|---|---|---|---|
| ES+NQ | **ESNQ-F5 EXPWITCH** quarterly expiration-Friday forced-hedging conditioning | NEW | 2/2/2/3/2 = **11** | ES leg **BLOCKED_TRIAL_BUDGET at birth** (cap 24 FROZEN, D4); NQ leg GATED (A7/D2, calendar-2026, D9, owner NQ ceiling) | +12 full / +7 minimal per leg (14 both legs) | es_nq/HYPOTHESES_ESNQ_R3.md §2; expirations FACT-grade in-repo 68/68 + verbatim termination rule texts (nq_cal_coverage.json); MDE 23.6bp ES / 38.7bp NQ vs RT(S2) — power-marginal, disclosed |
| ES | PB1 OVN pair + ES-F1..F4 | CARRIED ×5 | 11/11/11/11/10 (FINAL_RANKING) | CAP_BLOCKED (36>24) | 0 | es_nq/CARRIED_STATUS.md |
| NQ | NQ-F1..F4 | CARRIED ×4 | 11/11/10/9 | GATED (cost A7, calendar-2026, rebuild, D9) | 0 | NQ-F3 rebuild precondition executable on cache_v3 (R2 §4.2 carried) |
| 6E/6B | FX-F1..F6 + RMM legs | CARRIED ×7 | 12..8 (FINAL_RANKING + R2) | PB_HOLD (F1) / GATED others | 0 | fx_eb/CARRIED_STATUS.md; honest 0 NEW, 12 adjudicated |
| 6E/6B | C-02 SETTLE-ANCHOR (final-settlement fixing anchor) | CONSTRUCTION-ONLY | n/a | CONSTRUCTION_ONLY (0 IDs) | 0 | fx_eb/HYPOTHESES_FXEB_R3.md; DC §1.3 |
| 6E/6B | C-08 GILT-AUCT, C-11 OPT-EXPIRY | DATA-BLOCKED (candidate-grade) | 6 (C-08) | DATA_BLOCKED | 0 (dossier only) | fx_eb dossier; DMO auction calendar NOT in corpus |
| 6J | JF1..JF3 + RMM legs | CARRIED ×4 | 11/11/9/11 | GATED (orientation, BBO, cost A7, 6J ceiling) | 0 | fx_ja/CARRIED_STATUS.md |
| 6A | AF1..AF3 + AF4 + RMM legs | CARRIED ×5 | 10/8/11/10/11 | PB_PARK (all 6A contingency-only) | 0 | PB3 PARK never reopened |
| 6J/6A | AU-REL, CN-REL (AU/China data windows) | DATA-BLOCKED (candidate-grade) | n/a (ABS/China calendars NOT_RUN) | DATA_BLOCKED | 0 | fx_ja dossier |
| CL | **CL-F3 OPEC-DEC-FLOW** supply-policy decision flow | NEW (DATA-BLOCKED) | 1/2/2/2/1 = **8** | DATA_BLOCKED — NOT_RUN_DATA_ABSENT | +24 full / +11 minimal (hypothetical) | comm_energy/HYPOTHESES_COMM_EN_R3.md; opec.org dated JMMC items (200 verified) + captures |
| CL+NG | **CLNG-F4 STEO-REV** monthly EIA forecast-revision flow | NEW (DATA-BLOCKED) | 1/2/2/2/1 = **8** | DATA_BLOCKED | +48 full / +22 minimal (hypothetical, both legs) | EIA STEO embargo stamps captured; archives 403 → completeness NOT_RUN |
| NG | NG-F1/F2 + NG-F3 law | CARRIED ×3 | 10/8 | DATA_BLOCKED | 0 | **Material update: EIA dnav NG futures page kills futures after 2024-04-05** — baseline free NG price-extension path dead |
| CL | CL-F1/F2 + cost-law | CARRIED ×3 | 9/9 | DATA_BLOCKED | 0 | CPC issuance law closed verbatim ("issued daily between 3pm & 4pm ET") |
| GC+SI | **R3-F1 COT-CROWD** CFTC managed-money extremes | NEW (DATA-BLOCKED) | 1/3/2/2/1 = **9** | DATA_BLOCKED | +24 full / +11 minimal (hypothetical) | comm_metal dossier; CFTC Friday-15:30 clock + money-manager definition captured verbatim |
| GC+SI | **R3-F2 VAULT-FLOW** COMEX registered-vault stock flow | NEW (DATA-BLOCKED, construction-adjacent) | 1/2/2/2/1 = **8** | DATA_BLOCKED + K6 boundary | +12 full / +7 minimal (hypothetical) | series NOT_OBTAINED (CME 403; archive JS-shell); GC-F2 T5 precedent |
| GC | GC-F1/F2 | CARRIED ×2 | 10/9→ | DATA_BLOCKED | 0 | GC .995 fineness flagged UNVERIFIED-PREMISE (not in any captured spec) |
| SI | SI-F1/F2 + SI-F3 law | CARRIED ×3 | 10/10 | DATA_BLOCKED | 0 | SI per-side tier update 83.76/108.76/133.76 declared alongside 4-tick base |
| 6F | — | (standing) NOT_RUN_DATA_ABSENT | n/a | n/a | 0 | not in scope; no data assumed |

## 3. Candidate adjudication ledger (every candidate this round touched)

| Lane | Adjudicated | NEW | CARRIED rows | DUPLICATE-VETO / VETO | DATA-BLOCKED | CONSTRUCTION-ONLY | Subsumed / out-of-law |
|---|---|---|---|---|---|---|---|
| ESNQ | 27 | 1 (EXPWITCH) | 9 | 17 vetoes (named walls: XSECT-VOLSHK, TOM-SETTLE SFV3-A6, CNG1 precedents, PB1 anti-multi-trial, ES-F3 class, MOC/earnings/basis data-absent...) | — | 1 (close-era natural experiment) | — |
| FXEB | 12 | 0 (honest zero) | 7 | 7 (fix-certainty twice-dead TRACKA2-P4A-FIXCERT-01 + DTPFX1-A1-MEFIX-VARIANT; UK/euro releases vs dead own-economy classes FXFV6/FXNG4; ECB accounts power; lead-lag FXFV7-A6-P2; round-levels) | 2 (gilt auctions, options-expiry) | 1 (settle-anchor) | 2 |
| FXJA | 16 | 0 (honest zero) | 8 | 9 (FYJ-SEAS calendar-flow dead ×5; JGB-AUCT; JP-0850; TOKYO-FIX dead ×2; OPXE; GLOBEX-OPEN; + AF1-MIN/JGB-BOJ-OPS/YIELD-CND dup) | 2 (AU-REL, CN-REL) | — | 5 |
| COMM-EN | 8 | 2 | 6 | 6 (incl. COT ancestry veto COMMNG1-A4-P2 ×3 measured-closed) | 2 (the NEW are DATA-BLOCKED) | — | — |
| COMM-ME | 7 | 2 | 6 | 5 (LBMA fix-window dead-class + licence wall; central-bank flows PIT; GC/SI ratio MR dead DT100-75/79; DXY overlay PIT; options data-absent) | 2 (the NEW are DATA-BLOCKED) | — | — |
| CROSS | 0 (infra) | 0 | 31 (matrix) | court infra: 173 rows → 16 clusters × 10 rejection modes | — | — | — |
| **Total** | **~62** | **5** | **31 + candidate rows** | **~35 veto-wall deaths** | **8 DATA-BLOCKED entries** | **2** | **7** |

## 4. Hypothetical census delta (fills CROSS CENSUS_DELTA's empty column)

Nothing below is registered; arithmetic only, mixed conventions NOT summed
across lane conventions (CENSUS_FINAL §4/§5 law):

| Symbol group | Standing census (before) | This round adds (hypothetical) | New standing |
|---|---|---|---|
| ES | 36 minimal vs 24 FROZEN (headroom 0) | +7 (EXPWITCH ES leg) — born BLOCKED | 43 hypothetical > 24 |
| NQ | 36 minimal CTG | +7 (EXPWITCH NQ leg) | 43 hypothetical CTG |
| 6E/6B | ≈648 program-hypothetical (+8 RMM = 656) | 0 | 656 uncapped |
| 6J | ≈29-36 minimal (+4 RMM surface) | 0 | ≈33-40 |
| 6A | PB3 PARK 0 (+4 contingency) | 0 | 0 (+4 contingency) |
| CL/NG | 54 COMM minimal | +11 (CL-F3) +11 (CLNG-F4 CL leg) +11 (CLNG-F4 NG leg) = +33 | 87 hypothetical |
| GC/SI | (inside the 54) | +11 (COT-CROWD) +7 (VAULT-FLOW) = +18 | 72 hypothetical |
| **COMM total** | **54 minimal** | **+51** | **105 hypothetical > 24 ⇒ BLOCKED_TRIAL_BUDGET on any single-cycle attempt; no registration path until owner data decision** |

## 5. Ancestry-court novelty verdicts (consolidated; court infra = cross/ANCESTRY_COURT_INFRA.md)

- **ESNQ-F5 EXPWITCH: NO VETO** — nearest dead rows are calendar-flow and
  roll-window classes; the family's conditioner is the exchange-published
  expiration calendar itself (68/68 in-repo, dual captures), the actor is
  options/pin-hedging forced by termination mechanics, and no prior scored
  equity-index-futures ancestor exists in any dead list (NQ addendum §10
  re-scanned). D2 capped at 2 conservatively (CNG1-A5-P2 nearest-name +
  options-side capture BLOCKED_TRANSPORT).
- **CL-F3 / CLNG-F4 / R3-F1 / R3-F2: NO VETO, all DATA-BLOCKED** — each
  passed the court §b distinguishability test with captured primary clocks
  (opec.org item dates; EIA STEO embargo stamps; CFTC Friday-15:30 ET +
  Code as-of rows; vault-series NOT_OBTAINED declared). The commodities COT
  class is measured-closed by COMMNG1-A4-P2 ×3 — R3-F1 survives ONLY as a
  DATA-BLOCKED dossier with that precedent cited as its K7-style risk.
- **The dominant kill pattern this round**: FX candidate space is
  effectively mined out — 7 of FXEB's 12 candidates died on twice-dead or
  own-economy classes; FXJA's calendar-flow space died on 5 independent
  dead rows. This is evidence the dead-corpus veto machine works, not
  evidence the symbols lack structure.

## 6. NOT_RUN / NOT_OBTAINED / BLOCKED_TRANSPORT register (round-level)

1. ESNQ lane fetches: 5 attempts, ALL BLOCKED_TRANSPORT (0 bytes, 0
   captures) — web.archive.org routes exhausted for the probed URLs; no
   bypass attempted. EXPWITCH's load-bearing evidence is in-repo
   (FACT-grade calendar captures committed in prior rounds).
2. CME-hosted content (specs, vault reports): CME_BLOCKED_TRANSPORT
   everywhere (403); archive.org JS-shells recorded (comm_metal). GC
   .995 fineness therefore UNVERIFIED-PREMISE.
3. EIA STEO archive completeness: NOT_RUN (403).
4. BoJ intraday stamps / ABS / China calendars: inherited NOT_RUN,
   unchanged; AU-REL, CN-REL stay DATA-BLOCKED.
5. LBMA underlying licence wall: captured; any LBMA-anchored scored use
   would need an owner rights ruling (D11-adjacent).
6. Fee A7: NOT_RUN (D2 open) — every cost number in every dossier remains
   MODELED / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN.
7. BBO: NOT_RUN all 10 symbols (conservative fill law binds every
   [PROVISIONAL] entry/exit spec).

— End CANDIDATE_CENSUS_10SYM.md. Outcome-blind; every number traces to a
lane artifact cited above; nothing registered, scheduled, or scored.
