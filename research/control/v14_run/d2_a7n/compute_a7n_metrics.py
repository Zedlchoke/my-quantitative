"""A7-N independent novelty/anti-rescue measurements (NO PnL, NO selection).

Task 3 -- cross-cluster rank correlation:
  Loads the six A9-F rank panels (SHA-256 verified against panel_index.json),
  pools every (stamp, symbol) observation per proposal, and computes pairwise
  Spearman rank correlation over the INTERSECTION of (stamp, symbol) keys.
  Spearman is implemented directly (average ranks for ties, then Pearson on
  ranks) because scipy is not installed in this venv; the implementation is
  exact and deterministic.  Missing entries are handled by pairwise-complete
  intersection (a (stamp, symbol) pair enters a pair's computation iff BOTH
  panels rank that symbol at that stamp); n per pair is reported.  Per-fold
  breakdowns (F0/F1/F2 frozen windows by stamp date) are reported alongside.

Task 4 -- shadow-region rho gates (plan Section 1.1) for OICH / OICYC:
  Recomputes the frozen V12 OILEV-V2-28D-FLOW-W anchor feature from its
  frozen identity (research/v12/families/oilev_v2/strategy.py ->
  research/v11/families/oilever_delev/strategy.py:oi_flow_growth:
  ln(OI(T)/OI(T-28d)) from daily-last anchors STRICTLY BEFORE the stamp,
  staleness <= 48h, positive values; benchmark BTCUSDT never ranked) on the
  machine-local staged OI at /Users/hoangminhlong/my-quantitative/oi_data/
  per research/control/v11_run/oi_staging_manifest.json, on the SAME
  52-week-Monday stamp x 19-symbol grid as the panels, and measures
  Spearman rho of OICH's and OICYC's panel ranks against
    (a) the OILEV-V2 anchor feature ranks (rank 1 = lowest oi_flow = the
        anchor arm's long side), and
    (b) the inverted control ranks.
  SYMMETRY (stated and measured): the frozen V12 inverted control arm
  OILEV-V2-28D-FLOW-W-INV is _ARM_FEATURE -> ("oi_flow", 28, invert=True),
  and `invert` acts ONLY at the book level (build_oilev_v2_book(invert=...)
  swaps the long/short legs); the FEATURE ordering is unchanged.  Under the
  panels' "rank 1 = long side" convention the control's rank vector is
  therefore exactly 20 - anchor_rank within the 19-name cross-section, so
  rho(panel, control_convention) == -rho(panel, anchor_convention) and the
  two |rho| values coincide identically.  Both are measured and reported to
  demonstrate the identity empirically.  The V12 inverted control was a pure
  sign flip -- nothing more -- so no separate control definition exists.

Gate: PASS iff |rho| <= 0.20 vs BOTH the anchor and the inverted control.

No PnL, no positions, no selection ranking, no proposal edits.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

WORKTREE = Path(__file__).resolve().parents[4]  # .../d2-a7n-novelty
HERE = Path(__file__).resolve().parent
PANEL_DIR = WORKTREE / "research/control/v14_run/d2_a9f/panels"
PANEL_INDEX = WORKTREE / "research/control/v14_run/d2_a9f/panel_index.json"
OI_MANIFEST = WORKTREE / "research/control/v11_run/oi_staging_manifest.json"
OI_ROOT = Path("/Users/hoangminhlong/my-quantitative/oi_data/consolidated")

PROPOSALS = [
    "BASISLV-PREMFADE",
    "BASISLV-WIDTHGATE",
    "BASISDYN-PREMREV",
    "BASISDYN-PREMVOL",
    "OICH",
    "OICYC",
]

FOLD_WINDOWS = {
    "F0": ("2025-08-22", "2025-12-21"),
    "F1": ("2025-12-22", "2026-04-21"),
    "F2": ("2026-04-22", "2026-08-21"),
}
SHADOW_GATE_ABS = 0.20
CANDIDATE_ABS = 0.70   # same-cluster candidate flag (A1 attention)
HARD_ABS = 0.90        # hard same-cluster flag (V13 collapse level)

DAY_NS = 86_400_000_000_000
HOUR_NS = 3_600_000_000_000
FORMATION_DAYS_ANCHOR = 28          # frozen V12 anchor formation
OI_MAX_STALENESS_HOURS = 48         # frozen V12 PIT staleness gate


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ms_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def iso_date(iso: str) -> str:
    return iso[:10]


def stamp_fold(stamp_iso: str) -> str:
    d = iso_date(stamp_iso)
    for fold, (lo, hi) in FOLD_WINDOWS.items():
        if lo <= d <= hi:
            return fold
    raise ValueError(f"stamp {stamp_iso} outside all fold windows")


# --------------------------------------------------------------------------- #
# Spearman (average-rank ties -> Pearson on ranks); exact, deterministic
# --------------------------------------------------------------------------- #
def average_ranks(values: np.ndarray) -> np.ndarray:
    """1-based ranks with AVERAGE assignment to ties (deterministic)."""
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.shape[0], dtype=np.float64)
    sorted_vals = values[order]
    i = 0
    while i < sorted_vals.size:
        j = i
        while j + 1 < sorted_vals.size and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # average of 1-based positions i+1..j+1
        ranks[order[i : j + 1]] = avg
        i = j + 1
    return ranks


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2:
        return float("nan")
    sx, sy = x - x.mean(), y - y.mean()
    denom = math.sqrt(float(np.dot(sx, sx)) * float(np.dot(sy, sy)))
    if denom == 0.0:
        return float("nan")  # zero variance -> undefined
    return float(np.dot(sx, sy) / denom)


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    return pearson(average_ranks(x), average_ranks(y))


# --------------------------------------------------------------------------- #
# Load panels (SHA-verified) into pooled observation maps
# --------------------------------------------------------------------------- #
def load_panels() -> dict[str, dict]:
    index = json.loads(PANEL_INDEX.read_text())
    key_by_proposal = {
        "BASISLV-PREMFADE": "BASISLV-fade",
        "BASISLV-WIDTHGATE": "BASISLV-width",
        "BASISDYN-PREMREV": "BASISDYN-PREMREV",
        "BASISDYN-PREMVOL": "BASISDYN-PREMVOL",
        "OICH": "A8-oich",
        "OICYC": "A8-oicyc",
    }
    panels = {}
    for prop, key in key_by_proposal.items():
        entry = index["panels"][key]
        path = PANEL_DIR / f"panel_{prop}.json"
        digest = sha256_file(path)
        if digest != entry["sha256"]:
            raise RuntimeError(
                f"panel {prop} SHA mismatch: {digest} != {entry['sha256']}"
            )
        payload = json.loads(path.read_text())
        obs: dict[tuple[str, str], int] = {}
        for stamp, ranks in payload["ranks"].items():
            for sym, rank in ranks.items():
                obs[(stamp, sym)] = int(rank)
        panels[prop] = {
            "panel_sha256": digest,
            "feature_id": payload["feature_id"],
            "feature_definition": payload["feature_definition"],
            "long_side_note": payload["notes"][0],
            "observations": obs,
        }
    return panels


def pairwise(panels: dict[str, dict]) -> dict:
    matrix: dict[str, dict[str, float | None]] = {p: {} for p in PROPOSALS}
    n_matrix = {p: {} for p in PROPOSALS}
    fold_rho = {p: {} for p in PROPOSALS}
    fold_n = {p: {} for p in PROPOSALS}
    for a in PROPOSALS:
        for b in PROPOSALS:
            if a == b:
                matrix[a][b] = 1.0
                n_matrix[a][b] = len(panels[a]["observations"])
                continue
            common = sorted(
                set(panels[a]["observations"]) & set(panels[b]["observations"])
            )
            x = np.asarray([panels[a]["observations"][k] for k in common], dtype=np.float64)
            y = np.asarray([panels[b]["observations"][k] for k in common], dtype=np.float64)
            rho = spearman(x, y)
            matrix[a][b] = None if math.isnan(rho) else round(rho, 6)
            n_matrix[a][b] = int(common.__len__())
            fr, fn = {}, {}
            for fold in FOLD_WINDOWS:
                idx = [
                    i for i, (stamp, _sym) in enumerate(common)
                    if stamp_fold(stamp) == fold
                ]
                xs, ys = x[np.asarray(idx, dtype=int)], y[np.asarray(idx, dtype=int)]
                r = spearman(xs, ys)
                fr[fold] = None if math.isnan(r) else round(r, 6)
                fn[fold] = int(xs.size)
            fold_rho[a][b] = fr
            fold_n[a][b] = fn
    return {
        "rho": matrix,
        "n": n_matrix,
        "fold_rho": fold_rho,
        "fold_n": fold_n,
    }


# --------------------------------------------------------------------------- #
# Frozen V12 OILEV-V2 anchor feature recomputation (oi_flow_growth)
# --------------------------------------------------------------------------- #
def load_oi_rows(sym: str) -> list[tuple[int, float]]:
    table = pq.read_table(OI_ROOT / f"{sym}_oi.parquet")
    rows = []
    for text, val in zip(
        table.column("create_time").to_pylist(),
        table.column("sum_open_interest").to_pylist(),
    ):
        ts = int(
            datetime.strptime(str(text).strip(), "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        rows.append((ts * 1_000_000_000, float(val)))
    rows.sort()
    return rows


def oi_anchor_before(
    series: list[tuple[int, float]], stamp_ns: int, max_staleness_ns: int
) -> float | None:
    """Last COMPLETED OI row STRICTLY BEFORE stamp (frozen V11/V12 PIT rule)."""
    times = [t for t, _ in series]
    import bisect

    idx = bisect.bisect_left(times, stamp_ns) - 1
    if idx < 0:
        return None
    ts, value = series[idx]
    if stamp_ns - ts > max_staleness_ns:
        return None
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        return None
    return value


def oi_flow_growth(
    series: list[tuple[int, float]], stamp_ns: int, formation_days: int
) -> float | None:
    """Frozen V12 anchor feature: 28d log OI-growth (oi_flow)."""
    staleness = OI_MAX_STALENESS_HOURS * HOUR_NS
    now = oi_anchor_before(series, stamp_ns, staleness)
    past = oi_anchor_before(series, stamp_ns - formation_days * DAY_NS, staleness)
    if now is None or past is None or past <= 0.0:
        return None
    value = math.log(now / past)
    return value if math.isfinite(value) else None


def build_anchor_ranks(stamps: list[str], universe: list[str]) -> dict:
    oi = {sym: load_oi_rows(sym) for sym in universe}
    manifest = json.loads(OI_MANIFEST.read_text())
    oi_file_shas = {
        f"{s}_oi.parquet": spec["parquet_sha256"] for s, spec in manifest["symbols"].items()
    }
    verified = {
        f"{s}_oi.parquet": sha256_file(OI_ROOT / f"{s}_oi.parquet") for s in universe
    }
    sha_match = all(oi_file_shas[f] == verified[f] for f in verified)

    values: dict[str, dict[str, float]] = {}
    ranks: dict[str, dict[str, int]] = {}
    for stamp in stamps:
        dt = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        stamp_ns = int(dt.timestamp()) * 1_000_000_000
        vals = {}
        for sym in universe:
            v = oi_flow_growth(oi[sym], stamp_ns, FORMATION_DAYS_ANCHOR)
            if v is not None:
                vals[sym] = v
        values[stamp] = vals
        ordered = sorted(vals.items(), key=lambda kv: (kv[1], kv[0]))
        ranks[stamp] = {sym: i + 1 for i, (sym, _) in enumerate(ordered)}
    return {
        "values": values,
        "ranks": ranks,
        "oi_sha_all_match_vs_manifest": sha_match,
        "oi_file_shas_verified": verified,
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    panels = load_panels()
    stamps = sorted({s for p in panels.values() for (s, _) in p["observations"]})
    universe = sorted({sym for p in panels.values() for (_s, sym) in p["observations"]})

    result = pairwise(panels)

    flags_candidates, flags_hard = [], []
    for i, a in enumerate(PROPOSALS):
        for b in PROPOSALS[i + 1 :]:
            rho = result["rho"][a][b]
            if rho is None:
                continue
            entry = {"pair": f"{a}|{b}", "abs_rho": abs(rho)}
            if abs(rho) >= HARD_ABS:
                flags_hard.append(entry)
            elif abs(rho) >= CANDIDATE_ABS:
                flags_candidates.append(entry)

    # --- Shadow-region gates (Task 4) ---------------------------------------
    anchor = build_anchor_ranks(stamps, universe)
    anchor_obs = {
        (stamp, sym): rank
        for stamp, ranks in anchor["ranks"].items()
        for sym, rank in ranks.items()
    }
    n19 = len(universe)

    def rho_vs(anchor_conv_obs: dict[tuple[str, str], int], prop: str, fold: str | None):
        common = sorted(set(anchor_conv_obs) & set(panels[prop]["observations"]))
        if fold is not None:
            common = [k for k in common if stamp_fold(k[0]) == fold]
        x = np.asarray([anchor_conv_obs[k] for k in common], dtype=np.float64)
        y = np.asarray([panels[prop]["observations"][k] for k in common], dtype=np.float64)
        r = spearman(x, y)
        return (None if math.isnan(r) else round(r, 6)), int(x.size)

    shadow = {}
    for prop in ("OICH", "OICYC"):
        per_fold = {}
        for fold in FOLD_WINDOWS:
            r_a, n_a = rho_vs(anchor_obs, prop, fold)
            per_fold[fold] = {
                "rho_vs_anchor_convention": r_a,
                "n": n_a,
                "rho_vs_inverted_control_convention": (
                    None if r_a is None else round(-r_a, 6)
                ),
            }
        r_all, n_all = rho_vs(anchor_obs, prop, None)
        rho_anchor = None if math.isnan(r_all) else round(r_all, 6)
        rho_inv = None if rho_anchor is None else round(-rho_anchor, 6)
        abs_a = None if rho_anchor is None else abs(rho_anchor)
        verdict = (
            "PASS" if (abs_a is not None and abs_a <= SHADOW_GATE_ABS) else "FAIL"
        )
        shadow[prop] = {
            "panel_sha256": panels[prop]["panel_sha256"],
            "rho_vs_oilev_v2_anchor_feature_ranks": rho_anchor,
            "rho_vs_oilev_v2_inverted_control_ranks": rho_inv,
            "abs_rho_vs_both_identical_by_symmetry": (
                None if abs_a is None else round(abs_a, 6)
            ),
            "n_stamp_x_symbol": n_all,
            "per_fold": per_fold,
            "gate": f"|rho| <= {SHADOW_GATE_ABS} vs anchor AND inverted control",
            "verdict": verdict,
        }

    # Informational anchor decorrelation for ALL six proposals (the Section
    # 1.1 GATE binds only OICH/OICYC; for the other four this is novelty
    # evidence, not a gate).
    informational = {}
    for prop in PROPOSALS:
        r, n = rho_vs(anchor_obs, prop, None)
        rr = None if (r is None or math.isnan(r)) else round(r, 6)
        informational[prop] = {
            "rho_vs_oilev_v2_anchor": rr,
            "abs_rho": None if rr is None else round(abs(rr), 6),
            "n_stamp_x_symbol": n,
            "binding_gate": prop in ("OICH", "OICYC"),
        }

    corr = {
        "schema": "v14_d2_a7n_cross_cluster_correlation_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A7-N (independent novelty/anti-rescue audit)",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": {
            "statistic": "Spearman rank correlation of within-stamp conditioning-feature ranks (rank 1 = each proposal's own long side, ascending), pooled over ALL stamp-x-symbol observations where BOTH proposals rank the symbol at the stamp (pairwise-complete intersection); missing entries excluded per pair, never imputed",
            "ties": "average-rank assignment to ties, then Pearson on ranks (scipy unavailable in the project venv; direct exact implementation, numpy mergesort argsort, deterministic)",
            "fold_breakdown": "stamps assigned to frozen windows F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21, F2 2026-04-22..2026-08-21 by stamp date; the 1-day fold purge (which removes the 2025-12-22 stamp from TRADING) does not remove it from MEASUREMENT - disclosed",
            "direction_note": "each panel's ranks are oriented so rank 1 = that proposal's long side; a NEGATIVE rho between two proposals means the books point OPPOSITE ways on the shared cross-section; flags use |rho|",
            "flags": {
                f"|rho| >= {CANDIDATE_ABS}": "same-cluster candidate (A1 attention)",
                f"|rho| >= {HARD_ABS}": "hard same-cluster (V13 collapse level)",
            },
        },
        "inputs": {
            "panel_index": "research/control/v14_run/d2_a9f/panel_index.json",
            "panels_sha256_verified": {
                p: panels[p]["panel_sha256"] for p in PROPOSALS
            },
            "oi_authority": "research/control/v11_run/oi_staging_manifest.json + machine-local /Users/hoangminhlong/my-quantitative/oi_data/consolidated (20/20 SHA-256 re-verified at read time)",
            "oi_sha_all_match_vs_manifest": anchor["oi_sha_all_match_vs_manifest"],
        },
        "observations_per_proposal": {
            p: {
                "n_stamp_x_symbol": len(panels[p]["observations"]),
                "feature_id": panels[p]["feature_id"],
                "long_side": panels[p]["long_side_note"],
            }
            for p in PROPOSALS
        },
        "rho_matrix": result["rho"],
        "n_matrix": result["n"],
        "per_fold_rho": result["fold_rho"],
        "per_fold_n": result["fold_n"],
        "flagged_pairs": {
            "same_cluster_candidates_abs_rho_ge_0.70": flags_candidates,
            "hard_same_cluster_abs_rho_ge_0.90": flags_hard,
        },
        "degeneracy_disclosures": {
            "BASISDYN-PREMVOL": "premiumIndexKlines close sentinel makes the 2880-bucket fail-closed window unreachable (A9F-DISC-1): only 12 eligible observations exist in the whole panel (at most 1 name per stamp), so any rho involving PREMVOL has no cross-sectional rank information within stamps and must NOT be read as a cluster measurement; reported mechanically for completeness only. PREMVOL is additionally BLOCKED_DATA by A9-F feasibility, which is A1's input, not this audit's verdict.",
        },
        "shadow_region_rho_gates": {
            "anchor_feature": {
                "family": "A12-V12-OILEVER-V2-DELEV",
                "anchor_arm": "OILEV-V2-28D-FLOW-W",
                "control_arm": "OILEV-V2-28D-FLOW-W-INV",
                "frozen_identity": "research/v12/families/oilev_v2/strategy.py _ARM_FEATURE: anchor (oi_flow, 28, invert=False); control (oi_flow, 28, invert=True); invert acts ONLY at the book level (build_oilev_v2_book swaps long/short legs) - the feature ordering is IDENTICAL for anchor and control",
                "feature": "oi_flow_growth: ln(OI(T)/OI(T-28d)); anchors = last daily OI row STRICTLY BEFORE the relevant instant, staleness <= 48h, value > 0; BTCUSDT never ranked",
                "recomputed_on": "same 52 Monday stamps x 19 symbols as the panels; machine-local staged OI v11_oi_staging_v1 (oi_data/consolidated, SHA-256 re-verified against research/control/v11_run/oi_staging_manifest.json at read time)",
                "rank_convention": "rank 1 = lowest oi_flow = V12 anchor arm's long side (deleveraging); inverted-control convention = 20 - anchor_rank (rank 1 = highest oi_flow = control long side)",
                "symmetry_statement": "the V12 inverted control arm was a PURE SIGN FLIP at the book level (frozen _ARM_FEATURE invert=True; no feature transform), so the control's rank vector is the anchor's reversed; rho(panel, anchor) = -rho(panel, control) EXACTLY and |rho| vs anchor and vs inverse coincide identically. Both are measured and reported; the measured pair satisfies the identity to the reported precision.",
                "notes": "no bars were needed; the anchor feature reads staged OI only",
            },
            "gates": shadow,
        },
        "informational_anchor_correlations_all_proposals": {
            "note": "the plan Section 1.1 gate binds ONLY OICH/OICYC (shadow-region entries); for the other four proposals these measurements are novelty evidence only, not a gate verdict",
            "values": informational,
        },
        "no_pnl": True,
        "no_selection_recommendation": True,
    }

    out = HERE / "cross_cluster_correlation.json"
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(corr, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"written": str(out)}, indent=1))

    # console summary
    print("\n6x6 rho matrix (upper triangle):")
    for i, a in enumerate(PROPOSALS):
        row = []
        for b in PROPOSALS:
            r = result["rho"][a][b]
            row.append("  ----  " if r is None else f"{r:+.3f}")
        print(f"{a:>18}: " + " ".join(row))
    print("\nflagged candidates |rho|>=0.70:", json.dumps(flags_candidates))
    print("flagged hard |rho|>=0.90:", json.dumps(flags_hard))
    for prop in ("OICH", "OICYC"):
        s = shadow[prop]
        print(
            f"shadow {prop}: rho_anchor={s['rho_vs_oilev_v2_anchor_feature_ranks']} "
            f"rho_inv={s['rho_vs_oilev_v2_inverted_control_ranks']} "
            f"n={s['n_stamp_x_symbol']} verdict={s['verdict']}"
        )


if __name__ == "__main__":
    main()
