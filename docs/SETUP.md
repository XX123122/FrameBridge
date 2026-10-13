# Browser setup and Skill migration

This guide assumes no browser access, login or generation consent has been established. Examples use port 9222 only after the current user selects it. Do not attach to an unexplained listener or inherit a maintainer's session.

## Install and inspect

Start with the clone/venv commands in [README](../README.md#quick-start). `doctor` reports local environment/executable candidates without a browser connection; its output can contain personal paths, so redact it before posting.

```powershell
.\scripts\start_edge.ps1 -DryRun
```

DryRun reads executable/policy/listener metadata and prints a plan; it does not create a profile, start Edge, log in or generate. For a nonstandard install use `-EdgePath` with your verified executable. `-ProfileDirectory` can select a separate location **outside this checkout and outside the default Edge profile**. The browser itself manages the profile; the program does not copy authentication data.

## Explicit local-control approval

After reviewing and accepting local debugging access:

```powershell
.\scripts\start_edge.ps1 -ConfirmLocalControl -Port 9222
```

No approval flag means no launch. The launcher uses a visible window, binds with `--remote-debugging-address=127.0.0.1`, refuses an occupied port and respects the Edge `RemoteDebuggingAllowed` policy. It does not close other windows or override policy. Login and any verification are manual.

Check the actual listener before a client connection:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 9222 | Select-Object LocalAddress, LocalPort
```

Only loopback addresses such as `127.0.0.1` and `::1` are acceptable. If the browser/version ignores the binding and listens on `0.0.0.0` or another address, stop, close that session manually, and investigate; do not connect, expose, forward, or tunnel it. A launch flag is not proof of actual binding. This release preparation does not launch or reconfigure the maintainer's existing session.

Once **your** session is configured and signed in:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page https://chatgpt.com/ probe
```

The client accepts explicit HTTP loopback endpoints only; remote hosts, URL credentials and query tokens are rejected. It does not scan ports. A ready composer is not proof of image quota or compatibility. Current image-mode labels were tested in Chinese; other languages/versions may stop and require review. Chrome connections use the same adapter but have no equivalent live trial evidence; see [Microsoft's CDP documentation](https://learn.microsoft.com/en-us/microsoft-edge/devtools/protocol/) and [Chrome's nondefault-profile debugging requirements](https://developer.chrome.com/blog/remote-debugging-port).

## Skill installation, moving and upgrading

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py
```

The installer reads this checkout's entry and writes an installed `SKILL.md` plus `framebridge-install.json` containing only ownership/name/project-path metadata. It creates no task state, login, CDP connection or authorization record. Frontmatter name is `framebridge-web-imagegen`. Default destination is `$CODEX_HOME/skills` or `~/.codex/skills`, consistent with [Codex's Skill documentation](https://learn.chatgpt.com/docs/build-skills).

If the checkout moves, run the installer from the **new** location:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py --update
```

Or use `--project` and `--destination` with your own selected directories. Managed updates keep the previous entry as `SKILL.md.previous`. They do not overwrite another Skill name or another tool's manifest. Reload Skill discovery in your Codex version after an update; this task does not certify discovery on every Codex build.

Pre-v0.1 entries have no ownership manifest and may contain maintainer-specific assumptions. Review the existing entry first. If it is this project's legacy Skill and you want to replace it:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/install_skill.py --update --adopt-existing
```

Adoption requires explicit selection; installation/update still grants no browser or generation consent. Do not publish the installed manifest or backup: they contain local paths and may preserve legacy instructions. No installed global Skill or browser profile is changed by the release-preparation task.
