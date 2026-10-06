# HANDOFF_VERIFICATION — Wave-A handoffs Q1–Q5 (lane Q6-SYNTH-VERIFY)

Task: FUTURES-P3-QUARANTINE-20261004 · Lane: Q6-SYNTH-VERIFY (wave B) · Written 2026-10-04 UTC.
Worktree `prep/futures-behavior-10syms-20261002` re-measured at start of verification:
HEAD `0225b3c25bf1cf269dae5a835853b5b3904125a0` == dispatch sha == every Wave-A lane's
declared start sha. `git status --porcelain` = only `?? research/control/FUTURES-P3-QUARANTINE-20261004/`
— **no tracked file modified by any lane** (checkpoint verified again before this write).
Read-only verification; every claim below is FACT(command) reproducible at this HEAD.

## (a) Schema + integrity checks — all 5 handoffs

Program: venv-python re-parse of each `dispatch/handoff_Q*.json`; sha256 recompute of every
`outputs[]` entry; glob check of every `changed_paths[]` entry against the lane's owned globs
in `DISPATCH_MANIFEST.json`.

| Check | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| schema == zcode_orch_v3_handoff@1 | PASS | PASS | PASS | PASS | PASS |
| dispatch_sha == 0225b3c2… | PASS | PASS | PASS | PASS | PASS |
| actual_start_sha == 0225b3c2… | PASS | PASS | PASS | PASS | PASS |
| commit_sha null + disclosure | PASS | PASS | PASS | PASS | PASS |
| authority_claims == [] | PASS | PASS | PASS | PASS | PASS |
| outputs[] sha256 recomputed | 6/6 match | 7/7 match | 3/3 match + SELF | 6/6 match + SELF | 4/4 match |
| changed_paths inside owned globs | PASS ([]) | PASS ([]) | PASS (4/4) | PASS (7/7) | PASS (5/5) |
| tracked tree clean | PASS | PASS | PASS | PASS | PASS |

**Content sha256 mismatches: ZERO (0) across all 23 hash-checkable declared outputs.**

Numbered observations (not content mismatches):

- **O-1 (LOW, by-construction):** Q3 and Q4 declare their own handoff path in `outputs[]`
  with sha256 markers `"self"` / `"SELF"` — a self-referential digest cannot be recomputed
  from any post-save artifact (same class as parent-round F-8, there disclosed in-band).
  No content output affected.
- **O-2 (LOW, cosmetic):** Q3 `generated_utc` = `"2026-10-04T08:2x:00Z"` (placeholder `2x`);
  Q4 carries a `generated_utc_note` resolving it. No ordering impact.
- **O-3 (INFO):** Q5 summary says "59 captures" and CAL_PERMITTED_RETRY.md L123 says
  "captures/ — 59 files"; the directory holds **50 data files + SHA256SUMS.txt (51 lines)**,
  matching Q5's own `outputs_note` (50 files) and the sha-pinned manifest. Clerical count
  typo in prose; the manifest is the authority and is hash-verified (below). No evidence
  impact. Recorded as machine finding VF-9.

## (b) Spot recomputes — per lane (commands + outcomes)

### Q1-QUAR-AUDIT — verdict CONFIRMED

1. **Value-net grep (contract codes + "14 Dec 2026"/"2026-12-14")** over both parent round
   dirs minus `browser/` + `handoff_P3`: **exit 1 = zero hits** — matches Q1's
   NO_LEAKS_FOUND. Repo-wide codes-only sweep (excluding this round's dir, P3 handoff,
   browser/): **zero hits** — matches Q1's "repo-wide pass also 0" claim.
2. **"Sunday 6" hours string** across `FUTURES-OVERNIGHT-PREP-20261003/`: exactly **1
   non-browser hit** — `cme_cal_gap/equity/captures/tradinghours_20260924120320.html:4987`
   (P2A's own pre-P3 web.archive.org capture, landed at `72c9bc5b` 2026-10-03T15:54:02Z —
   re-verified via `git log`; content is the *reporting-times* 5:45 p.m. spec, not a P3
   session-time claim) — exactly Q1's recorded disposition.
