"""Regression for CSRF continuity after a simulated process restart."""
import io
import json
import os
import tempfile
import unittest
import web_app
from persistent_sessions import SQLiteSessionManager


class RestartCsrfTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.original_db,self.original_sessions=web_app.DB_PATH,web_app.SESSIONS
        web_app.DB_PATH=os.path.join(self.tmp.name,'db.sqlite3')
        web_app.SESSIONS=SQLiteSessionManager(web_app.DB_PATH)

    def tearDown(self):
        web_app.DB_PATH,web_app.SESSIONS=self.original_db,self.original_sessions
        self.tmp.cleanup()

    def call(self,method,path,data=None,cookie='',csrf=None):
        raw=json.dumps(data).encode() if data is not None else b''
        env={'REQUEST_METHOD':method,'PATH_INFO':path,
             'CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw),
             'HTTP_COOKIE':cookie}
        if csrf is not None: env['HTTP_X_CSRF_TOKEN']=csrf
        result={}
        def start(status,headers):
            result['status']=int(status.split()[0])
            result['headers']=dict(headers)
        result['data']=json.loads(b''.join(web_app.app(env,start)))
        return result

    def test_restart_preserves_authenticated_write_with_csrf(self):
        first=self.call('POST','/register',{'username':'alice','password':'a secure long password'})
        cookie=first['headers']['Set-Cookie'].split(';')[0]
        csrf=self.call('GET','/csrf',cookie=cookie)['data']['csrf_token']
        web_app.SESSIONS=SQLiteSessionManager(web_app.DB_PATH)
        self.assertEqual(self.call('GET','/csrf',cookie=cookie)['data']['csrf_token'],csrf)
        saved=self.call('POST','/my/sync',{'book_id':'book-1',
                         'state':{'notes':'after restart'},'expected_revision':0},cookie,csrf)
        self.assertEqual(saved['status'],200)
        self.assertEqual(self.call('GET','/my/sync',cookie=cookie)['data']['books'][0]['state']['notes'],'after restart')


if __name__=='__main__':
    unittest.main()
