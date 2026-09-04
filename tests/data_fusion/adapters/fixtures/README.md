# Data Fusion adapter fixtures

Every file in this directory is a tiny hand-written fixture modeled on the
**documented public format** of its source.  None of them is production
data, none was downloaded from the network, and none contains a credential,
token or account reference.  Malformed/duplicate/revision cases are derived
from these files inside the tests by mutation, so the fixture set stays
minimal.

| file | source / format | hand-computed content |
| --- | --- | --- |
| `sec_submissions.json` | SEC EDGAR `submissions/CIK##########.json` shape | CIK 1, two filings; filing dates 2024-01-03 (with acceptanceDateTime) and 2024-01-08 (empty acceptance) |
| `sec_companyfacts.json` | SEC EDGAR XBRL `companyfacts/CIK##########.json` shape | CIK 1; one instant fact `us-gaap:Assets` (USD 5000, filed 2024-01-08) and one duration fact `us-gaap:Revenues` (skipped in V1) |
| `ecb_sdmx_exr.json` | ECB Data API SDMX-JSON 2.0 shape (EXR dataflow) | series `D.EUR.USD.SP00.A`; EUR/USD reference rates 1.0951 (2024-01-02) and 1.0969 (2024-01-03) |
| `bis_cbpol.json` | BIS Data API SDMX-JSON shape (WS_CBPOL) | series `US.P`; policy rate 4.0 effective 2024-03-20 and 4.25 effective 2024-05-01 |
| `finra_shortsale_volume.txt` | FINRA Reg SHO daily short-sale-volume pipe file | 2024-01-02; AAPL 1000/100/5000 market B; MSFT 2000/0/7000 market Q |
| `truefx_ticks_usdjpy.csv` | TrueFX monthly archive CSV member | USD/JPY ticks 20240101 22:00:00.000 (141.102/141.132) and 20240102 00:00:00.123 (141.085/141.115) |
| `fred_vintagedates.json` | FRED API `file_type=json` vintagedates array | CPIAUCSL-style vintage dates 2024-01-12 and 2024-02-09 |
| `fred_alfred_obs.json` | ALFRED observations (`file_type=json`) | one 2023-12-01 observation in two vintages (272.712 then revised 272.690) plus one `.` missing value |

Expected values quoted in the table are the numbers asserted by the tests;
nothing here authorizes any source for research use.
