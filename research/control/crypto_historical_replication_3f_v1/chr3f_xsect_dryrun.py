"""CHR3F XSECT sanitized dry-run (DR2): real frozen identity shape
(H-XSECT-FUNDING-CARRY-v1 universe) + deterministic synthetic panel.
No real PnL anywhere: prices/funding are synthetic by construction; outputs
land in the cycle namespace under DRYRUN experiment ids. hypothesis-dir is a
DISCLOSED COPY of the frozen candidate with locked_at_utc = the CHR3F A2
owner-instruction stamp (the original files have locked_at_utc: null; the V6
lock lived in the lost launch bundle)."""
from __future__ import annotations
import json, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

R = Path("/Users/hoangminhlong/my-quantitative")
CD = R / ".worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1"
V6 = CD / "recovered/v6_root"
RUN = CD / "chr3f_xsect_run"
PY = R / ".venv/bin/python"
A2_LOCK = "2026-09-23T10:40:00Z"

SYMS = ["ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","LINKUSDT","ADAUSDT"]

def build_workspace() -> Path:
    if RUN.exists():
        shutil.rmtree(RUN)
    (RUN / "config").mkdir(parents=True)
    (RUN / "config/research_baseline_altcoin.yaml").write_text("backtest:\n  fee_model: stub\n")
    hyp = RUN / "research/hypotheses/H-XSECT-FUNDING-CARRY-v1"
    hyp.mkdir(parents=True)
    cand = (R / "research/hypotheses/H-XSECT-FUNDING-CARRY-v1/candidate.yaml").read_text()
    cand = cand.replace("locked_at_utc: null", f'locked_at_utc: "{A2_LOCK}"')
    (hyp / "candidate.yaml").write_text(cand)
    (hyp / "DISCLOSED_COPY_NOTE.txt").write_text(
        "CHR3F dry-run copy of the frozen candidate.yaml; ONLY locked_at_utc "
        f"populated with the CHR3F A2 owner-instruction stamp {A2_LOCK} "
        "(original frozen file has locked_at_utc: null; the V6-era lock value "
        "lived in the lost launch bundle). No other field changed.\n")
    dc = RUN / "results/matrix/data_contract_v2"
    dc.mkdir(parents=True)
    (dc / "data_contract_v2.json").write_text('{"schema_version": 2}')
    return RUN

def build_spec() -> dict:
    # deterministic synthetic panel: real universe, flat prices, known funding
    bars, funding = [], []
    days = ["2021-01-05", "2021-01-06", "2021-01-07", "2021-01-08"]
    closes = {s: 100.0 + i for i, s in enumerate(SYMS)}
    for day in days:
        for hhmm in ("00:15", "00:30"):
            ts = f"{day}T{hhmm}:00Z"
            for s in SYMS:
                bars.append({"symbol": s, "ts": ts, "open": closes[s], "high": closes[s],
                             "low": closes[s], "close": closes[s], "volume": 1.0})
            bars.append({"symbol": "BTCUSDT", "ts": ts, "open": 100.0, "high": 100.0,
                         "low": 100.0, "close": 100.0, "volume": 1.0})
    for i, s in enumerate(SYMS):
        funding.append({"symbol": s, "funding_time_ms": 1609948800000 + i,
                        "fundingRate": "0.0001" if i % 2 == 0 else "-0.0002"})
    return {
        "traded_symbols": SYMS, "benchmark_symbol": "BTCUSDT",
        "initial_capital": 100000.0, "fee_taker": 0.0005, "slippage_ticks": 1,
        "tick_size": {"*": 0.01}, "step_size": {"*": 0.001}, "min_notional": 5.0,
        "bars": bars, "funding": funding,
        "targets": {"longs": [["ETHUSDT", 0.15], ["BNBUSDT", 0.15]],
                    "shorts": [["DOGEUSDT", -0.15], ["ADAUSDT", -0.15]]},
    }

def main() -> int:
    ws = build_workspace()
    spec = build_spec()
    (ws / "chr3f_dr2_panel.json").write_text(json.dumps(spec))
    argv = [str(PY), str(V6 / "research/portfolio_runner.py"),
            "--experiment-id", "CHR3F-XSECT-DRYRUN-DR2",
            "--lookback-days", "7",
            "--window-start", "2021-01-05T00:00Z",
            "--window-end", "2021-01-08T00:00Z",
            "--folds", "3",
            "--matrix-id", "chr3f_dryrun",
            "--registry-path", "results/registry/chr3f_dryrun.jsonl",
            "--hypothesis-dir", str(ws / "research/hypotheses/H-XSECT-FUNDING-CARRY-v1"),
            "--synthetic-panel", str(ws / "chr3f_dr2_panel.json"),
            "--output-root", str(ws / "results/chr3f_dryrun")]
    import os
    env = dict(os.environ, PYTHONPATH=str(V6))
    r = subprocess.run(argv, cwd=str(ws), capture_output=True, text=True, env=env)
    log = ws / "dr2_runner.log"
    log.write_text(r.stdout + "\n" + r.stderr)
    print("rc:", r.returncode)
    tail = [l for l in (r.stdout + r.stderr).splitlines() if l][-6:]
    print("\n".join(tail))
    exp = ws / "results/chr3f_dryrun/CHR3F-XSECT-DRYRUN-DR2"
    artifacts = sorted(p.name for p in exp.glob("*")) if exp.exists() else []
    print("artifacts:", artifacts[:14])
    verdict = {"utc": datetime.now(timezone.utc).isoformat(), "rc": r.returncode,
               "artifacts": artifacts, "universe": SYMS, "lock_stamp": A2_LOCK,
               "namespace": "CHR3F-XSECT-DRYRUN-DR2 (synthetic panel; not scored)"}
    (CD / "xsect_dryrun_dr2_verdict.json").write_text(json.dumps(verdict, indent=1))
    return 0 if r.returncode == 0 and artifacts else 1

if __name__ == "__main__":
    sys.exit(main())
