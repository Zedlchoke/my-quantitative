"""DGS10 control-series pin builder (P-13 inherited pin law).

The exact-spec CTL-DGS10LEVEL arms of BOTH selected families consume
vintaged DGS10 bytes.  The cycle's frozen S2 set carries only the five
CPI legs, so the DGS10 vintaged evidence is pinned from V8's committed
staged-vintaged evidence (inherited pin): the V8 run contract pins the
staged_vintaged MANIFEST by digest c8ae7877...; that manifest pins
DGS10.json by sha256; this lane copies the bytes and verifies every link.

Usage:
    .venv/bin/python -m research.assets.forex_ng1.run.ctlpin \
        [--out research/control/forex_ng1_run/i/ctl_dgs10_pin.json]

The copy under data_raw/ stays UNTRACKED (data_raw/ is not gitignored in
this worktree; raw bytes are never committed -- only this manifest).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1.run import config as C          # noqa: E402

SCHEMA = "forex_ng1_ctl_dgs10_pin@1"

#: The V8 worktree still carries the staged bytes (untracked leftovers;
#: the worktree itself left `git worktree list`, the bytes remain).
DEFAULT_SOURCE = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
                  "forex-free-v8/integration/research/control/"
                  "forex_free_v8_run/staged_vintaged/DGS10.json")
#: Surviving committed copies of the V8 staged-vintaged manifest (the V8
#: worktree's own copy is gone with its tree; every surviving copy is
#: byte-identical and hashes to the run-contract pin).
MANIFEST_WITNESSES = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v9/"
    "integration/research/control/forex_free_v8_run/"
    "staged_vintaged_manifest.json",
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v9/"
    "i-family/research/control/forex_free_v8_run/"
    "staged_vintaged_manifest.json",
)
MANIFEST_SHA256_PIN = ("c8ae78777102ab45cec433f5da6c786355b57c884"
                       "be5f15c39c1fc18ca328e7c")
DGS10_SHA256_PIN = ("03dde429ba022e6d011ae3a61323124e38c5a3fac"
                    "888b492823406a51c4c4aa0")


class PinError(Exception):
    """Fail-closed pin verification error."""


def build_pin(source: str = DEFAULT_SOURCE,
              copy_path: str | None = None,
              out_path: str | None = None) -> dict:
    copy_path = copy_path or os.path.join(
        REPO_ROOT, "data_raw/forex_ng1_ctl/DGS10.json")
    out_path = out_path or os.path.join(
        REPO_ROOT, "research/control/forex_ng1_run/i/ctl_dgs10_pin.json")

    # 1. verify the manifest chain (every surviving witness hashes to the
    #    V8 run-contract pin)
    manifest_ok = {}
    for w in MANIFEST_WITNESSES:
        if os.path.exists(w):
            manifest_ok[w] = C.sha256_file(w)
    if not manifest_ok:
        raise PinError("no staged_vintaged_manifest witness survives")
    bad = {p: d for p, d in manifest_ok.items() if d != MANIFEST_SHA256_PIN}
    if bad:
        raise PinError(f"manifest witness drift: {bad}")

    # 2. read the manifest's DGS10 entry
    witness = next(iter(manifest_ok))
    with open(witness, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    entry = manifest["series"]["DGS10"]
    if entry["sha256"] != DGS10_SHA256_PIN:
        raise PinError("manifest DGS10 entry disagrees with the expected "
                       f"digest: {entry['sha256']}")

    # 3. verify the source bytes against the manifest entry
    source_sha = C.sha256_file(source)
    if source_sha != entry["sha256"]:
        raise PinError(
            f"source DGS10 bytes drift: {source_sha} != manifest "
            f"{entry['sha256']}")

    # 4. copy (byte-identical) and re-verify
    os.makedirs(os.path.dirname(copy_path), exist_ok=True)
    with open(source, "rb") as fh:
        raw = fh.read()
    with open(copy_path, "wb") as fh:
        fh.write(raw)
    copy_sha = C.sha256_file(copy_path)
    if copy_sha != source_sha:
        raise PinError(f"copy drift: {copy_sha} != {source_sha}")

    import hashlib
    payload = json.loads(raw.decode("utf-8"))
    observations = (payload["observations"]
                    if isinstance(payload, dict) else payload)
    from research.assets.forex_ng1.d2.series import (
        parse_realtime_observations,
    )
    rows = parse_realtime_observations(observations)
    numeric = [r for r in rows if r["value"] is not None]

    pin = {
        "schema": SCHEMA,
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-i-runners",
        "pin_law": "P-13 inherited pin: V8 run-contract data_pins pin the "
                   "staged_vintaged MANIFEST by digest; the manifest pins "
                   "DGS10.json by sha256; this lane copies the bytes and "
                   "verifies source==copy==manifest entry",
        "v8_staged_vintaged_manifest": {
            "sha256": MANIFEST_SHA256_PIN,
            "pin_basis": "FOREX-FREE-V8 run_contract.json "
                         "data_pins.staged_vintaged_manifest_sha256",
            "witnesses_verified": manifest_ok,
        },
        "dgs10": {
            "file": "DGS10.json",
            "sha256": copy_sha,
            "source_path": source,
            "copy_path": copy_path,
            "source_copy_identical": copy_sha == source_sha,
            "manifest_entry": {"kind": entry["kind"],
                               "binding_rows": entry["binding_rows"],
                               "distinct_obs_dates":
                                   entry["distinct_obs_dates"],
                               "obs_first": entry["obs_first"],
                               "obs_last": entry["obs_last"]},
            "reparse_rows": len(rows),
            "reparse_numeric_rows": len(numeric),
            "asof_law": "value in effect at day d = row with max "
                        "realtime_start <= d (V8 staged manifest "
                        "semantics, inherited verbatim)",
            "consumers": ["FXNG1-A5-P1-CTL-DGS10LEVEL",
                          "FXNG1-A4-P2-CTL-DGS10LEVEL"],
        },
        "raw_bytes_policy": "UNTRACKED_NEVER_COMMITTED (data_raw/ is not "
                            "gitignored; only this manifest commits)",
        "payload_digest_for_note": hashlib.sha256(
            json.dumps({"obs_first": entry["obs_first"],
                        "obs_last": entry["obs_last"],
                        "binding_rows": entry["binding_rows"]},
                       sort_keys=True).encode()).hexdigest(),
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(pin, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return pin


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    args = ap.parse_args(argv)
    pin = build_pin(source=args.source, out_path=args.out)
    print(json.dumps({"out": args.out or os.path.join(
        REPO_ROOT, "research/control/forex_ng1_run/i/ctl_dgs10_pin.json"),
        "dgs10_sha256": pin["dgs10"]["sha256"],
        "identical": pin["dgs10"]["source_copy_identical"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
