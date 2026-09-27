# Hosted gateway quickstart

No local server install is required. You need an existing **public HTTPS MCP server** that you control and a trusted client. Mithrandir rejects upstream URLs with embedded credentials, query strings, fragments, or private network destinations. For this pilot, send synthetic or public non-sensitive data.

1. Open [setup](https://mithrandir-production.up.railway.app/start), enter your upstream MCP URL, accept the service terms, and create an Observe gateway. An optional upstream `Authorization` value is supplied there and kept by Mithrandir; it is separate from the Mithrandir API key.
2. Save the issued API key securely. The setup tab displays it briefly and cannot recover it later.
3. Use **Check connection and discover tools** on that page. It calls `initialize` and `tools/list`, not a tool execution.
4. In VS Code, run **MCP: Open User Configuration**. Copy the generated configuration from setup into `mcp.json`. If you already have MCP servers, merge the new `inputs` and `servers.mithrandir` entries rather than replacing the entire file. It has this shape (replace only the gateway URL):

```json
{
  "inputs": [
    {"type": "promptString", "id": "mithrandir-key", "description": "Mithrandir API key", "password": true}
  ],
  "servers": {
    "mithrandir": {
      "type": "http",
      "url": "https://mithrandir-production.up.railway.app/gateway/YOUR_GATEWAY_ID/mcp",
      "headers": {"Authorization": "Bearer ${input:mithrandir-key}"}
    }
  }
}
```

5. Start the MCP server entry in VS Code and paste the key at its secure prompt. Never paste the key into the JSON file or commit it to GitHub.
6. On the setup page, review discovered tools and approve only the read-only tools you know have no side effects. `readOnlyHint: true` from an upstream is necessary but does not replace your review. Customer-supplied per-call costs are estimates, not provider-verified charges.
7. Run your normal agent workflow through this gateway. In Observe, all calls still reach your upstream. Check the proof on setup; a stronger economic assessment needs a representative workload and time window.

If you use another HTTP MCP client, configure its issued `/gateway/<id>/mcp` URL with `Authorization: Bearer <key>`. The service's public `/mcp` URL is a different server and will not route your upstream calls.

### Common setup failures

| Symptom | Check |
| --- | --- |
| 401 | The saved Mithrandir key and its bearer header; do not use your upstream key here. |
| Tool absent | Run `tools/list` through the gateway, and confirm the upstream exposes the tool. |
| No repeat evidence | Approve the tool, keep arguments exactly equal, allow stable results, and use stateless JSON reads. |
| No reuse in Observe | Expected: Observe always forwards. Optimize requires an entitlement and explicit gateway mode. |
| SSE or sessionful server | It can be forwarded, but exact response reuse does not apply to those calls. |

For the latest limits and terms, read the live [quickstart](https://mithrandir-production.up.railway.app/quickstart.json) and [service contract](https://mithrandir-production.up.railway.app/service-contract).
