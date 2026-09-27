import contextlib
import io
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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

    def test_unknown_route_does_not_become_an_upstream_call_estimate(self):
        records = [{"route": "unreported", "replayed": False, "equal": True,
                    "direct_ms": 1, "gateway_ms": 2}]
        summary = compare_gateway.summarize(records)
        self.assertFalse(summary["route_reporting_complete"])
        self.assertIsNone(summary["estimated_upstream_calls_for_gateway_leg"])

    def test_modern_wire_and_legacy_counteroffer_over_http(self):
        class MCPFixture(BaseHTTPRequestHandler):
            requests = []

            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                method = body["method"]
                self.requests.append((method, dict(self.headers), body["params"]))
                if method == "notifications/initialized":
                    self.send_response(204)
                    self.end_headers()
                    return
                if method == "initialize":
                    result = {"protocolVersion": "2025-11-25", "capabilities": {}}
                elif method == "server/discover":
                    result = {"supportedVersions": ["2026-07-28"]}
                elif method == "tools/list":
                    result = {"tools": [{"name": "public_read",
                                         "annotations": {"readOnlyHint": True}}]}
                elif method == "tools/call":
                    if self.headers.get("MCP-Protocol-Version") == "2026-07-28":
                        assert self.headers.get("Mcp-Method") == method
                        assert self.headers.get("Mcp-Name") == body["params"]["name"]
                        assert body["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] == "2026-07-28"
                    result = {"content": [{"type": "text", "text": "fixed"}]}
                else:
                    self.send_error(400)
                    return
                response = json.dumps({"jsonrpc": "2.0", "id": body["id"],
                                       "result": result}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

        server = ThreadingHTTPServer(("127.0.0.1", 0), MCPFixture)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/mcp"
            modern = compare_gateway.discover(url, None, "public_read",
                                               protocol=compare_gateway.MODERN_PROTOCOL)
            self.assertEqual(modern, compare_gateway.MODERN_PROTOCOL)
            result, _, _ = compare_gateway.post(url, None, "tools/call",
                                                 {"name": "public_read", "arguments": {}},
                                                 protocol=modern)
            self.assertEqual(result["content"][0]["text"], "fixed")
            legacy = compare_gateway.discover(url, None, "public_read",
                                               protocol=compare_gateway.LEGACY_PROTOCOL)
            self.assertEqual(legacy, "2025-11-25")
            compare_gateway.post(url, None, "tools/call",
                                 {"name": "public_read", "arguments": {}}, protocol=legacy)
            methods = [request[0] for request in MCPFixture.requests]
            self.assertEqual(methods, ["server/discover", "tools/list", "tools/call",
                                       "initialize", "notifications/initialized",
                                       "tools/list", "tools/call"])
            headers = {key.lower(): value for key, value in MCPFixture.requests[-1][1].items()}
            self.assertEqual(headers["mcp-protocol-version"], "2025-11-25")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
