import contextlib
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from addon import command, nginx, options


class ConfigurationTests(unittest.TestCase):
    def cfg(self, **values):
        return options({'library_path': ['/share/My Books'], **values})

    def test_migration_preserves_only_authenticated_direct_access(self):
        self.assertFalse(self.cfg()['direct_enabled'])
        self.assertFalse(self.cfg(enable_auth=False)['direct_enabled'])
        cfg = self.cfg(enable_auth=True)
        self.assertTrue(cfg['direct_enabled'])
        self.assertTrue(cfg['http_enabled'])
        self.assertFalse(self.cfg(enable_auth=True, direct_access='disabled')['direct_enabled'])

    def test_explicit_direct_access_requires_transport_configuration(self):
        with self.assertRaises(ValueError):
            self.cfg(direct_access='enabled')
        self.assertTrue(self.cfg(direct_access='enabled', allow_insecure_http=True)['direct_enabled'])
        cfg = self.cfg(direct_access='enabled', direct_url='https://books.example', trusted_proxies=['192.168.1.5'])
        self.assertFalse(cfg['http_enabled'])
        self.assertIn('if ($direct_proto != https)', nginx(cfg))

    def test_rejects_nginx_injection_and_invalid_values(self):
        for values in [dict(allowed_ha_user_ids=['x; return 200;']), dict(trusted_proxies=['all']),
                       dict(direct_url='https://example/evil'), dict(direct_url='https://user:password@example'),
                       dict(library_path=[]), dict(language='en')]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.cfg(**values)

    def test_library_arguments_are_not_shell_interpreted(self):
        args = command(self.cfg(title='$(touch /tmp/no)'))
        self.assertIn('/share/My Books', args)
        self.assertIn('$(touch /tmp/no)', args)
        self.assertIn('--enable-auth', args)
        self.assertIn('127.0.0.1/32', args)
        self.assertNotIn('172.30.32.0/23', args)

    def test_proxy_identity_is_exclusive_to_supervisor_entrypoint(self):
        conf = nginx(self.cfg(direct_access='enabled', allow_insecure_http=True))
        ingress, direct = conf.split('listen 38492;')
        self.assertIn('if ($remote_addr != 172.30.32.2)', ingress)
        self.assertIn('if ($allowed_user = 0)', ingress)
        self.assertIn('proxy_set_header Cookie "";', ingress)
        self.assertIn('proxy_set_header X-KoShelf-User "";', direct)
        self.assertIn('proxy_set_header X-Forwarded-Prefix "";', direct)
        self.assertNotIn('listen 38492;', nginx(self.cfg()))

    def test_allowlist_is_exact(self):
        uid = 'a' * 32
        conf = nginx(self.cfg(allowed_ha_user_ids=[uid]))
        self.assertIn(f'"{uid}" 1;', conf)
        self.assertNotIn('"~^[a-f0-9]{32}$"', conf)

    def test_former_default_proxy_is_not_trusted_after_migration(self):
        with contextlib.redirect_stdout(io.StringIO()):
            cfg = self.cfg(enable_auth=True, trusted_proxies=['172.30.32.0/23', '192.168.1.5'])
        self.assertEqual(cfg['trusted_proxies'], ['192.168.1.5/32'])
        self.assertNotIn('172.30.32.0/23', nginx(cfg))
        explicit = self.cfg(direct_access='enabled', allow_insecure_http=True, trusted_proxies=['172.30.32.0/23'])
        self.assertEqual(explicit['trusted_proxies'], ['172.30.32.0/23'])
        for everything in ('0.0.0.0/0', '::/0'):
            with self.subTest(everything=everything), self.assertRaises(ValueError):
                self.cfg(trusted_proxies=[everything])

    def test_direct_host_is_compared_in_lowercase(self):
        cfg = self.cfg(direct_access='enabled', direct_url='https://Books.Example:8443', trusted_proxies=['192.168.1.5'])
        self.assertIn('if ($http_host != "books.example:8443")', nginx(cfg))

    def test_statistics_only_and_legacy_sources_are_merged_without_duplicates(self):
        cfg = self.cfg(library_path=[], database_path='/share/kobo.sqlite3',
                       statistics_db=['/share/kobo.sqlite3', '/media/boox.sqlite3'])
        args = command(cfg)
        paths = [args[i + 1] for i, arg in enumerate(args) if arg == '--statistics-db']
        self.assertEqual(paths, ['/share/kobo.sqlite3', '/media/boox.sqlite3'])
        self.assertNotIn('--include-unread', args)
        self.cfg(library_path=[], statistics_db=['/share/stats.sqlite3'])
        for invalid in ('/share/stats.sqlite3', [''], [42]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.cfg(statistics_db=invalid)

    def test_archive_disable_is_explicit_and_management_remains_opt_in(self):
        args = command(self.cfg(archive_enabled=False, archive_retention_days='forever',
                                document_metadata_folder='hash'))
        self.assertEqual(args[args.index('--archive-enabled') + 1], 'false')
        self.assertEqual(args[args.index('--archive-retention-days') + 1], 'forever')
        self.assertEqual(args[args.index('--document-metadata-folder') + 1], 'hash')
        self.assertNotIn('--enable-library-management', args)
        self.assertIn('--enable-library-management', command(self.cfg(enable_library_management=True)))
        for invalid in ('-1', '1.5', '4294967296', '', True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.cfg(archive_retention_days=invalid)
        for valid in ('0', '30', '4294967295', 'forever'):
            self.cfg(archive_retention_days=valid)
        with self.assertRaises(ValueError):
            self.cfg(document_metadata_folder='other')


if __name__ == '__main__':
    unittest.main()
