"""PhorecOne (gate A) — tests for the ONE-account two-sleeve read model."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import portfolio_lib as pl  # noqa: E402
from one import read_model as rm  # noqa: E402


def _state():
    return rm.build_one_state()


# ---------- mount law ----------
def test_exactly_two_sleeves_mounted():
    s = _state()
    assert set(s["sleeves"]) == {"FX-RANGEFADE-2M", "BTC4H-BANDRIDGE"}


def test_no_auto_mount_unknown_sleeve_fails_closed():
    cfg = json.loads((HERE / "epoch_config.json").read_text())
    cfg["adapters"]["registry_default"] = ["FX-RANGEFADE-2M", "GHOST"]
    try:
        rm.mount_adapters(cfg)
        raise AssertionError("unknown sleeve mounted silently")
    except ValueError as exc:
        assert "GHOST" in str(exc)


def test_adapter_registry_has_no_discovery():
    cfg = json.loads((HERE / "epoch_config.json").read_text())
    assert cfg["adapters"]["auto_mount"] is False


# ---------- single-account accounting ----------
def test_default_config_is_activated():
    """Epoch-2 was activated 2026-09-25T05:07:30Z by owner instruction —
    the default config must serve ACTIVE with the $100k baseline."""
    s = _state()
    assert s["mode"] == "ACTIVE"
    assert s["activation_ts_utc"] == "2026-09-25T05:07:30Z"
    assert s["account"]["epoch2"]["status"] in ("ACTIVE", "ACTIVE_PARTIAL")
    assert s["account"]["epoch2"]["opening_equity_usd_eq"] == 100000.0
    assert s["account"]["epoch2"]["pnl_total"] is not None


def test_pending_config_stays_inert(tmp_path):
    """A PENDING config (the pre-activation state) must never produce
    epoch-2 numbers — pinned with an explicit fixture, independent of the
    live config's status."""
    base = json.loads((HERE / "epoch_config.json").read_text())
    base["status"] = "PENDING_OWNER_GO"
    p = tmp_path / "pending.json"
    p.write_text(json.dumps(base))
    s = rm.build_one_state(p)
    assert s["mode"] == "PREVIEW"
    assert s["account"]["epoch2"]["status"] == "NOT_ACTIVATED"
    assert s["account"]["epoch2"]["pnl_total"] is None
    assert s["account"]["opening_equity_usd_eq"] == 100000.0


def test_usdt_ref_is_declared_and_labeled():
    s = _state()
    ref = s["account"]["usdt_usd_ref"]
    assert ref["rate"] == 1.0
    assert "GIẢ ĐỊNH BÁO CÁO" in ref["label"]
    # gross exposure joins the two books ONLY through the declared ref
    fx = s["account"]["fx_gross_usd"]
    br = s["account"]["bandridge_gross_usdt"]
    assert abs(s["account"]["gross_exposure_usd_eq"] - (fx + br * ref["rate"])) < 0.01


def test_build_one_state_deterministic():
    a = json.dumps(_state(), sort_keys=True, default=str)
    b = json.dumps(_state(), sort_keys=True, default=str)
    assert a == b


# ---------- reconciliation: equity ↔ calendar ↔ trades ----------
def test_fx_calendar_matches_journal_total():
    s = _state()
    fx_sum = sum(d["sleeves"]["FX-RANGEFADE-2M"]["day_realized_usd"]
                 for d in s["history_days"])
    rep = pl.fx_replay(pl.FX_DIR / "shadow_journal.jsonl")
    assert abs(fx_sum - rep["realized_usd"]) < 0.01
    closed = s["sleeves"]["FX-RANGEFADE-2M"]["closed_trades"]
    assert abs(sum(t["pnl_usd"] for t in closed) - rep["realized_usd"]) < 0.01


def test_bandridge_calendar_matches_equity_delta():
    s = _state()
    marks = pl.read_jsonl(pl.PSV1_RESULTS /
                          "valuation_marks/BTC4H-BANDRIDGE.jsonl")
    stampeds = [m["equity"] for m in marks
                if (str(m.get("mark_timestamp_utc")
                        or m.get("observed_at_utc") or ""))
                and isinstance(m.get("equity"), (int, float))]
    day_sum = sum((d["sleeves"]["BTC4H-BANDRIDGE"].get("day_pnl") or 0.0)
                  for d in s["history_days"])
    assert abs(day_sum - (stampeds[-1] - stampeds[0])) < 0.05


