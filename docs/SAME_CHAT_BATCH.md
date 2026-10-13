# Same-conversation serial images

`batch` starts one fresh image-mode conversation, sends the explicitly listed prompts in order, and downloads/verifies each image before sending the next. It reuses one browser connection and the same conversation URL. It does not drain all pending tasks, adopt an unrelated private chat, run concurrently, retry refusals, or use image-URL extraction. Initial scope is **text-only tasks without reference uploads**.

## Prepare and authorize the finite list

Follow clone/venv/browser setup in [README](../README.md#quick-start) first. Preparation consumes no image quota:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add CAT01 --prompt prompts/cat-sequence-01.md --output outputs/CAT01.png
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add CAT02 --prompt prompts/cat-sequence-02.md --output outputs/CAT02.png
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet CAT01
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet CAT02
```

After the current user explicitly authorizes these **two prompts, two images, this browser session and normal downloads**:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 batch CAT01 CAT02 --confirmed --timeout 300
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check CAT01
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check CAT02
```

Use new IDs/output paths for new experiments. Both prompts and named task count must be approved; `--confirmed` is human consent, not platform permission. Later prompts inherit earlier conversation context/outputs. That does not guarantee character identity consistency. Do not include private context or reference material the user did not approve.

## Attribution, stopping and recovery

Each completed preceding turn is recorded as a local text fingerprint. Before the next Send, its conversation URL and fingerprint boundary must still match. The result detector scopes to exactly one new turn after that boundary, checks the frozen prompt and unique decoded image, and ignores historical galleries. Changed history, extra turns, multiple new images, refusal, verification, quota, ambiguity or interruption stop the list. Existing outputs are protected, and remaining tasks are left pending.

The image viewer is closed through its normal Close control after verified save. An already-open viewer during batch collection is rejected because it might show an earlier image. If a download fails, close the viewer manually, inspect the original conversation, and use `collect ID --confirmed` on the task's recorded original URL. Collection uses the saved turn boundary and never sends again. Do not rerun the batch: its completed/submitted tasks are rejected. There is no automatic resume of remaining pending tasks after a failure.

Supported paired-turn DOM/labels are narrow and may change. A text fingerprint is a consistency guard, not proof against every UI mutation or a semantic image identity check. The service-terms/CDP risks in [SECURITY.md](../SECURITY.md) still apply; normal download buttons do not create platform permission.

## Timing and evidence

Individual timing reports remain in ignored `logs/<ID>/timing.json` and timing.md. `logs/<FIRST_ID>/batch.json` records exact IDs, completion/stopping, per-task timings and a monotonic preparation-through-final-cleanup wall time, including failures. It never implies an unsuccessful image was generated. Private URLs/state/output images are excluded from Git.

Offline fixtures test distinct downloads in one conversation, preserved history, old-viewer refusal, pending new turns, stop-on-refusal, preflight protection, navigation recovery URLs, legacy message containers and second-image download recovery without another Send. The local full suite passed **65 tests in 46.390 s** before the last two fixtures were added; both additional fixtures then passed targeted runs. This is local evidence, not a CI result for this feature branch.

## Actual two-image acceptance — 2026-10-13, Beijing time

The user authorized adding/testing a same-conversation sequence and delegated test prompt construction; two cat prompts above were used, no reference uploads. One CDP connection and **one conversation URL** were verified in local state. Two Send events and two distinct verified outputs were recorded, no recovery/retry. Both files are PNG 1672×941; they were decoded, hash-checked and visually inspected locally. The second image shows the cat raising a paw/tilting its head while retaining a similar window/blue cushion/garden composition; this observation does not prove identity preservation generally.

| Task | Send → observed complete | Download + verify | Send → verified save | Bytes |
| --- | --- | --- | --- | --- |
| SC01: cat sitting by the window | 39.828 s | 1.547 s | 42.500 s | 2,253,232 |
| SC02: continue context, change pose | 36.954 s | 1.093 s | 39.172 s | 2,298,873 |

Whole batch: **88.469 s**, from 12:47:18.925 to 12:48:47.393 Beijing time, including browser connection/image-mode preparation, viewer cleanup and history recording. The batch timer starts after local preflight; writing prompts/adding tasks is excluded. Individual Send→save timings exclude that shared browser preparation/cleanup. Polling/stability delays are included; these are observations, not server compute time or speed guarantees.

SC01 SHA-256: `23b2d617ee9e9e65457c2a831d8631d4d813822313f4671a49b109e72afe43f9`.

SC02 SHA-256: `9aac5c880dd76efb421626b6a69473076f54f823eef513939b43791f5aec2f2b`.

Actual files/logs and private conversation URL remain ignored local artifacts, not public demo assets. This trial demonstrates only this two-image Windows/Edge/Chinese-UI sequence; arbitrary batch size, live references, other UI variants, and platform permission remain unverified.
