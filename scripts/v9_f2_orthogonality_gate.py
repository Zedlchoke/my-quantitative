"""F2 RESMR vs rejected weekly-reversal orthogonality gate (frozen before scoring).

Frozen rule (A1, pre-launch): over all Monday cutoffs in the dry-run window
[2025-01-06, 2025-08-18] using ONLY PIT data, compute per-stamp Spearman rank
correlation between (a) RESMR residual z-scores and (b) weekly-reversal raw
7d-return scores. Gate PASS iff mean absolute correlation <= 0.50.
Fail => F2 archived NOT_RUN_RESCUE_OF_REJECTED_FAMILY without consuming budget.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.v9_residual_mr import residual_z_scores

CATALOG = "/Users/hoangminhlong/my-quantitative/catalog_live_crypto"
SYMBOLS = ["ETHUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ENAUSDT","SUIUSDT",
           "1000PEPEUSDT","ADAUSDT","BNBUSDT","LINKUSDT"]

def main():
    from research.portfolio_runner import load_engine
    call = load_engine()
    panel = call["build_daily_panel"](
        symbols=[*SYMBOLS, "BTCUSDT"],
        window_start_ns=int(datetime(2024,10,1,tzinfo=timezone.utc).timestamp()*1e9),
        window_end_ns=int(datetime(2025,8,21,tzinfo=timezone.utc).timestamp()*1e9),
    ) or {}
    closes = panel.get("daily_closes") or {}
    bench = panel.get("benchmark_daily_closes") or []
    if isinstance(bench, dict):
        bench = bench.get("BTCUSDT") or []
    def monday_cutoffs(start="2025-01-06", end="2025-08-19"):
        from datetime import timedelta
        d = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        enddt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
        while d <= enddt:
            yield int(d.timestamp()*1e9); d += timedelta(days=7)

    def rev_scores(cutoff):
        # weekly reversal raw score: trailing 7d return (higher=more winner)
        out = {}
        for s in SYMBOLS:
            pts = [(t,v) for t,v in (closes.get(s) or []) if t < cutoff]
            if len(pts) < 8: continue
            p0 = [v for t,v in pts if t >= cutoff - 7*86400*10**9]
            out[s] = (p0[-1]/p0[0]-1.0) if p0 else None
        return out

    import statistics
    rhos = []
    for cut in monday_cutoffs():
        zs = residual_z_scores(daily_closes=closes, benchmark_closes=bench,
                               signal_cutoff_ns=cut, traded_symbols=SYMBOLS)
        rs = rev_scores(cut)
        common = sorted(set(zs)&set(rs))
        if len(common) < 6: continue
        zr = {s: zs[s]["z"] for s in common}
        pairs = [(zr[s], rs[s]) for s in common
                 if zr[s] is not None and rs[s] is not None]
        if len(pairs) < 6:
            continue
        za = [p[0] for p in pairs]; ra = [p[1] for p in pairs]
        def rank(a):
            order = sorted(range(len(a)), key=lambda i: a[i])
            r=[0.0]*len(a)
            for pos,i in enumerate(order): r[i]=pos
            return r
        rz, rr = rank(za), rank(ra)
        mz, mr = sum(rz)/len(rz), sum(rr)/len(rr)
        cov = sum((a-mz)*(b-mr) for a,b in zip(rz,rr))
        vz = (sum((a-mz)**2 for a in rz))**.5; vr=(sum((b-mr)**2 for b in rr))**.5
        if vz and vr: rhos.append(cov/(vz*vr))
    mean_abs = sum(abs(r) for r in rhos)/len(rhos) if rhos else 1.0
    verdict = "PASS_DISTINCT" if mean_abs <= 0.50 and len(rhos)>=20 else "FAIL_RESCUE_ARCHIVE"
    doc = {"artifact":"v9_f2_orthogonality_gate","rule":"mean|spearman(resmr_z, wrev_7d_ret_rank)|<=0.50 over >=20 Monday stamps in dry-run 2025-01-06..2025-08-18, PIT-only",
           "stamps_evaluated": len(rhos), "mean_abs_spearman": round(mean_abs,4),
           "max_abs": round(max((abs(r) for r in rhos), default=0),4),
           "verdict": verdict}
    Path("research/audits/v9p").mkdir(parents=True, exist_ok=True)
    Path("research/audits/v9p/f2_orthogonality_gate.json").write_text(json.dumps(doc, indent=2)+"\n")
    print(json.dumps(doc))

if __name__ == "__main__":
    main()
