# SKEPTIC_DAILY_PLAN — fresh-context final gate on the DAILY successor package (2026-10-01)

Reviewer: fresh-context skeptic (no authorship of any reviewed object).
Objects: `../OI_DECISIONS_APPLIED.md`, `PLAN_DAILY_SUCCESSOR_DRAFT.md`, `../SUCCESSOR_PLAN_DRAFT.md`
(as edited: §3.2 rewrite, §3.4 no-unseal [already operative at HEAD, diff shows only
§3.2 + §7b changed], §7b quote-CCY). Method: every check below was re-measured by me
this session (own `ls`/`find`, own `shasum -a 256`, own `.venv/bin/python` date
arithmetic, own reads of the corpus files, frozen TSVs, IDENTITY_FREEZE,
XCHECK_REPORT@cbae7556, PASS_BARS_V2, FILL_ACCOUNTING_SPEC, JOURNAL_SCHEMA,
H1 docket). Read-only except this one file. Nothing herein scores, registers,
admits, or touches S1/ledger/registry.

Label law: BLOCKING = must be fixed before commit (object-level fidelity
defect); MINOR = fix at commit or at latest at registration freeze (citation /
disclosure hygiene); INFO = recorded for the owner, no edit required.

---

## 1. OI fidelity (OI_DECISIONS_APPLIED vs owner directives) — PASS, no defects

- **OI-1** — label string `LAG_DECLARED_BY_OWNER (DECLARED, NOT MEASURED —
  historical lag not measured; point-1/point-2 presence evidence on file)` is
  byte-identical in OI_DECISIONS_APPLIED and daily-plan §0; "use ONLY closed
  bars from the NEXT business day" present in both (§0 row + §6.1
  `available_time_utc` = next business day); σ tripwire FROZEN 1σ/5σ/0.5σ
  "NEVER loosened to pass", tripwire in panel-σ units, tight-bars-demote-ECB
  carried in OI_DECISIONS (§0 compresses to "never loosened" — acceptable; the
  registration gate item 2 recomputes the tripwire at freeze). The divergence
  note (option (a) vs any registered artifact) has no live conflict: no
  registered artifact found that specifies otherwise. Consistent with
  `pit_status=NOT_MEASURED` / `ASSUMED_NEXT_BUSINESS_DAY` in
  `IDENTITY_FREEZE_2026-09-30.json` and with REV-3's
  `PERSISTENCE_PRESENCE_MEASURED_2pts` (value-stability still NOT_MEASURED —
  carried in §0). ✓
- **OI-2 — verified myself:** `ls ~/.my-quantitative-data/ibkr_statement/`
  → No such file or directory; `find ~/.my-quantitative-data -iname
  "*statement*|*flex*|*activity*"` → zero files anywhere under the data home.
  The "does NOT exist / no statement/flex/activity files" claim is accurate;
  NOTHING-scores-before-OI-2 is stated unambiguously in three places (plan
  status header, §5, §7.1). Export instruction contains no account IDs/keys. ✓
- **OI-3 — re-hashed myself:** `shasum -a 256` of
  `.worktrees/forex-ng6/integration/research/control/forex_ng6_run/p0/staging/XAUUSD_1day_full.json`
  = `49c2684ebb045302acf0c452b5aa9a3b96dff73eb3bc6f5add1801d6817fb33d`,
  1,347,055 bytes — EXACT match to the quoted sha and byte count, and to
  `IDENTITY_FREEZE…xau_overlap_vs_td_archive.archive_sha256`
  (`archive_sha256_dv_verified: true`, same path). ✓
