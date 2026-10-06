#!/usr/bin/env python
# DRYRUN-V2-1 builder — cycle FUTURES-ES-PB1-V1, gate 4 RE-RUN after the D-V2-1
# defect correction (diagnosis: dryrun_v2/DRYRUN_V2_REPORT.md §5).
#
# EXACT COPY of dryrun_v2/dryrun_builder_v2.py (the shim-only v2 rehearsal
# machinery, itself an exact copy of the v1 builder with the two v2 shims) with
# EXACTLY ONE additional logic change (lane DRYRUN-V2-1 mission M1; ANY other
# divergence = CRITICAL):
#   C1 (the correction law, conservative-intent carryover within the owner's
#      repair authorization "holiday repair"): the SL-donor EXCLUSION session
#      set is the SESSION-SET IDENTICAL to v1's 139 sessions — evaluated on the
#      V1 class labels (freezegen/exclude_list.json, HISTORY, read-only;
#      donor classes {HOLIDAY_FACT_EARLYCLOSE, HOLIDAY_UNCERTAIN,
#      COVERAGE_LT60}). The repair's 35 COVERAGE_LT60 ->
#      HOLIDAY_PDF_EQUITY_2011_2015 relabels are evidentiary metadata only and
#      must NOT alter donor statistics. The v2-only class adds nothing: 35 of
#      the 36 HOLIDAY_PDF_EQUITY sessions were COVERAGE_LT60 in v1 (already
#      covered by using v1 labels) and 2015-07-02 had NO v1 label — donor-
#      ADMITTED in v1 and kept donor-admitted (the repair changes EVAL
#      membership only, not donor law). Eval surface / eval sets / FOMCIN /
#      WARMUP remain on the v2 labels. Asserted in load_inputs:
#      donor-excluded count == 139 == v1; 2015-07-02 donor-admitted.
#   Lane shims (same class as v2 S2/S3, required to run this lane):
#      S2' outputs under dryrun_v2_1/ (quarantine + quarantine_rerun);
#      S3' digest head_sha = measured worktree HEAD 148a7bf5…; lane DRYRUN-V2-1;
#          schema dryrun_v2_1_digest@1; digest file dryrun_v2_1_digest.json;
#          digest additionally embeds inp["donor_correction"] evidence and the
#          D-V2-1-FIX finding (documentation only, no simulation logic touched).
#   Inherited v2 shims (unchanged): S1 v2 freeze/exclude inputs; S4
#      GENERATED_UTC fixed "2026-10-05"; S5 post-hoc criteria (d)/(e); S6
#      main(lock_record).
# dryrun/ (v1) and dryrun_v2/ (v2) are HISTORY: not modified, not executed.
#
# QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED — ZERO DENOMINATOR CONSUMPTION —
# pre-GO rehearsal per registered plan §4 gate 4.
#
# LAWS CONSUMED (every mechanic cites its law):
#   SPEC_PB1_ES.md (sha 445f7499..., pinned):
#     §1  L16-46   universe/chain/era-correct session clock; Roll T-5; C_prev.
#     §2  L48-69   EXCLUDE rules E1-E5 (applied via the FROZEN exclude_list.json).
#     §3  L71-81   m = log(open_0830 / C_prev); |m| >= q80(|m|, trailing-252d,
#                  strict-past); arms CONT/REV; tails UP/DN; warmup 252 sessions;
#                  FOMC statement-day base-exclude; FOMCIN = inverse include set;
#                  RTH-core coverage <60% => EXCLUDE (baked into frozen list).
#     §4  L83-93   entry first 1m bar 08:30 (D0) or 09:00 (D30) in arm direction,
#                  fill = open of NEXT 1m bar; TP = 2.0 x SL-distance;
#                  SL = 1.0 x median of trailing 20 RTH session ranges (strict
#                  past, era-correct close marks, exclude short/flagged sessions)
#                  [ERRATUM A7-SPEC-M5]; same-bar TP/SL => SL priority (worse
#                  price); time exit = era-correct RTH close, flat forced.
#     §5  L95-113  cost table STALE per COST_FREEZE_ERRATUM law — NOT consumed;
#                  Variant A (registered plan §2) consumed instead.
#     §6  L115-136 the 24 identities (consumed byte-exact from
#                  selection_freeze.json identity_table).
#     §7  L139-143 4 folds post-EXCLUDE; warmup 252 sessions per fold head.
#   plans/PLAN_futures_es_pb1_v1.md §2 (Variant A cost contract, owner D3):
#     commission 0.85 + exchange 1.38 + NFA 0.02 (0.01 only 2014-10-01..2017-12-31)
#     = 2.25/side fees; spread half-turn 6.25; slippage S1/S2/S3 = 12.50/25.00/37.50
#     => all-in/side 21.00/33.50/46.00 (window rows 20.99/33.49/45.99); RT x2.
#     Retired values 1.386 / 21.006 / 33.506 / 46.006 are NEVER consumable.
#   PLAYBOOKS_DRAFT.md §1 L76/L86-89 (control mechanics):
#     C1 clock/random-sign placebo: entry 08:30, direction = seeded random sign
#       (seed 20261002, deterministic per session), delay 0, tier S2, same
#       fold/session set as primary; no arm/tail conditioning.
#     C2 always-in-RTH baseline: tier S2, same folds (direction law not stated —
#       ambiguity finding D-A2: implemented unconditional LONG, hold to close).
#     C3 flat anchor: zero trades, identity logged.
#     C4 OVN-direction-unconditional (dose-response): sign(m) EVERY day, no
#       threshold, delay 0, tier S2, full TP/SL mechanics.
#
# IMPLEMENTATION PINS (not laws; pinned for determinism, recorded as findings):
#   D-A1 q80 percentile method unspecified in law ("q80 from anatomy, not tuned")
#        => numpy.percentile(values, 80) linear interpolation.
#   D-A2 C2 direction unspecified ("C2 always-in-RTH baseline | CÓ") =>
#        unconditional LONG entry 08:31 open, hold to RTH close, no TP/SL
#        (the only reading consistent with "always-in").
#   D-A3 C1 RNG algorithm unspecified ("seed 20261002, sign-draw deterministic
#        theo session") => sign = +1 iff sha256("FBES1-PLA-D0-S2|seed=20261002|"
#        + session_date).digest()[0] < 0x80 else -1.
#   D-A4 window fencing unspecified: q80 window = trailing 252 sessions with
#        computable m, chain-wide strict past (not fold-fenced); SL donor window
#        = trailing 20 chain sessions strict past, excluding short/flagged
#        donors (reason classes HOLIDAY_FACT_EARLYCLOSE / HOLIDAY_UNCERTAIN /
#        COVERAGE_LT60 — the "short/flagged" set of SPEC §4). Trading itself is
#        fold-fenced via the frozen eval windows + warmup carve-outs.
#   D-A5 costs applied as USD lines per side at pinned table values (fill
#        prices unadjusted); TP/SL levels derive from the fill price per SPEC §4.
#
# Determinism: outputs carry fixed generated_utc "2026-10-05"; two independent
# passes (each re-reading every input from disk) must produce byte-identical
# per-identity JSONs and an identical trades-index sha256 (M3 criterion c).