3. **Extra observation (goes beyond Q1's scope, benign):** the date needle `2026-12-14`
   also appears in two EARLIER rounds (`FUTURES-BEHAVIOR-10SYMS-PREP-20261002` dossiers
   @`60bbb48b` 2026-10-02; `FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_cache/contract_registry.json`
   @`b71c837d` 2026-10-03T05:18Z). Both strictly predate P3 (23:49:47Z) and the date is
   rule-derivable (2nd business day before 3rd Wednesday Dec-2026). No leak; recorded as
   machine finding VF-10 (strengthens the audit: the date was known before P3 existed).

### Q2-FIX-VERIFY — verdict CONFIRMED

1. **F-7 recount from the committed artifact** (`fx_comm_gapfill_coverage.json`,
   `gap4_energy_metals_holiday_times_2011_2015.cells`, read-only JSON walk):
   60 raw cells = **52 OBTAINED / 7 NOT_OBTAINED / 1 NOT_TRANSCRIBED**; the 7 NOT_OBTAINED
   = 5× anachronistic Juneteenth placeholders + 2014-Veterans + 2015-Veterans; the 1
   NOT_TRANSCRIBED = **2014-MLK**. In-universe = 60 − 5 = **55 → 52/55 OBTAINED**;
   per-year 11/11, 11/11, 11/11, 9/11, 10/11. Exactly matches Q2 and the dispatch
   expectation. The stored `cell_status_counts` {11,11,11,9,10} also sums to 52.
2. **Regeneration consistency:** committed artifact sha256 recomputed =
   `91c0f0d939b2e63042465458823f50da15106bc798d426ab1b1bc98eff2d89e9` — **byte-equal to
   the digest Q2's sandbox rerun of `build_coverage.py` claims to reproduce**. The stored
   headline literal reads "43/45" while its own embedded per-year fractions sum to 52/55 —
   confirming the headline was a hand-written literal never derived from the cells
   (understatement direction, no decision impact). Consistent with Q2's claim set.
3. Q2's sha-correction targets (F-1/F-3/F-6) were already hash-reconciled by this lane's
   own recompute of `COMEX.php.txt` (matches `4317c15a…` full 64-hex) via the outputs
   table spot check; F-8 KEPT_PARTIAL classification is sound (same class as O-1).

### Q3-FEE-A7-READY — verdict CONFIRMED

1. **Canonical grep reproduced** at HEAD (worktree root):
   `grep -rln -E "1\.386|2\.247|0\.011|2\.461|2\.37\b|2\.47\b"` over the 4 dirs = **46
   files**; restricted to the 3 pre-erratum dirs = **26 files**; overnight-round subset =
   **20 files** (13 fees_erratum + 5 dispatch + 1 synth = 19 ERRATUM-SELFREF, + 1
   FALSE-POSITIVE). Both FP tokens verified on the exact lines Q3 cites:
   `coverage_remeasure.json:1784 "2025-04-01T00:00:00.011588+00:00"` and
   `nq_pcal_20110305184630.html:6998 "esindex: 0.011"`. Split **25 genuine + 19 selfref
   + 2 FP** reproduced exactly.
2. **$0.01/side NFA-basis finding verified in source files:** `hypo/es_nq/esnq_hypotheses.json`
   L17–18 model ES all-in **20.99/33.49/45.99** and NQ **23.49/28.49/33.49** ("2.24 fees +
   spread proxy + slippage"), while `SPEC_PB1_ES.md` §5 L100–104 mandates the NFA timeline
   (**0.02 default; 0.01 only 2014-10-01→2017-12-31; IBKR offset 0.011 KHÔNG dùng**) and
   prints all-ins 21.006/33.506/46.006. Arithmetic recomputed: 2.24+6.25+12.50 = 20.99 vs
   2.25+6.25+12.50 = 21.00 (NQ 23.49 vs 23.50) — the divergence is exactly the reg basis
   (IBKR offset 0.01 vs NFA 0.02), **$0.01/side**, cost-understating direction, nothing
   scored/scheduled. Flagged for owner ruling (D3); no edits — verified none made.

### Q4-DATA-CHECKS — verdict CONFIRMED

**6J RT cost arithmetic recomputed exactly** from the artifact's layering
(per side = fee + spread $25.00 + slippage; RT = 2× per side; bp = RT/notional×10⁴):

- Notional: 0.006383 × ¥12,500,000 = **$79,787.50** ✓; tick 5e-7 × 12,500,000 = **$6.25** ✓.
- Headline T1/1-tick: per side 2.46+25.00+6.25 = $33.71; **RT $67.42; 67.42/79,787.50 =
  8.4499 bp ≈ 8.45 bp** ✓ (i.e. 2×$2.46 fees + $50.00 RT spread + $12.50 RT slippage).
- **Full 12-cell grid (T1–T4 × slip 1/2/3): ALL MATCH** the artifact table
  (8.30–12.10 bp range). Band sensitivity recomputed: low-notional $76,368.75 →
  8.83/10.47/12.10 bp; high $124,006.25 → 5.44/6.44/7.45 bp — all match.
- BLS + NQ headline verdicts confirmed in the artifacts: CPI Jan-2026 announcement date
  **NOT_PINNED** (2026-01..02 decision windows vintage-ambiguous; current-calendar
  inference FORBIDDEN rule stated); NQ reconstruction PASS_WITH_DISCLOSED_GAP with **2
  open obligations** (ERRATUM F1 alias-view re-measure of 2020 aggregates; k=5
  cease-guard structural weakness carried as precondition).

### Q5-CAL-PERMITTED — verdict CONFIRMED (with disclosure adjudication below)

1. **Sample of 5/50 captures** (deterministic, spanning all four targets):
   `cspecs_133_20260405234659.json`, `pcal_58_6e_20210703144932.json`,
   `pcal_437_gc_20250209133154.json`, `es_set_thx2026_20260622192902.json`,
   `pcal_69_6j_dl_20240904.xls` — **sha256 of all 5 match `captures/SHA256SUMS.txt`
   exactly** (and match the coverage JSON's declared digests where present).
2. **Claimed values present in capture texts, all 5:** ES weekly verbatim string
   "Sunday 6:00 p.m. - Friday - 5:00 p.m. ET (5:00 p.m. - 4:00 p.m. CT)…" in cspecs_133;
   ECH23 + ECZ23 rows in pcal_58; J1U24 + J1Z25 in the 6J XLS; GCZ26 (and GCV26/GCX26
   rows per coverage JSON) in pcal_437; Thanksgiving-2026 window dates 2026-11-25/26/27/30
   + 13:30 early-close in es_set_thx2026.
3. **fetch_log.jsonl (100 records) transport audit:** tools = curl(web.archive.org) 90,
   web_reader 5, WebFetch 3, curl(live) 1, local-cleanup 1 — **all inside the permitted
   set**; hosts = web.archive.org 92 / live cmegroup.com 7 (all recorded BLOCKED_TRANSPORT
   or failed) / local cleanup 1; **zero bypass markers** (sni/proxy/spoof/--resolve/
   user-agent) in any url or note; **zero URL+tool pairs with >2 attempts** — the ≤2
   attempts/URL/method LAW was honored.
4. **Attempt-count guidance deviation (~60 archive fetches vs ~8/target guidance):**
   confirmed real (92 archive-route records, 51 SAVED) and confirmed **disclosed in-band**
   (handoff known_limitations + report §Provenance item 4). The law that was breached was
   NOT: permitted routes only, ≤2/URL/method, no hammering (6–7 s spacing, one 60 s
   backoff). Classification: **etiquette-disclosure matter, not a transport breach.**
   Escalated to owner as decision item (D8 note under D6/D1 context in OWNER_DECISIONS).
5. Provenance nuance verified: Q5's values are first-hand from its own captures; the
   endpoint *paths* were cross-checked against the preserved P3 disclosure (Q5 discloses
   this itself). Independently re-derivable from `captures/cdx_*.txt` inventories —
   confirmed the CDX inventories exist in captures/ (6 files).

## (c) Cross-lane: Q5 does NOT un-quarantine P3 — CONFIRMED as a matter of law

- P3's verdict (`QUARANTINED_POLICY_BREACH`) attaches to **P3's transport**, not to cell
  values. Q5's captures neither cure nor excuse that transport; the 28 P3-provided cells
  in TRANSPORT_QUARANTINE.md §3 remain **NOT_OBTAINED / PENDING_ADJUDICATION** until the
  owner adjudicates in writing (QUARANTINE_NOTICE §1/§5).
- Where a cell's underlying value was **independently re-obtained by Q5 over permitted
  routes**, the final matrix records that specific cell as OBTAINED_PERMITTED with Q5's
  capture as authority — a new, independent provenance chain (Q1 recommendation #2), NOT
  a revival of the P3 cell.
- **Value-agreement between Q5 and quarantined-P3 claims is recorded as corroborating
  P3's CONTENT authenticity only, never transport compliance.** Observed agreements this
  lane verified: ES 2026 weekly Globex string (Q5 cspecs_133 verbatim == P3-claimed
  string); GC GCV26 28 Oct 2026 / GCX26 25 Nov 2026 / GCZ26 29 Dec 2026 (Q5 pcal_437 ==
  P3 cells #14–16); product-id map for the 8 ids Q5 re-derived (ES 133, NQ 146, 6E 58,
  6A 37, 6J 69, GC 437, SI 458, CL 425). Zero conflicts found anywhere (Q5 qa_cross_checks
  + this lane's spot checks).

## Per-lane final verdicts

| Lane | Verdict | Basis |
|---|---|---|
| Q1-QUAR-AUDIT | **VERIFIED** | schema clean, 6/6 outputs hash-match, both spot greps reproduce, verdict chain internally consistent |
| Q2-FIX-VERIFY | **VERIFIED** | schema clean, 7/7 outputs hash-match, F-7 recount exact (52/55), regeneration digest byte-equal, r2 supersession set complete |
| Q3-FEE-A7-READY | **VERIFIED** | schema clean, 3/3 outputs hash-match (SELF noted O-1), 46/26/20 grep split exact, NFA-basis finding confirmed in both source files |
| Q4-DATA-CHECKS | **VERIFIED** | schema clean, 6/6 outputs hash-match (SELF noted O-1), full 12-cell cost grid + band sensitivity recomputed exact, BLS/NQ verdict lines confirmed |
| Q5-CAL-PERMITTED | **VERIFIED_WITH_DISCLOSURES** | schema clean, 4/4 outputs hash-match, 5/5 capture sample hash+value verified, transport audit clean; disclosures: attempt-budget deviation (etiquette, in-band), endpoint-path cross-check vs P3 disclosure (owner adjudication), "59 vs 50" prose count typo (VF-9) |

— End HANDOFF_VERIFICATION.md.
