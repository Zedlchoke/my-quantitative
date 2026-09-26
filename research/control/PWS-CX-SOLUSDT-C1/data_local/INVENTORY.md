# data_local/INVENTORY — sha256 of every file (PWS-CX-SOLUSDT-C1)

- Generated: recovery C1/C2 PIT-data-auditor lane, 2026-09-26, worktree
  `.worktrees/pws-cx-solusdt-c1/integration` branch `orca/pws-cx-solusdt-c1-integration`.
- Why this file exists: `data_local/` is ~12 GB (bookTicker monthly zips dominate),
  far above the 50 MB commit ceiling — **no zip is committed**. The klines 1h zips
  (72 files, 2.4 MB total) and the 6 bookTicker zips (12 GB) remain UNTRACKED on disk;
  every one of them is sha256-pinned below so any later re-download can be verified
  byte-exact before use. The funding JSONs (1.7 MB, not zips) ARE committed.
- Provenance: klines + bookTicker = Binance Vision keyless public archives
  (license: `licenses/Binance_Vision-Terms_of_Use.pdf`, sha-pinned below);
  funding = Binance fapi `/fapi/v1/fundingRate` public endpoint (CHR3F staging
  campaign 2026-09-23/24, H1 + H2 windows, merged).
- Cross-corpus check (prior lane, disclosed): the 72 klines zips are byte-identical
  (72/72 sha256) to the copy in the ETHUSDT-OPEN-SEARCH-V2 worktree at
  `.worktrees/ethusdt-open-search-v2/integration/research/control/ethusdt_open_search_v2/data_local/vision/klines_um_SOLUSDT_1h`
  — read-only comparison, no re-staging of that cycle's corpus.

