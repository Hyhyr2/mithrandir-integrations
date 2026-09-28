# Downloads, packages, and versioning

Mithrandir is a **hosted** gateway. Start at [setup](https://mithrandir-production.up.railway.app/start); you do not install the server from this repository. This repository distributes a small JavaScript connection command and source examples.

| Place | What it contains | Recommended use |
| --- | --- | --- |
| [GitHub Releases](https://github.com/Hyhyr2/mithrandir-integrations/releases) | Versioned npm tarball for the `mithrandir-connect` CLI, checksum, and release notes | Easiest download if you want a command without cloning the repository |
| [GitHub Packages](https://github.com/Hyhyr2/mithrandir-integrations/packages) | The same scoped npm CLI package, `@hyhyr2/mithrandir-connect` | Optional for users with GitHub npm registry credentials |
| [JavaScript](javascript.md) and [Go](go.md) | Reviewed source examples and language-specific instructions | Integrate the official MCP SDK directly into your application |
| [Documentation](quickstart.md) | Hosted setup, compatibility, measurements, and security boundaries | Understand how the gateway works before using it |

The GitHub Packages npm registry requires a GitHub token even for public packages. The Release tarball avoids that extra login. The Go example is source code, not a published Go library. The MCP Registry `server.json` version describes discovery metadata for the hosted service and **does not** version this integration kit.

## Install the command from a Release

1. Create a free gateway at [setup](https://mithrandir-production.up.railway.app/start) and save the **Mithrandir** key. Your existing upstream must be a public HTTPS MCP endpoint.
2. Open the [latest GitHub Release](https://github.com/Hyhyr2/mithrandir-integrations/releases/latest), download `hyhyr2-mithrandir-connect-<version>.tgz` and `SHA256SUMS`. Verify with `sha256sum -c SHA256SUMS` on Linux, `shasum -a 256 -c SHA256SUMS` on macOS, or `Get-FileHash .\hyhyr2-mithrandir-connect-<version>.tgz -Algorithm SHA256` on PowerShell (compare the displayed hash with `SHA256SUMS`).
3. With Node.js 22 or newer, install the downloaded file using `npm install -g ./hyhyr2-mithrandir-connect-<version>.tgz`. Replace `<version>` with the actual file version; the package installs its official MCP client dependency from npm.
4. Set `MITHRANDIR_GATEWAY_URL` to your issued `/gateway/<id>/mcp` URL and `MITHRANDIR_API_KEY` to your Mithrandir account or bound subject key, then run `mithrandir-connect`. See [JavaScript setup](javascript.md) for safe key input in macOS/Linux and PowerShell.

The command lists the advertised tools without calling them. Set `MCP_TOOL` and `MCP_ARGS_JSON` only when you deliberately want to call a named tool. Your upstream may charge for such calls. Do not place credentials in shell history, source files, or GitHub issues.

## Optional GitHub Packages installation

If you already use GitHub Packages, authenticate your npm client to `npm.pkg.github.com` with a token allowed to read packages, then install `@hyhyr2/mithrandir-connect` from that registry. The [official npm registry instructions](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry) describe the required scopes and authentication. Avoid putting the token in a checked-in `.npmrc`. Use the Release tarball if you do not want a GitHub token.

## Release process

The `package.json` version defines this integration kit's `v<version>` GitHub tag and Release. A workflow tests the packed CLI against a local authenticated MCP fixture, creates the Release with a checksum, and publishes the package to GitHub Packages. It skips versions already published. Future releases must update the package version, lockfile, changelog, and matching `docs/release-notes/v<version>.md`. Source tags and artifacts let you pin a specific integration kit version; the hosted gateway can change on its own schedule.
