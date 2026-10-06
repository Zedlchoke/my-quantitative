# CLAIM_LINEAGE — dependency graph of every P3-BROWSER-CAL claim/cell

Task FUTURES-P3-QUARANTINE-20261004 · Lane Q1-QUAR-AUDIT · 2026-10-04 UTC.
Method: forward walk from every P3-provided cell (enumerated in
`TRANSPORT_QUARANTINE.md` §3, cells #1–#28) through the repo — targeted reads
of every synth/verify/hypo artifact named by the dispatch, `git log` landing
timestamps per path, and a value-level grep net across the whole round dir and
the repo. No re-fetching; git history is the timestamp authority.

## 0. Timeline (commit timestamps, %cI; UTC in parentheses)

| Commit | Local (+07:00) | UTC | Content |
|---|---|---|---|
| `a8cd06f2` | 2026-10-03T21:47:01 | 2026-10-03T14:47:01Z | FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 (A1-A5, B1-B2, VERIFY) |
| `72c9bc5b` | 2026-10-03T22:54:02 | 2026-10-03T15:54:02Z | Overnight batch-1: P0A, P0B, P2A, P2B, P2C |
| `d7fc6231` | 2026-10-04T05:40:10 | 2026-10-03T22:40:10Z | Overnight batches 2-3: P0-VERIFY, P1 lanes, SYNTH-VERIFY — **SAFE BASELINE** |
| `0225b3c2` | 2026-10-04T06:49:47 | 2026-10-03T23:49:47Z | Overnight batch-4: **P3-BROWSER-CAL — quarantined layer** |

P3's own fetch log shows activity 2026-10-03T23:28:52Z onward — after the safe
baseline commit (22:40:10Z) and before its own commit (23:49:47Z). P3 was the
final lane of the round; every other artifact predates it. The gap between the
safe baseline and the P3 commit is 69m37s.

## 1. P3-containing artifacts (the complete set — nothing else holds P3 data)

| Artifact | Kind | Landed | Evidence |
|---|---|---|---|
| `FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/browser/**` (166 files: captures, tools, coverage json, evidence md, fetch_log) | quarantined evidence | `0225b3c2` | `git show --name-status 0225b3c2`: 167 files, all `A`, 166 under browser/ |
| `FUTURES-OVERNIGHT-PREP-20261003/dispatch/handoff_P3-BROWSER-CAL.json` | quarantined handoff | `0225b3c2` | same commit, the 167th added file |
| Commit message of `0225b3c2` | git evidence | `0225b3c2` | message text carries P3 results + transport disclosure |
| Lead's final chat report of FUTURES-OVERNIGHT-PREP-20261003 | **chat evidence, not a repo file** | ~2026-10-04T00:0xZ (chat) | reported batch-4 results incl. P3 cells as "pending owner ruling" |
| `FUTURES-P3-QUARANTINE-20261004/QUARANTINE_NOTICE.md` + `dispatch/DISPATCH_MANIFEST.json` + this round's outputs | containment artifacts (this round) | untracked, 2026-10-04 | reference P3 by path/class only, per TRANSPORT LAW |

## 2. Forward walk — every candidate consumer, checked

| Consumer (path under `research/control/FUTURES-OVERNIGHT-PREP-20261003/`) | Landed | P3 cells used? | Evidence of independence |
|---|---|---|---|
| `synth/BLOCKER_MATRIX.md` | `d7fc6231` (pre-P3 by 69m37s) | **NO** | ES row says "2026 product Globex times NOT_OBTAINED"; FX rows "2023-2026 NOT_OBTAINED"; GC "2024-2026 NOT_OBTAINED"; SI "2023-2026 NOT_OBTAINED" — i.e. it encodes the pre-P3 state, exactly what quarantine restores |
| `synth/blocker_matrix.json` | `d7fc6231` | **NO** | machine twin of the same cells; `worktree_sha` records its own base `72c9bc5b`; zero P3 values |
| `synth/FINAL_RANKING.md` | `d7fc6231` | **NO** | ranking rubric is package-quality; grep for SNI/browser/P3/ECZ26/GCV26 = 0 hits |
| `synth/CENSUS_FINAL.md` | `d7fc6231` | **NO** | same grep = 0 hits |
| `synth/REPORT_VI.md` | `d7fc6231` | **NO** | same grep = 0 hits (no 'session'/'Dec 2026'/browser/SNI mentions at all) |
| `verify2/findings.json` | `d7fc6231` | **NO** | same grep = 0 hits; findings F-1..F-8 all concern batch 1-3 lanes |
| `hypo/es_nq/**`, `hypo/6e_6b/**`, `hypo/6j_6a/**`, `hypo/comm/**`, `hypo/cross/**` | `d7fc6231` | **NO** | repo-wide needle grep (§3) — the only "08:15" hit is `hypo/6e_6b/fx_hypotheses.json:72` "ECB decision minute 07:15/08:15 CT", an event-window parameter unrelated to P3's Good-Friday close; no calendar cells cite browser/ |
| `dispatch/handoff_P0A/P0B/P2A/P2B/P2C/P0-VERIFY/P1-*/SYNTH-VERIFY.json` | `72c9bc5b` / `d7fc6231` | **NO** | all predate `0225b3c2`; `grep -rl 'P3-BROWSER-CAL'` over the round returns only P3's own dir + its handoff |
| `fees_erratum/**` (P0A/P0B outputs incl. `GATE_REVIEW_NOTE.md`, `FEE_ERRATUM_DRAFT.md`) | `72c9bc5b` | **NO** | their `LIVE_OFFICIAL` token is the A4/fees label (public fee tables), unrelated to P3 calendar cells; landed pre-P3 |
| `cme_cal_gap/equity/**`, `cme_cal_gap/fx_comm/**`, `bls_vintage/**` (P2A/P2B/P2C outputs) | `72c9bc5b` | **NO** | pre-P3 by 53m45s; values come from web.archive.org captures enumerated in their own fetch logs |
| DEEPFOUR round dirs (`FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/**`) | `a8cd06f2` | **NO** | pre-P3 by ~9h; no P3 references (grep §3) |

**Result: ZERO downstream dependents.** No valid artifact before or after P3
cites or depends on any P3 cell. The safe baseline d7fc6231 is clean.

## 3. Value-level leak net (second net over the whole round dir)

Needles = P3-derived distinctive values: contract codes ECZ26/BPZ26/J1Z26/ADZ26
/GCV26/GCX26/GCZ26/SIV26/SIX26/SIZ26 and dated forms ("14 Dec 2026",
"2026-12-14", "28 Oct", "2026-10-28"), session strings ("Sunday 6pm",
"6pm-Friday", "5pm ET", "08:15 CT", "05:00 resume"), "12:45 CT" (Dec-24 2025),
"Sunday 6", plus reference needles "P3-BROWSER-CAL", "0225b3c2", "SNI".
Searched `research/control/FUTURES-OVERNIGHT-PREP-20261003/**` and
`research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/**`, excluding
`cme_cal_gap/browser/` (P3's own dir) — then repo-wide as a third pass.

| Hit (file:line) | Needle | Disposition |
|---|---|---|
| `cme_cal_gap/equity/captures/tradinghours_20260924120320.html:4987` | "Sunday 6" | **No leak.** P2A's own web.archive.org capture (landed `72c9bc5b`, pre-P3): "Sunday 6:00 p.m. - Friday 5:45 p.m. CT … no reporting" — a *reporting-times* spec P2A itself cited as NOT the 2026 product session times (settlement/price-report window, 5:45 p.m., vs P3's 5 p.m. session claim). Independent provenance by timestamp |
| `dispatch/handoff_P3-BROWSER-CAL.json:165-166` | "14 Dec 2026", summary | P3's own handoff — expected holder, quarantined evidence |
| `cme_cal_gap/fx_comm/build_coverage.py:108`, `fxcomm_gapfill_coverage.json:2536,2610,2683,2690,2742,2801,2859,2931`, `captures/holiday_transcription.json:211,235,284,293,309,416,488`, `captures/extracted/2019-christmas-holiday-schedule.xls.txt:20,27,42`, `captures/extracted/2017-4th-of-july-holiday-schedule.xls.txt:25` | "12:45"/"12:15" | **No leak.** All are P2B's 2011-2019 archived holiday XLS transcriptions (landed `72c9bc5b`); P3's 12:45 cell is the 2025-12-24 product close. Different years, different lane, pre-P3 timestamp |
| `hypo/6e_6b/fx_hypotheses.json:72` | "08:15 CT" | **No leak.** ECB decision-minute stratum definition (07:15/08:15 CT), P1-6E6B lane; coincidental value overlap with P3's Good-Friday 08:15 close claim |
| DEEPFOUR `cme_cal/nq_es/fetch_log.jsonl` (WebSearch lines), `events_bbo_coverage/fetch_log.jsonl`, `cme_cal_gap/equity/fetch_log.jsonl` (WebSearch lines) | substring "sni" | **False positives.** The substring occurs inside the word "snippet" in WebSearch outcome prose; no SNI manipulation anywhere in pre-P3 logs (see `PRE_P3_INDEPENDENCE_CHECK.md`) |
| Repo-wide (plans/, CLAUDE.md, research/ minus the two round dirs) | all needles | **0 hits** for contract codes; `0225b3c2` referenced nowhere outside this quarantine round; `d7fc6231` appears only inside P3's own evidence files (P3 recording its dispatch base — expected) |

**Leak-net verdict: NO LEAKS FOUND.** Every hit is either pre-P3 provenance
(proven by landing commit), a false-positive substring, or P3's own quarantined
files.

## 4. Note on one metadata quirk (recorded, immaterial)

`synth/blocker_matrix.json` declares `generated_utc: 2026-10-04T07:30:00Z`,
which postdates its own landing commit `d7fc6231` (22:40:10Z) — the lane
mislabeled local (+07:00) time as UTC (07:30 local = 00:30Z, consistent with a
commit at 05:40 local). Git commit timestamps are used as authority throughout
this audit; the quirk does not affect ordering (all such SYNTH-VERIFY files
landed in the same commit, before P3). Same class of quirk in
`handoff_P3-BROWSER-CAL.json` (`generated_utc 00:10:00Z` vs commit 23:49:47Z).

— End of CLAIM_LINEAGE.md.
