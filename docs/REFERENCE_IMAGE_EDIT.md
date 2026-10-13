# Reference images and prompt-directed edits

FrameBridge accepts explicitly named PNG/JPG/JPEG/WebP reference images for individual tasks. An `edit` task records that intent and requires at least one reference. It uploads only immutable snapshots through a normal file input or the page's normal Upload-from-computer chooser, submits the original edit prompt once, then downloads/verifies the new generated result. No image URL, credential, private-model endpoint or region-mask API is used.

## Prepare locally

Follow [setup](SETUP.md) first. Put your explicitly selected image in references/ under a new filename, preserving the original. If selecting an existing output, copy its bytes without overwriting either file; do not resize/recompress it. Original outputs are never edited in place.

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py add EDIT01 --operation edit --prompt prompts/cat-edit-cushion.md --reference references/my-cat.png --output outputs/EDIT01.png
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py packet EDIT01
```

Use your own actual reference filename and new ID/output. Each additional image must be explicitly authorized and named with another `--reference`. The original Prompt/bytes, format, dimensions, SHA-256 and reference list are frozen in logs/. Task preparation consumes no quota and uploads nothing. Files must be static images within the [local limits](USAGE.md).

For ordinary reference-guided generation, omit `--operation edit` and use `generate`. `edit` records an edit request, not a guarantee that the model preserves every unmodified pixel or identity. Batch remains text-only; references are rejected by that path before browser access.

## Authorize and execute one edit

Only after the current user approves this Prompt, exact reference list, one output and normal download:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 edit EDIT01 --confirmed --timeout 300
.\.venv\Scripts\python.exe -X utf8 scripts/framebridge.py check EDIT01
```

The new task starts a fresh image-mode chat, not an unrelated private conversation. Multiple hidden file inputs are resolved through the normal Upload button/file-chooser event; no arbitrary first-input selection. It rejects existing attachments, checks approved snapshots, observes retained exact selection or decoded draft previews without visible upload progress, and requires stable enabled Send. Upload errors, verification/quota, ambiguous controls or uncertain readiness stop before Send. These UI signals are not a private server acknowledgement.

`web.reference_upload` records method, reference snapshot hashes/count, readiness evidence and elapsed selection/readiness time. Individual timing reports start at Send, so upload/browser setup is not included in Send→save. A technically valid file can still contain an incorrect edit: compare it with the original visually before declaring the requested change satisfied.

## Scope and recovery

Keep original identity/roles and edit intent; do not silently replace references or rewrite prompts. Only authorized image snapshots are uploaded, not Markdown files, logs, tasks.json or the project. `generate` rejects a prepared edit task so intent is not silently changed. Earlier tasks without an operation field retain their original generate behavior.

Do not rerun a submitted/uncertain edit. After reviewing the original conversation and closing unrelated previews, explicitly authorize `collect` on its recorded URL; it downloads the original result without resending or uploading again. Use [recovery](USAGE.md) for interruptions. Files identical to a reference, corrupted files and existing output collisions are rejected. Local stop does not prove the remote request stopped.

For a failed **never-submitted edit draft only**, `resume-draft` can perform its first Send without reuploading. Current-user approval must cover the same exact task/reference/output. It requires no submission intent/event/timestamp, the recorded home URL and endpoint, unchanged original Prompt, decoded reference previews with matching names/dimensions, recorded snapshot hashes, and no messages/generation/other active uncertainty. Submitted requests and changed drafts are rejected, not retried:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/web_chatgpt.py --cdp http://127.0.0.1:9222 --page https://chatgpt.com/ resume-draft EDIT01 --confirmed --timeout 300
```

This is a guarded explicit recovery action, not an automatic loop or a cryptographic attestation of browser pixels. If any check is uncertain, stop and inspect manually. Multi-paragraph plain ProseMirror drafts are verified by their paragraph/line-break structure rather than innerText's additional visual spacing; original prompt bytes and internal blank lines/spaces are preserved.

This is generative editing from a reference and prompt, not a pixel-preserving paint/mask workflow. Identity consistency, perfect region isolation, arbitrary UI versions and live multi-reference behavior are not guaranteed. Standard web UI automation is unofficial and automated output collection has service-terms risk; see [SECURITY.md](../SECURITY.md). No paid/private API fallback or protection bypass is included.

## Validation evidence

Offline checks cover operation validation/backward compatibility, exact snapshots, normal chooser selection despite decoy inputs, input-reset/preview readiness, upload-error stops, multiple named references, paragraph serialization, never-submitted draft recovery and no submission without approval. **78 tests passed, zero failures/skips, in 71.899 seconds** on the local Windows/isolated Edge suite. Browser requests are mocked/intercepted; this is not live upload evidence or a CI result on this new branch. Actual live acceptance is recorded here only after completion.

### Live PNG edit acceptance — 2026-10-13, Beijing time

The user delegated selecting an existing image and constructing/testing an edit prompt. Source SC01 was copied byte-for-byte to a new reference file and snapshotted; one PNG was selected through the normal file chooser. The [prompt](../prompts/cat-edit-cushion.md) requested changing only the blue cushion to red while preserving the cat/scene. REFEDIT01 was downloaded through the normal page button, decoded and hash-checked, then visually inspected locally: the cushion is red and the overall cat pose/window/flowerpot/garden composition is similar. Fine details need not be pixel-identical; this is not proof of general identity/region isolation.

| Measurement | Actual observation |
| --- | --- |
| Reference selection/readiness | 10.297 s; normal file chooser, one decoded draft preview |
| Send → observed completion | 64.641 s |
| Normal download + verify | 6.094 s |
| Send → verified save | 71.891 s |
| Actual Send count | 1 |
| Output | PNG 1672×941, 2,181,558 bytes |

The first local execution stopped **before Send** because the editor's innerText added paragraph spacing. After strict paragraph serialization and regression tests, the unchanged existing draft was resumed once without reuploading. No earlier submission intent/event/timestamp existed. This pre-submission debugging/test wait and the earlier upload are excluded from Send→save; no preparation-through-save end-to-end time is claimed. Submitted results were never retried.

Source/reference/snapshot SHA-256, rechecked unchanged: `23b2d617ee9e9e65457c2a831d8631d4d813822313f4671a49b109e72afe43f9`.

Edited output SHA-256: `d29f4da2d8b4617c611c246a42479269ddcf7b930626fcc2c260a1e3e5ba4b9d`.

Original images, reference copy, snapshots, private conversation URL and task/timing logs remain ignored local artifacts; they are not public demo media. Narrow evidence: one PNG, Windows/visible Edge/Chinese UI. Live multiple references/JPG/WebP/other UI variants and exact identity/pixel preservation remain unverified.
