# FINAL_SAFE_BLOCKER_MATRIX — FUTURES-P3-QUARANTINE-20261004 (Q6-SYNTH-VERIFY)

Safe baseline **d7fc6231** (owner-designated, pre-P3) + round FUTURES-P3-QUARANTINE-20261004
overlay (Q1 quarantine + Q5 permitted-route recoveries). Machine mirror:
`synth/final_safe_blocker_matrix.json`. Verification basis:
`verify/HANDOFF_VERIFICATION.md` + `verify/findings_final.json`.

**Law: no P3 cell raises any dimension.** Every upgrade below is NEW provenance from Q5's
own permitted captures (web.archive.org replay of official cmegroup.com endpoints, plain
curl unmodified / web_reader / WebFetch; ≤2 attempts/URL/method; zero bypass techniques —
audited by Q6 on fetch_log.jsonl, 100 records). P3's verdict
(**QUARANTINED_POLICY_BREACH**) stands regardless of Q5.

## Headline

| Dimension | State after this round |
|---|---|
| FX expiry quarters | **236/272** (6E 64, 6A 62, 6J 58, 6B 52) — baseline 208 + **Q5 +28 permitted** |
| GC expiry | baseline →Dec-2023 **+ 2025 (11/12, GCF25 absent) + 2026 12/12 permitted** (incl. GCV26 28 Oct / GCX26 25 Nov / GCZ26 29 Dec 2026); 2024 open |
| SI expiry | baseline →Dec-2022 **+ 2023 + 2024 + 2025 (dual captures) permitted**; 2026 open |
| ES 2026 times | **weekly + all deviation windows OBTAINED_PERMITTED** (cspecs_133 + svc_2026×12); ClearPort row in preserved capture, unadjudicated |
| NQ 2026 times | **weekly OBTAINED_PERMITTED** (cspecs_146); deviations NOT_OBTAINED (no archive, live blocked) |
| CL/GC 2024-25 holiday times | **19/20 windows each OBTAINED_PERMITTED** (Labor-2025 lost) |
| NG/SI 2024-25 holiday times | NOT_OBTAINED (ids 444/458 in no archived service URL — exhausted) |
| P3 cells (28) | **8 OBTAINED_PERMITTED** (#1,#3,#4,#14,#15,#16,#22,#24) + #27 partial (8/10 ids); **19 PENDING_ADJUDICATION** |
| Fees | 10/10 tier-1 UPHELD; MODELED COST; VERIFIED_VS_ACCOUNT=NOT_RUN; A7 packet READY (not run) |
| 6J cost | Q4 layers, Q6-recomputed exact: RT **$67.42 = 8.45 bp** T1/1-tick on $79,787.50; range 8.30–12.10 bp |
| BLS | PIT vintage rule standing (inference FORBIDDEN); **CPI Jan-2026 announce NOT_PINNED** (D5) |

## Per-symbol matrix (8 dimensions; only changed/decision-relevant cells annotated)

| Sym | expiry_calendar | holiday_hours | event_PIT | BBO | cost | data_rights | roll_rule | open defects |
|---|---|---|---|---|---|---|---|---|
| ES | CLOSED 68/68 | **UPG: 2026 weekly+deviations OBTAINED_PERMITTED**; P3#2 ClearPort PENDING (preserved-capture recoverable) | CLOSED-PREP | NOT_RUN | 2.24 UPHELD; **D3 $0.01 reg-basis open** | PASS | OBSERVED 61/66 | BLOCKED_TRIAL_BUDGET 36>24; SPEC §5 UNDER REVIEW |
| NQ | CLOSED 68/68 | **UPG: weekly OBTAINED_PERMITTED**; deviations NOT_OBTAINED (P3#5 PENDING) | CLOSED-PREP | NOT_RUN | 2.24 UPHELD; D3 | PARTIAL (rebuild precondition; **Q4: CLEAN-as-built + 2 obligations: ERRATUM F1 alias re-measure, k=5 cease-guard**) | BLOCKED-INFERENCE (corr 0.99908) | sibling-after-gates |
| 6E | **UPG 64/68** (Q5 +12; ECH26/ECM26 in capture unextracted) | PARTIAL | CLOSED-PREP | NOT_RUN | 2.46 UPHELD (alias-map PARTIAL, A7 e.1) | PASS | NOT_RUN | PB2 HOLD; no cap |
| 6B | unchanged 52/68 (Q5 0/12) | PARTIAL | CLOSED-PREP | NOT_RUN | 2.46 UPHELD | PASS | NOT_RUN | FX-F4 gate; PB2 HOLD |
| 6J | **UPG 58/68** (Q5 +6; **J1Z26 + 2026-2029 rows in preserved XLS, unextracted — no new fetch needed**) | PARTIAL | PARTIAL (BoJ dates, no stamps) | NOT_RUN (book 35.8% thinner, Q4) | **Q4 exact layers: $67.42 RT = 8.45bp; tier 8.30-12.10bp; MODELED/UNDER REVIEW** | PASS | NOT_RUN | SECONDARY gates; BoJ stamps = owner |
| 6A | **UPG 62/68** (Q5 +10; **ADZ26 + 2027-28 rows in preserved capture, unextracted**) | PARTIAL | CLOSED-PREP | NOT_RUN | 2.46 UPHELD | PASS | BLOCKED (k=5 extrapolation; cease-guard law) | PB3 PARK; K0 kill |
| CL | CLOSED (rule+183mo) | **UPG: 2024 10/10 + 2025 9/20 permitted**; Labor-2025 open | PARTIAL (WPSR; naive freeze) | NOT_RUN_DATA_ABSENT (0 comm O1M) | 2.36 UPHELD | NOT_QUALIFIED_V2 | PARTIAL | no registration path |
| NG | CLOSED (rule+240mo) | unchanged; 2024-25 open (id 444 unreachable) | PARTIAL (r-1 unsigned) | NOT_RUN_DATA_ABSENT | 2.46 UPHELD | NOT_QUALIFIED_V2 | PARTIAL | **D7 signed-surprise rule** |
| GC | **UPG: 2025 11/12 + 2026 12/12 permitted**; 2024 open | **UPG: 2024 10/10 + 2025 9/20 permitted** | PARTIAL | NOT_RUN_DATA_ABSENT | 2.51 UPHELD (epoch windows = A7 e.3) | NOT_QUALIFIED_V2 | PARTIAL | owner data decision |
| SI | **UPG: 2023 + 2024 + 2025 permitted** (2025 dual); 2026 open | unchanged; 2024-25 open (id 458 unreachable) | PARTIAL | NOT_RUN_DATA_ABSENT | 2.51 UPHELD | NOT_QUALIFIED_V2 | PARTIAL | depth ≥2y |
| 6F | NOT_RUN_DATA_ABSENT (all dims; standing) | | | | | | | unchanged |

## The 28 P3 cells — final disposition

- **OBTAINED_PERMITTED (new provenance, Q5):** #1 ES weekly; #3 ES deviations (11 windows
  vs P3's 12 dated entries — same calendar, different grouping, zero conflicts); #4 NQ
  weekly; #14/#15/#16 GCV26/GCX26/GCZ26 (values == P3 claims — content corroboration
  only); #22 CL 2025 T/Xmas times; #24 GC 2025 T/Xmas times; #27 product-id map (8/10;
  NG 444 unreachable).
