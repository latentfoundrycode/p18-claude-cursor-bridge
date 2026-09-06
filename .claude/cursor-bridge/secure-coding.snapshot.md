<!-- Bundled secure-coding rule body, DERIVED from OWASP Application Security Verification
Standard (ASVS) v5.0.0 (May 2025). This is the frozen source cursor-configurator writes into
each project's `.cursor/rules/secure-coding.mdc`, level-filtered to the project's chosen tier
(L1 baseline / L2 most apps / L3 high-assurance). Snapshot taken 6 September 2026; ASVS is a
stable standard (major releases ~6-yearly), so the freeze pins v5.0.0 and does NOT need the
per-project live-fetch-validation the beta Vercel rules need — this bundled copy is the source.

Requirements are tagged [L1]/[L2]/[L3] (cumulative: L2 includes L1, L3 includes L2). Cite as
`v5.0.0-<chapter>.<section>.<req>`. Each rule is a derived, condensed restatement — consult the
full standard for the authoritative text and requirement numbers.

ASVS is licensed CC BY-SA 4.0 (© OWASP Foundation); this derived work carries the same licence.

NOTE: ASVS deliberately excludes AI-specific risks. For an LLM-bearing product, the supervisor
supplements this rule with the OWASP Top 10 for LLM Applications (recorded in the project's
`.mdc`, never silently) — see the final section. -->

# Secure Coding Rules (ASVS 5.0.0, derived)

Concise secure-by-default rules for the builder to self-apply during generation. Use
MUST/SHOULD/NEVER. Tags: **[L1]** baseline, **[L2]** most applications, **[L3]** high-assurance.

## V1 — Encoding & Sanitization

- MUST [L1]: Contextual output encoding at the sink (HTML, HTML-attribute, JS, CSS, URL) — encode on output, not input
- MUST [L1]: Parameterised queries / prepared statements for all data access; NEVER build a query by string concatenation of untrusted input
- MUST [L1]: OS commands use a safe API with an argument vector; NEVER pass untrusted input to a shell string
- MUST [L2]: Untrusted data in a template engine is auto-escaped; NEVER disable auto-escaping for untrusted content
- MUST [L2]: Path/filename input is canonicalised and confined; reject traversal (`..`, absolute paths, null bytes)
- SHOULD [L2]: Prefer allow-list sanitisation over deny-list for structured formats (HTML via a vetted sanitiser, not regex)

## V2 — Validation & Business Logic

- MUST [L1]: Validate all input at the trust boundary for type, length, range, and format — server-side, never client-only
- MUST [L1]: Reject by default; accept only what the allow-list permits
- MUST [L2]: Enforce business-logic limits (quantity, price, sequence, state transitions) server-side; NEVER trust client-computed values
- MUST [L2]: Protect check-then-act sequences against TOCTOU/race; make the critical step atomic
- MUST [L2]: Anti-automation on sensitive flows (rate limits, throttling) so a flow cannot be abused at scale
- MUST [L3]: Protect against replay of intended flows (nonces, idempotency keys, one-time tokens)

## V3 — Web Frontend Security

- MUST [L1]: Set a restrictive Content-Security-Policy; avoid `unsafe-inline`/`unsafe-eval`
- MUST [L1]: Cookies are `Secure`, `HttpOnly`, and `SameSite` (Lax or Strict) as the flow allows
- MUST [L2]: Set `X-Content-Type-Options: nosniff`, a frame-ancestors/`X-Frame-Options` clickjacking defence, and a sensible `Referrer-Policy`
- MUST [L2]: State-changing requests carry CSRF protection (token or SameSite-strict + origin check)
- SHOULD [L2]: Subresource Integrity on externally hosted scripts/styles

## V4 — API & Web Service

- MUST [L1]: Enforce the same authN/authZ on the API as on the UI — the API is not a trusted caller
- MUST [L1]: Responses set a correct `Content-Type`; JSON APIs never reflect input as HTML
- MUST [L2]: Validate `Content-Type` on requests; reject unexpected media types
- MUST [L2]: Apply per-principal rate limiting and payload-size limits to every endpoint
- SHOULD [L2]: Version the API and avoid leaking internal identifiers in responses

## V5 — File Handling

- MUST [L1]: Validate uploaded file type by content, not extension; store outside the web root
- MUST [L2]: Cap upload size and count; scan or sandbox where the file is later processed
- MUST [L2]: Serve user files with a safe `Content-Disposition` and a non-executable content type; NEVER serve from a path built from untrusted input

## V6 — Authentication

- MUST [L1]: Store passwords with a memory-hard KDF (argon2id / scrypt / bcrypt); NEVER plaintext, NEVER fast/unsalted hashes
- MUST [L1]: Enforce credential strength and check against known-breached password lists
- MUST [L1]: Generic authentication-failure messages; NEVER reveal whether the username or the password was wrong
- MUST [L2]: Support MFA for sensitive accounts; re-authenticate before sensitive actions
- MUST [L2]: Rate-limit and lock out credential-stuffing/brute-force attempts
- MUST [L3]: Bind authenticators to the user; resist phishing (WebAuthn/FIDO2 where warranted)

## V7 — Session Management

- MUST [L1]: Generate session tokens with a CSPRNG, sufficient entropy, and server-side validation
- MUST [L1]: Regenerate the session identifier on login and on privilege change (anti-fixation)
- MUST [L1]: Invalidate the session server-side on logout and on idle/absolute timeout
- MUST [L2]: Bind sessions so a stolen token alone is limited; allow the user to view/revoke active sessions

