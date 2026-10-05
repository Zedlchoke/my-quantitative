# PREP_SUMMARY — WNBA-WINPROB-PREP-V1 (controller synthesis, 2026-10-05)

- Cycle: WNBA-WINPROB-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · no GO phrase (never
  registered, never consumed). Verdict: **PREP_COMPLETE_PENDING_OWNER_DECISIONS** (after a
  verification FAIL → remediation → delta PASS arc, fully disclosed below).
- Chain: plan commit 5276a7b8 (root main) → registry register fefc18cd → G0 673b4f27
  (dispatch packets + state) → lanes A/B/C landed 18fa135b → D verification FAIL landed
  448710a6 → remediation r1 landed f3098d95 → delta re-verify PASS landed d99fb517.
- Independence law held: verifier confirmed no NBA data/parameter/verdict was imported as
  WNBA evidence anywhere in the lanes.

## Verification arc (transparency)

- Lane D round 0: VERIFICATION_FAIL — D-1 MAJOR (team-key lineage resolved on the wrong
  branch: encoded a UTA→SAN→DAL "merger"; data refutes it) + 4 MINOR.
- Remediation wbap-a-data-r1 (lane A owner fixed from data, verifier never repairs):
  lineage rebranched to LVA := UTA(1997–2002)→SAN(2003–2017)→LVA(2018–) and
  DAL := DET(1998–2009)→TUL(2010–2015)→DAL(2016–), LAS continuous; 21→20 franchise keys;
  3 MINOR fixes (DET/TUL ESPN mislabel spans all 2002–2009; WIL×3/STE×2 alias breakdown;
  Cup finals 7→6). ERRATUM_TEAM_KEY_R1.
- Lane D delta r1: VERIFICATION_PASS — lineage re-measured from stats schedule bytes
  (UTA 193 rows / SAN 536 / LVA 384 / DET 445 / TUL 206 / DAL 408 / LAS 1,111 rows
  continuous; SAN+DAL coexist 2016 AND 2017); no regression in census/filter/join/
  timestamp laws; lanes B/C byte-unchanged.
- Open-by-design (for the successor B1 freeze, per lane C §12.4): lane C's verbatim-inherit
  sections carry stale 14-ASG/15-neutral counts (correct: 21 alias rows incl. WIL/STE;
  16 neutral rows) — reconciled at successor registration, not silently here.

## Data layer (lane A + r1, measured)

