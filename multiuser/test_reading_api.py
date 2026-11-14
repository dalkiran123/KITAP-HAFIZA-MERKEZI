import io
import json
import os
import tempfile
import unittest
import web_app

class ReadingAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        web_app.DB_PATH=os.path.join(self.tmp.name,'users.sqlite3')
        web_app.SESSIONS=web_app.SessionManager()
    def tearDown(self): self.tmp.cleanup()
    def call(self,method,path,data=None,cookie=''):
        body=json.dumps(data).encode() if data is not None else b''
        result={}
        def start(status,headers):
            result['code']=int(status.split()[0])
            result['headers']=dict(headers)
        response=b''.join(web_app.app({'REQUEST_METHOD':method,'PATH_INFO':path,'CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body),'HTTP_COOKIE':cookie},start))
        return result['code'],json.loads(response),result['headers']
    def test_private_reading_and_leaderboard(self):
        _,_,ha=self.call('POST','/register',{'username':'alice','password':'a secure long password'})
        _,_,hb=self.call('POST','/register',{'username':'bobby','password':'another secure password'})
        a=ha['Set-Cookie'].split(';')[0]
        b=hb['Set-Cookie'].split(';')[0]
        event={'book_id':'book-1','completed_at':'2026-11-14T12:00:00Z'}
        self.assertEqual(self.call('POST','/my/reading',event,a)[0],200)
        self.assertEqual(self.call('POST','/my/reading',event,a)[0],200)
        self.assertEqual(len(self.call('GET','/my/reading',cookie=a)[1]['reading']),1)
        self.assertEqual(self.call('GET','/my/reading',cookie=b)[1]['reading'],[])
        self.assertEqual(self.call('GET','/my/reading')[0],401)
        board=self.call('GET','/leaderboard',cookie=b)[1]['leaderboard']
        self.assertEqual(dict((r['username'],r['books']) for r in board),{'alice':1,'bobby':0})
    def test_invalid_event(self):
        _,_,h=self.call('POST','/register',{'username':'alice','password':'a secure long password'})
        c=h['Set-Cookie'].split(';')[0]
        self.assertEqual(self.call('POST','/my/reading',{'book_id':'x','completed_at':'bad'},c)[0],400)

if __name__=='__main__': unittest.main()
