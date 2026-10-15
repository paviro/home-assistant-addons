"""Install only a reviewed, checksum-pinned compatible release binary."""
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
from urllib.request import urlopen
import zipfile


def install(arch):
    manifest = json.loads(Path(__file__).with_name('upstream.json').read_text())
    if not manifest['integration_ready']:
        raise SystemExit('Release blocked: publish KoShelf proxy integration first, then update upstream.json. See UPSTREAM.md.')
    if not arch:
        arch = {'x86_64': 'amd64', 'aarch64': 'aarch64', 'armv7l': 'armv7', 'i686': 'i386'}.get(platform.machine())
    if arch not in manifest['assets']:
        raise SystemExit(f'Unsupported architecture: {arch}')
    asset = manifest['assets'][arch]
    url = f"https://github.com/paviro/KoShelf/releases/download/{manifest['version']}/{asset['name']}"
    with urlopen(url, timeout=120) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != asset['sha256']:
        raise SystemExit('Upstream archive checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        binary = bundle.read('koshelf')
    target = Path('/usr/local/bin/koshelf')
    target.write_bytes(binary)
    target.chmod(0o755)
    help_text = subprocess.check_output([str(target), 'serve', '--help'], text=True)
    if any(flag not in help_text for flag in manifest['required_flags']):
        raise SystemExit('Upstream release lacks required proxy integration')


if __name__ == '__main__':
    install(sys.argv[1] if len(sys.argv) > 1 else '')
