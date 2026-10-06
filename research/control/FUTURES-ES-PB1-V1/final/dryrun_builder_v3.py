#!/usr/bin/env python
# DRYRUN-V3 builder — cycle FUTURES-ES-PB1-V1, gate 4 dry-run (third
# adjudication) on the combined corrected final state: freeze v3 (v2 + the 11
# y2016 fail-closed additions) + the FLAG-BASED SPEC §4 donor law.
#
# EXACT COPY of dryrun_v2_1/dryrun_builder_v2_1.py (the D-V2-1-corrected
# rehearsal machinery, itself an exact copy of the v1 builder with two v2
# shims) with EXACTLY ONE logic change (lane FREEZE-V3-MACHINERY mission M2;
# ANY other divergence = CRITICAL):
#   C2 (the correction law, repair/FAIL_DONOR_VIOLATION.md — FAIL record
#      D-V2-2, superseding the D-V2-1 carryover law as law): the SL-donor
#      exclusion set is FLAG-BASED on the CURRENT freeze (v3), per SPEC §4
#      [ERRATUM A7-SPEC-M5] "loại session short/flagged":
#        donor-excluded := {in-panel sessions bearing ANY exclusion/flag class
#                           in the short/flag family in exclude_list_v3}
#                         ∪ {prev_short-flagged sessions — the v2.1 carryover
#                           set (v1 labels, 139), carried so the correction can
#                           never re-admit a previously donor-excluded session}
#      short/flag family = {HOLIDAY_FACT_EARLYCLOSE,
#      HOLIDAY_PDF_EQUITY_2011_2015, HOLIDAY_2016_UNPROVEN_FAILCLOSED,
#      HOLIDAY_UNCERTAIN, COVERAGE_LT60} — the classes that mark a session
#      short or its close marks unproven/era-suspect. FOMC_STATEMENT_DAY
#      (full session; statement-risk only) and WARMUP (positional fold-head
#      label) are NOT short/flag classes and remain donor-admitted exactly as
#      in every prior state (FAIL record: expected set at freeze v2 = 139 +
#      2015-07-02 = 140). The donor-excluded COUNT is machine-DERIVED and
#      reported with per-session delta reasons — never asserted to a number.
#      Eval surface / eval sets / FOMCIN / WARMUP run on the v3 labels.
#   Lane shims (same class as v2 S2/S3, required to run this lane):
#      S2'' outputs under final/ (quarantine + quarantine_rerun);
#      S3'' digest head_sha = measured worktree HEAD a855dab8…; lane
#          FREEZE-V3-MACHINERY; schema dryrun_v3_digest@1; digest file
#          dryrun_v3_digest.json; digest embeds inp["donor_law_v3"] evidence
#          and the D-V2-2-FIX finding (documentation only, no simulation
#          logic touched).
#   Inherited shims (unchanged in effect): S1' v3 freeze/exclude inputs
#      (schema @3); S4 GENERATED_UTC fixed "2026-10-05"; S5' criterion (d)
#      rewritten to delta-vs-v2.1 (EXPECTED-CHANGE-TOLERANT per mission M3d:
#      removals + donor-window impact are the correction's real cost —
#      checked, tabulated, never presented as a defect); S6 main(lock_record).
# dryrun/ (v1), dryrun_v2/ (v2), dryrun_v2_1/ (v2.1) are HISTORY: not
# modified, not executed (the v2.1 quarantine is READ as the criterion-(d)
# baseline; the v1 label column is READ as the carryover baseline).
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
#        COVERAGE_LT60 — the "short/flagged" set of SPEC §4; amended by C2/D-V2-2:
#        the family is now the five short/flag classes of the CURRENT freeze
#        (see load_inputs)). Trading itself is
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
DRYRUN = WT + "/research/control/FUTURES-ES-PB1-V1/final"
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
    p_freeze = WT + "/research/control/FUTURES-ES-PB1-V1/final/selection_freeze_v3.json"
    p_excl = WT + "/research/control/FUTURES-ES-PB1-V1/final/exclude_list_v3.json"
    p_panel = ES_CACHE + "/es_1m_outright.parquet"
    p_chain = ES_CACHE + "/es_chain_T5.parquet"
    measured = {
        "SPEC_PB1_ES.md": sha256_file(p_spec),
        "es_1m_outright.parquet": sha256_file(p_panel),
        "es_chain_T5.parquet": sha256_file(p_chain),
        "exclude_list_v3.json": sha256_file(p_excl),
        "selection_freeze_v3.json": sha256_file(p_freeze),
    }
    assert measured["SPEC_PB1_ES.md"] == PIN_SPEC, "SPEC sha mismatch vs pin"
    assert measured["es_1m_outright.parquet"] == PIN_PANEL, "panel sha mismatch vs pin"
    assert measured["es_chain_T5.parquet"] == PIN_CHAIN, "chain sha mismatch vs pin"

    freeze = json.load(open(p_freeze))
    excl = json.load(open(p_excl))
    assert freeze["schema"] == "selection_freeze@3"
    assert excl["schema"] == "exclude_list@3"
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
    # DRYRUN-V3 correction C2 (the ONE logic change vs dryrun_builder_v2_1.py;
    # implements repair/FAIL_DONOR_VIOLATION.md — FAIL record D-V2-2): the
    # SL-donor exclusion set is FLAG-BASED on the CURRENT freeze (v3), per
    # SPEC §4 [ERRATUM A7-SPEC-M5] ("loại session short/flagged"):
    #   donor-excluded := {in-panel sessions bearing ANY exclusion/flag class
    #                      in the short/flag family in exclude_list_v3}
    #                    ∪ {prev_short-flagged sessions — the v2.1 carryover
    #                      set (v1 labels, 139), carried so the correction can
    #                      never re-admit a previously donor-excluded session}
    # short/flag family = the classes that mark a session short or its close
    # marks unproven/era-suspect. FOMC_STATEMENT_DAY (full session;
    # statement-risk only) and WARMUP (positional fold-head label) are NOT
    # short/flag classes and remain donor-admitted exactly as in every prior
    # state (FAIL record: expected set at freeze v2 = 139 + 2015-07-02 = 140).
    # The donor-excluded COUNT is machine-DERIVED and reported with
    # per-session delta reasons — never asserted to a number.
    excl_v1 = json.load(open(WT + "/research/control/FUTURES-ES-PB1-V1/"
                             "freezegen/exclude_list.json"))
    assert excl_v1["schema"] == "exclude_list@1", "v1 label column schema mismatch"
    classes_v1 = {}
    for it in excl_v1["exclusions"]:
        if not it.get("in_panel", False):
            continue
        classes_v1.setdefault(it["session_date"], set()).add(it["reason_class"])
    prev_short_flagged = {
        d for d, cs in classes_v1.items()
        if cs & {"HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_UNCERTAIN", "COVERAGE_LT60"}
    }
    assert len(prev_short_flagged) == 139, "carryover baseline drifted"
    donor_family_v3 = {"HOLIDAY_FACT_EARLYCLOSE",
                       "HOLIDAY_PDF_EQUITY_2011_2015",
                       "HOLIDAY_2016_UNPROVEN_FAILCLOSED",
                       "HOLIDAY_UNCERTAIN", "COVERAGE_LT60"}
    sf_flags = {d for d, cs in classes.items() if cs & donor_family_v3}
    short_flagged = sf_flags | prev_short_flagged
    assert prev_short_flagged <= short_flagged, "carryover union broken"
    # derived delta evidence (reported in the digest; NOT asserted to a count)
    delta_prev = sorted(short_flagged - prev_short_flagged)
    # the FAIL-record's v2 baseline is evaluated on the TRUE v2 labels
    # (repair/exclude_list_v2.json): expected 139 + 2015-07-02 = 140
    excl_v2 = json.load(open(WT + "/research/control/FUTURES-ES-PB1-V1/"
                             "repair/exclude_list_v2.json"))
    assert excl_v2["schema"] == "exclude_list@2"
    classes_v2 = {}
    for it in excl_v2["exclusions"]:
        if not it.get("in_panel", False):
            continue
        classes_v2.setdefault(it["session_date"], set()).add(it["reason_class"])
    fam_no_2016 = donor_family_v3 - {"HOLIDAY_2016_UNPROVEN_FAILCLOSED"}
    sf_v2_labels_true = {d for d, cs in classes_v2.items() if cs & fam_no_2016}
    delta_140 = sorted(short_flagged - sf_v2_labels_true)

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
        "prev_short_flagged": prev_short_flagged,
        "short_flagged": short_flagged, "folds": folds,
        "chain_dates": chain_dates, "held": held,
        "chain_close": chain_close, "chain_rth_open": chain_rth_open,
        "panel_path": p_panel, "measured_shas": measured,
        "donor_law_v3": {
            "law": "D-V2-2 correction C2 (repair/FAIL_DONOR_VIOLATION.md): "
                   "SL-donor exclusion is FLAG-BASED on the current freeze "
                   "(v3) per SPEC §4 [ERRATUM A7-SPEC-M5] — donor-excluded = "
                   "{in-panel sessions with any short/flag-family class in "
                   "exclude_list_v3} ∪ {v2.1 carryover set (v1 labels, 139)}",
            "donor_family_v3": sorted(donor_family_v3),
            "not_donor_classes": ["FOMC_STATEMENT_DAY", "WARMUP"],
            "carryover_source": "freezegen/exclude_list.json (schema "
                                "exclude_list@1, HISTORY, read-only)",
            "donor_excluded_count_v1_carryover": len(prev_short_flagged),
            "donor_excluded_count_v2_labels_true": len(sf_v2_labels_true),
            "v2_labels_true_source": "repair/exclude_list_v2.json (the "
                                     "FAIL-record baseline: '139 + 2015-07-02 "
                                     "= 140' evaluated on the v2 labels)",
            "donor_excluded_count_v3_derived": len(short_flagged),
            "delta_vs_139_per_session": [
                {"session_date": d,
                 "v3_classes": sorted(classes.get(d, set())),
                 "v1_classes": sorted(classes_v1.get(d, set())),
                 "reason": ("v2/v3 flag HOLIDAY_PDF_EQUITY_2011_2015 with no "
                            "v1 label (FAIL record D-V2-2 case 1)"
                            if "HOLIDAY_PDF_EQUITY_2011_2015"
                            in classes.get(d, set())
                            else "v3 flag HOLIDAY_2016_UNPROVEN_FAILCLOSED "
                                 "(y2016 fail-closed addition; D-V2-2 "
                                 "correction law applied to the new class)")}
                for d in delta_prev],
            "delta_vs_140_sessions": delta_140,
            "supersedes": "repair/DONOR_LAW_CARRYOVER.md (withdrawn by D-V2-2)",
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
    {"id": "D-V2-2-FIX", "type": "DEFECT-CORRECTION", "severity": None,
     "finding": "D-V2-2 (repair/FAIL_DONOR_VIOLATION.md: builder v2.1's "
                "carryover donor law keeps 2015-07-02 donor-admitted although "
                "the current freeze flags it HOLIDAY_PDF_EQUITY_2011_2015; "
                "builder v2's label-based 3-class list likewise donor-admitted "
                "the 35 relabeled flagged sessions — same violation class) "
                "corrected here per the SPEC §4 flag-based law: donor-"
                "excluded = {sessions with any short/flag-family class in "
                "exclude_list_v3} ∪ {the v2.1 carryover 139 (v1 labels)}; the "
                "count is machine-derived and reported in digest "
                "donor_law_v3 (never asserted); eval surface = freeze v3 "
                "(2,921). The carryover union guarantees the correction never "
                "re-admits a previously donor-excluded session. Impact "
                "discipline: SL distances and trade paths DO change on "
                "affected dates; the full impact table is digest "
                "pass_criteria.d_surface_delta; prior rehearsal outputs stand "
                "as history; NO choice was justified by keeping/restoring any "
                "prior PnL path."},
]

