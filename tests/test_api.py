"""Exercise the HTTP boundary with a fake session and synthetic token."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest

base = Path(__file__).parents[1] / 'custom_components/calmean'
package = types.ModuleType('calmean_test_api')
package.__path__ = [str(base)]
sys.modules[package.__name__] = package
spec = importlib.util.spec_from_file_location('calmean_test_api.api', base / 'api.py')
api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = api
spec.loader.exec_module(api)

class Response:
    def __init__(self, status, payload):
        self.status, self.payload = status, payload
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        return False
    async def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload

class Session:
    def __init__(self, status=200, payload=None, error=None):
        self.status, self.payload, self.error = status, payload, error
    def post(self, url, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return Response(self.status, self.payload)

class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_and_sensitive_request_controls(self):
        session = Session(payload=[{'deviceId': 'demo'}])
        result = await api.CalmeanClient(session, 'synthetic-token').devices()
        self.assertIn('demo', result)
        self.assertFalse(session.kwargs['allow_redirects'])
        self.assertEqual(session.kwargs['headers']['Authorization'], 'Bearer synthetic-token')
        self.assertEqual(session.kwargs['timeout'].total, 20)

    async def test_auth_errors(self):
        for status in (401, 403):
            with self.assertRaises(api.InvalidAuth):
                await api.CalmeanClient(Session(status=status), 'synthetic-token').devices()

    async def test_server_rate_limit_and_redirect_errors(self):
        for status in (429, 500, 302):
            with self.assertRaises(api.CannotConnect):
                await api.CalmeanClient(Session(status=status), 'synthetic-token').devices()

    async def test_timeout(self):
        with self.assertRaises(api.CannotConnect):
            await api.CalmeanClient(Session(error=asyncio.TimeoutError()), 'synthetic-token').devices()

    async def test_bad_json_and_unrecognized_schema(self):
        for payload in (ValueError('bad json'), {'unexpected': True}):
            with self.assertRaises(api.InvalidResponse):
                await api.CalmeanClient(Session(payload=payload), 'synthetic-token').devices()
