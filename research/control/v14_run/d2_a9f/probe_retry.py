"""A9-F T1b: retry the basis-route probes that hit transient HTTP 418.

The first probe pass saw 29/76 /futures/data/basis point anchors return
HTTP 418 with EMPTY bodies, scattered across symbols and anchors (not a
data boundary pattern; kline-route probes interleaved in the same run all
returned 200).  This pass re-runs exactly those (symbol, anchor) checks
after a cooldown with a longer 1.5s sleep and archives retry evidence as
evidence/d2retry_XXXX.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from probe_basis_depth import (  # noqa: F401
    BASIS_ANCHORS,
    UNIVERSE,
    _counter,
    iso_to_ms,
    probe_get,
    utc_now_iso,
)

HERE = Path(__file__).resolve().parent
SLEEP = 1.5


def main() -> None:
    # Continue the probe-id sequence AFTER the first pass (304 requests) so
    # retry evidence never collides with first-pass evidence files.
    _counter["n"] = 304
    summary = []
    # honour the cooldown before touching the endpoint again
    print(f"[{utc_now_iso()}] cooldown 60s before retry pass", flush=True)
    time.sleep(60)
    for sym in UNIVERSE:
        for anchor_name, iso in BASIS_ANCHORS.items():
            params = {
                "pair": sym,
                "contractType": "PERPETUAL",
                "period": "15m",
                "limit": 1,
                "startTime": iso_to_ms(iso),
                "endTime": iso_to_ms(iso) + 899_999,
            }
            rec = probe_get("/futures/data/basis", params, f"basis_retry|{sym}|{anchor_name}")
            written = HERE / "evidence" / f"{rec['probe_id']}.json"
            retry_id = rec["probe_id"].replace("d2probe_", "d2retry_")
            target = HERE / "evidence" / f"{retry_id}.json"
            rec["probe_id"] = retry_id
            if written.exists() and written != target:
                written.rename(target)
            summary.append(
                {
                    "probe_id": rec["probe_id"],
                    "route": "basis_futures_data",
                    "symbol": sym,
                    "anchor": anchor_name,
                    "http_status": rec.get("http_status"),
                    "row_count": rec.get("row_count"),
                    "first_row_open_utc": rec.get("first_row_open_utc"),
                    "basis_row": rec.get("first_row") if isinstance(rec.get("first_row"), dict) else None,
                }
            )
            time.sleep(SLEEP)
        print(f"[{utc_now_iso()}] {sym}: basis retries complete", flush=True)
    with open(HERE / "probe_retry_summary.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "schema": "v14_d2_a9f_probe_retry_summary_v1",
                "producer_role": "A9-F",
                "generated_utc": utc_now_iso(),
                "sleep_seconds": SLEEP,
                "note": "retry of basis-route point anchors that returned transient HTTP 418 (empty body) in the first pass",
                "probes": summary,
            },
            handle,
            indent=1,
            sort_keys=True,
        )
        handle.write("\n")
    ok = sum(1 for s in summary if s["http_status"] == 200 and (s["row_count"] or 0) >= 1)
    print(f"retry rows-ok: {ok}/{len(summary)}")


if __name__ == "__main__":
    main()
