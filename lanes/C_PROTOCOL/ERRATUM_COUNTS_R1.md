# ERRATUM R1 — Stale All-Star / neutral-site counts in the protocol draft (Lane C, WNBA-WINPROB-PREP-V1)

- task `wbap-c-proto-r1` · cycle `WNBA-WINPROB-PREP-V1` · role quant-implementer · 2026-10-05
- Scope: EXTEND-ONLY remediation of the lane-C stale prior-memo counts recorded as former
  verifier finding D-5 (`lanes/D_VERIFY/VERIFICATION_REPORT.md`) and deliberately left open by
  `lanes/A_DATA/ERRATUM_TEAM_KEY_R1.md` §5. No commits (controller lands). Write scope honored:
  `lanes/C_PROTOCOL/**` only — this file plus surgical edits to
  `lanes/C_PROTOCOL/PROTOCOL_DRAFT_WNBA.md` and the new `handoff_C_r1.json`.
- Base: branch `orca/wnba-winprob-prep-v1-integration`, HEAD measured
  `6681486d356d04690873f25badf05500ed22f430` (= dispatch_sha = actual_start_sha; tree clean at
  start). Lane C is NOT re-measuring the corpus: the numbers below are the data-verified,
  delta-re-verified values from lane A's erratum r1 + lane D's independent delta pass
  (authorities listed in §2). No outcome computed; schema/coverage counting only.

---

## 1. What was wrong

The protocol draft (`PROTOCOL_DRAFT_WNBA.md`, task `wbap-c-proto`) inherited prior-memo counts
written before lane A's byte audit landed. Stale values:

1. **Alias token list incomplete** — the draft's two token enumerations (§2.1 filter law and
   §8 test 6) carried only 8 tokens: `EAST/WEST/ALL/DEL/PAR/CLA/COOP/WNBASTARS`, missing
   `USA`, `WIL`, `STE`, `COL`, `SPO`. Under that list **11 of the real alias rows would leak**
   past the filter and the alias-contamination assertion: USA×4, WIL×3, STE×2, COL×1, SPO×1
   (erratum r1 §5 of lane A).
2. **Alias row count stale** — §8 test 6 said "the 14 All-Star rows are counted and excluded";
   the measured count is **21**.
3. **Neutral-site row count stale** — §2.3 and §8 test 4 said "15 rows"; the measured count
   is **16**.
4. **Cup finals**: checked — the draft carries **no** Cup-finals count anywhere (no "7" to
   correct; Cup rows are handled by flag per lane A, §2.3/§8 test 7). Nothing to change.

## 2. Authoritative measured numbers (adjudicated; sources)

- `lanes/A_DATA/ERRATUM_TEAM_KEY_R1.md` (task `wbap-a-data-r1`) — §4b/§4c/§5.
- `lanes/D_VERIFY/DELTA_REVERIFY_R1.md` (task `wbap-d-verify-r1`, verdict VERIFICATION_PASS) —
  Check 2 (D-3 alias) and Check 3 (no-regression filter law), independent implementation.

| quantity | stale value in lane C | corrected measured value |
|---|---|---|
| All-Star/exhibition alias rows (ESPN) | 14 | **21** (2002–2026; one per ASG season, none in Olympic years; stats side **0**) |
| Alias token set | 8 tokens | **13 tokens**: EAST, WEST, ALL, USA, DEL, PAR, WIL, STE, CLA, COL, SPO, COOP, WNBASTARS |
| Per-token slots (home+away sides of the 21 rows) | not stated | EAST 11, WEST 11 (2002–2017 classic format), USA 4 (2004/2010/2021/2024), WIL 3 (2019/2022/2023 Team Wilson), ALL 3 (2004/2010/2021; 2024 uses `WNBASTARS`), STE 2 (2022/2023 Team Stewart), DEL 2 (2018/2019 Team Delle Donne), PAR 1 (2018 Team Parker), COL 1 + CLA 1 (2025 Team Collier/Clark), SPO 1 + COOP 1 (2026 Team Spoon/Coop) |
| Neutral-site rows | 15 | **16** (2013–2026 = 10 All-Star + 6 real games incl. Cup finals; only 2021/2025/2026 finals are neutral) |
| Commissioner's Cup finals | not stated in lane C | **6** (one per Cup season 2021–2026; 301 Cup rows) — no lane-C text carried the stale 7 |
| Filter-law anchors (unchanged, re-checked) | — | 17 pre-rows / 1 forfeit / 2 postponed / **21 alias** / 7 TBD; ESPN real 5,988 = 5,230 RS-excl-Cup + 301 Cup + 457 PO; stats real 7,008 = 6,493 + 515; union 7,017 |

