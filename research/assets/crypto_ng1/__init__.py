"""CRYPTO-NG1 asset package: platform v3 data-plane adoption (P0).

Consumption of the frozen S4 series happens ONLY through
``research.assets.crypto_ng1.plane_adapter`` (the consume_via_plane
shape: AuthorityRegistry verdict -> CADS resolve verify-on-read ->
manifest-verified query).  Open data files are never read directly in
scored code.
"""
