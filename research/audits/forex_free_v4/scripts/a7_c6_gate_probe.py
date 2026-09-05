#!/usr/bin/env python3
"""A7 C6 probe: (a) does the w4_freeze gate hash-check branch work when the
freeze artifact carries freeze_token (proving the token-key check is the only
reason the real artifact fails); (b) would the driver launch on a STALE GO
(the 03:41 OWNER_INTENT GO copied to the fresh-GO path) with a synthetic S0?"""
import json, os, shutil, sys
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v4/q-a7-prelaunch")
sys.path.insert(0, str(WT))
from research.assets.forex_free_v4 import exec_driver_v4 as D

TMP = Path("/tmp/a7_gate_probe")
if TMP.exists():
    shutil.rmtree(TMP)
CTL = TMP / "research/control/forex_free_v4_run"
CTL.mkdir(parents=True)

# symlink every repo file except the v4 control dir (read-only view)
for name in os.listdir(WT):
    if name in ("research",):
        continue
    os.symlink(WT / name, TMP / name)
RES = TMP / "research"
os.symlink(WT / "research/assets", RES / "assets")
for sub in ("control", "proposals"):
    os.symlink(WT / "research" / sub, RES / sub) if sub == "proposals" else None
# control: real dir with only the files we craft (gate reads only specific files)
shutil.copy(WT / "research/control/forex_free_v4_run/w4_freeze.json", CTL / "w4_freeze.json")
shutil.copy(WT / "research/control/forex_free_v4_run/run_contract.json", CTL / "run_contract.json")
shutil.copy(WT / "research/control/forex_free_v4_run/state.json", CTL / "state.json")

out = {}

# --- (a) real artifact as-is ---
ok, gates = D.evaluate_launch_gates(root=str(TMP))
out["a_real_artifact"] = {"all_pass": ok, "w4_freeze": gates["w4_freeze"]}

# --- (b) real artifact + freeze_token key added (simulating the token the driver wants) ---
fr = json.loads((CTL / "w4_freeze.json").read_text())
fr["freeze_token"] = "FOREX_FREE_V4_W4"
(CTL / "w4_freeze.json").write_text(json.dumps(fr, indent=1))
ok, gates = D.evaluate_launch_gates(root=str(TMP))
out["b_token_added_hash_branch"] = {"all_pass": ok, "w4_freeze": gates["w4_freeze"],
                                    "s0": gates["s0_launch_authorized"]["ok"],
                                    "fresh_go": gates["owner_fresh_go"]["ok"],
                                    "budget": gates["budget"],
                                    "s1": gates["s1_seal"]}

# --- (c) STALE-GO adversarial: synthetic S0 (authorized, past) + stale 03:41 GO on fresh path ---
(CTL / "s0_launch_authorized.json").write_text(json.dumps({
    "schema": "forex_free_v4_s0_launch_authorization_v1",
    "verdict": "FOREX_FREE_V4_S0_LAUNCH_AUTHORIZED", "unresolved_high_critical": 0,
    "authorized_utc": "2026-09-05T00:00:00Z"}))
shutil.copy(WT / "research/control/forex_free_v4_run/owner_go_scored_execution.json",
            CTL / "owner_fresh_go.json")
ok, gates = D.evaluate_launch_gates(root=str(TMP))
out["c_stale_go_attack"] = {"all_pass": ok, "w4_freeze": gates["w4_freeze"]["ok"],
                            "s0": gates["s0_launch_authorized"]["ok"],
                            "fresh_go": gates["owner_fresh_go"],
                            "budget": gates["budget"]["ok"], "s1": gates["s1_seal"]["ok"]}

# --- (d) stale GO dated AFTER reclassification but before S0? then AFTER S0 ---
(CTL / "owner_fresh_go.json").write_text(json.dumps({
    "instruction_verbatim": "GO FOREX V4 SCORED EXECUTION",
    "received_utc": "2026-09-05T09:00:00Z"}))  # postdates reclass 03:46 but PREdates synthetic S0 00:00? no, postdates. set S0 later:
out["d"] = "see c"
shutil.rmtree(TMP)
print(json.dumps(out, indent=1))
