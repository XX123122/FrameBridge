# Historical maintainer experiments (not new-user configuration)

Recorded 2026-10-13, Asia/Shanghai. These earlier experiments used one maintainer-selected visible Edge session on Windows 10 build 19045, Python 3.11.11, Pillow 12.3.0 and Playwright 1.63.0, with Chinese ChatGPT UI and no reference images. Browser and Codex accounts differed. Each task was explicitly authorized and submitted once.

| Trial | Subject / output | Evidence |
| --- | --- | --- |
| K01 | Ceramic mug; PNG 1672×941, 1,824,583 bytes | Old-message selector timed out; original request collected after DOM adaptation; no resend |
| K02 | Doraemon; PNG 1254×1254, 1,592,602 bytes | Observed generation 48.998 s; successful download/verify 0.485 s; total 152.588 s including preview repair/recovery |
| K03 | Cat; PNG 1374×1145, 2,211,575 bytes | Optimized one-command flow; observed generation 46.485 s, download/verify 1.828 s, total 49.453 s; no recovery |

Earlier K02 re-download (no new generation) measured 0.859 s from reopening the preview through download and hash checking. Its scope differs from total generation time. Different prompts/recovery paths do not support a model-speed comparison or guarantee.

Hashes and detailed chronology remain in [historical test results](TEST_RESULTS.md) and [optimization evidence](OPTIMIZATION.md). Original runtime images/logs are private, ignored local artifacts; they are not shipped or used as a fabricated demo. Public example prompts are nonsensitive samples. Historical test counts/timings are retained, with provenance, not rewritten to match later CI.

The records prove narrow earlier success, not general Chrome/Linux/macOS/English-UI compatibility, real reference uploads, preserved character identities, future quota availability or platform approval. They do not imply an installed/logged-in browser or authorize another user's request. The publication checks themselves perform no generation. A later, explicitly authorized serial trial is recorded separately in [queue trial](QUEUE_TRIAL.md); it does not replace these original records. Future live test samples use cats at the current user's request.
