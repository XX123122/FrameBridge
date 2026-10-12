"""Re-download a completed task's existing image to a temporary file. No generation."""
import argparse
import json
import tempfile
import time

from framebridge import Ledger, TaskError, atomic_json, digest, read_limited, now
from web_chatgpt import connected_page, guard, new_result, unique_visible, normal_download


def benchmark(ledger, task_id, endpoint):
    original = ledger.check(task_id)
    if not original.get('valid_output'):
        raise TaskError('仅对已完成且校验有效的任务进行下载复测')
    task = ledger.task(ledger.load(), task_id)
    page_url = task.get('web', {}).get('page_url')
    if not page_url or task['web'].get('endpoint') != endpoint:
        raise TaskError('需要该任务原来的浏览器端口和对话，不能猜测其它会话')
    with connected_page(endpoint, page_url) as page:
        guard(page)
        if new_result(page, task) is None:
            raise TaskError('原对话结果尚不能唯一匹配，停止')
        dialog = unique_visible(page.get_by_role('dialog'), '图片预览', False)
        if dialog is not None:
            unique_visible(dialog.get_by_role('button', name='关闭查看器', exact=True), '关闭查看器').click()
            dialog.wait_for(state='hidden', timeout=8_000)
        ready = new_result(page, task)
        if ready is None:
            raise TaskError('关闭预览后无法匹配原结果，停止')
        started_at, started_clock = now(), time.monotonic()
        with tempfile.TemporaryDirectory(prefix='framebridge-download-check-') as directory:
            downloaded = normal_download(page, *ready, directory)
            checksum = digest(read_limited(downloaded))
            if checksum != original['sha256']:
                raise TaskError('重新下载结果与已保存原图不符，停止而不覆盖')
            elapsed = time.monotonic() - started_clock
        report = {'task': task_id, 'started_at': started_at, 'verified_at': now(),
                  'preview_download_verify_seconds': round(elapsed, 3),
                  'generation_requests_sent': 0, 'original_file_unchanged': True,
                  'sha256': checksum, 'scope': 'completed_image_preview_download_hash_check'}
    atomic_json(ledger.bounded(f'logs/{task_id}/optimization-download-check.json', 'logs'), report)
    return report


if __name__ == '__main__':
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--cdp', required=True)
    parser.add_argument('id')
    args = parser.parse_args()
    print(json.dumps(benchmark(Ledger(args.root), args.id, args.cdp), ensure_ascii=False, indent=2))
