"""CRYPTO V14 implementation-lane family packages (Phase V14-I).

One subpackage per selected family, one lane per family (plan
``PLAN_crypto_v14.md`` section 9): each package exposes the same plugin
interface the V14 driver (adapted by A1 from the frozen V13 cell runner)
consumes mechanically -- ``cost_model()``, decision stamps, folds, universe,
one book per arm, preflight digests.
"""
