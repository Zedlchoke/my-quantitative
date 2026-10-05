# a7_null_synth.py — A7 audit · designed-null on MY OWN synthetic stream (A7-3)
# Own generator (deliberately different from the harness's synthetic_stream):
# 3 seasons x 6 teams, same-tip triple-batches, 2 neutral rows, my own RNG seed.
# c≡1 and φ=0 must equal the parent p_home stream bit-for-bit (float64 hex).
import math
import random

TEAMN = 6
SEASONS = (2101, 2102, 2103)  # synthetic-only seasons, no real-year overlap


def my_synth():
    rng = random.Random(7007)
    fks = ["AUD%d" % i for i in range(TEAMN)]
    games = []
    day = 0
    for s in SEASONS:
        for a in range(TEAMN):
            for b in range(a + 1, TEAMN):
                for rep in range(2):
                    home, away = (a, b) if rng.random() < 0.5 else (b, a)
                    games.append({
                        "tip": day, "game_id": "AUD-%d-%d-%d-%d" % (s, a, b, rep),
                        "season": s, "fk_home": fks[home], "fk_away": fks[away],
                        "home_win": int(rng.random() < 0.62), "neutral": False,
                        "row_home": None, "row_away": None,
                    })
                    day += 1
    # same-tip triple batches + two neutral rows
    for t in range(0, len(games) - 3, 37):
        for g in games[t:t + 3]:
            g["tip"] = games[t]["tip"]
    games[5]["neutral"] = True
    games[40]["neutral"] = True
    games.sort(key=lambda g: (g["tip"], g["game_id"]))
    return games


def run(games, phi=None, x_fn=None, c_fn=None):
    r, ls, preds = {}, {}, []
    i = 0
    while i < len(games):
        tip = games[i]["tip"]
        j = i
        batch = []
        while j < len(games) and games[j]["tip"] == tip:
            batch.append(games[j]); j += 1
        ctx = []
        for g in batch:
            hca_eff = 0.0 if g["neutral"] else 50.0
            c_h = c_fn(g["row_home"], g["season"]) if c_fn else None
            rh = eff(g["fk_home"], g["season"], 0.65, c_h, r, ls, c_fn)
            ra = eff(g["fk_away"], g["season"], 0.65, None, r, ls, c_fn)
            arg = rh - ra + hca_eff
            if x_fn is not None:
                xh, _ = x_fn(g["row_home"], g["season"])
                xa, _ = x_fn(g["row_away"], g["season"])
                arg = arg + phi * (xh - xa)
            p = 1.0 / (1.0 + 10.0 ** (-arg / 400.0))
            ctx.append((g, p))
            preds.append(float(p).hex())
        for g, p in ctx:
            y = float(g["home_win"])
            r[g["fk_home"]] += 32.0 * (y - p)
            r[g["fk_away"]] += 32.0 * ((1.0 - y) - (1.0 - p))
        i = j
    return preds


def eff(fk, season, gamma, c, r, ls, c_fn):
    if ls.get(fk) != season:
        if fk in r:
            r[fk] = 1500.0 + gamma * (c if c is not None else 1.0) * (r[fk] - 1500.0)
        else:
            r[fk] = 1500.0
        ls[fk] = season
    return r[fk]


games = my_synth()
parent = run(games)
phi0 = run(games, phi=0.0, x_fn=lambda row, s: (0.37, None))
c1 = run(games, c_fn=lambda row, s: 1.0)
both = run(games, phi=0.0, x_fn=lambda row, s: (0.37, None),
           c_fn=lambda row, s: 1.0)
n = len(parent)
ok_phi = phi0 == parent
ok_c = c1 == parent
ok_both = both == parent
print("A3_SYNTH n=%d phi0_identical=%s c1_identical=%s both_identical=%s"
      % (n, ok_phi, ok_c, ok_both))
# negative control: a real feature argument MUST break identity (probe sensitivity)
toggle = [0]


def x_alt(row, s):
    toggle[0] ^= 1
    return (0.37 if toggle[0] else -0.37), None


phi_real = run(games, phi=25.0, x_fn=x_alt)
ok_neg = phi_real != parent
print("A3_SYNTH negative_control_phi25_differs=%s" % ok_neg)
raise SystemExit(0 if (ok_phi and ok_c and ok_both and ok_neg) else 1)
