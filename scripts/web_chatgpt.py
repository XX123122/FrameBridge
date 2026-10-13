"""One authorized ChatGPT UI task using visible Edge/Chrome over local CDP.

Only DOM controls and the page's normal Download/Save action are used. This is
NOT an officially supported ChatGPT API. No auth/storage/network-response access.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.parse import urlparse

from framebridge import Ledger, TaskError, inspect_image, read_limited, now

ASSISTANT = '[data-message-author-role="assistant"]'
USER = '[data-message-author-role="user"]'
COMPOSER = '#prompt-textarea, [role="textbox"][contenteditable="true"]'
SEND = 'button[data-testid="send-button"], button[data-testid="composer-submit-button"], button[aria-label="发送"]'
STOP = 'button[data-testid="stop-button"]'
BLOCKED = re.compile(
    r"verify you are human|checking your browser|unusual activity|too many requests|"
    r"you.ve reached.*limit|image generation limit|can.t generate.*right now|"
    r"not allowed|access denied|验证您是人类|验证你是人类|请求过多|已达到.*上限|额度已用完|无权访问", re.I)
DOWNLOAD_NAME = re.compile(r"^(Download( image)?|Save( image)?|下载(图片|图像)?|保存(图片|图像)?)$", re.I)
REFUSAL = re.compile(r"(?:抱歉[^\n]*?(?:不能|无法)[^\n]*?(?:生成|创建)|(?:I (?:cannot|can't|can’t|am unable to)|unable to)\s+(?:generate|create))", re.I)
POLL_SECONDS = 1
PREVIEW_TIMEOUT_MS = 8_000


def composer_matches(actual, prompt):
    # contenteditable paragraph rendering can add terminal blank lines to innerText.
    # Keep the original bytes/prompt passed to fill; ignore only DOM terminal newlines.
    return actual.replace("\r\n", "\n").rstrip("\n") == prompt.replace("\r\n", "\n").rstrip("\n")


def composer_text(composer):
    # ProseMirror innerText adds visual paragraph spacing. Serialize its plain
    # paragraph structure instead, preserving every internal blank line/space.
    return composer.evaluate('''el => {
        const nodes=Array.from(el.childNodes);
        if(!nodes.length || !nodes.every(n=>n.nodeType===1 && n.tagName==='P')) return el.innerText;
        const read=n=>n.nodeType===3?n.textContent:n.nodeType!==1?'':
            n.tagName==='BR'?(n.classList.contains('ProseMirror-trailingBreak')?'':'\\n'):
            Array.from(n.childNodes).map(read).join('');
        return nodes.map(read).join('\\n');
    }''')


def checked_endpoint(value):
    url = urlparse(value)
    if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "[::1]", "::1"}
            or url.username or url.password or url.path not in {"", "/"} or url.query or url.fragment or not url.port):
        raise TaskError("CDP 仅允许明确指定的本机 HTTP 端口；不会扫描端口或连接远程浏览器")
    return value.rstrip("/")


def checked_page(value):
    url = urlparse(value)
    if (url.scheme != "https" or url.netloc != "chatgpt.com" or url.query or url.fragment
            or not re.fullmatch(r"/|/c/[A-Za-z0-9-]+", url.path)):
        raise TaskError("只支持明确指定的 https://chatgpt.com/ 或 /c/<id> 页面，不接受查询参数")
    return value


def unique_visible(locator, label, required=True):
    visible = [locator.nth(i) for i in range(locator.count()) if locator.nth(i).is_visible()]
    if len(visible) > 1 or (required and not visible):
        raise TaskError(f"{label} 不是唯一可见控件（{len(visible)}）；停止并人工核对 UI")
    return visible[0] if visible else None


def wait_ready(page, locator, label, timeout_ms=PREVIEW_TIMEOUT_MS):
    deadline = time.monotonic() + timeout_ms / 1000
    while True:
        guard(page)
        control = unique_visible(locator, label, False)
        if control is not None and control.is_enabled():
            return control
        if time.monotonic() >= deadline:
            raise TaskError(f'{label} 等待超时；不重复点击或发送')
        page.wait_for_timeout(100)


def guard(page):
    checked_page(page.url)
    if re.search(r"just a moment|attention required|access denied", page.title(), re.I):
        raise TaskError("verification")
    if unique_visible(page.locator('iframe[src*="challenges.cloudflare.com"], input[name="cf-turnstile-response"]'), "安全验证", False):
        raise TaskError("verification")
    # Do not read authentication, browser storage, request headers or response bodies.
    if page.get_by_text(BLOCKED).count():
        if any(page.get_by_text(BLOCKED).nth(i).is_visible() for i in range(page.get_by_text(BLOCKED).count())):
            raise TaskError("verification_or_quota_or_permission")
    login_controls = page.get_by_role("button", name=re.compile(r"^(Log in|Sign up|登录|注册)$", re.I))
    # Logged-out pages normally show both controls; their multiplicity is not UI drift.
    if any(login_controls.nth(i).is_visible() for i in range(login_controls.count())):
        raise TaskError("login_required")


def probe(page):
    guard(page)
    composer = unique_visible(page.locator(COMPOSER), "输入框")
    return {"composer": True, "composer_editable": composer.is_editable(),
            "image_entry_visible": bool(unique_visible(page.get_by_role("button", name=re.compile(r"^(Create image|Images|创建图片|创建图像|生成图片|图像)(?:\s|$)", re.I)), "图片入口", False)),
            "file_inputs": page.locator('input[type="file"]').count(),
            "download_strategy": "normal_page_button_only", "request_submitted": False}


@contextmanager
def connected_browser(endpoint):
    endpoint = checked_endpoint(endpoint)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise TaskError("未安装可选 Playwright；先审查 requirements-browser.txt，再安装。不会切换浏览器。") from error
    with sync_playwright() as runtime:
        browser = runtime.chromium.connect_over_cdp(endpoint, timeout=10_000)
        # Never call browser.close(): the browser is owned by the user.
        yield browser


@contextmanager
def connected_page(endpoint, page_url):
    page_url = checked_page(page_url)
    with connected_browser(endpoint) as browser:
        candidates = [p for context in browser.contexts for p in context.pages if p.url == page_url]
        if len(candidates) != 1:
            raise TaskError(f"指定页面必须只存在一个标签页；找到 {len(candidates)} 个。请手动打开并登录。")
        page = candidates[0]
        page.set_default_timeout(5_000)
        page.bring_to_front()
        yield page


def prepare_image_page(context):
    roots = [page for page in context.pages if page.url == 'https://chatgpt.com/']
    if len(roots) > 1:
        raise TaskError('存在多个首页标签页，请人工确定目标')
    if roots:
        page = roots[0]
    else:
        page = context.new_page()
        page.goto('https://chatgpt.com/', wait_until='domcontentloaded', timeout=20_000)
    page.set_default_timeout(5_000)
    page.bring_to_front()
    guard(page)
    page.locator(COMPOSER).wait_for(state='visible', timeout=15_000)
    composer = unique_visible(page.locator(COMPOSER), '输入框')
    headings = page.locator('main').get_by_role('heading',
        name=re.compile(r'^(你说：|You said:|ChatGPT 说：|ChatGPT said:)$'), include_hidden=True)
    if composer.inner_text().strip() or page.locator(USER).count() or page.locator(ASSISTANT).count() or headings.count():
        raise TaskError('页面已有草稿或消息，保持原内容并停止')
    wait_ready(page, page.get_by_role('button', name='添加文件等内容', exact=True), '添加菜单').click()
    wait_ready(page, page.get_by_role('button', name=re.compile(r'^创建图像(?:\s|$)')), '创建图像').click()
    # Wait for the default text generated by the image-mode selection itself.
    deadline = time.monotonic() + 5
    while True:
        guard(page)
        composer = unique_visible(page.locator(COMPOSER), '图片输入框')
        text = composer.inner_text().strip()
        if text == '创建图像':
            composer.fill('')
            break
        if text:
            raise TaskError('图片模式出现未知内容，停止而不替换')
        if time.monotonic() >= deadline:
            raise TaskError('无法确认图片模式选择，停止而不发送')
        page.wait_for_timeout(100)
    return page


@contextmanager
def connected_image_page(endpoint):
    with connected_browser(endpoint) as browser:
        if len(browser.contexts) != 1:
            raise TaskError('需要唯一的已授权浏览器会话，不能猜测其它登录档')
        yield prepare_image_page(browser.contexts[0])


def record_web(ledger, task_id, **fields):
    with ledger.lock():
        state = ledger.load()
        task = ledger.task(state, task_id)
        task.setdefault("web", {}).update(fields)
        ledger.event(task, "web_state_recorded")
        ledger.save(state)


def fail_uncertain(ledger, task_id):
    task = ledger.task(ledger.load(), task_id)
    if task["status"] == "running":
        ledger.stop(task_id, "uncertain")


def prepare_submission(ledger, task_id, page, endpoint, previous_task_id=None):
    task = ledger.task(ledger.load(), task_id)
    if task["mode"] != "web-ui":
        raise TaskError("任务路径不匹配；不会切换到网页")
    probe(page)
    composer = unique_visible(page.locator(COMPOSER), "输入框")
    existing = composer_text(composer)
    if existing.strip() and not composer_matches(existing, task["prompt_text"]):
        raise TaskError("输入框已有不同内容；不会替换用户草稿")
    if unique_visible(page.locator(STOP), "生成中", False):
        raise TaskError("当前页面正在生成，停止")
    current_headings = page.locator('main').get_by_role(
        'heading', name=re.compile(r'^(你说：|You said:|ChatGPT 说：|ChatGPT said:)$'), include_hidden=True)
    continuation = {}
    if previous_task_id is not None:
        from conversation_batch import continuation_baseline
        continuation = continuation_baseline(ledger, previous_task_id, page, endpoint)
    elif (page.url != 'https://chatgpt.com/' or page.locator(USER).count()
            or page.locator(ASSISTANT).count() or current_headings.count()):
        raise TaskError("首次提交必须使用空白新对话，避免混淆旧结果")
    ledger.start(task_id, confirmed=True)
    record_web(ledger, task_id, endpoint=endpoint, page_url=page.url,
               baseline_assistant_count=continuation.get('baseline_assistant_count', 0),
               baseline_user_count=continuation.get('baseline_user_count', 0), backend="playwright-ui",
               **{k: v for k, v in continuation.items() if k not in {'baseline_assistant_count', 'baseline_user_count'}})
    # Only explicit, immutable reference snapshots are attached; never upload a directory.
    if task["references"]:
        from reference_upload import upload_references
        record_web(ledger, task_id, reference_upload_started_at=now())
        upload = upload_references(ledger, task, page)
        record_web(ledger, task_id, reference_upload=upload)
    composer.fill(task["prompt_text"])
    if not composer_matches(composer_text(composer), task["prompt_text"]):
        raise TaskError("网页输入内容与原始 Prompt 不一致，停止")
    send_prepared(ledger, task_id, page)


def send_prepared(ledger, task_id, page):
    task = ledger.task(ledger.load(), task_id)
    if not composer_matches(composer_text(unique_visible(page.locator(COMPOSER), 'Composer')), task['prompt_text']):
        raise TaskError('Prepared draft changed; do not Send')
    button = unique_visible(page.locator(SEND), "发送按钮")
    button.wait_for(state="visible", timeout=30_000)
    deadline = time.monotonic() + 30
    while True:
        guard(page)
        if task['references']:
            from reference_upload import assert_upload_ok
            assert_upload_ok(page)
        if button.is_enabled():
            if not task['references']:
                break
            page.wait_for_timeout(500)
            guard(page)
            assert_upload_ok(page)
            if button.is_enabled():
                break
        if time.monotonic() >= deadline:
            raise TaskError("上传/发送未就绪；不会点击或重新提交")
        page.wait_for_timeout(500)
    guard(page)
    # Persist intent BEFORE the one click. A crash at this boundary is uncertain,
    # never a reason to click again.
    ledger.submitted(task_id, confirmed=True)
    record_web(ledger, task_id, submission_intent=True)
    click_at, click_clock = now(), time.monotonic()
    button.click()
    record_web(ledger, task_id, send_click_started_at=click_at,
               send_click_monotonic=click_clock, timing_process_id=os.getpid())


def new_result(page, task):
    guard(page)
    recorded_url = task.get('web', {}).get('page_url')
    if recorded_url and recorded_url != 'https://chatgpt.com/' and page.url != recorded_url:
        raise TaskError('Conversation changed during observation; stop')
    if task.get('web', {}).get('baseline_history'):
        from conversation_batch import batch_result
        return batch_result(page, task)
    users = page.locator(USER)
    assistants = page.locator(ASSISTANT)
    baseline = task["web"]["baseline_assistant_count"]
    # Current ChatGPT UI uses semantic headings and a completed generated-image
    # gallery instead of the legacy data-message-author-role containers.
    if users.count() == 0 and assistants.count() == 0:
        main = page.locator('main')
        galleries = main.get_by_test_id('generated-image-gallery')
        if galleries.count() > 1:
            raise TaskError("返回多个图像画廊，等待人工选择")
        if galleries.count() == 0:
            completed = main.locator('[data-talvt-turn-state="complete"]')
            if completed.count() == 1 and REFUSAL.search(completed.nth(0).inner_text()):
                raise TaskError('platform_refusal: completed text response, no image; do not rewrite/resubmit')
            return None
        gallery = galleries.nth(0)
        turn = gallery.locator('xpath=ancestor::*[@data-talvt-turn-state][1]')
        if turn.count() != 1 or turn.get_attribute('data-talvt-turn-state') != 'complete':
            return None
        user_headings = main.get_by_role('heading', name=re.compile(r'^(你说：|You said:)$'), include_hidden=True)
        assistant_headings = main.get_by_role('heading', name=re.compile(r'^(ChatGPT 说：|ChatGPT said:)$'), include_hidden=True)
        if user_headings.count() > 1 or assistant_headings.count() > 1:
            raise TaskError("对话包含额外消息，无法确定输出归属")
        if user_headings.count() != 1 or assistant_headings.count() != 1:
            return None
        expected = re.sub(r'\s+', ' ', task['prompt_text']).strip()
        actual = re.sub(r'\s+', ' ', main.inner_text()).strip()
        if expected not in actual:
            raise TaskError("用户消息与任务 Prompt 不一致，无法确定输出归属")
        previews = gallery.get_by_test_id('generated-image-preview')
        if previews.count() > 1:
            raise TaskError("返回多张图片，只授权一张，等待人工选择")
        if previews.count() != 1:
            return None
        images = previews.nth(0).locator('img')
        if images.count() != 1:
            raise TaskError("已生成图片的预览不唯一")
        image = images.nth(0)
        if not image.evaluate('el => el.complete && el.naturalWidth >= 256 && el.naturalHeight >= 256'):
            return None
        return turn, image
    if users.count() != 1:
        if users.count() > 1:
            raise TaskError("对话包含额外请求；无法确定输出归属，停止")
        return None
    expected = re.sub(r"\s+", " ", task["prompt_text"]).strip()
    actual = re.sub(r"\s+", " ", users.nth(0).inner_text()).strip()
    if expected not in actual:
        raise TaskError("用户消息与任务 Prompt 不一致，无法确定输出归属")
    # The submitted prompt is the only user message in this task-specific chat.
    if assistants.count() <= baseline or unique_visible(page.locator(STOP), "生成中", False):
        return None
    if assistants.count() != baseline + 1:
        raise TaskError("存在多个新回复，无法自动归属图片")
    result = assistants.nth(baseline)
    images = result.locator("img, canvas")
    generated = []
    for index in range(images.count()):
        item = images.nth(index)
        if item.is_visible() and item.evaluate("el => el.tagName === 'CANVAS' ? el.width >= 256 && el.height >= 256 : el.complete && el.naturalWidth >= 256 && el.naturalHeight >= 256"):
            generated.append(item)
    if len(generated) > 1:
        raise TaskError("返回多张图片，只授权一张，停止并等待人工选择")
    return (result, generated[0]) if generated else None


def normal_download(page, result, image, directory, *, progress=None, preview_timeout_ms=PREVIEW_TIMEOUT_MS,
                    allow_active_preview=True):
    active_dialog = unique_visible(page.get_by_role('dialog'), '图片预览', False)
    if active_dialog is not None and not allow_active_preview:
        raise TaskError('Open viewer may belong to an earlier image; close it before collecting this batch task')
    if active_dialog is not None:
        button = wait_ready(page, active_dialog.get_by_role('button', name=DOWNLOAD_NAME), '预览下载按钮', preview_timeout_ms)
    else:
        button = None
    if button is None:
        button = unique_visible(result.get_by_role("button", name=DOWNLOAD_NAME), "下载按钮", False)
    preview = image.locator('xpath=ancestor::button[@data-testid="generated-image-preview"][1]')
    if button is None and preview.count() == 0:
        image.hover()
        button = unique_visible(result.get_by_role("button", name=DOWNLOAD_NAME), "下载按钮", False)
    if button is None:
        # Open the actual generated-image preview, not an arbitrary asset URL.
        if progress: progress('opening_preview')
        if preview.count():
            unique_visible(preview, '已生成图片预览').click()
        else:
            image.click()
        dialog = wait_ready(page, page.get_by_role('dialog'), '图片预览', preview_timeout_ms)
        button = wait_ready(page, dialog.get_by_role('button', name=DOWNLOAD_NAME), '预览下载按钮', preview_timeout_ms)
    guard(page)
    if not button.is_enabled():
        button = wait_ready(page, button, '下载按钮', preview_timeout_ms)
    if progress: progress('downloading')
    with page.expect_download(timeout=30_000) as event:
        button.click()
    download = event.value
    failure = download.failure()
    if failure:
        raise TaskError(f"页面下载失败: {failure}")
    filename = Path(download.suggested_filename).name
    if Path(filename).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise TaskError("下载文件扩展名不支持，停止")
    path = Path(directory) / filename
    download.save_as(path)
    inspect_image(read_limited(path), path.suffix, output=True)
    return path


def collect(ledger, task_id, page, endpoint, timeout=180, progress=None):
    if not 1 <= timeout <= 600:
        raise TaskError("观察时间必须为 1–600 秒")
    task = ledger.task(ledger.load(), task_id)
    if task["status"] == "completed":
        return ledger.check(task_id)
    if not (task["status"] == "running" or (task["status"] == "failed" and task["needs_confirmation"])):
        raise TaskError("只有已提交的运行或待确认任务可以收集")
    web = task.get("web", {})
    if not web.get("submission_intent") or web.get("endpoint") != endpoint:
        raise TaskError("没有同一路径的提交记录；不会猜测页面或重新生成")
    checked_page(page.url)
    if web.get("page_url") == "https://chatgpt.com/":
        raise TaskError("提交后未记录唯一对话 URL；必须人工核对并下载，不能猜测其它对话")
    if page.url != web.get("page_url"):
        raise TaskError("对话页面与任务记录不一致")
    if page.url == "https://chatgpt.com/":
        raise TaskError("尚未取得唯一对话 URL，请观察原页面后恢复 collect，不重新提交")
    record_web(ledger, task_id, page_url=page.url)
    deadline = time.monotonic() + timeout
    next_progress = time.monotonic() + 15
    while time.monotonic() < deadline:
        current = ledger.task(ledger.load(), task_id)
        if task["status"] == "running" and current["status"] != "running":
            raise TaskError("本地任务已被人工停止，结束观察和下载")
        if task["status"] == "failed" and not current["needs_confirmation"]:
            raise TaskError("待确认任务已被人工关闭，结束观察和下载")
        ready = new_result(page, task)
        if progress and time.monotonic() >= next_progress:
            start_at = web.get('send_click_started_at', task.get('submitted_at'))
            elapsed = (datetime.fromisoformat(now()) - datetime.fromisoformat(start_at)).total_seconds()
            progress('waiting_image', elapsed_seconds=round(elapsed, 1))
            next_progress = time.monotonic() + 15
        if ready:
            observed_at = web.get('generation_complete_observed_at') or now()
            observed_clock = web.get('generation_complete_monotonic')
            if observed_clock is None and not web.get('generation_complete_observed_at'):
                observed_clock = time.monotonic()
            # Require the completion signals twice; never infer completion from
            # elapsed time, an uploaded reference, or a placeholder alone.
            page.wait_for_timeout(1000)
            ready = new_result(page, task)
            if not ready:
                continue
            if not web.get('generation_complete_observed_at'):
                record_web(ledger, task_id, generation_complete_observed_at=observed_at,
                           generation_complete_monotonic=observed_clock)
            if progress: progress('image_ready')
            with tempfile.TemporaryDirectory(prefix="framebridge-download-") as directory:
                download_at, download_clock = now(), time.monotonic()
                record_web(ledger, task_id, download_started_at=download_at)
                downloaded = normal_download(page, *ready, directory, progress=progress,
                                             allow_active_preview=not bool(web.get('batch_id')))
                record_web(ledger, task_id, output_matched="unique_new_assistant_image_normal_download")
                ledger.import_image(task_id, downloaded, confirmed=True, convert_png=True)
                finished_at, finished_clock = now(), time.monotonic()
                start_at = web.get('send_click_started_at', task.get('submitted_at'))
                if (web.get('timing_process_id') == os.getpid() and 'send_click_monotonic' in web
                        and observed_clock is not None):
                    elapsed_generation = observed_clock - web['send_click_monotonic']
                    elapsed_total = finished_clock - web['send_click_monotonic']
                    basis = 'monotonic'
                else:
                    elapsed_generation = (datetime.fromisoformat(observed_at) - datetime.fromisoformat(start_at)).total_seconds()
                    elapsed_total = (datetime.fromisoformat(finished_at) - datetime.fromisoformat(start_at)).total_seconds()
                    basis = 'utc_wall_clock_recovery'
                record_web(ledger, task_id, timing={
                    'send_click_started_at': start_at, 'generation_complete_observed_at': observed_at,
                    'download_started_at': download_at, 'saved_verified_at': finished_at,
                    'generation_seconds': round(elapsed_generation, 3),
                    'download_and_verify_seconds': round(finished_clock - download_clock, 3),
                    'total_to_saved_seconds': round(elapsed_total, 3), 'clock_basis': basis,
                    'observation_poll_seconds': POLL_SECONDS,
                })
                result = ledger.task(ledger.load(), task_id)
                from timing_report import write_report
                write_report(ledger, result)
                if progress: progress('saved', total_seconds=round(elapsed_total, 1))
                return result
        page.wait_for_timeout(POLL_SECONDS * 1000)
    raise TaskError("观察超时；结果待确认，仅恢复 collect，禁止重新提交")


def finish_submission(ledger, task_id, page, endpoint, timeout, progress):
    if progress: progress('submitted')
    page.wait_for_url(re.compile(r"https://chatgpt\.com/c/[A-Za-z0-9-]+$"), timeout=30_000)
    known_url = ledger.task(ledger.load(), task_id).get('web', {}).get('page_url')
    if known_url and known_url != 'https://chatgpt.com/' and page.url != known_url:
        raise TaskError('Conversation changed after Send; preserve original recovery URL')
    record_web(ledger, task_id, page_url=page.url)
    return collect(ledger, task_id, page, endpoint, timeout, progress=progress)


def remember_failed_submission(ledger, task_id, page):
    task = ledger.task(ledger.load(), task_id)
    if task.get('web', {}).get('submission_intent'):
        try:
            current_url = checked_page(page.url)
            known_url = task.get('web', {}).get('page_url')
            if current_url != 'https://chatgpt.com/' and known_url in {None, 'https://chatgpt.com/'}:
                record_web(ledger, task_id, page_url=current_url)
        except (AttributeError, TaskError):
            pass
    fail_uncertain(ledger, task_id)


def run(ledger, task_id, page, endpoint, timeout=180, progress=None, previous_task_id=None):
    try:
        prepare_submission(ledger, task_id, page, endpoint, previous_task_id)
        return finish_submission(ledger, task_id, page, endpoint, timeout, progress)
    except BaseException:
        remember_failed_submission(ledger, task_id, page)
        raise


def resume_draft(ledger, task_id, page, endpoint, timeout=180, progress=None):
    """Only the exact failed, never-submitted edit draft, with retained references."""
    guard(page)
    task = ledger.task(ledger.load(), task_id)
    web = task.get('web', {})
    if (task['status'] != 'failed' or not task['needs_confirmation'] or task.get('operation') != 'edit'
            or task['mode'] != 'web-ui' or not task.get('references')
            or web.get('submission_intent') or task.get('submitted_at')
            or any(e['event'] == 'submission_recorded' for e in task['events'])
            or web.get('endpoint') != endpoint or web.get('page_url') != 'https://chatgpt.com/'
            or page.url != 'https://chatgpt.com/'):
        raise TaskError('Not a proven unsubmitted edit draft; use collect for a submitted request')
    ledger.verify_inputs(task)
    composer = unique_visible(page.locator(COMPOSER), 'Composer')
    if not composer_matches(composer_text(composer), task['prompt_text']):
        raise TaskError('Unsubmitted draft does not match the original prompt')
    if (page.locator(USER).count() or page.locator(ASSISTANT).count()
            or page.locator('main [data-talvt-turn-state]').count()
            or unique_visible(page.locator(STOP), 'Generating', False)
            or unique_visible(page.get_by_role('dialog'), 'Preview', False)):
        raise TaskError('Page already has messages/generation/preview; no draft submission')
    upload = web.get('reference_upload', {})
    expected = [(Path(r['snapshot_path']).name, r['width'], r['height']) for r in task['references']]
    if upload.get('snapshot_sha256') != [r['sha256'] for r in task['references']]:
        raise TaskError('Missing approved upload record')
    form = composer.locator('xpath=ancestor::form[1]')
    if form.count() != 1:
        raise TaskError('Cannot verify retained reference previews')
    images = form.locator('img')
    visible = [images.nth(i) for i in range(images.count()) if images.nth(i).is_visible()]
    actual = [tuple(image.evaluate('el=>[el.alt,el.naturalWidth,el.naturalHeight]')) for image in visible]
    if actual != expected or any(not image.evaluate('el=>el.complete') for image in visible):
        raise TaskError('Retained references do not match the approved draft')
    with ledger.lock():
        state = ledger.load()
        current = ledger.task(state, task_id)
        if current != task or any(t['id'] != task_id and (t['status'] == 'running' or t['needs_confirmation']) for t in state['tasks']):
            raise TaskError('Task state changed or another task needs review; stop')
        if ledger.bounded(task['output_path'], 'outputs').exists():
            raise TaskError('Existing output protected')
        current.update(status='running', phase='awaiting_submission', needs_confirmation=False)
        ledger.event(current, 'unsubmitted_draft_resumed_without_reupload')
        ledger.save(state)
    try:
        send_prepared(ledger, task_id, page)
        return finish_submission(ledger, task_id, page, endpoint, timeout, progress)
    except BaseException:
        remember_failed_submission(ledger, task_id, page)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--cdp", required=True, help="用户配置的 Edge/Chrome 本机 CDP 地址，不扫描")
    parser.add_argument("--page", help="已打开并登录的唯一 ChatGPT 标签页 URL；generate 自动准备空白页")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("probe")
    for name in ("run", "collect", "generate", "edit", "resume-draft"):
        command = commands.add_parser(name)
        command.add_argument("id")
        command.add_argument("--confirmed", action="store_true", help="用户明确授权这一个任务及正常按钮下载")
        command.add_argument("--timeout", type=int, default=180)
    batch = commands.add_parser('batch', help='Explicit finite task list: one conversation, serial Send/Download')
    batch.add_argument('ids', nargs='+')
    batch.add_argument('--confirmed', action='store_true', help='Current user approved all listed prompts, image count and downloads')
    batch.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args(argv)
    ledger = Ledger(args.root)
    try:
        if args.command != "probe" and not args.confirmed:
            raise TaskError("缺少明确任务确认；不会提交、上传或下载")
        if args.command != "probe" and not 1 <= args.timeout <= 600:
            raise TaskError("观察时间必须为 1–600 秒")
        if args.command == 'batch':
            if args.page is not None:
                raise TaskError('batch starts a fresh conversation; it does not adopt an unrelated --page')
            from conversation_batch import run_batch
            result = run_batch(ledger, args.ids, checked_endpoint(args.cdp), args.timeout,
                               confirmed=args.confirmed,
                               progress=lambda task_id, phase, **metrics: print(json.dumps(
                                   {'task': task_id, 'phase': phase, **metrics}, ensure_ascii=False),
                                   file=sys.stderr, flush=True))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command in {'generate', 'edit'}:
            if args.page is not None:
                raise TaskError('generate/edit 自动准备空白页，不接受 --page；指定页面请使用 run')
            task = ledger.task(ledger.load(), args.id)
            if task['status'] != 'pending' or task['mode'] != 'web-ui':
                raise TaskError('generate 仅接受已明确授权的 pending 网页任务，不能重新发送已有任务')
            if args.command == 'edit' and (task.get('operation') != 'edit' or not task.get('references')):
                raise TaskError('edit requires an explicitly prepared edit task with reference images')
            if args.command == 'generate' and task.get('operation') == 'edit':
                raise TaskError('Use edit for a prepared edit task; do not silently change its intent')
            ledger.verify_inputs(task)
            if ledger.bounded(task['output_path'], 'outputs').exists():
                raise TaskError('目标已存在，不会生成或覆盖')
            if any(t['status'] == 'running' or t['needs_confirmation'] for t in ledger.load()['tasks']):
                raise TaskError('先处理运行或待确认任务，不能准备下一任务')
            connection = connected_image_page(args.cdp)
        else:
            if not args.page:
                raise TaskError('probe/run/collect 必须明确指定 --page')
            connection = connected_page(args.cdp, args.page)
        def progress(phase, **metrics):
            print(json.dumps({'task': getattr(args, 'id', None), 'phase': phase, **metrics}, ensure_ascii=False), file=sys.stderr, flush=True)
        with connection as page:
            endpoint = checked_endpoint(args.cdp)
            if args.command == "probe": result = probe(page)
            elif args.command in {"run", "generate", "edit"}: result = run(ledger, args.id, page, endpoint, args.timeout, progress=progress)
            elif args.command == 'resume-draft': result = resume_draft(ledger, args.id, page, endpoint, args.timeout, progress=progress)
            else:
                try:
                    result = collect(ledger, args.id, page, endpoint, args.timeout, progress=progress)
                except BaseException:
                    fail_uncertain(ledger, args.id)
                    raise
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except KeyboardInterrupt:
        print("已中断；原网页请求可能仍在生成。仅恢复 collect 或人工停止网页，不重发。")
        return 130
    except Exception as error:
        print(json.dumps({"error": str(error), "automatic_retry": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
