"""PIT security master, membership, snapshots, S0 floors and sealed windows.

Synthetic fixtures only (no provider entitlement exists in this sprint).
"""

from __future__ import annotations

from datetime import date

import pytest

from research.assets.stocks.universe import (
    ACCEPTED,
    REJECTED,
    EligibilityInput,
    HistorySpan,
    MembershipBackfillError,
    MembershipRecord,
    MembershipTable,
    S0FloorViolation,
    SecurityMaster,
    SecurityMasterError,
    SecurityRecord,
    SealedWindowError,
    TickerRecord,
    UniverseError,
    UniverseRow,
    UniverseSnapshot,
    build_rebalance_snapshot,
    declare_sealed_windows,
    evaluate_delisting_retention,
    evaluate_s0_floors,
)

# --- synthetic security master ------------------------------------------------ #
DELIST_DATE = date(2022, 6, 17)
TICKER_CHANGE = date(2020, 1, 3)


def build_master() -> SecurityMaster:
    """One delisted name with a ticker change, one live name, one early delist."""
    return SecurityMaster(
        [
            SecurityRecord(
                security_id="SEC_DEL",
                primary_exchange="XNYS",
                listed_date=date(2012, 1, 3),
                ticker_history=(
                    TickerRecord("AAA", date(2012, 1, 3), date(2020, 1, 2)),
                    TickerRecord("AAB", TICKER_CHANGE, DELIST_DATE),
                ),
                delisted_date=DELIST_DATE,
                last_valid_event=DELIST_DATE,
            ),
            SecurityRecord(
                security_id="SEC_LIVE",
                primary_exchange="XNAS",
                listed_date=date(2014, 3, 4),
                ticker_history=(TickerRecord("BBB", date(2014, 3, 4), None),),
            ),
            SecurityRecord(
                security_id="SEC_SHORT",
                primary_exchange="XNYS",
                listed_date=date(2018, 5, 7),
                ticker_history=(
                    TickerRecord("CCC", date(2018, 5, 7), date(2019, 11, 29)),
                ),
                delisted_date=date(2019, 11, 29),
            ),
        ]
    )


class TestSecurityMaster:
    def test_ticker_history_is_effective_dated(self):
        master = build_master()
        assert master.ticker_as_of("SEC_DEL", date(2019, 12, 31)) == "AAA"
        assert master.ticker_as_of("SEC_DEL", date(2020, 1, 2)) == "AAA"
        assert master.ticker_as_of("SEC_DEL", TICKER_CHANGE) == "AAB"
        assert master.ticker_as_of("SEC_DEL", DELIST_DATE) == "AAB"
        # never-listed and post-delisting as-of dates resolve to nothing
        assert master.ticker_as_of("SEC_DEL", date(2012, 1, 2)) is None
        assert master.ticker_as_of("SEC_SHORT", date(2020, 1, 2)) is None

    def test_ticker_resolution_is_point_in_time(self):
        master = build_master()
        assert master.resolve_security_id("AAA", date(2019, 6, 28)) == "SEC_DEL"
        # the retired ticker must NOT resolve after the change: no backfill
        assert master.resolve_security_id("AAA", date(2021, 1, 4)) is None
        # the new ticker must NOT resolve before it became effective
        assert master.resolve_security_id("AAB", date(2019, 6, 28)) is None
        assert master.resolve_security_id("AAB", date(2021, 1, 4)) == "SEC_DEL"

    def test_membership_respects_listing_and_delisting(self):
        master = build_master()
        assert "SEC_SHORT" in master.members_as_of(date(2019, 6, 28))
        assert "SEC_SHORT" not in master.members_as_of(date(2020, 1, 2))
        # still a member ON the delisting date (inclusive range)
        assert "SEC_DEL" in master.members_as_of(DELIST_DATE)
        assert "SEC_DEL" not in master.members_as_of(date(2022, 6, 20))
        # before listing: not a member
        assert "SEC_LIVE" not in master.members_as_of(date(2014, 3, 3))
        assert "SEC_LIVE" in master.members_as_of(date(2014, 3, 4))

    def test_duplicate_security_id_rejected(self):
        base = build_master()
        with pytest.raises(SecurityMasterError, match="duplicate security_id"):
            SecurityMaster(list(base._by_id.values()) + [base.get("SEC_LIVE")])

    def test_discontiguous_ticker_history_rejected(self):
        with pytest.raises(SecurityMasterError, match="contiguous"):
            SecurityMaster(
                [
                    SecurityRecord(
                        security_id="X",
                        primary_exchange="XNYS",
                        listed_date=date(2020, 1, 2),
                        ticker_history=(
                            TickerRecord("XXX", date(2020, 1, 2), date(2020, 1, 30)),
                            TickerRecord("XXY", date(2020, 2, 5), None),
                        ),
                    )
                ]
            )

    def test_first_ticker_range_must_start_on_listing_date(self):
        with pytest.raises(SecurityMasterError, match="listing date"):
            SecurityMaster(
                [
                    SecurityRecord(
                        security_id="X",
                        primary_exchange="XNYS",
                        listed_date=date(2020, 1, 2),
                        ticker_history=(
                            TickerRecord("XXX", date(2020, 1, 3), None),
                        ),
                    )
                ]
            )

    def test_delisted_security_must_close_its_ticker_range(self):
        with pytest.raises(SecurityMasterError, match="delisted security"):
            SecurityMaster(
                [
                    SecurityRecord(
                        security_id="X",
                        primary_exchange="XNYS",
                        listed_date=date(2020, 1, 2),
                        ticker_history=(TickerRecord("XXX", date(2020, 1, 2), None),),
                        delisted_date=date(2021, 1, 4),
                    )
                ]
            )

    def test_overlapping_ticker_across_securities_rejected(self):
        with pytest.raises(SecurityMasterError, match="overlapping securities"):
            SecurityMaster(
                [
                    SecurityRecord(
                        security_id="P",
                        primary_exchange="XNYS",
                        listed_date=date(2020, 1, 2),
                        ticker_history=(TickerRecord("SHR", date(2020, 1, 2), None),),
                    ),
                    SecurityRecord(
                        security_id="Q",
                        primary_exchange="XNYS",
                        listed_date=date(2020, 1, 2),
                        ticker_history=(TickerRecord("SHR", date(2020, 1, 2), None),),
                    ),
                ]
            )

    def test_unknown_security_fails_closed(self):
        with pytest.raises(SecurityMasterError, match="unknown security_id"):
            build_master().get("NOPE")


