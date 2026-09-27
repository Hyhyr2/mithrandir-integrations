# Security and disclosure

This repository contains public integration examples. It does not contain the hosted service's source, production configuration, or customer data.

- Never commit a Mithrandir key, upstream credential, real customer trace, or private result. Use your client's secure input or a trusted local environment.
- During the pilot, use synthetic or public non-sensitive data. A gateway forwards Observe calls to your upstream; review the live [terms](https://mithrandir-production.up.railway.app/terms) and [privacy notice](https://mithrandir-production.up.railway.app/privacy) before connecting.
- Treat upstream tool annotations as hints. Approve only tools you control and know to be safe for exact reuse; effectful calls should not be allowlisted.
- Avoid public issues for vulnerabilities or sensitive details. Use GitHub's private vulnerability reporting if available, or the support contact in the live service terms.

The example client uses HTTPS, keeps upstream and gateway authorization separate, and refuses HTTP redirects. Its route and receipt values are operational evidence from the service, not an independent security certification.
