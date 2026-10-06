# VERIFY_REPORT_R2 — FUTURES-SIX-ADOPT-PREP-20261004

- **Verifier**: VERIFY-R2, fresh-context independent verifier (lane 8 of 9; audits only, repairs nothing)
- **Round**: FUTURES-SIX-ADOPT-PREP-20261004 (round 2, PREP + cycle preparation)
- **Worktree**: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-adopt/prep`, branch `codex/futures-six-adopt-prep-20261004`
- **Measured HEAD at verify start**: `f5d2e7a2be1a136d2054b83994f5787a95456d76` (wave-1 checkpoint; matches dispatch packet; one permitted rev-parse)
- **Worktree state at verify end**: `git status --porcelain` EMPTY (the single permitted use) — controller had committed all wave-1 lane outputs; zero stray uncommitted files.
- **Method**: every load-bearing number below was re-measured by THIS lane from committed bytes — hashes recomputed, parquets re-counted, XLS/JSON captures re-parsed, greps re-run. Lane JSONs were treated as claims to diff, never as evidence.

---

## 1. Verdict per lane

| Lane | Verdict | Recomputation performed | Result |
|---|---|---|---|
| ADOPT | **VERIFIED** | 3/3 cache_v3 re-hashes; panel re-count; alias re-count; 66 rolls re-counted two independent ways; V2 non-modification (byte-diff vs sibling worktree); D8/D9 NOT-ratified line verbatim | all claims reproduce exactly |
| CAL-EB | **VERIFIED** | fetch_log re-count; 14/14 SHA256SUMS_lane re-verify; both 6B XLS vintages re-parsed; OBTAINED-cell scan | 10 records; 21/21 shared rows exact; BPU24/BPV24 drop + 3 new rows reproduced; 0 OBTAINED cells |
| CAL-JANQ | **VERIFIED** | fetch_log re-count + digest; retry-cap audit; both 6J XLS vintages re-parsed; pcal_37 Sep-2023 re-parsed; corrections + BLOCKED_TRANSPORT read from delta | 28 records; 4/4 2026 quarters identical across vintages; 4 AD 2026 rows present; max 2 attempts/(url,method) |
| FEE-ES | **VERIFIED** | 3/3 A7 input re-hashes; D3 percentages recomputed; bounded authorization grep re-run; NOT_RUN wording check | all match; no authorization artifact exists anywhere |
| PUB-RIGHTS | **VERIFIED** | manifest sums recomputed; 5/5 manifest spot-hashes vs disk; pub worktree HEAD/file-count/size/blob checks; 3/3 pub-file hashes vs manifest | 123/125/2,922,690 exact; HEAD `fd27dd82e79cb29ca4c627ad60011a683fb4aa70`; 124 files; 0 >100MB; 0 .dbn |
| HYPO | **VERIFIED** | positive-claim pattern scan; ancestry-table citation check; family count; trial-ID language scan; FAMILY_FAILURES.jsonl row count | 0 positive return/PnL claims; 173 rows confirmed; 2 families (<=6); 0 trial IDs |
| PACKET | **VERIFIED** | GO-law section verbatim check; open-decisions count; evidence-pin count + 3/3 sha spot-verify | GO-law present verbatim; 12 decisions D1-D12; 13 pins, 3/3 match disk |

**Round verdict: 7/7 lanes VERIFIED. Findings: 0 CRITICAL / 0 MAJOR / 1 MINOR / 5 NOTE.**
Nothing in this round claims ratification, GO, scoring, or a profitable edge; every quantitative
claim I re-measured reproduced exactly.

---

## 2. Lane-by-lane evidence

### 2.1 ADOPT — VERIFIED

| # | Check | Method | Result |
|---|---|---|---|
| A1 | cache_v3 hashes | `shasum -a 256` on `contract_registry_v3.json`, `held_volume_k5_v3.parquet`, `nq_sessions_v3.parquet` in `FUTURES-SIX-READINESS-20261004/nq/cache_v3/` | 3/3 == `adopt/cache_v3_hashes.json` (`6a629d71…`, `99ff1ca1…`, `30bc1ec3…`) |
| A2 | panel row count | pyarrow metadata + full read of `nq_outright_1m_v3.parquet` | **6,780,608 rows** exact; ts 2010-06-06 22:00Z .. 2026-09-30 23:59Z |
| A3 | alias count | re-count rows with `instrument_id==16908 AND ts<2020-06-01` | **92,075 rows**, volume **24,686,121**, `raw_symbol` unique = `[NQM0]`, window 2018-08-15 14:37Z..2020-05-31 23:59Z; post-cutover id-16908 = **19,406 rows** all NQM0 |
| A4 | 66 rolls | (a) `v3_rolls_spread_stats.parquet` row count; (b) symbol transitions in `held_volume_k5_v3.parquet` (4,219 rows) | (a) 66 rows all NQ->NQ; (b) 67 transitions incl. first = **66 rolls**; crash roll row exact: `NQH0_2020->NQM0_2020 @2020-03-19, dte=1, old 85,489 / new 487,005` |
| A5 | DEPRECATION non-modification | (a) mtime scan of all 242 files under `FUTURES-DEEPRESEARCH-V2-20261003/`; (b) byte-compare (`cmp`) all 242 vs sibling round-1 worktree `futures-six-readiness/prep` | (a) all mtimes in 11:37:23–11:37:30 local band — see NOTE N1; zero files after 11:38. (b) **242/242 byte-identical, 0 differing, 0 missing** — v2 tree untouched |
| A6 | D8/D9 NOT-ratified line | grep `adopt/D8_D9_DECISION_SHEET.md` | line 5 verbatim: `**NOT ratified by owner as of 2026-10-04; this sheet is input to a ruling, not a ruling.**`; all other "ratif" tokens are option descriptions, not claims |

### 2.2 CAL-EB — VERIFIED

| # | Check | Method | Result |
|---|---|---|---|
| B1 | fetch_log count | parse `cal_eb/fetch_log.jsonl` | **10 records**, all `curl(web.archive.org)`; one 404 (matches incident I1: wrong path, corrected next attempt on a different URL); budget 10/35 consistent |
| B2 | capture hashes | `shasum -a 256 -c SHA256SUMS_lane.txt` | **14/14 OK** (9 captures + 5 lane files); far exceeds the >=3 minimum |
| B3 | XLS cross-vintage | re-parse `pcal_42_6b_dl_20241108.xls` (this round) vs `pcal_42_6b_dl_20240903.xls` (sibling round-1) with xlrd | Sep sheet: **BPU24+BPV24 present**; Nov sheet: **both absent**; shared contracts **21, 0 mismatches** on Last Trade (spot: BPF25 2025-01-13, BPH25 2025-03-17, BPH26 2026-03-16, BPH27 2027-03-15, BPH28 2028-03-13 — all EXACT); new in Nov: BPG25/BPJ25/BPU29 — exactly as claimed |
| B4 | 0 OBTAINED cells | deep scan of `calendar_delta.json` for any `OBTAINED` token; status enumeration | `new_grid_cells_obtained: 0`; **0 OBTAINED tokens anywhere**; all 58 open cells carry `NOT_OBTAINED` or `INCONCLUSIVE_AGED_OUT`, each with per-cell absence evidence + capture paths; 3 out-of-grid rows carry sha256 provenance (`b38ef64e…` XLS) |

### 2.3 CAL-JANQ — VERIFIED

| # | Check | Method | Result |
|---|---|---|---|
| C1 | fetch_log count + digest | line count + sha256 | **28 records**; digest == handoff pin `ae88a931…9859af` |
| C2 | retry cap | per-(url,method) attempt histogram | max **2**; 0 pairs >2; zero live cmegroup.com contacts; all routes web.archive.org |
| C3 | dual-vintage 6J 2026 | re-parse BOTH `pcal_69_6j_dl_20240904.xls` (Q5, in futures-behavior/prep P3-QUARANTINE captures) and `pcal_69_6j_dl_20251104.xls` (this round) | 16 shared contracts, 0 mismatches; **2026 quarters identical in both vintages**: J1H26 2026-03-16, J1M26 2026-06-15, J1U26 2026-09-14, J1Z26 2026-12-14 |
| C4 | pcal_37 Sep-2023 | re-parse `pcal_37_6a_20230916051415.json` (Q5 sibling) | **4 AD 2026 rows present with full last-trade dates**: ADH26 16 Mar 2026, ADM26 15 Jun 2026, ADU26 14 Sep 2026, ADZ26 14 Dec 2026 |
| C5 | corrections documented | read `calendar_delta.json.corrections_to_prior_rounds` | **2 corrections**, each with capture + re-parse basis: (1) dispatch "6J 2026 CONFIRMED ABSENT" contradicted (my C3 confirms); (2) "pcal_37 exhausted" incomplete for 2026 (my C4 confirms) |
| C6 | BLOCKED_TRANSPORT | read `absence_and_blocks.trading_hours_holiday_download` + fetch_log | status `BLOCKED_TRANSPORT`, reason cites 403 on both timestamps across id_/standard replay + WebFetch; log shows exactly 4 curl 403s (recs 07/08/13/14) + 1 WebFetch 403 (rec 27); route stopped, no retry-beyond-2 |

### 2.4 FEE-ES — VERIFIED

| # | Check | Method | Result |
|---|---|---|---|
| D1 | A7 input hashes | `shasum -a 256` on 3 of the 21 inputs in this worktree | `source/CME.php.txt` `75a86470…78565`, `source/fees_corrected.json` `7cd65f25…2aca8`, `verify/p0_verdict.json` `f1e5b636…0d347` — **3/3 == packet table** |
| D2 | D3 percentage | `0.02/42.00` recomputed | **0.047619% -> 0.0476%** as printed; also reproduced 0.0299% (0.02/67.00) and 0.0217% (0.02/92.00) and the 41.98/66.98/91.98 offset column |
| D3 | authorization grep | bounded recursive grep over `research/control/FUTURES-*/` for `GO_FOR_A7|authorize the (fee )?A7|D2 (GO|authorized|approved)|approved to run|run the (fee )?A7` | 20 raw hits, 9 files; every hit a negation / status restatement / decision REQUEST (regex text, verify-record contexts, "packet existence is NOT authorization", "do NOT run the A7"); 7 hits inside this round are its OWN parallel-written decision-request text (see NOTE N2). **No authorization artifact exists.** |
| D4 | NOT_RUN wording | grep `A7_EXECUTION_PACKET.md` + `DECISION_PACKET_INDEX.md` | `STATUS: NOT_RUN — no D2 ruling exists.` (L11); `fee A7 = NOT_RUN; D2 OPEN; fees UNDER REVIEW` (L29); index L3: `**NO RULING EXISTS AS OF 2026-10-04. NOTHING IN THIS PACKET IS RATIFIED.**`; packet footer: "Nothing here is ratified; A7 remains NOT_RUN as of 2026-10-04" |

### 2.5 PUB-RIGHTS — VERIFIED

| # | Check | Method | Result |
|---|---|---|---|
| E1 | manifest sums | recompute from `publication_manifest.json` `files[]` | **125 entries**; **123 push_recommended**; push bytes **2,922,690** exact (== `push_set` field); classes AUTHORED_DOC 62 / SCRIPT 34 / SMALL_DERIVED 10 / RAW_CAPTURE 17 / BIG_DERIVED 2 — all as claimed |
| E2 | manifest spot-hash | 5 entries sampled across the push set (indices 0/30/60/90/122), hashed vs disk | **5/5 MATCH** |
| E3 | pub worktree HEAD | read `.git` metadata file of `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-pub/pub` (file reads, not git commands) | HEAD ref `codex/futures-six-readiness-20261004-pub` = **`fd27dd82e79cb29ca4c627ad60011a683fb4aa70`** — matches controller claim |
| E4 | pub tree shape | `find` counts + size filters | **124 files** under `FUTURES-SIX-READINESS-20261004/` (= 123 push set + `PROVENANCE.md` at round-dir root); **0 files >100MB**; **0 `.dbn` files** |
| E5 | push content matches manifest | all 123 push-set paths exist in pub worktree (0 missing); 3 sampled files hashed | **3/3 MATCH** manifest shas |

### 2.6 HYPO — VERIFIED

| # | Check | Method | Result |
|---|---|---|---|
| F1 | 0 positive return/PnL claims | pattern scan (`expectancy [><=]`, `hit rate [><=]`, `% win/return`, `expected return`, `sharpe`, `profit factor`, `CAGR`, `\bPnL\b`) over `HYPOTHESES_R2.md` | no positive-claim hits. Only matches: (a) dead-corpus ancestry citations `−2.353 / PF 0.849 / 11,459 trades` (NEGATIVE numbers of the dead FX V1-A3-P1, cited as veto evidence, not as this round's result); (b) anatomy percentages `28.7→23.7%` (6B London-share drift, "background, never a conditioning variable") and `~49%` (odd-print share in era-2 tick chunks). Both are microstructure anatomy, not performance |
| F2 | ancestry citations | read §6 ancestry table + grep `FAMILY_FAILURES` | §6 states all **173** entries scanned; table cites row-level evidence (e.g. row 4 SELECTION_REJECTION; nearest-dead DT100-71/74 with class-difference rationale); `research/wayfinder/FAMILY_FAILURES.jsonl` re-counted = **173 lines** |
| F3 | families <= 6 | parse `hypotheses_r2.json` | **2 families** (R2-F1 RMM, R2-F2 AF4), both `PROPOSAL`; plus carried-status proposals and 2 diagnostics, 0 IDs each |
| F4 | no trial IDs | language scan | "No cycle registration, no trial creation", "0 identities" throughout; nothing minted |

### 2.7 PACKET — VERIFIED

| # | Check | Method | Result |
|---|---|---|---|
| G1 | GO-law section verbatim | read §7 of `CYCLE_LAUNCH_DRAFT.md` | present verbatim: `**NOTHING in this packet runs until the owner issues a typed GO at this cycle's own gate, AFTER registration.**` incl. NO_GO_REGISTER/SCORE/ORDER, the "cho agent làm đi" limitation, exact GO form `GO <REGISTERED-CYCLE-ID> SCORED EXECUTION`, two-key completion, `BLOCKED_AUTHORITY` consequence |
| G2 | open decisions | parse `open_decisions_dependency.json` | **12 decisions**, IDs D1–D12; D2 flagged hardest in both mirror and draft |
| G3 | evidence pins | count sha256 literals in §9 + spot-verify 3 | **13 pins**; spot-verified `OWNER_DECISIONS.md` `d14e436f…`, `DATA_READINESS_6A.md` `28ea9093…`, `SPEC_PB1_ES.md` `445f7499…` — **3/3 match disk** |

