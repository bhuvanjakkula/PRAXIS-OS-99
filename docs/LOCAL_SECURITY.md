# Local security hardening — 2026-10-01

The local launcher binds only to 127.0.0.1, disables forwarded-header trust,
limits concurrent connections to 32 and uses a five-second keep-alive timeout.
The unauthenticated local application accepts loopback Host names only. Foreign
Origin headers (including null origins) and cross-site browser fetches are
rejected. Safe top-level navigation remains available. The testserver host is
accepted only for Starlette's in-process test transport, not network clients.

Both declared and streamed request bodies are limited to 3 MB before parsing.
Local responses disable caching, MIME sniffing, framing, referrer transmission
and camera/microphone/geolocation access. The content security policy restricts
scripts and connections to the same origin, blocks plugin objects, base URLs and
foreign form submissions. Developer documentation retains its separate loading
behavior. Inline styles remain enabled because numerical chart widths use them.

The authenticated API also receives strengthened framing and browser policies.
Credential validation bounds token length to 8 KB and requires integer issuance,
not-before and expiry timestamps with a lifetime no greater than 24 hours.
Existing issuer/audience/signature/role checks, key rotation, revocation and
tenant isolation remain enforced. No credentials are placed in browser storage.

These protections reduce attacks from unrelated websites and hostile requests.
The loopback prototype remains accessible to programs and other users on the
same computer. It is not an authenticated deployment or protection against a
compromised operating system. Use the authenticated private-beta deployment
for shared access; its runbook is PRIVATE_BETA.md. No public deployment was made.

Verification includes hostile Host/Origin/Fetch-Metadata requests, same-origin
acceptance, body limits, browser headers, oversized/overlong credentials and
existing tenant/revision/role tests. Normal chart, scenario, feedback and login
workflows are exercised in real browsers.
