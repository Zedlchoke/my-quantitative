#!/usr/bin/env python3
"""V14 P1 A3 — archive PROVIDER DOCUMENTATION evidence for probed endpoints.

The live docs domain (developers.binance.com) serves a bot challenge to
non-browser fetchers, so this script retrieves the provider pages as archived
by the Internet Archive Wayback Machine, recording BOTH URLs: the original
provider URL (the citation of record) and the exact snapshot URL fetched
(snapshot timestamp + digest available from web.archive.org). Text is
extracted from the server-rendered HTML with the stdlib html.parser.

stdlib only; no credentials; light on the archive host (>= 1.5 s between
fetches, 12 pages total).
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

LANE_DIR = Path(__file__).resolve().parent
OUT_DIR = LANE_DIR / "evidence" / "docs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WAYBACK_PREFIX = "http://web.archive.org/web/"

# (slug, original provider URL of record, wayback snapshot timestamp)
PAGES = [
    ("open_interest_statistics", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics", "20250123113224"),
    ("taker_buysell_volume", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Taker-BuySell-Volume", "20250123101712"),
    ("top_long_short_account_ratio", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Top-Long-Short-Account-Ratio", "20250123104931"),
    ("top_trader_long_short_ratio", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Top-Trader-Long-Short-Ratio", "20250123120056"),
    ("long_short_ratio", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio", "20250123111747"),
    ("basis", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Basis", "20250430094449"),
    ("kline_candlestick_data", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data", "20250123095726"),
    ("mark_price_kline", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price-Kline-Candlestick-Data", "20250123105427"),
    ("index_price_kline", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Index-Price-Kline-Candlestick-Data", "20250426013622"),
    ("premium_index_kline", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Premium-Index-Kline-Data", "20250123110534"),
    ("get_funding_rate_history", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History", "20250123093348"),
    ("open_interest", "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest", "20250123100715"),
]


class TextExtractor(HTMLParser):
    """Extract visible text; drop script/style; keep code blocks line-broken."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self._block_tags = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "br", "table", "pre"}

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "svg", "nav", "footer"}:
            self.skip_depth += 1
        elif tag in self._block_tags:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "svg", "nav", "footer"} and self.skip_depth:
            self.skip_depth -= 1
        elif tag in self._block_tags:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def extract_text(html: str) -> str:
    parser = TextExtractor()
    parser.feed(html)
    raw = "".join(parser.parts)
    lines = [ln.strip() for ln in raw.splitlines()]
    # collapse runs of blank lines
    out: list[str] = []
    for ln in lines:
        if ln == "" and (not out or out[-1] == ""):
            continue
        out.append(ln)
    return "\n".join(out).strip()


def main() -> int:
    manifest = []
    for slug, original_url, ts in PAGES:
        snapshot_url = f"{WAYBACK_PREFIX}{ts}/{original_url}"
        rec = {
            "slug": slug,
            "provider_url_of_record": original_url,
            "wayback_snapshot_url": snapshot_url,
            "wayback_snapshot_utc": datetime.strptime(ts, "%Y%m%d%H%M%S").strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            "fetch_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "http_status": None,
        }
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    snapshot_url,
                    headers={"User-Agent": "v14-p1-a3-doc-evidence/1.0"})
                with urllib.request.urlopen(req, timeout=60.0) as resp:
                    rec["http_status"] = resp.status
                    html = resp.read().decode("utf-8", errors="replace")
                break
            except Exception as exc:  # noqa: BLE001 - archive host can hiccup
                rec["error"] = repr(exc)
                if attempt < 2:
                    time.sleep(8.0)
        if rec.get("http_status") == 200:
            text = extract_text(html)
            rec["extracted_text_chars"] = len(text)
            rec["extracted_text"] = text
            rec["error"] = None
        manifest.append(rec)
        print(slug, rec["http_status"], len(rec.get("extracted_text", "")))
        time.sleep(1.5)
    out = OUT_DIR / "docs_fetch_manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
