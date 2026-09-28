# Connect from Go

This sample connects to **your existing Mithrandir gateway** and lists its tools. It makes no tool calls by default. You need Go 1.25+ and a gateway created at [Mithrandir setup](https://mithrandir-production.up.railway.app/start); Mithrandir itself stays hosted.

The Go example is source code in this repository. It is not published as a Go library or a GitHub Package. You can download a [versioned source archive](https://github.com/Hyhyr2/mithrandir-integrations/releases/latest) to pin the example, or follow the clone steps below. See [downloads and versioning](releases.md).

Copy the **issued** gateway URL (`/gateway/<id>/mcp`) and save the Mithrandir key shown during setup. If the upstream server uses OAuth, finish its provider authorization on the setup page first. Do not use the upstream provider token as your Mithrandir key. Clone this example repository, or [download its ZIP](https://github.com/Hyhyr2/mithrandir-integrations/archive/refs/heads/main.zip) and open the extracted folder.

### macOS / Linux

```bash
git clone https://github.com/Hyhyr2/mithrandir-integrations.git
cd mithrandir-integrations/examples/go
export MITHRANDIR_GATEWAY_URL='https://mithrandir-production.up.railway.app/gateway/YOUR_GATEWAY_ID/mcp'
read -rs MITHRANDIR_API_KEY && echo
export MITHRANDIR_API_KEY
go run .
```

### Windows PowerShell

```powershell
git clone https://github.com/Hyhyr2/mithrandir-integrations.git
cd mithrandir-integrations/examples/go
$env:MITHRANDIR_GATEWAY_URL = 'https://mithrandir-production.up.railway.app/gateway/YOUR_GATEWAY_ID/mcp'
$secret = Read-Host 'Mithrandir key' -AsSecureString
$env:MITHRANDIR_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
go run .
```

You should see `"connected": true` and a list of tool names. To **explicitly call** a tool whose effects and upstream costs you understand, set `MCP_TOOL` to one of those names and `MCP_ARGS_JSON` to its JSON object arguments, then rerun `go run .`. For example, in bash:

```bash
export MCP_TOOL='YOUR_APPROVED_READ_TOOL'
export MCP_ARGS_JSON='{"id":"public-example"}'
go run .
```

In PowerShell use `$env:MCP_TOOL = 'YOUR_APPROVED_READ_TOOL'` and `$env:MCP_ARGS_JSON = '{"id":"public-example"}'`. This optional call may charge your upstream provider. The default list is sufficient to confirm your connection.

The example uses the official [`modelcontextprotocol/go-sdk` v1.8](https://github.com/modelcontextprotocol/go-sdk) Streamable HTTP client. It provides the Mithrandir key through the SDK's Bearer token handler, so no password is stored in code or command arguments. The sample does not run an interactive OAuth client login. In subject mode, use your own bound client key: the account key manages subjects but cannot call their tools. See [access scopes](quickstart.md#access-for-more-than-one-person).

### If it fails

| Error | Check |
| --- | --- |
| Invalid URL | Use the **issued** `/gateway/<id>/mcp` URL, not Mithrandir's public `/mcp`. |
| 401 / 403 | Check the Mithrandir key and mode. If the upstream uses OAuth, reconnect that provider at `/connect/<id>`. |
| Empty tools | Inspect upstream discovery on `/start`; your upstream may expose no tools to this identity. |
| Tool not advertised | Run without `MCP_TOOL` first and copy the exact tool name. |
