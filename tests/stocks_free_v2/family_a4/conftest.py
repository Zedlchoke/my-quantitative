"""Pytest fixtures for the family_a4 suite (offline, synthetic only)."""

from __future__ import annotations

import pytest

from tests.stocks_free_v2.family_a4._fixtures import (  # noqa: F401
    make_inputs,
)


@pytest.fixture(scope="session")
def real_spec():
    from research.stocks_free_v2.family_a4 import load_frozen_spec

    return load_frozen_spec()


@pytest.fixture(scope="session")
def hand_sessions():
    from tests.stocks_free_v2.family_a4._fixtures import calendar_sessions

    return calendar_sessions(300)


@pytest.fixture()
def hand_inputs(hand_sessions):
    from tests.stocks_free_v2.family_a4._fixtures import (
        hand_partition,
        hand_raw,
        hand_spec,
        hand_tr,
        make_inputs,
    )

    return make_inputs(
        hand_spec(),
        hand_sessions,
        hand_tr(hand_sessions),
        hand_raw(hand_sessions),
        hand_partition(hand_sessions),
    )


@pytest.fixture(scope="session")
def s0_sessions():
    from tests.stocks_free_v2.family_a4._fixtures import full_s0_sessions

    return full_s0_sessions()
