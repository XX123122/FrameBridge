"""Finite, explicitly approved, text-only tasks in one ChatGPT conversation.

Scope each new turn against a persisted history boundary. Never drain the ledger,
adopt an arbitrary conversation, retry a failed request, or fetch image URLs.
"""
import hashlib
import re
import time
import uuid

from framebridge import TaskError, atomic_json, now
from web_chatgpt import (ASSISTANT, USER, STOP, REFUSAL, connected_image_page,
                        guard, unique_visible, wait_ready, record_web, run)

USER_HEADING = re.compile(r'^(你说：|You said:)$')
ASSISTANT_HEADING = re.compile(r'^(ChatGPT 说：|ChatGPT said:)$')
CLOSE = re.compile(r'^(关闭查看器|关闭|Close(?: viewer)?)$', re.I)


def text_digest(node):
    # Text content includes hidden semantic headings and excludes mutable CSS.
    text = re.sub(r'\s+', ' ', node.text_content() or '').strip()
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def history(page, limit=None):
    users, assistants = page.locator(USER), page.locator(ASSISTANT)
    if users.count() or assistants.count():
        count = min(users.count(), assistants.count()) if limit is None else limit
        if users.count() < count or assistants.count() < count:
            raise TaskError('Conversation history disappeared; stop')
        return {'style': 'legacy', 'users': users.count(), 'assistants': assistants.count(),
                'prefix': [[text_digest(users.nth(i)), text_digest(assistants.nth(i))] for i in range(count)]}
    turns = page.locator('main [data-talvt-turn-state]')
    count = turns.count() if limit is None else limit
    if turns.count() < count:
        raise TaskError('Conversation history disappeared; stop')
    prefix = []
    for i in range(count):
        turn = turns.nth(i)
        if (turn.get_attribute('data-talvt-turn-state') != 'complete'
                or turn.get_by_role('heading', name=USER_HEADING, include_hidden=True).count() != 1
                or turn.get_by_role('heading', name=ASSISTANT_HEADING, include_hidden=True).count() != 1):
            raise TaskError('Unsupported or incomplete paired conversation turn; stop')
        prefix.append(text_digest(turn))
    return {'style': 'modern', 'turns': turns.count(), 'prefix': prefix}


def close_preview(page):
    guard(page)
    dialog = unique_visible(page.get_by_role('dialog'), 'Image preview', False)
    if dialog is not None:
        wait_ready(page, dialog.get_by_role('button', name=CLOSE), 'Close image viewer').click()
        dialog.wait_for(state='hidden', timeout=8000)


def continuation_baseline(ledger, previous_id, page, endpoint):
    previous = ledger.task(ledger.load(), previous_id)
    web = previous.get('web', {})
    if (previous['status'] != 'completed' or not web.get('conversation_history')
            or web.get('endpoint') != endpoint or web.get('page_url') != page.url):
        raise TaskError('Continuation requires the verified preceding task in this same conversation')
    ledger.check(previous_id)
    if history(page) != web['conversation_history']:
        raise TaskError('Conversation changed since the preceding verified save; stop before Send')
    snapshot = web['conversation_history']
    return {'baseline_history': snapshot, 'previous_task_id': previous_id,
            'baseline_assistant_count': snapshot.get('assistants', 0),
            'baseline_user_count': snapshot.get('users', 0)}


