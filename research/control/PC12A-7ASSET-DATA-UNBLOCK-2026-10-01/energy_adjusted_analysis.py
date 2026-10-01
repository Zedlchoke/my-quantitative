#!/usr/bin/env python
"""Regenerate ENERGY_ADJUSTED_ANALYSIS.json from landed raw bytes (skeptic
finding 5: the artifact previously had no generating script on file).
Inputs: d6_full_adjusted_last.json, eia_v2_*_daily.json, PC12A CONTFUT TRADES.
Note (finding 8): the adjusted pull is CLOSE-ONLY -> the flat metric is
consecutive-equal-closes, NOT O=H=L=C flat bars; labeled accordingly."""
import json, shutil, statistics as st, math
from pathlib import Path
RAW=Path.home()/".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw"
IBKR=Path.home()/".my-quantitative-data/portfolio-composite-12assets-100k-v1/ibkr_acq_20260930"
CTL=Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001/research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01")
W=("2020-10-01","2026-09-30")
def pctl(xs,q):
    xs=sorted(xs)
    if not xs: return None
    k=(len(xs)-1)*q; f,c=math.floor(k),math.ceil(k)
    return xs[f] if f==c else xs[f]+(xs[c]-xs[f])*(k-f)
adj={k:{r["date"]:r["close"] for r in v["rows"]} for k,v in json.load(open(RAW/"ibkr_ro_20261001/d6_full_adjusted_last.json")).items() if isinstance(v,dict) and "rows" in v}
eia={k:{r["period"]:float(r["value"]) for r in json.loads((RAW/f).read_text())["rows"] if r.get("value") is not None}
     for k,f in [("WTI","eia_v2_RWTC_daily.json"),("NATGAS","eia_v2_RNGWHHD_daily.json"),("BRENT","eia_v2_RBRTE_daily.json")]}
trd={}
for a,f in [("WTI","WTI_CONTFUT_TRADES_1d_6Y.json"),("NATGAS","NATGAS_CONTFUT_TRADES_1d_6Y.json"),("BRENT","BRENT_CONTFUT_TRADES_1d_6Y.json")]:
    trd[a]={r["date"][:10]:r["close"] for r in json.loads((IBKR/f).read_text())}
out={"schema":"pc12a_energy_adjusted_analysis@1","window":W,
     "caveat":"adjusted channel pull is CLOSE-ONLY; flat metric below = consecutive-equal-closes (O=H=L=C flatness NOT MEASURABLE from this pull)",
     "assets":{}}
for a in ["BRENT","WTI","NATGAS"]:
    A=adj[a]; S={d:v for d,v in eia[a].items() if W[0]<=d<=W[1]}; T={d:v for d,v in trd[a].items() if W[0]<=d<=W[1]}
    ca=sorted(d for d in A.keys()&S.keys() if W[0]<=d<=W[1]); ba=[A[d]-S[d] for d in ca]
    pairs=list(zip(ca,ca[1:]))
    ag=sum(1 for x,y in pairs if (A[y]-A[x])*(S[y]-S[x])>0)
    nz=[(x,y) for x,y in pairs if A[y]-A[x]!=0 and S[y]-S[x]!=0]
    agn=sum(1 for x,y in nz if (A[y]-A[x])*(S[y]-S[x])>0)
    ct=sorted(d for d in A.keys()&T.keys() if W[0]<=d<=W[1]); dv=[(d,A[d]-T[d]) for d in ct]
    out["assets"][a]={"adj_n":len(A),"adj_first":min(A),"adj_last":max(A),
      "adj_vs_eia_spot":{"n":len(ca),"signed_mean_usd":round(st.mean(ba),4),
        "abs_p50_usd":round(pctl([abs(x) for x in ba],.5),4),
        "abs_p95_usd":round(pctl([abs(x) for x in ba],.95),4),
        "sign_agree_all":round(ag/len(pairs),4),
        "sign_agree_nonzero":round(agn/len(nz),4) if nz else None},
      "adj_vs_trades":{"n":len(ct),
        "first_divergence_date":next((d for d,v in dv if abs(v)>1e-9),None),
        "last_equal_date":next((d for d,v in reversed(dv) if abs(v)<1e-9),None),
        "max_abs_div_usd":round(max(abs(v) for d,v in dv),4),
        "note":"divergence is dollar-scale for oil ($1.73/$1.11 max) and cents for gas; a genuine back-adjusted roll chain would diverge by tens of dollars over 2020-2026 - this channel is NOT that"},
      "consecutive_equal_closes_pct":round(100*sum(1 for x,y in pairs if A[y]==A[x])/len(pairs),2)}
res=RAW.parent/"ENERGY_ADJUSTED_ANALYSIS.json"; res.write_text(json.dumps(out,indent=1))
shutil.copy(res,CTL/"ENERGY_ADJUSTED_ANALYSIS.json")
print("regenerated; divergences:",{a:out["assets"][a]["adj_vs_trades"]["max_abs_div_usd"] for a in out["assets"]})
