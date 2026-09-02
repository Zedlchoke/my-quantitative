
import sys, json
sys.path.insert(0, r"C:\Users\ROYAL\exec-v10-R1c")
from research.panel import build_daily_closes
import yaml, pandas as pd
syms = yaml.safe_load(open("config/research_scan_top20.yaml"))
symbols = list(syms["market"]["symbols"])
closes = build_daily_closes("catalog_live_crypto", symbols, "2025-08-21T00:00:00Z", "2026-08-21T00:00:00Z")
frame = pd.DataFrame({s: pd.Series([c for _, c in v]) for s, v in closes.items()})
rets = frame.pct_change()
ranks = rets.rank(axis=1)
print(json.dumps({"symbols": len(closes), "rows": int(len(frame)), "rank_cols": int(ranks.shape[1])}))
