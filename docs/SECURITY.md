# Security boundary

The hackathon deployment is a single-tenant judge appliance, not a general account system.

- Caddy publishes only HTTPS routes. PostgreSQL, the memory API, MCP, and OpenClaw control traffic remain on the Compose network.
- `MNEMAGENT_API_TOKEN` is mandatory between cloud services.
- `demo-brain` contains presentation data and must be read-only in the submitted deployment.
- The interactive run uses one resettable `judge-*` namespace. A query-string user ID is not sufficient authorization for real user data.
- OpenClaw's Web UI is protected independently with Caddy basic authentication. No shell or SSH terminal is exposed through the browser.
- Secrets belong in `.env.cloud` on ECS. Logs, screenshots, health responses, and Git history must not contain them.

For a multi-user product, replace the shared judge boundary with OIDC. Map the OIDC subject to a canonical internal user ID and enforce that tenant claim in the harness, MCP server, API, and database policy. Add durable rate limiting, session revocation, audit logs, and managed secret storage before accepting public sign-ups.
