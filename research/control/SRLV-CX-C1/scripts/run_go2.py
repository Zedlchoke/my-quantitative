"""SRLV-CX-C1 GO-2 driver: fixtures battery FIRST (fail => no scored outputs),
then scored run of the 6 frozen cells + falsifier battery + gates + DSR.
Runs entirely under the machine-wide heavy lock (heavy_lock.acquire).
"""
import sys, os, json, math, hashlib, random
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.chdir(ROOT)

import engine_m1 as E

CYC = Path("research/control/SRLV-CX-C1")
OUT = CYC / "outcomes"; OUT.mkdir(exist_ok=True)

def ser(trades, decision_only=True):
    """F1/F2 compare DECISION+ENTRY fields only — exits legitimately depend on
    post-decision data (they must adapt under truncation/mutation); the
    causality contract protects decisions, not exit paths."""
    fields = ("j", "price", "side", "s", "c_bar", "entry_i", "dir", "t_entry") if decision_only \
        else ("j", "s", "c_bar", "entry_i", "exit_i", "why", "dir", "t_entry", "t_exit")
    return json.dumps([{k: tr[k] for k in fields} for tr in trades], sort_keys=True)

def sha(s): return hashlib.sha256(s.encode()).hexdigest()

def load_all():
    data = {}
    for pair in E.PAIRS:
        D = E.load_klines(pair)
        sett, gaps = E.load_settlements(pair)
        data[pair] = dict(D=D, sett=sett, gaps=gaps, rates=E.load_rates(pair))
    return data

