import io
import json
import os
import tempfile
import unittest
import web_app


class CsrfBrowserTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_db,self.old_sessions=web_app.DB_PATH,web_app.SESSIONS
        web_app.DB_PATH=os.path.join(self.tmp.name,'db.sqlite3')
        web_app.SESSIONS=web_app.SessionManager()

    def tearDown(self):
        web_app.DB_PATH,web_app.SESSIONS=self.old_db,self.old_sessions
        self.tmp.cleanup()

    def call(self,method,path,payload=None,cookie='',csrf=None,origin=None):
        raw=json.dumps(payload).encode() if payload is not None else b''
        env={'REQUEST_METHOD':method,'PATH_INFO':path,
             'CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw),
             'HTTP_COOKIE':cookie,'HTTP_HOST':'books.example.test',
             'wsgi.url_scheme':'https'}
        if csrf is not None: env['HTTP_X_CSRF_TOKEN']=csrf
        if origin is not None: env['HTTP_ORIGIN']=origin
        result={}
        def start(status,headers):
            result['status']=int(status.split()[0])
            result['headers']=dict(headers)
        result['data']=json.loads(b''.join(web_app.app(env,start)))
        return result

    def test_browser_write_requires_token_and_logout_revokes_session(self):
        registered=self.call('POST','/register',{'username':'alice','password':'a secure long password'})
        cookie=registered['headers']['Set-Cookie'].split(';')[0]
        token=self.call('GET','/csrf',cookie=cookie)['data']['csrf_token']
        origin='https://books.example.test'
        data={'book_id':'one','state':{'notes':'safe'},'expected_revision':0}
        self.assertEqual(self.call('POST','/my/sync',data,cookie,origin=origin)['status'],403)
        self.assertEqual(self.call('POST','/my/sync',data,cookie,csrf='invalid',origin=origin)['status'],403)
        self.assertEqual(self.call('POST','/my/sync',data,cookie,csrf=token,origin=origin)['status'],200)
        self.assertEqual(self.call('POST','/logout',{},cookie,origin=origin)['status'],403)
        self.assertEqual(self.call('POST','/logout',{},cookie,csrf=token,origin=origin)['status'],200)
        self.assertEqual(self.call('GET','/csrf',cookie=cookie)['status'],401)


if __name__=='__main__':
    unittest.main()
