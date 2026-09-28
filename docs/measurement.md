# Measure the gateway without inventing savings

The public comparison client calls **your upstream** and **your existing Mithrandir gateway** with the same MCP `tools/call` arguments. It makes additional upstream calls and may incur your provider's normal charges. Start with public or synthetic non-sensitive data and a small sample.

## Before running

- Create an Observe gateway at [setup](https://mithrandir-production.up.railway.app/start), save its key, and discover the upstream catalog through the gateway.
- Select one read-only, non-destructive tool. Approve it in the gateway's `safe_read_tools` through setup. An upstream `readOnlyHint: true` is a declaration, not proof of safety.
- Use a public HTTPS, stateless MCP server that returns JSON rather than SSE for this comparison. The script rejects sessions and unsupported responses.
- Set `MCP_UPSTREAM_URL` to the original upstream URL and `MITHRANDIR_GATEWAY_URL` to the issued `/gateway/<id>/mcp` URL. They are different endpoints. If direct upstream access needs a credential, set the **full** `MCP_UPSTREAM_AUTHORIZATION` header in a trusted environment. The script never sends that value to the gateway.
- Set `MCP_TOOL` to the approved tool name. `MCP_ARGS_JSON` must be one JSON object accepted by that tool. The script prompts for the Mithrandir key if `MITHRANDIR_API_KEY` is unset.
- The raw comparison script authenticates with a Mithrandir API key; it does not run a browser OAuth flow. OAuth-capable clients can use the same gateway URL with browser consent for normal use. Use `--protocol 2026-07-28` only when **both** the upstream and the gateway support the stateless 2026 wire revision. The default is the widely used 2025-06-18 handshake; each leg follows a supported server counteroffer within the handshake era.

On Windows PowerShell, for example:

```powershell
$env:MCP_UPSTREAM_URL = 'https://your-public-mcp.example/mcp'
$env:MITHRANDIR_GATEWAY_URL = 'https://mithrandir-production.up.railway.app/gateway/YOUR_GATEWAY_ID/mcp'
$env:MCP_TOOL = 'your_approved_read_tool'
$env:MCP_ARGS_JSON = '{"id":"public-example"}'
python examples/compare_gateway.py --calls 5
```

Replace the tool and arguments with a valid read call. The script prompts for the Mithrandir API key; it does not write it to a file. For a representative workload, create a local JSON array of argument objects and run `python examples/compare_gateway.py --trace path/to/your-trace.json`. Do not commit a real customer trace. The sample in [`examples/trace.example.json`](../examples/trace.example.json) is illustrative and must be adapted to your tool's schema.

## What the output means

| Field | Interpretation |
| --- | --- |
| `full_result_matches` | Complete decoded MCP `result` objects agree for paired calls. JSON-RPC request IDs are excluded. Any mismatch needs investigation. |
| `direct_ms`, `gateway_ms` | Client-observed request time; p50/p95 are descriptive for this sample and depend on network and order. |
| `route: upstream` | The gateway called the upstream. |
| `route: shadow_reusable` | Observe saw a stable exact repeat, but **still called** the upstream. Actual avoided calls: zero. |
| `route: reuse` | With free Optimize active and within the test allowance, a response was delivered without that upstream call. |
| `route: verification_match` or `verification_mismatch` | Reliability check called the upstream; a mismatch serves the fresh result. |
| `receipt_id` | Identifier for the gateway's authenticated proof receipt; no third-party attestation is implied. |
| `route_reporting_complete` | False when the script sees an unknown or missing route. In that case `estimated_upstream_calls_for_gateway_leg` is `null`, rather than guessing that every unknown route called upstream. |

The script counts only observed routes from its own calls. It does not inspect provider invoices or infer LLM token savings. Its `estimated_upstream_calls_for_gateway_leg` assumes the route header describes the server's behavior; reconcile with an **independent upstream invocation counter** and the authenticated gateway savings/proof report before making a public claim. The direct leg also calls the upstream, so subtract those direct calls from a provider counter before attributing any difference to the gateway. Customer-entered upstream cost is **configured evidence**, not a verified charge. An upstream can report per-call cost in `X-Mithrandir-Upstream-Cost-Microusd` or MCP result metadata `io.mithrandir/costMicrousd`; Mithrandir labels that **provider-reported**, not independently invoiced. If no independent provider cost is known, monetary savings remain unknown.

## Two useful runs

1. **Mechanism check:** repeat identical arguments a few times. This can confirm exact matching, but manufactured repetition says little about real demand.
2. **Representative trace:** use genuine, consented read-only arguments from a normal workflow over time. Report the fraction of repeated eligible calls, full result agreement, route counts, distribution of latency, and independently supported upstream cost. Keep any identifying data private.

A mismatch may be caused by changing upstream data between paired calls, not necessarily by the gateway. A match in a short run does not prove that responses will remain fresh throughout a TTL. Check verification matches, mismatches, and prevented stale candidates over time.

A short run cannot establish the full decision-ready proof, which requires sufficient eligible traffic over 24 hours, reusable opportunities and cost coverage. In Observe the gateway cannot avoid upstream work. The script never switches the gateway's mode; enable the bounded free Optimize test on the setup page after one verified repeated read. Measure actual avoided calls, result agreement and provider cost evidence before claiming a financial saving. The test does not charge a Mithrandir fee; forwarded and verification calls may still cost money at your upstream. Check the live [proof method](https://mithrandir-production.up.railway.app/proof) and [test limits](https://mithrandir-production.up.railway.app/pricing).

The repository's CI exercises the script against a local protocol fixture and mocked route accounting. It does not connect to a live hosted gateway, reconcile an upstream invoice or certify production interoperability. See [compatibility](compatibility.md).
