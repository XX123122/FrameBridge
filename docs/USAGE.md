# Tasks, local files and recovery

Use the project root and venv created in [Quick start](../README.md#quick-start). Each image requires its own current-user authorization. Creating tasks is local preparation; `--confirmed` must not be inferred from examples or prompt-file instructions.

## Local state

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py list
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py show EXAMPLE
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check EXAMPLE
```

`show`/`packet` can print original prompts and paths. Keep output private or redact it. `tasks.json` is authoritative; `logs/<ID>/task.json` is a derived mirror. UTF-8 BOM/CRLF bytes are preserved in snapshots; browser-rendered terminal blank lines are tolerated without rewriting the original.

`pending/running/completed/failed` are primary states. `needs_confirmation` marks uncertain results. At most one task runs; uncertainty blocks starting the next. There is no unattended queue drain or infinite retry. Completed means the file was collected/validated, not a guarantee of visual identity or artistic quality.

## Interrupt and inspect

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py stop EXAMPLE --reason interrupted
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py recover
```

Ctrl+C/stop affects the local process, not necessarily the server request. Inspect the original browser conversation yourself. `recover` records uncertainty and never sends a prompt. Resolve verification/permissions manually; do not defeat protection or resubmit to get around quota.

## Collect only the original request

After explicitly authorizing recovery, replace the placeholder URL with the recorded original conversation privately:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page 'https://chatgpt.com/c/REPLACE_WITH_ORIGINAL_ID' collect EXAMPLE --confirmed --timeout 180
```

No normal command should guess another tab/conversation. `collect` has no Send step. It checks the endpoint, original conversation, prompt and unique result. Do not post that private URL in issues.

If a file was written before the last status update, authorize hash-based confirmation:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py confirm-output EXAMPLE --confirmed
```

Only the recorded candidate is accepted. Never overwrite or auto-delete a mismatching/incomplete file. If abandoning collection after review, use `resolve EXAMPLE --confirmed`. A new request uses a new ID and its own authorization.

## Manual download import

Choose `--mode manual-web` at task creation. After explicit task consent, `start EXAMPLE --confirmed` only updates local status; the user uploads/submits on the page, then records `submitted EXAMPLE --confirmed`. Import an explicitly selected downloaded file:

```powershell
$downloadedImage = Read-Host 'Absolute path to the image you downloaded and matched to this task'
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py import EXAMPLE --file $downloadedImage --confirmed
```

This does not scan Downloads, choose the newest file or delete its source. A stale file, identical reference, wrong/corrupt format or output collision is rejected. `--convert-png` explicitly permits PNG conversion; it is not a model call. Manual import still requires a started/uncertain task, so do not run these commands for an unrelated completed task.

## Diagnostics and timing

The image checks are local reasonable bounds: static PNG/JPEG/WebP, at most 64 MiB, shortest output side at least 256, longest at most 8192 and at most 32 million pixels. They are not model output specifications.

`logs/<ID>/timing.json`/`timing.md` separate Send→observed completion, download/verification and Send→save. Observation uses a 1-second interval and 1-second stability check; recovery preserves the earliest complete time. Recovery waiting is part of total time, not a new generation measurement.

`inspect_web.py` reports UI metadata by default. `--include-conversation-text` and `--screenshot` are explicit sensitive opt-ins; screenshots can expose account/history information. Do not attach their unredacted output publicly. Diagnostic/benchmark tools can connect/download when explicitly invoked: they are **not CI steps** and must not be used during an offline-only audit.