import hashlib
import json
import sys
from collections import OrderedDict

import numpy as np
import pandas as pd

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
ES_CACHE = WT + "/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache"
DRYRUN = WT + "/research/control/FUTURES-ES-PB1-V1/dryrun_v2_1"
GENERATED_UTC = "2026-10-05"
QUARANTINE_HEADER = (
    "QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED — ZERO DENOMINATOR CONSUMPTION — "
    "pre-GO rehearsal per registered plan §4 gate 4"
)

PIN_SPEC = "445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073"
PIN_PANEL = "7ae6de2d5896d9e150f70209f2709ca70b625f0b06bbdbfed348b1b0e0227b95"
PIN_CHAIN = "7b6179d27a2c9da7dd5972f03d40209ded0119aabfc14a5abc08167894e8f06f"

# Era-correct RTH close marks (CT minutes-of-day), SPEC §1 L22-23 +
# es_session_holiday.json weekly_template_by_era (2013-01..2015-11-19 / 2015-11-20..):
def era_close_min(date: str) -> int:
    if date <= "2012-12-31":
        return 16 * 60 + 30      # 16:30 CT (→2012)
    if date <= "2015-11-19":
        return 16 * 60 + 15      # 16:15 CT (2013→2015-11-19)
    return 16 * 60 + 0           # 16:00 CT (from 2015-11-20)

RTH_OPEN_MIN = 8 * 60 + 30       # 08:30 CT (SPEC §3 L73 open_0830)
D30_SIGNAL_MIN = 9 * 60 + 0      # 09:00 CT (SPEC §4 L85 D30)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def c1_sign(session_date: str) -> int:
    # IMPLEMENTATION PIN D-A3 (see module docstring).
    d = hashlib.sha256(
        f"FBES1-PLA-D0-S2|seed=20261002|{session_date}".encode()
    ).digest()
    return 1 if d[0] < 0x80 else -1


def load_inputs():
    """Input gate: pinned shas, freeze artifacts, chain. Aborts pre-write."""
    p_spec = WT + "/research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md"
    p_freeze = WT + "/research/control/FUTURES-ES-PB1-V1/repair/selection_freeze_v2.json"
    p_excl = WT + "/research/control/FUTURES-ES-PB1-V1/repair/exclude_list_v2.json"
    p_panel = ES_CACHE + "/es_1m_outright.parquet"
    p_chain = ES_CACHE + "/es_chain_T5.parquet"
    measured = {
        "SPEC_PB1_ES.md": sha256_file(p_spec),
        "es_1m_outright.parquet": sha256_file(p_panel),
        "es_chain_T5.parquet": sha256_file(p_chain),
        "exclude_list_v2.json": sha256_file(p_excl),
        "selection_freeze_v2.json": sha256_file(p_freeze),
    }
    assert measured["SPEC_PB1_ES.md"] == PIN_SPEC, "SPEC sha mismatch vs pin"
    assert measured["es_1m_outright.parquet"] == PIN_PANEL, "panel sha mismatch vs pin"
    assert measured["es_chain_T5.parquet"] == PIN_CHAIN, "chain sha mismatch vs pin"

    freeze = json.load(open(p_freeze))
    excl = json.load(open(p_excl))
    assert freeze["schema"] == "selection_freeze@2"
    assert excl["schema"] == "exclude_list@2"
    # sha round-trip: freeze embeds the exclude list sha (gate-2 law)
    assert freeze["exclude_list"]["sha256"] == sha256_file(p_excl), "exclude sha mismatch"

    # ---- cost contract Variant A (from the freeze, never hardcoded) ----
    cc = freeze["cost_contract"]["embedded"]["effective_cost_table_es"]
    fees_normal = cc["commission"] + cc["exchange"] + cc["regulatory"]
    fees_window = cc["commission"] + cc["exchange"] + \
        cc["window_exception_2014_10_01_to_2017_12_31"]["regulatory"]
    assert abs(fees_normal - cc["fees_per_side"]) < 1e-12, "fees table mismatch"
    spread = cc["spread_half_turn"]
    slip = cc["slippage_tiers_per_side"]
    for t in ("S1", "S2", "S3"):
        assert abs(fees_normal + spread + slip[t] - cc["all_in_per_side"][t]) < 1e-12
        w = fees_window + spread + slip[t]
        assert abs(w - cc["window_exception_2014_10_01_to_2017_12_31"]
                   ["all_in_per_side"][t]) < 1e-12
        assert abs(2 * cc["all_in_per_side"][t] - cc["round_trip"][t]) < 1e-12
    # retired values must never appear (COST_FREEZE_ERRATUM law)
    cc_json = json.dumps(cc)
    for banned in ("1.386", "21.006", "33.506", "46.006"):
        assert banned not in cc_json, f"retired cost value present: {banned}"
    cost = {
        "fees_normal": fees_normal,          # 2.25
        "fees_window": fees_window,          # 2.24 (NFA 0.01)
        "window": ("2014-10-01", "2017-12-31"),
        "spread": spread,                    # 6.25
        "slip": slip,                        # 12.5 / 25.0 / 37.5
        "table": cc,
    }

    # ---- identity table (byte-exact ids) ----
    ids = [it["id"] for it in freeze["identity_table"]["embedded"]["identities"]]
    assert len(ids) == 24 and len(set(ids)) == 24

    # ---- exclude list ----
    classes = {}          # date -> set(reason_class)
    excluded = set()      # any-class excluded dates
    fomc_days = set()
    for it in excl["exclusions"]:
        if not it.get("in_panel", False):
            continue
        d = it["session_date"]
        classes.setdefault(d, set()).add(it["reason_class"])
        excluded.add(d)
        if it["reason_class"] == "FOMC_STATEMENT_DAY":
            fomc_days.add(d)
    # DRYRUN-V2-1 correction C1 (the ONE logic change vs dryrun_builder_v2.py):
    # the SL-donor exclusion set is the SESSION-SET identical to v1's — the v1
    # class labels (freezegen/exclude_list.json, HISTORY, read-only) filtered by
    # the v1 donor classes. The repair's 35 COVERAGE_LT60 ->
    # HOLIDAY_PDF_EQUITY_2011_2015 relabels are evidentiary metadata only and
    # must not alter donor statistics; 2015-07-02 had no v1 label and stays
    # donor-admitted (repair is EVAL-only). Eval sets / FOMCIN / WARMUP below
    # remain on the v2 labels.
    excl_v1 = json.load(open(WT + "/research/control/FUTURES-ES-PB1-V1/"
                             "freezegen/exclude_list.json"))
    assert excl_v1["schema"] == "exclude_list@1", "v1 label column schema mismatch"
    classes_v1 = {}
    for it in excl_v1["exclusions"]:
        if not it.get("in_panel", False):
            continue
        classes_v1.setdefault(it["session_date"], set()).add(it["reason_class"])
    short_flagged = classes_v1 and {
        d for d, cs in classes_v1.items()
        if cs & {"HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_UNCERTAIN", "COVERAGE_LT60"}
    }
    # D-V2-1 correction asserts (mandated by lane DRYRUN-V2-1 mission M1)
    assert short_flagged and len(short_flagged) == 139, (
        f"donor-excluded count {len(short_flagged or set())} != v1's 139")
    assert "2015-07-02" not in short_flagged, (
        "2015-07-02 must remain donor-admitted (no v1 label; EVAL-only repair)")
    sf_v2_labels = {d for d, cs in classes.items()
                    if cs & {"HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_UNCERTAIN",
                             "COVERAGE_LT60"}}
    recovered = sorted(set(short_flagged) ^ sf_v2_labels)
    assert len(recovered) == 35, (
        f"expected exactly the 35 relabeled sessions, got {len(recovered)}")
    assert all(classes_v1.get(d) == {"COVERAGE_LT60"}
               and classes.get(d) == {"HOLIDAY_PDF_EQUITY_2011_2015"}
               for d in recovered), (
        "relabeled session labels are not COVERAGE_LT60 -> HOLIDAY_PDF_EQUITY_2011_2015")

    # ---- folds ----
    folds = freeze["fold_structure"]["folds"]

    # ---- chain (held T-5 contract per session) ----
    chain = pd.read_parquet(p_chain)
    chain = chain.sort_index()
    chain_dates = [d.strftime("%Y-%m-%d") for d in chain.index]
    held = dict(zip(chain_dates, chain["symbol"].tolist()))
    chain_close = dict(zip(chain_dates, chain["close"].tolist()))
    chain_rth_open = dict(zip(chain_dates, chain["rth_open"].tolist()))

    return {
        "freeze": freeze, "excl": excl, "cost": cost, "ids": ids,
        "classes": classes, "excluded": excluded, "fomc_days": fomc_days,
        "short_flagged": short_flagged, "folds": folds,
        "chain_dates": chain_dates, "held": held,
        "chain_close": chain_close, "chain_rth_open": chain_rth_open,
        "panel_path": p_panel, "measured_shas": measured,
        "donor_correction": {
            "law": "D-V2-1 correction C1: SL-donor exclusion set == v1's exact "
                   "139-session set, evaluated on the v1 class labels "
                   "(freezegen/exclude_list.json, read-only); the repair's "
                   "35 COVERAGE_LT60 -> HOLIDAY_PDF_EQUITY_2011_2015 relabels "
                   "are evidentiary metadata only and do not alter donor "
                   "statistics; 2015-07-02 stays donor-admitted (EVAL-only repair)",
            "v1_label_source": "freezegen/exclude_list.json (schema exclude_list@1)",
            "donor_classes": ["HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_UNCERTAIN",
                              "COVERAGE_LT60"],
            "donor_excluded_count_v1_labels": len(short_flagged),
            "donor_excluded_count_v2_labels": len(sf_v2_labels),
            "relabeled_sessions_recovered": len(recovered),
            "relabeled_first": recovered[0] if recovered else None,
            "relabeled_last": recovered[-1] if recovered else None,
            "session_2015_07_02_donor_admitted": "2015-07-02" not in short_flagged,
        },
    }


