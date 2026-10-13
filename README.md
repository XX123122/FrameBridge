# FrameBridge

A local ChatGPT browser image generation workflow for Windows and Codex, with human approval and verified file saving.

English | [简体中文](README.zh-CN.md)

FrameBridge turns a local prompt file into a supervised, single-image browser task: you choose the session and authorize the request; Playwright submits once, observes the result, clicks the normal download button, and validates the saved file. It is **unofficial**, uses no paid OpenAI API, and does not provide a hosted API or bypass account limits.

## Demo

**No approved public software recording is available yet.** See the [recording guide](docs/DEMO_RECORDING.md) and [asset requirements](docs/assets/README.md). The intended demo is: prompt file → manually signed-in visible browser → single-task approval → generation → normal download → local verification. Mocked test pages are not product demos.

## Features

- UTF-8 `.txt`/`.md` prompts; original bytes and explicitly named PNG/JPEG/WebP references are snapshotted locally.
- Explicit reference-guided `edit` tasks preserve originals and save a new output; see [reference/edit workflow](docs/REFERENCE_IMAGE_EDIT.md).
- One task at a time, with `pending`, `running`, `completed`, `failed`, and a separate uncertainty flag.
- Single-command browser preparation, one submission, normal-page download, and PNG/JPEG/WebP decoding, size and SHA-256 checks.
- Recovery collects the original request's result; it never resends the prompt. Existing output files are protected.
- An explicitly approved finite `batch` can generate/download serial images in one conversation; initial scope is text-only. See [same-chat workflow](docs/SAME_CHAT_BATCH.md).
- Progress updates and local JSON/Markdown timing reports.
- A portable Codex Skill for task preparation, execution, checking and recovery. Installation grants no browser or generation permission.

## Verified scope and limitations

| Capability | Evidence / boundary |
| --- | --- |
| Visible Edge, Windows, Chinese ChatGPT UI, text-only generation/download | Three earlier maintainer-authorized single-image trials; [historical evidence](docs/HISTORICAL_EXPERIMENTS.md) |
| Python 3.11, Playwright, Pillow | Historical local Windows tests; current results in [release readiness](docs/RELEASE_READINESS.md) |
| Task state, recovery, formats, uploads and UI edge cases | Offline logic tests and mocked browser fixtures; not proof of live reference uploads |
| Limited serial trial | Two verified saves and one refused task; stopped on failure and resumed only after human approval; [trial record](docs/QUEUE_TRIAL.md) |
| Same-conversation sequence | Two text-only cat images generated/downloaded in one conversation; [actual timings and scope](docs/SAME_CHAT_BATCH.md) |
| Chrome / other UI languages or versions | CDP adapter can connect; no equivalent live compatibility claim |
| Single PNG reference-guided edit | One normal-upload/red-cushion edit/download verified; [evidence and limits](docs/REFERENCE_IMAGE_EDIT.md) |
| Multiple live references, JPG/WebP upload and identity/pixel consistency | Not live-verified; multiple-upload controls/formats have offline coverage |
| Large queues | Not live-verified; only the limited serial trial above was observed |
| GitHub CI, v0.1.0 Release | Workflow/release preparation only until actual remote checks and publication |

Browser automation cannot guarantee generation time, output quality, account availability or unchanged UI. The current image-mode preparation uses Chinese control labels. Detailed K01/K02/K03 measurements are evidence for those trials, not speed guarantees or authorization for new users. No passing CI badge is displayed before CI has run.

## Quick start

Prerequisites: Git, **Python 3.11+**, Windows PowerShell and a separately installed Microsoft Edge. Python 3.11 is the historically tested interpreter; additional CI versions remain pending until their jobs run. This source tree prepares v0.1.0; no v0.1.0 tag/release is claimed.

```powershell
git clone https://github.com/XX123122/FrameBridge.git
cd FrameBridge
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-browser.txt
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py init
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py doctor
```

These are proposed-release instructions. Changes not yet merged/published may differ from the remote default branch. Installation/doctor do not generate images, configure login, or prove that your browser/UI is compatible. Dependency installs use your configured package index; review it first.

### Configure the browser yourself

New users start **not logged in, not configured and not authorized**. Review local browser-control access and the [setup guide](docs/SETUP.md). Preview the launcher without starting anything:

```powershell
.\scripts\start_edge.ps1 -DryRun
```

Only after deciding to enable a separate visible browser session and loopback debugging:

```powershell
.\scripts\start_edge.ps1 -ConfirmLocalControl
```

The browser manages a separate profile outside the checkout. Supply `-EdgePath` if discovery fails and choose `-Port` if needed; see [setup and migration](docs/SETUP.md). Sign in manually, verify the intended account, and check the listener is only `127.0.0.1`/`::1`. Never expose or forward CDP. Existing default profiles are not copied; organization restrictions are not changed.

