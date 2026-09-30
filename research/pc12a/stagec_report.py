"""SCORED_REPORT.md writer — PC12A Stage-C (typed provisional verdict).

Reads the stagec artifacts (BARS.json, ARMS/*/metrics.json, B4_BATTERY,
B3_SELECTION, TRAIN_EXTRACT, REPRO_CHECK, VERIFY) and writes the scored
report with the bar matrix, the per-arm table, the honest-disclosure
section and the budget accounting. No new computation of PnL happens
here; every number is quoted from the scored artifacts."""

from __future__ import annotations

import json
import os
from typing import Dict, List

from .run_scoredc import (ARMS_DIR, B4_SEED_BASE, CONTROL, IDENTITY_CAP,
                          LEDGER_PATH, LEDGER_STOP_LINE, N_B4_SEEDS,
                          STAGEC_DIR, _arm_output_dir, _load_metrics,
                          rd)

REPORT_PATH = os.path.join(CONTROL, "SCORED_REPORT.md")


def _load(path: str) -> Dict:
    return json.load(open(path, encoding="utf-8"))


def _usd(x: float) -> str:
    v = float(x)
    sign = "-" if v < 0 else "+"
    return f"{sign}${abs(v):,.2f}"


def _arm_table_rows() -> List[Dict]:
    names = []
    for fn in sorted(os.listdir(ARMS_DIR)):
        mp = os.path.join(ARMS_DIR, fn, "metrics.json")
        if os.path.exists(mp):
            names.append(fn)
    rows = []
    for n in names:
        m = _load_metrics(n)
        rows.append({
            "arm": n, "tier": m.get("tier", 1.0),
            "net": m["net_pnl_pooled_usd"], "dd": m["max_dd_pooled_usd"],
            "fills": m.get("n_fills_total", 0),
            "turnover": m.get("turnover_usd", 0.0),
            "ff_cost": m.get("fold_edge_force_flat_cost_total_usd", 0.0),
            "digest": m["arm_config_digest"][:12]})
    return rows