def batch_result(page, task):
    baseline = task['web']['baseline_history']
    count = len(baseline['prefix'])
    current = history(page, limit=count)
    if current['style'] != baseline['style'] or current['prefix'] != baseline['prefix']:
        raise TaskError('Prior conversation history changed; cannot attribute the new result')
    if unique_visible(page.locator(STOP), 'Generating', False):
        return None
    if baseline['style'] == 'legacy':
        users, assistants = page.locator(USER), page.locator(ASSISTANT)
        if users.count() > count + 1 or assistants.count() > count + 1:
            raise TaskError('Extra messages appeared; stop')
        if users.count() <= count or assistants.count() <= count:
            return None
        user, result = users.nth(count), assistants.nth(count)
        galleries = None
    else:
        turns = page.locator('main [data-talvt-turn-state]')
        if turns.count() > count + 1:
            raise TaskError('Extra conversation turns appeared; stop')
        if turns.count() <= count:
            return None
        result = turns.nth(count)
        if result.get_attribute('data-talvt-turn-state') != 'complete':
            return None
        if (result.get_by_role('heading', name=USER_HEADING, include_hidden=True).count() != 1
                or result.get_by_role('heading', name=ASSISTANT_HEADING, include_hidden=True).count() != 1):
            return None
        user = result
        galleries = result.get_by_test_id('generated-image-gallery')
        if galleries.count() > 1:
            raise TaskError('Multiple new galleries; only one image authorized')
    expected = re.sub(r'\s+', ' ', task['prompt_text']).strip()
    if expected not in re.sub(r'\s+', ' ', user.inner_text()).strip():
        raise TaskError('New user turn does not match the frozen prompt')
    if galleries is not None:
        if galleries.count() == 0:
            if REFUSAL.search(result.inner_text()):
                raise TaskError('platform_refusal: stop batch without rewriting/resubmitting')
            return None
        previews = galleries.get_by_test_id('generated-image-preview')
        if previews.count() > 1:
            raise TaskError('Multiple new images; only one image authorized')
        images = previews.locator('img')
    else:
        images = result.locator('img, canvas')
        if images.count() == 0 and REFUSAL.search(result.inner_text()):
            raise TaskError('platform_refusal: stop batch without rewriting/resubmitting')
    generated = []
    for i in range(images.count()):
        item = images.nth(i)
        if item.is_visible() and item.evaluate("el => el.tagName === 'CANVAS' ? el.width >= 256 && el.height >= 256 : el.complete && el.naturalWidth >= 256 && el.naturalHeight >= 256"):
            generated.append(item)
    if len(generated) > 1:
        raise TaskError('Multiple decoded new images; stop')
    return (result, generated[0]) if generated else None


def preflight(ledger, ids):
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise TaskError('batch requires at least two distinct, explicitly approved task IDs')
    state = ledger.load()
    if any(t['status'] == 'running' or t['needs_confirmation'] for t in state['tasks']):
        raise TaskError('Resolve running/uncertain tasks before starting a batch')
    for task_id in ids:
        task = ledger.task(state, task_id)
        if task['status'] != 'pending' or task['mode'] != 'web-ui' or task.get('references'):
            raise TaskError('Initial same-chat batch supports only pending text-only web tasks')
        ledger.verify_inputs(task)
        if ledger.bounded(task['output_path'], 'outputs').exists():
            raise TaskError('Existing output protected; stop entire batch before connecting')


def run_batch(ledger, ids, endpoint, timeout=180, *, confirmed=False, progress=None):
    if not confirmed:
        raise TaskError('Explicit approval for this finite prompt/image list required')
    if not 1 <= timeout <= 600:
        raise TaskError('Observation timeout must be 1–600 seconds per task')
    preflight(ledger, ids)
    started_at, started_clock = now(), time.monotonic()
    report = {'batch_id': uuid.uuid4().hex, 'ids': list(ids), 'mode': 'same-conversation',
              'started_at': started_at, 'status': 'running', 'completed': [], 'stopped_at': None}
    report_path = ledger.bounded(f'logs/{ids[0]}/batch.json', 'logs')
    atomic_json(report_path, report)
    current_id = ids[0]
    try:
        with connected_image_page(endpoint) as page:
            previous_id = None
            for index, current_id in enumerate(ids):
                preflight_one = ledger.task(ledger.load(), current_id)
                if preflight_one['status'] != 'pending' or preflight_one.get('references'):
                    raise TaskError('Next task changed; stop')
                close_preview(page)
                record_web(ledger, current_id, batch_id=report['batch_id'], batch_index=index)
                callback = (lambda phase, **metrics: progress(current_id, phase, **metrics)) if progress else None
                result = run(ledger, current_id, page, endpoint, timeout, progress=callback,
                             previous_task_id=previous_id)
                report['completed'].append({'id': current_id, 'output': result['output_path'],
                                            'timing': result['web']['timing']})
                atomic_json(report_path, report)
                close_preview(page)
                record_web(ledger, current_id, conversation_history=history(page))
                previous_id = current_id
        report['status'] = 'completed'
        return report
    except BaseException as error:
        report.update(status='stopped', stopped_at=current_id, error=str(error), automatic_retry=False)
        raise
    finally:
        report.update(finished_at=now(), wall_seconds=round(time.monotonic() - started_clock, 3))
        atomic_json(report_path, report)
