import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from update_checker import (
    UpdateInfo, check_for_update, download_release_asset,
    parse_version, pick_platform_asset,
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

    def test_assets_are_collected(self):
        payload = {
            "tag_name": "v3.0.0",
            "html_url": "https://x",
            "assets": [
                {"name": "KI_Analysetool-macos.zip",
                 "browser_download_url": "https://x/macos.zip",
                 "size": 123},
                {"name": "ohne-url.zip"},  # wird ignoriert
            ],
        }
        with mock.patch("update_checker.urlopen",
                        return_value=self._mock_response(payload)):
            info = check_for_update("2.1.0")
        self.assertEqual(len(info.assets), 1)
        self.assertEqual(info.assets[0]["name"], "KI_Analysetool-macos.zip")


class TestPickPlatformAsset(unittest.TestCase):

    def _info(self):
        return UpdateInfo(
            current_version="2.1.0", latest_version="3.0.0",
            update_available=True,
            assets=[
                {"name": "KI_Analysetool-macos.zip", "url": "u1"},
                {"name": "KI_Analysetool-Windows.zip", "url": "u2"},
                {"name": "KI_Analysetool-Linux.zip", "url": "u3"},
            ])

    def test_macos(self):
        asset = pick_platform_asset(self._info(), platform="darwin")
        self.assertEqual(asset["url"], "u1")

    def test_windows(self):
        asset = pick_platform_asset(self._info(), platform="win32")
        self.assertEqual(asset["url"], "u2")

    def test_linux(self):
        asset = pick_platform_asset(self._info(), platform="linux")
        self.assertEqual(asset["url"], "u3")

    def test_no_matching_asset_returns_none(self):
        info = UpdateInfo(current_version="1", latest_version="2",
                          update_available=True,
                          assets=[{"name": "source.tar.gz", "url": "u"}])
        self.assertIsNone(pick_platform_asset(info, platform="darwin"))

    def test_empty_assets(self):
        info = UpdateInfo(current_version="1", latest_version="2",
                          update_available=True, assets=[])
        self.assertIsNone(pick_platform_asset(info, platform="linux"))


class TestDownloadReleaseAsset(unittest.TestCase):

    def _mock_response(self, data: bytes):
        response = mock.MagicMock()
        response.read = io.BytesIO(data).read
        response.headers = {"Content-Length": str(len(data))}
        response.__enter__ = lambda s: s
        response.__exit__ = mock.MagicMock(return_value=False)
        return response

    def test_download_writes_file_to_dest(self):
        asset = {"name": "KI_Analysetool-macos.zip",
                 "url": "https://x/app.zip"}
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("update_checker.urlopen",
                            return_value=self._mock_response(b"PK\x03\x04data")):
                path = download_release_asset(asset, dest_dir=Path(tmp))
            self.assertIsNotNone(path)
            self.assertEqual(path.name, "KI_Analysetool-macos.zip")
            self.assertEqual(path.read_bytes(), b"PK\x03\x04data")

    def test_failed_download_returns_none_and_cleans_up(self):
        asset = {"name": "x.zip", "url": "https://x/x.zip"}
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("update_checker.urlopen",
                            side_effect=OSError("offline")):
                path = download_release_asset(asset, dest_dir=Path(tmp))
            self.assertIsNone(path)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_missing_url_returns_none(self):
        self.assertIsNone(download_release_asset({"name": "x.zip"}))


if __name__ == "__main__":
    unittest.main()