def build_sessions(inp):
    """Single-shot panel read -> per-session RTH bar arrays (held chain only).

    Panel law: raw_symbol containing '-' filtered (SPEC §1 L20, E5/dash law);
    prices fixed-point 1e-9; ts_event = bar START (UTC ns).
    """
    panel = pd.read_parquet(inp["panel_path"])
    n0 = len(panel)
    dash = panel["raw_symbol"].str.contains("-", regex=False)
    n_dash = int(dash.sum())
    panel = panel[~dash]
    held = inp["held"]
    kept_symbols = set(held.values())
    panel = panel[panel["raw_symbol"].isin(kept_symbols)]

    ts = pd.to_datetime(panel["ts_event"], utc=True).dt.tz_convert("America/Chicago")
    date = ts.dt.strftime("%Y-%m-%d")
    tod = ts.dt.hour * 60 + ts.dt.minute
    df = pd.DataFrame({
        "date": date, "tod": tod,
        "sym": panel["raw_symbol"].to_numpy(),
        "o": panel["open"].to_numpy() / 1e9,
        "h": panel["high"].to_numpy() / 1e9,
        "l": panel["low"].to_numpy() / 1e9,
        "c": panel["close"].to_numpy() / 1e9,
        "tns": panel["ts_event"].to_numpy(),
    })
    df = df[df["tod"] >= RTH_OPEN_MIN]
    df = df[df["tod"] < 16 * 60 + 30]        # widest era close (16:30)
    df = df[[d in held for d in df["date"]]]
    df = df[[held[d] == s for d, s in zip(df["date"], df["sym"])]]
    df = df.sort_values(["date", "tod"], kind="mergesort")

    sessions = OrderedDict()
    for d, g in df.groupby("date", sort=True):
        gg = g[g["tod"] < era_close_min(d)]
        sessions[d] = {
            "tod": gg["tod"].to_numpy(),
            "tns": gg["tns"].to_numpy(),
            "o": gg["o"].to_numpy(), "h": gg["h"].to_numpy(),
            "l": gg["l"].to_numpy(), "c": gg["c"].to_numpy(),
        }
    return sessions, {"panel_rows": n0, "dash_rows_filtered": n_dash,
                      "rth_rows_kept": int(len(df))}


