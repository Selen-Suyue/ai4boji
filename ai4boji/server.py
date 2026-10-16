"""Loopback-only dashboard; no external services or telemetry."""
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

DASHBOARD = Path(__file__).resolve().parent / 'web'


def create_server(service, port=8765, demo=False):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Keep private query and record data out of console logs.

        def reply(self, status, content, content_type='application/json; charset=utf-8'):
            if not isinstance(content, bytes):
                content = json.dumps(content, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(content)

        def valid_host(self):
            port = self.server.server_port
            return self.headers.get('Host') in [f'127.0.0.1:{port}', f'localhost:{port}']

        def do_GET(self):
            if not self.valid_host():
                return self.reply(403, {'error': 'Host not allowed'})
            parts = urlsplit(self.path)
            try:
                if parts.path == '/api/state':
                    day = parse_qs(parts.query).get('date', [None])[0]
                    return self.reply(200, dict(service.state(day), demo=demo))
                if parts.path == '/api/export':
                    return self.reply(200, service.store.export())
                if parts.path == '/api/history':
                    key = parse_qs(parts.query).get('id', [''])[0]
                    return self.reply(200, service.store.history(key))
                assets = {'/': ('index.html', 'text/html'), '/index.html': ('index.html', 'text/html'),
                          '/app.js': ('app.js', 'application/javascript'), '/style.css': ('style.css', 'text/css')}
                if parts.path not in assets:
                    return self.reply(404, {'error': 'Not found'})
                filename, mime = assets[parts.path]
                content = (DASHBOARD / filename).read_text(encoding='utf-8')
                if filename == 'index.html':
                    content = content.replace('__CSRF_TOKEN__', token)
                self.reply(200, content.encode(), mime + '; charset=utf-8')
            except ValueError as error:
                self.reply(400, {'error': str(error)})

        def do_POST(self):
            port = self.server.server_port
            origins = [f'http://127.0.0.1:{port}', f'http://localhost:{port}']
            if not self.valid_host() or self.headers.get('Origin') not in origins or not secrets.compare_digest(self.headers.get('X-CSRF-Token', ''), token):
                return self.reply(403, {'error': 'Request not allowed'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.reply(415, {'error': 'Expected application/json'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 65536:
                    return self.reply(413, {'error': 'Invalid request size'})
                data = json.loads(self.rfile.read(length))
                routes = {'/api/profile': service.save_profile, '/api/checkin': service.save_checkin,
                          '/api/log': service.save_log, '/api/memory': service.save_memory,
                          '/api/plan': lambda d: service.generate_plan(d.get('date')),
                          '/api/forget': lambda d: service.store.forget(d.get('id', ''))}
                if self.path not in routes:
                    return self.reply(404, {'error': 'Not found'})
                if not isinstance(data, dict):
                    raise ValueError('Expected JSON object')
                self.reply(200, routes[self.path](data))
            except (ValueError, KeyError, TypeError) as error:
                self.reply(400, {'error': str(error)})

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server


def run(service, port=8765, demo=False):
    server = create_server(service, port, demo)
    print(f"AI4薄肌 {'· 合成演示 / Synthetic demo' if demo else '· 本地档案 / Personal'}", flush=True)
    print(f'http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
