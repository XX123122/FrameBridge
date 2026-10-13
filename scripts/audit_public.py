"""Heuristic scan of public source/Git blobs. Never prints matched secret values."""
import argparse
import json
from pathlib import Path
import re
import subprocess

PATTERNS = {
    'credential-shaped-value': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,}|sk-(?:proj-)?[A-Za-z0-9_-]{30,})'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'private-chat-url': re.compile(r'https://chatgpt\.com/c/[0-9a-f]{8}-[0-9a-f-]{20,}', re.I),
}
SENSITIVE_NAMES = {'Cookies', 'Cookies-journal', 'Login Data', 'Local State', 'auth.json', '.env'}


def sensitive_path(name):
    parts = Path(name).parts
    return (Path(name).name in SENSITIVE_NAMES or Path(name).name.startswith('.env.')
            or any(p in {'User Data', 'browser-profiles', 'edge-session'} for p in parts)
            or name.startswith(('logs/', 'outputs/', 'references/')) and not name.endswith('/.gitkeep'))


def scan_text(text, source):
    return [{'source': source, 'line': text.count('\n', 0, match.start()) + 1, 'rule': rule}
            for rule, pattern in PATTERNS.items() for match in pattern.finditer(text)]


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def audit(root, history=False):
    root = Path(root).resolve()
    tracked = git(root, 'ls-files', '-z').decode().split('\0')
    new = git(root, 'ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')
    findings = []
    files = [p for p in sorted(set(tracked + new)) if p and (root / p).is_file()]
    for name in files:
        if sensitive_path(name):
            findings.append({'source': name, 'rule': 'runtime-or-auth-file'})
        data = (root / name).read_bytes()
        if b'\0' not in data:
            findings.extend(scan_text(data.decode('utf-8', errors='replace'), name))
    blobs = 0
    if history:
        # Unique reachable blobs across all local refs, not credentials or browser data.
        for entry in git(root, 'rev-list', '--objects', '--all').decode().splitlines():
            oid, _, name = entry.partition(' ')
            if not name or git(root, 'cat-file', '-t', oid).strip() != b'blob':
                continue
            blobs += 1
            if sensitive_path(name):
                findings.append({'source': f'{oid[:12]}:{name}', 'rule': 'runtime-or-auth-file-in-history'})
            data = git(root, 'cat-file', 'blob', oid)
            if b'\0' not in data:
                findings.extend(scan_text(data.decode('utf-8', errors='replace'), f'{oid[:12]}:{name}'))
    return {'public_files': len(files), 'history_blobs': blobs, 'findings': findings,
            'scope': 'working public files and optional reachable Git blobs; heuristic, not a security certification'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    report = audit(Path(__file__).resolve().parents[1], args.history)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(bool(report['findings']))
