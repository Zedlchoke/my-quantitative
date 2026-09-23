"""Phase-rule goldens on synthetic paths (hand-computed / independent
reference), UNKNOWN assignment, warmup exclusion, no-lookahead mutation,
boundary law, and date-independence (XNYS/DST note)."""

from datetime import date, timedelta

from psv1_spy.phase_rule import (
    ACCUMULATION,
    DISTRIBUTION,
    DOWNTREND,
    RuleParams,
    UNKNOWN,
    UPTREND,
    compute_labels,
    label_from_observables,
)

P = RuleParams()  # frozen defaults: SMA200, slope 20, bands 1% / 0.5%


# ---------------------------------------------------------------- boundary law
def test_quadrant_boundary_law_hand_table():
    # r, s, expected — exact frozen semantics (>= on band edges for named
    # phases; UNKNOWN is the complement of the four quadrant conditions)
    table = [
        (0.02, 0.02, UPTREND),
        (0.02, -0.02, DISTRIBUTION),
        (-0.02, 0.02, ACCUMULATION),
        (-0.02, -0.02, DOWNTREND),
        (0.005, 0.02, UNKNOWN),   # |r| < band
        (0.02, 0.004, UNKNOWN),   # |s| < band
        (-0.005, -0.02, UNKNOWN),
        (0.02, -0.004, UNKNOWN),
        (0.01, 0.005, UPTREND),   # exact band edge belongs to the quadrant
        (-0.01, -0.005, DOWNTREND),
        (0.0, 0.0, UNKNOWN),
        (0.009999, 0.02, UNKNOWN),
    ]
    for r, s, expected in table:
        assert label_from_observables(r, s, P.p_band, P.s_band) == expected, (r, s)


# ------------------------------------------------------------ synthetic paths
def flat_then(step_from, n_flat=220, n_after=80):
    return [100.0] * n_flat + [step_from] * n_after


def closes_uptrend():
    # 220 flats at 100, then 80 bars at 120.
    # Hand check t=239: SMA = (180*100 + 20*120)/200 = 102; r = 120/102-1 =
    # +17.6%; SMA at t-20 (=219) = 100; s = +2%  => UPTREND.
    return flat_then(120.0)


def closes_downtrend():
    # mirror: t=239 SMA = 98.0? precisely (196*100+4*80)/200 at t=223 ...
    # at t=239: SMA = (180*100+20*80)/200 = 98; r = 80/98-1 = -18.4%;
    # s = (98-100)/100 = -2% => DOWNTREND.
    return flat_then(80.0)


def closes_distribution():
    # high plateau 130 (bars 0..99), washout 105 (bars 100..199), recovery
    # to 118 (bars 200..299). Hand check t=299:
    # SMA299 = mean(closes[100..299]) = (100*105 + 100*118)/200 = 111.5;
    # price 118 => r = 118/111.5-1 = +5.83% >= +1%.
    # SMA279 = mean(closes[80..279]) = (20*130 + 100*105 + 80*118)/200
    #        = 22540/200 = 112.7;
    # s = (111.5-112.7)/112.7 = -1.06% <= -0.5% => DISTRIBUTION.
    return [130.0] * 100 + [105.0] * 100 + [118.0] * 100


def closes_accumulation():
    # trough 60 (bars 0..59), peak 100 (bars 60..159), glide down to 74
    # (bars 160..259). Hand check t=259:
    # SMA259 = mean(closes[60..259]) = (100*100 + 86.87*100)/200 = 93.435;
    # price 74 => r = 74/93.435-1 = -20.8% <= -1%.
    # Slope: SMA259 - SMA239 = [sum(closes[240..259]) - sum(closes[40..59])]
    # / 200 = (1529.4 - 1200)/200 = +1.647 (the exiting block is the TROUGH
    # at bars 40..59, so the slope turns UP while price is still far below
    # the peak-carrying SMA); SMA239 = 91.788 =>
    # s = +1.795% >= +0.5% => ACCUMULATION.
    out = [60.0] * 60
    out += [100.0] * 100
    out += [100.0 - 0.26 * k for k in range(1, 101)]  # bars 160..259
    return out