- **NOT_OBTAINED/PENDING_ADJUDICATION (19):** #2 (ClearPort; preserved-capture
  recoverable), #5 (NQ deviations), #6–#13 (FX Dec-2026 + 2027-2031 supersets; **J1Z26 /
  ADZ26 / ECH26 / ECM26 and 2027-2029 chains sit inside preserved Q5 captures, dated
  values not yet extracted under any lane's authority — extraction needs no new fetch and
  no P3 data**), #17 (GC superset GCM32), #18–#21 (SI 2026 + superset), #23 (NG), #25
  (SI), #26 (ESZ26/NQZ26 — likely moot: baseline already CLOSED 68/68 through Dec-2026),
  #28 (widget window list).

## Cross-lane law (restated)

Q5's provenance is its own captures; **it does not un-quarantine P3**. Value-agreement
between Q5 and quarantined-P3 claims, where it exists (ES weekly string; GC 2026 Q4
dates; id map), is recorded as corroborating P3's CONTENT authenticity only — never
transport compliance. Owner adjudication of P3 transport (D1) remains open either way;
Q5's independent recovery makes most P3 cells moot for coverage purposes.

## Standing rulings — all unchanged

NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER; PB2 HOLD; PB3 PARK; 6F NOT_RUN_DATA_ABSENT;
ES 24 identities frozen (headroom 0); NQ sibling-after-cost/clock-gate; CL/NG/GC/SI
PROVISIONAL-only; all fees MODELED COST / VERIFIED_VS_ACCOUNT=NOT_RUN, UNDER REVIEW until
new A7; BLS PIT vintage law in force. No new trial families, no rankings, no scoring.

— End FINAL_SAFE_BLOCKER_MATRIX.md.
