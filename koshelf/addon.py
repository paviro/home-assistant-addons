#!/usr/bin/env python3
"""KoShelf Home Assistant wrapper. No application credentials cross the proxy."""
import ipaddress
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

RUNTIME = Path('/run/koshelf')
OPTIONS = Path('/data/options.json')
BINARY = '/usr/local/bin/koshelf'
RESET_MARKER = Path('/data/.password-reset-pending')


def options(raw):
    cfg = dict(raw)
    mode = cfg.get('direct_access', 'auto')
    if mode not in ('auto', 'enabled', 'disabled'):
        raise ValueError('direct_access must be auto, enabled or disabled')
    legacy = mode == 'auto' and cfg.get('enable_auth') is True
    cfg['direct_enabled'] = mode == 'enabled' or legacy
    cfg['http_enabled'] = cfg.get('allow_insecure_http', False) is True or legacy
    cfg['allowed_ha_user_ids'] = cfg.get('allowed_ha_user_ids', [])
    if not isinstance(cfg['allowed_ha_user_ids'], list) or any(
        not isinstance(v, str) or not re.fullmatch(r'[a-f0-9]{32}', v)
        for v in cfg['allowed_ha_user_ids']
    ):
        raise ValueError('allowed_ha_user_ids must contain Home Assistant user IDs (32 lowercase hex characters)')
    cfg['trusted_proxies'] = [str(ipaddress.ip_network(v, strict=False)) for v in cfg.get('trusted_proxies', [])]
    if any(net.endswith('/0') for net in cfg['trusted_proxies']):
        raise ValueError('trusted_proxies must list specific proxy addresses, not every address')
    origin = cfg.get('direct_url', '').rstrip('/')
    url = urlsplit(origin)
    if origin and (url.scheme != 'https' or not url.hostname or url.path or url.query or url.fragment
                   or url.username or url.password or not re.fullmatch(r'https://[A-Za-z0-9.\-\[\]:]+', origin)):
        raise ValueError('direct_url must be an HTTPS origin, without a path or credentials')
    if origin:
        _ = url.port  # validates port syntax and range
    # Browsers send lowercase hostnames; nginx compares Host case-sensitively.
    cfg['direct_host'] = url.netloc.lower()
    if cfg['direct_enabled'] and not cfg['http_enabled'] and (not origin or not cfg['trusted_proxies']):
        raise ValueError('HTTPS direct access requires direct_url and trusted_proxies; alternatively explicitly allow LAN HTTP')
    libraries = cfg.get('library_path', [])
    if not isinstance(libraries, list) or any(not isinstance(p, str) or not p for p in libraries):
        raise ValueError('library_path must be a list of nonempty paths')
    statistics = cfg.get('statistics_db', [])
    if not isinstance(statistics, list) or any(not isinstance(p, str) or not p for p in statistics):
        raise ValueError('statistics_db must be a list of nonempty paths')
    if not libraries and not cfg.get('database_path') and not statistics:
        raise ValueError('Configure library_path, database_path or statistics_db under /share or /media')
    if cfg.get('document_metadata_folder', 'doc') not in ('doc', 'dir', 'hash'):
        raise ValueError('document_metadata_folder must be doc, dir or hash')
    if not isinstance(cfg.get('archive_enabled', True), bool):
        raise ValueError('archive_enabled must be true or false')
    retention = str(cfg.get('archive_retention_days', '30'))
    if retention != 'forever' and (not re.fullmatch(r'[0-9]{1,10}', retention) or int(retention) > 4294967295):
        raise ValueError('archive_retention_days must be a nonnegative 32-bit integer or forever')
    if any(cfg.get(k) for k in ('kobo_db', 'docsettings_path', 'hashdocsettings_path')) and not libraries:
        raise ValueError('Kobo and separate metadata paths require library_path')
    if re.fullmatch(r'[A-Za-z]{2}', cfg.get('language', 'en_US')):
        raise ValueError('language requires a full locale such as en_US or de_DE')
    return cfg


