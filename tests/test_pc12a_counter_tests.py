"""PC12A verification battery §8 counter-tests -- prove the DETECTORS
work, not just that the current outputs are clean.

Battery 4 (RGC-INC-1 hardening): the dry-run self-grep leak scan is fed a
deliberately POISONED report ('net_pnl') and must FAIL; each forbidden key
individually trips the scan; and the full CLI gate is counter-tested end
to end -- a journal row carrying a forbidden field makes run_dry exit 2.

Battery 5 (reconciliation counter-test): a synthetic journal with NET_ORDER
cost rows gets ONE tampered cost field (a flipped byte); the hash-chain
verifier must catch it (row digest mismatch) AND the independent
spread/slip/cross-cost identity plus the books decomposition invariant
must break too -- two unrelated detectors, same tamper.

No PnL value is ever computed or asserted: the poisons are synthetic
strings injected into copies, and every numeric assertion is on COST
fields and chain digests only.
"""

import datetime as dt
import json
import pathlib
import shutil

import pytest

from research.pc12a import books
from research.pc12a import journal as jr
from research.pc12a import legs as _legs
from research.pc12a import panels as _panels
from research.pc12a import run_dry as rd

UTC = dt.timezone.utc
WORKTREE = pathlib.Path(__file__).resolve().parent.parent
PYTHON = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
REAL_LEGS_DIR = WORKTREE / "research" / "pc12a" / "legs_config"
SMOKE = WORKTREE / "research" / "pc12a" / "smoke_dry_run"


# ---------------------------------------------------------------------------
# Battery 4: leak-scan hardening (poisoned-report counter-tests)
# ---------------------------------------------------------------------------


def _clean_report_shape() -> dict:
    """A schema-correct dry-run report skeleton with ONLY lawful fields."""
    return {
        "schema": rd.REPORT_SCHEMA,
        "cycle_id": "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1",
        "run_id": "0" * 16,
        "window": {"start": "2024-06-05", "end": "2024-06-18"},
        "tier": 1.0,
        "legs": {"VC1-VAEDGE-EURUSD": {
            "decisions": 12, "votes": {"1": 4, "0": 8},
            "fills_by_outcome": {"FILLED": 4},
            "outcome_exposed_label": "CLASS_CANDIDATE_ANCESTRY_RHO_LABELLED",
            "family_id": "VOLPROF-M1-VAEDGE", "mech_key": "vc1_vaedge",
            "symbol": "EURUSD"}},
        "cost_bill_totals_usd": {"spread_once": 40.0, "slip": 0.0,
                                 "slip_gap_excess": 0.0, "commission": 7.0,
                                 "swap": 3.0},
        "blocked_reason_histogram": {"NETTED_TO_ZERO": 2},
        "journal_row_count": 30,
        "elapsed_seconds": 0.5,
        "code_digest": "0" * 64,
        "data_digests": {"EURUSD": "0" * 64},
        "notes": ["counts and cost bills only"],
    }


def test_leak_scan_fails_on_poisoned_net_pnl_report():
    """THE battery-4 law: a report containing 'net_pnl' must FAIL the
    self-grep (proves the scanner works, not just that today's output is
    clean)."""
    poisoned = _clean_report_shape()
    poisoned["net_pnl"] = 1234.56        # the deliberate poison
    text = json.dumps(poisoned, sort_keys=True)   # exactly how main() does
    scan = rd.leak_scan(text)
    assert scan["clean"] is False
    assert "pnl" in scan["keys"]          # compound keys trip the substring


@pytest.mark.parametrize("key", rd.FORBIDDEN_KEYS)
def test_each_forbidden_key_trips_the_scan(key):
    poisoned = _clean_report_shape()
    poisoned[f"some_{key}_field"] = 1.0
    scan = rd.leak_scan(json.dumps(poisoned, sort_keys=True))
    assert scan["clean"] is False and key in scan["keys"]


def test_clean_report_control_scans_clean():
    scan = rd.leak_scan(json.dumps(_clean_report_shape(), sort_keys=True))
    assert scan["clean"] is True and scan["keys"] == []
    # compound cost field names must NOT false-positive
    ok = rd.leak_scan('{"spread_once_usd": 1.0, "slip_gap_excess": 0.0,'
                      ' "cost_bill_totals_usd": {"commission": 2.0}}')
    assert ok["clean"] is True


def test_poisoned_journal_file_scans_dirty(tmp_path):
    """main() reads the journal back from disk before its final gate; a
    poisoned journal FILE (not just an in-memory dict) must trip it."""
    p = tmp_path / "journal.jsonl"
    p.write_text('{"row_kind": "NET_ORDER", "net_pnl": 9.9}\n')
    scan = rd.leak_scan(p.read_text())
    assert scan["clean"] is False and "pnl" in scan["keys"]