class TestMembershipTable:
    def _table(self) -> MembershipTable:
        return MembershipTable(
            [
                MembershipRecord(
                    security_id="SEC_LIVE",
                    universe_id="UX1000",
                    effective_from=date(2021, 1, 4),
                    effective_to=date(2022, 12, 30),
                ),
                MembershipRecord(
                    security_id="SEC_DEL",
                    universe_id="UX1000",
                    effective_from=date(2021, 1, 4),
                    effective_to=None,
                ),
            ]
        )

    def test_membership_is_effective_dated_only(self):
        table = self._table()
        # before the effective range: NOT a member, even though the security
        # is listed and is a member "now" — no current-membership backfill.
        assert table.members_as_of(date(2020, 12, 31)) == ()
        assert "SEC_LIVE" in table.members_as_of(date(2021, 6, 30))
        # closed range expires
        assert "SEC_LIVE" not in table.members_as_of(date(2023, 1, 2))
        # open-ended range continues
        assert "SEC_DEL" in table.members_as_of(date(2023, 1, 2))
        assert table.members_as_of(date(2021, 6, 30), universe_id="UX1000") == (
            "SEC_DEL",
            "SEC_LIVE",
        )
        assert table.members_as_of(date(2021, 6, 30), universe_id="OTHER") == ()

    def test_structural_ban_no_current_members_accessor(self):
        forbidden = ("members", "current_members", "all_members", "latest_members",
                     "members_now", "constituents")
        present = {name for name in forbidden if hasattr(MembershipTable, name)}
        assert not present, f"MembershipTable leaked a non-as-of accessor: {present}"

    def test_membership_row_without_effective_from_cannot_exist(self):
        # effective_from is a mandatory constructor argument: a membership row
        # without effective dating cannot even be expressed.
        with pytest.raises(TypeError):
            MembershipRecord(security_id="S", universe_id="U")  # type: ignore[call-arg]

    def test_overlapping_membership_ranges_rejected(self):
        with pytest.raises(MembershipBackfillError, match="overlapping"):
            MembershipTable(
                [
                    MembershipRecord("S", "U", date(2020, 1, 2), date(2021, 1, 1)),
                    MembershipRecord("S", "U", date(2020, 6, 1), None),
                ]
            )


