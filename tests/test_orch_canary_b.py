"""Hand-computed tests for the P7-B canary fixture module."""

from research.fixtures.orch_canary.module_b import canary_b_mirror


def test_canary_b_mirror_empty() -> None:
    assert canary_b_mirror([]) == []


def test_canary_b_mirror_single_element() -> None:
    assert canary_b_mirror(["a"]) == ["A"]


def test_canary_b_mirror_two_elements_reversed_and_uppercased() -> None:
    assert canary_b_mirror(["ab", "cd"]) == ["CD", "AB"]
