# Compatibility and verification

This integration kit tracks the hosted Mithrandir Savings Gateway after the September 27, 2026 client OAuth release. The gateway deployment and this repository have separate release cycles. Prefer the live [quickstart](https://mithrandir-production.up.railway.app/quickstart.json) and [service contract](https://mithrandir-production.up.railway.app/service-contract) if they disagree with this repository.

| Path | Documented support | What this repository verifies |
| --- | --- | --- |
| VS Code HTTP MCP + Mithrandir OAuth | Gateway URL alone; browser consent accepts an existing account or bound subject key. Protected-resource discovery, S256 PKCE and Dynamic Client Registration are supported by the service. | Configuration and expected flow are documented. CI does **not** drive an interactive VS Code login or token refresh against production. |
| HTTP MCP + API key | The issued gateway URL with `Authorization: Bearer <Mithrandir key>`. | The comparison script keeps direct upstream credentials separate from gateway credentials; a local HTTP fixture verifies request framing. |
| MCP 2025-06-18 | Handshake (`initialize`, `notifications/initialized`) and stateless JSON calls. A supported handshake-era counteroffer is followed on each leg. | Local protocol fixture runs the handshake and counteroffer over HTTP. |
| MCP 2026-07-28 | Explicit `--protocol 2026-07-28` uses `server/discover`, per-request `_meta`, `Mcp-Method` and `Mcp-Name` on tool calls. Both legs must support this revision. | Local protocol fixture checks header and body consistency. No full live upstream/gateway test runs in public CI. |
| Exact response reuse | Only approved, stable, stateless JSON `tools/call` reads are candidates; Observe forwards all calls. | Unit accounting covers upstream, shadow and reuse routes. It does not inspect a provider counter or invoice. |
| Streaming/session calls | Completed bounded SSE and sessionful POST may pass through without reuse. Long-lived SSE, GET subscriptions and DELETE termination are unsupported. | The comparison script deliberately rejects SSE and sessions. |

Mithrandir OAuth covers **client-to-gateway** authorization only. It does not obtain upstream OAuth tokens, provide third-party account sign-in, or support Client ID Metadata Documents (CIMD) yet. The [2026-07-28 MCP release](https://blog.modelcontextprotocol.io/posts/2026-07-28/) favors CIMD while retaining DCR for compatibility; check a client's registration support before selecting OAuth.

For a reproducible business claim, use an upstream server with an independently observable invocation counter, a consented representative trace, both routes in the same time window, and provider invoice or rate-card evidence. Publish the counter delta, full-result mismatches, latency distribution, verification outcomes, actual reuse hits and the subscription cost allocated to that workload. A synthetic loop proves only the mechanism.