FINDINGS_NOTE = (
    "D-F2/D-F3/D-F4/D-F6 are FACTs recorded on the v1/v2.1 rehearsal "
    "surfaces (history); their surface-dependent counts are NOT re-asserted "
    "on the v3 surface. D-A1..D-A5 pins and D-F1/D-F5/D-F7 remain in force "
    "(D-A4 as amended by C2). The D-V2-1-FIX carryover law is WITHDRAWN by "
    "D-V2-2 (repair/FAIL_DONOR_VIOLATION.md) and is superseded here by "
    "D-V2-2-FIX.")


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


V21_QUAR = WT + "/research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/quarantine"
V21_INDEX = V21_QUAR + "/trades_index.json"   # v2.1 HISTORY, read-only baseline
REMOVED_DATES = ("2016-07-01", "2020-07-02", "2021-07-02", "2021-12-31")


def _donor_series(dates, rth_range, excluded_set):
    """Recompute an SL-donor series (values + trailing-20 donor windows) under
    a given donor-exclusion set on the SAME ranges — used ONLY by the
    criterion-(d) checker for causal attribution of SL-distance changes
    (mirrors derive_state's loop; not simulation logic)."""
    sldist, donors, windows = {}, [], {}
    for d in dates:
        if len(donors) >= 20:
            sldist[d] = float(np.median(donors[-20:]))
            windows[d] = tuple(donors[-20:])
        else:
            sldist[d] = None
        r = rth_range.get(d)
        if r is not None and (d not in excluded_set):
            donors.append(r)
    return sldist, windows


