"""Install/update the local Skill entry. Does not configure or authorize a browser."""
import argparse
import json
import os
from pathlib import Path
import re

NAME = 'framebridge-web-imagegen'
OWNER = 'FrameBridge skill installer'


def install(project, destination, *, update=False, adopt_existing=False):
    project = Path(project).resolve()
    for required in ('SKILL.md', 'scripts/framebridge.py', 'scripts/web_chatgpt.py'):
        if not (project / required).is_file():
            raise FileNotFoundError(f'Project is incomplete: {required}')
    content = (project / 'SKILL.md').read_text(encoding='utf-8').replace('PROJECT_ROOT_VALUE', str(project))
    if not re.search(r'^name: framebridge-web-imagegen\s*$', content, re.M):
        raise ValueError('Unexpected Skill name')
    target = Path(destination).resolve() / NAME / 'SKILL.md'
    if target.parent.is_symlink() or target.is_symlink():
        raise ValueError('Refusing to install through a Skill symlink')
    manifest = target.parent / 'framebridge-install.json'
    if manifest.is_symlink() or target.with_name('SKILL.md.previous').is_symlink():
        raise ValueError('Refusing to write through a Skill metadata/backup symlink')
    owned = False
    if manifest.exists():
        metadata = json.loads(manifest.read_text(encoding='utf-8'))
        owned = metadata.get('managed_by') == OWNER and metadata.get('skill') == NAME
        if not owned:
            raise FileExistsError('Install metadata belongs to another tool; not overwriting')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = target.read_text(encoding='utf-8')
        if existing != content:
            if not update:
                raise FileExistsError(f'Existing version preserved: {target}. Use --update explicitly.')
            if not owned and not adopt_existing:
                raise FileExistsError('Legacy/unmanaged entry: review it, then use --update --adopt-existing.')
            if not re.search(r'^name: framebridge-web-imagegen\s*$', existing, re.M):
                raise FileExistsError('Existing entry has a different Skill name; not overwriting')
            target.with_name('SKILL.md.previous').write_text(existing, encoding='utf-8', newline='\n')
            target.write_text(content, encoding='utf-8', newline='\n')
    else:
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    manifest.write_text(json.dumps({'schema': 1, 'managed_by': OWNER, 'skill': NAME,
                                   'project': str(project)}, indent=2) + '\n', encoding='utf-8')
    return target.resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=str(Path(__file__).resolve().parents[1]))
    codex_directory = Path(os.environ["CODEX_HOME"]) if os.environ.get("CODEX_HOME") else Path.home() / ".codex"
    parser.add_argument("--destination", default=str(codex_directory / "skills"))
    parser.add_argument('--update', action='store_true', help='Explicitly update this managed Skill, including its project path')
    parser.add_argument('--adopt-existing', action='store_true', help='With --update, replace a reviewed legacy entry with this same name')
    args = parser.parse_args()
    if args.adopt_existing and not args.update:
        parser.error('--adopt-existing requires --update')
    print(install(args.project, args.destination, update=args.update, adopt_existing=args.adopt_existing))
