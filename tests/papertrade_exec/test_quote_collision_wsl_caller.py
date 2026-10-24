"""ROUND3: original A7 WSL caller reproducer, now terminal and journaled."""
import copy
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock, patch

import pytest
from research.papertrade_exec import wsl_lane as W, execute as E
from tests.papertrade_exec import test_fixall_w1 as F

env = F.env

# Original A7_ROUND2_TEST_LOG.txt input, unchanged.
q={'type':'MARKET_QUOTE','league':'WSL','match_id':'candidate','bookmaker':'polymarket','payload_sha256':'b'*64,'event_id':'event-b','odds':{'HOME':2},'pm_outcomes':{'HOME':{'market_id':'market-b','token_id_yes':'token-b'}},'fetch_ts_utc':'2026-10-24T00:00:00Z','source_last_update_utc':'2026-10-24T00:00:00Z','market':'h2h','commence_time_utc':'2026-10-24T20:00:00Z'}
fx={'match_id':'candidate','home':'H','away':'A','kickoff_utc':'2026-10-24T20:00:00Z'}
class Led:
 def __init__(self,rows):self.rows=rows
 def load(self):return self
 def verify_chain(self):return True,[]
 def equity_cents(self):return 100000
 def decided_match_ids(self):return set()
 def append_decision(self,row,**kw):self.rows.append(row);return row


def run_caller(candidate, forbidden_downstream=True):
    led=Led([{'type':'FORECAST','league':'WSL','match_id':'candidate','p':{'HOME':.55},'recorded_at_utc':'2026-10-24T00:00:00Z'},candidate])
    evaluate=Mock(return_value={'type':'DECISION','match_id':'candidate','status':'NO_EDGE','stake_cents':0})
    stake=Mock(return_value=500)
    if forbidden_downstream:
        evaluate.side_effect=AssertionError('EV must not precede incomplete-candidate refusal')
        stake.side_effect=AssertionError('Stake must not precede incomplete-candidate refusal')
    core=N(ledger=N(PaperLedger=lambda p:led),stake_for_decision=stake,risk=N(evaluate_match=evaluate))
    args=N(date='2026-10-24',wsl_registry='unused')
    with patch.object(W,'now_of',return_value='2026-10-24T01:00:00Z'),patch.object(W,'core_of',return_value=core),patch.object(W,'register_wsl_league_law'),patch.object(W,'ledger_path_of',return_value=Path('unused')),patch.object(W,'fixtures_for_day',return_value=[fx]),patch.object(W,'make_in_lock_recheck',return_value=lambda x:x) as recheck,patch.object(E,'papertrade_flags',return_value={'ai_authority_active':False}):
        result=W.cmd_decide(args)
        if forbidden_downstream: recheck.assert_not_called()
    return led,result,evaluate,stake


@pytest.mark.parametrize('field',['bookmaker','payload_sha256','event_id','market_id','leg_identity'])
def test_wsl_real_caller_missing_candidate_is_terminal(field):
    candidate=copy.deepcopy(q)
    if field=='market_id': candidate['pm_outcomes']['HOME'].pop('market_id')
    elif field=='leg_identity': candidate.pop('pm_outcomes')
    else: candidate.pop(field)
    led,result,evaluate,stake=run_caller(candidate)
    decisions=[r for r in led.rows if r.get('type')=='DECISION']
    assert len(decisions)==1
    dec=decisions[0]
    assert dec['status']=='QUOTE_IDENTITY_MISSING'
    assert dec['stake_cents']==0 and dec['chosen_leg'] is None
    assert ('pm_event_id' if field=='event_id' else field) in dec['reason']
    assert result['journaled'][0]['status']=='QUOTE_IDENTITY_MISSING'
    evaluate.assert_not_called();stake.assert_not_called()
    assert candidate==led.rows[1]  # The quote is not repaired or rewritten.


def test_wsl_complete_candidate_reaches_same_downstream_path():
    led,result,evaluate,stake=run_caller(copy.deepcopy(q),False)
    evaluate.assert_called_once();stake.assert_called_once()
    assert result['journaled'][0]['status']=='NO_EDGE'
    assert len([r for r in led.rows if r.get('type')=='DECISION'])==1


@pytest.mark.parametrize('field',['bookmaker','payload_sha256'])
def test_standard_real_caller_already_guards_missing_identity(env,field):
    led=F._sandbox_ledger(env);F._seed_chain(led,'m1',bookmaker='polymarket')
    # Standard quote_index deliberately freezes the FIRST quote, not latest.
    # Supply the missing-field candidate in memory, as in the original A7 probe.
    candidate=next(r for r in led.rows if r.get('type')=='MARKET_QUOTE')
    candidate.pop(field)
    evaluate=Mock(side_effect=AssertionError('Incomplete candidate must not reach EV'))
    result=F._run_decide(env,led,evaluate=evaluate)
    dec=[r for r in led.rows if r.get('type')=='DECISION'][-1]
    assert dec['status']=='QUOTE_IDENTITY_MISSING' and dec['stake_cents']==0
    assert field in dec['reason'] and result['journaled'][0]['status']=='QUOTE_IDENTITY_MISSING'
    evaluate.assert_not_called()
