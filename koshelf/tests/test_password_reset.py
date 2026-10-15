import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import addon


class PasswordResetTests(unittest.TestCase):
    def test_api_failure_does_not_rotate_password_again_on_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'pending'
            cfg = {'reset_password': True, 'direct_enabled': False, 'http_enabled': False, 'direct_host': ''}
            response = MagicMock()
            response.__enter__.return_value.read.return_value = b'{"result":"ok"}'
            with patch.object(addon, 'RESET_MARKER', marker), patch.dict(addon.os.environ, {'SUPERVISOR_TOKEN': 'test-only'}), \
                 patch.object(addon.subprocess, 'run') as run, patch.object(addon, 'urlopen', side_effect=[OSError('unavailable'), response]) as api:
                with self.assertRaises(OSError):
                    addon.reset_password(cfg)
                self.assertTrue(marker.exists())
                addon.reset_password(cfg)
                self.assertEqual(run.call_count, 1)
                self.assertFalse(marker.exists())
                sent = json.loads(api.call_args.args[0].data)['options']
                self.assertFalse(sent['reset_password'])
                self.assertNotIn('direct_enabled', sent)

    def test_failed_password_command_never_marks_reset_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'pending'
            with patch.object(addon, 'RESET_MARKER', marker), patch.object(addon.subprocess, 'run', side_effect=RuntimeError('failed')):
                with self.assertRaises(RuntimeError):
                    addon.reset_password({'reset_password': True})
                self.assertFalse(marker.exists())