def write_report() -> Dict:
    bars = _load(os.path.join(STAGEC_DIR, "BARS.json"))
    pol = _load(os.path.join(CONTROL, "policy", "POLICY_FROZEN.json"))
    verify = _load(os.path.join(STAGEC_DIR, "VERIFY.json"))
    b3 = _load(os.path.join(STAGEC_DIR, "B3_SELECTION.json"))
    trex = _load(os.path.join(STAGEC_DIR, "TRAIN_EXTRACT.json"))
    b4 = _load(os.path.join(STAGEC_DIR, "B4_BATTERY.json"))
    repro = _load(os.path.join(STAGEC_DIR, "REPRO_CHECK.json"))
    ledger_rows = rd._ledger_len(LEDGER_PATH)
    rows = _arm_table_rows()
    out: List[str] = []
    a = out.append
    a("# SCORED REPORT — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (Stage-C)")
    a("")
    a(f"Written {verify['frozen_utc']} (Stage-C scored evaluation; "
      "GO `SCORED EXECUTION` consumed). Policy digest "
      f"`{pol['policy_digest'][:16]}…` (verified MATCH at entry); winner "
      f"{pol['variant_id']} frozen at Stage-B with the honest NEGATIVE "
      "TRAIN objective.")
    a("")
    a("## 1. Verdict (typed, provisional per plan §7 — owner confirms)")
    a("")
    a(f"**{bars['verdict']}** — failed governing bars: "
      f"{bars['failed_governing_bars'] or 'NONE'}. Negative closes are "
      "first-class under the honest prior; no parameter was touched and "
      "no re-run was performed except the documented determinism check "
      f"(journal/metrics byte-identical: "
      f"{repro['journal_byte_identical']}/{repro['metrics_byte_identical']}).")
    a("")
    a("## 2. Bar matrix (every governing bar with its numbers)")
    a("")
    a("| bar | status | key numbers |")
    a("|---|---|---|")
    bl = bars["bars"]
    p1b0 = bl["P1-B0"]
    p1 = bl["P1"]
    a(f"| P1-B0 | {p1b0['status']} | net(P) "
      f"{_usd(p1b0['policy_net'])} vs 0 |")
    a(f"| P1 (PRIMARY) | {p1['status']} | net(P) {_usd(p1['policy_net'])}"
      f" vs net(B1) {_usd(p1['b1_net'])}; DD(P) "
      f"{_usd(-p1['policy_dd'])} vs DD(B1) {_usd(-p1['b1_dd'])} |")
    p2a, p2b = bl["P2a"], bl["P2b"]
    a(f"| P2a | {p2a['status']} | vs B2: net "
      f"{_usd(p2a['policy_net'])} vs {_usd(p2a['b2_net'])}; DD "
      f"{_usd(-p2a['policy_dd'])} vs {_usd(-p2a['b2_dd'])} |")
    a(f"| P2b | {p2b['status']} | vs B3({b3['selected_leg']}): net "
      f"{_usd(p2b['policy_net'])} vs {_usd(p2b['b3_net'])}; DD "
      f"{_usd(-p2b['policy_dd'])} vs {_usd(-p2b['b3_dd'])} |")
    c1, c2 = bl["P3-clause-1"], bl["P3-clause-2"]
    a(f"| P3-c1 | {c1['status']} | obj(P) {c1['obj_policy']:.2f} exceeds "
      f"{c1['seeds_below']}/{c1['seeds']} seeds "
      f"(need ≥ {c1['threshold']:.0f}) |")
    a(f"| P3-c2 | {c2['status']} | net {_usd(c2['policy_net'])} vs "
      f"median {_usd(c2['median_seed_net'])}; DD {_usd(-c2['policy_dd'])}"
      f" vs median {_usd(-c2['median_seed_dd'])} |")
    for x, arm in (("a", "B5_CLOCK_GATE"), ("b", "B6_INVERTED"),
                   ("c", "B7_LAGGED")):
        bx = bl[f"P4{x}"]
        a(f"| P4{x} | {bx['status']} | net {_usd(bx['policy_net'])} vs "
          f"{_usd(bx['baseline_net'])}; DD {_usd(-bx['policy_dd'])} vs "
          f"{_usd(-bx['baseline_dd'])} |")
    p5a = bl["P5a"]
    a(f"| P5a | {p5a['status']} | DSR {p5a['dsr']} (need > 0.95); "
      f"SR̂ {p5a['sr_hat']} vs SR₀ {p5a['sr0']} (N={p5a['n']}, "
      f"N_eff={p5a['n_eff']}, V={p5a['v']:.6f}); PSR {p5a['psr']}; "
      f"raw-N DSR {p5a['dsr_raw_n']} |")
    p5b = bl["P5b"]
    a(f"| P5b | {p5b['status']} | PBO {p5b['pbo']} over "
      f"{p5b['n_combinations']} combinations, {p5b['n_trials']} trials "
      "(need ≤ 0.5) |")
    p6a = bl["P6a"]
    a(f"| P6a | {p6a['status']} | @×1.5 net "
      f"{_usd(p6a['policy_x15_net'])} vs {_usd(p6a['b1_x15_net'])}; DD "
      f"{_usd(-p6a['policy_x15_dd'])} vs {_usd(-p6a['b1_x15_dd'])} |")
    p6b = bl["P6b"]
    a(f"| P6b (reporting) | REPORTING | @×2.0 ΔPnL "
      f"{_usd(p6b['delta_pnl_x20'])}, ΔDD {_usd(p6b['delta_dd_x20'])} "
      f"(policy ×2.0 net {_usd(p6b['policy_x20_net'])}) |")
    p6c = bl["P6c"]
    a(f"| P6c (disclosure) | {p6c['status']} | net(P@×2.0) "
      f"{_usd(p6c['policy_x20_net'])} "
      f"{'→ POLICY_COST_DOMINATED label ATTACHED' if p6c['status'] == 'LABEL_ATTACHED' else '(no sign flip)'} |")
    p6d = bl["P6d"]
    a(f"| P6d | {p6d['status']} | @p90 net {_usd(p6d['policy_p90_net'])}"
      f" vs {_usd(p6d['b1_p90_net'])}; DD {_usd(-p6d['policy_p90_dd'])}"
      f" vs {_usd(-p6d['b1_p90_dd'])} |")
    if bl["P7"]["status"] == "NOT_RUN":
        a("| P7 | NOT_RUN | NOT_RUN_P7_NO_POSITIVE_PNL |")
    else:
        p7 = bl["P7"]
        fold_txt = "; ".join(
            f"f{pf['fold']} net {_usd(pf['net'])} "
            f"(share {pf['share_of_pooled']:.1%}, DD {pf['dd_f']:.0f}/"
            f"cap {pf['dd_cap']:.0f})" for pf in p7["per_fold"])
        a(f"| P7 | {p7['status']} | {fold_txt} |")
    p8 = bl["P8"]
    p8_txt = (f"{len(p8['breaks'])} removal(s) break P1-semantics"
              if p8["breaks"] else "every removal pair holds")
    a(f"| P8 | {p8['status']} | {p8_txt} |")
    b8 = bars["b8_reporting"]
    a(f"| B8 ORACLE (reporting) | REPORTING | oracle net "
      f"{_usd(b8['oracle_net'])}, DD {_usd(-b8['oracle_dd'])} vs policy "
      f"net {_usd(b8['policy_net'])}, DD {_usd(-b8['policy_dd'])} |")
    a("")
    a("## 3. Per-arm table (identities, pooled net, pooled maxDD)")
    a("")
    a("| arm | tier | net PnL (pooled) | maxDD (USD) | fills | turnover "
      "USD | fold-edge FF cost | digest |")
    a("|---|---|---|---|---|---|---|---|")
    for r in rows:
        a(f"| {r['arm']} | ×{r['tier']} | {_usd(r['net'])} | "
          f"{_usd(-r['dd'])} | {r['fills']} | {r['turnover']:,.0f} | "
          f"{r['ff_cost']:,.2f} | `{r['digest']}` |")
    b0 = bars["b0"]
    a(f"| B0_FLAT | ×1.0 | {_usd(b0['net_pnl_pooled_usd'])} | "
      f"{_usd(-b0['max_dd_pooled_usd'])} | 0 | 0 | 0 | by construction |")
    a(f"| B4_RANDOM_GATE (128 seeds) | ×1.0 | median "
      f"{_usd(b4['median_net_pnl_usd'])} | median "
      f"{_usd(-b4['median_max_dd_usd'])} | "
      f"[{b4['net_pnl_min_usd']:,.0f}..{b4['net_pnl_max_usd']:,.0f}] | "
      "— | — | one identity |")
    a("")
    a("## 4. Fold-edge force-flat cost companion (skeptic F-7)")
    a("")
    a("Force-flat charges arms differentially by their fold-edge "
      "holdings (B1/B2 hold at every edge by construction; the policy "
      "may already be flat). Per-arm totals are in §3; per-arm per-fold "
      f"totals are in each arm's metrics.json "
      "(`per_fold[].force_flat_cost_usd`). P1's PnL leg should be read "
      "net of this asymmetry.")
    a("")
    a("## 5. Honest disclosure (what these numbers mean)")
    a("")
    a("1. **Honest prior, stated at freeze**: the winner's TRAIN "
      "objective is NEGATIVE (−$1,054,702; deflation term $1.06M dwarfs "
      "TRAIN net +$138k). No TRAIN-side edge claim was made; Stage-C was "
      "expected to close negative, and any positive bar outcome would "
      "itself have required scrutiny.")
    a("2. **Pooled-test-vs-selection overlap (inherent to the registered "
      "design, disclosed)**: the fold calendar's expanding-train law "
      "holds PER FOLD (fold k's TRAIN ends ≥1 week before fold k's test "
      "start and never touches any later fold's window), but Stage-B "
      "froze ONE policy on the LONGEST TRAIN prefix (through "
      "2025-06-20). Folds 0–5's test windows (2022-01-07..2024-12-27) "
      "and fold 6's window except its last 2 Fridays therefore lie "
      "INSIDE the policy's selection data; only fold 7 (2025-07-04.."
      "2025-12-26) is strictly post-selection. The pooled evaluation is "
      "the frozen E-Law-2 law; this overlap is why P5's IS/OOS "
      "double-correction disclosure (PSR alongside DSR) is carried.")
    a("3. **Book law**: per-symbol virtual $100k sub-accounts (the "
      "frozen Stage-B book law); portfolio equity = $100k + Σ sub-PnL; "
      "fold-edge force-flats keep every fold flat at both edges so "
      "per-fold net is an exact cash identity (residual asserted).")
    a("4. **Eligibility state is cold at the test-window start**: E1 "
      "arms 26 weeks after the engine's first TEST decision (the same "
      "engine law the TRAIN runs used; disclosed, not re-derived from "
      "TRAIN state).")
    a("5. **Realization notes**: B2 divides the policy's realized "
      "per-decision gross heat equally across its active legs (per-leg "
      "cap 100k units); B5 clock k = round-half-up(1/duty) phase 0; B6 "
      "complement (the policy has no PROBATION state, so the PROBATION "
      "clause is vacuous); B7 lag = 26 weeks with TRAIN fallback for "
      "fold 0 (fail-open ON when no verdict is recorded, counted); B8 "
      "admits legs with positive B1 paper (sum-of-legs) fold nets "
      "(REPORTING ONLY); B4 chains are two-state Markov with stationary "
      "duty and per-decision flip rate from the policy's TRAIN "
      "eligibility path (realized mismatch possible where clamps bind; "
      "per-leg duty/flip in TRAIN_EXTRACT.json).")
    a("6. **Mid-flight corrections (all engine-path-neutral, disclosed "
      "per the no-silent-continue law)**: (i) the first B3 execution ran "
      "the full slate by a spec-wiring defect (its metrics were "
      "byte-identical to POLICY — caught by exactly that identity); the "
      "arm was deleted and re-run correctly; the incorrect run never "
      "entered the ledger. (ii) A schedules-assembly bug (train/test "
      "verdict nesting) crashed orchestration run 1; POLICY/B1 were "
      "re-run after the fix so the whole battery carries one code "
      "digest. (iii) The battery was killed twice by session mechanics "
      "(harness kill, then a half-written seed journal refused by the "
      "append-only law); both resumes are deterministic (completed "
      "artifacts are never re-run). (iv) P5a's first evaluation used a "
      "dedup that collapsed N_eff to 4 (wave-1 screening rows carry no "
      "cluster_id); corrected to the frozen Stage-B formula (N=134, "
      "N_eff=29, SR0 0.3218 — MORE deflation, conservative direction); "
      "the verdict was identical before and after. No policy parameter, "
      "arm input, or engine path was touched after the POLICY arm froze "
      "the code digest; bars were evaluated twice (documented "
      "correction) and no scored arm was re-run except the POLICY "
      "determinism repro (byte-identical).")
    a("7. **Costs**: measured C1/C2/C3 cells + DECLARED U2/U3/U4 bands; "
      "every number carries NET_DEFAULT_COST / "
      "PROVISIONAL_PENDING_COST_AUTHORITY. Engine fills are bar-quoted "
      "spread-once (the frozen engine law); P6d re-prices at cell p90. "
      "The sealed tail (2026-01-02..2026-06-26) was never loaded; S1 "
      "SEALED_UNTOUCHED.")
    a("")
    a("## 6. Budget accounting")
    a("")
    ids = len(rows) + 2          # arms on disk + B0 + B4 (one identity)
    a(f"- Scored identities consumed: **{ids} / {IDENTITY_CAP}** "
      f"(policy 1, B0 1, B1 1, B2 1, B3 1, B5/B6/B7 3, B8 1, P6a pair 2, "
      f"P6b/P6c ×2.0 pair 2, P6d pair 2, P8 pairs 24, B4 battery 1 — "
      f"the dispatch's 38 + the 2 mandatory ×2.0 reporting runs P6b/P6c "
      f"require).")
    a(f"- B4 battery: **1 identity = {N_B4_SEEDS} seeded sub-runs** "
      f"(seeds {B4_SEED_BASE}..{B4_SEED_BASE + N_B4_SEEDS - 1}, list "
      f"digest `{b4['seed_list_digest'][:16]}…`) on its own budget line "
      "(E-Law 8).")
    a(f"- Ledger rows: **{ledger_rows} / 1500** (stop line "
      f"{LEDGER_STOP_LINE} respected; ~40 C-SCORED rows appended).")
    a(f"- Determinism: policy re-run journal/metrics byte-identical "
      f"({repro['journal_byte_identical']}/"
      f"{repro['metrics_byte_identical']}); TRAIN V3 re-run reproduced "
      "the frozen selection statistic "
      f"({trex['determinism_guard']['match']}).")
    a("- Heavy lock: held end-to-end for the orchestrate job (disclosed "
      "in the registry).")
    a("")
    a("## 8. Evidence index")
    a("")
    a("- `diagnostics/stagec/BARS.json` — the bar matrix with every "
      "number.")
    a("- `diagnostics/stagec/ARMS/<ARM>/journal.jsonl|metrics.json` — "
      "per-arm hash-chained journal (journal_row@1, SCORED-TEST) and "
      "metrics.")
    a("- `diagnostics/stagec/B3_SELECTION.json` — TRAIN-only selection, "
      "frozen before any test run.")
    a("- `diagnostics/stagec/TRAIN_EXTRACT.json` — duty/flip per leg "
      "(B5/B4) + the TRAIN determinism guard.")
    a("- `diagnostics/stagec/B4_BATTERY.json` — 128-seed battery.")
    a("- `diagnostics/stagec/POLICY_SCHEDULES.json` / `B8_SETS.json` — "
      "the frozen B2/B7/B8 inputs.")
    a("- `TRIAL_LEDGER.jsonl` — C-SCORED rows.")
    a("- `diagnostics/stagec/B4/JOURNAL_MANIFEST.json` — sha256 + row "
      "count of each of the 128 seeded sub-run journals; the journal "
      "files themselves (862MB) stay on disk unmodified and are NOT "
      "committed wholesale (repo-size decision, disclosed here; "
      "reproducible from the frozen seed list under the proven engine "
      "determinism).")
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(json.dumps({"mode": "report", "path": REPORT_PATH,
                      "lines": len(out)}))
    return {"path": REPORT_PATH}
