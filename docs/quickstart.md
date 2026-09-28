# Hosted gateway quickstart

There is nothing to install locally. Bring an existing **public HTTPS MCP server** that you control and a trusted HTTP MCP client. Mithrandir rejects upstream URLs with embedded credentials, query strings, fragments or private network destinations. For this pilot, use synthetic or public non-sensitive data.

1. Open [setup](https://mithrandir-production.up.railway.app/start). Enter your existing upstream MCP URL, or paste a VS Code `mcp.json` / portable `.mcp.json` configuration to fill in a remote HTTP server. Review the URL before accepting the terms and creating a free Observe gateway. The imported JSON is cleared from the page after import. Local commands, unresolved credential variables, and non-Authorization custom headers cannot be imported.
2. Save the issued Mithrandir **account key** securely. The page shows it briefly and cannot recover it later. Mithrandir probes your upstream server: if it advertises OAuth, review the issuer, sign-in host and permissions, then open its provider link in a new browser tab to grant access. A public server can be discovered immediately. A server without compatible OAuth may require its own Bearer token instead. Provider grants are encrypted and scoped to this gateway or one bound subject.
3. Click **Install in VS Code** or **Install in Cursor** on setup. The editor may ask you to confirm the MCP server. On first connection, review the client and return address on Mithrandir's *separate* consent page, then enter the saved Mithrandir key. The install link contains the gateway URL only. This editor authorization does not expose an upstream token to the editor.
4. Mithrandir checks `initialize` and `tools/list` without calling a tool. If discovery fails, the page shows the error and offers a retry. Explicitly approve only reads known to be free of side effects and set a maximum result age and credible per-call cost. `readOnlyHint: true` is an upstream declaration, not a substitute for review.
5. If you want a controlled technical check, choose an approved read tool, enter public or synthetic JSON arguments, and explicitly authorize **three real upstream calls**. The upstream may charge for them. Mithrandir checks response stability and displays the proof; this short test is not a financial ROI result.
6. Route representative agent work through the gateway. Observe forwards **every** call to your upstream. Review the proof after real traffic; `shadow_reusable` is a verified repeat, not an avoided call. After a verified repeated approved read, click **Activate free Optimize** on this gateway. The test is bounded to 500 calls over 72 hours, including up to 100 successful reuse hits; no card is required.

## Connect from code

If you are writing an agent or MCP client, use the ready-to-run [JavaScript / Node.js](javascript.md) or [Go](go.md) example. Each accepts the issued gateway URL and a Mithrandir key, connects with the official MCP SDK, and lists the available tools. A tool is called only when you explicitly set `MCP_TOOL` and its JSON arguments. The examples use the API-key path; this does not require your application to implement a browser OAuth callback. The separate upstream OAuth grant, if needed, is completed on Mithrandir's setup or connect page.

## Manual VS Code configuration

If the one-click link does not open your editor, run **MCP: Open User Configuration** and merge the `mithrandir` entry into your existing `mcp.json`:

```json
{
  "servers": {
    "mithrandir": {
      "type": "http",
      "url": "https://mithrandir-production.up.railway.app/gateway/YOUR_GATEWAY_ID/mcp"
    }
  }
}
```

Start the server entry and complete the same consent step. Do not put your Mithrandir key in the OAuth configuration.

Use the **issued `/gateway/<id>/mcp` URL**, not the service's public `/mcp` endpoint, which exposes Mithrandir's own tools. The gateway URL alone does not make a local stdio server publicly accessible.

## Clients without OAuth

Legacy clients can send their Mithrandir key as `Authorization: Bearer <key>`. VS Code can prompt securely instead of putting the key in the configuration:

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

Merge both `inputs` and `servers.mithrandir` when you already have a user configuration. Never paste a real key directly into JSON or commit it to GitHub. The [comparison client](../examples/compare_gateway.py) uses this API-key path for raw HTTP measurements; it does not open a browser or perform OAuth login.

## Access for more than one person

| Mode | Who can call the gateway? | Upstream identity and reuse scope |
| --- | --- | --- |
| Account (default) | Holders of the gateway's account key, including an OAuth client authorized with it. | One upstream OAuth grant or Bearer credential and potentially shared eligible cached answers. Use only for reads safe to share among those holders. |
| Subject | Separately issued client keys, one per person or agent. The operator key manages subjects but cannot proxy their calls. | Each bound key can authorize its own upstream OAuth grant, or use a distinct Bearer token. Catalog, cache, replay and reported upstream cost are separated by subject and credential revision. |

For subject mode, use setup or the management API to create each subject, switch `authorization_scope` to `subject`, and give each person **only their bound Mithrandir client key**. Share the returned `/connect/{gateway_id}` link separately from the key. The person opens that link, enters their own key, and authorizes the upstream provider without an operator key. They also paste their bound key on Mithrandir's separate editor consent page. Rotate or revoke the subject when access changes; rotation clears its cached candidates and tool discovery. If the operator supplies a manual token, Mithrandir cannot verify it belongs to the named subject.

There are two distinct OAuth roles. For **upstream access**, Mithrandir discovers Protected Resource Metadata and the provider's metadata, prefers its hosted Client ID Metadata Document (CIMD), falls back to Dynamic Client Registration (DCR), checks PKCE state and issuer, encrypts the resulting grant and renews it when possible. A provider that supports neither registration method requires a manual token. For **editor access**, Mithrandir's gateway supports authorization code with S256 PKCE, protected-resource discovery, consent, rotating refresh tokens and DCR; this client-facing flow does **not** yet offer CIMD. Clients that require CIMD without DCR need the API-key path or another compatible client. See [compatibility details](compatibility.md).

## Common setup failures

| Symptom | Check |
| --- | --- |
| Upstream provider link absent | Check that your server advertises MCP OAuth Protected Resource Metadata and supports CIMD or DCR. Otherwise use its Bearer token. For multiple advertised providers, choose the intended issuer. |
| Editor OAuth page does not open | Verify the editor supports MCP OAuth and Dynamic Client Registration, and that the issued gateway URL is used without an Authorization header. |
| 401 after consent | Use the correct account key in account mode or the bound client key in subject mode. Complete both upstream and editor authorization if required. Retry after key rotation or revoked provider access. |
| Tool absent | Run `tools/list` through the gateway and verify the upstream exposes it for that account or subject. |
| No repeat evidence | Approve the tool, use exactly matching arguments and stable results, and stay within its TTL on stateless JSON reads. |
| No reuse in Observe | Expected: Observe always forwards. After a verified repeated approved read, explicitly activate free Optimize on the same gateway. |
| SSE or sessions | Completed bounded SSE and sessionful POST calls can pass through without reuse. Long-lived SSE, GET subscriptions and DELETE session termination are unsupported. |

For current limits and terms, read the live [machine-readable quickstart](https://mithrandir-production.up.railway.app/quickstart.json) and [service contract](https://mithrandir-production.up.railway.app/service-contract).
