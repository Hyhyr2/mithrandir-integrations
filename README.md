# Mithrandir integrations

Mithrandir is a hosted Savings Gateway for existing MCP servers. It forwards calls in free **Observe** mode and measures exact repeated reads. With an active Optimize entitlement, it can reuse eligible responses under explicit rules. A repeated call does not by itself prove a financial saving.

This public repository contains setup instructions and a small comparison client. The hosted server implementation, operational configuration, customer data, and credentials are not here. You do **not** need to clone or install this repository to use the hosted service.

## Get connected

1. Open [Mithrandir setup](https://mithrandir-production.up.railway.app/start). Bring an existing public HTTPS MCP endpoint that you control, or paste its VS Code / portable MCP JSON to fill the remote connection fields. During the pilot, use synthetic or public non-sensitive data.
2. Create a free Observe gateway and save its account key. The key is shown only briefly. It is used once at Mithrandir's OAuth consent page, and never placed in the editor installation link.
3. Click **Install in VS Code** or **Install in Cursor** on the setup page. Confirm the editor's MCP prompt, review the Mithrandir consent page, and enter the saved key. A manual configuration is available in [the quickstart](docs/quickstart.md).
4. Mithrandir checks the connection and discovers tools automatically. Explicitly approve only safe reads you trust; choose their maximum result age and supported per-call cost estimates. Discovery does not execute a tool.
5. To verify the mechanism without an agent prompt, you can choose an approved read, supply public or synthetic JSON arguments, and explicitly authorize three real upstream calls. Those calls may incur upstream costs. Inspect the proof, then route representative work through the gateway before deciding whether Optimize is worthwhile. [How the measurement works](docs/measurement.md).

The public [`/mcp`](https://mithrandir-production.up.railway.app/mcp) endpoint exposes Mithrandir's own tools. It does not proxy your MCP server. Your issued `/gateway/<id>/mcp` URL does.

**Access scope:** The default account mode shares eligible cached answers among holders of its account key. For reads whose results depend on a person's upstream permissions, an operator must issue a separate Mithrandir client key and provision a distinct upstream Bearer credential for each subject, then enable subject mode. In that mode the account key manages the gateway but cannot call its proxied tools. Mithrandir's OAuth authenticates the client to this gateway; it is not account sign-in or delegated OAuth to your upstream server. See [access and OAuth setup](docs/quickstart.md#access-for-more-than-one-person).

## Run a transparent comparison

[`examples/compare_gateway.py`](examples/compare_gateway.py) sends paired, identical read calls directly to your upstream and through an **existing** gateway. It reports full JSON result agreement, per-call time, Mithrandir route, and proof receipt identifiers. It does not create a gateway, buy a subscription, change modes, or authorize prepaid charges.

```bash
python examples/compare_gateway.py --help
```

Use fixed arguments to check the mechanism, then a representative trace to assess your own work. A short synthetic repeat is not a return-on-investment result. See [measurement setup and interpretation](docs/measurement.md).

The comparison script uses an API key for its raw HTTP calls; it does not run a browser OAuth flow. It supports the `2025-06-18` handshake by default and an explicit `--protocol 2026-07-28` stateless run. Its CI uses a local protocol fixture and mocked accounting, **not** a live paid gateway. See [tested compatibility](docs/compatibility.md).

## Current boundaries

| Supported by this example | Outside this example |
| --- | --- |
| HTTPS MCP POST with stateless JSON responses | Local stdio and private network upstreams |
| Exact, operator-approved, read-only `tools/call` | Effectful, sessionful, SSE, or long-lived stream reuse |
| Full JSON result comparison and measured request time | Inferred LLM token savings or independently verified provider bills |

Observe forwards every call to your upstream. `shadow_reusable` is evidence of a potential repeat, not an avoided call. Only a `reuse` route in Optimize represents an actual avoided upstream call. The [service contract](https://mithrandir-production.up.railway.app/service-contract), [pricing](https://mithrandir-production.up.railway.app/pricing), and [proof method](https://mithrandir-production.up.railway.app/proof) on the live service take precedence over this example.

The hosted Optimize subscription is currently advertised at **$24.50/month**, with up to **100,000 successful reuse hits per UTC month**. Those are included hits, not guaranteed savings. For example, at an independently established avoided upstream cost of $0.01 per call, more than 2,450 real reuse hits are needed just to cover the subscription, before other costs. Provider-reported costs and operator estimates are labeled separately; neither verifies a bill. Subscription cost cannot be assigned to an individual gateway's ROI without account-wide invoice attribution.

## Contributing and security

Documentation fixes and compatibility reports are welcome through GitHub issues. Do not post keys, request bodies, private upstream URLs, or customer results. For a sensitive issue, see [SECURITY.md](SECURITY.md). The MIT license applies to **this integration repository only**, not to the hosted Mithrandir service.
