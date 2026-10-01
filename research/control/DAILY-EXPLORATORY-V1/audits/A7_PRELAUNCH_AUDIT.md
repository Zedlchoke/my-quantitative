# A7_PRELAUNCH_AUDIT — DAILY-EXPLORATORY-V1 (2026-10-01)

Auditor: A7 PRELAUNCH, fresh context, independent, read-only (audit
artifacts only; no repairs, no git operations, no network, no engine
edits). Everything below was re-measured by this auditor on disk unless
marked "reported-only". Audited state: ROOT `main` @
`dfae4fb807e0a23e5d6aabce9b2154d1784540c4`; worktree
`.worktrees/pc12a-daily-exploratory-prep` @
`2f7bc8325a1f65ae5beceffae6faae5dddf7f419` (branch
`orca/pc12a-daily-exploratory-prep`, clean). This audit executes gate
G12 (post-registration prelaunch) of the registered plan.

---

## A7_PRELAUNCH_VERDICT: **AUTHORIZED_WITH_FINDINGS**

Severity counts: **CRITICAL 0 · HIGH 0 · MEDIUM 2 · LOW 3 · INFO 2**.
No CRITICAL/HIGH finding remains; under the two-key law (P-8) nothing
here blocks the owner's scored GO key. Both MEDIUM findings are binding
conditions to discharge (execute + log) **before the first exploratory
battery run writes its first journal row** — they are execution-time
reconciliation duties, not registration-lawfulness defects. Findings
F1–F7 in §VERDICT below.

---

## 1. AUTHORITY CHAIN — PASS

- **Owner election verbatim recorded (3 independent places).**
  "ĐI TIẾP KHÔNG CÓ SAO KÊ": `PLAN_DAILY_SUCCESSOR_DRAFT.md:597` (§7
  gate text); `plans/CYCLE_REGISTRY.json` `write_token`
  `register:DAILY-EXPLORATORY-V1:Owner election 2026-10-01 verbatim 'ĐI
  TIẾP KHÔNG CÓ SAO KÊ'`; `plans/CYCLE_REGISTRY.events.jsonl` line 1194
  (`CYCLE_REGISTERED` reason field quotes it verbatim); and the worktree
  FREEZE.md header (line 3).
- **Registration lawful.** `CYCLE_REGISTRY.events.jsonl:1193`
  (`REGISTRY_SAVED`, writer + token + content_sha256 `01f411bd…` +
  projection_sha256 `792f230a…`) followed by `:1194`
  (`CYCLE_REGISTERED`) at 2026-10-01T08:12:41Z — the researchctl
  registry write path; `plans/ACTIVE_CYCLES.json` regenerated
  deterministically (`generated_from_registry_updated_at_utc` matches
  the registry `updated_at_utc`) and carries the identical row.
  Registration commit `dfae4fb8` (root main) touches ONLY registry
  files + the plan.
- **Registry row == measured reality.** Row: lifecycle ACTIVE_LIGHT,
  phase REGISTERED, head `2f7bc8325a1f65ae5beceffae6faae5dddf7f419`,
  branch `orca/pc12a-daily-exploratory-prep`, worktree path exact —
  all four re-measured on the live worktree and match exactly. Budget
  used 0 / max 10; `s0 OPEN`, `s1 SEALED_UNTOUCHED`; workers 0;
  heavy lock inspected: `FREE_PROVEN` (no `NOT_RUN_RESOURCE_CONFLICT`).
- **GO phrase registered-not-consumed; no prior consumption.** "GO
  DAILY EXPLORATORY V1 SCORED EXECUTION" occurs exactly once in the
  repo (registry row, `go_phrase_state REGISTERED_NOT_CONSUMED`).
  Events file ends at line 1194 — no write after registration, no
  consumption event anywhere (grep over `research/` + `plans/`).
- **One Lead session (P-17).** One `REGISTRY_SAVED` + one
  `CYCLE_REGISTERED` pair, single writer token, single timestamp; work
  tree commits `09fb1b74` (14:55) → `2f7bc832` (14:56) then root
  registration `dfae4fb8` (15:13) form one linear chain; no competing
  registry writes.