Read-only readiness check for **your explicitly configured endpoint**:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page https://chatgpt.com/ probe
```

### Prepare, approve, generate

```powershell
Copy-Item prompts/example.md prompts/my-image.md
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add EXAMPLE --prompt prompts/my-image.md --output outputs/EXAMPLE.png
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet EXAMPLE
```

Edit the copied file before `add`; snapshots freeze the original. Select references individually with `--reference references/file.png`. This preparation uses no image quota. For repeat experiments, use a new ID and output path.

**Only after the current user approves this exact task, its references and download:**

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 generate EXAMPLE --confirmed --timeout 300
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check EXAMPLE
```

`--confirmed` records human consent; it is not platform authorization. There is no automatic queue drain. Outputs go under `outputs/`, originals/logs/reports under `logs/<ID>/`, and local state in `tasks.json`. Those runtime files are not shipped. Stop for verification, quota, permission, ambiguous UI or uncertain results. Use [recovery](docs/USAGE.md), not another submission.

## Codex Skill

For step-by-step setup and copyable instructions to test in another Codex conversation, see the [Chinese usage/test tutorial](docs/TEST_WITH_CODEX.zh-CN.md).

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py
```

This installs only the entry and project-path metadata under `$CODEX_HOME/skills/framebridge-web-imagegen` or `~/.codex/skills/`. It does not start a browser, log in, install a browser extension, or grant image generation consent. Reload Skill discovery as required by your Codex version. See [official Skill documentation](https://learn.chatgpt.com/docs/build-skills).

Example: “Use $framebridge-web-imagegen to prepare prompts/my-image.md and the reference files I explicitly name. Show the task first. Do not generate until I authorize it.”

After moving/updating the checkout, explicitly update its path:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py --update
```

Run from the moved checkout, or pass `--project` with its new location. Legacy entries without installer metadata require separate review and `--update --adopt-existing`; unrelated Skills are not replaced. See [migration details](docs/SETUP.md).

## How it works

FrameBridge supports ChatGPT image generation with Codex through a local task ledger and standard Playwright controls. It connects only to a user-selected loopback CDP endpoint, matches a single new result in the original conversation, and handles Playwright ChatGPT image download through the page's normal download event. It does not call model APIs or export browser authentication.

```text
Local prompt + named references → snapshot → current-user approval
→ visible browser: one Send → observed complete result
→ normal Download → image verification → local state/timing report
```

Timing is measured from Send to observed completion and verified save, with polling/stability delay; it is not server compute time. Runtime browser behavior is separated from offline fixtures.

## Safety and service terms

ChatGPT web UI automation is **not an official API**. OpenAI's [Terms of Use](https://openai.com/policies/terms-of-use/) prohibit automatic/programmatic output extraction; using normal buttons, a subscription, or low volume does not establish an exemption or official approval. Review applicability before choosing this workflow. User consent does not override service terms.

No paid OpenAI API, stealth, CAPTCHA solving, credential exports, private-model endpoints or limit bypasses are included. Keep CDP private; do not send cookies, tokens, passwords, private conversation URLs or raw logs in issues. See [security policy](SECURITY.md), [risk notes](docs/RISKS.md), and [audit](docs/PROJECT_AUDIT.md). Diagnostic conversation text and screenshots require explicit opt-in and can still reveal personal information.

## FAQ

**Which account generates the image?** The ChatGPT account in the chosen browser, which may differ from the Codex account. No credential migration takes place.

**Can I resume a failed task?** Inspect its original conversation/state and authorize `collect`; it never sends the prompt again. A local interruption does not cancel a remote generation.

**Does an English README mean the English ChatGPT UI is tested?** No. The currently verified image-mode labels are Chinese. Unsupported labels cause a stop.

**Are reference uploads and preserved identities verified?** One PNG reference edit/upload/download was observed, with offline format/multiple-input coverage. Live multiple references/JPG/WebP and general identity or pixel preservation are not verified. Models may not follow every identity instruction.

**Can this run as an unattended public service?** That is outside the project's scope. Authorization, account restrictions, unsupported UI and terms risk remain.

## Contributing / license

Read [CONTRIBUTING.md](CONTRIBUTING.md) for offline checks and scoped changes. Use the issue templates with sanitized diagnostics, or follow [SECURITY.md](SECURITY.md) for sensitive reports. [Release readiness](docs/RELEASE_READINESS.md) distinguishes local checks from CI and publication; [v0.1.0 notes](docs/RELEASE_NOTES_v0.1.0.md) are a draft.

MIT — [LICENSE](LICENSE). No affiliation with or endorsement by OpenAI/Microsoft is claimed.