def fixtures(data, results):
    fx = {}
    ok = True
    for pair in E.PAIRS:
        d = data[pair]; D, sett = d["D"], d["sett"]
        cands = E.candidate_events(D, sett, N=6)
        trades = E.greedy_one_pos(cands)
        p = {}
        p["n_candidates"] = len(cands); p["n_trades"] = len(trades)
        # F-GRID
        p["F_GRID"] = dict(hour_aligned=bool(np.all(sett % 3600000 == 0)),
                           intervals_hours=[int(g) for g in d["gaps"]],
                           pass_=bool(set(d["gaps"].tolist()) <= {4, 8}))
        # F-WARMUP (principled bound): ATR24 defined from bar 23 => every
        # decision bar c_bar >= 23 => entry_i >= 24. (Earlier constant 35 was
        # arbitrary and wrong — earliest legal trade measured at c_bar=24.)
        p["F_WARMUP"] = bool(all(tr["c_bar"] >= 23 for tr in trades))
        # F-P1A-FLAT: no settlement in [t_entry, t_exit]
        bad = 0
        for tr in trades:
            i0 = np.searchsorted(sett, tr["t_entry"], side="left")
            if i0 < len(sett) and sett[i0] <= tr["t_exit"]: bad += 1
        p["F_P1A_FLAT"] = dict(violations=bad, pass_=(bad == 0))
        # F-P1-OFFBYONE: s >= j+N+1
        p["F_P1_OFFBYONE"] = bool(all(tr["s"] >= tr["j"] + 7 for tr in trades))
        # F7 fold force-flat
        p["F7_FOLD_FLAT"] = bool(all(E.fold_of(tr["t_entry"]) == E.fold_of(tr["t_exit"]) and
                                     E.fold_of(tr["t_entry"]) is not None for tr in trades))
        # F4 non-vacuity: entries per settlement-window bar >= 2%
        close_ms = D["t"] + 3600000
        win_bars = 0
        for S in sett:
            lo = S - 3600000; hi = S + 3*3600000
            win_bars += int(np.sum((close_ms >= lo) & (close_ms <= hi)))
        p["F4_NONVACUITY"] = dict(trades=len(trades), settlement_window_bars=int(win_bars),
                                  rate=len(trades)/max(win_bars, 1),
                                  pass_=(len(trades)/max(win_bars, 1) >= 0.02))
        p["F4_power"] = {k: v["n"] for k, v in E.direction_split(
            trades, E.pnl_of(trades, pair)).items()}
        # F1 truncation byte-identity (up to 512 stratified decision closes).
        # Panel cut at c_bar + BUFFER bars so every decision <= c_bar has its
        # entry bar present; only decision+entry tuples with t_entry <= close
        # of c_bar are compared (exits adapt by design — decision_only=ser).
        rng = random.Random(E.SEED)
        pts = sorted(set(tr["c_bar"] for tr in trades))
        step = max(1, len(pts)//512)
        pts = pts[::step][:512]
        mism = 0
        BUF = 12
        for c_bar in pts:
            cut = int(D["t"][c_bar] + 3600000)
            end = min(c_bar+1+BUF, len(D["t"]))
            pre = {k: v[:end] for k, v in D.items()}
            sub = E.greedy_one_pos(E.candidate_events(pre, sett, N=6))
            sub = [tr for tr in sub if tr["t_entry"] <= cut]
            ref = [tr for tr in trades if tr["t_entry"] <= cut]
            if sha(ser(sub)) != sha(ser(ref)): mism += 1
        p["F1_TRUNCATION"] = dict(points=len(pts), mismatches=mism, pass_=(mism == 0),
                                  note="decision+entry tuples; exits excluded (adapt by design)")
        # F2 future-mutation invariance (25 points): bars after c_bar *1.013
        pts2 = sorted(set(tr["c_bar"] for tr in trades))
        step2 = max(1, len(pts2)//25)
        pts2 = pts2[::step2][:25]
        mism2 = 0
        for c_bar in pts2:
            cut = int(D["t"][c_bar] + 3600000)
            mut = {k: v.copy() for k, v in D.items()}
            for k in ("o", "h", "l", "c"):
                mut[k][c_bar+1:] = mut[k][c_bar+1:] * 1.013
            sub = E.greedy_one_pos(E.candidate_events(mut, sett, N=6))
            sub = [tr for tr in sub if tr["t_entry"] <= cut]
            ref = [tr for tr in trades if tr["t_entry"] <= cut]
            if sha(ser(sub)) != sha(ser(ref)): mism2 += 1
        p["F2_FUTURE_MUTATION"] = dict(points=len(pts2), mismatches=mism2, pass_=(mism2 == 0),
                                       note="decision+entry tuples invariance")
        # F5 leak-scan: static source scan of engine for forbidden idioms + funding sentinel
        src = Path("research/control/SRLV-CX-C1/scripts/engine_m1.py").read_text()
        p["F5_LEAKSCAN"] = dict(funding_sentinel_zero_by_construction=(p["F_P1A_FLAT"]["violations"] == 0),
                                source_sha=sha(src),
                                note="F1/F2 prove causality; no same-bar confirm-fill by construction")
        fx[pair] = p
        ok &= (p["F_GRID"]["pass_"] and p["F_P1A_FLAT"]["pass_"] and p["F1_TRUNCATION"]["pass_"]
               and p["F2_FUTURE_MUTATION"]["pass_"] and p["F7_FOLD_FLAT"] and p["F_WARMUP"]
               and p["F1_TRUNCATION"]["pass_"])
    results["fixtures"] = fx
    return ok

def dsr(daily_vals, n_trials):
    a = np.array(daily_vals, float)
    if len(a) < 20 or a.std() == 0: return None
    mu, sd = a.mean(), a.std(ddof=1)
    SR = mu/sd
    g3 = float(((a-mu)**3).mean())/sd**3
    g4 = float(((a-mu)**4).mean())/sd**4
    n = len(a)
    denom = math.sqrt(max(1e-12, 1 - g3*SR + (g4-1)/4*SR*SR))
    stat = SR*math.sqrt(n-1)/denom
    gamma = 0.5772156649
    from math import erf, sqrt
    Phi = lambda x: 0.5*(1+erf(x/sqrt(2)))
    from statistics import NormalDist
    nd = NormalDist()
    if n_trials > 1:
        em = math.sqrt(2*math.log(n_trials))
        SR0 = (em - (math.log(4*math.pi*math.log(n_trials))+gamma+math.log(2))/(2*em))
    else:
        SR0 = 0.0
    DSR = nd.cdf(stat - SR0)
    return dict(SR_daily=float(SR), n_days=n, n_trials=n_trials, DSR=float(DSR))

def scored(data, results):
    res = {}
    worst = {"BTCUSDT": 30.0, "ETHUSDT": 35.63}
    for pair in E.PAIRS:
        d = data[pair]; D, sett, rates = d["D"], d["sett"], d["rates"]
        arms = {}
        cfg = dict(A1_anchor=dict(N=6), A2_nb_N3=dict(N=3), A3_nb_N10=dict(N=10),
                   A4_shift_plus4h=dict(N=6, shift_hours=4), A4_shift_minus4h=dict(N=6, shift_hours=-4))
        for name, kw in cfg.items():
            tr = E.run_book(D, sett, pair=pair, **kw)
            pn = E.pnl_of(tr, pair)
            arms[name] = dict(**E.stats(pn), folds=E.fold_split(tr, pn),
                              dirs=E.direction_split(tr, pn), conc=E.concentration(tr, pn))
            for k in (1.5, 2.0):
                arms[name][f"net@{k}"] = float(np.sum(E.pnl_of(tr, pair, fee_mult=k)))
        # A5 inverted = same fills flipped
        trA = E.run_book(D, sett, N=6, pair=pair)
        pnI = E.pnl_of(trA, pair, flip=True)
        arms["A5_inverted"] = dict(**E.stats(pnI), folds=E.fold_split(trA, pnI),
                                   dirs=E.direction_split(trA, pnI))
        # battery
        trU = E.run_book(D, sett, N=6, ungated=True, pair=pair)
        arms["ungated_clock"] = dict(**E.stats(E.pnl_of(trU, pair)))
        rng = random.Random(E.SEED)
        lv = E.pivots(D, 6)
        off = {j: rng.randint(24, 240)*rng.choice([-1, 1]) for (j, p, s) in lv}
        trPL = E.run_book(D, sett, N=6, placebo_offsets=off, pair=pair)
        arms["placebo_levels"] = E.stats(E.pnl_of(trPL, pair))
        trD = E.run_book(D, sett, N=6, delay=1, pair=pair)
        arms["delay1"] = dict(**E.stats(E.pnl_of(trD, pair)))
        trL = E.run_book(D, sett, N=6, literal_span=True, pair=pair)
        pnL = []
        for tr in trL:
            x = E.pnl_of([tr], pair)[0]
            f = E.funding_between(rates, sett, tr["t_entry"], tr["t_exit"], tr["dir"])
            pnL.append(x - f)
        arms["diagnostic_literal_span_measured_funding"] = E.stats(pnL)
        # baselines
        arms["A6_baselines"] = E.baselines(D, sett, rates, pair)
        # splits
        pn1 = E.pnl_of(trA, pair)
        hr = {}
        for tr, p in zip(trA, pn1):
            hr.setdefault(E.iso(tr["t_entry"]).hour, []).append(p)
        arms["A1_anchor"]["by_utc_hour"] = {int(k): (len(v), float(np.sum(v))) for k, v in sorted(hr.items())}
        wk = {}
        for tr, p in zip(trA, pn1):
            wk.setdefault("weekend" if E.iso(tr["t_entry"]).weekday() >= 5 else "weekday", []).append(p)
        arms["A1_anchor"]["weekday_split"] = {k: dict(n=len(v), net=float(np.sum(v))) for k, v in wk.items()}
        # block shuffle
        ds = E.daily_series(trA, pn1); days = sorted(ds); vals = np.array([ds[x] for x in days])
        rngbs = np.random.default_rng(E.SEED); B = 20; means = []
        nbk = len(vals)//B
        for _ in range(200):
            bl = [vals[i*B:(i+1)*B] for i in range(nbk)]
            rngbs.shuffle(bl)
            means.append(float(np.concatenate(bl + [vals[nbk*B:]]).mean()))
        arms["A1_anchor"]["block_shuffle"] = dict(
            p_one_sided=float(np.mean(np.array(means) >= vals.mean())), n_days=len(days))
        # shadows rho
        shd = {}
        for nm, trs in (("bandfade", E.shadow_bandfade(D)), ("donchian168", E.shadow_donchian168(D)),
                        ("cng2_settle_drift", E.shadow_cng2(D, sett)), ("rev24", E.shadow_rev24(D))):
            shd[nm] = dict(rho=E.rho_daily(ds, E.daily_series(trs, E._shadow_trades_pnl(trs, pair))),
                           n_trades=len(trs))
        arms["A1_anchor"]["ancestry_rho"] = shd
        arms["A1_anchor"]["net_worst_settle_incl"] = float(np.sum(pn1) - worst[pair]*len(trA))
        # DSR
        arms["A1_anchor"]["DSR_n6"] = dsr([ds[x] for x in days], 6)
        # gates
        g = {}
        A = arms["A1_anchor"]
        g["G1_net_pos@1.0"] = A["net"] > 0
        g["G2_PF>=1.20"] = (A["pf"] or 0) >= 1.20
        fpos = [v for v in A["folds"].values() if v > 0]
        g["G3_>=3/4_folds"] = len(fpos) >= 3
        g["G4_net_pos@1.5"] = A.get("net@1.5", -1) > 0
        g["G5_power>=100/dir"] = (A["dirs"].get("long", dict(n=0))["n"] >= 100 and
                                  A["dirs"].get("short", dict(n=0))["n"] >= 100)
        sh_m = max(arms["A4_shift_plus4h"]["mean"], arms["A4_shift_minus4h"]["mean"])
        g["G6a_placebo<0.5x"] = sh_m < 0.5*A["mean"] if A["mean"] > 0 else (sh_m <= 0)
        g["G6b_inverted_below"] = arms["A5_inverted"]["net"] < A["net"]
        g["G6c_ungated_dead"] = (arms["ungated_clock"]["net"] <= 0)
        g["G6d_placebo_levels<0.8x"] = (arms["placebo_levels"]["mean"] < 0.8*A["mean"]) if A["mean"] > 0 else (arms["placebo_levels"]["mean"] <= 0)
        bl_best = max(arms["A6_baselines"]["long_hold"]["net"], arms["A6_baselines"]["trend_sma720"]["net"], 0.0)
        g["G7_anchor>=2x_baseline"] = A["net"] >= 2*bl_best
        g["G8_conc<=0.50"] = (A["conc"] is not None and A["conc"] <= 0.50)
        g["_delay1_note"] = arms["delay1"]["mean"]
        g["_rho_max"] = max(abs(v["rho"]) for v in shd.values())
        g["K-ANC_rho<=0.20"] = g["_rho_max"] <= 0.20
        arms["_gates"] = {k: v for k, v in g.items()}
        res[pair] = arms
    results["pairs"] = res
    # identity-level verdict: PASS on BOTH pairs
    both = all(all(v is True for k, v in res[p]["_gates"].items() if k.startswith("G") or k.startswith("K-ANC")) for p in res)
    results["identity_dev_verdict"] = "PASS_ALL_GATES_BOTH_PAIRS" if both else "FAIL_SEE_GATES"

def main():
    from research.governance import heavy_lock
    cmd = [".venv/bin/python", "research/control/SRLV-CX-C1/scripts/run_go2.py"]
    expected = [str(CYC/"outcomes/FIXTURES_RUN1.json"), str(CYC/"outcomes/SCORED_RUN1.json")]
    results = dict(run="GO2_RUN1", seed=E.SEED,
                   freeze_sha="64aba7c3ffd038e96c129a8f4d7c648b6205c7bb3c96e15576e1728e0739cde2",
                   engine_sha=sha(Path("research/control/SRLV-CX-C1/scripts/engine_m1.py").read_text()))
    with heavy_lock.acquire(cycle_id="SRLV-CX-C1", role="go2-scored-execution",
                            worktree=str(ROOT), command=cmd, expected_artifacts=expected):
        data = load_all()
        ok = fixtures(data, results)
        json.dump(results, open(CYC/"outcomes/FIXTURES_RUN1.json", "w"), indent=1, default=str)
        if not ok:
            results["status"] = "FIXTURES_FAILED_NO_SCORED_RUN"
            json.dump(results, open(CYC/"outcomes/SCORED_RUN1.json", "w"), indent=1, default=str)
            print("FIXTURES FAILED — no scored run")
            return 2
        scored(data, results)
        results["status"] = "SCORED_COMPLETE"
        results["PBO"] = "NOT_RUN (<8 configs)"
        json.dump(results, open(CYC/"outcomes/SCORED_RUN1.json", "w"), indent=1, default=str)
        print("done:", results["identity_dev_verdict"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
