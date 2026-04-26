"""Tests for HelloAGENTS update-channel detection."""

import unittest
from unittest.mock import patch

from helloagents.core import version_check as vc


class VersionCheckTests(unittest.TestCase):
    def test_parse_github_repo_variants(self):
        cases = {
            "https://github.com/Micah123321/helloagents.git": ("Micah123321", "helloagents"),
            "git+https://github.com/Micah123321/helloagents.git": ("Micah123321", "helloagents"),
            "https://github.com/Micah123321/helloagents": ("Micah123321", "helloagents"),
            "git@github.com:Micah123321/helloagents.git": ("Micah123321", "helloagents"),
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(vc._parse_github_repo(url), expected)

    def test_maintenance_version_defaults_to_maintenance_branch(self):
        self.assertTrue(vc._is_maintenance_version("2.3.9+m"))
        self.assertTrue(vc._is_maintenance_version("2.3.9-m"))
        self.assertFalse(vc._is_maintenance_version("3.0.12"))
        self.assertEqual(vc._default_branch_for_version("2.3.9+m"), "dev/2.3.8")
        self.assertEqual(vc._default_branch_for_version("3.0.12"), "main")

    def test_detect_channel_prefers_requested_revision(self):
        direct_url = {"vcs_info": {"requested_revision": "feature/test"}}
        with patch.object(vc, "_read_direct_url", return_value=direct_url):
            self.assertEqual(vc._detect_channel("2.3.9+m"), "feature/test")

    def test_detect_channel_falls_back_to_maintenance_branch_for_m_build(self):
        with patch.object(vc, "_read_direct_url", return_value={}):
            self.assertEqual(vc._detect_channel("2.3.9+m"), "dev/2.3.8")

    def test_get_repo_url_prefers_direct_url(self):
        direct_url = {"url": "https://github.com/Micah123321/helloagents.git"}
        with patch.object(vc, "_read_direct_url", return_value=direct_url):
            self.assertEqual(vc._get_repo_url(), direct_url["url"])

    def test_fetch_latest_version_non_main_skips_release_api(self):
        with patch.object(vc, "_fetch_remote_version", return_value="2.3.9+m") as fetch_remote:
            with patch.object(vc, "urlopen") as urlopen:
                remote = vc.fetch_latest_version(
                    "dev/2.3.8",
                    repo_url="https://github.com/Micah123321/helloagents.git",
                    timeout=1,
                )
        self.assertEqual(remote, "2.3.9+m")
        fetch_remote.assert_called_once()
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