class TestRebalanceSnapshot:
    def _rule(self):
        def rule(metric: EligibilityInput) -> tuple[bool, str]:
            if (
                metric.median_dollar_volume >= 5_000_000
                and metric.history_days >= 500
            ):
                return True, "liquidity_and_history_floors_met"
            return False, "median_dollar_volume_or_history_below_floor"

        return rule

    def _metrics(self, master: SecurityMaster, decision: date):
        metrics = {}
        for security_id in master.members_as_of(decision):
            if security_id == "SEC_LIVE":
                metrics[security_id] = EligibilityInput(
                    security_id=security_id,
                    ticker="BBB",
                    decision_date=decision,
                    history_days=2500,
                    median_dollar_volume=1_000_000,  # rejected: thin
                    last_obs=date(2021, 6, 29),
                )
            else:
                metrics[security_id] = EligibilityInput(
                    security_id=security_id,
                    ticker="AAB",
                    decision_date=decision,
                    history_days=2400,
                    median_dollar_volume=50_000_000,
                    last_obs=date(2021, 6, 29),
                )
        return metrics

    def test_accepted_and_rejected_rows_both_retained_with_reasons(self):
        master = build_master()
        decision = date(2021, 6, 30)
        snapshot = build_rebalance_snapshot(
            master,
            universe_id="UX1000",
            decision_date=decision,
            metrics=self._metrics(master, decision),
            rule=self._rule(),
        )
        # SEC_DEL (via AAB) accepted, SEC_LIVE rejected, SEC_SHORT long gone
        assert snapshot.status_counts() == {ACCEPTED: 1, REJECTED: 1}
        accepted = snapshot.accepted()
        rejected = snapshot.rejected()
        assert [row.security_id for row in accepted] == ["SEC_DEL"]
        assert [row.security_id for row in rejected] == ["SEC_LIVE"]
        for row in accepted + rejected:
            assert row.reason.strip(), "every retained row needs a reason"
            assert row.ticker == master.ticker_as_of(row.security_id, decision)
        # digest is stable and identity-sensitive
        digest = snapshot.digest()
        assert digest == snapshot.digest()
        tampered = UniverseSnapshot(
            universe_id=snapshot.universe_id,
            decision_date=snapshot.decision_date,
            rows=tuple(
                UniverseRow(
                    security_id=r.security_id,
                    ticker=r.ticker,
                    decision_date=r.decision_date,
                    status=r.status,
                    reason=r.reason + "!",
                    history_days=r.history_days,
                    median_dollar_volume=r.median_dollar_volume,
                    last_obs=r.last_obs,
                )
                for r in snapshot.rows
            ),
        )
        assert tampered.digest() != digest

    def test_member_without_metrics_fails_closed(self):
        master = build_master()
        decision = date(2021, 6, 30)
        metrics = self._metrics(master, decision)
        del metrics["SEC_LIVE"]
        with pytest.raises(UniverseError, match="refusing to decide without data"):
            build_rebalance_snapshot(
                master,
                universe_id="UX1000",
                decision_date=decision,
                metrics=metrics,
                rule=self._rule(),
            )

    def test_rule_must_give_a_reason_even_for_rejections(self):
        master = build_master()
        decision = date(2021, 6, 30)
        with pytest.raises(UniverseError, match="reason is mandatory"):
            build_rebalance_snapshot(
                master,
                universe_id="UX1000",
                decision_date=decision,
                metrics=self._metrics(master, decision),
                rule=lambda m: (False, "   "),
            )


# --- S0 floors ------------------------------------------------------------------ #
def _eligible_histories():
    return {
        f"S{i:02d}": HistorySpan(
            security_id=f"S{i:02d}",
            first_obs=date(2010, 1, 4),
            last_obs=date(2018, 7, 2),
            eligible=True,
        )
        for i in range(32)
    }


