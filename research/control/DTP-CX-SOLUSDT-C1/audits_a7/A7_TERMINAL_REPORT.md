# A7 TERMINAL REPORT — DTP-CX-SOLUSDT-C1 (independent reproducer, fresh context)

- **Verdict line: `A7 TERMINAL VERDICT: CONFIRM_WITH_FINDINGS`** — the claimed
  close reconciles from bytes end-to-end; the recommended cycle verdict
  **NO_ELIGIBLE_PROPOSAL stands** and no finding blocks it.
- Audit scope: terminal audit of the GO-1 arc (registry/GO, data gate, court R1
  I002 kill, court R2 death ledger, corpus blindness + floor, freeze chain,
  hygiene). Audited at worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/integration`,
  branch `orca/dtp-cx-solusdt-c1-integration`, HEAD
  `03d685efedc111b38e1a2fd442665697dd2b58d5`, interpreter
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
- No strategy PnL exists and none was computed. All recomputes are
  outcome-blind feasibility censuses. No sealed/S1 content touched.

## 0. Recompute scorecard (court R1, I002 kill — expected = court_machine@1.json, measured = this audit)

Independent implementation (`audits_a7/a7_recompute_court_r1.py`; own zip
reader, own oneshot greedy, own median; 21 s CPU, streaming month-by-month over
the 72 BTC + 72 SOL staged 1m zips). Definitions taken from the pinned
`pins_census` block: event `|close/open−1| ≥ θ/1e4`; oneshot consumes m+1;
lag arrays `sign(r_btc)·SOL-return·1e4` with presence rules.

| # | Metric | Expected | Measured | Result |
|---|--------|----------|----------|--------|
| 1 | BTC 1m rows total | 3,155,040 | 3,155,040 | MATCH (exact) |
| 2 | **θ=25 oneshot events (full span)** | **47,083** | **47,083** | **MATCH (exact)** |
| 3 | **θ=25 SOL same-minute conditional median (bps)** | **36.13582929771985** | **36.13582929771985** | **MATCH (exact, tol ±0.05)** |
| 4 | **θ=25 SOL next-minute close-to-close conditional median (bps)** | **0.0** | **0.0** | **MATCH (exact, tol ±0.05)** |
| 5 | θ=25 raw events | 56,795 | 56,795 | MATCH |
| 6 | θ=25 evaluable / excluded / same-min n | 46,620 / 463 / 46,616 | 46,620 / 463 / 46,616 | MATCH |
| 7 | θ=25 bookTicker-window evaluable | 1,962 | 1,962 | MATCH |
| 8 | θ=10 oneshot events | 315,579 | 315,579 | MATCH |
| 9 | θ=10 same-minute conditional median (bps) | 17.797816801139454 | 17.797816801139454 | MATCH |
| 10 | θ=10 next-cc median (bps) | −0.0 | −0.0 | MATCH |
| 11 | θ=10 raw / evaluable / excluded / BT-window | 420,039 / 312,299 / 3,280 / 17,195 | same | MATCH |
| 12 | BTC first/last open ms | 1,598,918,400,000 / 1,788,220,740,000 | same | MATCH |

18/18 scorecard rows bit-exact. The three kill laws (K-F0
information-measured-fictional, K-COST jointly-empty ceiling grid with power in
hand, K-ANC representation ρ>0.20) therefore rest on verified numbers.

## 1. Section-by-section results

### A. Registry / budget / GO — PASS
- Registry row: `DTP-CX-SOLUSDT-C1 ACTIVE_LIGHT 0/18`, head `03d685ef`,
  branch matches; `s1=SEALED_UNTOUCHED`; workers 0;
  `go_phrase "GO DTP CX SOLUSDT C1 SCORED EXECUTION" = REGISTERED_NOT_CONSUMED`.
- GO-1 phrase in root `GO_RECORD.md` (`GO DTP CX SOLUSDT C1 COUNCIL AND
  FREEZE`) matches the plan-registered phrase char-exact
  (`plans/PLAN_daytrade_playbooks_program_v1.md` line 411).
- GO-2 never consumed: no GO record beyond GO-1 in root or worktree; every
  "SCORED EXECUTION" occurrence is a registration/registry/moot statement;
  `trial_ledger.jsonl` header-only; no scored artifact exists in the tree.
- Owner Q1–Q5 readings recorded in GO_RECORD, consistent with
  GO1_OWNER_PACKET.md.

### B. Data gate re-derivation — PASS
- 6/6 re-hashes MATCH (sha256 via `shasum -a 256`):
  - Inherited PWS: `klines_um_SOLUSDT_1h/2024-06.zip` =
    `80e770b2…f4809d`; `funding/SOLUSDT_funding.json` = `9e850cb4…5a1036`;
    `bookTicker_um_SOLUSDT/SOLUSDT-bookTicker-2023-05.zip` = `394fa34c…00f8a`
    — each equals its committed `INVENTORY.md` row.
  - Staged this cycle: `klines_um_SOLUSDT_1m/SOLUSDT-1m-2021-05.zip` =
    `cd19f804…a16616`; `markPriceKlines_um_SOLUSDT_1m/SOLUSDT-1m-2021-05.zip`
    = `f362c332…ca1b39`; `klines_um_BTCUSDT_1m/BTCUSDT-1m-2021-05.zip` =
    `dcf7c567…0187dc8` — each equals its lane sha manifest row.
- **L-TRACKB1-1 confirmed**: months 2020-09 / 2023-07 / 2026-08 of
  `klines_um_SOLUSDT_1m` scanned row-by-row — every timestamp < 1e14
  (millisecond scale, no µs migration); endpoints equal the census (first
  2020-09-14T07:00Z, last 2026-08-31T23:59Z); 0 intra-month gaps, 0 duplicates.
- **2024-06 cross-granularity confirmed**: day 2024-06-15 UTC — 1m→15m
  aggregation 96/96 buckets consistent, 1m→1h (vs inherited PWS 1h zip)
  24/24 consistent, tolerance abs 1e-6 / rel 1e-9 per field. Matches the
  claimed full-month 2880/2880 and 720/720.

### C. Court R1 (I002 kill) — MATCH_ALL (scorecard above)

### D. Court R2 (death ledger) — PASS
- **38/38** distinct cited family_ids (union of all `kill_family_ids` /
  `family_ids` lists in `court_r2_machine@1.json`) present **exactly once**
  in root `research/wayfinder/FAMILY_FAILURES.jsonl` (137 rows; exceeds the
  ≥10 sample mandate — full coverage). Ledger sha256
  `195671d4…504777` equals the court's provenance pin.
- 9/9 provenance sha pins of court R2 re-verified byte-exact (RULE_CANDIDATES,
  CORPUS_MANIFEST, FETCH_LOG, PLAYBOOK_TAXONOMY, R1 court report + machine,
  FREEZE_R1, master plan, root MAP.md).
- Skeleton mappings independently judged **CORRECT**:
  - RANGE_FADE → measured fade-at-extreme family (TRACKA1-M1 law verified
    verbatim: PIT-clean PF 1.0334/1.0509 dead, lookahead twin passes);
    RSI+BB variant correctly routed to the gated-re-variant precedent.
  - BREAKOUT_CONTINUATION → with-break continuation both directions measured
    dead; E07 OI-form honestly NOT_CONSTRUCTIBLE; E09 clock variant routed to
    the FXFV clock/calendar deaths.
  - PATTERN_REVERSAL (E12 H&S) → **the court's correction is right**: the
    codified entry is a WITH-break short, i.e. the breakdown-continuation
    skeleton (PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT, ledger confirms
    CONTROL_OUTEARNED); SRLVCX1-M1 is fade-after-sweep with the opposite
    trigger direction, so it is not E12's skeleton; the failed-breakout
    re-label fork is independently dead. Both branches dead → verdict
    unchanged, as recorded.
  - TREND_PULLBACK → DINV-1D ledger row confirms ρ 0.3032/0.3103 with
    ancestry in the continuation leg.

### E. Corpus blindness + floor — PASS
- FETCH_LOG entries #1–#37 reconcile (30 + 7 supplementary = 37/50); every
  non-yielding fetch is accounted for in the rejected log (R01/R02
  DATE_UNVERIFIED, R03/R05 walls, R04 JS-empty, R06 K-cap overflow).
- CORPUS_MANIFEST.jsonl = 1 meta + 12 admissible (E01–E12) + 13
  uncodifiable-retained (U01–U13) — matches FREEZE_R2 and FETCH_LOG.
- 6 distinct admissible authors (≥5 required); K=5 respected (Kraken Learn
  and LiteFinance at exactly 5; R07 headroom note reflects round-1 state).
- Every admissible entry carries a platform-recorded publication timestamp;
  undateable candidates (crypto.com, Binance Square) were rejected, not
  admitted. Prohibition list respected: 0 ex-post recaps encountered;
  illustrative P&L recorded as claims, never evidence; no panel ever loaded —
  attested consistently across FETCH_LOG, both addenda, RULE_CANDIDATES,
  FREEZE_R2 (`panel_ever_loaded=false`) and both court machines. (Annotator
  blindness is attestable only from artifacts — inherent limit, disclosed.)

### F. Freeze integrity — PASS_WITH_FINDINGS (F-1)
- Chain coherent: FREEZE_R1 (I001 generator FROZEN C1–C6, I002 F0_KILLED,
  slot-3 SLATE_EMPTY) → constants addendum (K=5, N≤10, no-panel annotation
  rule, floor ≥12/≥5, 30-fetch cap) → r2 supplementary addendum (≤20 more
  fetches granted publicly pre-run, `CORPUS_FLOOR_FAILED` fallback declared)
  → corpus/court R2/FREEZE_R2. FETCH_LOG executed exactly the granted budget.
- **Mandatory bounded-scope sentence present** in FREEZE_R2.json; byte-identical
  to the court machine's English sentence except one glyph (em-dash vs hyphen
  at char 118; both 454 chars) — substantively verbatim (finding F-2).
- 0 scored cells / 0 ledger rows / 0/18 budget in registry and both freezes;
  "0 of 11 constructible rules survived" reconciles (11 F0_KILLED + E03
  DATA_GATED + E07-OI NOT_CONSTRUCTIBLE = 12 codified entries).

### G. Hygiene — PASS_WITH_FINDINGS (F-2, F-3)
- Tree clean at `03d685ef` except untracked data zips under `data_local/`
  (untracked-by-law with committed sha manifests) and this audit's own
  outputs. Heavy lock FREE_PROVEN; workers 0.
- No sealed/S1 content touched anywhere in the arc (all S1 mentions are
  attestations). Branch touched only this cycle + program packet prep.
- Root IDENTITY_REGISTRY.jsonl: I001 FREEZE_ELIGIBLE + I002 F0_KILLED rows
  intact, court-R2 outcome added as an append-only comment (law respected).

## 2. Findings (numbered)

- **F-1 (MEDIUM) — declared-vs-git timestamp reconciliation in R1/R2 authority
  artifacts.** FREEZE_R1 `frozen_at 06:40:00Z` vs first commit `e23ff983`
  06:34:25Z; FREEZE_R2 `frozen_at 08:05:00Z` vs first commit `03d685ef`
  07:41:01Z; `court_r2_machine generated_utc 09:30:00Z` vs its own lane
  handoff 07:38:37Z and the 07:41:01Z commit. Skew −6…+109 min. **Impact on
  content integrity: none** — every sha pin re-verifies, cross-pins prove
  existence ordering (court R2 pins FREEZE_R1's sha; skp-r2 handoff precedes
  the R2 commit; court R2 `dispatch_sha == e23ff983`), and the R2 arc landed
  in a single clean terminal commit with no post-commit edits. Disposition:
  record a clock-note erratum in the two-half close.
- **F-2 (LOW)** — FREEZE_R2 scope sentence uses an em-dash where the court
  machine used a hyphen-minus (1 glyph; otherwise identical). Pin one
  canonical string at close.
- **F-3 (LOW)** — `court_r2_machine` notes / HANDOFF_skp_r2 say "45 distinct
  family_id citations"; the true distinct union is 38 (45 = citation instances
  in class_verdicts, 5+8+3+6+23). The substantive claim (every cited id exists
  exactly once in the ledger) verified TRUE for all 38; correct the wording at
  close.
- **F-4 (LOW, inherent limit — not a defect)** — annotator "no panel loaded"
  is attestable only from artifacts (blind checklists signed on all 25 rows +
  no-panel rules); no independent byte-level proof is possible ex post.

## 3. Commands / evidence

```
git -C <worktree> rev-parse HEAD   # 03d685efedc111b38e1a2fd442665697dd2b58d5
researchctl.py cycle list | grep DTP   # ACTIVE_LIGHT 0/18 03d685e
shasum -a 256 <6 data files + 9 provenance pins>   # 15/15 MATCH
.venv/bin/python research/control/DTP-CX-SOLUSDT-C1/audits_a7/a7_recompute_court_r1.py
.venv/bin/python research/control/DTP-CX-SOLUSDT-C1/audits_a7/a7_recompute_datagate.py
```
Machine outputs: `audits_a7/a7_court_r1_recompute_machine@1.json`,
`audits_a7/a7_datagate_spot_machine@1.json`, and
`audits_a7/a7_terminal_machine@1.json` (per-section verdicts).

**Chưa có PnL nào được xem hoặc tính toán trong audit này.**
