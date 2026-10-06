# VERIFY_REPORT_R3 — FUTURES-TEN-HYPO-PREP-20261004

- Verifier: lane VERIFY, fresh-context independent audit. Audit only — nothing repaired, nothing ruled, nothing ratified.
- Start HEAD: `55408ceb98694c8a37a5850ad389b3c58d144d6b` (wave-2), branch `prep/futures-ten-hypo-20261004`. Status at start: clean.
- Waves audited: wave-1 `b7f274a4` (6 lane outputs + dispatch manifest), wave-2 `55408ceb` (synthesis + SUMS corrections).
- Method: bytes only. Every claim below was recomputed from files on disk (and committed blobs where stated); lane JSONs treated as claims, never evidence. Zero network.

## Round verdict

**6/6 lanes + synthesis VERIFIED** — 0 CRITICAL, 0 MAJOR, 6 MINOR, 6 NOTE. All load-bearing novelty verdicts reconcile against `research/wayfinder/FAMILY_FAILURES.jsonl` (173/173 rows, 0 mapping mismatches). All 53 capture/hash rows recompute byte-exact. Zero-PnL / zero-registration language law holds across every round artifact.

## A. Zero-PnL / language law

| Check | Method | Result |
|---|---|---|
| A1 positive return/PnL patterns (11 regexes incl. `expectancy [><=]`, `hit rate`, `%win`, `expected return`, `sharpe`, `profit factor`, `CAGR`, `\bPnL\b`, `profitable`, `edge exists`, `GO granted`) over all round .md/.json | python re-scan, per-line | **PASS.** Every `\bPnL\b` hit (≈40) is a negation/disclosure ("0 PnL", "no PnL claim", "Zero-PnL law", "killed before any PnL") or dead-corpus ancestry citation. No hit for expectancy-comparison, hit rate, %win, expected return, profit factor, CAGR, "edge exists", "GO granted". `sharpe` hits are the word "sharpened" (false positive — NOTE N3). |
| A1 residual context reads | manual | cross/CENSUS_DELTA.md:15 "with its own PnL path" = definitional restatement of the census-unit convention citing CENSUS_FINAL (NOTE N1). cross/ANCESTRY_COURT_INFRA.md:37-38 "killed before any PnL" = veto-class description. |
| A2 "measured cost"/"complete cost" | re-scan | **PASS with NOTE.** All hits except two are prohibition statements ("FORBIDDEN", "forbidden words"). Residual: cross/ANCESTRY_COURT_INFRA.md:133 and cross/hypotheses_cross.json:1146 use the phrase inside the dead-row rejection-mode class DECLARED_BAND_BELOW_MEASURED_COST and its binding criterion "declared band ≥ measured cost" — dead-corpus taxonomy citation, not a cost-measurement claim (NOTE N2). |
| A3 trial-registration language | re-scan for mint formats + registration claims | **PASS.** No trial-id minting anywhere. "0 identities" / "no registration" / "no trial creation" pervasive and consistent; [PROVISIONAL] discipline stated in every lane. Nothing registered. |

## B. Handoff schema (6 handoffs in dispatch/)

| Check | Method | Result |
|---|---|---|
| B1 parse + schema + core fields | json.load + key check | **5/6 PASS.** All parse; all schema == `zcode_orch_v3_handoff@1`; all core fields present EXCEPT **handoff_COMM-EN.json has no `outputs` key** (uses `deliverables` instead) — **MINOR M1a**. |
| B2 actual_start_sha bare 40-hex == a4a882658e09092b5b282b666b30a3cfc5ac3418 | repr() check | **PASS 6/6** — all bare, all equal. |
| B3 dispatch_sha == a4a88265… | repr() check | **5/6 PASS.** handoff_COMM-EN.json dispatch_sha = `"a4a882658e09092b5b282b666b30a3cfc5ac3418 (dispatch base_sha; == measured HEAD)"` — bare sha correct but prose appended in the sha field (round-2 M1 lesson pattern) — **MINOR M1b**. |

