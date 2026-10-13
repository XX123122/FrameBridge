# FrameBridge v0.1.0 — release notes draft

**Prepared, not tagged or published.** Replace pending items with verified evidence before approving publication. No release archive/install-from-tag command is advertised as already available.

## Supported

- Local Windows/Python 3.11+ workflow with standard Playwright and visible, current-user-configured Edge.
- txt/md originals, named PNG/JPEG/WebP references, single-task approval, serial states, normal download, file verification and recovery without resend.
- Finite explicitly approved text-only `batch` lists in one conversation, with scoped history boundaries and individual downloads; reference uploads are not supported by this new batch path.
- Codex Skill entry/installer, moved-project update and reviewed legacy migration; installing grants no browser or generation authority.

## Tested

- Earlier authorized Windows/Edge/Chinese-UI text-only trials are recorded in [historical experiments](HISTORICAL_EXPERIMENTS.md).
- A later explicitly authorized [serial trial](QUEUE_TRIAL.md) saved Q01 and Q03; Q02 was refused, stopped the runner, and was closed by the user before Q03 resumed. This is not three successful unattended generations.
- A separate [same-conversation cat sequence](SAME_CHAT_BATCH.md) saved two images, with local offline legacy/current-DOM and recovery fixtures. This new feature still needs remote CI/fresh-user verification.
- Local offline logic/browser evidence and release checks are recorded in [RELEASE_READINESS.md](RELEASE_READINESS.md). Do not conflate mocked upload tests with real uploads.
- GitHub Actions Windows/Linux/Python matrix is defined but **remote success is pending** until the first actual run. No passing badge is claimed.

## Known limitations

Chinese image-mode control labels; changing UI may fail closed. Chrome, other languages/versions, real reference upload/identity consistency and large queues lack equivalent live verification. Polling adds observation delay; model speed/quality/quota are not guaranteed. Local stop does not cancel a remote request. This is not a hosted service/API or unattended unlimited batch runner.

## Security and terms considerations

Read [SECURITY.md](../SECURITY.md) and [RISKS.md](RISKS.md). CDP is powerful local browser control: keep it loopback-only, never forward it, do not copy default profiles or credentials. Fresh users configure, log in and approve their own session/tasks. Official service terms may prohibit automated output extraction; personal usage and normal UI buttons do not establish permission. No paid API, private model endpoints, stealth or verification/limit bypasses are included.

## Installation

Use the clone/venv instructions in [README](../README.md#quick-start) for the reviewed source checkout. Inspect `start_edge.ps1 -DryRun`, then explicitly authorize local control and sign in manually. Prepare a task locally; generating requires its own approval. Until v0.1.0 is actually published, the remote default branch may not contain this prepared source tree.

## Upgrade notes

- Public Skill no longer inherits any author's browser/login/generation consent. Re-establish current-user configuration; never reuse legacy permission text.
- Reinstall after moving: `install_skill.py --update` from the new checkout. Reviewed pre-manifest entries require `--update --adopt-existing`. Keep private backups/manifests out of Git.
- Edge launch now requires `-ConfirmLocalControl`; discovery/overrides replace the old fixed executable path. Default and in-checkout profiles are refused.
- Diagnostics no longer dump conversation text/screenshots by default; use sensitive opt-ins only locally.
- Preserve existing tasks, outputs and original snapshots. This preparation does not migrate/drop task history or alter browser login data.

## Publication gates

Reviewed diff, privacy/history scan, offline tests, actual CI, fresh-user setup/Skill update check, redacted demo approval, dependency/action review, metadata and final release approval. Tag/Release/push/community actions require separate explicit authorization; see [checklist](RELEASE_CHECKLIST.md).
