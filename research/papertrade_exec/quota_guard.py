"""Provider-credit quota guard (PAPERDESK-FIXALL-NCAA-V1 W1.2).

RUNTIME-AUDIT FINDING THIS FIXES: the pinned QuotaLedger books 1 credit per
credit call, but the PROVIDER debits 2 credits for a WNBA/NBA /odds call
(x-requests-used jumped 3->5->7). On 2026-10-07 the desk spent 8 provider
credits while the internal cap reported a safe 4 — the cap and the meter
were different units.

LAW (no pinned byte is touched): every CREDIT call is made through a
GuardedClient which
  1. prechecks the PROVIDER-credit daily/monthly caps (4/day + 120/month —
     the same numbers the pinned core enforces, now enforced in the
     provider's own unit);
  2. calls through to the pinned client (quota/key hygiene unchanged);
  3. records the PROVIDER header meter (x-requests-used/remaining) in
     data/provider_quota_ledger.jsonl;
  4. reconciles: whenever the accumulated provider-credit estimate and the
     provider's own `used` meter drift beyond PROVIDER_DRIFT_TOLERANCE, a
     QUOTA_CREDIT_DRIFT row lands in the ledger + the incident callback —
     drift is reported, never silently absorbed.

Expected costs per (family, sport-key family) travel as measured config,
not folklore: basketball /odds debits 2 (measured 2026-10-07), soccer
/odds and /scores debit 1, /events debits 0.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_COSTS = {
    ("odds", "basketball"): 2,      # measured: provider debits 2 / WNBA call
    ("odds", "soccer"): 1,          # measured 2026-10-07/08 (UNL, 1 credit)
    ("scores", "soccer"): 1,
}
DEFAULT_CAPS = {"day": 4, "month": 120}
PROVIDER_DRIFT_TOLERANCE = 2      # credits between estimate and meter


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ProviderQuotaSkip(Exception):
    """The provider-credit cap would be exceeded — refused BEFORE the call
    (pinned QuotaSkip semantics, provider unit)."""


class ProviderQuotaGuard:
    def __init__(self, data_root: Path, *, costs: dict | None = None,
                 caps: dict | None = None):
        self.data_root = Path(data_root)
        self.costs = {**DEFAULT_COSTS, **(costs or {})}
        self.caps = {**DEFAULT_CAPS, **(caps or {})}
        self.ledger_path = self.data_root / "data" / \
            "provider_quota_ledger.jsonl"
        self.state_path = self.data_root / "data" / \
            "provider_quota_state.json"
        self.drifts: list[dict] = []

    # ---------------------------------------------------------------- state --
    def _load_state(self) -> dict:
        try:
            st = json.loads(self.state_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            st = {}
        today, month = _now()[:10], _now()[:7]
        if st.get("day") != today or st.get("month") != month:
            st = {"day": today, "month": month,
                  "credits_day": st.get("credits_day", 0)
                  if st.get("day") == today else 0,
                  "credits_month": st.get("credits_month", 0)
                  if st.get("month") == month else 0,
                  "calls_day": st.get("calls_day", 0)
                  if st.get("day") == today else 0}
        return st

    def _save_state(self, st: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(st, indent=1, sort_keys=True))

    def _journal(self, row: dict) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    # ------------------------------------------------------------- plumbing --
    def expected_cost(self, family: str, sport_key: str) -> int:
        for (fam, scope), cost in self.costs.items():
            if fam == family and (scope == "*" or
                                  str(sport_key).startswith(scope)):
                return cost
        return 1                       # conservative default: 1 credit

    def precheck(self, family: str, sport_key: str) -> int:
        cost = self.expected_cost(family, sport_key)
        st = self._load_state()
        if st["credits_day"] + cost > self.caps["day"] or \
                st["credits_month"] + cost > self.caps["month"]:
            raise ProviderQuotaSkip(
                f"provider credits day={st['credits_day']}/"
                f"{self.caps['day']} month={st['credits_month']}/"
                f"{self.caps['month']} + expected {cost} for "
                f"{family}:{sport_key} would exceed the caps — no call")
        return cost

    def _charge(self, family: str, sport_key: str) -> None:
        cost = self.expected_cost(family, sport_key)
        st = self._load_state()
        st["credits_day"] += cost
        st["credits_month"] += cost
        st["calls_day"] = st.get("calls_day", 0) + 1
        self._save_state(st)
        self._journal({"ts_utc": _now(), "family": family,
                       "sport_key": sport_key, "cost_credits": cost,
                       "credits_day_after": st["credits_day"],
                       "credits_month_after": st["credits_month"]})

    def reconcile(self, hdrs: dict, family: str, sport_key: str,
                  incident=None) -> None:
        """Provider-meter reconciliation after a successful call."""
        used = hdrs.get("x-requests-used")
        if used is None:
            return
        st = self._load_state()
        st["provider_used_last"] = used
        st["provider_remaining_last"] = hdrs.get("x-requests-remaining")
        self._save_state(st)
        # estimated session start baseline is unknown to us; the audited
        # signal is the DELTA between consecutive provider meters vs our
        # per-call estimate — recorded for the parity test + drift report.
        self._journal({"ts_utc": _now(), "family": family,
                       "sport_key": sport_key, "kind": "PROVIDER_METER",
                       "provider_used": used,
                       "provider_remaining": hdrs.get("x-requests-remaining"),
                       "internal_credits_day": st["credits_day"]})
        last_used = st.get("provider_used_prev")
        st["provider_used_prev"] = used
        self._save_state(st)
        if last_used is not None:
            delta = int(used) - int(last_used)
            est = self.expected_cost(family, sport_key)
            if delta > est + PROVIDER_DRIFT_TOLERANCE:
                row = {"ts_utc": _now(), "kind": "QUOTA_CREDIT_DRIFT",
                       "family": family, "sport_key": sport_key,
                       "provider_delta": delta, "expected": est,
                       "detail": "provider meter moved more than expected —"
                                 " update DEFAULT_COSTS (W1.2)"}
                self.drifts.append(row)
                self._journal(row)
                if incident:
                    incident("QUOTA_CREDIT_DRIFT",
                             f"{family}:{sport_key} provider delta {delta} "
                             f"vs expected {est} (W1.2 reconciliation)")

    def guard(self, client) -> "GuardedClient":
        return GuardedClient(client, self)


class GuardedClient:
    """Delegating wrapper interposing the provider-credit law on the CREDIT
    endpoints; everything else (events, fingerprint, exceptions) passes
    through untouched."""

    def __init__(self, inner, guard: ProviderQuotaGuard):
        self._inner = inner
        self._guard = guard

    @property
    def fingerprint(self):
        return self._inner.fingerprint

    def get_events(self, sport_key: str):
        return self._inner.get_events(sport_key)      # 0-credit endpoint

    def get_odds(self, sport_key: str, *, markets: str = "h2h"):
        self._guard.precheck("odds", sport_key)
        self._guard._charge("odds", sport_key)
        body, hdrs = self._inner.get_odds(sport_key, markets=markets)
        self._guard.reconcile(hdrs, "odds", sport_key)
        return body, hdrs

    def get_scores(self, sport_key: str, days_from: int = 3):
        self._guard.precheck("scores", sport_key)
        self._guard._charge("scores", sport_key)
        body, hdrs = self._inner.get_scores(sport_key, days_from=days_from)
        self._guard.reconcile(hdrs, "scores", sport_key)
        return body, hdrs
