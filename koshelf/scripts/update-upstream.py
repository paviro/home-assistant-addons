#!/usr/bin/env python3
"""Propose a stable upstream release; never change the running container."""
import argparse
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def fetch(url):
    request = Request(url, headers={'User-Agent': 'koshelf-addon-updater'})
    with urlopen(request, timeout=60) as response:
        return response.read()


def candidate(current, release, checksum_text):
    version = release['tag_name']
    if release.get('draft') or release.get('prerelease') or not re.fullmatch(r'\d{4}\.\d+\.\d+', version):
        raise ValueError('Only stable calendar-versioned KoShelf releases are supported')
    if tuple(map(int, version.split('.'))) <= tuple(map(int, current['version'].split('.'))):
        return None
    names = {asset['name'] for asset in release['assets']}
    hashes = {}
    for line in checksum_text.splitlines():
        match = re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?([A-Za-z0-9._-]+)', line)
        if match:
            digest, name = match.groups()
            if name in hashes:
                raise ValueError('Duplicate checksum entry')
            hashes[name] = digest.lower()
    result = json.loads(json.dumps(current))
    for asset in result['assets'].values():
        if asset['name'] not in names or asset['name'] not in hashes:
            raise ValueError(f"Release lacks asset/checksum: {asset['name']}")
        asset['sha256'] = hashes[asset['name']]
    result['version'] = version
    # This is a candidate only: every architecture must build and pass runtime
    # integration tests before the workflow creates a reviewable PR.
    result['integration_ready'] = True
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    manifest = ROOT / 'upstream.json'
    current = json.loads(manifest.read_text())
    release = json.loads(fetch('https://api.github.com/repos/paviro/KoShelf/releases/latest'))
    version = release['tag_name']
    if not re.fullmatch(r'\d{4}\.\d+\.\d+', version):
        raise ValueError('Invalid release tag')
    checksum = fetch(f'https://github.com/paviro/KoShelf/releases/download/{version}/SHA256SUMS').decode()
    proposed = candidate(current, release, checksum)
    if proposed and args.write:
        manifest.write_text(json.dumps(proposed, indent=2) + '\n')
        config = ROOT / 'config.yaml'
        text, count = re.subn(r'^version: "[^"\n]+"$', f'version: "{version}"', config.read_text(), flags=re.M)
        if count != 1:
            raise ValueError('Expected exactly one add-on version')
        config.write_text(text)
        changelog = ROOT / 'CHANGELOG.md'
        changelog.write_text(f'# {version}\n\n- Update KoShelf to {version}. Review upstream release notes and Home Assistant smoke results before merging.\n\n' + changelog.read_text())
    if output := os.environ.get('GITHUB_OUTPUT'):
        with open(output, 'a') as stream:
            stream.write(f'changed={str(proposed is not None).lower()}\nversion={version}\n')
    print(f'Candidate: {version}' if proposed else 'No newer stable upstream release')


if __name__ == '__main__':
    main()
