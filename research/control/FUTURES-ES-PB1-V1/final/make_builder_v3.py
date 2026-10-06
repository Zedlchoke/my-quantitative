#!/usr/bin/env python
# FREEZE-V3-MACHINERY (lane M2) — derive final/dryrun_builder_v3.py from
# dryrun_v2_1/dryrun_builder_v2_1.py (HISTORY, read-only) with EXACTLY ONE
# logic change: the FLAG-BASED SPEC §4 SL-donor law (C2), implementing
# repair/FAIL_DONOR_VIOLATION.md (FAIL record D-V2-2).
#
# Method: exact-marker replacement with occurrence-count enforcement and a
# REVERSE-APPLY PROOF — reverting every recorded hunk on the produced file
# must byte-reproduce the source; this proves the two files differ ONLY
# inside the declared hunks (no unaccounted divergence).
#
# Hunk classes:
#   (a) THE one logic hunk: H4 (C2 donor law in load_inputs);
#   (b) documentation/metadata: H1 header, H2/H3 paths+schemas, H5 evidence
#       plumbing, H6 pin amendment note, H7 finding record, H10 digest;
#   (c) criterion-(d) CHECKER rewrite: H8/H9 (S5' post-hoc checker, not
#       simulation logic; the v2.1 lane rewrote it identically when its
#       baseline moved v1 -> v2; here it moves v2.1 -> v3 and becomes
#       EXPECTED-CHANGE-TOLERANT per mission M3d).

import hashlib

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
SRC = (WT + "/research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/"
       "dryrun_builder_v2_1.py")
DST = WT + "/research/control/FUTURES-ES-PB1-V1/final/dryrun_builder_v3.py"

src = open(SRC).read()
orig = src
PAIRS = []   # (new_text, old_text) in application order


def rep(old, new, tag, count=1):
    global src
    n = src.count(old)
    assert n == count, f"hunk {tag}: marker count {n} != {count}"
    src = src.replace(old, new)
    PAIRS.append((new, old))
    print("hunk applied:", tag)


def rep_between(start, end, new, tag, keep_end=True):
    global src
    i = src.index(start)
    assert src.count(start) == 1, f"hunk {tag}: start marker not unique"
    j = src.index(end, i)
    j2 = j + len(end)   # region [start..end] inclusive is consumed; `new` is
    old_text = src[i:j2]   # always self-contained
    src = src[:i] + new + src[j2:]
    PAIRS.append((new, old_text))
    print("hunk applied:", tag)


# ---------------------------------------------------------------- H1 ------
H1_NEW = '''# DRYRUN-V3 builder — cycle FUTURES-ES-PB1-V1, gate 4 dry-run (third
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
'''
rep_between("# DRYRUN-V2-1 builder —",
            "# dryrun/ (v1) and dryrun_v2/ (v2) are HISTORY: not modified, not executed.\n",
            H1_NEW, "H1-header", keep_end=False)

# ---------------------------------------------------------------- H2 ------
rep('DRYRUN = WT + "/research/control/FUTURES-ES-PB1-V1/dryrun_v2_1"',
    'DRYRUN = WT + "/research/control/FUTURES-ES-PB1-V1/final"',
    "H2-DRYRUN-path")

# ---------------------------------------------------------------- H3 ------
rep('    p_freeze = WT + "/research/control/FUTURES-ES-PB1-V1/repair/selection_freeze_v2.json"\n'
    '    p_excl = WT + "/research/control/FUTURES-ES-PB1-V1/repair/exclude_list_v2.json"',
    '    p_freeze = WT + "/research/control/FUTURES-ES-PB1-V1/final/selection_freeze_v3.json"\n'
    '    p_excl = WT + "/research/control/FUTURES-ES-PB1-V1/final/exclude_list_v3.json"',
    "H3-input-paths")

rep('        "exclude_list_v2.json": sha256_file(p_excl),\n'
    '        "selection_freeze_v2.json": sha256_file(p_freeze),',
    '        "exclude_list_v3.json": sha256_file(p_excl),\n'
    '        "selection_freeze_v3.json": sha256_file(p_freeze),',
    "H3b-measured-keys")

rep('    assert freeze["schema"] == "selection_freeze@2"\n'
    '    assert excl["schema"] == "exclude_list@2"',
    '    assert freeze["schema"] == "selection_freeze@3"\n'
    '    assert excl["schema"] == "exclude_list@3"',
    "H3c-schema-asserts")

# ---------------------------------------------------------------- H4 ------
# THE ONE LOGIC CHANGE — C1 (v2.1 carryover donor law) -> C2 (flag-based law)
C2_BLOCK = '''    # DRYRUN-V3 correction C2 (the ONE logic change vs dryrun_builder_v2_1.py;
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
'''
rep_between("    # DRYRUN-V2-1 correction C1 (the ONE logic change vs dryrun_builder_v2.py):",
            '''               for d in recovered), (
        "relabeled session labels are not COVERAGE_LT60 -> HOLIDAY_PDF_EQUITY_2011_2015")
''',
            C2_BLOCK, "H4-C2-DONOR-LAW (THE ONE LOGIC CHANGE)", keep_end=False)

# ---------------------------------------------------------------- H5 ------
rep('        "classes": classes, "excluded": excluded, "fomc_days": fomc_days,',
    '        "classes": classes, "excluded": excluded, "fomc_days": fomc_days,\n'
    '        "prev_short_flagged": prev_short_flagged,',
    "H5a-return-prev-set")

