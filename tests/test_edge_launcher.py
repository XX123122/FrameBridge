"""Windows launcher safety checks: never launches or uses a browser profile."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import unittest


POWERSHELL = shutil.which('powershell') if os.name == 'nt' else None
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(POWERSHELL, 'Windows PowerShell launcher checks')
class EdgeLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.exe = self.base / 'fixture edge.exe'
        self.exe.write_bytes(b'not an executable: must never be launched')
        self.profile = self.base / 'unused profile'

    def call(self, *flags, profile=None):
        return subprocess.run([
            POWERSHELL, '-NoProfile', '-NonInteractive', '-File',
            str(ROOT / 'scripts/start_edge.ps1'), '-EdgePath', str(self.exe),
            '-ProfileDirectory', str(profile or self.profile), *flags],
            text=True, capture_output=True, timeout=20)

    def test_no_consent_stops_without_profile_creation(self):
        result = self.call()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ConfirmLocalControl', result.stderr)
        self.assertFalse(self.profile.exists())

    def test_dry_run_is_loopback_and_does_not_launch(self):
        result = self.call('-DryRun')
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan['BindAddress'], '127.0.0.1')
        self.assertFalse(plan['WouldLaunch'])
        self.assertFalse(plan['LocalControlConfirmed'])
        self.assertFalse(self.profile.exists())

    def test_default_profile_rejected_even_for_dry_run(self):
        result = self.call('-DryRun', profile=Path(os.environ['LOCALAPPDATA']) / 'Microsoft/Edge/User Data/Default')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('default Edge profile', result.stderr)

    def test_checkout_profile_rejected_even_for_dry_run(self):
        result = self.call('-DryRun', profile=ROOT / '.cache/unused-profile')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('outside this source checkout', result.stderr)

    def test_occupied_port_refuses_launch(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen()
            port = str(listener.getsockname()[1])
            result = self.call('-ConfirmLocalControl', '-Port', port)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('port is in use', result.stderr)
        self.assertFalse(self.profile.exists())


if __name__ == '__main__':
    unittest.main()
