import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
os.environ['MONGODB_URI'] = 'mongomock://'
os.environ['ADMIN_PASSWORD'] = 'test'
os.environ['PUBLIC_VIEW'] = 'false'
from fastapi.testclient import TestClient
import app
from store import Store


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.store = Store('mongomock://')
        self.store.init()
        self.patch = patch.object(app, 'store', self.store)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.client = TestClient(app.app)
        self.headers = {'Authorization': 'Bearer ' + app.make_token()}
        self.store.events.insert_many([
            {'id': f'{i:04}', 'rx': i // 3, 'device': 'old' if i < 10 else 'busy',
             'source': 'linux' if i < 10 else 'router', 'level': i % 4}
            for i in range(650)
        ])

    def get(self, **params):
        return self.client.get('/api/events', params=params, headers=self.headers)

    def test_snapshot_counts_all_retained_events_and_devices(self):
        state = self.client.get('/api/state', headers=self.headers).json()
        self.assertEqual(len(state['events']), 400)
        self.assertEqual(state['total'], 650)
        self.assertEqual(sum(state['counts'].values()), 650)
        self.assertEqual(sum(d['count'] for d in state['devices']), 650)
        self.assertEqual({d['name'] for d in state['devices']}, {'old', 'busy'})

    def test_snapshot_ignores_stale_device_cache_after_expiration(self):
        self.store.devices.insert_one({'name': 'expired', 'count': 999})
        self.store.events.delete_many({'device': 'old'})
        state = self.store.snapshot()
        self.assertEqual(state['total'], 640)
        self.assertEqual([d['name'] for d in state['devices']], ['busy'])
        self.store.events.delete_many({})
        self.assertEqual(self.store.snapshot(),
                         {'events': [], 'devices': [], 'counts': {}, 'total': 0})

    def test_snapshot_does_not_cap_device_count_at_200(self):
        self.store.events.insert_many([
            {'id': f'd{i}', 'device': f'device{i}', 'rx': 1000, 'source': 'linux', 'level': 0}
            for i in range(205)
        ])
        self.assertEqual(len(self.store.snapshot()['devices']), 207)

    def test_device_outside_global_snapshot(self):
        self.assertFalse(any(e['device'] == 'old' for e in self.store.recent()))
        page = self.get(device='old').json()
        self.assertEqual(len(page['events']), 10)
        self.assertIsNone(page['next'])

    def test_pagination_with_tied_timestamps_and_new_arrivals(self):
        ids = []
        before = None
        while True:
            params = {'limit': 37}
            if before:
                params['before'] = json.dumps(before)
            page = self.get(**params).json()
            ids.extend(e['id'] for e in page['events'])
            if before is None:
                self.store.events.insert_one({'id': 'new', 'rx': 999, 'device': 'busy'})
            before = page['next']
            if before is None:
                break
        self.assertEqual(ids, [f'{i:04}' for i in reversed(range(650))])

    def test_filters_apply_before_pagination(self):
        rows = self.get(source='linux', alerts='true', limit=2).json()['events']
        self.assertEqual([e['id'] for e in rows], ['0007', '0006'])
        self.assertEqual(self.get(device='missing').json(), {'events': [], 'next': None})

    def test_authentication_required(self):
        self.assertEqual(self.client.get('/api/events').status_code, 401)

    def test_invalid_cursors_and_limits(self):
        for cursor in ['broken', '{}', '[true,"id"]', '[NaN,"id"]', '[1,{}]', '[1]']:
            self.assertEqual(self.get(before=cursor).status_code, 400)
        for limit in [0, -1, 401]:
            self.assertEqual(self.get(limit=limit).status_code, 422)


if __name__ == '__main__':
    unittest.main()