def derive_state(inp, sessions):
    """m / q80 / SL-donor chain-wide strict-past state + fold eval sets."""
    dates = inp["chain_dates"]
    excluded, classes, sf = inp["excluded"], inp["classes"], inp["short_flagged"]

    # open_0830, last-bar close, RTH range per session
    open830, last_close, rth_range = {}, {}, {}
    for d, s in sessions.items():
        idx = np.flatnonzero(s["tod"] == RTH_OPEN_MIN)
        open830[d] = float(s["o"][idx[0]]) if len(idx) else None
        last_close[d] = float(s["c"][-1]) if len(s["c"]) else None
        rth_range[d] = float(s["h"].max() - s["l"].min()) if len(s["h"]) else None

    # era validation vs chain reference doubles (evaluation view, reported)
    close_match = sum(
        1 for d in dates
        if d in sessions and sessions[d]["c"].size
        and inp["chain_close"].get(d) is not None
        and not (isinstance(inp["chain_close"].get(d), float)
                 and np.isnan(inp["chain_close"].get(d)))
        and abs(sessions[d]["c"][-1] - float(inp["chain_close"][d])) < 1e-6
    )
    open_match = sum(
        1 for d in dates
        if d in sessions and sessions[d]["c"].size
        and open830.get(d) is not None
        and inp["chain_rth_open"].get(d) is not None
        and not (isinstance(inp["chain_rth_open"].get(d), float)
                 and np.isnan(inp["chain_rth_open"].get(d)))
        and abs(open830[d] - float(inp["chain_rth_open"][d])) < 1e-6
    )

    # m per session: log(open_0830 / C_prev), C_prev = actual close of the
    # immediately-prior chain session at its era-correct mark (SPEC §3 L73,
    # §1 L43-44). Chain-wide (strict past); fold-fencing applies to TRADING.
    m = {}
    for i in range(1, len(dates)):
        d, dp = dates[i], dates[i - 1]
        o, cp = open830.get(d), last_close.get(dp)
        if o is not None and cp is not None and cp > 0 and o > 0:
            m[d] = float(np.log(o / cp))

    # q80 threshold: trailing 252 computable |m| sessions, strict past
    # (IMPLEMENTATION PIN D-A4; percentile method D-A1).
    q80, m_hist = {}, []
    for d in dates:
        if len(m_hist) >= 252:
            q80[d] = float(np.percentile(m_hist[-252:], 80))
        else:
            q80[d] = None
        if d in m:
            m_hist.append(abs(m[d]))

    # SL donor distance: median of trailing 20 usable RTH ranges, strict past;
    # donors in short/flagged classes excluded (SPEC §4 [ERRATUM A7-SPEC-M5];
    # fencing pin D-A4).
    sldist, donors = {}, []
    for d in dates:
        if len(donors) >= 20:
            sldist[d] = float(np.median(donors[-20:]))
        else:
            sldist[d] = None
        r = rth_range.get(d)
        if r is not None and (d not in sf):
            donors.append(r)

    # fold eval sets (frozen windows − any-class excluded) + FOMCIN set.
    # Warmup law is POSITIONAL ("warmup 252 sessions per fold head — excluded
    # from scoring", exclude_list evidence + selection_freeze fold law): no
    # identity trades at or before the fold's warmup_carve_out.last date. FOMC
    # days inside the warmup head are priority-labeled FOMC_STATEMENT_DAY, so
    # the FOMCIN set additionally requires d > warmup_last.
    eval_sets, fomcin_sets = {}, {}
    counts_ok = True
    for f in inp["folds"]:
        w_from, w_to = f["window"]["from"], f["window"]["to"]
        warm_last = f["warmup_carve_out"]["last"]
        ev, fi = [], []
        for d in dates:
            if not (w_from <= d <= w_to):
                continue
            cs = classes.get(d, set())
            if not cs:
                ev.append(d)
            if (d > warm_last and "FOMC_STATEMENT_DAY" in cs and not (
                cs & {"HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_UNCERTAIN",
                      "COVERAGE_LT60", "WARMUP"}
            )):
                fi.append(d)
        eval_sets[f["fold"]] = ev
        fomcin_sets[f["fold"]] = fi
        ok = (len(ev) == f["eval_sessions"]["n"]
              and (not ev or ev[0] == f["eval_sessions"]["first"])
              and (not ev or ev[-1] == f["eval_sessions"]["last"]))
        counts_ok = counts_ok and ok

    return {
        "open830": open830, "last_close": last_close, "rth_range": rth_range,
        "m": m, "q80": q80, "sldist": sldist,
        "eval_sets": eval_sets, "fomcin_sets": fomcin_sets,
        "counts_ok": counts_ok,
        "validation": {
            "era_close_match_vs_chain": close_match,
            "rth_open_match_vs_chain": open_match,
            "n_chain_sessions": len(dates),
        },
    }


def parse_identity(iid: str):
    """Map a frozen identity id to its mechanics (SPEC §6 table semantics)."""
    if iid == "FBES1-FLAT":
        return {"klass": "C3"}
    if iid == "FBES1-PLA-D0-S2":
        return {"klass": "C1", "delay": 0, "tier": "S2"}
    if iid == "FBES1-ALW-D0-S2":
        return {"klass": "C2", "delay": 0, "tier": "S2"}
    if iid == "FBES1-DOSE-D0-S2":
        return {"klass": "C4", "delay": 0, "tier": "S2"}
    if iid.startswith("FBES1-PB1-"):
        parts = iid.split("-")           # FBES1 PB1 <CONT|REV> <UP|DN> <D0|D30> S<n> [-FOMCIN]
        arm, tail, delay, tier = parts[2], parts[3], parts[4], parts[5]
        fomcin = len(parts) > 6 and parts[6] == "FOMCIN"
        return {
            "klass": "FOMC" if fomcin else ("P-A" if delay == "D30" else "P-B"
                                            if tier in ("S1", "S3") else "P-A"),
            "arm": arm, "tail": tail,
            "delay": 0 if delay == "D0" else 30,
            "tier": tier, "fomcin": fomcin,
        }
    raise AssertionError(f"unparseable identity id: {iid}")


