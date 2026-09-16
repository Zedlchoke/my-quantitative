from research.free_data_frontier.sources.ofr import (
    CURATED_MNEMONICS,
    full_series_url,
    mnemonics_url,
)


def test_ofr_inventory_uses_documented_metadata_route():
    url = mnemonics_url()
    assert url == "https://data.financialresearch.gov/v1/metadata/mnemonics/"
    assert "/v1/mnemonics/" not in url


def test_ofr_full_series_uses_query_endpoint():
    assert full_series_url("FNYR-SOFR-A") == (
        "https://data.financialresearch.gov/v1/series/full/?mnemonic=FNYR-SOFR-A"
    )
    assert "/timeseries/FNYR-SOFR-A" not in full_series_url("FNYR-SOFR-A")


def test_ofr_curated_reference_rate_set_is_frozen():
    assert CURATED_MNEMONICS == (
        "FNYR-SOFR-A",
        "FNYR-EFFR-A",
        "FNYR-BGCR-A",
        "FNYR-TGCR-A",
        "FNYR-OBFR-A",
    )