- The elected path is the recorded OI-2 option (c):
  `successor/OI_DECISIONS_APPLIED.md` §OI-2(c) — "run EXPLORATORY-only
  under declared costs, with no after-cost PASS possible (current law,
  unchanged)". (Note: OI_DECISIONS_APPLIED.md lives at
  `successor/OI_DECISIONS_APPLIED.md`, one level above
  `daily_successor/` — the plan binds it as `../OI_DECISIONS_APPLIED.md`
  at line 15; path note only, not a defect.)

## 2. EXPLORATORY-ONLY LAW — PASS (residuals F4/F5, all defused)

Question: can ANY future reader treat the 2020–2026 battery output as a
PASS/edge claim? **No — the law reads in four independent layers, each
re-read; every "PASS" in the package is an input/identity-gate verdict,
never a battery verdict:**

1. **PLAN §4 scope law (binding):** "every bar in this section reads
   ONLY on the prospective surface (≥6×26w of post-registration
   accumulated daily bars; earliest honest evaluation ≈ 2029-09 …) The
   §2 2020–2026 battery (folds 1–8) is EXPLORATORY reporting at most —
   no PASS, no GO, no after-cost claim is readable from it; 'pooled
   over folds 1–8' below means exploratory reporting only."
   Reinforced at §0b ¶4 (calendar-exposure honesty, "PASS bars apply
   ONLY on the prospective surface; the 2020–2026 battery may run as
   EXPLORATORY evidence at most") and §2 ("All folds in this section
   are EXPLORATORY per §0b ¶4").
2. **§7 carve-out (skeptic F1, discharged — diff-verified
   541fc223→dfae4fb8):** the registration gate now reads "…or, where
   the owner has elected the EXPLORATORY-ONLY amendment — owner
   election 2026-10-01 verbatim 'ĐI TIẾP KHÔNG CÓ SAO KÊ' — G1/G2 are
   waived for that amendment's registration: the cycle registers as
   exploratory-only with DECLARED costs, NO after-cost PASS ever, and
   the PASS bars scoped to the prospective surface only", and item 1
   now reads "OI-2 LANDS (or the exploratory-only election stands in
   its place)".
3. **DRAFT_AMENDMENT_EXPLORATORY_ONLY.md:** "No scored GO is requested
   or implied … the PASS bars DO NOT READ on this battery"; "No
   after-cost PASS, ever, under this amendment"; budget "consumed as
   EXPLORATORY ledger rows only". (Its status line is now stale — see
   F5.)
4. **FREEZE.md header (worktree):** "no after-cost PASS ever; PnL
   published only as exploratory under frozen ×1.0/1.5/2.0 stress; no
   edge claim from the 2020–2026 exposed folds; validation surface =
   post-registration prospective accumulation only."
5. **Mechanical layer (strongest):** the G9 journal writer enforces the
   RGC-INC-1 leak law at write time on every row (forbidden key
   vocabulary incl. nested, counter-tested). **This auditor's own
   poison key** (`net_pnl_after_costs`) **was REJECTED by the writer**
   (LeakLawViolation path exercised); grep of all engine outputs under
   this auditor's own extended vocabulary (incl. `alpha`, `edge`,
   `score`): clean. A journal row that looks like a score cannot be
   written.

G3/G4/G5 file "PASS" usages re-read one-by-one: all are VIX-span,
σ-tripwire, and spread-derivation verdicts on inputs — none reads on
strategy output. `G6_ADJUDICATION.md` §2.1: "No PASS is at stake … the
2020–2026 battery is EXPLORATORY; PASS bars read only on the
prospective surface." No file anywhere in the package claims
validation, edge, or survival from the 2020–2026 folds.

Residuals (dated session artifacts, documented as superseded, must not
be cited as current gate state): see F5.

## 3. FREEZE INTEGRITY — PASS (findings F1, F2, F7)

`research/control/DAILY-EXPLORATORY-V1/FREEZE.md` (worktree commit
`2f7bc832`) checked item-by-item against the frozen artifacts:

