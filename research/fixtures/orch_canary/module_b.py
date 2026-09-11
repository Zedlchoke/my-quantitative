"""Canary P7-B fixture module for orchestration gate Z3-G6."""


def canary_b_mirror(values: list[str]) -> list[str]:
    """Return the input list reversed with every element uppercased.

    Hand-computed expectations:
      [] -> []
      ["a"] -> ["A"]
      ["ab", "cd"] -> ["CD", "AB"]
    """
    return [value.upper() for value in reversed(values)]
