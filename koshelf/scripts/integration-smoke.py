#!/usr/bin/env python3
"""Exercise the real KoShelf server and nginx. Uses disposable data and ports."""
import argparse
import http.client
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from addon import command, nginx, options


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def request(port, path='/', headers=None, body=None, method='GET'):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    connection.request(method, path, body=body, headers=headers or {})
    response = connection.getresponse()
    result = response.status, dict(response.getheaders()), response.read()
    connection.close()
    return result


def wait(port):
    for _ in range(100):
        try:
            request(port, '/api/site')
            return
        except (OSError, http.client.HTTPException):
            time.sleep(.1)
    raise AssertionError('service did not start')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', required=True)
    parser.add_argument('--nginx', required=True)
    args = parser.parse_args()
    backend, ingress, direct = free_port(), free_port(), free_port()
    password = secrets.token_urlsafe(32)
    children = []
    with tempfile.TemporaryDirectory(prefix='koshelf-smoke-') as folder:
        root = Path(folder).resolve()
        root.chmod(0o755)
        folder = str(root)
        library = root / 'books'
        library.mkdir()
        data = root / 'data'
        log = (root / 'services.log').open('w+')
        env = dict(os.environ, KOSHELF_PASSWORD=password)
        subprocess.run([args.binary, 'set-password', '--data-path', str(data)], env=env, check=True, stdout=log, stderr=log)
        base = command(options({'library_path': [str(library)],
                                'archive_retention_days': 'forever',
                                'document_metadata_folder': 'hash',
                                'enable_library_management': True}))
        base[0] = args.binary
        base[base.index('--data-path') + 1] = str(data)
        base[base.index('--port') + 1] = str(backend)
        proxy_index = base.index('--auth-proxy-peers')
        del base[proxy_index:proxy_index + 2]
        try:
            # Forwarded-IP trust alone must not grant authentication.
            server = subprocess.Popen(base, stdout=log, stderr=log)
            children.append(server)
            wait(backend)
            assert request(backend, '/api/items', {'X-KoShelf-User': 'alice'})[0] == 403
            server.terminate()
            server.wait(timeout=10)
            server = subprocess.Popen(base + ['--auth-proxy-peers', '127.0.0.1/32'], stdout=log, stderr=log)
            children.append(server)
            wait(backend)
            assert request(backend, '/api/items')[0] == 401
            assert request(backend, '/assets/files/private.epub')[0] == 401
            auth = {'X-KoShelf-User': 'alice', 'X-Forwarded-Prefix': '/api/hassio_ingress/test'}
            status, headers, body = request(backend, '/', auth)
            assert status == 200 and b'<base href="/api/hassio_ingress/test/">' in body
            assert headers.get('x-frame-options') == 'SAMEORIGIN'
            assert 'set-cookie' not in {key.lower() for key in headers}
            site = json.loads(request(backend, '/api/site', auth)[2])['data']
            assert site['auth']['authenticated'] and site['auth']['method'] == 'proxy'
            assert request(backend, '/api/items', auth)[0] == 200
            assert request(backend, '/api/auth/sessions', auth)[0] == 403
            assert request(backend, '/api/items', {**auth, 'X-Forwarded-Prefix': '//evil'})[0] == 403
            login = json.dumps({'password': password})
            h = {'Content-Type': 'application/json'}
            assert request(backend, '/api/auth/login', h, login, 'POST')[0] == 403
            h['X-KoShelf-Request'] = '1'
            # Client IP comes only through the explicitly trusted loopback proxy.
            lan = {**h, 'Host': '192.168.1.10:38492', 'X-Forwarded-For': '192.168.1.20'}
            status, lan_headers, _ = request(backend, '/api/auth/login', lan, login, 'POST')
            assert status == 200
            lan_cookie = next(value for key, value in lan_headers.items() if key.lower() == 'set-cookie')
            assert '; Secure' not in lan_cookie
            status, tls_headers, _ = request(backend, '/api/auth/login', {**lan, 'X-Forwarded-Proto': 'https'}, login, 'POST')
            assert status == 200
            assert '; Secure' in next(value for key, value in tls_headers.items() if key.lower() == 'set-cookie')
            assert request(backend, '/api/auth/login', {**h, 'Origin': 'https://evil.example', 'Sec-Fetch-Site': 'cross-site'}, login, 'POST')[0] == 403
            _, preflight, _ = request(backend, '/api/auth/login', {
                'Origin': 'https://evil.example', 'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'X-KoShelf-Request'}, method='OPTIONS')
            assert not any(key.lower() == 'access-control-allow-origin' for key in preflight)
            status, headers, _ = request(backend, '/api/auth/login', h, login, 'POST')
            assert status == 200
            cookie = next(value for key, value in headers.items() if key.lower() == 'set-cookie').split(';')[0]
            assert request(backend, '/api/items', {'Cookie': cookie})[0] == 200
            assert request(backend, '/api/auth/logout', {**h, 'Cookie': cookie}, '{}', 'POST')[0] in (200, 204)
            assert request(backend, '/api/items', {'Cookie': cookie})[0] == 401

            cfg = options({'library_path': [str(library)], 'direct_access_enabled': True, 'allow_insecure_http': True})
            conf = nginx(cfg).replace('/run/koshelf', folder).replace('127.0.0.1:3000', f'127.0.0.1:{backend}')
            conf = conf.replace('listen 8099;', f'listen 127.0.0.1:{ingress};').replace('listen 38492;', f'listen 127.0.0.1:{direct};')
            conf_path = root / 'nginx.conf'
            conf_path.write_text(conf)
            subprocess.run([args.nginx, '-t', '-p', folder, '-c', str(conf_path)], check=True, stdout=log, stderr=log)
            proxy = subprocess.Popen([args.nginx, '-p', folder, '-c', str(conf_path), '-g', 'daemon off;'], stdout=log, stderr=log)
            children.append(proxy)
            wait(direct)
            forged = {**auth, 'X-Remote-User-Id': 'a' * 32, 'X-Ingress-Path': '/api/hassio_ingress/test', 'X-Forwarded-For': '172.30.32.2'}
            assert request(ingress, '/', forged)[0] == 403
            assert request(direct, '/api/items', forged)[0] == 401
            assert request(direct, '/api/site', forged)[0] == 200
            assert json.loads(request(direct, '/api/site', forged)[2])['data']['auth']['method'] == 'password'
            # Exercise nginx body buffering as well as direct authentication.
            large_login = json.dumps({'password': password, 'padding': 'x' * 65536})
            assert request(direct, '/api/auth/login', h, large_login, 'POST')[0] == 200
            proxy.terminate()
            proxy.wait(timeout=10)
            # Simulate Supervisor on loopback solely in this disposable test config.
            conf_path.write_text(conf.replace('172.30.32.2', '127.0.0.1'))
            proxy = subprocess.Popen([args.nginx, '-p', folder, '-c', str(conf_path), '-g', 'daemon off;'], stdout=log, stderr=log)
            children.append(proxy)
            wait(direct)
            assert request(ingress, '/')[0] == 403
            assert request(ingress, '/api/items', forged)[0] == 200
            assert request(ingress, '/api/auth/sessions', forged)[0] == 403
            assert request(direct, '/api/items', forged)[0] == 401
            status, headers, html = request(ingress, '/', forged)
            assert status == 200 and b'<base href="/api/hassio_ingress/test/">' in html
            assert request(ingress, '/core/js/theme-bootstrap.js', forged)[0] == 200
            manifest = json.loads(request(ingress, '/manifest.json', forged)[2])
            assert manifest['start_url'] == './'
            stream = http.client.HTTPConnection('127.0.0.1', ingress, timeout=5)
            stream.request('GET', '/api/events/stream', headers=forged)
            response = stream.getresponse()
            assert response.status == 200
            assert response.getheader('Content-Type').startswith('text/event-stream')
            assert b'data_changed' in response.readline()
            stream.close()
            # An exact HA allowlist must deny a different, otherwise valid identity.
            proxy.terminate()
            proxy.wait(timeout=10)
            conf_path.write_text(conf.replace('172.30.32.2', '127.0.0.1').replace('"~^[a-f0-9]{32}$" 1;', '"' + 'b' * 32 + '" 1;'))
            proxy = subprocess.Popen([args.nginx, '-p', folder, '-c', str(conf_path), '-g', 'daemon off;'], stdout=log, stderr=log)
            children.append(proxy)
            wait(direct)
            assert request(ingress, '/api/items', forged)[0] == 403
            assert request(ingress, '/api/items', {**forged, 'X-Remote-User-Id': 'b' * 32})[0] == 200
            proxy.terminate()
            proxy.wait(timeout=10)
            tls_cfg = options({'library_path': [str(library)], 'direct_access_enabled': True,
                               'direct_url': 'https://books.example', 'trusted_proxies': ['192.0.2.1']})

            def tls_config():
                return nginx(tls_cfg).replace('/run/koshelf', folder).replace('127.0.0.1:3000', f'127.0.0.1:{backend}').replace('listen 8099;', f'listen 127.0.0.1:{ingress};').replace('listen 38492;', f'listen 127.0.0.1:{direct};')

            conf_path.write_text(tls_config())
            proxy = subprocess.Popen([args.nginx, '-p', folder, '-c', str(conf_path), '-g', 'daemon off;'], stdout=log, stderr=log)
            children.append(proxy)
            wait(direct)
            tls_headers = {'Host': 'books.example', 'X-Forwarded-Proto': 'https'}
            assert request(direct, '/api/site', tls_headers)[0] == 403
            proxy.terminate()
            proxy.wait(timeout=10)
            tls_cfg['trusted_proxies'] = ['127.0.0.1/32']
            conf_path.write_text(tls_config())
            proxy = subprocess.Popen([args.nginx, '-p', folder, '-c', str(conf_path), '-g', 'daemon off;'], stdout=log, stderr=log)
            children.append(proxy)
            wait(direct)
            assert request(direct, '/api/site', {'Host': 'books.example'})[0] == 403
            assert request(direct, '/api/site', tls_headers)[0] == 200
            assert request(direct, '/api/site', {**tls_headers, 'Host': 'evil.example'})[0] == 403
            print('PASS: real-server auth, CSRF, session revocation, subpaths, Supervisor isolation and direct header stripping')
        except Exception:
            log.flush()
            log.seek(0)
            print(log.read().replace(password, '[redacted]')[-5000:], file=sys.stderr)
            raise
        finally:
            for child in reversed(children):
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=20)
            log.close()


if __name__ == '__main__':
    main()