| FREEZE item | Traced to | Re-verified by auditor |
|---|---|---|
| OI-1 labels (`LAG_DECLARED_BY_OWNER`, closed bars next business day) | PLAN §0 OI-1 row; journal.py `_check_pit_snapshot` enforces next-business-day at write time | PASS (code read + my Fri→Sat rejection test) |
| σ tripwire 1σ/5σ/0.5σ, NZD 64.64 / CHF 49.62 / XAU 112.18 bps, never loosened | G3_G4_VIX_SIGMA.md (64.6388 / 49.6150 / 112.1838; tripwire table lines 230–295) | PASS (rounding consistent; "never loosened" language present in PLAN §0, FREEZE item 1, G3_G4 header) |
| G5 band table "D1BAND-* per G5_G6 file" | G5_G6 §1.8 ↔ costkernel.py `D1BAND_TABLE` hardcoded verbatim (spot-verified cell-for-cell, e.g. `D1BAND-NZDUSD-O-FOLDS` 2.6118/21.3272/32.7445/414.6256 n=1031; sha pins in `BAND_AGGREGATE_SHA256`) | PASS |
| G6: 16/16 sha, 66/66 weekdays, forming bar excluded, FAIL stands, adjudicated (b), HMDS-D1-CLOSE-ENVELOPE@1, venue seam p50 0.35 | g6_pull MANIFEST/VERIFICATION + G6_ADJUDICATION.md | PASS (fully re-measured, §5 below) |
| G9 engine commit `09fb1b74`, 13/13 tests, leak-clean, synthetic-only | worktree `git diff 09fb1b74..2f7bc832` = FREEZE.md only — engine bytes at HEAD are exactly 09fb1b74's | PASS (engine sha IS named in the freeze, item 4) |
| Slate DS-03 + DS-05, 5 parked (owner law §0b ¶1) | PLAN §0b ¶1 + G7 table | PASS (but see F1 on the row cap) |
| Budget ≤10 identities / ≤83 rows | PLAN §3 rescope | MISMATCH possible — F1 (identities reconcile; rows ambiguous 83 vs 91) |
| Calendar EXPLORATORY 8×26w 2020-10-02→2026-09-24, prospective post-registration, S1 SEALED, PC12A folds never relabeled | PLAN §2 | PASS (arithmetic reproduces exactly, §6 below) |
| DECLARED-cost labels (commission/swap/slippage/spread DECLARED or NOT_RUN, never MEASURED) | PLAN §5, costkernel constants (U2 0.35 bps, U3 0.2/1.0 pip, U4/U5 1 pip Wed×3), OI-2 | PASS |

Every frozen item traces to a committed artifact (all package files
tracked at main HEAD `dfae4fb8`; engine at worktree commit named in the
freeze). G6_ADJUDICATION.md (skeptic F6) is committed (`f9dfb813`,
blob `7ac84973…`). F7 records that the freeze is reference-complete
but not self-contained (F9-class items not folded in).

## 4. ENGINE (G9) — PASS (finding F6 INFO)

- **13/13 tests, run twice by this auditor** (0.29 s / 0.24 s), both
  green, worktree clean after both runs. Coverage observed: quote-CCY
  §6 identity on hand numbers (EURUSD + USDJPY + blocked-zero-event +
  Wed×3), ×1.5/×2.0 stress, bar-side-difference law, hardcoded band
  table, tamper detection, leak-law poison counter-tests (top-level +
  nested), byte-identical determinism, OI-1 next-business-day
  enforcement (lookahead/Saturday/Sunday/too-late).
- **Independent quote-CCY verification on MY OWN synthetic case**
  (constructed by this auditor; neither the suite's fixtures nor the
  prior skeptic's case): USDJPY BUY 25,000 Wed 2026-07-01 fill
  21:00Z at ASK_open 157.560 + 0.2-pip slip → **157.562**; hold
  through 6 charged accruals (Wed×3 07-01, Thu×1 07-02, Sun×1 07-05,
  Mon×1 07-06, Tue×1 07-07, Wed×3 07-08 — Thursday-exit event correctly
  NOT charged, membership law `iter_swap_events` == hand list); SELL
  Thu 2026-07-09 at BID_open 158.000 − slip → **157.998**; opening
  USD 1,000,000 at 157.530 (inexact division). Engine == hand ledger
  on every line to the last decimal: commission **137.8667500 /
  138.2482500 JPY**, spread_once **750.000 / 500.000**, slip
  **50.000 / 50.000**, swap **2,500.0000** (6 events), §6 identity
  LHS = RHS = **8,123.885 JPY exact**, final cash equals the hand
  ledger at full 28-digit Decimal precision, conversion rows = 10
  (1 open + 2 fills + 6 swaps + 1 mark) each at the correct same-bar
  rate with `usd == quote × rate` exact, par-replay within the
  disclosed algebraic bound. Identity residual **2.06E-22** (opening
  division rounding only; frozen gate 1e-9 holds with 13 orders of
  margin) — see F6.
- **Bar-side-difference law verified in code AND behavior:** fills
  price at the bar's own OPEN side quote (BUY→`ask_open`+slip,
  SELL→`bid_open`−slip); `spread_once = |quoted_side − mid|` (0.030,
  the side-quote distance — NOT the 0.060 full width); full width
  reported only as `bar_side_difference_bps` with
  `bar_side_difference_executable = False`; crossing identity
  `spread_once + slip == |fill − mid|` enforced per fill (assertion in
  `price_fill`); band cells are validation-only (`validate_bar_spread`
  never prices; USDJPY typed NOT_COMPUTED, never guessed).