def simulate(iid, cfg, st, inp, sessions):
    """Run one identity over its frozen session set. Returns record dict."""
    cost = inp["cost"]
    folds = {f["fold"]: f for f in inp["folds"]}
    trades, skips = [], {
        "skip_session_bars_missing": 0, "skip_no_q80_window": 0,
        "skip_tail_not_matched": 0, "skip_m_unavailable": 0,
        "skip_no_entry_bar": 0, "skip_no_fill_bar": 0,
        "skip_no_sl_window": 0,
    }

    def fold_of(d):
        for fn, f in folds.items():
            if f["window"]["from"] <= d <= f["window"]["to"]:
                return fn
        return None

    def cost_for(d, tier):
        inwin = cost["window"][0] <= d <= cost["window"][1]
        fees = cost["fees_window"] if inwin else cost["fees_normal"]
        slip = cost["slip"][tier]
        side = fees + cost["spread"] + slip
        return {
            "reg_window_2014_10_01_2017_12_31": bool(inwin),
            "fees_per_side": round(fees, 10),
            "spread_half_turn": cost["spread"],
            "slippage_per_side": slip,
            "side_cost_usd": round(side, 10),
            "rt_cost_usd": round(2 * side, 10),
        }

    if cfg["klass"] == "C3":
        return {"trades": [], "skips": skips, "n_sessions": 0,
                "fold_n": {}}, []

    if cfg["klass"] == "FOMC":
        session_set = [d for f in sorted(inp["freeze"]["fold_structure"]["folds"],
                                         key=lambda x: x["fold"])
                       for d in st["fomcin_sets"][f["fold"]]]
    else:
        session_set = [d for f in sorted(inp["freeze"]["fold_structure"]["folds"],
                                         key=lambda x: x["fold"])
                       for d in st["eval_sets"][f["fold"]]]

    signal_min = D30_SIGNAL_MIN if cfg.get("delay") == 30 else RTH_OPEN_MIN

    for d in session_set:
        s = sessions.get(d)
        if s is None or s["c"].size == 0:
            skips["skip_session_bars_missing"] += 1
            continue
        mv = st["m"].get(d)
        # --- direction (per class) ---
        if cfg["klass"] in ("P-A", "P-B", "FOMC"):
            q = st["q80"].get(d)
            if q is None:
                skips["skip_no_q80_window"] += 1
                continue
            if mv is None:
                skips["skip_m_unavailable"] += 1
                continue
            tail = "UP" if mv > 0 else ("DN" if mv < 0 else None)
            if tail is None or tail != cfg["tail"] or abs(mv) < q:
                skips["skip_tail_not_matched"] += 1
                continue
            direction = 1 if cfg["arm"] == "CONT" else -1
        elif cfg["klass"] == "C4":
            if mv is None:
                skips["skip_m_unavailable"] += 1
                continue
            if mv == 0:
                skips["skip_m_unavailable"] += 1
                continue
            direction = 1 if mv > 0 else -1
        elif cfg["klass"] == "C1":
            direction = c1_sign(d)
        elif cfg["klass"] == "C2":
            direction = 1            # PIN D-A2 (unconditional long baseline)
        else:
            raise AssertionError(cfg)

        # --- entry mechanics (SPEC §4): signal bar, fill = next 1m bar open ---
        i_sig = np.flatnonzero(s["tod"] == signal_min)
        if len(i_sig) == 0:
            skips["skip_no_entry_bar"] += 1
            continue
        i_sig = int(i_sig[0])
        i_fill = i_sig + 1
        if i_fill >= len(s["tod"]) or s["tns"][i_fill] != s["tns"][i_sig] + 60_000_000_000:
            skips["skip_no_fill_bar"] += 1
            continue
        entry = float(s["o"][i_fill])

        # --- SL/TP (SPEC §4); C2 = always-in, hold to close (PIN D-A2) ---
        use_tpsl = cfg["klass"] != "C2"
        tp = sl = sld = None
        if use_tpsl:
            sld = st["sldist"].get(d)
            if sld is None:
                skips["skip_no_sl_window"] += 1
                continue
            tp = entry + 2.0 * sld if direction == 1 else entry - 2.0 * sld
            sl = entry - sld if direction == 1 else entry + sld

        # --- exit scan (SL priority same-bar; time exit at era-close mark) ---
        reason, exit_px, exit_bar = None, None, None
        if use_tpsl:
            for k in range(i_fill, len(s["tod"])):
                hit_sl = (s["l"][k] <= sl) if direction == 1 else (s["h"][k] >= sl)
                hit_tp = (s["h"][k] >= tp) if direction == 1 else (s["l"][k] <= tp)
                if hit_sl:                      # SL priority (worse price)
                    reason, exit_px, exit_bar = "SL", sl, k
                    break
                if hit_tp:
                    reason, exit_px, exit_bar = "TP", tp, k
                    break
        if reason is None:
            reason, exit_px, exit_bar = "TIME", float(s["c"][-1]), len(s["tod"]) - 1

        c = cost_for(d, cfg["tier"])
        gross = direction * (exit_px - entry) * 50.0     # ES mult 50 (SPEC §1 L16)
        tns = s["tns"]
        trades.append({
            "fold": fold_of(d), "session_date": d, "direction": direction,
            "m": None if mv is None else round(mv, 12),
            "q80_threshold": None if cfg["klass"] not in ("P-A", "P-B", "FOMC")
            else round(st["q80"][d], 12),
            "sl_distance_pts": None if sld is None else round(sld, 12),
            "signal_bar_utc": pd.Timestamp(int(tns[i_sig]), unit="ns", tz="UTC").isoformat(),
            "fill_bar_utc": pd.Timestamp(int(tns[i_fill]), unit="ns", tz="UTC").isoformat(),
            "entry_price": round(entry, 10),
            "tp_price": None if tp is None else round(tp, 10),
            "sl_price": None if sl is None else round(sl, 10),
            "exit_reason": reason,
            "exit_bar_utc": pd.Timestamp(int(tns[exit_bar]), unit="ns", tz="UTC").isoformat(),
            "exit_price": round(exit_px, 10),
            "gross_pnl_usd": round(gross, 10),
            "cost": c,
            "net_pnl_usd": round(gross - c["rt_cost_usd"], 10),
        })

    fold_n = {}
    for t in trades:
        fold_n[t["fold"]] = fold_n.get(t["fold"], 0) + 1
    return {"trades": trades, "skips": skips,
            "n_sessions": len(session_set), "fold_n": fold_n}, session_set


CITATIONS = {
    "signal": "SPEC_PB1_ES §3 L73-76: m = log(open_0830 / C_prev); |m| >= q80(|m|, trailing-252d, strict-past); warmup 252 session",
    "entry": "SPEC_PB1_ES §4 L85-86: bar 1m đầu 08:30 CT (D0) hoặc 09:00 CT (D30) theo hướng arm; fill = open bar 1m kế tiếp",
    "tpsl": "SPEC_PB1_ES §4 L87-90: TP = 2.0 × SL-distance; SL = 1.0 × median của 20 range RTH session liền trước (strict past; close marks era-correct; loại session short/flagged) [ERRATUM A7-SPEC-M5]; same-bar TP/SL ⇒ SL ưu tiên",
    "time_exit": "SPEC_PB1_ES §4 L91: Time exit: close RTH era-correct — flat bắt buộc",
    "fomc": "SPEC_PB1_ES §3 L77-79 [ERRATUM A7-SPEC-M3]: MỌI ngày có statement FOMC base-EXCLUDE cấp NGÀY; FOMCIN arm = tập INCLUDE ngược",
    "folds": "SPEC_PB1_ES §7 L140-141 + selection_freeze fold_structure: 4 folds tuần tự post-EXCLUDE, warmup 252 session/fold head",
    "cost": "PLAN_futures_es_pb1_v1 §2 Variant A (owner D3): fees 2.25/side (NFA 0.01 chỉ 2014-10-01..2017-12-31 ⇒ 2.24) + spread 6.25 + slippage S1/S2/S3 12.50/25.00/37.50 ⇒ all-in 21.00/33.50/46.00; 1.386/21.006/33.506/46.006 retired",
    "controls": "PLAYBOOKS_DRAFT §1 L76 + L86-89: C1 clock/random-sign (seed 20261002), C2 always-in-RTH, C3 flat, C4 sign(m) mọi ngày không threshold",
    "roll": "SPEC_PB1_ES §1 L24-32: Roll T-5 (held chain es_chain_T5.parquet, pin 7b6179d2…)",
}

