"""cells_registry.py — shared frozen cell registry for cycle D2-CURIOSITY-V1.

Frozen law (plans/PLAN_d2_curiosity_v1.md section 2 + three_cell_contract.json
"exactly_three_enforcement"): the cycle's cell registry is EXACTLY

    {SFNG2-A4-P1, FXNG3-A4-P1, CNG2-A5-P1}

Engines and tests hard-fail on any other cell set or any unknown cell id.
This file is the shared registry consumed by every implementation lane
engine (SFNG2, FXNG3, CNG2). It is READ-ONLY by construction:

- ``validate_cell_id``  rejects any id outside the frozen three.
- ``assert_registry_intact`` rejects any candidate registry != the frozen three.
- ``register_cell``     always raises: the registry is frozen; there are no
                        registry writes from lanes (registry authority is
                        researchctl only, and this cycle adds no cells).

NON_GOVERNING_DIAGNOSTIC cycle. No outcome semantics live here.
"""

SCHEMA = "d2c_cells_registry@1"
CYCLE_ID = "D2-CURIOSITY-V1"

# Frozen exactly-three cell ids (sorted). Source of truth:
# research/control/d2_curiosity_v1_run/three_cell_contract.json (cells[].cell_id)
EXACTLY_THREE_CELLS = ("CNG2-A5-P1", "FXNG3-A4-P1", "SFNG2-A4-P1")


class RegistryError(RuntimeError):
    """Base error for registry integrity violations."""


class UnknownCellError(RegistryError):
    """A cell id outside the frozen exactly-three registry was used."""


class RegistryFrozenError(RegistryError):
    """An attempt to mutate the frozen registry (forbidden in any lane)."""


def validate_cell_id(cell_id):
    """Return ``cell_id`` if it is one of the frozen three, else raise."""
    if cell_id not in EXACTLY_THREE_CELLS:
        raise UnknownCellError(
            "UnknownCellError: cell id %r is not in the frozen exactly-three "
            "registry %s for cycle %s (exactly_three_enforcement)"
            % (cell_id, list(EXACTLY_THREE_CELLS), CYCLE_ID)
        )
    return cell_id


def assert_registry_intact(candidate=None):
    """Assert a candidate registry equals the frozen exactly-three set."""
    if candidate is None:
        candidate = EXACTLY_THREE_CELLS
    got = tuple(sorted(set(candidate)))
    if got != EXACTLY_THREE_CELLS or len(list(candidate)) != 3:
        raise RegistryError(
            "RegistryError: cell registry %s != frozen exactly-three %s "
            "(cycle %s, three_cell_contract.json exactly_three_enforcement)"
            % (list(candidate), list(EXACTLY_THREE_CELLS), CYCLE_ID)
        )
    return EXACTLY_THREE_CELLS


def register_cell(*args, **kwargs):
    """Always raises: the registry is frozen. Lanes never write registries."""
    raise RegistryFrozenError(
        "RegistryFrozenError: the D2-CURIOSITY-V1 cell registry is frozen at "
        "exactly three cells %s; no lane may register cells (registry "
        "authority is researchctl only)" % (list(EXACTLY_THREE_CELLS),)
    )


# Import-time self-check: this module cannot be imported in a broken state.
assert_registry_intact()
