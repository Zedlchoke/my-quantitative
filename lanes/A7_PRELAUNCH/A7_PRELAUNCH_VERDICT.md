# A7 PRELAUNCH VERDICT — WNBA-PLAYERFEAT-SCORED-V1 · lane A7_PRELAUNCH · INDEPENDENT AUDITOR

Date of record: 2026-10-05 · auditor: fresh-context independent agent · never repaired, recomputed
from bytes · interpreter `/Users/hoangminhlong/my-quantitative/.venv/bin/python` (only) · git
READ-ONLY · audited HEAD `12e05508de30de61da3825b10a6df8a87291f796` on
`orca/wnba-playerfeat-scored-v1-integration`.

## VERDICT: A7_PRELAUNCH_PASS — 9/9 checks PASS, 0 blockers.

The one owner action unlocked by this verdict: **run the 2-arm B0-vs-B1-WNBA walk-forward OOS
evaluation on the frozen window [2020..2026], post-GO, exactly as frozen** (see
OWNER_GATE_BRIEF.md). GO itself remains owner-only, typed verbatim at this cycle's own gate.

## Per-check table

| # | check | verdict | decisive evidence (recomputed independently where numeric) |
|---|---|---|---|
| A7-1 | SHA chain linear + clean tree | PASS | HEAD == dispatch SHA `12e05508…`; single-parent chain `03cc27f7 → 8130de5a → 34d8c267 → 5a1d0618 → 12e05508` (T_SELECT = work `34d8c267` + control event `5a1d0618`); merge-base ancestor checks OK; tree clean except the untracked dispatch packet itself |
| A7-2 | Own-code B1-WNBA recompute | PASS | auditor-fresh engine (no `arms`/`harness` import): B0 `0.6037546933667084` exact; **27/27 grid points match ledger, max |ΔLL| = 2.22e-16**; winner K=32/HCA=50/γ=0.65 pooled validation LL `0.623497720316443` vs frozen `0.6234977203164429` (≈1e-15 ≪ 1e-9, 1774 games); kill-test ΔLL `-0.054386188557277` exact, own bootstrap CI `[-0.070150, -0.038275]` == recorded, entirely < 0; named spots K=16/HCA=100/γ=0.75, K=8/HCA=0/γ=0.85, K=32/HCA=0/γ=0.65 all ≤ 1.1e-16; persisted frozen stream = exactly the 3995 ≤2018 games, max |Δp| 1.665e-15 (last-ulp implementation-order rounding only) |
| A7-3 | Designed null byte-identity | PASS | real data (own engine): φ=0 (standardized x path) and c≡1 both float64-hex identical to parent on all 5,017 corpus games; own synthetic stream (90 games, same-tip batches, neutral rows): φ=0 / c≡1 / both identical, negative control (φ=25, alternating x) correctly breaks identity; corroborates ledger `DESIGNED_NULL_REAL_DATA designed_null_ok=true` and selftest canary |
| A7-4 | Cap / OOS lock | PASS | `SEASON_MAX_REAL=2018` code-read (harness.py:32) + filter-at-read; doctored-2019 probe → `CapViolation` loud (control {2002,2018} passes); frozen selftest **14/14 PASS exit 0**; `evaluate-oos --source real` refused `OOS-GATE-REFUSED` with an audit hook observing **0 real-data fs events at refusal time** (pre-read); fabricated lowercase token and path-as-token both refused; synthetic control allowed pre-gate; exact-phrase path (gate check only, execution still refuses POST-GO) verified by code-read — this audit never typed the registered phrase |
| A7-5 | Ledger completeness | PASS | 49 rows = 38 scored fits (27 grid + WF-A 1 + WF-B 5 + WF-C 5) + 11 bookkeeping; all rows mode=select, season_cap=2018, seed=20261005; grid == dispatch constants K{8,16,32}×HCA{0,50,100}×γ{0.65,0.75,0.85}; ledger sha256 `603aa412…fde58df` == the deterministic-rerun claim in handoff_T_SELECT; all 7 handoff output shas match bytes on disk |
| A7-6 | S_SYNTH dry-run evidence | PASS | sandbox verified from bytes: `diff -r rehearsal_run1 rehearsal_run2` byte-identical; rehearsal.json sha `51a513b7…` equal both runs == recorded; probe_results.json sha `d70f2b91…` == recorded; hand-fixture checks all ok at tol 1e-12 in rehearsal.json and auditor independently re-derived fixture game 1 (p 0.5714631174084 / LL 0.5595553342981 / Brier 0.1836438597413 — exact); dryrun.py asserts frozen T_SELECT shas and refuses drift; synthetic-only (SYNTH_ ids, seasons 2027–2030) |
| A7-7 | Honesty | PASS | WF-A `MACHINERY_SUSPECT` recorded in ledger + both verdict tables (twin ΔLL −0.000968 beats OWN parent; parent real-data fold slope 0.9047 INSIDE [0.85,1.15] → exemption correctly NOT applied; arm UN-SCORED, machinery audit owed); WF-B/WF-C RELEASE justified — auditor recomputed all 10 per-φ fold LLs: φ=0 strictly minimal in both arms, φ=0 ≡ parent by byte identity; warm-up 1997–2001 (1,022 rows) stream-only (code-read + frozen stream set-equality + selftest check) |
| A7-8 | Boundaries | PASS | budget 0/9 in control state AND registry; no 2019–2026 token anywhere in ledger (only float-substring/seed coincidences — inspected), persisted parquet exactly ≤2018, S_SYNTH sandbox SYNTH_-only; registry `go_phrase_state: REGISTERED_NOT_CONSUMED`, control state "GO phrase registered NOT typed", event log "GO not typed"; branch has no upstream, 0 matching heads on origin, 50 local commits ahead of origin/main — nothing pushed, no merge |
| A7-9 | Freeze completeness for post-GO read | PASS | 2 fielded arms frozen (B0 0.603755 train rate; packet law carries per-fold B0 refit on OOS; B1-WNBA K=32/HCA=50/γ=0.65 with 1997–2001 warm-up); released slots WF-B/WF-C; WF-A un-scored; OOS window [2020..2026] frozen in plan (completed seasons only; 2026 in-progress excluded); metrics frozen (LL primary, Brier/reliability/slope band [0.85,1.15], paired tip-date-cluster bootstrap 10,000 resamples seed 20261005); B1 falsifier frozen (REJECT iff pooled 95% paired CI of ΔLL includes 0 OR ≥ half season folds non-negative); neutral law HCA=0 + separate report; single-batch OOS law stated (one computation per arm); standardization moments verified NOT applicable downstream (no φ admitted) — post-GO read is exactly the 2-arm path S_SYNTH rehearsed |

## Blockers

None.

## Non-blocking observations (recorded, no action required this round)

1. INFO — SELECTION_REPORT §1 wording "2019–2026 rows never entered memory" is imprecise:
   `pd.read_parquet` materializes all 11,976 rows before the ≤2018 filter drops them. The
   material invariant (no OOS season used in any computation; cap asserted at read) holds —
   verified by code-read and by this audit's own ≤2018-only recompute.
2. INFO — independent-implementation float agreement: auditor's engine vs persisted frozen
   stream is 1,089/3,995 bit-identical with max |Δp| = 1.665e-15 on the remainder (operation
   order rounding); all 27 pooled LLs agree to ≤ 2.22e-16. No discrepancy of substance.
3. INFO — stray empty directory `lanes/T_SELECT lanes/` (disclosed in handoff_T_SELECT) still
   present; outside A7 write scope, left untouched.
4. INFO — the audit's own synthetic negative control initially used a constant x on both sides
   (feature term cancels) and was fixed to alternating x before any conclusion was drawn;
   disclosed in the handoff incidents.

## What this verdict does NOT do

Does not type GO; does not run, authorize-by-itself, or schedule any scored computation; does
not modify any audited byte. GO consumption is owner-only at this cycle's own gate, post-A7.
