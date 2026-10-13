# Authorized serial trial — 2026-10-13

This is a narrow observed trial on the maintainer-selected Windows/visible Edge/Chinese UI session, not general batch certification. The user explicitly requested reuse of K01–K03. New task IDs/output paths protected the original images and snapshots. Exactly one Send was recorded for each new task; no reference images were used.

| Task | Original prompt | Outcome | Send → observed image | Download + verify | Send → verified save |
| --- | --- | --- | --- | --- | --- |
| Q01 | K01: ceramic mug | Completed; PNG 1672×941, 1,960,452 bytes | 39.110 s | 1.719 s | 41.938 s |
| Q02 | K02: Doraemon | Completed textual refusal; no image; failed and later explicitly closed by user | Not available | Not performed | Not available |
| Q03 | K03: cat | Completed after explicit user authorization to skip Q02; PNG 1312×1199, 2,358,265 bytes | 46.609 s | 2.000 s | 49.750 s |

Q02 stopped the serial runner. The page returned a refusal to generate the requested character. The original detector waited for an image and timed out: Send → timeout was **301.541 s**. This is failure waiting, not image generation time. The observable interval from Q01 Send to that queue stop was **348.833 s**; a complete preparation-inclusive queue stopwatch was not persisted. Human waiting before Q03 is excluded from per-image timings, and no uninterrupted three-success queue time is claimed.

The user then explicitly approved skipping Q02 and running only the original Q03 cat task. Q02 was closed without output; its prompt was not rewritten, retried or replaced. A completed-text refusal detector and isolated regression fixture were added afterward, but not validated by repeating a live refusal. It recognizes specific wording and DOM states; unknown text results still stop on timeout.

The user's final test preference is **cats for future tests**. `prompts/example.md` and the synthetic browser prompt use cats. Historical K01/K02/K03 and Q01/Q02 snapshots remain unchanged. This mixed trial does not prove three successful cat tasks or unattended queue behavior. There is no automatic general queue drain: the trial wrapper contained only the three explicitly authorized IDs and stopped on first failure.

## Local artifacts and measurement limits

Q01 SHA-256: `57034d24e969eefda787a5a2713cd051577a937144678bb95310ef23441fd0bb`.

Q03 SHA-256: `5744bb7e9ef2ea79c8d2d444226a25afdd110df31e84b58bb7e2d7fcb831480b`.

Images, original prompt snapshots, state, private conversation URLs and detailed timing logs remain ignored local artifacts in outputs/, logs/ and tasks.json; they are not public demo assets. Successful downloads used the page's normal Download action, were decoded and hash-checked. Q03 was also visually inspected locally and depicts a cat. Timings include polling, stability and preview delays, not server compute time; they offer no performance or future quota guarantee.

See [historical experiments](HISTORICAL_EXPERIMENTS.md), [usage/recovery](USAGE.md) and [release readiness](RELEASE_READINESS.md). This trial does not establish official platform permission or live reference-upload compatibility.
