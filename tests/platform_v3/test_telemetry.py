"""V3 telemetry contract tests: redaction + noninterference (section 7)."""

import hashlib
import json
import os

from research.platform_v3.telemetry import (
    JsonlTelemetry,
    NoopTelemetry,
    redact_attributes,
    redact_value,
    telemetry_from_env,
)


def read_lines(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def test_redaction_of_credential_names():
    out = redact_attributes({
        "api_key": "sk-123", "Authorization": "Bearer x",
        "cookie": "a=b", "password": "h", "access_token": "t",
        "EODHD_API_KEY": "k",
    })
    assert all(v == "[REDACTED_KEY]" for v in out.values())


def test_redaction_of_urls_with_query_secrets():
    assert redact_value("https://eodhd.invalid?api_key=SECRET&x=1") == \
        "[REDACTED_URL_SECRET]"
    assert redact_value("https://eodhd.invalid?plain=1").startswith("https://")


def test_redaction_of_env_maps_and_s1_paths_and_outcomes():
    out = redact_attributes({
        "env": {"PATH": "/usr/bin", "MY_KEY": "v"},
        "s1_path": "/data/s1/sealed.parquet",
        "raw_payload": "x" * 600,
        "net_pnl": 123.45,
        "sharpe": 1.5,
        "profit_factor": 1.2,
        "drawdown": -0.2,
    })
    assert out["env"] == "[REDACTED_MAP]"
    assert out["s1_path"] == "[REDACTED_S1_PATH]"
    assert out["raw_payload"] == "[REDACTED_LONG_VALUE]"
    assert out["net_pnl"] == "[REDACTED_KEY]"
    assert out["sharpe"] == "[REDACTED_KEY]"
    assert out["profit_factor"] == "[REDACTED_KEY]"
    assert out["drawdown"] == "[REDACTED_KEY]"


def test_jsonl_exporter_writes_redacted_local_file(tmp_path):
    path = str(tmp_path / "runtime" / "trace.jsonl")
    t = JsonlTelemetry(path, trace_id="0" * 32,
                       identifiers={"cycle_id": "RESEARCH-PLATFORM-V3",
                                    "phase_id": "P3",
                                    "lane_id": "A1",
                                    "job_id": "j1",
                                    "run_id": "r1",
                                    "gate_id": "V3-G3"})
    with t.span_start("job", dataset_id="mdp:m:1", api_key="sk-1"):
        t.event("progress", done=1)
    t.close()
    rows = read_lines(path)
    assert rows[0]["name"] == "job" or rows[0]["event"] == "span_start"
    joined = json.dumps(rows)
    assert "sk-1" not in joined
    assert "[REDACTED_KEY]" in joined
    assert all(r["trace_id"] == "0" * 32 for r in rows)


def test_noop_default_writes_nothing(tmp_path):
    before = set(os.listdir(tmp_path))
    t = NoopTelemetry()
    with t.span_start("x", api_key="sk-1"):
        t.event("e", a=1)
    assert set(os.listdir(tmp_path)) == before


def test_disable_env_makes_jsonl_behave_as_noop(tmp_path, monkeypatch):
    monkeypatch.setenv("V3_TELEMETRY_DISABLE", "1")
    path = str(tmp_path / "t.jsonl")
    t = JsonlTelemetry(path, trace_id="1" * 32)
    with t.span_start("x"):
        pass
    t.close()
    assert not os.path.exists(path)


def test_telemetry_noninterference_scientific_bytes_equal(tmp_path,
                                                          monkeypatch):
    """The same deterministic 'research' computation with telemetry
    enabled (JSONL) and disabled must produce byte-identical outputs."""

    def research_output(telemetry):
        rows = []
        for i in range(64):
            with telemetry.span_start("job", dataset_id="m:1", step=i):
                rows.append((i, (i * 7) % 13))
        # NOTE: an outcome-shaped metric is included in the scientific
        # payload on purpose; it must survive telemetry untouched.
        rows.append(("total", sum(v for _, v in rows)))
        return json.dumps(rows, sort_keys=True).encode()

    monkeypatch.delenv("V3_TELEMETRY", raising=False)
    off = research_output(telemetry_from_env(
        str(tmp_path / "off.jsonl"), "a" * 32))

    monkeypatch.setenv("V3_TELEMETRY", "jsonl")
    on = research_output(telemetry_from_env(
        str(tmp_path / "on.jsonl"), "b" * 32))

    assert hashlib.sha256(off).hexdigest() == \
        hashlib.sha256(on).hexdigest()
    assert os.path.exists(tmp_path / "on.jsonl")
    assert not os.path.exists(tmp_path / "off.jsonl")