def test_committed_smoke_artifacts_scan_clean():
    """Control on the real committed artifacts (the impl lane's smoke run):
    both the report and the journal stay clean under the same scanner."""
    if not (SMOKE / "DRY_RUN_REPORT.json").exists():
        pytest.skip("smoke artifacts not present in this checkout")
    report_text = (SMOKE / "DRY_RUN_REPORT.json").read_text()
    journal_text = (SMOKE / "journal.jsonl").read_text()
    assert rd.leak_scan(journal_text, report_text)["clean"] is True


# ---------------------------------------------------------------------------
# Battery 4 (end to end): the CLI gate itself fails a poisoned run
# ---------------------------------------------------------------------------


def _tiny_synthetic_env(tmp_path: pathlib.Path):
    root = tmp_path / "panels"
    sym = "EURUSD"
    for side in ("BID", "ASK"):
        (root / sym / side).mkdir(parents=True)
    d = dt.date(2024, 5, 1)
    while d <= dt.date(2024, 6, 18):
        vol = _panels.synthetic_day_bytes(
            sym, d, mid_level=1.0850, vol_pattern=(
                None if d.weekday() < 5
                else __import__("numpy").zeros(
                    _panels.RECORDS_PER_DAY)),
            seed=d.toordinal() * 10)
        (root / sym / "BID" / f"{d.isoformat()}.bi5").write_bytes(vol[0])
        (root / sym / "ASK" / f"{d.isoformat()}.bi5").write_bytes(vol[1])
        d += dt.timedelta(days=1)
    legs_dir = tmp_path / "legs"
    legs_dir.mkdir()
    for cfg in _legs.load_leg_configs(str(REAL_LEGS_DIR)):
        if cfg["symbol"] == sym and cfg["sleeve_id"] == "POOL_B_VOLPROF":
            (legs_dir / f"{cfg['class_candidate_id']}.json").write_text(
                json.dumps(cfg))
    import os
    env = dict(os.environ)
    env["PC12A_PANEL_ROOTS"] = json.dumps({sym: str(root / sym)})
    return env, str(legs_dir)


def test_cli_exits_2_when_a_journal_row_carries_a_forbidden_field(
        tmp_path, monkeypatch):
    """Counter-test of the RGC-INC-1 RUN gate: poison the journal at the
    source (net_order_row gains a forbidden field) and the CLI must print
    the violation and return 2 -- the same gate the real run relies on."""
    env, legs = _tiny_synthetic_env(tmp_path)
    monkeypatch.setenv("PC12A_PANEL_ROOTS", env["PC12A_PANEL_ROOTS"])
    real_builder = jr.net_order_row

    def poisoned_builder(**kw):
        row = real_builder(**kw)
        row["net_pnl"] = 0.0            # the poison
        return row

    monkeypatch.setattr(jr, "net_order_row", poisoned_builder)
    out = str(tmp_path / "out_poisoned")
    rc = rd.main(["--legs", legs, "--window", "2024-06-05,2024-06-18",
                  "--out", out])
    assert rc == 2, "the CLI must FAIL a run whose journal carries PnL"
    poisoned_journal = (pathlib.Path(out) / "journal.jsonl").read_text()
    assert "net_pnl" in poisoned_journal
    assert rd.leak_scan(poisoned_journal)["clean"] is False


# ---------------------------------------------------------------------------
# Battery 5: reconciliation counter-test (tampered cost field)
# ---------------------------------------------------------------------------


def _write_cost_journal(path: pathlib.Path, n_orders=4) -> list:
    """A small synthetic journal of NET_ORDER rows whose cost fields
    satisfy the spread-once identity (spread + slip == cross_cost), plus
    SWAP rows.  Returns the rows as written."""
    import hashlib
    rows = []
    with jr.JournalWriter(str(path), "tamper-test") as jw:
        for i in range(n_orders):
            spread = 3.0 + i
            slip = 0.5
            row = jr.net_order_row(
                order_id=f"EURUSD-o{i:05d}", order_kind="OPEN",
                ts_fill_utc=f"2024-06-0{i + 1}T14:0{i}:00Z",
                symbol="EURUSD", side="buy" if i % 2 == 0 else "sell",
                delta_units=10_000, fill_price=1.0840 + i * 1e-4,
                quoted_side=1.0840 + i * 1e-4, mid_at_fill=1.0839,
                spread_once_usd=spread, slip_beyond_halfspread_usd=slip,
                cross_cost_usd=spread + slip,      # identity holds
                commission_usd=0.35, cell_id="C1",
                u3_band_id="U3_NON_EVENT", venue_model="PANEL_DUKA",
                units_after=(i + 1) * 10_000 * (1 if i % 2 == 0 else -1),
                contributing_legs=[{"leg_id": f"L{i}", "vote": 1,
                                    "contribution_units": 10_000}])
            rows.append(jw.write("NET_ORDER", row))
        rows.append(jw.write("SWAP", jr.swap_row(
            ts_utc="2024-06-04T22:00:00Z", symbol="EURUSD",
            weekday_utc="tuesday", units_abs=10_000, multiplier=1,
            swap_usd=1.25, wed_x3=False, units_after=10_000)))
    return rows