# ---------- open positions / restart idempotence / missing data ----------
def test_open_positions_shapes():
    s = _state()
    for sid in ("FX-RANGEFADE-2M", "BTC4H-BANDRIDGE"):
        for p in s["sleeves"][sid]["open_positions"]:
            if sid == "FX-RANGEFADE-2M":
                assert {"pair", "side", "lots", "entry_px"} <= set(p)
            else:
                assert {"symbol", "side", "qty", "notional_usdt"} <= set(p)


def test_fx_replay_survives_duplication(tmp_path):
    src = pl.FX_DIR / "shadow_journal.jsonl"
    lines = src.read_text().splitlines()
    dup = tmp_path / "dup.jsonl"
    dup.write_text("\n".join(lines + lines) + "\n")
    a = rm.FxAdapter(json.loads((HERE / "epoch_config.json").read_text()),
                     journal_path=src)
    b = rm.FxAdapter(json.loads((HERE / "epoch_config.json").read_text()),
                     journal_path=dup)
    assert a.replay()["trades"] == b.replay()["trades"]
    assert a.replay()["realized_usd"] == b.replay()["realized_usd"]


def test_missing_bandridge_mark_day_is_not_zero(tmp_path):
    cfg = json.loads((HERE / "epoch_config.json").read_text())
    m = tmp_path / "br.jsonl"
    rows = [
        {"mark_timestamp_utc": "2026-09-20T23:55:00Z", "equity": 100000.0,
         "status": "FLAT_OK", "positions": []},
        {"mark_timestamp_utc": "2026-09-22T23:55:00Z", "equity": 100010.0,
         "status": "RUNNING", "positions": []},
    ]
    m.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    ad = rm.BandridgeAdapter(cfg, marks_path=m)
    series = ad.daily()
    # the day BETWEEN the two marks (09-21) never appears as $0 anywhere
    days = [r["day_utc"] for r in series["rows"]]
    assert "2026-09-21" not in days
    assert series["rows"][1]["status"] == "GAP_SPAN"  # Δ spans the gap, labelled


def test_bandridge_pending_from_state(tmp_path):
    cfg = json.loads((HERE / "epoch_config.json").read_text())
    st = tmp_path / "state.json"
    st.write_text(json.dumps({"pending": {"target": 1.0}, "position": 0.0}))
    ad = rm.BandridgeAdapter(cfg, state_path=st)
    assert ad.pending_orders() == [{"raw": {"target": 1.0}}]
    st.write_text(json.dumps({"pending": None}))
    assert rm.BandridgeAdapter(cfg, state_path=st).pending_orders() == []


# ---------- activation gate ----------
def test_activation_fail_closed_and_epoch2_from_tstar(tmp_path):
    base = json.loads((HERE / "epoch_config.json").read_text())
    bad = dict(base, status="ACTIVE", activation_ts_utc=None,
           open_position_law="PENDING_OWNER", rule_digest=None,
           review_log_sha256=None,
           allocation=dict(base["allocation"], mode="OWNER_DECISION"))
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(bad))
    s = rm.build_one_state(p)
    assert s["mode"] == "PREVIEW_FORCED" and s["activation_error"]

    good = dict(base, status="ACTIVE", activation_ts_utc="2099-01-01T00:00:00Z",
                open_position_law="FLAT_START",
                allocation=dict(base["allocation"], mode="EQUAL_2WAY"),
                rule_digest="x", review_log_sha256="y")
    p.write_text(json.dumps(good))
    s = rm.build_one_state(p)
    assert s["mode"] == "ACTIVE"
    e2 = s["account"]["epoch2"]
    assert e2["status"] == "ACTIVE_PARTIAL"          # BR has no mark ≥ 2099 yet
    assert e2["pnl_total"] == 0.0                    # nothing countable yet
    assert e2["equity"] == 100000.0
    assert e2["sleeves"]["BTC4H-BANDRIDGE"]["status"] == "UNAVAILABLE"  # never $0-by-assumption


