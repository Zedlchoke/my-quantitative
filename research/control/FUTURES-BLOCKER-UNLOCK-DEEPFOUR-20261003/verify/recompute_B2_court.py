#!/usr/bin/env python3
"""VERIFY-lane independent recompute of B2 court-draft arithmetic:
b4 6B round-trip = close-proxy + slippage + commission (5.8-10.4 bp);
c3 MDE = 2.80 * sigma / sqrt(n) for the tabulated n values (6E sigma 46.3bp, 6B 54.9bp);
evaluable-session arithmetic 1746 - 60(warmup?) - event exclusions ~= 1573/1572.
Exit 0 = arithmetic reproduces."""
import json, sys, math
sigma_6e, sigma_6b = 46.3, 54.9   # bp per day (from 6E_a1_regimes / 6B dossier §1)
z = 2.80
print("n      6E_MDE(calc)  6E(tab)   6B_MDE(calc)  6B(tab)")
table = {100:(12.97,15.38), 300:(7.49,8.88), 500:(5.80,6.88), 600:(5.30,6.28), 900:(4.32,5.13), 1573:(3.27,None), 1572:(None,3.88)}
ok=True
for n,(t6e,t6b) in table.items():
    ce = z*sigma_6e/math.sqrt(n) if t6e else None
    cb = z*sigma_6b/math.sqrt(n) if t6b else None
    m6e = f"{ce:.2f}" if ce else "  -  "
    m6b = f"{cb:.2f}" if cb else "  -  "
    e6e = f"{t6e}" if t6e else "-"
    e6b = f"{t6b}" if t6b else "-"
    d6e = f"{abs(ce-t6e):.2f}" if ce and t6e else "-"
    d6b = f"{abs(cb-t6b):.2f}" if cb and t6b else "-"
    print(f"{n:<6} {m6e:>10} {e6e:>8} (d={d6e})  {m6b:>10} {e6b:>8} (d={d6b})")
    if ce and t6e and abs(ce-t6e) > 0.15: ok=False; print("   6E deviation >0.15bp")
    if cb and t6b and abs(cb-t6b) > 0.15: ok=False; print("   6B deviation >0.15bp")
# MDE range quoted "3.3-15.4bp"
print(f"\nquoted MDE range 3.3-15.4: calc min={z*sigma_6e/math.sqrt(1573):.2f} max={z*sigma_6b/math.sqrt(100):.2f}")
# 6B cost arithmetic: close-proxy 2.11-2.89 + slippage 0.77-2.31 + commission 0.010 (per side -> RT = 2x)
lo = 2*(2.11+0.77+0.010); hi = 2*(2.89+2.31+0.010)
print(f"6B RT cost: 2x(2.11..2.89 + 0.77..2.31 + 0.010) = {lo:.2f}..{hi:.2f} (quoted 5.8-10.4)")
lo6e = 2*(1.21+0.45+0.006); hi6e = 2*(1.57+1.36+0.006)
print(f"6E RT cost: 2x(1.21..1.57 + 0.45..1.36 + 0.006) = {lo6e:.2f}..{hi6e:.2f} (quoted 3.3-5.9)")
# evaluable sessions
for sym, ev in (("6E",55+58),("6B",56+58)):
    print(f"{sym}: 1746 sessions - warmup(60d ~41 sess) - {ev} event days = {1746-41-ev}")
sys.exit(0 if ok else 1)