def check_surface_delta_v3(results_v3, st, inp):
    """M3(d): full impact delta vs the v2.1 quarantine (HISTORY, read-only).

    EXPECTED changes ONLY (mission M3d):
      (i)  trades removed exactly on the newly-excluded eval dates
           (2016-07-01 F2; 2020-07-02, 2021-07-02, 2021-12-31 F3);
      (ii) SL-distance changes on dates whose trailing-20 donor window
           composition changed because of the newly donor-excluded sessions
           (2015-07-02 + the 4 v3 additions), with knock-on TP/SL/exit
           changes — the correction's real cost, tabulated, NOT a defect;
      (iii) NO other change (any other difference = CRITICAL).
    Pairing key: (identity, session_date) — one trade per identity per
    session. Fields that must be identical on every common trade: fold,
    direction, m, q80_threshold, signal_bar_utc, fill_bar_utc, entry_price,
    cost. Impact-allowed fields: sl_distance_pts, tp_price, sl_price,
    exit_reason, exit_bar_utc, exit_price, gross_pnl_usd, net_pnl_usd — any
    difference there requires a sl_distance_pts difference on that trade AND
    a donor-window-composition change at that date (causal attribution via
    _donor_series under the v2.1 carryover law).
    """
    v21 = json.load(open(V21_INDEX))["index"]
    idx_v3 = {iid: [[t["session_date"], t["fill_bar_utc"], t["exit_bar_utc"]]
                    for t in results_v3[iid]["trades"]]
              for iid in results_v3}
    ok = set(v21) == set(idx_v3)

    # causal attribution: both donor series recomputed on the same ranges
    sld_v21law, win_v21law = _donor_series(inp["chain_dates"], st["rth_range"],
                                           inp["prev_short_flagged"])
    sld_v3, win_v3 = _donor_series(inp["chain_dates"], st["rth_range"],
                                   inp["short_flagged"])
    # cross-check: the recomputed v3-law series must equal the builder state
    assert sld_v3 == st["sldist"], "recomputed v3 donor series mismatch"
    comp_changed, sl_changed = [], []
    for d in inp["chain_dates"]:
        if win_v3.get(d) is not None and win_v21law.get(d) is not None \
                and win_v3[d] != win_v21law[d]:
            comp_changed.append(d)
            if sld_v3[d] != sld_v21law[d]:
                sl_changed.append(d)
    sl_changed_set = set(sl_changed)

    REQUIRED = ("fold", "direction", "m", "q80_threshold", "signal_bar_utc",
                "fill_bar_utc", "entry_price", "cost")
    IMPACT = ("sl_distance_pts", "tp_price", "sl_price", "exit_reason",
              "exit_bar_utc", "exit_price", "gross_pnl_usd", "net_pnl_usd")
    EXIT = ("exit_reason", "exit_bar_utc", "exit_price")
    n_removed_total, other_diffs, attribution_breaks = 0, [], []
    per_identity, removed_detail, impact_rows = [], [], {}
    for iid in sorted(v21):
        v21_tr = json.load(open(f"{V21_QUAR}/{iid}.json"))["trades"]
        old_t = {t["session_date"]: t for t in v21_tr}
        new_t = {t["session_date"]: t for t in results_v3[iid]["trades"]}
        rem_n = sum(1 for d in old_t if d in REMOVED_DATES)
        n_removed_total += rem_n
        if rem_n:
            removed_detail.append({"identity": iid, "n_removed": rem_n,
                                   "dates": sorted(d for d in old_t
                                                   if d in REMOVED_DATES)})
        kept_dates = [d for d in old_t if d not in REMOVED_DATES]
        len_ok = len(new_t) == len(kept_dates)
        extra = sorted(set(new_t) - set(kept_dates))
        if extra:
            other_diffs.append({"identity": iid,
                                "unexpected_new_dates": extra})
        ok = ok and len_ok and not extra
        n_id = {"identity": iid, "v21_trades": len(old_t),
                "v3_trades": len(new_t), "removed": rem_n,
                "common_compared": 0, "sl_changed_trades": 0,
                "exit_changed_trades": 0}
        for d in kept_dates:
            if d not in new_t:
                other_diffs.append({"identity": iid, "session_date": d,
                                    "why": "expected common trade missing"})
                continue
            a, b = old_t[d], new_t[d]
            n_id["common_compared"] += 1
            req_bad = [k for k in REQUIRED if a[k] != b[k]]
            if req_bad:
                other_diffs.append({"identity": iid, "session_date": d,
                                    "required_field_diffs": req_bad})
            imp_bad = [k for k in IMPACT if a[k] != b[k]]
            if not imp_bad:
                continue
            if a["sl_distance_pts"] == b["sl_distance_pts"]:
                attribution_breaks.append(
                    {"identity": iid, "session_date": d,
                     "why": "impact fields differ but sl_distance_pts equal"})
                continue
            if d not in sl_changed_set:
                attribution_breaks.append(
                    {"identity": iid, "session_date": d,
                     "why": "trade changed on a date whose donor window did "
                            "not change under the recomputed v2.1-law series"})
                continue
            exit_changed = any(k in imp_bad for k in EXIT)
            n_id["sl_changed_trades"] += 1
            if exit_changed:
                n_id["exit_changed_trades"] += 1
            row = impact_rows.setdefault(d, {
                "date": d,
                "sl_distance_pts_v21_law":
                    None if sld_v21law.get(d) is None
                    else round(sld_v21law[d], 12),
                "sl_distance_pts_v3":
                    None if sld_v3.get(d) is None else round(sld_v3[d], 12),
                "n_trades_sl_changed": 0, "n_exit_changed": 0,
                "identities": []})
            row["n_trades_sl_changed"] += 1
            row["identities"].append(iid)
            if exit_changed:
                row["n_exit_changed"] += 1
        per_identity.append(n_id)
    for row in impact_rows.values():
        row["identities"] = sorted(set(row["identities"]))
    impact = [impact_rows[d] for d in sorted(impact_rows)]

    ok = ok and not other_diffs and not attribution_breaks
    return {"quarantine": QUARANTINE_HEADER,
            "criterion": "M3(d) surface + trade-level delta vs the v2.1 "
                         "quarantine: (i) trades removed exactly on the 4 "
                         "newly-excluded eval dates; (ii) SL-distance changes "
                         "only on dates whose donor-window composition "
                         "changed (2015-07-02 + the 4 v3 donor additions), "
                         "with knock-on exit changes — the correction's real "
                         "cost, reported, not a defect; (iii) NO other change "
                         "(any unexpected difference = CRITICAL)",
            "v21_index_baseline": V21_INDEX,
            "v21_index_quarantine_stamp":
                json.load(open(V21_INDEX))["quarantine"],
            "removed_dates_expected": list(REMOVED_DATES),
            "n_trades_removed_total": n_removed_total,
            "removed_detail": removed_detail,
            "donor_window_composition_changed": {
                "n": len(comp_changed),
                "first": comp_changed[0] if comp_changed else None,
                "last": comp_changed[-1] if comp_changed else None},
            "sl_changed_dates": {"n": len(sl_changed), "list": sl_changed},
            "impact_table": impact,
            "n_trades_sl_changed_total": sum(r["n_trades_sl_changed"]
                                             for r in impact),
            "n_exit_changed_total": sum(r["n_exit_changed"] for r in impact),
            "unexpected_differences": other_diffs,
            "attribution_breaks": attribution_breaks,
            "per_identity": per_identity,
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

    # M3(d)/M3(e) — criterion (d) compares pass-1 results against the v2.1
    # quarantine (HISTORY, read-only) with expected-change tolerance (shim
    # S5'); (e) is unchanged (shim S5).
    delta = check_surface_delta_v3(res1, st, inp)
    warm = check_warmup_regression(res1, inp)

    digest = {
        "quarantine": QUARANTINE_HEADER,
        "schema": "dryrun_v3_digest@1",
        "cycle_id": "FUTURES-ES-PB1-V1", "lane": "FREEZE-V3-MACHINERY",
        "gate": 4,
        "generated_utc": GENERATED_UTC,
        "head_sha": "a855dab809be73c4b6eef60ab8c41566532febcd",
        "law_quarantine": "budget counters untouched; outputs descriptive-only; zero scored cells; observed denominator NOT incremented; NO GO exists or is implied",
        "law_zero_denominator": "no ledger/counter/registry write anywhere; ALL numerics QUARANTINED descriptive-only; zero scored cells; zero denominator consumption; NO GO exists or is implied",
        "freeze_surface": {"selection_freeze_v3":
                           "final/selection_freeze_v3.json",
                           "exclude_list_v3": "final/exclude_list_v3.json",
                           "change_vs_v2": "exclude set +4 in-panel sessions "
                                           "(2016-07-01 F2; 2020-07-02, "
                                           "2021-07-02, 2021-12-31 F3) + 7 "
                                           "COVERAGE_LT60 -> "
                                           "HOLIDAY_2016_UNPROVEN_FAILCLOSED "
                                           "evidence relabels; eval surface "
                                           "2925 -> 2921 (F2 949 -> 948, F3 "
                                           "711 -> 708, F3 eval-last "
                                           "2021-12-31 -> 2021-12-30)"},
        "donor_law_v3": inp["donor_law_v3"],
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
        "findings_note": FINDINGS_NOTE,
        "impact_discipline_law":
            "the correction's real cost (removed trades + SL/exit changes on "
            "donor-window-affected dates) is REPORTED in "
            "pass_criteria.d_surface_delta as the expected consequence of "
            "implementing the SPEC §4 flag-based law (D-V2-2); it is not a "
            "machinery defect and no choice was made to preserve any prior "
            "PnL path",
        "pass_criteria": {"a_enumeration": enum, "b_cost_recompute": sample,
                          "c_determinism": det,
                          "d_surface_delta": delta, "e_warmup_regression": warm},
        "gate4_verdict": "PASS" if (enum["verdict"] == "PASS"
                                    and sample["verdict"] == "PASS"
                                    and det["verdict"] == "PASS"
                                    and delta["verdict"] == "PASS"
                                    and warm["verdict"] == "PASS") else "FAIL",
    }
    with open(DRYRUN + "/dryrun_v3_digest.json", "w") as f:
        json.dump(digest, f, indent=1, sort_keys=True)
    print(json.dumps({
        "gate4_verdict": digest["gate4_verdict"],
        "a": enum["verdict"], "b": sample["verdict"], "c": det["verdict"],
        "d": delta["verdict"], "e": warm["verdict"],
        "index_sha": sha1,
        "trades_removed_total": delta["n_trades_removed_total"],
        "sl_changed_dates": delta["sl_changed_dates"]["n"],
        "trades_sl_changed_total": delta["n_trades_sl_changed_total"],
        "exit_changed_total": delta["n_exit_changed_total"],
        "other_diffs": len(delta["unexpected_differences"]),
        "attribution_breaks": len(delta["attribution_breaks"]),
        "n_trades": {k: v["n_trades"] for k, v in sum1["per_identity"].items()},
    }, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "NOT_RECORDED")
