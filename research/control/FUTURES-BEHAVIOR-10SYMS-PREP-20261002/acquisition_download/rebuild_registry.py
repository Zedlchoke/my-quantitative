#!/usr/bin/env python3
"""rebuild_registry.py — rebuild CONTRACT_REGISTRY.json from ALL delivered
definition .dbn.zst files (outright contracts only, dash spread composites
excluded per the measured re-list convention). Ordered by chunk window."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ACQ = Path(__file__).resolve().parent
sys.path.insert(0, str(ACQ))
import qa_batch  # noqa: E402
from futbt.dbn import ingest  # noqa: E402

RAW = Path("/Users/hoangminhlong/my-quantitative-data/"
           "futures-databento-av1trim/raw/dbn_zst/AV1T-definition-ALL10")


def main() -> None:
    reg = ingest.ContractRegistry()
    scratch_dir = qa_batch.SCRATCH
    scratch_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(RAW.glob("*.dbn.zst"))
    print(f"rebuilding from {len(files)} definition files")
    n_out = n_spread = 0
    for i, zst in enumerate(files):
        scratch = scratch_dir / (zst.stem + ".rebuild.scratch.dbn")
        qa_batch.decompress_to_scratch(zst, scratch)
        frame = ingest.ingest_file(scratch)
        for d in frame.definitions:
            if qa_batch.OUTRIGHT_RE.match(d.raw_symbol):
                n_out += 1
                reg.apply(d)
            else:
                n_spread += 1
        scratch.unlink()
        print(f"  [{i+1}/{len(files)}] {zst.name}: registry="
              f"{len(reg.by_raw)} (outright actions {n_out:,}, spread "
              f"{n_spread:,})")
    qa_batch.save_registry(reg)
    print(f"saved CONTRACT_REGISTRY.json: {len(reg.by_raw)} outright "
          f"contracts; {n_out:,} outright actions, {n_spread:,} spread "
          f"actions census")


if __name__ == "__main__":
    main()