## 3. What changed (line-level)

All edits to `PROTOCOL_DRAFT_WNBA.md` are surgical, each with an `[ERRATUM_COUNTS_R1: …]`
pointer note at the changed site; no section was rewritten.

1. §2.1 filter law (was line 113): alias list `EAST/WEST/ALL/DEL/PAR/CLA/COOP/WNBASTARS` →
   the 13-token set with the measured 21-row count and stats-side 0.
2. §2.3 segmentation law (was line 168): "Neutral-site rows (15 rows, 2013–2026, …)" →
   "(16 rows, 2013–2026, …)".
3. §8 test 4 (was line 368): "(15 rows, flagged in-data)" → "(16 rows, flagged in-data)".
4. §8 test 6 (was lines 374–376): 8-token list → 13-token set; "the 14 All-Star rows are
   counted and excluded everywhere" → "the 21 All-Star/exhibition alias rows are counted and
   excluded everywhere" with the measured per-token slot breakdown incl. WIL×3 / STE×2.
5. §12 item 4 (was lines 465–467): the successor re-verify law is KEPT unchanged (it stays
   true); corrected reference values (21 alias rows / 13 tokens; 16 neutral) are now cited
   inline so the clause no longer points at stale implicit anchors.

Unchanged on purpose: the draft header's dispatch/start sha (`673b4f27…`) is the historical
record of the original lane-C run (task `wbap-c-proto`); this remediation's own shas live in
`handoff_C_r1.json`. Sections 0–1, 2.2, 3–11 (except the three count sites above), 9, 12 items
1–3/5 are byte-untouched. Census planning sketches (~230 RS games/season, ~440/block) were
never measurements and stay as marked (§3.2, §12 item 3).

## 4. Impact statement

These counts are **assertion / audit parameters** in the protocol's verification battery:
the §2.1 filter exclusion, the §8 test 4 HCA=0 handling, the §8 test 6 alias-contamination
assertion, and the §12 item 4 re-verify targets. There is **no split, arm, fold, gate,
window, or metric-semantics change**: Sections 3–7 and 10–11 (split design, arm budget,
metrics, gates, negative controls, stop rules, freeze/GO law) are byte-untouched. What the
fix removes is a concrete leakage hazard — under the stale 8-token list, 11 real exhibition
rows (USA×4, WIL×3, STE×2, COL×1, SPO×1) could have entered scored/training sets and tripped
the §8 test 6 assertion at successor runtime; the filter now enumerates exactly the measured
21-row / 13-token set. The neutral count moves 15 → 16 inside an already-flagged, HCA=0
reporting rule; no exclusion set changes (neutral-site rows are flagged, never dropped).

## 5. Reproduction

```
git -C /Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration rev-parse HEAD
        # 6681486d356d04690873f25badf05500ed22f430 (start; no commits made by this lane)
grep -n "ERRATUM_COUNTS_R1" lanes/C_PROTOCOL/PROTOCOL_DRAFT_WNBA.md   # 5 pointer sites
grep -n "14 All-Star\|15 rows" lanes/C_PROTOCOL/PROTOCOL_DRAFT_WNBA.md  # 0 hits after fix
```

No corpus re-count was needed (schema/coverage counting only; the adjudicated numbers are
reproducible per the two authority files' own reproduction sections).
