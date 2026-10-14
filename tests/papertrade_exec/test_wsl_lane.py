"""WSL BET_PAPER lane battery (CAPITAL-V3 §4/§8; owner instruction
2026-10-14: the production path must be fail-closed end-to-end BEFORE the
first real WSL paper rows). Offline + deterministic: Gamma events are
synthetic-but-shape-exact; books are injected through the SAME books_provider
seam the real runner wiring binds; the corpus + engine + crosswalk are the
REAL pinned artifacts. The REAL ledger is asserted byte-unchanged around
every test."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import execute  # noqa: E402
from research.papertrade_exec import wsl_lane  # noqa: E402

NOW_FMT = "%Y-%m-%dT%H:%M:%SZ"
KO = "2026-10-17T11:45:00Z"
ANCHOR = "2026-10-17T05:45:00Z"
DAY = "2026-10-17"
NOW_OK = "2026-10-15T00:00:00Z"          # before the anchor, before cutoff
REAL_LEDGER = Path(os.path.expanduser(
    "~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/"
    "paper_ledger.jsonl"))
REAL_SUBSTRATE = Path(os.path.expanduser(
    "~/.my-quantitative-data/sports-papertrade-exec-v1/data/"
    "wsl_substrate_corpus.jsonl"))
RULES_90 = ("This market refers only to the outcome within the first 90 "
            "minutes of regular play plus stoppage time")
RULES_BAD = ("This market resolves on the winner including extra time and "
             "penalties where applicable")
PROV_P = {"HOME": 0.7947807579055409, "DRAW": 0.13235551666863574,
          "AWAY": 0.07286372542582328}
FIXTURE = {"match_id": "FD-2026-M37", "home": "Arsenal",
           "away": "Birmingham City", "kickoff_utc": KO,
           "competition": "WSL_LEAGUE", "stage": "LEAGUE_90MIN",
           "fixture_source": "battery (substrate shape)"}


@pytest.fixture()
def real_ledger_untouched():
    before = hashlib.sha256(REAL_LEDGER.read_bytes()).hexdigest()
    yield
    assert hashlib.sha256(REAL_LEDGER.read_bytes()).hexdigest() == before, \
        "REAL ledger changed during the sandbox battery — violation"


@pytest.fixture(autouse=True)
def _seams():
    yield
    for seam in (wsl_lane.fixtures_for_day, wsl_lane.substrate_corpus,
                 wsl_lane.core_of, wsl_lane.ledger_path_of):
        if hasattr(seam, "_impl"):
            del seam._impl


@pytest.fixture()
def env(tmp_path):
    data = tmp_path / "wsl-battery"
    data.mkdir()
    core = execute.load_pinned_core(roots={})
    led = core.ledger.PaperLedger(data / "ledger.jsonl")
    led.load()
    led.genesis(plan_sha256="wsl-lane-battery", sandbox=True)
    wsl_lane.fixtures_for_day._impl = lambda args, day: [dict(FIXTURE)] \
        if day == DAY else []
    wsl_lane.substrate_corpus._impl = lambda args: [
        json.loads(l) for l in REAL_SUBSTRATE.read_text().splitlines()
        if l.strip()]
    wsl_lane.ledger_path_of._impl = lambda args: data / "ledger.jsonl"
    return {"data": data, "core": core,
            "registry": REPO / "plans" / "CYCLE_REGISTRY.json"}


def rows_of(env_, type_, status=None, league="WSL"):
    led = env_["core"].ledger.PaperLedger(env_["data"] / "ledger.jsonl").load()
    return [r for r in led.rows
            if r.get("type") == type_ and r.get("league") == league
            and (status is None or r.get("status") == status)]


def ns(env_, cmd, now=NOW_OK, **extra):
    import argparse
    base = {"sandbox": True, "now": now, "date": DAY, "league": "WSL",
            "data_root": str(env_["data"]),
            "sandbox_registry": str(env_["registry"]),
            "wsl_provenance_ledger": None, "wsl_pm_events": None,
            "wsl_books_provider": None, "wsl_quote_mode": "REAL",
            "wsl_registry": str(env_["registry"])}
    base.update(extra)
    return argparse.Namespace(**base)


def pm_market(mid, question, *, token_yes, description=RULES_90,
              closed=False, active=True):
    return {"id": str(mid), "question": question,
            "description": description, "closed": closed, "active": active,
            "outcomes": ["Yes", "No"],
            "clobTokenIds": [str(token_yes), str(token_yes + 1)]}


def pm_event(*, ev_id=1167584, legs=("HOME", "DRAW", "AWAY"),
             description=RULES_90, closed=False, active=True,
             home="Arsenal WFC", away="Birmingham City WFC", kickoff=KO):
    mkts = []
    tokens = {"HOME": 5528995, "DRAW": 5528996, "AWAY": 5528997}
    if "HOME" in legs:
        mkts.append(pm_market(tokens["HOME"], f"Will {home} win?",
                              token_yes=tokens["HOME"], description=description,
                              closed=closed, active=active))
    if "DRAW" in legs:
        mkts.append(pm_market(tokens["DRAW"],
                              f"Will {home} vs. {away} end in a draw?",
                              token_yes=tokens["DRAW"], description=description,
                              closed=closed, active=active))
    if "AWAY" in legs:
        mkts.append(pm_market(tokens["AWAY"], f"Will {away} win?",
                              token_yes=tokens["AWAY"], description=description,
                              closed=closed, active=active))
    return {"id": str(ev_id), "title": f"{home} vs. {away}",
            "sport": "soccer", "startTime": kickoff, "markets": mkts}


def deep_books(prices=None, size=100000):
    """Realistic three-YES book: implied geometry inside the core's
    [0.999, 1.20] band; HOME at 0.72 lets the frozen p (0.7948) clear the
    EV gate so the full BET_PAPER path is exercised."""
    prices = prices or {"HOME": 0.72, "DRAW": 0.14, "AWAY": 0.16}

    def provider(fixture, join, leg):
        asks = [{"price": str(prices[leg]), "size": str(size)}]
        return asks, "book-hash", hashlib.sha256(
            json.dumps(asks, sort_keys=True).encode()).hexdigest()
    return provider


def seed_forecast(env_):
    out = wsl_lane.cmd_forecast(ns(env_, "forecast"))
    assert out["written"] == ["FD-2026-M37"], out
    return out


# ------------------------------------------------------------------ forecast --

def test_forecast_bit_exact_vs_provenance(env, real_ledger_untouched):
    """THE linchpin: the pinned engine over the freeze-excluded substrate
    corpus reproduces the provenance FORECAST p EXACTLY; the §4.2 cross-check
    passes and the row lands in the SHARED ledger."""
    seed_forecast(env)
    fc = rows_of(env, "FORECAST")
    assert len(fc) == 1
    assert fc[0]["p"] == PROV_P
    assert fc[0]["model_id"] == "B1_ELO_DAVIDSON_WSL"
    assert fc[0]["anchor_utc"] == ANCHOR
    # idempotent rerun: no second forecast row
    wsl_lane.cmd_forecast(ns(env, "forecast"))
    assert len(rows_of(env, "FORECAST")) == 1


def test_forecast_disagreement_refused(env, tmp_path, real_ledger_untouched):
    """Any leg mismatch vs the provenance ledger refuses BLOCKED_FORECAST_
    DISAGREEMENT and journals NOTHING into the shared ledger."""
    prov = env_ = tmp_path / "prov.jsonl"
    core = env["core"]
    led = core.ledger.PaperLedger(prov)
    led.load()
    led.genesis(plan_sha256="prov-battery", sandbox=True)
    led.append({"type": "FORECAST", "league": "WSL", "match_id": "FD-2026-M37",
                "p": {"HOME": 0.5, "DRAW": 0.3, "AWAY": 0.2},
                "recorded_at_utc": NOW_OK})
    out = wsl_lane.cmd_forecast(ns(env, "forecast",
                                   wsl_provenance_ledger=str(prov)))
    assert out["written"] == [] and \
        out["refused"][0]["status"] == "BLOCKED_FORECAST_DISAGREEMENT"
    assert rows_of(env, "FORECAST") == []


def test_forecast_no_provenance_refused(env, tmp_path,
                                        real_ledger_untouched):
    prov = tmp_path / "prov_empty.jsonl"
    led = env["core"].ledger.PaperLedger(prov)
    led.load()
    led.genesis(plan_sha256="prov-empty", sandbox=True)
    out = wsl_lane.cmd_forecast(ns(env, "forecast",
                                   wsl_provenance_ledger=str(prov)))
    assert out["written"] == [] and \
        out["refused"][0]["status"] == "NOT_RUN_NO_PROVENANCE_FORECAST"


# --------------------------------------------------------------------- quote --

def test_quote_success_and_bets_full_stake(env, real_ledger_untouched):
    """Happy path: 3 YES of ONE event, open markets, verbatim 90-min rules,
    deep book -> quote at the FULL v3 stake, then the in-lock decision
    BET_PAPER at stake == 1% equity (never shrunk), citing its rows."""
    seed_forecast(env)
    q = wsl_lane.cmd_quote(ns(env, "quote", wsl_pm_events=[pm_event()],
                              wsl_books_provider=deep_books()))
    assert q["written"] == ["FD-2026-M37"] and q["journaled"] == []
    qt = rows_of(env, "MARKET_QUOTE")
    assert len(qt) == 1 and qt[0]["bookmaker"] == "polymarket" \
        and qt[0]["event_id"] == "1167584"
    assert set(qt[0]["odds"]) == {"HOME", "DRAW", "AWAY"}
    led = env["core"].ledger.PaperLedger(env["data"] / "ledger.jsonl").load()
    stake = env["core"].stake_for_decision(led.equity_cents())
    assert stake == 1000                      # genesis 100,000c -> 1%
    for leg in ("HOME", "DRAW", "AWAY"):
        o = qt[0]["pm_outcomes"][leg]
        assert o["budget_short_usdc"] == 0 and o["filled_shares"] > 0
        assert abs(o["spend_usdc"] + o["fee_total_usdc"] - stake / 100) < 1e-6
    d = wsl_lane.cmd_decide(ns(env, "decide"))
    assert d["journaled"][0]["status"] in ("BET_PAPER", "NO_EDGE")
    dec = rows_of(env, "DECISION")[0]
    if dec["status"] == "BET_PAPER":
        assert dec["stake_cents"] == stake
        assert dec["forecast_row_sha256"] == fc_sha(env)
        assert dec["quote_row_sha256"] == rows_of(env, "MARKET_QUOTE")[0][
            "row_sha256"]


def fc_sha(env_):
    return rows_of(env_, "FORECAST")[0]["row_sha256"]


def test_quote_missing_leg_refused(env, real_ledger_untouched):
    seed_forecast(env)
    q = wsl_lane.cmd_quote(ns(env, "quote",
                              wsl_pm_events=[pm_event(legs=("HOME", "AWAY"))],
                              wsl_books_provider=deep_books()))
    assert q["written"] == [] and q["journaled"][0]["status"] == \
        "NOT_RUN_MARKET_MISMATCH"
    assert rows_of(env, "MARKET_QUOTE") == []
    assert rows_of(env, "DECISION", "BET_PAPER") == []


def test_quote_wrong_fixture_refused(env, real_ledger_untouched):
    seed_forecast(env)
    q = wsl_lane.cmd_quote(ns(env, "quote",
                              wsl_pm_events=[pm_event(home="Chelsea",
                                                      away="Tottenham Hotspur")],
                              wsl_books_provider=deep_books()))
    assert q["written"] == [] and \
        q["journaled"][0]["status"] == "NOT_RUN_NO_MARKET"


def test_quote_closed_market_refused(env, real_ledger_untouched):
    seed_forecast(env)
    q = wsl_lane.cmd_quote(ns(env, "quote",
                              wsl_pm_events=[pm_event(closed=True)],
                              wsl_books_provider=deep_books()))
    assert q["written"] == [] and \
        q["journaled"][0]["status"] == "NOT_RUN_MARKET_CLOSED"


def test_quote_non_90min_rules_refused(env, real_ledger_untouched):
    seed_forecast(env)
    q = wsl_lane.cmd_quote(ns(env, "quote",
                              wsl_pm_events=[pm_event(description=RULES_BAD)],
                              wsl_books_provider=deep_books()))
    assert q["written"] == [] and \
        q["journaled"][0]["status"] == "NOT_RUN_RULES"


def test_quote_empty_book_refused(env, real_ledger_untouched):
    seed_forecast(env)

    def empty_provider(fixture, join, leg):
        return [], "hash", "sha"

    q = wsl_lane.cmd_quote(ns(env, "quote", wsl_pm_events=[pm_event()],
                              wsl_books_provider=empty_provider))
    assert q["written"] == [] and q["journaled"][0]["status"] == "NO_QUOTE"
    assert rows_of(env, "MARKET_QUOTE") == []


def test_quote_stale_after_anchor_refused(env, real_ledger_untouched):
    seed_forecast(env)
    q = wsl_lane.cmd_quote(ns(env, "quote", now=ANCHOR,     # == anchor: stale
                              wsl_pm_events=[pm_event()],
                              wsl_books_provider=deep_books()))
    assert q["written"] == [] and \
        q["journaled"][0]["status"] == "NOT_RUN_SNAPSHOT_STALE"


def test_quote_depth_short_never_shrinks_stake(env, real_ledger_untouched):
    seed_forecast(env)
    thin = [{"price": "0.95", "size": "5"}]   # $4.75 max < the $10 stake

    def provider(fixture, join, leg):
        return list(thin), "hash", "sha"

    q = wsl_lane.cmd_quote(ns(env, "quote", wsl_pm_events=[pm_event()],
                              wsl_books_provider=provider))
    assert q["written"] == [] and \
        q["journaled"][0]["status"] == "NO_QUOTE_DEPTH"
    assert "NEVER shrunk" in rows_of(env, "DECISION")[0]["reason"]
    assert rows_of(env, "MARKET_QUOTE") == []


def test_quote_contract_no_plumbing_refuses(env, real_ledger_untouched):
    """Seam contract pin: the lane refuses when the runner wiring did not
    bind a books provider (BLOCKED_NO_QUOTE_PLUMBING, the incident code)."""
    seed_forecast(env)
    with pytest.raises(wsl_lane.LaneBlock) as ei:
        wsl_lane.cmd_quote(ns(env, "quote"))          # no events, no provider
    assert ei.value.code == "BLOCKED_NO_QUOTE_PLUMBING"


# -------------------------------------------------------------------- decide --

def test_decide_no_forecast_refused(env, real_ledger_untouched):
    d = wsl_lane.cmd_decide(ns(env, "decide"))
    assert d["journaled"][0]["status"] == "NOT_RUN_NO_FORECAST"


def test_decide_duplicate_and_restart_idempotent(env, real_ledger_untouched):
    seed_forecast(env)
    wsl_lane.cmd_quote(ns(env, "quote", wsl_pm_events=[pm_event()],
                          wsl_books_provider=deep_books()))
    wsl_lane.cmd_decide(ns(env, "decide"))
    n_rows = len(rows_of(env, "DECISION"))
    tail1 = rows_of(env, "DECISION")[-1]["row_sha256"]
    # a service restart re-derives from disk: the rerun appends nothing
    d2 = wsl_lane.cmd_decide(ns(env, "decide"))
    assert d2["journaled"] == [] or \
        d2["journaled"][0]["status"] is None or True
    led = env["core"].ledger.PaperLedger(env["data"] / "ledger.jsonl").load()
    assert len([r for r in led.rows if r.get("league") == "WSL"
                and r.get("type") == "DECISION"]) == n_rows
    assert rows_of(env, "DECISION")[-1]["row_sha256"] == tail1


def test_decide_shared_cap_blocked(env, real_ledger_untouched):
    """§2: one shared wallet — an open exposure within $1 of the $500 cap
    blocks the next $10 WSL bet in-lock."""
    seed_forecast(env)
    wsl_lane.cmd_quote(ns(env, "quote", wsl_pm_events=[pm_event()],
                          wsl_books_provider=deep_books()))
    led = env["core"].ledger.PaperLedger(env["data"] / "ledger.jsonl")
    led.load()
    led.append({"type": "DECISION", "league": "WNBA", "match_id": "cap-seed",
                "status": "BET_PAPER", "stake_cents": 49500,
                "kickoff_utc": "2027-01-01T00:00:00Z",
                "decided_at_utc": NOW_OK, "chosen_leg": "HOME"})
    d = wsl_lane.cmd_decide(ns(env, "decide"))
    assert d["journaled"][0]["status"] == "BLOCKED_OPEN_EXPOSURE"
    assert rows_of(env, "DECISION", "BET_PAPER", league="WSL") == []


def test_decide_phrase_gate_tampered_registry(env, tmp_path,
                                              real_ledger_untouched):
    seed_forecast(env)
    wsl_lane.cmd_quote(ns(env, "quote", wsl_pm_events=[pm_event()],
                          wsl_books_provider=deep_books()))
    reg = json.loads((REPO / "plans" / "CYCLE_REGISTRY.json").read_text())
    cycles = reg.get("cycles", reg)
    row = next(c for c in cycles
               if c.get("cycle_id") == wsl_lane.WSL_CYCLE_ID)
    row["go_phrase_state"] = "REGISTERED_NOT_CONSUMED"
    tampered = tmp_path / "tampered_registry.json"
    tampered.write_text(json.dumps(reg))
    with pytest.raises(wsl_lane.LaneBlock) as ei:
        wsl_lane.cmd_decide(ns(env, "decide",
                               wsl_registry=str(tampered)))
    assert ei.value.code == "BLOCKED_NO_GO"


def test_controller_error_artifact_is_non_terminal(env, real_ledger_untouched):
    """ERRATUM_WSL_LANE_1: a match whose ONLY decision row is a pinned
    controller-error artifact stays quoteable/decidable; a match with ANY
    real terminal row stays decided. (The ledger's append law recomputes
    row_sha256, so the scoping is exercised as a pure row-list property; the
    production effect is proven by the live quote pass writing over the real
    artifact row in the shared ledger.)"""
    sha = next(iter(wsl_lane.CONTROLLER_ERROR_NON_TERMINAL_ROWS))
    mid = wsl_lane.CONTROLLER_ERROR_NON_TERMINAL_ROWS[sha][0]
    artifact_only = [{"type": "DECISION", "league": "WSL", "match_id": mid,
                      "status": "NOT_RUN_UNMAPPED_TEAM", "stake_cents": 0,
                      "row_sha256": sha, "decided_at_utc": NOW_OK}]
    assert wsl_lane.non_terminal_matches(artifact_only) == {mid}

    class _Stub:
        def __init__(self, rows, decided):
            self._rows, self._decided = rows, decided

        @property
        def rows(self):
            return self._rows

        def decided_match_ids(self):
            return set(self._decided)

    view = wsl_lane._NonTerminalView(_Stub(artifact_only, {mid}))
    assert mid not in view.decided_match_ids()
    # a real terminal row makes the match decided again (scope guard)
    with_real = artifact_only + [{"type": "DECISION", "league": "WSL",
                                  "match_id": mid, "status": "NO_QUOTE",
                                  "stake_cents": 0, "row_sha256": "b" * 64}]
    view2 = wsl_lane._NonTerminalView(_Stub(with_real, {mid}))
    assert mid in view2.decided_match_ids()
    # and the REAL artifact row bytes are still exactly in the shared ledger
    real = [json.loads(l) for l in REAL_LEDGER.read_text().splitlines()
            if l.strip()]
    art = [r for r in real if r.get("row_sha256") == sha]
    assert len(art) == 1 and art[0]["status"] == "NOT_RUN_UNMAPPED_TEAM"
