# Connect from JavaScript / Node.js

This sample connects to **your existing Mithrandir gateway** and lists its tools. It makes no tool calls by default. You need Node.js 22+ and a gateway created at [Mithrandir setup](https://mithrandir-production.up.railway.app/start); the hosted service needs no Python installation on your machine.

For the fewest local steps, download the `mithrandir-connect` npm tarball and checksum from the [latest GitHub Release](https://github.com/Hyhyr2/mithrandir-integrations/releases/latest), verify it, and run `npm install -g ./hyhyr2-mithrandir-connect-<version>.tgz`. Then follow the environment setup below and run `mithrandir-connect` in place of `node client.mjs`. The [release guide](releases.md) covers verification and optional GitHub Packages installation. To inspect or change the example source, use the clone instructions below.

Copy the **issued** gateway URL (`/gateway/<id>/mcp`) and save the Mithrandir key shown during setup. If your upstream server uses OAuth, complete its provider authorization on the setup page first. These are separate credentials: never use an upstream token as `MITHRANDIR_API_KEY`. Clone this example repository, or [download its ZIP](https://github.com/Hyhyr2/mithrandir-integrations/archive/refs/heads/main.zip) and open the extracted folder.

### macOS / Linux

```bash
git clone https://github.com/Hyhyr2/mithrandir-integrations.git
cd mithrandir-integrations/examples/javascript
npm ci
export MITHRANDIR_GATEWAY_URL='https://mithrandir-production.up.railway.app/gateway/YOUR_GATEWAY_ID/mcp'
read -rs MITHRANDIR_API_KEY && echo
export MITHRANDIR_API_KEY
node client.mjs
```

### Windows PowerShell

```powershell
git clone https://github.com/Hyhyr2/mithrandir-integrations.git
cd mithrandir-integrations/examples/javascript
npm ci
$env:MITHRANDIR_GATEWAY_URL = 'https://mithrandir-production.up.railway.app/gateway/YOUR_GATEWAY_ID/mcp'
$secret = Read-Host 'Mithrandir key' -AsSecureString
$env:MITHRANDIR_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
node client.mjs
```

You should see `"connected": true` and an array of tool names. To **explicitly call** one tool whose effects and upstream costs you understand, set `MCP_TOOL` to a name from that list and `MCP_ARGS_JSON` to its JSON object arguments, then rerun `node client.mjs`. For example, in bash:

```bash
export MCP_TOOL='YOUR_APPROVED_READ_TOOL'
export MCP_ARGS_JSON='{"id":"public-example"}'
node client.mjs
```

In PowerShell use `$env:MCP_TOOL = 'YOUR_APPROVED_READ_TOOL'` and `$env:MCP_ARGS_JSON = '{"id":"public-example"}'`. The call may reach your upstream service and may incur its charges. `MCP_TOOL` is not needed to confirm the connection.

The example uses the official [`@modelcontextprotocol/client` v2](https://github.com/modelcontextprotocol/typescript-sdk/tree/main/packages/client) and the MCP Streamable HTTP transport. It sends the key as a Bearer header and does not run an interactive OAuth client login. Once connected, integrate `client.listTools()` and `client.callTool()` into your own Node application. Review [access scopes](quickstart.md#access-for-more-than-one-person) before sharing a key: in subject mode each person needs a separate bound client key.

### If it fails

| Error | Check |
| --- | --- |
| Invalid URL | Use the **issued** `/gateway/<id>/mcp` URL, not Mithrandir's public `/mcp`. |
| 401 / 403 | Use the Mithrandir account key in account mode or your bound client key in subject mode. The upstream OAuth grant may also need reconnecting at `/connect/<id>`. |
| Empty tools | Verify the upstream connection and tool discovery on `/start`; the client only lists what the upstream exposes to this identity. |
| Tool not advertised | List first and copy the exact name. A tool call happens only when `MCP_TOOL` is set. |