def command(cfg):
    args = [BINARY, 'serve', '--port', '3000', '--bind-address', '127.0.0.1',
            '--data-path', '/data', '--enable-auth', '--auth-proxy-peers', '127.0.0.1/32',
            '--trusted-proxies', '127.0.0.1/32']
    for path in cfg.get('library_path', []):
        args += ['--library-path', path]
    # Keep the old single-path option and avoid passing identical paths twice.
    statistics = ([cfg['database_path']] if cfg.get('database_path') else []) + cfg.get('statistics_db', [])
    for path in dict.fromkeys(statistics):
        args += ['--statistics-db', path]
    args += ['--archive-enabled', str(cfg.get('archive_enabled', True)).lower(),
             '--archive-retention-days', str(cfg.get('archive_retention_days', '30')),
             '--document-metadata-folder', cfg.get('document_metadata_folder', 'doc')]
    mapping = {'kobo_db': 'kobo-db',
               'docsettings_path': 'docsettings-path', 'hashdocsettings_path': 'hashdocsettings-path',
               'title': 'title', 'heatmap_scale_max': 'heatmap-scale-max', 'day_start_time': 'day-start-time',
               'timezone': 'timezone', 'min_pages_per_day': 'min-pages-per-day',
               'min_time_per_day': 'min-time-per-day', 'language': 'language'}
    for key, flag in mapping.items():
        if cfg.get(key) not in (None, ''):
            args += ['--' + flag, str(cfg[key])]
    for key in ('include_unread', 'include_all_stats', 'enable_writeback', 'enable_library_management', 'ignore_stable_page_metadata'):
        if cfg.get(key) is True and (key != 'include_unread' or cfg.get('library_path')):
            args += ['--' + key.replace('_', '-')]
    return args


def nginx(cfg):
    ids = cfg['allowed_ha_user_ids']
    allowed = '\n'.join(f'        "{uid}" 1;' for uid in ids)
    if not ids:
        allowed = '        "~^[a-f0-9]{32}$" 1;'
    networks = '\n'.join(f'        {net} 1;' for net in cfg['trusted_proxies'])
    realip = '\n'.join(f'        set_real_ip_from {net};' for net in cfg['trusted_proxies'])
    common = '''
        location / {
            proxy_pass http://127.0.0.1:3000;
            proxy_http_version 1.1;
            proxy_set_header Host $http_host;
            proxy_set_header Connection "";
            proxy_set_header Forwarded "";
            proxy_set_header X-Real-IP "";
            proxy_set_header CF-Connecting-IP "";
            proxy_set_header X-Remote-User-Id "";
            proxy_set_header X-Remote-User-Name "";
            proxy_set_header X-Remote-User-Display-Name "";
            proxy_set_header X-Ingress-Path "";
            proxy_buffering off;
            proxy_read_timeout 3600s;
            client_max_body_size 21m;
            # listener-specific headers below
            HEADERS
        }
'''
    ingress = common.replace('HEADERS', '''proxy_set_header X-KoShelf-User $http_x_remote_user_id;
            proxy_set_header X-Forwarded-Prefix $ingress_prefix;
            proxy_set_header X-Forwarded-For 172.30.32.2;
            proxy_set_header X-Forwarded-Proto $ingress_proto;
            proxy_set_header Cookie "";
            proxy_set_header Authorization "";
            proxy_hide_header Set-Cookie;''')
    direct = common.replace('HEADERS', '''proxy_set_header X-KoShelf-User "";
            proxy_set_header X-Forwarded-Prefix "";
            proxy_set_header X-Forwarded-For $remote_addr;
            proxy_set_header X-Forwarded-Proto $direct_proto;''')
    direct_server = ''
    if cfg['direct_enabled']:
        https_gate = ''
        if not cfg['http_enabled']:
            https_gate = f'''if ($direct_proto != https) {{ return 403; }}
        if ($http_host != "{cfg['direct_host']}") {{ return 403; }}'''
        direct_server = f'''server {{
        listen 38492;
        server_name _;
{realip}
        real_ip_header X-Forwarded-For;
        real_ip_recursive on;
        {https_gate}
        add_header Content-Security-Policy "frame-ancestors 'none'" always;
{direct}
    }}'''
    return f'''worker_processes 1;
pid /run/koshelf/nginx.pid;
error_log /dev/stderr warn;
events {{ worker_connections 512; }}
http {{
    access_log off;
    server_tokens off;
    client_body_temp_path /run/koshelf/client;
    proxy_temp_path /run/koshelf/proxy;
    # The default follows the CPU cache line (32 on armv7), too small for user-ID keys.
    map_hash_bucket_size 128;
    map $http_x_remote_user_id $allowed_user {{
        default 0;
{allowed}
    }}
    map $http_x_ingress_path $ingress_prefix {{
        default "";
        "~^(/api/hassio_ingress/[A-Za-z0-9_-]+)/?$" $1;
    }}
    map $http_x_forwarded_proto $ingress_proto {{
        default http;
        https https;
    }}
    geo $realip_remote_addr $trusted_direct_proxy {{
        default 0;
{networks}
    }}
    map "$trusted_direct_proxy:$http_x_forwarded_proto" $direct_proto {{
        default http;
        "1:https" https;
    }}
    server {{
        listen 8099;
        server_name _;
        # Check the actual peer before serving, including rewrite-phase responses.
        if ($remote_addr != 172.30.32.2) {{ return 403; }}
        allow 172.30.32.2;
        deny all;
        if ($allowed_user = 0) {{ return 403; }}
        if ($ingress_prefix = "") {{ return 403; }}
{ingress}
    }}
    {direct_server}
}}
'''


