"""Compare exact MCP reads directly and through an existing Mithrandir gateway.

No gateway creation, mode change, purchase, or prepaid authorization is performed.
The script requires a stateless HTTPS MCP server with JSON responses.
"""
from __future__ import annotations

import argparse
import getpass
import json
import math
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlsplit

LEGACY_PROTOCOL = "2025-06-18"
MODERN_PROTOCOL = "2026-07-28"
HANDSHAKE_PROTOCOLS = {"2025-03-26", "2025-06-18", "2025-11-25"}
CLIENT_INFO = {"name": "mithrandir-comparison", "version": "1.1"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def https_url(value: str, *, gateway: bool = False) -> str:
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("MCP URLs must use HTTPS without embedded credentials")
    if parts.query or parts.fragment:
        raise ValueError("MCP URLs must not contain a query or fragment")
    if gateway and ("/gateway/" not in parts.path or not parts.path.endswith("/mcp")):
        raise ValueError("Use the issued /gateway/<id>/mcp URL, not the public /mcp endpoint")
    return value


def post(url: str, authorization: str | None, method: str, params: dict,
         *, protocol: str = LEGACY_PROTOCOL, notification: bool = False) -> tuple[dict, float, dict]:
    request_id = uuid.uuid4().hex
    request_params = dict(params)
    if protocol == MODERN_PROTOCOL:
        request_params["_meta"] = {
            "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL,
            "io.modelcontextprotocol/clientCapabilities": {},
            "io.modelcontextprotocol/clientInfo": CLIENT_INFO,
        }
    elif protocol not in HANDSHAKE_PROTOCOLS:
        raise ValueError(f"Unsupported MCP protocol version: {protocol}")
    body = {"jsonrpc": "2.0", "method": method, "params": request_params}
    if not notification:
        body["id"] = request_id
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream",
               "MCP-Protocol-Version": protocol}
    if protocol == MODERN_PROTOCOL:
        headers["Mcp-Method"] = method
        if method == "tools/call":
            headers["Mcp-Name"] = request_params["name"]
    if authorization:
        headers["Authorization"] = authorization
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers=headers, method="POST")
    started = time.perf_counter()
    try:
        with OPENER.open(request, timeout=45) as response:
            raw = response.read(2_000_001)
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            status = response.status
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"MCP {method} returned HTTP {exc.code}") from None
    elapsed_ms = (time.perf_counter() - started) * 1000
    if len(raw) > 2_000_000:
        raise RuntimeError("Response exceeds this example's 2 MB limit")
    if response_headers.get("mcp-session-id"):
        raise RuntimeError("Sessionful MCP is outside this exact-reuse comparison")
    if notification:
        if status >= 400:
            raise RuntimeError(f"MCP notification failed with HTTP {status}")
        return {}, elapsed_ms, response_headers
    if "application/json" not in response_headers.get("content-type", ""):
        raise RuntimeError("This example requires JSON responses, not SSE")
    payload = json.loads(raw)
    if payload.get("id") != request_id:
        raise RuntimeError("MCP response ID differs from the request ID")
    if "error" in payload:
        raise RuntimeError(f"MCP {method} returned JSON-RPC error: {payload['error']}")
    if "result" not in payload:
        raise RuntimeError("MCP response has no result")
    return payload["result"], elapsed_ms, response_headers


def discover(url: str, authorization: str | None, tool_name: str,
             *, protocol: str = LEGACY_PROTOCOL) -> str:
    if protocol == MODERN_PROTOCOL:
        discovery, _, _ = post(url, authorization, "server/discover", {}, protocol=protocol)
        if MODERN_PROTOCOL not in discovery.get("supportedVersions", []):
            raise RuntimeError("The server does not advertise MCP 2026-07-28")
    else:
        init, _, _ = post(url, authorization, "initialize", {
            "protocolVersion": protocol, "capabilities": {}, "clientInfo": CLIENT_INFO,
        }, protocol=protocol)
        negotiated = init.get("protocolVersion")
        if negotiated not in HANDSHAKE_PROTOCOLS:
            raise RuntimeError("The server negotiated an unsupported MCP version")
        protocol = negotiated
        post(url, authorization, "notifications/initialized", {},
             protocol=protocol, notification=True)
    cursor = None
    tool = None
    for _ in range(10):
        catalog, _, _ = post(url, authorization, "tools/list",
                             {"cursor": cursor} if cursor else {}, protocol=protocol)
        tool = next((item for item in catalog.get("tools", [])
                     if item.get("name") == tool_name), None)
        if tool:
            break
        cursor = catalog.get("nextCursor")
        if not cursor:
            break
    if not tool:
        raise RuntimeError(f"Tool {tool_name!r} is absent from tools/list")
    hints = tool.get("annotations") or {}
    if hints.get("readOnlyHint") is not True or hints.get("destructiveHint") is True:
        raise RuntimeError("Only explicitly read-only, non-destructive tools are accepted")
    return protocol


