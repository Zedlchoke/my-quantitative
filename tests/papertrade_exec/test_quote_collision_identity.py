"""Owner W1.4 regression: source identity, historical replay, downstream gates."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from research.papertrade_exec import execute as E
from tests.papertrade_exec.quote_identity_fixtures import identity_fields
from tests.papertrade_exec import test_fixall_w1 as W

env = W.env
CONTROL = Path(__file__).resolve().parents[2] / 'research/control/PAPERDESK-QUOTE-COLLISION-FIX-V1'
HISTORY = json.loads((CONTROL / 'HISTORICAL_CASES.json').read_text())
QUOTES = {r['match_id']: r for r in HISTORY if r['type'] == 'MARKET_QUOTE'}
FULL_QUOTES = json.loads((CONTROL / 'ROUND2_FULL_QUOTE_LEDGER.json').read_text())
PAIRS = [('401909853','401909845'), ('401909095','401909093'),
         ('401909849','401909850'), ('401909850','401909849')]


def quote(mid):
    return {'type':'MARKET_QUOTE','league':'NBA','match_id':mid,
            'bookmaker':'POLYMARKET_CLOB','odds':{'HOME':2.030539,'AWAY':1.843471},
            **identity_fields(mid)}


@pytest.mark.parametrize('full_ledger', [False, True])
@pytest.mark.parametrize('mid,peer', PAIRS)
def test_historical_price_twins_reach_ev_and_ai(env, mid, peer, full_ledger):
    # Only isolated sandbox data are written. No historic decisions are replayed
    # into the real ledger, nor are downstream economic outcomes inferred.
    led = W._sandbox_ledger(env)
    W._seed_chain(led, mid, bookmaker='POLYMARKET_CLOB')
    q = next(r for r in led.rows if r.get('type') == 'MARKET_QUOTE')
    q.update(copy.deepcopy(QUOTES[mid]))
    led.rows.extend(copy.deepcopy(FULL_QUOTES if full_ledger else [QUOTES[peer]]))
    fx = E.A.Fixture(league='NBA', match_id=mid, home=q['home'], away=q['away'],
                    kickoff_utc=q['kickoff_utc'], competition='NBA',
                    et_local_date=q['kickoff_utc'][:10], source_ref='TEST')
    calls = []
    def evaluate(*args, **kw):
        calls.append('EV')
        return {'type':'DECISION','match_id':mid,'league':'NBA','status':'BET_PAPER',
                'reason':'stub economic pass','stake_cents':500,'chosen_leg':'HOME',
                'ev_net_by_leg':{'HOME':0.06}, 'p_frozen':{'HOME':0.55},
                'odds_frozen':q['odds'],'equity_at_decision_cents':100000}
    def ai(*args):
        calls.append('AI')
        return {'type':'DECISION','match_id':mid,'league':'NBA','status':'NOT_PLACED_AI_VETO',
                'reason':'stub veto','stake_cents':0,'chosen_leg':None}
    with patch.object(E,'papertrade_flags',return_value={'ai_authority_active':True}), \
         patch.object(E,'apply_ai_gate_v2',side_effect=ai):
        W._run_decide(env,led,evaluate=evaluate,fixtures=[fx])
    assert calls == ['EV','AI']
    dec = [r for r in led.rows if r.get('type') == 'DECISION'][-1]
    assert dec['status'] == 'NOT_PLACED_AI_VETO'
    notes = {n['code']:n for n in dec['quote_observations']}
    assert peer in notes['PRICE_TWIN_OBSERVED']['match_ids']
    assert notes['LEG_IDENTITY_SEMANTIC_FALLBACK']['quotes']
    if full_ledger:
        assert notes['INCOMPLETE_PEERS_SKIPPED']['count'] == 10
        assert len(notes['INCOMPLETE_PEERS_SKIPPED']['peers']) == 10


@pytest.mark.parametrize('kind', ['payload','market','event_leg'])
def test_reused_source_blocks_even_with_different_prices(kind):
    a,b=quote('a'),quote('b'); b['odds']={'HOME':3.0,'AWAY':1.5}
    if kind=='payload': b['payload_sha256']=a['payload_sha256']
    if kind=='market': b['pm_walk']['market_id']=a['pm_walk']['market_id']
    if kind=='event_leg': b['pm_walk']['event_id']=a['pm_walk']['event_id']
    result=E.quote_collision(SimpleNamespace(rows=[a]),'b',b)
    assert result['status']=='NOT_RUN_QUOTE_COLLISION'
    assert {'payload':'payload_sha256=', 'market':'(bookmaker, market_id)=',
            'event_leg':'(pm_event_id, leg_identity)='}[kind] in result['reason']


@pytest.mark.parametrize('side',['candidate','peer'])
@pytest.mark.parametrize('field',['payload_sha256','bookmaker','market_id','event_id','legs'])
def test_missing_identity_fails_closed(side,field):
    a,b=quote('a'),quote('b')
    a['pm_walk']['event_id']=b['pm_walk']['event_id']
    a['pm_walk']['market_id']=b['pm_walk']['market_id']
    target=b if side=='candidate' else a
    if field in ('payload_sha256','bookmaker'): target.pop(field)
    else: target['pm_walk'].pop(field)
    result=E.quote_collision(SimpleNamespace(rows=[a]),'b',b)
    assert result['status']=='QUOTE_IDENTITY_MISSING'
    assert 'QUOTE_IDENTITY_MISSING' in result['reason']


def test_collision_is_cross_league_and_same_fixture_is_exempt():
    a,b=quote('a'),quote('b'); a['league']='WSL';b['payload_sha256']=a['payload_sha256']
    assert E.quote_collision(SimpleNamespace(rows=[a]),'b',b)['status']=='NOT_RUN_QUOTE_COLLISION'
    assert E.quote_collision(SimpleNamespace(rows=[dict(b)]),'b',b)['status']=='CLEAR'


@pytest.mark.parametrize('kind', ['payload', 'market', 'event_leg', 'missing'])
def test_decision_blocks_source_reuse_before_ev(env, kind):
    led = W._sandbox_ledger(env)
    W._seed_chain(led, 'm1', bookmaker='POLYMARKET_CLOB')
    current = next(r for r in led.rows if r.get('type') == 'MARKET_QUOTE')
    peer = quote('peer')
    if kind == 'payload': peer['payload_sha256'] = current['payload_sha256']
    elif kind == 'market': peer['pm_walk']['market_id'] = current['pm_walk']['market_id']
    elif kind == 'event_leg': peer['pm_walk']['event_id'] = current['pm_walk']['event_id']
    else:
        peer['pm_walk'].pop('event_id')
        peer['payload_sha256']=current['payload_sha256']
    led.append(peer)
    calls = []
    def evaluate(*args, **kwargs):
        calls.append('EV')
        raise AssertionError('A W1.4 block must precede EV')
    W._run_decide(env, led, evaluate=evaluate)
    dec = [r for r in led.rows if r.get('type') == 'DECISION'][-1]
    assert not calls
    assert dec['status'] == ('QUOTE_IDENTITY_MISSING' if kind == 'missing' else 'NOT_RUN_QUOTE_COLLISION')
    assert dec['stake_cents'] == 0 and dec['chosen_leg'] is None
    assert ('QUOTE_IDENTITY_MISSING' if kind == 'missing' else
            {'payload':'payload_sha256=', 'market':'(bookmaker, market_id)=',
             'event_leg':'(pm_event_id, leg_identity)='}[kind]) in dec['reason']


def test_vwap_twin_and_bookmaker_aliases():
    a,b=quote('a'),quote('b')
    b['odds']={'HOME':1.7,'AWAY':2.1}
    for row in (a,b):
        row['pm_walk']['legs']={'HOME':{'vwap_ask':0.5},'AWAY':{'vwap_ask':0.51}}
    result=E.quote_collision(SimpleNamespace(rows=[a]),'b',b)
    assert result['status']=='CLEAR' and result['price_twin_match_ids']==['a']
    a['bookmaker']='polymarket'
    b['pm_walk']['market_id']=a['pm_walk']['market_id']
    assert E.quote_collision(SimpleNamespace(rows=[a]),'b',b)['status']=='NOT_RUN_QUOTE_COLLISION'


def test_wsl_explicit_outcomes_identity():
    a={'type':'MARKET_QUOTE','league':'WSL','match_id':'w1','bookmaker':'polymarket',
       'payload_sha256':'a'*64, 'event_id':'event-w1',
       'odds':{'HOME':2.0,'DRAW':3.0,'AWAY':4.0},
       'pm_outcomes':{leg:{'market_id':'w1-'+leg,'token_id_yes':'token-'+leg}
                      for leg in ('HOME','DRAW','AWAY')}}
    b=copy.deepcopy(a);b.update(match_id='w2',payload_sha256='b'*64,event_id='event-w2')
    for leg in b['pm_outcomes']: b['pm_outcomes'][leg]['market_id']='w2-'+leg
    assert E.quote_collision(SimpleNamespace(rows=[a]),'w2',b)['status']=='CLEAR'
    b['pm_outcomes']['DRAW']['market_id']=a['pm_outcomes']['DRAW']['market_id']
    result=E.quote_collision(SimpleNamespace(rows=[a]),'w2',b)
    assert result['status']=='NOT_RUN_QUOTE_COLLISION' and 'w1-DRAW' in result['reason']


def test_a7_f1_and_f2_verbatim_regression():
    # Exact A7_REPORT.md data and sequence; assertions replace its print calls.
    a = {"type":"MARKET_QUOTE", "match_id":"peer", "bookmaker":"polymarket",
         "payload_sha256":"a"*64, "event_id":"event-actual", "odds":{"HOME":2.0},
         "pm_outcomes":{"HOME":{"market_id":"market-a", "token_id_yes":"actual-token-123"}}}
    b = {"type":"MARKET_QUOTE", "match_id":"candidate", "bookmaker":"polymarket",
         "payload_sha256":"b"*64, "event_id":"event-actual", "odds":{"YES":2.0},
         "pm_outcomes":{"YES":{"market_id":"market-b", "token_id_yes":"actual-token-123"}}}
    result=E.quote_collision(SimpleNamespace(rows=[a]), "candidate", b)
    assert result['status']=='NOT_RUN_QUOTE_COLLISION'
    assert 'event-actual' in result['reason'] and 'actual-token-123' in result['reason']
    a.pop("bookmaker")
    a["payload_sha256"] = b["payload_sha256"]
    assert E.quote_collision(SimpleNamespace(rows=[a]), "candidate", b)['status']=='QUOTE_IDENTITY_MISSING'


@pytest.mark.parametrize('field',['token_id_yes','token_id','tokenId','outcome_id','outcomeId'])
def test_explicit_leg_ids_override_labels_both_directions(field):
    a,b=quote('a'),quote('b')
    a['pm_walk']['event_id']=b['pm_walk']['event_id']='same-event'
    a['pm_walk']['legs']={'HOME':{field:'same-id'}};a['odds']={'HOME':2.0}
    b['pm_walk']['legs']={'YES':{field:'same-id'}};b['odds']={'YES':2.0}
    assert E.quote_collision(SimpleNamespace(rows=[a]),'b',b)['status']=='NOT_RUN_QUOTE_COLLISION'
    b['pm_walk']['legs']={'HOME':{field:'different-id'}};b['odds']={'HOME':2.0}
    result=E.quote_collision(SimpleNamespace(rows=[a]),'b',b)
    assert result['status']=='CLEAR'
    assert not result['leg_identity_fallbacks']


@pytest.mark.parametrize('strong',['payload','market','event',None])
def test_incomplete_peer_two_tier_disclosed(strong):
    a,b=quote('a'),quote('b');a.pop('bookmaker')
    if strong=='payload': a['payload_sha256']=b['payload_sha256']
    elif strong=='market': a['pm_walk']['market_id']=b['pm_walk']['market_id']
    elif strong=='event': a['pm_walk']['event_id']=b['pm_walk']['event_id']
    result=E.quote_collision(SimpleNamespace(rows=[a]),'b',b)
    if strong:
        assert result['status']=='QUOTE_IDENTITY_MISSING'
        assert result['incomplete_peers_skipped_count']==0
    else:
        assert result['status']=='CLEAR' and result['incomplete_peers_skipped_count']==1
        dec=E.note_price_twins({},result)
        note=next(n for n in dec['quote_observations'] if n['code']=='INCOMPLETE_PEERS_SKIPPED')
        assert note['count']==1 and note['peers'][0]['match_id']=='a'
        assert note['peers'][0]['missing']==['bookmaker']


@pytest.mark.parametrize('reverse',[False,True])
def test_missing_relevant_peer_precedes_collision_and_keeps_skip_count(reverse):
    a,b,c=quote('a'),quote('b'),quote('c');d=quote('d')
    a['payload_sha256']=b['payload_sha256']
    c.pop('bookmaker');c['payload_sha256']=b['payload_sha256']
    d.pop('bookmaker')
    peers=[a,c,d]
    if reverse: peers.reverse()
    result=E.quote_collision(SimpleNamespace(rows=peers),'b',b)
    assert result['status']=='QUOTE_IDENTITY_MISSING'
    assert result['incomplete_peers_skipped_count']==1


def test_candidate_missing_identity_never_uses_skip_rule():
    b=quote('b');b['pm_walk'].pop('market_id')
    assert E.quote_collision(SimpleNamespace(rows=[]),'b',b)['status']=='QUOTE_IDENTITY_MISSING'
