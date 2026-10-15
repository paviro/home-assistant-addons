import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import addon


class MigrationTests(unittest.TestCase):
    def test_access_choices_survive_schema_removal(self):
        cases = [
            ({}, False, False),
            ({'enable_auth': True}, True, True),
            ({'direct_access': 'auto', 'enable_auth': True}, True, True),
            ({'direct_access': 'auto', 'enable_auth': False}, False, False),
            ({'direct_access': 'enabled', 'allow_insecure_http': True}, True, True),
            ({'direct_access': 'enabled', 'allow_insecure_http': False}, True, False),
            ({'direct_access': 'disabled', 'enable_auth': True}, False, False),
        ]
        for legacy, enabled, http in cases:
            with self.subTest(legacy=legacy):
                stored = {'library_path': ['/share/books'], 'title': '!secret library_name',
                          'trusted_proxies': ['172.30.32.0/23'], **legacy}
                raw = {k: v for k, v in stored.items() if k not in ('direct_access', 'enable_auth')}
                raw['title'] = 'My library'
                with patch.object(addon, 'supervisor_options', side_effect=[{'data': {'options': stored}}, {}]) as api:
                    migrated = addon.migrate_options(raw)
                saved = api.call_args_list[1].args[1]
                self.assertEqual(migrated['direct_access_enabled'], enabled)
                self.assertEqual(migrated['allow_insecure_http'], http)
                self.assertNotIn('direct_access', saved)
                self.assertNotIn('enable_auth', saved)
                self.assertEqual(saved['title'], '!secret library_name')
                self.assertEqual(migrated['title'], 'My library')
                self.assertEqual(saved['trusted_proxies'], ['172.30.32.0/23'])
                with patch.object(addon, 'supervisor_options') as api:
                    self.assertEqual(addon.migrate_options(migrated), migrated)
                    api.assert_not_called()

    def test_explicit_new_choice_never_reads_legacy_settings(self):
        for enabled in (True, False):
            raw = {'direct_access_enabled': enabled, 'allow_insecure_http': False}
            with patch.object(addon, 'supervisor_options') as api:
                self.assertEqual(addon.migrate_options(raw), raw)
                api.assert_not_called()

    def test_failed_save_retries_without_changing_input(self):
        raw = {'library_path': ['/share/books']}
        stored = {**raw, 'enable_auth': True}
        with patch.object(addon, 'supervisor_options', side_effect=[
            {'data': {'options': stored}}, OSError('unavailable'),
            {'data': {'options': stored}}, {},
        ]):
            with self.assertRaises(OSError):
                addon.migrate_options(raw)
            self.assertNotIn('direct_access_enabled', raw)
            self.assertTrue(addon.migrate_options(raw)['direct_access_enabled'])

    def test_supervisor_request_and_rejected_save(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"result":"ok","data":{"options":{}}}'
        with patch.dict(addon.os.environ, {'SUPERVISOR_TOKEN': 'test-only'}), patch.object(addon, 'urlopen', return_value=response) as api:
            addon.supervisor_options('GET')
            self.assertEqual(api.call_args.args[0].full_url, 'http://supervisor/addons/self/info')
            addon.supervisor_options('POST', {'direct_access_enabled': False})
            request = api.call_args.args[0]
            self.assertEqual(request.full_url, 'http://supervisor/addons/self/options')
            self.assertEqual(json.loads(request.data), {'options': {'direct_access_enabled': False}})
            response.__enter__.return_value.read.return_value = b'{"result":"error"}'
            with self.assertRaises(RuntimeError):
                addon.supervisor_options('POST', {})