## C. Hash / capture verification (recomputed, never trusted)

| Check | Method | Result |
|---|---|---|
| C1 lane SUMS recompute | sha256 every row, resolve lane-relative / repo-relative / `~` paths | **PASS 53/53.** fx_eb 4/4, fx_ja 2/2, comm_metal 14/14 (all `captures/`-relative), comm_energy 33/33 (9 lane captures + 9 repo-relative + 15 home rows). 0 mismatch, 0 missing. NOTE N6: one home row uses `~/my-quantitative-data/...` (no dot) vs `~/.my-quantitative-data/...` on the other 14 — both resolve, hashes verified. |
| C2 comm_energy correction block | read SUMS header + rehash 9 rewritten rows + `git cat-file blob a4a88265:<path>` for each | **PASS.** Correction block present and explicit (P3 worktree never accessed; paths rewritten, hashes unchanged). 9/9 rewritten rows hash-match on disk AND their committed blobs at base a4a88265 carry exactly the recorded hashes (9/9 byte-identical). Controller statement verified TRUE against the baseline register: all 24 register hashes appear verbatim in the SUMS; exactly 9 register rows name the P3 worktree path. |
| C3 fetch_log per lane | parse every line; required keys; histogram per (url,method); status/tool census | **Counts PASS** (es_nq 5, fx_eb 11, fx_ja 5, comm_energy 20, comm_metal 28 — all MATCH, all ≤30). All lines parse. comm_energy 4×403 marked BLOCKED_TRANSPORT/"No bypass"; fx_eb TIMEOUT + web_search rows status null (non-HTTP ops); comm_metal connect-failures status 0 noted egress-filtered + 429 marked; no bypass patterns (no x-forwarded/spoof/origin-forgery). **Three MINOR findings:** M2 es_nq 3 attempts on one (url,method) pair (cboe SPX page GET ×3: 2× webReader then 1× WebFetch; lane note claims "different tool/method" but method is identical; cap then honored, 0 bytes) — and SOURCE_INVENTORY §4's "≤ 2 per (url,method)" aggregate claim is therefore inaccurate; M3 comm_metal rows use `ts_utc` (date-only) + `seq` instead of the `ts` ISO timestamp every other lane uses; M4 comm_metal row 28 save_path `captures/nt_gold_specs_archive_429.html` ≠ on-disk `nt_gold_specs_archive.html` (same 620-byte Wayback 429 block page; disk name is the one pinned in SUMS; filename misleading but lane rests no fact on it — fineness stays NOT_IN_ANY_CAPTURED_SPEC). |
| C4 cross zero-network | filesystem + handoff/json disclosure grep | **PASS.** No fetch_log under cross/. Disclosure present: handoff_CROSS.json ("zero-network") and hypotheses_cross.json `"network": "zero-network lane (disclosed)"`. |

## D. Ancestry-claim spot-checks vs research/wayfinder/FAMILY_FAILURES.jsonl (173 rows)