class TestS0Floors:
    def _counts(self, n=32, decision=date(2016, 6, 30)):
        return {decision: n}

    def test_passing_configuration(self):
        problems = evaluate_s0_floors(
            histories=_eligible_histories(),
            eligible_counts_by_decision=self._counts(),
            latest_complete_date=date(2024, 7, 1),
            s0_end=date(2022, 6, 30),
        )
        assert problems == ()

    def test_history_floor_fails_below_eight_years(self):
        histories = _eligible_histories()
        histories["S00"] = HistorySpan("S00", date(2011, 6, 1), date(2018, 7, 2))
        problems = evaluate_s0_floors(
            histories=histories,
            eligible_counts_by_decision=self._counts(),
            latest_complete_date=date(2024, 7, 1),
            s0_end=date(2022, 6, 30),
        )
        assert any("history_floor" in p for p in problems)

    def test_ineligible_names_do_not_shrink_the_common_window(self):
        histories = _eligible_histories()
        # ineligible name with a tiny span must not affect the eligible window
        histories["XX"] = HistorySpan("XX", date(2017, 1, 3), date(2017, 2, 28),
                                      eligible=False)
        assert evaluate_s0_floors(
            histories=histories,
            eligible_counts_by_decision=self._counts(),
            latest_complete_date=date(2024, 7, 1),
            s0_end=date(2022, 6, 30),
        ) == ()

    def test_eligible_names_floor(self):
        problems = evaluate_s0_floors(
            histories=_eligible_histories(),
            eligible_counts_by_decision=self._counts(n=29),
            latest_complete_date=date(2024, 7, 1),
            s0_end=date(2022, 6, 30),
        )
        assert any("eligible_names_floor" in p for p in problems)

    def test_s0_separation_floor(self):
        problems = evaluate_s0_floors(
            histories=_eligible_histories(),
            eligible_counts_by_decision=self._counts(),
            latest_complete_date=date(2024, 7, 1),
            s0_end=date(2023, 12, 31),  # only ~6 months before latest complete
        )
        assert any("s0_separation_floor" in p for p in problems)

    def test_delisting_retention_floor_via_master(self):
        master = build_master()
        histories = {
            "SEC_DEL": HistorySpan("SEC_DEL", date(2012, 1, 3), date(2022, 6, 17)),
            "SEC_LIVE": HistorySpan("SEC_LIVE", date(2014, 3, 4), date(2022, 6, 17)),
            "SEC_SHORT": HistorySpan(
                "SEC_SHORT", date(2018, 5, 7), date(2019, 11, 29)
            ),
        }
        assert evaluate_delisting_retention(
            master,
            {
                "SEC_DEL": date(2022, 6, 17),
                "SEC_LIVE": date(2022, 6, 17),
                "SEC_SHORT": date(2019, 11, 29),
            },
        ) == ()
        problems = evaluate_s0_floors(
            histories=histories,
            eligible_counts_by_decision={date(2016, 6, 30): 2},
            latest_complete_date=date(2024, 7, 1),
            s0_end=date(2022, 6, 17),
            master=master,
            min_history_years=1.0,
            min_eligible_names=2,
        )
        assert problems == ()
        # a delisted name truncated before its final valid event is a violation
        histories["SEC_SHORT"] = HistorySpan(
            "SEC_SHORT", date(2018, 5, 7), date(2019, 11, 15)
        )
        problems = evaluate_s0_floors(
            histories=histories,
            eligible_counts_by_decision={date(2016, 6, 30): 2},
            latest_complete_date=date(2024, 7, 1),
            s0_end=date(2022, 6, 17),
            master=master,
            min_history_years=1.0,
            min_eligible_names=2,
        )
        assert any("SEC_SHORT" in p and "truncated" in p for p in problems)
        # a delisted name with NO observations at all is also a violation
        problems = evaluate_delisting_retention(
            master,
            {"SEC_LIVE": DELIST_DATE, "SEC_DEL": DELIST_DATE},
        )
        assert any("NO retained observations" in p and "SEC_SHORT" in p
                   for p in problems)

    def test_assert_variant_raises_aggregated(self):
        from research.assets.stocks.universe import assert_s0_floors

        with pytest.raises(S0FloorViolation) as excinfo:
            assert_s0_floors(
                histories=_eligible_histories(),
                eligible_counts_by_decision=self._counts(n=10),
                latest_complete_date=date(2024, 7, 1),
                s0_end=date(2024, 1, 31),
            )
        assert "eligible_names_floor" in str(excinfo.value)
        assert "s0_separation_floor" in str(excinfo.value)


class TestSealedWindows:
    def test_s0_usable_s1_sealed(self):
        windows = declare_sealed_windows(
            s0_start=date(2012, 1, 3),
            s0_end=date(2022, 6, 30),
            latest_complete_date=date(2024, 7, 1),
        )
        assert windows.s0_window() == (date(2012, 1, 3), date(2022, 6, 30))
        assert windows.s1_starts_on == date(2022, 7, 1)
        with pytest.raises(SealedWindowError):
            windows.s1_window()

    def test_boundary_touch_fails_closed(self):
        windows = declare_sealed_windows(
            s0_start=date(2012, 1, 3),
            s0_end=date(2022, 6, 30),
            latest_complete_date=date(2024, 7, 1),
        )
        windows.require_within_s0(date(2015, 1, 4), date(2022, 6, 30))
        with pytest.raises(SealedWindowError, match="sealed"):
            windows.require_within_s0(date(2022, 1, 3), date(2022, 7, 1))

    def test_buffer_violation_rejected_at_construction(self):
        with pytest.raises(UniverseError, match="months before the latest complete"):
            declare_sealed_windows(
                s0_start=date(2012, 1, 3),
                s0_end=date(2024, 1, 31),  # only ~5 months of separation
                latest_complete_date=date(2024, 7, 1),
            )

    def test_exact_twelve_month_buffer_allowed(self):
        windows = declare_sealed_windows(
            s0_start=date(2010, 1, 4),
            s0_end=date(2023, 7, 1),
            latest_complete_date=date(2024, 7, 1),
        )
        assert windows.s0_window()[1] == date(2023, 7, 1)
