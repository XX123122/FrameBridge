# Completed image detection repair — 2026-11-03

## Reproduced problem and fix

A user reported that an image was visible in their original conversation, but both generation observation and a later collect-only attempt reached their 300-second observation limits. Inspection of that exact existing page found one completed turn, one generated-image gallery and one decoded preview. No new prompt was sent during diagnosis.

The page now decorates the message headings: `你说：你` and `ChatGPT 说：ChatGPT`. The old detector matched only the exact labels `你说：` / `ChatGPT 说：`; its message-count check therefore stayed unready despite a completed image. The new shared `message_headings` helper uses `data-conversation-role` on semantic headings, retaining exact old labels as a compatibility fallback. It does not accept arbitrary text prefixes. Single-image observation, empty-chat checks and same-conversation history/result checks share this helper.

Prompt matching, original conversation URL, complete turn state, unique gallery/decoded image, extra-message rejection and output protection remain required. This repairs the observed DOM variant, not every possible future interface. Missing/ambiguous markers still stop or time out rather than guessing.

Pre-existing uncommitted completed-text failure handling was preserved and tested alongside this fix: recognized tool-error, reference-request and refusal wording stops observation with a local diagnostic code and uncertainty flag. Assistant prose is not a verified backend error diagnosis; unknown wording can still time out. No automatic retry, account switch or prompt rewrite is added.

## Evidence

- Full offline suite: **87 passed, zero failed/skipped, 78.730 seconds**, Windows/Python 3.11/isolated Edge. Fixtures intercept page requests and block service workers; no personal profile or live ChatGPT request is used by the suite.
- Regression coverage: decorated-role heading recovery, same-chat latest-image scope, changed Prompt/extra messages, refusal to trust arbitrary unmarked heading suffixes, completed-text failures and existing no-overwrite/no-resend cases.
- The existing image-mode preparation fixture additionally checks one click on Add files, one click on Create image and zero Send clicks. Those are two different controls; no live repeat-generation test was performed to investigate the user's double-click concern.
- Live **collect-only recovery** succeeded through the original page's normal preview/Download button. PNG 1752×897, 1,711,062 bytes, decoded/hash-checked and inspected locally. Submission count remained **one** before/after recovery. No new image generation or reference upload occurred, and no other pending tasks were executed.
- Output SHA-256: `6f2920aaa29bb7e8f3136e67aa193b01ea3cc3af0282ee0970ffe125e13e8c67`.

The original Send→save timing includes earlier timeouts, diagnosis and recovery waiting. It is not generation speed. The actual server completion time was not measured. Private task IDs, prompt content, conversation URL, output file and detailed logs remain local ignored artifacts; the image is not published as demo media.

## Continue an existing task

Use this checkout's updated source. Inspect `framebridge.py show/check ID` locally first: if it is already completed, link the existing file instead of generating again. For a submitted uncertain task, authorize only `collect` on its recorded original page. Never rerun generate/batch to collect an already-generated image. See [recovery](USAGE.md) and [same-chat workflow](SAME_CHAT_BATCH.md).

Do not infer from this fix that remaining tasks are authorized to run. No additional Tag/Release, repository settings or community publication is included. Remote CI results require an actual run on the submitted fix revision.
