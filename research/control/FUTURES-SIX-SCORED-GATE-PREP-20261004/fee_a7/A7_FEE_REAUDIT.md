# A7_FEE_REAUDIT — independent fee A7 audit execution (lane FEE-A7)

- Round: **FUTURES-SIX-SCORED-GATE-PREP-20261004**, lane FEE-A7 (independent audit execution).
- Run date: 2026-10-04. Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-gate/prep`,
  branch `prep/futures-six-gate-20261004`.
- Executed run-order: `research/control/FUTURES-SIX-ADOPT-PREP-20261004/fee_es/A7_EXECUTION_PACKET.md`
  steps 0–9 (read in full before work).
- **Verdict: AUTHORIZED_WITH_FINDINGS — 0 HIGH / 0 CRITICAL unresolved.** Audit only; no value
  fixed, no D-ruling made, nothing ratified, nothing scored.

## 0. Authorization basis + anchor (recorded, not re-litigated)

- **Authorization**: the owner's 2026-10-04 instruction to this thread lists "cost/fee A7" among
  the PREP items to resolve ("Giải các việc PREP được phép: dữ liệu, calendar, NQ cache_v3,
  cost/fee A7, PIT..."). The round `dispatch/DISPATCH_MANIFEST.json` (`interpretation_law`)
  records this as written authorization to EXECUTE the audit. It is **NOT** a D2/D3/e.1–e.4
  ruling — those remain owner signatures and are tabulated below as pending slots.
  NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER stand; PB2 HOLD; PB3 PARK; ES cap 24 FROZEN.
  Zero PnL by construction (document audit only). Zero network (all evidence committed captures).
- **Anchor**: `git -C <worktree> rev-parse HEAD` →
  `893db28cd1b3299c914369ec08cb33f68bf5798a` == dispatch `base_sha` (exact match, no drift).
- **Lineage note (drift vs packet pins)**: the executed packet was written in the sibling
  FUTURES-SIX-ADOPT-PREP-20261004 worktree at HEAD `9fb66c88`; its input hashes were recorded
  from the P3-quarantine sibling packet taken at `0225b3c2`. Per dispatch, no drift check
  against the packet's own worktree is performed — integrity is established by re-hashing the
  21 inputs in THIS worktree (step 1, below). The packet's P3-sibling readiness packet was NOT
  read (P3 worktree access is absolutely forbidden).

## 1. Step 1 — input integrity: 21/21 MATCH + 4/4 supporting MATCH (FACT)

All 21 §2 inputs under `research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/`
recomputed with `shasum -a 256` at HEAD 893db28c; every digest equals the packet's recorded
value (recorded from sibling packet §b at 0225b3c2; re-verified by FEE-ES at 9fb66c88).

| Layer | Files | Result |
|---|---|---|
| source/ (16) | archive_CME.php.html `0f726c52…`; archive_COMEX.php.html `8809dec0…`; archive_NYMEX.php.html `9031e0d9…`; archive_NYMEX.php.html.gz_raw `64ecfd22…`; archive_commissions-futures.php.html `6df03fd5…`; archive_commissions-futures.php.html.gz_raw `50a950c9…`; CME.php.txt `75a86470…`; COMEX.php.txt `4317c15a…`; NYMEX.php.txt `dbcc25b3…`; commissions-futures-amer.php.txt `14d79331…`; CME.php.md (quarantined) `469d8220…`; fees_corrected.json `7cd65f25…`; FEES_CORRECTED.md `006d6372…`; superscript_adjudication.md `e36a0123…`; fetch_log.jsonl `f370f305…`; MANIFEST.md `c8c8ff5a…` | 16/16 REHASHED_HERE_MATCH |
| impact/ (3) | FEE_ERRATUM_DRAFT.md `3796579d…`; validate_fee_sources.py `fdead766…`; GATE_REVIEW_NOTE.md `5d50ac79…` | 3/3 MATCH |
| verify/ (2) | P0_ERRATUM_VERDICT.md `6967a804…`; p0_verdict.json `f1e5b636…` | 2/2 MATCH |

Supporting pins (context, also re-hashed): `FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md`
`445f7499…` MATCH; `FUTURES-ES-V1-PACKET/audit/a7_spec/A7_SPEC.md` `0ce63a0d…` MATCH;
`…/a7_spec_checks.json` `ac334145…` MATCH; `FUTURES-ES-V1-PACKET/PLAN_futures_es_v1.md`
`06140882…` MATCH. **Total 25/25 MATCH — zero drift, zero STOP condition.**

## 2. Step 2 — per-cell source-text re-extraction (byte citations; RAW HTML authority)

All extractions reproduced in `fee_a7/reextraction_cells.txt` (this lane's own capture).
Classification per load-bearing cell; `*.php.txt` renders are tag-stripped glue-demonstration
exhibits, never value authority.

| # | Cell | Capture + line | Byte evidence | Class (corrected / parent value) |
|---|---|---|---|---|
| 1 | NQ exchange | archive_CME.php.html (RAW 2026-06-08) row L1691–1695 | row label L1691–1692 `E-mini Equity Futures` / `BQX, ER2, NQ, QCN, RS1, RSG, RSV, RTY, SPSOX, XAZ`; value cell L1694 `<td class="text-price">1.38<sup>6</sup></td>` | **LITERAL-marker-adjacent** (1.38 literal, marker 6 adjacent) / parent 1.386 = FOOTNOTE_GLUED |
| 2 | ES exchange | archive_CME.php.html row L1703–1707 | row label L1703–1704 `E-Mini S&P; Equity Futures` / `EMD, ES, SMC, SPXESUP, …`; value cell L1706 `1.38<sup>6</sup>` | **LITERAL-marker-adjacent** / parent 1.386 = FOOTNOTE_GLUED |
| 3 | Housing trap (negative check) | archive_CME.php.html L1655–1659 | `1.38<sup>` occurs **exactly 3×**: L1659 `1.38<sup>2</sup>` belongs to row `Housing Index / BOS, CHI, CUS, DEN, LAV, LAX, MIA, NYM, SDG, SFR, WDC` — **NOT attributed to ES/NQ** (sup-6 count = exactly 2) | trap correctly excluded |
| 4 | FX row 1.60 | archive_CME.php.html L1664–1673 | label L1665 `Forex Futures</strong><sup>9</sup>` (marker 9 ON LABEL); value cell L1668 `<td class="text-price">1.60</td>` CLEAN; aliases incl. EUR/GBP/JPY/AUD/6H, no verbatim 6E/6B/6J/6A | **LITERAL** (value); mapping PARTIAL by design |
| 5 | Footnote 6 text | archive_CME.php.html footnote `<ol>` L1903–1912 | ordered-list item 6 (L1909) = `Non-Member spread orders will be charged $1.30 per contract.`; item 9 (L1912) = `Exchange Fee is waived-off for 6H Futures.`; items 2–5 spread rates $1.30/$0.35/$0.14/$1.90 — coherent footnote family, not decimals | FACT (numbering independently re-counted) |
| 6 | CME reg, June epoch | archive_CME.php.html L1890 | `0.02<sup>1</sup><br/>(For IB-JP customers: 0.022 incl. tax)` | **LITERAL-marker-adjacent** (0.02, marker 1) |
| 7 | CME reg, live epoch | CME.php.txt (render) L97–98 | `0.011` + `(For IB-JP customers: 0.011 incl. tax)` — glued render; base token 0.01 destroyed by renderer | corrected 0.01 = **NOT_LOCATED in this render** (documented limitation; adjudicated by 3 independent signals: paren tax arithmetic, IBKR worked example, NYMEX/COMEX reg rows) / parent 0.011 = glued artifact |
| 8 | NYMEX CL row | archive_NYMEX.php.html (RAW 2026-09-25) L2543–2546 | `CL, HO, RB` → `USD 1.50 / USD 1.50 / USD 0.75`, no markers | **LITERAL** |
| 9 | NYMEX NG row | archive_NYMEX.php.html L2549–2552 | `NG` → `USD 1.60 / USD 0.90 / USD 0.80`, no markers | **LITERAL** |
| 10 | NYMEX reg All | archive_NYMEX.php.html L2712–2715 | `All` → `0.01 / 0.01 / 0.00` clean `<span class="text-price">` cells; **zero `<sup>` in L2690–2740** | **LITERAL** / parent 0.02 = NOT_LOCATED (parent contradicted; error-classification INFERENCE per erratum) |
| 11 | NYMEX options glue demo | archive_NYMEX.php.html L2650 + NYMEX.php.txt L41 | RAW `USD <span class="text-price">0.95</span><sup>4</sup>` renders glued `0.954` | in-vivo glue mechanism DEMONSTRATED (span-wrapped marker — validator wart (b) exhibit) |
| 12 | COMEX live GC/SI | COMEX.php.txt (live 2026-10-03) L21, L45, L39 | `GC, HG, SI \| USD 1.65 \| USD 0.75`; reg `All \| USD 0.01`; give-up `All \| USD 0.05` | **LITERAL** |
| 13 | COMEX March epoch | archive_COMEX.php.html (RAW 2026-03-10) L1132–1134, L1147–1150, L1152–1155, reg L1169/L1174/L1226 | `GC, HG, SI → 1.60/0.75`; `MGC → 0.60/0.20`; `QO, QI, QC → 1.00/0.50`; reg `0.02` | **LITERAL both epochs** → temporal changes GC/SI 1.60→1.65 and reg 0.02→0.01 are FACT |
| 14 | IBKR worked examples | archive_commissions-futures.php.html (RAW 2026-09-25) L4047–4057 | Tiered ES: `0.85 + 1.38 + 0.00 + 0.00 = USD 2.24` (printed sum; components 2.23 — stale reg cell); E7: `0.5 + 0.85 + 0.00 + 0.01 = USD 1.36` (exact); Fixed ES: `0.85 + 1.38 + 0.00 + 0.01 = USD 2.24` (exact) | **LITERAL** |
| 15 | Commission ladder | commissions-futures-amer.php.txt (live, ?re=amer) L23–26 + RAW identical | `<=1,000: 0.85; 1,001–10,000: 0.65; 10,001–20,000: 0.45; >20,000: 0.25`; Fixed 0.85; marginal volume across all futures | **LITERAL** |
| 16 | Live glued renders | CME.php.txt L52/L54/L56/L97–98 | NQ `1.386`, ES `1.386`, Micro `0.353`, reg `0.011` — exactly base+marker glued | glue-demonstration exhibits only |

## 3. Step 3 — independent arithmetic re-check (FACT; 40/40 PASS)

Full log `fee_a7/arithmetic_check.txt` (40 PASS / 0 FAIL):

- **Commission ladder deltas**: 0.85→0.65→0.45→0.25 = −0.20 per tier (T1→T2/T3/T4 = −0.20/−0.40/−0.60). All 10 codes' tier-2/3/4 all-ins reproduce: commission+exchange+reg with clearing 0.00 — ES/NQ 2.24/2.04/1.84/1.64; FX 2.46/2.26/2.06/1.86; CL 2.36/2.16/1.96/1.76; NG 2.46/2.26/2.06/1.86; GC/SI 2.51/2.31/2.11/1.91. Fixed == T1 for every code (0.85 both).
- **IBKR worked examples**: Fixed ES `0.85+1.38+0.00+0.01=2.24` EXACT; E7 `0.5+0.85+0.00+0.01=1.36` EXACT; Tiered ES components sum 2.23 vs printed 2.24 → **IBKR page-internal stale reg-0.00 cell characterized (+0.01 discrepancy), NOT inherited as a value** — the 0.01 reg is carried by the Fixed example + IB-JP paren + NYMEX/COMEX reg rows (3 independent signals).
- **IB-JP paren tax arithmetic**: live `0.011 = 0.01×1.1` EXACT; June `0.022 = 0.02×1.1` EXACT; counterfactual (base 0.011) would print 0.0121→0.012 ≠ 0.011 → bases are the un-glued values. Sibling parens: NIY `2.15×1.2=2.58` EXACT (glued 2.155→2.586≈2.59 mismatch), NIY-mini `1.28×1.2=1.536` EXACT.
- **SPEC §5 family**: as-published `0.85+1.386+0.02+6.25+{12.5,25,37.5}` = 21.006/33.506/46.006 EXACT (stale exchange); corrected-NFA 21.00/33.50/46.00; corrected-offset 20.99/33.49/45.99; A/B delta $0.01/side, $0.02/RT; window 2014-10-01→2017-12-31 shift = exchange delta −0.006 only (both bases agree at 0.01 there); divergence = 0.446% of the tier-1 fee cell.

## 4. Step 4 — validator real-mode reproduction (FACT)

Script: `impact/validate_fee_sources.py` (sha `fdead766…`, unchanged). Logs captured:
`fee_a7/validator_selftest.log`, `fee_a7/validator_realmode.log`; my report `fee_a7/a7_validator_report.json`.

- **Self-test: 6/6 PASS, exit 0** (LITERAL / FOOTNOTE_GLUED / NOT_LOCATED / marker-adjacency all asserted).
- **Real mode** vs `verify/p0_verify_expected.json` (37-check grid): **exit 1 — FAIL semantics, as expected** (the grid deliberately includes adverse parent-value checks). Outcome: **31 LITERAL / 2 FOOTNOTE_GLUED / 4 NOT_LOCATED** — per-check statuses **37/37 IDENTICAL** to the committed `p0_verify_validator_report.json`.
  - corrected values all LITERAL (incl. marker-adjacent 1.38 on both CME rows; worked-example 1.38/0.01/2.24 in RAW);
  - `1.386` → **FOOTNOTE_GLUED ×2** (base 1.38 + marker 6 on NQ and ES rows); `0.011` NOT_LOCATED (June RAW); NYMEX `0.02` NOT_LOCATED; `0.954` NOT_LOCATED; CME live base `0.01` NOT_LOCATED (renderer destroyed the token into the `0.011` artifact — the documented limitation; authority = §2 cell 7's three signals).
- **3 validator warts, all observed**: (a) argv parser treats `--expected`/`--report`/`--window` VALUES as capture paths — demonstrated live: first invocation with `--window 1` crashed `FileNotFoundError: '1'`; workaround (omit `--window`, default is 1; pre-create the `--report` file) mirrors the committed P0-VERIFY invocation; (b) glue classifier misses span-wrapped markers — `0.95</span><sup>4</sup>` yields NOT_LOCATED, not FOOTNOTE_GLUED (visible in my 0.954 check); (c) `CME.php.txt` flagged MARKERS_PRESENT spuriously (P0A annotation header L11 itself contains the literal `<sup>` string).
- No arithmetic-pass path exists in the tool (code read + self-test design).

## 5. Step 5 — propagation grep reproduction at 893db28c (FACT)

Canonical pattern (from FEE_ERRATUM_DRAFT §3):
`grep -rln -E "1\.386|2\.247|0\.011|2\.461|2\.37\b|2\.47\b"` over the three canonical rounds.
Raw output + classification: `fee_a7/propagation_grep.txt`.

- **26 files** — identical to the erratum's measured 26 (the DISPATCH_MANIFEST's "27" remains a
  clerical off-by-one, Lead-owned, retired as recorded).
- **1 false positive**: `…/events_bbo_coverage/coverage_remeasure.json` L1784
  `"ts_event_min_utc": "2025-04-01T00:00:00.011588+00:00"` (sub-second timestamp).
- **25 genuine = 22 FROZEN-HISTORICAL + 3 LIVING-DOC** (7 frozen ES-V1 / 3 frozen + 3 living
  DATAQUAL / 12 frozen DEEPFOUR), plus PLAYBOOKS_DRAFT.md as supplementary rounded-value living
  site (2.24 tokens only; not in pattern) — per-file classification verified against
  FEE_ERRATUM_DRAFT §3.
- **New-site sweep** (same pattern over ALL of `research/control/`, excluding the 3 canonical
  rounds and this lane's own dir): every hit classified by line-level sampling as
  **ERRATUM-SELFREF** (erratum/adopt/readiness-round documents quoting the retired values AS
  retired or UNDER-REVIEW: fees_erratum/**, OVERNIGHT dispatch handoffs + synth/REPORT_VI.md
  L26/L34, ADOPT fee_es packets + handoff_FEE-ES, READINESS es_fee_status.json /
  verify_fee_and_census.py / fee_a7_status.json) or **FALSE POSITIVE** (trade prices
  19801.386, PnL floats −312.247/+274,572.47/−84,732.37, timestamps 0.011588, statistics
  std_daily_logret 0.011841 / spread 0.011 USD/MMBtu / fwd_maxdd −2.37/−2.47, SVG path
  coordinates, log tails). **Zero NEW genuine fee-value sites outside the erratum rounds.**

## 6. Step 6 — frozen-vs-living integrity (FACT)

One permitted read-only git call: `git -C <worktree> show --stat 72c9bc5b` (output:
`fee_a7/batch1_commit_stat.txt`).

- Summary line: **"359 files changed, 246390 insertions(+)"** — no deletions component ⇒
  **zero tracked files modified or removed** (pure additions).
- All 359 stat rows parsed; each abbreviated path (leading `...` stripped, endswith match)
  resolves against the worktree tree: **359/359 land under
  `research/control/FUTURES-OVERNIGHT-PREP-20261003/`** (fees_erratum/** + bls_vintage/** +
  cme_cal_gap/fxcomm calendar captures + dispatch handoffs). **Zero rows** reference
  FUTURES-ES-V1-PACKET, FUTURES-DATACONTRACT-QUAL-V1, or
  FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 ⇒ **no frozen-historical file was touched** by the
  erratum batch-1 commit. (The full 40-hex sha `72c9bc5b1d94b812044a9bd21768c53b4d378436` is
  confirmed from the same output's commit line; no additional git log call needed.)
- Worktree round dir now holds 398 files (359 batch-1 + 39 later verify-lane additions) — consistent.
- Combined with step 1 (21/21 inputs byte-identical to pins taken at 0225b3c2/9fb66c88):
  **FROZEN-INTEGRITY: PASS.**

## 7. Step 7 — "no-measured-cost" language scan (FACT)

Log: `fee_a7/language_scan.txt`. Scope: fees_erratum/**, DEEPFOUR fees/**, DATAQUAL round,
SPEC_PB1_ES.md, OVERNIGHT synth/REPORT_VI.md, READINESS es_fee_status.json, ADOPT
CYCLE_LAUNCH_DRAFT.md.

- Forbidden language: every `measured cost` / `complete cost` occurrence is a **negation or
  prohibition** ("Nothing is a measured cost from any account", "KHÔNG PHẢI MEASURED COST",
  "CẤM dùng chữ complete-cost/measured-cost", "No words 'measured cost' may appear",
  "'measured cost'/'complete cost' forbidden (0 positive uses…)"). **Zero positive uses.**
- Required labels present: `MODELED_COST` in all 12 fee-value-bearing files;
  `VERIFIED_VS_ACCOUNT=NOT_RUN` in 14 files including every fee table
  (fees_corrected.json, fees_table_all.json, fees_table_es.json, FEES_BY_CODE.md,
  FEES_CORRECTED.md, GATE_REVIEW_NOTE.md, OWNER_DECISION_PACKET.md, es_fee_status.json, …).

## 8. Step 8 — SPEC_PB1_ES under-review consistency adjudication

**Byte-verification (FACT)**: the stale §5 lines print byte-identically at 893db28c —
L100 `| Exchange (CME) | 1.386 | public LIVE_OFFICIAL (IBKR CME.php offset table); …`;
L101 `| Regulatory (NFA) | **0.02** (mặc định); **0.01** cho 2014-10-01→2017-12-31 | … IBKR offset 0.011 KHÔNG dùng, KHÔNG cộng kèm …`;
L104 `| **All-in/side (mặc định NFA 0.02)** | **S1 21.006 · S2 33.506 · S3 46.006** | …`.
Both `GATE_REVIEW_NOTE.md` §1 and `FEE_ERRATUM_DRAFT.md` §4 (LAW 2–4) record exactly these
lines as **UNDER REVIEW**; P1 families consume `fees_corrected.json`. Consistency: CONSISTENT
(no doc claims the SPEC was edited; nothing edits the frozen spec in this round either).

**Ruling e.4 (= D3) is UNRULED — owner slot. Both variants tabulated (NOT chosen):**

| | Variant A — NFA basis (SPEC law) | Variant B — IBKR offset basis |
|---|---|---|
| Regulatory component | 0.02 default; 0.01 only in window 2014-10-01→2017-12-31 | 0.01 throughout (current capture epoch) |
| Fee all-in/side (corrected exchange 1.38) | 0.85+1.38+**0.02** = **2.25** | 0.85+1.38+**0.01** = **2.24** |
| ES all-in/side S1/S2/S3 (+6.25 spread, +12.5/25/37.5 slippage) | **21.00 / 33.50 / 46.00** | **20.99 / 33.49 / 45.99** |
| ES round-trip S1/S2/S3 | 42.00 / 67.00 / 92.00 | 41.98 / 66.98 / 91.98 |
| NQ all-in/side S1/S2/S3 (spread/slippage per NQ cell) | 23.50 / 28.50 / 33.50 | 23.49 / 28.49 / 33.49 |
| As-published SPEC print (stale 1.386) | 21.006 / 33.506 / 46.006 (RT 42.012/67.012/92.012) | — |
| Delta | — | −$0.01/side = −$0.02/RT (0.446% of fee cell; ≤0.048% of tier RT cost) |
| Basis law | SPEC §5 L101 single-source NFA timeline; both bases agree at 0.01 inside the window | matches corrected IBKR capture + family composition (53 value sites); requires dated owner annotation reversing SPEC L101 |
| Status | **UNRULED — owner signature required; this lane does not pick.** Per D3_QUANT_SHEET §5 fail-closed default: while undecided, both bases coexist and no cost gate may consume either number. |

## 9. Findings ledger

Typed FACT / INFERENCE / NOT_RUN. **Missing evidence is NOT_RUN, never inferred PASS.**

| id | type | finding | severity |
|---|---|---|---|
| F-01 | FACT | Input integrity 25/25 MATCH (21 §2 inputs + 4 supporting pins); zero drift at 893db28c | — |
| F-02 | FACT | Glue mechanism byte-confirmed: `1.38<sup>6</sup>` exactly ×2 (NQ L1694, ES L1706); Housing L1659 `1.38<sup>2</sup>` correctly excluded; footnote 6 = $1.30 spread note (item numbering re-counted from the ordered list) | — |
| F-03 | FACT | Parent values fail source location: 1.386 FOOTNOTE_GLUED ×2; 0.011 / NYMEX 0.02 / 0.954 NOT_LOCATED (validator, 37/37 grid reproduced) | — |
| F-04 | FACT | Corrected table arithmetic-exact (40/40); worked examples exact except IBKR's own Tiered stale reg cell (+0.01, characterized, not inherited) | — |
| F-05 | FACT | Propagation 26 files = 25 genuine (22 frozen + 3 living) + 1 FP; zero new genuine sites repo-wide | — |
| F-06 | FACT | Batch-1 `72c9bc5b`: 359 files, insertions-only, 359/359 paths inside the erratum round dir; frozen files untouched | — |
| F-07 | FACT | Language law holds: 0 positive "measured cost" uses; MODELED_COST / VERIFIED_VS_ACCOUNT=NOT_RUN labels present throughout | — |
| F-08 | FACT | SPEC stale lines L100/L101/L104 byte-identical to the UNDER-REVIEW records; nothing edited | — |
| F-09 | INFERENCE | NYMEX parent-0.02 = extraction error (live + 2026-09-25 RAW both 0.01; 0.01→0.02→0.01 flip in ≤2.5h implausible, not physically excludable from this machine) — inherited classification, unchanged | LOW |
| F-10 | NOT_RUN | VERIFIED_VS_ACCOUNT on every fee value (all MODELED_COST public-reference); owner account verification untouched | binding gap |
| F-11 | NOT_RUN | Overnight Position Fee tables (JS-driven, never render); FX verbatim 6E/6B/6J/6A (alias mapping PARTIAL); parent quote "charged by all IBKR entities" (0 archive hits — do not cite); live re-fetch (transport BLOCKED, zero attempts by this lane) | carried |
| F-12 | INFERENCE (residual) | CME live-epoch reg 0.01 rests on 3 independent signals — no post-June-08 RAW CME.php capture exists (live raw transport blocked); documented residual, unchanged from P0-VERIFY | LOW |
| F-13 | INFO | Validator wart (a) demonstrated live (`--window 1` → `FileNotFoundError: '1'`); workaround = omit `--window` (default 1) + pre-create `--report` target; 37/37 outcomes unaffected | LOW |
| F-14 | INFO | DISPATCH_MANIFEST "27 files" vs measured 26 — clerical off-by-one stands as recorded (Lead-owned manifest) | LOW |
| F-15 | INFO | Incidents this lane: (1) propagation sweep self-grep initially appended its own output (302 MB) inside this lane's writable dir; rebuilt cleanly at ~15 KB; no file outside `fee_a7/**` + handoff touched, git tree unaffected; (2) first validator invocation crashed on wart (a) as above. Both recorded in handoff `incidents`. | LOW |

**Unresolved HIGH/CRITICAL: 0.** Blocking-for-scoring items remain the standing owner slots, not
audit defects.

## 10. Pending owner-slot table (recorded, NOT decided here)

| slot | question | status |
|---|---|---|
| D2 | Ratify erratum consumption / corrected-fee basis downstream | PENDING (owner) |
| D3 (= e.4) | Reg-component basis for modeled all-ins: NFA 0.02 vs IBKR offset 0.01 | **UNRULED — both variants tabulated §8; owner signature required** |
| e.1 | FX-group fee mapping corroboration (accept PARTIAL: CME alias row, 1.60 confirmed; 6E/6B/6J/6A never verbatim) | PENDING (owner) |
| e.2 | Account-geography basis for the IB-JP paren (0.011 = 0.01×1.1 tax artifact; US-entity pages operative) | PENDING (owner) |
| e.3 | NYMEX reg 0.02→0.01 temporal window / epoch-binding rule for historical-year modeling | PENDING (owner) |
| PB2 / PB3 | Lift instruments only; HOLD/PARK remain | PENDING (owner) |
| caps | ES 24 FROZEN; any raise = owner-signed option with disclosed arithmetic | PENDING (owner) |
| GO | No typed GO exists; NO_GO_SCORE stands | PENDING (owner) |

## 11. R2 non-inheritance statement

The parent A7's R2 verdict ("recomputed exact", `a7_spec_checks.json` L47) was
arithmetic-consistency-of-the-transcribed-table — a blind spot: it never asserted source-text
verification. **This audit does not inherit that language.** Its own arithmetic re-check
(step 3) is likewise arithmetic-only and is **never used as a source-value pass**: source
values are established independently by (a) step-2 byte re-extraction in marker-preserving RAW
HTML with row-label scoping, and (b) step-4 source-location validation (LITERAL /
FOOTNOTE_GLUED / NOT_LOCATED; internal arithmetic is a hard-non-pass in the tool by
construction). No verdict in this document says "exact" about any fee value except in the
arithmetic-consistency sense explicitly scoped to a named table.

## 12. Git commands run (complete list)

1. `git -C <worktree> rev-parse HEAD` → `893db28cd1b3299c914369ec08cb33f68bf5798a`
2. `git -C <worktree> status --porcelain` (start) → only untracked `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/`
3. `git -C <worktree> show --stat 72c9bc5b` (step 6, permitted)
4. `git -C <worktree> status --porcelain` (end, in handoff `tree_status`)

No staging, no commit, no push, no other git.

— End A7_FEE_REAUDIT.md. This lane audits only; it fixes no value, rules no D-ruling, ratifies nothing.
