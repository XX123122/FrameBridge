# GitHub settings — manual actions, not executed

Repository: https://github.com/XX123122/FrameBridge

The local portable gh CLI was checked during this preparation and reported **not logged in**. Browser GitHub login is separate and does not make the CLI authenticated. No credentials were read/exported, and no repository metadata was modified.

## About fields to paste manually

Description:

> ChatGPT image generation via browser automation for local Codex workflows. Unofficial, open-source, and human-supervised.

Topics:

```text
chatgpt, codex, image-generation, browser-automation, playwright, python, codex-skills, ai-tools, edge-browser
```

Use only relevant topics; no unrelated trending terms. Leave the website field unset unless there is a real maintainer-controlled documentation site. Do not invent downloads/stars/test badges/endorsements.

## Other pending settings

- Confirm public visibility, Issues and Actions availability for intended contributors.
- Enable private vulnerability reporting if supported; verify the Security tab actually offers it before claiming a private reporting channel.
- After separately approving a push and observing the first real CI run, add appropriate main-branch review/check rules. Do not require guessed nonexistent job names or advertise passing early.
- Review dependency/action updates and available secret-scanning/push-protection settings; availability depends on repository/account configuration.
- Review social-preview/demo media for rights and irreversible redaction before upload.
- No Tag/Release until the exact source tree and publication checklist are approved.

If a maintainer later authenticates gh and separately approves metadata writes, the equivalent description command is:

```powershell
gh repo edit XX123122/FrameBridge --description 'ChatGPT image generation via browser automation for local Codex workflows. Unofficial, open-source, and human-supervised.'
```

Topics can be added through the GitHub About dialog (recommended for this task). This document is preparation, not an authorization to execute external writes. Do not paste a token into an issue or assistant chat.