- **Determinism:** my full-pipeline serialization hashed twice in
  separate processes → identical blob sha
  `3df7c4d556d87e577644b1134b97fd43193844df8e8e7296de28d74ca91e870b`;
  suite re-run identical; no wall-clock in any row.
- **Leak-scan:** clean under this auditor's OWN vocabulary (incl.
  `alpha`, `edge`, `score`) and under the engine scanner, over all
  engine outputs AND over journal rows written to temp by this
  auditor; poison key rejected at write time.
- **OI-1 write-time enforcement:** a trade row with
  `consumed_bar_date 2026-07-03 (Fri)` / `available_time_utc 2026-07-04
  (Sat)` was REJECTED by the writer.

## 5. G6 DATA — PASS

- **Re-hash: 16/16 raw files match MANIFEST.json** on sha256 AND byte
  size (this auditor, `hashlib`, all 16 entries).
- **Coverage: 66/66 weekdays** 2026-07-01→2026-09-30 per instrument per
  side, `missing_weekdays []`, `interior_gaps []`, BID/ASK date sets
  identical; US holidays 2026-07-03 / 2026-09-07 present in source
  (measured calendar law). The Jul-1 boundary defect recovery verified:
  2026-07-02 appears in both the main chunk and the `*a` addendum chunk
  with **byte-identical rows**; addendum conIds re-verified
  (AUD 14433401 / CAD 15016062, match main pass).
- **Forming-bar exclusion verified:** the live 2026-10-01 bar exists
  verbatim in 4 raw files (no-filter rule) and
  VERIFICATION.json `forming_bar_disclosure` records all four with the
  law "EXCLUDED from every in-window panel and MUST NOT be consumed
  downstream"; my independent panel build over the in-window dates
  contains no 2026-10-01 bar; June overlap rows are the addendum's
  disclosed verbatim verification window, also outside the panel.
- **The envelope FAIL stands, not relabeled:**
  `VERIFICATION.json` `sanity_verdicts.pre_registered_band =
  {"AUDUSD": "FAIL", "USDCAD": "FAIL"}` with the band note verbatim.
- **Independent recompute of every load-bearing number (66-day panel,
  crossed-book filter, quantile 'lower') reproduces the adjudication
  exactly:** AUDUSD p50 2.5 / p90 8.5; USDCAD p50 2.5 / p90 14.0 (the
  `< 8 pips` leg FAILs both); midweek medians **1.5 / 2.0**, midweek
  p90 **4.0 / 3.5**; Friday medians **8.5 / 16.0**; **10/13** of the
  top-13 spreads are Fridays on both pairs; 0 crossed books; 0 minTick
  violations; mid domains plausible.