def arguments(args: argparse.Namespace) -> list[dict]:
    if args.trace:
        values = json.loads(Path(args.trace).read_text(encoding="utf-8"))
        if not isinstance(values, list) or not values or len(values) > 500:
            raise ValueError("Trace must be a nonempty JSON array of at most 500 argument objects")
    else:
        values = [json.loads(args.arguments)] * args.calls
    if not all(isinstance(value, dict) for value in values):
        raise ValueError("Every tools/call arguments value must be a JSON object")
    return values


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(fraction * len(ordered)) - 1)], 2)


def summarize(records: list[dict]) -> dict:
    routes = sorted({record["route"] for record in records})
    direct = [record["direct_ms"] for record in records]
    gateway = [record["gateway_ms"] for record in records]
    forwarded_routes = {"upstream", "shadow_reusable", "verification_match",
                        "verification_mismatch"}
    reported_routes = forwarded_routes | {"reuse"}
    routes_complete = all(record["route"] in reported_routes for record in records)
    return {
        "paired_calls": len(records),
        "full_result_matches": sum(record["equal"] for record in records),
        "full_result_mismatches": sum(not record["equal"] for record in records),
        "observed_actual_reuse": sum(record["route"] == "reuse" and not record["replayed"]
                                     for record in records),
        "observed_shadow_opportunities": sum(record["route"] == "shadow_reusable"
                                              for record in records),
        "direct_ms": {"p50": percentile(direct, .5), "p95": percentile(direct, .95)},
        "gateway_ms": {"p50": percentile(gateway, .5), "p95": percentile(gateway, .95)},
        "gateway_routes": {route: {"count": sum(r["route"] == route for r in records),
                                   "p50_ms": percentile([r["gateway_ms"] for r in records
                                                          if r["route"] == route], .5)}
                           for route in routes},
        "route_reporting_complete": routes_complete,
        "estimated_upstream_calls_for_gateway_leg": (
            sum(record["route"] in forwarded_routes for record in records)
            if routes_complete else None),
        "upstream_cost_usd": "unknown unless independently measured or supplied",
        "llm_token_savings": "not measured",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", default=os.getenv("MCP_TOOL"), required=not bool(os.getenv("MCP_TOOL")))
    parser.add_argument("--arguments", default=os.getenv("MCP_ARGS_JSON", "{}"))
    parser.add_argument("--calls", type=int, default=5)
    parser.add_argument("--trace", help="JSON array of real tools/call argument objects")
    parser.add_argument("--protocol", choices=[LEGACY_PROTOCOL, MODERN_PROTOCOL],
                        default=LEGACY_PROTOCOL,
                        help="MCP wire revision for both legs (default: %(default)s)")
    args = parser.parse_args()
    if not 1 <= args.calls <= 500:
        parser.error("--calls must be between 1 and 500")
    try:
        direct_url = https_url(os.environ["MCP_UPSTREAM_URL"])
        gateway_url = https_url(os.environ["MITHRANDIR_GATEWAY_URL"], gateway=True)
        gateway_key = os.getenv("MITHRANDIR_API_KEY") or getpass.getpass("Mithrandir API key: ")
        if not gateway_key:
            raise ValueError("MITHRANDIR_API_KEY is empty")
        sample = arguments(args)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    upstream_auth = os.getenv("MCP_UPSTREAM_AUTHORIZATION")
    gateway_auth = f"Bearer {gateway_key}"
    direct_protocol = discover(direct_url, upstream_auth, args.tool, protocol=args.protocol)
    gateway_protocol = discover(gateway_url, gateway_auth, args.tool, protocol=args.protocol)
    records = []
    for index, tool_args in enumerate(sample):
        results = {}
        for leg in (("direct", "gateway") if index % 2 == 0 else ("gateway", "direct")):
            url, auth = ((direct_url, upstream_auth) if leg == "direct"
                         else (gateway_url, gateway_auth))
            results[leg] = post(url, auth, "tools/call",
                                {"name": args.tool, "arguments": tool_args},
                                protocol=direct_protocol if leg == "direct" else gateway_protocol)
        direct_result, direct_ms, _ = results["direct"]
        gateway_result, gateway_ms, headers = results["gateway"]
        records.append({"pair": index + 1, "equal": direct_result == gateway_result,
                        "direct_ms": round(direct_ms, 2), "gateway_ms": round(gateway_ms, 2),
                        "route": headers.get("x-mithrandir-route", "unreported"),
                        "mode": headers.get("x-mithrandir-gateway-mode", "unreported"),
                        "replayed": headers.get("x-replayed", "false").lower() == "true",
                        "receipt_id": headers.get("x-mithrandir-proof-receipt")})
    print(json.dumps({"summary": summarize(records), "calls": records}, indent=2))
    return 0 if all(record["equal"] for record in records) else 2


if __name__ == "__main__":
    raise SystemExit(main())
