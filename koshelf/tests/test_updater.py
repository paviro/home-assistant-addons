import importlib.util
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('updater', ROOT / 'scripts/update-upstream.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.current = json.loads((ROOT / 'upstream.json').read_text())
        self.release = {'tag_name': '2099.1.0', 'assets': [{'name': item['name']} for item in self.current['assets'].values()]}
        self.sums = '\n'.join('a' * 64 + '  ' + item['name'] for item in self.current['assets'].values())

    def test_candidate_pins_all_architectures(self):
        candidate = updater.candidate(self.current, self.release, self.sums)
        self.assertEqual(candidate['version'], '2099.1.0')
        self.assertTrue(all(item['sha256'] == 'a' * 64 for item in candidate['assets'].values()))

    def test_missing_architecture_or_checksum_fails(self):
        self.release['assets'].pop()
        with self.assertRaises(ValueError):
            updater.candidate(self.current, self.release, self.sums)

    def test_unstable_tags_are_rejected(self):
        for tag in ['2099.1.0;evil', '2099.1.0-rc1', '../2099.1.0']:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                updater.candidate(self.current, {**self.release, 'tag_name': tag}, self.sums)

    def test_same_release_is_not_republished(self):
        self.assertIsNone(updater.candidate(self.current, {**self.release, 'tag_name': self.current['version']}, self.sums))

    def test_write_keeps_addon_version_in_sync_with_upstream(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ['upstream.json', 'config.yaml', 'CHANGELOG.md']:
                (root / name).write_text((ROOT / name).read_text())
            with patch.object(updater, 'ROOT', root), patch.object(
                updater, 'fetch', side_effect=[json.dumps(self.release).encode(), self.sums.encode()]
            ), patch('sys.argv', ['update-upstream.py', '--write']), patch.dict(updater.os.environ, {}, clear=True):
                updater.main()
            self.assertIn('version: "2099.1.0"\n', (root / 'config.yaml').read_text())
            self.assertTrue((root / 'CHANGELOG.md').read_text().startswith('# 2099.1.0\n'))
            self.assertEqual(json.loads((root / 'upstream.json').read_text())['version'], '2099.1.0')
