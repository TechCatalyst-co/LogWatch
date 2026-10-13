import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
os.environ['MONGODB_URI'] = 'mongomock://'
os.environ['ADMIN_PASSWORD'] = 'test'

import httpx
from fastapi.testclient import TestClient
import app
from store import Store


class AiErrorTests(unittest.TestCase):
    def test_provider_errors_preserve_fallback_without_exposing_key_or_raw_body(self):
        cases = [
            (401, {'error': {'message': 'Invalid key secret-test-key'}},
             'Invalid key [redacted]'),
            (400, {'error': {'message': 'Your credit balance is too low'}},
             'Your credit balance is too low'),
            (404, {'error': {'message': 'model: unavailable'}}, 'model: unavailable'),
            (429, {'error': {'message': 'Rate limit exceeded'}}, 'Rate limit exceeded'),
            (502, None, ''),
            (500, {'error': 'unexpected format'}, ''),
        ]
        for status, payload, expected in cases:
            with self.subTest(status=status):
                request = httpx.Request('POST', 'https://api.anthropic.com/v1/messages')
                response = (httpx.Response(status, json=payload, request=request)
                            if payload is not None else
                            httpx.Response(status, text='private raw body', request=request))
                error = httpx.HTTPStatusError('provider error', request=request, response=response)
                store = Store('mongomock://')
                store.init()
                with patch.object(app, 'store', store), patch.object(app, 'API_KEY', 'secret-test-key'), \
                     patch.object(app, 'ai_digest', AsyncMock(side_effect=error)):
                    result = TestClient(app.app).post('/api/digest?mode=ai', headers={
                        'Authorization': 'Bearer ' + app.make_token()})
                self.assertEqual(result.status_code, 200)
                data = result.json()
                self.assertEqual(data['mode'], 'rules')
                self.assertTrue(data['text'])
                self.assertIn(f'HTTP {status}', data['note'])
                self.assertIn(expected, data['note'])
                self.assertNotIn('secret-test-key', data['note'])
                self.assertNotIn('private raw body', data['note'])
