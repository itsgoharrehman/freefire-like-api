# Security Policy

## Supported Versions

| Version | Supported | Description |
| :--- | :--- | :--- |
| `1.0.x` | Yes | Current stable release branch (`main`) |
| `< 1.0.0` | No | Legacy versions |

## Security and Token Safeguards

freefire-like-api manages active account authentication tokens and dispatches high-concurrency network requests. Security invariants include:
* **Token Isolation**: The token cache (`tokens.json`) contains active authorization sessions and must remain strictly machine-local. Never commit token files to version control.
* **API Key Protection**: The master `API_KEY` controls access to dispatch endpoints and must be injected via process environment variables.
* **Quarantine Mechanics**: Tokens receiving authorization failure responses from remote game servers must be quarantined immediately to prevent cascade bans.

## Reporting a Vulnerability

If you discover an authentication bypass, token leakage vector, or denial-of-service vulnerability, report it privately:

* **Security Contact**: Gohar Rehman
* **Email**: `goharrehmanfsd260@gmail.com`
* **Response SLA**: Initial acknowledgement within 48 hours; resolution timeline provided within 7 days.

Please do not open public GitHub issues or discussions regarding undisclosed vulnerabilities.