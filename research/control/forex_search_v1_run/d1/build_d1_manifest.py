"""FOREX-SEARCH-V1 D1 search-space manifest builder + selfcheck (plan §5).

Freezes the 33-configuration search-space manifest BEFORE any D2 diagnostic
(D2 is itself SKIPPED this cycle per owner amendment §3b). OUTCOME-BLIND:
construction definitions + P0 fired-census COUNTS only — no returns, PnL,
PF, Sharpe, drawdown, expectancy or any performance statistic is computed
or stored anywhere in this module or its output.

Modes:
  (default)      build research/control/.../d1/search_space_manifest.json
  --selfcheck    offline validation of the written manifest: parses; 33
                 configs; IDs unique + lexicographic; counts byte-equal to
                 p0/fired_census.json; §3b family totals match; no
                 performance-field keys; self sha256 convention verifies.

stdlib only (python3, no third-party imports).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
RUN = WT / "research/control/forex_search_v1_run"
P0 = RUN / "p0"
D1 = RUN / "d1"
MANIFEST_PATH = D1 / "search_space_manifest.json"

BASE_SHA = "514764331cea17a610c519f5680abf3bbb25ec7b"
BRANCH = "orca/forex-search-v1-integration"

# §3b selection-tier inputs frozen by the dispatch packet (verified against
# the P0 census below — mismatch aborts fail-closed).
PACKET_FAMILY_FIRED_RECENT_FOLD = {
    "CLOCK-COND": 31850,
    "OPEN-GAP": 22672,
    "VOL-DRIFT": 12294,
    "EXTREME-FADE": 6193,
    "CLV-DIVERGENCE": 4154,
}
RECENT_FOLD = "3"

FLOOR_PER_STATE_PER_FOLD = 10  # §6 R2, pinned in THIS manifest before any D2

# performance-statistic key tokens banned from the manifest (outcome-blind
# law, §5: "NO return, expectancy, PF, Sharpe or any performance statistic
# may be computed for ANY configuration before the S freeze").
FORBIDDEN_KEY_TOKENS = (
    "pnl", "sharpe", "profit_factor", "expectancy", "drawdown",
    "hit_rate", "win_rate", "payoff", "survivor", "scored_",
)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def canon(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode()


# --------------------------------------------------------------- load + verify

def load_p0() -> dict:
    need = ["fired_census.json", "folds_freeze.json", "cost_financing_manifest.json",
            "p0_gate.json", "structural_census.json", "calendar_census.json",
            "manifest_pin.json"]
    art = {n: json.loads((P0 / n).read_text()) for n in need}
    # fail-closed: every digest recorded in the P0 gate must match the bytes
    for name, dig in art["p0_gate.json"]["artifact_sha256"].items():
        actual = sha256_file(P0 / name)
        if actual != dig:
            raise SystemExit(f"FATAL: digest mismatch {name}: {actual} != {dig}")
    return art


# ---------------------------------------------------------------- construction

def warmup_block() -> dict:
    return {
        "rule_verbatim_s8_amended": (
            "decision: frozen 16:00-NY daily clock; warmup = max(60, the "
            "family's LARGEST state-formation window INCLUDING auxiliary "
            "trailing distributions): VOL-DRIFT = max(L, 252) = 252 and "
            "OPEN-GAP = 252 — tercile boundaries and gap percentiles each "
            "consume a trailing 252-bar window — so first decision bar 253 "
            "for both; CLV-DIVERGENCE, EXTREME-FADE, CLOCK-COND = 60 (first "
            "decision bar 61); a state that cannot be formed from COMPLETE "
            "windows is NOT FIRED — fail-closed; no expanding-window or "
            "partial-window convention exists anywhere in this cycle; "
            "pinned per family in the D1 manifest"),
        "warmup_bars_by_family": {
            "VOL-DRIFT": 252, "OPEN-GAP": 252,
            "CLV-DIVERGENCE": 60, "EXTREME-FADE": 60, "CLOCK-COND": 60,
        },
        "first_decision_bar_1based_master_by_family": {
            "VOL-DRIFT": 253, "OPEN-GAP": 253,
            "CLV-DIVERGENCE": 61, "EXTREME-FADE": 61, "CLOCK-COND": 61,
        },
        "fold_interaction": (
            "warmup consumed inside fold 1; force-flat at fold boundary by "
            "construction (a firing counts only if the leg's own execution "
            "bar t+1 lies in the SAME fold as its decision bar t)"),
        "complete_window_fail_closed": (
            "no expanding or partial windows anywhere; VOL-DRIFT estimator "
            "windows additionally delay first firing to own-index >= L+251 "
            "(declared; supersedes the §8 warmup bar when later) — P0 pin #2"),
        "measured_by_p0_gate_warmup_first_decision_bar": {
            "CLOCK-COND": 61, "CLV-DIVERGENCE": 61, "EXTREME-FADE": 61,
            "OPEN-GAP": 253, "VOL-DRIFT": 253,
        },
    }


def family_blocks() -> dict:
    return {
        "CLV-DIVERGENCE": {
            "family": "CLV-DIVERGENCE",
            "plan_s5_definition": (
                "fresh K-bar close extreme + divergent 20-bar CLV pressure "
                "slope, K in {10, 20, 60} x slope window k in {5, 10} "
                "(NG7 anchor class, grid-extended)"),
            "param_grid": {"K": [10, 20, 60], "slope_k": [5, 10]},
            "param_source": "construction logic (Q-12); declared from the "
                            "mechanism, never tuned",
            "warmup_bars": 60,
            "first_decision_bar_1based_master": 61,
            "state_formula_template": (
                "CLV[i] = ((C[i]-L[i])-(H[i]-C[i]))/(H[i]-L[i]) (CLV = 0 "
                "when H[i] == L[i]); pressure20[i] = sum of CLV over the "
                "trailing 20 bars ending at and including i; slope s = "
                "pressure20[i] - pressure20[i-k] (complete windows only — "
                "if either window is incomplete the state is NOT FIRED, "
                "fail-closed); fresh_high = C[i] >= max of C over the "
                "trailing K bars ending at i; fresh_low = C[i] <= min of C "
                "over the trailing K bars ending at i"),
            "ctl_complement": (
                "CONFIRMED book (declared ex ante): same fresh-K-bar-close-"
                "extreme trigger on the NON-divergent side of the slope — "
                "fresh HIGH with s >= 0 -> LONG; fresh LOW with s <= 0 -> "
                "SHORT (pressure confirms the extreme; the divergence "
                "ingredient is absent). Same warmup (60), same holds"),
            "r4_trend_only_book": (
                "conditioning variable alone: the 20-bar CLV pressure slope "
                "traded without the fresh-extreme trigger — s > 0 -> LONG; "
                "s < 0 -> SHORT; warmup 60"),
        },
        "EXTREME-FADE": {
            "family": "EXTREME-FADE",
            "plan_s5_definition": (
                "fresh K-bar extreme faded, K in {10, 20, 60} — the causal "
                "complement direction"),
            "param_grid": {"K": [10, 20, 60]},
            "param_source": "construction logic (Q-12); declared from the "
                            "mechanism, never tuned",
            "warmup_bars": 60,
            "first_decision_bar_1based_master": 61,
            "state_formula_template": (
                "fresh_high = C[i] >= max of C over the trailing K bars "
                "ending at i; fresh_low = C[i] <= min of C over the "
                "trailing K bars ending at i (complete windows only — "
                "otherwise NOT FIRED, fail-closed)"),
            "ctl_complement": (
                "CONFIRMED book (declared ex ante): fresh K-bar close HIGH "
                "-> LONG; fresh LOW -> SHORT (continuation instead of "
                "fade; identical trigger, opposite direction). Same "
                "warmup (60), same holds"),
            "r4_trend_only_book": (
                "conditioning variable alone: the K-bar trend itself — "
                "C[i] - C[i-K] > 0 -> LONG; < 0 -> SHORT (fresh-extreme "
                "state traded WITHOUT the fade direction component). "
                "Disclosed identity: this equals the family's CTL-"
                "COMPLEMENT confirm book"),
        },
        "OPEN-GAP": {
            "family": "OPEN-GAP",
            "plan_s5_definition": (
                "opening-gap fade and confirm vs prior close, gap size "
                "threshold at {25th, 50th, 75th} percentile of the "
                "trailing 252-bar SIGNED-gap distribution (gap_t = open_t "
                "- close_{t-1}, SIGNED; the absolute-value reading is "
                "FORBIDDEN)"),
            "param_grid": {"mode": ["CONFIRM", "FADE"], "pct": [25, 50, 75]},
            "param_source": "construction logic (Q-12); declared from the "
                            "mechanism, never tuned",
            "warmup_bars": 252,
            "first_decision_bar_1based_master": 253,
            "state_formula_template": (
                "gap g[i] = O[i] - C[i-1], SIGNED; trigger level q = "
                "SIGNED quantile at p/100 (linear interpolation) of the "
                "trailing 252-gap window ending at and including g[i]; "
                "side selection PIN (P0 pin #1): the percentile ITSELF "
                "selects the side — p < 50 is a DOWN-tail level (state "
                "fires when g[i+1] <= q); p > 50 is an UP-tail level "
                "(fires when g[i+1] >= q); p = 50 is the MEDIAN split "
                "(fires when g[i+1] crosses the median in either "
                "direction; g[i+1] == median does not fire). Timing "
                "exception (§4 F3): state formed from close(t) and "
                "open(t+1), knowable exactly at bar t+1's open; the "
                "forced fill AT that same open(t+1) is the ONE declared "
                "exception to the no-same-bar-signal-fill rule (the fill "
                "price IS the first bookable price — no look-ahead); "
                "exit mapping: any exit condition knowable at a bar close "
                "executes at the next bar's open; state NOT FIRED when "
                "the 252-gap window is incomplete or no execution bar "
                "t+1 exists in the same fold (fail-closed)"),
            "ctl_complement": (
                "CONFIRMED book (declared ex ante): identical trigger and "
                "threshold traded in the CONFIRM direction — "
                "CTL-COMPLEMENT(FADE-Qp) = CONFIRM-Qp and "
                "CTL-COMPLEMENT(CONFIRM-Qp) = FADE-Qp (both enumerated in "
                "the grid); adjudicated from the same census machinery"),
            "r4_trend_only_book": (
                "conditioning variable alone: the SIGNED gap traded "
                "without threshold or fade direction — g[i+1] > 0 -> "
                "LONG; g[i+1] < 0 -> SHORT (up-gap -> LONG, down-gap -> "
                "SHORT, no percentile trigger)"),
        },
        "VOL-DRIFT": {
            "family": "VOL-DRIFT",
            "plan_s5_definition": (
                "realized-vol tercile-conditional 1-session momentum and "
                "reversal, lookback {21, 63}; tercile formation CAUSAL, "
                "pinned: estimator = close-to-close log-return SAMPLE std "
                "(ddof=1) over the trailing lookback L; boundaries = 1/3 "
                "and 2/3 quantiles (linear interpolation) of the TRAILING "
                "252-bar window ending at and including bar t, refreshed "
                "daily, same-bar assignment — NEVER full-sample "
                "(look-ahead class)"),
            "param_grid": {"mode": ["MOM", "REV"], "L": [21, 63]},
            "param_source": "construction logic (Q-12); regime pin from "
                            "mechanism (MOM conditions on LOW tercile — "
                            "drift persists in calm regimes; REV on HIGH "
                            "tercile — overreaction corrects in stressed "
                            "regimes), never tuned",
            "warmup_bars": 252,
            "first_decision_bar_1based_master": 253,
            "state_formula_template": (
                "vol[i] = SAMPLE std (ddof=1) of close-to-close log "
                "returns over the trailing L returns ending at and "
                "including i; tercile boundaries b1 = 1/3 quantile and "
                "b2 = 2/3 quantile (linear interpolation) of the trailing "
                "252-bar window of the SAME estimator ending at and "
                "including i — CAUSAL, refreshed daily, same-bar "
                "assignment, NEVER full-sample (look-ahead class); LOW "
                "tercile: vol[i] <= b1; HIGH tercile: vol[i] >= b2; r = "
                "C[i] - C[i-L]; complete-window law: first possible "
                "firing at own-index >= L+251 (declared), otherwise the "
                "state is NOT FIRED (fail-closed)"),
            "ctl_complement": (
                "COMPLEMENT book (declared ex ante): the same position "
                "map with the tercile condition flipped — "
                "CTL-COMPLEMENT(MOM-L) = the MOM-L position map applied "
                "on HIGH-tercile days; CTL-COMPLEMENT(REV-L) = the REV-L "
                "position map applied on LOW-tercile days (condition-"
                "flip book; not an enumerated grid configuration)"),
            "r4_trend_only_book": (
                "conditioning variable alone: the L-bar price change "
                "traded unconditionally — r = C[i] - C[i-L] > 0 -> LONG; "
                "r < 0 -> SHORT (no vol-tercile conditioning)"),
        },
        "CLOCK-COND": {
            "family": "CLOCK-COND",
            "plan_s5_definition": (
                "day-of-week / month-position conditional drift, "
                "ENUMERATED: 5 weekday states + 2 month-position states "
                "(first-half / second-half of month), each in both "
                "directions = 14 configurations (grid total 19 + 14 = 33 "
                "<= 80; exact count declared so the frozen DSR N is "
                "unambiguous at freeze time); declared EXPECTED-TO-DIE "
                "at R5; included so the search is honest about what the "
                "clock explains"),
            "param_grid": {"dow": [1, 2, 3, 4, 5], "monthpos": ["FIRST", "SECOND"],
                           "direction": ["LONG", "SHORT"]},
            "param_source": "enumerated per plan §5 (both directions as "
                            "distinct configurations inside the cap)",
            "warmup_bars": 60,
            "first_decision_bar_1based_master": 61,
            "state_formula_template_dow": (
                "state = (ISO weekday of the decision date D == dow); "
                "fires on every such session after warmup; fixed "
                "direction; no price input. ISO 1=Monday..7=Sunday; the "
                "grid enumerates trading weekdays 1..5 only"),
            "state_formula_template_monthpos": (
                "state = (day-of-month of the decision date D <= 15) for "
                "FIRST / (day-of-month >= 16) for SECOND — MONTHPOS "
                "day<=15 boundary PIN (P0 pin #3); fires on every such "
                "session after warmup; fixed direction; no price input"),
            "ctl_complement": (
                "COMPLEMENT book (declared ex ante): the same fixed "
                "direction traded on all sessions NOT in the state "
                "(complement calendar day-set), same warmup"),
            "r4_trend_only_book": (
                "NO trend/vol conditioning-variable analog exists (the "
                "state variable is the calendar position itself, not a "
                "price series; removing the direction component leaves "
                "no tradeable book) -> R4 NOT_ADJUDICABLE for this "
                "family, disclosed, never an inferred PASS (§6 R4)"),
            "expected_to_die_at_r5": True,
        },
    }


def build_configurations(fam: dict) -> list:
    """The 33 configurations, IDs stable + lexicographic (sorted)."""
    cfgs = []
    for K in (10, 20, 60):
        for k in (5, 10):
            cfgs.append({
                "config_id": f"FSS-CLV-DIVERGENCE-K{K}-S{k}",
                "family": "CLV-DIVERGENCE",
                "parameters": {"K": K, "slope_k": k},
                "mechanism_statement": (
                    f"A fresh {K}-bar close extreme that DIVERGES from the "
                    f"20-bar close-location-value (CLV) pressure slope "
                    f"marks exhaustion: price prints a new {K}-bar close "
                    f"high while CLV pressure is falling (slope s < 0) -> "
                    f"SHORT; price prints a new {K}-bar close low while "
                    f"CLV pressure is rising (s > 0) -> LONG"),
                "state_formula": fam["CLV-DIVERGENCE"]["state_formula_template"].replace(
                    "trailing K bars", f"trailing {K} bars").replace(
                    "pressure20[i-k]", f"pressure20[i-{k}]"),
                "sign_frozen": (
                    "fires SHORT when fresh_high AND s < 0 (bearish "
                    "divergence); fires LONG when fresh_low AND s > 0 "
                    "(bullish divergence); otherwise NOT FIRED"),
            })
    for K in (10, 20, 60):
        cfgs.append({
            "config_id": f"FSS-EXTREME-FADE-K{K}",
            "family": "EXTREME-FADE",
            "parameters": {"K": K},
            "mechanism_statement": (
                f"A fresh {K}-bar close extreme is over-extended and "
                f"mean-reverts over the next session: fade the fresh high "
                f"(SHORT) / fade the fresh low (LONG)"),
            "state_formula": fam["EXTREME-FADE"]["state_formula_template"].replace(
                "trailing K bars", f"trailing {K} bars"),
            "sign_frozen": (
                "fires SHORT when fresh_high; fires LONG when fresh_low; "
                "otherwise NOT FIRED"),
        })
    for mode in ("CONFIRM", "FADE"):
        for pct in (25, 50, 75):
            if pct < 50:
                side = ("DOWN-tail level: fires when g[i+1] <= q")
            elif pct > 50:
                side = ("UP-tail level: fires when g[i+1] >= q")
            else:
                side = ("MEDIAN split: fires when g[i+1] crosses the "
                        "median in either direction")
            if mode == "FADE":
                sign = ("up-gap -> SHORT; down-gap -> LONG (gap "
                        "over-extension faded back toward the prior close)")
            else:
                sign = ("up-gap -> LONG; down-gap -> SHORT (gap "
                        "information persists through the session)")
            cfgs.append({
                "config_id": f"FSS-OPEN-GAP-{mode}-Q{pct}",
                "family": "OPEN-GAP",
                "parameters": {"mode": mode, "pct": pct},
                "mechanism_statement": (
                    f"An opening gap beyond the {pct}th percentile of the "
                    f"trailing 252-bar SIGNED-gap distribution over-"
                    f"extends ({mode} mechanism)"),
                "state_formula": (
                    fam["OPEN-GAP"]["state_formula_template"].replace(
                        "p/100", f"{pct}/100")),
                "sign_frozen": f"{side}; direction: {sign}",
            })
    for mode in ("MOM", "REV"):
        for L in (21, 63):
            if mode == "MOM":
                sign = ("conditions on the LOW realized-vol tercile "
                        "(drift persists in calm regimes): r > 0 -> LONG; "
                        "r < 0 -> SHORT; otherwise NOT FIRED")
                mech = (f"One-session drift persists in calm regimes: in "
                        f"the LOW tercile of realized volatility "
                        f"(estimator lookback L={L}), the {L}-bar price "
                        f"direction continues")
            else:
                sign = ("conditions on the HIGH realized-vol tercile "
                        "(overreaction corrects in stressed regimes): "
                        "r > 0 -> SHORT; r < 0 -> LONG; otherwise NOT FIRED")
                mech = (f"Overreaction corrects in stressed regimes: in "
                        f"the HIGH tercile of realized volatility "
                        f"(estimator lookback L={L}), the {L}-bar price "
                        f"direction reverses")
            cfgs.append({
                "config_id": f"FSS-VOL-DRIFT-{mode}-L{L}",
                "family": "VOL-DRIFT",
                "parameters": {"mode": mode, "L": L},
                "mechanism_statement": mech,
                "state_formula": fam["VOL-DRIFT"]["state_formula_template"].replace(
                    "trailing L returns", f"trailing {L} returns").replace(
                    "C[i-L] > 0", f"C[i-{L}] > 0").replace(
                    "C[i-L] < 0", f"C[i-{L}] < 0").replace(
                    "C[i-L]", f"C[i-{L}]").replace(
                    "own-index >= L+251", f"own-index >= {L}+251"),
                "sign_frozen": sign,
            })
    for d in (1, 2, 3, 4, 5):
        for direction in ("LONG", "SHORT"):
            cfgs.append({
                "config_id": f"FSS-CLOCK-COND-DOW{d}-{direction}",
                "family": "CLOCK-COND",
                "parameters": {"dow": d, "direction": direction},
                "mechanism_statement": (
                    f"Calendar-conditioned drift: sessions on ISO weekday "
                    f"{d} drift {'up' if direction == 'LONG' else 'down'} "
                    f"at the next session (fixed direction; the clock is "
                    f"the only input)"),
                "state_formula": fam["CLOCK-COND"]["state_formula_template_dow"].replace(
                    "== dow", f"== {d}"),
                "sign_frozen": (
                    f"fixed direction {direction} on every fired session; "
                    f"both directions enumerated as distinct "
                    f"configurations; declared EXPECTED-TO-DIE at R5"),
            })
    for half in ("FIRST", "SECOND"):
        for direction in ("LONG", "SHORT"):
            cfgs.append({
                "config_id": f"FSS-CLOCK-COND-MONTHPOS-{half}-{direction}",
                "family": "CLOCK-COND",
                "parameters": {"monthpos": half, "direction": direction},
                "mechanism_statement": (
                    f"Calendar-conditioned drift: sessions in the "
                    f"{'first' if half == 'FIRST' else 'second'} half of "
                    f"the month "
                    f"({'day <= 15' if half == 'FIRST' else 'day >= 16'}) "
                    f"drift {'up' if direction == 'LONG' else 'down'} at "
                    f"the next session (fixed direction; the clock is the "
                    f"only input)"),
                "state_formula": fam["CLOCK-COND"]["state_formula_template_monthpos"].replace(
                    "for FIRST / (day-of-month >= 16) for SECOND",
                    f"= ({'day-of-month <= 15' if half == 'FIRST' else 'day-of-month >= 16'})"),
                "sign_frozen": (
                    f"fixed direction {direction} on every fired session; "
                    f"both directions enumerated as distinct "
                    f"configurations; declared EXPECTED-TO-DIE at R5"),
            })
    if len(cfgs) != 33:
        raise SystemExit(f"FATAL: enumeration produced {len(cfgs)} configs")
    return sorted(cfgs, key=lambda c: c["config_id"])


def attach(cfgs: list, fams: dict, census: dict, p0_gate: dict, folds: dict,
           census_sha: str) -> list:
    census_cfgs = census["per_config"]
    if set(c["config_id"] for c in cfgs) != set(census_cfgs):
        raise SystemExit("FATAL: manifest/census config ID sets differ")
    warm_first = p0_gate["gates"]["F3_CLOCK_EXECUTION"][
        "warmup_master_calendar_1based_first_decision_bar"]
    out = []
    for c in cfgs:
        fam = c["family"]
        f = fams[fam]
        cen = census_cfgs[c["config_id"]]
        # fired_total must equal the fold sum (sanity on copied counts)
        if cen["fired_total"] != sum(cen["fired_by_fold"].values()):
            raise SystemExit(f"FATAL: fired_total mismatch {c['config_id']}")
        params = c["parameters"]
        first_bar = warm_first[fam]
        if fam == "VOL-DRIFT":
            ctl = (f"condition-flip book: the {params['mode']}-L{params['L']} "
                   f"position map applied on the "
                   f"{'HIGH' if params['mode'] == 'MOM' else 'LOW'}-tercile "
                   f"days (see family r4/ctl definitions)")
        elif fam == "OPEN-GAP":
            twin = "FADE" if params["mode"] == "CONFIRM" else "CONFIRM"
            ctl = (f"CTL-COMPLEMENT of this configuration = "
                   f"FSS-OPEN-GAP-{twin}-Q{params['pct']} (enumerated)")
        else:
            ctl = f["ctl_complement"]
        entry = {
            "config_id": c["config_id"],
            "family": fam,
            "parameters": params,
            "mechanism_statement": c["mechanism_statement"],
            "state_formula": c["state_formula"],
            "sign_frozen": c["sign_frozen"],
            "direction_rule": (
                "sign frozen from the mechanism statement (§5 direction "
                "rule); R1 adjudicates the frozen sign and never selects "
                "it; where the mechanism admits both directions they are "
                "enumerated as distinct configurations inside the cap"),
            "holds": ("single-session: entry at bar t+1 open, exit at bar "
                      "t+1 close (§1 construction LAW)"),
            "warmup_bars": f["warmup_bars"],
            "first_decision_bar_1based_master": first_bar,
            "ctl_complement": ctl,
            "r4_trend_only_book": f["r4_trend_only_book"],
            "p0_fired_census": {
                "source_artifact": "research/control/forex_search_v1_run/p0/fired_census.json",
                "source_sha256": census_sha,
                "fired_by_fold": cen["fired_by_fold"],
                "fired_total": cen["fired_total"],
                "fired_by_leg": cen["fired_by_leg"],
                "counts_only": True,
            },
        }
        if fam == "CLOCK-COND":
            entry["expected_to_die_at_r5"] = True
        if fam == "VOL-DRIFT":
            entry["first_possible_firing_note"] = (
                f"complete-window law: own-index >= {params['L']}+251 "
                f"(declared; may be later than master decision bar 253)")
        out.append(entry)
    return out


def selection_block(census: dict, folds: dict) -> dict:
    per = census["per_config"]
    fam_totals = {}
    for cid, row in per.items():
        fam_totals.setdefault(row["family"], 0)
        fam_totals[row["family"]] += row["fired_by_fold"][RECENT_FOLD]
    if fam_totals != PACKET_FAMILY_FIRED_RECENT_FOLD:
        raise SystemExit(
            "FATAL: §3b family fired totals mismatch: "
            f"census={fam_totals} packet={PACKET_FAMILY_FIRED_RECENT_FOLD}")
    fam_rank = [f for f, _ in
                sorted(fam_totals.items(), key=lambda kv: (-kv[1], kv[0]))]
    cfg_order = {}
    for f in fam_rank:
        members = [(cid, row["fired_by_fold"][RECENT_FOLD])
                   for cid, row in per.items() if row["family"] == f]
        cfg_order[f] = [cid for cid, _ in
                        sorted(members, key=lambda kv: (-kv[1], kv[0]))]
    return {
        "amendment": (
            "owner amendment 2026-09-17 #2 (§3b): D2 SKIPPED — selection "
            "tier (i) is replaced by the P0 fired-population census and "
            "tier (ii) loses its W_c term (both non-performance, "
            "outcome-blind properties retained); T_F/W_c NOT computed"),
        "recent_fold": RECENT_FOLD,
        "recent_fold_span": folds["folds"][int(RECENT_FOLD) - 1],
        "family_fired_total_recent_fold": fam_totals,
        "family_ranking_tier_i_descending": fam_rank,
        "tie_rules": (
            "tier (i): DESCENDING by P0 fired-population census (family-"
            "level sum of fired decisions over the most recent fold), ties "
            "break by lexicographic family name; tier (ii): within a "
            "family, configurations DESCENDING by P0 fired-population "
            "census (config-level), tie-break lexicographic config ID"),
        "config_order_within_family_tier_ii": cfg_order,
        "selection_procedure_tier_iii": (
            "FAMILY-STRATIFIED round-robin over the tier-ordered families "
            "— one configuration per family per round, at most 2 scored "
            "cells per family, until 3 cells are filled; P-20 books-"
            "distinct at S: a candidate whose pooled |rho| vs any higher-"
            "ranked already-selected candidate exceeds 0.98 is SELF-"
            "SUBSUMED, skipped, next-in-order taken; unmeasurable pairwise "
            "rho = NOT_ADJUDICABLE, fail-closed"),
        "outcome_blind": (
            "every statistic consumed by this tier is a P0 census COUNT; "
            "no return, expectancy, PF, Sharpe or any performance "
            "statistic is computed for ANY configuration before the S "
            "freeze (§5 ban)"),
    }


def p0_pins() -> list:
    return [
        {
            "pin": 1,
            "verbatim": ("OPEN-GAP side-specific percentile reading — "
                         "percentile selects the side, p=50 median split"),
            "full_statement": (
                "the percentile ITSELF selects the side: p < 50 is a "
                "DOWN-tail level (fires when g[i+1] <= q); p > 50 is an "
                "UP-tail level (fires when g[i+1] >= q); p = 50 splits "
                "BOTH sides at the median (fires when g[i+1] crosses the "
                "median in either direction; equality does not fire). "
                "SIGNED gap throughout; the absolute-value reading is "
                "forbidden (§5 family 3)"),
            "source": "plans/PLAN_forex_search_v1.md §5 family 3 + P0 census threshold pin",
        },
        {
            "pin": 2,
            "verbatim": "warmup/fold interaction per §8 amended",
            "full_statement": (
                "warmup consumed inside fold 1 per §8; force-flat at fold "
                "boundary by construction (a firing counts only if the "
                "leg's own execution bar t+1 lies in the SAME fold as its "
                "decision bar t); a state that cannot be formed from "
                "COMPLETE windows is NOT FIRED — fail-closed; no "
                "expanding-window or partial-window convention anywhere; "
                "VOL-DRIFT estimator windows additionally delay first "
                "firing to own-index >= L+251 (declared)"),
            "source": "plans/PLAN_forex_search_v1.md §8 + folds_freeze.json law",
        },
        {
            "pin": 3,
            "verbatim": "MONTHPOS day<=15 boundary",
            "full_statement": (
                "month-position FIRST-half = day of month 1..15; "
                "SECOND-half = day of month 16..end-of-month (decision "
                "date's calendar day)"),
            "source": "plans/PLAN_forex_search_v1.md §5 family 5 + P0 census",
        },
    ]


def cost_financing_block(cf: dict) -> dict:
    return {
        "constants": cf["constants"],
        "financing_derivation_verbatim_from_plan_s4_F4":
            cf["financing_derivation_verbatim_from_plan_s4_F4"],
        "charged_uniformly": cf["charged_uniformly"],
        "dual_books_wiring": cf["dual_books_wiring"],
        "source_artifact": "research/control/forex_search_v1_run/p0/cost_financing_manifest.json",
        "source_sha256": sha256_file(P0 / "cost_financing_manifest.json"),
        "disclosure_language": (
            "financing = stated-conservative nightly-average "
            "extrapolation (1.7 bps; worst single night may exceed it; no "
            "per-leg differential census exists — OHLC-only source)"),
    }


# ------------------------------------------------------------------- manifest

def build_manifest() -> dict:
    art = load_p0()
    census = art["fired_census.json"]
    folds = art["folds_freeze.json"]
    gate = art["p0_gate.json"]
    cf = art["cost_financing_manifest.json"]
    census_sha = sha256_file(P0 / "fired_census.json")
    fams = family_blocks()
    cfgs = attach(build_configurations(fams), fams, census, gate, folds,
                  census_sha)
    fam_counts = {}
    for c in cfgs:
        fam_counts[c["family"]] = fam_counts.get(c["family"], 0) + 1
    expected = {"CLV-DIVERGENCE": 6, "EXTREME-FADE": 3, "OPEN-GAP": 6,
                "VOL-DRIFT": 4, "CLOCK-COND": 14}
    if fam_counts != expected:
        raise SystemExit(f"FATAL: family counts {fam_counts} != {expected}")
    manifest = {
        "schema": "search_space_manifest@1",
        "artifact": "D1 frozen search-space manifest (the cycle's "
                    "A2-equivalent dossier, plan §9 D1)",
        "cycle_id": "FOREX-SEARCH-V1",
        "orchestration_cycle": "ZCODE-ORCHESTRATION-V3",
        "plan": "plans/PLAN_forex_search_v1.md",
        "plan_sections_frozen": ["§3b", "§4 F3", "§4 F4", "§5", "§6", "§8"],
        "task_id": "fsearch-d1",
        "lane": "fsearch-d1",
        "role": "quant-implementer",
        "branch": BRANCH,
        "worktree": str(WT),
        "base_sha": BASE_SHA,
        "measured_frozen_utc": datetime.now(timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase_law": "committed BEFORE any D2 diagnostic and any scored "
                     "cell (§5); D2 itself SKIPPED per §3b",
        "universe": {
            "legs": ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"],
            "excluded": {"XAUUSD": "cost authority BLOCKED (FOREX-NG6 P0-F4)"},
            "per_leg_long_short_by_state": True,
            "no_cross_pair_input": True,
            "source": "TD 1day OHLC spot majors, single P-13 vintage "
                      "(p0/manifest_pin.json)",
        },
        "clock_contract": {
            "clock": "one frozen 16:00-NY daily decision clock; state on "
                     "completed bar t; entry at bar t+1 open, exit at bar "
                     "t+1 close — SINGLE-BAR HOLD LAW (§1)",
            "stamp_convention": art["structural_census.json"]["stamp_convention"],
            "open_gap_exception_s4_F3": gate["gates"]["F3_CLOCK_EXECUTION"][
                "open_gap_exception"],
            "same_bar_signal_fill": gate["gates"]["F3_CLOCK_EXECUTION"][
                "same_bar_signal_fill"],
        },
        "holds_law": "ALL configurations single-session (§1 law); force-flat "
                     "at fold boundary by construction",
        "warmup_rule": warmup_block(),
        "per_state_per_fold_population_floor": {
            "value": FLOOR_PER_STATE_PER_FOLD,
            "source": "§6 R2 (floor VALUE frozen HERE, in the D1 hashed "
                      "manifest, BEFORE any D2 measurement; S2 class)",
            "adjudication": "R2 evaluates later; P0 recorded the value "
                            "per config as r2_per_state_floor_recorded_only",
        },
        "grid": {
            "grid_cap_max_configurations": 80,
            "config_count": len(cfgs),
            "clock_cond_count": fam_counts["CLOCK-COND"],
            "family_counts": fam_counts,
            "dsr_frozen_grid_size_N": len(cfgs),
            "dsr_note": "exact count declared so the frozen DSR N is "
                        "unambiguous at freeze time (§5); DSR alpha 0.10 "
                        "owner-relaxed at N = grid; program-cumulative "
                        "~260 (P-9) at alpha 0.05 reported, not gating "
                        "(§3, §6)",
            "pbo_disposition_note": (
                "CSCV PBO requires >= 8 performance-evaluated "
                "configurations — unreachable BY CONSTRUCTION under this "
                "freeze + the 3-cell budget; PBO is NOT_RUN, declared "
                "fail-closed, printed on every result (§6, commit "
                "d0992d17df8e2dfde57c9a0806a5798f14021a4f class)"),
        },
        "p0_pins_verbatim": p0_pins(),
        "source_artifacts": {
            "p0_dir": "research/control/forex_search_v1_run/p0/",
            "digests_verified_against_p0_gate": gate["artifact_sha256"],
            "fold_freeze_reference": {
                "artifact": "research/control/forex_search_v1_run/p0/folds_freeze.json",
                "sha256": sha256_file(P0 / "folds_freeze.json"),
                "master_dates_sha256": folds["master_dates_sha256"],
                "boundaries_index": folds["boundaries_index"],
                "folds": folds["folds"],
                "law": folds["law"],
            },
            "fired_census_reference": {
                "artifact": "research/control/forex_search_v1_run/p0/fired_census.json",
                "sha256": census_sha,
                "law": census["law"],
            },
        },
        "families": [fams[k] for k in sorted(fams)],
        "configurations": cfgs,
        "selection_tier_s3b": selection_block(census, folds),
        "d2_r0_note": (
            "D2 SKIPPED per owner amendment §3b (verbatim intent: 'chay tu "
            "dau toi GO cua toi, nhung khong chay buoc D2' — run from the "
            "start to the owner GO, but do not run the D2 step): the R0 "
            "ancestry battery is NOT MEASURED in this cycle (R0_NOT_RUN — "
            "never an inferred PASS); this manifest carries NO R0/ancestry "
            "fields beyond this note; terminal survivor outcome names and "
            "result language carry R0_NOT_RUN alongside the standing "
            "0.20/0.30 disclosure"),
        "outcome_blindness_declaration": (
            "OUTCOME-BLIND artifact: this manifest contains NO returns, "
            "PnL, PF, Sharpe, drawdown, expectancy or any other "
            "performance statistic — construction definitions + P0 fired "
            "census COUNTS only (§5 ban: no performance-based narrowing "
            "before the S freeze; violation = BLOCKED_METHOD_CONTRACT)"),
        "reproduction": {
            "build_script": "research/control/forex_search_v1_run/d1/build_d1_manifest.py",
            "selfcheck_command": "python3 research/control/forex_search_v1_run/d1/build_d1_manifest.py --selfcheck",
            "determinism": "pure function of the pinned P0 artifacts; the "
                           "only non-deterministic field is "
                           "measured_frozen_utc (measured_* convention)",
        },
        "self_sha256_convention": (
            "self_sha256 = sha256 of the exact manifest bytes with the "
            "self_sha256 field set to the empty string, serialized as "
            "json.dumps(obj, indent=1, sort_keys=True) + '\\n'"),
        "self_sha256": "",
    }
    return manifest


def write_manifest(manifest: dict) -> tuple:
    D1.mkdir(parents=True, exist_ok=True)
    pre = canon(manifest)
    self_sha = hashlib.sha256(pre).hexdigest()
    manifest["self_sha256"] = self_sha
    MANIFEST_PATH.write_bytes(canon(manifest))
    return self_sha, sha256_file(MANIFEST_PATH)


# ------------------------------------------------------------------ selfcheck

def walk_keys(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{prefix}.{k}" if prefix else str(k)
            yield from walk_keys(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, prefix)


def selfcheck() -> int:
    art = load_p0()
    census = art["fired_census.json"]
    m = json.loads(MANIFEST_PATH.read_text())
    errs = []

    # 1. parses + schema
    if m.get("schema") != "search_space_manifest@1":
        errs.append("schema field missing/wrong")

    # 2. exactly 33 configs, family split 6/3/6/4/14
    cfgs = m["configurations"]
    if len(cfgs) != 33:
        errs.append(f"config count {len(cfgs)} != 33")
    fc = {}
    for c in cfgs:
        fc[c["family"]] = fc.get(c["family"], 0) + 1
    if fc != {"CLV-DIVERGENCE": 6, "EXTREME-FADE": 3, "OPEN-GAP": 6,
              "VOL-DRIFT": 4, "CLOCK-COND": 14}:
        errs.append(f"family counts wrong: {fc}")

    # 3. IDs unique + lexicographic + FSS-<FAMILY>-<PARAMKEY> form
    ids = [c["config_id"] for c in cfgs]
    if len(set(ids)) != len(ids):
        errs.append("config IDs not unique")
    if ids != sorted(ids):
        errs.append("config IDs not in lexicographic order")
    for i in ids:
        if not i.startswith("FSS-") or i.count("-") < 3:
            errs.append(f"bad ID form: {i}")

    # 4. per-config required fields present
    for c in cfgs:
        for k in ("family", "parameters", "mechanism_statement",
                  "state_formula", "sign_frozen", "holds", "warmup_bars",
                  "first_decision_bar_1based_master", "ctl_complement",
                  "r4_trend_only_book", "p0_fired_census"):
            if k not in c:
                errs.append(f"{c['config_id']}: missing {k}")

    # 5. counts byte-equal to fired_census.json
    cc = census["per_config"]
    if set(ids) != set(cc):
        errs.append("manifest/census ID set mismatch")
    for c in cfgs:
        ref = cc[c["config_id"]]
        got = c["p0_fired_census"]
        if got["fired_by_fold"] != ref["fired_by_fold"]:
            errs.append(f"{c['config_id']}: fired_by_fold mismatch")
        if got["fired_total"] != ref["fired_total"]:
            errs.append(f"{c['config_id']}: fired_total mismatch")
        if got["fired_by_leg"] != ref["fired_by_leg"]:
            errs.append(f"{c['config_id']}: fired_by_leg mismatch")

    # 6. §3b family totals + ranking
    sel = m["selection_tier_s3b"]
    if sel["family_fired_total_recent_fold"] != PACKET_FAMILY_FIRED_RECENT_FOLD:
        errs.append("§3b family fired totals mismatch")
    exp_rank = [f for f, _ in sorted(PACKET_FAMILY_FIRED_RECENT_FOLD.items(),
                                     key=lambda kv: (-kv[1], kv[0]))]
    if sel["family_ranking_tier_i_descending"] != exp_rank:
        errs.append("family ranking wrong")

    # 7. floor pinned = 10
    if m["per_state_per_fold_population_floor"]["value"] != 10:
        errs.append("per-state per-fold floor != 10")

    # 8. no performance-field keys (outcome-blind law)
    for key in walk_keys(m):
        low = key.lower()
        for tok in FORBIDDEN_KEY_TOKENS:
            if tok in low:
                errs.append(f"forbidden performance key: {key}")

    # 9. required plan fields present
    for k in ("warmup_rule", "clock_contract", "p0_pins_verbatim",
              "selection_tier_s3b", "d2_r0_note", "grid", "families",
              "source_artifacts"):
        if k not in m:
            errs.append(f"missing top-level field: {k}")
    if len(m["p0_pins_verbatim"]) != 3:
        errs.append("P0 pins != 3")
    if m["grid"]["dsr_frozen_grid_size_N"] != 33:
        errs.append("frozen DSR N != 33")
    fin = m["source_artifacts"]
    if fin["fold_freeze_reference"]["sha256"] != sha256_file(
            P0 / "folds_freeze.json"):
        errs.append("fold freeze digest reference mismatch")

    # 10. self sha256 convention verifies
    stored = m["self_sha256"]
    m["self_sha256"] = ""
    recomputed = hashlib.sha256(canon(m)).hexdigest()
    if stored != recomputed:
        errs.append(f"self_sha256 mismatch: {stored} != {recomputed}")

    if errs:
        print("SELFCHECK FAIL:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("SELFCHECK PASS: manifest parses; 33 configs (CLV 6 / FADE 3 / "
          "GAP 6 / VOL 4 / CLOCK 14); IDs unique + lexicographic; fired "
          "counts byte-equal to p0/fired_census.json; §3b family totals "
          "match; family ranking correct; floor=10 pinned; 3 P0 pins "
          "verbatim; no performance-field keys; self sha256 verifies.")
    return 0


def main() -> int:
    if "--selfcheck" in sys.argv:
        return selfcheck()
    manifest = build_manifest()
    self_sha, file_sha = write_manifest(manifest)
    print(f"manifest written: {MANIFEST_PATH}")
    print(f"self_sha256 (convention): {self_sha}")
    print(f"file_sha256 (committed bytes): {file_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
