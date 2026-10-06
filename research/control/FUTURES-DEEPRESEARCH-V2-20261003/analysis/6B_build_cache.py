"""6B v2 stage 0 — build caches: outright 1m panel, contract registry,
annotated panel, session table, held-contract chains (calendar + volume
crossover), roll tables. Writes 6B_cache/*.parquet + 6B_build_report.json.

Lane DEEP-6B, FUTURES-DEEPRESEARCH-V2-20261003. Descriptive only.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

# module filename starts with a digit -> load via file path
import importlib.util

_LIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "6B_deep_lib.py")
_spec = importlib.util.spec_from_file_location("six_b_deep_lib", _LIB_PATH)
lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lib)

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = lib.CACHE

report = {}

panel = lib.load_outright_1m()
report["panel_rows_outright"] = int(len(panel))
report["panel_span"] = [str(panel["dt"].min()), str(panel["dt"].max())]

reg = lib.build_contract_registry(panel)
q = reg[~reg["stray"]]
report["contracts_resolved"] = int(len(q))
report["contracts_by_year"] = {
    str(y): int(n) for y, n in q.groupby("year").size().items()}
report["strays"] = [
    {"symbol": r["symbol"], "cluster": r["cluster"], "n_bars": r["n_bars"],
     "volume": r["volume"], "first_bar": str(r["first_bar"]),
     "last_bar": str(r["last_bar"])}
    for _, r in reg[reg["stray"]].iterrows()]
# serial contracts (non-HMUZ) present but thin — summarize
serial_sym = panel[~panel["raw_symbol"].str.fullmatch(r"6B[HMUZ]\d")]
report["serial_rows"] = int(len(serial_sym))
report["serial_volume_total"] = int(serial_sym["volume"].sum())

df = lib.annotate_panel(panel, reg)
df.to_parquet(os.path.join(CACHE, "6b_annotated_1m.parquet"), index=False)

sess = lib.build_session_table(df)
sess.to_parquet(os.path.join(CACHE, "6b_sessions.parquet"), index=False)
report["session_rows"] = int(len(sess))
report["n_sessions"] = int(sess["session_date"].nunique())
report["session_span"] = [str(sess["session_date"].min()), str(sess["session_date"].max())]

# session minute-of-day coverage (break + boundary check)
d = df[df["contract"].notna()]
mo = d["minute_ct"]
report["minute_ct_histogram_edges"] = {
    "min_minute": int(mo.min()), "max_minute": int(mo.max()),
    "bars_in_break": int(d["in_break"].sum()),
    "bars_ge_1700": int((mo >= 17 * 60).sum()),
    "bars_lt_0400_ct": int((mo < 4 * 60).sum()),
    "weekend_anomaly_bars": int(d["weekend_anomaly"].sum()),
}

held_cal = lib.front_by_calendar(sess, reg)
held_vol = lib.front_by_volume_crossover(sess, k=5)
held_cal.to_parquet(os.path.join(CACHE, "held_calendar.parquet"), index=False)
held_vol.to_parquet(os.path.join(CACHE, "held_volume_crossover.parquet"), index=False)
report["held_calendar_sessions"] = int(len(held_cal))
report["held_volume_crossover_sessions"] = int(len(held_vol))

# agreement between rules
j = held_cal.merge(held_vol, on="session_date", suffixes=("_cal", "_vol"))
report["rule_agreement_sessions"] = int((j["held_cal"] == j["held_vol"]).sum())
report["rule_agreement_frac"] = float((j["held_cal"] == j["held_vol"]).mean())
dis = j[j["held_cal"] != j["held_vol"]]
report["rule_disagreement_examples"] = [
    {"session_date": str(r.session_date), "cal": r.held_cal, "vol": r.held_vol}
    for r in dis.head(12).itertuples()]

lib.jdump(report, os.path.join(HERE, "6B_build_report.json"))
print(json.dumps({k: v for k, v in report.items()
                  if k not in ("strays", "rule_disagreement_examples")}, indent=1)[:1500])
print("strays:", report["strays"][:8])