- Corpus: wehoop/sportsdataverse (rights CC BY 4.0 badge + MIT store, internal research +
  attribution; NO direct scraping of wnba.com/stats.wnba.com/ESPN/SR; balldontlie
  excluded) at ~/.my-quantitative-data/wnba-v1/ + new artifacts (5 downloads 1.24 MB,
  sha256'd; team_key_table 20 keys; release depth census) at ~/.my-quantitative-data/
  wnba-prep-v1/.
- Game universe (union 7,017): ESPN real 5,988 = 5,230 RS-excl-Cup + 301 Cup + 457 PO
  (25 seasons 2002–2026); stats real 7,008 = 6,493 RS + 515 PO (30 seasons 1997–2026);
  reconciliation exact: 9 ESPN-only (3 regular + 6 Cup finals stats lacks) + 1,029
  stats-only (1,022 pre-2002 era + 7 genuine 2002–2004 extras, listed games match).
  Season shape: 1997=115; ~220–260/yr mid-era; 2020 Wubble 147/147 REAL; 2025=311;
  2026 snapshot 341 played + 17 future 0–0 pre rows (7 TBD) + 2 postponed.
- Filter law (measured): 17 non-post prefill rows; exactly 1 forfeit (2018-08-03
  WAS–LVA 0–0); 2 postponed; 21 All-Star alias rows (13 tokens incl. WIL/STE); 7 TBD
  placeholders; 16 neutral-site rows; 301 Cup rows embedded in RS (6 finals, one/season).
  NEVER filter on score presence (unplayed rows are pre-filled 0–0).
- Clock law: tip_utc := parse(ESPN schedule date, UTC) — all three ESPN schedule columns
  are ONE instant (6,029/6,029); box game_date_time = same instant + cosmetic fixed
  −0400 (NOT venue-local — corrects the prior memo); pbp wallclock 100% UTC; stats
  game_date == ET date 5,954/5,954.
- Franchise lineage (NORMATIVE, from data): LVA := UTA→SAN→LVA (see arc above);
  DAL := DET→TUL→DAL; LAS continuous; 6 defunct (CHA/CLE/HOU/SAC/MIA/POR-fire);
  expansion ATL 2008 / CHI 2006 / GSV 2025 / TOR+PDX 2026; ESPN DET rows mislabeled
  TUL across ALL ESPN seasons 2002–2009 → join on display_name/crosswalk only.
- PIT: 12 feature classes adjudicated — rolling-window results features PIT_SAFE-by-
  construction (strictly-prior-game inputs); player_box active/DNP/starter/ejected are
  POST-GAME FACTS (never pre-game features); injury/lineup NOT_RUN_PIT (no $0 source
  with rights + real publish timestamps; 5 leakage hazards measured and warded).

## Mechanisms (lane B): 3 advanced, frozen falsifiers

- W-H1 fresh WNBA Elo baseline — own train-only K/HCA/γ selection (grid pre-registered:
  K∈{8,16,32}×HCA∈{0,50,100}×γ∈{0.65,0.75,0.85}); NBA constants citable context only.
- W-H2 continuity-modulated carryover (H-C5) — HARD-GATED on roster census + PIT verdict
  (lane A released the gate inputs; slot released, never reallocated, if it fails).
- W-H3 SOS decomposition under a short season — early-season-concentrated claim.
- Each: REJECT iff pooled 95% paired date-cluster-bootstrap CI of ΔLL vs parent includes
  0 or ≥ half folds non-negative; time-shuffled twins; designed-null parents; honest
  capacity (~5.1–6.0k RS games; min fold 2020 ≈140 games; resolvable floor ~0.003–0.004).
- Rejected (9): additive logistic-over-Elo; MOV-Elo; 538/odds/current-box; NBA params as
  WNBA evidence; b2b/travel fatigue arms (WNBA travel-regime change mis-specifies pooled
  coefficient; prospective re-proposal allowed later); expansion-init prior (starvation);
  overseas availability (NOT_RUN_PIT, absorbed by W-H2); matchup familiarity; dead mains.

## Protocol draft (lane C) for successor WNBA-WINPROB-SCORED-V1

- Era law FROZEN: 1997–2001 stats-side schedules = rating-stream WARM-UP ONLY (never
  train/score/feature rows); TRAIN 2002→(first OOS season −1) with 4 expanding-origin
  2-season validation blocks inside; OOS = final 7 complete seasons at freeze (placeholder
  2019–2025); future seasons PROSPECTIVE ONLY (append-only ledger, rows timestamped
  strictly pre-tip; ≥2 accrued seasons before any report).
- Arms: ceiling 9, allocated 5 (B0; B1 fresh WNBA Elo; W-H2 continuity; conditional
  lane-B mechanism slot; reserve), 4 released. Twins = DIAGNOSTIC outside budget.

## Successor registration conditions (exact)

1. This cycle's PREP_COMPLETE verdict (this document) + owner instruction naming the
   successor (proposed id WNBA-WINPROB-SCORED-V1).
2. Fresh registry registration (budget scored, GO phrase registered-not-consumed).
3. Data freeze (corpus + team_key_table 20-key lineage + manifests sha256) + code
   freeze + protocol constants digest, frozen BEFORE any test-window look; the lane C
   stale-count reconciliation (§Open-by-design) lands in the same freeze.
4. Independent A7 prelaunch AUTHORIZED with 0 unresolved HIGH/CRITICAL.
5. Owner typed GO, fresh, verbatim, at the successor cycle's own gate (two-key law).
6. Prohibited regardless: any scored/S1/paper/live/push/merge/purchase before all five;
   no GO survives from this or any earlier cycle (P-8).