def reset_password(cfg):
    if not cfg.get('reset_password'):
        return
    # Persist the completed reset before contacting Supervisor. A failed options
    # update must not rotate the password again on every container restart.
    marker = RESET_MARKER
    if not marker.exists():
        subprocess.run([BINARY, 'set-password', '--data-path', '/data', '--random', '--overwrite'], check=True)
        marker.touch(mode=0o600)
    updated = dict(cfg)
    updated['reset_password'] = False
    for key in ('direct_enabled', 'http_enabled', 'direct_host'):
        updated.pop(key, None)
    request = Request('http://supervisor/addons/self/options',
                      data=json.dumps({'options': updated}).encode(), method='POST',
                      headers={'Authorization': 'Bearer ' + os.environ['SUPERVISOR_TOKEN'],
                               'Content-Type': 'application/json'})
    with urlopen(request, timeout=15) as response:
        result = json.load(response)
    if result.get('result') != 'ok':
        raise RuntimeError('Supervisor did not confirm password-reset option update')
    marker.unlink()


def healthcheck():
    if not os.access('/data', os.W_OK):
        return 1
    with urlopen('http://127.0.0.1:3000/api/site', timeout=5) as response:
        if response.status != 200:
            return 1
    # Ingress must answer but refuse an ordinary loopback caller.
    import urllib.error
    try:
        urlopen('http://127.0.0.1:8099/', timeout=5)
    except urllib.error.HTTPError as error:
        return 0 if error.code == 403 else 1
    return 1


def main():
    if '--healthcheck' in sys.argv:
        return healthcheck()
    cfg = options(json.loads(OPTIONS.read_text()))
    # nginx drops worker privileges; workers need to traverse to their body buffers.
    RUNTIME.mkdir(mode=0o755, parents=True, exist_ok=True)
    RUNTIME.chmod(0o755)
    help_text = subprocess.check_output([BINARY, 'serve', '--help'], text=True)
    for flag in ('--bind-address', '--auth-proxy-peers'):
        if flag not in help_text:
            raise RuntimeError('This KoShelf release lacks required proxy integration; install a compatible upstream release')
    if not cfg.get('reset_password'):
        RESET_MARKER.unlink(missing_ok=True)
    reset_password(cfg)
    config = RUNTIME / 'nginx.conf'
    config.write_text(nginx(cfg))
    subprocess.run(['nginx', '-t', '-c', str(config)], check=True)
    if cfg.get('debug_log'):
        os.environ['RUST_LOG'] = 'debug'
    print(f"KoShelf: Ingress enabled; direct access {'enabled' if cfg['direct_enabled'] else 'disabled'}", flush=True)
    if cfg['direct_enabled'] and cfg['http_enabled']:
        print('Direct LAN HTTP is enabled: passwords and sessions are not encrypted. Use HTTPS outside a trusted LAN.', flush=True)
    children = []
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        # Do not pass the Supervisor credential into either network-facing child.
        env = {key: value for key, value in os.environ.items() if key not in ('SUPERVISOR_TOKEN', 'HASSIO_TOKEN')}
        children.append(subprocess.Popen(command(cfg), env=env))
        children.append(subprocess.Popen(['nginx', '-c', str(config), '-g', 'daemon off;'], env=env))
        while not stopping and all(child.poll() is None for child in children):
            time.sleep(0.25)
        return 0 if stopping else 1
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        deadline = time.monotonic() + 20
        for child in children:
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'KoShelf startup failed: {error}', file=sys.stderr)
        sys.exit(1)
