import io
import json
import os
import tempfile
import unittest
import web_app

class SyncAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        web_app.DB_PATH=os.path.join(self.tmp.name,'db.sqlite3')
        web_app.SESSIONS=web_app.SessionManager()
    def tearDown(self): self.tmp.cleanup()
    def call(self,method,path,data=None,cookie=''):
        body=json.dumps(data).encode() if data is not None else b''
        result={}
        def start(status,headers):
            result['code']=int(status.split()[0])
            result['headers']=dict(headers)
        response=b''.join(web_app.app({'REQUEST_METHOD':method,'PATH_INFO':path,
          'CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body),
          'HTTP_COOKIE': cookie,
          'HTTP_X_CSRF_TOKEN': web_app.csrf_for(cookie.split('=',1)[1]) if cookie.startswith('session=') else ''},start))
        return result['code'],json.loads(response),result['headers']
    def test_two_device_conflict_and_isolation(self):
        _,_,ha=self.call('POST','/register',{'username':'alice','password':'a secure long password'})
        _,_,hb=self.call('POST','/register',{'username':'bobby','password':'another secure password'})
        a=ha['Set-Cookie'].split(';')[0]
        b=hb['Set-Cookie'].split(';')[0]
        self.assertEqual(self.call('POST','/my/sync',{'book_id':'b1','state':{'notes':'phone'},'expected_revision':0},a)[1]['revision'],1)
        self.assertEqual(self.call('POST','/my/sync',{'book_id':'b1','state':{'notes':'tablet'},'expected_revision':1},a)[1]['revision'],2)
        self.assertEqual(self.call('POST','/my/sync',{'book_id':'b1','state':{'notes':'stale'},'expected_revision':1},a)[0],409)
        self.assertEqual(self.call('GET','/my/sync',cookie=a)[1]['books'][0]['state']['notes'],'tablet')
        self.assertEqual(self.call('GET','/my/sync',cookie=b)[1]['books'],[])
        self.assertEqual(self.call('GET','/my/sync')[0],401)

if __name__=='__main__': unittest.main()
