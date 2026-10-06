# A7_DATACONTRACT — independent fresh-context audit of FUTURES-DATACONTRACT-QUAL-V1 (Bước 1 closure)

- Lane **A7-DC** (independent auditor), 2026-10-03. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` @
  `b71c837d1f72d17b35475ab5e2795f6d113c1f9f` (== dispatch_sha; no commits made).
- Objects audited in full: `DATACONTRACT_QUALIFICATION.md`; `analysis/verify/**`
  (VERIFICATION_LOG, verify_results.json, 5 check scripts + 4 stdouts + 2 JSONs);
  `analysis/nq2020_remeasure/**` (ADDENDUM, JSON, script);
  `dispatch/DISPATCH.json` + the two lane handoffs (DC-VERIFY, NQ-2020-REMEASURE).
- Authority refs (read-only): all six `dossiers_v2/*.md` (errata applied),
  `analysis/ERRATA_SUMMARY.md`, `REPORT_VI_DEEPRESEARCH_V2.md`, and
  `/Users/hoangminhlong/my-quantitative/research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md`
  + `S1_IDENTITY.json` (cost/identity provenance).
- Method: every check recomputed where cheap, from raw bytes, with commands and
  results recorded below. Nothing repaired; no dossier/implementation edits.

---

## 1. Findings table

| # | severity | where | finding | evidence |
|---|---|---|---|---|
| F1 | **MINOR** | DATACONTRACT_QUALIFICATION.md §2 (NQ row) + §1.6 item 6 | Stale internal state: §2 says "re-measure đang chạy" and §1.6 says "tới khi addendum land, các số 2020 ... cờ 'recompute pending'" while §3 item 5 and §1.5 correctly record the re-measure as DONE (addendum landed 13:05; doc saved 13:06). Not a false claim about the data, but §2/§1.6 were not refreshed when the lane returned. | §2/§1.6 vs §3.5/§1.5 in the same file; handoff_NQ-2020-REMEASURE.json mtime 13:05 < doc 13:06 |
| F2 | **MINOR** | nq2020_remeasure (ADDENDUM §1 + JSON `roll_week_2020.note`) | The quoted trail5 magnitude "NQM0 trail5 357k" does not reproduce: my independent recompute of the k=5 trailing-5-session mean at close of 2020-03-19 gives NQM0(id 16908) = **428,574** (window 03-13..03-19) and 339,953 ending 03-18; the NQH0 side (**229,267**) reproduces exactly. Neither window yields 357k. The crossover DATE is confirmed (no crossover at close 03-18: NQH0 381,512 > NQM0 339,953; crossover at close 03-19: 428,574 > 229,267), so the switch decision and every downstream number are unaffected; only the quoted magnitude is mis-stated. | R5 recompute below (raw vendor bytes); JSON `roll_week_closes_1e9` matches my per-session closes/volumes 10/10 |
| F3 | **MINOR** | DATACONTRACT_QUALIFICATION.md §1.3 (6A row) | The 6A binding rule is declared "PIT k=5 volume-crossover" under a section tagged **[OBSERVED]**, but the 6A v2 dossier never measured a k=5 trailing-mean roll: its held chain was the declared calendar rule (27 rolls) and its crossover stat is a **daily total-volume** crossover (9–15 days after declared, median 11) plus an OI lead of 2–3 sessions. The k=5 parameterization for 6A is an extrapolation from 6B/6J/NQ (a defensible declared rule, but a declared rule, not an observed one). Also "OI leads 2-3 session (2023-12+)" — dossier says statistics available 2023-10+ with 12 measured rolls (first = Dec-2023), so the qualifier is defensible but should cite its basis. | 6A_DEEP_v2.md §3.1/§3.3 (no k=5 measurement); contrast 6B §3 ("trailing-5d mean") and 6J §1 (k=5 chain) |
| F4 | NOTE | §1.4 status column | `PASS_EVIDENCED` (FOMC, BoE, RBA, MOF, CoT) is not a taxon of the doc's own declared taxonomy (FACT/OBSERVED/POSTULATED/NOT_RUN/BLOCKED). Evidence IS cited at each site (so no PASS is inferred from nothing), and ECB is honestly PARTIAL — but the label embeds "PASS" in a corpus whose law says missing evidence is never PASS. Recommend relabeling as FACT/OBSERVED with the evidence pointer. | §1.4 rows; taxonomy line at doc header |
| F5 | NOTE | §1.3 6E row | "(= 1 session trước Monday last-trade)" states the typical case; the 6E dossier itself records quarterly expiries are Mondays **32/33** (the exception: Friday 2023-06-16, Juneteenth week, where Friday-of-expiry-week IS the last session). The 32/33 nuance is in the dossier but not carried into the contract line. | 6E_DEEP_v2.md §2 |
| F6 | NOTE | §1.3 cease-guard paragraph | "ERRATUM M-5/M-5b" — the 6J ledger ids are M-5 (major, 2022-09-20 artifact) and m-5 (minor, spec-vs-code timing); "M-5b" is an informal alias. Cosmetic. | 6J_DEEP_v2.md §10 ledger |
| F7 | NOTE | audit brief vs dispatch/ | Brief said "three handoff JSONs in dispatch/"; only two exist at audit time (DC-VERIFY, NQ-2020-REMEASURE) — the third is this lane's own handoff, written at closure. No artifact defect. | `ls dispatch/` |

**No BLOCKER. No MAJOR.** Every number I could trace or recompute is faithful; the
three MINOR items are stale text, one mis-quoted intermediate magnitude, and one
labeling overstatement — none changes a verdict, a gate, or a binding number.

## 2. Audit-check verdicts (per brief)

1. **CLAIM FIDELITY — PASS (with F1–F3).** Spot-recomputes, all matching:
   - Qualification matrix: all six v2-symbol rows trace to dossier sections
     (identity §1.1: NQ 111 clusters/4 strays, ES 71 contracts + Juneteenth
     2026-06-18/2027-06-17, 6E 90 = 33Q+57 serial + 0.34%, 6B 48→32 + 59 strays
     incl. GCQ4 2,139 bars, 6A 86 + 6BU5 1,584 + instr 7084, 6J 95 + 6AV3;
     session §1.2: NQ 32/32 DST, ES close history 16:30→16:15→16:00, 6J
     1,380/1,357, holiday NOT_RUN-official everywhere, 119 NQ inferred shorts,
     6J 15 holidays, 6B missing-weekdays=holidays; roll §1.3: NQ 66 rolls +
     DTE median 7 + corr 0.999, ES T-5 66/66 dev 0..−2 + OI same-day 12/12
     (2023-10+), 6E Friday 27/27 + expiry 80/80 + 0 thin <10k, 6B median 11
     after declared (9–13) + old 66–172k + thin 1,069..13,222, 6A 9–15d median
     11 + OI lead 2–3, 6J 27 rolls + OI lead 1–3 calendar days 12/12 mode 2 +
     2022-09-20 artifact; CIP descriptors 6B +0.84 Pearson, 6A 16/16 @|Δ|≥25bp,
     6E 27/27 sign but r=0.91→PIT −0.107, 6J near<far 100%). Matrix verdicts
     QUALIFIED_WITH_GAPS ×6 / NOT_QUALIFIED_V2 ×4 / NOT_RUN_DATA_ABSENT 6F are
     consistent with the evidence and the owner directive.
   - Cost table §1.7 vs FINAL_REPORT (FUTURES-DATA-10SYMS-V1): commission
     $0.85/side doc 2026-10-02 ✓; ES exchange 1.38+reg→all-in 2.24 doc, others
     NOT_FETCHED ✓; spreads 12.50/32.50/18.75/18.75/20/25 ✓ exact; slippage
     NOT_RUN_NO_DECLARED_VALUE ✓; margins 26-29k/42-46k/2.4-2.6k·2.2-2.4k/1.9-2.1k/2.7-3.0k
     ✓ exact; NQ 6.5-tick close-proxy caveat ✓; BBO NOT_RUN ✓.
   - §1.1 multipliers/minTicks vs S1_IDENTITY.json: NQ 20/0.25, ES 50/0.25,
     6E 125,000/5e-05, 6B 62,500/0.0001, 6A 100,000/5e-05, 6J 12,500,000/5e-07 —
     all ✓ exact; 6A legacy 1e-4 conflict unadjudicated ✓ (6A defects #8).
2. **TAXONOMY — PASS.** No READY anywhere; §3 explicitly "không ghi READY,
   không đăng ký cycle scored"; registration gate honestly **BLOCKED** with six
   concrete blockers (fees 5/6, slippage all, holiday NOT_RUN, ECB 45/55,
   serial IBKR re-fetch, BBO/depth). Missing evidence stays NOT_RUN (BLS/ABS/
   China, gilt 2025-26, pre-2023 OI). See F4 NOTE on the PASS_EVIDENCED label.
3. **DC-VERIFY RE-RUN — PASS.** Re-ran 5 of 8 checks from raw bytes + 2 extra
   probes; every result matches VERIFICATION_LOG/verify_results.json exactly
   (commands+results in §3 below). Recorded commands match saved scripts and
   stdouts; the saved scripts do what the log says.
4. **NQ-2020 RE-MEASURE — PASS.** (a) Old-behavior control: v2 a1 JSON +
   `NQ_cache/nq_held_daily.parquet` independently read — ret +13.2046%,
   worst −11.1487%, best +8.8488%, DD −32.28%, rvol20 max 92.4132 @03-27,
   rvol60 max 57.1281 @04-13 all match the remeasure's `v2_reference_numbers`
   digit-for-digit; my independent rebuild of the March roll-week closes/
   volumes matches the JSON's `roll_week_closes_1e9` 10/10 (corroborates the
   lane's sessionization/registry behind the 0/537 held-map-agreement claim).
   (b) Decomposition closes exactly: +13.2046 +32.6530 −7.4232 = +38.4344;
   the −7.4232 restatement also equals the sum of the two roll-day ret
   deltas (−0.2815 + −7.1417) — two independent constructions, same number;
   delta = +25.23pp ✓. (c) Worst-day-date: from BOTH the v2 cache and my raw
   recompute, worst = −11.1487% @ **2020-03-12** and 2020-03-16 = −10.4218%
   (≈−10.42%) — the addendum's correction of the dossier's "(2020-03-16)"
   label is right; new-view rets 03-19 −1.0350% / 03-20 −3.7509% reproduce
   exactly. (d) Addendum stays descriptive: no PnL, no conditional tables, no
   signals (script + prose inspected). One figure mis-stated (F2).
5. **PATH LAW — PASS.** Physical root EXISTS (76 parquet files); dotted
   av1trim alias MISSING; nonprice + IBKR raw at dotted paths EXIST — exactly
   as §1.5 PATH LAW and DC-VERIFY check 7 state.
6. **HOLIDAY/EVENT PIT TABLE — PASS.** All §1.4 entries trace: FOMC 147=132+15,
   92 timed (2016+), 85@14:00 + 7 irregular, 40 untimed 2011-15 (ES §5 +
   ERRATUM F5); ECB 55 days / 10 machine-verified / 45 assembly, PARTIAL (6E
   §6); BoE 12:00 London (3,451 vs 1,392 contracts/min), assembly disclosed,
   rate-change subset == parquet (6B §0/§2); RBA 14:30 Sydney, eff-date −1 AU
   BD, 67 meetings, as-published (6A §4.1); MOF 386 ops 1991-05-13→2026-05-06,
   ~1-month lag, no same-day signal (6J §5); CoT Tue→Fri 15:30 ET as-published
   (all dossiers); BLS/ABS/China NOT_RUN (NQ §4, 6A §4.3-4.4, 6B §9).
7. **ORDERING-LAW COMPLIANCE — PASS.** No PLAYBOOKS_DRAFT exists anywhere under
   FUTURES-DATACONTRACT-QUAL-V1 (find -iname '*playbook*' → empty); no frozen
   executable spec; §4 defers playbooks to after A7-DC with [PROVISIONAL]/
   BLOCKED posture. No blocker.
8. **HONESTY — PASS (with F3).** Inferred calendars are labeled inferred /
   NOT_RUN official; spreads labeled close-proxy with "không claim spread
   thực"; CIP labeled structural input not signal; the cease-guard is labeled
   "mới" (new declared rule) rather than measured; roll ≠ alpha law stated.
   The one overstatement is F3 (k=5 on 6A presented as observed).

## 3. Every recompute run by this audit (command + result)

Interpreter `/Users/hoangminhlong/my-quantitative/.venv/bin/python`; probe
script + JSON kept here: `a7_probe.py`, `a7_probe_r1_r2_r5.json`.

| id | what | command (essence) | result | vs claim |
|---|---|---|---|---|
| R1 | Path law | `os.path.exists` on 4 roots + `glob …parquet/*/*.parquet` | physical av1trim EXISTS (76 parquet); dotted av1trim MISSING; nonprice EXISTS; futures-10syms-v1/raw EXISTS | == DC-VERIFY check 7 / qual §1.5 |
| R2a | MOF tidy | read parquet + filter observation_period | 386 rows, 1991-05-13..2026-05-06; 2022-10-24 = 7296.0 JPY_buying; `.bak_81rows_20261003` = 81 rows | == DC-VERIFY check 1, FACT |
| R2b | CFTC fixed tidy | `hashlib.sha256` raw bytes | `f7a2719e745c2f6f89f927ddafcb96df75ed7a6e89e69b84447e2acde6362fca`; rows 15,347; bak 13,369 rows sha16 `4f9cd78944ee79dc` | == DC-VERIFY check 2, FACT |
| R3 | NQ CoT ALT loader | `NQ_deep_lib.load_cot_nq_all_lines()` filter `__ALT__…CONSOLIDATED` | 850 rows, 2010-06-15..2026-09-22 | == DC-VERIFY check 3, FACT |
| R4 | 6E venue-OI dedupe | re-ran saved `check5_6e_oi.py` (reads 2 AV1T-statistics parquets, stat_type==9, ts_ref 2024-06-04) | 18 rows = 9 contracts × 2 publications; raw sum 1,343,543; deduped 671,736 | == DC-VERIFY check 5, FACT |
| R5 | NQ 2020-03 raw recompute | own sessionization (America/Chicago, 17:00 roll-forward, break dropped) of `AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet` | per-session NQH0 + id16908 closes/volumes 03-09..03-24 match `roll_week_closes_1e9` 10/10; old-view rets: 03-12 −11.1487%, 03-13 +8.8488%, 03-16 −10.4218%, 03-19 −0.7536%, 03-20 +3.3908%; new-view 03-19 −1.0350%, 03-20 −3.7509%; trail5: NQH0@03-19 = 229,267 (matches), NQM0@03-19 = 428,574 (**not** the quoted 357k → F2); crossover fires at close 03-19, not 03-18 | remeasure claims confirmed except F2 magnitude |
| R6 | v2 cache worst-day | read `NQ_cache/nq_held_daily.parquet`, min/max 2020 rets | worst −11.1487 @2020-03-12; best +8.8488 @2020-03-13; 03-16 = −10.4218; Σret = +13.2046; n=210 | == remeasure `v2_reference_numbers` / confirms date-error finding |
| R7 | a1 reference numbers | read `NQ_a1_regimes.json` 2020 row + rvol summary | ret 13.204595984…, vol 33.543446…, worst −11.148653…, DD 32.280029…, 260 sessions / 51 depleted, rvol20 0.9241319546 @03-27, rvol60 0.5712807713 @04-13 | == digit-for-digit |
| R8 | decomposition arithmetic | python: new−old−hole vs Σ roll-day ret deltas | −7.423182 == −7.423182 (two constructions); +32.653 − 7.423 = +25.230 = 38.434 − 13.205 | == addendum/handoff |
| R9 | S1 identity | read `S1_IDENTITY.json` symbols | multipliers/minTicks: NQ 20/0.25, ES 50/0.25, 6E 125000/5e-05, 6B 62500/0.0001, 6A 100000/5e-05, 6J 12500000/5e-07 | == qual §1.1 |
| R10 | taxonomy/ordering scans | grep READY/PASS/freeze; find -iname playbook | no READY; PASS only as PASS_EVIDENCED (F4) and in negative statements; no playbook file; no frozen spec | == checks 2/7 |

## 4. Step-1 closure assessment

The qualification doc does what the owner's ordering law demands: it freezes
the construction rules that ARE evidenced (identity, session/DST, roll
timing, exclusions, reconciliation laws), keeps every un-evidenced dimension
honest (cost fees/slippage, official holidays, BBO/fills, ECB remainder,
serial IBKR re-fetch), marks the registration gate BLOCKED, and defers
playbooks. The expected PARTIAL substance (cost/holiday/fill) is exactly what
§3 declares; nothing overclaims beyond it. The errata-grade items (F1–F3)
warrant small text fixes by the Lead before Bước 2, but none re-opens Bước 1.

**STEP1_VERDICT: CLOSED_WITH_ERRATA**

Errata requested (for the Lead, non-blocking for closure):
1. F1: refresh §2 NQ row + §1.6 item 6 to "re-measure DONE (addendum)".
2. F2: correct "trail5 357k" → ~429k (or state the window) in ADDENDUM §1 /
   JSON note (JSON authoritative fields already correct).
3. F3: relabel the 6A §1.3 rule as declared/extrapolated (or measure k=5 on 6A
   before any scored cycle uses it).
4. F4 (advisory): replace PASS_EVIDENCED with FACT/OBSERVED + evidence pointer.

— End of A7_DATACONTRACT.