- **Adjudication ruling (b) is mechanism-justified, not convenience:**
  (i) the failing `< 8 pips` cap is unsatisfiable by the frozen,
  ACCEPTED same-source corpus itself in the same quarter (same-source
  control NZDUSD p90 8.0 / USDCHF 12.5 — pre-dating the pull, corpus
  sha-frozen 2026-09-30) — a band no acceptable panel can pass cannot
  discriminate data quality; (ii) Friday close = the weekend-stale
  session-last print (16×/4.5× median gap in the frozen corpus; the
  midweek-only gate is a property of the observable's day-set, proven
  on data frozen BEFORE the pull existed — it cannot be
  data-driven convenience); (iii) the corrected law's anchors pre-date
  the pull (midweek bracket [0.5, 3.0] = the corpus's own midweek
  p50s; p90 cap 11.0 = corpus full-window midweek p90 max) and the
  data passes **by measurement with margin** (1.5/2.0 vs [0.5,3.0];
  4.0/3.5 vs 11.0); (iv) the corrected law is STRICTER everywhere
  else (fail-closed structural legs added; Friday disclosed-never-
  gated-never-trimed per the owner G5 no-trim law); (v) the excluded
  quantity prices nothing (kernel fills at OPEN-side quotes; the
  close-side statistic is not cost-consumed). `NOT_RUN_INPUT_END`
  rejection correctly refused (bars exist; typing absence over
  sha-verified data would be a false trial-accounting record).
- **Boundary hygiene of the pull:** `readonly: true`, clientId 66,
  `orders_placed 0`, `market_data_subscriptions 0`,
  `paper_du_prefix_only true`, `account_ids "REDACTED-NOT-RECORDED"`;
  raw files are pure OHLC rows (DU/accountId/key greps clean).

## 6. PROTOCOL CONFORMANCE — PASS (finding F1)

- **Corpus fidelity, read by this auditor in the corpus files:**
  - `symbols/USDJPY.md` line 241 (S65): "Signal: NATGAS 10d ret > +15%
    (breaking structure) khi Brent flat. · Trade: long USDJPY 5 phiên,
    stop 1×ATR. … · Coupling: chỉ khi Brent flat (để tách channel — nếu
    Brent cùng chạy thì là S64)." → PLAN DS-03 quotes this verbatim;
    G7 freezes Brent-flat as corpus-mandatory (it appears 2× in S65 —
    signal + coupling), hold 5 sessions, stop 1×ATR, ATR-14 DECLARED
    param-gap, "Brent flat" unquantified → LEARN grid G1 (A null-
    control only / B 3% default / C 5%) — lawful, no invented
    parameter; EIA inputs (RNGWHHD/RBRTE) signal-only 1bd, T+1-open
    decisions, never fills (OI-5).
  - `symbols/EURUSD.md` lines 264–265 (S6): "Signal: rank 20d return
    của {EUR,GBP,AUD,NZD,CHF,JPY,CAD} vs USD; vào EURUSD long chỉ khi
    EUR rank 1–2 · Trade: hold tới khi rơi khỏi top-3, stop 2×ATR … ·
    Coupling: rank nhất quán 2 tuần liên tiếp mới vào." → PLAN DS-05
    verbatim; G7 freezes all corpus parameters; the 2-week consistency
    coupling correctly carried as ENTRY LAW (not optional); ATR-14
    DECLARED; AUD/CAD input end = G6 outcome (resolved by the pull).
- **Parked-leg law applied correctly:** 5 legs (DS-01/02/04/06/07)
  parked under the owner's quoted review law ("nếu phải phát minh rule
  mới thì park chân đó") with per-leg reasons and named un-park
  conditions (PLAN §0b ¶1; G7 table); 2 further legs parked earlier by
  triage (§1.2 S100/S090) and 9 excluded with exact NOT_RUN reasons
  (§1.3). Operative slate = {DS-03, DS-05} only — matches FREEZE,
  registry event reason, G7.
- **Calendar arithmetic reproduces exactly** (this auditor, python):
  master 2020-10-02→2026-09-30 = **2,190 days = 312.857w**; warmup 52w
  = 364d → **2021-09-30**; LEARN 51w = 357d = **19.551%** of the
  post-warmup 260.857w (exactly 20% = 52.17w; **52 whole weeks would
  overshoot by exactly 1 day** — fold 8 ending 2026-10-01 > 09-30; the
  rounding-down law is stated and frozen); embargo 1w 2022-09-23→29;
  8 × 182d folds, each Fri→Thu: fold 1 2022-09-30→2023-03-30 … fold 8
  **2026-03-27→2026-09-24**; total 364+357+7+1456 = **2,184 ≤ 2,190**;
  unscored tail 2026-09-25→09-30 (6d). AUD/CA 2026-06-30 boundary
  resolved by the G6 pull (66/66 through 09-30) — fold 8 counts fully
  for DS-05.