FINDINGS = [
    {"id": "D-A1", "type": "AMBIGUITY", "severity": "MUST-PIN-BEFORE-SCORED-G6",
     "finding": "q80 percentile method is not pinned by any committed law. SPEC §3 L73-74: 'điều kiện |m| ≥ q80(|m|, trailing-252d, strict-past) — q80 từ anatomy (NQ dossier H4 refined spec; ES §8-H5), không tune'; checked ESNQ_HYPOTHESES.md, ES/NQ_DEEPFOUR_V3_ADDENDUM.md — no interpolation method declared. Pinned here: numpy.percentile(…, 80) linear interpolation. Does not affect gate-4 criteria (enumeration/cost/determinism); MUST be ratified (owner/freeze amendment) before scored execution."},
    {"id": "D-A2", "type": "AMBIGUITY", "severity": "MUST-PIN-BEFORE-SCORED-G6",
     "finding": "C2 direction law unstated. PLAYBOOKS L76: '(C2) always-in-RTH baseline — CÓ PnL path ⇒ scored identity'; L87 row gives only 'tier 2, cùng folds'. Implemented: unconditional LONG entry at D0 fill, hold to era-correct RTH close, no TP/SL (the only reading consistent with 'always-in'). Ratification required before gate 6."},
    {"id": "D-A3", "type": "AMBIGUITY", "severity": "MUST-PIN-BEFORE-SCORED-G6",
     "finding": "C1 RNG algorithm unstated. PLAYBOOKS L76: '(seed cố định 20261002, sign-draw deterministic theo session)'. Pinned here: sign=+1 iff sha256('FBES1-PLA-D0-S2|seed=20261002|'+session_date).digest()[0] < 0x80 else −1. Ratification required before gate 6 (a different generator = a different placebo path)."},
    {"id": "D-A4", "type": "IMPLEMENTATION-PIN", "severity": "LOW",
     "finding": "Window fencing: q80 and SL-donor windows computed chain-wide strict-past (trailing 252 computable-|m| sessions / trailing 20 non-short-flagged sessions), NOT fold-fenced; trading itself is fold-fenced by the frozen eval windows + POSITIONAL warmup carve-out enforced for every identity. Corroboration: under fold-fenced windows the F2-F4 eval heads would have zero trades for ~20+ sessions, contradicting the frozen eval-session counts (375/950/711/890, reproduced exactly)."},
    {"id": "D-A5", "type": "IMPLEMENTATION-PIN", "severity": "LOW",
     "finding": "Cost application: all-in/side booked as USD lines at the pinned Variant-A table values (fees 2.25 or 2.24-in-NFA-window + spread 6.25 + tier slippage); fill prices unadjusted; TP/SL levels derive from the fill price per SPEC §4."},
    {"id": "D-F1", "type": "FACT", "severity": None,
     "finding": "FOMCIN positional-warmup defect caught and fixed during this rehearsal: the first build traded warmup-position FOMC days (6 of 15 CONT-UP trades, e.g. 2013-03-20, 2018-01-31, 2022-01-26) because FOMC_STATEMENT_DAY has exclusion priority over WARMUP in the frozen list while the warmup carve-out is positional ('warmup 252 sessions per fold head — excluded from scoring'). Fix: FOMCIN set requires session_date > fold warmup_carve_out.last. Post-fix FOMCIN set = 104 sessions; scan confirms ZERO trades inside any warmup range across all 24 identities."},
    {"id": "D-F2", "type": "FACT", "severity": None,
     "finding": "Single D0 fill-bar gap: 2020-03-16 lacks the 08:31 bar (COVID limit-down open) — deterministic no-fill skip, no imputation. All other 2,925 eval sessions fill normally."},
    {"id": "D-F3", "type": "FACT", "severity": None,
     "finding": "7 eval sessions are m-unavailable (prior-session actual close or 08:30 open missing): 2012-04-09, 2012-10-31, 2015-04-06, 2021-04-05, 2023-04-10, 2025-01-10, 2026-04-06 (Easter-Monday-adjacent sessions, the 2025-01-10 mourning close, 2026 Easter Monday). E4-consistent no-signal skips."},
    {"id": "D-F4", "type": "FACT", "severity": None,
     "finding": "28 eval sessions have m == 0 exactly (open_0830 print-equal to C_prev) — no direction; C4 skips them, primaries classify tail=None."},
    {"id": "D-F5", "type": "FACT", "severity": "LOW",
     "finding": "Era-close validation vs baseline chain daily columns: last-RTH-bar close matches chain 'close' on 4,142/4,204 sessions; the 51 differing sessions differ by EXACTLY 1 tick (0.25) — the chain column embeds a different final-print convention; the consumed law is the panel last print (freeze pin: panel is 'THE ES data panel consumed by every signal/fill/SL computation'). RTH-open matches 4,193/4,204. Evaluation view only; no effect on any pass criterion."},
    {"id": "D-F6", "type": "FACT", "severity": None,
     "finding": "q80 tail share 553/2,926 = 18.9% (UP 289 / DN 264), consistent with the anatomy expectation '~20%' (ES_DEEPFOUR_V3_ADDENDUM L342)."},
    {"id": "D-F7", "type": "FACT", "severity": None,
     "finding": "Quarantine law honored: no ledger/counter/registry write anywhere; observed denominator NOT incremented; zero scored cells; S1 SEALED_UNTOUCHED; zero network; heavy-lock law honored (verdict FREE_PROVEN at start, single-shot panel reads, no worker touched, no lock taken)."},
    {"id": "D-V2-1-FIX", "type": "DEFECT-CORRECTION", "severity": None,
     "finding": "D-V2-1 (dryrun_v2/DRYRUN_V2_REPORT.md §5: 35 COVERAGE_LT60 -> HOLIDAY_PDF_EQUITY_2011_2015 relabels silently re-admitted those sessions as SL donors, 139 -> 104, changing sl_distance_pts on 244 eval dates / 177 exits) corrected here per the conservative-intent carryover law: the SL-donor exclusion set is again v1's exact 139-session set, evaluated on the V1 class labels (freezegen/exclude_list.json, read-only); the relabels are evidentiary metadata only. Eval surface stays on the v2 freeze (2,925 sessions; 2015-07-02 removed from EVAL). Asserted: donor-excluded == 139 == v1; 2015-07-02 donor-admitted."},
]


