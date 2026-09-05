# A7-N AUDIT HANDOFF — cycle FOREX-FREE-V4 (novelty / anti-rescue)

Auditor: A7-N (independent). Branch `orca/forex-free-v4-d2-a7-novelty`, base
`0a34678aafcb0a0b4626d1ea231bf13f6a6731d2` (verified). Audit UTC
2026-09-05T05:19:31Z. I wrote audit artifacts only; I repaired nothing and
computed no PnL anywhere.

## 0. What was measured and how (bytes, not prose)

The mandated ancestry measurement reconstructs DECISION SERIES (per pair, per
daily 16:00 America/New_York decision clock: signed direction in {-1, 0, +1};
no PnL) for:

- **V3 family2 (FXFV3-A6-P1) anchor, two variants**, by importing the frozen
  `research/assets/forex_free_v3/family2.py` READ-ONLY from the V3 worktree
  and driving it with the frozen `PolicyRateReader`:
  - variant (a) as-scored: V3 asserted-bound vintages
    `data_raw/forex_free_v3_macro` (V3 tree);
  - variant (b) evidenced-corrected: `data_raw/forex_free_v3r_macro_evidenced`
    (V3R tree).
  Both variants share the identical price side (H1 snapshot) and identical
  220-valid-NY-day warmup; only the vintage availability differs.
- **FXFV4-A4-P1** (kappa = 48 bps budget sizing, 0.10 hysteresis,
  exit-on-flip/zero) over the P0a evidenced vintages (v2 ledger pin
  `ae5e1f2e...` — sha256 verified against `LEDGER_PINNED`).
- **FXFV4-A4-P2** (event-anchored entries >= 48 bps, H = 63, event-exit
  < 24 bps, crash unwind 2.5x/63-median x2 clocks + lockout) over ledger
  events deduped (area, effective_date) LAST-ROW-WINS + snapshot closes.
- **FXFV4-A6-P2** (policy-change drift, delta sign at availability, H = 10
  NY-days, US drives all 7 long-USD on hike, first_ok 2020-02-11).

Certification, all recorded in `a7_n_measurements_raw.json`:

1. My mirrored family2 walk reproduces the frozen `_schedule_pair` trips
   EXACTLY (7/7 pairs, both variants).
2. The V3R `decision_diff_table.json` is replicated ROW-EXACTLY by my two
   vintage readers: 158 differing readable-rate cells / 19 sign flips,
   identical row sets.
3. All 8 P0a evidenced-vintage canonical sha256 match both the V4 tree
   manifest and the worktree `p0a_evidenced_vintages_manifest.json`.
4. Interpretation of (2): the 158/19 availability differences land almost
   entirely outside family2's in-market states — the ancestor variant (a)
   vs (b) decision panels agree at rho 0.9993. The correction changed the
   contract, not the direction series.

## 1. Declared bar (frozen BEFORE measurement)

Written to `A7_N_DECLARED_BAR.md` before the measurement script first ran.
Gating statistic: **Spearman rho over ACTIVE shared cells** (both books
non-flat) — "when both books are in the market, do they point the same way".
|rho| < 0.5 with n_active >= 30 admits novelty; 0.5–0.7 CONDITIONAL;
> 0.7 = re-grade = REJECT; n < 30 INDETERMINATE. rho_full (flats included)
reported as a non-gating diagnostic. Front door: REJECTED if the bar is
breached vs EITHER ancestor variant.

## 2. Rho table (all comparisons)

| comparison | n_shared (total/active) | rho_gating (active) | rho_full | agreement (active) | verdict |
|---|---|---|---|---|---|
| A4-P1 vs F2 (a) as-scored | 9491 / 5335 | **1.000** | 0.750 | 100.0% | REJECT_RE_GRADE |
| A4-P1 vs F2 (b) evidenced | 9491 / 5335 | **1.000** | 0.750 | 100.0% | REJECT_RE_GRADE |
| A4-P2 vs F2 (a) as-scored | 9491 / 2283 | **0.9974** | 0.464 | 99.87% | REJECT_RE_GRADE |
| A4-P2 vs F2 (b) evidenced | 9491 / 2283 | **0.9991** | 0.465 | 99.96% | REJECT_RE_GRADE |
| A6-P2 vs F2 (a) as-scored | 9491 / 768 | **0.0537** | 0.013 | 52.7% | NOVELTY_PASS |
| A6-P2 vs F2 (b) evidenced | 9491 / 768 | **0.0538** | 0.013 | 52.7% | NOVELTY_PASS |
| F2 (a) vs F2 (b) [control] | 9491 / 5338 | 0.9993 | 0.999 | 99.96% | (control, not an admission test) |

The A4-P2 diagnostic divergence (rho_full 0.46 < 0.5 vs gating 0.997) is a
participation artifact, not direction novelty: A4-P2 holds through vol
(24% of shared cells active) while family2 goes flat in HIGH states (56%
active); A4-P2 overlaps ALL of family2's active cells and agrees on
direction ~99.9% of them. The declared bar assigns the decision to the
gating statistic; both numbers are in the owner block.