- **PASS bars prospective-only; P-MW/P-FA defined:** §4 items 5 (P-MW,
  LORO per-leg with the mandatory two-sided per-fold table;
  one-sided reporting ⇒ `NOT_RUN_INTEGRITY`) and 6 (P-FA
  false-admission mirror + ≥50% single-trade concentration
  disclosure); P7 fold concentration; P8L one-break typing; floors
  unmet ⇒ `NOT_RUN_THIN`. All under the §4 scope law (prospective
  surface only).
- **Budget:** 10 identities ≤ 24 ✓. Row arithmetic — see F1.

## 7. PIT / VEHICLE — PASS

- OI-1 declaration law present and mechanical: label
  `LAG_DECLARED_BY_OWNER (DECLARED, NOT MEASURED …)` in PLAN §0;
  `available_time = next business day` for every OI-1 panel input
  (PLAN §0 table); journal writer enforces next-business-day on every
  PIT entry at write time (my counter-test rejected a Sat serving).
- σ tripwire frozen 1σ/5σ/0.5σ with explicit never-loosened language:
  PLAN §0 OI-1 ("never loosened"), FREEZE item 1 ("never loosened"),
  G3_G4 header ("re-run and frozen — and never loosened to pass").
- Vehicle = FX-spot pairs only: PLAN §0 "Executable vehicles: FX-spot
  pairs only"; §1.1 traded-vehicle column all FX-spot; engine PIP/
  QUOTE tables include XAU/XAG for band-completeness only, explicitly
  never vehicles (XAU signal-only OI-3; XAG NOT_RUN OI-4).
- No CONTFUT / ADJUSTED_LAST anywhere in the engine, tests, or package
  (grep clean; the only mentions are prohibitive statements). EIA rows
  are signal-only, never fill prices, in three binding places (OI-5
  row, §1.1 input basis, DS-03 param note). Energy execution FLAT.

## 8. BOUNDARY SWEEP — PASS

- **No S1 / paper / live / orders / GO consumption:** registry `s1
  SEALED_UNTOUCHED`; `go_phrase_state REGISTERED_NOT_CONSUMED`;
  registry events end at the registration event (1194 lines); G6 pull
  `readonly true`, orders 0, subscriptions 0, disconnected true; every
  session doc carries the no-S1/no-orders/no-GO compliance line.
- **TERMINAL cycles untouched:** every commit in the chain
  `3acf085d → 7d14f72e → 9db7f7f1 → 541fc223 → f9dfb813 → dfae4fb8`
  touches ONLY `research/control/terminal_review_2026-10-01/successor/**`
  (plus `plans/` registry files at registration); worktree commits
  `09fb1b74`/`2f7bc832` touch ONLY `research/daily_exploratory/**`,
  `tests/test_daily_exploratory.py`, `research/control/
  DAILY-EXPLORATORY-V1/FREEZE.md`.
- **No closed-budget reuse:** fresh cycle budget 0/10, fresh 10-identity
  rescope; no prior cycle's ledger/budget referenced.
- **Owner dirty tree preserved:** the pre-audit dirty entries remain
  (SIXSOURCE `sessions_index.jsonl` modified + 2 sanitized-window
  untracked files; untracked `SANDBOX-OVERFIT-3ASSETS/{data,out}`,
  `SLEEVE-FX5-100K-V1/`); the only change is `G6_ADJUDICATION.md` now
  lawfully committed (the required F6 discharge), nothing else moved.
- **Data-lane worktree untouched:** `.worktrees/pc12a-7asset-unblock-
  20261001` @ `d722f5d5` (referenced read-only by G3_G4 for
  `validate_xcheck.py`); no writes.
- **No account IDs / keys / credentials:** VERIFICATION.json
  `account_ids "REDACTED-NOT-RECORDED"`, `paper_du_prefix_only true`;
  DU-prefix/accountId/api-key/secret/token/password greps over package,
  engine, and raw files: clean.

---

## VERDICT — findings (each with evidence + remediation)