def _sma_reference(closes, n, t):
    window = closes[t - n + 1 : t + 1]
    return sum(window) / n


def _independent_label_at(closes, t):
    """Independent reference (direct O(n) means, no package code)."""
    sma = _sma_reference(closes, P.sma_n, t)
    base = _sma_reference(closes, P.sma_n, t - P.slope_k)
    r = closes[t] / sma - 1.0
    s = (sma - base) / base
    return label_from_observables(r, s, P.p_band, P.s_band)


def test_quadrant_goldens_at_hand_checkpoints():
    cases = [
        (closes_uptrend(), 239, UPTREND),
        (closes_downtrend(), 239, DOWNTREND),
        (closes_distribution(), 299, DISTRIBUTION),
        (closes_accumulation(), 259, ACCUMULATION),
    ]
    for closes, t, expected in cases:
        labels = compute_labels(closes, P)
        assert labels[t] == expected, (expected, t)
        assert labels[t] == _independent_label_at(closes, t)


def test_constant_path_is_unknown_everywhere():
    labels = compute_labels([100.0] * 300, P)
    assert set(labels) == {UNKNOWN}


def test_insufficient_evidence_unknown_bands():
    closes = closes_uptrend()
    labels = compute_labels(closes, P)
    # t=219: price 100 vs SMA 100 => r=0 => UNKNOWN (margin band)
    assert labels[219] == UNKNOWN
    # t=223: SMA=(196*100+4*120)/200=100.4, s=+0.4% < +0.5% => UNKNOWN
    assert labels[223] == UNKNOWN
    # slope needs 20 post-step bars; by t=239 it is built => UPTREND
    assert labels[239] == UPTREND


def test_warmup_exclusion():
    closes = closes_uptrend()
    assert len(closes) == 300
    labels = compute_labels(closes, P)
    assert all(lab == UNKNOWN for lab in labels[: P.warmup])
    # a series shorter than the warmup can never produce a quadrant label
    short = compute_labels(closes[:219], P)
    assert set(short) == {UNKNOWN}


def test_no_lookahead_mutation():
    for closes in (
        closes_uptrend(),
        closes_downtrend(),
        closes_distribution(),
        closes_accumulation(),
    ):
        base = compute_labels(closes, P)
        for cut in (220, 240, 259, len(closes) - 1):
            mutated = list(closes)
            mutated[cut] = mutated[cut] * 3.0 + 50.0
            after = compute_labels(mutated, P)
            assert after[:cut] == base[:cut], (cut,)
        # perturbing strictly-future bars (beyond t) never changes label t
        t = 230
        mutated = list(closes)
        for j in range(t + 1, len(closes)):
            mutated[j] = 7.0
        assert compute_labels(mutated, P)[: t + 1] == base[: t + 1]


def _weekdays(start: date, n: int):
    out = []
    d = start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def test_labels_independent_of_dates_and_dst():
    # The rule consumes the ordered close series only; date relabels (which is
    # what a DST-boundary or stamp-convention change amounts to for date-only
    # bytes) must leave the full pipeline output identical.
    from psv1_spy.gates import rotate_dates, run_pipeline

    closes = closes_uptrend() + closes_distribution()
    folds = [("F1", "ERA-X", P.warmup, len(closes) - 1)]
    d1 = _weekdays(date(2024, 1, 1), len(closes))  # crosses US DST 2024-03-10
    base = run_pipeline(closes, d1, folds)
    for k in range(1, 5):
        rotated = run_pipeline(closes, rotate_dates(d1, k), folds)
        assert rotated["labels"] == base["labels"]
        assert rotated["per_fold_occupancy"] == base["per_fold_occupancy"]
        assert (
            rotated["transition_matrix_post_warmup"]
            == base["transition_matrix_post_warmup"]
        )
