# CROSSCHECK REPORT — FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 / lane VERIFY

Generated 2026-10-03 UTC. Independent cross-check of 7 sibling-lane handoffs. All work
read-only except `verify/**` and `dispatch/handoff_VERIFY.json`.

## 0. Environment re-measure

- Worktree HEAD re-measured: `7149425df83b7c47f34848fc83d36e450b802bc5` == dispatch sha == all
  7 handoffs' dispatch_sha/actual_start_sha. No drift; sibling lanes committed nothing.
- `git status --porcelain`: **zero tracked-file modifications**; one untracked root
  `research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/`; nothing outside it.
- Heavy lock: not taken (FREE_PROVEN respected).

## 1. Per-lane verdict table

| Lane | Verdict | sha256 pins | What VERIFY recomputed independently |
|---|---|---|---|
| A1-CMECAL-NQES | **VERIFIED** | 5/5 MATCH | holidays 17/17; NQ exp 68/68 = 36 product + 32 family; 3rd-Friday arithmetic on all 68 dates (67 conform; 2026-06-18 = documented Juneteenth shift of Jun 19); ES 63/68 = 37+26 with 5 NOT_OBTAINED; fetch-log spot-checks pass (F-5 note on inherited 2011 D3 URL) |
| A2-CMECAL-FX | **PARTIAL** | 3/3 MATCH | flat list 96 rows; rule check 96/96 reproduced (all dates == Mon-before-3rd-Wed / fallback); verbatim rule quote + 2012-era capture URLs x4 + 2023 confirmation present; **but per-symbol split wrong: 6E rows = 17, claimed 18 (F-1)**; handoff REFUSED-as-submitted on authority_claims (F-2) |
| A3-CMECAL-COMM | **PARTIAL** | 12/12 MATCH | CL 183 distinct rows (75+108, 0 overlap), NG 240 (120+120), GC 22, SI 20; ranges Apr2010..Feb2027 / Jun2010..Feb2027 / Aug2013..Jun2019 / Mar2015..Dec2019; 4 rule quotes verbatim x2 eras + URLs; SI 12:25 vs GC 12:30 offset sourced; handoff REFUSED-as-submitted on authority_claims (F-2); tests/changed_paths empty (F-3/F-4) |
| A4-FEES | **VERIFIED** | 4/4 MATCH | 45/45 ALL_IN rows = commission+exchange+regulatory exact (NQ 2.247=0.85+1.386+0.011; FX 2.461=0.85+1.60+0.011; CL 2.37; NG 2.47; GC/SI 2.51; tier ladder); label law on all 108 rows (SOURCE=PUBLIC_REFERENCE, VERIFIED_VS_ACCOUNT=NOT_RUN); FX alias-mapping PARTIAL corroboration honestly recorded in fx_mapping_note |
| A5-EVENTS-BBO-COVERAGE | **VERIFIED** | 7/7 MATCH | CPI 204 + EMPSIT 204 (17y x 12, all 08:30); both anomalies verbatim with explicit no-cause-claims; staleness 0.825–0.891d over 1,160 files, 2 symbols recomputed exactly from max mtime vs 2026-10-03T00:00Z; BBO doc states bbo-1m cannot prove intrabar fill/queue (F-6 note: log timestamps reconstructed, disclosed) |
| B1-DEEP-ESNQ | **VERIFIED** | 3/3 MATCH | both addenda exactly 12 numbered sections; 26/26 evidence_index artifacts exist with sha256 pin MATCH; ≥10 headline numbers reproduced (rolls 66; FOMC 132/91/40; var_on 20.9–53.8 by year; sessions 4204; decl_thin median 9.0; sign 61/66; NQ 4219 / acf1 −0.076 / VR .81/.71/.67; NQ2020 +13.20→+38.43); acf1 adjudication below |
| B2-DEEP-6E6B | **VERIFIED** | 4/4 MATCH | court draft sections (a)–(d) present; renders explicit "NO reopening verdict. PB2 remains HOLD"; ≥6 citations verified at source (27/27; 0.8423; 0.9097 vs −0.107 PIT; thin window 1,069..13,222; FOMC ×17.2 = m780 17.2418); MDE table 2.80σ/√n reproduced all 12 cells ≤0.01bp; costs 3.33–5.87 / 5.78–10.42 reproduce quoted 3.3–5.9 / 5.8–10.4; evaluable sessions 1,746−60−113/114 = 1,573/1,572 exact |

## 2. Findings (numbered, with severity)

- **F-1 MAJOR — A2 per-symbol coverage internally inconsistent.** Machine rows say
  6E = **17** quarters (per_symbol_by_year: 4+2+3+4+4; flat list EC codes = 17; Mar-2012
  / ECH12 absent), and the flat list totals 96. But the JSON summary dict, the evidence
  MD ("6E … 18 quarters … 2012 all 4 (Mar 19, Jun 18, Sep 17, Dec 17)"), and the handoff
  verdict ("6E 18/68") all say 18 — and 18+31+13+35 = **97**, contradicting their own
  "96/272". The handoff's own limitation ("6E lacks … Mar 2012") matches the 17-row data
  and contradicts its own verdict. Fix: amend to 6E 17/68 everywhere (total stays 96), or
  add a genuinely sourced ECH12 row and change 96→97 everywhere. One of the two must move.
