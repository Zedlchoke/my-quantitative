# D1 freeze note — FOREX-SEARCH-V1 search-space manifest (task fsearch-d1)

Cycle: FOREX-SEARCH-V1 (orchestration cycle ZCODE-ORCHESTRATION-V3).
Branch: `orca/forex-search-v1-integration`, worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration`,
base SHA `514764331cea17a610c519f5680abf3bbb25ec7b` (verified before any
work: pwd, branch, HEAD all matched the dispatch packet).

## What was frozen

`research/control/forex_search_v1_run/d1/search_space_manifest.json` — the
D1 frozen search-space contract of `plans/PLAN_forex_search_v1.md` §5,
committed BEFORE any D2 diagnostic and any scored cell (§9 D1; D2 itself is
SKIPPED per owner amendment §3b).

- ALL 33 configurations, stable lexicographic IDs `FSS-<FAMILY>-<PARAMKEY>`:
  CLV-DIVERGENCE 6 (K in {10,20,60} x slope k in {5,10}), EXTREME-FADE 3
  (K in {10,20,60}), OPEN-GAP 6 ({FADE,CONFIRM} x {Q25,Q50,Q75}), VOL-DRIFT 4
  ({MOM,REV} x {L21,L63}), CLOCK-COND 14 (5 DOW x {LONG,SHORT} + 2 MONTHPOS
  x {LONG,SHORT}). Grid total 19 + 14 = 33 <= 80; frozen DSR N = 33 declared
  at freeze time (§5).
- Per configuration: mechanism statement, fully expanded state formula, sign
  frozen from the mechanism statement (§5 direction rule — R1 adjudicates,
  never selects), single-session hold law, warmup bars + 1-based first
  decision master bar, CTL-COMPLEMENT book, R4 trend-only book, and the P0
  measured fired counts per fold (plus totals and per-leg counts) copied
  byte-equal from `p0/fired_census.json`.
- Warmup per §8 as amended: VOL-DRIFT and OPEN-GAP 252 (first decision bar
  253), CLV-DIVERGENCE / EXTREME-FADE / CLOCK-COND 60 (first decision bar
  61); complete-window fail-closed; no expanding/partial windows; warmup
  consumed inside fold 1; force-flat at fold boundary.
- Per-state per-fold population floor = 10 pinned in the manifest (§6 R2,
  frozen before any D2 measurement).
- The three P0 pins carried verbatim: (1) OPEN-GAP side-specific percentile
  reading — percentile selects the side, p=50 median split; (2) warmup/fold
  interaction per §8 amended; (3) MONTHPOS day<=15 boundary.
- §4 F4 financing derivation + caveats verbatim (NG7-A4 "~5.1 bps over 3
  nights" for NZD-USD; 5.1/3 = 1.7; a 3-night cumulative average does NOT
  bound the single worst night; NZD-USD-worst generalized to all five legs
  without a per-leg differential census, none derivable from OHLC-only TD)
  and the cost/financing constants (1.5 bps/fill + 1.7 bps/night, stress 2.0
  PRIMARY = 9.4 bps worst case per round trip), from
  `p0/cost_financing_manifest.json`.
- §3b selection tier inputs: family fired totals over the most recent fold
  (fold 3, 2020-10-06..2026-09-10): CLOCK-COND 31850 / OPEN-GAP 22672 /
  VOL-DRIFT 12294 / EXTREME-FADE 6193 / CLV-DIVERGENCE 4154, and the family
  ranking they induce under amended tier (i) DESCENDING by P0
  fired-population census with lexicographic tie-break:
  CLOCK-COND > OPEN-GAP > VOL-DRIFT > EXTREME-FADE > CLV-DIVERGENCE.
  Tier (ii) within-family config order (DESC by fold-3 fired count,
  tie-break lexicographic config ID) is frozen in the manifest.
- Fold freeze digest reference: `p0/folds_freeze.json`
  sha256 `c2a4e6765ff2ca2891b6ade8a81930a3b633024da7ba9a9eca6e46ca4965519b`,
  master dates sha256
  `e511b7dac6eeb96ee585628bb9537af7113365e5b6842474d532411fabd21964`,
  boundaries [0, 1641, 3282, 4924].
- D2 skipped per §3b: NO R0/ancestry fields — only the note that the R0
  battery is NOT_RUN by owner amendment (never an inferred PASS).
- OUTCOME-BLIND: construction + census COUNTS only. No returns, PnL, PF,
  Sharpe, drawdown, expectancy or any performance statistic appears
  anywhere in the manifest.

## Manifest hashes

- self sha256 (convention: sha256 of the exact manifest bytes with the
  `self_sha256` field set to the empty string, serialized
  `json.dumps(obj, indent=1, sort_keys=True) + "\n"`):
  `5db03cdba179d3713181fbb34638164a23e153b4706043836c611a4e7b8cfe33`
- committed file bytes sha256:
  `1b39aa6f726215df973833d1db5a8e3639aa226e62b7ce0f077c7e829c4d07b9`

## Source references

- Plan (read in full, read-only): `plans/PLAN_forex_search_v1.md` §3b, §4
  F3/F4, §5, §6, §8.
- P0 outputs (integrated lane, read-only; committed at base 51476433):
  `research/control/forex_search_v1_run/p0/{p0_gate,fired_census,
  folds_freeze,structural_census,calendar_census,cost_financing_manifest,
  manifest_pin}.json`. All seven digests re-verified byte-equal to the
  digests recorded inside `p0_gate.json` before use.
- Construction engines (authoritative formulas, read-only):
  `research/control/forex_search_v1_run/p0/p0_census.py`.
- Builder (committed, reproducible): `research/control/forex_search_v1_run/
  d1/build_d1_manifest.py` — pure function of the pinned P0 artifacts; the
  only non-deterministic field is `measured_frozen_utc`.

## Validation record (offline, no scored data touched)

Command: `python3 research/control/forex_search_v1_run/d1/build_d1_manifest.py --selfcheck`
Exit code: 0. Verdict: PASS. Checks: manifest parses; 33 configs with the
exact family split 6/3/6/4/14; IDs unique + lexicographic; per-config fired
counts byte-equal to `p0/fired_census.json` (folds, totals, per-leg);
§3b family totals match the packet-frozen numbers; family ranking correct;
per-state per-fold floor 10 pinned; 3 P0 pins verbatim; no
performance-field keys (key scan: pnl / sharpe / profit_factor / expectancy
/ drawdown / hit_rate / win_rate / payoff / survivor / scored_); self
sha256 convention verifies. `tests/` is outside this lane's allowed paths,
so no file was added there — the `--selfcheck` mode is the durable,
rerunnable validation.

## Scope

Only paths under `research/control/forex_search_v1_run/d1/`,
`research/control/forex_search_v1_run/handoffs/`, and the inbox handoff
path were written. No plans/, registry/ledger, S1, p0/, m0/, or other
lane's files touched; no performance computation; no network acquisition.
