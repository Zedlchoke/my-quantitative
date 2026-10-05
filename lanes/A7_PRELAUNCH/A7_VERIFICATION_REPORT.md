# A7 VERIFICATION REPORT — NBA-PLAYERFEAT-SCORED-V1 · Lane A7_NEGVERIFY

- Verifier: A7-role fresh-context, NEGATIVE-selection verification · 2026-10-05
- Target: T_SELECT negative verdict (all three PF arms NOT_ADMITTED; no φ frozen; slot release)
- Method: recompute from raw bytes with A7-OWN code (loader, Elo replay, LL, IRLS slope,
  clustered bootstrap, synthetic streams — none of it imports the T_SELECT lane). No repairs,
  no edits to T_SELECT files, no OOS access, no scored computation beyond ledger-contained
  train-internal numbers (folds 2018–2021; warm-up 2016–2017 stream-only). Interpreter:
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`. No git commands.
- Own-code artifacts (this lane): `verify/a7_recompute.py` + `a7_recompute_results.json`,
  `verify/a7_cap_probes.py` + `a7_cap_probe_results.json`, `verify/a7_ledger_check.py`
  + `a7_ledger_check_results.json`.

## Task 1 — B1* replay (OWN code) → MATCH

Own loader (schedule files 2016–2021 only; 2022–2026 paths never referenced), own date-grain
same-day-exclusion replay (K=32, HCA=100, γ=0.75, μ=1500), own fold-row assembly.

| quantity | lane claim | A7 own recompute | abs err |
|---|---|---|---|
| pooled fold LL (n=4599) | 0.6383266072624096 | 0.6383266072624096 | 0.0 |
| calibration slope | 0.780102170044627 | 0.780102170044627 | 0.0 |

Corpus counts reproduced exactly: loaded 7616 · played 7572 · postponed 44 · stream updates
7556 · season reversions 180 · play-in played 7 (never scored) · exhibitions 9 in window
(7 in fold seasons) · fold rows {2018:1230, 2019:1230, 2020:1059, 2021:1080} = 4599 · playoff
rows 332 · neutral_site=true fold rows 9. B0 constants per fold and pooled LL 0.684339489926359
(abs err 0.0) and B1-HCA0 pooled LL 0.6428161170449253 (abs err 0.0) also reproduced.
Requirement "within 1e-9": MET (err 0.0). Slope claim 0.7801: CONFIRMED.

## Task 2 — PF grid points + own bootstrap → MATCH; grid-min-at-φ=0 confirmed both ways

PF-A φ=−25 (claim ΔLL +0.00504 CI [+0.0017, +0.0084]):
- point: own +0.005038373917038531 (abs err 8.7e-19); pooled LL 0.6433649811794481 (err 0.0)
- own INDEPENDENT bootstrap (10,000 resamples, seed 20261005, tip-date clusters; different RNG
  consumption pattern and aggregation from the lane's): [0.0017099725811, 0.0083745509797]
  vs claimed [0.0017099725811, 0.0083745509797] — abs err 2.2e-19 / 8.7e-19, i.e. last-ulp,
  far inside the 5e-4 Monte-Carlo tolerance. A scheme-faithful replication of the lane's
  documented 1000-chunk/np.add.at pattern also agrees to ~1e-18 (not bit-exact only because
  A7's LL uses log1p(-pc) vs the lane's log(1-pc)).
- CI entirely > 0 ⇒ non-zero φ DEGRADES the model: confirmed.

PF-B φ=+25 (claim +0.00425 [+0.0015, +0.0071]):
- point: own +0.004247277631594098 (abs err 8.7e-19); pooled LL 0.6425738848940037 (err 0.0)
- own independent CI [0.0014798661131, 0.0071180060209] vs claimed — abs err ≤ 8.7e-19.

Full 3×5 grid recomputed with own code: every ledger pooled LL matches, max abs err 1.1102e-16
(PF-B|phi=−25). Pooled-LL minimum over each arm's 5-point grid sits at φ=0 in BOTH the ledger
and the A7 recompute (PF-A / PF-B / PF-C all: min at 0). Standardization moments recomputed
from bytes match the pinned table to last-ulp (population n=14,118 team-side rows,
tip_utc < 2021-08-01Z, ddof=0). Feature-table per-season manifest accounting reproduced:
28,374 total; future per-season {2022:2648, 2023:2642, 2024:2640, 2025:2648, 2026:2652};
capped 15,144; neutral per season {152,152,154,154,154,152} — all equal the manifest.

## Task 3 — Designed null, independent re-run → PASS

- Real fold rows (own code): p(φ=0) vs B1* p — max|Δp| = 0.0 exactly for PF-A, PF-B, PF-C.
- A7-OWN synthetic streams (own generator: variable 2–4 games/day, random rest days, 3 season
  labels, seeds 101/202/303 — construction deliberately different from the lane's): max|Δp| = 0.0
  exactly on all three. φ=0 ≡ B1* byte-identity confirmed independently.

## Task 4 — Cap audit → PASS

Code-read (harness.py): `SEASON_MAX_REAL=2021` (line 72) wired into run_select →
SelectionContext → `load_schedule` (per-file assertion: any row outside [2016,2021] ⇒
TechAbort SEASON_CAP_VIOLATION, lines 118–125; future files 2022–2026 never opened, listed
as skipped, lines 127–130) and `load_features` (sha256 assertion, 28,374-row assertion,
future per-season accounting equality, slice to ≤2021 with 15,144-row assertion, lines
152–178). `mode_evaluate_oos(real_data=True)` raises before ANY data path is touched
(lines 1116–1131).

A7 probes (own driver, doctoring only on tmp copies):
- Doctored 2022 row inside a full-range tmp copy (2016–2021) ABORTS:
  `SEASON_CAP_VIOLATION: file nba_schedule_2021.csv carries 1 row(s) with season outside
  [2016,2021] (observed [2022]); hard cap SEASON_MAX_REAL=2021`.
- Healthy copy passes: max observed season 2021, 7616 rows.
- `evaluate-oos --real` exits 1 with `OOS_REFUSED_NO_GO_TOKEN`; GO token path absent on disk.
- Lane `--selftest`: 39/39 PASS, exit 0 (corroborates the handoff claim).

## Task 5 — Ledger completeness → PASS

- 18 rows exactly = 15 pre-registered grid configs (3 arms × φ∈{−50,−25,0,25,50}) + B0 + B1*
  + B1-HCA0; zero unexpected rows.
- Grid constants in code == dispatch packet (asserted by import): PHI_GRID (−50,−25,0,25,50),
  PF_GROUPS (PF-A/PF-B/PF-C), K=32, HCA=100, γ=0.75, μ=1500, seed 20261005, 10,000 resamples,
  slope band [0.85,1.15], group columns PF-A z(a_top5_share_k5)+z(a_load_top5_k5),
  PF-B z(b_form_top3), PF-C z(c_abs_out)+z(c_abs_streak). No post-hoc tampering: the grid in
  code equals the dispatch pre-registration, and the ledger equals A7's independent recompute.
- No un-counted fits: the code path evaluates exactly the 15 configs (one ledger row each) +
  2 references + 1 diagnostic; 4 B0 refits; 2 Elo replays (B1*, B1-HCA0; PF arms share the
  B1* stream — φ enters only the argument); 6 twin evaluations declared outside budget;
  playoff segment (n=332) scored with frozen models, reported separately, never in criterion.
- Determinism corroboration: lane ledger sha256 0ede824fb0de4d4dde6a711e17cbc2668bcce5325732b6996150192882152492
  == data-dir copy == handoff claim; VERDICT_TABLE 72b6a4e8… == data-dir copy == claim.

## Task 6 — Honesty audit → PASS

- Twins-winning diagnostics DISCLOSED, not hidden: SELECTION_REPORT "Diagnostics" section
  reports PF-A φ=−25 parent 0.643365 vs twin 0.641190 (WINS), PF-B φ=25 parent 0.642574 vs
  twin 0.641048 (WINS), PF-C no win — framed as machinery/noise disclosure; the same
  `twin_wins: true` sits in the ledger rows (PF-A|phi=−25, PF-B|phi=25) and in the handoff
  `known_limitations` ("non-zero configs are noise, not stable feature cost"). The winning
  twins do not change any verdict (they fired only on non-selected, already-doomed configs).
- B1* slope 0.780102170044627 disclosed (report B1* section + verdict table); the out-of-band
  [0.85,1.15] consequence is carried in the arm reasons and handoff limitations.
- Language: calibration/forecasting vocabulary only; no betting vocabulary in lane artifacts.

## VERDICT

**NEGATIVE_VERIFIED.** The negative is evidence-hardened: with a fully independent
implementation, B1* pooled LL and slope reproduce exactly; both named grid points and their
pinned-seed CIs reproduce to last-ulp; every non-zero φ in all three grids increases pooled
fold LL vs B1*; each grid's minimum is its own φ=0 designed null; the designed null is
byte-identical on real rows and on A7's own synthetic streams; the season cap, OOS refusal
and GO-token absence all hold; the ledger is complete with no un-counted fits; and the
unfavorable twin diagnostics are disclosed. No defect found.

Minor notes (non-defects):
- CI bounds agree to ~1e-18, not bit-exact: A7's LL uses log1p(-pc) vs the lane's log(1-pc).
  Conclusions unaffected (bounds are ≥ +0.0015 from zero).
- A7 did not re-run the lane's `select` mode; the independent recompute supersedes it.
- The moment population includes some season-2021-labeled rows with tip before the cutoff;
  A7's independent construction reproduces the pinned moments exactly, so the lane used the
  same effective population (no discrepancy).