| Check | Method | Result |
|---|---|---|
| D1 ESNQ-F5 EXPWITCH NO_VETO | grep cited ids; asset census over whole ledger | **PASS.** XSECT-VOLSHK-S15 exists (ledger line 4, crypto, SELECTION_REJECTION); CNG1-A5-P2 exists (line 79, SELECTION_REJECTION, primary ANCESTRY_RHO_BLOCK, title "monthly post-options-expiry unwind…" — matches lane description verbatim). "No prior scored equity-index-futures ancestor": ledger asset histogram = crypto 78, stocks 36, forex 41, sprint 6, rates 3, vol 6, commodities 3 — **zero equity-index rows**; the ES1-* ids (lines 121-122) are crypto families (cycle BTC-H4-*, asset crypto), not ES futures. Claim holds. |
| D2 COMM-EN COT veto | grep COMMNG1-A4-P2 | **PASS.** Exactly 3 ledger rows (lines 107-109: ARM1-NEUTRAL / ARM2-TAILWIDE / ARM3-WINDOWSHORT), all SCORED_REJECTION with primary code **CONTROL_OUT_EARNS_RELEASE_CLOCK** (actual value quoted; detail: "the bare release-clock control … out-earned every anchor after costs"). Lane cites "106/107/108" = 0-indexed positions of those same rows (NOTE N5: cross lane uses 1-indexed ids; family ids cited alongside make it unambiguous). |
| D3 FXEB fix-certainty veto | grep both ids + binding-RC language | **PASS.** TRACKA2-P4A-FIXCERT-01 (line 132): SELECTION_REJECTION, DECLARED_BAND_BELOW_MEASURED_COST, secondary REOPENING_CONDITION "owner amendment with a NEW economic basis (cheaper measured execution or larger evidenced premium); parameter re-tunes are barred". DTPFX1-A1-MEFIX-VARIANT (line 140): VARIANT_SAME_FAMILY, detail contains "FIXCERT RC is binding: 'owner amendment with a NEW economic basis (cheaper measured execution or larger evidenced premium)…'" — the binding-RC language is in the dead row exactly as the lane claims. FXEB quotes match verbatim. |
| D4 CROSS court infra | re-count ledger; rebuild cluster partition from hypotheses_cross.json; per-row code diff vs ledger; mode-table arithmetic | **PASS.** Ledger = 173 rows. 16 clusters, sum n_rows = 173, 173 distinct row ids (1..173), each row in exactly one cluster; cross row-id → ledger file-line mapping verified 173/173 (0 mismatches); per-row primary_code matches ledger primary_failure.code 173/173 (0 mismatches). Rejection-mode partition recomputed: EXP_FLOOR 69 + ANCESTRY_VARIANT 37 + CONTROL 25 + CONCENTRATION 15 + COST_CEILING 10 + DATA_ACCESS 7 + LEDGER_UNKNOWN 5 + DEV_GATE 2 + PIT_METHOD 2 + HOLDOUT 1 = **173** — every per-code count in ANCESTRY_COURT_INFRA.md §1 matches my histogram exactly. |

## E. Synthesis-consistency checks

