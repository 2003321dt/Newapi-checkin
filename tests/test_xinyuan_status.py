"""Offline checks for Xinyuan manual-verification check-in status."""
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from checkin import NewAPICheckin


class XinyuanStatusTests(unittest.TestCase):
    def setUp(self):
        self.today = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
        self.client = NewAPICheckin("https://xinyuanai666.com", "dummy-session", user_id="123")

    def test_calendar_record_confirms_checkin_without_post(self):
        self.client.get_checkin_history = Mock(return_value={
            "stats": {"records": [{"checkin_date": self.today}], "checked_in_today": True}
        })
        with patch.object(self.client.session, "post") as post:
            result = self.client.checkin()
        self.assertTrue(result["success"])
        self.assertEqual(result["checkin_date"], self.today)
        post.assert_not_called()

    def test_today_flag_confirms_checkin_without_records(self):
        self.client.get_checkin_history = Mock(return_value={
            "stats": {"checked_in_today": True, "records": []}
        })
        self.assertTrue(self.client._xinyuan_checked_in_today())

    def test_not_signed_reports_manual_verification_required(self):
        self.client.get_checkin_history = Mock(return_value={
            "stats": {"checked_in_today": False, "records": []}
        })
        response = SimpleNamespace(
            status_code=200,
            json=lambda: {"success": False, "message": "请先完成人机验证"},
        )
        with patch.object(self.client.session, "post", return_value=response) as post:
            result = self.client.checkin()
        self.assertFalse(result["success"])
        self.assertIn("人工", result["message"])
        post.assert_called_once()

    def test_other_sites_do_not_query_calendar_before_post(self):
        client = NewAPICheckin("https://other.example", "dummy", user_id="123")
        client.get_checkin_history = Mock(side_effect=AssertionError("unexpected calendar read"))
        response = SimpleNamespace(
            status_code=200,
            json=lambda: {
                "success": True,
                "message": "签到成功",
                "data": {"checkin_date": self.today, "quota_awarded": 5},
            },
        )
        with patch.object(client.session, "post", return_value=response):
            result = client.checkin()
        self.assertTrue(result["success"])
        client.get_checkin_history.assert_not_called()


if __name__ == "__main__":
    unittest.main()
