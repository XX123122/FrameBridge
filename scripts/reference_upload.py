"""Normal reference-image selection only; no credentials or asset-URL access."""
from pathlib import Path
import re
import time

from framebridge import TaskError, now
from web_chatgpt import COMPOSER, guard, unique_visible, wait_ready

UPLOAD = re.compile(r'添加照片和文件|Add photos (?:&|and) files|Upload photos and files', re.I)
UPLOAD_ERROR = re.compile(r'上传失败|无法上传|文件过大|failed to upload|unable to upload|file.*too large|unsupported file', re.I)


def assert_upload_ok(page):
    composer = unique_visible(page.locator(COMPOSER), 'Composer')
    form = composer.locator('xpath=ancestor::form[1]')
    scope = form if form.count() == 1 else page.locator('body')
    errors = scope.get_by_text(UPLOAD_ERROR)
    if any(errors.nth(i).is_visible() for i in range(errors.count())):
        raise TaskError('Reference upload failed; stop before Send')


def upload_references(ledger, task, page, timeout_ms=30000):
    ledger.verify_inputs(task)
    refs = task['references']
    if not refs:
        raise TaskError('No approved reference snapshots')
    guard(page)
    composer = unique_visible(page.locator(COMPOSER), 'Composer')
    form = composer.locator('xpath=ancestor::form[1]')
    scope = form if form.count() == 1 else page.locator('body')
    inputs = scope.locator('input[type="file"]')
    if any(inputs.nth(i).evaluate('el => (el.files || []).length > 0') for i in range(inputs.count())):
        raise TaskError('Existing selected attachments; do not replace or add extra files')
    initial_images = sum(scope.locator('img').nth(i).is_visible() for i in range(scope.locator('img').count()))
    if initial_images:
        raise TaskError('Existing composer images; review attachments before upload')
    paths = [str(ledger.root / ref['snapshot_path']) for ref in refs]
    expected = [Path(path).name for path in paths]
    started = time.monotonic()
    image_inputs = scope.locator('input[type="file"][accept*="image"]')
    candidate = image_inputs if image_inputs.count() else inputs
    chooser_used = candidate.count() != 1
    if not chooser_used:
        selected_input = candidate.nth(0)
        if len(paths) > 1 and selected_input.get_attribute('multiple') is None:
            raise TaskError('Upload control does not support the approved multiple references')
        selected_input.set_input_files(paths)
    else:
        upload = unique_visible(page.get_by_role('button', name=UPLOAD), 'Upload from computer', False)
        if upload is None:
            wait_ready(page, page.get_by_role('button', name='添加文件等内容', exact=True), 'Add files menu').click()
            upload = wait_ready(page, page.get_by_role('button', name=UPLOAD), 'Upload from computer')
        with page.expect_file_chooser(timeout=8000) as event:
            upload.click()
        chooser = event.value
        if len(paths) > 1 and not chooser.is_multiple():
            raise TaskError('File chooser does not support the approved multiple references')
        selected_input = chooser.element
        chooser.set_files(paths)
    # Some normal upload UIs clear/replace the input after handling change.
    # Exact selection comes from set_files(paths); then require draft preview or
    # a retained exact FileList. Send readiness is checked separately by run().
    deadline = started + timeout_ms / 1000
    while True:
        guard(page)
        assert_upload_ok(page)
        try:
            selected = selected_input.evaluate('el => Array.from(el.files || []).map(f => f.name)')
        except Exception:
            selected = []  # Input can be removed by the UI after selection.
        if selected and selected != expected:
            raise TaskError('Unexpected selected reference list; stop')
        images = scope.locator('img')
        visible_images = [images.nth(i) for i in range(images.count()) if images.nth(i).is_visible()]
        if len(visible_images) > len(refs):
            raise TaskError('Unexpected extra attachment previews; stop')
        progress = scope.get_by_role('progressbar')
        progressing = any(progress.nth(i).is_visible() for i in range(progress.count()))
        thumbnails_ready = len(visible_images) == len(refs) and all(
            image.evaluate('el => el.complete && el.naturalWidth > 0 && el.naturalHeight > 0')
            for image in visible_images)
        if not progressing and (selected == expected or thumbnails_ready):
            return {'method': 'normal_file_chooser' if chooser_used else 'unique_file_input',
                    'count': len(refs), 'snapshot_names': expected,
                    'snapshot_sha256': [r['sha256'] for r in refs],
                    'selection_observed_at': now(), 'seconds': round(time.monotonic() - started, 3),
                    'evidence': 'exact_file_list' if selected == expected else 'decoded_draft_previews'}
        if time.monotonic() >= deadline:
            raise TaskError('Reference upload readiness unknown; stop before Send')
        page.wait_for_timeout(100)
