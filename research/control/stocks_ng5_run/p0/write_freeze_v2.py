"""Write the round-3 freeze artifacts (A2R-F1..F4 + A4): shadow inventory v2
and representation addendum v2.  Deterministic; no network."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time

CTL = pathlib.Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng5/integration/research/control/stocks_ng5_run")


def main() -> int:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    v2 = {
        "schema": "stocks_ng5_d2_shadow_inventory_freeze@2",
        "cycle_id": "STOCKS-NG5",
        "frozen_at_utc": ts,
        "supersedes": "d2_shadow_inventory_freeze.json (v1, commit 1bc2f19b) — superseded pre-rho per A2R-F1/A4; v1 remains committed history",
        "law": "plan §7 A7-F2 + A2 review: the inventory is enumerated and frozen BEFORE any rho; an under-enumerated inventory is an invalid PASS (fail-closed). Any shadow that cannot be constructed must be recorded UNMEASURABLE-with-reason => D2 records INVALID_PASS and refuses. The 0.20 pooled |rho| bar is immovable (G9).",
        "anchor_representation_to_measure": "ANCHOR-TREND-L13 weekly decision weights on the state series indexed ONLY on available weekly observations (reindex convention; representation addendum v2), starting 2006-04-28 (first complete weekly observation)",
        "data_authority": {
            "price_series": "P0 staging sha-pinned EODHD adjusted closes (QQQ/SPY/QQEW/RSP)",
            "macro_series": "P0-extension re-pinned FRED DGS10/DFII10 (granted set; digests in p0_extension_macro_shadows.json); AX2 as-of availability (+1 conservative day)",
            "xlk": "NOT USED — the D1 R0-S2 'XLK/SPY momentum OR QQQ/SPY rolling-beta' alternative is frozen at the rolling-beta form (computable from pinned data; no new instrument authority)",
        },
        "shadow_series_frozen": [
            {"id": "SH-A1-RELMOM-13W", "desc": "QQQ/SPY relative price momentum, L=13w change of QQQ/SPY log ratio (D1 R0-S1; V2 ancestor template)", "class": "E_FALSIFICATION"},
            {"id": "SH-A1b-RELMOM-52W", "desc": "QQQ/SPY relative price momentum, L=52w (12-1 month class, V2 A4_XSEC exact horizon)", "class": "E_FALSIFICATION"},
            {"id": "SH-A2-ABSMOM-63D", "desc": "QQQ absolute momentum, 63-SESSION (momentum_63s generic shadow)", "class": "E_FALSIFICATION"},
            {"id": "SH-A2b-ABSMOM-252D", "desc": "QQQ absolute momentum, 252-session", "class": "E_FALSIFICATION"},
            {"id": "SH-A3-VOLLEVEL-21S", "desc": "QQQ realized vol LEVEL state, trailing 21-SESSION window (D1 R0-S3 declared unit; A2R-F5 unit corrected)", "class": "E_FALSIFICATION"},
            {"id": "SH-A3b-VOLLEVEL-52W", "desc": "QQQ realized vol level, 52-week window (sensitivity form)", "class": "E_FALSIFICATION"},
            {"id": "SH-A4-DOLLARVOL", "desc": "QQQ dollar-volume level state, 63-session median (D1 R0-S5)", "class": "E_FALSIFICATION"},
            {"id": "SH-A5-DOW", "desc": "decision day-of-week geometry (weekly grid; near-degenerate, kept for completeness)", "class": "E_FALSIFICATION"},
            {"id": "SH-A5b-WEEKPARITY", "desc": "week-of-year / ISO-week parity calendar geometry (D1 R0-S6; A2R-F1(c))", "class": "E_FALSIFICATION"},
            {"id": "SH-A5c-MONTHEND", "desc": "month-end / calendar-distance geometry shadow (plan §7 A5; A2R-F1(e))", "class": "E_FALSIFICATION"},
            {"id": "SH-A6-QQQHEAT", "desc": "beta-decomposition book: hold QQQ iff QQQ 13w momentum > 0 (plan §7 A6)", "class": "E_FALSIFICATION"},
            {"id": "SH-A7a-ROLLBETA-63S", "desc": "QQQ/SPY rolling 63-SESSION beta state (D1 R0-S2 frozen alternative; dossier SPY-beta concentration; A2R-F1(c)/(d))", "class": "E_FALSIFICATION"},
            {"id": "SH-A8a-DFII10-SHOCK-13W", "desc": "DFII10 13-week SHOCK state (real-yield shock; cross-plane RATES-NG1 template)", "class": "E_FALSIFICATION"},
            {"id": "SH-A8b-DGS10-LEVEL-13W", "desc": "DGS10 nominal LEVEL state, 13-week z (D1 R0-S4; falsification #14/#15 lineage — the program's most lethal control; A2R-F1(a))", "class": "E_FALSIFICATION"},
            {"id": "SH-A9-DIV-DECOMP", "desc": "SFV13 dividend-policy decomposition: price-only vs distribution-only components of the EW/CW spread", "class": "E_FALSIFICATION"},
            {"id": "SH-A9b-TRENDDEF-GEOM", "desc": "SFV2-A5 TREND-DEFENSIVE book-geometry shadow: weekly binary QQQ-vs-cash TSM12 state", "class": "E_FALSIFICATION"},
            {"id": "SH-A10-MNQ-CAUSAL-TEMPLATE", "desc": "QuantPulse IF1/IF2 index-causal class: no rescue of index-level causal conditioning forms; carried as binding template rule + measured via A1/A2 price shadows", "class": "TEMPLATE_RULE"},
        ],
        "not_constructible_register": {
            "law": "A7-F2 fail-closed: any shadow in the binding declarations that cannot be constructed on this cycle's pinned substrate is recorded here with its reason; a D2 run that meets an UNMEASURABLE member not registered here is an INVALID PASS.",
            "entries": [
                {"shadow": "goodwill_bloat / balance-sheet bloat forms", "reason": "V8/NG1 ancestry requires the SEC fundamentals panel; no fundamentals substrate pinned in this price-only cycle; ancestry closed (V8 cluster #9, NG1 veto -0.3547)"},
                {"shadow": "amendment cadence-latency / filing-event forms", "reason": "requires Form-4/EDGAR substrate; not pinned in-cycle; ancestry measured-closed (V11 cluster #13, V12, NG1/NG2)"},
                {"shadow": "downward-correction drift breadth", "reason": "requires revision substrate; not pinned in-cycle; closed (SFV10-A5-H1)"},
                {"shadow": "earnings/SUE forms", "reason": "earnings-history entitlement closed at STOCKS-NG3 F1; not pinned in-cycle"},
            ],
        },
        "kill_rule": "pooled |rho| = max |weight-Pearson, weight-Spearman(midrank), signal-rank-Spearman(midrank)| vs each shadow on the frozen weekly decision grid under the M0 contract; ANY shadow over 0.20 => family VETOED, cycle closes 0/3 with terminal A7",
        "non_scored": "D2 computes NO returns/PnL/PF/Sharpe of the anchor; correlations + populations + turnover + cost ceiling only",
    }
    v2["self_hash_note"] = "self_hash = sha256 of this JSON with self_hash field empty, pinning the inventory before any rho"
    v2_copy = dict(v2)
    v2_copy["self_hash"] = ""
    blob = json.dumps(v2_copy, indent=1, sort_keys=True).encode()
    v2["self_hash"] = hashlib.sha256(blob).hexdigest()
    (CTL / "d2/d2_shadow_inventory_freeze_v2.json").write_text(
        json.dumps(v2, indent=1, sort_keys=True) + "\n")
    print("shadow inventory v2 written; self_hash", v2["self_hash"][:16])

    recon2 = {
        "schema": "stocks_ng5_representation_reconciliation@2",
        "cycle_id": "STOCKS-NG5",
        "frozen_at_utc": ts,
        "supersedes_sections": "p0_addendum_representation_reconciliation.json (v1) stays binding for SKIP-AND-HOLD; v2 adds the P-12 hole + grid-start pins ordered by A2R-F3/F4",
        "z_hole_semantics_frozen": "REINDEX reading: the weekly state series is indexed ONLY on available weekly observations (a week with any of the four adjusted closes missing yields NO observation — no imputation, no forward-fill); z_t is computed over the trailing 104 COMPLETE weekly observations; warmup is counted in complete observations; the affected weekly decision (ISO week of 2008-11-28) is SKIPPED under SKIP-AND-HOLD and the book holds its prior leg; exactly one skipped decision in-window; the IDENTICAL convention binds the anchor and EVERY shadow series (P-12).",
        "weekly_grid_start_frozen": "2006-04-28 — the first complete weekly observation (P0-evidenced QQEW first session 2006-04-25; A2R-F4: the D1 '2006-04-21' assertion is impossible and is SUPERSEDED-AS-EVIDENCED)",
        "binding_on": ["D2", "S", "I", "Z", "E"],
    }
    (CTL / "p0/p0_addendum_representation_reconciliation_v2.json").write_text(
        json.dumps(recon2, indent=1, sort_keys=True) + "\n")
    print("representation v2 written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
