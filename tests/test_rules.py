import unittest
from datetime import date
from bot import demo, recommend

class RulesTests(unittest.TestCase):
    def setUp(self):
        self.day = date(2026, 10, 5)
        self.entries = demo(self.day)

    def test_cold_dry_morning(self):
        result = recommend(self.entries, self.day, 8, 10)
        self.assertIn('gloves', result)
        self.assertNotIn('rain trousers', result)

    def test_wet_evening(self):
        self.assertIn('rain trousers', recommend(self.entries, self.day, 17, 20))

    def test_missing_coverage_is_not_dry_weather(self):
        with self.assertRaises(RuntimeError):
            recommend([], self.day, 8, 10)

    def test_probability_triggers_without_rain_volume(self):
        entry = dict(self.entries[-1], rain={})
        self.assertIn('rain trousers', recommend([entry], self.day, 17, 20))

    def test_future_day_not_selected(self):
        with self.assertRaises(RuntimeError):
            recommend(self.entries, date(2026, 10, 6), 8, 10)

class DeliveryTests(unittest.TestCase):
    def test_delivery_posts_expected_message(self):
        from unittest.mock import patch, MagicMock
        import json
        from bot import send_telegram
        response = MagicMock()
        response.read.return_value = json.dumps({'ok': True}).encode()
        response.__enter__.return_value = response
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'fake', 'TELEGRAM_CHAT_ID': '123'}):
            with patch('bot.urlopen', return_value=response) as call:
                send_telegram('test message')
                self.assertIn(b'text=test+message', call.call_args.args[0].data)

    def test_missing_credentials_fail_before_network(self):
        from unittest.mock import patch
        from bot import send_telegram
        with patch.dict('os.environ', {}, clear=True), patch('bot.urlopen') as call:
            with self.assertRaises(RuntimeError):
                send_telegram('test')
            call.assert_not_called()