- **F1 [MEDIUM] — Budget row-count arithmetic in PLAN §3 rescope does
  not self-reconcile.** Evidence:
  `PLAN_DAILY_SUCCESSOR_DRAFT.md` §3 rescope paragraph (lines 395–401)
  enumerates SLATE 8, B0 0, B1S 8, B2 8, B3 8, C2 8, LORO×2 16, ×1.5
  stress×2 16 — **summing to 72 scored rows** — but states "10
  identities / 64 scored rows", "67 total", "→ 83". The 64/67/83 chain
  is exact ONLY under the convention that the C2 battery's 8 fold-rows
  sit on their own disclosed line outside the row budget, which the
  rescope text does not state, while the superseded §3 table directly
  below counts C2's 8 rows INSIDE its 112-row subtotal — two unstated,
  inconsistent conventions. Under the inclusive reading the composition
  needs 72 + 3 LEARN = 75 scored rows and 91 with the ×2.0 reporting
  tier — **exceeding the frozen "≤83 rows" cap in FREEZE.md item 5**
  and the registry-adjacent statement (10 identities / 83 rows max).
  Identities (10 ≤ 24) reconcile either way; the discrepancy is in the
  conservative direction (frozen cap tighter than the inclusive
  requirement), and budget used is 0/10 today, so nothing has been
  misspent. Remediation (owner/Lead, before fold-1 execution): a
  one-line budget-composition amendment in the cycle control dir
  naming the governing convention — either (a) C2 fold-rows on their
  own disclosed line outside the ≤83 (then 64+3+16=83 is exact and the
  freeze stands as written), or (b) inclusive counting (then restate
  the cap to 91 ≤ 120 or drop one 8-row component). Frozen numbers
  must reconcile before the first ledger row exists.
- **F2 [MEDIUM] — Registration-day freeze-time acts (recorded ceremony
  duties) not executed/logged at registration.** Evidence: SKEPTIC_
  PREREG_FINAL.md §VERDICT closing paragraph ("Registration ceremony
  must additionally EXECUTE the named freeze-time acts: G3 re-run +
  VIX tail re-extension, G4 re-run on registration-day bytes, G5
  vehicle-side band derivation (MEASURED-DERIVED, logged), and name
  the holiday calendar for next_business_day (F8)"); the registration
  commit `dfae4fb8` diff touches only registry files — no G3/G4 re-run
  artifacts, no vehicle-side band derivation (engine still types
  EURUSD/GBPUSD/USDJPY/AUDUSD/USDCAD `D1BAND-NOT_COMPUTED-
  PENDING-REGISTRATION-FREEZE`, `costkernel.py` line ~209);
  `journal.next_business_day` models weekend-skip only (holiday
  calendar unnamed). Contained: PASS bars never read on the battery,
  fills price from bar-quoted sides, NOT_COMPUTED is fail-closed, and
  the frozen VIX fetch (through 2026-09-25) covers the exploratory
  folds (end 2026-09-24); the tail matters for prospective
  accumulation. Remediation (Lead, before the first battery run):
  execute and log in the cycle control dir: G3 re-run + VIX tail
  re-extension (2026-09-28..30+), G4 re-run on registration-day bytes,
  G5 vehicle-side D1 band derivation (MEASURED-DERIVED, logged), and
  the holiday-calendar naming (or the typed fallback) for
  `next_business_day`.
- **F3 [LOW] — Envelope-law owner ratification recorded only
  implicitly.** Evidence: `G6_ADJUDICATION.md` §3 "this law takes
  effect only at owner freeze and applies prospectively"; the
  lane-authored worktree FREEZE (commit `2f7bc832` message + item 3)
  declares it frozen; but the ROOT registration artifacts (commit
  `dfae4fb8` message; registry event 1194 reason) do not name
  HMDS-D1-CLOSE-ENVELOPE@1 — SKEPTIC_PREREG_FINAL F7 asked the
  registration packet to ratify it explicitly. The substantive chain
  is intact (owner election → researchctl registration naming the
  plan/FREEZE → adjudication tracked at HEAD) and NO relabeling
  occurred anywhere (FAIL stands; re-verified). Remediation: one
  explicit owner-ratification sentence for HMDS-D1-CLOSE-ENVELOPE@1 +
  the G6 AUD/CAD acceptance in the cycle control dir at the first
  scored-run gate.
- **F4 [LOW] — §7 registration input-list (skeptic F2) not extended.**
  Evidence: the F1 discharge diff (541fc223→dfae4fb8, PLAN lines
  593–604 + item-1 lead) added only the carve-out; §7 "Then A1" (line
  632) still names the pre-G3–G10 list and not `G3_G4_VIX_SIGMA.md`,
  `G5_G6_SPREADS_INPUTEND.md`, `G6_ADJUDICATION.md`,
  `g6_pull/{MANIFEST,VERIFICATION}.json`,
  `DRAFT_AMENDMENT_EXPLORATORY_ONLY.md`, or the worktree FREEZE +
  engine commit. The registry row's plan pointer + FREEZE.md tie these
  artifacts in fact (all traced in §3 above). Remediation: optional
  conforming edit; otherwise rely on the registry plan path + FREEZE
  as the binding citation set.
- **F5 [LOW] — Residual pre-election session text remains in dated
  artifacts (documented as superseded; must not be cited as current).**
  Evidence: `ACTION_PACKET_GATES.md` line 37 "when G1–G12 ALL PASS →
  register"; `G7_G8_G10_FREEZE_DRAFTS.md` lines 70–73 "blocked until
  G1–G12 ALL PASS"; PLAN §4 inheritance line 458 "≥6-fold calendar
  floor — met with 8" (skeptic F3 residual; defused by the scope-law
  paragraph above it); `DRAFT_AMENDMENT_EXPLORATORY_ONLY.md` status
  line still reads "DRAFT — awaiting owner election. Not registered,
  not dispatched" although the election is recorded and the cycle IS
  registered (registry event 1194) — stale, and its "validation =
  post-registration prospective surface only" phrasing retains the F5
  ambiguity the prior skeptic noted (defused by item 2 "No after-cost
  PASS, ever" and item 3's purpose = feeding a LATER measured-cost
  cycle). Remediation: mark the amendment "ELECTED & SUPERSEDED by
  registration 2026-10-01 (see registry + FREEZE.md)" at the next
  lawful touch of the control dir; never cite the two gate-status
  tables as current state (per SKEPTIC_PREREG_FINAL item 6).
