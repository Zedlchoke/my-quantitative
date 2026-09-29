#!/usr/bin/env python
"""Deterministic artifact-pin manifest builder (A1-only).

Walks the PC12A control dir, sha256-hashes every file EXCEPT the manifest
dir itself (a manifest cannot contain its own hash), and writes
manifest/ARTIFACT_PINS.json (schema artifact_pins@1). Run by A1 at every
integration point; never by lanes.
"""
import hashlib, json, os, time

CTRL = "/Users/hoangminhlong/my-quantitative/research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
MANIFEST_DIR = os.path.join(CTRL, "manifest")

def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    files = []
    for root, dirs, names in os.walk(CTRL):
        dirs[:] = [d for d in dirs if d != os.path.basename(MANIFEST_DIR)]
        for n in sorted(names):
            if n == ".DS_Store":
                continue
            p = os.path.join(root, n)
            rel = os.path.relpath(p, CTRL)
            files.append(rel)
    entries = [{"path": rel, "bytes": os.path.getsize(os.path.join(CTRL, rel)),
                "sha256": sha256(os.path.join(CTRL, rel))} for rel in sorted(files)]
    out = {"schema": "artifact_pins@1",
           "cycle": "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1",
           "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "writer": "A1 integration",
           "n_files": len(entries), "files": entries}
    os.makedirs(MANIFEST_DIR, exist_ok=True)
    dst = os.path.join(MANIFEST_DIR, "ARTIFACT_PINS.json")
    with open(dst, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(f"wrote {dst} ({len(entries)} files)")

if __name__ == "__main__":
    main()