| file | bytes | sha256 |
|---|---|---|
| `data_local/funding/MANIFEST_fapi_merged_SOLUSDT.json` | 253 | `698a6275a89bbe834f7b04fb3fafcc343d4735b2d0e5db4bb8731ddd446c7285` |
| `data_local/funding/SOLUSDT_funding.json` | 638513 | `9e850cb4e24cd309a3123fe9b3b3c543aef6f7e510ca36a7e241f5df4d5a1036` |
| `data_local/funding/fapi_scan2026_H1_SOLUSDT.json` | 721892 | `3dcac8d8f9064a433747fe5da84990f4c91cb5f0af05ccb602572368d87332c0` |
| `data_local/funding/fapi_scan2026a_H2_SOLUSDT.json` | 382534 | `3c5366492cce9e59110019c8b11309d8df4b30c8436796be15d0687383c1cb1c` |
| `data_local/vision/klines_um_SOLUSDT_1h_MANIFEST.json` | 6274 | `64286fdffc350f6595d5b19b363ca056d5d2d66d28db8e15abf6a716554d69cb` |
| `data_local/vision/bookTicker_um_SOLUSDT/SOLUSDT-bookTicker-2023-05.zip` | 353545384 | `394fa34c4e476278f2788518cdf8e58f21b0cb4d3c29191c05c99aa530400f8a` |
| `data_local/vision/bookTicker_um_SOLUSDT/SOLUSDT-bookTicker-2023-07.zip` | 1535718844 | `c00cd37641e534222b6072cdf2cdfe2fbfc6e86a7759a5e2b977c0db8cd1f1d5` |
| `data_local/vision/bookTicker_um_SOLUSDT/SOLUSDT-bookTicker-2023-09.zip` | 880613774 | `1137aac577b8522ab3b5e8d92ad7bb4614f693cc8906fe0c5d7eb07fc8ed9980` |
| `data_local/vision/bookTicker_um_SOLUSDT/SOLUSDT-bookTicker-2023-11.zip` | 2565674561 | `c3ebda1d7a36f3e12ea7add808535b0aa4f058ceaeaa0dde981e661390e17597` |
| `data_local/vision/bookTicker_um_SOLUSDT/SOLUSDT-bookTicker-2024-01.zip` | 3676029516 | `9a4bda3e66218bae8a73559761e10d573b51201a9450adce086f19591a57a1ab` |
| `data_local/vision/bookTicker_um_SOLUSDT/SOLUSDT-bookTicker-2024-03.zip` | 3952724227 | `c444869dcc1d0ec59e7933d21df9a5e509fcceb2d06beea705bfde288f68b966` |
| `data_local/vision/klines_um_SOLUSDT_1h/2020-09.zip` | 17124 | `bc926b98121dcb870999c4c8b0cdb72551bbb7ac9d6e00047bba34156fce3bb2` |
| `data_local/vision/klines_um_SOLUSDT_1h/2020-10.zip` | 30933 | `5f6131a244d980d631388ee504922b2bb09848e42cf6e3e59c933679887f5975` |
| `data_local/vision/klines_um_SOLUSDT_1h/2020-11.zip` | 30469 | `348047e07a306d93694a6c6cf0273a31e4b735740759e78ec9d39678e02d53a8` |
| `data_local/vision/klines_um_SOLUSDT_1h/2020-12.zip` | 31156 | `bd5f75cc091658b0794eb80777914b3d7e8940438da77980bd659a935f6bbd5d` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-01.zip` | 32709 | `fef310549a5baf8fcdb67a2c6c97a0ec05f25dbc87afbb2a0ba0f08842a52c27` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-02.zip` | 30285 | `029ec118946bf80d43f27baec8a80004265134c9540e7f9a04e440e453a43f99` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-03.zip` | 33547 | `94eaba4252ae9189c9be07ea2d40e3f016ee924a761462303882ffc9bb4e4e4c` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-04.zip` | 33681 | `21d8b0ffa824a3d4845f4e0103f9739a9931e4788a5da3958a0c8e4552552965` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-05.zip` | 34221 | `efb32d5fd15525744c959ce9685e20af8227b6104ea3b279faae0dc8d73cd4a3` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-06.zip` | 32420 | `8fe15facd01ac0eec8d23b04bc606f2c56344c1ee2aa88c3758c07a6cfeb5765` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-07.zip` | 32512 | `b1d3d3064ad1c48ee3db89da36f402ba27ed8764c14f5f8725db8c2d44412826` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-08.zip` | 33795 | `13a75507c7c6396782ca02659d2738a668a5b16a438d239b64199f19c69f81a0` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-09.zip` | 34447 | `11ee5441a6a3d72b10b501b1ac246bff97ee0673def1954d116ecd2b09f584ff` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-10.zip` | 34752 | `400e88409c92a5a01eb4c4b7b6e4f5fddfef93dd4a3d9c8f89cc35d51cc298ac` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-11.zip` | 33457 | `4939d7a971e30ac1d7b87c6c0352375bf8a0a539cd13bbf3e3920969a24bb42e` |
| `data_local/vision/klines_um_SOLUSDT_1h/2021-12.zip` | 33565 | `61d5be6bdb0fb8007898c8f61375a83fe466cd18f1fc67c53e6f42b8b8a34d07` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-01.zip` | 32432 | `bbe2ad04379133e2ca7b68cb5351b5ba610523c6a0d53b4ecfd628b972165cc3` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-02.zip` | 25915 | `36b1e2ff3ffe162718e61bb23ef84a104dc2cc5591c18cd8ce4c04e96655b84c` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-03.zip` | 31327 | `044c37d917fea58900c8ddf4086b9fc71fcadd55215a10680e1e7461ffa78265` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-04.zip` | 28601 | `1e4464fee6301816ff2efa7696d8cf53f34684b9b60616cf6af26e8cd75cfefc` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-05.zip` | 31712 | `6a8888b3d3d5a856d44eff5907210c30cc81fe210364f8b611726ad24b6846ba` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-06.zip` | 30869 | `0a550357320ba4954437b15b85f01bf0cc0c455f07f19e27ca91ddda19f1f147` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-07.zip` | 31308 | `05fc6f96bc940ae0d290b1039387c3a223b5159596819998563f34508594719a` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-08.zip` | 30967 | `971ab9bee4ad830767c285d3af6df5357af1bfa2ddb084fa49596cf9b5276036` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-09.zip` | 29608 | `41699bac620ac3f15318dd9238392fc5782d4321660e5c7986925eee3d172381` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-10.zip` | 29913 | `bc6bb18da0f2e30171cefad3d2df55a70d12e7eafed7b566225ae67e737be6cd` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-11.zip` | 31881 | `e156bc7231bfe31e21aaf5628260062aa9d59184ef075412ab0fa546dea1fd80` |
| `data_local/vision/klines_um_SOLUSDT_1h/2022-12.zip` | 31660 | `8f1fa76f20f0cd161f238d4e7014274969df3d3ab5e8b6c9e1dc8327e02ec2d5` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-01.zip` | 33659 | `0d7bc47dc3b49cbadd29274b63c02af8f23af40fe241412d357903ae945aa79d` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-02.zip` | 30128 | `1dc1a4ad1c82935fbe8b4c218f22087470b3a20cc2c1a394574ad1587ba5a828` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-03.zip` | 33039 | `c41bd78088a2bb8547f1b3bf5c89fcadd7606397d2a74f0961c47cf6754f8f8a` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-04.zip` | 31579 | `34aca0062513dbb81e99b4b6e2e0e2dd29b453e33c629c8cea1beeff9faf7543` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-05.zip` | 32149 | `4c5b1305d4395bb122f85b60520db8995c810357a2c189158b2beae2d116b1bc` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-06.zip` | 31775 | `023229af2e8a8900ee79ba088837b174acc52512f2e8296b02aa279cf97a82f5` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-07.zip` | 33478 | `e45b525229f485463a33f3c59f4dc3eafa2de1f9fbca8f2126cd3c074f62b6bb` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-08.zip` | 32603 | `d509bcda20054981e3f738ef1a33090dc12ddaea5593932e2545a285ee4987c9` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-09.zip` | 31342 | `99ac300173c437de0b735ca04ff7ac55512431eedd381795f2ba069edd9020c6` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-10.zip` | 33522 | `e9046fe166dd07107386312716030e66aad44136d40712b17b976ff9dd905bef` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-11.zip` | 33524 | `96c7b5324c80818622477b6d3fa71b82f62ae2266ec42f763433a11eef7494bb` |
| `data_local/vision/klines_um_SOLUSDT_1h/2023-12.zip` | 34912 | `5d7fea512037fe238b6133df8bec56231cf086b73a44bdff89e5dcdfb991d62f` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-01.zip` | 34837 | `eb8a8dc7685761609f19b403db0eb6655d757f720f71da9b8c1ab638ddfc85b9` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-02.zip` | 32441 | `7d87e385b8befd2c3fd6090475904fb6d28ec65d1afb1f1892570178bfba54ac` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-03.zip` | 35540 | `b679c264fc7d70ccf70d9fb25481bfed485a01c2cd439b8b698933b9398119c1` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-04.zip` | 34176 | `02fdeb42d8293094fab995cca7b33ef6fb18714d173e6da9e894119c734557e9` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-05.zip` | 34908 | `b22668d0d3fc2fb430efd5cca654dcf167b5df2d8997401f49d8e3f9ba43b3c8` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-06.zip` | 33318 | `80e770b293faa4ae6da7d149df3e1912da67bb121b58123260c7f4b755f4809d` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-07.zip` | 34792 | `da7072219268b51067972bf51032440ba3214d63df037180bc0c9e33a77ffa8b` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-08.zip` | 34981 | `08bc16fd25cb4b024ac2f3d187d4ed5426014e48808ea9523b9792b141dca34d` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-09.zip` | 33345 | `c99c50b8413b34318d5aa778b890d8d06d5c333c4db101570c1c9ee7e35b6451` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-10.zip` | 33909 | `ae94c6ea35e4b98c5a2e41a32a9d75e18793ced7c3e55c9e524a3e0c43ae75d7` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-11.zip` | 33016 | `620f261485e352e46458f683129cdf5141d2f70222a70b65228d6473f884ca81` |
| `data_local/vision/klines_um_SOLUSDT_1h/2024-12.zip` | 33906 | `bdb5c900670da54eac3653f7be69529dbfeb13574aa6072049ff1c419d7f5567` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-01.zip` | 34133 | `372c98abd2da7bbf5e3cbe39e77296efe8ef4e94790c3566da3e7313049be7b8` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-02.zip` | 30836 | `863aeb10c3a31a5a9da82bfbcd120740c0dfad5078a579366caf166f58aa9b34` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-03.zip` | 33026 | `04b504d8b18dd7e1dce1783add7bf40df0132e6aeb9932a46aa950abb36534c8` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-04.zip` | 35055 | `6d8784d0f2a936547897208aada8b57d65104bd3307cfad32fb39070fdec061c` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-05.zip` | 37400 | `b20e5bf7b4b3b3d5c0720ab2d845e03933ef08f15d3f06570b009463ba12bad9` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-06.zip` | 36082 | `72d6fb9cab913d98220a06a08eab70a361b5d3fe84ea9701420e5f2cc6600c7c` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-07.zip` | 37422 | `5493328c22d7804c5d64298e8ac475786eba0810cdb31ed6e6134f5720c5a2bc` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-08.zip` | 38009 | `ff753c960ffa6954d3ffbd9cf6f6a0f8d2b280753cf868ebe4732d0afa5a14fd` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-09.zip` | 36707 | `9cbc37023b21bc91802c38689466e2bb69eff22e55d6012c6feb0bb0bce56004` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-10.zip` | 37859 | `8d96a116ab53375ce88316e027fed319d625a35756122ed4af79d75584133b97` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-11.zip` | 36358 | `2a74a61262338c2cf49d65d3c2d8e5a27ccda3aadedeaeed87da0544b13fb372` |
| `data_local/vision/klines_um_SOLUSDT_1h/2025-12.zip` | 36683 | `7c25b753fd893dc697b5e7e8a1d0db904150181be7b7991cc05ba5b08f81cdf8` |
| `data_local/vision/klines_um_SOLUSDT_1h/2026-01.zip` | 36611 | `cc16e807c075689a73f096b7603c34f1eb289bb2d782ca8f6147e4c42632ed0e` |
| `data_local/vision/klines_um_SOLUSDT_1h/2026-02.zip` | 33200 | `fa733e5400163477fa7eb544a9a7e04b5c679656720ccb7f92787fcf33b739a3` |
| `data_local/vision/klines_um_SOLUSDT_1h/2026-03.zip` | 36150 | `5e9440665d3e4209c320e2dab897b5c3cec578800e669e1c8fd3503f157e49f1` |
| `data_local/vision/klines_um_SOLUSDT_1h/2026-04.zip` | 34581 | `2f466580c7e6d2e02a67a968428c0f9b987108cc1a3d2ba73061e329aacc208d` |
| `data_local/vision/klines_um_SOLUSDT_1h/2026-05.zip` | 35689 | `0d1aef19746005c140421825e55e482813330b19a82cbc24c792aaa0464778c2` |
| `data_local/vision/klines_um_SOLUSDT_1h/2026-06.zip` | 35026 | `5b6913a64843d8fbadeb1783a2ef064291355a33e6eee84f1a03c7e8786acfc8` |
| `data_local/vision/klines_um_SOLUSDT_1h/2026-07.zip` | 35322 | `4a88a47617d14ba94ae2154732ba724497a8cad66b1d7fd0dc4f88216101e0be` |
| `data_local/vision/klines_um_SOLUSDT_1h/2026-08.zip` | 35792 | `a25ab3dfcabcf739bd8bdd0aa9b1302865d5c571a5af1ffbb6e4a2b5c26ab833` |
| `licenses/Binance_Vision-Terms_of_Use.pdf` | 145552 | `94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b` |

## Verification status (independent recount by this lane)

- Klines: 72/72 zip sha256 re-verified against
  `C1_machine_KLINE_CENSUS_SOLUSDT.json`; full recount 52,145 bars, 0 duplicate
  open times, first 2020-09-14T07:00Z, last 2026-08-31T23:00Z, 120 missing bars =
  two venue maintenance windows (2022-02-26..28 = 72 bars; 2022-04-01..02 = 48 bars).
- Funding: H1+H2 merged (1 boundary duplicate dropped) n=6,580; mean/median/neg_share/worst
  reproduced to machine precision; 101 non-8h spacings confined to 2022-11-09T16:00Z..2022-11-18T08:00Z
  (99×1-4h + 2×5-7h; FTX-week emergency cadence — disclosed, not repaired).
- Spread: 2 sample months (2023-05 K=13, 2023-09 K=32) recomputed from raw zips —
  per-hour n/p50/p99 match the machine census (see C1_data_gate_REPORT.md).

Total files inventoried: 84
