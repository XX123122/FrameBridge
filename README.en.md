# FrameBridge

English | [简体中文](README.md)

FrameBridge is a local Python assistant for personal, low-volume image generation experiments on Windows. It operates ChatGPT's normal web interface in a visible browser that the user signs into manually, then downloads and verifies the resulting image.

The workflow is simple: prepare a local prompt and optional reference images, authorize one task, submit it once, wait for completion, use the page's normal download button, and record the output and elapsed time. Generated images remain available in the original ChatGPT conversation.

## Features

- UTF-8 `.txt` and `.md` prompts, with the original bytes preserved in task snapshots.
- Explicit PNG, JPEG, and WebP reference files; no automatic upload of a project or unrelated files.
- Serial tasks with `pending`, `running`, `completed`, and `failed` states, plus a confirmation flag for uncertain results.
- A single `generate` command for browser preparation, submission, observation, download, and verification.
- Recovery through `collect`, which resumes collection from the original conversation and never sends the prompt again.
- Output format, pixel decoding, dimensions, and SHA-256 checks; existing images are never overwritten.
- Progress updates and automatic JSON/Markdown timing reports.
- A local Codex Skill for preparing, executing, checking, and recovering explicitly authorized tasks.

The current setup uses Microsoft Edge and standard Playwright over a local Chrome DevTools Protocol (CDP) connection. Chrome is also supported by the underlying browser adapter when explicitly configured. The ChatGPT account in the browser can differ from the Codex account: image generation and conversation history belong to the selected browser session.

## Scope and limitations

This is a personal learning prototype, not a public service or an officially supported ChatGPT automation API. OpenAI's [Terms of Use](https://openai.com/policies/terms-of-use/) prohibit automatic or programmatic extraction of data or output. Automating collection through the normal download button does not establish an exemption or official authorization. Review the project's [risk notes](docs/RISKS.md) before use.

The implementation does not read or export cookies, OAuth tokens, passwords, browser authentication storage, or authentication headers. It does not use a paid OpenAI API, reverse-engineered model endpoints, stealth packages, or protection bypasses. Stop when verification, quota limits, permission errors, or uncertain page states appear; let the user resolve them manually.

The tested UI is the current Chinese-language ChatGPT interface. Some control labels are specific to that interface; a different language or page version may require updating the documented selectors. The script stops when it cannot identify a unique control rather than guessing or resubmitting.

## Quick start

Requirements: Windows, Python 3.11 or later, and a visible Edge browser. Run these commands from the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requirements.txt -r requirements-browser.txt
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py init
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py doctor
```

After explicitly approving a separate local browser session, start the visible Edge window:

```powershell
.\scripts\start_edge.ps1
```

The launcher uses a separate browser-managed profile under `%LOCALAPPDATA%\FrameBridge\edge-session` and port `127.0.0.1:9222`. It does not copy the user's default profile or close existing browser windows. Sign into the intended ChatGPT account manually. Keep the debugging port local; do not expose or forward it to a public network. The launcher currently uses the verified standard Windows Edge installation path; see the [Chinese setup guide](README.md#edge-与会话准备不生图) if your environment differs.

Save your own prompt as `prompts/example.md`, then prepare a task without consuming image quota:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add EXAMPLE --prompt prompts/example.md --output outputs/EXAMPLE.png
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet EXAMPLE
```

For reference images, add one `--reference references/filename.png` option per explicitly authorized file. Do not reuse an existing task ID or output path.

Only after the user has authorized this specific image request, submit it once:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 generate EXAMPLE --confirmed --timeout 300
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check EXAMPLE
```

`--confirmed` records user authorization; it is not authorization from OpenAI. The command prepares an empty image-mode tab in the existing session, stops if another draft or uncertain task would be affected, and uses only normal page controls. Output goes to `outputs/EXAMPLE.png`; task snapshots and reports go to `logs/EXAMPLE/`.

For an interrupted task, inspect `show EXAMPLE` and use `collect` with the recorded conversation URL after explicitly authorizing recovery. Do not run `generate` again to recover a submitted request. See the [recovery guide](README.md#状态队列与恢复) for commands and manual confirmation cases.

## Codex Skill

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py
```

The installer places the project's own Skill entry in `$CODEX_HOME/skills/framebridge-web-imagegen`, or `~/.codex/skills/` when `CODEX_HOME` is unset. It does not overwrite a different installed version. Reload Skill discovery or start a new chat after the first installation.

Example request:

> Use $framebridge-web-imagegen. Read prompts/example.md and the explicitly listed reference images, prepare one image task, and save the result to outputs/EXAMPLE.png. Show the task first and wait for my confirmation before the first real generation.

## Verification

Local tests do not generate real images:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v

# Optional isolated browser fixtures; all page requests are intercepted locally.
$env:FRAMEBRIDGE_FIXTURE_BROWSER = 'msedge'
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
Remove-Item Env:\FRAMEBRIDGE_FIXTURE_BROWSER
```

The current implementation has passed 43 tests and three individually authorized real single-image trials. The optimized cat-image trial took approximately 46.5 seconds from Send to observed completion and 49.5 seconds from Send to verified local save, with one submission and no manual recovery. These measurements describe that trial, not a guaranteed generation speed.

Real reference-image uploads, identity consistency, additional UI versions, and larger queues have not been comprehensively tested. See [test results](docs/TEST_RESULTS.md), [optimization notes](docs/OPTIMIZATION.md), and the [reference-project review](docs/REFERENCE_REVIEW.md). Those detailed reports are currently in Chinese.

Local task state, generated images, logs, reference images, browser sessions, and review caches are excluded from Git by default. The source code is available under the [MIT license](LICENSE).
