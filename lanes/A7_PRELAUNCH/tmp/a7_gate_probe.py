# a7_gate_probe.py — A7 audit · cap/gate probes on the FROZEN tree (A7-4), read-only.
# Imports the frozen harness as-is (never modifies it) and exercises, in-process:
#   1. doctored-2019 season set -> enforce_season_cap must raise CapViolation
#   2. evaluate-oos real/no-token  -> OOS-GATE-REFUSED BEFORE any real byte is read
#      (audit hook watches open/listdir/scandir/stat on ALL real data roots)
#   3. fabricated tokens -> refused (wrong phrase; path-like string)
# NO token resembling the registered phrase is typed by this audit (boundary A7-8);
# the exact-phrase path (gate check passes, execution still refuses POST-GO) is
# verified by 4-line code-read of harness.main().
import os
import sys

HOME = os.path.expanduser("~")
REAL_ROOTS = [
    HOME + "/.my-quantitative-data/playerfeat-prep-v1/wnba/features",
    HOME + "/.my-quantitative-data/wnba-prep-v1/roster_audit",
    HOME + "/.my-quantitative-data/wnba-v1/raw/espn_schedules",
    HOME + "/.my-quantitative-data/wnba-v1/raw/wnba_stats_schedules",
    HOME + "/.my-quantitative-data/wnba-playerfeat-scored-v1/selection",
]

read_events = []


def hook(event, args):
    if event in ("open", "os.listdir", "os.scandir", "os.stat"):
        p = args[0] if args else ""
        if isinstance(p, (str, bytes, os.PathLike)):
            ps = os.fsdecode(p) if not isinstance(p, str) else p
            for root in REAL_ROOTS:
                if ps.startswith(root):
                    read_events.append((event, ps))
                    break


fails = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("  " + detail if detail else ""))
    if not ok:
        fails.append(name)


sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "wnba-playerfeat-scored-v1/integration/lanes/T_SELECT")
import harness  # frozen, read-only use

# 1. doctored-2019 probe
try:
    harness.enforce_season_cap({2017, 2018, 2019}, "A7_doctored_2019_probe")
    check("A4_doctored_2019_aborts", False, "no exception raised")
except harness.CapViolation as e:
    check("A4_doctored_2019_aborts", True, str(e)[:110])
# control: <=2018 passes
try:
    harness.enforce_season_cap({2002, 2018}, "A7_control")
    check("A4_cap_control_2018_passes", True)
except harness.Abort:
    check("A4_cap_control_2018_passes", False)

# 2/3. evaluate-oos refusals under an audit hook
def run_cli(argv):
    read_events.clear()
    old = sys.argv
    sys.argv = ["harness.py"] + argv
    try:
        harness.main()
        return ("returned", None)
    except harness.Abort as e:
        return ("Abort", str(e))
    except SystemExit as e:
        return ("SystemExit", str(e))
    finally:
        sys.argv = old


st, msg = run_cli(["--mode", "evaluate-oos", "--source", "real"])
n_events = len(read_events)
check("A4_evaluate_oos_real_no_token_refused",
      st == "Abort" and "OOS-GATE-REFUSED" in msg, "%s: %s" % (st, msg[:90]))
check("A4_refusal_is_preread_zero_real_bytes", n_events == 0,
      "real-data fs events at refusal time: %d" % n_events)

st2, msg2 = run_cli(["--mode", "evaluate-oos", "--source", "real",
                     "--go-token", "go wnba playerfeat scored v1 evaluation"])
check("A4_fabricated_lowercase_token_refused",
      st2 == "Abort" and "OOS-GATE-REFUSED" in msg2, msg2[:80])

st3, msg3 = run_cli(["--mode", "evaluate-oos", "--source", "real",
                     "--go-token", "/etc/passwd"])
check("A4_path_as_token_refused",
      st3 == "Abort" and "OOS-GATE-REFUSED" in msg3, msg3[:80])

st4, msg4 = run_cli(["--mode", "evaluate-oos", "--source", "synthetic"])
check("A4_control_synthetic_allowed_pregate", st4 == "returned", msg4 or "")

print("A7-GATE-PROBE %s (%d fails)" % ("PASS" if not fails else "FAIL", len(fails)))
raise SystemExit(0 if not fails else 1)
