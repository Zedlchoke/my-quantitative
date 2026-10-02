#!/usr/bin/env python
"""Census + complementarity analysis over the COMMITTED PC12A Stage-C journals.

Read-only over research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS/.
Writes census.json + complementarity.json next to this script.

Provenance law: every number here is either
  [M]      read directly from a committed journal/metrics row, or
  [derived] arithmetic on those rows under the conventions stated in the code.
No engine run, no re-scoring. The 8 test folds (2022-01-07..2025-12-26) are
EXPOSED; everything below is hypothesis-generating only.
"""
import json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = os.path.abspath(os.path.join(
    HERE, '..', '..', 'PORTFOLIO-COMPOSITE-12ASSETS-100K-V1',
    'diagnostics', 'stagec', 'ARMS'))

PRIMARY = ['POLICY', 'B1_ALWAYS_ON']


def load_journal(arm):
    rows = []
    with open(os.path.join(ARMS, arm, 'journal.jsonl')) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def load_metrics(arm):
    with open(os.path.join(ARMS, arm, 'metrics.json')) as f:
        return json.load(f)


def week_key(ts):
    # ts 'YYYY-MM-DDTHH:MM:SSZ' -> ISO week bucket (Friday-mark convention is
    # approximated by calendar ISO week; used only for co-loss bucketing)
    d = ts[:10]
    y, m, dd = int(d[:4]), int(d[5:7]), int(d[8:10])
    import datetime
    dt = datetime.date(y, m, dd)
    mon = dt - datetime.timedelta(days=dt.weekday())
    return mon.isoformat()


