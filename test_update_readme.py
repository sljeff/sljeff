import io
import json
import sys
import unittest
import urllib.error
from unittest import mock


class UpdateReadmeTest(unittest.TestCase):
    def test_import_does_not_fetch_network(self):
        sys.modules.pop("update_readme", None)
        with mock.patch(
            "urllib.request.urlopen",
            side_effect=AssertionError("network called at import"),
        ):
            __import__("update_readme")

    def test_build_wakatime_section_renders_top_languages(self):
        import update_readme

        stats = {
            "data": {
                "languages": [
                    {"name": "Markdown", "text": "5 hrs 3 mins", "percent": 19.6},
                    {"name": "Rust", "text": "3 hrs 12 mins", "percent": 12.4},
                ]
            }
        }

        section = update_readme.build_wakatime_section(stats)

        self.assertIn("#### 📊 Weekly development breakdown", section)
        self.assertIn("```text", section)
        self.assertIn("Markdown   5 hrs 3 mins", section)
        self.assertIn("19.6%", section)
        self.assertIn("Rust       3 hrs 12 mins", section)

    def test_build_wakatime_section_rejects_missing_languages(self):
        import update_readme

        with self.assertRaisesRegex(ValueError, "missing data.languages"):
            update_readme.build_wakatime_section({"data": {"error": "bad api key"}})

    def test_replace_wakatime_section_preserves_surrounding_readme_structure(self):
        import update_readme

        readme = """<td valign=\"top\" width=\"50%\">

<!-- waka-box start -->
old content
<!-- waka-box end -->

</td>"""

        updated = update_readme.replace_wakatime_section(readme, "new content")

        self.assertIn("<td valign=\"top\" width=\"50%\">", updated)
        self.assertIn("<!-- waka-box start -->\nnew content\n<!-- waka-box end -->", updated)
        self.assertIn("</td>", updated)
        self.assertNotIn("old content", updated)

    def _mock_response(self, payload):
        return io.BytesIO(json.dumps(payload).encode())

    def test_fetch_wakatime_stats_uses_bearer_without_fallback_on_success(self):
        import update_readme

        auth_headers = []

        def fake_urlopen(request, timeout=None):
            auth_headers.append(request.get_header("Authorization"))
            return self._mock_response({"data": {"languages": []}})

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            stats = update_readme.fetch_wakatime_stats("oauth-token")

        self.assertEqual(stats, {"data": {"languages": []}})
        self.assertEqual(auth_headers, ["Bearer oauth-token"])

    def test_fetch_wakatime_stats_falls_back_to_basic_on_401(self):
        import update_readme

        auth_headers = []

        def fake_urlopen(request, timeout=None):
            auth_headers.append(request.get_header("Authorization"))
            if len(auth_headers) == 1:
                raise urllib.error.HTTPError(
                    request.full_url, 401, "UNAUTHORIZED", None, None
                )
            return self._mock_response({"data": {"languages": []}})

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            stats = update_readme.fetch_wakatime_stats("api-key")

        self.assertEqual(stats, {"data": {"languages": []}})
        self.assertEqual(len(auth_headers), 2)
        self.assertTrue(auth_headers[0].startswith("Bearer "))
        self.assertTrue(auth_headers[1].startswith("Basic "))

    def test_fetch_wakatime_stats_raises_when_both_auth_methods_rejected(self):
        import update_readme

        with mock.patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                "https://example.com", 401, "UNAUTHORIZED", None, None
            ),
        ):
            with self.assertRaises(urllib.error.HTTPError):
                update_readme.fetch_wakatime_stats("bad-token")


if __name__ == "__main__":
    unittest.main()
