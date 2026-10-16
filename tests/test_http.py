import http.client
import json
import re
import tempfile
import threading
import unittest

from ai4boji.core import Service
from ai4boji.server import create_server
from ai4boji.storage import Store


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = Service(Store(self.tmp.name))
        self.server = create_server(self.service, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port
        self.origin = 'http://127.0.0.1:' + str(self.port)
        code, html, headers = self.request('GET', '/')
        self.assertEqual(code, 200)
        self.token = re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        conn.request(method, path, json.dumps(body) if body is not None else None, headers or {})
        response = conn.getresponse()
        result = (response.status, response.read().decode(), dict(response.getheaders()))
        conn.close()
        return result

    def post(self, path, payload):
        return self.request('POST', path, payload, {'Origin': self.origin, 'X-CSRF-Token': self.token,
                                                   'Content-Type': 'application/json'})

    def test_dashboard_serves_chinese_and_never_exposes_database(self):
        code, html, headers = self.request('GET', '/')
        self.assertIn('<html lang="zh-CN">', html)
        self.assertIn('<title>AI4薄肌</title>', html)
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        for path in ['/data/ai4boji.sqlite3', '/../README.md', '/api/unknown']:
            self.assertEqual(self.request('GET', path)[0], 404)
        self.assertEqual(self.request('GET', '/', headers={'Host':'evil.example'})[0], 403)

    def test_post_requires_origin_token_and_json(self):
        self.assertEqual(self.request('POST', '/api/profile', {})[0], 403)
        self.assertEqual(self.request('POST', '/api/profile', {}, {'Origin':'https://evil.example',
            'X-CSRF-Token':self.token,'Content-Type':'application/json'})[0], 403)
        self.assertEqual(self.request('POST', '/api/profile', {}, {'Origin':self.origin,
            'X-CSRF-Token':self.token,'Content-Type':'text/plain'})[0], 415)
        self.assertEqual(self.post('/api/log', [1,2])[0], 400)

    def test_http_end_to_end_writes_are_visible_to_cli_core(self):
        code, body, _ = self.post('/api/profile', {'name':'Web test','age':25,'goal':'build a habit',
             'minutes':20,'days':[0,2,4],'equipment':'bodyweight','expected_revision':0})
        self.assertEqual(code, 200, body)
        self.assertEqual(self.post('/api/checkin', {'minutes':20,'pain':False})[0], 200)
        self.assertEqual(self.post('/api/plan', {})[0], 200)
        record={'id':'web-one','status':'partial','duration_min':12,'expected_revision':0}
        self.assertEqual(self.post('/api/log',record)[0],200)
        self.assertEqual(self.post('/api/log',record)[0],200)
        fresh=Service(Store(self.tmp.name))
        self.assertEqual(fresh.context()['report']['total_minutes'],12)
        status,state,_=self.request('GET','/api/state')
        self.assertEqual(status,200)
        self.assertEqual(len(json.loads(state)['logs']),1)
        self.assertEqual(json.loads(state)['title'],'AI4薄肌')

    def test_invalid_payload_does_not_modify_data(self):
        self.assertEqual(self.post('/api/forget', {'id': None})[0], 400)
        self.assertEqual(self.post('/api/profile',{'age':17})[0],400)
        self.assertIsNone(self.service.profile())
        self.assertEqual(self.post('/api/checkin',{'sleep_hours':99})[0],400)
        self.assertEqual(self.service.store.list('checkin'),[])


if __name__ == '__main__':
    unittest.main()
