"""Write local timing summaries from an already completed task; no browser access."""
from datetime import datetime, timedelta, timezone
import json
import os
import uuid

from framebridge import atomic_json, TaskError


def write_report(ledger, task):
    if task['status'] != 'completed' or not task.get('web', {}).get('timing'):
        raise TaskError('仅已完成且有计时数据的任务可写耗时报告')
    timing = task['web']['timing']
    artifact = task['artifact']
    report = {'task': task['id'], 'output_path': task['output_path'],
              'submission_count': sum(e['event'] == 'submission_recorded' for e in task['events']),
              'timing': timing, 'artifact': {k: artifact[k] for k in ('format', 'width', 'height', 'bytes', 'sha256')}}
    directory = ledger.bounded(f"logs/{task['id']}", 'logs')
    atomic_json(directory / 'timing.json', report)
    china_time = timezone(timedelta(hours=8))
    def local(stamp):
        return datetime.fromisoformat(stamp).astimezone(china_time).isoformat(timespec='milliseconds')
    content = '\n'.join([
        f"# {task['id']} 耗时记录", '', '时间为北京时间（UTC+8）。', '',
        '| 项目 | 记录 |', '| --- | --- |',
        f"| 点击发送开始 | {local(timing['send_click_started_at'])} |",
        f"| 首次观察到生成完成 | {local(timing['generation_complete_observed_at'])} |",
        f"| 保存并验证完成 | {local(timing['saved_verified_at'])} |",
        f"| 发送至页面生成完成 | {timing['generation_seconds']:.3f} 秒 |",
        f"| 成功下载与验证步骤 | {timing['download_and_verify_seconds']:.3f} 秒 |",
        f"| 发送至保存总耗时 | {timing['total_to_saved_seconds']:.3f} 秒 |", '',
        f"观察间隔 {timing['observation_poll_seconds']} 秒，表示页面完成观测时间，不是服务端纯计算时间。",
        '总耗时包含稳定复核、预览、下载与校验；发生恢复时也包含恢复等待，不覆盖首次生成完成时间。', '',
        f"输出：{task['output_path']}（{artifact['format']}，{artifact['width']}×{artifact['height']}）。",
        f"SHA-256：`{artifact['sha256']}`。", f"提交记录：{report['submission_count']} 次。", '',
    ])
    path = directory / 'timing.md'
    temporary = directory / f'.timing.{uuid.uuid4().hex}.tmp'
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return report
