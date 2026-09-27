# Hosted gateway quickstart

There is nothing to install locally. Bring an existing **public HTTPS MCP server** that you control and a trusted HTTP MCP client. Mithrandir rejects upstream URLs with embedded credentials, query strings, fragments or private network destinations. For this pilot, use synthetic or public non-sensitive data.

1. Open [setup](https://mithrandir-production.up.railway.app/start), enter your upstream MCP URL, accept the service terms and create a free Observe gateway. If your upstream needs a Bearer token, supply that upstream credential in setup. It is separate from your Mithrandir key and is not copied into the client configuration.
2. Save the issued Mithrandir **account key** securely. The page shows it briefly and cannot recover it later. The new OAuth flow still needs this key at the consent page; OAuth is not a user account login.
3. Select **Check connection and discover tools** on setup. This performs discovery, not a tool call. Approve only reads that you know have no side effects. `readOnlyHint: true` is an upstream declaration and does not replace your review.
4. In VS Code, run **MCP: Open User Configuration**. Copy the issued gateway URL into `mcp.json` (merge its `servers.mithrandir` entry with your existing servers):

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

5. Start the Mithrandir server entry. An OAuth-capable client should open Mithrandir's consent page. Check the client name and return address, then paste your saved account key. The client receives a short-lived token restricted to this gateway; no key appears in `mcp.json`.
6. Run your usual agent workflow. Observe forwards **every** call to your upstream. Review the proof after representative traffic; `shadow_reusable` is an observed repeat, not a saving. Optimize needs an active entitlement and must be enabled for this gateway.

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
| Account (default) | Holders of the gateway's account key, including an OAuth client authorized with it. | One configured upstream credential and potentially shared eligible cached answers. Use only for reads safe to share among those holders. |
| Subject | Separately issued client keys, one per person or agent. The operator key manages subjects but cannot proxy their calls. | The operator must provision a **different upstream Bearer token** per subject. Catalog, cache, replay and reported upstream cost are separated by subject and credential revision. |

For subject mode, use the gateway controls on setup or the management API to create each subject with its own upstream Bearer token, switch `authorization_scope` to `subject`, and give each person **only their bound Mithrandir client key**. That person pastes the bound key on the OAuth consent page. Rotate or revoke the subject when upstream access changes; rotation clears its cached candidates and tool discovery. Mithrandir cannot verify that an operator-provided upstream token really belongs to the named person. OAuth on the client side does not obtain upstream OAuth tokens automatically.

The gateway currently supports authorization code with S256 PKCE, protected-resource discovery, consent, rotating refresh tokens and Dynamic Client Registration for public clients. It does **not** yet support Client ID Metadata Documents (CIMD) or sign-in with a third-party identity provider. Clients that require CIMD and do not support DCR need the API-key path or another compatible client. See [compatibility details](compatibility.md).

## Common setup failures

| Symptom | Check |
| --- | --- |
| OAuth page does not open | Verify the client supports MCP OAuth and Dynamic Client Registration, and that the issued gateway URL is used without an Authorization header. |
| 401 after consent | Use the correct account key in account mode or the bound client key in subject mode. Your upstream token is separate. Retry authorization after key rotation or revocation. |
| Tool absent | Run `tools/list` through the gateway and verify the upstream exposes it for that account or subject. |
| No repeat evidence | Approve the tool, use exactly matching arguments and stable results, and stay within its TTL on stateless JSON reads. |
| No reuse in Observe | Expected: Observe always forwards. Optimize requires an entitlement and explicit gateway mode. |
| SSE or sessions | Completed bounded SSE and sessionful POST calls can pass through without reuse. Long-lived SSE, GET subscriptions and DELETE session termination are unsupported. |

For current limits and terms, read the live [machine-readable quickstart](https://mithrandir-production.up.railway.app/quickstart.json) and [service contract](https://mithrandir-production.up.railway.app/service-contract).