### 2.8 Round hygiene

| # | Check | Method | Result |
|---|---|---|---|
| H1 | language scan | pattern scan over all round-2 `*.md`/`*.json` for positive `scored`/`GO granted`/`edge`/`profitable` claims | residual "scored" hits are all structural/negative (e.g. "3 scored controls", "513 scored trials in ledger", the GO form string, "data-ready ≠ scored-authorized", "any scoring implementation MUST use the explicit cease-guard"); "edge" hits are the forbidden-claims disclaimer itself and the Wayback network edge; zero `profitable`/`GO granted`/`alpha exists` hits. **Negations only.** |
| H2 | write boundary | the single permitted `git -C <wt> status --porcelain` | **EMPTY** — clean tree; nothing uncommitted anywhere; combined with A5 (242/242 V2 byte-identical) and the round-dir inventory, no file outside the round dir + dispatch/ was created or modified by this round |
| H3 | round-dir inventory | walk `FUTURES-SIX-ADOPT-PREP-20261004/` (70 files) vs handoff changed_paths/outputs | all files accounted for by lane declarations; adopted lane dirs: adopt 7, cal_eb 16, cal_janq 25, dispatch 8, fee_es 5, hypo 2, packet 2, pub 5. No unlisted files |
| H4 | relocated handoffs | parse `handoff_CAL-EB.json` / `handoff_CAL-JANQ.json` from round-dir `dispatch/`; check worktree root | both parse, schema `zcode_orch_v3_handoff@1`, all core fields present, `dispatch_sha == actual_start_sha == 9fb66c88…`, `commit_sha: null`; **no worktree-root dispatch strays remain** |
| H5 | handoff schema sweep | all 7 handoffs vs required core fields | 7/7 schema-valid; 7/7 dispatch==start; 7/7 commit null (see MINOR M1 on HYPO field format) |

