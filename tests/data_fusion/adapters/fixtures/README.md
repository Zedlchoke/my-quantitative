# Data Fusion adapter fixtures — policy

Fixtures in this directory are tiny, hand-written files modeled on the
**documented public format** of their source.  None is production data,
none was downloaded from the network, and none contains a credential,
token or account reference.

Ownership: each lane engineer (A2 stocks, A3 macro, A4 forex) adds and owns
only the fixture files for its own sources.  Malformed, duplicate, timezone,
revision and conflict cases are derived from these files inside the lane's
tests by mutation, so the committed fixture set stays minimal.

Nothing here authorizes any source for research use; authority lives in
``research.data_fusion.authority`` and the owner-run registry.
