"""Local task ledger. Browser operations live in the optional web adapter."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import platform
import re
import sys
import uuid
import warnings

from PIL import Image, UnidentifiedImageError

FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}
MAX_BYTES = 64 * 1024 * 1024
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class TaskError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_limited(path, limit=MAX_BYTES):
    if not path.is_file():
        raise TaskError(f"不是普通文件: {path}")
    with path.open("rb") as handle:
        data = handle.read(limit + 1)
    if not data or len(data) > limit:
        raise TaskError(f"文件为空或超过 {limit} 字节: {path}")
    return data


def inspect_image(data, suffix, *, output=False):
    expected = FORMATS.get(suffix.lower())
    if not expected:
        raise TaskError("仅支持 PNG / JPG / JPEG / WebP")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                actual, size = image.format, image.size
                frames = getattr(image, "n_frames", 1)
                if actual != expected:
                    raise TaskError(f"扩展名与真实格式不一致: {suffix} / {actual}")
                low = 256 if output else 1
                if min(size) < low or max(size) > 8192 or size[0] * size[1] > 32_000_000:
                    raise TaskError(f"尺寸不合理: {size}; 最短边至少 {low}，最长边最多 8192，最多 3200 万像素")
                if frames != 1:
                    raise TaskError("只接受静态单帧图片")
                image.verify()
            with Image.open(BytesIO(data)) as image:
                image.load()  # Decode pixels too; checking the header alone misses truncation.
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise TaskError(f"图片无效或损坏: {error}") from error
    return {"format": actual, "width": size[0], "height": size[1], "bytes": len(data), "sha256": digest(data)}


def atomic_json(path, data):
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_exclusive(path, data):
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


class Ledger:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.path = self.root / "tasks.json"

    def bounded(self, value, folder):
        path = Path(value)
        path = (path if path.is_absolute() else self.root / path).resolve()
        boundary = (self.root / folder).resolve()
        # A directory symlink/junction must not silently move the boundary outside the project.
        if not boundary.is_relative_to(self.root) or not path.is_relative_to(boundary) or path == boundary:
            raise TaskError(f"路径必须在项目 {folder}/ 内: {value}")
        for part in path.relative_to(self.root).parts:
            if part.split('.')[0].upper() in RESERVED or part.endswith((' ', '.')) or ':' in part:
                raise TaskError(f"Windows 不安全文件名: {part}")
        return path

    @contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".framebridge.lock").open("a+b") as handle:
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise TaskError("另一个进程正在修改任务，请稍后重试") from error
            try:
                yield
            finally:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def load(self):
        if not self.path.exists():
            raise TaskError("请先运行 init")
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise TaskError("tasks.json 无法读取；不会重置，请恢复备份") from error
        if state.get("version") != 1 or not isinstance(state.get("tasks"), list):
            raise TaskError("不支持的任务文件格式")
        ids, outputs = set(), set()
        for task in state["tasks"]:
            if not isinstance(task, dict) or not ID_PATTERN.fullmatch(task.get("id", "")):
                raise TaskError("任务数据或 ID 损坏")
            if task.get("status") not in {"pending", "running", "completed", "failed"}:
                raise TaskError("任务状态损坏")
            if task.get('operation', 'generate') not in {'generate', 'edit'}:
                raise TaskError('任务 operation 损坏')
            task_id = task["id"]
            expected_log = f"logs/{task_id}/task.json"
            if task.get("log_path") != expected_log:
                raise TaskError("任务日志路径损坏，停止写入")
            self.bounded(expected_log, "logs")
            self.bounded(task.get("prompt_snapshot", ""), "logs")
            output = str(self.bounded(task.get("output_path", ""), "outputs")).lower()
            if task_id.lower() in ids or output in outputs:
                raise TaskError("任务 ID 或输出路径冲突")
            ids.add(task_id.lower())
            outputs.add(output)
        return state

    def save(self, state):
        atomic_json(self.path, state)
        # tasks.json is authoritative; these per-task logs are derived mirrors.
        for task in state["tasks"]:
            atomic_json(self.bounded(f"logs/{task['id']}/task.json", "logs"), task)

    def init(self):
        with self.lock():
            for folder in ("prompts", "references", "outputs", "logs"):
                path = self.root / folder
                if not path.resolve().is_relative_to(self.root):
                    raise TaskError(f"{folder} 不能指向项目外")
                path.mkdir(exist_ok=True)
            if not self.path.exists():
                atomic_json(self.path, {"version": 1, "tasks": []})
            return self.load()

    @staticmethod
    def task(state, task_id):
        for task in state["tasks"]:
            if task["id"] == task_id:
                return task
        raise TaskError(f"任务不存在: {task_id}")

    @staticmethod
    def event(task, name):
        task["updated_at"] = now()
        task["events"].append({"at": task["updated_at"], "event": name,
                               "status": task["status"], "phase": task["phase"]})

    def add(self, task_id, prompt, references, output, mode="web-ui", operation='generate'):
        if not ID_PATTERN.fullmatch(task_id) or task_id.upper() in RESERVED:
            raise TaskError("任务 ID 必须为 1–64 位 ASCII 字母、数字、下划线或连字符，不能是 Windows 保留名")
        if mode not in {"web-ui", "manual-web", "codex-imagegen"}:
            raise TaskError("不支持的生成路径")
        if operation not in {'generate', 'edit'} or operation == 'edit' and not references:
            raise TaskError('edit 操作至少需要一张明确的参考图')
        with self.lock():
            state = self.load()
            if any(t["id"].lower() == task_id.lower() for t in state["tasks"]):
                raise TaskError("任务 ID 已存在（Windows 不区分大小写）")
            pp = self.bounded(prompt, "prompts")
            if pp.suffix.lower() not in {".txt", ".md"}:
                raise TaskError("Prompt 只接受 txt / md")
            raw = read_limited(pp, 1024 * 1024)
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeError as error:
                raise TaskError("请将 Prompt 保存为 UTF-8（支持 BOM）") from error
            if not text.strip():
                raise TaskError("Prompt 不能为空白")
            op = self.bounded(output, "outputs")
            if op.suffix.lower() not in FORMATS or op.exists():
                raise TaskError("输出格式不支持或文件已存在；不会覆盖")
            if any(t["output_path"].lower() == str(op.relative_to(self.root)).lower() for t in state["tasks"]):
                raise TaskError("输出路径已被其他任务保留")
            refs = []
            for value in references:
                path = self.bounded(value, "references")
                data = read_limited(path, 32 * 1024 * 1024)
                meta = inspect_image(data, path.suffix)
                if any(r["sha256"] == meta["sha256"] for r, _ in refs):
                    raise TaskError("重复参考图；请明确提供一次")
                refs.append(({"original_path": str(path.relative_to(self.root)), "role": "reference", **meta}, data))
            directory = self.bounded(f"logs/{task_id}", "logs")
            directory.mkdir()  # Exclusive: never reuse orphaned snapshots silently.
            snapshot = directory / f"prompt{pp.suffix.lower()}"
            write_exclusive(snapshot, raw)
            for index, (meta, data) in enumerate(refs, 1):
                dest = directory / f"reference-{index:02d}{Path(meta['original_path']).suffix.lower()}"
                write_exclusive(dest, data)
                meta["snapshot_path"] = str(dest.relative_to(self.root))
            task = {"id": task_id, "status": "pending", "phase": "prepared", "mode": mode, 'operation': operation,
                    "needs_confirmation": False, "created_at": now(), "updated_at": now(),
                    "prompt_path": str(pp.relative_to(self.root)), "prompt_snapshot": str(snapshot.relative_to(self.root)),
                    "prompt_sha256": digest(raw), "prompt_text": text, "references": [r for r, _ in refs],
                    "output_path": str(op.relative_to(self.root)), "log_path": f"logs/{task_id}/task.json", "events": []}
            self.event(task, "prepared")
            state["tasks"].append(task)
            self.save(state)
            return task

    def verify_inputs(self, task):
        data = read_limited(self.bounded(task["prompt_snapshot"], "logs"), 1024 * 1024)
        if digest(data) != task["prompt_sha256"] or data.decode("utf-8-sig") != task["prompt_text"]:
            raise TaskError("Prompt 快照被更改，停止任务")
        for ref in task["references"]:
            data = read_limited(self.bounded(ref["snapshot_path"], "logs"), 32 * 1024 * 1024)
            if digest(data) != ref["sha256"]:
                raise TaskError("参考图快照被更改，停止任务")
            inspect_image(data, Path(ref["snapshot_path"]).suffix)

    def packet(self, task_id):
        task = self.task(self.load(), task_id)
        self.verify_inputs(task)
        return {"id": task["id"], "mode": task["mode"], "status": task["status"],
                'operation': task.get('operation', 'generate'),
                "prompt_text": task["prompt_text"], "prompt_snapshot": str(self.root / task["prompt_snapshot"]),
                "references": [{**r, "upload_path": str(self.root / r["snapshot_path"])} for r in task["references"]],
                "output_path": str(self.root / task["output_path"]),
                "instruction": "仅处理这个任务；网页自动化见 web_chatgpt.py。此命令本身不会生成或上传。"}

    def start(self, task_id, confirmed=False):
        if not confirmed:
            raise TaskError("需要用户确认单个任务后才能 start；start 本身只更新本地状态")
        with self.lock():
            state = self.load()
            task = self.task(state, task_id)
            if task["status"] != "pending":
                raise TaskError("仅 pending 可开始；不得重复提交或自动重试")
            if any(t["status"] == "running" or t["needs_confirmation"] for t in state["tasks"]):
                raise TaskError("已有运行或待确认任务，必须先处理；队列始终串行")
            self.verify_inputs(task)
            if self.bounded(task["output_path"], "outputs").exists():
                raise TaskError("目标文件已存在，不会覆盖")
            task.update(status="running", phase="awaiting_submission", started_at=now())
            self.event(task, "user_authorized")
            self.save(state)
            return task

    def submitted(self, task_id, confirmed=False):
        if not confirmed:
            raise TaskError("需要用户确认已提交，或内置工具调用已被明确授权")
        with self.lock():
            state = self.load()
            task = self.task(state, task_id)
            if task["status"] != "running" or task["phase"] != "awaiting_submission":
                raise TaskError("任务不在等待提交阶段；禁止重复记录提交")
            task.update(phase="awaiting_download", submitted_at=now())
            self.event(task, "submission_recorded")
            self.save(state)
            return task

    def stop(self, task_id, reason="interrupted"):
        if reason not in {"interrupted", "verification", "quota", "permission", "terms", "uncertain", "service_error"}:
            raise TaskError("不支持的停止原因")
        with self.lock():
            state = self.load()
            task = self.task(state, task_id)
            if task["status"] not in {"pending", "running"}:
                raise TaskError("任务已经结束")
            # Even awaiting_submission may have reached the website before a local crash.
            uncertain = task["status"] == "running"
            task.update(status="failed", phase=reason, needs_confirmation=uncertain)
            self.event(task, reason)
            self.save(state)
            return task

    def recover(self):
        with self.lock():
            state = self.load()
            changed = []
            for task in state["tasks"]:
                if task["status"] == "running":
                    task.update(status="failed", phase="uncertain", needs_confirmation=True)
                    self.event(task, "recovered_without_resubmit")
                    changed.append(task["id"])
            self.save(state)
            return {"needs_confirmation": changed, "instruction": "检查原网页与下载目录；不会重新提交。"}

    def resolve(self, task_id, confirmed=False):
        if not confirmed:
            raise TaskError("必须人工核对后确认不再收集此任务的输出")
        with self.lock():
            state = self.load()
            task = self.task(state, task_id)
            if task["status"] != "failed" or not task["needs_confirmation"]:
                raise TaskError("任务没有待确认状态")
            task.update(needs_confirmation=False, phase="closed_without_output")
            self.event(task, "user_closed")
            self.save(state)
            return task

    def import_image(self, task_id, source=None, confirmed=False, convert_png=False, existing=False):
        if not confirmed:
            raise TaskError("必须人工确认图片属于该任务且是新生成结果；尺寸无法证明归属")
        with self.lock():
            state = self.load()
            task = self.task(state, task_id)
            if not (task["status"] == "running" or (task["status"] == "failed" and task["needs_confirmation"])):
                raise TaskError("仅运行中或待确认任务可收集图片")
            self.verify_inputs(task)
            target = self.bounded(task["output_path"], "outputs")
            if existing:
                meta = inspect_image(read_limited(target), target.suffix, output=True)
                candidate = task.get("artifact_candidate")
                if not candidate or candidate["sha256"] != meta["sha256"]:
                    raise TaskError("已有输出与中断前记录不符；不能直接认领")
            else:
                if target.exists():
                    raise TaskError("目标文件已存在，不会覆盖；崩溃恢复可用 confirm-output")
                path = Path(source).resolve()
                # Never automatically search Downloads or choose the newest file.
                data = read_limited(path)
                meta = inspect_image(data, path.suffix, output=True)
                stamp = datetime.fromisoformat(task["started_at"]).timestamp()
                if path.stat().st_mtime < stamp - 2:
                    raise TaskError("文件早于任务开始，不能确定是本次输出")
                if any(r["sha256"] == meta["sha256"] for r in task["references"]):
                    raise TaskError("文件与参考图相同，不能作为生成结果")
                if any(t.get("artifact", {}).get("source_sha256", t.get("artifact", {}).get("sha256")) == meta["sha256"]
                       for t in state["tasks"] if t["id"] != task_id):
                    raise TaskError("该文件已用于其他任务")
                source_hash = meta["sha256"]
                if FORMATS[target.suffix.lower()] != meta["format"]:
                    if not convert_png or target.suffix.lower() != ".png":
                        raise TaskError("输出扩展名与下载格式不一致；PNG 目标可显式使用 --convert-png")
                    buffer = BytesIO()
                    with Image.open(BytesIO(data)) as image:
                        image.save(buffer, format="PNG")
                    data = buffer.getvalue()
                    if len(data) > MAX_BYTES:
                        raise TaskError("转换后文件过大")
                    meta = inspect_image(data, ".png", output=True)
                meta.update(source_sha256=source_hash, source_path=str(path))
                task.update(artifact_candidate=meta, phase="importing")
                self.event(task, "local_import_prepared")
                self.save(state)  # Recovery evidence committed before writing the output.
                target.parent.mkdir(parents=True, exist_ok=True)
                write_exclusive(target, data)
                written = inspect_image(read_limited(target), target.suffix, output=True)
                if written["sha256"] != meta["sha256"]:
                    raise TaskError("输出写入后校验不匹配；保持待确认，不覆盖")
            task.update(status="completed", phase="verified", needs_confirmation=False,
                        artifact=task["artifact_candidate"], completed_at=now())
            self.event(task, "output_verified_and_matched_by_user")
            self.save(state)
            return task

    def check(self, task_id):
        task = self.task(self.load(), task_id)
        self.verify_inputs(task)
        if task["status"] != "completed":
            return {"id": task_id, "status": task["status"], "phase": task["phase"],
                    "needs_confirmation": task["needs_confirmation"], "valid_output": False}
        path = self.bounded(task["output_path"], "outputs")
        meta = inspect_image(read_limited(path), path.suffix, output=True)
        if meta["sha256"] != task["artifact"]["sha256"]:
            raise TaskError("完成后的输出被更改或损坏")
        return {"id": task_id, "status": "completed", "valid_output": True, "output_path": str(path), **meta}


def doctor():
    import importlib.util
    local_app_data = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local')))
    candidates = [Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
                  Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
                  local_app_data / "Google/Chrome/Application/chrome.exe"]
    edge_candidates = [Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
                       Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Microsoft/Edge/Application/msedge.exe",
                       local_app_data / "Microsoft/Edge/Application/msedge.exe"]
    return {"platform": platform.platform(), "python": platform.python_version(), "python_executable": sys.executable,
            "pillow": Image.__version__, "playwright_installed": importlib.util.find_spec("playwright") is not None,
            "chrome_standard_paths": [str(p) for p in candidates if p.is_file()],
            "edge_standard_paths": [str(p) for p in edge_candidates if p.is_file()],
            "preferred_browser": "edge",
            "account_source": "selected_browser_chatgpt_session_not_codex_account",
            "browser_session": "not_inspected_by_python", "network_requests": 0,
            "default_mode": "web-ui", "web_automation": "optional_normal_ui_download_with_terms_risk",
            "instruction": "浏览器连接与登录必须用 Codex 可用 UI 工具检查；本程序不读取任何认证数据。"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="项目根目录")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "doctor", "list", "recover"):
        commands.add_parser(name)
    add = commands.add_parser("add")
    add.add_argument("id")
    add.add_argument("--prompt", required=True)
    add.add_argument("--reference", action="append", default=[])
    add.add_argument("--output", required=True)
    add.add_argument("--mode", choices=["web-ui", "manual-web", "codex-imagegen"], default="web-ui")
    add.add_argument('--operation', choices=['generate', 'edit'], default='generate', help='edit requires explicit reference images')
    for name in ("show", "packet", "check", "start", "submitted", "stop", "resolve", "import", "confirm-output"):
        command = commands.add_parser(name)
        command.add_argument("id")
        if name in {"start", "submitted", "resolve", "import", "confirm-output"}:
            command.add_argument("--confirmed", action="store_true", help="仅在用户明确确认后使用；不是服务端授权")
        if name == "stop":
            command.add_argument("--reason", choices=["interrupted", "verification", "quota", "permission", "terms", "uncertain", "service_error"], default="interrupted")
        if name == "import":
            command.add_argument("--file", required=True, help="人工下载或内置工具明确返回的本地文件")
            command.add_argument("--convert-png", action="store_true")
    args = parser.parse_args(argv)
    ledger = Ledger(args.root)
    try:
        if args.command == "doctor": result = doctor()
        elif args.command == "init": result = ledger.init()
        elif args.command == "add": result = ledger.add(args.id, args.prompt, args.reference, args.output, args.mode, args.operation)
        elif args.command == "list": result = [{k: t[k] for k in ("id", "status", "phase", "needs_confirmation", "output_path")} for t in ledger.load()["tasks"]]
        elif args.command == "show": result = ledger.task(ledger.load(), args.id)
        elif args.command == "packet": result = ledger.packet(args.id)
        elif args.command == "check": result = ledger.check(args.id)
        elif args.command == "start": result = ledger.start(args.id, args.confirmed)
        elif args.command == "submitted": result = ledger.submitted(args.id, args.confirmed)
        elif args.command == "stop": result = ledger.stop(args.id, args.reason)
        elif args.command == "recover": result = ledger.recover()
        elif args.command == "resolve": result = ledger.resolve(args.id, args.confirmed)
        elif args.command == "import": result = ledger.import_image(args.id, args.file, args.confirmed, args.convert_png)
        elif args.command == "confirm-output": result = ledger.import_image(args.id, confirmed=args.confirmed, existing=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (TaskError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error), "automatic_retry": False}, ensure_ascii=False), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("已中断。若任务可能已提交，请执行 recover 并人工核对，禁止直接重发。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
