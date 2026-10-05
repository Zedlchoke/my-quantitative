# FREEZE PACKET — DRAFT (NFL-WINPROB-NG-PREP-V1 output; NOT a freeze)

Status: DRAFT for the owner decision packet. Nothing here is frozen; the real freeze happens
inside the successor scored cycle at its own gate, with fresh A7 + owner typed GO (P-8).
Evidence chain: lanes A/A-r1/B/C/D/D-r2 landed; integration head at time of writing e8333253.

## 1. Arms (≤9, binding enumeration at real freeze)

| slot | arm | status |
|---|---|---|
| 1 | B0 constant p=league-base-rate | mandatory anchor |
| 2 | B1* own-Elo K=40, HCA=0, γ=2/3 | MANDATORY baseline (frozen from NFL-WINPROB-SCORED-V1; never re-fit) |
| 3 | C1 SOS-adjusted Elo (R̃ = R − β·(SOS − mean), β train-internal then frozen) | candidate |
| 4 | C2 home/away split rating (λ shrink train-internal; designed-null parent = B1*) | candidate |
| 5 | C3 offseason EPA prior train-only (θ; pbp post-game compiled — train-only role only) | candidate |
| 6 | C4 short-week×away interaction | CONDITIONAL on G-INT train-internal gate (power predicts starvation); else released |
| 7 | reserve — must be NAMED in this packet's real-freeze successor before any prospective look | open |
| 8–9 | RELEASED at freeze; never reallocated | fixed |

Negative controls (time-shuffled twins per candidate) are diagnostic arms: reported, never
counted as candidate wins. Rejected families stay dead (MOV-weighted Elo, K/HCA/rest/form
re-grids, additive logistic-over-elo_diff, in-season pbp, 538/odds/current-box).

## 2. Injury/availability

NOT_RUN_PIT — carried from lane A verdicts (r1 re-confirmed): nflverse injuries schema has NO
publish-timestamp column; depth_charts/weekly_rosters unproven. No availability arm; no
retro-fill from any source, ever. Re-audit only in a future prep round on explicit evidence.

## 3. Data + windows

- Source: nflverse releases, CC BY 4.0 (LICENSE sha256 2a82ac9b… pinned; §2(a)(1) and §3(a)(1)(A)
  quoted verbatim post-r1; attribution chain in raw/ATTRIBUTION.md + DOWNLOAD_MANIFEST.md).
  Raw+derived outside git: ~/.my-quantitative-data/nfl-nflverse-v1/ (terminal-cycle archive,
  untouched) + nfl-ng-prep-v1/ (this cycle, 15 pinned files incl. r1 refresh).
- TRAIN (train-internal selection territory): audited complete seasons 2000–2018 (1999 excluded:
  gametime 100% missing). 2019–2025 = SPENT (cite-only). 2026+ = PROSPECTIVE ONLY via the ledger.
- 2026 status at r1 recount (2026-10-05T07:16:19Z; verifier-r2 independently reproduced at
  07:23:28Z): 272 scheduled REG; 63 played (all with final scores) → NOT_RUN prospective
  forever; 209 future (0 scored); earliest future kickoff 2026-10-06T00:15:00Z (2026_04_ATL_NO).

## 4. Prediction ledger (nfl_ng_ledger@1)

Tool: research/control/NFL-WINPROB-NG-PREP-V1/ledger/nfl_ng_ledger.py — append-only JSONL,
flock+fsync, sha256 hash chain from a freeze GENESIS record, no outcome columns (closed field
set + blocklist), recorded_at_utc < kickoff_utc enforced at append AND at scoring vs ACTUAL
kickoffs, postponement/cancellation as chained notice rows, no rewrite/delete API. 42/42
SYNTHETIC tests pass (verifier r2 re-ran them and ran 4 adversarial probes of its own).
O-2 restatement (binding at real freeze): scoring-time row classes include row-level NOT_RUN
and NOT_SCORED_NO_ACTUAL_DATA (lane-E disclosed vocabulary; schema-faithful). Weekly batch
cadence with ≥6h margin before first kickoff UTC is the placeholder until the freeze names the
recorder and margin.

## 5. Metrics, uncertainty, gates

Log loss primary; Brier + 10-bin reliability + calibration slope (band [0.85, 1.15]) secondary;
paired ΔLL with kickoff-date-clustered bootstrap, 10,000 resamples, seed 20261005 (inherited);
T1/T2/T3 gate shape inherited from the terminal protocol; R1–R3 negative-terminal thresholds
re-stated verbatim at real freeze; playoffs reported separately, never pooled.

## 6. Power disclosure (binding language for the successor plan)

One NFL regular season ≈ 272 games. Measured paired CI calibration (lane B POWER_NOTES):
MDD(80%) ≈ 0.026–0.056 at 1 season; 0.019–0.039 at 2 seasons (~540); ~0.006–0.013
train-internal (~4,839 games). Plausible single-mechanism effects (ΔLL 0.002–0.010) are
STARVED at 1 season; 2 seasons adjudicates only ≥~0.02. Therefore: train-internal adjudication
FIRST; prospective accrual is an evidence accumulator, not a 1-season verdict; STRONG
conclusions require ≥2 completed prospective seasons; no outcome-based early stopping (decision
reads once per completed season; prospective aborts are operational only).

## 7. Open items the real freeze must bind (cannot be pre-filled here)

(1) successor cycle_id + plan + registered GO phrase; (2) train-internal selection results
(β for C1, λ for C2, θ for C3, C4 G-INT verdict) computed inside the successor cycle on TRAIN;
(3) reserve arm identity (slot 7) before any prospective look; (4) recorder + cadence + margin;
(5) GENESIS digest (created at freeze); (6) final TRAIN season list confirmation from the
freshest lane-A coverage at that time.
