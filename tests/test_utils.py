import unittest
from datetime import datetime
from app import create_app, db
from app.utils import make_week_top_and_bottom_day


class UtilsTestCase(unittest.TestCase):
    def test_make_week_top_and_bottom_day(self):
        the_time = datetime(2016, 7, 13)  # Wednesday
        top, bottom = make_week_top_and_bottom_day(the_time)
        self.assertEqual(top.day, 9)  # We want latest Saturday
        self.assertEqual(bottom.day, 3)  # 6 days ago

        the_time = datetime(2016, 7, 17)  # Sunday
        top, bottom = make_week_top_and_bottom_day(the_time)
        self.assertEqual(top.day, 16)  # We want latest Saturday
        self.assertEqual(bottom.day, 10)  # 6 days ago
