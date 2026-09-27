"""Exercise the published Node/Go examples against an authenticated MCP endpoint.

This is a local protocol fixture, not a live customer gateway or a savings test.
"""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "2026-07-28"


class GatewayFixture(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *_args):
        pass

    def do_GET(self):
        # A short-lived inspection client needs only POST responses.
        self.send_error(405)

    def do_POST(self):
        if self.path != "/gateway/gw_fixture/mcp":
            self.send_error(404)
            return
        if self.headers.get("Authorization") != "Bearer fixture-key":
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Bearer error="invalid_token"')
            self.end_headers()
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            method = body["method"]
            params = body.get("params", {})
            if self.headers.get("Mcp-Protocol-Version") != PROTOCOL:
                raise ValueError("protocol header missing")
            if self.headers.get("Mcp-Method") != method:
                raise ValueError("method header differs from body")
            if params["_meta"]["io.modelcontextprotocol/protocolVersion"] != PROTOCOL:
                raise ValueError("request metadata differs from protocol")

            if method == "server/discover":
                result = {
                    "resultType": "complete",
                    "supportedVersions": [PROTOCOL],
                    "capabilities": {"tools": {}},
                    "_meta": {"io.modelcontextprotocol/serverInfo":
                              {"name": "fixture", "version": "1.0.0"}},
                }
            elif method == "tools/list":
                result = {"resultType": "complete", "ttlMs": 0,
                          "cacheScope": "private", "tools": [
                    {"name": "public_read", "description": "Synthetic read",
                     "inputSchema": {"type": "object", "properties":
                                     {"id": {"type": "string"}}},
                     "annotations": {"readOnlyHint": True}}
                ]}
            elif method == "tools/call":
                if (self.headers.get("Mcp-Name") != "public_read" or
                        params.get("name") != "public_read" or
                        params.get("arguments") != {"id": "public-example"}):
                    raise ValueError("unexpected tool call")
                result = {"resultType": "complete", "content":
                          [{"type": "text", "text": "fixture result"}]}
            else:
                raise ValueError("unexpected MCP method: " + method)
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))
            return

        self.requests.append(method)
        response = json.dumps({"jsonrpc": "2.0", "id": body["id"],
                               "result": result}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def exercise(language, env, tool=None):
    sample = ROOT / "examples" / language
    if language == "javascript":
        cmd = ["node", "client.mjs"]
    elif language == "go":
        cmd = ["go", "run", "."]
    else:
        raise ValueError("language must be javascript or go")
    values = dict(env)
    values.pop("MCP_TOOL", None)
    values.pop("MCP_ARGS_JSON", None)
    if tool:
        values.update(MCP_TOOL=tool, MCP_ARGS_JSON='{"id":"public-example"}')
    completed = subprocess.run(cmd, cwd=sample, env=values, text=True,
                               capture_output=True, timeout=180, check=False)
    if completed.returncode:
        raise AssertionError(f"{language} failed: {completed.stderr}")
    return json.loads(completed.stdout)


def main(language):
    GatewayFixture.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), GatewayFixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = dict(os.environ,
                   MITHRANDIR_GATEWAY_URL=f"http://127.0.0.1:{server.server_port}/gateway/gw_fixture/mcp",
                   MITHRANDIR_API_KEY="fixture-key")
        listing = exercise(language, env)
        assert listing == {"connected": True, "tools": ["public_read"]}, listing
        assert "tools/call" not in GatewayFixture.requests, GatewayFixture.requests

        called = exercise(language, env, tool="public_read")
        assert called["connected"] and called["tools"] == ["public_read"], called
        assert called["call"]["content"][0]["text"] == "fixture result", called
        assert GatewayFixture.requests.count("tools/call") == 1, GatewayFixture.requests

        bad_env = dict(env, MITHRANDIR_API_KEY="wrong-fixture-key")
        command = ["node", "client.mjs"] if language == "javascript" else ["go", "run", "."]
        rejected = subprocess.run(command, cwd=ROOT / "examples" / language,
                                  env=bad_env, text=True, capture_output=True,
                                  timeout=180, check=False)
        assert rejected.returncode != 0, "invalid key unexpectedly accepted"
        assert "wrong-fixture-key" not in rejected.stdout + rejected.stderr
        assert GatewayFixture.requests.count("tools/call") == 1, GatewayFixture.requests
        print(f"{language}: authenticated discovery, listing, opt-in call and key rejection OK")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    main(sys.argv[1])