def _rewrite(path: pathlib.Path, rows: list) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True,
                                separators=(",", ":")) + "\n")


def test_untampered_control_chain_and_identities_hold(tmp_path):
    p = tmp_path / "journal.jsonl"
    _write_cost_journal(p)
    assert jr.verify_chain(str(p))["ok"] is True
    for r in jr.read_rows(str(p)):
        if r["row_kind"] == "NET_ORDER":
            assert abs((r["spread_once_usd"]
                        + r["slip_beyond_halfspread_usd"])
                       - r["cross_cost_usd"]) < 1e-12


def test_tampered_cost_field_caught_by_chain_and_by_identity(tmp_path):
    """Flip ONE byte in ONE cost field (spread_once_usd 3.0 -> 8.0 in the
    first order).  Two INDEPENDENT detectors must both catch it:
    (a) the hash chain (row digest mismatch), and
    (b) the spread-once / cross-cost reconciliation identity.
    """
    p = tmp_path / "journal.jsonl"
    _write_cost_journal(p)
    rows = jr.read_rows(str(p))
    first_order = next(i for i, r in enumerate(rows)
                       if r["row_kind"] == "NET_ORDER")
    rows[first_order]["spread_once_usd"] = 8.0   # the single tampered byte
    _rewrite(p, rows)
    res = jr.verify_chain(str(p))
    assert res["ok"] is False
    assert res["reason"] == "row_sha256 mismatch (field tampered)"
    tampered = jr.read_rows(str(p))[first_order]
    assert abs((tampered["spread_once_usd"]
                + tampered["slip_beyond_halfspread_usd"])
               - tampered["cross_cost_usd"]) > 4.0   # identity broken


def test_tampered_header_meta_now_detected(tmp_path):
    """Counter-test for the verifier hardening: adding/changing a field on
    the HEADER row (e.g. the run meta) must break verification now that
    the header self-hash is recomputed (previously it rooted the chain on
    faith and a tampered header went undetected)."""
    p = tmp_path / "journal.jsonl"
    _write_cost_journal(p)
    rows = jr.read_rows(str(p))
    assert rows[0]["row_kind"] == "HEADER"
    rows[0]["meta"]["legs_digest"] = "0" * 64    # forged identity
    _rewrite(p, rows)
    res = jr.verify_chain(str(p))
    assert res["ok"] is False
    assert res["first_bad_seq"] == 0


def test_tampered_last_row_still_detected(tmp_path):
    """Tampering the FINAL row (no later rows to propagate onto) is still
    caught by its own self-hash."""
    p = tmp_path / "journal.jsonl"
    _write_cost_journal(p)
    rows = jr.read_rows(str(p))
    rows[-1]["swap_usd"] = 999.0            # the SWAP row is last
    _rewrite(p, rows)
    assert jr.verify_chain(str(p))["ok"] is False


def test_raw_byte_flip_in_file_detected(tmp_path):
    """Byte-level tamper WITHOUT re-serialization (same file length, one
    character changed in the raw text) is caught too."""
    p = tmp_path / "journal.jsonl"
    _write_cost_journal(p)
    text = p.read_text()
    assert '"spread_once_usd":3.0' in text
    p.write_text(text.replace('"spread_once_usd":3.0',
                              '"spread_once_usd":9.0', 1))
    res = jr.verify_chain(str(p))
    assert res["ok"] is False
    assert res["first_bad_seq"] is not None


def test_books_decomposition_breaks_under_cost_tamper():
    """The FILL_ACCOUNTING_SPEC §6 invariant as a third detector: with the
    untampered costs the equity delta reconciles exactly; inflate the
    spread component by the tamper and the residual jumps."""
    gross = 100.0
    spread, slip, comm, swap = 4.0, 0.5, 0.35, 1.25
    eq_delta = gross - spread - slip - comm - swap
    assert abs(books.decomposition_residual(
        gross, spread, slip, comm, swap, eq_delta)) < 1e-9
    tampered_residual = books.decomposition_residual(
        gross, 9.0, slip, comm, swap, eq_delta)   # spread 4.0 -> 9.0
    assert abs(tampered_residual) > 4.0
