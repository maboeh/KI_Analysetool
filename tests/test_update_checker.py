import json
import unittest
from unittest import mock

from update_checker import (
    UpdateInfo, check_for_update, parse_version,
)


class TestParseVersion(unittest.TestCase):

    def test_plain_version(self):
        self.assertEqual(parse_version("2.1.0"), (2, 1, 0))

    def test_tag_with_v_prefix(self):
        self.assertEqual(parse_version("v3.0.1"), (3, 0, 1))

    def test_partial_version(self):
        self.assertEqual(parse_version("2.5"), (2, 5))

    def test_empty(self):
        self.assertEqual(parse_version(""), (0,))
        self.assertEqual(parse_version(None), (0,))


class TestCheckForUpdate(unittest.TestCase):

    def _mock_response(self, payload):
        response = mock.MagicMock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        response.__enter__ = lambda s: s
        response.__exit__ = mock.MagicMock(return_value=False)
        return response

    def test_newer_version_detected(self):
        payload = {
            "tag_name": "v9.9.9",
            "html_url": "https://github.com/x/releases/tag/v9.9.9",
            "body": "Neue Features",
        }
        with mock.patch("update_checker.urlopen",
                        return_value=self._mock_response(payload)):
            info = check_for_update("2.1.0")
        self.assertTrue(info.update_available)
        self.assertEqual(info.latest_version, "9.9.9")
        self.assertIsNone(info.error)

    def test_same_version_no_update(self):
        payload = {"tag_name": "v2.1.0", "html_url": "https://x", "body": ""}
        with mock.patch("update_checker.urlopen",
                        return_value=self._mock_response(payload)):
            info = check_for_update("2.1.0")
        self.assertFalse(info.update_available)

    def test_older_release_no_update(self):
        payload = {"tag_name": "v1.0.0", "html_url": "https://x", "body": ""}
        with mock.patch("update_checker.urlopen",
                        return_value=self._mock_response(payload)):
            info = check_for_update("2.1.0")
        self.assertFalse(info.update_available)

    def test_network_error_returns_error_info(self):
        with mock.patch("update_checker.urlopen",
                        side_effect=OSError("offline")):
            info = check_for_update("2.1.0")
        self.assertFalse(info.update_available)
        self.assertIsNotNone(info.error)
        self.assertIsNone(info.latest_version)

    def test_missing_tag_returns_error(self):
        with mock.patch("update_checker.urlopen",
                        return_value=self._mock_response({})):
            info = check_for_update("2.1.0")
        self.assertIsNotNone(info.error)


if __name__ == "__main__":
    unittest.main()
