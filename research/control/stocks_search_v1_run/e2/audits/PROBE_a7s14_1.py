# A7S14-1 probe (committed evidence; band-law-valid geometry t=440/n=460)
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '../i')
import numpy as np
from datetime import date, timedelta
import i_engine
import i_amended_legs
cal = []
d = date(2015, 1, 2)
while len(cal) < 500:
    if d.weekday() < 5:
        cal.append(d.isoformat())
    d += timedelta(days=1)
ci = {x: i for i, x in enumerate(cal)}
fends = i_engine.fold_ends(tuple(cal), cal[200], cal[350])
n = 460
def mk(op):
    return i_engine.NameData('DZ', tuple(cal[:n]), op, op + 1, op - 1,
                             np.full(n, 100.0), np.full(n, 1e6))
op = np.full(n, 100.0); op[441] = 0.0
_, cens, cnt = i_amended_legs.build_legs_amended(mk(op), [440], 20, ci, fends, 2.0)
assert [c.censored_kind for c in cens] == ['unpriceable_adj_price']
op2 = np.full(n, 100.0); op2[459] = 0.0
_, cens2, _ = i_amended_legs.build_legs_amended(mk(op2), [440], 20, ci, fends, 2.0)
assert [c.censored_kind for c in cens2] == ['unpriceable_adj_price']
op3 = np.full(n, 100.0)
_, cens3, _ = i_amended_legs.build_legs_amended(mk(op3), [440], 20, ci, fends, 2.0)
assert [c.censored_kind for c in cens3] == ['death_open']
print('A7S14-1 PROBE PASS')
