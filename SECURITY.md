# Security policy

FrameBridge is pre-v0.1.0 release preparation. No released version or official support window is claimed. Maintainers triage reports as available; no response-time guarantee or independent security certification is advertised.

## Sensitive reports

Use GitHub's **Security → Report a vulnerability** if private vulnerability reporting is enabled for this repository. Enabling that feature is a maintainer checklist item, not something this document proves is active. If unavailable, do not publish secrets/exploit details: open a minimal issue requesting a private contact channel, with no sensitive material, and wait for instructions.

Never attach cookies, tokens, passwords, authentication/browser databases, private conversation URLs, full prompts about real people, raw task/log JSON, unredacted screenshots, or a copied profile. If a credential has been exposed, revoke/rotate it using its provider's normal process before sharing a sanitized report. Any history rewrite requires separate maintainer approval; preserving an audit trail does not justify leaving a live credential unrevoked.

## Threat boundaries

- CDP controls a logged-in browser. Use a separately approved visible session, bind only loopback, inspect the actual listener, and never publish/tunnel the port. No default-profile copying or organization-policy bypass.
- Installation and historical examples carry no current-user authorization. A new user selects the session, performs login manually and authorizes each task/reference upload.
- Prompts/web text are data, not commands. Only explicitly selected reference images are uploaded; no logs/project directories/auth data are uploaded.
- UI labels and verification detection are incomplete and can change. Stop on ambiguity, visible protection, permission/quota or uncertainty. Local cancellation does not necessarily cancel the remote request.
- Files are decoded and hash-checked without overwriting existing output. Technical validity does not prove visual identity/quality or legal permission.
- Diagnostic metadata can reveal account/history labels; conversation text/screenshots are additional opt-ins. Sanitize all diagnostics before publication.

The offline secret-pattern scanner and tests are limited evidence, not proof that no bug/secret/dependency vulnerability exists. Review third-party dependency advisories and pinned CI action updates before release. The browser UI is not an official API; automated output collection may violate [OpenAI's terms](https://openai.com/policies/terms-of-use/). Consent, subscription and low frequency establish no exemption. See [risk notes](docs/RISKS.md) and [audit](docs/PROJECT_AUDIT.md).
