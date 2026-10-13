# P0 project audit

Audit date: 2026-10-13. Scope: README variants, SKILL.md, every scripts/tests/docs file, requirements, LICENSE, .gitignore, public working changes and reachable local Git blobs. The core image mechanism is retained: normal UI Send, observation and Download, not model API calls.

## Evidence classification

| Classification | Findings |
| --- | --- |
| Earlier live verification | Three explicitly authorized text-only images in visible Edge/Chinese UI/Windows; K03 completed automatically; [trial evidence](HISTORICAL_EXPERIMENTS.md) |
| Later explicitly approved serial trial | Q01/Q03 saved; Q02 refused; queue stopped and Q03 resumed only after user approval; [separate evidence](QUEUE_TRIAL.md) |
| Offline/mocked verification | Ledger, snapshots, formats, output protection, serial/uncertain state, upload controls, UI readiness/preview waits, no resend and local timing reports |
| Implemented but not general live-certified | Reference file upload, Chrome CDP connection, all UI/language variants, broad quota/identity behavior |
| Not included | Hosted API/service, stealth/challenge solving, private-model calls, paid API integration, automatic unlimited queue/retry, official platform authorization |
| Publication boundary | v0.1.0 preparation; user subsequently approved commit/push/PR, while Tag, Release, community posts and listing submissions remain unapproved; remote CI success requires actual observation |

## Maintainer assumptions corrected

- Source Skill formerly inherited the maintainer's browser/CDP/generation permission. The public entry now starts unconfigured and obtains each user's session/task consent; historical authorization is never reused.
- Legacy installer refused changed paths without a migration route. Managed metadata, explicit updates, reviewed legacy adoption and a previous-entry backup provide a defined move/update procedure. Installed metadata contains a path/name, never login/permission state.
- Launcher had one fixed machine installation path and assumed approval. It now discovers standard Edge installations or accepts explicit overrides, supports DryRun, requires current consent, and refuses default/in-checkout profiles, occupied ports and disabled debugging policy.
- Doctor no longer has an author-specific home-directory fallback. README examples use clone/relative paths, not the author's checkout.
- Diagnostic result inspection formerly dumped conversation text and screenshots by default. Both now require opt-in; even UI metadata must be sanitized before sharing.

## Privacy / security scope

`audit_public.py --history` scans public source and reachable Git blobs for credential-shaped values, private keys, private ChatGPT conversation URLs and sensitive runtime filenames. It prints file/rule/line only, not matched values. Local logs/output/prompts copied for private work, review caches, venv, authentication artifacts and browser profiles are ignored; the launcher keeps its default profile outside the source checkout.

The scan is heuristic, not a security certification or dependency vulnerability audit. Git author names/emails are ordinary existing public metadata; old commits also retain author-specific path examples and old Skill assumptions. No history is rewritten and no historical evidence is deleted. If maintainers want different author identity metadata, configure future commits deliberately; rewriting public history needs separate review/authorization.

CDP URL validation only permits explicitly provided HTTP loopback host/port without credentials/query parameters; no port scan or auth/storage/header extraction occurs. The launcher requests binding to 127.0.0.1; actual listener addresses must still be checked before use. Do not tunnel it, change organization policy or bypass platform protection.

Live reference/identity security, all Edge policies/versions and externally managed machines are not proven by the earlier trials. A public bug report must exclude credentials, private URLs, raw conversations and unredacted screenshots. See [SECURITY.md](../SECURITY.md), [risks](RISKS.md), and [release readiness](RELEASE_READINESS.md) for current evidence and pending gates.
