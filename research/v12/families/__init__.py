"""V12 family implementations (Phase I implementation lanes).

One subpackage per eligible frozen family.  Each subpackage wires its own
plugin (:class:`research.adapter_v10.base.GenericStrategyBase` subclass),
frozen-identity primitives, evidence builders and golden fixtures.  A1's
centralized wiring commit registers the plugins; nothing here edits central
publication, ledgers or freezes.
"""
