import contextlib
import io
import json
import os
import sys
import unittest
from unittest.mock import patch

from examples import compare_gateway


class ComparisonTests(unittest.TestCase):
    def test_paired_accounting_and_separate_credentials(self):
        calls = []
        routes = iter(["upstream", "shadow_reusable", "reuse"])

        def fake_post(url, authorization, method, params, **kwargs):
            calls.append((url, authorization, method))
            if method != "tools/call":
                raise AssertionError("Discovery is stubbed for this test")
            headers = {"x-mithrandir-route": next(routes), "x-replayed": "false"} \
                if "/gateway/" in url else {}
            return {"content": [{"type": "text", "text": "same result"}]}, 10.0, headers

        env = {"MCP_UPSTREAM_URL": "https://upstream.example/mcp",
               "MITHRANDIR_GATEWAY_URL": "https://mithrandir.example/gateway/example/mcp",
               "MITHRANDIR_API_KEY": "sample-key", "MCP_TOOL": "public_read",
               "MCP_ARGS_JSON": '{"id":"public"}'}
        output = io.StringIO()
        with patch.dict(os.environ, env), patch.object(sys, "argv", ["compare_gateway", "--calls", "3"]), \
             patch.object(compare_gateway, "discover"), patch.object(compare_gateway, "post", fake_post), \
             contextlib.redirect_stdout(output):
            self.assertEqual(compare_gateway.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["summary"]["full_result_matches"], 3)
        self.assertEqual(report["summary"]["observed_actual_reuse"], 1)
        self.assertEqual(report["summary"]["observed_shadow_opportunities"], 1)
        self.assertEqual(report["summary"]["estimated_upstream_calls_for_gateway_leg"], 2)
        self.assertEqual(sum(url.startswith("https://upstream") for url, _, _ in calls), 3)
        self.assertEqual({auth for url, auth, _ in calls if "/gateway/" in url}, {"Bearer sample-key"})
        self.assertEqual({auth for url, auth, _ in calls if "upstream.example" in url}, {None})

    def test_gateway_url_is_not_public_discovery_endpoint(self):
        with self.assertRaises(ValueError):
            compare_gateway.https_url("https://mithrandir.example/mcp", gateway=True)
        with self.assertRaises(ValueError):
            compare_gateway.https_url("https://user:secret@example.com/mcp")


if __name__ == "__main__":
    unittest.main()