## 3. Front-door admission decision (numbers to owner, either way)

- **FXFV4-A4-P1: REJECTED.** rho 1.000 vs both variants. Its book holds
  EXACTLY the ancestor's direction at every one of the 5335 shared
  in-market decision cells. The financing-budget sizing, kappa scaling and
  event hysteresis are size/timing machinery over the same direction
  series. A V4 survivor would re-grade the invalidated ancestor — forbidden
  by definition (PLAN section 1 item 4).
- **FXFV4-A4-P2: REJECTED.** rho 0.997/0.999 vs both variants. Fixed
  horizon, crash unwind and lockout change holding duration and exit
  timing, not direction; in-market direction agreement is ~99.9%.
- **The section-1.1 carry front door is CLOSED for FOREX-FREE-V4.** Any
  future front-door plan must be directionally distinct from the
  differential-carry direction, not merely cost-relieved.

## 4. Per-proposal novelty verdicts

| proposal | verdict | basis |
|---|---|---|
| FXFV4-A4-P1 | **NOVELTY_FAIL** | measured: rho 1.000 / 1.000 (re-grade) |
| FXFV4-A4-P2 | **NOVELTY_FAIL** | measured: rho 0.9974 / 0.9991 (re-grade) |
| FXFV4-A5-P1 | **CONDITIONAL** | DATA_BLOCKED, unmeasurable (CPI leg unwired). Features distinct from all V1/V2/V3-family1 rows, but the nominal component of its signal IS the ancestor's information source (its own disclosure). Its preregistered inflation-sign-inversion placebo governs at scoring; re-measure rho when the CPI ledger extension lands. |
| FXFV4-A5-P2 | **NOVELTY_PASS** | features: zero interest-rate input anywhere — cannot be a carry descendant by construction; all four features distinct from every forbidden row (data-blocked, but novelty is not the binding question) |
| FXFV4-A6-P1 | **NOVELTY_PASS** | features: price-only cross-sectional event basket; information source, clock, control, functional form all distinct from every forbidden row; explicitly checked and excluded: sign-inversion of V1-family2, session-clock relabel, vol-gate rescue of family2 |
| FXFV4-A6-P2 | **NOVELTY_PASS** | measured (mandated for the policy-event packet): rho 0.0537 / 0.0538, active agreement 52.7% = chance level. Reads the same ledger but uses the event DELTA sign at availability — decision-level orthogonal to the ancestor. Feature table distinct on all four features vs all rows. |

The full 6-proposals x 7-forbidden-rows feature table (information source,
decision clock, causal control, signal functional form, rescue-variant
check: clock relabel / sign inversion / threshold neighbourhood / pair
subset / cost relief / control swap) is in
`a7_n_novelty_v4.json -> forbidden_rows_feature_table`.

## 5. Notes the owner should read

1. Both A4 packets disclosed their confirmatory-re-entry status honestly and
   pre-committed to dying on these numbers. The rejection is the front door
   working as designed, not a packet defect: their novelty claim (cost
   survival by construction) is real but lives entirely outside the
   direction series, and the PLAN gates ancestry on the direction series.
2. The ancestor variant control (a-vs-b rho 0.9993) plus the exact 158/19
   diff-table replication means the front-door rejection does NOT depend on
   which availability convention the ancestor is graded under.
3. A5-P1 is the only remaining carry-adjacent live family. It is
   data-blocked; when the CPI evidence lands, its measured rho vs both
   ancestor variants must be taken BEFORE any scoring, per this audit's
   CONDITIONAL verdict.
4. A6-P2's PASS is measured, not argued — but its own packet discloses a
   USD-drift gate risk (~45% of pair-events are US-area). Novelty and
   viability are different gates; this audit rules only on the former.

## 6. Limitations

Recorded verbatim in `a7_n_novelty_v4.json -> limitations`. Headlines:
decision-series only (no PnL/gates); gating-vs-full rho resolution frozen ex
ante; A4-P2 crash-estimator and H-day exit offsets have +-1-session
convention freedom (immaterial at 0.997+); A5 verdicts are feature-level
until CPI evidence exists; 138 reconstructed family2 round trips per variant
are the raw schedule book, not the runner's scored/purged population.

## 7. Artifacts (this worktree only)

- `research/audits/forex_free_v4/A7_N_DECLARED_BAR.md` — bar, written first
- `research/audits/forex_free_v4/a7_n_measurements_raw.json` — raw numbers + integrity checks
- `research/audits/forex_free_v4/a7_n_novelty_v4.json` — the audit deliverable
- `research/audits/forex_free_v4/scripts/a7n_measure.py` — measurement script (replayable against the frozen inputs)

— A7-N, 2026-09-05
