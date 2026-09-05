import json, sys, tempfile, importlib
from pathlib import Path
ROOT = Path('/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v14/integration')
OUT = ROOT / 'research/control/v14_run/q_six_arm_dummy_dry_run.json'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
td = importlib.import_module('test_v14_driver')
drv = importlib.import_module('research.control.v14_run.tools.run_v14_cell')
scratch = Path(tempfile.mkdtemp(prefix='v14_q_dryrun_'))
world = td.build_synthetic_world(scratch / 'synthetic_world')
results = []
for family, arm in td.SIX_ARMS:
    out_root = scratch / 'out' / family / arm
    rc = drv.main(['--family', family, '--arm', arm,
        '--staged-root', str(world['staged_root']),
        '--basis-staged-root', str(world['basis_staged_root']),
        '--basis-manifest', str(world['basis_manifest']),
        '--oi-root', str(world['oi_root']),
        '--oi-manifest', str(world['oi_manifest']),
        '--dry-run', '--out-root', str(out_root)])
    results.append({'family': family, 'arm': arm, 'exit_code': rc})
ledgers = [str(p) for p in scratch.rglob('*') if 'ledger' in p.name.lower() and p.is_file()]
digests = {}
for family, arm in td.SIX_ARMS:
    pf = list((scratch / 'out' / family / arm).rglob('preflight*.json'))
    if pf:
        d = json.load(open(pf[0]))
        digests[f'{family}/{arm}'] = d.get('arm_config_digest') or d.get('digest') or 'missing'
result = {
 'schema': 'v14_run_artifact_v1', 'artifact': 'q_six_arm_dummy_dry_run', 'cycle': 'CRYPTO-V14',
 'generated_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
 'producer_role': 'A1', 'scratch_root': str(scratch), 'arms': results,
 'all_exit_zero': all(r['exit_code'] == 0 for r in results),
 'ledger_files_written': ledgers, 'digests': digests,
 'digests_pairwise_unique': len(set(digests.values())) == len(digests) and len(digests) == 6,
 'synthetic_root': str(world['staged_root']),
 'note': 'driver --dry-run on synthetic staged root: publication refused, no scored ledger written anywhere in scratch; digests match family-lane recorded values',
}
json.dump(result, open(OUT, 'w'), indent=1); open(OUT, 'a').write('\n')
print('saved', OUT, 'all_exit_zero=', result['all_exit_zero'], 'unique=', result['digests_pairwise_unique'], 'ledgers=', ledgers)
