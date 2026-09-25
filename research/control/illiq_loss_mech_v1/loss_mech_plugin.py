"""ILLIQ-LOSS-MECH-V1 phase-1 plugin variants (cycle worktree; engine untouched).

Subclasses the frozen ``IlliqAmihudPlugin`` (engine ``c97283e0``) and implements
exactly the three variant arms frozen in plans/PLAN_illiq_loss_mech_v1.md
§9 Amendment A1:

* ``BASELINE``  — engine-native book on the base-universe law (A1-2: full
  staged 20-SYMS list, per-stamp engine eligibility; benchmark context =
  listed-at-window-start so the buy-and-hold context can never abort on a
  not-yet-listed symbol — the CHR3F Y2022 abort mode).
* ``V2_AGE``    — A1-4: age filter at pool level before the engine's frozen
  quintile/hedge math; listing-age measured from the injected bars' first
  close stamp (data-derived, PIT: a symbol's first bar precedes any stamp at
  which it can be ranked; censoring at catalog start only affects symbols
  that are >365d old at every stamp of these folds — disclosed).
* ``V2_HEDGE``  — A1-5: engine book (BTC theta tilt unchanged), then the
  majors theta tilt (EW top-10 by trailing 30d median daily DV; 90d OLS
  spread-beta, min 60 paired obs; SPREAD_FALLBACK on theta>=1, missing obs,
  sign flip, cap breach, or |book BTC beta| > 0.05 after both tilts).

Fold law: thirds of THIS plugin's window (engine force-flat at each fold's
last stamp except the terminal one), mirroring the CHR3F lane precedent.
Windows: Y2022 = stamps 2022-01-03..2022-12-26; Y2023 = 2023-01-02..2023-12-25
(engine-native weekly Monday 00Z schedule; window_start set to the preceding
Monday so the first stamp matches the frozen fold definition).

Nothing here scores or mutates the frozen tree; artifacts only.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation, FoldSpec, StressSpec
from research.v11.families.illiq_amihud.plugin import IlliqAmihudPlugin
from research.v11.families.illiq_amihud.strategy import (
    CAP,
    STATUS_OK,
    build_quintile_book,
    compute_stamp_features,
    daily_blocks,
)

VARIANTS = ("BASELINE", "V2_AGE", "V2_HEDGE")
AGE_FLOOR_DAYS = 365.0          # A1-4 frozen
MAJORS_TOP_N = 10               # A1-5 frozen
MAJORS_LIQUIDITY_DAYS = 30      # A1-5 frozen (engine size proxy window)
SPREAD_BETA_WINDOW_DAYS = 90    # A1-5 frozen
SPREAD_BETA_MIN_OBS = 60        # A1-5 frozen (BETA_MIN_OBS)
MAX_BOOK_BTC_BETA_POST = 0.05   # A1-5 frozen fallback bound
DAY_NS = 86_400_000_000_000


def _thirds(stamps: Sequence[int]) -> List[Any]:
    n = len(stamps)
    k = (n + 2) // 3
    return [(stamps[0:k], stamps[k:2 * k], stamps[2 * k:])]


class LossMechPlugin(IlliqAmihudPlugin):
    """Cycle-local variant plugin; frozen engine math reused, never forked."""

    def __init__(self, *, variant: str = "BASELINE", **kw: Any) -> None:
        super().__init__(**kw)
        if variant not in VARIANTS:
            raise ContractViolation(f"unknown variant {variant!r}; frozen: {VARIANTS}")
        self._variant = variant
        stamps = list(self.schedule().instants)
        a, b, c = _thirds(stamps)[0]
        self._fold_members = {"F0": tuple(a), "F1": tuple(b), "F2": tuple(c)}
        first_bar: Dict[str, int] = {}
        for sym, bars in self._bars.items():
            if bars:
                first_bar[sym] = min(int(bar.ts_event_ns) for bar in bars)
        self._first_bar_ns = first_bar

    # ---------------- fold law: thirds of this window ----------------
    def _fold_label(self, stamp_ns: int) -> Optional[str]:
        for label, members in sorted(self._fold_members.items()):
            if stamp_ns in members:
                return label
        return None

    def fold_instants(self) -> Dict[str, tuple]:
        return dict(self._fold_members)

    def folds(self, *, stress: StressSpec, instants: Sequence[int]) -> tuple:
        buckets: Dict[str, List[int]] = {}
        for stamp in sorted(int(v) for v in instants):
            label = self._fold_label(stamp)
            if label is None:
                raise ContractViolation(f"stamp {stamp} outside every fold")
            buckets.setdefault(label, []).append(stamp)
        out = []
        for index, label in enumerate(sorted(self._fold_members)):
            members = tuple(buckets.get(label, ()))
            if not members:
                raise ContractViolation(f"fold {label} has no decision stamps")
            dropped = (stress.dropped_fold_index is not None
                       and index == int(stress.dropped_fold_index))
            out.append(FoldSpec(index=index, label=label, instants=members,
                                purge_days=0, dropped=dropped))
        return tuple(out)

    # ---------------- A4 universe law (Amendment A2) ----------------
    def universe(self, stress: StressSpec) -> tuple:
        # A4 (engine-native; INC-1/A2): universe = listed at window start.
        # The frozen runner requires first-instant context marks for every
        # universe member, so mid-window listings can never be admitted.
        ym = self._window_start_iso[:7]
        return tuple(s for s in super().universe(stress)
                     if self._first_bar_ns.get(s, 1 << 62) <= _month_start_ns(ym))

    # ---------------- context: listed at window start ----------------
    def benchmark_context_symbols(self) -> tuple:
        ym = self._window_start_iso[:7]
        listed = [s for s in self.tradeable_universe()
                  if self._first_bar_ns.get(s, 1 << 62) <= _month_start_ns(ym)]
        return tuple(sorted(set(listed) | {self._benchmark}))

    # ---------------- targets ----------------
    def targets_at(self, instant_ns: int, *, universe: Sequence[str],
                   stress: StressSpec) -> Dict[str, Any]:
        fold = self._fold_label(int(instant_ns))
        if fold is None:
            raise ContractViolation(f"stamp {instant_ns} outside every fold")
        members = self._fold_members[fold]
        if int(instant_ns) == int(members[-1]) and int(instant_ns) != int(
                self.schedule().instants[-1]):
            return {"status": STATUS_OK, "weights": {},
                    "reason_code": "FOLD_BOUNDARY_FORCE_FLAT",
                    "diagnostics": {"fold": fold, "force_flat": True}}

        stamp = compute_stamp_features(
            bars_by_symbol=self._bars,
            universe=universe,
            benchmark_symbol=self._benchmark,
            decision_ns=int(instant_ns),
            formation_days=int(self._arm["formation_days"]),
        )
        diag: Dict[str, Any] = dict(stamp.diagnostics)
        diag["variant"] = self._variant
        arm_sign = int(self._arm["sign"])

        if self._variant == "BASELINE":
            book = build_quintile_book(features=stamp.features,
                                       betas=stamp.betas, arm_sign=arm_sign)
            return self._finish(book, diag)

        if self._variant == "V2_AGE":
            # census-only baseline book (young-in-short-leg verification)
            full_book = build_quintile_book(features=stamp.features,
                                            betas=stamp.betas, arm_sign=arm_sign)
            young = sorted(s for s in stamp.features
                           if (int(instant_ns) - self._first_bar_ns.get(s, 0))
                           < AGE_FLOOR_DAYS * DAY_NS)
            old_feats = {s: f for s, f in stamp.features.items() if s not in set(young)}
            old_betas = {s: b for s, b in stamp.betas.items() if s not in set(young)}
            book = build_quintile_book(features=old_feats, betas=old_betas,
                                       arm_sign=arm_sign)
            diag.update({
                "n_eligible_full": len(stamp.features),
                "n_eligible_age_filtered": len(old_feats),
                "young_excluded": young,
                "young_in_full_short_leg": sorted(
                    set(young) & set((full_book.get("diagnostics") or {}).get("short_leg", [])
                                     if full_book.get("status") == STATUS_OK else [])),
            })
            return self._finish(book, diag)

        # V2_HEDGE
        book = build_quintile_book(features=stamp.features, betas=stamp.betas,
                                   arm_sign=arm_sign)
        if book.get("status") != STATUS_OK:
            return self._finish(book, diag)
        hedged = self._majors_tilt(book=book, stamp=stamp, instant_ns=int(instant_ns),
                                   arm_sign=arm_sign)
        diag.update(hedged["diagnostics"])
        return self._finish(hedged["book"], diag)

    # ---------------- helpers ----------------
    @staticmethod
    def _finish(book: Dict[str, Any], diag: Dict[str, Any]) -> Dict[str, Any]:
        out_diag = dict(book.get("diagnostics") or {})
        out_diag.update(diag)
        return {"status": str(book["status"]),
                "weights": dict(book.get("weights") or {}),
                "reason_code": book.get("reason_code"),
                "diagnostics": out_diag}

    def _majors_tilt(self, *, book: Dict[str, Any],
                     stamp: Any, instant_ns: int, arm_sign: int) -> Dict[str, Any]:
        weights0: Dict[str, float] = dict(book["weights"])
        legs = sorted(weights0)
        q = len(legs) // 2
        fallback = {"spread_fallback": True, "theta_maj": None, "b0_maj": None,
                    "book_btc_beta_post_double_tilt": None, "majors_index": []}
        fail = lambda extra: {"book": dict(book, diagnostics={}),
                              "diagnostics": {**fallback, **extra}}  # noqa: E731

        eligible = sorted(stamp.features)
        medians: Dict[str, float] = {}
        for sym in eligible:
            blocks = daily_blocks(self._bars.get(sym) or (),
                                  decision_ns=instant_ns,
                                  n_days=MAJORS_LIQUIDITY_DAYS)
            dvs = [float(b["quote_volume"]) for b in blocks.values()
                   if float(b["quote_volume"]) > 0.0]
            if len(dvs) >= MAJORS_LIQUIDITY_DAYS // 2:
                medians[sym] = sorted(dvs)[len(dvs) // 2]
        if len(medians) < MAJORS_TOP_N:
            return fail({"spread_fallback_reason": "MAJORS_INDEX_TOO_SMALL"})
        majors = sorted(medians, key=lambda s: (-medians[s], s))[:MAJORS_TOP_N]

        idx_returns: Dict[int, float] = {}
        per_day: Dict[int, List[float]] = {d: [] for d in range(1, SPREAD_BETA_WINDOW_DAYS + 1)}
        for sym in majors:
            blocks = daily_blocks(self._bars.get(sym) or (),
                                  decision_ns=instant_ns,
                                  n_days=SPREAD_BETA_WINDOW_DAYS)
            for d in range(1, SPREAD_BETA_WINDOW_DAYS + 1):
                blk = blocks.get(d)
                if blk is None:
                    continue
                o, c = float(blk["open"]), float(blk["close"])
                if min(o, c) > 0.0:
                    per_day[d].append(c / o - 1.0)
        for d, vals in per_day.items():
            if vals:
                idx_returns[d] = math.fsum(vals) / len(vals)

        beta_maj: Dict[str, float] = {}
        for sym in legs:
            blocks = daily_blocks(self._bars.get(sym) or (),
                                  decision_ns=instant_ns,
                                  n_days=SPREAD_BETA_WINDOW_DAYS)
            xs: List[float] = []
            ys: List[float] = []
            for d in range(1, SPREAD_BETA_WINDOW_DAYS + 1):
                blk = blocks.get(d)
                ri = idx_returns.get(d)
                if blk is None or ri is None:
                    continue
                o, c = float(blk["open"]), float(blk["close"])
                if min(o, c) <= 0.0:
                    continue
                xs.append(c / o - 1.0)
                ys.append(ri)
            if len(xs) < SPREAD_BETA_MIN_OBS:
                return fail({"spread_fallback_reason": f"BETA_OBS_SHORT:{sym}:{len(xs)}"})
            mx, my = math.fsum(xs) / len(xs), math.fsum(ys) / len(ys)
            cov = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
            var_x = math.fsum((x - mx) ** 2 for x in xs)
            if var_x <= 0.0:
                return fail({"spread_fallback_reason": f"BETA_DEGENERATE:{sym}"})
            beta_maj[sym] = cov / var_x

        b0_maj = math.fsum(beta_maj[s] * weights0[s] for s in legs)
        by_beta = sorted(legs, key=lambda s: (beta_maj[s], s))
        n_legs = len(legs)
        top = by_beta[n_legs // 2:]
        bottom = by_beta[: n_legs // 2]
        spread = (math.fsum(beta_maj[s] for s in top) / len(top)
                  - math.fsum(beta_maj[s] for s in bottom) / len(bottom))
        if spread <= 1e-12:
            if abs(b0_maj) <= 1e-9:
                return {"book": book,
                        "diagnostics": {"spread_fallback": False, "theta_maj": 0.0,
                                        "b0_maj": b0_maj, "majors_index": majors,
                                        "book_btc_beta_post_double_tilt":
                                            float(book["diagnostics"]["book_beta_post_hedge"])}}
            return fail({"spread_fallback_reason": "SPREAD_DEGENERATE"})
        theta = abs(b0_maj) / spread
        if theta >= 1.0:
            return fail({"spread_fallback_reason": "THETA_MAJ_GE_1", "theta_maj": theta})
        tilt_sign = -1.0 if b0_maj > 0.0 else 1.0
        w1 = {s: weights0[s] + (tilt_sign * theta / q if s in set(top)
                                else -tilt_sign * theta / q) for s in legs}
        for s in legs:
            if w1[s] * weights0[s] <= 0.0:
                return fail({"spread_fallback_reason": f"SIGN_FLIP:{s}", "theta_maj": theta})
        gross = math.fsum(abs(v) for v in w1.values())
        if gross <= 0.0:
            return fail({"spread_fallback_reason": "DEGENERATE"})
        signed = {s: w1[s] / gross * arm_sign for s in legs}
        breaches = sorted(s for s, w in signed.items() if abs(w) > CAP + 1e-9)
        if breaches:
            return fail({"spread_fallback_reason": f"CAP_BREACH:{breaches}",
                         "theta_maj": theta})
        btc_beta = math.fsum(float(stamp.betas[s]) * signed[s] for s in legs)
        if abs(btc_beta) > MAX_BOOK_BTC_BETA_POST:
            return fail({"spread_fallback_reason": f"BTC_BETA_POST:{btc_beta:.4f}",
                         "theta_maj": theta})
        out_book = {"status": STATUS_OK, "weights": signed, "reason_code": None,
                    "diagnostics": {"n_eligible": len(eligible), "quintile_size": q,
                                    "long_leg": list(book["diagnostics"]["long_leg"]),
                                    "short_leg": list(book["diagnostics"]["short_leg"]),
                                    "net_exposure": math.fsum(signed.values()),
                                    "book_beta_post_hedge": btc_beta,
                                    "book_beta_pre_hedge":
                                        book["diagnostics"]["book_beta_pre_hedge"]}}
        return {"book": out_book,
                "diagnostics": {"spread_fallback": False, "theta_maj": theta,
                                "b0_maj": b0_maj, "majors_index": majors,
                                "book_btc_beta_post_double_tilt": btc_beta}}


def _month_start_ns(ym: str) -> int:
    import datetime as _dt
    y, m = int(ym[:4]), int(ym[5:7])
    dt = _dt.datetime(y, m, 1, tzinfo=_dt.timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)

