import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from install_skill import install
from audit_public import scan_text, sensitive_path
from check_docs import heading_ids


class PublicSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / 'project with spaces'
        (self.project / 'scripts').mkdir(parents=True)
        (self.project / 'scripts/framebridge.py').write_text('# fixture\n')
        (self.project / 'scripts/web_chatgpt.py').write_text('# fixture\n')
        (self.project / 'SKILL.md').write_text('---\nname: framebridge-web-imagegen\ndescription: fixture\n---\nRoot: PROJECT_ROOT_VALUE\n', encoding='utf-8')
        self.destination = self.base / 'skills'

    def test_install_does_not_store_session_or_consent(self):
        target = install(self.project, self.destination)
        metadata = json.loads(target.with_name('framebridge-install.json').read_text())
        self.assertEqual(set(metadata), {'schema', 'managed_by', 'skill', 'project'})
        self.assertIn(str(self.project.resolve()), target.read_text())
        self.assertFalse((self.project / 'tasks.json').exists())

    def test_explicit_update_after_project_move(self):
        target = install(self.project, self.destination)
        moved = self.base / 'moved project'
        moved.mkdir()
        (moved / 'scripts').mkdir()
        for name in ('SKILL.md', 'scripts/framebridge.py', 'scripts/web_chatgpt.py'):
            (moved / name).write_bytes((self.project / name).read_bytes())
        with self.assertRaises(FileExistsError): install(moved, self.destination)
        install(moved, self.destination, update=True)
        self.assertIn(str(moved.resolve()), target.read_text())
        self.assertIn(str(self.project.resolve()), target.with_name('SKILL.md.previous').read_text())

    def test_legacy_requires_reviewed_adoption(self):
        folder = self.destination / 'framebridge-web-imagegen'
        folder.mkdir(parents=True)
        entry = folder / 'SKILL.md'
        entry.write_text('---\nname: framebridge-web-imagegen\ndescription: legacy\n---\nold\n')
        with self.assertRaises(FileExistsError): install(self.project, self.destination, update=True)
        install(self.project, self.destination, update=True, adopt_existing=True)
        self.assertIn(str(self.project.resolve()), entry.read_text())

    def test_different_skill_cannot_be_adopted(self):
        folder = self.destination / 'framebridge-web-imagegen'
        folder.mkdir(parents=True)
        entry = folder / 'SKILL.md'
        entry.write_text('---\nname: unrelated-skill\n---\nkeep\n')
        with self.assertRaises(FileExistsError): install(self.project, self.destination, update=True, adopt_existing=True)
        self.assertIn('unrelated-skill', entry.read_text())

    def test_incomplete_checkout_installs_nothing(self):
        (self.project / 'scripts/web_chatgpt.py').unlink()
        with self.assertRaises(FileNotFoundError): install(self.project, self.destination)
        self.assertFalse(self.destination.exists())

    def test_secret_scanner_redacts_values(self):
        value = 'ghp_' + 'A' * 40
        findings = scan_text('example\n' + value, 'fixture.py')
        self.assertEqual(findings[0]['line'], 2)
        self.assertNotIn(value, json.dumps(findings))

    def test_sensitive_history_paths_include_binary_profiles(self):
        for path in ('profile/User Data/Default/Preferences', '.env.production', 'logs/A/task.json', 'edge-session/file.bin'):
            self.assertTrue(sensitive_path(path), path)
        self.assertFalse(sensitive_path('logs/.gitkeep'))
        self.assertFalse(sensitive_path('prompts/example.md'))

    def test_foreign_manifest_preserved(self):
        target = install(self.project, self.destination)
        manifest = target.with_name('framebridge-install.json')
        original = '{"managed_by":"another installer"}\n'
        manifest.write_text(original)
        with self.assertRaises(FileExistsError):
            install(self.project, self.destination, update=True, adopt_existing=True)
        self.assertEqual(manifest.read_text(), original)

    def test_chinese_and_duplicate_heading_links(self):
        self.assertEqual(heading_ids('# 安全与服务条款\n## Quick start\n## Quick start\n'),
                         {'安全与服务条款', 'quick-start', 'quick-start-1'})


if __name__ == '__main__':
    unittest.main()
