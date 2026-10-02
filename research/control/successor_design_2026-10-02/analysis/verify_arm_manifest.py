#!/usr/bin/env python
"""Verify the canonical arm manifest (F5): recompute per-option totals from
the arms list and assert they match the declared totals block. Read-only on
arm_manifest.json; exit 1 on any mismatch. Run:
  .venv/bin/python research/control/successor_design_2026-10-02/analysis/verify_arm_manifest.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
m = json.load(open(os.path.join(HERE, 'arm_manifest.json')))

def totals_for(option, with_hn5):
    ids = rows = 0
    for a in m['arms']:
        if option not in a['options']:
            continue
        if a['class'] == 'optional_hypothesis' and not with_hn5:
            continue
        ids += 1
        rows += a['rows']
    res_ids = m['reserve']['identities']
    res_rows = m['reserve']['rows']
    learn = m['totals']['learn_side']['grid_rows']
    return {
        'committed_identities': ids,
        'committed_scored_rows': rows,
        'max_identities_with_reserve': ids + res_ids,
        'max_scored_rows_with_reserve': rows + res_rows,
        'max_total_rows_with_LEARN': rows + res_rows + learn,
    }

fail = 0
for opt_key, opt in (('option_A', 'A'), ('option_B', 'B')):
    for hn5 in (False, True):
        got = totals_for(opt, hn5)
        key = 'committed_identities_with_HN5' if hn5 else 'committed_identities'
        keyr = 'committed_scored_rows_with_HN5' if hn5 else 'committed_scored_rows'
        want_ids = m['totals'][opt_key][key]
        want_rows = m['totals'][opt_key][keyr]
        tag = f"{opt_key} hn5={hn5}"
        if got['committed_identities'] != want_ids:
            print(f"MISMATCH {tag} identities: manifest says {want_ids}, arms sum to {got['committed_identities']}")
            fail += 1
        if got['committed_scored_rows'] != want_rows:
            print(f"MISMATCH {tag} rows: manifest says {want_rows}, arms sum to {got['committed_scored_rows']}")
            fail += 1
        if hn5:
            for k, wk in (('max_identities_with_reserve', 'max_identities_with_reserve_HN5'),
                          ('max_scored_rows_with_reserve', 'max_scored_rows_with_reserve_HN5'),
                          ('max_total_rows_with_LEARN', 'max_total_rows_with_LEARN12')):
                if got[k] != m['totals'][opt_key][wk]:
                    print(f"MISMATCH {tag} {k}: manifest {m['totals'][opt_key][wk]}, computed {got[k]}")
                    fail += 1
        print(f"computed {tag}: {got['committed_identities']} ids / {got['committed_scored_rows']} rows")

classes = {a['class'] for a in m['arms']}
assert 'baseline' in classes and 'lol' in classes
lol_ids = [a['arm_id'] for a in m['arms'] if a['class'] == 'lol']
assert len(lol_ids) == len(set(lol_ids)), 'duplicate LOL ids'
assert not any('S017' in i for i in lol_ids), 'LOL over retired S017 must not exist'
b0 = [a for a in m['arms'] if a['arm_id'] == 'B0_FLAT'][0]
assert b0['rows'] == 0 and b0['folds'] == 0, 'B0 law: 1 identity, 0 rows'
n_seed = [a for a in m['arms'] if a['class'] == 'control_battery']
assert len(n_seed) == 1 and 'seed_line' in n_seed[0]
print('structural checks: PASS')
print('LOL arms:', len(lol_ids), sorted(lol_ids))
if fail:
    print(f'{fail} MISMATCHES -- manifest totals block is wrong; fix it to the computed values')
    sys.exit(1)
print('ALL TOTALS MATCH')
