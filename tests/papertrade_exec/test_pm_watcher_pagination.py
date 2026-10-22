"""Gamma's broad offset cap must not hide a listed WSL match."""

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


WATCHER = (Path(__file__).resolve().parents[2] / "research" / "control" /
           "SPORTS-PAPERTRADE-EXEC-V1" / "pm_watcher" / "pm_watcher.py")
spec = importlib.util.spec_from_file_location("pm_watcher_pagination_test", WATCHER)
watcher = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = watcher
spec.loader.exec_module(watcher)


class FakeSource:
    NOT_RUN_TAXONOMY = {"NOT_RUN_NO_MARKET": "no market"}
    GAMMA_EVENTS_URL = "https://gamma-api.polymarket.com/events"

    def __init__(self):
        self.urls = []

    def gamma_fetch_open_events(self, **_):
        return [], [{"page": 21, "error": "HTTP 422",
                     "trailing_past_end_marker": True}]

    def http_get_json(self, url, **_):
        self.urls.append(url)
        return [{"id": "1167584", "title": "Arsenal WFC vs. Birmingham City WFC"}], \
            {"sha256": "fixture-byte-hash"}


def test_wsl_tag_scan_finds_event_beyond_broad_offset_cap():
    source = FakeSource()
    events, meta = watcher.gamma_events(source, ["WSL", "NBA"])
    assert [e["id"] for e in events] == ["1167584"]
    assert meta["broad_scan_complete"] is False
    assert meta["wsl_tag_complete"] is True
    assert "tag_id=105959" in source.urls[0]


def test_incomplete_scan_cannot_claim_no_market():
    fixture = {"match_id": "M1", "home": "Arsenal", "away": "Birmingham City",
               "kickoff_utc": "2026-10-17T11:45:00Z"}
    now = datetime(2026, 10, 14, tzinfo=timezone.utc)
    result = watcher.scan_scope(FakeSource(), "WSL", [fixture], [], {}, now,
                                scan_complete=False)
    assert result["results"][0]["status"] == "NOT_RUN_SOURCE_SCAN_INCOMPLETE"