## V8 — Authorization

- MUST [L1]: Enforce authorization on every request at the server, for every function and object — deny by default
- MUST [L1]: Verify object ownership/role before acting (defeat IDOR/BOLA); NEVER authorise on a client-supplied identifier alone
- MUST [L2]: Enforce function-level authZ (no access to an admin function by guessing its route)
- MUST [L2]: Centralise the authorization decision; do not scatter ad-hoc checks that can drift
- MUST [L3]: Enforce field/attribute-level authZ where records mix sensitivities

## V9 — Self-contained Tokens (JWT etc.)

- MUST [L1]: Verify token signature with an explicit expected algorithm; NEVER accept `alg: none` or an attacker-chosen algorithm
- MUST [L1]: Validate issuer, audience, and expiry on every use
- MUST [L2]: Scope token lifetime tightly; support revocation for long-lived grants
- NEVER [L1]: Put a secret in a token payload — payloads are readable

## V10 — OAuth & OIDC

- MUST [L2]: Use the authorization-code flow with PKCE; NEVER the implicit flow for new work
- MUST [L2]: Validate `state` (CSRF) and `nonce` (replay); register exact redirect URIs
- MUST [L2]: Verify ID-token signature, issuer, audience, and expiry
- SHOULD [L2]: Request least-privilege scopes

## V11 — Cryptography

- MUST [L1]: Use vetted library primitives; NEVER hand-roll crypto
- MUST [L1]: Authenticated encryption (e.g. AES-GCM / ChaCha20-Poly1305) for confidentiality+integrity
- MUST [L1]: All randomness for security uses a CSPRNG; NEVER `Math.random`/`rand()` for tokens/keys/IVs
- MUST [L2]: Keys are generated, stored, and rotated via a key store/secret manager; NEVER hard-coded or committed
- NEVER [L1]: Use MD5/SHA1 for security, ECB mode, static IVs, or deprecated ciphers
- SHOULD [L3]: Plan for crypto-agility (algorithm identifiers, rotation paths)

## V12 — Secure Communication

- MUST [L1]: TLS for all data in transit; redirect HTTP→HTTPS and set HSTS
- MUST [L2]: Validate certificates fully; NEVER disable verification or trust all certs
- SHOULD [L2]: Modern TLS only (1.2+), strong cipher suites; disable legacy protocols

## V13 — Configuration

- MUST [L1]: No secrets in source, config committed to VCS, logs, or error output; load from a secret manager / environment
- MUST [L1]: Ship secure defaults; disable debug endpoints, directory listing, and verbose stack traces in production
- MUST [L2]: Remove default/sample accounts and credentials; least-privilege service accounts
- MUST [L2]: Keep dependencies patched; fail the build on known-vulnerable or known-malicious packages
- SHOULD [L2]: Pin dependencies and CI actions to immutable versions (a full commit SHA for actions), never a mutable tag

## V14 — Data Protection

- MUST [L1]: Classify data by sensitivity; encrypt sensitive data at rest
- MUST [L1]: NEVER log secrets, credentials, tokens, or full PII; redact before logging
- MUST [L2]: Minimise collection and retention; honour the declared data sensitivity/PII scope
- MUST [L2]: Set anti-caching headers on responses carrying sensitive data
- SHOULD [L2]: Mask sensitive fields in UI and in error responses

## V15 — Secure Coding & Architecture

- MUST [L1]: Fail securely — an error denies access, it does not fall through to allow
- MUST [L1]: NEVER swallow a security-relevant error silently; surface and handle it
- MUST [L2]: Validate and pin the integrity of build-time and run-time dependencies; treat the toolchain as an attack surface
- MUST [L2]: Deserialise only trusted data with a safe deserialiser; NEVER native-deserialise untrusted input
- SHOULD [L2]: Keep the trusted computing base small; isolate untrusted processing

## V16 — Security Logging & Error Handling

- MUST [L1]: Log security-relevant events (authN, authZ failures, validation failures, admin actions) with enough context to investigate
- MUST [L1]: User-facing errors are generic; internal detail (stack traces, queries) stays server-side
- MUST [L2]: Protect logs from injection (encode untrusted values) and from tampering
- SHOULD [L2]: Emit logs to a central, time-synced store; do not log the sensitive values themselves

## V17 — WebRTC (only if used)

- MUST [L2]: Authenticate and authorise signalling; encrypt media (SRTP/DTLS)
- SHOULD [L2]: Rate-limit signalling and validate SDP/ICE input

---

## LLM supplement (only for AI-bearing products — OWASP Top 10 for LLM Applications)

Add when the product embeds an LLM; ASVS does not cover these. Condensed:

- MUST: Treat all model input (prompts, retrieved documents, tool output) as untrusted — defend against **prompt injection**; never let model output alone authorise a side-effect
- MUST: Constrain and validate model **output** before it reaches a sink (code exec, SQL, shell, DOM, downstream call) — **insecure output handling**
- MUST: Enforce least privilege on tools/agents the model can call; a human or a deterministic check gates irreversible/side-effectful actions — **excessive agency**
- MUST: Guard against **sensitive-information disclosure** — do not place secrets/PII where the model can echo them; filter outputs
- SHOULD: Control the RAG/training/plugin supply chain (**data & model poisoning**, **supply-chain**); pin and vet sources
- SHOULD: Rate-limit and bound model calls against **unbounded consumption** (cost/DoS)
