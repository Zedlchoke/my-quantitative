def canary_a_checksum(values: list[int]) -> int:
    """Position-weighted checksum: sum of i * v for 0-based index i.

    Hand-computed reference values:
      []     -> 0
      [5]    -> 0 * 5 = 0
      [2, 3] -> 0 * 2 + 1 * 3 = 3
    """
    return sum(i * v for i, v in enumerate(values))