def run_pass(inp, out_dir):
    sessions, panel_stats = build_sessions(inp)
    st = derive_state(inp, sessions)
    assert st["counts_ok"], "fold eval-set derivation mismatch vs selection_freeze"

    results, index = OrderedDict(), OrderedDict()
    for iid in inp["ids"]:
        cfg = parse_identity(iid)
        rec, session_set = simulate(iid, cfg, st, inp, sessions)
        results[iid] = {
            "quarantine": QUARANTINE_HEADER,
            "generated_utc": GENERATED_UTC,
            "identity_id": iid,
            "arm_class": cfg["klass"],
            "delay_min": cfg.get("delay"),
            "cost_tier": cfg.get("tier"),
            "mechanics_citations": CITATIONS,
            "implementation_pins": ["D-A1 q80 numpy.percentile linear",
                                     "D-A2 C2 long hold-to-close",
                                     "D-A3 C1 sha256 seed 20261002",
                                     "D-A4 chain-wide strict-past windows",
                                     "D-A5 costs as USD lines"],
            "totals": {
                "n_sessions_in_set": rec["n_sessions"],
                "n_trades": len(rec["trades"]),
                "skips": rec["skips"],
                "n_trades_per_fold": rec["fold_n"],
            },
            "trades": rec["trades"],
        }
        index[iid] = [[t["session_date"], t["fill_bar_utc"], t["exit_bar_utc"]]
                      for t in rec["trades"]]

    import os
    os.makedirs(out_dir, exist_ok=True)
    summary = {
        "quarantine": QUARANTINE_HEADER,
        "generated_utc": GENERATED_UTC,
        "panel_stats": panel_stats,
        "validation": st["validation"],
        "per_identity": {iid: {
            "n_sessions_in_set": results[iid]["totals"]["n_sessions_in_set"],
            "n_trades": results[iid]["totals"]["n_trades"],
            "n_trades_per_fold": results[iid]["totals"]["n_trades_per_fold"],
            "skips": results[iid]["totals"]["skips"],
        } for iid in inp["ids"]},
    }
    with open(out_dir + "/trades_index.json", "w") as f:
        json.dump({"quarantine": QUARANTINE_HEADER, "generated_utc": GENERATED_UTC,
                   "index": index}, f, sort_keys=True)
    for iid in inp["ids"]:
        with open(f"{out_dir}/{iid}.json", "w") as f:
            json.dump(results[iid], f, sort_keys=True)
    with open(out_dir + "/summary.json", "w") as f:
        json.dump(summary, f, indent=1, sort_keys=True)

    canonical = json.dumps(index, sort_keys=True, separators=(",", ":"))
    return results, summary, hashlib.sha256(canonical.encode()).hexdigest(), st


def check_cost_sample(results, inp, n=20):
    """M3(b): recompute applied cost for n sampled trades by independent arithmetic."""
    all_trades = []
    for iid in inp["ids"]:
        for t in results[iid]["trades"]:
            all_trades.append((iid, t))
    assert len(all_trades) >= n
    picks = [all_trades[i] for i in
             np.linspace(0, len(all_trades) - 1, n).round().astype(int)]
    rows, ok_all = [], True
    cc = inp["cost"]["table"]
    for iid, t in picks:
        inwin = t["cost"]["reg_window_2014_10_01_2017_12_31"]
        fees = inp["cost"]["fees_window"] if inwin else inp["cost"]["fees_normal"]
        slip = inp["cost"]["slip"][_tier_of(iid, inp)]
        side = fees + inp["cost"]["spread"] + slip
        rt = 2 * side
        gross = t["direction"] * (t["exit_price"] - t["entry_price"]) * 50.0
        ok = (abs(t["cost"]["side_cost_usd"] - side) < 1e-9
              and abs(t["cost"]["rt_cost_usd"] - rt) < 1e-9
              and abs(t["gross_pnl_usd"] - gross) < 1e-9)
        table_ref = cc["window_exception_2014_10_01_to_2017_12_31"] if inwin else cc
        ok = ok and abs(table_ref["all_in_per_side"][_tier_of(iid, inp)] - side) < 1e-9
        ok_all = ok_all and ok
        rows.append({"identity": iid, "session_date": t["session_date"],
                     "tier": _tier_of(iid, inp), "reg_window": bool(inwin),
                     "recomputed_side": round(side, 6),
                     "recomputed_rt": round(rt, 6),
                     "recorded_rt": t["cost"]["rt_cost_usd"],
                     "recomputed_gross": round(gross, 6),
                     "recorded_gross": t["gross_pnl_usd"],
                     "match": bool(ok)})
    return {"quarantine": QUARANTINE_HEADER, "n_sampled": n,
            "all_match": bool(ok_all), "samples": rows}


def _tier_of(iid, inp):
    cfg = parse_identity(iid)
    return cfg["tier"]


V1_INDEX = (WT + "/research/control/FUTURES-ES-PB1-V1/dryrun/quarantine/"
            "trades_index.json")   # v1 HISTORY, read-only baseline (criterion d)


def check_surface_delta(index_v2):
    """M2(d): v2 index == v1 index minus EXACTLY the 2015-07-02 rows, per identity.

    Law: the v2 freeze differs from v1 only by excluding session 2015-07-02 from
    F2; q80/SL-donor state windows are chain-wide over unchanged chain sessions,
    so no other session's trade may change. Any other difference = CRITICAL.
    """
    v1 = json.load(open(V1_INDEX))["index"]
    ok = set(v1) == set(index_v2)
    removed_ids, rows = [], []
    for iid in sorted(v1):
        old = v1[iid]
        rem = [t for t in old if t[0] == "2015-07-02"]
        kept = [t for t in old if t[0] != "2015-07-02"]
        new = index_v2.get(iid, [])
        same = (new == kept)
        ok = ok and same
        if rem:
            removed_ids.append(iid)
        rows.append({"identity": iid, "v1_trades": len(old), "v2_trades": len(new),
                     "removed_2015_07_02": len(rem),
                     "list_identical_after_removal": same})
    return {"quarantine": QUARANTINE_HEADER,
            "criterion": "M2(d) surface delta vs v1 quarantine index: ONLY trades dated "
                         "2015-07-02 removed (freeze repair, F2); NO other change "
                         "permitted (any unexpected difference = CRITICAL)",
            "v1_index_baseline": V1_INDEX,
            "v1_index_quarantine_stamp": json.load(open(V1_INDEX))["quarantine"],
            "identities_with_removed_trades": removed_ids,
            "n_trades_removed_total": sum(r["removed_2015_07_02"] for r in rows),
            "per_identity": rows,
            "verdict": "PASS" if ok else "FAIL"}