- **F6 [INFO] — quoteccy docstring exactness nuance.** Evidence:
  `quoteccy.py` module docstring "Decimal-exact here, so the observed
  residual is 0" holds only when the opening conversion divides
  exactly; with an inexact opening rate (auditor case 1,000,000 /
  157.530) the §6 identity residual is 2.06E-22 (28-digit rounding of
  the opening division carried through level arithmetic) — inside the
  frozen 1e-9 gate by 13 orders. Not a defect. Optional: one-word
  docstring precision ("exact for exact conversions; ≤ Decimal
  context rounding otherwise, gate 1e-9").
- **F7 [INFO] — FREEZE.md is reference-complete but not self-contained
  (skeptic F9 items not folded in).** Evidence: warmup/LEARN/embargo
  boundaries + fold table + rounding law, G1 grid nodes + LEARN
  objective/tie-break, G3 tail re-extension duty, G5 vehicle-side
  NOT_COMPUTED note, declared-cost constants one-liner, XAU archive
  sha, AUD/CAD conIds are reachable only via PLAN §2/§3/§5, G3_G4,
  G5_G6, and the engine commit. Every item WAS traced to a committed
  artifact by this auditor (§3 table), so this is completeness-of-
  reference, not integrity. Remediation: fold the F9 one-liners into
  the freeze at the first lawful amendment touch.

### What was verified clean (summary of positives)

Registration lawful and reconciled on every axis; election verbatim in
three authoritative places; GO phrase registered-not-consumed with zero
consumption events; exploratory-only law airtight in prose AND
mechanically (write-time enforcement, auditor-poison-tested); every
frozen item traced to a committed artifact including the engine commit
sha named in the freeze; engine exact to the last decimal on an
auditor-constructed case, deterministic byte-identical, leak-clean,
bar-side law correct; G6 data 16/16 re-hashed, 66/66 coverage, forming
bar excluded by law, FAIL standing not relabeled, corrected envelope
law mechanism-justified by data frozen before the pull existed; corpus
rules verbatim-faithful for both operative legs; calendar arithmetic
reproduces exactly incl. the 1-day 52-week overshoot claim; parked-leg
law applied; PIT/vehicle laws present and enforced; boundaries clean
(no S1, no orders, TERMINAL cycles untouched, no budget reuse, owner
dirty tree preserved, no credentials).

— end A7_PRELAUNCH_AUDIT —