- **OI-4 — XAG stays NOT_RUN:** grep of the daily plan shows XAG only in the
  §0 OI-1 panel list (the owner's own four-panel declaration), the OI-4 row,
  the §1.3 exclusion row (XAUUSD-S063/XAGUSD-S081 — both corpus gids verified
  to exist with those mechanisms), the "no XAG dependency in §1.1"
  verification note, and attack item §8-e. No XAG admission, no prose
  override of the PIT-FAIL, no SLV proxy, no purchase. ✓
- **OI-5 — all five elements present in both files:** RBRTE/RWTC/RNGWHHD
  signal-only, 1bd declared serving, SINGLE-SOURCE label, never fill prices;
  energy execution FLAT/NOT_RUN; no CONTFUT / no ADJUSTED_LAST / no
  EIA-spot fills; no subscriptions enabled; AECO/TTF rows NOT_RUN. The §1.3
  excluded table enforces exactly this state (TTF row, WTI-execution rows,
  futures-curve rows, intraday row, AECO row). ✓
- M1-CAL=N1 / S1 sealed ("no unseal is authorized", §3.4) and M1-D
  (USDCAD/AUDUSD intraday NOT_RUN; daily-clock judged separately) restated
  consistently in both files. ✓

## 2. Daily slate — quotes verbatim; 2 BLOCKING label/coupling defects

All nine candidate rule texts were opened in the corpus
(`FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/*.md`) and compared fragment by
fragment. DS-01 (AUDUSD.md S81), DS-02 (USDJPY.md S63), DS-03 (S65), DS-04
(S83), DS-05 (EURUSD.md S6), DS-06 (S61), DS-07 (S85), and both parked legs
(AUDUSD.md S100, USDCAD.md S90): every quoted Signal/Trade/Data/Coupling
fragment is **verbatim** (elisions marked "…", Vietnamese quoted as written);
all numeric parameters in the plan (60d z, ±2, <20d half-life, 0.3/3 exits,
1:1 legs, 2×half-life cap, VIX Δ5d>+4, 1.5σ, 1×ATR, VIX<20, 10d +15%, 5
phiên, 1 tuần, top-3/2×ATR, 20d rank, rank 1–2, z(20d)>2, ≤10 phiên, ±2.5σ)
trace to the corpus text. No invented parameters: every gap is a declared
PARAM-GAP (owner declaration or ATR-14/60d conventions labeled DECLARED) or a
≤3-node LEARN grid (G1 Brent-flat, G2 Kalman band) with the corpus default
preserved as a node. Park reasons verified: S100 = kill-switch of S31/S32/S63
(host rules not in cohort) + optional scalp unparameterized ("stop siết" — no
distance/size) — faithful; S090 = meta re-weight of S88 + corpus "Data: 2
futures D" (verbatim) making EIA-spot substitution an owner re-freeze, not an
inference — faithful. The Matrix-B "ADMITTABLE-AS" data verdict being
distinguished from rule-readiness is stated and honored.

Line citations: LEG_RESOLUTION_MATRIX.tsv lines 34/63/83/99/149/163/167 (the
7 NEW-DAILY-CANDIDATE rows) and 257 (USDCAD-S090) all verified correct;
outcome labels for DS-01/02/04/05/06/07 match the frozen
PORTFOLIO_ELIGIBILITY_1200.tsv exactly.

Findings:

- **F-1 (BLOCKING) — DS-03 outcome_exposed_label misquote.** Plan §1.1 row 3
  says `FAMILY_HISTORY_NEGATIVE (YES)`; the frozen row (eligibility TSV and
  LEG_RESOLUTION_MATRIX line 65) says **PRIOR_NOT_SCORED / known_negative_prior
  NO**. By the plan's own §8-d law ("verbatim quotes vs paraphrases — any
  drift = integrity trip") a misquoted frozen label in the slate book must be
  corrected before commit. Direction is conservative (claims a MORE negative
  prior than exists), so no admission decision changes — but it is still a
  misquote of frozen evidence in the core preregistration table.
- **F-2 (BLOCKING) — DS-01 corpus coupling silently dropped.** AUDUSD.md S81
  ends `Coupling: S35 hai policy path hội tụ mới vào` (enter only when S35's
  two policy paths converge). The plan quotes the S81 Signal/Trade/Risk-hold
  fragments and asserts "**Rule-ready otherwise**" without disclosing this
  coupling — inconsistent with its own treatment of DS-02 ("gold trend phải
  đang dương" — inclusion/exclusion frozen at registration), DS-04-b
  (FOMC/NFP veto) and DS-06-a (BTP-Bund gate). S35 is not in the cohort and
  its inputs are unevidenced here, so the coupling cannot fire: that needs a
  disclosed registration decision (mirror of DS-06-a), not silence.
- **F-3 (MINOR) — wrong line citation.** §1 says "USDJPY-S065 line 128";
  USDJPY-S065 is **line 65** (class FUTURES-BLOCKED, one of the two
  EIA-signal legs, consistent with the plan's framing). Line 128 is
  USDJPY-S011 — an unrelated ALREADY-RUNNABLE row. Evidence pointer must be
  corrected (one-cell edit).
- INFO: no inference upgrades found — every §1.1 input carries OI-1 / OI-3 /
  OI-5 / evidenced-panel (I-EUR/I-GBP/I-JPY poolB M1; I-AUD/I-CAD frozen H1
  panels) basis, and VIX is carried on Matrix B's citation alone with span
  re-verification made a registration-gate item (§7.2) and an attack item
  (§8-a(iii)) — labeled, not upgraded.

## 3. Calendar arithmetic — PASS, recomputed exactly

Recomputed independently (venv python): 2020-10-02→2026-09-30 = **2,190 d =
312.857 w** ✓; warmup 364 d ends **2021-09-30** ✓; LEARN 357 d =
**2021-10-01→2022-09-22** ✓; 51/260.857 w = **19.55%** ✓; exactly 20% =
52.17 w ✓; a 52w LEARN shifts fold 8 to end **2026-10-01** (1 d overshoot) ✓;
embargo **2022-09-23→2022-09-29** ✓; the 8 fold rows (2022-09-30→2023-03-30 …
2026-03-27→2026-09-24) are **byte-exact** ✓; unscored tail
2026-09-25→2026-09-30 = **6 d** ✓; 364+357+7+8×182 = 2,184 ≤ 2,190 ✓; majors
inputs available 2021-01-04 inside warmup ✓; 8 folds ≥ 6-fold floor (E-Law 5)
✓.

Exposure disclosure: §2.1 states explicitly that ALL seven legs consume
majors-derived D1 closes from panels inside the PC12A exposed window and are
labeled **EXPOSURE-ADJACENT at the input level**, while
NZDUSD/USDCHF/XAUUSD/EIA inputs are "untouched by any scored run at any
date"; corpus-knowledge contamination (written 2026-09-28) is disclosed with
its mitigations, and §8-a(iv) makes me attack exactly this. Honest and
explicit. INFO: for AUDUSD/USDCAD specifically, "WERE part of the PC12A
exposed window" slightly overstates (their H1 panels were staged/TRAIN-only,
not scored — H1 docket §C); the over-label is the conservative direction and
harmless, but the owner should know the precise provenance at registration.

## 4. Budget — PASS, recount exact

Identities recounted: SLATE 1 + B0 1 + B1S 1 + B2 1 + B3 1 + C2 battery-as-1
(seeds on their own sub-run line) 1 + LORO×7 + ×1.5 SLATE 1 + ×1.5 B1S 1 =
**15 ≤ 24** ✓ (headroom 9). Rows: 8+0+8+8+8+8+56+8+8 = **112 scored** +
6 LEARN-grid rows (G1+G2 × 3 nodes, single LEARN pass) = **118 ≤ 120** ✓
(headroom 2). B0 zero-row law consistent with PB2 §1 ("no orders ever;
equity constant; netPnL=0/maxDD=0 by construction") — no orders ⇒ no journal
rows ✓. Battery-as-1 per E-Law 8 ✓. ×1.5 runs on BOTH governing arms ✓; B3
preserves PB2's ×2.0-kernel selection objective and frozen tie-break chain ✓
(not inconsistent with the ×2.0 reporting-tier deferral, which is a separate
identity). P1-B0 sub-bar matches PB2 §2; P7/P8L match PB2 §7/§8 semantics.

- **F-4 (MINOR) — ×2.0 reporting-tier deferral.** PB2 P6b is "REPORTING only,
  ×2.0 (non-governing)" and still says "compute and report"; the plan defers
  it (8 more rows needed, only 2 headroom), keeps ×1.5 governing on both
  arms, keeps the cost-dominated sign-flip disclosure at ×1.5, and self-
  attacks the deferral in §8-c. Acceptable ONLY as an owner-visible deviation
  frozen at registration (the plan says exactly this); recorded here so the
  owner sees it at the gate.

## 5. Cost law — PASS, every measured cell re-checked

- Blocker law unambiguous in three places (status header, §5, §7.1):
  statement absent ⇒ NOTHING scores, no after-cost PASS, no scored run. ✓
- Measured cells vs `IDENTITY_FREEZE_2026-09-30.json@87e65f00`: NZDUSD
  p50 0.88 / p90 18.65 / max 239.07 bps (n=1553; freeze: 0.8822/18.6544/
  239.0719) ✓; USDCHF 4.51/16.02/216.10 (4.5124/16.0242/216.096) ✓; XAUUSD
  5.52/18.61/74.17 (n=1543; 5.5163/18.6133/74.1656; crossed-book-day caveat
  matches) ✓. Panel shas c681402b…/7fbd3a80…/02445884… ✓; conId 39453441 ✓
  (also in ACQUISITION_REPORT.json identity). Note for the record: the spread
  cells live in IDENTITY_FREEZE (ACQUISITION_REPORT.json carries identity +
  chunk shas, not spread stats) — the plan cites the correct artifact.
- σ values: NZDUSD 64.64 / USDCHF 49.62 bps = XCHECK_REPORT@cbae7556
  `panel_volatility` (64.6388/49.615) ✓. XAU TD-overlap n=1531, abs p50
  3.2462 / p95 26.5142 bps, signed mean +0.3359 USD — EXACT vs
  `xau_overlap_vs_td_archive` ✓.
- M1 window cells: "C1 Fri-20:00 p50/p90 pips EURUSD 0.3/0.5 · GBPUSD 0.8/1.3
  · USDJPY 0.5/0.9" — EXACT vs FILL_ACCOUNTING_SPEC cost table (COST_
  AUTHORITY_TABLE C1, n=286/286) ✓. H1 cells: AUDUSD C1 1.0/1.3 pips — EXACT
  vs H1 docket C §1.4 ✓. The "daily-band stats NOT YET COMPUTED for the five
  majors → MEASURED-DERIVED at registration freeze, never guessed" statement
  is the right fail-closed posture ✓.
- Swap law: matches FILL_ACCOUNTING_SPEC verbatim — 1 pip/night against the
  position both directions (never income), 22:00 UTC boundary, Sun×1/Mon×1/
  Tue×1/Wed×3/Thu×1/Fri×0/Sat none = 7 pip-nights per 7-night week,
  membership `u(E⁻)≠0`, DECLARED modeling convention (NOT venue-measured),
  OI-2 statement replaces it whole ✓. U2 commission 0.35 bps/side DECLARED ✓;
  U3 daily variant DECLARED ✓; spread-once identity (no third crossing line)
  = spec §2 ✓; ×1.5 scales all VARIABLE components, fences unscaled = spec §5
  ✓; PROVISIONAL_PENDING_COST_AUTHORITY / NET_DEFAULT_COST labels present ✓.
- EIA input class: RNGWHHD 1496d / RBRTE 1512d / RWTC 1494d,
  2020-10-01→2026-09-29, sha-pinned, 1bd serving — consistent with the frozen
  matrix + MANIFEST_RAW@cbae7556 (XCHECK's 1511 for BRENT is the
  CONTFUT-aligned count, not the RBRTE span). INFO only.

## 6. Plan-consistency — PASS with 2 citation defects

- **§3.2 vs daily LEARN:** §3.2 says "the first 20% of the admitted daily
  panels' calendar (2020-10-02→)"; the daily plan's warmup-before-LEARN /
  51w = 19.55% placement is explicitly disclosed as a deviation (§2.2
  "Deviation disclosure"), justified (warmup-inside-LEARN leaves ~10.4w of
  usable learning data; 52w overshoots by 1 day), owner-frozen at
  registration, and self-attacked (§8-b). Deviation DISCLOSED ✓.
- **§7b quote-CCY:** referenced by name in the daily plan's journal spec
  (§6.4) with matching content (quote-CCY books, one frozen convention,
  per-fill realization rates, 1e-9 §6-identity reconciliation, par-convention
  replay bound). USDJPY legs carry explicit JPY→USD conversion rows; no
  USDCHF vehicle leg exists in this slate (USDCHF is signal-only), so §7b's
  "USDJPY/USDCHF" wording reduces correctly. ✓
- **M1 rules not imported:** zero SU-RS/SU-H occurrences in the daily plan;
  RULE_SLATE explicitly marked "deliberately NOT imported here". ✓
- **Registration gate complete:** OI-2 lands + PIT gates (incl. XAU σ at
  freeze, VIX re-verification) + cost gates + vehicle gates (sha-pinned
  panels, declared aggregations, DS-04-a synthetics, PARAM-GAP freezes) + D1
  input-completion (§2.4) + selection freeze. ✓
- **F-5 (MINOR) — dangling citation "JOURNAL_SCHEMA §1/§8".** The schema has
  §1–§4 only (88 lines); the cited law (every order intent journaled —
  filled/blocked/deferred/netted/fail-closed; hash-chained `prev_row_sha256`
  under the freeze SHA) lives in its header + §1. One-token fix.
- **F-6 (MINOR) — dangling citation "the 10-week-split variant of RULE_SLATE
  §4".** No 10-week split exists in RULE_SLATE §4 (its learning-window law is
  the whole-window LEARN + the 26w live-accumulation fallback; the 10w idea
  appears nowhere in the successor docs). The operative statement ("ONE LEARN
  pass; LEARN is a single window") is correct — the cross-reference is wrong.

## 7. Boundaries — PASS

No registration/scored-run/GO executed anywhere in the objects (all
scored/registration actions are gated future conditionals); S1 sealed-tail
language intact ("no unseal is authorized"); TERMINAL cycles untouched (git
status shows no modifications under any PC12A/BTC-COMBO6 path; the only
tracked-file modification, `DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/
sessions_index.jsonl`, plus the sanitized-*.json / SANDBOX / SLEEVE-FX5
untracked files are the sixsource collector lane's Sep-28 artifacts —
today's drafting session wrote only the three objects under review, mtimes
Oct 1 11:39/11:50). Grep for account-ID/API-key/secret/token/password
patterns across all three objects: clean (single false positive
"6-hypothesis book"). No orders, purchases, network, or credentials. Commit
must stage by explicit pathspec (standing law; other lanes' artifacts are in
the tree).

---

## VERDICT: **FIX_THEN_COMMIT**

The OI application, the slate's rule fidelity, the calendar, the budget, the
cost kernel and the boundary posture all survive independent re-measurement —
but two frozen-evidence fidelity defects in §1.1 (by the plan's own §8-d
integrity law) and three citation defects must be fixed first. Exact minimal
edits, all in `PLAN_DAILY_SUCCESSOR_DRAFT.md`:

1. **(F-1)** §1.1 row 3, last-but-one column: `FAMILY_HISTORY_NEGATIVE (YES)`
   → `PRIOR_NOT_SCORED (NO)`.
2. **(F-2)** §1.1 DS-01 block, after the direction-disclosure bullet, add a
   coupling line mirroring DS-06-a, e.g.: "Coupling disclosure (registration
   decision DS-01-b): the corpus entry condition `Coupling: S35 hai policy
   path hội tụ mới vào` (AUDUSD.md S81) cannot fire — S35 is not in this
   cohort and its inputs are unevidenced here; default = run ungated with the
   omission disclosed (owner may name a source or park at registration)."
   and qualify the closing claim `Rule-ready otherwise.` →
   `Rule-ready otherwise modulo DS-01-a/DS-01-b.`
3. **(F-3)** §1: `(USDJPY-S065 line 128, USDCAD-S090 line 257)` →
   `(USDJPY-S065 line 65, USDCAD-S090 line 257)`.
4. **(F-5)** §6 lead-in: `(JOURNAL_SCHEMA §1/§8)` →
   `(JOURNAL_SCHEMA header law + §1)`.
5. **(F-6)** §3 grid row: `(LEARN is a single window; the 10-week-split
   variant of RULE_SLATE §4 does not apply at this calendar)` →
   `(LEARN is a single window; RULE_SLATE §4's split/fallback variants are
   M1-track constructs and do not apply at this calendar)`.

Non-blocking, recommended at the same touch (owner-visible, not required for
commit): one sentence in §2.1 noting AUDUSD/USDCAD H1 panels were
staged/TRAIN-only in PC12A (not scored) and are labeled EXPOSURE-ADJACENT
conservatively; and one sentence in §3 recording that the ×2.0 reporting-tier
deferral (F-4) is a registered deviation from PB2 P6b (non-governing).

— end of skeptic report —
