import io
import json
import os
import tempfile
import unittest
import web_app


class OriginProtectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.original_path=web_app.DB_PATH
        self.original_sessions=web_app.SESSIONS
        web_app.DB_PATH=os.path.join(self.temp.name,'db.sqlite3')
        web_app.SESSIONS=web_app.SessionManager()

    def tearDown(self):
        web_app.DB_PATH=self.original_path
        web_app.SESSIONS=self.original_sessions
        self.temp.cleanup()

    def call(self,origin=None):
        body=json.dumps({'username':'alice','password':'a secure long password'}).encode()
        env={'REQUEST_METHOD':'POST','PATH_INFO':'/register',
             'CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body),
             'HTTP_HOST':'books.example.test','wsgi.url_scheme':'https'}
        if origin is not None:
            env['HTTP_ORIGIN']=origin
        result={}
        def start(status,headers):
            result['status']=int(status.split()[0])
        data=json.loads(b''.join(web_app.app(env,start)))
        return result['status'],data

    def test_same_origin_allowed(self):
        self.assertEqual(self.call('https://books.example.test')[0],200)

    def test_other_origin_blocked(self):
        code,_=self.call('https://evil.example.test')
        self.assertEqual(code,403)
        self.assertEqual(self.call('https://books.example.test')[0],200)

    def test_wrong_scheme_blocked(self):
        self.assertEqual(self.call('http://books.example.test')[0],403)

    def test_origin_with_path_blocked(self):
        self.assertEqual(self.call('https://books.example.test/other')[0],403)

    def test_legacy_no_origin_still_accepted(self):
        self.assertEqual(self.call()[0],200)


if __name__=='__main__':
    unittest.main()
