import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client';

const rawUrl = process.env.MITHRANDIR_GATEWAY_URL;
const key = process.env.MITHRANDIR_API_KEY;

function gatewayUrl(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error('Set MITHRANDIR_GATEWAY_URL to your issued /gateway/<id>/mcp URL.');
  }
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if ((url.protocol !== 'https:' && !(local && url.protocol === 'http:')) ||
      url.username || url.password || url.search || url.hash ||
      !/^\/gateway\/[^/]+\/mcp$/.test(url.pathname)) {
    throw new Error('Use the issued HTTPS /gateway/<id>/mcp URL without credentials or query parameters.');
  }
  return url;
}

async function main() {
  const url = gatewayUrl(rawUrl);
  if (!key || /[\r\n]/.test(key)) {
    throw new Error('Set MITHRANDIR_API_KEY to your Mithrandir account or bound client key.');
  }

  const client = new Client(
    { name: 'mithrandir-javascript-example', version: '1.0.0' },
    { versionNegotiation: { mode: 'auto' } },
  );
  const transport = new StreamableHTTPClientTransport(url, {
    requestInit: { headers: { Authorization: `Bearer ${key}` } },
  });

  try {
    await client.connect(transport);
    const { tools } = await client.listTools();
    const output = { connected: true, tools: tools.map(({ name }) => name) };

    // Listing tools is safe; a call is made only when the operator explicitly chooses one.
    if (process.env.MCP_TOOL) {
      const name = process.env.MCP_TOOL;
      if (!tools.some((tool) => tool.name === name)) {
        throw new Error(`Tool ${JSON.stringify(name)} was not advertised by this gateway.`);
      }
      let args;
      try {
        args = JSON.parse(process.env.MCP_ARGS_JSON || '{}');
      } catch {
        throw new Error('MCP_ARGS_JSON must be a JSON object.');
      }
      if (args === null || Array.isArray(args) || typeof args !== 'object') {
        throw new Error('MCP_ARGS_JSON must be a JSON object.');
      }
      output.call = await client.callTool({ name, arguments: args });
    }
    console.log(JSON.stringify(output, null, 2));
  } finally {
    // The gateway does not support DELETE session termination. Close locally.
    await client.close();
  }
}

main().catch((error) => {
  console.error(`Mithrandir connection failed: ${error.message}`);
  process.exitCode = 1;
});