---

## 3. Findings

### MINOR

- **M1 — HYPO handoff `actual_start_sha` embeds prose.** Value is
  `"9fb66c88… (measured: one permitted git …)"` rather than a bare 40-hex string, so strict
  machine equality `actual_start_sha == dispatch_sha` evaluates false even though the embedded
  sha is correct. Cosmetic schema-hygiene defect only; the sha itself matches the dispatch base.
  (VERIFY-R2's own handoff uses a bare hash.)

### NOTE

- **N1 — The dispatch-prescribed mtime test for ADOPT is superseded by a stronger test.** All 242
  files under `FUTURES-DEEPRESEARCH-V2-20261003/` carry mtimes 2026-10-04 11:37:23–11:37:30 local —
  newer than the prescribed 09:30 cutoff — but this band is the **worktree materialization stamp**:
  every tracked file in every round dir (incl. the untouched round-1 tree) carries the identical
  band, and zero V2 files are newer than 11:38. The decisive check is content-level: **all 242 V2
  files are byte-identical (`cmp`) to the sibling round-1 worktree** at the same base. No V2 file
  was written. Future verify rounds should prescribe the byte-diff, not mtimes, for worktree checkouts.
- **N2 — FEE-ES's "0 hits in FUTURES-SIX-ADOPT-PREP-20261004" is time-indexed, not false.** The
  lane's grep ran before its sibling lanes finished writing. A re-run at verify time finds 7
  additional in-round hits, every one in this round's own parallel-written text: the A7 packet's own
  pattern documentation (2), the D2 sheet title + "Decision requested (owner D2, carried)" (2), the
  FEE-ES handoff's test description (1), and PACKET's dependency mirror + draft D2 row (2). All are
  decision requests / status restatements. No artifact grants authorization. Conclusion unchanged.
- **N3 — CAL-EB handoff declares "11 files + captures/" under `cal_eb/`; disk has 16** (6 declared
  lane files + 9 captures + `fetch_log.jsonl`/`SHA256SUMS_lane.txt` counted in outputs + a small
  `.budget_state.json` not itemized in `outputs[]`). `.budget_state.json` sits inside the declared
  `cal_eb/**` changed-path glob; content is the 10/35 budget state consistent with the log. Cosmetic.
- **N4 — CAL-JANQ handoff `changed_paths` omits its own handoff file.** The file exists at exactly
  the manifest-dispatched path (`dispatch/handoff_CAL-JANQ.json`) and is schema-valid; six other
  lanes list theirs. Self-reference nit only.
- **N5 — Timestamp-precision variance across handoffs** (`run_date`/`generated_utc` sometimes
  date-only "2026-10-04", sometimes full ISO). No field is wrong; uniformity would ease future
  machine audits.

---

## 4. Verifier disclosures

- Exactly one `git rev-parse` (HEAD + branch at start) and one `git status --porcelain` (final
  hygiene check, both explicitly permitted by the dispatch packet). Pub-worktree HEAD verified by
  reading `.git` metadata FILES (not git commands). No other git.
- Zero network. Zero PnL/S1/GO/scoring. No registry/ledger writes.
- Writes confined to `research/control/FUTURES-SIX-ADOPT-PREP-20261004/verify/**` +
  `dispatch/handoff_VERIFY-R2.json`. Everything else read-only (incl. sibling worktrees
  `futures-six-readiness/prep`, `futures-behavior/prep`, `futures-six-pub/pub`, data roots).
- Heavy parquet reads (149MB panel) were single-shot; no lock contention encountered; no foreign
  worker touched.
- This verifier audits only; it repaired nothing, ruled nothing, ratified nothing. D1–D12 remain
  open; NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER remain in force.

— VERIFY-R2, 2026-10-04
