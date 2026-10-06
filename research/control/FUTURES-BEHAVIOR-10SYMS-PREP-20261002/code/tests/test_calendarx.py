"""Calendar placeholder tests + fixture determinism tests."""
import datetime as dt
import hashlib
import tempfile
import unittest
from pathlib import Path

from futbt.calendarx import (WeekdayCalendar, calendar_from_bars,
                             require_real_calendar)
from futbt.synth import FIXTURE_DESCRIPTION, build_universe
from futbt.taxonomy import EvidenceTag, PolicyError


class TestWeekdayCalendar(unittest.TestCase):
    def setUp(self):
        self.cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 3, 31))

    def test_sessions_are_weekdays_only(self):
        for s in self.cal.sessions():
            self.assertLess(s.weekday(), 5)

    def test_last_session_before(self):
        # Jan 1 2026 is Thursday; before Feb 1 (Sunday) -> Fri Jan 30
        self.assertEqual(self.cal.last_session_before(dt.date(2026, 2, 1)),
                         dt.date(2026, 1, 30))
        self.assertEqual(self.cal.last_session_before(dt.date(2026, 1, 5)),
                         dt.date(2026, 1, 2))  # Mon Jan 5 -> Fri Jan 2

    def test_next_prev_session(self):
        self.assertEqual(self.cal.next_session(dt.date(2026, 1, 2)),
                         dt.date(2026, 1, 5))
        self.assertEqual(self.cal.prev_session(dt.date(2026, 1, 5)),
                         dt.date(2026, 1, 2))

    def test_provenance_is_postulated_not_run(self):
        self.assertEqual(self.cal.provenance().tag, EvidenceTag.POSTULATED)
        self.assertIn("NOT_RUN", self.cal.provenance().note)


class TestRealCalendarPlaceholder(unittest.TestCase):
    def test_require_real_calendar_raises_not_run(self):
        with self.assertRaisesRegex(PolicyError, "NOT_RUN"):
            require_real_calendar("official roll-date session times")


class TestEmpiricalCalendar(unittest.TestCase):
    def test_built_from_bars_union(self):
        cal = calendar_from_bars([dt.date(2026, 1, 5), dt.date(2026, 1, 6),
                                  dt.date(2026, 1, 5)], tz="US/Eastern")
        self.assertEqual(cal.sessions(), [dt.date(2026, 1, 5),
                                          dt.date(2026, 1, 6)])
        self.assertEqual(cal.tz_name(), "US/Eastern")
        self.assertEqual(cal.provenance().tag, EvidenceTag.OBSERVED)


class TestFixtureDeterminism(unittest.TestCase):
    def test_same_seed_same_bytes(self):
        with tempfile.TemporaryDirectory() as t1, \
                tempfile.TemporaryDirectory() as t2:
            u1 = build_universe(t1, seed=20261002)
            u2 = build_universe(t2, seed=20261002)
            self.assertEqual(sorted(u1.files_written),
                             sorted(u2.files_written))
            for name in u1.files_written[:12]:
                h1 = hashlib.sha256(Path(t1, name).read_bytes()).hexdigest()
                h2 = hashlib.sha256(Path(t2, name).read_bytes()).hexdigest()
                self.assertEqual(h1, h2, name)

    def test_fixture_description_documents_pathologies(self):
        self.assertIn("close-only", str(FIXTURE_DESCRIPTION))
        self.assertIn("NEGATIVE", str(FIXTURE_DESCRIPTION))
        self.assertIn("DST NOT", str(FIXTURE_DESCRIPTION))


if __name__ == "__main__":
    unittest.main()