def main():
    out = {}

    # ---------- 1. CENSUS ----------
    census = {'arms': {}, 'notes': []}
    all_arms = sorted(os.listdir(ARMS))
    for arm in all_arms:
        jp = os.path.join(ARMS, arm, 'journal.jsonl')
        if not os.path.exists(jp):
            continue
        kinds = defaultdict(int)
        legs = set()
        hdr = None
        with open(jp) as f:
            for line in f:
                r = json.loads(line)
                if r.get('row_kind') == 'HEADER':
                    hdr = r['meta']
                    continue
                kinds[r['row_kind']] += 1
                if r.get('leg_id'):
                    legs.add(r['leg_id'])
        m = load_metrics(arm) if os.path.exists(os.path.join(ARMS, arm, 'metrics.json')) else {}
        census['arms'][arm] = {
            'row_counts': dict(kinds),
            'n_legs_meta': len(hdr['legs']) if hdr else None,
            'tier': hdr.get('tier') if hdr else None,
            'legs': sorted(legs),
            'metrics_net_pooled_usd': m.get('net_pnl_pooled_usd'),
            'metrics_max_dd_pooled_usd': m.get('max_dd_pooled_usd'),
            'metrics_n_decisions_total': m.get('n_decisions_total'),
            'metrics_n_fills_total': m.get('n_fills_total'),
        }

    # dedup classification of arms by role
    roles = {
        'primary_scored': ['POLICY', 'B1_ALWAYS_ON'],
        'tier_repricing_same_decisions': ['POLICY_P90', 'POLICY_X15', 'POLICY_X20',
                                          'B1_P90', 'B1_X15', 'B1_X20'],
        'portfolio_controls': ['B2_EQUAL_WEIGHT', 'B3_BEST_SINGLE', 'B5_CLOCK_GATE',
                               'B6_INVERTED', 'B7_LAGGED', 'B8_ORACLE'],
        'solo_paper_books': [a for a in all_arms if '_MO_' in a],
    }
    census['arm_roles'] = roles
    census['dedup_law'] = (
        'Only POLICY + B1_ALWAYS_ON are portfolio-realized scored books at tier x1.0. '
        'Tier arms re-price the same corpus under different cost multipliers: the B1 '
        'family emits byte-identical decision counts (3,467), while the POLICY family '
        'varies slightly (3,124/3,126/3,114/3,110 for P/X1.0/P90/X15/X20) because the '
        'L6 cost guard defers cost-dependently — measured difference, disclosed; no '
        'tier arm adds a NEW market decision stream. Solo (_MO_) arms are single-leg '
        'paper books with no netting interactions. Portfolio trades are therefore '
        'counted ONCE from the POLICY/B1 pair; nothing is summed across arms or tiers.')

    # per-leg decision/blocked inventory for the two primaries
    for arm in PRIMARY:
        per_leg = defaultdict(lambda: defaultdict(int))
        with open(os.path.join(ARMS, arm, 'journal.jsonl')) as f:
            for line in f:
                r = json.loads(line)
                k = r.get('row_kind')
                if k in ('HEADER', 'SWAP'):
                    continue
                lid = r.get('leg_id')
                if k == 'DECISION':
                    per_leg[lid]['decisions'] += 1
                    if r.get('direction_vote', 0) != 0:
                        per_leg[lid]['decisions_nonzero_vote'] += 1
                elif k == 'BLOCK':
                    per_leg[lid]['blocked'] += 1
                    per_leg[lid]['block_' + str(r.get('eligibility_rule_id'))] += 1
                elif k == 'DEFER':
                    per_leg[lid]['deferred'] += 1
                elif k == 'NETTED_TO_ZERO':
                    per_leg[lid]['netted_zero'] += 1
                elif k == 'NET_ORDER':
                    per_leg[lid]['fills'] += 1
        census.setdefault('per_leg_inventory', {})[arm] = {k: dict(v) for k, v in sorted(per_leg.items(), key=lambda x: str(x[0]))}

    # fill matching POLICY <-> B1 by (symbol, ts)
    fills = {arm: defaultdict(list) for arm in PRIMARY}
    for arm in PRIMARY:
        with open(os.path.join(ARMS, arm, 'journal.jsonl')) as f:
            for line in f:
                r = json.loads(line)
                if r.get('row_kind') != 'NET_ORDER':
                    continue
                key = (r['symbol'], r['ts_fill_utc'])
                fills[arm][key].append(r.get('delta_units'))
    p_keys, b_keys = set(fills['POLICY']), set(fills['B1_ALWAYS_ON'])
    shared = p_keys & b_keys
    p_only, b_only = p_keys - b_keys, b_keys - p_keys
    same_size = sum(1 for k in shared if fills['POLICY'][k] == fills['B1_ALWAYS_ON'][k])
    census['fill_matching'] = {
        'definition': 'unique (symbol, ts_fill_utc) NET_ORDER timestamps; a shared ts is ONE market trade, possibly sized differently',
        'POLICY_unique_fill_ts': len(p_keys),
        'B1_unique_fill_ts': len(b_keys),
        'shared_ts': len(shared),
        'shared_same_size': same_size,
        'shared_sized_differently': len(shared) - same_size,
        'POLICY_only_ts': len(p_only),
        'B1_only_ts': len(b_only),
        'union_unique_market_fills': len(p_keys | b_keys),
    }

    # unique decision points across arms
    dec = {arm: set() for arm in PRIMARY}
    for arm in PRIMARY:
        with open(os.path.join(ARMS, arm, 'journal.jsonl')) as f:
            for line in f:
                r = json.loads(line)
                if r.get('row_kind') == 'DECISION':
                    dec[arm].add((r['leg_id'], r['ts_decision_utc']))
    census['decision_dedup'] = {
        'POLICY_decision_points': len(dec['POLICY']),
        'B1_decision_points': len(dec['B1_ALWAYS_ON']),
        'union_decision_points': len(dec['POLICY'] | dec['B1_ALWAYS_ON']),
        'intersection': len(dec['POLICY'] & dec['B1_ALWAYS_ON']),
        'note': 'decision streams are leg-level engine inputs; the union is the corpus-unique decision count for the window',
    }
    out['census'] = census

    # ---------- 2. COMPLEMENTARITY ----------
    comp = {}
    weekly = {}
    for arm in PRIMARY:
        per_sym_week = defaultdict(lambda: defaultdict(float))
        with open(os.path.join(ARMS, arm, 'journal.jsonl')) as f:
            for line in f:
                r = json.loads(line)
                k = r.get('row_kind')
                if k == 'NET_ORDER':
                    wk = week_key(r['ts_fill_utc'])
                    per_sym_week[r['symbol']][wk] += r.get('cash_delta_usd', 0.0)
                elif k == 'SWAP':
                    wk = week_key(r['ts_utc'])
                    per_sym_week[r['symbol']][wk] -= r.get('swap_usd', 0.0)
        weekly[arm] = {s: dict(w) for s, w in per_sym_week.items()}
    comp['weekly_cash_net_by_symbol'] = {
        arm: {s: {wk: round(v, 2) for wk, v in sorted(w.items())}
              for s, w in weekly[arm].items()} for arm in PRIMARY}
    comp['weekly_convention'] = (
        'cash-basis weekly nets per symbol (fills cash_delta - swap debits), '
        'ISO-Monday buckets. Realized-cash convention; MTM drawdowns differ '
        '(see dossier friday_equity reconstructions). USDJPY amounts are '
        'par-convention journal units (at-par JPY quote-CCY, DP §13).')

    # co-loss / co-drawdown on B1 always-on path (the reference)
    def coloss(arm, thresh):
        syms = sorted(weekly[arm])
        allw = sorted({w for s in syms for w in weekly[arm][s]})
        both_loss = 0
        jpy_dd_weeks = 0
        detail = []
        for w in allw:
            nets = {s: weekly[arm][s].get(w, 0.0) for s in syms}
            losers = [s for s, v in nets.items() if v < -thresh]
            if len(losers) >= 2:
                both_loss += 1
                detail.append((w, {s: round(nets[s]) for s in losers}))
        return {'week_threshold_usd': thresh, 'weeks_total': len(allw),
                'weeks_2plus_symbols_lose': both_loss, 'examples': detail[:12]}
    comp['co_loss_B1'] = coloss('B1_ALWAYS_ON', 1000)
    comp['co_loss_POLICY'] = coloss('POLICY', 1000)

    # correlations of weekly nets (B1)
    def corr(a, b):
        keys = sorted(set(a) & set(b))
        if len(keys) < 8:
            return None, len(keys)
        xa = [a[k] for k in keys]
        xb = [b[k] for k in keys]
        n = len(keys)
        ma, mb = sum(xa) / n, sum(xb) / n
        cov = sum((x - ma) * (y - mb) for x, y in zip(xa, xb))
        va = sum((x - ma) ** 2 for x in xa) ** .5
        vb = sum((y - mb) ** 2 for y in xb) ** .5
        return (cov / (va * vb) if va * vb else 0.0), n
    syms = sorted(weekly['B1_ALWAYS_ON'])
    comp['weekly_corr_B1'] = {}
    for i, s1 in enumerate(syms):
        for s2 in syms[i + 1:]:
            c, n = corr(weekly['B1_ALWAYS_ON'][s1], weekly['B1_ALWAYS_ON'][s2])
            comp['weekly_corr_B1'][f'{s1}|{s2}'] = {'pearson': round(c, 4) if c is not None else None, 'n_weeks': n}

    # per-symbol net contribution (metrics per_symbol_fold_records)
    contrib = {}
    for arm in PRIMARY:
        m = load_metrics(arm)
        recs = m['per_symbol_fold_records']
        agg = defaultdict(float)
        for sym, folds in recs.items():
            for fid, fr in folds.items():
                agg[sym] += fr.get('net_pnl_usd', fr.get('net', 0.0))
        contrib[arm] = {s: round(v, 2) for s, v in agg.items()}
    comp['per_symbol_net_contribution'] = contrib

    # exposure overlap from heat_events_by_symbol (position time series; only
    # POLICY metrics carry it — B1 metrics have an empty dict, disclosed)
    for arm in PRIMARY:
        m = load_metrics(arm)
        heat = m.get('heat_events_by_symbol', {})
        exp = {}
        for sym, ev in heat.items():
            total = nonzero = 0
            for i in range(1, len(ev)):
                dt = ev[i][0] - ev[i - 1][0]
                total += dt
                if ev[i - 1][1] != 0:
                    nonzero += dt
            exp[sym] = {'pct_time_in_position': round(100.0 * nonzero / total, 2) if total else None,
                        'events_n': len(ev)}
        comp[f'exposure_{arm}'] = exp
        # pairwise joint in-position time (only computable where heat exists)
        if heat:
            joints = {}
            syms_h = sorted(heat)
            def intervals(ev):
                out = []
                for i in range(1, len(ev)):
                    if ev[i - 1][1] != 0:
                        out.append((ev[i - 1][0], ev[i][0]))
                return out
            iv = {s: intervals(heat[s]) for s in syms_h}
            for i, s1 in enumerate(syms_h):
                for s2 in syms_h[i + 1:]:
                    a, b = iv[s1], iv[s2]
                    tot1 = sum(en - st for st, en in a)
                    j = 0
                    ib = 0
                    for st, en in a:
                        while ib < len(b) and b[ib][1] <= st:
                            ib += 1
                        jb = ib
                        while jb < len(b) and b[jb][0] < en:
                            j += min(en, b[jb][1]) - max(st, b[jb][0])
                            jb += 1
                    w_start = min(ev[0][0] for ev in heat.values())
                    w_end = max(ev[-1][0] for ev in heat.values())
                    span = w_end - w_start
                    joints[f'{s1}|{s2}'] = {
                        'joint_in_position_pct_of_window': round(100.0 * j / span, 2) if span else None,
                        'joint_as_pct_of_s1_inposition': round(100.0 * j / tot1, 2) if tot1 else None}
            comp[f'exposure_joint_{arm}'] = joints
    comp['exposure_source_note'] = (
        'heat_events_by_symbol is present in POLICY metrics only; the key is '
        'ABSENT from B1_ALWAYS_ON metrics.json (measured absence — this script '
        'reads it via .get default). B1 exposure is therefore [NR] from '
        'metrics; POLICY exposure proxies shared-market exposure structure. '
        'Joint EURUSD+USDJPY in-position time = 22.92% of the window '
        '(marginals 36.92/57.84; union 71.8%) — computed from POLICY heat '
        'events; do NOT state the pair holds together "a majority" of the time.')

    # direction mix per symbol per arm (fills)
    for arm in PRIMARY:
        dm = defaultdict(lambda: [0, 0])  # symbol -> [long_delta_fills, short]
        with open(os.path.join(ARMS, arm, 'journal.jsonl')) as f:
            for line in f:
                r = json.loads(line)
                if r.get('row_kind') != 'NET_ORDER':
                    continue
                if r.get('delta_units', 0) > 0:
                    dm[r['symbol']][0] += 1
                elif r.get('delta_units', 0) < 0:
                    dm[r['symbol']][1] += 1
        comp[f'direction_fill_mix_{arm}'] = {s: {'buy_fills': v[0], 'sell_fills': v[1]} for s, v in dm.items()}

    # solo paper books (already in census metrics; summarize for complementarity)
    solo = {}
    for arm in all_arms:
        if '_MO_' not in arm:
            continue
        m = load_metrics(arm)
        solo[arm] = {'net': m.get('net_pnl_pooled_usd'), 'maxDD': m.get('max_dd_pooled_usd'),
                     'sr_weekly': m.get('sr_hat_weekly'), 'n_fills': m.get('n_fills_total')}
    comp['solo_paper_books'] = solo
    comp['solo_caveat'] = (
        'Solo arms are single-leg paper books: no netting, no caps, no portfolio '
        'interactions. They bound per-leg standalone economics and CANNOT be '
        'summed (double-counts the market) nor subtracted from portfolio nets '
        '(netting paths differ). B1_MO_* vs POLICY_MO_* differ only where the '
        'E1/L6 eligibility layers bit (S009, S017, S002, S023, VC2 x2).')

    out['complementarity'] = comp

    with open(os.path.join(HERE, 'census.json'), 'w') as f:
        json.dump(out['census'], f, indent=1)
    with open(os.path.join(HERE, 'complementarity.json'), 'w') as f:
        json.dump(out['complementarity'], f, indent=1)
    print('written census.json + complementarity.json')
    # headline prints
    print(json.dumps(census['fill_matching'], indent=1))
    print(json.dumps(census['decision_dedup'], indent=1))
    print('co-loss B1:', json.dumps(comp['co_loss_B1'], default=str)[:600])
    print('corr B1:', json.dumps(comp['weekly_corr_B1'], indent=1))
    print('contrib:', json.dumps(comp['per_symbol_net_contribution'], indent=1))
    print('exposure B1:', json.dumps(comp['exposure_B1_ALWAYS_ON'], indent=1))


if __name__ == '__main__':
    main()