rep_between('''        "donor_correction": {''',
            '''            "session_2015_07_02_donor_admitted": "2015-07-02" not in short_flagged,
        },''',
            '''        "donor_law_v3": {
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
        },''',
            "H5b-donor-evidence-dict", keep_end=False)

# ---------------------------------------------------------------- H6 ------
rep('COVERAGE_LT60 — the "short/flagged" set of SPEC §4). Trading itself is',
    'COVERAGE_LT60 — the "short/flagged" set of SPEC §4; amended by C2/D-V2-2:\n'
    '#        the family is now the five short/flag classes of the CURRENT freeze\n'
    '#        (see load_inputs)). Trading itself is',
    "H6-D-A4-pin-amendment")

# ---------------------------------------------------------------- H7 ------
rep_between('    {"id": "D-V2-1-FIX", "type": "DEFECT-CORRECTION", "severity": None,',
            '''donor-excluded == 139 == v1; 2015-07-02 donor-admitted."},
]''',
            '''    {"id": "D-V2-2-FIX", "type": "DEFECT-CORRECTION", "severity": None,
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
    "D-V2-2-FIX.")''',
            "H7-findings-D-V2-2-FIX", keep_end=False)

# ---------------------------------------------------------------- H8 ------
H8_NEW = '''V21_QUAR = WT + "/research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/quarantine"
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
        if win_v3.get(d) is not None and win_v21law.get(d) is not None \\
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
            "verdict": "PASS" if ok else "FAIL"}'''
rep_between('V1_INDEX = (WT + "/research/control/FUTURES-ES-PB1-V1/dryrun/quarantine/"',
            '''            "verdict": "PASS" if ok else "FAIL"}''',
            H8_NEW, "H8-criterion-d-checker (S5' shim)", keep_end=False)

# ---------------------------------------------------------------- H9 ------
rep('''    # M2(d)/M2(e) — POST-HOC checks only (shim S5); the pass-1 index on disk is
    # the exact compared artifact.
    delta = check_surface_delta(
        json.load(open(DRYRUN + "/quarantine/trades_index.json"))["index"])''',
    '''    # M3(d)/M3(e) — criterion (d) compares pass-1 results against the v2.1
    # quarantine (HISTORY, read-only) with expected-change tolerance (shim
    # S5'); (e) is unchanged (shim S5).
    delta = check_surface_delta_v3(res1, st, inp)''',
    "H9-delta-call")

# --------------------------------------------------------------- H10 ------
rep('''        "schema": "dryrun_v2_1_digest@1",
        "cycle_id": "FUTURES-ES-PB1-V1", "lane": "DRYRUN-V2-1", "gate": 4,''',
    '''        "schema": "dryrun_v3_digest@1",
        "cycle_id": "FUTURES-ES-PB1-V1", "lane": "FREEZE-V3-MACHINERY",
        "gate": 4,''',
    "H10a-digest-schema")

rep('        "head_sha": "148a7bf52b4e4351ae156e4f704a7e7e22c87f0a",',
    '        "head_sha": "a855dab809be73c4b6eef60ab8c41566532febcd",',
    "H10b-digest-head")

rep('''        "freeze_surface": {"selection_freeze_v2": "repair/selection_freeze_v2.json",
                           "exclude_list_v2": "repair/exclude_list_v2.json",
                           "repair_change_vs_v1": "exclude set + exactly one in-panel session 2015-07-02 (F2); eval surface 2926 -> 2925; F2 950 -> 949; warmup sets identical"},
        "donor_correction": inp["donor_correction"],''',
    '''        "freeze_surface": {"selection_freeze_v3":
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
        "donor_law_v3": inp["donor_law_v3"],''',
    "H10c-digest-surface")

rep('''        "findings": FINDINGS,''',
    '''        "findings": FINDINGS,
        "findings_note": FINDINGS_NOTE,
        "impact_discipline_law":
            "the correction's real cost (removed trades + SL/exit changes on "
            "donor-window-affected dates) is REPORTED in "
            "pass_criteria.d_surface_delta as the expected consequence of "
            "implementing the SPEC §4 flag-based law (D-V2-2); it is not a "
            "machinery defect and no choice was made to preserve any prior "
            "PnL path",''',
    "H10d-digest-findings-note")

rep('    with open(DRYRUN + "/dryrun_v2_1_digest.json", "w") as f:',
    '    with open(DRYRUN + "/dryrun_v3_digest.json", "w") as f:',
    "H10e-digest-path")

rep('''        "surface_delta_removed_ids": delta["identities_with_removed_trades"],''',
    '''        "trades_removed_total": delta["n_trades_removed_total"],
        "sl_changed_dates": delta["sl_changed_dates"]["n"],
        "trades_sl_changed_total": delta["n_trades_sl_changed_total"],
        "exit_changed_total": delta["n_exit_changed_total"],
        "other_diffs": len(delta["unexpected_differences"]),
        "attribution_breaks": len(delta["attribution_breaks"]),''',
    "H10f-print-block")

# ------------------------------------------------- reverse-apply proof ----
chk = src
for new, old in reversed(PAIRS):
    assert chk.count(new) >= 1, "reverse-apply: hunk text not found"
    chk = chk.replace(new, old, 1)
assert chk == orig, "REVERSE-APPLY PROOF FAILED: unaccounted divergence"
print("REVERSE-APPLY PROOF: PASS — produced file differs from v2.1 source "
      "ONLY inside the", len(PAIRS), "declared hunks")

with open(DST, "w") as f:
    f.write(src)
print("dryrun_builder_v3.py sha256:",
      hashlib.sha256(src.encode()).hexdigest())
print("bytes:", len(src))
