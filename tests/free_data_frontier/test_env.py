import os

import pytest

from research.free_data_frontier.env import check_presence, load_secret, parse_env_keys


def test_parse_env_keys_reports_names_only(tmp_path):
    env = tmp_path / ".env"
    env.write_text('SEC_CONTACT_NAME=someone\nEIA_API_KEY="abc123"\n# comment\n\n')
    presence = parse_env_keys(env)
    assert presence == {"SEC_CONTACT_NAME": True, "EIA_API_KEY": True}


def test_check_presence_present_missing(tmp_path):
    env = tmp_path / ".env"
    env.write_text("EIA_API_KEY=x\n")
    verdict = check_presence(["EIA_API_KEY", "SEC_CONTACT_EMAIL"], env_path=env)
    assert verdict["EIA_API_KEY"] == "PRESENT"
    assert verdict["SEC_CONTACT_EMAIL"] == "MISSING"


def test_presence_output_never_contains_value(tmp_path):
    secret = "SUPERSECRETVALUE123"
    env = tmp_path / ".env"
    env.write_text(f"EIA_API_KEY={secret}\n")
    verdict = check_presence(["EIA_API_KEY"], env_path=env)
    blob = repr(verdict)
    assert secret not in blob
    assert verdict["EIA_API_KEY"] == "PRESENT"


def test_load_secret_returns_value_in_memory_only(tmp_path):
    env = tmp_path / ".env"
    env.write_text('EIA_API_KEY="quoted-value"\n')
    assert load_secret("EIA_API_KEY", env_path=env) == "quoted-value"


def test_load_secret_missing_raises_fail_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("NO_SUCH_KEY", raising=False)
    with pytest.raises(Exception):
        load_secret("NO_SUCH_KEY", env_path=tmp_path / "absent.env")
