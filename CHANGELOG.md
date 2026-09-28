# Integration kit changelog

This log covers the public clients and instructions in this repository. The hosted Mithrandir service and its MCP Registry entry have separate versions.

## 0.1.0 — 2026-09-28

- Package the JavaScript connection example as an installable `mithrandir-connect` command. It lists tools by default and calls a tool only when explicitly requested.
- Publish a versioned GitHub Release with an npm tarball and SHA-256 checksum.
- Publish the same client to GitHub Packages for users who already authenticate to GitHub's npm registry.
- Add release and installation guidance for JavaScript, Go, and the hosted gateway.

The integration tests use a local MCP fixture; this release does not claim to verify a customer gateway or savings in production.
