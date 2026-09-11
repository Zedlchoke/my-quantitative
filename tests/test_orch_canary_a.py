from research.fixtures.orch_canary.module_a import canary_a_checksum


def test_empty_list_returns_zero():
    # Hand-computed: no elements -> 0.
    assert canary_a_checksum([]) == 0


def test_single_element_returns_zero():
    # Hand-computed: 0 * 5 = 0.
    assert canary_a_checksum([5]) == 0


def test_two_elements_returns_three():
    # Hand-computed: 0 * 2 + 1 * 3 = 3.
    assert canary_a_checksum([2, 3]) == 3
