import os
import unittest
from unittest.mock import patch
from server import app

class AppTests(unittest.TestCase):
    def setUp(self): self.client=app.test_client()
    def test_home_without_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            r=self.client.get('/')
            self.assertEqual(r.status_code,200)
            self.assertIn(b'Fictional',r.data)
    def test_health(self): self.assertEqual(self.client.get('/health').json['status'],'ok')
    def test_no_secret_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.client.post('/webhook/call-completed',json={}).status_code,503)
    def test_invalid_auth(self):
        with patch.dict(os.environ, {'WEBHOOK_SECRET':'test-only'}, clear=True):
            self.assertEqual(self.client.post('/webhook/call-completed',json={}).status_code,401)
    def test_payload_validation(self):
        with patch.dict(os.environ, {'WEBHOOK_SECRET':'test-only'}, clear=True):
            h={'Authorization':'Bearer test-only'}
            self.assertEqual(self.client.post('/webhook/call-completed',json=[],headers=h).status_code,400)
            self.assertEqual(self.client.post('/webhook/call-completed',json={'call':[],'transcript':42},headers=h).status_code,400)
            self.assertEqual(self.client.post('/webhook/call-completed',json={},headers=h).status_code,200)
            self.assertEqual(self.client.post('/webhook/call-completed',json={'transcript':'example'},headers=h).status_code,503)
if __name__=='__main__': unittest.main()
