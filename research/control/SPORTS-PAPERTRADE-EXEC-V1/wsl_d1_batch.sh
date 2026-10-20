#!/bin/bash
# WSL D-1 provenance batch (POLICY_FREEZE: forecast-only; writes the
# provenance ledger ONLY). D = tomorrow ICT. Idempotent: existing
# forecasts are skipped by the pinned adapter (verified in battery).
set -euo pipefail
EXEC_WT="/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration"
PREP_DATA="/Users/hoangminhlong/.my-quantitative-data/wsl-winprob-paper-prep-v1"
ADAPTER="/Users/hoangminhlong/my-quantitative/.worktrees/wsl-winprob-prospective-paper-prep-v1/integration/research/control/WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1/lanes/L_ADAPTER/wsl_forecast_adapter.py"
PY="/Users/hoangminhlong/my-quantitative/.venv/bin/python"
D=$($PY -c "from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) + timedelta(hours=7, days=1)).strftime('%Y-%m-%d'))")
FIX="$PREP_DATA/first_batch/fixtures_d$D.json"
"$PY" - "$D" <<'PYEOF'
import json, csv, sys
from pathlib import Path
D = sys.argv[1]
prep = Path('/Users/hoangminhlong/.my-quantitative-data/wsl-winprob-paper-prep-v1')
cross = {r['source_name']: r['ewf_team_id'] for r in csv.DictReader(
    open(prep / 'evidence/crosswalk/crosswalk_fixturedownload_to_ewf_teamid.csv'))}
subs = [json.loads(l) for l in open('/Users/hoangminhlong/.my-quantitative-data/'
        'sports-papertrade-exec-v1/data/wsl_fixture_substrate.jsonl') if l.strip()]
csv_rows = list(csv.DictReader(open('/tmp/wsl2026_d1.csv'))) if False else None
fx = []
for s in sorted((x for x in subs if x.get('kickoff_utc', '').startswith(D)),
                key=lambda x: x['kickoff_utc']):
    cross2 = {}
    fx.append({'match_id': s['match_id'], 'date': D,
               'kickoff_utc': s['kickoff_utc'],
               'home_team_id': cross[s['home']], 'home_name': s['home'],
               'away_team_id': cross[s['away']], 'away_name': s['away'],
               'competition': 'WSL_LEAGUE', 'note': s.get('note') or 'NA',
               'venue': s.get('venue'), 'round': s.get('round')})
Path(prep / 'first_batch' / f'fixtures_d{D}.json').write_text(
    json.dumps({'fixtures': fx, 'generated_utc': 'auto-d1',
                'source': 'exec substrate + pinned crosswalk (D-1 batch)'},
               indent=1, ensure_ascii=False))
print(f'fixtures_d{D}.json: {len(fx)} fixtures')
PYEOF
cd "$(dirname "$ADAPTER")"
"$PY" "$ADAPTER" forecast --date "$D" --fixtures "$FIX" \
  --corpus "$PREP_DATA/first_batch/corpus_merged_dminus1_20261018.csv" \
  --ledger "$PREP_DATA/ledger/paper_ledger.jsonl" \
  --data-root "$PREP_DATA"
