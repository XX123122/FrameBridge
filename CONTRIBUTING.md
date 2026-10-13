# Contributing

FrameBridge is a small Windows browser-UI experiment, not a hosted API. Contributions should improve portability, correctness, privacy and truthful documentation without changing its single-task consent, no-resend and no-overwrite boundaries.

## Local checks

Clone/install from [README](README.md#quick-start), then:

```powershell
.\.venv\Scripts\python.exe -m compileall -q scripts tests
.\.venv\Scripts\python.exe scripts/check_docs.py
.\.venv\Scripts\python.exe scripts/audit_public.py --history
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

Core checks do not connect to a browser. To run fixtures with an installed Edge, set `$env:FRAMEBRIDGE_FIXTURE_BROWSER = 'msedge'` and run `python -m unittest discover -s tests -p test_browser_fixture.py -v`. Use `chrome` only if separately installed. Every context is isolated, all page requests are locally intercepted, and service workers are blocked. No real ChatGPT requests, user profiles, accounts or cookies belong in tests/CI. Browser installation requires its own review and is not a live generation authorization.

Use the cat example in `prompts/example.md` for future explicitly approved live experiments. K01/K02/K03 remain unchanged historical samples. Synthetic fixture images test file/UI behavior; they do not prove visual generation quality.

Reuse relevant tests; add cases for meaningful behavior rather than increasing a test-count badge. Report passed, skipped and failed cases separately. Syntax/link checks do not establish live UI compatibility. A live test requires a human's separately authorized prompt/references/image count/session and should never be a CI step.

## Review scope

- Preserve originals, scoped uploads, explicit human authority, loopback-only endpoints and failure stops.
- No stealth, verification/limit bypass, auth export, private-model endpoints or automatic paid-backend fallback.
- Keep claims proportional to evidence; mark unsupported UI/language/platform behavior. Update English/Chinese docs and migration notes together where applicable.
- Never commit tasks.json, logs, real references/output, browser profiles, installed Skill manifests/backups, credentials or private conversation URLs. Copy examples to ignored prompt files before private work.
- Keep PRs focused, explain the trigger/result and list exact local validation. Separate release/promotion decisions from code changes.

Use the bug/feature templates with sanitized reproducible examples. For vulnerabilities follow [SECURITY.md](SECURITY.md), not a public dump. Existing historical evidence should be annotated, not fabricated, silently altered or removed. AI-assisted contributions are welcome if disclosed and reviewed; tests and human review remain necessary.
