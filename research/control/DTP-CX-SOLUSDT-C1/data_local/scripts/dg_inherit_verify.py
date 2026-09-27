#!/usr/bin/env python
"""DTP-CX-SOLUSDT-C1 data gate T1 — INHERIT-VERIFY.

Streaming sha256 of the inherited PWS-CX-SOLUSDT-C1 corpus (read-only, no copy):
  (a) all 72 klines_um_SOLUSDT_1h zips
  (b) the 4 funding JSONs
  (c) the 6 bookTicker monthly zips
against the pinned hashes in PWS data_local/INVENTORY.md.
Writes machine JSON into this cycle's data_gate/ dir. No outcome/PnL touched.
"""
import hashlib, json, os, re, sys, time

PWS = ("/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-solusdt-c1/"
       "integration/research/control/PWS-CX-SOLUSDT-C1")
INVENTORY = os.path.join(PWS, "data_local", "INVENTORY.md")
OUT = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
       "integration/research/control/DTP-CX-SOLUSDT-C1/data_gate/"
       "C1_machine_INHERIT_VERIFY_SOLUSDT.json")

CHUNK = 8 * 1024 * 1024


def parse_inventory(path):
    rows = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*`([0-9a-f]{64})`\s*\|", line)
            if m:
                rows[m.group(1)] = {"bytes": int(m.group(2)), "sha256": m.group(3)}
    return rows


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    inv = parse_inventory(INVENTORY)
    assert len(inv) > 0, "INVENTORY.md parse failed"
    sets = {
        "klines_um_SOLUSDT_1h": [k for k in inv if k.startswith("data_local/vision/klines_um_SOLUSDT_1h/") and k.endswith(".zip")],
        "funding_jsons": [k for k in inv if k.startswith("data_local/funding/") and k.endswith(".json")],
        "bookTicker_um_SOLUSDT": [k for k in inv if k.startswith("data_local/vision/bookTicker_um_SOLUSDT/") and k.endswith(".zip")],
        # bonus evidence (cheap, part of pinned corpus)
        "aux": [k for k in inv if k.endswith("klines_um_SOLUSDT_1h_MANIFEST.json") or k.endswith("Binance_Vision-Terms_of_Use.pdf")],
    }
    out = {
        "schema": "dtp/dg_inherit_verify@1",
        "cycle_id": "DTP-CX-SOLUSDT-C1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inventory_source": INVENTORY,
        "inventory_sha256": sha256_file(INVENTORY),
        "method": "streaming sha256 (8 MiB chunks), no file copied",
        "sets": {},
    }
    n_match = n_mismatch = n_missing = 0
    for setname, keys in sets.items():
        rows = []
        for rel in sorted(keys):
            expect = inv[rel]
            full = os.path.join(PWS, rel)
            row = {"file": rel, "expected_bytes": expect["bytes"],
                   "expected_sha256": expect["sha256"]}
            if not os.path.exists(full):
                row.update(status="MISSING", actual_bytes=None, actual_sha256=None)
                n_missing += 1
            else:
                actual = sha256_file(full)
                ab = os.path.getsize(full)
                ok = (actual == expect["sha256"]) and (ab == expect["bytes"])
                row.update(actual_bytes=ab, actual_sha256=actual,
                           status="MATCH" if ok else "MISMATCH")
                if ok:
                    n_match += 1
                else:
                    n_mismatch += 1
            rows.append(row)
        out["sets"][setname] = {"n_expected": len(keys), "files": rows}
    out["summary"] = {"n_match": n_match, "n_mismatch": n_mismatch,
                      "n_missing": n_missing,
                      "verdict": "PASS" if (n_mismatch == 0 and n_missing == 0) else "FAIL"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out["summary"]))
    for setname, s in out["sets"].items():
        bad = [r["file"] for r in s["files"] if r["status"] != "MATCH"]
        print(f"{setname}: n={s['n_expected']} bad={bad}")


if __name__ == "__main__":
    main()
