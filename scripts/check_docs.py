"""Offline Markdown links/fences and public Skill frontmatter checks."""
import json
from pathlib import Path
import re
import subprocess
import unicodedata


def heading_ids(text):
    ids, counts = set(), {}
    in_code = False
    for line in text.splitlines():
        if line.startswith('```'):
            in_code = not in_code
        elif not in_code and re.match(r'^#{1,6} ', line):
            title = re.sub(r'^#{1,6} ', '', line).strip().lower()
            title = re.sub(r'[`*_]', '', title)
            title = ''.join(c for c in title if c in '-_ ' or unicodedata.category(c)[0] not in {'P', 'S'})
            slug = title.replace(' ', '-')
            count = counts.get(slug, 0)
            counts[slug] = count + 1
            ids.add(slug if count == 0 else f'{slug}-{count}')
    return ids


def check(root):
    root = Path(root).resolve()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    new = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=root).decode().split('\0')
    paths = sorted({p for p in tracked + new if p.endswith('.md') and (root / p).exists()})
    errors = []
    for name in paths:
        text = (root / name).read_text(encoding='utf-8')
        if sum(line.startswith('```') for line in text.splitlines()) % 2:
            errors.append({'file': name, 'issue': 'unclosed code fence'})
        without_code = re.sub(r'```.*?```', '', text, flags=re.S)
        for target in re.findall(r'\]\(([^\s)]+)\)', without_code):
            if target.startswith(('https://', 'http://', 'mailto:', 'app:', 'codex:')):
                continue
            target = target.strip('<>')
            file_part, _, anchor = target.partition('#')
            destination = ((root / name).parent / file_part).resolve() if file_part else root / name
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append({'file': name, 'issue': 'missing/outside local link', 'target': target})
            elif anchor and destination.suffix == '.md' and anchor not in heading_ids(destination.read_text(encoding='utf-8')):
                errors.append({'file': name, 'issue': 'missing heading anchor', 'target': target})
    skill = (root / 'SKILL.md').read_text(encoding='utf-8')
    if not re.match(r'\A---\nname: framebridge-web-imagegen\ndescription: .+\n---\n', skill):
        errors.append({'file': 'SKILL.md', 'issue': 'invalid required frontmatter'})
    return {'markdown_files': len(paths), 'errors': errors, 'external_links_fetched': False}


if __name__ == '__main__':
    report = check(Path(__file__).resolve().parents[1])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(bool(report['errors']))
