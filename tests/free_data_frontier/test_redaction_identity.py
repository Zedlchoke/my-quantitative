import hashlib
import json

import pytest

from research.free_data_frontier.http import (
    canonical_request_identity,
    redact_headers,
    redact_query,
)


def test_redact_query_hides_api_key_values():
    url = "https://api.eia.gov/v2/petroleum?api_key=SECRET123&frequency=monthly"
    redacted = redact_query(url)
    assert "SECRET123" not in redacted
    assert "api_key=<redacted>" in redacted
    assert "frequency=monthly" in redacted


def test_redact_query_case_insensitive_param_names():
    url = "https://x.example/a?Token=abc&b=1"
    assert "abc" not in redact_query(url)


def test_redact_headers_hides_authorization_and_contacts():
    headers = {
        "User-Agent": "research sample name someone@example.gov",
        "Authorization": "Bearer abc",
        "Accept": "application/json",
    }
    redacted = redact_headers(headers)
    assert "someone@example.gov" not in json.dumps(redacted)
    assert "Bearer abc" not in json.dumps(redacted)
    assert redacted["Accept"] == "application/json"
    assert redacted["User-Agent"].startswith("<redacted:contact:len=")


def test_request_identity_deterministic_and_value_free():
    url = "https://api.eia.gov/v2/x?api_key=SECRET&x=1"
    headers = {"User-Agent": "agent someone@example.gov"}
    id1, red_url1 = canonical_request_identity("GET", url, headers)
    id2, red_url2 = canonical_request_identity("GET", url, headers)
    assert id1 == id2
    assert len(id1) == 64
    assert "SECRET" not in red_url1
    # different body -> different identity
    id3, _ = canonical_request_identity("GET", url, headers, body=b"payload")
    assert id3 != id1


def test_request_identity_canonical_form():
    rid, red = canonical_request_identity(
        "get", "https://h/p?a=1&api_key=z", {"b": "2", "a": "1"}
    )
    canonical = {
        "method": "GET",
        "url": "https://h/p?a=1&api_key=<redacted>",
        "headers": {"a": "1", "b": "2"},
        "body_sha256": hashlib.sha256(b"").hexdigest(),
    }
    expected = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert rid == expected
