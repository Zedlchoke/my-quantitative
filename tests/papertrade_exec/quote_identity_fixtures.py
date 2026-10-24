"""Complete explicit source identity for synthetic W1.4 test quotes."""
import hashlib


def identity_fields(match_id):
    return {"payload_sha256": hashlib.sha256(str(match_id).encode()).hexdigest(),
            "pm_walk": {"market_id": "market-" + str(match_id),
                        "event_id": "event-" + str(match_id),
                        "legs": {"HOME": {}, "AWAY": {}, "DRAW": {}}}}
