#!/usr/bin/env python3
"""Validate Home Assistant metadata, including real upgrade ordering."""
import json
from pathlib import Path
from awesomeversion import AwesomeVersion
import yaml

root = Path(__file__).resolve().parents[1]
config = yaml.safe_load((root / 'config.yaml').read_text())
build = yaml.safe_load((root / 'build.yaml').read_text())
manifest = json.loads((root / 'upstream.json').read_text())
labels = yaml.safe_load((root / 'translations/en.yaml').read_text())['configuration']
assert config['schema'].keys() == labels.keys()
assert config['options'].keys() == config['schema'].keys() - {'direct_access_enabled'}
assert config['schema']['direct_access_enabled'] == 'bool?'
assert 'enable_auth' not in config['schema']
assert set(config['arch']) == set(build['build_from']) == set(manifest['assets'])
assert AwesomeVersion(config['version']) >= AwesomeVersion(manifest['version'])
assert config['slug'] == 'koshelf'
assert config['ingress'] and config['ingress_port'] == 8099
# Keep the old default so upgrades retain the host port; the listener is gated by direct_access_enabled.
assert config['ports']['38492/tcp'] == 38492
assert config['timeout'] >= 20
# Omitted until first startup so migration can distinguish old installations.
assert 'direct_access_enabled' not in config['options']
print('PASS: metadata, translations, architecture coverage and in-place upgrade ordering')