# ---------- safety ----------
def test_no_order_surface_in_one_app():
    banned = ["POST", "place_order", "submit_order", "send_order", "broker",
              "api.binance.com/api", "websocket order"]
    for f in [HERE / "one/serve_one.py", HERE / "one_app_entry.py"]:
        text = f.read_text().lower()
        for b in banned:
            assert b.lower() not in text, f"{f.name} contains banned token {b}"
        assert "do_post" not in text  # GET-only servers


# ---------- open-position-law attribution (review finding) ----------
def _cfg_active(tmp_path, law, ts="2026-09-25T00:00:00Z"):
    base = json.loads((HERE / "epoch_config.json").read_text())
    cfg = dict(base, status="ACTIVE", activation_ts_utc=ts,
               open_position_law=law,
               allocation=dict(base["allocation"], mode="EQUAL_2WAY"),
               rule_digest="x", review_log_sha256="y")
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg))
    return p


def test_epoch2_fx_attribution_respects_open_position_law(tmp_path):
    """All current FX closes happened 2026-09-24 (pre-T*). With T* after
    them, epoch-2 FX PnL must be 0 under either law — never re-booked."""
    p = _cfg_active(tmp_path, "FLAT_START", ts="2026-09-25T00:00:00Z")
    s = rm.build_one_state(p)
    assert s["account"]["epoch2"]["sleeves"]["FX-RANGEFADE-2M"]["pnl"] == 0.0
    assert s["account"]["epoch2"]["pnl_total"] == 0.0


def test_reopen_without_boundary_manifest_is_unavailable(tmp_path):
    """Synthetic carry: a close at/after T* whose open was before T* must
    NOT book its full pre-T* PnL into epoch-2; without a boundary manifest
    the carried part is UNAVAILABLE (ACTIVE_PARTIAL), never silently 0/old."""
    import portfolio_lib as pl
    j = tmp_path / "j.jsonl"
    rows = [
        {"event": "fill_open", "pair": "EURUSD", "dir": 1, "entry_px": 1.10,
         "entry_ts": 1790000000, "lots": 1.5, "ts": "2026-09-20T02:00:00+00:00"},
        {"event": "fill_close", "pair": "EURUSD", "dir": 1, "entry_px": 1.10,
         "exit_px": 1.12, "pnl_usd": 3000.0, "reason": "signal",
         "ts": "2026-09-26T02:00:00+00:00"},
    ]
    j.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    p = _cfg_active(tmp_path, "REOPEN_AT_MARK", ts="2026-09-25T00:00:00Z")
    cfg = json.loads(p.read_text())
    fx = rm.FxAdapter(cfg, journal_path=j)
    # no marks ≥ T* for BANDRIDGE either → its part UNAVAILABLE too
    br = rm.BandridgeAdapter(cfg, marks_path=tmp_path / "none.jsonl")
    e2 = rm._epoch2_two_sleeves(cfg, fx, br, fx.replay(), {"rows": []})
    sleeve = e2["sleeves"]["FX-RANGEFADE-2M"]
    assert sleeve["carried_status"] == "UNAVAILABLE"
    assert e2["status"] == "ACTIVE_PARTIAL"
    assert sleeve["pnl"] == 0.0          # carried part NOT booked (no manifest)
    assert e2["sleeves"]["BTC4H-BANDRIDGE"]["status"] == "UNAVAILABLE"


def test_epoch2_gated_on_valid_activation(tmp_path):
    """A PREVIEW_FORCED config with a T* must NOT compute epoch-2 numbers."""
    base = json.loads((HERE / "epoch_config.json").read_text())
    bad = dict(base, status="ACTIVE", activation_ts_utc="2099-01-01T00:00:00Z",
               open_position_law="PENDING_OWNER", rule_digest=None,
               review_log_sha256=None,
               allocation=dict(base["allocation"], mode="OWNER_DECISION"))
    # missing law/allocation/digest → forced preview even though T* exists
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(bad))
    s = rm.build_one_state(p)
    assert s["mode"] == "PREVIEW_FORCED"
    assert s["account"]["epoch2"]["status"] == "NOT_ACTIVATED"
    assert s["account"]["epoch2"]["pnl_total"] is None