- **F-2 MAJOR — A2 & A3 handoffs REFUSED as submitted** (dispatch rule:
  authority_claims must be `[]`; A2 has 6 entries, A3 has 7). The entries are evidence
  claims misplaced into the wrong field, **not** governance-authority usurpation (no
  registry/gate/scoring claims). Mechanical amendment (move to summary/limitations)
  required before integration; content verification was still performed and is reported.
- **F-3 MINOR — tests[] shape.** Only A1 uses command/exit_code/verdict. A2/A5 use
  name/command/result; A4 embeds "PASS (exit 0)" in a string; B1/B2 use name/result/detail;
  A3 has `tests: []` entirely.
- **F-4 MINOR — changed_paths hygiene.** A3/B1/B2 declare `[]` despite non-empty outputs;
  A4 appends " (new, untracked)" inside path strings (prefix still glob-resolves).
- **F-5 NOTE — A1.** Holiday-2011 evidence URL absent from this session's fetch_log:
  inherited D3 transcription, marked `reverified_first_hand: false` + "(D3 transcription)"
  in the artifacts — disclosed, not fabricated. Re-fetched items (2010 PDF, 2026 live) are
  in the log.
- **F-6 NOTE — A5.** fetch_log timestamps are session reconstructions
  (`utc_reconstructed=true`), disclosed.
- **F-7 NOTE — A2 incident.** `pip install xlrd` into the **shared venv** — an environment
  write outside the lane boundary (not a repo write), honestly disclosed.
- **F-8 NOTE — dispatch-vs-artifact.** The VERIFY packet's "ECB 17.2x" is loose: ×17.2 is
  the **FOMC** statement-minute multiplier (JSON `m780 = 17.2418`); the dossier explicitly
  states ECB is ×1.7. Artifacts are internally correct.
- **F-9 NOTE — ES dossier erratum (adjudication).** See §3.

## 3. ES acf1 5/7-vs-6/7 adjudication

Read directly: `research/control/FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/ES_DEEP_v2.md`
(line 77 prose; section-2 era table) and `analysis/ES_regime_stats.json`.

- JSON era acf1_daily: −0.1091, **+0.0144**, −0.0652, −0.0380, −0.2432, **+0.0034**, −0.0885
  → negative in **5 of 7** eras (positives E2, E6).
- The dossier's own era table shows the same seven values (−0.109, +0.014, −0.065, −0.038,
  −0.243, +0.003, −0.088) → 5/7.
- The prose ("negative in 6/7 eras") is **wrong**; **5/7 is correct**. B1's addendum uses
  5/7, cites E2 +0.0144 / E6 +0.0034 (matches JSON under the table's 1-indexed labels), and
  disclosed the discrepancy without editing it — correct handling; the erratum belongs to
  the dossier-owning lane (F-9).

## 4. Cross-lane consistency

- B1/B2 recorded in-flight A-lane results as REQUIREMENTS only (disclosed, not consumed) —
  no contradiction with the landed A1/A2/A4 results. With A4 landed: NQ cost gate decidable
  (all-in 2.247 tier-1); B2's court fee layer fillable (6E/6B offset 1.60/side ≈ 0.23–0.25bp
  RT on the court's notional basis — does not overturn the "futures not cheaper" reading).
- Calendar source-class vocabulary LIVE_OFFICIAL / ARCHIVED_OFFICIAL(/_PRODUCT/_FAMILY) /
  NOT_OBTAINED consistent across A1/A2/A3; A4's PUBLIC_REFERENCE consistent in the fee domain.
- A1's family-wording authority rule consistent with A2's FX-family blocks and A3's PDF use.
- No lane claims a qualification upgrade (A3's explicit non-claim verified present).
- Forbidden-language scan: 6 hits, **all** explicit negations/laws; zero positive uses of
  "measured cost"/"complete cost". Taxonomy census: every lane tags claims
  (FACT/OBSERVED/POSTULATED/NOT_RUN/NOT_OBTAINED/PROVISIONAL) with citations; bare-PASS
  scan clean (hits are law statements or sourced prior-run references).

## 5. Overall integration recommendation

**INTEGRATE after amendments.** Zero CRITICAL findings: no inferred-PASS, no fabricated
URL (one inherited-D3 URL absence explained and disclosed, F-5), no account-fee evidence
(every A4 row PUBLIC_REFERENCE + VERIFIED_VS_ACCOUNT=NOT_RUN). Before folding into
DATACONTRACT_QUALIFICATION: (1) A2 fixes F-1 (6E 17-vs-18; 96 vs 97 cannot coexist);
(2) A2 + A3 clear `authority_claims` (F-2); (3) optional cosmetics F-3/F-4 at Lead's
discretion. All other content — fees arithmetic, calendar counts/ranges/rules, BLS counts,
dossier citations, court MDE/cost arithmetic — reproduces exactly under independent
recompute.

Recompute scripts kept (all exit 0 except the F-1 detector by design):
`verify/recompute_A4_fees.py`, `verify/recompute_A1_coverage.py` (exit 1 only if
fetch-log spot-checks fail; 2011 inherited-D3 case excluded per F-5 disclosure — see
script output), `verify/recompute_A2_fx.py` (exit 2 = F-1 discrepancy detector, by design),
`verify/recompute_A3_comm.py`, `verify/recompute_A5_events.py`, `verify/recompute_B1_citations.py`,
`verify/recompute_B2_court.py`. Machine-readable findings: `verify/verify_findings.json`.