| Check | Method | Result |
|---|---|---|
| E1 census dims + deltas | extract dims/identities from each lane JSON, diff vs synth table | **PASS exact.** ESNQ-F5 2/2/2/3/2=11 (json `dims` identical; minimal_total_per_leg 7, full 12/leg); CL-F3 1/2/2/2/1=8, minimal 11 / full 24; CLNG-F4 1/2/2/2/1=8, minimal 22 / full 48; R3-F1 1/3/2/2/1=9 (`d_scores_provisional` identical), minimal 11 / full 24; R3-F2 1/2/2/2/1=8, minimal 7 / full 12. COMM delta 11+22+11+7 = **+51**; 54 → 105 (comm_metal json census_standing: 54+18=72 for GC/SI; comm_energy legs 33; 72+33=105 consistent). |
| E2 ranking consistency | diff synth §1-§3 vs cross/RANKING_AGGREGATION.md; grep FXJA lane for divergence values | **PASS with MINOR.** Rows 1-8 + ESNQ-F5 inserted at 9 match RANKING_AGG values exactly ((3,3,2,3,1) AF3 … (2,3,2,3,1) RMM 11). SCORED_LEGAL_NOW = none, stated in both. FXJA divergence disclosed (synth §3.1) and verified in fx_ja json: JF3/AF3 re-scored (3,2,2,3,1)=11 with D2=2 dead-corpus clause, baseline kept authoritative. **MINOR M5:** the combined-view omits 4 carried rows — JF1 6J (11) and FX-F4 6E (11) appear neither in the "≥11" table nor the tail; ES-F3 (10) and AF1 (10) are absent from the "full carried tail (10 and below)" parenthetical, which is therefore not full. All values that ARE cited are exact; RANKING_AGGREGATION.md itself is complete. |
| E3 source inventory | diff claimed counts vs disk + my C1 recompute | **PASS.** 9+14+4+2 = 29 capture files match disk exactly (filenames listed match). "comm_energy 33/33, comm_metal 14/14, fx_eb 4/4, fx_ja 2/2, es_nq 0 captures" — all verified. §4 "each ≤30, ≤2 per (url,method)" — the ≤30 half verified; the ≤2 half contradicted by es_nq (see M2). |
| E4 owner decision packet | read | **PASS.** OD-1..OD-4 are decision REQUESTS with slots empty and explicit fail-closed defaults; "NOT A RULING. NOT AUTHORIZATION"; D1-D12 restated open; no self-ratification, no typed GO. (NOTE N4: §1 hash-row shorthand "33+24+14+4+2" is ambiguous — 33 already includes the 24 comm_energy baseline rows; the second 24 is comm_metal's separate 24-row register. Ambiguous writing, not an arithmetic error.) |

## F. Write-boundary / hygiene

| Check | Method | Result |
|---|---|---|
| F1 end-state git status | `git status --porcelain` at end | **PASS** — only `research/control/FUTURES-TEN-HYPO-PREP-20261004/verify/**` + `dispatch/handoff_VERIFY.json` (untracked round dir), nothing else. (Start status was clean.) |
| F2 round-dir inventory | walk round dir | **PASS.** Every file belongs to an adopted lane dir (es_nq, fx_eb, fx_ja, comm_energy, comm_metal, cross, synth, dispatch) or is REPORT_VI.md / dispatch/DISPATCH_MANIFEST.json. No strays. es_nq/captures is an intentionally empty (untracked) dir, declared in handoff_ESNQ.json. |
| F3 P3 non-usage | grep "futures-behavior" over all round outputs; classify each hit | **PASS.** 15 hits, all legitimate: comm_energy SUMS:17 + lane json/md/carried = the disclosed transcription correction; comm_metal md/carried = never-accessed declaration + correction context; fx_eb:14 = "was NEVER accessed"; handoff_FXJA ×2 = "was NEVER accessed"; handoffs COMM-EN/COMM-ME = never-accessed declarations; DISPATCH_MANIFEST:46 = the prohibition statement itself; es_nq json = "honored, zero reads"; synth/SOURCE_INVENTORY §3 = boundary statement. CROSS files: zero hits — its NQ-addendum path correction names FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 (a different dir that does not contain the string), disclosed in handoff_CROSS.json. No hit indicates P3 access. |
| F4 wave-1..wave-2 content diff | `git diff --stat b7f274a4 55408ceb` (permitted read-only git; recorded) | **PASS.** Exactly: comm_energy/SHA256SUMS_lane.txt (23 lines), comm_metal/SHA256SUMS_lane.txt (28 lines) modified + 4 new synth files + new REPORT_VI.md (56 lines). No other round file touched after wave-1. |

## Findings register

Severity counts: **0 CRITICAL / 0 MAJOR / 6 MINOR / 6 NOTE.**

| ID | Sev | Location | Finding |
|---|---|---|---|
| M1a | MINOR | dispatch/handoff_COMM-EN.json | Canonical `outputs` key missing; field present under non-canonical name `deliverables`. Content equivalent; schema deviation. |
| M1b | MINOR | dispatch/handoff_COMM-EN.json (dispatch_sha) | Prose appended in sha field: `"a4a88265… (dispatch base_sha; == measured HEAD)"` — round-2 M1 lesson pattern; bare sha itself correct. |
| M2 | MINOR | es_nq/fetch_log.jsonl:1-3 + synth/SOURCE_INVENTORY.md §4 | 3 attempts on one (url,method) pair (cboe SPX page GET: 2× webReader, then 1× WebFetch) vs the ≤2-per-(url,method) rule; lane note says "different tool/method" but method is identical (GET). Transparently logged, 0 bytes, cap honored after. SOURCE_INVENTORY's aggregate "≤ 2 per (url,method)" claim is inaccurate for this lane. |
| M3 | MINOR | comm_metal/fetch_log.jsonl (all 28 rows) | Timestamp field named `ts_utc` (date-only "2026-10-04") + `seq`, instead of the ISO `ts` used by the other 4 lanes — cross-lane log-schema inconsistency; time-of-day not recorded. |
| M4 | MINOR | comm_metal/fetch_log.jsonl:28 vs comm_metal/captures/ | save_path says `captures/nt_gold_specs_archive_429.html`; on-disk file is `nt_gold_specs_archive.html` (same 620-byte Wayback 429 block page — byte count matches, disk name is what SUMS pins). Filename suggests archived spec content; it is a rate-limit error page. Lane rests no fact on it (fineness NOT_IN_ANY_CAPTURED_SPEC). |
| M5 | MINOR | synth/OUTCOME_BLIND_RANKING_R3.md §1 | Combined-view completeness gap: JF1 6J (11) and FX-F4 6E (11) missing from the "≥11" table; ES-F3 (10) and AF1 (10) missing from the "full carried tail (10 and below)" parenthetical. No value corruption — every row that appears matches RANKING_AGGREGATION.md exactly, which remains complete. |
| N1 | NOTE | cross/CENSUS_DELTA.md:15 | "…with its own PnL path" — definitional restatement of the census-unit convention (citing CENSUS_FINAL), not a PnL claim. |
| N2 | NOTE | cross/ANCESTRY_COURT_INFRA.md:133; cross/hypotheses_cross.json:1146 | "declared band ≥ measured cost" — dead-row rejection-mode class name (DECLARED_BAND_BELOW_MEASURED_COST) and its binding criterion; not a measured-cost claim. Only A2 residuals outside explicit prohibition statements. |
| N3 | NOTE | comm_energy/CARRIED_STATUS.md:131 | Only "sharpe" regex hit = the word "sharpened". No Sharpe metric anywhere in the round. |
| N4 | NOTE | synth/OWNER_DECISION_PACKET.md §1 | Hash-row shorthand "33+24+14+4+2" ambiguous (comm_energy's 33 already contains its 24 baseline rows; the second 24 is comm_metal's separate register). Ambiguous writing, not an arithmetic error. |
| N5 | NOTE | comm_energy/HYPOTHESES_COMM_EN_R3.md:393 vs cross/hypotheses_cross.json | Row-numbering conventions differ (COMM-EN cites ledger rows 0-indexed 106/107/108; cross uses 1-indexed ids == file lines 107/108/109 for the same rows). Family ids cited alongside; unambiguous. |
| N6 | NOTE | comm_energy/SHA256SUMS_lane.txt row 20 | Home path style `~/my-quantitative-data/...` (no leading dot) vs `~/.my-quantitative-data/...` on the other 14 home rows. Both resolve; hash verified; style inconsistency inherited from the register. |

## Disclosures

- Commands run: `git rev-parse HEAD`, `git status --porcelain` (start + end), `git log --oneline -5`, `git rev-parse b7f274a4`, `git diff --stat b7f274a4 55408ceb` (explicitly permitted by the dispatch), `git cat-file blob a4a88265:<9 paths>` (read-only blob hash of committed copies, needed to verify the C2 correction claim against the verified base), plus read-only find/grep/python hashing over the worktree, the round dir, and `~/.my-quantitative-data` owner data rows named in the SUMS (read-only verify).
- Network: zero. No fetches, no S1, no purchases, no credentials.
- P3 quarantine: never touched. Non-usage verified by output scan only (F3).
- Nothing repaired, nothing ruled, nothing ratified. Lane JSONs were treated as claims; every verdict above was recomputed from bytes.
- Files written: this report, verify/verify_findings_r3.json, dispatch/handoff_VERIFY.json. Nothing else.
