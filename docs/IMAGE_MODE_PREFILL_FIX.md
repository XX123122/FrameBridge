# Image-mode preparation and draft protection — 2026-11-03

## Observed block

A second independent image task stopped before submission with “different existing composer content.” Inspection found only the page's native Create-image inline tool pill, not user-authored prompt text: a noneditable element with `data-inline-selection-pill` and `data-system-hint-type="picture_v2"`. Its visible label was included in innerText. Clearing it caused the editor to restore it, so preparation appeared empty briefly and the following submission guard rejected the returned label as a foreign draft.

Opening another home tab or clicking New chat did not remove this tool hint in the observed session. The repair therefore identifies the tool structurally rather than clearing arbitrary text or relaxing draft protection.

## Behavior

- The composer serializer excludes only that exact native noneditable image hint from user text. Real prompt text, internal blank lines and spaces still require matching the immutable task prompt. A paragraph containing just a filler BR represents an empty paragraph, rather than an extra line break.
- An already-selected native image tool is retained; preparation does not click Add/Create image again. Normal editor selection/input replaces only content after the pill, preserving the active tool and the original multiline Prompt.
- For the older plain-text image-mode UI, preparation retains short-lived, same-page, process-local proof of its own menu selection. Only the known default from that action may be replaced if it reappears. Arbitrary existing text reading “创建图像” is still a protected draft without that proof; nothing is inferred from a historical session or stored authorization.
- Automatic fresh-task preparation reuses only one demonstrably empty home. Occupied or ambiguous homes are left untouched and a separate tab is created within the selected browser context. If the new page restores real draft/attachment content too, it stops without clearing it or starting an endless new-tab loop.
- Explicit `--page ... run` still preserves a different draft rather than choosing another conversation. New-page preparation grants no Send/upload authority, skips no failed task and does not run other pending tasks.

## Validation

Offline regression coverage includes reappearing own defaults, no-proof lookalike text, real drafts after preparation, native-hint multiline insertion and tool preservation, existing attachments, occupied homes and restored drafts in new tabs. Existing single-image/edit/batch/result-attribution checks remain in the suite. **96 tests passed, zero failures/skips, in 85.391 seconds**, on the local Windows/Python 3.11/isolated Edge suite; page requests are intercepted and service workers blocked. This is an actual local result, not inferred from earlier CI.

Zero-quota verification against the current visible Edge session succeeded: the exact pending second task's multiline Prompt was staged and checked in a disposable newly created tab, the native image hint remained, and original home-tab user text was unchanged. No Send, download, reference upload or task-state change occurred; only that disposable probe tab was closed. The second task remained pending with zero submission events. Earlier generated/downloaded images were not regenerated or overwritten.

The zero-quota verification does not claim the next real generation/download has occurred. Remaining task execution belongs to the user's authorized generation conversation. Use this checkout's updated source and existing pending ID; do not recreate tasks or repeat a completed image. Remote CI requires an actual run on this fix revision. Unknown tool markers/UI variants still require review; no storage/authentication extraction, private API or protection bypass is added.