def check_warmup_regression(results, inp):
    """M2(e): zero warmup-position trades across all 24 identities (v1 D-F1 class)."""
    folds = inp["folds"]
    warm_last = {f["fold"]: f["warmup_carve_out"]["last"] for f in folds}
    warm_dates = {e["session_date"] for e in inp["excl"]["exclusions"]
                  if e["reason_class"] == "WARMUP"}
    bad, n_tr = [], 0
    for iid in inp["ids"]:
        for t in results[iid]["trades"]:
            n_tr += 1
            d, fo = t["session_date"], t["fold"]
            if fo in warm_last and d <= warm_last[fo]:
                bad.append({"identity": iid, "session_date": d,
                            "why": "session <= fold warmup_carve_out.last"})
            if d in warm_dates:
                bad.append({"identity": iid, "session_date": d,
                            "why": "WARMUP-labelled excluded session"})
    return {"quarantine": QUARANTINE_HEADER,
            "criterion": "M2(e) FOMCIN warmup-defect regression (v1 finding D-F1 class): "
                         "zero trades at or before any fold warmup head and zero trades "
                         "on WARMUP-labelled sessions, across all 24 identities",
            "n_trades_scanned": n_tr,
            "violations": bad,
            "verdict": "PASS" if not bad else "FAIL"}


def main(lock_record="NOT_RECORDED"):
    inp = load_inputs()
    res1, sum1, sha1, st = run_pass(inp, DRYRUN + "/quarantine")

    # mid-run lock re-check is performed by the caller between passes when run
    # in two invocations; in this single invocation both passes re-read disk.
    res2, sum2, sha2, _ = run_pass(inp, DRYRUN + "/quarantine_rerun")

    # M3(a) enumeration
    frozen_ids = list(inp["ids"])
    sim_ids = list(res1.keys())
    enum_ok = frozen_ids == sim_ids
    enum = {"quarantine": QUARANTINE_HEADER,
            "criterion": "M3(a) identity enumeration byte-exact vs selection_freeze.identity_table",
            "n_frozen": len(frozen_ids), "n_simulated": len(sim_ids),
            "set_equal": set(frozen_ids) == set(sim_ids),
            "order_equal": frozen_ids == sim_ids,
            "extras": [i for i in sim_ids if i not in set(frozen_ids)],
            "missing": [i for i in frozen_ids if i not in set(sim_ids)],
            "verdict": "PASS" if enum_ok else "FAIL"}

    # M3(b) cost recomputation
    sample = check_cost_sample(res1, inp, 20)
    sample["verdict"] = "PASS" if sample["all_match"] else "FAIL"

    # M3(c) determinism: byte-compare per-identity JSONs + index sha
    import hashlib as _h
    import os
    byte_ok, files_cmp = True, []
    for iid in inp["ids"]:
        a = open(f"{DRYRUN}/quarantine/{iid}.json", "rb").read()
        b = open(f"{DRYRUN}/quarantine_rerun/{iid}.json", "rb").read()
        same = a == b
        byte_ok = byte_ok and same
        files_cmp.append({"file": f"{iid}.json", "sha_pass1": _h.sha256(a).hexdigest(),
                          "sha_pass2": _h.sha256(b).hexdigest(), "identical": same})
    det_ok = byte_ok and sha1 == sha2
    det = {"quarantine": QUARANTINE_HEADER,
           "criterion": "M3(c) determinism: two full passes, byte-identical per-identity outputs + identical trades-index sha",
           "trades_index_sha_pass1": sha1, "trades_index_sha_pass2": sha2,
           "all_identity_files_byte_identical": bool(byte_ok),
           "files": files_cmp,
           "verdict": "PASS" if det_ok else "FAIL"}

    # M2(d)/M2(e) — POST-HOC checks only (shim S5); the pass-1 index on disk is
    # the exact compared artifact.
    delta = check_surface_delta(
        json.load(open(DRYRUN + "/quarantine/trades_index.json"))["index"])
    warm = check_warmup_regression(res1, inp)

    digest = {
        "quarantine": QUARANTINE_HEADER,
        "schema": "dryrun_v2_1_digest@1",
        "cycle_id": "FUTURES-ES-PB1-V1", "lane": "DRYRUN-V2-1", "gate": 4,
        "generated_utc": GENERATED_UTC,
        "head_sha": "148a7bf52b4e4351ae156e4f704a7e7e22c87f0a",
        "law_quarantine": "budget counters untouched; outputs descriptive-only; zero scored cells; observed denominator NOT incremented; NO GO exists or is implied",
        "law_zero_denominator": "no ledger/counter/registry write anywhere; ALL numerics QUARANTINED descriptive-only; zero scored cells; zero denominator consumption; NO GO exists or is implied",
        "freeze_surface": {"selection_freeze_v2": "repair/selection_freeze_v2.json",
                           "exclude_list_v2": "repair/exclude_list_v2.json",
                           "repair_change_vs_v1": "exclude set + exactly one in-panel session 2015-07-02 (F2); eval surface 2926 -> 2925; F2 950 -> 949; warmup sets identical"},
        "donor_correction": inp["donor_correction"],
        "lock_record": {"pre_run": "FREE_PROVEN (locks inspect at lane start)",
                        "pre_panel_pass": lock_record,
                        "single_shot": True},
        "inputs": {"measured_shas": inp["measured_shas"],
                   "exclude_list_sha": inp["excl_sha"] if "excl_sha" in inp else None,
                   "freeze_schema": inp["freeze"]["schema"]},
        "panel_stats": sum1["panel_stats"],
        "era_validation": sum1["validation"],
        "summary_table": sum1["per_identity"],
        "findings": FINDINGS,
        "pass_criteria": {"a_enumeration": enum, "b_cost_recompute": sample,
                          "c_determinism": det,
                          "d_surface_delta": delta, "e_warmup_regression": warm},
        "gate4_verdict": "PASS" if (enum["verdict"] == "PASS"
                                    and sample["verdict"] == "PASS"
                                    and det["verdict"] == "PASS"
                                    and delta["verdict"] == "PASS"
                                    and warm["verdict"] == "PASS") else "FAIL",
    }
    with open(DRYRUN + "/dryrun_v2_1_digest.json", "w") as f:
        json.dump(digest, f, indent=1, sort_keys=True)
    print(json.dumps({
        "gate4_verdict": digest["gate4_verdict"],
        "a": enum["verdict"], "b": sample["verdict"], "c": det["verdict"],
        "d": delta["verdict"], "e": warm["verdict"],
        "index_sha": sha1,
        "surface_delta_removed_ids": delta["identities_with_removed_trades"],
        "n_trades": {k: v["n_trades"] for k, v in sum1["per_identity"].items()},
    }, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "NOT_RECORDED")
